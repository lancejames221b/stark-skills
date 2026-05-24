---
name: gpu-free
description: Use to pause / resume Jarvis voice services (Whisper STT, Chatterbox TTS, Kokoro TTS docker) on <INFERENCE_HOST> to free RTX 4090 VRAM for testing larger Ollama models. Voice will not work while paused — explicit cost. Pairs with the <VOICE_RUNTIME> env-var toggles for durable on/off. Trigger phrases — "/gpu-free", "free up the gpu", "pause jarvis", "stop voice services so I can test a model", "resume jarvis".
category: execution
runtimes: [claude]
pii_safe: true
---

# /gpu-free — Pause/Resume Jarvis on <INFERENCE_HOST> to free GPU

<INFERENCE_HOST>'s RTX 4090 (24 GB) is shared by Ollama and the <VOICE_RUNTIME> voice stack (Whisper STT + Chatterbox TTS + Kokoro TTS docker). When testing a 17–24 GB model, the voice services hog ~5–9 GB of VRAM and can starve the model.

This skill stops them **temporarily** so you can test, then restarts them when done. For **durable** off-by-default mode (e.g., on-the-go text-only Jarvis), use the <VOICE_RUNTIME> env-var toggles instead — see "Durable mode" below.

⚠️ **Voice goes silent while paused** — no STT, no TTS, no Jarvis voice replies. Type to interact. Resume when finished.

## Durable mode (preferred for "off-by-default")

When <USER_NAME>wants the voice stack permanently off (e.g., on-the-go), set these env vars in `<LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env`:

```
JARVIS_STT_ENABLED=false
JARVIS_TTS_CHATTERBOX_ENABLED=false
JARVIS_TTS_KOKORO_ENABLED=false
```

Then `systemctl --user restart <VOICE_RUNTIME>-voice.service`. The startup hook (`src/service-control.js`, merged from `feature/voice-service-toggles` on 2026-05-06) automatically stops the matching systemd units and Docker container on every <VOICE_RUNTIME>-voice startup. Survives reboots without ritual.

`/gpu-free` is for AD-HOC, "I'm running a benchmark for the next 10 minutes" usage. Don't pile both mechanisms on top of each other for the same outcome — pick one per use case.

## What gets paused

| Service | VRAM | Notes |
|---|---|---|
| `whisper-service.service` (system) | ~1.4 GB | Whisper STT large-v3-turbo — <USER_NAME>s preferred STT |
| `jarvis-chatterbox-tts.service` (user) | ~3.9 GB | <USER_NAME>voice clone TTS |
| Kokoro TTS docker (port 8880) | ~1.1 GB | Backup TTS |

Plus any Ollama models currently warm — those are evicted via `keep_alive=0` so the next model load gets a clean GPU.

## Subcommands

```bash
gpu-free pause       # stop services + evict ollama models, show VRAM
gpu-free resume      # restart services, show VRAM + compute-apps
gpu-free status      # show current state without changing anything
gpu-free help
```

## Script location

`~/.local/bin/gpu-free` on <WORKSTATION_HOST> (drives generic via SSH). Distribute to other machines as needed via `scp ~/.local/bin/gpu-free <host>:~/.local/bin/`.

## Behavior notes

- Idempotent — `pause` when already paused is harmless; same for `resume`.
- Uses `ssh <INFERENCE_HOST>` — needs working SSH. Override target: `GENERIC_HOST=<other> gpu-free pause`.
- The `jarvis-whisper-stt.service` (user-level large-v3) is intentionally NOT in the pause list because <USER_NAME>disabled it as a duplicate on 2026-05-06 (kept the system-level large-v3-turbo). If it gets re-enabled later, add it back to `USER_SVCS` in the script.
- **Kokoro is a USER-level systemd unit** (`kokoro-tts.service` under `systemctl --user`), not a system unit. The script stops via `docker stop <container>` which kills both the unit and the container in one shot. As of 2026-05-06, `kokoro-tts.service` is also `disabled` at user level so it doesn't auto-restart on next login.
- Kokoro restart is best-effort: `gpu-free resume` tries `docker start` on the existing container. If you've fully removed/disabled it (current state), `gpu-free resume` won't bring it back — you must manually `systemctl --user enable --now kokoro-tts.service`.
- **Coexistence with env-var toggles**: if `JARVIS_*_ENABLED=false` is set in <VOICE_RUNTIME>-voice's `.env`, the <VOICE_RUNTIME> startup hook will re-stop services on every <VOICE_RUNTIME>-voice restart. So if you `gpu-free resume` AND `<VOICE_RUNTIME>-voice` restarts, services come up only briefly before being stopped again. Either flip env vars to `true` first, or use `gpu-free` only in AD-HOC bursts where <VOICE_RUNTIME>-voice isn't restarting.

## After resume — verify

```bash
gpu-free status
ssh <INFERENCE_HOST> 'curl -s http://localhost:8000/health'   # whisper
ssh <INFERENCE_HOST> 'curl -s http://localhost:8880/health'   # kokoro
```

If a service didn't come back, `journalctl --user -u <service> -n 20` (or `sudo journalctl -u <service>`) will show why.

## Why this exists

Created 2026-05-06 after testing qwen3.6:27b on <INFERENCE_HOST> and discovering 8.9 GB of VRAM was held by voice services, leaving only 715 MB free. Pausing them yielded full 23 GB free for the model.
