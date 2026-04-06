#!/usr/bin/env python3
"""Shared helpers for parsing plugin skill metadata."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

GENERIC_PHRASES = {
    "user",
    "users",
    "task",
    "tasks",
    "work",
    "data",
    "questions",
    "question",
    "only",
    "touches",
    "touch",
    "touching",
    "builds",
    "build",
    "writes",
    "write",
    "reviews",
    "review",
    "fixes",
    "fix",
    "edits",
    "edit",
    "manages",
    "manage",
    "creates",
    "create",
    "needs",
    "need",
    "with",
    "about",
    "the",
    "a",
    "an",
    "or",
    "and",
}


def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md is missing YAML frontmatter")
    _, frontmatter, _ = text.split("---\n", 2)
    return frontmatter


def parse_frontmatter_field(frontmatter: str, key: str) -> str | None:
    lines = frontmatter.splitlines()
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue

        value = line[len(prefix) :].strip()
        if value and value not in {">", "|"}:
            return value.strip("\"'")

        collected: list[str] = []
        for next_line in lines[index + 1 :]:
            if not next_line.startswith((" ", "\t")):
                break
            collected.append(next_line.strip())
        return collapse_ws(" ".join(part for part in collected if part))

    return None


def parse_openai_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    in_interface = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line == "interface:":
            in_interface = True
            continue
        if in_interface and not raw_line.startswith("  "):
            break
        if not in_interface:
            continue

        key, _, value = line.strip().partition(":")
        if not key or not value:
            continue
        data[key] = value.strip().strip("\"'")

    return data


def parse_overlay(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    if not path.exists():
        return sections

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if not raw_line.startswith(" "):
            current_section = line[:-1]
            sections[current_section] = {}
            continue
        if current_section is None:
            continue
        key, _, value = line.strip().partition(":")
        if not key or not value:
            continue
        sections[current_section][key] = value.strip().strip("\"'")

    return sections


def extract_clause(description: str, label: str) -> str:
    pattern = rf"{label}:\s*(.+?)(?=(DO NOT TRIGGER when:|TRIGGER when:|$))"
    match = re.search(pattern, description, re.IGNORECASE)
    if not match:
        return ""
    return collapse_ws(match.group(1))


def normalize_phrase(phrase: str) -> str:
    phrase = re.sub(r"\(use [^)]+\)", "", phrase)
    phrase = phrase.replace(" or ", ", ")
    phrase = phrase.replace(" and ", ", ")
    phrase = phrase.replace("/", " / ")
    phrase = collapse_ws(phrase.lower())
    for prefix in (
        "user ",
        "the task is ",
        "the task is about ",
        "the task involves ",
        "the user is ",
    ):
        if phrase.startswith(prefix):
            phrase = phrase[len(prefix) :]
    phrase = re.sub(
        r"^(writes|reviews|fixes|builds|edits|creates|manages|tests|browses|sets up|touches|runs|pulls)\s+",
        "",
        phrase,
    )
    phrase = phrase.strip(" ,.")
    return phrase


def split_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()

    def add_keyword(keyword: str) -> None:
        keyword = keyword.strip()
        if not keyword or keyword in seen:
            return
        keywords.append(keyword)
        seen.add(keyword)
        if " " in keyword and keyword.endswith("s") and not keyword.endswith(("ss", "es")):
            singular = keyword[:-1]
            if singular not in seen:
                keywords.append(singular)
                seen.add(singular)
        if keyword.startswith("salesforce "):
            trimmed = keyword.removeprefix("salesforce ").strip()
            if trimmed and trimmed not in seen:
                keywords.append(trimmed)
                seen.add(trimmed)

    for chunk in re.split(r",|;|\bor\b|\band\b", text, flags=re.IGNORECASE):
        raw_chunk = chunk.lower()
        for match in re.findall(r"[a-z0-9.-]+\.[a-z]{2,}|\.[a-z0-9-]+", raw_chunk):
            add_keyword(match)
        phrase = normalize_phrase(chunk)
        if not phrase or phrase in GENERIC_PHRASES:
            continue
        words = phrase.split()
        if len(words) == 1 and words[0] in GENERIC_PHRASES:
            continue
        add_keyword(phrase)
    return keywords


def build_skill_manifest_entry(skill_dir: Path) -> dict[str, object]:
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    description = parse_frontmatter_field(frontmatter, "description") or ""
    metadata = parse_openai_yaml(skill_dir / "agents" / "openai.yaml")
    overlay = parse_overlay(skill_dir / "overlay.yaml")
    trigger_when = extract_clause(description, "TRIGGER when")
    do_not_trigger_when = extract_clause(description, "DO NOT TRIGGER when")
    keyword_source = trigger_when or description

    return {
        "name": parse_frontmatter_field(frontmatter, "name") or skill_dir.name,
        "description": description,
        "path": f"./skills/{skill_dir.name}",
        "upstreamPath": f"./skills/{skill_dir.name}/upstream",
        "overlayPath": f"./skills/{skill_dir.name}/overlay.yaml",
        "displayName": metadata.get("display_name", ""),
        "shortDescription": metadata.get("short_description", ""),
        "defaultPrompt": metadata.get("default_prompt", ""),
        "iconSmall": metadata.get("icon_small", ""),
        "iconLarge": metadata.get("icon_large", ""),
        "brandColor": metadata.get("brand_color", ""),
        "sourceRepoPath": overlay.get("source", {}).get("repo_path", ""),
        "sourceSkill": overlay.get("source", {}).get("skill", skill_dir.name),
        "syncMode": overlay.get("source", {}).get("sync_mode", ""),
        "family": overlay.get("plugin", {}).get("family", ""),
        "status": overlay.get("plugin", {}).get("status", ""),
        "routingPriority": overlay.get("routing", {}).get("priority", ""),
        "triggerWhen": trigger_when,
        "doNotTriggerWhen": do_not_trigger_when,
        "keywords": split_keywords(keyword_source),
        "negativeKeywords": split_keywords(do_not_trigger_when),
    }


def build_skill_manifest(skills_dir: Path = SKILLS_DIR) -> list[dict[str, object]]:
    return [
        build_skill_manifest_entry(skill_dir)
        for skill_dir in sorted(path for path in skills_dir.glob("sf-*") if path.is_dir())
        if (skill_dir / "SKILL.md").exists()
    ]


def score_manifest_entry(entry: dict[str, object], prompt: str) -> int:
    prompt_lower = prompt.lower()
    score = 0

    for keyword in entry.get("keywords", []):
        if keyword and keyword in prompt_lower:
            score += 3

    for keyword in entry.get("negativeKeywords", []):
        if keyword and keyword in prompt_lower:
            score -= 4

    return score
