from fastapi import APIRouter

from app.services.rag_service import generate_grounded_answer
from app.utils.schemas import RagGenerationRequest

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/answer")
async def generate_answer(payload: RagGenerationRequest) -> dict:
    return generate_grounded_answer(question=payload.question, limit=payload.limit)
