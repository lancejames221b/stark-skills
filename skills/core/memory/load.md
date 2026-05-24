---
name: load
description: Load context from Obsidian memory + Notion (meetings, plans). Use when the user asks to "load", "retrieve", "recall", "check history", or "what do you know about X".
---

# Load Skill

> **Universal path: ALL backends are accessed via `ssh <INFERENCE_HOST> mcporter`. This works identically from claude-code, opencode, PI, and any host with SSH to <INFERENCE_HOST>. Don't use the local `mcp__*` tools — those are session-tied and not portable.**

Retrieve memories from Obsidian (internal brain) and Notion (meetings, plans, docs).

## Architecture

- **Obsidian** — canonical internal memory. Indexed in hAIveMind as `[OBS-MEM]` entries.
- **hAIveMind** — semantic search index over Obsidian. Holds `[OBS-MEM]` pointers + summaries. Hosted on <INFERENCE_HOST>.
- **Notion** — intake surface: meeting transcripts, plans opened on-screen, incoming docs. Searched via the official Notion remote MCP, accessed through <INFERENCE_HOST>.

All three are reachable via `mcporter` running on <INFERENCE_HOST>. There is exactly **one** path to invoke any of them:

```bash
ssh <INFERENCE_HOST> 'mcporter call <server>.<tool> "param1=value1" "param2=value2"'
```

Each parameter is a SEPARATE quoted arg — never query-string-encode them.

## Backends and tool names (mcporter)

| Server      | Key tools                                                       | Notes                                                                                            |
| ----------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `haivemind` | `search_memories`, `get_recent_memories`, `retrieve_memory`     | Semantic + chronological. `semantic=true` forces vector search; `semantic=false` forces keyword. |
| `obsidian`  | `read_file`, `read_text_file`, `search_files`, `list_directory` | Vault root: `/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/`                                           |
| `notion`    | `notion-search`, `notion-fetch`, `notion-query-meeting-notes`   | Pass `include_transcript=true` as a separate arg when fetching meeting pages.                    |

## Project-local MEMORY.md

`./MEMORY.md` is the always-available local fallback. It is a grep-friendly append-only file written by `/save`. Read it in two tiers:

### Tier 1 — project context prefix (always, when present)

Before calling mcporter, check for `./MEMORY.md` in cwd. No SSH needed — purely local read.

**Project detection (same heuristic as /save):**

1. `.git/` directory exists in cwd
2. `CLAUDE.md` file exists in cwd
3. `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` exists in cwd
4. cwd path contains `/Dev/` or `/dev/` or `/Documents/Dev/`

If cwd is a project AND `./MEMORY.md` exists:

1. Read the file. The entries are one-liners: `- YYYY-MM-DD HH:MM | category | title — summary [obsidian:...] [hv:...]`
2. If the user's query is non-empty, grep for the query terms (case-insensitive) and surface matching lines. If empty query, show the 5 most recent lines (last 5 lines of the file).
3. Display as `[Project: <basename>]` tier ABOVE all Obsidian/Notion results:

```
[Project: <basename>]
- 2026-05-10 14:32 | project | Title — summary [obsidian:project/file.md] [hv:uuid]
...

--- (Obsidian / Notion results below) ---
```

If `./MEMORY.md` does not exist or cwd is not a project, skip silently and proceed to mcporter.

### Tier 2 — primary source when haivemind + Obsidian are both unreachable

If `ssh <INFERENCE_HOST>` fails (both IP variants) AND `./MEMORY.md` exists:

1. Read the entire `./MEMORY.md`.
2. If the user provided a query, grep for matching lines. If empty, show all lines in reverse order (most recent first).
3. Display as `[Project Memory — OFFLINE MODE]` with a header warning:

```
⚠️  Obsidian + hAIveMind unreachable (<INFERENCE_HOST> offline). Showing local MEMORY.md only.
    Results may be incomplete — authoritative index is on <INFERENCE_HOST>.

[Project Memory — OFFLINE MODE: <basename>]
<matching or all lines>
```

4. Do NOT attempt mcporter calls. Return immediately after showing MEMORY.md content.

If `./MEMORY.md` also does not exist in offline mode, tell the user: "<INFERENCE_HOST> is offline and no local MEMORY.md exists in this project. No memory available."

## Flow

### 1. Parse input

- **Empty input** → `mcporter call haivemind.get_recent_memories "limit=5"`, skip Notion, show recent items.
- **`#category` prefix** → category filter (applies to haivemind only; strip from query).
- **Temporal keywords** (`today`, `yesterday`, `last week`, explicit dates) → append date to query.
- **Remainder** → query string.

### 2. Search in parallel — three calls, one message

To avoid the keyword-vs-semantic miss (e.g. "telegram scraper" missed when haivemind defaults to keyword), force BOTH modes on haivemind, plus Notion. Each call goes via `ssh <INFERENCE_HOST> mcporter` and they run concurrently.

**A — haivemind semantic (forced):**

```bash
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<user query>" "semantic=true" "limit=8" "category=<filter or omit>"'
```

**B — haivemind keyword (forced):**

```bash
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<user query>" "semantic=false" "limit=8" "category=<filter or omit>"'
```

**C — Notion search:**

```bash
ssh <INFERENCE_HOST> 'mcporter call notion.notion-search "query=<user query>" "query_type=internal"'
```

If on a host where the local `mcp__haivemind__search_memories` tool is loaded and you need the absolute fastest local-call path, you may use it as an alternative to call A — but ONLY after confirming the mcporter+ssh path is reachable. The mcporter path is always correct; local MCP is a same-machine optimization for claude-code only.

### 3. Merge and deduplicate

For each haivemind result: key = `obsidian_path` (or `Obsidian:` field from `[OBS-MEM]` body, else memory ID).
For each Notion result: key = `HV-ID` property if set, otherwise Notion page ID.

Track which sources hit each key. Tier and label:

- Found by both haivemind:semantic AND haivemind:keyword → `[Obsidian]` (high confidence — multi-mode hit)
- haivemind:semantic only → `[Obsidian:hv-semantic]`
- haivemind:keyword only → `[Obsidian:hv-keyword]` — surface these; they're saves the embedding index missed
- Same Obsidian key + Notion → `[Obsidian+Notion]`
- Notion only → `[Notion]`

Rank: prefer multi-mode hits, then any single-mode hit (preserve each backend's relevance score), then Notion-only. Show up to 10 total.

### 4. Display results

```
1. [Obsidian] <Title>  (<category>, <date>)
   <summary>
   → <LOCAL_PATH>/obsidian/<path>

2. [Notion] <Title>  (<database name>, <date>)
   <summary>
   → <notion_url>

3. [Obsidian+Notion] <Title>  (<category>, <date>)
   <summary>
   → Obsidian: <path>  |  Notion: <url>
```

Show up to 10 results total (haivemind + Notion combined, ranked by relevance).

### 5. Fetch details on demand

When the user asks for details on a result, use mcporter:

- `[Obsidian]` → `ssh <INFERENCE_HOST> 'mcporter call obsidian.read_text_file "path=/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/<path>"'`
- `[Notion]` → `ssh <INFERENCE_HOST> 'mcporter call notion.notion-fetch "id=<page URL or UUID>" "include_transcript=true" "include_discussions=true"'`
- `[Obsidian+Notion]` → prefer Obsidian (source of truth); Notion for context

Summarize the content — don't dump the full page. Extract decisions, action items, key context.

## Why mcporter on <INFERENCE_HOST>

- **Portability**: opencode, PI, and any host with SSH to <INFERENCE_HOST> gets the same memory access. No per-host MCP setup.
- **Notion access**: the Notion remote MCP requires <USER_NAME>'s authenticated session, which lives on <INFERENCE_HOST>. Local `mcp__notion__*` requires per-page sharing in Notion's UI and 404s on most pages — never go that route. See memory `feedback_notion_via_mcporter`.
- **Single source of truth**: haivemind, the Obsidian filesystem, and Notion auth all live on <INFERENCE_HOST>. mcporter is the unified frontend.

## Voice path (Jarvis)

Same mcporter path. Prefer haivemind summary text — don't fetch full files unless user asks for "details". Max 3 results, one or two sentences each.

## Failure modes

| Symptom                                                                     | What to do                                                                                                                                                                                                           |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ssh: connect to host <INFERENCE_HOST>` fails                                        | Confirm Tailscale up; try `ssh <HOST_ALIAS>` or `ssh <PRIVATE_IP>` directly. If both fail, <INFERENCE_HOST> is offline — activate Tier 2: read `./MEMORY.md` as primary source (see "Project-local MEMORY.md" section above). |
| `mcporter call notion.*` returns "URL type webpage not currently supported" | You appended args to the URL string (`?id=X&include_transcript=true`). Each param must be a SEPARATE quoted arg.                                                                                                     |
| `mcporter call notion.notion-fetch` returns "Transcript omitted"            | Add `include_transcript=true` as a separate arg.                                                                                                                                                                     |
| Empty result on a query that should match                                   | Force the OTHER haivemind mode (semantic ↔ keyword). The two indexes catch different things.                                                                                                                         |

## Related skills

- `/save` — store a new memory (also routes through mcporter)
- `/handoff` — cross-session relay
- `/live` — Notion forensic case sync (uses same mcporter path)
