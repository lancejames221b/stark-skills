---
name: oplan
description: Opus PLAN — produce a structured implementation plan using main Claude (Opus, full context, all tools) in the same format /pplan emits. Output is saved as a markdown plan file that /pdo can execute locally. Use when planning needs cloud-tier reasoning OR full repo context, but execution should stay private. Trigger phrases — "/oplan", "opus plan", "plan with opus", "claude plan and pi do".
category: planning
runtimes: [claude]
pii_safe: true
---

# /oplan — Opus PLAN (cloud planner, local executor)

Pair to `/pplan`. Produces the same plan structure but uses **main Claude (Opus, this session)** as the planner — getting cloud-tier reasoning, full repo context, brainstorming-skill rigor — then saves to a file that `/pdo --plan` can execute locally.

## When to use this vs /pplan vs /kb-plan

| Skill | Planner | Use when |
|---|---|---|
| `/pplan` | local PI + Ollama | Plan content is sensitive; you want everything local |
| **`/oplan`** | main Claude (Opus, this session) | Plan needs strong reasoning + repo context, but execution should stay private |
| `/kb-plan` | Cline Kanban Opus ticket (separate session) | Want plan tracked on the kanban board, ticketed for handoff |

Common flow: `/oplan` → high-quality plan → `/pdo --plan <file>` → local private execution.

## When NOT to use
- Trivial tasks (1-2 files, mechanical) — overkill, just /pdo directly
- When you already invoked `/pplan` for the same topic — pick one planner, not both

## Flow

When user invokes `/oplan <topic>`:

### 1. Brainstorm first (mandatory — uses superpowers:brainstorming)
- Invoke `superpowers:brainstorming` to explore intent, requirements, constraints with the user
- Don't skip — local-execution risk goes up if the plan is mis-aimed
- Once user-aligned, proceed

### 2. Gather context
- Read referenced files (user-named or inferred from topic)
- Check git status, recent commits if relevant
- Use Grep/Glob to map scope
- DO NOT make any edits — this is plan-only

### 3. Produce the plan in the EXACT structure below
Save to `./plans/<slug>-<YYYYMMDD-HHMM>.md` (auto-mkdir).

```markdown
---
topic: <topic>
generated_by: oplan (model: claude-opus-4-7)
generated_at: <ISO timestamp>
discord_thread: <if --discord flag used, else "">
---

# <Topic>

## Goal
<one sentence>

## Context
<what's known, what's been tried, constraints, references>

## Approach
<the chosen approach + why over alternatives, brief>

## Phases
### Phase 1: <name>
- Step 1.1 — <action>
- Step 1.2 — <action>
- **Verification**: <how we know phase 1 worked>

### Phase 2: <name>
…

## Files to touch
- /abs/path/file1.ts — <what changes>
- /abs/path/file2.py — <what changes>

## Files NOT to touch
- /abs/path/keep1 — <why off-limits>

## Risks
- <risk> → <mitigation>

## Open questions
- <thing you couldn't decide>

## Recommended executor
- **Model**: <one of: qwen3-coder:30b | qwen3.6:35b-a3b-coding-mxfp8 | nemotron3:33b | qwen3.6:35b-a3b-q8_0 | gemma4:latest>
- **Why**: <one sentence — match the task shape to the model's strength>
- **Suggested timeout**: <seconds>
- **Suggested flag**: `/pdo --model <id> --timeout <sec>` or `/pdo --reason` etc.

## Next action
<the very first concrete step a follow-up /pdo would take>
```

### 4. Executor selection heuristics (same as /pplan)

| Task shape | Model | Timeout |
|---|---|---|
| Mechanical: bulk rename, move, format conversion, single-file scaffold | `qwen3-coder:30b` | 300–600s |
| Heavy code generation: new module, complex types, lots of new code | `qwen3.6:35b-a3b-coding-mxfp8` | 600s (loop-prone — hard cap) |
| Multi-file with logic dependencies, debugging, edge-case reasoning | `nemotron3:33b` | 900s |
| Architecture-shaped, needs full repo context | `qwen3.6:35b-a3b-q8_0` | 1800s — but consider keeping cloud Claude for these |
| Trivial, single-line edit, format fix | `gemma4:latest` | 180s |

You must explicitly cite which heuristic applied and why.

### 5. Save + present
- Write the plan file
- Show the user a tight summary: title, phase count, recommended executor, file path
- Offer: `Run /pdo --plan <path> now? (y/n)`
- If yes → invoke /pdo with the plan file
- If no → leave the file for them to run later

## Flags

```
/oplan <topic>                     full plan, brainstorm first, save to ./plans/
/oplan --skip-brainstorm <topic>   skip brainstorming step (only if you've already aligned)
/oplan --output <path> <topic>     custom save path
/oplan --discord <topic>           ALSO post the final plan to a Discord thread
/oplan --auto-pdo <topic>          chain straight into /pdo --plan after writing
/oplan --no-files <topic>          don't read any files; produce plan from your own knowledge only
```

## Examples

**Good fit**
```
/oplan migrate ~/Dev/<VOICE_RUNTIME>/src/voice from CommonJS to ESM, including imports + package.json type field
```
→ Brainstorm intent, read voice/ tree, produce plan with `qwen3-coder:30b` recommended (mechanical multi-file refactor), save to ./plans/.

**Good fit**
```
/oplan refactor <PRODUCT_NAME> search query builder to support nested boolean expressions
```
→ Read query-builder code, brainstorm edge cases, produce plan recommending `nemotron3:33b` (multi-file with logic deps).

**BAD fit**
```
/oplan fix the typo in README
```
→ Refuse. Tell user: just edit it directly, don't waste a planning round.

## Output to user

```
[oplan: <duration>, plan saved to: <path>, phases: <N>, executor: <model>]

<plan summary — Goal + Approach + phase count, not the whole plan>

Next action: <quote from plan's "Next action" section>

Run /pdo --plan <path> now? (y/n)
```

## Related

- `/pplan` — same flow but local-private planner (gemma4 / nemotron3 via pi)
- `/pdo` — execute the plan locally with PI+Ollama
- `/kb-plan` — ticketed plan on Cline Kanban
- `superpowers:brainstorming` — invoked first, mandatory
- `superpowers:writing-plans` — main-Claude plan structure (this skill mirrors it)
