from __future__ import annotations

import json
from pathlib import Path

from scripts.skill_utils import build_skill_manifest, score_manifest_entry


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "skill-routing-evals.json"


def test_prompt_fixtures_route_to_expected_skill() -> None:
    entries = build_skill_manifest()
    entries_by_name = {entry["name"]: entry for entry in entries}
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))

    for fixture in fixtures:
        prompt = fixture["prompt"]
        expected_skill = fixture["expected_skill"]

        scores = sorted(
            ((entry["name"], score_manifest_entry(entry, prompt)) for entry in entries),
            key=lambda item: item[1],
            reverse=True,
        )
        best_skill, best_score = scores[0]

        assert expected_skill in entries_by_name, f"Missing expected skill in manifest: {expected_skill}"
        assert best_score > 0, f"Prompt did not match any skill: {prompt}"
        assert best_skill == expected_skill, (
            f"Expected {expected_skill} for prompt {prompt!r}, got {best_skill}. "
            f"Top scores: {scores[:5]}"
        )
