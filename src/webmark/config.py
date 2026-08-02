from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import requests


class ConfigError(RuntimeError):
    """Raised when WebMark cannot load or validate its configuration."""


SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "app_secret",
    "password",
    "private_key",
    "secret",
    "sync_key",
    "token",
}


@dataclass(frozen=True)
class EffectiveConfig:
    settings: dict[str, Any]
    config_path: Path
    source_mode: str
    cache_path: Path | None = None

    @property
    def base_dir(self) -> Path:
        return self.config_path.parent

    def section(self, name: str) -> dict[str, Any]:
        value = self.settings.get(name) or {}
        if not isinstance(value, dict):
            raise ConfigError(f"settings.{name} must be a JSON object")
        return value

    def resolved_raw_root(self) -> Path:
        storage = self.section("storage")
        value = storage.get("raw_root")
        if not isinstance(value, str) or not value.strip():
            raise ConfigError("settings.storage.raw_root is required")
        return resolve_path(value, self.base_dir)

    def agent_view(self) -> dict[str, Any]:
        result = deepcopy(self.settings)
        result.setdefault("storage", {})["raw_root"] = str(self.resolved_raw_root())
        return result


def load_effective_config(
    path: str | Path,
    *,
    initialize: bool = False,
    upgrade_url: str | None = None,
) -> EffectiveConfig:
    config_path = Path(path).expanduser().resolve()
    local = _read_json_object(config_path, label="WebMark config")

    source = local.get("source") or {"mode": "inline"}
    if not isinstance(source, dict):
        raise ConfigError("source must be a JSON object")
    mode = str(source.get("mode") or "inline").strip().lower()

    if mode == "inline":
        settings = local.get("settings")
        if not isinstance(settings, dict):
            raise ConfigError("settings must be a JSON object in inline mode")
        effective = deepcopy(settings)
        cache_path = None
    elif mode == "remote":
        url = upgrade_url or source.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ConfigError("source.url must be an HTTP or HTTPS URL in remote mode")
        cache_value = source.get("cache_path")
        if not isinstance(cache_value, str) or not cache_value.strip():
            raise ConfigError("source.cache_path is required in remote mode")
        cache_path = resolve_path(cache_value, config_path.parent)
        timeout = int(source.get("request_timeout_seconds", 30))
        document = _load_remote_document(
            url,
            cache_path,
            timeout=timeout,
            initialize=initialize,
            explicit_upgrade=upgrade_url is not None,
        )
        selector = str(source.get("selector") or "runtime.webmark")
        effective = deepcopy(_select_object(document, selector))
    else:
        raise ConfigError("source.mode must be 'inline' or 'remote'")

    overrides = local.get("overrides") or {}
    if not isinstance(overrides, dict):
        raise ConfigError("overrides must be a JSON object")
    effective = deep_merge(effective, overrides)

    _reject_embedded_secrets(effective)
    validate_settings(effective)
    return EffectiveConfig(
        settings=effective,
        config_path=config_path,
        source_mode=mode,
        cache_path=cache_path,
    )


def validate_settings(settings: Mapping[str, Any]) -> None:
    storage = _required_object(settings, "storage")
    _required_text(storage, "raw_root", "settings.storage.raw_root")

    fetch = _required_object(settings, "fetch")
    _required_text(fetch, "primary_tool", "settings.fetch.primary_tool")

    lexiang = _optional_object(settings, "lexiang")
    if bool(lexiang.get("enabled", False)):
        for key in ("mcp_server", "import_tool", "team_id", "space_id", "root_entry_id"):
            _required_text(lexiang, key, f"settings.lexiang.{key}")
        _required_http_url(
            lexiang.get("public_page_base_url"),
            "settings.lexiang.public_page_base_url",
        )

    raw_publish = _optional_object(settings, "raw_publish")
    if bool(raw_publish.get("enabled", False)):
        _required_http_url(raw_publish.get("site_base_url"), "settings.raw_publish.site_base_url")
        sync = _optional_object(raw_publish, "sync")
        if bool(sync.get("enabled", False)):
            _required_text(sync, "adapter", "settings.raw_publish.sync.adapter")

    response = _optional_object(settings, "response")
    success_fields = response.get("success_fields", [])
    if not isinstance(success_fields, list) or not all(isinstance(item, str) for item in success_fields):
        raise ConfigError("settings.response.success_fields must be an array of strings")


def integration_targets(settings: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "lexiang": deepcopy(_optional_object(settings, "lexiang")),
        "raw_publish": deepcopy(_optional_object(settings, "raw_publish")),
    }


def resolve_path(value: str, base_dir: Path) -> Path:
    expanded = os.path.expandvars(value)
    candidate = Path(expanded).expanduser()
    return candidate if candidate.is_absolute() else (base_dir / candidate).resolve()


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _load_remote_document(
    url: str,
    cache_path: Path,
    *,
    timeout: int,
    initialize: bool,
    explicit_upgrade: bool,
) -> dict[str, Any]:
    should_fetch = initialize or explicit_upgrade or not cache_path.exists()
    if not should_fetch:
        try:
            return _read_json_object(cache_path, label="cached remote config")
        except ConfigError:
            should_fetch = True

    if should_fetch:
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            document = response.json()
        except (requests.RequestException, ValueError) as exc:
            if cache_path.exists() and not explicit_upgrade:
                try:
                    return _read_json_object(cache_path, label="cached remote config")
                except ConfigError:
                    pass
            raise ConfigError(f"Unable to load remote config from {url}: {exc}") from exc
        if not isinstance(document, dict):
            raise ConfigError("Remote config must be a JSON object")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return document

    raise ConfigError("Unable to resolve remote configuration")


def _select_object(document: Mapping[str, Any], selector: str) -> dict[str, Any]:
    value: Any = document
    for part in [item for item in selector.split(".") if item]:
        if not isinstance(value, Mapping) or part not in value:
            raise ConfigError(f"Remote config selector not found: {selector}")
        value = value[part]
    if not isinstance(value, dict):
        raise ConfigError(f"Remote config selector must resolve to a JSON object: {selector}")
    return value


def _reject_embedded_secrets(value: Any, path: str = "settings") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in SENSITIVE_KEYS and child not in (None, ""):
                raise ConfigError(
                    f"{path}.{key_text} must not contain a secret. "
                    "Use WorkBuddy MCP/credential storage and keep only a credential_ref in JSON."
                )
            _reject_embedded_secrets(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_embedded_secrets(child, f"{path}[{index}]")


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError(f"Invalid {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a JSON object")
    return value


def _required_object(settings: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = settings.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"settings.{key} must be a JSON object")
    return value


def _optional_object(settings: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = settings.get(key) or {}
    if not isinstance(value, dict):
        raise ConfigError(f"settings.{key} must be a JSON object")
    return value


def _required_text(container: Mapping[str, Any], key: str, label: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} is required")
    return value.strip()


def _required_http_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith(("http://", "https://")):
        raise ConfigError(f"{label} must be an HTTP or HTTPS URL")
    return value.rstrip("/")
