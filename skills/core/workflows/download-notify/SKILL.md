---
name: download-notify
description: **Auto-notify when torrents/downloads complete.**
category: workflows
runtimes: [claude]
pii_safe: true
---
# Download Notification Skill

**Auto-notify when torrents/downloads complete.**

## When to Use
User says: "ping me when done" / "let me know when it's ready" / "notify me when complete"

## Pattern

### 1. Extract context
```javascript
{
  download_name: "torrent name or unique identifier",
  channel_id: "current session channel ID",
  threshold: 99  // completion percentage
}
```

### 2. Create cron job
```javascript
cron({
  action: "add",
  job: {
    text: "Check qBittorrent for '[DOWNLOAD_NAME]'. Run: curl -s http://127.0.0.1:9999/api/v2/torrents/info --user admin: and find torrent matching name. If progress >= [THRESHOLD]%, respond in channel [CHANNEL_ID]: ✅ [DOWNLOAD_NAME] is ready. Include file location. Then remove this cron job.",
    schedule: "*/5 * * * *"  // Every 5 minutes (recurring check)
  }
})
```

**Note:** For channel routing, include the channel ID in the instruction text. The cron system will deliver to that channel.

### 3. Verify and confirm
```bash
# Get the job ID from cron add response
cron list --includeDisabled | grep "[DOWNLOAD_NAME]"

# Confirm to user
"Monitoring [DOWNLOAD_NAME]. Will check every 5 minutes and notify here when complete."
```

## Key Rules
1. **Always use cron** — never shell scripts or background loops
2. **Include channel context** — use sessionKey to target correct channel
3. **Self-cleanup** — cron task removes itself after notification
4. **Verify creation** — check cron list before confirming to user
5. **Fast downloads** — for <15 min tasks, monitor manually instead

## Example

**User:** "Ping me when Leon is done downloading"

**Agent:**
```javascript
// Extract
const torrent = "Leon The Professional"
const channel = "<DISCORD_CHANNEL_ID>"

// Create cron
cron.add({
  text: `Check torrent 'Leon The Professional'. If complete, notify: ✅ Leon is ready at <LOCAL_PATH>/dev/plex/movies. Then remove this job.`,
  schedule: "*/5 * * * *",
  note: "Monitor Leon download",
  sessionKey: `agent:main:discord:channel:${channel}`
})

// Confirm
"Monitoring Leon. Will ping you every 5 minutes until complete."
```

## Implementation Script

For consistency, use helper:

```bash
#!/bin/bash
# <LOCAL_PATH>/dev/scripts/monitor_download.sh

DOWNLOAD_NAME="$1"
CHANNEL_SESSION="$2"
THRESHOLD="${3:-99}"

cron add \
  --text "Check download progress for '$DOWNLOAD_NAME' via qBittorrent API. If >= $THRESHOLD%, notify completion with file path. Remove this cron job after notification." \
  --schedule "*/5 * * * *" \
  --note "Monitor: $DOWNLOAD_NAME" \
  --sessionKey "$CHANNEL_SESSION"
```

## Verification Pattern

Before confirming to user:
1. ✅ Cron job created (check return code)
2. ✅ Job appears in `cron list`
3. ✅ SessionKey matches current channel
4. ✅ Schedule is valid

## Why This Works
- Cron runs in agent context → can send messages
- SessionKey routes notification to correct channel
- Self-cleanup prevents notification spam
- Verification ensures promise can be kept

## Never Do This
❌ Background shell scripts  
❌ nohup loops without messaging  
❌ "Mental notes" to check later  
❌ Promising notifications without verification
