#!/usr/bin/env python3
"""Build a publishable ClawHub bundle artifact from the repo workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "clawhub"
REPORT_NAME = "bundle-report.json"

ROOT_FILES = (
    ".codex-plugin/plugin.json",
    "package.json",
    "openclaw.bundle.json",
    "salesforce.md",
    "README.md",
    "agents/openai.yaml",
)
ROOT_DIRS = ("assets",)
SKILL_BASE_FILES = ("SKILL.md", "agents/openai.yaml")
PROFILE_DIRS = {
    "core": (),
    "core-assets": ("assets",),
    "core-refs-assets": ("assets", "references"),
    "runtime": ("assets", "references", "scripts", "hooks"),
}


def copy_file(relative_path: str, output_dir: Path) -> None:
    source = ROOT / relative_path
    if not source.is_file():
        return
    destination = output_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(relative_path: str, output_dir: Path) -> None:
    source = ROOT / relative_path
    if not source.is_dir():
        return
    destination = output_dir / relative_path
    shutil.copytree(source, destination, dirs_exist_ok=True)


def build_bundle(output_dir: Path, profile: str) -> dict[str, object]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in ROOT_FILES:
        copy_file(relative_path, output_dir)
    for relative_path in ROOT_DIRS:
        copy_tree(relative_path, output_dir)

    skills_dir = ROOT / "skills"
    published_skills: list[str] = []
    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        published_skills.append(skill_dir.name)
        for relative_path in SKILL_BASE_FILES:
            source = skill_dir / relative_path
            if not source.is_file():
                continue
            destination = output_dir / "skills" / skill_dir.name / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        for directory_name in PROFILE_DIRS[profile]:
            source_directory = skill_dir / directory_name
            if not source_directory.is_dir():
                continue
            destination_directory = output_dir / "skills" / skill_dir.name / directory_name
            shutil.copytree(source_directory, destination_directory, dirs_exist_ok=True)

    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    report = {
        "profile": profile,
        "outputDir": str(output_dir),
        "fileCount": len(files),
        "totalBytes": sum(path.stat().st_size for path in files),
        "skills": published_skills,
    }
    (output_dir / REPORT_NAME).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_DIRS),
        default="core",
        help="Bundle profile to emit. The default core profile is the publish-safe shape verified against ClawHub.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for the built bundle.",
    )
    args = parser.parse_args()

    output_dir = args.out / args.profile if args.out == DEFAULT_OUTPUT else args.out
    report = build_bundle(output_dir.resolve(), args.profile)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
