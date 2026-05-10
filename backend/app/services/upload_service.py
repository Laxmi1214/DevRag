import re
from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import HTTPException, UploadFile, status

from app.config.settings import settings
from app.services.active_source_service import set_active_source
from app.services.chunking_service import chunk_text_sources
from app.services.storage_service import get_pdf_upload_dir
from app.services.vector_service import insert_chunk_embeddings

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


async def process_pdf_upload(file: UploadFile) -> dict[str, object]:
    validate_pdf_upload(file)

    upload_dir = get_pdf_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    upload_id = uuid4().hex
    safe_name = build_safe_filename(file.filename or "document.pdf")
    destination = upload_dir / safe_name
    source_name = file.filename or "document.pdf"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF is empty.",
            )

        destination.write_bytes(content)
        pages = extract_pdf_pages(destination)
        extracted_text = "\n\n".join(page["text"] for page in pages)
        chunk_result = chunk_text_sources(
            source_type="pdf",
            source_id=safe_name,
            upload_id=upload_id,
            source_name=source_name,
            documents=pages,
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
                "source_type": "pdf",
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
            detail="Failed to process uploaded PDF.",
        ) from exc
    finally:
        await file.close()

    preview = build_text_preview(extracted_text)

    return {
        "filename": source_name,
        "stored_filename": safe_name,
        "upload_id": upload_id,
        "source_type": "pdf",
        "source_name": source_name,
        "active_source": active_source,
        "status": "success",
        "message": "PDF uploaded and text extracted successfully.",
        "preview": preview,
        "preview_characters": len(preview),
        "total_characters": len(extracted_text),
        "chunk_count": chunk_result["chunk_count"],
        "chunks_stored_filename": chunk_result["stored_filename"],
    }


def validate_pdf_upload(file: UploadFile) -> None:
    filename = file.filename or ""
    content_type = file.content_type or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    if content_type and content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF.",
        )


def build_safe_filename(filename: str) -> str:
    path_name = Path(filename).name
    stem = Path(path_name).stem
    cleaned_stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip(".-") or "document"
    return f"{cleaned_stem}-{uuid4().hex}.pdf"


def extract_pdf_pages(pdf_path: Path) -> list[dict[str, object]]:
    try:
        with fitz.open(pdf_path) as document:
            pages = [
                {
                    "text": page.get_text("text").strip(),
                    "metadata": {"page_number": page_number},
                }
                for page_number, page in enumerate(document, start=1)
            ]
    except fitz.FileDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        ) from exc

    readable_pages = [page for page in pages if str(page["text"]).strip()]

    if not readable_pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No extractable text was found in the PDF.",
        )

    return readable_pages


def build_text_preview(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[: settings.TEXT_PREVIEW_LIMIT]
