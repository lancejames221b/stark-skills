# Download Notification Skill

**Auto-notify when downloads complete using <PROJECT_NAME> cron.**

## Quick Use

User says: *"Ping me when [download] is ready"*

**You respond:**
```javascript
cron.add({
  text: "Check download '[name]'. If complete, notify: ✅ [name] is ready. Remove this job.",
  schedule: "*/5 * * * *",
  sessionKey: "[current_session_key]"
})
```

Then verify and confirm to user.

## Files
- `SKILL.md` - Full pattern documentation
- `<LOCAL_PATH>/dev/scripts/monitor_download.sh` - Helper script

## Global Integration
- Added to `AGENTS.md` as mandatory pattern
- Stored in haivemind (memory ID: <MEMORY_ID>)
- Applies to ALL channels, ALL downloads

## Origin
Created 2026-02-08 after Leon channel notification failure.
Promise Verification protocol applied to download monitoring.
