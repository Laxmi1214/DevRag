from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from google import genai
from google.genai import types

from app.config.settings import settings
from app.services.retrieval_service import retrieve_relevant_chunks


def generate_grounded_answer(question: str, limit: int | None = None) -> dict[str, Any]:
    retrieval_result = retrieve_relevant_chunks(question, limit)
    chunks = retrieval_result["chunks"]

    if not chunks:
        return {
            "status": "success",
            "question": question,
            "answer": "I could not find relevant context in the indexed documentation.",
            "retrieved_sources": [],
            "source_citations": [],
            "active_source": retrieval_result.get("active_source"),
            "metadata_filter": retrieval_result.get("metadata_filter"),
            "collection": retrieval_result["collection"],
            "embedding_model": retrieval_result["embedding_model"],
            "generation_model": settings.GEMINI_MODEL_NAME,
        }

    prompt = build_rag_prompt(question=question, chunks=chunks)
    answer = call_gemini(prompt)
    citations = build_source_citations(chunks)

    return {
        "status": "success",
        "question": retrieval_result["question"],
        "answer": answer,
        "retrieved_sources": chunks,
        "source_citations": citations,
        "collection": retrieval_result["collection"],
        "embedding_model": retrieval_result["embedding_model"],
        "generation_model": settings.GEMINI_MODEL_NAME,
        "active_source": retrieval_result.get("active_source"),
        "metadata_filter": retrieval_result.get("metadata_filter"),
    }


def build_rag_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    context_blocks = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source_label = format_source_label(index, metadata)
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}] {source_label}",
                    f"Similarity score: {chunk.get('similarity_score')}",
                    "Content:",
                    chunk.get("text", ""),
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are DevRag, a documentation question-answering assistant.

Answer the user's question using only the provided retrieved documentation context.

Rules:
- Ground every factual claim in the provided context.
- Cite sources inline using bracket citations like [Source 1] or [Source 2].
- If the context does not contain enough information, say so clearly.
- Do not mention Gemini, embeddings, vector databases, or internal implementation details.
- Keep the answer concise and useful.

Question:
{question}

Retrieved documentation context:
{context}

Grounded answer:
"""


def call_gemini(prompt: str) -> str:
    client = get_gemini_client()

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=build_gemini_error_message(exc),
        ) from exc

    text = getattr(response, "text", None)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API returned an empty response.",
        )

    return text.strip()


@lru_cache(maxsize=1)
def get_gemini_client():
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured.",
        )

    return genai.Client(api_key=api_key)


def build_source_citations(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        citations.append(
            {
                "source_number": index,
                "chunk_id": chunk.get("id"),
                "label": format_source_label(index, metadata),
                "source_type": metadata.get("source_type"),
                "source_name": metadata.get("source_name"),
                "upload_id": metadata.get("upload_id"),
                "filename": metadata.get("filename"),
                "page_number": metadata.get("page_number"),
                "url": metadata.get("url"),
                "chunk_filename": metadata.get("chunk_filename"),
                "similarity_score": chunk.get("similarity_score"),
            }
        )

    return citations


def format_source_label(index: int, metadata: dict[str, Any]) -> str:
    source_type = metadata.get("source_type", "source")
    filename = metadata.get("filename")
    page_number = metadata.get("page_number")
    url = metadata.get("url")

    if url:
        return f"{source_type}: {url}"

    if filename and page_number:
        return f"{source_type}: {filename}, page {page_number}"

    if filename:
        return f"{source_type}: {filename}"

    return f"Source {index}"


def build_gemini_error_message(exc: Exception) -> str:
    message = str(exc)

    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        return "Gemini API quota exceeded. Check your Google AI Studio quota, billing, API key project, or try another Gemini model."

    if "API key" in message or "permission" in message.lower() or "403" in message:
        return "Gemini API authentication failed. Check that GEMINI_API_KEY is valid and enabled for the Gemini API."

    return "Gemini API request failed."
