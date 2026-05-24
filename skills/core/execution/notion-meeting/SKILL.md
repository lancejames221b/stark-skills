---
name: notion-meeting
description: Create a new Notion AI meeting notes page and open it in Chrome on <WORKSTATION_HOST>. Use when user says "new meeting", "notion meeting", "start a meeting", "open notion meeting".
category: execution
runtimes: [claude]
pii_safe: true
---

# Notion Meeting Skill

> **Notion access — use mcporter on <INFERENCE_HOST> FIRST.** Local `mcp__notion__*` tools require per-page sharing in Notion's UI and 404 on most pages. Use `ssh <INFERENCE_HOST> 'mcporter call notion.<tool> ...'` instead. Tools available: notion-search, notion-fetch, notion-query-meeting-notes, notion-update-page, notion-create-pages, notion-create-view, notion-update-view (16 total). See memory `feedback_notion_via_mcporter`.

Creates a new Notion meeting notes page and opens it immediately in Chrome on <WORKSTATION_HOST>.

## Usage
- `/notion-meeting` — New meeting page titled with today's date, opens in Chrome
- `/notion-meeting <title>` — New meeting page with custom title

## Implementation

### Step 1: Determine title

- No argument → `Meeting — April 20, 2026` (use today's date, spelled out)
- Argument provided → use as-is, append date if it looks like a name: `<USER_NAME><TEAM_MEMBER> — April 20, 2026`

### Step 2: Create the Notion page

Use `notion-create-pages` with **no parent** (workspace-level — this is how Notion AI meeting notes are stored):

```
pages:
  - properties:
      title: "<title>"
    icon: "📋"
    content: |
      ## Attendees

      ## Agenda

      ## Notes

      ## Action Items
      - [ ] 
```

### Step 3: Open in Chrome on <WORKSTATION_HOST>

Take the `url` from the create response and run:

```bash
google-chrome "<url>" &
```

Use regular Chrome (not `--app` mode) so the user gets the full Notion sidebar and AI features.

### Step 4: Confirm

Reply with one line:
```
Opened: <title> → <url>
```

## Notes
- Meeting pages are created at workspace root — they appear in Notion AI's meeting notes view automatically because of their structure
- `google-chrome` is at `/usr/bin/google-chrome` on <WORKSTATION_HOST>
- Today's date format: "Month D, YYYY" (e.g. "April 20, 2026")
- If Chrome is already open, the page opens as a new tab
- The Notion PWA (app mode) is at `~/.local/bin/notion` — don't use it here, user wants full Notion
