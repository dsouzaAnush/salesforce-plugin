#!/usr/bin/env python3
"""Build plugin skill outputs from synced upstream content."""

from __future__ import annotations

import argparse
import filecmp
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"


def copy_path(source: Path, destination: Path) -> None:
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def build_skills() -> int:
    count = 0
    for skill_dir in sorted(path for path in SKILLS_DIR.glob("sf-*") if path.is_dir()):
        upstream_dir = skill_dir / "upstream"
        upstream_skill = upstream_dir / "SKILL.md"
        if not upstream_skill.exists():
            continue

        for entry in upstream_dir.iterdir():
            copy_path(entry, skill_dir / entry.name)
        count += 1

    return count


def compare_paths(source: Path, destination: Path) -> list[str]:
    if not destination.exists():
        return [f"Missing built path: {destination}"]

    if source.is_file():
        if not filecmp.cmp(source, destination, shallow=False):
            return [f"Built file is stale: {destination}"]
        return []

    errors: list[str] = []
    source_names = {path.name for path in source.iterdir()}
    destination_names = {path.name for path in destination.iterdir()}

    missing = sorted(source_names - destination_names)
    extra = sorted(destination_names - source_names)
    if missing:
        errors.append(f"Missing built entries in {destination}: {', '.join(missing)}")
    if extra:
        errors.append(f"Unexpected built entries in {destination}: {', '.join(extra)}")

    for child_name in sorted(source_names & destination_names):
        errors.extend(compare_paths(source / child_name, destination / child_name))

    return errors


def check_build_outputs() -> list[str]:
    errors: list[str] = []
    for skill_dir in sorted(path for path in SKILLS_DIR.glob("sf-*") if path.is_dir()):
        upstream_dir = skill_dir / "upstream"
        if not upstream_dir.exists():
            errors.append(f"Missing upstream copy for {skill_dir.name}")
            continue

        for entry in sorted(upstream_dir.iterdir()):
            errors.extend(compare_paths(entry, skill_dir / entry.name))

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Build plugin skill outputs from synced upstream skills")
    parser.add_argument("--check", action="store_true", help="Fail if built skill outputs are stale")
    args = parser.parse_args()

    if args.check:
        errors = check_build_outputs()
        if errors:
            raise SystemExit("\n".join(errors))
        print("Validated plugin skill outputs")
        return

    count = build_skills()
    print(f"Built {count} plugin skill outputs")


if __name__ == "__main__":
    main()
