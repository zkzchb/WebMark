from pathlib import Path

import yaml

from webmark.config import load_effective_config


ROOT = Path(__file__).resolve().parents[1]


def test_public_config_template_is_valid_and_local_only():
    config = load_effective_config(ROOT / "config.json")
    assert config.settings["lexiang"]["enabled"] is False
    assert config.settings["raw_publish"]["enabled"] is False
    assert config.settings["response"]["success_fields"] == ["local_path"]


def test_skill_front_matter_is_minimal():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    _, front_matter, _ = text.split("---", 2)
    metadata = yaml.safe_load(front_matter)
    assert set(metadata) == {"name", "description"}
