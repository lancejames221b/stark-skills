---
name: sonos
description: Send a TTS announcement to a Sonos speaker using a configurable voice profile. Uses a Chatterbox-style TTS service on <INFERENCE_HOST> for voice generation. Triggers on "tell <TEAM_MEMBER>", "announce", "say on sonos", "send message to kitchen/bedroom".
category: execution
runtimes: [claude]
pii_safe: true
---

# Sonos Announce Skill

Send a TTS message (using your configured voice profile) to any Sonos speaker on your local network.

## Required setup

- `VOICE_PROFILE` — name of the voice your TTS service should use (e.g. `default`, or the name of a trained Chatterbox voice profile)
- `TTS_HOST` — URL of your TTS service (e.g. `http://<INFERENCE_HOST>:3340`)

## Optional providers

- **Chatterbox TTS** — the default integration. Other TTS services with a compatible `/tts` endpoint work by changing `TTS_HOST`.

## Speakers

| Location | Command | IP |
|----------|---------|-----|
| Bedroom (upstairs/bathroom) | `up` | <PRIVATE_IP> |
| Kitchen (downstairs) | `down` | <PRIVATE_IP> |
| Both | `all` | — |

## Usage

```bash
sonos-say <up|down|all> "message" [volume]
sonos-vol <up|down|all> [0-100 | +N | -N]
```

### Examples

```bash
# Announce at specific volume (restores original after ~5s)
sonos-say down "Hey <TEAM_MEMBER>, dinner is ready." 20
sonos-say up "Good morning, here's your news." 15

# Announce at current volume
sonos-say down "Hey <TEAM_MEMBER>, <USER_NAME>wanted you to check your phone."

# Get current volume
sonos-vol down        # → Kitchen (downstairs): 10
sonos-vol up          # → Bedroom (upstairs): 45

# Set volume
sonos-vol down 25
sonos-vol up 30
sonos-vol all 20

# Adjust relative to current
sonos-vol down +10
sonos-vol up -5
```

## Volume behavior

When a volume is passed to `sonos-say`, it:
1. Saves the current volume
2. Sets the requested volume
3. Plays the announcement
4. Restores the original volume after 5 seconds

This means "quiet morning news" doesn't leave the speaker stuck at low volume.

## How it works

1. SSHes to `<INFERENCE_HOST>` (<PRIVATE_IP>) and calls the TTS service at `$TTS_HOST/tts` with `voice: $VOICE_PROFILE`
2. SCPs the generated wav back to <WORKSTATION_HOST> at `/tmp/sonos-say.wav`
3. Ensures HTTP server is running on <WORKSTATION_HOST> port 8765
4. Sends UPnP SetAVTransportURI + Play commands to the target Sonos

### `all` target — true Sonos grouping

When target is `all`, the script forms a real Sonos group instead of firing
two independent streams:

1. Discovers each speaker's UUID at runtime via `device_description.xml`
2. Joins **bedroom** to **kitchen** (coordinator) by `SetAVTransportURI` with
   `x-rincon:<KITCHEN_UUID>` on bedroom
3. Plays the announcement only on the coordinator (kitchen) — bedroom syncs
4. After ~5s, ungroups bedroom via `BecomeCoordinatorOfStandaloneGroup` so
   the speakers return to standalone (TTS is one-shot; lingering grouping
   would be surprising)

If UUID discovery fails, the script falls back to independent playback on
both speakers.

## When invoked

- Always use the configured `$VOICE_PROFILE` voice
- Default target is **down** (kitchen) unless user says "upstairs" or "bedroom"
- Keep messages natural and polite — spoken by the configured voice on the user's behalf
- If user just says a message without specifying where, default to `down` and confirm

## Notes

- HTTP server at <WORKSTATION_HOST>:8765 auto-starts if not running
- Script lives at `~/.local/bin/sonos-say`
- Can be called from any machine that can SSH to <INFERENCE_HOST> and reach <WORKSTATION_HOST>
