# DevRag

## AI-Powered Documentation Retrieval & Developer Assistant:

DevRag is a full-stack AI documentation assistant built using Retrieval-Augmented Generation (RAG) architecture.

## The platform allows users to:

- Upload PDFs
- Upload images for OCR-based text extraction
- Connect documentation websites
- Ask contextual questions
- Receive grounded AI-generated answers

DevRag uses semantic retrieval, vector embeddings, ChromaDB, LangChain, OCR, and Gemini API to provide accurate and context-aware responses from uploaded knowledge sources.

## Stack

- React + Vite frontend
- Tailwind CSS
- FastAPI backend
- Modular backend layout for future RAG implementation

## Project Structure

```text
devdocs-ai/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── pages/
├── backend/
│   └── app/
│       ├── config/
│       ├── rag/
│       ├── routes/
│       ├── services/
│       └── utils/
└── README.md
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite app runs on `http://localhost:5173`.

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000`.

## API Endpoints

- `GET /api/health` - health check
- `POST /upload/pdf` - upload a PDF, store it in `backend/uploads/pdfs`, and return an extracted text preview
- `POST /api/upload/pdf` - same PDF upload endpoint under the API prefix for frontend calls
- `POST /upload/image` - upload a PNG or JPG, store it in `backend/uploads/images`, and return OCR text from EasyOCR
- `POST /api/upload/image` - same image OCR endpoint under the API prefix for frontend calls
- `POST /upload/url` - crawl a documentation URL, store extracted metadata in `backend/uploads/urls`, and return a readable text preview
- `POST /api/upload/url` - same URL ingestion endpoint under the API prefix for frontend calls

The first image OCR request may take longer while EasyOCR initializes and downloads its language
model files.

RAG logic is not implemented yet. The `backend/app/rag` module is reserved for future embedding,
retrieval, and generation code.

## Chunking

PDF text, OCR text, and crawled documentation content are chunked with LangChain's
`RecursiveCharacterTextSplitter`. Chunk files are stored as JSON in `backend/uploads/chunks` with
source metadata such as source type, filename, page number, and URL. Embeddings are intentionally
not implemented yet.

## Vector Storage

Chunk files can be embedded with `sentence-transformers/all-MiniLM-L6-v2` and stored in ChromaDB.
By default, the persistent Chroma database lives in `C:/tmp/devrag-chroma` to avoid SQLite file
locking issues in OneDrive-backed project folders. Override `CHROMA_DB_DIR` in `backend/.env` if
you want a different location.

- `POST /api/vectors/insert` - insert embeddings for all chunk files or one `chunk_filename`
- `GET /api/vectors/chunks` - list available chunk files
- `POST /api/vectors/reset` - clear the current ChromaDB collection
- `POST /api/vectors/query` - retrieve similar stored chunks for a query
- `POST /api/retrieval/semantic` - retrieve top relevant chunks for a user question, including metadata and similarity scores
- `POST /api/rag/answer` - retrieve relevant chunks, send grounded context to Gemini, and return an answer with source citations

Set `GEMINI_API_KEY` in `backend/.env` before using Gemini answer generation.

## ✨ Features
📄 Multi-Source Knowledge Ingestion

## Supports:

- PDF documentation
- OCR-based image text extraction
- Documentation website indexing
- 🧠 Retrieval-Augmented Generation (RAG)

## Implements a complete RAG pipeline:

- Extract content
- Chunk documents
- Generate embeddings
- Store vectors in ChromaDB
- Perform semantic retrieval
- Generate grounded AI answers using Gemini
- 🔍 Semantic Search

Instead of traditional keyword matching, DevRag uses vector embeddings and semantic similarity search to retrieve contextually relevant information.

## 🖼 OCR Integration

## Uses EasyOCR to extract text from:

- screenshots
- scanned notes
- technical diagrams
- image-based documents
- 🌐 Documentation Website Processing

## Users can connect documentation URLs such as:

- React Docs
- FastAPI Docs
- LangChain Docs

The system extracts readable content and indexes it for AI-powered retrieval.

## 📌 Source-Aware Retrieval Filtering

DevRag prevents retrieval contamination using metadata-aware vector filtering.

Each uploaded source is tagged with:

- upload_id
- source_type
- source_name
- filename
- URL metadata

During retrieval, ChromaDB filters vectors using:
where={"upload_id": active_upload_id}

## This ensures:

- PDF questions retrieve PDF chunks only
- React documentation questions retrieve React chunks only
- no cross-source contamination occurs
- ⚠️ Engineering Challenge Solved
- Retrieval Contamination Problem
- Issue

## Initially, all vectors from:

- PDFs
- URLs
- OCR images

were stored inside the same ChromaDB collection.

This caused unrelated vectors (such as React documentation chunks) to appear during PDF-related queries.

## As a result:

- retrieval returned incorrect chunks
- Gemini generated unrelated answers
  
## ✅ Solution

Implemented metadata-aware retrieval filtering.

- Fixes Added
- unique upload_id for every upload
- active source tracking
- metadata-based ChromaDB filtering
- source-aware semantic retrieval
- retrieval debug logging

This eliminated cross-source retrieval contamination without requiring vector resets.

## 🏗 System Architecture
```
PDF / Image / Documentation URL
                ↓
Content Extraction Layer
                ↓
OCR / PDF Parsing / URL Processing
                ↓
Chunking
                ↓
Embedding Generation
                ↓
ChromaDB Vector Storage
                ↓
Semantic Retrieval
                ↓
Metadata Filtering
                ↓
Gemini LLM
                ↓
Grounded AI Response
```

## 🔄 Complete Workflow

## 1. Upload Knowledge Source

User uploads:

- PDF
- image
- documentation URL

## 2. Content Extraction

- PDFs → PyMuPDF
- Images → EasyOCR
- URLs → BeautifulSoup

## 3. Chunking

Large text is split into smaller chunks using LangChain text splitters.

## 4. Embedding Generation

Each chunk is converted into vector embeddings using Sentence Transformers.

## 5. Vector Storage

Embeddings are stored inside ChromaDB along with metadata.

## 6. Semantic Retrieval

- User question is converted into embeddings.

- ChromaDB performs similarity search to retrieve relevant chunks.

## 7. Metadata Filtering

Retrieval is filtered using:

- upload_id
- source_type
- source_name

This prevents retrieval contamination.

## 8. Grounded AI Response

Retrieved chunks are sent to Gemini API to generate contextual grounded answers.

## 🧠 Core Concepts Implemented

- Retrieval-Augmented Generation (RAG)
- Semantic Retrieval
- Vector Embeddings
- ChromaDB Vector Search
- OCR Text Extraction
- Metadata-Aware Filtering
- Grounded AI Generation
- Multi-Source Knowledge Ingestion
- Similarity Search
- Source-Aware Retrieval
- Hallucination Reduction

## 🚀 Future Improvements

- Authentication & User Sessions
- Multi-user Workspace Support
- Streaming Responses
- Chat History
- Local LLM Support (Ollama / Llama3)
- Multi-document simultaneous querying
- Hybrid Search (keyword + vector)
- Deployment using Docker & AWS

## 📸 Screenshots

Add:

## Home Page
<img width="1600" height="697" alt="WhatsApp Image 2026-05-10 at 7 27 43 PM" src="https://github.com/user-attachments/assets/e9e59a1e-7217-472c-a649-b11e0d18ecce" />
## Upload Dashboard

<img width="1600" height="705" alt="WhatsApp Image 2026-05-10 at 7 28 09 PM" src="https://github.com/user-attachments/assets/2f0531e1-7c71-4fa7-9793-642fae72a1cc" />

<img width="1600" height="709" alt="WhatsApp Image 2026-05-10 at 7 28 34 PM" src="https://github.com/user-attachments/assets/7cb724e2-670e-4f53-88b4-62874f0440f9" />

## Chat Interface
<img width="1600" height="701" alt="WhatsApp Image 2026-05-10 at 7 28 53 PM" src="https://github.com/user-attachments/assets/11103d1b-d829-4465-9b3d-6479599361d8" />

##  Document Crawling 
<img width="1600" height="709" alt="WhatsApp Image 2026-05-10 at 7 29 57 PM" src="https://github.com/user-attachments/assets/23616bab-33c9-490f-a071-eb806683dc09" />

## Retrieval Results
<img width="1600" height="713" alt="WhatsApp Image 2026-05-10 at 7 30 40 PM" src="https://github.com/user-attachments/assets/70113bfc-4221-4882-bb4e-4087807988e8" />
