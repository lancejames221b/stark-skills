---
name: model-switch
description: Use when switching the loaded Ollama model on <MAC_HOST> (:11434), checking what's loaded, listing available models, or setting PI's default model. Replaces the docker-switch workflow now that Ollama is the primary local-inference backend. Trigger phrases — "/model-switch", "switch ollama model", "load qwen", "load nemotron", "what's loaded on <MAC_HOST>", "set pi default to".
category: execution
runtimes: [claude]
pii_safe: true
---

# Ollama Model Switcher

Switch the loaded Ollama model on Mac. Backed by `~/.local/bin/model-switch` — a thin curl wrapper around Mac's Ollama API at `$OLLAMA_HOST` (defaults to `http://<PRIVATE_IP>:11434`).

Pair: `/ollama` for general Ollama ops; `/docker-switch` for the legacy Docker Model Runner path (rarely used now).

## Commands

```bash
model-switch <alias|full-name>     # warm a model (load into VRAM, ~10–30s for first load)
model-switch list                  # show currently loaded
model-switch ls                    # show all available models on Mac
model-switch unload <name>         # force-unload (sends keep_alive=0)
model-switch default <alias>       # set PI's defaultModel on the LOCAL machine
model-switch help                  # full reference + alias table
```

From any machine, the script talks to Mac directly via `$OLLAMA_HOST`. From Mac, it works the same.

## Aliases (curated)

| Alias | Full name | Notes |
|---|---|---|
| `qwen36-a3b` | `qwen3.6:35b-a3b` | **PI default — primary coding model** |
| `qwen36-coding` | `qwen3.6:35b-a3b-coding-nvfp4` | Coding-tuned variant, faster (FP4) |
| `qwen36` | `qwen3.6:latest` | Latest qwen3.6 (Q4) |
| `qwen36-27b` | `qwen3.6:27b` | Lighter qwen3.6 |
| `nemotron` | `nemotron-cascade-2:latest` | Long context (was old PI default) |
| `nemotron-3` | `nemotron-3-super:latest` | 123B heavyweight reasoner |
| `qwen3-coder` | `qwen3-coder:30b` | MoE coding |
| `qwen235` | `qwen3:235b-a22b` | The big one (142 GB, will swap) |
| `qwen3-4b` | `qwen3:4b` | Voice orchestrator (always-warm via unloader pin) |
| `gemma4` | `gemma4:latest` | Vision/multimodal |
| `lfm2` | `lfm2:latest` | LFM2 MoE |
| `laguna` | `laguna-xs.2:latest` | Laguna XS |

Pass any full Ollama name not in the table and it loads as-is.

## Common workflows

**"Switch to qwen3.6 for coding"**
```bash
model-switch qwen36-a3b
```

**"What's actually loaded right now?"**
```bash
model-switch list
```

**"Make qwen3.6 the PI default"** (local machine only — run on each box)
```bash
model-switch default qwen36-a3b
```

**"Free Mac's GPU"**
```bash
model-switch unload nemotron      # specific model
# or
ssh <MAC_HOST> ollama stop --all          # all models (use the /ollama skill)
```

## Interaction with the unloader

`<LOCAL_PATH>/dev/scripts/ollama-unloader.py` (running as `ollama-unloader.service` on <INFERENCE_HOST>) polls `<PRIVATE_IP>:11434/api/ps` every 10s. When >1 model is loaded, it evicts non-pinned ones via `keep_alive=0`. Pinned (`PINNED_PAIRS`) currently:
- `qwen3:4b` — voice orchestrator
- `qwen3.5:35b-a3b` — sub-agent brain
- `qwen3.6:35b-a3b` — `/pdo` coding model (added 2026-05-05)

Switching to a non-pinned model and switching away will let the unloader free its VRAM as expected. Pinned models won't get evicted *by the unloader* — but Ollama's natural 5-min idle keep_alive still applies (so they unload if unused, just on Ollama's clock, not the unloader's).

## When to use this vs `/ollama`

| Task | Use |
|---|---|
| Switch what's loaded | **`/model-switch`** |
| List loaded / available | **`/model-switch list` or `ls`** |
| Set PI default | **`/model-switch default`** |
| Pull a new model | `/ollama` (uses `ollama pull`) |
| Inspect template / capabilities / params | `/ollama` |
| Recreate the `/opt/homebrew/bin/ollama` symlink | `/ollama` |

## Notes

- Requires `~/.local/bin/model-switch` on PATH. Distributed by copying to `/tmp/model-switch` on the target then `mv /tmp/model-switch ~/.local/bin/`.
- First load of a 30+ GB model takes ~15s (cold) or ~2s (already in OS page cache). Switching between previously-warmed models is sub-second.
- Loading a second model doesn't crash anything on Ollama (unlike Docker Model Runner) — both share VRAM until eviction.
