---
name: qwen-do
description: Run the Qwen Code CLI as a one-shot bounded executor in a plan/do/verify loop. A frontier model (or you) plans the next bounded step and verifies the result; qwen-do makes a local model do exactly that one step, smoke-test first, then stop. Use when you want a cheap local model to do grunt coding while a smarter orchestrator keeps it on rails.
category: workflows
runtimes: [claude, qwen]
pii_safe: true
tier: STARK
triggers:
  - "qwen do"
  - "have qwen do"
  - "let the local model do"
  - "plan do verify"
  - "delegate this step to qwen"
  - "run this on the local executor"
---

# qwen-do - local executor for a plan/do/verify loop

Splits the orchestrator and executor roles so the model doing the work does not also plan it.
A frontier model (the planner/verifier) decides the next bounded step and checks the result;
`qwen-do` runs a local Qwen Code session that does exactly that one step and stops.

## Why

When the model doing the work is also allowed to plan, it drifts: it launches its own
sub-agents, kicks off multi-hour pipelines, and discovers bugs only after the run finishes.
Separating the roles keeps each step cheap, fast, and verifiable. The planner spends its
(expensive) tokens on judgment; the local model spends its (free) tokens on typing.

## The loop

1. **Plan** - the orchestrator picks the *smallest* next step (prefer "write the fix + a <30s
   unit test, run it, show output" over "do the whole feature").
2. **Do** - `qwen-do -f step.md` (or inline). The wrapper layers a fixed executor system prompt:
   do-one-step-then-STOP, smoke-test-first, block-don't-substitute, distrust-perfect-metrics.
3. **Verify** - the orchestrator reads the transcript (`./.qwen-runs/<stamp>.log`) and
   independently re-checks the gate. Read the "Surprises" line first. Then authorize the next
   step or send it back.

## Usage

```bash
qwen-do "TASK: <one bounded step>. Smoke-test on <tiny sample> first, show that output,
then run for real. STOP and report."

qwen-do -f path/to/step.md          # feed a STOP-gated task file
qwen-do --warm "TASK: <next step>"  # carry context across steps of ONE task
echo "TASK" | qwen-do               # prompt on stdin
```

## Preferred channel for an interactive, watched, warm run: tmux over ssh

`qwen-do` is the default and is fresh-per-step (no warm carryover unless `--warm`). When you instead
want a PERSISTENT warm qwen REPL that a human can also watch live, run `qwen --yolo` in a `tmux`
session ON the executor box and drive it over ssh. Prefer this over any terminal-control MCP that
screen-scrapes a GUI terminal (those need the app open, render the TUI as garbage when read, time out
on long inference, and die if the machine sleeps).

```bash
# start a detached session running the interactive REPL
ssh host 'tmux new-session -d -s NAME -c REPO \
  "export QWEN_MODEL=<model> QWEN_BASE_URL=<url> QWEN_CODE_SUPPRESS_YOLO_WARNING=1; qwen --yolo"'
# fire a step: ship a quote-heavy prompt to a file, send it, then send Enter SEPARATELY
base64 -w0 step.md | ssh host 'base64 -d > /tmp/step.md'
ssh host 'tmux send-keys -t NAME "$(cat /tmp/step.md)"; sleep 1; tmux send-keys -t NAME Enter'
# read (clean) and scrape scrollback for results
ssh host 'tmux capture-pane -t NAME -p'           # current screen
ssh host 'tmux capture-pane -t NAME -p -S -150'   # scrollback
```

Gotchas: send the prompt text and Enter as TWO `send-keys` calls (combining can race into a partial
submit); ship quote-heavy prompts via a file, never interpolate inline quotes into the ssh+tmux line;
VERIFY artifacts on disk (ls / git diff / re-run the smoke), never trust the pane text. A human
watches by attaching to the SAME session: `tmux attach -t NAME`.

## Configuration (no host/IP baked in)

Set these for your own local model server (LM Studio, Ollama, vLLM, anything OpenAI-compatible):

| Env var        | Meaning                                                            |
| -------------- | ------------------------------------------------------------------ |
| `QWEN_MODEL`   | model id the server exposes (or set `model.name` in `~/.qwen/settings.json`) |
| `QWEN_BASE_URL`| OpenAI-compatible endpoint URL of the server                       |
| `QWEN_API_KEY` | placeholder key (most local servers ignore the value)              |
| `QWEN_APPROVAL`| `auto` (default) \| `auto-edit` \| `yolo` \| `default` \| `plan`   |

A capable local coder model is recommended (e.g. a Qwen3 coder / 30B-class MoE). The wrapper is
model-agnostic; pick whatever your server runs well.

## Sessions

Fresh by default (no context carryover) for robustness and to prevent executor drift. Use
`--warm` only to carry conversation context across the steps of ONE task; `--resume <id>` for a
specific session. If your local server keeps the model resident, there is no weight cold-start
between calls, so fresh sessions cost little.

## The rule that makes this work: SMOKE-TEST FIRST

Every code change proves itself on a tiny sample (a few hundred rows, or a hand-built micro
example) in under ~30s BEFORE any full-data or training run. This is baked into the executor
system prompt; restate it in each step prompt. A step that would run for minutes and has not
been smoke-tested is a BLOCK.

## Install

Requires the Qwen Code CLI (`npm i -g @qwen-code/qwen-code`) and a configured provider in
`~/.qwen/settings.json` (or the env vars above). Then put the wrapper on PATH:

```bash
install -m 0755 qwen-do.sh ~/.local/bin/qwen-do
```

Transcripts are written to `./.qwen-runs/` in the working repo - add that to `.gitignore`.

## Files

- `qwen-do.sh` - the wrapper. Project-agnostic, no hard-coded hosts or credentials.
