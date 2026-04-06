from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from scripts import build_skill_manifest as manifest_script
from scripts import build_skills as build_script
from scripts import skill_utils
from scripts import sync_upstream_skills as sync_script
from scripts import validate as validate_script


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_skill_utils_build_manifest_entry_and_scoring(tmp_path: Path) -> None:
    skill_dir = tmp_path / "sf-demo"
    write_file(
        skill_dir / "SKILL.md",
        """---
name: sf-demo
description: >
  Demo skill.
  TRIGGER when: user reviews Apex classes, touches .cls files, or checks help.salesforce.com.
  DO NOT TRIGGER when: Flow XML only.
---

# Demo
""",
    )
    write_file(
        skill_dir / "agents" / "openai.yaml",
        """interface:
  display_name: "Salesforce Demo"
  short_description: "Demo metadata"
  icon_small: "./assets/salesforce-logo.png"
  icon_large: "./assets/salesforce-logo.png"
  brand_color: "#0176D3"
  default_prompt: "Use $sf-demo for help with Salesforce Demo work."
""",
    )
    write_file(
        skill_dir / "overlay.yaml",
        """source:
  repo_path: "/tmp/upstream"
  skill: "sf-demo"
  sync_mode: "local-copy"

plugin:
  family: "salesforce"
  status: "synced"

routing:
  priority: "medium"
""",
    )

    entry = skill_utils.build_skill_manifest_entry(skill_dir)

    assert entry["name"] == "sf-demo"
    assert "apex classes" in entry["keywords"]
    assert ".cls" in entry["keywords"]
    assert "help.salesforce.com" in entry["keywords"]
    assert "flow xml only" in entry["negativeKeywords"]
    assert skill_utils.score_manifest_entry(entry, "Review these Apex classes in a .cls file") > 0
    assert skill_utils.score_manifest_entry(entry, "This is Flow XML only") < 0


def test_sync_helpers_prune_copy_and_report(tmp_path: Path, monkeypatch) -> None:
    upstream_root = tmp_path / "upstream"
    upstream_skill = upstream_root / "skills" / "sf-alpha"
    local_skills = tmp_path / "plugin-skills"
    generated_dir = tmp_path / "generated"

    write_file(upstream_skill / "SKILL.md", "---\nname: sf-alpha\ndescription: Demo\n---\n")
    write_file(upstream_skill / "agents" / "openai.yaml", "interface:\n  display_name: \"Alpha\"\n")
    write_file(local_skills / "sf-stale" / "SKILL.md", "stale\n")

    monkeypatch.setattr(sync_script, "SKILLS_DIR", local_skills)
    monkeypatch.setattr(sync_script, "GENERATED_DIR", generated_dir)

    discovered = sync_script.discover_upstream_skills(upstream_root)
    assert [path.name for path in discovered] == ["sf-alpha"]

    sync_script.remove_stale_skills({"sf-alpha"})
    assert not (local_skills / "sf-stale").exists()

    sync_script.sync_skill(discovered[0], upstream_root)
    assert (local_skills / "sf-alpha" / "upstream" / "SKILL.md").is_file()
    assert (local_skills / "sf-alpha" / "overlay.yaml").is_file()

    sync_script.write_sync_report(upstream_root, ["sf-alpha"])
    report = json.loads((generated_dir / "sync-report.json").read_text(encoding="utf-8"))
    assert report["skillCount"] == 1
    assert report["skills"] == ["sf-alpha"]


def test_build_helpers_copy_outputs_and_detect_staleness(tmp_path: Path, monkeypatch) -> None:
    skills_dir = tmp_path / "skills"
    upstream_dir = skills_dir / "sf-alpha" / "upstream"

    write_file(upstream_dir / "SKILL.md", "---\nname: sf-alpha\ndescription: Demo\n---\n")
    write_file(upstream_dir / "agents" / "openai.yaml", "interface:\n  display_name: \"Alpha\"\n")
    write_file(upstream_dir / "assets" / "example.txt", "alpha\n")

    monkeypatch.setattr(build_script, "SKILLS_DIR", skills_dir)

    assert build_script.build_skills() == 1
    assert (skills_dir / "sf-alpha" / "SKILL.md").is_file()
    assert (skills_dir / "sf-alpha" / "agents" / "openai.yaml").is_file()
    assert build_script.check_build_outputs() == []

    write_file(skills_dir / "sf-alpha" / "SKILL.md", "stale\n")
    errors = build_script.check_build_outputs()
    assert errors
    assert "stale" in errors[0].lower()


def test_manifest_builder_write_and_check(tmp_path: Path, monkeypatch) -> None:
    output_file = tmp_path / "skill-manifest.json"
    monkeypatch.setattr(manifest_script, "GENERATED_DIR", tmp_path)
    monkeypatch.setattr(manifest_script, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(
        manifest_script,
        "build_skill_manifest",
        lambda: [{"name": "sf-alpha", "path": "./skills/sf-alpha"}],
    )

    missing_errors = manifest_script.check_manifest_is_current()
    assert missing_errors
    assert "missing" in missing_errors[0].lower()

    manifest_script.write_manifest()
    assert output_file.is_file()
    assert manifest_script.check_manifest_is_current() == []

    output_file.write_text("[]\n", encoding="utf-8")
    errors = manifest_script.check_manifest_is_current()
    assert errors
    assert "stale" in errors[0].lower()


def test_manifest_main_raises_when_check_fails(monkeypatch) -> None:
    monkeypatch.setattr(manifest_script, "check_manifest_is_current", lambda: ["manifest stale"])
    monkeypatch.setattr(sys, "argv", ["build_skill_manifest.py", "--check"])

    with pytest.raises(SystemExit):
        manifest_script.main()


def test_validate_collects_errors_for_broken_state(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    plugin_manifest = root / ".codex-plugin" / "plugin.json"
    marketplace = root / ".agents" / "plugins" / "marketplace.json"
    root_agent = root / "agents" / "openai.yaml"
    sync_report = root / "generated" / "sync-report.json"

    write_file(
        plugin_manifest,
        json.dumps(
            {
                "name": "salesforce-plugin",
                "skills": "./skills/",
                "interface": {
                    "composerIcon": "./assets/missing.png",
                    "logo": "./assets/missing.png",
                },
            }
        ),
    )
    write_file(
        marketplace,
        json.dumps(
            {
                "plugins": [
                    {
                        "name": "salesforce-plugin",
                        "source": {"path": "./wrong"},
                    }
                ]
            }
        ),
    )
    write_file(
        root_agent,
        """interface:
  display_name: "Salesforce Plugin"
  icon_small: "./assets/missing.png"
  icon_large: "./assets/missing.png"
""",
    )
    write_file(sync_report, json.dumps({"skillCount": 0, "skills": []}))

    monkeypatch.setattr(validate_script, "ROOT", root)
    monkeypatch.setattr(validate_script, "PLUGIN_MANIFEST", plugin_manifest)
    monkeypatch.setattr(validate_script, "MARKETPLACE", marketplace)
    monkeypatch.setattr(validate_script, "ROOT_AGENT_METADATA", root_agent)
    monkeypatch.setattr(validate_script, "SYNC_REPORT", sync_report)
    monkeypatch.setattr(
        validate_script,
        "build_skill_manifest",
        lambda: [{"name": "sf-alpha", "path": "./skills/sf-alpha"}],
    )
    monkeypatch.setattr(validate_script, "check_build_outputs", lambda: ["build stale"])
    monkeypatch.setattr(validate_script, "check_manifest_is_current", lambda: ["manifest stale"])

    errors = validate_script.collect_validation_errors()

    assert any("missing" in error.lower() for error in errors)
    assert any("stale" in error.lower() for error in errors)


def test_build_compare_paths_reports_missing_and_extra(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"

    write_file(source / "only-in-source.txt", "alpha\n")
    write_file(source / "shared.txt", "alpha\n")
    write_file(destination / "shared.txt", "alpha\n")
    write_file(destination / "only-in-destination.txt", "beta\n")

    errors = build_script.compare_paths(source, destination)

    assert any("missing built entries" in error.lower() for error in errors)
    assert any("unexpected built entries" in error.lower() for error in errors)
    assert build_script.compare_paths(source / "shared.txt", destination / "missing.txt")


def test_build_main_raises_when_check_fails(monkeypatch) -> None:
    monkeypatch.setattr(build_script, "check_build_outputs", lambda: ["build stale"])
    monkeypatch.setattr(sys, "argv", ["build_skills.py", "--check"])

    with pytest.raises(SystemExit):
        build_script.main()


def test_validate_main_raises_when_errors_exist(monkeypatch) -> None:
    monkeypatch.setattr(validate_script, "collect_validation_errors", lambda: ["bad state"])
    monkeypatch.setattr(sys, "argv", ["validate.py"])

    with pytest.raises(SystemExit):
        validate_script.main()


def test_build_and_validate_cli_mains(tmp_path: Path, monkeypatch) -> None:
    output_file = tmp_path / "skill-manifest.json"
    monkeypatch.setattr(manifest_script, "GENERATED_DIR", tmp_path)
    monkeypatch.setattr(manifest_script, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(
        manifest_script,
        "build_skill_manifest",
        lambda: [{"name": "sf-alpha", "path": "./skills/sf-alpha"}],
    )
    monkeypatch.setattr(sys, "argv", ["build_skill_manifest.py"])
    manifest_script.main()
    assert output_file.exists()

    monkeypatch.setattr(sys, "argv", ["build_skill_manifest.py", "--check"])
    manifest_script.main()

    monkeypatch.setattr(build_script, "check_build_outputs", lambda: [])
    monkeypatch.setattr(build_script, "build_skills", lambda: 2)
    monkeypatch.setattr(sys, "argv", ["build_skills.py", "--check"])
    build_script.main()
    monkeypatch.setattr(sys, "argv", ["build_skills.py"])
    build_script.main()

    monkeypatch.setattr(validate_script, "collect_validation_errors", lambda: [])
    monkeypatch.setattr(sys, "argv", ["validate.py"])
    validate_script.main()


def test_sync_main_copies_expected_skills(tmp_path: Path, monkeypatch) -> None:
    upstream_root = tmp_path / "upstream"
    upstream_skill = upstream_root / "skills" / "sf-alpha"
    local_skills = tmp_path / "plugin-skills"
    generated_dir = tmp_path / "generated"

    write_file(upstream_skill / "SKILL.md", "---\nname: sf-alpha\ndescription: Demo\n---\n")
    write_file(upstream_skill / "agents" / "openai.yaml", "interface:\n  display_name: \"Alpha\"\n")

    monkeypatch.setattr(sync_script, "SKILLS_DIR", local_skills)
    monkeypatch.setattr(sync_script, "GENERATED_DIR", generated_dir)
    monkeypatch.setattr(sys, "argv", ["sync_upstream_skills.py", "--upstream", str(upstream_root)])

    sync_script.main()

    assert (local_skills / "sf-alpha" / "upstream" / "SKILL.md").is_file()
    assert (generated_dir / "sync-report.json").is_file()
