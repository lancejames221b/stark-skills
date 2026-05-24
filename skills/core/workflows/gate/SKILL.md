---
name: gate
description: >
  Structural approval gate for all outbound actions with real-world side effects.
  Intercepts messaging (iMessage, SMS, WhatsApp, Signal), Slack posts, calendar invites to others,
  git pushes, and any external action outside <USER_NAME>s personal bubble.
  Load this skill before ANY gated action. Presents approve/deny in Discord with optional pre-checks.
  Triggers on: any personal message send, Slack post, git commit/push, calendar invite to third parties,
  or when a /gate command is issued.
category: workflows
runtimes: [claude]
pii_safe: true
---

# gate

The gate is a structural approval layer. Not a soft rule — a hard stop. Before any gated action executes, I pause, present the action to <USER_NAME>in Discord with buttons, and wait for explicit approval. The action does not happen until the thumbs up is given.

> "The approval rules I have now are correct but they're enforced by text in a file I wrote to myself. That's fragile. A proper gate skill would be structural — I literally cannot proceed past certain action types without a Discord confirmation from you. Not 'I should ask' but 'I cannot not ask.'"

---

## Gated Action Categories

These action types ALWAYS require a gate before executing:

| Category | Examples | Default policy |
|----------|----------|----------------|
| **personal-message** | iMessage, SMS, WhatsApp, Signal to anyone except <USER_NAME>human` |
| **slack-post** | Any post or reply to Slack (even #<USER_NAME>-workspace) | `human` |
| **calendar-invite** | Invites or event edits that include other attendees | `human` |
| **git-push** | `git push` to any remote, any branch | `human` + `check pii` |
| **email-send** | Any send via Gmail or MCP (not drafts — drafts are free) | `human` |
| **external-api-write** | Create/update/delete calls to HubSpot, Stripe, Zapier, etc. | `human` |
| **file-share** | Sharing Drive files or adding permissions for other users | `human` |

**Never gated (free to proceed):**
- Drafts (Gmail drafts, Notion pages, Slack drafts for review)
- Read operations (search, list, fetch, analyze)
- Internal writes (haivemind, Notion pages, local files, Discord in this channel)
- Messages to <USER_NAME>s own number (<PHONE_NUMBER>)
- Calendar events <USER_NAME>is attending alone

---

## Gate Flow

```
1. Detect gated action intent
2. Run any configured pre-checks (pii, secrets, custom)
3. If pre-check fails with policy=block → STOP, report why
4. Build approval message (action summary + preview/diff if available)
5. Determine gate destination:
   - Use the inbound message's channel ID (from conversation metadata chat_id / channelId)
   - Fallback to #gate-skill (<DISCORD_CHANNEL_ID>) only if no source channel is available
6. Post approval message to that channel with Approve/Deny buttons
7. Wait for response
8. On Approve → proceed with action, log to haivemind
9. On Deny → cancel, log to haivemind with reason if given
10. Timeout (15 min no response) → auto-cancel, notify
```

---

## Command Syntax

```
/gate [action description] [options]
```

### Gate Policies

| Policy | Behavior |
|--------|----------|
| `human` (default) | Always ask <USER_NAME>before proceeding |
| `auto` | Run checks → if all pass, proceed automatically (no human ask) |
| `block` | Never proceed, always deny (hard block, no exceptions) |

### Check Flags

Checks run BEFORE the human ask. Results are shown in the approval message.

| Flag | What it does | Failure behavior |
|------|-------------|-----------------|
| `check pii` | Runs `pii_scan.py --diff --report` on staged diff or content | Default: block on dirty |
| `check secrets` | High-entropy + credential patterns only | Default: block on dirty |
| `check script:/path` | Custom checker script (exit 0=pass, exit 1=fail) | Configurable |

### Check failure overrides

Append to change default failure behavior:

```
/gate commit to GitHub check pii          → pii block (default)
/gate commit to GitHub check pii human    → pii block OR clean → ask human
/gate commit to GitHub check pii escalate → pii escalate (don't block, show in approval)
/gate commit to GitHub check pii auto     → pii pass = proceed automatically
```

### Examples

```
/gate send message to <TEAM_MEMBER>
/gate post to Slack #<PROJECT_NAME>
/gate commit to GitHub
/gate commit to GitHub check pii
/gate push to production check pii check secrets human
/gate invite <TEAM_MEMBER> to calendar event
/gate share Drive doc with external@example.com
```

---

## Discord Approval Message Format

Post to the **originating channel** (from inbound `chat_id` / `channelId` metadata) with buttons.
If no source channel is available, fall back to #gate-skill (<DISCORD_CHANNEL_ID>).

Format:

```
🔒 GATE — [Action Type]

Action: [What I'm about to do]
Target: [Who/where]

[Preview block — message content, diff summary, invite details, etc.]

[Check results if any:
  ✅ PII scan: clean (0 matches)
  ⚠️ Secrets scan: 1 high-entropy string flagged (line 47)]

Approve to proceed. Deny to cancel.
```

Use Discord components with:
- **Approve** button (style: success)
- **Deny** button (style: danger)

If <USER_NAME>types "approve", "yes", "send it", "go ahead", "do it", "make it so" — that counts as approval.
If <USER_NAME>types "deny", "no", "cancel", "stop", "don't" — that counts as denial.

---

## Pre-Check Integration

### PII Scan (git-pii-guard)

For git commits/pushes:
```bash
python3 ~/dev/skills/git-pii-guard/scripts/pii_scan.py --diff --report
```

For message content:
```bash
echo "MESSAGE_CONTENT" | python3 ~/dev/skills/git-pii-guard/scripts/pii_scan.py --text -
```

Exit codes: 0=clean, 1=blocking issues, 2=warnings only

### Message Content Preview

Before sending any personal message, show the content in the approval message. No hidden sends.

---

## Logging

After every gate decision, store to haivemind:

```bash
# Approved
mcporter call haivemind.store_memory \
  content="GATE-APPROVED [timestamp] action=[type] target=[who] checks=[results]: [1-line summary]" \
  category="operations"

# Denied
mcporter call haivemind.store_memory \
  content="GATE-DENIED [timestamp] action=[type] target=[who] reason=[reason if given]" \
  category="operations"

# Blocked by check
mcporter call haivemind.store_memory \
  content="GATE-BLOCKED [timestamp] action=[type] check=[which] finding=[what failed]" \
  category="operations"
```

---

## /link Command (bonus — channel resource registry)

Register named resources to the current channel so "open the spec" or "open the PR" just works:

```
/link spec https://docs.google.com/...
/link pr https://github.com/...
/link board https://trello.com/...
```

Stored in `contexts/channel-registry.json` under `channels.[id].resources`:

```json
{
  "channels": {
    "<DISCORD_CHANNEL_ID>": {
      "resources": {
        "spec": "https://docs.google.com/...",
        "pr": "https://github.com/..."
      }
    }
  }
}
```

When <USER_NAME>says "open the spec" — check channel resources first, then mac-open it.

---

## What This Skill Is NOT

- Not a rules document (those are in SOUL.md)
- Not a soft suggestion (it's a hard stop)
- Not about research, drafting, or analysis (those are always free)
- Not about actions inside <USER_NAME>s own bubble (Discord here, haivemind, local files)

---

## Activation Pattern for Jarvis

When I detect a gated action is about to happen:

1. **STOP** before executing
2. Load this skill (you're reading it)
3. Identify the action category and default policy
4. Run any configured checks
5. Build the approval message
6. Post to #gate-skill with buttons
7. **WAIT** — do not proceed until approval received
8. Log the decision

If I'm in the middle of a longer task and hit a gated action, I pause the task, gate it, then resume on approval.
