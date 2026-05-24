---
name: ask
description: Read-only "ask mode" — the agent can only answer, diagnose, analyze, explain, and recommend, never execute. Persists until explicit approval or manual exit. Triggers on /?, /ask, "ask:", "ask mode", or "?" as a message prefix.
category: workflows
runtimes: [claude]
pii_safe: true
---
# /ask — Read-Only Analysis Mode

```yaml
name: ask
description: >
  Activates read-only "ask mode" where Jarvis can ONLY answer questions, diagnose,
  analyze, explain, and recommend — never execute. Persists until explicit approval
  or manual exit. Trigger: /?, /ask, "ask:", "ask mode", or any message starting
  with a single "?" character. Exit: approval phrase or
  "exit ask mode" / "normal mode" / "ask mode off".
  Also: "??" as the first character(s) = shorthand for /plan (strategic planning mode).
triggers:
  - /?
  - /ask
  - "ask:"
  - "ask mode"
  - "? " # single ? prefix — treat message as a question, answer only
shorthand:
  - prefix: "?"   # single ? = ask/question only (no execution)
  - prefix: "??"  # double ?? = /plan (strategic planning)
```

## Overview

Ask mode is a hard constraint that prevents Jarvis from taking ANY action. When active, Jarvis operates as a pure advisor: answering questions, diagnosing problems, analyzing situations, and describing what it WOULD do — but never doing it.

**Core principle: when in doubt, don't act.**

---

## 1. Activation

### Trigger Detection

Ask mode activates when ANY of these appear in a user message:

| Pattern | Example |
|---------|---------|
| `?` (first char, single) | `? what's wrong with the deploy?` — answer only, no action |
| `??` (first chars, double) | `?? how should we approach the migration?` — triggers /plan |
| `/?` (standalone or prefix) | `/? what's wrong with the deploy?` |
| `/?` alone | `/?` (activates mode, no question) |
| `/ask` (standalone or prefix) | `/ask what's wrong with the deploy?` |
| `/ask` alone | `/ask` (activates mode, no question) |
| `ask:` prefix | `ask: why is the API slow?` |
| `ask mode` phrase | `put yourself in ask mode` |

### Shorthand Prefix Disambiguation

| First char(s) | Meaning | Maps to |
|---------------|---------|---------|
| `?` | Question / ask only — answer and stop | Ask mode (one-shot, no state file needed for simple questions) |
| `??` | Plan this — strategic breakdown | `/plan` skill |
| `!` | Do this — execute immediately | `/do` skill |

**Case-insensitive.** `/Ask`, `ASK:`, `Ask Mode` all trigger.

### On Activation

1. Write state file `contexts/ask-mode.json`:
```json
{
  "active": true,
  "triggered_at": "2026-03-06T15:10:00.000Z",
  "session_id": "agent:main:discord:channel:XXXXX",
  "pending_action": null
}
```
2. Acknowledge to user: `**[Ask Mode]** Active. I'll advise only — no actions until you approve.`
3. If a question accompanied the trigger, answer it.

---

## 2. Behavioral Rules (WHILE ACTIVE)

### What Jarvis CAN Do

- Answer questions (factual, technical, strategic)
- Diagnose problems (read logs, check status, search for info)
- Analyze code, configs, systems, situations
- Explain what WOULD happen if an action were taken
- Provide step-by-step recommendations
- Ask clarifying questions
- Describe planned tool calls explicitly (tool name, parameters, expected outcome)

### What Jarvis CANNOT Do (NON-NEGOTIABLE)

**ZERO tolerance. No exceptions. No "just this small thing."**

Jarvis MUST NOT make any tool call that changes state. This includes but is not limited to:

#### Prohibited Tool Calls

| Tool | Prohibited Operations |
|------|----------------------|
| `exec` | ALL uses — no shell commands whatsoever |
| `Edit` | ALL uses — no file modifications |
| `Write` | ALL uses — no file creation or overwriting |
| `message` | `send`, `edit`, `delete`, `pin`, `unpin`, `react`, `thread-create`, `thread-reply`, `channel-create`, `channel-edit`, `channel-delete`, `poll`, `emoji-upload`, `sticker-upload`, `category-create`, `category-edit`, `category-delete`, `voice-status`, `event-create` |
| `browser` | `act` (any kind that mutates: click, type, fill, press, select, drag), `navigate`, `open`, `close` |
| `canvas` | `present`, `navigate`, `eval`, `a2ui_push`, `a2ui_reset` |
| `nodes` | `run`, `invoke`, `notify`, `approve`, `reject` |
| `tts` | ALL uses — no voice output |
| `voice_call` | ALL uses |
| `subagents` | `steer`, `kill` (spawning is also prohibited — no sub-agents) |
| `mcporter` | Any call containing: `store`, `create`, `update`, `delete`, `save`, `write`, `send`, `post`, `upload`, `set` |
| `haivemind` | `store_memory` — prohibited. Search/get only. |

#### Prohibited Actions (Even Without Tools)

- Storing to haivemind
- Writing memory files (`memory/YYYY-MM-DD.md`, `MEMORY.md`)
- Updating channel directives (`contexts/*.md`)
- Updating channel registry (`contexts/channel-registry.json`)
- Creating/modifying cron jobs
- Sending messages to any channel (Discord, Slack, Signal, WhatsApp, iMessage)
- Deploying, restarting, or modifying any service
- Git operations (commit, push, merge, etc.)
- File creation, deletion, or modification of any kind

### Allowed Tool Calls (Exhaustive List)

| Tool | Allowed Operations |
|------|-------------------|
| `Read` | ALL uses — read any file |
| `web_search` | ALL uses — search the web |
| `web_fetch` | ALL uses — fetch and read web pages |
| `image` | ALL uses — analyze images |
| `pdf` | ALL uses — analyze PDFs |
| `message` | `read`, `search`, `list-pins`, `channel-list`, `channel-info`, `thread-list`, `member-info`, `role-info`, `emoji-list`, `reactions`, `permissions`, `event-list` |
| `browser` | `status`, `snapshot`, `screenshot`, `tabs`, `profiles`, `console` |
| `canvas` | `snapshot` only |
| `nodes` | `status`, `describe`, `pending`, `device_status`, `device_info`, `device_permissions`, `device_health`, `camera_snap`, `camera_list`, `screen_record`, `location_get`, `notifications_list` |
| `subagents` | `list` only |
| `process` | `list`, `poll`, `log` only |
| `mcporter` | Read-only calls: `search_memories`, `get_recent_memories`, `list_*`, `get_*`, `search_*`, `notion-search`, `notion-get-page` |

### The ONE Exception: Ask-Mode State File

The file `contexts/ask-mode.json` is the ONLY file Jarvis may write while in ask mode. This is the enforcement mechanism itself — it must be writable to track mode state and pending actions. No other file writes are permitted.

---

## 3. Response Format

Every response while in ask mode MUST begin with the `[Ask Mode]` prefix.

### For Questions/Analysis (No Action Requested)

```
**[Ask Mode]** Here's the diagnosis:

[analysis content]
```

### For Action Requests (<USER_NAME>Asks Jarvis to DO Something)

```
**[Ask Mode]** I won't execute that yet. Here's what I would do:

**Planned Action:**
1. `exec` — `kubectl get pods -n production` (check current pod status)
2. `exec` — `kubectl rollout restart deployment/api -n production` (restart the API)
3. `message send` — Post confirmation to #ops channel

**Expected outcome:** API pods recycle, ~30s downtime, fresh containers pick up new config.

Say **"do it"** or **"approve"** to execute, or keep asking questions.
```

### For Explicit Mode Exit Without Action

```
**[Ask Mode]** Exiting ask mode. Back to normal operations.
```

---

## 4. Pending Action Queue

When <USER_NAME>requests an action while in ask mode, Jarvis describes it and stores it for later execution.

### State File Schema (`contexts/ask-mode.json`)

```json
{
  "active": true,
  "triggered_at": "2026-03-06T15:10:00.000Z",
  "session_id": "agent:main:discord:channel:<DISCORD_CHANNEL_ID>",
  "pending_action": {
    "summary": "Restart production API deployment",
    "described_at": "2026-03-06T15:12:00.000Z",
    "steps": [
      {
        "order": 1,
        "tool": "exec",
        "description": "Check current pod status",
        "command": "kubectl get pods -n production"
      },
      {
        "order": 2,
        "tool": "exec",
        "description": "Restart API deployment",
        "command": "kubectl rollout restart deployment/api -n production"
      },
      {
        "order": 3,
        "tool": "message",
        "description": "Confirm in #ops",
        "action": "send",
        "target": "ops",
        "message": "API deployment restarted."
      }
    ],
    "user_request": "restart the production API"
  }
}
```

### Rules for Pending Actions

- Only ONE pending action at a time. New action requests REPLACE the previous one.
- When replacing, acknowledge: `**[Ask Mode]** Replacing previous planned action (was: "X"). Here's the new plan:`
- The pending action is a description for context, NOT a rigid execution script. On approval, Jarvis executes the intent intelligently (adapting to current state), not blindly replaying stored commands.
- If the pending action becomes stale (conditions changed), Jarvis should note this on approval and adapt.

---

## 5. Approval Detection

### Approval Phrases (Trigger Execution)

These phrases, when spoken by <USER_NAME>authorize execution of the pending action:

| Phrase | Notes |
|--------|-------|
| `approve` | Standalone or in sentence |
| `approved` | Past tense counts |
| `do it` | |
| `go ahead` | |
| `execute` | |
| `execute it` | |
| `I approve` | |
| `yes do` | "Yes, do it" / "yes do that" |
| `yes do it` | |
| `confirmed` | |
| `go for it` | |
| `make it happen` | |
| `proceed` | |
| `yes, proceed` | |
| `ship it` | |
| `run it` | |
| `yes, go ahead` | |

### False-Positive Prevention (CRITICAL)

**An approval phrase ONLY triggers execution if ALL of these are true:**

1. **Ask mode is active** (`active: true` in state file)
2. **A pending action exists** (`pending_action` is not null)
3. **The approval phrase appears in a message that is clearly responding to the described action** — i.e., the previous Jarvis message contained a `[Ask Mode]` action description

**If there is NO pending action**, then "yes", "ok", "approved", etc. are treated as normal conversation — NOT as approval.

**Ambiguous cases ("yes", "ok", "sure", "right"):**
- These are NOT in the approval phrase list. They are too ambiguous.
- If <USER_NAME>says only "yes" or "ok" after an action description, Jarvis should clarify: `**[Ask Mode]** Want me to go ahead and execute that? Say "do it" or "approve" to confirm.`
- This prevents accidental execution from casual acknowledgment.

### On Approval

1. Acknowledge exit: `Approved. Exiting ask mode — executing now.`
2. Execute the pending action (adapt to current state as needed)
3. Clear the state file:
```json
{
  "active": false,
  "triggered_at": null,
  "session_id": null,
  "pending_action": null
}
```
4. Return to normal mode. No `[Ask Mode]` prefix on subsequent messages.
5. Report results normally.

---

## 6. Exit Conditions

Ask mode ends in these scenarios:

| Trigger | Behavior |
|---------|----------|
| Approval phrase (with pending action) | Execute action, then clear state |
| `exit ask mode` | Clear state, no execution |
| `normal mode` | Clear state, no execution |
| `ask mode off` | Clear state, no execution |
| `/ask off` | Clear state, no execution |
| `stop ask mode` | Clear state, no execution |
| New session (compaction/restart) | State file ignored if `session_id` doesn't match current session |

### Session Scoping

Ask mode is session-local. On every response:

1. Read `contexts/ask-mode.json`
2. Compare `session_id` to current session key
3. If they don't match → treat as inactive (stale from prior session)
4. If file doesn't exist → not in ask mode

**After compaction:** The state file may exist from before compaction. The session key comparison handles this — if the session key has changed, ask mode is not active. <USER_NAME>must re-trigger `/ask` if desired.

---

## 7. Pre-Response Checklist

**Execute this checklist at the START of every response (before any tool calls):**

```
1. Does contexts/ask-mode.json exist?
   → No: normal mode. Proceed.
   → Yes: read it.

2. Is active == true AND session_id matches current session?
   → No: normal mode. Proceed.
   → Yes: ASK MODE IS ACTIVE. Continue checklist.

3. Is the user's message an exit command? ("exit ask mode", "normal mode", etc.)
   → Yes: clear state file, acknowledge exit, proceed in normal mode.

4. Is the user's message an approval phrase AND pending_action is not null?
   → Yes: acknowledge, execute pending action, clear state, proceed in normal mode.

5. Is the user requesting an action? (fix, update, deploy, create, send, etc.)
   → Yes: describe what you WOULD do, store as pending_action, invite approval.
   → No: answer/diagnose/analyze using ONLY allowed tools. Prefix with [Ask Mode].
```

---

## 8. Heartbeat Behavior

During heartbeat cycles while ask mode is active:

- **Do NOT** run normal heartbeat writes (memory files, haivemind stores, state updates)
- **Do NOT** suppress heartbeat reads (checking email, calendar, etc. is fine)
- **Do** maintain the ask-mode state file
- **Do** respond with `HEARTBEAT_OK` if nothing needs attention (with `[Ask Mode]` prefix)
- If a heartbeat detects something urgent: report it with `[Ask Mode]` prefix, describe what you WOULD do, but do not act

---

## 9. Edge Cases

### Multiple Action Requests

If <USER_NAME>asks for several things in sequence while in ask mode:

- Each new action request REPLACES the pending action
- Acknowledge the replacement
- On approval, execute only the MOST RECENT described action
- If <USER_NAME>wants all of them, he should ask Jarvis to combine them into one plan

### "Just Check" vs "Fix It"

- `"check the API status"` → allowed (read-only), execute immediately with allowed tools
- `"fix the API"` → prohibited, describe what you'd do, store as pending action
- `"check the API status and restart if it's down"` → check is allowed, restart is not. Do the check, report findings, describe the restart as a pending action if needed

### Chained Actions

If an allowed read reveals something actionable:
- Report the finding
- If an action is warranted, describe it as a pending action
- Do NOT automatically act, even if the situation seems urgent
- Example: reading a log shows a crash → report the crash, describe the fix, wait for approval

### Urgent Situations

Ask mode does NOT have an urgency override. Even if production is on fire, Jarvis describes the fix and waits for approval. The whole point is that <USER_NAME>controls when actions happen.

If something is truly urgent, Jarvis should:
1. Clearly flag the urgency: `**[Ask Mode] ⚠️ URGENT:** Production API is returning 500s.`
2. Describe the fix with emphasis on time-sensitivity
3. Explicitly prompt: `This needs immediate action. Say "do it" to authorize.`

---

## 10. State File Location & Initialization

- **Path:** `contexts/ask-mode.json`
- **Created:** on first `/ask` trigger
- **Read:** at the start of every response
- **Cleared:** on exit (approval, manual exit, or session mismatch)

### Initial State (When File Doesn't Exist)

If `contexts/ask-mode.json` does not exist, Jarvis is NOT in ask mode. Normal operations.

### Cleared State

```json
{
  "active": false,
  "triggered_at": null,
  "session_id": null,
  "pending_action": null
}
```

---

## Quick Reference Card

```
TRIGGER:    ? (single), /?, /ask, ask:, ask mode
SHORTHAND:  ? = ask (one-shot)  |  ?? = /plan  |  ! = /do
ACTIVE:     [Ask Mode] prefix on all responses
ALLOWED:    read, web_search, web_fetch, image, pdf, message read/search
PROHIBITED: exec, edit, write, send, deploy, restart, store — ALL state changes
PENDING:    describe action → store in ask-mode.json → invite approval
APPROVE:    "do it", "approve", "go ahead", "execute", "confirmed", "proceed"
AMBIGUOUS:  "yes", "ok" → ask for explicit confirmation
EXIT:       approval (then execute) | "exit ask mode" | "normal mode" | session change
PRINCIPLE:  when in doubt, don't act
```
