# Legal Support API

This API allows you to process legal documents (.docx files) using the Legal Support Agents and retrieve information using Retrieval Augmented Generation (RAG).

## Installation

1. Install the package and dependencies:

```bash
pip3 install -e .
```

2. Set up environment variables (create a `.env` file in the root directory):

```
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_VERSION=your_azure_openai_version
GPT4_DEPLOYMENT_NAME=your_gpt4_deployment_name
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# Optional LanceDB Configuration (defaults to local file storage)
LANCEDB_STORAGE=lancedb_local
# For Azure Blob Storage
# LANCEDB_URI=az://lancedb
# LANCEDB_ACCOUNT_NAME=your_account_name
# LANCEDB_ACCOUNT_KEY=your_account_key
```

## Running the API

```bash
python3 app.py
```

By default, the API will run on `0.0.0.0:8000`.

## API Endpoints

### POST /query

Send a text query for analysis.

**Example using curl:**

```bash
curl -X POST "http://localhost:8000/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key clauses in a UK employment contract?"}'
```

**Example using Python requests:**

```python
import requests
import json

url = "http://localhost:8000/query"
payload = {"query": "What are the key clauses in a UK employment contract?"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json())
```

### POST /docx-query

Upload a .docx file to extract the text content and store it in the vector database for retrieval.

**Example using curl:**

```bash
curl -X POST "http://localhost:8000/docx-query" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.docx" \
  -F "document_name=Employment Contract - John Doe"
```

**Example using Python requests:**

```python
import requests

url = "http://localhost:8000/docx-query"
files = {"file": open("your_document.docx", "rb")}
data = {"document_name": "Employment Contract - John Doe"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Response Format for /docx-query

```json
{
  "filename": "your_document.docx",
  "document_name": "Employment Contract - John Doe",
  "document_id": "b8f3e8a1-d1c2-43a5-9d7f-8a5e5b6c9d13",
  "document_text": "Extracted text from the document...",
  "chunks_added": 12
}
```

### POST /search

Search for documents or sections matching a query using vector search and keyword matching.

**Example using curl:**

```bash
curl -X POST "http://localhost:8000/search" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the working hours?",
    "document_id": "b8f3e8a1-d1c2-43a5-9d7f-8a5e5b6c9d13",
    "limit": 5
  }'
```

**Example using Python requests:**

```python
import requests
import json

url = "http://localhost:8000/search"
payload = {
    "query": "What are the working hours?",
    "document_id": "b8f3e8a1-d1c2-43a5-9d7f-8a5e5b6c9d13",  # Optional: to search within a specific document
    "limit": 5  # Optional: number of results to return
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json())
```

### Response Format for /search

```json
{
  "query": "What are the working hours?",
  "results": [
    {
      "text": "Your normal working hours will be from 9:00 am to 5:00 pm on Monday to Friday inclusive. You will be entitled to an hour's lunch break during each working day taken by agreement with your supervisor. Subject to clause 9.1, your hours and days of work will not vary.",
      "document_id": "b8f3e8a1-d1c2-43a5-9d7f-8a5e5b6c9d13",
      "document_name": "Employment Contract - John Doe",
      "section": "10.1 Hours of Work",
      "score": 0.92
    },
    {
      "text": "You may be required to work at such other times as may be reasonably necessary for the proper performance of your duties without additional remuneration.",
      "document_id": "b8f3e8a1-d1c2-43a5-9d7f-8a5e5b6c9d13",
      "document_name": "Employment Contract - John Doe",
      "section": "10.2 Hours of Work",
      "score": 0.85
    }
  ]
}
```

## API Documentation

When the API is running, you can access the interactive documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 