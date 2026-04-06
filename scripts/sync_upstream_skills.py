#!/usr/bin/env python3
"""Sync sf-* skills from the local upstream salesforce-skills checkout."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPSTREAM = Path("/Users/anushdsouza/Developer/work/salesforce-skills")
DEFAULT_UPSTREAM_REPOSITORY = "https://github.com/dsouzaAnush/salesforce-skills"
SKILLS_DIR = ROOT / "skills"
GENERATED_DIR = ROOT / "generated"


def discover_upstream_skills(upstream_root: Path) -> list[Path]:
    upstream_skills_dir = upstream_root / "skills"
    return sorted(path for path in upstream_skills_dir.glob("sf-*") if path.is_dir())


def write_overlay(skill_dir: Path, upstream_repository: str, skill_name: str) -> None:
    overlay = (
        "source:\n"
        f'  repo_path: "{upstream_repository}"\n'
        f'  skill: "{skill_name}"\n'
        '  sync_mode: "local-copy"\n'
        "\n"
        "plugin:\n"
        '  family: "salesforce"\n'
        '  managed_by_plugin: false\n'
        '  status: "synced"\n'
        "\n"
        "routing:\n"
        '  priority: "medium"\n'
    )
    (skill_dir / "overlay.yaml").write_text(overlay, encoding="utf-8")


def sync_skill(upstream_skill_dir: Path, upstream_repository: str) -> None:
    skill_name = upstream_skill_dir.name
    plugin_skill_dir = SKILLS_DIR / skill_name
    upstream_dest = plugin_skill_dir / "upstream"

    plugin_skill_dir.mkdir(parents=True, exist_ok=True)

    if upstream_dest.exists():
        shutil.rmtree(upstream_dest)

    shutil.copytree(upstream_skill_dir, upstream_dest)
    shutil.copy2(upstream_dest / "SKILL.md", plugin_skill_dir / "SKILL.md")
    write_overlay(plugin_skill_dir, upstream_repository, skill_name)


def remove_stale_skills(expected_skill_names: set[str]) -> None:
    for skill_dir in sorted(path for path in SKILLS_DIR.glob("sf-*") if path.is_dir()):
        if skill_dir.name not in expected_skill_names:
            shutil.rmtree(skill_dir)


def write_sync_report(upstream_root: Path, upstream_repository: str, skills: list[str]) -> None:
    GENERATED_DIR.mkdir(exist_ok=True)
    report = {
        "upstreamLocalPath": str(upstream_root),
        "upstreamRepository": upstream_repository,
        "skillCount": len(skills),
        "skills": skills,
    }
    (GENERATED_DIR / "sync-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync sf-* skills from the upstream skills repo")
    parser.add_argument(
        "--upstream",
        default=str(DEFAULT_UPSTREAM),
        help="Path to the upstream salesforce-skills repo",
    )
    parser.add_argument(
        "--upstream-repository",
        default=DEFAULT_UPSTREAM_REPOSITORY,
        help="Public repository URL for the upstream salesforce-skills repo",
    )
    args = parser.parse_args()

    upstream_root = Path(args.upstream).resolve()
    if not upstream_root.is_dir():
        raise SystemExit(f"Upstream repo not found: {upstream_root}")

    skill_dirs = discover_upstream_skills(upstream_root)
    if not skill_dirs:
        raise SystemExit(f"No sf-* skills found in: {upstream_root / 'skills'}")

    SKILLS_DIR.mkdir(exist_ok=True)
    remove_stale_skills({path.name for path in skill_dirs})
    for skill_dir in skill_dirs:
        sync_skill(skill_dir, args.upstream_repository)

    write_sync_report(upstream_root, args.upstream_repository, [path.name for path in skill_dirs])
    print(f"Synced {len(skill_dirs)} skills from {upstream_root}")


if __name__ == "__main__":
    main()
