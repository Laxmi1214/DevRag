from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "DevRag"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    UPLOAD_DIR: str = "uploads"
    PDF_UPLOAD_DIR: str = "uploads/pdfs"
    IMAGE_UPLOAD_DIR: str = "uploads/images"
    URL_UPLOAD_DIR: str = "uploads/urls"
    TEXT_PREVIEW_LIMIT: int = 1200
    CHUNK_UPLOAD_DIR: str = "uploads/chunks"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHROMA_DB_DIR: str = "C:/tmp/devrag-chroma"
    CHROMA_COLLECTION_NAME: str = "devrag_chunks"
    VECTOR_QUERY_LIMIT: int = 5
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.2
    OCR_LANGUAGES: list[str] = ["en"]
    CRAWL_TIMEOUT_SECONDS: float = 15.0
    CRAWL_USER_AGENT: str = "DevRagBot/0.1"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
