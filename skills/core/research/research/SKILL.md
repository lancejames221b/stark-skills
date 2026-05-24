---
name: research
description: Deep research skill. Triggers on /research [topic], "research [topic]", "look into [topic]", "do research on [topic]", or when /live plan needs research before planning. Uses sonnet-high by default; switches to opus-high when <USER_NAME>says "opus", "deep", or "exhaustive". Combines web search, content extraction, source verification, and synthesis into a structured report. Posts executive summary to Discord and full report to file.
category: research
runtimes: [claude]
pii_safe: true
---

# /research — Deep Research Skill

## Model Selection (MANDATORY — check first)

| Trigger | Model |
|---------|-------|
| Default | `sonnet-high` (max-high/claude-sonnet-4-6) |
| "opus", "deep", "exhaustive", "go deep" | `opus-high` (max-high/claude-opus-4-6) |

Announce model choice before starting: "Researching [topic] with sonnet-high…" or "Going deep with opus-high…"

## Invocation Forms

| What <USER_NAME>says | Behavior |
|----------------|----------|
| `/research [topic]` | Research topic, post results |
| `/research opus [topic]` | Research with opus-high |
| `research [topic]` | Same as /research |
| `look into [topic]` | Same |
| `/live plan` → needs research phase | Auto-trigger research before planning |

## Workflow

### Phase 1: Scope (fast, 1-2 searches)
1. Run 1-2 broad searches to map the landscape
2. Identify: key concepts, major sources, sub-questions to answer
3. If scope is ambiguous: ask ONE clarifying question before proceeding

### Phase 2: Deep Dive (3-6 targeted searches + fetches)
1. Targeted `web_search` for each sub-question
2. `web_fetch` for top 2-3 sources per sub-question
3. **If `web_fetch` returns empty/truncated content** (JS-heavy pages, SPAs): use Linux Playwright to get fully rendered content — see `skills/browser-test/SKILL.md`
4. Extract key claims, data points, dates, conflicts
5. Track source credibility (primary > secondary, authoritative > anonymous)

### Phase 3: Synthesis
1. Cross-reference claims across sources
2. Identify consensus, contradictions, gaps
3. Assign confidence levels: **High** (multiple authoritative sources), **Medium** (one good source), **Low** (single/uncertain source)

### Phase 4: Report
Write full report to `<LOCAL_PATH>/dev/tmp/results/research-[slug]-[YYYYMMDD-HHmm].md`

### Phase 5: Notion Page (MANDATORY)
Create a Notion page for every research run using the `notion-oauth` MCP server.

```bash
<LOCAL_PATH>/dev/skills/notion-oauth/create-page.sh "Research: [Topic] — YYYY-MM-DD" "<NOTION_PAGE_ID>" /path/to/report.md
```

- Parent: **Research** hub page (`<NOTION_PAGE_ID>`) — https://www.notion.so/<NOTION_PAGE_ID>
- Use the wrapper script (mcporter CLI cannot pass nested JSON reliably)
- Pass the already-written report .md file as the content argument
- Title format: `Research: [Topic] — YYYY-MM-DD`
- Content: full report (same as the .md file)
- Capture the returned page URL

Post executive summary to Discord (under 1800 chars):
```
🔬 **Research: [Topic]**
**Model:** [sonnet-high / opus-high]

**TL;DR:** [2-3 sentences]

**Key Findings:**
• [finding 1] — [confidence]
• [finding 2] — [confidence]
• [finding 3] — [confidence]

**Sources:** [N] sources checked
**Notion:** [page URL]
**Full report:** `tmp/results/research-[slug]-[timestamp].md`
```

## /live plan Integration

When `/live plan` is invoked and the directive requires research before planning:
1. Auto-trigger `/research [directive topic]` first
2. Use research output as context for ticket generation
3. Reference research file in the plan's Notion page

**Trigger condition:** Directive contains unknown technology, competitor analysis, architectural decisions, or "research first" language.

**In /live plan model table**, add:
- Pre-planning research phase → `sonnet-high` (or `opus-high` if user said opus)

## Output File Format

```markdown
# Research: [Topic]
**Date:** [ISO]  **Model:** [model]  **Sources:** [N]

## TL;DR
[2-3 sentences]

## Key Findings
### [Theme 1]
[findings with inline citations]

### [Theme 2]
...

## Source Assessment
| Source | Authority | Freshness | Used For |
|--------|-----------|-----------|----------|

## Contradictions / Open Questions
[anything unresolved]

## Confidence Map
- [claim] → High/Medium/Low
```

## Rules
- Always search hAIveMind first: `mcporter call haivemind.search_memories query="research [topic]" limit=5` — avoid re-researching what's already known
- Store completed research: `mcporter call haivemind.store_memory content="RESEARCH [topic] [date]: [tldr] | file=[path] | notion=[url]" category="global"`
- Max 8 web_search calls + 6 web_fetch calls per research run — don't over-search
- Never assert facts without source attribution
- If running as sub-agent: post results back to originating channel per `skills/subagent-result-posting/SKILL.md`
