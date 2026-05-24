---
description: "Search memory across Obsidian + hAIveMind (+ Notion). Usage: /load [#category] <query> [today|yesterday|date]"
---

Search memory. Arguments: $ARGUMENTS

> **Universal path: ALL backends are accessed via `ssh <INFERENCE_HOST> mcporter`. Same pattern as /save.**

## Architecture

- **Obsidian** = canonical internal memory at `/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/`. Indexed in hAIveMind as `[OBS-MEM]` entries.
- **hAIveMind** = semantic search index over Obsidian. Holds `[OBS-MEM]` pointers + summaries.
- **Notion** = intake surface (meetings, plans, deliverables). Searched directly when relevant.

Search both in parallel. Merge with source labels.

## Parsing $ARGUMENTS

- Empty → `haivemind.get_recent_memories` limit 5, skip Notion search.
- `#word` prefix → category filter (applies to hAIveMind).
- Temporal keywords (`today`, `yesterday`, `last week`, explicit dates `2026-05-08` / `5/8` / `May 8`) → resolve to `YYYY-MM-DD` and append `[YYYY-MM-DD]` to the query so timestamped entries surface.
- Remainder → query string.

## Search — three calls in parallel (one message)

```bash
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<query>" "semantic=true"  "limit=8"' &
ssh <INFERENCE_HOST> 'mcporter call haivemind.search_memories "query=<query>" "semantic=false" "limit=8"' &
ssh <INFERENCE_HOST> 'mcporter call notion.notion-search       "query=<query>" "query_type=internal"' &
wait
```

`semantic=true` forces vector/embedding search — catches paraphrases. `semantic=false` forces keyword/chronological — catches exact phrase matches and recent timestamps. Both are needed; relying on one mode misses memories.

## Merge & dedupe

For each hAIveMind result: key = `obsidian_path` (or `Obsidian:` field from `[OBS-MEM]` body, else memory ID).
For each Notion result: key = `HV-ID` property if set, else page ID.

Tier and label:

| Hits | Label |
|---|---|
| Both hAIveMind modes (semantic AND keyword) | `[Obsidian]` (high confidence) |
| Semantic only | `[Obsidian:semantic]` |
| Keyword only | `[Obsidian:keyword]` (recent saves the embedding hasn't ranked yet — surface them) |
| Same key + Notion | `[Obsidian+Notion]` |
| Notion only | `[Notion]` |

Rank: multi-mode hits first, then single-mode (preserve relevance score), then Notion-only. Show up to 10.

## Display

```
1. [Obsidian] <Title>  (<category>, <date>)
   <summary>
   → <obsidian_path>

2. [Notion] <Title>  (<database>, <date>)
   <summary>
   → <notion_url>

3. [Obsidian+Notion] <Title>  (<category>, <date>)
   <summary>
   → Obsidian: <path>  |  Notion: <url>
```

## Fetch details on demand

When user asks for details on a result:

```bash
# Obsidian
ssh <INFERENCE_HOST> 'mcporter call obsidian.read_text_file "path=/media/<INFERENCE_HOST>/storage1/Obsidian/Claude/<path>"'

# Notion
ssh <INFERENCE_HOST> 'mcporter call notion.notion-fetch "id=<url-or-uuid>" "include_transcript=true" "include_discussions=true"'
```

For meeting-notes pages ALWAYS include `include_transcript=true` — without it the response says "Transcript omitted" and you get nothing.

For `[Obsidian+Notion]` results, prefer the Obsidian file (source of truth); use Notion only for transcript/comments.

Summarize the content — don't dump the raw page. Pull out decisions, action items, open questions.

## Project-local MEMORY.md

`./MEMORY.md` is the always-available local fallback — no SSH needed. Entries are one-liners written by `/save`:
`- YYYY-MM-DD HH:MM | category | title — summary [obsidian:...] [hv:...]`

### Project detection (same as /save)

1. `.git/` in cwd
2. `CLAUDE.md` in cwd
3. `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` in cwd
4. cwd path contains `/Dev/` or `/dev/` or `/Documents/Dev/`

### Tier 1 — project context prefix (when mcporter reachable)

Before calling mcporter, check for `./MEMORY.md`. If present and cwd is a project:

- Grep lines matching the query (case-insensitive). If empty query, show last 5 lines.
- Display as `[Project: <basename>]` tier ABOVE all Obsidian/Notion results.
- Proceed to mcporter as normal.

### Tier 2 — primary source (when <INFERENCE_HOST> offline)

If `ssh <INFERENCE_HOST>` fails (both IPs), activate offline mode:

1. Read `./MEMORY.md` entirely. Grep for query terms; if empty query show all lines reversed.
2. Display with header: `⚠️ Obsidian + hAIveMind unreachable. Showing local MEMORY.md only.`
3. Skip mcporter calls entirely. If `./MEMORY.md` also missing: tell user "<INFERENCE_HOST> offline and no local MEMORY.md."

## Failure modes

- `ssh <INFERENCE_HOST>` unreachable → activate Tier 2 MEMORY.md fallback (see above).
- Notion search 401/auth fail → continue with hAIveMind results only; mention Notion was unreachable.
- Empty results across all three → before declaring "nothing found", retry once with `semantic=true` only and a broader query (drop category filter).
