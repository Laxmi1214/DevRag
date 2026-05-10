import logging
from typing import Any

from app.services.active_source_service import build_active_source_filter, get_active_source
from app.services.vector_service import query_vectors

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(question: str, limit: int | None = None) -> dict[str, Any]:
    active_source = get_active_source()
    where_filter = build_active_source_filter()

    logger.debug(
        "Active retrieval source upload_id=%s filter=%s",
        active_source.get("upload_id") if active_source else None,
        where_filter,
    )

    vector_results = query_vectors(question, limit, where=where_filter)
    source_names = [chunk.get("source_name") for chunk in vector_results["matches"]]
    logger.debug("Retrieved source names=%s", source_names)

    return {
        "status": "success",
        "question": vector_results["query"],
        "collection": vector_results["collection"],
        "embedding_model": vector_results["embedding_model"],
        "active_source": active_source,
        "metadata_filter": where_filter,
        "chunks": vector_results["matches"],
    }
