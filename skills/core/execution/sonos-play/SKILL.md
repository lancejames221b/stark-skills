---
name: sonos-play
description: Play music on a Sonos speaker by searching YouTube with yt-dlp and streaming the mp3 over a local HTTP server. Use when the user says "play X on sonos", "play music downstairs/upstairs", "queue up X", "put on some Y", or otherwise asks for a song, artist, album, or playlist on the house speakers.
category: execution
runtimes: [claude]
pii_safe: true
---

# Sonos Play Skill

Search YouTube → download as mp3 → serve from <WORKSTATION_HOST> → stream via Sonos UPnP.

## Speakers

| Location | Command | IP |
|----------|---------|-----|
| Bedroom (upstairs) | `up` | <PRIVATE_IP> |
| Kitchen (downstairs) | `down` | <PRIVATE_IP> |
| Both | `all` | — |

Default target is **down** (kitchen) unless the user says upstairs/bedroom.

## Usage

```bash
sonos-play <up|down|all> "<search query>"
```

### Examples

```bash
sonos-play down "Boyz II Men End of the Road"
sonos-play up "Janet Jackson Rhythm Nation"
sonos-play all "lo-fi hip hop playlist"
sonos-play down "Stevie Wonder I Wish"
```

## How it works

1. Slugifies the query (lowercase, non-alphanum → `-`, capped at 60 chars)
2. If `/tmp/sonos-music/<slug>.mp3` does not exist, runs:
   ```bash
   yt-dlp -x --audio-format mp3 --audio-quality 0 \
     -o "<slug>.%(ext)s" "ytsearch1:<query>"
   ```
   `ytsearch1:` grabs the top YouTube result.
3. Ensures `python3 -m http.server 8766` is running in `/tmp/sonos-music/`
   (checks via `ss -ltn sport = :8766` — `lsof` hangs while Sonos is
   actively streaming; starts via `nohup … & disown` if missing).
4. Sends three UPnP SOAP calls to the target Sonos at port 1400:
   - `AVTransport#Stop`
   - `AVTransport#SetAVTransportURI` with `<CurrentURI>http://<PRIVATE_IP>:8766/<slug>.mp3</CurrentURI>`
   - `AVTransport#Play`

Cached mp3s are reused on repeat queries — no re-download.

### `all` target — true Sonos grouping

When target is `all`, the script forms a real Sonos group rather than firing
two independent streams:

1. Discovers each speaker's UUID at runtime via `device_description.xml`
2. Joins **bedroom** to **kitchen** (coordinator) with
   `SetAVTransportURI` → `x-rincon:<KITCHEN_UUID>` on bedroom
3. Plays the mp3 only on the coordinator (kitchen) — bedroom follows in sync

Unlike `sonos-say`, the speakers stay grouped after `sonos-play all` — music
is intentional, ongoing playback. To ungroup, run `sonos-play up "..."` or
manually send `BecomeCoordinatorOfStandaloneGroup` to bedroom.

If UUID discovery fails, the script falls back to independent playback on
both speakers.

## Notes

- Script lives at `~/.local/bin/sonos-play`
- Music cache: `/tmp/sonos-music/`
- HTTP server port: **8766** (sonos-say uses 8765 — distinct, both auto-start)
- Sibling skill `sonos` handles TTS announcements
