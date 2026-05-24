---
name: handoff
description: Memory-backed session handoff. Post a structured snapshot to Notion+hAIveMind so the next session (any machine) can pick up instantly. Replaces Discord-relay handoff. Use when handing work between machines, times, or Claude sessions.
argument-hint: "[target-machine] [what's done / what's next]  |  pickup  |  (no args → pickup last)"
category: handoff
runtimes: [claude]
pii_safe: true
---

# Handoff

> **Notion access — use mcporter on <INFERENCE_HOST> FIRST.** Local `mcp__notion__*` tools require per-page sharing in Notion's UI and 404 on most pages. Use `ssh <INFERENCE_HOST> 'mcporter call notion.<tool> ...'` instead. Tools available: notion-search, notion-fetch, notion-query-meeting-notes, notion-update-page, notion-create-pages, notion-create-view, notion-update-view (16 total). See memory `feedback_notion_via_mcporter`.

Context ferry between Claude sessions using Notion+hAIveMind as the relay.
Works across <WORKSTATION_HOST>, <INFERENCE_HOST>, and mac without Discord token resolution.

## Usage

**Send a handoff:**

```
/handoff <INFERENCE_HOST> finishing phase 8 cred detection, next is phase 9 handoff rewrite — you are it
/handoff <MAC_HOST> done with threat analysis, need to review YARA rules next
/handoff phase 7+8 done. obsidian live. next: migrate memories from <NOTION_DATABASE_ID>
```

**Pick up a handoff:**

```
/handoff pickup        — load most recent handoff from any machine
/handoff               — same as pickup (no args)
```

**Optional Discord ping** (append to send):

```
/handoff notify generic phase 9 shipped, picking up from <WORKSTATION_HOST>
```

---

## Tool loading

```
ToolSearch select:mcp__notion__notion-create-pages,mcp__haivemind__store_memory,mcp__haivemind__search_memories,mcp__notion__notion-fetch
```

---

## SEND flow

### 1. Parse intent

- `pickup` or no args → jump to PICKUP flow
- `notify <rest>` → set `discord_ping=true`, parse rest normally
- First word matches a known machine (`<WORKSTATION_HOST>`, `<INFERENCE_HOST>`, `<MAC_HOST>`) → set `target_machine`, rest is message
- Otherwise: no specific target, message is entire args

### 2. Build handoff content

Infer structure from the message + conversation context:

```
FROM: <current machine (hostname)>
TO: <target_machine or "any">
DATE: <YYYY-MM-DD HH:MM>

## What's done
<completed work from the message / conversation>

## What's next
<next steps from the message / conversation>

## Key context
<any Notion URLs, file paths, ticket IDs, decisions from the current conversation worth carrying forward>

## Jump-in command
/handoff pickup
```

### 3. Save to Notion + hAIveMind

Call `mcp__notion__notion-create-pages`:

```
parent: {"data_source_id": "<NOTION_DATABASE_ID>"}
pages: [{
  properties: {
    title: "Handoff — <from> → <to> — <YYYY-MM-DD>",
    "Category": "project",
    "Tags": ["handoff", "<from-machine>", "<to-machine-or-any>"],
    "Machine": "<from-machine>",
    "date:Date:start": "<YYYY-MM-DD>",
    "Summary": "<one-line summary of what's next>",
    "Source": "save"
  },
  content: <full handoff markdown above>
}]
```

Capture `id` and `url`.

Store hAIveMind index entry via `mcp__haivemind__store_memory`:

```
[HANDOFF-MEM] Handoff — <from> → <to> — <date>
Category: project
Tags: handoff, <from>, <to-or-any>
Machine: <from>
Date: <YYYY-MM-DD>
Notion: <url>
Notion-ID: <id>
Summary: <what's next in one line>
```

### 4. Optional Discord ping

Only if `discord_ping=true` (user said `notify`). One curl call — no token resolution gymnastics:

```bash
# Get token
TOKEN=$(grep '^DISCORD_TOKEN=' <LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env 2>/dev/null | cut -d= -f2 \
  || ssh -o BatchMode=yes <INFERENCE_HOST> "grep '^DISCORD_TOKEN=' <LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env | cut -d= -f2" 2>/dev/null)

HUD_CHANNEL="<DISCORD_CHANNEL_ID>"
MSG="🤝 Handoff posted: <notion_url>\n$(echo "$SUMMARY" | head -c 200)"

[ -n "$TOKEN" ] && curl -s -X POST \
  "https://discord.com/api/v10/channels/$HUD_CHANNEL/messages" \
  -H "Authorization: Bot $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"content\": \"$MSG\"}" > /dev/null
```

### 5. Confirm

```
✅ Handoff posted: **Handoff — <WORKSTATION_HOST> → <INFERENCE_HOST> — 2026-04-24**
→ <notion_url>
Next session: /handoff pickup
```

---

## PICKUP flow

### 1. Search hAIveMind for most recent handoff

Call `mcp__haivemind__search_memories`:

```
query: "[HANDOFF-MEM]"
limit: 5
```

If no results → also try `query: "handoff session"`.

### 2. Pick the most recent entry

Sort by `Date:` field in the index content. Take the newest.

### 3. Fetch Notion page

Call `mcp__notion__notion-fetch` with the Notion URL from the index entry.

### 4. Present as briefing

```
## 🤝 Handoff Pickup — <from> → <to> — <date>

**From:** <from-machine>   **To:** <to-machine>

### What's done
<content>

### What's next
<content>

### Key context
<content>

---
Notion: <url>
```

Ask: "Ready to continue? I can start on [first next step] now."

---

## Notes

- No Discord token resolution required for send. Token only needed if user says `notify`.
- The Notion page is the source of truth — hAIveMind is just the index pointer.
- If Notion is unavailable, write Obsidian file under `<LOCAL_PATH>/obsidian/project/handoff-<date>.md` and store `[HANDOFF-MEM]` with `Obsidian-Path` instead of Notion URL.
- Previous Discord-based `/handoff` slash command (a historical fallback) is preserved for sending Discord messages directly — it just no longer carries the primary session state.
