# DevRag

Production-style full-stack scaffold for a developer-documentation RAG app.

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
