#!/usr/bin/env python3
"""Generate a lightweight manifest of synced plugin skills."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.skill_utils import build_skill_manifest
else:
    from .skill_utils import build_skill_manifest


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "generated"
OUTPUT_FILE = GENERATED_DIR / "skill-manifest.json"

def render_manifest_json() -> str:
    manifest = build_skill_manifest()
    return json.dumps(manifest, indent=2) + "\n"


def write_manifest() -> None:
    GENERATED_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(render_manifest_json(), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} with {len(build_skill_manifest())} skills")


def check_manifest_is_current() -> list[str]:
    expected = render_manifest_json()
    if not OUTPUT_FILE.exists():
        return [f"Missing generated manifest: {OUTPUT_FILE}"]

    current = OUTPUT_FILE.read_text(encoding="utf-8")
    if current != expected:
        return [f"Generated manifest is stale: {OUTPUT_FILE}"]

    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the generated plugin skill manifest")
    parser.add_argument("--check", action="store_true", help="Fail if the generated manifest is stale")
    args = parser.parse_args()

    if args.check:
        errors = check_manifest_is_current()
        if errors:
            raise SystemExit("\n".join(errors))
        print(f"Validated {OUTPUT_FILE}")
        return

    write_manifest()


if __name__ == "__main__":
    main()
