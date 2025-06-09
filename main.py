from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import re
import json
import os
from serpapi import GoogleSearch
import mysql.connector
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import asyncio
from datetime import date

# ---- App Initialization ----
app = FastAPI()

# ---- DB Config ----
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Qwert54321@',
    'database': 'assessmentdb',
    'port': 3306
}

SERP_API_KEY = "0d8f5af11b2b23cbaf8cf14c0f294503e2353114ccbff990230b77727cdb1220"

@app.get("/homepage", response_class=HTMLResponse)
async def read_root():
    with open("C://Users//rishu//OneDrive//Desktop//assessment//rag_agentic_chat//static//index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# ---- User Query Model ----
class QueryRequest(BaseModel):
    query: str

# ---- Sample Tool Function ----
async def search_documents_by_keyword(keyword: str):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        #query = """
        #    SELECT title,  abstract, pdf_url, publication_date, excerpts
        #    FROM federal_documents
        #    WHERE title LIKE %s OR abstract LIKE %s OR excerpts LIKE %s
        #"""
        query = """
            SELECT title, abstract, pdf_url, publication_date, excerpts,
                MATCH(title, abstract, excerpts) AGAINST (%s IN NATURAL LANGUAGE MODE) AS score
            FROM federal_documents
            WHERE MATCH(title, abstract, excerpts) AGAINST (%s IN NATURAL LANGUAGE MODE)
            ORDER BY score DESC
            LIMIT 5;
        """
        cursor.execute(query, (keyword, keyword))
        #wildcard = f"%{keyword}%"
        #cursor.execute(query, (wildcard, wildcard, wildcard))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}

async def web_search_with_serpapi(keyword: str):
    try:
        params = {
            "engine": "google",
            "q": keyword,
            "api_key": SERP_API_KEY,
            "num" : 5
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        top_results = []
        for result in results.get("organic_results", [])[:5]:
            top_results.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet")
            })

        return top_results
       
    except Exception as e:
        return {"error": str(e)}
    

# ---- TOOL FUNCTION DEFINITIONS (function schema) ----
TOOLS = {
    "search_documents_by_keyword": {
        "name": "search_documents_by_keyword",
        "description": "Search documents by a keyword in title, abstract, or excerpts",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"}
            },
            "required": ["keyword"]
        }
    },
     "web_search_with_serpapi": {
        "name": "web_search_with_serpapi",
        "description": "Search the web using SerpAPI for real-time information.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"}
            },
            "required": ["keyword"]
        }
    }
}


# ---- Ollama Chat with Tool Calling (Streaming Version) ----
async def chat_with_agent(user_query: str):


    SYSTEM_PROMPT = (
        "You are a helpful agent that can answer user queries using your own knowledge or by using tools.\n\n"
        "Available tools:\n"
        "1. search_documents_by_keyword — for searching local government documents.\n"
        "2. web_search_with_serpapi — for searching live web results using SerpAPI.\n\n"
        "Your behavior:\n"
        "- If you are **very confident** about the answer, respond directly like this:\n"
        "  {\"answer\": \"...\"}\n"
        "- If you are **not confident**, then get help from a tool. Decide **which tool** is appropriate for the query.\n"
        "- If you are using a tool, respond like this:\n"
        "  {\"tool_call\": {\"name\": \"tool_name_here\", \"arguments\": {\"keyword\": \"...\"}}, \"answer\": \"...\"}\n\n"
        "**Important**:\n"
        "- If you use a tool, the final response **must be based strictly on the tool output**, not your own assumptions.\n"
        "- Do not hallucinate or add extra information not present in the tool result.\n"
        "- Be helpful, factual, and concise."
    )


    body = {
        "model": "llama3.2:latest",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.3
    }

    full_response = ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0)) as client:
        async with client.stream("POST", "http://localhost:11434/api/chat", json=body) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        json_obj = json.loads(line)
                        full_response += json_obj.get("message", {}).get("content", "")
                    except json.JSONDecodeError:
                        continue

    content = full_response.strip()

    # Check if it's a tool call (JSON)
    try:
        json_str_match = re.search(r"\{[\s\S]*\}", content)
        if not json_str_match:
            raise ValueError("No JSON object found in content.")
    
        tool_obj = json.loads(json_str_match.group())

        #tool_obj = json.loads(content)
        tool_response = ""

        if "tool_call" in tool_obj:
            tool_name = tool_obj["tool_call"]["name"]
            args = tool_obj["tool_call"]["arguments"]
            if tool_name in TOOLS:
                result = await eval(f"{tool_name}(**args)")
                print("Tool Result:\n", result)

                summary =  await summarize_tool_result(user_query, result,tool_name)
                tool_response += summary
                print('Tool_response:\n',tool_response)
                #return tool_response
            
                final_response =  f"{tool_obj.get('answer', '')}\n\n{tool_response}".strip()
                print("final_response:\n",final_response)
                return final_response
         # If no tool call or tool processing failed, return the answer
        return f"{tool_obj.get('answer', '')}\n\n{tool_response}".strip()
            
    except Exception as e:
        print("Tool call processing failed:",e)
        print("Raw LLM response content:\n", content)

        return content

# ---- Final Summary After Tool Execution ----
async def summarize_tool_result(user_query, tool_result, tool_name = None):
    # Convert datetime.date objects to ISO string format
   # Convert each dict to JSON
    json_results = []
    if tool_name == "search_documents_by_keyword":
        for item in tool_result:
            
            for key, value in item.items():
                if isinstance(value, date):
                    item[key] = value.isoformat()
            # Convert to JSON string
            json_str = json.dumps(item, ensure_ascii=False, indent=2)
            json_results.append(json_str)
            
    elif tool_name == "web_search_with_serpapi":
        for item in tool_result:
                snippet = f"""
            Title: {item.get('title')}
            Link: {item.get('link')}
            Snippet: {item.get('snippet')}
    """
                json_results.append(snippet.strip())
    print("JSON results: \n",json_results)

    tool_type = "government document search" if tool_name == "search_documents_by_keyword" else "live web search using SerpAPI"

    if all('title' in item and 'link' in item and 'snippet' in item for item in tool_result):
    # Tool: Serpapi web search tool
        system_content = (
            "You are a helpful assistant. Based on the following search results provided as plain text entries, write a short, factual summary. Only use the provided data. Each entry includes a title, link, snippet."
                    "Snippet includes detailed description of the article so give more attention to snippet section."
                    "Also include link section in the answer so that user can open the link for more information."
                    "Do not add your own assumptions. Only use the information from the tool result."
        )
    elif all('title' in item and 'abstract' in item and 'pdf_url' in item and 'excerpts' in item for item in tool_result):
        # Tool database search 
        system_content = (
            "You are a helpful assistant.Based on the following search results provided as plain text entries, write a short, factual summary. Only use the provided data. Each entry includes a title, abstract, pdf_url,publication_date,excerpts."
                    "abstract and excerpts includes detailed description of the article so give more attention to abstract and excerpts section."
                    "Also include pdf_url section in the answer so that user can open the link for more information."
                    "Also include publication_date in the answer so that user can know about the date details."
                    "Do not add your own assumptions. Only use the information from the tool result."
    )
        
    body = {
        "model": "llama3.2:latest",
        "messages": [
            {
                "role": "system",
                "content": system_content
                   
                
            },
            {
                "role": "user",
                "content": f"Query: {user_query}\n\nTool Result:\n" + "\n".join(json_results)

            }
        ]
    }
   

    full_response = ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=60.0)) as client:
        async with client.stream("POST", "http://localhost:11434/api/chat", json=body) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        json_obj = json.loads(line)
                        full_response += json_obj.get("message", {}).get("content", "")
                    except json.JSONDecodeError:
                        continue
    print("full response: \n",full_response.strip())
    return full_response.strip()

# ---- API Route ----
@app.post("/query")
async def query_agent(query_req: QueryRequest):
    try:
        answer = await chat_with_agent(query_req.query)
        try:
            decoded = json.loads(answer)
            clean_response = decoded.get("answer", answer)
        except json.JSONDecodeError:
            clean_response = answer

        return {"response": clean_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
