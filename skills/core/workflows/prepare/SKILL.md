---
name: prepare
description: >
  Meeting preparation skill. Opens all relevant docs/tabs on Mac Chrome and sends a
  2-minute Discord reminder before a meeting. Two modes: (1) /prepare [topic] [time] —
  explicit prep for a specific meeting; (2) /prepare check — scan today's full calendar
  and auto-prep for every meeting. Uses channel-registry, haivemind, Notion, and Google
  Calendar/Drive to find the right docs. Triggers on "/prepare", "prepare me for",
  "get me ready for", "/prepare check".
category: workflows
runtimes: [claude]
pii_safe: true
triggers:
  - "/prepare"
  - "prepare me for"
  - "get me ready for"
  - "prep for my meeting"
model: sonnet-high
---

# /prepare — Meeting Prep

Opens Chrome tabs on Mac + sends a 2-minute Discord channel ping before meetings.
Pulls context from calendar, channel-registry, haivemind, Notion, and Google Drive.

---

## Trigger Patterns

| Command | Behavior |
|---------|----------|
| `/prepare [topic] [time]` | Prep for one specific meeting |
| `/prepare` (no args) | Use current channel topic + ask for time |
| `/prepare check` | Scan today's full calendar, prep all meetings |
| `/prepare check [date]` | Prep for a specific day (e.g. "tomorrow") |

**Examples:**
- `/prepare <PROJECT_NAME> sprint 2:30pm`
- `/prepare check`
- `prepare me for my 3pm`
- `/prepare <PRODUCT_NAME> standup 10am`

---

## Mode 1: Single Meeting Prep

### Step 1 — Parse the request

Extract:
- **topic**: meeting subject (from args, or from current channel's `currentFocus` in channel-registry)
- **time**: when is the meeting (parse relative times — "in 30min", "at 2:30", "3pm" — always run `date` first for baseline)
- **channel_id**: the Discord channel where `/prepare` was invoked (this is where the 2-min ping goes)

If topic is missing → use current channel's `currentFocus` from channel-registry.json.
If time is missing → ask <USER_NAME>What time is the meeting?"

### Step 2 — Context resolution

Run all three in parallel:

**A. Channel registry lookup**
```bash
cat ~/dev/contexts/channel-registry.json | python3 -c "
import json, sys, re
topic = '[TOPIC]'.lower()
r = json.load(sys.stdin)
matches = []
for cid, ch in r.get('channels', {}).items():
    name = (ch.get('name') or '').lower()
    focus = (ch.get('currentFocus') or '').lower()
    ctx = ch.get('contextFile')
    if any(word in name or word in focus for word in topic.split()):
        matches.append({'id': cid, 'name': ch.get('name'), 'focus': ch.get('currentFocus'), 'ctx': ctx})
print(json.dumps(matches, indent=2))
"
```

If a matching channel has a `contextFile`, read it:
```bash
cat ~/dev/contexts/[contextFile]
```

**B. hAIveMind search**
```bash
mcporter call haivemind.search_memories query="[TOPIC] meeting docs urls" limit=10
```

**C. Notion search**
```bash
mcporter call notion-oauth.notion-search query="[TOPIC]" page_size=5
```

**D. Google Drive search** (if relevant docs expected)
```bash
mcporter call google-workspace.search_docs \
  user_google_email="<EMAIL_ADDRESS>" \
  query="[TOPIC]" \
  page_size=5
```

**E. Google Calendar — find the actual event** (confirms time + gets invite body + meeting link)
```bash
# Get today's date range
TODAY_START=$(date -u +"%Y-%m-%dT00:00:00Z")
TODAY_END=$(date -u +"%Y-%m-%dT23:59:59Z")

mcporter call google-workspace.list_events \
  user_google_email="<EMAIL_ADDRESS>" \
  time_min="$TODAY_START" \
  time_max="$TODAY_END"
```

From the calendar event extract:
- Exact start time (ISO timestamp)
- Description / body (may contain doc links, agenda)
- Conference link (Google Meet, Zoom, etc.)
- Attendees

### Step 3 — Assemble URL list

Priority order for URLs to open:
1. Conference/meeting link from calendar event (Google Meet, Zoom, Teams)
2. URLs found in calendar event description
3. Notion pages matching the topic
4. Google Drive docs matching the topic
5. Channel context file URLs (from contextFile)
6. hAIveMind recalled URLs for this topic
7. Linear board if project channel found in registry

Deduplicate. Cap at **8 URLs** max (Chrome handles it; more is overwhelming).

If zero URLs found → still schedule the ping, skip the tab opening, note "No docs found — only pinging at T-2min"

### Step 4 — Calculate T-2min fire time

```bash
# Always run date first
date "+%A %B %d %Y %H:%M %Z"

# Calculate fire time
# Meeting at e.g. 14:30 EST = 19:30 UTC
# T-2min = 14:28 EST = 19:28 UTC
FIRE_TIME=$(date -d "[MEETING_TIME] - 2 minutes" -u +"%Y-%m-%dT%H:%M:%SZ")
echo "Fire time: $FIRE_TIME"
```

**Validation:** If meeting is less than 3 minutes away → open tabs NOW, post ping NOW, skip cron.
If meeting is in the past → tell <USER_NAME>and abort.

### Step 5 — Schedule T-2min cron job

Create ONE cron job that does both actions (open tabs + post ping):

```javascript
cron({
  action: "add",
  job: {
    name: "prepare-[TOPIC_SLUG]-[HH]MM",
    sessionTarget: "isolated",
    schedule: {
      kind: "at",
      at: "[FIRE_TIME_ISO]"  // T-2min in UTC
    },
    payload: {
      kind: "agentTurn",
      message: `Meeting prep firing for: [MEETING TITLE] at [TIME].

STEP 1 — Open these URLs on Mac via SSH:
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no <USER_NAME>@<TAILSCALE_IP> 'open "[URL1]" && open "[URL2]" && open "[URL3]"'
(run the SSH command, open all URLs)

STEP 2 — Post this message to Discord channel [CHANNEL_ID]:
📋 **[MEETING TITLE]** in 2 minutes
[CHANNEL_MENTION if project channel found]
[URL1_SHORT_DESC]: <URL1>
[URL2_SHORT_DESC]: <URL2>
[MEETING_LINK if present]

Use the message tool: action=send channel=discord target=[CHANNEL_ID] message="[formatted message]"

Do both steps. Do not skip either.`,
      model: "google/gemini-3.1-flash-lite-preview",
      timeoutSeconds: 60
    },
    delivery: {
      mode: "announce",
      channel: "discord",
      to: "channel:[CHANNEL_ID]"
    }
  }
})
```

### Step 6 — Verify cron created

```javascript
cron({ action: "list", includeDisabled: false })
// Find job by name, extract jobId
```

### Step 7 — Post confirmation to current channel

```
✅ **Prep scheduled for [MEETING TITLE]**
⏰ Fires at: [T-2min time] EST
📂 Opening [N] tabs: [list of doc names/URLs]
🔔 Ping goes to: [#current-channel] [<#project-channel> if found]
🆔 Job: [jobId]
```

If <USER_NAME>wants to change anything: "edit the URLs" → update and reschedule.

---

## Mode 2: `/prepare check` — Full Day Scan

### Step 1 — Pull today's calendar

```bash
TODAY_START=$(date -u +"%Y-%m-%dT00:00:00Z")
TODAY_END=$(date -u +"%Y-%m-%dT23:59:59Z")

mcporter call google-workspace.list_events \
  user_google_email="<EMAIL_ADDRESS>" \
  time_min="$TODAY_START" \
  time_max="$TODAY_END"
```

### Step 2 — Filter relevant meetings

Skip:
- Events you created but have no attendees (solo blocks)
- "Busy" / "OOO" / "Focus time" events
- Events that have already passed (start time < now)
- Events < 5 minutes away (too late for prep scheduling — handle immediately)

Keep: anything with a meeting title that implies participation.

### Step 3 — For each meeting, run Mode 1 Steps 2–6

Run context resolution per meeting. Schedule a cron per meeting.

### Step 4 — Post summary

```
📅 **Today's prep queue — [DATE]**

✅ 10:00 AM — <PROJECT_NAME> Sprint Review → [N] tabs, cron job [id]
✅ 2:30 PM — <PRODUCT_NAME> standup → [N] tabs, cron job [id]
⚠️ 4:00 PM — 1:1 May → no docs found, ping only, cron job [id]
⏭️ 9:00 AM — Daily standup → already passed, skipped

All reminders fire 2 minutes before each meeting.
```

---

## URL Formatting for Discord Ping

In the 2-min Discord message, format URLs cleanly:

```
📋 **<PROJECT_NAME> Sprint Review** in 2 minutes
<#<DISCORD_CHANNEL_ID>>

📄 Sprint doc: <https://notion.so/...>
📊 Linear board: <https://linear.app/...>
🎥 Meet: <https://meet.google.com/...>
```

- Wrap in `<>` to suppress embeds
- Use short descriptive labels (not raw URLs)
- Channel mention on its own line so it's instantly tappable
- Keep total message under 500 chars

---

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| Meeting < 3 min away | Open tabs NOW + post ping NOW, skip cron |
| Meeting already passed | Tell <USER_NAME>abort |
| No docs found | Schedule ping-only cron, note it in confirmation |
| Mac SSH fails at fire time | Post ping anyway, note "Mac unreachable — open tabs manually" |
| Multiple meetings same time | Prep all, separate cron per meeting |
| No calendar event found | Use topic as-is, skip calendar-based URL extraction |
| `/prepare check` finds 0 meetings | "Nothing on the calendar today." |

---

## Channel Context for Ping Target

The 2-min ping **always goes to the channel where `/prepare` was invoked**.
If a matching project channel is found in registry, it's **linked** (not posted to) in the message.

Pattern: post to invoking channel, mention project channel as a clickable link.

```
📋 **<PROJECT_NAME> Sprint Review** in 2 minutes
→ <#<DISCORD_CHANNEL_ID>>   ← tap to go there
```

---

## Model

Use `sonnet-high` for context resolution and URL assembly.
The cron payload fires with `google/gemini-3.1-flash-lite-preview` (lightweight executor, just opens tabs + posts message).

---

## hAIveMind Store (after scheduling)

```bash
mcporter call haivemind.store_memory \
  content="PREPARE [channel-id] [ISO-timestamp]: scheduled prep for '[MEETING_TITLE]' at [TIME]. URLs=[N]. CronJob=[jobId]. Tabs: [URL1, URL2...]" \
  category="operations"
```

---

## Notes

- Mac must be awake on Tailscale (<TAILSCALE_IP>) when cron fires
- SSH key: `~/.ssh/id_rsa`
- If MAC is asleep, SSH will timeout — ping still fires to Discord
- All times calculated in EST, converted to UTC for cron `at` field
- Always run `date` before any time calculation — never calculate in head
- Channel registry is the primary source of truth for project→channel mapping
