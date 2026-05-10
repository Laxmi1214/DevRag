import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

from app.config.settings import settings
from app.services.active_source_service import set_active_source
from app.services.chunking_service import chunk_text_sources
from app.services.storage_service import get_url_upload_dir
from app.services.vector_service import insert_chunk_embeddings

REMOVABLE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "button",
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    ".nav",
    ".navbar",
    ".sidebar",
    ".breadcrumb",
    ".breadcrumbs",
    ".toc",
    ".table-of-contents",
    ".pagination",
    ".footer",
    ".header",
    ".menu",
]

CONTENT_SELECTORS = [
    "main",
    "article",
    "[role='main']",
    ".content",
    ".docs-content",
    ".documentation",
    ".markdown-body",
    ".prose",
]


async def process_url_ingestion(url: str) -> dict[str, object]:
    normalized_url = normalize_url(url)
    upload_id = uuid4().hex
    html = await fetch_webpage(normalized_url)
    metadata = extract_page_metadata(normalized_url, html)
    text = extract_readable_text(html)
    source_name = metadata["title"] or normalized_url

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable documentation content was found at this URL.",
        )

    stored_filename = store_crawl_metadata(metadata, text)
    chunk_result = chunk_text_sources(
        source_type="url",
        source_id=stored_filename,
        upload_id=upload_id,
        source_name=source_name,
        documents=[
            {
                "text": text,
                "metadata": {"url": normalized_url},
            }
        ],
        base_metadata={
            "url": normalized_url,
            "title": metadata["title"],
            "stored_filename": stored_filename,
            "source_name": source_name,
            "upload_id": upload_id,
        },
    )
    insert_chunk_embeddings(chunk_filename=chunk_result["stored_filename"])
    active_source = set_active_source(
        {
            "upload_id": upload_id,
            "source_type": "url",
            "source_name": source_name,
            "url": normalized_url,
            "chunk_filename": chunk_result["stored_filename"],
        }
    )
    preview = build_text_preview(text)

    return {
        "url": normalized_url,
        "upload_id": upload_id,
        "source_type": "url",
        "source_name": source_name,
        "active_source": active_source,
        "status": "success",
        "message": "Documentation URL crawled successfully.",
        "stored_filename": stored_filename,
        "title": metadata["title"],
        "preview": preview,
        "preview_characters": len(preview),
        "total_characters": len(text),
        "chunk_count": chunk_result["chunk_count"],
        "chunks_stored_filename": chunk_result["stored_filename"],
        "metadata": metadata,
    }


def normalize_url(url: str) -> str:
    candidate = url.strip()
    parsed = urlparse(candidate)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid http or https URL.",
        )

    return candidate


async def fetch_webpage(url: str) -> str:
    headers = {"User-Agent": settings.CRAWL_USER_AGENT}

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.CRAWL_TIMEOUT_SECONDS,
            headers=headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"URL returned HTTP {exc.response.status_code}.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch the provided URL.",
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided URL did not return an HTML page.",
        )

    return response.text


def extract_page_metadata(url: str, html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""

    return {
        "url": url,
        "title": title or url,
        "description": description,
        "crawled_at": datetime.now(UTC).isoformat(),
    }


def extract_readable_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for selector in REMOVABLE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    content_root = find_content_root(soup)
    text = content_root.get_text("\n", strip=True)
    return clean_text(text)


def find_content_root(soup: BeautifulSoup):
    for selector in CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if element:
            return element

    return soup.body or soup


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = []
    previous = ""

    for line in lines:
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized or normalized == previous:
            continue
        cleaned_lines.append(normalized)
        previous = normalized

    return "\n".join(cleaned_lines).strip()


def store_crawl_metadata(metadata: dict[str, str], text: str) -> str:
    upload_dir = get_url_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = build_crawl_filename(metadata["url"])
    destination = upload_dir / stored_filename
    payload = {
        "metadata": metadata,
        "content": text,
        "total_characters": len(text),
    }

    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return stored_filename


def build_crawl_filename(url: str) -> str:
    parsed = urlparse(url)
    host = re.sub(r"[^A-Za-z0-9_.-]+", "-", parsed.netloc).strip(".-") or "url"
    return f"{host}-{uuid4().hex}.json"


def build_text_preview(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[: settings.TEXT_PREVIEW_LIMIT]
