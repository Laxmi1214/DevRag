from fastapi import APIRouter, File, UploadFile, status

from app.services.ocr_service import process_image_upload
from app.services.upload_service import process_pdf_upload
from app.services.url_ingestion_service import process_url_ingestion
from app.utils.schemas import UrlIngestionRequest

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/pdf", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)) -> dict:
    return await process_pdf_upload(file)


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)) -> dict:
    return await process_image_upload(file)


@router.post("/url", status_code=status.HTTP_201_CREATED)
async def upload_url(payload: UrlIngestionRequest) -> dict:
    return await process_url_ingestion(str(payload.url))
