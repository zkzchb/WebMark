import json
from pathlib import Path

import pytest

from webmark.config import ConfigError, load_effective_config


def base_settings(tmp_path: Path) -> dict:
    return {
        "fetch": {"primary_tool": "WebFetch"},
        "storage": {"raw_root": str(tmp_path / "raw")},
        "lexiang": {"enabled": False},
        "raw_publish": {"enabled": False},
        "response": {"success_fields": []},
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_inline_config(tmp_path: Path):
    path = tmp_path / "config.json"
    write_json(path, {"source": {"mode": "inline"}, "settings": base_settings(tmp_path), "overrides": {}})
    config = load_effective_config(path)
    assert config.source_mode == "inline"
    assert config.resolved_raw_root() == tmp_path / "raw"


def test_remote_config_and_override(tmp_path: Path, monkeypatch):
    remote = {"runtime": {"webmark": base_settings(tmp_path)}}
    remote["runtime"]["webmark"]["classification"] = {"article_min_characters": 500}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return remote

    monkeypatch.setattr("webmark.config.requests.get", lambda *args, **kwargs: Response())
    path = tmp_path / "config.json"
    write_json(
        path,
        {
            "source": {
                "mode": "remote",
                "url": "https://config.example.com/manifest.json",
                "cache_path": "cache.json",
                "selector": "runtime.webmark",
            },
            "settings": {},
            "overrides": {"classification": {"article_min_characters": 900}},
        },
    )
    config = load_effective_config(path, initialize=True)
    assert config.settings["classification"]["article_min_characters"] == 900
    assert (tmp_path / "cache.json").exists()


def test_daily_remote_run_uses_cache(tmp_path: Path, monkeypatch):
    cache = tmp_path / "cache.json"
    write_json(cache, {"runtime": {"webmark": base_settings(tmp_path)}})
    path = tmp_path / "config.json"
    write_json(
        path,
        {
            "source": {
                "mode": "remote",
                "url": "https://config.example.com/manifest.json",
                "cache_path": "cache.json",
                "selector": "runtime.webmark",
            },
            "settings": {},
            "overrides": {},
        },
    )

    def fail(*args, **kwargs):
        raise AssertionError("network must not be used")

    monkeypatch.setattr("webmark.config.requests.get", fail)
    config = load_effective_config(path)
    assert config.source_mode == "remote"


def test_secret_values_are_rejected(tmp_path: Path):
    settings = base_settings(tmp_path)
    settings["lexiang"] = {"enabled": False, "access_token": "secret"}
    path = tmp_path / "config.json"
    write_json(path, {"source": {"mode": "inline"}, "settings": settings, "overrides": {}})
    with pytest.raises(ConfigError, match="must not contain a secret"):
        load_effective_config(path)


def test_enabled_lexiang_requires_ids(tmp_path: Path):
    settings = base_settings(tmp_path)
    settings["lexiang"] = {"enabled": True}
    path = tmp_path / "config.json"
    write_json(path, {"source": {"mode": "inline"}, "settings": settings, "overrides": {}})
    with pytest.raises(ConfigError, match="settings.lexiang.mcp_server"):
        load_effective_config(path)
