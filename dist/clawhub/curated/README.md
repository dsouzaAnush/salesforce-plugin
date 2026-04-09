<p align="center">
  <img src="assets/salesforce-logo.png" alt="Salesforce cloud logo" width="88" height="88">
</p>

# salesforce-plugin

A dedicated plugin wrapper repo for Salesforce agent skills.

This repository is packaged as a **Codex bundle plugin** and is also intended to
be publishable to **ClawHub** as an OpenClaw-compatible bundle package.

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

## Host compatibility

- **Codex** reads the bundle from [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json)
- **ClawHub / OpenClaw** can publish and install a generated bundle artifact rooted at [`package.json`](package.json) plus [`openclaw.bundle.json`](openclaw.bundle.json)

The root `package.json` is intentionally additive packaging metadata. It does not
change the Codex plugin behavior or the shipped Salesforce skills.

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

3. Build a publishable ClawHub artifact:

```bash
python3 scripts/build_clawhub_bundle.py
```

The default `curated` profile is the current publish-safe ClawHub shape. It
keeps the plugin Codex-compatible and adds a small set of high-value reference
docs for the main Salesforce skill families while avoiding the larger sync-only
payloads that caused ClawHub bundle publishes to fail in practice.

It includes:

- root bundle manifests and plugin branding assets
- root agent metadata
- each skill's `SKILL.md`
- each skill's `agents/openai.yaml`
- a curated subset of reference docs for Apex, LWC, Flow, SOQL, metadata,
  testing, deploy, integration, connected apps, and selected Agentforce skills

Other profiles are available when you need stricter or larger artifacts:

- `core`
- `core-assets`
- `core-refs-assets`
- `runtime`

At the moment, both `core` and `curated` are verified to publish cleanly to
ClawHub for this repo. `core` is the fallback minimal shape. `curated` is the
recommended publish target.

4. Run stale-build checks:

```bash
python3 scripts/build_skills.py --check
python3 scripts/build_skill_manifest.py --check
python3 scripts/validate.py
```

5. Run tests:

```bash
pytest -q
pytest --cov=scripts --cov-report=term-missing -q
```

## Current status

- The repo is scaffolded as a plugin root.
- Salesforce skills are synced from the local upstream checkout.
- Generated artifacts are tracked and validated for drift.
- Overlay metadata is intentionally minimal in v1, but the generated manifest now exposes structured routing metadata and prompt fixtures for eval-style checks.
- ClawHub publishing should use the generated `dist/clawhub/curated/` artifact instead of the full repo root.
