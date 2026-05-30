#!/usr/bin/env bash
# qwen-do: run the Qwen Code CLI as a one-shot bounded executor.
#
# The "do" half of a plan/do/verify loop: a planner (a frontier model, or you) decides WHAT
# the next bounded step is and verifies the result; qwen-do just executes that one step with a
# fixed executor system prompt and saves a transcript. The executor does ONE step and stops; it
# does not plan the next step and does not spawn sub-agents.
#
# Why this exists: when the model doing the work is also allowed to plan, it drifts - launches
# its own sub-agents, kicks off long pipelines, and discovers bugs only after the fact. Splitting
# the roles (frontier model plans + verifies, a local model executes one bounded step) keeps the
# work cheap, fast, and correct.
#
# Project-agnostic: run from any repo. Transcripts go to ./.qwen-runs/ in the current project.
#
# Usage:
#   qwen-do "TASK PROMPT"            # fresh session, prompt as arg
#   qwen-do -f path/to/task.md       # prompt from a file
#   echo "TASK" | qwen-do            # prompt on stdin
#   qwen-do --warm "TASK"            # resume most recent session (carry context within a task)
#   qwen-do --resume <id> "TASK"     # resume a specific session id
#
# Env overrides (set these for your own setup - no defaults bake in any host/IP):
#   QWEN_MODEL     model id the local server exposes (REQUIRED unless set in ~/.qwen/settings.json)
#   QWEN_BASE_URL  OpenAI-compatible endpoint of your local model server (e.g. LM Studio/Ollama)
#   QWEN_API_KEY   placeholder key var name's value; most local servers ignore it
#   QWEN_APPROVAL  auto|auto-edit|yolo|default|plan   (default: auto)
set -euo pipefail

APPROVAL="${QWEN_APPROVAL:-auto}"
# Most local OpenAI-compatible servers ignore the key but the provider requires the var to exist.
export OPENAI_API_KEY="${QWEN_API_KEY:-${OPENAI_API_KEY:-local}}"

command -v qwen >/dev/null 2>&1 || { echo "qwen-do: 'qwen' not on PATH (install @qwen-code/qwen-code)" >&2; exit 127; }

RUNDIR="$PWD/.qwen-runs"
mkdir -p "$RUNDIR"
STAMP="$(date +%Y%m%dT%H%M%S)"
LOG="$RUNDIR/$STAMP.log"

# Session continuity. Default fresh; --warm resumes most recent; --resume <id> a specific one.
# Fresh-by-default avoids executor drift and stale context bleeding across tasks.
SESSION_ARGS=(--chat-recording)
case "${1:-}" in
  --warm)   SESSION_ARGS=(--continue --chat-recording); shift ;;
  --fresh)  shift ;;
  --resume) [[ -n "${2:-}" ]] || { echo "qwen-do: --resume needs a session id" >&2; exit 2; }
            SESSION_ARGS=(--resume "$2" --chat-recording); shift 2 ;;
esac

# Resolve the prompt: -f FILE, else args, else stdin.
PROMPT=""
if [[ "${1:-}" == "-f" ]]; then
  [[ -f "${2:-}" ]] || { echo "qwen-do: file not found: ${2:-}" >&2; exit 2; }
  PROMPT="$(cat "$2")"
elif [[ $# -gt 0 ]]; then
  PROMPT="$*"
elif [[ ! -t 0 ]]; then
  PROMPT="$(cat)"
fi
[[ -n "$PROMPT" ]] || { echo "qwen-do: empty prompt. Usage: qwen-do [--warm|--resume ID] \"TASK\" | -f FILE | stdin" >&2; exit 2; }

# Fixed executor system prompt: do the bounded step, smoke-test first, then STOP. Never plan ahead.
read -r -d '' SYS <<'SYSEOF' || true
You are the EXECUTOR in a plan/do/verify loop. A separate planner decides WHAT to do and
verifies your output; you only DO the single bounded step in this prompt.

Rules:
- Do exactly the step described. Do NOT plan or start the next task. Do NOT launch sub-agents.
  Do NOT do "while I'm here" extra work.
- SMOKE-TEST FIRST: before any slow/full-data/training run, prove the code on a tiny sample
  (a few hundred rows, or a hand-built micro example) and show that output. Never kick off a
  multi-minute run to discover a bug a 10-second test would have caught.
- A missing input or a failed gate is a BLOCK. Stop and report exactly what failed. Never
  lower a gate, never substitute-and-continue.
- Distrust perfect/implausible metrics (F1=1.0, AUC=1.0, a suddenly round huge count) -
  investigate, do not celebrate.
- Never print or commit secrets (.env, config files with credentials).
- End every run with this block:
  STEP - <PASS|BLOCKED>
  Commands run: <...>
  Key numbers: <the metrics/counts the prompt asked for>
  Surprises / deviations: <anything unexpected, or "none">
  Files changed: <paths, or "none">
SYSEOF

MODEL_ARGS=()
[[ -n "${QWEN_MODEL:-}" ]] && MODEL_ARGS=(--model "$QWEN_MODEL")
BASEURL_ARGS=()
[[ -n "${QWEN_BASE_URL:-}" ]] && BASEURL_ARGS=(--openai-base-url "$QWEN_BASE_URL")

echo "qwen-do: host=$(hostname) model=${QWEN_MODEL:-<settings.json default>} approval=$APPROVAL session=${SESSION_ARGS[*]} log=$LOG" >&2
{ echo "===== PROMPT ====="; echo "$PROMPT"; echo "===== OUTPUT ====="; } >>"$LOG"

qwen "$PROMPT" \
  --approval-mode "$APPROVAL" \
  --append-system-prompt "$SYS" \
  "${MODEL_ARGS[@]}" \
  "${SESSION_ARGS[@]}" \
  "${BASEURL_ARGS[@]}" \
  2>&1 | tee -a "$LOG"

echo >&2
echo "qwen-do: done. transcript: $LOG" >&2
