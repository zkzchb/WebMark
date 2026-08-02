import json
from datetime import datetime, timezone
from pathlib import Path

from webmark.archive import ingest_payload
from webmark.config import load_effective_config


def make_config(tmp_path: Path, *, publish: bool):
    settings = {
        "fetch": {"primary_tool": "WebFetch"},
        "storage": {
            "raw_root": str(tmp_path / "raw"),
            "file_naming_pattern": "{saved_date}-{title}-{id}.md",
            "filename_max_title_length": 20,
            "filename_safe_replacement": "-",
            "id_length": 10,
            "encoding": "utf-8",
        },
        "front_matter": {"cleanup": 0},
        "lexiang": {"enabled": False},
        "raw_publish": {
            "enabled": publish,
            "site_base_url": "https://raw.example.com" if publish else None,
        },
        "response": {"success_fields": []},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"source": {"mode": "inline"}, "settings": settings}), encoding="utf-8")
    return load_effective_config(path)


def test_ingest_uses_configured_storage_and_url(tmp_path: Path):
    config = make_config(tmp_path, publish=True)
    result = ingest_payload(
        {
            "source_url": "https://Example.com/a#fragment",
            "title": "测试：文章",
            "body_markdown": "# 正文\n\n内容。",
            "collection": "tech",
            "content_type": "article",
            "fetched_by": "workbuddy.WebFetch",
        },
        config=config,
        now=datetime(2026, 8, 2, 13, 0, tzinfo=timezone.utc),
    )
    text = Path(result.local_path).read_text(encoding="utf-8")
    assert "cleanup: 0" in text
    assert "source: https://example.com/a" in text
    assert result.raw_site_url == f"https://raw.example.com/tech/{result.document_id}"


def test_ingest_does_not_invent_raw_url_when_disabled(tmp_path: Path):
    config = make_config(tmp_path, publish=False)
    result = ingest_payload(
        {
            "source_url": "https://example.com/a",
            "title": "Title",
            "body_markdown": "Body",
            "collection": "inbox",
        },
        config=config,
    )
    assert result.raw_site_url is None
