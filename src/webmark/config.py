from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_MANIFEST_URL = "https://config.fanqiemiao.com/mdFlow/v1/manifest.json"


class ConfigError(RuntimeError):
    """Raised when WebMark cannot load a usable configuration."""


@dataclass(frozen=True)
class RuntimeConfig:
    raw_root: Path
    manifest_cache: Path
    manifest_url: str = DEFAULT_MANIFEST_URL
    raw_site_base_url: str | None = None
    request_timeout_seconds: int = 30

    @classmethod
    def from_file(cls, path: str | Path) -> "RuntimeConfig":
        config_path = Path(path).expanduser().resolve()
        data = json.loads(config_path.read_text(encoding="utf-8"))
        base = config_path.parent

        def resolve(value: str) -> Path:
            candidate = Path(value).expanduser()
            return candidate if candidate.is_absolute() else (base / candidate).resolve()

        return cls(
            raw_root=resolve(data["raw_root"]),
            manifest_cache=resolve(data.get("manifest_cache", "mdflow/manifest.json")),
            manifest_url=data.get("manifest_url", DEFAULT_MANIFEST_URL),
            raw_site_base_url=data.get("raw_site_base_url"),
            request_timeout_seconds=int(data.get("request_timeout_seconds", 30)),
        )


def load_manifest(config: RuntimeConfig, *, initialize: bool = False, upgrade_url: str | None = None) -> dict[str, Any]:
    """Load mdFlow locally; access the network only when policy permits.

    Network access occurs only for initialization, a missing local cache, or an
    explicit upgrade URL. Ordinary runs read the local cache exclusively.
    """
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


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError(f"Invalid local mdFlow manifest at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError("Local mdFlow manifest must be a JSON object")
    return value
