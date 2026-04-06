from __future__ import annotations

from scripts.build_skill_manifest import check_manifest_is_current
from scripts.build_skills import check_build_outputs
from scripts.validate import collect_validation_errors


def test_build_outputs_are_current() -> None:
    assert check_build_outputs() == []


def test_generated_manifest_is_current() -> None:
    assert check_manifest_is_current() == []


def test_validate_reports_no_errors() -> None:
    assert collect_validation_errors() == []
