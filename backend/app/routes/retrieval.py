from fastapi import APIRouter

from app.services.retrieval_service import retrieve_relevant_chunks
from app.utils.schemas import SemanticRetrievalRequest

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/semantic")
async def semantic_retrieval(payload: SemanticRetrievalRequest) -> dict:
    return retrieve_relevant_chunks(question=payload.question, limit=payload.limit)
