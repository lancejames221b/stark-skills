---
name: minimax
description: Control the MiniMax-M2.7 JANGTQ vmlx server on <MAC_HOST> (:8765). Best local coder <USER_NAME>owns (78% SWE-bench Verified) but holds ~60 GB Mac memory continuously. Use to start, stop, status-check, restart, tail logs, or smoke-test the server. Trigger phrases — "/minimax", "start minimax", "stop minimax", "minimax status", "is minimax loaded", "free minimax memory".
category: execution
runtimes: [claude]
pii_safe: true
---

# /minimax — JANGTQ MiniMax-M2.7 server control

MiniMax-M2.7 in JANGTQ format is **the best local coding model <USER_NAME>owns** — 78% SWE-bench Verified, beats Qwen3.6-27B and 35B-A3B. Runs via vmlx-engine (custom MLX TurboQuant runtime) since LM Studio's stock loader can't handle JANGTQ.

Server lives independently of LM Studio:

| | LM Studio | vmlx (this skill) |
|---|---|---|
| Port | 1234 | **8765** |
| Models | qwen, glm, gpt-oss, lfm2, scout, gemma | **minimax-m2.7-jangtq** |
| Auto-evict | yes (single-model JIT) | no — stays loaded |
| Memory | varies per loaded model | **~60 GB always** |

## Commands

```bash
minimax start     # bring server up (~60 GB Mac memory)
minimax stop      # shut down + free memory
minimax restart   # bounce
minimax status    # running? memory? ready?
minimax logs      # tail server log
minimax test      # send a sanity chat request
```

Script: `~/.local/bin/minimax` — deployed on <WORKSTATION_HOST>, generic, and max. SSH-aware (runs `launchctl` locally on max, via SSH from <WORKSTATION_HOST>/generic).

## When to stop it

Stop minimax when you need to load an LM Studio model **larger than ~50 GB** alongside it. With 128 GB total Mac RAM:

| LM Studio model | Size | Coexists with minimax? |
|---|---|---|
| qwen-turboquant, glm, gemma, gpt-oss, lfm2, qwen27 | ≤37 GB | ✓ |
| **llama-4-scout** | 61 GB | ✗ — `minimax stop` first |

The vmlx server holds ~60 GB Metal-wired memory continuously (per `launchd` plist `KeepAlive: true`). LM Studio's `unloadPreviousJITModelOnLoad` only manages its own port-1234 models; it does NOT touch vmlx.

## Endpoints

`http://<PRIVATE_IP>:8765/v1/...`

- `GET /v1/models` — list (returns `minimax-m2.7-jangtq` + full HF id)
- `POST /v1/chat/completions` — OpenAI format
- `POST /v1/messages` — Anthropic format (use with Claude Code via `ANTHROPIC_BASE_URL`)
- `POST /v1/embeddings`

## Use it from clients

| Client | How |
|---|---|
| Claude Code | `claude-lms-minimax` (sets `ANTHROPIC_BASE_URL` + `--model minimax-m2.7-jangtq`) |
| OpenCode | provider `vmlx-jangtq-mac/minimax` (or `/minimax-m2.7-jangtq`) |
| PI agent | provider `vmlx-jangtq-mac/minimax-m2.7-jangtq` |
| curl | examples above |

## Persistence

Managed by launchd plist `~/Library/LaunchAgents/com.<ORG_NAME>.vmlx-jangtq.plist` on max. `RunAtLoad: true`, `KeepAlive: true` — survives reboots, auto-restarts on crash. Logs at `~/.local/share/jangtq/logs/vmlx.log`.

## Sampling defaults baked in

vmlx server was started with these defaults (per MiniMax recommendations):
- `--default-temperature 1.0`
- `--default-top-p 0.95`
- `--reasoning-parser auto` (resolves to qwen3 for MiniMax)
- `--enable-auto-tool-choice` (tool calling enabled with `minimax` parser)

Per-request overrides work normally — these are just the floor when client doesn't specify.

## Troubleshooting

**Server not responding** → `minimax restart`. If still dead, `minimax logs` for the actual error.

**Out of memory at load** → check `vm_stat` on Mac. Probably an LM Studio model is loaded — unload it (`ssh <MAC_HOST> '~/.lmstudio/bin/lms unload --all'`) then `minimax restart`.

**Slow first response** → first request after load is ~6-8s (Metal kernel JIT cache cold). Subsequent requests fast. Acceptable.

**Want to change served port / model** → edit `~/Library/LaunchAgents/com.<ORG_NAME>.vmlx-jangtq.plist` then `minimax restart`.
