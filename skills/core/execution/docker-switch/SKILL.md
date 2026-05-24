---
name: docker-switch
description: Use when switching the local Docker Model Runner model on <MAC_HOST> (:12434). Handles loading/unloading models, checking what's running, and configuring Cline/opencode to use a specific local model. Only one model can run at a time on Metal.
category: execution
runtimes: [claude]
pii_safe: true
---

# Docker Model Switcher

Docker Model Runner on <MAC_HOST> (:12434). OpenAI-compatible. **One model at a time** — loading a second crashes Metal compute.

## Switch Model

From any machine (<WORKSTATION_HOST>, <INFERENCE_HOST>):
```bash
ssh <MAC_HOST> "docker-switch <alias>"
```

From Mac directly:
```bash
docker-switch <alias>
```

## Available Models

| Alias | Model ID | Size | Best For |
|-------|----------|------|----------|
| `coder-next` | docker.io/ai/qwen3-coder-next:latest | 45GB | Planning, architecture (71.3% SWE-bench) |
| `qwen36` | docker.io/ai/qwen3.6:latest | 21GB | Code generation (68.2% SWE-bench) |
| `devstral` | docker.io/ai/devstral-small-2:latest | 14GB | Agentic coding (68% SWE-bench, fast) |
| `gemma4` | docker.io/ai/gemma4:26B | 16GB | Vision/multimodal |
| `nemotron` | docker.io/ai/nemotron3:latest | 22GB | Long context (1M tokens) |
| `qwen3coder` | docker.io/ai/qwen3-coder:30B-A3B-UD-Q4_K_XL | 16GB | Coding MoE |

## Check Current Model

```bash
ssh <MAC_HOST> "docker-switch list"
```

## <USER_NAME>s Workflow

- **Planning phase** → `ssh <MAC_HOST> "docker-switch coder-next"`
- **Coding phase** → `ssh <MAC_HOST> "docker-switch qwen36"`

## Cline / opencode Config

- **Base URL**: `http://<PRIVATE_IP>:12434/v1`
- **API Key**: `sk-local`
- **Model ID**: full Docker Hub ID (e.g. `docker.io/ai/qwen3.6:latest`)

## Common Issues

| Problem | Fix |
|---------|-----|
| Compute error 500 | Two models loaded — run `ssh <MAC_HOST> "docker-switch <alias>"` to flush and load one |
| Model not found | Use full ID or supported alias |
| Slow first response | Model loading into Metal RAM — normal for first request |
| TTL expiry | Models auto-unload after ~4min idle — just make a request to reload |

## Metal Limits on Mac (128GB)

Models over ~25GB risk Metal compute errors when another model is also loaded.
Always use `docker-switch` (which unloads all first) rather than loading directly.
