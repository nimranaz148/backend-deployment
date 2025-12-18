<!-- README.md -->
# RAG Chatbot Backend

This is the backend service for the RAG Chatbot, built with FastAPI. It handles document ingestion, vector embedding, Qdrant interaction, and chat responses using the OpenAI API.

## Features

-   **Document Ingestion**: Processes markdown files from the `physical-ai-textbook/docs/` directory, chunks them by headers, creates embeddings, and stores them in a Qdrant vector database.
-   **Chat Endpoint**: Provides a streaming API for answering questions based on the ingested textbook content.
-   **API Key Security**: Secures endpoints with a pre-shared API key.
-   **Chat History Logging**: Logs all user-AI interactions to a Neon Postgres database.

## Tech Stack

-   **Framework**: FastAPI
-   **ASGI Server**: Uvicorn
-   **Environment Management**: python-dotenv
-   **Data Validation**: Pydantic
-   **Vector Database**: Qdrant-client
-   **LLM Integration**: OpenAI Python Library
-   **HTML Parsing**: beautifulsoup4 (for future potential use in document loading)
-   **PostgreSQL Driver**: psycopg2-binary
-   **Database**: Neon Serverless Postgres (for chat history)

## Setup

### Prerequisites

-   Python 3.12+
-   `pip` for package installation
-   Access to OpenAI, Qdrant, and Neon accounts.

### Environment Variables

Create a `.env` file in the `rag_chatbot/` directory. You can use the provided `.env.example` as a template:

```bash
cp .env.example .env
```

Now, fill in the values in the `.env` file:

```ini
OPENAI_API_KEY="sk-..."                     # Your OpenAI API Key
QDRANT_URL="https://your-qdrant-url.cloud"  # Your Qdrant Cloud URL
QDRANT_API_KEY="..."                        # Your Qdrant Cloud API Key
NEON_DB_URL="postgres://..."                # Your Neon Postgres Database URL
API_KEY="a-secure-random-string"            # A secure, random string for API access
```

**Important**: Ensure all required environment variables are set. The application will raise an error if any are missing.

### Install Dependencies

It is recommended to use a Python virtual environment.

```bash
# Navigate to the backend directory
cd rag_chatbot

# Create a virtual environment (if you haven't already)
python -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### 1. Start the Server

From the `rag_chatbot/` directory, use `uvicorn` to run the FastAPI application:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can access the FastAPI interactive documentation at `http://localhost:8000/docs`.

### 2. Run Document Ingestion

To populate the vector database with textbook content, send a POST request to the `/ingest` endpoint. This process runs in the background.

```bash
curl -X POST http://localhost:8000/ingest \
-H "X-API-Key: your-api-key"
```
Replace `your-api-key` with the value set in your `.env` file.

### 3. Test the Chat Endpoint

Once ingestion is complete, you can test the chat functionality:

```bash
curl -X POST http://localhost:8000/api/chat \
-H "Content-Type: application/json" \
-H "X-API-Key: your-api-key" \
-d 
{
  "message": "What is Physical AI?",
  "history": []
}
```
Replace `your-api-key` with the value set in your `.env` file. The response will be streamed.

---
