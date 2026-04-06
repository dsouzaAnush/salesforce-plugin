<p align="center">
  <img src="assets/salesforce-logo.png" alt="Salesforce cloud logo" width="88" height="88">
</p>

# salesforce-plugin

A dedicated plugin wrapper repo for Salesforce agent skills.

This repo is the plugin-side companion to the upstream skills repo at:

- [dsouzaAnush/salesforce-skills](https://github.com/dsouzaAnush/salesforce-skills)

The split is intentional:

- `salesforce-skills` stays the reusable upstream source of truth for `sf-*` skills
- `salesforce-plugin` adds plugin-specific wrapper structure:
  - plugin manifest
  - future hooks, commands, and agents
  - generated manifests
  - plugin-specific routing metadata
  - upstream sync workflow

## Layout

```text
salesforce-plugin/
├── .codex-plugin/plugin.json
├── .agents/plugins/marketplace.json
├── salesforce.md
├── skills/
│   └── sf-*/ 
│       ├── overlay.yaml
│       ├── upstream/
│       │   └── ...
│       └── SKILL.md
├── scripts/
│   ├── sync_upstream_skills.py
│   ├── build_skills.py
│   ├── build_skill_manifest.py
│   ├── skill_utils.py
│   └── validate.py
├── generated/
├── hooks/
├── commands/
├── agents/
└── tests/
```

## Upstream workflow

1. Sync current upstream skills:

```bash
python3 scripts/sync_upstream_skills.py
```

2. Rebuild top-level plugin skill outputs:

```bash
python3 scripts/build_skills.py
python3 scripts/build_skill_manifest.py
```

3. Run stale-build checks:

```bash
python3 scripts/build_skills.py --check
python3 scripts/build_skill_manifest.py --check
python3 scripts/validate.py
```

4. Run tests:

```bash
pytest -q
pytest --cov=scripts --cov-report=term-missing -q
```

## Current status

- The repo is scaffolded as a plugin root.
- Salesforce skills are synced from the local upstream checkout.
- Generated artifacts are tracked and validated for drift.
- Overlay metadata is intentionally minimal in v1, but the generated manifest now exposes structured routing metadata and prompt fixtures for eval-style checks.
