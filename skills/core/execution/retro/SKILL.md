---
name: retro
description: Host or co-pilot a recurring team retrospective. Reads the retro doc, runs the writing timer, parses & ranks votes, highlights the active topic, captures action items, and writes deltas back. Triggers on "retro", "retrospective", "it's retro time", or any request to read, analyze, or highlight the retro doc.
category: execution
runtimes: [claude]
pii_safe: true
---

# retro

A team retrospective co-pilot. Walks the host through the meeting format, runs the silent-writing timer, parses and ranks votes after writing time, highlights the active topic in the doc, captures action items, and appends deltas back to the doc.

This is a generic implementation of the **vote-and-discuss retro format** — Mad/Sad/Glad, Start/Stop/Continue, or 😀/😞/👀/🔺 all map to the same flow. The skill is tool-bound to Google Docs because that's the dominant live-collab surface; the four-section vote-and-discuss pattern is the actual contract.

## Required setup

- `RETRO_DOC_ID` — Google Doc ID for the rolling retro doc (one doc with a new `--- TAB:` per session)
- `RETRO_TEAM_NAME` — used in prompts and the action-item formatter (e.g., `Engineering`, `Product`)
- `RETRO_CADENCE` — human-readable cadence (e.g., `Biweekly Friday 12pm`, `Weekly Tuesday`)
- `GOOGLE_WORKSPACE_USER` — Google account used for Google Docs MCP calls
- `RETRO_SECTIONS` — comma-separated section labels in the doc (default: `What worked,What didn't work,Observations,Deltas`). The skill parses these as the vote categories.

## Optional providers

- **Host guide page** — set `RETRO_HOST_GUIDE_URL` (Notion or any URL) for the skill to fetch and surface the format reference for new hosts.
- **Action-item destination** — set `ACTION_ITEM_TARGET=notion` and `NOTION_DATABASE_ID` if action items should be created as Notion DB rows in addition to being written to the Deltas section. Default behavior: write deltas only to the Google Doc.
- **Live transcript integration** — set `LIVE_TRANSCRIPT_SOURCE=notion` and `NOTION_DATABASE_ID` to allow `/live` invocations to pull a transcript page and append its action items as deltas.
- **Timer mechanism** — set `TIMER_PROVIDER=schedule_wakeup` (default) or `TIMER_PROVIDER=manual` if you prefer the host calls time manually. Without scheduling, the skill prompts the host to say "time's up" themselves.

## Key resources

- **Google Doc:** `<RETRO_DOC_ID>`
- **Host guide:** `<RETRO_HOST_GUIDE_URL>` (if set)
- **Email:** `<GOOGLE_WORKSPACE_USER>`
- **Cadence:** `<RETRO_CADENCE>`

## Step 1 — On invoke

Load two things in parallel:
1. `get_doc_content` on the Google Doc — find the last `--- TAB:` section, note its `(ID: t.xxxxxxx)` — that's the current tab
2. If `RETRO_HOST_GUIDE_URL` set, fetch it so the format is ready

Then walk the host through the meeting format (welcome → writing → voting → discussion → action items → close). **Do NOT parse or rank items yet.** Just be ready.

## Step 2 — Writing timer

When the host says anything like *"I'll give you guys 5 minutes"* or *"5 minutes to write"*:
- Confirm: "Starting 5-minute writing timer"
- If `TIMER_PROVIDER=schedule_wakeup`: use `ScheduleWakeup` with `delaySeconds: 300`
- When it fires: call out time is up, go to Step 3
- If `TIMER_PROVIDER=manual`: wait for the host to say "time's up"

## Step 3 — After writing time: parse & rank

`get_doc_content` again (fresh read), then `inspect_doc_structure` on current tab (`detailed: true`) for all character indices.

Parse the `RETRO_SECTIONS` (default 4), count `+1`s per item, rank by most → least votes.

Report the ranked agenda to the host in one tight message. Then **highlight the #1 item** in yellow (`#FFFF00`) in the doc.

## Step 4 — Navigating topics

Listen for voice cues like *"next", "okay next one", "let's move on", "moving on"*:
1. Clear current highlight (set `background_color: "#FFFFFF"`, NOT null — null throws)
2. Brief the host on the next item (1–2 sentences: what it is, why it matters, any pattern from past retros)
3. Highlight the next item yellow

Repeat until all items are covered.

## Step 5 — Action items

As the host calls out action items during discussion, capture them. Format: `[ ] [Person] to [action]` — always a named owner.

When the host says *"let's review action items"*: read back everything captured.

If `ACTION_ITEM_TARGET=notion`: also create a row in `NOTION_DATABASE_ID` for each item (title, owner, due-date if mentioned).

## Highlighting

Always use `inspect_doc_structure` (`detailed: true`) for exact indices first. Then:

```json
{
  "type": "format_text",
  "start_index": <n>,
  "end_index": <m>,
  "background_color": "#FFFF00",
  "tab_id": "<current_tab_id>"
}
```

To clear: use `"background_color": "#FFFFFF"`. Do NOT use `null`, it throws.

## Writing deltas to the doc

After each topic resolves, append action items to the Deltas section (last entry in `RETRO_SECTIONS`) using `insert_text` at the index just before the trailing newline. Format:

```
[Person] to [action]
```

Get the exact insert index from `inspect_doc_structure` — find the paragraph after the Deltas heading and insert there.

## `/live` transcript integration

When the host invokes `/live` and provides a Notion page URL with an incoming transcript (requires `LIVE_TRANSCRIPT_SOURCE=notion`):
1. Fetch the Notion page
2. Extract action items / decisions from the transcript
3. Append them as deltas to the Deltas section
4. Confirm back to the host what was captured

## Meeting format (reference)

| Phase | Time | What |
|-------|------|------|
| Welcome | 2 min | Attendance, note absences |
| Writing | 5 min | Silent — everyone adds items |
| Voting | 3 min | +1s on topics |
| Discussion | 35–40 min | Most → least votes |
| Action item review | 5 min | Read back all, confirm owners |
| Close | 2 min | Anything missed? Confirm next date |

## Doc structure per tab

The default `RETRO_SECTIONS` maps to:
- **What worked** — positives
- **What didn't work** — pain points
- **Observations** — neutral
- **Deltas** — action items

You can substitute any other 3-or-4-section vote framework by changing `RETRO_SECTIONS`.

## Common patterns (for topic briefs)

- Shadow work / DMs disrupting focus → proper channels
- Deployment gaps → checklists, staging
- Observability wins
- "No surprises" — communicate process exceptions in advance
- Tooling-adoption friction

## Adapt to your toolchain

- Replace Google Docs with a wiki page: still works if it supports range-highlight + append. Replace `format_text` and `insert_text` MCP calls with your wiki's equivalents.
- Replace the timer with a physical kitchen timer if you have no scheduler — the skill still drives parse-and-rank correctly when you say "time's up".
- The four-section vote+discuss flow is the actual skill. Everything else is plumbing.
