import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from fastapi import HTTPException, status
from sentence_transformers import SentenceTransformer

from app.config.settings import settings
from app.services.storage_service import get_chroma_db_dir, get_chunk_upload_dir

logger = logging.getLogger(__name__)


def insert_chunk_embeddings(
    *,
    chunk_filename: str | None = None,
    reindex: bool = True,
) -> dict[str, Any]:
    chunk_files = resolve_chunk_files(chunk_filename)
    collection = get_collection()
    inserted_count = 0
    indexed_files = []

    for chunk_file in chunk_files:
        payload = load_chunk_payload(chunk_file)
        chunks = payload.get("chunks", [])

        if not chunks:
            continue

        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [
            sanitize_metadata(
                {
                    **chunk.get("metadata", {}),
                    "chunk_index": chunk.get("chunk_index"),
                    "chunk_filename": chunk_file.name,
                    "source_type": payload.get("source_type"),
                    "source_id": payload.get("source_id"),
                    "source_name": payload.get("source_name"),
                    "upload_id": payload.get("upload_id"),
                }
            )
            for chunk in chunks
        ]

        embeddings = embed_texts(texts)

        if reindex:
            existing = collection.get(ids=ids)
            existing_ids = existing.get("ids", [])
            if existing_ids:
                collection.delete(ids=existing_ids)

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        inserted_count += len(ids)
        indexed_files.append(chunk_file.name)

    return {
        "status": "success",
        "message": "Chunk embeddings inserted into ChromaDB.",
        "collection": settings.CHROMA_COLLECTION_NAME,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "inserted_count": inserted_count,
        "indexed_files": indexed_files,
    }


def list_available_chunk_files() -> dict[str, Any]:
    chunk_dir = get_chunk_upload_dir()
    files = []

    for path in sorted(chunk_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = load_chunk_payload(path)
        files.append(
            {
                "filename": path.name,
                "source_type": payload.get("source_type"),
                "source_id": payload.get("source_id"),
                "source_name": payload.get("source_name"),
                "upload_id": payload.get("upload_id"),
                "chunk_count": payload.get("chunk_count", 0),
                "created_at": payload.get("created_at"),
                "metadata": payload.get("metadata", {}),
            }
        )

    return {
        "status": "success",
        "chunk_files": files,
    }


def reset_vector_collection() -> dict[str, Any]:
    client = get_chroma_client()

    try:
        client.delete_collection(settings.CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    get_collection()

    return {
        "status": "success",
        "message": "Vector collection reset successfully.",
        "collection": settings.CHROMA_COLLECTION_NAME,
    }


def query_vectors(
    query: str,
    limit: int | None = None,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    query_limit = limit or settings.VECTOR_QUERY_LIMIT
    collection = get_collection()
    query_embedding = embed_texts([cleaned_query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=query_limit,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, vector_id in enumerate(ids):
        matches.append(
            {
                "id": vector_id,
                "text": documents[index],
                "metadata": metadatas[index],
                "distance": distances[index],
                "similarity_score": distance_to_similarity_score(distances[index]),
                "source_name": metadatas[index].get("source_name"),
                "source_type": metadatas[index].get("source_type"),
            }
        )

    logger.debug(
        "Chroma query filter=%s retrieved_sources=%s",
        where,
        [match.get("source_name") for match in matches],
    )

    return {
        "status": "success",
        "query": cleaned_query,
        "collection": settings.CHROMA_COLLECTION_NAME,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "where": where,
        "matches": matches,
    }


def resolve_chunk_files(chunk_filename: str | None) -> list[Path]:
    chunk_dir = get_chunk_upload_dir()

    if chunk_filename:
        chunk_path = chunk_dir / Path(chunk_filename).name
        if not chunk_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk file was not found.",
            )
        return [chunk_path]

    chunk_files = sorted(path for path in chunk_dir.glob("*.json") if path.is_file())
    if not chunk_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chunk files found to index.",
        )

    return chunk_files


def load_chunk_payload(chunk_file: Path) -> dict[str, Any]:
    try:
        return json.loads(chunk_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunk JSON file: {chunk_file.name}",
        ) from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_chroma_client():
    db_dir = get_chroma_db_dir()
    db_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_dir))


def get_collection():
    return get_chroma_client().get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"embedding_model": settings.EMBEDDING_MODEL_NAME},
    )


def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    sanitized = {}

    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = json.dumps(value)

    return sanitized


def distance_to_similarity_score(distance: float) -> float:
    return round(1 / (1 + max(distance, 0)), 4)
