---
description: "Recall remembered decisions/rules. Usage: /recall <search term or topic>"
argument-hint: "Search term or topic to recall"
tools: ["mcp__haivemind__search_memories", "mcp__notion__notion-fetch"]
---

Recall remembered decisions, rules, and resolved issues. Arguments: $ARGUMENTS

This is `/load` scoped to category = `important` (and optionally tags `decision` / `rule`). It also checks local `./CLAUDE.md` for remembered entries.

## Architecture

Remembered items live in Notion database `<NOTION_ID>`, indexed in hAIveMind as `[NOTION-MEM]` entries with category = `important`. Fetch Notion pages on demand for full detail.

## Search

1. **hAIveMind first** — `mcp__haivemind__search_memories` with:
   - Query: `[NOTION-MEM] <user's query>`
   - Category filter: `important`
   - Limit: 10

2. **Local CLAUDE.md** — if `./CLAUDE.md` exists, grep for the query terms in `## Remembered:` sections. Surface any matches alongside Notion results.

3. **Legacy fallback** — if fewer than 3 Notion-backed results, also search hAIveMind categories `rules` and `security` without the `[NOTION-MEM]` prefix to catch pre-migration entries.

## Display

Sort by relevance, then date (recent first). Show:

```
1. 📌 <Title> — <YYYY-MM-DD> (<tags>)
   <summary>
   → <notion_url>
```

For CLAUDE.md-only matches:
```
📄 (local CLAUDE.md) <Title> — <YYYY-MM-DD>
   <summary>
```

## Fetch details

If the user asks for more detail on a specific entry, or the query has a single strong match:
- `ToolSearch select:mcp__notion__notion-fetch`
- Fetch the Notion page and summarize: problem, decision, prevention/rule.

Default to compact list. Show 5-10 results max.

## Empty state

If nothing matches, say so clearly. Offer to broaden the search (e.g., drop category filter, search last 30 days).
