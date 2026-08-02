from datetime import datetime, timezone
from pathlib import Path

from webmark.archive import ingest_payload


def test_ingest_payload_writes_foldermark_markdown(tmp_path: Path):
    result = ingest_payload(
        {
            "source_url": "https://Example.com/a#fragment",
            "title": "测试：文章",
            "body_markdown": "# 正文\n\n内容。",
            "collection": "tech",
            "content_type": "article",
            "fetched_by": "workbuddy.WebFetch",
        },
        raw_root=tmp_path,
        raw_site_base_url="https://md.fanqiemiao.com/",
        now=datetime(2026, 8, 2, 13, 0, tzinfo=timezone.utc),
    )
    path = Path(result.local_path)
    text = path.read_text(encoding="utf-8")
    assert "cleanup: 0" in text
    assert "source: https://example.com/a" in text
    assert result.raw_site_url == f"https://md.fanqiemiao.com/tech/{result.document_id}"
