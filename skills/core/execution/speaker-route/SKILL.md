---
name: speaker-route
description: Route Jarvis voice responses to a house speaker. Mic stays on Discord/phone — only audio output is redirected. Speaker command and room names are configured in .env — not tied to any specific speaker system.
category: execution
runtimes: [claude]
pii_safe: true
---

# speaker-route — Route Jarvis Audio to House Speakers

The mic stays on Discord (phone). Jarvis's spoken response plays through whichever room speaker the user chooses.

## Configuration (.env)

The speaker system is fully configurable. Users define their own command and room names:

```env
# Command to send audio to a speaker
# Args: <room> "message text" [optional-volume]
# Example with Sonos: sonos-say
# Example with cast: catt cast_site --device "Kitchen"
# Example with Home Assistant: ha-speak
JARVIS_SPEAKER_CMD=sonos-say

# Room → speaker target mapping (pipe-separated: name:target)
# "target" is whatever your speaker command uses as the first argument
JARVIS_SPEAKER_ROOMS=kitchen:down|bedroom:up|upstairs:up|downstairs:down|bathroom:up|everywhere:all

# Default room when none is specified
JARVIS_SPEAKER_DEFAULT=down
```

## Reading config at runtime

```bash
SPEAKER_CMD="${JARVIS_SPEAKER_CMD:-sonos-say}"
SPEAKER_ROOMS="${JARVIS_SPEAKER_ROOMS:-kitchen:down|bedroom:up|upstairs:up|downstairs:down|everywhere:all}"
SPEAKER_DEFAULT="${JARVIS_SPEAKER_DEFAULT:-down}"
```

Parse room → target by splitting on `|` and matching `name:target`.

## Trigger phrases

- "respond in the kitchen/bedroom/upstairs/downstairs"
- "switch to [room] speaker"
- "speaker mode on" / "go into speaker mode"
- "speaker mode off" / "back to phone"
- "say that on the speaker"
- "follow me to the [room]"
- "voice mode" + room name

## How to route a single response

When the user says "say that on the speaker" or "respond in the kitchen":
1. Resolve the room → target from `$JARVIS_SPEAKER_ROOMS`
2. Strip markdown from response text
3. Run: `$SPEAKER_CMD <target> "<response text>" [volume]`
4. Keep the Discord text reply as normal

## Persistent speaker mode (stays on until turned off)

**Turn on:**
```bash
echo "<target>" > /tmp/jarvis-speaker-mode
```
Confirm in Discord only — do NOT call `$SPEAKER_CMD` for the activation message itself. Just reply: "Speaker mode on."
The speaker will pick up on the NEXT response, not this one.

**Check if active** (do this on every response EXCEPT the activation/deactivation command itself):
```bash
ACTIVE=$(cat /tmp/jarvis-speaker-mode 2>/dev/null)
```
If non-empty → also call `$SPEAKER_CMD $ACTIVE "<spoken summary>"` after your response.

**Turn off:**
```bash
rm -f /tmp/jarvis-speaker-mode
```
Confirm: "Speaker mode off — back to Discord."

## With volume

If the user says "quiet mode" or specifies a volume:
```bash
$SPEAKER_CMD <target> "response text" <volume>
```

## Spoken response format

**Normal voice mode (verbose OFF):** The response is already short and conversational. Send it directly to the speaker as-is — it's already Jarvis.

**Verbose mode (verbose ON):** The response is long and formatted. Never read the full verbose output to the speaker. Write a separate 1–3 sentence spoken summary in Jarvis voice — confident, dry, understated.

| Verbose Discord response | Spoken speaker version |
|--------------------------|------------------------|
| 40-line deployment report | "Deployment complete, sir." |
| Bulleted news brief with 8 items | "Top story: Iran talks resuming, blockade still in place." |
| Long code explanation | "Done. Fix is on the feature branch." |
| Detailed calendar summary | "Two calls today — standup at nine, <PROJECT_NAME> sync at two." |

The rule: if it fits in a sentence or two naturally, read it. If it's a wall of text or formatted output, summarize it like Jarvis would say it out loud.

## Graceful fallback

If `$SPEAKER_CMD` is not found or fails, log the error and respond in Discord only — never crash or leave the user without a response.

## Always check speaker mode

At the start of every response, silently check:
```bash
ACTIVE=$(cat /tmp/jarvis-speaker-mode 2>/dev/null)
```
If non-empty → append a speaker call after generating the response.
