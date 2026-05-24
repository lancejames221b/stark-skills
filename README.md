# stark-skills

A curated, depersonalized skills library for Claude AI, pi (Pi Coding Agent), OpenCode, and voice-enabled agents.

> **Looking for the full setup recipe?** See [docs/optimal-setup.md](docs/optimal-setup.md)
> for the personal-AI architecture this skills library is designed for — memory store,
> voice runtime, multi-machine fabric, and which SaaS to wire in. The skills compose
> with that stack; the doc walks a stranger from zero to a working setup in ~30 minutes.

## What It Is

A reusable collection of agent skills organized into canonical categories, with runtime adapters for different agents and install scripts that are safe by default.

The skills assume (but do not require) a broader ecosystem: a memory layer
([`agent-hivemind`](https://github.com/lancejames221b/agent-hivemind) + an Obsidian
vault), a notes layer (Notion via the official MCP server), an optional voice runtime
([`openjarvis`](https://github.com/lancejames221b/openjarvis)), and a multi-machine
fabric stitched together with SSH aliases, Tailscale, and `mcporter`. Most skills
degrade gracefully if a layer is missing; the ones that don't say so up front. See
[docs/optimal-setup.md](docs/optimal-setup.md) for how the pieces fit together.

## Safety Policy

All skills in this repo have been redacted or parameterized to remove personal information:

- Names, usernames, email addresses
- Phone numbers and home/office addresses
- Private machine names and hostnames
- Private IPs, tokens, keys, credentials
- Local absolute paths (e.g. `/home/<user>/...`)
- Channel/page/database IDs

All examples and templates use placeholders like `<USER_NAME>`, `<GITHUB_ORG>`, `<HOST_ALIAS>`.

## Repository Layout

```text
stark-skills/
  skills/core/          — canonical, agent-agnostic skills
  skills/agents/        — runtime-specific wrappers (thin adapters)
  skills/workflows/     — end-to-end multi-skill procedures
  skills/integrations/  — external-service connectors
  skills/voice/         — voice-first workflows and assistant behaviors
  adapters/             — agent-specific adapter code
  scripts/              — inventory, redaction, validation, and install
  docs/                 — documentation (inventory, policies, workflows)
  examples/             — placeholder-only examples for public use
  tests/                — layout and PII validation
```

## Quick Start (dry-run)

```bash
# Inventory your existing skills from known paths
./scripts/inventory-skills.sh --dry-run

# See what would be installed into Claude skills
./scripts/install-claude.sh --dry-run

# See what would be installed into pi skills
./scripts/install-pi.sh --dry-run

# Install to all supported agents (use with caution)
./scripts/install-all.sh --claude --pi --opencode
```

## Installation

See `docs/install.md`.

## Contribution Guidelines

See `docs/contributing.md` (pending).

## License

MIT. See LICENSE.
