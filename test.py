import httpx
import asyncio
import json
timeout = httpx.Timeout(60.0, connect=30.0)

async def test_ollama():
    async with httpx.AsyncClient() as client:
        body = {
            "model": "llama3.2:latest",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        }
       # response = await client.post("http://localhost:11434/api/chat", json=body)
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0)) as client:
            async with client.stream("POST", "http://localhost:11434/api/chat", json=body) as response:
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip():  # avoid empty lines
                        try:
                            json_obj = json.loads(line)
                            full_response += json_obj.get("message", {}).get("content", "")
                        except json.JSONDecodeError:
                            print("Skipping line due to JSON error:", line)

                print("Final Response:\n", full_response)
            

asyncio.run(test_ollama())
