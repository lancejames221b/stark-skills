---
name: opusplan
description: Call `claude -p --model opus` to produce an execution-ready plan via the Claude Code CLI. Uses cloud Opus (separate billing) with a system prompt optimized for plans that guide local execution end-to-end. Trigger phrases — "/opusplan", "opus plan via claude", "plan with claude opus".
category: planning
runtimes: [claude]
pii_safe: true
---

# /opusplan — Execution plan via `claude -p --model opus`

Calls the local `claude` CLI in plan mode with Opus, producing a structured implementation plan designed to guide an executor (main Claude or `/pdo`) through end-to-end success. Uses cloud Opus — separate billing from the current session.

## When to use vs alternatives

| Skill | Planner | Use when |
|---|---|---|
| **`/opusplan`** | `claude -p --model opus` (external CLI) | Want cloud Opus reasoning but the plan is for a *different* machine or future session; no current-session context is needed |
| `/oplan` | main Claude (this session) | You're already in a Claude Code session and want full repo context available during planning |
| `/cplan` | `claude -p` (default: opus) with /plan skill | Frontend/UI planning or default cplan flow |
| `/pplan` | local PI + Ollama | Sensitive plans, no cloud needed |

## Flow

When user invokes `/opusplan <topic>`:

### 1. Build the brief

```
You are an execution-focused planner. Produce a plan that any capable coding agent can follow step by step without needing to ask clarifying questions.

## Output rules
- Every phase has exactly one "Verification" bullet with a concrete, executable command or test.
- Every file change cites the exact path and what changes (not "add feature", but "add `fetchUsers` in src/api/users.ts:45").
- Commands must be copy-paste runnable (include the full path, flags, expected args).
- If a step depends on a prior step's output, state the dependency explicitly.

## Structure (follow exactly)
```markdown
---
topic: <short topic>
generated_by: opusplan (claude -p --model opus)
generated_at: <ISO timestamp>
---

# <Topic>

## Goal
<one sentence describing the successful end state>

## Prerequisites
- <thing that must exist before starting; commands to verify>

## Phases
### Phase 1: <name>
**Goal**: <what this phase leaves in a working state>

- [ ] Step 1 — <exact action with file path and line numbers>
  - **Verify**: `<command to run>`
- [ ] Step 2 — <exact action>
  - **Verify**: `<command>`

### Phase 2: <name>
**Goal**: <what this phase leaves in a working state>

- [ ] Step 2.1 — ...
...

## Files changed (full inventory)
| File | Action | What changes |
|---|---|---|
| `/abs/path/file.py` | MODIFY | <specific lines/signatures> |

## Files created
| File | Purpose |
|---|---|
| `/abs/path/new.py` | <1 sentence> |

## Risks & gotchas
- `<risk>` — `<mitigation or workaround>`

## Open questions
- <anything the planner could not fully resolve>

## End-to-end verification
<the full command sequence to run after all phases are done, proving the work works>

## Next action
<first concrete step to take right now>
```

Keep the plan narrow: each phase should be completable in one sustained coding session (under ~15 minutes of active typing). If the task is bigger, chain phases so each one leaves the repo in a working state.

If you do not know enough about the codebase to cite specific file paths, say so in Open questions rather than guessing.

</topic>
```

### 2. Invoke `claude -p --model opus`

Check that the `claude` CLI exists on PATH. If not, fall back to `/oplan` (current session Opus) and tell the user:

```
[opusplan: `claude` CLI not found — falling back to /oplan (current session)]
```

Build and run:

```bash
claude -p --model opus "$(cat $BRIEF_FILE)"
```

Use `timeout` with a generous budget: **1800s** (30 min). Opus planning can take time for complex tasks.

### 3. Validate the output

Reject and warn if the plan:
- Is missing required sections (Goal, Phases with Verification, Files changed, End-to-end verification)
- Is < 500 chars or looks truncated mid-sentence
- Has no concrete file paths (all generic)
- Has phases without Verification bullets

### 4. Save the plan

Default: `./plans/opusplan-<slug>-<YYYYMMDD-HHMM>.md` (auto-mkdir).

Wrap with frontmatter:
```markdown
---
topic: <topic>
generated_by: opusplan (claude -p --model opus)
generated_at: <ISO timestamp>
duration_s: <elapsed seconds>
---

<claude output>
```

### 5. Present to user

```
[opusplan: <duration>s, plan saved to: <path>, phases: <N>]

**Goal**: <one sentence>
**Files**: <N> changed, <M> created

Next action: <quote from plan's "Next action" section>

Run this now? (y/n)
```

## Flags

```
/opusplan <topic>                     full plan, save to ./plans/
/opusplan --timeout 600 <topic>       custom timeout (seconds)
/opusplan --output <path> <topic>     custom save path
/opusplan --no-save <topic>           print plan only, don't save to file
```

## Examples

**Good fit**
```
/opusplan add CSV export to the kanban CLI — output should mirror existing JSON exporter
```

**Good fit**
```
/opusplan refactor <PRODUCT_NAME> ES query builder to support nested boolean expressions
```

**BAD fit**
```
/opusplan fix the typo in README
```
→ Refuse. Tell user: just edit it directly, don't waste a planning round.

## When `claude` CLI is unavailable

If the `claude` binary isn't found on PATH:
1. Try common install locations (`~/.npm-global/bin/claude`, `/usr/local/bin/claude`)
2. If still not found, fall back to `/oplan` and tell the user

## Related

- `/oplan` — same flow but using current session's Claude (full repo context available)
- `/cplan` — generic `claude -p` wrapper with /plan skill system prompt
- `/pdo` — execute an opusplan-saved plan locally with PI + Ollama
- `/pplan` — local-only planning via PI + Ollama (no cloud billing)
