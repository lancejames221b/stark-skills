---
name: kb-plan
description: Create a Cline Kanban planning ticket that always runs on Opus in plan mode with xhigh reasoning, regardless of the calling agent's model. Works in any git-repo project (<PROJECT_NAME>, <VOICE_RUNTIME>, <PRODUCT_NAME>, anywhere) — auto-registers the project on first ticket if not already registered. Use when the user says "plan this in kanban", "kb-plan", "kanban plan", "write a plan ticket", or wants design/architecture work decomposed before implementation. The ticket produces a written plan (saved as a markdown file in the project) that a follow-up implementation ticket executes.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Plan Skill

Create a **Cline Kanban** ticket that runs in **plan mode on Opus** with **xhigh reasoning**, regardless of which model the calling agent is on. This is for design, architecture, audit, and decomposition work that benefits from careful thinking before code is touched.

**Project-agnostic.** Works for any git repo: <PROJECT_NAME>, <VOICE_RUNTIME>, <PRODUCT_NAME>, hAIveMind — anywhere. No project-specific assumptions. Cline Kanban auto-registers a workspace the first time you pass its path to `task create`, so the same skill creates new projects implicitly.

## When to use

Trigger on any of: `/kb-plan`, "plan this in kanban", "kanban plan", "kb-plan", "write a plan ticket", "design a kanban task", "decompose with opus", or when the user explicitly asks for a plan-only Kanban ticket.

Also invoke proactively when the user asks to add a Kanban ticket whose work would obviously benefit from upfront design (schema changes, API surfaces, security-sensitive code, multi-system changes, novel-for-this-codebase work).

## Inputs

- **Required:** task description (free text, may span multiple lines)
- **Optional flags in args:**
  - `--project <path>` (defaults to current working directory)
  - `--title "<text>"` (default: derive from first line of description)
  - `--no-plan-mode` (rare — only if user explicitly wants the planner agent to also write code)

## What this skill produces

A Kanban backlog task that, when started:
1. Runs on Opus 4.7 with xhigh reasoning
2. Starts in plan mode (no code edits, just plan output)
3. Outputs a markdown plan file in the project (path specified in the prompt)
4. Moves to review when the plan is written

The plan file is the deliverable. A separate implementation ticket (use `/kb-do` for that) reads the plan and executes it.

## Procedure

1. **Resolve project path.** If `--project <path>` was given, use it. Otherwise use `pwd` (the current working directory).

2. **Verify Kanban CLI exists** (sanity check):
   ```bash
   ls <LOCAL_PATH>/.local/bin/kanban
   ```
   If missing, tell the user Kanban isn't installed and stop.

3. **Compose the planning prompt.** Always include:
   - Clear problem statement (from user's input)
   - Explicit instruction: "DO NOT write code. Produce a detailed plan file."
   - Required output path: `<project>/PLAN-<short-slug>.md` (or somewhere the user-specified)
   - Required plan structure: goal, prerequisites, file-by-file changes, validation steps, risks, rollback
   - Note that a follow-up ticket will execute the plan

4. **Create the Kanban task** with these fixed flags:
   ```bash
   '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task create \
     --project-path "<resolved-project-path>" \
     --title "PLAN: <short title>" \
     --prompt "<composed planning prompt>" \
     --start-in-plan-mode true \
     --agent-id claude
   ```

   Use Python subprocess if the prompt has shell metacharacters (dollar signs, quotes) — never inline a complex prompt directly into bash. Pattern:
   ```python
   import subprocess
   subprocess.run(['/usr/bin/node', '<LOCAL_PATH>/.local/bin/kanban', 'task', 'create',
       '--project-path', project, '--title', title, '--prompt', prompt,
       '--start-in-plan-mode', 'true',
       '--agent-id', 'claude',
   ], check=True, capture_output=True, text=True)
   ```

   **Why `--agent-id claude` (Claude Code) and NOT cline:** the household's cline config has only an OpenAI-compatible local-MLX provider, no Anthropic provider. Forcing cline + anthropic causes "Incorrect API key" failures. Claude Code uses its own auth and runs cleanly. (See `kb-status` of any successful task — they all run on agent=claude.)

5. **Capture and report the task ID.** Tell the user:
   - The task ID
   - The project it landed in
   - The expected plan file path
   - Whether to start it now (`task start --task-id <id>`) or leave in backlog

## Defaults

- **Agent:** `claude` (Claude Code) — uses its own configured model
- **Plan mode:** `true`
- **Model recommendation:** Opus 4.7 + xhigh reasoning (advisory in prompt body, since Claude Code's actual model is set per-session by the user via `/model` or workspace config)

## Why these defaults

- **Claude Code agent (`claude`):** The cline agent in this household has a broken provider config (OpenAI-compatible MLX server, no Anthropic provider) and fails with "Incorrect API key". Claude Code uses its own auth and works.
- **Plan mode:** prevents the planning agent from drifting into implementation. The plan file IS the deliverable.
- **Opus advisory:** mention the Opus + xhigh recommendation in the prompt body so the user can switch their Claude Code session before starting if they want — but kanban can't enforce model selection on the claude agent.

## Edge cases

- **User is already on Opus.** Doesn't matter — the Cline Kanban task runs on its own model setting, independent of the calling Claude Code agent. Always pass the flags explicitly.
- **Project path not yet registered in Cline Kanban.** Cline Kanban auto-registers any git repo path passed to `--project-path`. No separate `project create` command needed — the first task in a new project IS the project creation.
- **Project path not a git repo.** Cline Kanban only auto-registers git repos. If not a git repo, surface the error rather than silently failing — suggest `git init` if the user wants to use it.
- **User wants a different planner model** (e.g. Sonnet for cost): override `--cline-model` only if user explicitly says so. Default is non-negotiable.
- **Driving from outside Claude Code** (Discord/Jarvis, scripts, automation): the same `kanban task create` CLI is the API. Anything that can shell out to `/usr/bin/node <LOCAL_PATH>/.local/bin/kanban` can drive Cline Kanban — including the Discord Jarvis bot.

## Anti-patterns

- Do NOT skip plan mode "to save time" — the whole point of this skill is upfront thinking.
- Do NOT use Sonnet to plan unless the user specifically asks. Plans run once; their cost is amortized over the implementation work that follows.
- Do NOT produce the plan inline in the conversation. The plan goes into a Kanban task that runs on Opus with full project context.
