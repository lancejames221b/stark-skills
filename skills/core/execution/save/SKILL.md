---
name: save
description: Save a memory to Obsidian (primary) + hAIveMind index. Empty input → checkpoint mode (auto-summarize current conversation). Add :notion flag to also push to Notion. Use when the user asks to "save", "remember this", "store this", "note this down", or "checkpoint".
category: execution
runtimes: [claude]
pii_safe: true
---

# Save Skill

> **Universal path: ALL backends are accessed via `ssh <INFERENCE_HOST> mcporter`. Works identically from claude-code, opencode, PI, or any host with SSH to <INFERENCE_HOST>. The local `mcp__*` tools are session-tied — don't use them.**

Persist a memory to the internal brain. Obsidian on <INFERENCE_HOST> is the canonical store.

## Two modes

- **Explicit mode** — user provides content: `/save <text>` or `/save :notion #project <text>`.
- **Checkpoint mode** — empty input (or only flags): auto-summarize the current conversation. See "Checkpoint mode" below.

## Architecture

- **Obsidian** — canonical, always written. Path on <INFERENCE_HOST>: `/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/<category>/<slug>.md`. Sensitive content goes here **only**.
- **hAIveMind** — `[OBS-MEM]` index entry for fast semantic search. Always written.
- **Notion** — external surface (meetings, plans, deliverables). Written **only** when user explicitly passes `:notion` flag. Never for sensitive content.

All three backends are reachable via `mcporter` running on <INFERENCE_HOST>. There is exactly **one** invocation pattern:

```bash
ssh <INFERENCE_HOST> 'mcporter call <server>.<tool> "param1=value1" "param2=value2" ...'
```

Each parameter is a SEPARATE quoted arg — never query-string-encode them.

## Backends and tool names (mcporter)

| Server | Key tools | Notes |
|---|---|---|
| `haivemind` | `store_memory`, `update_memory`, `search_memories` | `category` arg is required for store. |
| `obsidian` | `write_file`, `read_text_file`, `search_files` | Vault root: `/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/` |
| `notion` | `notion-create-pages`, `notion-update-page`, `notion-search` | DB id `<NOTION_ID>` for the Memory database. |

If `ssh <INFERENCE_HOST>` is unreachable, the save skill must REFUSE to claim success — there is no local-write fallback that preserves cross-machine retrieval.

## Credential Detection

Scan the full content body for these patterns. Any match → `sensitive=true`, route to `Vault/`, skip Notion **even if `:notion` flag is set**.

| Pattern (case-insensitive) | Matches |
|----------------------------|---------|
| `sk-[A-Za-z0-9\-_]{20,}` | OpenAI / Anthropic keys |
| `AKIA[A-Z0-9]{16}` | AWS access key IDs |
| `ghp_[A-Za-z0-9]{10,}` | GitHub PATs |
| `gho_[A-Za-z0-9]{10,}` | GitHub OAuth tokens |
| `xoxb-[0-9A-Za-z\-]+` | Slack bot tokens |
| `xoxp-[0-9A-Za-z\-]+` | Slack user tokens |
| `api[_-]?key\s*[:=]\s*\S{8,}` | Generic API key assignments |
| `password\s*[:=]\s*\S{4,}` | Password assignments |
| `passwd\s*[:=]\s*\S{4,}` | Passwd assignments |
| `-----BEGIN (RSA\|EC\|PRIVATE\|CERTIFICATE)` | PEM / cert blocks |
| `(postgres\|mysql\|mongodb)://[^@]+:[^@]+@` | DB URLs with embedded creds |
| `Bearer [A-Za-z0-9\-._~+/]{20,}` | Bearer tokens |
| `[A-Z][A-Z0-9_]*(_SECRET\|_TOKEN\|_PASSWORD\|_API_KEY)\s*[=:]\s*\S+` | Secret env var assignments |

When `sensitive=true`:
- Write to `Vault/<slug>.md` (not category subdir)
- Prepend `> ⚠️ Credential content — Obsidian-only, never synced to Notion`
- Skip Notion write regardless of `:notion` flag
- Tag haivemind entry with `auto-detected-credential`

## Sensitive categories (Obsidian ONLY)

`security`, `personal`, `sensitive` → always write to `Vault/<slug>.md`, never Notion.

## Checkpoint mode (empty input)

Triggered when args are empty OR contain only flag tokens (`:notion`, `#category`, `:tag1:tag2`) with no content body.

Build the memory body yourself from the current conversation. Don't ask "what to save" — that defeats the purpose. Produce:

- **Body** — 4–10 bullet points: Goal, What was done, Decisions (only if non-obvious), Open items, References (paths/URLs/IDs).
- **Title** — short phrase capturing the session's outcome.
- **Category** — infer from work (`project`, `infrastructure`, `incident`, `deployment`, `feature`, etc.). User's `#category` flag overrides.
- **Tags** — 2–5 relevant tags.

If the conversation is too short (<3 user/assistant exchanges), tell the user there's nothing meaningful to checkpoint rather than producing thin content.

After building the body, set `source: save-checkpoint` in frontmatter and proceed through the flow below.

## Flow

### 1. Parse input

- `:notion` anywhere → set `notion_flag=true`, strip `:notion` from content
- `#category` → category (valid: `global`, `project`, `infrastructure`, `security`, `deployment`, `rules`, `incident`, `feature`, `config`, `documentation`, `important`, `personal`, `sensitive`). Default: `global`.
- `:tag1:tag2` → tags.
- Remainder → content body. **If empty after stripping flags → checkpoint mode.**

### 2. Credential scan

Run all 13 patterns against the content body. Apply rules above.

### 3. Build properties

- **Title** — short phrase ≤ 100 chars
- **Slug** — kebab-case of title, ≤ 60 chars (filename)
- **Summary** — first sentence or first ~200 chars, one line. Never include secrets.
- **Machine** — current hostname → `<WORKSTATION_HOST>`/`<INFERENCE_HOST>`/`<MAC_HOST>` / `multi`.
- **Date** — today, `YYYY-MM-DD`.

### 4. Dedup probe (run before write)

Two parallel calls via mcporter:

```bash
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<Title>" "semantic=true"  "limit=5"'
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<Title>" "semantic=false" "limit=5"'
```

Match logic:
- **Strong match** = same `obsidian_path` (or `Obsidian:` field) as the planned `<obsidian_subdir>/<slug>.md`, OR title overlap ≥ 80%, OR top result score ≥ 0.85 + same category.
- **Weak match** = score 0.7–0.85 in same category.

Behavior:
- **Strong** → update the existing memory (overwrite Obsidian file preserving original `date:`, set `updated:` field; call `haivemind.update_memory` with the existing memory_id). Skip step 5 + 7. Continue to Notion (step 6) only if `:notion` and not previously synced. Confirmation: `🔄 Updated existing memory: **<Title>** → <existing path>`.
- **Weak** → proceed with new write, include `related: [<existing slug>]` in frontmatter.
- **No match** → proceed normally.

In checkpoint mode, skip the dedup probe — checkpoints are inherently new.

### 5. Write Obsidian file (always)

```bash
ssh <INFERENCE_HOST> 'mcporter call obsidian.write_file \
  "path=/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/<obsidian_subdir>/<slug>.md" \
  "content=<full frontmatter + body>"'
```

Frontmatter template:

```markdown
---
title: <Title>
category: <category>
tags: [<tags>]
machine: <machine>
date: <YYYY-MM-DD>
source: save
sensitive: <true|false>
notion_url: ""
---

<full content body>
```

Build the content with a heredoc piped into the ssh command, or write to a temp file and pass via `cat`/scp if the body has shell-special chars.

### 6. Create Notion page (only if `notion_flag=true` AND `sensitive=false`)

```bash
ssh <INFERENCE_HOST> 'mcporter call notion.notion-create-pages \
  "parent={\"data_source_id\":\"<NOTION_ID>\"}" \
  "pages=[{...}]"'
```

Page properties: `title`, `Category`, `Machine`, `date:Date:start`, `Summary`, `Source: "save"`.

Capture returned `id` and `url`. If Notion fails: continue (Obsidian already succeeded), but include 🚧 in confirmation. Update Obsidian frontmatter `notion_url:` with the URL via a follow-up `obsidian.write_file` call.

### 7. Store hAIveMind index entry

```bash
ssh <INFERENCE_HOST> 'mcporter call haivemind.store_memory \
  "category=<category>" \
  "content=[OBS-MEM] <Title>
Category: <category>
Tags: <tag1, tag2>
Machine: <machine>
Date: <YYYY-MM-DD>
Obsidian: <obsidian_subdir>/<slug>.md
Sensitive: <true|false>
Notion: <url or empty>
Summary: <summary>"'
```

### 8. Verify (mandatory before claiming success)

Round-trip read-back:

```bash
ssh <INFERENCE_HOST> 'mcporter call obsidian.read_text_file "path=<the path you just wrote>" "head=10"'
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<Title>" "limit=1"'
```

If either returns empty or different content from what was written, the write failed silently. Do NOT confirm to the user. Re-write and re-verify, or surface the failure.

### 9. Confirm

```
✅ Saved: **<Title>**
   → Obsidian: <subdir>/<slug>.md
   → Notion: <url>          ← only if notion_flag=true and succeeded
   → Vault only             ← only if sensitive
```

## Why mcporter on <INFERENCE_HOST>

- **Portability**: opencode, PI, and any host with SSH to <INFERENCE_HOST> uses the same path. No per-host MCP setup.
- **Single source of truth**: Obsidian filesystem, haivemind, and Notion auth all live on <INFERENCE_HOST>. mcporter is the unified frontend.
- **Notion auth**: the Notion remote MCP requires <USER_NAME>s authenticated session, which is on <INFERENCE_HOST>. Local `mcp__notion__*` requires per-page sharing in Notion's UI and 404s on most pages — never go that route. See memory `feedback_notion_via_mcporter`.

## Voice path (Jarvis)

Same flow, `source: voice`. Spoken confirmation: "Saved as *<title>*."

## Failure modes

| Symptom | What to do |
|---|---|
| `ssh: connect to host <INFERENCE_HOST>` fails | Confirm Tailscale up; try `ssh <TAILSCALE_IP>` or `ssh <PRIVATE_IP>`. If both fail, refuse to claim save success — buffer in temp and retry, or tell the user the save is queued/blocked. |
| `mcporter call obsidian.write_file` "Access denied: path not in allowed dirs" | Confirm path starts with `/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/`. The MCP only writes inside that root. |
| Heredoc / quoting fails on multi-line content | Write to `/tmp/save-content.md` first, then `scp` to <INFERENCE_HOST>, then `mcporter call obsidian.write_file "path=..." "content=$(cat /tmp/...)"`. Or pass via stdin if mcporter supports it. |
| haivemind store succeeds but search doesn't find it | Indexing lag — wait 30s and retry verification. Don't claim failure on first miss. |

## Project-local MEMORY.md

When running inside a project folder, /save ALSO appends a one-line entry to `./MEMORY.md` in the cwd. This is a purely local filesystem operation — no SSH, no mcporter. It is the always-available fallback for when Obsidian + hAIveMind are unreachable.

### Project detection (check in order, stop at first hit)

1. `.git/` directory exists in cwd
2. `CLAUDE.md` file exists in cwd
3. `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` exists in cwd
4. cwd path contains `/Dev/` or `/dev/` or `/Documents/Dev/`

If none match, skip the project-local step entirely.

### MEMORY.md format

Header (written once on first create):

```
# Project Memory

Local-first memory fallback. Authoritative copies in Obsidian + hAIveMind.
```

Each entry is a single line appended at the bottom:

```
- YYYY-MM-DD HH:MM | <category> | <title> — <one-line summary> [obsidian:<subdir>/<slug>.md] [hv:<memory_id>]
```

Example:

```
- 2026-05-10 14:32 | project | Telegram scraper infra — GCP prod, 17 realtime workers running [obsidian:project/telegram-scraper-infra.md] [hv:a1b2c3d4]
```

Rules:
- Append-only. Never rewrite or restructure the file.
- One line per entry, no multi-line content.
- `[obsidian:...]` and `[hv:...]` tokens are machine-parseable — keep them bracket-wrapped without spaces.
- Do NOT `.gitignore` this file. It should be committed so other agents on other machines see it.

### Write behavior

**Happy path** (Obsidian + hAIveMind both succeed — after steps 5–8):

1. Detect project (heuristic above). If not in a project, skip.
2. If `./MEMORY.md` does not exist, create it with the header above.
3. Append the one-line entry to the end of the file (standard `>>` append — no temp file needed for a single line).
4. If `./CLAUDE.md` exists in cwd AND does not already contain `@MEMORY.md`, append `@MEMORY.md` to it. Do NOT create `./CLAUDE.md` if it doesn't exist.
5. Add to confirmation: `✅ Saved: **<Title>** + appended to ./MEMORY.md`.

**Fallback path** (Obsidian AND hAIveMind both fail — `ssh <INFERENCE_HOST>` unreachable or both mcporter calls error):

1. Still write `./MEMORY.md` (same format, same append behavior). Use `[obsidian:PENDING]` and `[hv:PENDING]` as placeholders.
2. Surface a warning to the user:

   ```
   ⚠️  Obsidian + hAIveMind unreachable. Entry saved to ./MEMORY.md only.
       Authoritative save will need to be retried when <INFERENCE_HOST> is back online.
   ```

3. Do NOT claim the save succeeded to Obsidian/hAIveMind.

### Checkpoint mode in a project folder

When /save is in checkpoint mode (empty input) AND cwd is a project, bias the checkpoint summary toward work done in this project folder — cwd-scoped decisions, open items, file paths — rather than a generic session recap.

## Related skills

- `/load` — retrieve memories (also routes through mcporter on <INFERENCE_HOST>)
- `/handoff` — cross-session relay
- `/live` — Notion forensic case sync (uses same mcporter path)
