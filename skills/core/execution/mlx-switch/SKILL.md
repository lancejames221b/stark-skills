---
name: mlx-switch
description: Use when switching the local MLX inference server model on Mac, checking what model is loaded, monitoring downloads, or configuring Cline/Roo Code to use a local model.
category: execution
runtimes: [claude]
pii_safe: true
---

# MLX Model Switcher

Local MLX inference server on <MAC_HOST> (:8080). OpenAI-compatible. One model loaded at a time — model field in requests is cosmetic, server always uses the loaded model.

## Switch Model

```bash
ssh <MAC_HOST> "bash /usr/local/bin/mlx-switch <alias>"
```

Wait for ready:
```bash
until ssh <MAC_HOST> "curl -sf http://localhost:8080/v1/models >/dev/null 2>&1"; do sleep 4; done && ssh <MAC_HOST> "tail -1 /tmp/mlx-server.log"
```

## Available Models

| Alias | Model ID | Context | Type | Best For |
|-------|----------|---------|------|----------|
| `qwen36big` | mlx-community/Qwen3.6-35B-A3B-4bit | 256K | MoE 35B/3B | **Default coder (73.4% SWE-bench, ~91 tok/s)** |
| `coder-next` | mlx-community/Qwen3-Coder-Next-4bit | 256K | MoE 80B/25B | Code backup |
| `gemma` | mlx-community/gemma-4-26b-a4b-it-4bit | 256K | MoE 26B/4B | Vision/multimodal |

## Cline / Roo Code Config

- **Base URL**: `http://<PRIVATE_IP>:8080/v1`
- **API Key**: any non-empty string (e.g. `local`)
- **Model**: must match the exact model ID currently loaded (e.g. `mlx-community/Qwen3-Coder-Next-4bit`)
- **Vision**: only `gemma` supports image/screenshot input
- **Thinking preamble**: Qwen3.x models output `<think>` blocks — add `/no_think` to system prompt or use `devstral2`/`coder-next` instead

## Check Current Model

```bash
ssh <MAC_HOST> "curl -s http://localhost:8080/v1/models | python3 -c 'import json,sys; [print(m[\"id\"]) for m in json.load(sys.stdin)[\"data\"]]'"
# Note: lists ALL cached models, not just active one
# Active model = what's in the plist:
ssh <MAC_HOST> "/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:2' ~/Library/LaunchAgents/com.<ORG_NAME>.mlx-server.plist"
```

## Monitor Download

```bash
ssh <MAC_HOST> "tail -5 /tmp/mlx-devstral2.log && du -sh ~/.bun/cache/huggingface/hub/models--mlx-community--Devstral-2-123B-Instruct-2512-4bit/ 2>/dev/null"
```

Cache location: `/Users/<USER_NAME>/.bun/cache/huggingface/hub/`
HF_TOKEN: stored in `~/.zprofile` and plist env on Mac.

## Add New Model

1. Add `alias)  echo "mlx-community/Model-ID-4bit" ;;` to `/usr/local/bin/mlx-switch` case statement
2. Add to model list in `/usr/local/bin/mlx-download`
3. Reload: `ssh <MAC_HOST> "bash /usr/local/bin/mlx-switch <alias>"`

## Common Issues

| Problem | Fix |
|---------|-----|
| `declare -A` error | Mac uses bash 3.2 — script uses `case` statement, not associative arrays |
| Cache not found | Plist needs `HF_HUB_CACHE=/Users/<USER_NAME>/.bun/cache/huggingface/hub` |
| Model field ignored | mlx_lm.server loads one model at startup — set Cline model to match active |
| `<think>` blocks breaking tool calls | Use `devstral2`, or add `/no_think` to system prompt |
| Architecture not supported | Nemotron (NemotronH_Nano) not supported in mlx_lm 0.31.3 |
