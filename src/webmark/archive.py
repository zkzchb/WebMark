from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

import yaml

from .config import ConfigError, EffectiveConfig


class PayloadError(ValueError):
    """Raised when an Agent payload is incomplete or invalid."""


@dataclass(frozen=True)
class ArchiveResult:
    status: str
    local_path: str
    raw_site_url: str | None
    document_id: str
    collection: str
    source_url: str
    title: str

    def as_dict(self) -> dict[str, Any]:
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
    config: EffectiveConfig,
    now: datetime | None = None,
) -> ArchiveResult:
    settings = config.settings
    storage = _object(settings, "storage")
    front_matter = _object(settings, "front_matter", optional=True)
    raw_publish = _object(settings, "raw_publish", optional=True)

    source_url = _required_text(payload, "source_url")
    title = _required_text(payload, "title")
    body = _required_text(payload, "body_markdown")
    collection = _safe_segment(_required_text(payload, "collection"))
    content_type = str(payload.get("content_type") or "article")
    fetched_by = str(payload.get("fetched_by") or "agent")
    saved = now or datetime.now().astimezone()
    canonical_url = normalize_url(source_url)

    id_length = int(storage.get("id_length", 10))
    if id_length < 6 or id_length > 64:
        raise ConfigError("settings.storage.id_length must be between 6 and 64")
    document_id = str(payload.get("id") or stable_id(canonical_url, length=id_length))

    metadata: dict[str, Any] = {
        "id": document_id,
        "title": title,
        "cleanup": int(front_matter.get("cleanup", 0)),
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

    max_title = int(storage.get("filename_max_title_length", 80))
    replacement = str(storage.get("filename_safe_replacement", "-"))
    pattern = str(storage.get("file_naming_pattern", "{saved_date}-{title}-{id}.md"))
    safe_title = _safe_filename(title, limit=max_title, replacement=replacement)
    filename = _render_filename(
        pattern,
        saved_date=saved.date().isoformat(),
        title=safe_title,
        document_id=document_id,
        collection=collection,
    )

    raw_root = config.resolved_raw_root()
    directory = raw_root / collection
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    encoding = str(storage.get("encoding", "utf-8"))
    markdown = "---\n" + yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ) + "---\n\n" + body.strip() + "\n"
    path.write_text(markdown, encoding=encoding)

    raw_url: str | None = None
    if bool(raw_publish.get("enabled", False)):
        base = raw_publish.get("site_base_url")
        if not isinstance(base, str) or not base.startswith(("http://", "https://")):
            raise ConfigError("settings.raw_publish.site_base_url must be configured when enabled")
        raw_url = f"{base.rstrip('/')}/{collection}/{document_id}"

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


def stable_id(source_url: str, *, length: int = 10) -> str:
    return hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:length]


def read_payload(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PayloadError(f"Invalid payload JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PayloadError("payload JSON must be an object")
    return value


def _render_filename(
    pattern: str,
    *,
    saved_date: str,
    title: str,
    document_id: str,
    collection: str,
) -> str:
    allowed = {
        "saved_date": saved_date,
        "title": title,
        "id": document_id,
        "collection": collection,
    }
    try:
        filename = pattern.format(**allowed)
    except KeyError as exc:
        raise ConfigError(f"Unsupported file naming variable: {exc.args[0]}") from exc
    if not filename.lower().endswith(".md"):
        filename += ".md"
    return _safe_filename(filename, limit=180, replacement="-")


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadError(f"{key} is required")
    return value.strip()


def _safe_segment(value: str) -> str:
    result = re.sub(r"[^\w.-]+", "-", value, flags=re.UNICODE).strip("-._")
    if not result or result.lower() == "index":
        raise PayloadError("collection is invalid")
    return result


def _safe_filename(value: str, *, limit: int, replacement: str) -> str:
    replacement = replacement or "-"
    result = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', replacement, value).strip(" .-")
    result = re.sub(r"\s+", "", result)
    return (result or "untitled")[:limit]


def _object(settings: Mapping[str, Any], key: str, *, optional: bool = False) -> dict[str, Any]:
    value = settings.get(key)
    if value is None and optional:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"settings.{key} must be a JSON object")
    return value
