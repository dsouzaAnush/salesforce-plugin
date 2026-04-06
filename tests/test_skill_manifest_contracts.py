from __future__ import annotations

from scripts.skill_utils import build_skill_manifest


def test_generated_manifest_entries_have_structured_metadata() -> None:
    manifest = build_skill_manifest()
    assert manifest

    for entry in manifest:
        assert entry["name"].startswith("sf-")
        assert entry["path"].startswith("./skills/")
        assert entry["upstreamPath"].endswith("/upstream")
        assert entry["overlayPath"].endswith("/overlay.yaml")
        assert entry["displayName"]
        assert entry["shortDescription"]
        assert entry["defaultPrompt"]
        assert entry["iconSmall"]
        assert entry["iconLarge"]
        assert entry["brandColor"] == "#0176D3"
        assert entry["sourceRepoPath"]
        assert entry["family"] == "salesforce"
        assert entry["routingPriority"] == "medium"


def test_trigger_style_skills_publish_routing_keywords() -> None:
    manifest = {entry["name"]: entry for entry in build_skill_manifest()}

    assert "apex classes" in manifest["sf-apex"]["keywords"]
    assert "record-triggered" in manifest["sf-flow"]["keywords"]
    assert "data cloud connections" in manifest["sf-datacloud-connect"]["keywords"]
    assert "help.salesforce.com" in manifest["sf-docs"]["keywords"]
