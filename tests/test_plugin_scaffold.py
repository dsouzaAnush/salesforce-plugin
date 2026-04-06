from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_manifest_exists() -> None:
    manifest = ROOT / ".codex-plugin" / "plugin.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["name"] == "salesforce-plugin"
    assert data["skills"] == "./skills/"
    assert data["interface"]["composerIcon"] == "./assets/salesforce-logo.png"
    assert data["interface"]["logo"] == "./assets/salesforce-logo.png"
    assert (ROOT / "assets" / "salesforce-logo.png").is_file()


def test_synced_skills_have_expected_layout() -> None:
    skill_dirs = sorted(path for path in (ROOT / "skills").glob("sf-*") if path.is_dir())
    assert skill_dirs

    for skill_dir in skill_dirs:
        assert (skill_dir / "overlay.yaml").is_file()
        assert (skill_dir / "upstream" / "SKILL.md").is_file()
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "agents" / "openai.yaml").is_file()
        assert (skill_dir / "assets" / "salesforce-logo.png").is_file()


def test_generated_manifest_exists() -> None:
    manifest = ROOT / "generated" / "skill-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data
    assert all(item["name"].startswith("sf-") for item in data)
