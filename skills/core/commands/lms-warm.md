---
name: lms-warm
description: Unified LM Studio control on Mac — pull, load (with optional max context), warm prefill cache, unload, fresh-reload (unload-then-load), status, list. Use when the user says "warm up <model>", "preload", "prime the cache", "load <model>", "unload", "reload <model>", "fresh load", "switch to <model>", "download <model>", "what's loaded", "max context".
---

# /lms-warm — One command for all LM Studio control

A single shell command (`lms-warm`) on all 3 machines (<WORKSTATION_HOST>, <INFERENCE_HOST>, max). On Mac it runs locally; on <WORKSTATION_HOST>/generic it passthrough-SSHs to max.

## What "warm" actually means

LM Studio caches the prefix tokens (system prompt + early messages) after the first prefill. **Warm = load + send a tiny first request** so that prefix cache is built. Subsequent requests with the *same* prefix skip prefill (the slow 30–90s part on a 35B model with a long system prompt).

The win comes from **what** you cache, not from warming itself. Pre-warm with the exact system prompt you'll use later, and your real session is fast. Pre-warm with a generic "hello" and you've cached nothing useful.

## Subcommands

```bash
# DEFAULT — load + warm (use the system prompt you'll actually use later)
lms-warm <model-id> "<system prompt>"
lms-warm <model-id> "$(cat plans/my-plan.md)"           # prime with your real plan
lms-warm <model-id> "<system>" --max-ctx                # load with model's max context window
lms-warm <model-id> "<system>" --keep                   # also background-ping every 8 min

# FRESH — unload everything first, then load + warm (clean slot for the new model)
lms-warm fresh <model-id> "<system prompt>"
lms-warm fresh <model-id> "<system>" --max-ctx

# LOAD only (no warm, no unload of others)
lms-warm load <model-id>
lms-warm load <model-id> --max-ctx

# UNLOAD all currently loaded models
lms-warm unload

# DOWNLOAD a new model from HuggingFace (mixed case, MLX by default)
lms-warm pull lmstudio-community/Qwen3-Coder-Next-MLX-4bit
lms-warm pull mlx-community/Some-Model --gguf

# INSPECT
lms-warm --status      # what's currently loaded (= lms ps)
lms-warm --list        # all downloaded models (= lms ls)
lms-warm --stop        # kill the background keep-warm pinger
```

## Max context

`--max-ctx` flag loads the model with its full context window from this map (verified 2026-05-10):

| Model | Max ctx |
|---|---|
| `qwen3.6-35b-a3b-turboquant-mlx` | 262144 |
| `qwen/qwen3-coder-30b` | 262144 |
| `qwen/qwen3-coder-next` | 262144 |
| `qwen/qwen3-next-80b` | 262144 |
| `nemotron-cascade-2-30b-a3b` | 262144 |
| `nvidia/nemotron-3-nano` | 262144 |
| `gemma-4-31b-it-turboquant-mlx` | 131072 |
| `gemma-4-26b-a4b-it-turboquant-mlx` | 131072 |
| `gemma-4-26b-a4b-it` | 131072 |
| `llama-4-scout-17b-16e-instruct` | 10485760 |
| `zai-org/glm-4.7-flash` | 202752 |
| `glm-4.7-flash-mlx@4bit` | 202752 |
| `openai/gpt-oss-20b` | 131072 |
| `liquid/lfm2-24b-a2b` | 128000 |

**Cost note**: max context = bigger KV cache = more RAM. On a 64 GB Mac with the 35B 8bit model loaded (37 GB), full 262K context can push memory hard. Use `--max-ctx` when you need long-context tasks; skip it for short interactive sessions.

## Aliases (in opencode/PI model picker, NOT in this CLI)

The opencode/PI model picker resolves these short aliases. The `lms-warm` CLI takes the FULL model id (alias resolution doesn't happen in shell).

| Alias | Full model id |
|---|---|
| `qwen` | qwen3.6-35b-a3b-turboquant-mlx |
| `qwen-next` | qwen/qwen3-next-80b |
| `coder` | qwen/qwen3-coder-30b |
| `coder-next` | qwen/qwen3-coder-next |
| `glm` | glm-4.7-flash-mlx@4bit |
| `cascade` | nemotron-cascade-2-30b-a3b |
| `nemotron` | nvidia/nemotron-3-nano |
| `gemma` | gemma-4-26b-a4b-it-turboquant-mlx |
| `scout` | llama-4-scout-17b-16e-instruct |
| `gpt-oss` | openai/gpt-oss-20b |
| `lfm2` | liquid/lfm2-24b-a2b |

## Behavior when invoked

When this skill is called, parse the user's intent and run the matching subcommand via Bash:

- "warm up X" / "preload X" / "prime cache for X" → `lms-warm <full-id> [system]`
- "switch to X" / "load X fresh" / "reload X" → `lms-warm fresh <full-id> [system]`
- "load X" (no warm) → `lms-warm load <full-id>`
- "unload" / "free memory" → `lms-warm unload`
- "what's loaded" → `lms-warm --status`
- "what models do I have" → `lms-warm --list`
- "download X" / "pull X from HF" → `lms-warm pull <hf-path>`

If the user asks for "max context", append `--max-ctx`. If the user asks to "keep it warm" or "stay warm", append `--keep`.

If the user names a model by alias (qwen, coder-next, qwen-next, etc.), resolve to the full id from the table above before passing to lms-warm.

## Related

- `/plan` — the planning skill recommends an executor; output includes the exact `lms-warm` command to use
- `/cplan` — Claude planner that uses `/plan` skill content as system prompt
- LM Studio + opencode/PI configs are synced across all 3 machines (Mac is the host on `<PRIVATE_IP>:1234`)
