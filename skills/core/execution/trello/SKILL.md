---
name: trello
description: Lifecycle-aware Trello board management for long-running projects. Tracks which board is "active" for the current project, auto-adds Done/In-Progress cards as work happens, clears the Done column on milestone success, and archives boards when projects close out. Trigger phrases — "/trello", "add to trello", "trello this", "clear done", "clear that trello board", "archive that board", "we're done with this project", "show me the board".
category: execution
runtimes: [claude]
pii_safe: true
---

# Trello Skill

Lifecycle management for Trello boards on <USER_NAME>s long-running projects. Goal: <USER_NAME>shouldn't have to micromanage Trello as he works. Claude tracks which board is active, adds cards automatically when work happens, and cleans up when phases close.

## When to invoke

- `/trello` — show the currently active board + counts per column
- `/trello use <board name or id>` — set the active board for this session/project
- `/trello add <list> <card title>` — add a card to a list on the active board
- `/trello done <card title or partial>` — move a card to the Done column
- `/trello inprogress <card>` — move a card to In Progress
- `/trello nice-to-have <card>` — move a card to Nice-to-Have (if list exists)
- `/trello clear-done` — archive ALL cards currently in the Done column (use after a milestone success)
- `/trello archive-board` — archive the entire board (project closeout)
- `/trello list` — list all boards
- Auto-fire when <USER_NAME>says: "add this to trello", "trello it", "we just finished X" (→ done), "X is in progress now", "clear that trello board" (→ clear-done), "we're done with this project" (→ archive-board, ask confirm), "archive that board"

## Active board context

The "active board" is sticky per project + machine. Stored at:
- Local: `~/.claude/projects/-home-yari/.trello-active-board.json`
- Schema: `{"board_id": "...", "board_name": "...", "set_at": "<iso>", "set_by": "claude|lance"}`

Resolution order when a command needs a board:
1. `--board <id|name>` flag if passed
2. Active board file (if exists and < 24h old)
3. Match cwd against project→board hint mapping (see "Project hints" below)
4. Match active conversation context (any mention of a board name in last N messages)
5. Ask <USER_NAME>I don't know which board you mean — `list` shows all of them; tell me which."

## Project hints (auto-detect mapping)

These are the historical project→board mappings. Update this section as new projects come up.

| Project / context | Trello board | Board ID |
|---|---|---|
| <INTERNAL_SERVICE_HOST>, <EXTERNAL_ORG> Disruption, <PROJECT_NAME> demo | <EXTERNAL_ORG> Disruption 2026 — Demo Prep | `6a03753d28162b0988fea720` |
| Engineering pipeline / weekly | Engineering Pipeline | `69b047414e0f15846e1eb44f` |
| Hiring conversations | Engineering Hiring | `68beecf2da7453c4930665fa` |
| Product+Eng planning | Product & Eng Planning | `68a35349f048f1a416a64aaf` |
| Eng on-site planning, themes, <TEAM_MEMBER>'s 4Q | Eng On-Site Planning | `69cab82fa378c652ea15330f` |
| <EXTERNAL_ORG> / <EXTERNAL_ORG> CVE-2026-33634 | <EXTERNAL_ORG> / <EXTERNAL_ORG> | `69c6d42df2a6774d46f38679` |
| Malware analysis, IOC collection | <EXTERNAL_ORG> — Malware Analysis & IOC Collection | `69c6d9de49eef1ea03f7df3f` |
| IT board | IT board | `<TRELLO_BOARD_ID>` |
| Sales & Business Development | Sales & Business Development | `68f6556a0a321b4430885c8b` |
| <PROJECT_NAME> (active product) | <PROJECT_NAME> | `6a036514d136721f383ca536` |

When a new project comes up that doesn't match, ask <USER_NAME>whether to (a) use an existing board, (b) create a new one, or (c) skip Trello tracking for this work.

## Tool layer

All Trello calls go through the project's Trello MCP — local `mcp__trello__*` tools, not mcporter (Trello MCP runs locally per session). Common patterns:

```
mcp__trello__get_boards            → list all boards
mcp__trello__get_lists(board_id)   → list columns on a board
mcp__trello__get_cards(list_id)    → list cards in a column
mcp__trello__create_card({idList, name, desc})
mcp__trello__update_card(card_id, {idList: <new_list>, closed: true})
mcp__trello__get_card(card_id)     → card detail
```

To archive a card: `update_card(card_id, {closed: true})`.
To archive a list: it has no `closed` field in this MCP — instead, archive every card in it, then leave the empty list.
To archive a whole BOARD: call the underlying Trello API directly via mcporter or curl with the user's PAT. (Not commonly needed — usually keeping the board around as history is fine.)

## Commands — detailed

### `/trello`

1. Read active-board file.
2. `get_lists(board_id)` → list columns.
3. `get_cards(list_id)` per column → counts.
4. Output:
   ```
   Board: <name> (https://trello.com/b/...)
   Lists:
     🔥 Must Have Today: N cards
     🚧 In Progress: N cards
     ✅ Done: N cards
     💡 Nice to Have: N cards
   ```

### `/trello use <name or id>`

1. If ID, validate via `get_board(id)`.
2. If name, `get_boards()` and fuzzy-match (case-insensitive, contains).
3. Write to active-board file.
4. Confirm: `Active board → <name>`.

### `/trello add <list> <title>`

1. Resolve list by name on the active board (fuzzy-match against `get_lists()`).
2. `create_card({idList, name})`.
3. Confirm with URL.

### `/trello done <card>`

1. Find the Done list on the active board (name contains "Done" or "✅").
2. Fuzzy-match the card title across ALL lists on the board (case-insensitive substring).
3. If multiple matches, list them and ask which.
4. `update_card(card_id, {idList: done_list_id})`.
5. Prepend `✅ ` to the card name if not already.

### `/trello clear-done`

**This is the milestone-success cleanup <USER_NAME>asked for.**

1. Find the Done list on the active board.
2. `get_cards(done_list_id)` → all cards.
3. Print the list so <USER_NAME>can sanity-check before destructive action:
   ```
   About to archive 18 cards from "✅ Done":
     - card 1
     - card 2
     ...
   ```
4. **ALWAYS prompt for confirmation** before archiving in bulk: "Archive all N? [y/N]". This is a soft-destructive op (archive ≠ delete, but it removes from view).
5. On confirmation, loop: `update_card(card_id, {closed: true})` for each.
6. Report: `Archived N cards from Done.`

Behavior nuance: <USER_NAME>said "clear out dons" when a milestone closes — meaning the board lives on (more milestones to come) but the Done column is emptied. Archive ≠ delete, so the cards remain queryable via Trello's "Archived items" view if anyone needs the history.

### `/trello archive-board`

**This is the project-closeout cleanup.**

1. Confirm with <USER_NAME>Archive entire board '<name>' (all lists, all cards, board itself becomes hidden)? [y/N]"
2. On confirm, archive ALL cards in ALL lists first (loop using `update_card({closed: true})`).
3. Then close the board via direct Trello API (need <USER_NAME>s PAT). If PAT isn't available, archive all the cards and leave the board itself open but empty — note this in the report.
4. Clear the active-board file.
5. Report: `Project closeout: <board name> — N cards archived, board hidden.`

### Auto-fire patterns

When Claude is doing work in a long-running session and sees these triggers, auto-add to Trello with the active board:

- <USER_NAME>says "we just finished X" → propose `done` on a matching card OR add a new Done card
- <USER_NAME>says "X is in progress" → propose `inprogress`
- Claude completes a meaningful unit of work (deploy, fix, feature ship) → propose adding a Done card with a 1-line title and a 2-3 sentence description
- <USER_NAME>describes a future task ("we should add Y", "remind me to do Z") → propose adding to "Nice to Have" or "Backlog"
- "Clear that trello board" / "demo was a success, let's clean up" → propose `clear-done` with the card list shown for confirmation
- "We're done with this project" / "archive that board" → propose `archive-board` with strong confirmation prompt

In all cases, OFFER the action with the proposed card content; don't fire silently. <USER_NAME>approves with "yes" / "go ahead" / "do it".

## Hard rules

- **Never archive without confirmation.** `clear-done` and `archive-board` always show the list and require an affirmative response.
- **Match the active board's column scheme.** Don't assume "Done" — read the lists and find the column whose name contains "Done" or has the ✅ prefix. Some boards use "Shipped", "Complete", "Resolved".
- **Card descriptions matter.** When auto-adding a Done card, the description should explain WHAT was done + WHY + verification evidence. <USER_NAME>reviews the board visually — terse "fixed bug" cards are unhelpful.
- **Update the project-hints table** when a new project↔board mapping comes up. The table is the auto-detect index.
- **Don't double-add.** Before creating a card, fuzzy-check that a similar card doesn't already exist on the board. If a near-match exists, update it instead of creating a duplicate.

## Verification (per /verification-completion)

After any board-modifying op:
1. Re-fetch the affected list(s) and count cards.
2. Confirm the card you created/moved/archived shows in the expected place.
3. Report measured counts ("before: 18 in Done, after: 0 in Done, 18 archived").

Never claim "cleared" without re-fetching to confirm.

## Project closeout retro hook

When `/trello archive-board` runs, before archiving, AUTO-RUN one final retro:
- Pull all Done cards' titles + descriptions
- Generate a project summary: what shipped, what was deferred to nice-to-have, what was dropped
- Save the summary as a memory: `project_retro_<slug>_<YYYY-MM-DD>.md`
- Post a copy to the Notion Meeting Retros dashboard (id `<NOTION_ID>`) as a sub-page titled `Project Closeout — <board name> — <date>`

This way every closed project produces a learning artifact, same pattern as [[meeting-retro]].

## Related

- [[meeting-retro]] — sibling skill, retros for meetings instead of project closeouts
- [[feedback-demo-education]] — example of feedback-type memory the closeout retro might produce
- Trello board universe: `/trello list` to see all of <USER_NAME>s boards

## Source

Created 2026-05-14 at <USER_NAME>s request after the <EXTERNAL_ORG> Disruption demo success. <USER_NAME>wanted "you just kind of know" — auto-add cards as work happens, clear Done on milestone success, archive board on project closeout. First use case: clearing the Done column on `<EXTERNAL_ORG> Disruption 2026 — Demo Prep` after the demo succeeds.
