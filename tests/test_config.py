from pathlib import Path

from webmark.config import (
    RuntimeConfig,
    resolve_lexiang_target,
    resolve_raw_site_base_url,
)


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


def test_manifest_distributes_lexiang_target(tmp_path: Path):
    config = RuntimeConfig(raw_root=tmp_path, manifest_cache=Path("manifest.json"))
    manifest = {
        "runtime": {
            "webmark": {
                "lexiang": {
                    "team_id": "team",
                    "space_id": "space",
                    "root_entry_id": "root",
                    "public_page_base_url": "https://lexiangla.com/pages/",
                }
            }
        }
    }
    target = resolve_lexiang_target(config, manifest)
    assert target.team_id == "team"
    assert target.space_id == "space"
    assert target.root_entry_id == "root"
    assert target.public_page_base_url == "https://lexiangla.com/pages"


def test_local_lexiang_override_wins(tmp_path: Path):
    config = RuntimeConfig(
        raw_root=tmp_path,
        manifest_cache=Path("manifest.json"),
        lexiang_team_id="local-team",
        lexiang_space_id="local-space",
        lexiang_root_entry_id="local-root",
    )
    manifest = {
        "runtime": {
            "webmark": {
                "lexiang": {
                    "team_id": "remote-team",
                    "space_id": "remote-space",
                    "root_entry_id": "remote-root",
                }
            }
        }
    }
    target = resolve_lexiang_target(config, manifest)
    assert target.team_id == "local-team"
    assert target.space_id == "local-space"
    assert target.root_entry_id == "local-root"
