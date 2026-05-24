---
name: cplan
description: Call Claude (your existing Claude Code login — whichever account/host) to produce a plan, with optional custom system prompt. Default system prompt is the /plan skill (research-first, design-primer-aware, Qwen-ready format, recommends an executor model). Uses the local `claude` CLI so no API key juggling. Use when user says "/cplan", "claude plan", "cplan with system prompt", or wants Claude-as-planner without setting up keys.
category: execution
runtimes: [claude]
pii_safe: true
---

# /cplan — Claude planner via local `claude` CLI

A thin wrapper around the `claude` CLI on the current machine. Uses whichever Claude Code session you're already logged into (<MAC_HOST>, <WORKSTATION_HOST>, or wherever) — no API key file, no header juggling, just shells out to `claude --print --model <model> --permission-mode plan`.

By default the system prompt is the `/plan` skill content, so every cplan invocation gets:
- Step 0: Memory pass (`/load` + mcporter + prior plans + project tags)
- Step 1: Online research (versions, references, API docs, gotchas)
- Step 2: Clarify (only if genuinely ambiguous)
- Step 3: Write the plan in Qwen-ready format
- Step 3.5: Recommend the local executor model (`qwen`, `coder-next`, `qwen-next`, etc.)
- Step 4: Save plan to memory
- Step 5: Hand off

## Tool

The `cplan` shell command exists on all 3 machines (<WORKSTATION_HOST>, <INFERENCE_HOST>, max). It locates and invokes `claude` from PATH or common install dirs. Output goes to stdout (or `-o <file>` to save).

## Usage

```bash
# Default — use /plan skill as system prompt
cplan "build a settings page for <PROJECT_NAME> with dark mode toggle"

# Save the plan to a file
cplan -o ./plans/<PROJECT_NAME>-settings.md "build a settings page..."

# Custom system prompt (inline)
cplan -s "You are a senior security engineer. Produce a threat model." "review the auth flow in <PROJECT_NAME>"

# Custom system prompt from a file
cplan -s ./prompts/threat-model.md "review the auth flow in <PROJECT_NAME>"

# Override model (default is opus)
cplan -m sonnet "quick refactor plan for the discord realtime daemon"
cplan -m opus "complex architectural decision for the <PRODUCT_NAME> ingestion pipeline"

# Plain chat (no system prompt at all)
cplan --plain "what's the current best way to do server-side streaming in Next.js 15?"
```

## When to use vs alternatives

| Skill | Provider | Account | When to use |
|---|---|---|---|
| `/plan` | model-agnostic | depends on opencode/PI selection | You're already in opencode/PI and your model is set; this is the system prompt that drives whoever's selected |
| `/cplan` | Claude (CLI) | your current `claude` login | You want Claude specifically, from terminal, without worrying about which provider/billing |
| `/oplan` | main Claude (this session) | this session's account | Already in Claude Code; want Opus + full repo context inside the session |
| `/pplan` | local Ollama via PI | free / local | Sensitive plans, no cloud round-trip needed |

## Behavior when invoked

When `/cplan` is called:
1. Take the user's task as `$ARGUMENTS`.
2. If a custom system prompt was provided (text or file), pass it via `-s`.
3. If the user asked for a specific output file or a slug-style save, pass `-o ./plans/<slug>.md` (mkdir if needed).
4. Run via Bash:
   ```bash
   cplan [-s ...] [-m sonnet|opus] [-o ...] "<task>"
   ```
5. Surface the plan output to the user. If saved to a file, also print the path + the recommended executor command (`lms-warm <model> "<system>"` for warm-up + handoff).

## Notes

- Uses local `claude` CLI — no API key. Whatever account `claude` is logged into is what gets billed.
- Default model is `opus`. Switch to `sonnet` for faster/cheaper plans.
- Output is plain text to stdout unless `-o` is passed.
- `--permission-mode plan` is set so claude doesn't try to write files — it just produces the plan text.
- Pair with `/pdo` to execute the plan locally on the recommended Qwen model.

## Related

- `/plan` — the system-prompt content this skill uses by default
- `/pdo` — execute a saved plan with local Qwen
- `/oplan` — Opus plan inside Claude Code (current session, full context)
- `/pplan` — local-only plan via PI + Ollama
- `/lms-warm` — pre-load + prime the recommended executor model
