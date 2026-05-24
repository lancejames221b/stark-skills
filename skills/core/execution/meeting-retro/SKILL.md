---
name: meeting-retro
description: Retro a recorded meeting (transcript source = Notion page or local transcript file) to surface communication patterns, decision quality, follow-up clarity, and reusable lessons. Saves a single retro per meeting and supports a `patterns` cross-meeting synthesis. Invoke as /meeting-retro (latest), /meeting-retro <date or search query>, or /meeting-retro patterns.
category: execution
runtimes: [claude]
pii_safe: true
---

# meeting-retro

Turn each recorded meeting into a personal-leadership learning loop. Every retro captures what worked, what didn't, communication patterns, skeptic handling, decision quality, and follow-up clarity. Retros accumulate; the `patterns` subcommand surfaces recurring themes across all prior retros — that's the actual feedback loop.

## Required setup

- `TRANSCRIPT_SOURCE` — `notion` or `file` (which input mode to use)
- `RETRO_OUTPUT_DIR` — absolute path where individual retro markdown files are written (e.g., `<LOCAL_PATH>/retros/`)
- `RETRO_INDEX_FILE` — absolute path to a markdown index that gets a one-liner per retro (e.g., `<LOCAL_PATH>/retros/INDEX.md`)

## Optional providers

- **Notion as transcript source** — set `NOTION_DATABASE_ID` pointing at your meeting-notes data source. The skill uses `mcporter` over SSH to call `notion-search` and `notion-fetch include_transcript=true`. Set `MCPORTER_HOST_ALIAS=<HOST_ALIAS>` if mcporter is on another machine.
- **Local transcript files** — set `TRANSCRIPT_FILE_GLOB` (e.g., `<LOCAL_PATH>/transcripts/*.md`) if you record with Otter / Granola / a local recorder. The skill picks the most-recently-modified file matching the glob (or matches by date / substring).
- **Obsidian mirror** — set `OBSIDIAN_VAULT_PATH` to also write each retro into your vault (recommended if you use Obsidian as canonical memory).
- **Semantic memory index** — set `MEMORY_INDEX_PROVIDER=haivemind` (or another provider with a `store_memory` MCP tool) to index each retro for cross-meeting search. Without it, the `patterns` subcommand still works by filesystem-scanning `RETRO_OUTPUT_DIR`.
- **Review dashboard** — set `RETRO_DASHBOARD_PAGE_ID` if you want each retro also pushed as a sub-page under a Notion "Meeting Retros — Dashboard" parent for end-of-day scanning. Skip if you only want filesystem retros.

## When to invoke

- `/meeting-retro` — retro the most recent meeting from `TRANSCRIPT_SOURCE`
- `/meeting-retro <YYYY-MM-DD>` — retro a meeting from a specific date
- `/meeting-retro <substring>` — search the transcript source for a title matching the substring
- `/meeting-retro patterns` — read all prior retros and surface cross-meeting patterns
- Auto-invoke on user phrases: "retro this meeting", "what should I learn from that meeting", "help me improve as a manager after that call"

## Architecture

- **Transcript source**: Notion pages OR local files, controlled by `TRANSCRIPT_SOURCE`.
- **Retro storage**:
  - Filesystem (canonical): `<RETRO_OUTPUT_DIR>/meeting_retro_<YYYY-MM-DD>_<slug>.md`
  - Obsidian mirror (if `OBSIDIAN_VAULT_PATH` set): `<OBSIDIAN_VAULT_PATH>/meeting-retros/meeting_retro_<YYYY-MM-DD>_<slug>.md`
  - Semantic index (if `MEMORY_INDEX_PROVIDER` set): one entry per retro with tags `meeting-retro, executive, leadership, <topic>`
  - Index file: one-liner appended to `RETRO_INDEX_FILE`

## Flow

### 1. Resolve the target meeting

**No args / `/meeting-retro`:**
- `notion` source: `ssh <MCPORTER_HOST_ALIAS> 'mcporter call notion.notion-search "query=meeting" "query_type=internal"'`. Pick the page with timestamp closest to today AND the longest body. List the top 5 with timestamps if ambiguous.
- `file` source: pick the most-recently-modified file in `TRANSCRIPT_FILE_GLOB`.

**Date arg `/meeting-retro 2026-05-14`:**
- `notion`: search that date string. `file`: glob files matching the date.

**Substring arg `/meeting-retro <text>`:**
- Search the source for matching titles. Pick the best match.

**`patterns` arg:**
- Skip to step 6 — synthesize from existing retros, no new fetch.

### 2. Fetch the transcript

**Notion:**
```bash
ssh <MCPORTER_HOST_ALIAS> 'mcporter call notion.notion-fetch "id=<page-id>" "include_transcript=true"'
```
Save to `/tmp/meeting-transcript.txt`. Strip Notion footnote URLs and angle-bracket markup:
```python
import re
clean = re.sub(r'\[\^https://www\.notion\.so/[^\]]+\]', '', text)
clean = re.sub(r'<[^>]+>', '\n', clean)
```

**File:**
Read the file directly. Same cleanup if the format wraps tokens in angle brackets.

### 3. Extract meeting structure

Parse:
- **Title + date + attendees** (from page properties or filename + first lines)
- **Auto-generated summary** (if present)
- **Action items** (look for `### Action Items` or similar)
- **Decisions** (lines containing "agreed", "decided", "consensus", "will be")
- **Conflict points** ("skeptical", "but", "I disagree", "I don't", "pushed back")
- **Speaking patterns** (who pushed back, who endorsed, who was quiet)

### 4. Generate the retro

Each dimension gets a short observation grounded in transcript quotes:

1. **Communication quality** — clarity, analogies, over/under-explaining
2. **Skeptic handling** — pre-empt, redirect, get defensive?
3. **Stage-gating discipline** — on-roadmap vs concept; unintentional commitments?
4. **Audience read** — match audience level; know the decision-maker?
5. **Decision quality** — clear decisions; anything left dangling?
6. **Follow-up clarity** — owned + dated action items, or vague "team to figure out"?
7. **Time management** — drift; high-value sections rushed or skipped?
8. **What worked** — 1-3 quoted moments that landed well
9. **What to do differently next time** — 1-3 concrete patterns

Be honest. This is for improvement, not flattery. If something went poorly, say so plainly with evidence.

### 5. Save the retro

Slug: 2-4 word kebab-case from the meeting topic (e.g., `demo-prep`, `eng-weekly-feedback`).

Filename: `meeting_retro_<YYYY-MM-DD>_<slug>.md`.

Body:
```markdown
---
name: meeting-retro-<YYYY-MM-DD>-<slug>
description: One-line summary + top lesson
type: feedback
---

# Meeting Retro: <Title> — <YYYY-MM-DD>

**Attendees:** ...
**Source:** <notion URL or file path>

## What worked
- ...

## What to do differently
- ...

## Executive-leadership observations
1. Communication: ...
2. Skeptic handling: ...
3. Stage-gating: ...
4. Audience read: ...
5. Decision quality: ...
6. Follow-up clarity: ...
7. Time management: ...

## Quoted moments
- "<exact quote>" — <speaker>, <context>

## Action items I own
- [ ] ...

## Related retros
- [[meeting-retro-<prior-date>-<slug>]]

## Top lesson for next similar meeting
<ONE-LINE TAKEAWAY>
```

Write paths:
1. `<RETRO_OUTPUT_DIR>/meeting_retro_<YYYY-MM-DD>_<slug>.md` (canonical)
2. If `OBSIDIAN_VAULT_PATH`: also write to `<OBSIDIAN_VAULT_PATH>/meeting-retros/...`
3. If `MEMORY_INDEX_PROVIDER`: store via `mcp__<provider>__store_memory` with category=global, tags=[meeting-retro, executive, leadership, <topic>]
4. Append one-liner to `RETRO_INDEX_FILE`: `- [Meeting Retro <date> — <slug>](<path>) — <top lesson>`
5. If `RETRO_DASHBOARD_PAGE_ID`: create sub-page via `notion-create-pages` with the full retro markdown as body. Title: `<YYYY-MM-DD> — <Meeting title> — retro`.

### 6. Report back

Compact summary:

```
# Retro: <Meeting Title> — <date>

**Top 3 lessons:**
1. <strongest pattern>
2. <second>
3. <third>

**What worked:** <one quoted moment>

**What to fix next time:** <one specific action>

Full retro: <path>
```

End with: "Want cross-meeting patterns? Run `/meeting-retro patterns`."

## `patterns` subcommand

1. List all `meeting_retro_*.md` in `RETRO_OUTPUT_DIR` (and `OBSIDIAN_VAULT_PATH/meeting-retros/` if set).
2. Pull the "Executive-leadership observations" + "Top lesson" lines from each.
3. Cluster by dimension.
4. Surface repeats: same pattern in 3+ retros → real growth edge.
5. Output:
   - **Strengths** (consistently good across N retros)
   - **Growth edges** (repeats)
   - **One-off issues** (low signal)
   - **Recommended next focus** — pick ONE growth edge with a way to track progress
6. Save as `meeting_retro_patterns_<YYYY-MM-DD>.md` in `RETRO_OUTPUT_DIR` (so the meta-loop is itself retro-able).

## Hard rules

- **Be honest, not flattering.** Flattery breaks the feedback loop.
- **Quote the transcript** for claims. No paraphrase-passing-as-evidence.
- **Single dimension per observation.** Don't blend "communication AND audience read".
- **No vague advice.** "Be clearer" is useless. "Acknowledge AI limits in first 2 minutes when skeptics are present" is actionable.
- **Cross-link** related prior retros explicitly.
- **One retro per meeting.** Update in place if the slug already exists.

## Verification before claiming done

1. `ls <RETRO_OUTPUT_DIR>/meeting_retro_<...>.md` confirms the file exists.
2. If Obsidian mirror configured: confirm the write returned success.
3. If memory index configured: confirm the store call returned an ID.
4. Confirm `RETRO_INDEX_FILE` has the new line.

Report measured numbers (file size, memory id) — never quote unmeasured stats.

## Adapt to your toolchain

- Don't have Notion? Set `TRANSCRIPT_SOURCE=file` and point at local recorder output.
- Don't have a semantic index? The `patterns` subcommand reads the filesystem directly.
- Don't want a dashboard? Skip `RETRO_DASHBOARD_PAGE_ID` — filesystem retros are fully self-contained.
