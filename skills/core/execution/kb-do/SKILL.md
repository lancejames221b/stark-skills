---
name: kb-do
description: Create a Cline Kanban implementation ticket that picks the right Anthropic model (Sonnet 4.6 by default, escalate to Opus 4.7 for architecture/security/judgment-heavy work) and reasoning effort based on the task content. Works in any git-repo project (<PROJECT_NAME>, <VOICE_RUNTIME>, <PRODUCT_NAME>, anywhere) — auto-registers the project on first ticket if not already registered. Use when the user says "kb-do", "kanban do", "create a kanban ticket to do X", "make a kanban implementation task", or when adding any non-planning Cline Kanban ticket. Sonnet 4.6 or Opus 4.7 only.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Do Skill

Create a **Cline Kanban** implementation ticket with **model and reasoning effort chosen based on the work**. Defaults to **Sonnet 4.6 + medium reasoning**; escalates to **Opus 4.7** for architecture, security, ambiguous trade-offs, and judgment-heavy work.

Model choices: **claude-sonnet-4-6** or **claude-opus-4-7**. No other models.

**Project-agnostic.** Works for any git repo: <PROJECT_NAME>, <VOICE_RUNTIME>, <PRODUCT_NAME>, hAIveMind — anywhere. Cline Kanban auto-registers a workspace the first time you pass its path to `task create`, so the same skill creates new projects implicitly. No web UI required — everything (project creation, ticket creation, linking, starting) is CLI-driven, which means it can be invoked from Discord/Jarvis, cron, or any automation that can shell out.

## When to use

Trigger on any of: `/kb-do`, "kb-do", "kanban do", "create a kanban ticket to <verb>", "make a kanban task", "add this to kanban", "have an agent do <X>", or any user request that ends with creating a Kanban ticket whose purpose is *implementation* (not planning — use `/kb-plan` for that).

Also invoke proactively when the user asks to add multiple Kanban tickets at once. Apply the model-selection logic to each one independently.

## Inputs

- **Required:** task description (free text)
- **Optional flags in args:**
  - `--project <path>` (defaults to current working directory)
  - `--title "<text>"` (default: derive from first line of description)
  - `--model opus|sonnet` (force a specific model, skip the heuristic)
  - `--effort low|medium|high|xhigh` (force a specific reasoning effort)
  - `--auto-review commit|pr|move_to_trash` (enables auto-review with this mode)
  - `--depends-on <task-id>` (link this task as waiting on another)

## Model selection heuristic

Apply these rules in order. First match wins.

### Force Opus 4.7 (`claude-opus-4-7`) when ANY of:

- Task involves **schema design** (new tables, columns with semantic meaning, multi-table refactors)
- Task involves **security-sensitive code** (auth, crypto, secret handling, permission models)
- Task is an **audit / review / analysis** producing recommendations (not just code)
- Task requires **defining semantics** (what is a "unique X?", "valid Y?", "canonical Z?")
- Task involves **migration safety** (live-DB changes, breaking API changes, data backfill semantics)
- Task spans **>5 files** or touches **>2 subsystems** (high cross-context reasoning load)
- Task description contains: "design", "architect", "decide", "evaluate", "trade-off", "should we", "audit", "review for"
- Task is **customer-facing copy** that needs careful tone / accuracy (sales decks, status updates, public docs)

**Reasoning effort for Opus:** default to `high`. Escalate to `xhigh` when the task description suggests novel design (no existing pattern in codebase) or high-stakes correctness (security, financial, data loss possible).

### Default to Sonnet 4.6 (`claude-sonnet-4-6`) for:

- Implementing a documented plan (plan exists; agent follows it)
- Adding tests (unit, integration, fixture-based) for existing code
- Refactoring with clear before/after spec
- Data migration scripts following a documented pattern
- API integration work (calling a documented external API)
- Adding columns/indexes that are mechanically specified
- File renames, import path updates, dependency upgrades
- Boilerplate generation, scaffolding, code formatting fixes

**Reasoning effort for Sonnet:**
- `low` — pure mechanical (file moves, formatting, dep version bumps)
- `medium` (default) — most implementation work
- `high` — multi-step pipelines, debugging, integration work where things might go wrong
- `xhigh` — rare for Sonnet; if it needs xhigh, consider escalating to Opus instead

### Cheapest option = Sonnet at low effort

For trivial mechanical work, use `claude-sonnet-4-6` at `low` reasoning effort. Do not consider any other model.

## Procedure

1. **Resolve project path.** Use `--project <path>` if given, else `pwd`.

2. **Apply the heuristic** to pick model and effort. Print the choice and the reason in plain English ("→ Opus + xhigh because this defines schema semantics for a 960M-row table").

3. **Compose the implementation prompt.** Include:
   - Goal (one sentence)
   - Reference to any plan file or related ticket the agent should read first
   - Inputs / data sources
   - Deliverables (be concrete: file paths, schemas, scripts)
   - Constraints (e.g., "additive schema only", "no plaintext secrets in artifacts", "use mcporter via ssh <INFERENCE_HOST> for external services")
   - Definition of done

4. **Create the task** via Python subprocess (avoids shell-quoting pitfalls):
   ```python
   import subprocess
   args = [
       '/usr/bin/node', '<LOCAL_PATH>/.local/bin/kanban', 'task', 'create',
       '--project-path', project,
       '--title', title,
       '--prompt', prompt,
       '--agent-id', 'claude',  # Claude Code agent — use this, not cline
   ]
   if auto_review_mode:
       args += ['--auto-review-enabled', 'true', '--auto-review-mode', auto_review_mode]
   r = subprocess.run(args, check=True, capture_output=True, text=True)
   ```

   **IMPORTANT:** Use `--agent-id claude`, NOT `--agent-id cline`. The household's cline config has only an OpenAI-compatible local-MLX provider, no Anthropic provider — passing `--cline-provider anthropic --cline-model claude-X` causes "Incorrect API key" failures. Claude Code (the `claude` agent) uses its own auth and works.

   **Model recommendation is advisory:** the `chosen_model` and `effort` from the heuristic are printed for the user to see ("→ Opus + xhigh because this defines schema semantics") but are NOT enforced via Kanban CLI flags. Claude Code uses whatever model is set at the user's session level (`/model` in Claude Code, or workspace defaults). Mention the recommendation in the prompt body if you want the agent to consider switching its session before starting.

5. **If `--depends-on <task-id>` was provided**, link the new task as waiting on that task:
   ```bash
   '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task link \
     --task-id <new-task-id> \
     --linked-task-id <depends-on-task-id> \
     --project-path <project>
   ```

6. **Report back** with:
   - Task ID
   - Chosen model + effort + one-sentence reason
   - Whether to start it now or leave in backlog

## Examples

### Example 1: schema design → Opus
User: `/kb-do design a credential_extracts table to normalize messages.text into structured rows`
- Heuristic match: "design" + "schema" + multi-table → **Opus + xhigh**
- Title: "Design credential_extracts schema"

### Example 2: mechanical column add → Sonnet low
User: `/kb-do add canonical_name and last_seen_at columns to bots table, backfill from messages`
- Heuristic match: mechanical column add, documented → **Sonnet + medium**
- Title: "Add canonical_name + last_seen_at to bots"

### Example 3: API integration → Sonnet medium
User: `/kb-do integrate binlist.net to enrich pan_first6 → issuing_bank in credential_extracts`
- Heuristic match: API integration, documented inputs → **Sonnet + medium**

### Example 4: security audit → Opus
User: `/kb-do audit our session token handling for vulnerabilities`
- Heuristic match: "audit" + security-sensitive → **Opus + xhigh**

### Example 5: forced override
User: `/kb-do --model sonnet --effort low rename references to old_table → new_table across the codebase`
- Override applied: **Sonnet + low**

### Example 6: <VOICE_RUNTIME> bug fix → Sonnet medium
User: `/kb-do --project ~/Dev/<VOICE_RUNTIME> fix the TTS queue draining out of order in <VOICE_RUNTIME>-voice`
- Heuristic: bugfix in known component, single subsystem → **Sonnet + medium**
- Title: "Fix TTS queue ordering"

### Example 7: cross-cutting <VOICE_RUNTIME> feature → Opus
User: `/kb-do --project ~/Dev/<VOICE_RUNTIME> design a speaker-routing arbitration layer between the gateway, voice service, and Sonos worker`
- Heuristic: "design" + spans 3 subsystems → **Opus + xhigh**

### Example 8: brand-new project (auto-registers in Cline Kanban)
User: `/kb-do --project ~/Dev/new-thing scaffold a basic Flask app with one health endpoint`
- Cline Kanban auto-registers `~/Dev/new-thing` on first task create (must be a git repo)
- Heuristic: scaffolding → **Sonnet + low**

## Driving from outside Claude Code

Cline Kanban is fully CLI-driven. Anything that can shell out to `/usr/bin/node <LOCAL_PATH>/.local/bin/kanban` (or remote-shell into <WORKSTATION_HOST> and run it) can use this skill's logic. That means:

- **Discord Jarvis**: a Discord command can take "/kb-do ..." text and run the same model-selection heuristic to fire off `kanban task create`. Cline Kanban becomes a visual launcher for tickets created from the phone.
- **Cron / scheduled agents**: a cron job can create a recurring ticket on the right model.
- **CI / git hooks**: post-merge hooks can create follow-up tickets.

The model strings (`claude-opus-4-7`, `claude-sonnet-4-6`) and reasoning levels (`low|medium|high|xhigh`) are stable Cline Kanban inputs — no special config needed beyond the workspace's existing Anthropic provider setup.

## Anti-patterns

- Do NOT default to Opus "to be safe" — that wastes inference cost on mechanical work.
- Do NOT default to Sonnet for security/architecture work — false economy.
- Do NOT pick a model without explaining why in your reply to the user. They should be able to override.
- Do NOT pick any model other than `claude-sonnet-4-6` or `claude-opus-4-7`. Sonnet at `low` effort is the cheapest option used here.

## Companion skills

- `/kb-plan` — when the work needs upfront design before implementation. Always uses Opus + plan mode.
- `/kanban` — passcode and service management for the Kanban server itself.
