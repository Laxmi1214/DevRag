import re
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config.settings import settings
from app.services.active_source_service import set_active_source
from app.services.chunking_service import chunk_text_sources
from app.services.storage_service import get_image_upload_dir
from app.services.vector_service import insert_chunk_embeddings

IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


async def process_image_upload(file: UploadFile) -> dict[str, object]:
    validate_image_upload(file)

    upload_dir = get_image_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    upload_id = uuid4().hex
    safe_name = build_safe_image_filename(file.filename or "image.png")
    destination = upload_dir / safe_name
    source_name = file.filename or "image.png"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image is empty.",
            )

        destination.write_bytes(content)
        extracted_text = extract_image_text(destination)
        chunk_result = chunk_text_sources(
            source_type="image",
            source_id=safe_name,
            upload_id=upload_id,
            source_name=source_name,
            documents=[
                {
                    "text": extracted_text,
                    "metadata": {"filename": source_name},
                }
            ],
            base_metadata={
                "filename": source_name,
                "stored_filename": safe_name,
                "source_name": source_name,
                "upload_id": upload_id,
            },
        )
        insert_chunk_embeddings(chunk_filename=chunk_result["stored_filename"])
        active_source = set_active_source(
            {
                "upload_id": upload_id,
                "source_type": "image",
                "source_name": source_name,
                "filename": source_name,
                "chunk_filename": chunk_result["stored_filename"],
            }
        )
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded image.",
        ) from exc
    finally:
        await file.close()

    preview = build_text_preview(extracted_text)

    return {
        "filename": source_name,
        "stored_filename": safe_name,
        "upload_id": upload_id,
        "source_type": "image",
        "source_name": source_name,
        "active_source": active_source,
        "status": "success",
        "message": "Image uploaded and OCR text extracted successfully.",
        "text": extracted_text,
        "preview": preview,
        "preview_characters": len(preview),
        "total_characters": len(extracted_text),
        "chunk_count": chunk_result["chunk_count"],
        "chunks_stored_filename": chunk_result["stored_filename"],
    }


def validate_image_upload(file: UploadFile) -> None:
    filename = file.filename or ""
    content_type = file.content_type or ""
    extension = Path(filename).suffix.lower()

    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PNG and JPG image files are supported.",
        )

    if content_type and content_type not in IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PNG or JPG image.",
        )


def build_safe_image_filename(filename: str) -> str:
    path_name = Path(filename).name
    extension = Path(path_name).suffix.lower()
    stem = Path(path_name).stem
    cleaned_stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip(".-") or "image"

    if extension == ".jpeg":
        extension = ".jpg"

    return f"{cleaned_stem}-{uuid4().hex}{extension}"


def extract_image_text(image_path: Path) -> str:
    reader = get_ocr_reader()
    results = reader.readtext(str(image_path), detail=0, paragraph=True)
    text = "\n".join(item.strip() for item in results if item and item.strip())

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found in the image.",
        )

    return text


@lru_cache(maxsize=1)
def get_ocr_reader():
    try:
        ensure_bidi_easyocr_compatibility()
        import easyocr
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="EasyOCR is not installed. Run pip install -r requirements.txt.",
        ) from exc

    return easyocr.Reader(settings.OCR_LANGUAGES)


def ensure_bidi_easyocr_compatibility() -> None:
    try:
        import bidi
        from bidi.algorithm import get_display
    except ImportError:
        return

    if not hasattr(bidi, "get_display"):
        bidi.get_display = get_display


def build_text_preview(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[: settings.TEXT_PREVIEW_LIMIT]
