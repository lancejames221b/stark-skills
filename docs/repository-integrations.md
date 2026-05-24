# Repository Integrations

External-service skills under `skills/core/integrations/`. Each connects an agent to a third-party platform via that platform's MCP server, REST API, or CLI. All credentials are read from environment variables or local credential files — nothing is hard-coded.

## Available integrations

| Integration | What the skill does | Required env / config |
|---|---|---|
| **discord-activity-tracker** | Scans Discord channels for recent activity, extracts TODOs and topic context, updates a channel registry, indexes to hAIveMind, and produces a channel digest. Three modes: full digest, fast multi-channel ping, and per-topic lookup across hAIveMind + registry + channel history. | `DISCORD_TOKEN`; priority channel IDs in `channel-registry.json`; hAIveMind reachable via `mcporter`; optional `<TAILSCALE_IP>:3335` for voice output. |
| **gdrive-upload** | Uploads any local file (binary or text) to a specific Google Drive folder and returns a shareable link. Works for zip / pdf / xlsx / docx / images. Uses direct multipart POST against the Drive REST API with a refresh-token-derived access token (the Google Workspace MCP has no Drive write scope). | `<EMAIL_ADDRESS>`; OAuth credentials JSON at `<LOCAL_PATH>/.google_workspace_mcp/credentials/<EMAIL_ADDRESS>.json` containing `client_id`, `client_secret`, `refresh_token`; target Drive folder ID. |
| **linear** | Comprehensive Linear project management via the Linear MCP. Covers all 40 tools — issues, projects, initiatives, documents, comments, attachments, teams, users, cycles. Daily standups, sprint planning, bug triage, OKRs, roadmaps. | Linear MCP server configured; default assignee `<EMAIL_ADDRESS>` / `<LINEAR_ID>`; default team identifier (e.g. `Engineering`); project IDs referenced as `<UUID>`. |
| **notion-oauth** | Notion read/write via the official OAuth MCP. Search, fetch, create pages, update properties / blocks, move pages, manage databases, comments, and users. Includes wrapper scripts (`create-page.sh`, `update-page.sh`) that avoid the mcporter CLI's nested-JSON pitfalls. | `notion-oauth` MCP server configured via `mcporter`; parent page IDs as `<NOTION_PAGE_ID>` / `<NOTION_ID>`; optional org constants `<ORG_DOMAIN>`, `<ORG_NAME>`, `<ORG_ID>`. |

## Conventions

- **MCP-first.** Where a vendor ships an MCP server, the skill uses it (`mcporter call <server>.<tool> ...`). REST is the fallback only when the MCP lacks the needed scope (see `gdrive-upload`).
- **BYOK.** Tokens, refresh credentials, and IDs are always read from env vars or local files — never embedded in the SKILL.md. Replace `<PLACEHOLDER>` values in each skill with your own before running.
- **Read-only by default.** If a downstream service is sensitive (e.g. ticketing), the skill defaults to read-only and requires an explicit flag for writes.

## Adding a new integration

1. Create `skills/core/integrations/<name>/SKILL.md` following `templates/skill.md`.
2. Set `category: integrations` in the frontmatter.
3. Document required env vars in a `## Required setup` section near the top.
4. Run `./scripts/validate-no-pii.sh --path skills/core/integrations/<name>/` and fix any matches before committing.
5. Append a row to the table above with the integration name, one-line description, and required env / config.
