---
name: world-view
description: Aggregate a read-only snapshot of your world across configured providers (email, chat, notes, project boards, code-hosting, memory). Surfaces action items, active projects, blockers, and recent context in one view. Each provider is opt-in via env vars.
category: execution
runtimes: [claude]
pii_safe: true
---

# world-view

Produces a comprehensive, read-only snapshot of your current world by pulling from a configurable set of providers in parallel, then synthesizing the results into a single structured briefing.

Skills like this only work if they fit *your* toolchain. Every provider below is opt-in: configure the ones you have, ignore the rest. The brief still renders — sections without a configured provider are simply skipped with a one-line "not configured" note rather than failing the run.

## When to invoke

Trigger phrases:

- `/world-view`, "world view"
- "Catch me up", "catch me up on everything"
- "What's going on across the board?"
- "What do I need to know today?"
- "Status of everything"

## Required setup

Only two env vars are strictly required — enough to know where the brief lands:

- `WORLD_VIEW_OUTPUT_TARGET` — where the brief gets written: `markdown_file`, `notion`, or `gdocs`
- `WORLD_VIEW_OUTPUT_PATH` — the destination identifier:
  - For `markdown_file`: a filesystem path (e.g., `./world-view-<DATE>.md`)
  - For `notion`: a `<NOTION_DATABASE_ID>` (the brief is created as a new page in that data source)
  - For `gdocs`: omit or set to `auto` to create a new doc; otherwise an existing Google Doc ID

If `WORLD_VIEW_OUTPUT_TARGET=notion` and the destination is unreachable, the skill falls back to `markdown_file` at `./world-view-<DATE>.md` so a brief always lands somewhere.

At least one provider in the next section must be configured — otherwise there's nothing to aggregate. The skill errors out fast if zero providers are enabled.

## Optional providers

Each integration is opt-in. The skill checks for the enable-env-var; if absent, that section is skipped in the brief with a one-line `(provider not configured)` note. Configure as many or as few as fit your stack.

### Email — Gmail / IMAP

- `EMAIL_PROVIDER=gmail` (or `imap`)
- For Gmail: `GOOGLE_WORKSPACE_USER` — `<EMAIL_ADDRESS>` used for the Google Workspace MCP calls
- For IMAP: `IMAP_HOST`, `IMAP_USER`, `IMAP_PASSWORD` (or use the `1ps` BYOK pattern)
- Optional: `EMAIL_LOOKBACK_DAYS` (default `7`)

Pulls unread + starred threads from the lookback window and surfaces any thread awaiting a reply.

### Chat — Slack / Discord

- `CHAT_PROVIDER=slack` (or `discord`)
- `CHAT_CHANNEL_IDS` — comma-separated list of channel IDs to summarize (e.g., `<SLACK_CHANNEL_ID>,<SLACK_CHANNEL_ID>` or `<DISCORD_CHANNEL_ID>,<DISCORD_CHANNEL_ID>`)
- Optional: `CHAT_DM_LOOKBACK_HOURS` (default `48`) — pulls active DMs needing a reply within the window (Slack only; Discord MCPs vary)
- Optional: `CHAT_HISTORY_LIMIT` (default `20`) — messages per channel

### Notes — Notion

- `NOTES_PROVIDER=notion`
- `NOTION_DATABASE_ID` — meeting-notes data source
- Optional: `NOTION_VIA_MCPORTER=true` + `MCPORTER_HOST_ALIAS=<HOST_ALIAS>` — route Notion calls through `mcporter` on a remote host. Use this if the local `mcp__notion__*` tools 404 on pages you haven't manually shared.
- Optional: `NOTES_LOOKBACK_DAYS` (default `14`)

Pulls meeting notes from the lookback window and fetches full content for the 2–3 most recent.

### Project board — Trello / Linear / GitHub Projects

- `BOARD_PROVIDER=trello` (or `linear`, `github`)
- For Trello: `TRELLO_BOARD_IDS` (comma-separated) and per-purpose list IDs:
  - `TRELLO_SHIPPED_LIST_IDS` — recently-shipped work
  - `TRELLO_ACTIVE_LIST_IDS` — in-flight / "doing"
  - `TRELLO_BLOCKED_LIST_IDS` — blocked + needs-decision
- For Linear: `LINEAR_API_KEY` (read-only OK)
- For GitHub Projects: `GITHUB_PROJECT_IDS` + `GITHUB_TOKEN` (or `gh` CLI on the host)

The skill maps "shipped / active / blocked / decisions-needed" 1:1 to the configured lists/queries. If you can't cleanly partition your board, set only `TRELLO_ACTIVE_LIST_IDS` and a single "Active Work" section renders.

### Code hosting — GitHub

- `CODE_PROVIDER=github`
- `GITHUB_ORG` — org or user whose activity to summarize
- `GITHUB_TOKEN` (or `gh` CLI already authenticated on the host)
- Optional: `GITHUB_REPOS` — comma-separated filter (e.g., `org/repo1,org/repo2`); omit to scan the whole org
- Optional: `CODE_LOOKBACK_DAYS` (default `7`)

Surfaces recent PRs (open / needs-review / merged), recent issue activity, and any CI failures on default branches.

### Memory — hAIveMind / any `search_memories`-shaped MCP

- `MEMORY_PROVIDER=haivemind` (or any MCP exposing `get_recent_memories` / `search_memories`)
- `MEMORY_SOURCE_URL` — the MCP endpoint or `mcporter` route (e.g., `mcporter:haivemind`)
- Optional: `MEMORY_LIMIT` (default `10`)

Surfaces recent memories worth resurfacing — decisions, "remember this" notes, fresh context from prior sessions.

## Graceful degradation

If a provider isn't configured, that section is skipped with a `(provider not configured)` note rather than the brief failing. If a configured provider errors mid-run (auth expired, network blip, API rate limit), the skill logs the error in that section and continues with the rest. The brief degrades to whatever's enabled and working — partial signal is more useful than no brief at all.

The minimum useful configuration is one provider plus the required setup. A reasonable starter setup is `EMAIL_PROVIDER=gmail` + `NOTES_PROVIDER=notion` — that alone produces a "what's in my inbox, what was decided in recent meetings" brief.

## Execution flow

**Step 1 — Resolve enabled providers.** Read env; build the list of providers to query. If zero, error: `world-view: no providers configured. Set at least one provider env var.`

**Step 2 — Load all needed MCP tools in one ToolSearch call** based on enabled providers. Example for the full set:

```
select:mcp__google-workspace__search_gmail_messages,mcp__google-workspace__get_gmail_thread_content,mcp__slack__conversations_history,mcp__slack__check_dms,mcp__trello__get_cards,mcp__haivemind__get_recent_memories
```

For Notion via mcporter, no ToolSearch needed — call via `ssh <HOST_ALIAS> 'mcporter call notion.<tool> ...'`.

**Step 3 — Fire ALL data pulls in parallel** (one message, multiple tool calls):

- Email: `search_gmail_messages` with `is:unread OR is:starred newer_than:<EMAIL_LOOKBACK_DAYS>d`
- Notion: search + filter to last `<NOTES_LOOKBACK_DAYS>` days
- Project board: get_cards / Linear GraphQL / `gh project item-list` for each configured list/query
- Chat: `conversations_history` per channel (limit `<CHAT_HISTORY_LIMIT>`), plus `check_dms` if Slack
- Code: `gh pr list`, `gh issue list`, `gh run list --status failure` for each configured repo
- Memory: `get_recent_memories` (limit `<MEMORY_LIMIT>`)

**Step 4 — Hydrate details.** For email: batch-fetch the top 5 most recent message bodies. For Notion: fetch the 2–3 most recent meeting pages in full. For PRs: fetch review state / mergeability on the top open PRs.

**Step 5 — Cross-provider action-item extraction.** Scan all hydrated content for:

- Email threads explicitly awaiting your reply
- Meeting notes with action items assigned to you (case-insensitive match on a configured `USER_HANDLE` env var if set)
- Project-board cards with you as owner in a blocked/decision column
- PRs awaiting your review

Consolidate into a single "Action Items" list at the top of the brief.

**Step 6 — Synthesize and write to `WORLD_VIEW_OUTPUT_TARGET`.** Use the output format below.

**Step 7 — Return the brief location.** Print the path/URL so the user can open it.

## Output format

```markdown
# World View — <DATE>

**Generated**: <ISO timestamp>
**Providers configured**: email, notes, board, chat, code, memory  (list those enabled)

---

## Action Items (needs you)

Cross-provider list of things explicitly requiring your action — pulled from
email threads awaiting reply, meeting-note action items assigned to you,
board cards blocked on you, PRs awaiting your review.

- [ ] [source] [one-line action]

---

## Last Week — What Shipped

- [from board shipped column / Linear completed / GitHub merged PRs]
- (provider not configured) if none of the source providers are enabled

---

## This Week — What's Active

- [from board active column / Linear in-progress / GitHub open PRs]

---

## Blockers / Escalations / Decisions Needed

- [from board blocked + needs-decision lists]
- [from chat threads tagged as blocking]
- [from email threads marked urgent]

---

## Email — Needs Attention

Top threads needing a reply or decision. `subject` — `from` — one-line summary.

---

## Chat — Needs Attention

Active DMs and channel threads requiring a response. `channel` — `from` — one-line summary.

---

## Recent Meetings

Summaries of the last 2–3 meeting notes — decisions made, open items, who's on the hook.

---

## Code Activity

Open PRs awaiting review, recently merged PRs, any CI failures on the default branch.

---

## Context from Memory

Key facts from recent memories worth surfacing — decisions, fresh context, "remember this" notes.

---

## Provider Status

For transparency, list each configured provider and whether the pull succeeded:
- email (gmail): OK — N threads
- notes (notion): OK — N pages
- board (trello): SKIPPED — env var not set
- ...
```

## Notes

- This skill is **read-only** — it must not modify any source data
- All data pulls run in parallel for speed; the bottleneck is the slowest provider
- Keep summaries tight — one line per item where possible
- Flag anything time-sensitive or overdue prominently in the Action Items section
- If a configured provider fails (auth expired, rate-limited, network), note it in the Provider Status section and continue
- The brief is meant to be glanceable in under 60 seconds; ruthlessly trim noise

## Adapt to your toolchain

The skill's contract is "aggregate signal from N providers into one brief." The providers themselves are interchangeable:

- Replace Gmail with Outlook / Fastmail / IMAP — same query shape
- Replace Slack with Discord, Matrix, IRC — same "last N messages per channel" pattern
- Replace Trello with Linear, Jira, GitHub Projects, Asana — same "shipped / active / blocked" 1:1 list mapping
- Replace Notion with Confluence, Obsidian, plain markdown — same "search recent, fetch top N" flow
- Replace hAIveMind with any MCP exposing `get_recent_memories` / `search_memories` — same shape

Keep the seven-section brief structure (Action Items, Last Week, This Week, Blockers, Email, Chat, Meetings, Code, Memory) — it's the contract with the reader, not a tool dependency.
