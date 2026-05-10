from fastapi import APIRouter, status

from app.services.active_source_service import build_active_source_filter
from app.services.vector_service import (
    insert_chunk_embeddings,
    list_available_chunk_files,
    query_vectors,
    reset_vector_collection,
)
from app.utils.schemas import VectorInsertRequest, VectorQueryRequest

router = APIRouter(prefix="/vectors", tags=["vectors"])


@router.post("/insert", status_code=status.HTTP_201_CREATED)
async def insert_vectors(payload: VectorInsertRequest) -> dict:
    return insert_chunk_embeddings(
        chunk_filename=payload.chunk_filename,
        reindex=payload.reindex,
    )


@router.get("/chunks")
async def list_chunks() -> dict:
    return list_available_chunk_files()


@router.post("/reset")
async def reset_vectors() -> dict:
    return reset_vector_collection()


@router.post("/query")
async def retrieve_vectors(payload: VectorQueryRequest) -> dict:
    return query_vectors(
        query=payload.query,
        limit=payload.limit,
        where=build_active_source_filter(),
    )
