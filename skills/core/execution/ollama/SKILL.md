---
name: ollama
description: Use when running Ollama commands on <MAC_HOST> () — listing/pulling/showing/running models, inspecting templates, switching context. Captures the right SSH invocation, binary location, env vars, and the gotchas that have bitten before. Pair with /docker-switch for Docker Model Runner side-by-side.
category: execution
runtimes: [claude]
pii_safe: true
---

# Ollama on Mac

Mac runs Ollama as a desktop app on `<PRIVATE_IP>:11434`. From any other machine, `ssh <MAC_HOST> <ollama-command>`. From Mac, just `ollama`. **<USER_NAME>has corrected this multiple times — don't keep guessing paths.**

## Binary location & PATH

| Path | What | Notes |
|---|---|---|
| `/Applications/Ollama.app/Contents/Resources/ollama` | Real binary | Bundled with desktop app |
| `/usr/local/bin/ollama` | Symlink → real binary | Works in interactive shells |
| `/opt/homebrew/bin/ollama` | Symlink → `/usr/local/bin/ollama` | **Required for non-interactive SSH** because Mac's default SSH `$PATH` does NOT include `/usr/local/bin` |

If `ssh <MAC_HOST> ollama` returns "command not found", the `/opt/homebrew/bin` symlink got nuked. Recreate:
```bash
ssh <MAC_HOST> 'ln -sf /usr/local/bin/ollama /opt/homebrew/bin/ollama'
```

## Daily commands (from anywhere)

```bash
ssh <MAC_HOST> ollama list                       # what's pulled
ssh <MAC_HOST> ollama ps                         # what's loaded in Metal RAM right now
ssh <MAC_HOST> ollama pull <model>               # pull a model
ssh <MAC_HOST> ollama show <model>               # capabilities, parameters, license
ssh <MAC_HOST> ollama show --template <model>    # raw chat template (often `{{ .Prompt }}` passthrough)
ssh <MAC_HOST> ollama show --modelfile <model>   # full Modelfile (params, system, FROM)
ssh <MAC_HOST> ollama rm <model>                 # delete a model
ssh <MAC_HOST> ollama run <model>                # interactive REPL — usually skip, prefer pi/Cline/opencode
```

## API endpoint

OpenAI-compatible:
- LAN: `http://<PRIVATE_IP>:11434/v1`
- Local on Mac: `http://127.0.0.1:11434/v1`
- API key: literally `ollama` (no real auth)

Generic also has `OLLAMA_HOST=<PRIVATE_IP>:11434` env so its local Ollama CLI talks to Mac.

## Loading status / TTL

- Default keepalive: ~4 minutes idle → model auto-unloads from Metal
- First request after unload reloads (slow, model-dependent — 10–30s for 30GB)
- One model at a time on Metal compute; loading a second will fail or evict the first
- Practical Mac Metal compute graph limit: ~25GB safe, ~45GB risky, 60GB+ fails (despite 128GB unified RAM)

## Auto-sync pi config with pulled models

`pi-sync-ollama` (deployed at `~/.local/bin/pi-sync-ollama` on <WORKSTATION_HOST>/generic, `~/.local/bin/pi-sync-ollama` on Mac) hits Ollama's `/v1/models`, builds a fresh `~/.pi/agent/models.json` for every pulled model, and applies family-specific capability flags (Qwen 3.5/3.6 → `compat.thinkingFormat:"qwen"` + `reasoning:false` to avoid loops; Qwen3-VL → image input; Devstral → JSON tools; etc.). Backs up the old config to `models.json.bak.<timestamp>`.

```bash
# Standard workflow after pulling a new model:
ssh <MAC_HOST> ollama pull <new-model>
pi-sync-ollama                  # on whichever box you're working on
ssh <INFERENCE_HOST> ~/.local/bin/pi-sync-ollama   # if you want generic updated too
ssh <MAC_HOST> ~/.local/bin/pi-sync-ollama       # likewise for Mac

# Dry-run / preview what config would be written:
pi-sync-ollama --print

# Override endpoint (e.g. for a remote Ollama):
OLLAMA_BASE_URL=http://other-host:11434/v1 pi-sync-ollama
```

The sync script's family heuristics live in its `case` statement — extend it when new model families show up. Default behavior for unrecognized models is conservative (text-only, 32K context, reasoning off).

## Pulling from Hugging Face GGUFs

Ollama can pull HF GGUF directly using the `hf.co/<repo>` syntax:
```bash
ssh <MAC_HOST> ollama pull hf.co/unsloth/Qwen3.6-27B-GGUF:UD-Q4_K_XL
```

For non-GGUF (safetensors): write a Modelfile with `FROM <path-to-gguf>` and `ollama create <name> -f Modelfile`. Conversion to GGUF needs llama.cpp's `convert.py` first.

## Custom Modelfile (e.g. fix Qwen looping with min_p)

Ollama silently drops `repeat_penalty`/`presence_penalty` on Qwen 3.5/3.6 (Go runner has no penalty sampler). `min_p` is the one knob that *does* work:

```bash
ssh <MAC_HOST> '
ollama show qwen3.6:35b-a3b-coding-nvfp4 --modelfile > /tmp/qmf
echo "PARAMETER min_p 0.2" >> /tmp/qmf
ollama create qwen3.6-coder-fixed -f /tmp/qmf
'
```

## Known Mac-specific gotchas

| Symptom | Root cause | Fix |
|---|---|---|
| `ssh <MAC_HOST> ollama` → "command not found" | Non-interactive SSH `$PATH` excludes `/usr/local/bin` on macOS | Recreate `/opt/homebrew/bin/ollama` symlink (above) |
| `ssh <MAC_HOST> /opt/homebrew/bin/ollama` fails | Old assumption — that path was never canonical | Use `/usr/local/bin/ollama` or the symlink |
| Qwen3.5/3.6 tool calls loop or hang | Ollama Go runner has wrong tool-call renderer (Hermes JSON instead of Qwen XML) + drops penalty params + leaves `<think>` tags unclosed | Use `compat.thinkingFormat: "qwen"` in pi config + set `reasoning: false` to skip thinking phase entirely; or switch to non-Qwen models like devstral-small-2 |
| Vision broken on coding-fine-tuned variants | Coding post-training degrades the vision tower; nvfp4 quant compounds it | Use `qwen3-vl:32b` (purpose-built VL) for vision tasks |
| `ollama ps` says model loaded but inference hangs | Stale Metal compute state — usually after another model attempted to load | `ollama stop <model>` then `ollama run <model>` to reload clean |

## Coexistence with Docker Model Runner

Mac runs **both** Ollama (port 11434) and Docker Model Runner (port 12434) simultaneously. They're independent stacks but share the same Metal GPU — only one model can compute at a time across both. See `/docker-switch` skill for the Docker side.

`claude-local` (<WORKSTATION_HOST> zsh function at `~/.zshrc:880`) routes through LiteLLM proxy at `localhost:4000` → Ollama on Mac (NOT Docker, despite the misleading comment in `~/.litellm/start-proxy.sh`).

## Related skills

- `/docker-switch` — Docker Model Runner equivalent
- `/ollama-pull` — wrapper that pulls + auto-registers (note: <PROJECT_NAME> auto-registration is currently stale; only Anthropic models exposed)
- `/ollama-ps` — quick "what's loaded" check
- `/ollama-list` — quick model inventory
