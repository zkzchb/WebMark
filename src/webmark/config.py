from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_MANIFEST_URL = "https://config.fanqiemiao.com/mdFlow/v1/manifest.json"
DEFAULT_LEXIANG_PUBLIC_PAGE_BASE_URL = "https://lexiangla.com/pages"


class ConfigError(RuntimeError):
    """Raised when WebMark cannot load a usable configuration."""


@dataclass(frozen=True)
class LexiangTarget:
    team_id: str
    space_id: str
    root_entry_id: str
    public_page_base_url: str = DEFAULT_LEXIANG_PUBLIC_PAGE_BASE_URL

    def as_dict(self) -> dict[str, str]:
        return {
            "team_id": self.team_id,
            "space_id": self.space_id,
            "root_entry_id": self.root_entry_id,
            "public_page_base_url": self.public_page_base_url,
        }


@dataclass(frozen=True)
class RuntimeConfig:
    raw_root: Path
    manifest_cache: Path
    manifest_url: str = DEFAULT_MANIFEST_URL
    raw_site_base_url: str | None = None
    lexiang_team_id: str | None = None
    lexiang_space_id: str | None = None
    lexiang_root_entry_id: str | None = None
    lexiang_public_page_base_url: str | None = None
    request_timeout_seconds: int = 30

    @classmethod
    def from_file(cls, path: str | Path) -> "RuntimeConfig":
        config_path = Path(path).expanduser().resolve()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError(f"Invalid local config at {config_path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError("Local config must be a JSON object")

        base = config_path.parent
        lexiang = data.get("lexiang") or {}
        if not isinstance(lexiang, dict):
            raise ConfigError("Local lexiang configuration must be a JSON object")

        def resolve(value: str) -> Path:
            candidate = Path(value).expanduser()
            return candidate if candidate.is_absolute() else (base / candidate).resolve()

        return cls(
            raw_root=resolve(data["raw_root"]),
            manifest_cache=resolve(data.get("manifest_cache", "mdflow/manifest.json")),
            manifest_url=data.get("manifest_url", DEFAULT_MANIFEST_URL),
            raw_site_base_url=data.get("raw_site_base_url"),
            lexiang_team_id=lexiang.get("team_id"),
            lexiang_space_id=lexiang.get("space_id"),
            lexiang_root_entry_id=lexiang.get("root_entry_id"),
            lexiang_public_page_base_url=lexiang.get("public_page_base_url"),
            request_timeout_seconds=int(data.get("request_timeout_seconds", 30)),
        )


def load_manifest(
    config: RuntimeConfig,
    *,
    initialize: bool = False,
    upgrade_url: str | None = None,
) -> dict[str, Any]:
    """Load mdFlow locally and fetch only when the stated policy permits."""
    cache = config.manifest_cache
    should_fetch = initialize or upgrade_url is not None or not cache.exists()

    if should_fetch:
        url = upgrade_url or config.manifest_url
        try:
            response = requests.get(url, timeout=config.request_timeout_seconds)
            response.raise_for_status()
            manifest = response.json()
        except (requests.RequestException, ValueError) as exc:
            if cache.exists() and upgrade_url is None:
                return _read_manifest(cache)
            raise ConfigError(f"Unable to install mdFlow manifest from {url}: {exc}") from exc

        if not isinstance(manifest, dict):
            raise ConfigError("mdFlow manifest must be a JSON object")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return manifest

    return _read_manifest(cache)


def resolve_raw_site_base_url(config: RuntimeConfig, manifest: dict[str, Any]) -> str:
    """Resolve Raw endpoint from local override or mdFlow distribution."""
    value = config.raw_site_base_url or _webmark_runtime(manifest).get("raw_site_base_url")
    if not isinstance(value, str) or not value.startswith(("http://", "https://")):
        raise ConfigError(
            "Raw site base URL is missing. Set local raw_site_base_url or "
            "mdFlow runtime.webmark.raw_site_base_url."
        )
    return value.rstrip("/")


def resolve_lexiang_target(config: RuntimeConfig, manifest: dict[str, Any]) -> LexiangTarget:
    """Resolve non-secret Lexiang destination IDs from local overrides or mdFlow."""
    remote = _webmark_runtime(manifest).get("lexiang") or {}
    if not isinstance(remote, dict):
        raise ConfigError("mdFlow runtime.webmark.lexiang must be a JSON object")

    values = {
        "team_id": config.lexiang_team_id or remote.get("team_id"),
        "space_id": config.lexiang_space_id or remote.get("space_id"),
        "root_entry_id": config.lexiang_root_entry_id or remote.get("root_entry_id"),
        "public_page_base_url": (
            config.lexiang_public_page_base_url
            or remote.get("public_page_base_url")
            or DEFAULT_LEXIANG_PUBLIC_PAGE_BASE_URL
        ),
    }

    missing = [key for key in ("team_id", "space_id", "root_entry_id") if not _nonempty_text(values[key])]
    if missing:
        raise ConfigError(
            "Lexiang target is incomplete: "
            + ", ".join(missing)
            + ". Set local lexiang values or mdFlow runtime.webmark.lexiang."
        )
    public_base = values["public_page_base_url"]
    if not isinstance(public_base, str) or not public_base.startswith(("http://", "https://")):
        raise ConfigError("Lexiang public_page_base_url must be an HTTP or HTTPS URL")

    return LexiangTarget(
        team_id=str(values["team_id"]),
        space_id=str(values["space_id"]),
        root_entry_id=str(values["root_entry_id"]),
        public_page_base_url=public_base.rstrip("/"),
    )


def _webmark_runtime(manifest: dict[str, Any]) -> dict[str, Any]:
    runtime = manifest.get("runtime") or {}
    if not isinstance(runtime, dict):
        raise ConfigError("mdFlow runtime must be a JSON object")
    webmark = runtime.get("webmark") or {}
    if not isinstance(webmark, dict):
        raise ConfigError("mdFlow runtime.webmark must be a JSON object")
    return webmark


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError(f"Invalid local mdFlow manifest at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError("Local mdFlow manifest must be a JSON object")
    return value
