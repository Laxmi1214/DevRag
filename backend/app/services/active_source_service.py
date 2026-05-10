import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.storage_service import resolve_backend_path

ACTIVE_SOURCE_STATE_FILE = "uploads/active_source.json"


def set_active_source(source: dict[str, Any]) -> dict[str, Any]:
    active_source = {
        "upload_id": source["upload_id"],
        "source_type": source["source_type"],
        "source_name": source["source_name"],
        "filename": source.get("filename"),
        "url": source.get("url"),
        "chunk_filename": source.get("chunk_filename"),
        "activated_at": datetime.now(UTC).isoformat(),
    }

    state_path = get_active_source_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(active_source, indent=2), encoding="utf-8")
    return active_source


def get_active_source() -> dict[str, Any] | None:
    state_path = get_active_source_state_path()

    if not state_path.exists():
        return None

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_active_source_filter() -> dict[str, str] | None:
    active_source = get_active_source()

    if not active_source or not active_source.get("upload_id"):
        return None

    return {"upload_id": active_source["upload_id"]}


def get_active_source_state_path() -> Path:
    return resolve_backend_path(ACTIVE_SOURCE_STATE_FILE)
