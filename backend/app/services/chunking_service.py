import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.services.storage_service import get_chunk_upload_dir


def chunk_text_sources(
    *,
    source_type: str,
    source_id: str,
    upload_id: str,
    source_name: str,
    documents: list[dict[str, Any]],
    base_metadata: dict[str, Any],
) -> dict[str, Any]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []

    for document in documents:
        text = document.get("text", "")
        if not text.strip():
            continue

        document_metadata = {
            **base_metadata,
            **document.get("metadata", {}),
            "source_type": source_type,
            "source_id": source_id,
            "source_name": source_name,
            "upload_id": upload_id,
        }

        for chunk_text in splitter.split_text(text):
            chunk_index = len(chunks)
            chunks.append(
                {
                    "id": f"{source_type}-{uuid4().hex}",
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "character_count": len(chunk_text),
                    "metadata": document_metadata,
                }
            )

    stored_filename = store_chunks(
        source_type,
        source_id,
        upload_id,
        source_name,
        chunks,
        base_metadata,
    )

    return {
        "stored_filename": stored_filename,
        "chunk_count": len(chunks),
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
    }


def store_chunks(
    source_type: str,
    source_id: str,
    upload_id: str,
    source_name: str,
    chunks: list[dict[str, Any]],
    base_metadata: dict[str, Any],
) -> str:
    upload_dir = get_chunk_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = build_chunk_filename(source_type, source_id)
    destination = upload_dir / stored_filename
    payload = {
        "source_type": source_type,
        "source_id": source_id,
        "source_name": source_name,
        "upload_id": upload_id,
        "metadata": base_metadata,
        "chunk_count": len(chunks),
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "created_at": datetime.now(UTC).isoformat(),
        "chunks": chunks,
    }

    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return stored_filename


def build_chunk_filename(source_type: str, source_id: str) -> str:
    stem = Path(source_id).stem if source_id else source_type
    cleaned_stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip(".-") or source_type
    return f"{source_type}-{cleaned_stem}-{uuid4().hex}.json"
