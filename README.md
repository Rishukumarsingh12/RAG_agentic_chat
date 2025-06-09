# 🧠 RAG-Based Executive Order Summarizer Chatbot

This project is a **Retrieval-Augmented Generation (RAG)** chat system designed to respond to user questions about U.S. executive orders. It fetches real-time documents from the Federal Register API, stores them in a MySQL database, and uses a locally hosted **LLM (LLaMA 3.2 via Ollama)** to provide summarized, factual responses with references.

---

## 🚀 Query Example
**Query Asked**:  what are the new executive orders by president donald trump this month and summarize them for me.


**Response from System**:

![Response Screenshot]![Screenshot 2025-06-09 195047](https://github.com/user-attachments/assets/0fbfe730-3c51-43af-ad29-f5f239605c83)


---

## 🛠️ Tools Used in the RAG Agentic System

This project leverages two custom tool functions integrated into the agent framework to support retrieval-augmented responses:

### 🔍 Tool 1: `search_documents_by_keyword`
- **Function**: `search_documents_by_keyword`
- **Description**: Searches pre-fetched executive orders from the Federal Register API stored in your local MySQL database.
- **Search Scope**: Title, abstract, and excerpt fields.
- **Use Case**: This tool is used when the query pertains to U.S. government documents such as presidential executive orders or agency updates.

### 🌐 Tool 2: `web_search_with_serpapi`
- **Function**: `web_search_with_serpapi`
- **Description**: Executes real-time web searches via [SerpAPI](https://serpapi.com) to fetch up-to-date public web data.
- **Search Scope**: Broader web search, especially when internal sources do not provide enough information.
- **Use Case**: This tool is used when a query requires external context, like news headlines, recent events, or general knowledge.

The agent intelligently decides which tool to invoke based on the user query and presents only relevant results to the language model.

---
## 🛠️ System Architecture
+-----------------------------+
| User (Frontend) |
| - Text input / HTML UI |
+-------------+--------------+
|
v
+-------------+--------------+
| FastAPI Backend |
| - Serves UI |
| - Receives user queries |
| - Passes them to LLM tool |
+-------------+--------------+
|
v
+-------------+--------------+
| RAG Pipeline Core |
| |
| 1. Query search into the mysql DB through search qeury |
| 2. Relevant docs retrieved |
| 3. Prompt constructed |
| 4. Sent to Ollama (LLaMA3.2) |
+-------------+--------------+
|
v
+-----------------------------+
| LLM Response (Summarized) |
+-----------------------------+


1. **Daily Fetch**:
   - Uses the [Federal Register API](https://www.federalregister.gov) to pull the latest executive orders.
   - Parses nested JSON (including agencies).

2. **Dynamic Table Creation**:
   - Inspects API schema.
   - Creates MySQL tables dynamically.

3. **Database Insertion**:
   - Inserts records, including metadata like:
     - `title`
     - `summary`
     - `publication_date`
     - `pdf_url`
     - `agencies`

4. **Qeury Search**:
   - Embeds text using a local embedding model.
   - Relevent documents are searched using sql qeury or google search through serpapi.

---

## 🧠 LLM Agent

- **LLM Used**: `llama3.2:latest` via [Ollama](https://ollama.com)
- **Prompt Logic**:
  - System prompt restricts LLM to only use retrieved data.
  - Responses are concise, factual, and include source links.

---

## ⚙️ Technologies Used

| Tool        | Purpose                      |
|-------------|------------------------------|
| **FastAPI** | Backend and API              |
| **MySQL**   | Structured data storage      | |
| **Ollama**  | LLM inference engine         |
| **HTML/CSS**| UI for asking questions      |

---

## 📷 Screenshot

> A summarised answer given by the system for May 2025 executive orders by President Donald Trump:

![Summary Screenshot]![Screenshot 2025-06-09 195047](https://github.com/user-attachments/assets/011a30c8-0c78-4c10-9154-1172bda80496)

---

## 📌 Future Improvements

- Add support for multi-modal queries (e.g., voice input).
- Implement document upload for custom RAG.
- Enable feedback loop to fine-tune responses based on user rating.

---

## 👨‍💻 Author

**Rishu Kumar**

If you found this interesting or want to collaborate, feel free to connect on [GitHub](https://github.com/Rishukumarsingh12).
