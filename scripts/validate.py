#!/usr/bin/env python3
"""Validate plugin structure, generated artifacts, and synced skills."""

from __future__ import annotations

import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.build_skill_manifest import check_manifest_is_current
    from scripts.build_skills import check_build_outputs
    from scripts.skill_utils import build_skill_manifest, parse_openai_yaml
else:
    from .build_skill_manifest import check_manifest_is_current
    from .build_skills import check_build_outputs
    from .skill_utils import build_skill_manifest, parse_openai_yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
OPENCLAW_BUNDLE_MANIFEST = ROOT / "openclaw.bundle.json"
PACKAGE_JSON = ROOT / "package.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
ROOT_AGENT_METADATA = ROOT / "agents" / "openai.yaml"
SYNC_REPORT = ROOT / "generated" / "sync-report.json"


def validate_plugin_manifest() -> list[str]:
    errors: list[str] = []
    manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    if manifest.get("name") != "salesforce-plugin":
        errors.append("Plugin manifest name must be salesforce-plugin")
    if manifest.get("skills") != "./skills/":
        errors.append("Plugin manifest must point skills at ./skills/")

    interface = manifest.get("interface", {})
    for field in ("composerIcon", "logo"):
        asset = interface.get(field)
        if not asset:
            errors.append(f"Plugin manifest is missing interface.{field}")
            continue
        asset_path = ROOT / asset.removeprefix("./")
        if not asset_path.is_file():
            errors.append(f"Plugin manifest asset is missing: {asset_path}")

    return errors


def validate_openclaw_bundle_metadata() -> list[str]:
    errors: list[str] = []
    if not OPENCLAW_BUNDLE_MANIFEST.is_file():
        return [f"Missing OpenClaw bundle manifest: {OPENCLAW_BUNDLE_MANIFEST}"]
    if not PACKAGE_JSON.is_file():
        return [f"Missing package.json: {PACKAGE_JSON}"]

    bundle_manifest = json.loads(OPENCLAW_BUNDLE_MANIFEST.read_text(encoding="utf-8"))
    package_manifest = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    if package_manifest.get("name") != "openclaw-salesforce-plugin":
        errors.append("package.json name must be openclaw-salesforce-plugin")
    if bundle_manifest.get("format") != "codex":
        errors.append("openclaw.bundle.json format must be codex")
    if bundle_manifest.get("hostTargets") != ["codex"]:
        errors.append('openclaw.bundle.json hostTargets must be ["codex"]')
    return errors


def validate_marketplace() -> list[str]:
    errors: list[str] = []
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    plugins = marketplace.get("plugins", [])
    if not plugins:
        return ["Marketplace must contain at least one plugin entry"]

    plugin_entry = plugins[0]
    if plugin_entry.get("name") != "salesforce-plugin":
        errors.append("Marketplace first plugin entry must be salesforce-plugin")
    plugin_root = (MARKETPLACE.parent / plugin_entry["source"]["path"]).resolve()
    if plugin_root != ROOT.resolve():
        errors.append("Marketplace source path does not resolve back to the plugin root")
    return errors


def validate_root_agent_metadata() -> list[str]:
    errors: list[str] = []
    metadata = parse_openai_yaml(ROOT_AGENT_METADATA)
    for field in ("icon_small", "icon_large"):
        asset = metadata.get(field)
        if not asset:
            errors.append(f"Root agent metadata is missing {field}")
            continue
        asset_path = ROOT / asset.removeprefix("./")
        if not asset_path.is_file():
            errors.append(f"Root agent metadata asset is missing: {asset_path}")
    return errors


def validate_sync_report() -> list[str]:
    if not SYNC_REPORT.exists():
        return [f"Missing sync report: {SYNC_REPORT}"]

    report = json.loads(SYNC_REPORT.read_text(encoding="utf-8"))
    expected_skills = [entry["name"] for entry in build_skill_manifest()]
    if report.get("skills") != expected_skills:
        return ["Sync report skill list is stale"]
    if report.get("skillCount") != len(expected_skills):
        return ["Sync report skill count is stale"]
    return []


def validate_skills() -> list[str]:
    errors: list[str] = []
    manifest_entries = build_skill_manifest()
    if not manifest_entries:
        return ["No synced skills were discovered"]

    for entry in manifest_entries:
        skill_dir = ROOT / entry["path"].removeprefix("./")
        for required_path in ("SKILL.md", "overlay.yaml", "upstream/SKILL.md", "agents/openai.yaml"):
            if not (skill_dir / required_path).exists():
                errors.append(f"Missing required skill file: {skill_dir / required_path}")

    return errors


def collect_validation_errors() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_plugin_manifest())
    errors.extend(validate_openclaw_bundle_metadata())
    errors.extend(validate_marketplace())
    errors.extend(validate_root_agent_metadata())
    errors.extend(validate_sync_report())
    errors.extend(validate_skills())
    errors.extend(check_build_outputs())
    errors.extend(check_manifest_is_current())
    return errors


def main() -> None:
    errors = collect_validation_errors()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Validated salesforce-plugin")


if __name__ == "__main__":
    main()
