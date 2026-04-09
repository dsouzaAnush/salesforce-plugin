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
CURATED_REFERENCE_FILES = {
    "sf-ai-agentforce": ["references/builder-workflow.md"],
    "sf-ai-agentforce-testing": ["references/execution-protocol.md"],
    "sf-ai-agentscript": ["references/cli-guide.md"],
    "sf-apex": [
        "references/best-practices.md",
        "references/bulkification-guide.md",
        "references/design-patterns.md",
    ],
    "sf-connected-apps": [
        "references/oauth-flows-reference.md",
        "references/security-checklist.md",
    ],
    "sf-data": [
        "references/sf-cli-data-commands.md",
        "references/test-data-best-practices.md",
    ],
    "sf-datacloud": ["references/plugin-setup.md"],
    "sf-debug": ["references/debug-log-reference.md"],
    "sf-deploy": [
        "references/deployment-workflows.md",
        "references/trigger-deployment-safety.md",
    ],
    "sf-diagram-mermaid": ["references/mermaid-reference.md"],
    "sf-flow": [
        "references/flow-best-practices.md",
        "references/flow-quick-reference.md",
    ],
    "sf-integration": [
        "references/callout-patterns.md",
        "references/platform-events-guide.md",
    ],
    "sf-lwc": [
        "references/component-patterns.md",
        "references/lwc-best-practices.md",
        "references/performance-guide.md",
    ],
    "sf-metadata": [
        "references/metadata-types-reference.md",
        "references/sf-cli-commands.md",
    ],
    "sf-permissions": ["references/permission-model.md"],
    "sf-soql": [
        "references/query-optimization.md",
        "references/soql-reference.md",
    ],
    "sf-testing": [
        "references/mocking-patterns.md",
        "references/testing-best-practices.md",
    ],
}
PROFILE_DIRS = {
    "core": (),
    "curated": (),
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
    curated_reference_count = 0
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

        if profile == "curated":
            for relative_path in CURATED_REFERENCE_FILES.get(skill_dir.name, []):
                source = skill_dir / relative_path
                if not source.is_file():
                    continue
                destination = output_dir / "skills" / skill_dir.name / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                curated_reference_count += 1

    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    report = {
        "profile": profile,
        "outputDir": str(output_dir),
        "fileCount": len(files),
        "totalBytes": sum(path.stat().st_size for path in files),
        "skills": published_skills,
    }
    if profile == "curated":
        report["curatedReferenceFiles"] = curated_reference_count
    (output_dir / REPORT_NAME).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_DIRS),
        default="curated",
        help="Bundle profile to emit. The default curated profile is the current publish-safe shape recommended for ClawHub.",
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
