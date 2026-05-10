from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routes import health, rag, retrieval, upload, vectors


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(upload.router, prefix=settings.API_PREFIX)
    app.include_router(vectors.router, prefix=settings.API_PREFIX)
    app.include_router(retrieval.router, prefix=settings.API_PREFIX)
    app.include_router(rag.router, prefix=settings.API_PREFIX)
    app.include_router(upload.router, include_in_schema=False)
    app.include_router(vectors.router, include_in_schema=False)
    app.include_router(retrieval.router, include_in_schema=False)
    app.include_router(rag.router, include_in_schema=False)

    return app


app = create_app()
