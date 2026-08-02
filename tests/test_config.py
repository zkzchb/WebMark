from pathlib import Path

from webmark.config import RuntimeConfig, resolve_raw_site_base_url


def test_manifest_distributes_raw_site(tmp_path: Path):
    config = RuntimeConfig(raw_root=tmp_path, manifest_cache=Path("manifest.json"))
    manifest = {"runtime": {"webmark": {"raw_site_base_url": "https://md.fanqiemiao.com"}}}
    assert resolve_raw_site_base_url(config, manifest) == "https://md.fanqiemiao.com"


def test_local_raw_site_override_wins(tmp_path: Path):
    config = RuntimeConfig(
        raw_root=tmp_path,
        manifest_cache=Path("manifest.json"),
        raw_site_base_url="https://override.example/",
    )
    assert resolve_raw_site_base_url(config, {}) == "https://override.example"
