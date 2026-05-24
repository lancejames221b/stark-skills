---
name: pplan
description: Private PLAN — produce a written plan using local PI + Ollama. Read-only research, no file edits, no execution. Output is a structured implementation plan that a follow-up /pdo (or main Claude) executes. Trigger phrases — "/pplan", "private plan", "plan this on local", "local plan for".
category: execution
runtimes: [claude]
pii_safe: true
---

# /pplan — Private PLAN (PI worker, planning only)

Produce a structured plan for a task using local Ollama. **Pi runs without write/edit/bash tools** — it can only read files and respond. Output is a markdown plan saved to a file. No code changes. Useful for:

- Sensitive plans you don't want to traverse cloud APIs
- Decomposing a vague request before committing main-Claude tokens
- Running a planning pass while main Claude does something else

## When NOT to use
- Architecture decisions on unfamiliar codebases — local models lack the context window utilization to be reliable
- Anything requiring deep cross-file reasoning
- Time-critical planning — local inference is slow (1–10 min depending on model)

## Models

| Tag | Model | Notes |
|---|---|---|
| **default** | `nemotron3:33b` | Best reasoner currently installed locally |
| `--big` | `qwen3.6:35b-a3b-q8_0` | Highest local precision, slowest |
| `--coder` | `qwen3-coder:30b` | If the plan is mostly code-shape |
| `--fast` | `gemma4:latest` | Quick draft only — shallow reasoning |

## Flags

```
/pplan <topic>                    nemotron3:33b, 900s, save to ./plans/, Discord thread on
/pplan --big <topic>              qwen3 235b, 1800s
/pplan --fast <topic>             gemma4, 300s
/pplan --coder <topic>            qwen3-coder:30b
/pplan --model <id> <topic>       override
/pplan --timeout <sec> <topic>    override
/pplan --output <path> <topic>    custom save path
/pplan --no-discord <topic>       skip Discord thread
/pplan --dry <topic>              print pi command, do not execute
```

## Output structure

The plan must follow this shape (instructed via guardrails):

```markdown
# <Topic>

## Goal
<one sentence>

## Context
<what's known, what's been tried, constraints>

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
- <thing the planner couldn't decide>

## Recommended executor
- **Model**: <one of: qwen3-coder:30b | qwen3.6:35b-a3b-coding-mxfp8 | nemotron3:33b | qwen3.6:35b-a3b-q8_0 | gemma4:latest>
- **Why**: <one sentence — match the task shape to the model's strength>
- **Suggested timeout**: <seconds>
- **Suggested flag**: `/pdo --model <id> --timeout <sec>` or `/pdo --reason` etc.

## Next action
<the very first concrete step a follow-up /pdo or main-Claude would take>
```

### Executor selection heuristics (planner reasons over these)

| Task shape | Model | Timeout |
|---|---|---|
| Mechanical: bulk rename, move, format conversion, single-file scaffold | `qwen3-coder:30b` | 300–600s |
| Heavy code generation: new module, complex types, lots of new code | `qwen3.6:35b-a3b-coding-mxfp8` | 600s (loop-prone — hard cap) |
| Multi-file with logic dependencies, debugging, edge-case reasoning | `nemotron3:33b` | 900s |
| Architecture-shaped, needs full repo context | `qwen3.6:35b-a3b-q8_0` | 1800s |
| Trivial, single-line edit, format fix | `gemma4:latest` | 180s |

The planner must explicitly cite which heuristic applied and why.

## Flow

### 1. Build the planning brief (you)
Convert user's request into:
- **Topic** — what's being planned
- **Scope hints** — repos/dirs the plan should touch
- **Constraints** — hard rules (no new dependencies, must preserve API X, etc.)
- **Reference files** — paths pi should read first

### 2. Build guardrails
```
You are a focused planner. Produce ONLY a written plan in the structure shown — no code, no file edits, no execution. You may use the Read tool to inspect files. Do NOT use Bash, Edit, or Write tools.

Constraints:
- Match the output structure exactly. No deviation.
- If you cannot plan without more information, output the plan up to where you got stuck and put the rest in "Open questions".
- Cite specific file paths and line numbers as evidence for decisions.
- Keep phases small enough that each is verifiable independently.
- Prefer concrete steps ("rename getX to fetchX in src/api/users.ts") over vague ones ("refactor users module").
- The "Recommended executor" section is REQUIRED. Pick the model from the heuristic table that best matches the task shape. State which heuristic applied. Do not pick a model that's stronger than needed — match the task.
```

### 3. Spawn Discord thread (default)
Same pattern as `/pdo`:
- Channel: `#pdo-runs` (or override with `--channel`)
- Thread name: `pplan-<short-topic>-<HHMM>`
- Initial message: `🧭 **/pplan run started** — <topic>`
- Stream pi stdout into thread, batched every 5 lines or 2s

### 4. Invoke pi with limited toolset
```bash
timeout "$TIMEOUT" pi --print --no-session \
  --provider ollama --model "$MODEL" \
  --tools read \
  --append-system-prompt "$(cat $GUARDRAILS_FILE)" \
  "$(cat $BRIEF_FILE)" 2>&1
```

`--tools read` keeps pi locked to the read tool only — it cannot edit, write, or shell out. (If pi's `--tools` flag spelling differs, see `pi --help`; it accepts `-t <comma list>`.)

### 5. Save the plan
- Default: `./plans/<slug>-<YYYYMMDD-HHMM>.md`
- Or `--output <path>`
- Wrap the pi stdout with a frontmatter:
  ```markdown
  ---
  topic: <topic>
  generated_by: pplan (model: <model>)
  generated_at: <ISO timestamp>
  pi_session_log: /tmp/pplan-<ts>.log
  discord_thread: <url>
  ---

  <pi output>
  ```

### 6. Verify before showing user
Reject and warn if pi:
- Output didn't follow the structure (missing required sections)
- Output is empty / < 200 chars
- Looks like it tried to make edits anyway (look for diff syntax in the output)
- Truncated mid-sentence (likely timeout)

### 7. Output to user
```
[pplan: <model>, <duration>s, plan saved to: <path>, thread: <discord url>]

<plan, rendered>

Next action suggested: <quote from plan's "Next action" section>

Run /pdo with this plan? (y/n)
```

If yes → seed `/pdo` with the plan's "Phase 1" steps as the spec.

## Logs

`/tmp/pplan-<ISO-timestamp>.log` with:
- model, timeout, channel, thread, brief, guardrails, duration, exit, full output

## Examples

**Good fit**
```
/pplan migrate ~/Dev/<VOICE_RUNTIME>/src/voice from CommonJS to ESM, including all imports and the package.json type field
```

**Good fit**
```
/pplan add CSV export to the kanban CLI — output should mirror the existing JSON exporter's schema
```

**BAD fit**
```
/pplan how should we redesign Jarvis?
```
→ Refuse. Open-ended; needs main-Claude with full repo + brainstorming skill.

## Related

- `/pdo` — execute the plan privately
- `/kb-plan` — cloud-Claude planning ticket on Cline Kanban
- `superpowers:writing-plans` — main-Claude plan structure (this skill mirrors it)
