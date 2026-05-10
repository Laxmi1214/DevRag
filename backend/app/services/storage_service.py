from pathlib import Path

from app.config.settings import settings

BACKEND_DIR = Path(__file__).resolve().parents[2]


def resolve_backend_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path

    return BACKEND_DIR / path


def get_pdf_upload_dir() -> Path:
    return resolve_backend_path(settings.PDF_UPLOAD_DIR)


def get_image_upload_dir() -> Path:
    return resolve_backend_path(settings.IMAGE_UPLOAD_DIR)


def get_url_upload_dir() -> Path:
    return resolve_backend_path(settings.URL_UPLOAD_DIR)


def get_chunk_upload_dir() -> Path:
    return resolve_backend_path(settings.CHUNK_UPLOAD_DIR)


def get_chroma_db_dir() -> Path:
    return resolve_backend_path(settings.CHROMA_DB_DIR)
