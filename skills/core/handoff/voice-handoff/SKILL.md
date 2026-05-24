---
name: voice-handoff
description: Hand off current context, task status, or summary to Jarvis Voice. Use when the user says "hand off to voice", "sending this to voice", or switches to voice mode.
category: handoff
runtimes: [claude]
pii_safe: true
metadata: {
    "openclaw":
      {
        "emoji": "🗣️",
        "skillKey": "voice-handoff",
      },
  }
---

# Voice Handoff

Transfer context to the Jarvis Voice bot so it can brief the user immediately upon voice join.

## Usage

When the user wants to continue in voice, or needs Jarvis Voice to know about a completed task/decision:

1.  **Summarize** the current state/context (1-2 sentences).
2.  **Post** it to the voice handoff endpoint.

## Command

```bash
curl -X POST http://<TAILSCALE_IP>:3335/handoff \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <HUD_POST_TOKEN>" \
  -d '{
    "channel": "current-channel-name",
    "channelId": "channel-id", 
    "summary": "Brief summary of what was just done or discussed.",
    "topic": "Optional Topic",
    "source": "text-agent"
  }'
```

*Note: Replace `current-channel-name`, `channel-id`, `summary`, and `topic` with actual values.*

## Example

User: "Hand off to voice."
Agent:
1.  Summary: "User is asking about Roku controls. I just updated the skill to support 'Caturday mode' which sets volume to 23."
2.  Command:
    ```bash
    curl -X POST http://<TAILSCALE_IP>:3335/handoff \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer <HUD_POST_TOKEN>" \
      -d '{
        "channel": "general",
        "channelId": "123456789",
        "summary": "Updated Roku skill with Caturday mode (volume 23). Ready for testing.",
        "topic": "Roku Control",
        "source": "text-agent"
      }'
    ```
3.  Reply: "Handed off. Jarvis is ready in voice."
