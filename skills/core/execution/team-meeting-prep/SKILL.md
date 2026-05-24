---
name: team-meeting-prep
description: Prep a recurring team meeting by pulling email, meeting-notes, ticketing-board, and project-board signals into a single Last Week / This Week / Blockers brief. Creates a notes page and opens it on your primary screen. Trigger phrases — "/team-meeting-prep", "team meeting prep", "prep the meeting", "prep for meeting".
category: execution
runtimes: [claude]
pii_safe: true
---

# team-meeting-prep

Generic recurring-team-meeting prep. The skill aggregates four signal streams into a structured brief: **World View** (leadership/customer email), **Last Week** (what shipped), **This Week** (what's planned/in-flight), **Blockers** (what is stuck). It writes the brief to a notes page and opens it on your screen.

The original implementation targeted a weekly engineering team meeting; the template parameterizes every provider so any cadence and toolchain works.

## Required setup

These environment variables MUST be set for the skill to function at all:

- `TEAM_NAME` — name used in the brief title and prompts (e.g., `Engineering`, `Leadership Sync`)
- `MEETING_CADENCE` — human-readable cadence (e.g., `Mondays 2:00pm`, `Biweekly Friday 9am`)
- `MEETING_TIMEZONE` — IANA TZ string for date math (e.g., `America/New_York`)
- `BRIEF_OUTPUT_TARGET` — where to write the brief: `notion`, `gdocs`, or `markdown_file`

The skill produces a brief regardless of which providers are configured below; missing providers degrade gracefully with a note in the relevant section ("No signal from X").

## Optional providers

Each integration is opt-in. The skill checks for the env var; if absent, it skips that section and notes the gap rather than failing.

- **Gmail (leadership/customer email)** — set `EMAIL_PROVIDER=gmail` and `LEADERSHIP_EMAIL` (the email address whose threads you summarize for the World View section). Auth via the Google Workspace MCP using `GOOGLE_WORKSPACE_USER`.
- **Notion (meeting-notes search + brief output target)** — set `NOTION_DATABASE_ID` (meeting-notes data source) and route Notion calls via `mcporter` on `<HOST_ALIAS>` if you use the mcporter fan-out pattern (see the `mcporter` integration skill).
- **Trello (project board)** — set `TRELLO_BOARD_ID` and map list IDs by purpose: `TRELLO_SHIPPED_LIST_ID`, `TRELLO_BLOCKED_LIST_ID`, `TRELLO_NEXT_LIST_ID`, `TRELLO_DECISIONS_LIST_ID`. Each list maps 1:1 to a brief section.
- **Linear (ticketing)** — set `LINEAR_API_KEY` (read-only OK). The skill queries your assigned in-progress + recently completed + blocked tickets.
- **Slack/Discord (channel digest)** — set `SLACK_CHANNEL_ID` or `DISCORD_CHANNEL_ID` if you want a short channel-summary section. Optional.
- **Open-on-screen** — set `SCREEN_HOST_ALIAS` (defaults to local) to auto-open the brief in a browser tab on your primary screen after creation.

If `BRIEF_OUTPUT_TARGET=notion` and `NOTION_DATABASE_ID` is unset, the skill falls back to `markdown_file` and writes to `./team-meeting-prep-<DATE>.md` so a brief always lands somewhere.

## When to invoke

Trigger phrases: `/team-meeting-prep`, "team meeting prep", "prep the meeting", "prep for the sync", "<TEAM_NAME> meeting prep".

## What it builds

A structured brief with four sections:

1. **World View** — summary of recent email threads with `LEADERSHIP_EMAIL` (default window: last 7 days)
2. **Last Week** — what shipped, decisions made (Trello "shipped" list + Linear completed tickets + Notion meeting-notes action items marked done)
3. **This Week** — in-flight Trello "next" cards + Linear in-progress tickets
4. **Blockers** — Trello "blocked" + Trello "needs decision" + Linear blocked tickets + open asks from the email thread

## Data pulls (parallel)

Run all configured pulls in parallel. Skip and note any provider whose env vars are absent.

### A — Email (Gmail)

```
mcp__google-workspace__search_gmail_messages(
  user_google_email: "<GOOGLE_WORKSPACE_USER>",
  query: "from:<LEADERSHIP_EMAIL> OR to:<LEADERSHIP_EMAIL> after:YYYY/MM/DD",
  max_results: 10
)
```

Compute the date 7 days ago: `date -d '7 days ago' '+%Y/%m/%d'` (Linux) or `date -v-7d '+%Y/%m/%d'` (macOS).

For each result fetch the full thread via `get_gmail_thread_content`. Summarize key asks, decisions, and open items. If no results, note "No emails from `<LEADERSHIP_EMAIL>` in the past 7 days."

### B — Notion meeting notes

```bash
ssh <HOST_ALIAS> 'mcporter call notion.notion-search "query=<TEAM_NAME>" "query_type=internal"'
```

Fetch each result with `include_transcript=true`:
```bash
ssh <HOST_ALIAS> 'mcporter call notion.notion-fetch "id=<page_url_or_id>" "include_transcript=true"'
```

Extract decisions made, action items, open questions. Only pull notes from the last 14 days.

### C — Trello

```
mcp__trello__get_cards(list_id: "<TRELLO_SHIPPED_LIST_ID>")     # Last Week
mcp__trello__get_cards(list_id: "<TRELLO_BLOCKED_LIST_ID>")     # Blockers
mcp__trello__get_cards(list_id: "<TRELLO_NEXT_LIST_ID>")        # This Week
mcp__trello__get_cards(list_id: "<TRELLO_DECISIONS_LIST_ID>")   # Blockers (decisions)
```

### D — Linear tickets

Endpoint: `https://api.linear.app/graphql`. Auth: `Authorization: <LINEAR_API_KEY>`.

In-progress + recently completed (last 14 days):

```graphql
{
  viewer {
    assignedIssues(filter: {
      state: { type: { in: ["started", "completed"] } }
      updatedAt: { gt: "LAST_14_DAYS_ISO" }
    }) {
      nodes { title state { name } priority identifier updatedAt team { name } url }
    }
  }
}
```

Blocked:

```graphql
{
  viewer {
    assignedIssues(filter: { state: { name: { eq: "Blocked" } } }) {
      nodes { title identifier priority url }
    }
  }
}
```

If `LINEAR_API_KEY` is unset, skip with a note in the brief.

## Synthesis

Assemble the brief:

```markdown
# <TEAM_NAME> Meeting Prep — [DATE]

**Prepared**: [timestamp]

---

## World View

*Context from <LEADERSHIP_EMAIL> (last 7 days):*
- [bullet from email thread]
- [or: No emails in the past 7 days]

---

## Last Week

**Shipped:**
- [from Trello shipped list]
- [from Linear completed tickets]
- [from meeting-notes action items marked done]

**Key decisions:**
- [from meeting notes]

---

## This Week

**In flight:**
- [from Trello next list]
- [from Linear in-progress tickets with priority/team]

**Planned:**
- [from meeting notes]

---

## Blockers

- [from Trello blocked list]
- [from Trello decisions list]
- [from Linear blocked tickets]
- [open asks from email]

---

## References
- Trello board: https://trello.com/b/<TRELLO_BOARD_ID>
- Linear: https://linear.app/<ORG_NAME>
```

## Output

### If `BRIEF_OUTPUT_TARGET=notion`

```bash
ssh <HOST_ALIAS> 'mcporter call notion.notion-create-pages \
  "parent={\"data_source_id\":\"<NOTION_DATABASE_ID>\"}" \
  "pages=[{\"title\":\"<TEAM_NAME> Meeting Prep — [DATE]\",\"Summary\":\"Last week / this week / blockers brief\"}]"'
```

Capture the returned page ID + URL, then write the brief body via `batch_update_doc` or `insert_doc_elements`.

### If `BRIEF_OUTPUT_TARGET=gdocs`

```
mcp__google-workspace__create_doc(
  user_google_email: "<GOOGLE_WORKSPACE_USER>",
  title: "<TEAM_NAME> Meeting Prep — [DATE]"
)
```

Insert the brief, capture the doc URL.

### If `BRIEF_OUTPUT_TARGET=markdown_file`

Write to `./team-meeting-prep-<DATE>.md`. Print the path.

### Open on screen

If `SCREEN_HOST_ALIAS` is set:
```bash
ssh <SCREEN_HOST_ALIAS> 'open "<page_or_doc_url>"'
```
Otherwise: print the URL and let the user open it.

## Final output to user

```
Team Meeting Prep — <TEAM_NAME> — [DATE]
   • Brief: <url_or_path>
   • Email summary: <N found / none>
   • Trello: <N shipped> shipped, <N blocked> blocked, <N next> this week
   • Linear: <N in-progress>, <N blocked>
   • Opened on: <SCREEN_HOST_ALIAS or local>
```

## Notes

- If a configured provider fails, skip and note in the brief — don't abort
- Default window: last 7 days (last week), no date filter (this week)
- The Trello list-to-section mapping is 1:1 — trust the configured list IDs
- Use `mcporter` for Notion if local `mcp__notion__*` tools fail with 404 (per-page sharing requirement)

## Adapt to your toolchain

The skill assumes "email + meeting-notes + ticket-board + project-board" because that's the dominant signal pattern for recurring team syncs. Substitutions are straightforward:

- Replace Trello with GitHub Projects: pull issues by label
- Replace Linear with Jira: pull issues by assignee + status
- Replace Notion with Confluence: search by space + title
- Replace Gmail with IMAP or Outlook: same query shape

Keep the four-section brief structure — it's the contract with your team, not a tool dependency.
