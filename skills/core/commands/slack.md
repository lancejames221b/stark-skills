Read Slack channel messages using the Slack API.

## Usage
- `/slack <channel_url>` — Read a specific message/thread from a Slack URL
- `/slack <channel_id>` — Read recent messages from a channel
- `/slack <channel_id> <count>` — Read last N messages from a channel

## How to parse arguments

Parse `$ARGUMENTS` to determine the request type:

1. **Slack URL** (contains `slack.com/archives/`):
   - Extract channel ID from URL path (e.g., `C0AR6A7MWF9`)
   - Extract message timestamp from `p` parameter (e.g., `p1775679172776959` → `1775679172.776959`)
   - If timestamp present: fetch thread replies via `conversations.replies`
   - If no timestamp: fetch recent channel history

2. **Channel ID** (starts with `C` or `G`, alphanumeric):
   - Fetch recent messages via `conversations.history`
   - Default limit: 10 messages

3. **Channel ID + count**:
   - Fetch specified number of messages

## API Token (BYOK)

Set your Slack user token (xoxp-...) in the `SLACK_TOKEN` env var. Never commit a real token to the repo.

```bash
export SLACK_TOKEN="<SLACK_USER_TOKEN>"
```

User tokens (xoxp) have broader read access than bot tokens — pick the type that matches your auth model.

## API Calls

**Read thread/replies:**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/conversations.replies?channel=$CHANNEL&ts=$TS&limit=50"
```

**Read channel history:**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/conversations.history?channel=$CHANNEL&limit=$COUNT"
```

**Get channel info:**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/conversations.info?channel=$CHANNEL"
```

**Get user info (resolve user IDs to names):**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://slack.com/api/users.info?user=$USER_ID"
```

## Output Format

For each message, display:
- Timestamp (human readable)
- User name (resolve from user ID)
- Message text (clean up Slack markup: `<@U123>` → resolve to name, `<url|text>` → text)
- Any attachments or file references

## Notes
- Use `xoxp-` (user) tokens for broader read access; `xoxb-` (bot) tokens are scope-restricted
- Slack timestamps use Unix epoch with microseconds (e.g., `1775679172.776959`)
- URL format: `p` prefix + timestamp without dot = `p1775679172776959`
- To convert URL timestamp: remove `p` prefix, insert `.` before last 6 digits
