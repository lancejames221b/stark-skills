---
name: discord-activity-tracker
description: Scan Discord channels for recent activity, extract TODOs and topics, update channel-registry.json, index to hAIveMind, and produce a channel digest. Includes voice output via /speak. Three modes: (1) "channel digest" / "what's pending" — full scan; (2) "ping me" / "where am I" — fast multi-channel status; (3) "ping me [topic]" / "ping me ew-archiver" / "ping me <PROJECT_NAME> backfill" — topic lookup across hAIveMind + registry + channel history, returns everything known about that topic in one shot.
category: integrations
runtimes: [claude]
pii_safe: true
model: google/gemini-3-flash-preview
thinking: off
---

# discord-activity-tracker

**Model: Gemini Flash (google/gemini-3-flash-preview) — NON-NEGOTIABLE**
This skill always runs on Flash. It is a monitor/cron pattern. Never escalate to Sonnet or Opus for routine scans.
On-demand interactive use (e.g. <USER_NAME>asks "channel digest" in voice): Flash still. Only escalate if the task requires deep reasoning beyond scanning.

Tracks Discord channel activity, extracts TODOs, and keeps <USER_NAME>oriented across all channels.

## Triggers
- **Ping mode:** "ping me", "where am I", "quick status", "what am I working on", "status check"
- **Full digest:** "channel digest", "what's pending", "scan my channels", "what am I forgetting"
- **Heartbeat:** when `discordChannels` category is stale (>6h since last check)
- **Voice:** spoken TL;DR (top 3 channels) + full table posted to #discord-tasking-and-management (<DISCORD_CHANNEL_ID>)
- **Recent mode:** "recent activity", "where have I been", "what channels am I in", "active surfaces" — or called internally by worldview

---

---

## RECENT MODE

Triggered by: "recent activity", "where have I been", "active surfaces", "what channels am I in", or called by worldview as `wv-discord-activity` step.

**Goal:** Identify which Discord channels <USER_NAME>has personally sent messages in within a time window (default: last 4 hours, configurable). Returns a ranked list of active surfaces with topic context — used by worldview to frame what <USER_NAME>is currently working on.

### Why this is different from Ping
Ping mode scans all active channels for any activity. Recent mode scans for **<USER_NAME>s own messages** — channels where he's personally engaged. This tells worldview "here's the context <USER_NAME>is operating in right now."

### Recent Mode Steps

1. **Determine time window** — default 4h, accepts override ("last 2 hours", "today", "this session")
   - Map to Discord API lookback: compute `after` snowflake from current time minus window
   - Edge case: "this session" → use last seen timestamp from heartbeat-state.json if available

2. **Scan priority channels for <USER_NAME>s messages** — check each priority channel:
   ```
   message action=read channelId=[id] limit=30
   ```
   Filter messages by `sender_id = <DISCORD_CHANNEL_ID>` (<USER_NAME>s Discord ID).
   Only include channels where at least 1 message from <USER_NAME>exists within the window.

3. **Build active surfaces list** — for each matching channel:
   - Channel name + ID
   - <USER_NAME>s most recent message text (truncated to 60 chars)
   - Timestamp of last message
   - Topic context: last 3 messages from the channel (any author) for context

4. **Rank by recency** — most recent first.

5. **Output — structured (for worldview consumption):**
   ```json
   {
     "generatedAt": "ISO-timestamp",
     "windowHours": 4,
     "activeSurfaces": [
       {
         "channelId": "<DISCORD_CHANNEL_ID>",
         "channelName": "#discord-activity",
         "lastMessageAt": "2026-03-23T11:46:00-04:00",
         "lastMessageSnippet": "it",
         "topic": "Planning recent-activity skill for worldview"
       }
     ]
   }
   ```

6. **Output — human readable (Discord):**
   ```
   🗺️ **Active Surfaces** — last 4h
   
   • **#discord-activity** [11:46] — Planning recent-activity skill
   • **#hud** [10:06] — CTO ops, email bomb resolved
   • **#<PROJECT_NAME>** [09:15] — Backfill status check
   ```

7. **Store to hAIveMind:**
   ```bash
   mcporter call haivemind.store_memory \
     content="ACTIVE-SURFACES [ISO-date] window=[Nh]: channels=[#name1,#name2,#name3] topics=[topic1|topic2|topic3]" \
     category="operations"
   ```

### Recent Mode — Voice Output
One sentence: "You've been active in [N] channels in the last [window]: [top 2 channel names]."

---

## PING MODE

Triggered by: "ping me", "where am I", "quick status", "what am I working on", "status check"

**Ping mode is fast and light.** No full scan. No TODO extraction. Just: what's happening right now.

### Ping Steps

1. **Read registry** — load all channels where `priority: "active"` or `activityScore >= 2`
   - Also include any channel with `lastActive` within the past 48h (even if not marked active)
   - Skip `priority: "stale"` or `priority: "archived"` entirely

2. **For each active channel, read last 5 messages** (not 30 — ping is fast)
   - Extract: dominant topic in 10 words or less, any urgent signal (blocked/broken/urgent)
   - If `currentFocus` in registry is recent (<24h), use that instead of re-scanning

3. **Build ping table** — one line per channel:
   ```
   #channel-name — [10-word status] [time-ago]
   ```
   Examples:
   ```
   #ai-thread-and-channel-management — MCP registry + ping mode just shipped [now]
   #<PRODUCT_NAME>-engineering — Matilda's LD PR merged, no blockers [2d ago]
   #<PROJECT_NAME> — ELSER backfill shard 4 still processing [1d ago]
   #<VOICE_RUNTIME>-voice — Quiet, no recent activity [3d ago]
   ```

4. **Track lastPinged** — update `lastPinged` ISO timestamp per channel in registry
   - On next ping, channels with no new activity since `lastPinged` are marked `[no change]` and de-emphasized

5. **Output — Chat/Discord:**
   ```
   📍 **Status Ping** — Feb 25 2:45 PM
   
   🔴 Active:
   • #ai-thread-and-channel-management — MCP registry + ping mode shipped [now]
   • #<PRODUCT_NAME>-engineering — Matilda's LD PR merged, no blockers [2d ago]
   
   🟡 Watch:
   • #<PROJECT_NAME> — ELSER backfill shard 4 still processing [1d ago]
   
   ⚪ Quiet:
   • #<VOICE_RUNTIME>-voice — No recent activity [3d ago]
   ```
   Post to current channel (not #discord-tasking-and-management — ping is inline).

6. **Output — Voice:**
   Top 3 active channels only, one sentence each:
   ```
   "You're currently working on [channel 1]: [status]. 
   [Channel 2]: [status]. 
   [Channel 3]: [status]. 
   Full status posted to Discord."
   ```
   Send via: `curl -s -X POST http://<TAILSCALE_IP>:3335/speak -H "Content-Type: application/json" -d '{"text": "[voice summary]"}'`
   Then post full ping table to `#discord-tasking-and-management` (<DISCORD_CHANNEL_ID>).

### Ping vs Full Digest

| | Ping | Full Digest |
|---|---|---|
| Trigger | "ping me", "where am I" | "channel digest", "what's pending" |
| Messages read | 5 per channel | 30 per channel |
| TODO extraction | No | Yes |
| Registry update | lastPinged only | Full currentFocus/todos/activityScore |
| hAIveMind write | No (too frequent) | Yes |
| Speed | Fast (~10s) | Thorough (~60s) |
| Voice output | Top 3, 3 sentences | TL;DR headline |
| Post destination | Inline (current channel) | #discord-tasking-and-management |

---

## TOPIC LOOKUP MODE

Triggered by: "ping me [topic]", "ping me [channel-name]", "ping me [project]", "what's the status of [X]"

**Not a scan — a search.** Pull everything known about a topic from all sources and return it in one shot. No channel scanning needed.

### Detection
If `ping me` is followed by any word/phrase → topic lookup mode.
- `"ping me"` alone → multi-channel ping mode (existing)
- `"ping me <PROJECT_NAME>"` → topic lookup: "<PROJECT_NAME>"
- `"ping me ew-archiver"` → topic lookup: "ew-archiver"
- `"ping me the backfill"` → topic lookup: "backfill"
- `"ping me what's happening with auth"` → topic lookup: "auth"

### Lookup Steps

1. **hAIveMind search** (primary — fastest, most complete):
   ```bash
   mcporter call haivemind.search_memories query="[topic]" limit=10
   ```
   Extract: most recent entries, key decisions, current status, open items.

2. **Registry scan** (secondary — structured data):
   - Search `channels[*].currentFocus`, `channels[*].todos`, `channels[*].lastPingStatus` for topic match
   - Search `channels[*].name` and `channels[*].aliases` for channel name match
   - If channel match found → also read its `contexts/[channel-id].md`

3. **Channel history** (tertiary — only if steps 1+2 insufficient):
   - Identify which channel(s) most likely contain topic (by name/alias match in registry)
   - Read last 10 messages from that channel only
   - No GitHub, no Linear, no external APIs — local sources only

4. **Synthesize** — combine all sources into one response:
   ```
   📍 [Topic]: [current status in one sentence]
   
   Last activity: [when + where]
   Open items: [todos if any]
   Source: [haivemind / registry / #channel-name]
   ```

### Output — Chat
```
📍 **<PROJECT_NAME> backfill** — ELSER 90d backfill running, shard 4 still processing

Last activity: #<PROJECT_NAME>, 1d ago
Open: Check shard 4 completion, verify doc counts
Source: hAIveMind + #<PROJECT_NAME>
```

### Output — Voice
One sentence:
```
"[Topic] — [status]. [Open item if any]."
```
Example: *"<PROJECT_NAME> backfill is still running on shard four. No blockers reported."*

### Comparison Table Update

| | Topic Lookup | Ping | Full Digest |
|---|---|---|---|
| Trigger | "ping me [topic]" | "ping me" | "channel digest" |
| Source | hAIveMind + registry + channel | Registry + 5 msgs/channel | 30 msgs/channel |
| Scope | One topic, all sources | All active channels | All active channels |
| Speed | Very fast (~5s) | Fast (~10s) | Thorough (~60s) |
| Voice | 1 sentence | Top 3, 3 sentences | TL;DR headline |
| Post destination | Inline | Inline | #discord-tasking-and-management |

### lastPinged Schema Addition

Add to each channel entry in registry:
```json
{
  "lastPinged": "2026-02-25T14:45:00-05:00",
  "lastPingStatus": "MCP registry + ping mode shipped"
}
```

On repeat ping, if `lastActive < lastPinged` → show as `[no change since last ping]` in grey.

---

---

## Priority Channels (always scan these)

These channels get scanned every run. Add/remove as needed.

```json
{
  "priority": [
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>",
    "<DISCORD_CHANNEL_ID>"
  ],
  "extended": "scan only when --all flag or weekly run"
}
```

---

## Steps

### 1. Load registry
```bash
cat <LOCAL_PATH>/dev/contexts/channel-registry.json
```
Extract channel list + existing `currentFocus`, `todos`, `lastActive` for each.

### 2. Scan priority channels
For each priority channel ID:
```
message action=read channelId=[id] limit=30
```
Capture: message texts, authors, timestamps.

**Rate limiting:** 1 second pause between channel reads. Never scan >15 channels in one run without a pause.

### 3. Extract TODOs and topics

For each channel's messages, look for:

**Explicit TODO signals:**
- Lines starting with: `TODO`, `todo:`, `- [ ]`, `[ ]`
- Phrases: "need to", "follow up on", "remind me", "don't forget", "we need to", "I need to", "next step"
- Questions ending in `?` with no reply (open question = implicit TODO)
- Action assignments: "@jarvis", "can you", "please", "make sure"

**Topic extraction:**
- Dominant subject of last 10 messages (summarize in ≤10 words)
- Any named projects, ticket numbers (ENG-XXX), PR numbers

**Output per channel:**
```json
{
  "channelId": "...",
  "currentFocus": "...",
  "todos": ["...", "..."],
  "lastActive": "ISO timestamp of newest message",
  "activityScore": 0
}
```

**Activity scoring:**
- 0 — no messages in 14+ days
- 1 — messages but no TODOs
- 2 — TODOs present, resolved/discussed
- 3 — open TODOs, last active >2 days
- 4 — open TODOs, active today/yesterday
- 5 — urgent/blocked/critical signals ("blocked", "broken", "prod", "urgent", "down")

### 4. Update channel-registry.json
For each scanned channel, update in place:
```json
{
  "currentFocus": "...",
  "todos": [...],
  "lastActive": "...",
  "lastSummaryAt": "NOW",
  "priority": "active|watch|stale|archived",
  "activityScore": N
}
```

Priority rules:
- `activityScore >= 3` → `active`
- `activityScore 1-2` → `watch`
- `activityScore 0` or last active >7d → `stale`

### 5. Store to hAIveMind
For each channel with `activityScore >= 2`:
```bash
mcporter call haivemind.store_memory \
  content="ACTIVITY [channel-id] [channel-name] [ISO-date]: focus=[currentFocus] todos=[todos-count] score=[N] items=[todo-list]" \
  category="operations"
```

Also store the digest summary:
```bash
mcporter call haivemind.store_memory \
  content="CHANNEL-DIGEST [ISO-date]: active=[N] stale=[N] todos-total=[N] top-channels=[names]" \
  category="operations"
```

### 6. Produce channel digest

**Text format (Discord):**
```
📋 **Channel Digest** — Feb 25, 2026

🔴 **Active (TODOs pending):**
• **#ai-thread-and-channel-management** — "Building activity tracker" [today]
  └ TODOs: Finish skill, wire heartbeat, run backfill
• **#<PROJECT_NAME>** — "90d ELSER backfill" [2d ago]
  └ TODOs: Check shard 4 status

🟡 **Watch (recent, no open TODOs):**
• **#<PRODUCT_NAME>-engineering** — last active 1d ago
• **#<VOICE_RUNTIME>-voice** — last active 3d ago

⚪ **Stale (7+ days):**
• #forensics-case-1 (14d), #block-equity-audit (21d)

_Next scan: use "channel digest" or wait for heartbeat_
```

Post this to: `#discord-tasking-and-management` (<DISCORD_CHANNEL_ID>)

**Voice format (for /speak):**
```
[N] channels have open TODOs. Top priority: [channel-name] — [currentFocus]. 
[Second channel if score 5]. Full digest posted to #discord-tasking-and-management.
```

Send via:
```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "[voice summary]"}'
```

### 7. Update heartbeat-state.json
```bash
# Read current state
cat <LOCAL_PATH>/dev/memory/heartbeat-state.json

# Update discordChannels timestamp
# Set lastChecks.discordChannels = NOW (unix timestamp)
```

---

## Heartbeat Integration

**When spawning from heartbeat or cron:** always use `model=gemini-flash` — never Sonnet.
```
sessions_spawn task="run discord-activity-tracker" model="google/gemini-3-flash-preview"
```

Add `discordChannels` to the heartbeat rotation in `HEARTBEAT.md`:

| Category | Check | Score Guide |
|----------|-------|-------------|
| **discordChannels** | Channels with open TODOs, stale channels | 5=blocked/urgent in any channel, 4=TODO >3d old, 3=open TODOs today, 1=all clear |

**Cooldown:** Run at most once every 6 hours (check `lastChecks.discordChannels` in heartbeat-state.json).

**Heartbeat trigger condition:**
```
if (NOW - lastChecks.discordChannels > 6*3600*1000) → run scan
```

---

## Voice Mode Behavior

When invoked via voice ("what am I forgetting", "channel status", "what's pending"):

1. Run full scan (or use cached if <30min old)
2. Speak: TL;DR (2 sentences max) via `/speak`
3. Post full digest to `#discord-tasking-and-management` silently
4. Tell <USER_NAME>where details are: "Full digest in #discord-tasking-and-management, sir."

**Voice summary template:**
```
You have [N] open TODOs across [M] channels. 
[Top channel]: [currentFocus]. Full digest posted to Discord.
```

---

## Initial Backfill (one-time)

When running for the first time:
1. Scan ALL priority channels (not just active ones)
2. Use `limit=50` instead of 30 for deeper history
3. Store a `BACKFILL-COMPLETE [ISO-date]` entry to hAIveMind
4. Update `metadata.activityTracking.lastFullScan` in channel-registry.json

---

## Search Patterns (for recall)

```bash
# What was I working on in a channel?
mcporter call haivemind.search_memories query="ACTIVITY [channel-id]" limit=5

# Where was a topic discussed?
mcporter call haivemind.search_memories query="[topic keyword] activity" limit=10

# What are all open TODOs?
mcporter call haivemind.search_memories query="ACTIVITY todos" limit=20

# Latest digest
mcporter call haivemind.search_memories query="CHANNEL-DIGEST" limit=3
```

---

## Files Modified
- `contexts/channel-registry.json` — per-channel activity data
- `memory/heartbeat-state.json` — `lastChecks.discordChannels` timestamp
- hAIveMind — ACTIVITY + CHANNEL-DIGEST entries

## Notes
- Never scan more than 15 channels per run without rate limiting
- Voice summary is always ≤2 sentences
- TODOs are additive — new ones append, don't overwrite existing until marked done
- `voiceChannel: true` channels (<VOICE_RUNTIME>-voice) always appear in voice digest if score >=2
- <VOICE_RUNTIME>-voice channel activity = always surface to voice, even at score 1
