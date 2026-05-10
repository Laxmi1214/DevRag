from pydantic import BaseModel, HttpUrl


class UrlIngestionRequest(BaseModel):
    url: HttpUrl


class VectorInsertRequest(BaseModel):
    chunk_filename: str | None = None
    reindex: bool = True


class VectorQueryRequest(BaseModel):
    query: str
    limit: int | None = None


class SemanticRetrievalRequest(BaseModel):
    question: str
    limit: int | None = None


class RagGenerationRequest(BaseModel):
    question: str
    limit: int | None = None
