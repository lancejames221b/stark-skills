# Contributing to stark-skills

Welcome — thanks for considering a contribution. This repo is a curated, depersonalized skills library for Claude AI, pi (Pi Coding Agent), OpenCode, and voice-enabled agents. The bar is "useful to anyone with a similar toolchain"; the gate is "no PII, ever."

## The PII gate

Every change must pass:

```bash
./scripts/validate-no-pii.sh --path .
```

The validator catches the most common leakage patterns (emails, phone numbers, absolute home paths, private IPs, long ID strings). A clean run is required before any commit lands on `main`. A pre-commit hook (`scripts/git-pii-guard`) runs the same check locally.

When something private is unavoidable, replace it with a canonical placeholder (`<USER_NAME>`, `<EMAIL_ADDRESS>`, `<GITHUB_ORG>`, `<HOST_ALIAS>`, `<NOTION_PAGE_ID>`, `<DISCORD_CHANNEL_ID>`, `<LOCAL_PATH>`, etc.). The full list lives in `docs/redaction-policy.md`.

## Adding a skill

1. Pick the right home under `skills/`:
   - `skills/core/<category>/<name>/` — canonical, agent-agnostic skill. Categories include `planning`, `execution`, `memory`, `verification`, `debugging`, `research`, `handoff`, `workflows`, `integrations`.
   - `skills/voice/<name>/` — voice-first behavior (Jarvis-style).
   - `skills/agents/<runtime>/<name>/` — thin runtime-specific wrappers around a core skill.
   - `skills/workflows/<name>/` — end-to-end multi-skill procedures.

2. Copy `templates/skill.md` as your starting point. Required frontmatter shape:

   ```yaml
   ---
   name: <skill-slug>
   description: <one-sentence trigger and purpose>
   category: <planning | execution | memory | verification | debugging | research | handoff | workflows | integrations | voice>
   runtimes: [claude, pi, opencode]
   pii_safe: true
   ---
   ```

3. Body sections (recommended): `When to Use`, `Inputs`, `Procedure`, `Verification`, `Output Format`, `Runtime Notes`. Keep each step imperative and verifiable.

4. If the skill talks to a third-party service, document the env vars in a `## Required setup` section and add a row to `docs/repository-integrations.md`. Never hard-code credentials.

5. Run the PII validator on just your new file before staging:

   ```bash
   ./scripts/validate-no-pii.sh --path skills/<path>/<your-skill>/SKILL.md
   ```

## Commit-message style

Short, imperative, one-line subject. Body if it needs context. Example:

```
Add notion-oauth integration skill

Wraps mcporter call notion-oauth.* with safer JSON construction
via the create-page.sh / update-page.sh helpers.
```

Don't add `Co-Authored-By` lines for human contributors; reserve those for actual AI-assisted authorship.

## Pre-commit checklist

- [ ] `./scripts/validate-no-pii.sh --path .` exits clean.
- [ ] `./tests/validate-layout.sh` exits clean.
- [ ] Frontmatter has `name`, `description`, `category`, `runtimes`, `pii_safe`.
- [ ] No hard-coded credentials, channel IDs, or absolute home paths.
- [ ] Shell scripts (if added) pass `shellcheck`.

## Questions

Open an issue with the `question` label, or start a draft PR — happy to discuss design before you build.
