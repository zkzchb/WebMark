from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml


class PayloadError(ValueError):
    """Raised when an Agent payload is incomplete or invalid."""


@dataclass(frozen=True)
class ArchiveResult:
    status: str
    local_path: str
    raw_site_url: str
    document_id: str
    collection: str
    source_url: str
    title: str

    def as_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "local_path": self.local_path,
            "raw_site_url": self.raw_site_url,
            "document_id": self.document_id,
            "collection": self.collection,
            "source_url": self.source_url,
            "title": self.title,
        }


def ingest_payload(
    payload: dict[str, Any],
    *,
    raw_root: Path,
    raw_site_base_url: str,
    now: datetime | None = None,
) -> ArchiveResult:
    source_url = _required_text(payload, "source_url")
    title = _required_text(payload, "title")
    body = _required_text(payload, "body_markdown")
    collection = _safe_segment(_required_text(payload, "collection"))
    content_type = str(payload.get("content_type") or "article")
    fetched_by = str(payload.get("fetched_by") or "workbuddy")
    saved = now or datetime.now().astimezone()
    canonical_url = normalize_url(source_url)
    document_id = str(payload.get("id") or stable_id(canonical_url))

    metadata: dict[str, Any] = {
        "id": document_id,
        "title": title,
        "cleanup": 0,
        "saved": saved.isoformat(timespec="seconds"),
        "source": canonical_url,
        "collection": collection,
        "content_type": content_type,
        "fetched_by": fetched_by,
    }
    for key in ("author", "published", "summary", "tags", "source_channel"):
        value = payload.get(key)
        if value not in (None, "", []):
            metadata[key] = value

    filename = f"{saved.date().isoformat()}-{_safe_filename(title)}-{document_id}.md"
    directory = raw_root / collection
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    markdown = "---\n" + yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ) + "---\n\n" + body.strip() + "\n"
    path.write_text(markdown, encoding="utf-8")

    raw_url = f"{raw_site_base_url.rstrip('/')}/{collection}/{document_id}"
    return ArchiveResult(
        status="success",
        local_path=str(path),
        raw_site_url=raw_url,
        document_id=document_id,
        collection=collection,
        source_url=canonical_url,
        title=title,
    )


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise PayloadError("source_url must be an HTTP or HTTPS URL")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def stable_id(source_url: str) -> str:
    return hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:10]


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadError(f"{key} is required")
    return value.strip()


def _safe_segment(value: str) -> str:
    result = re.sub(r"[^\w.-]+", "-", value, flags=re.UNICODE).strip("-._")
    if not result or result.lower() == "index":
        raise PayloadError("collection is invalid")
    return result


def _safe_filename(value: str, limit: int = 80) -> str:
    result = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value).strip(" .-")
    result = re.sub(r"\s+", "", result)
    return (result or "untitled")[:limit]


def read_payload(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PayloadError("payload JSON must be an object")
    return value
