---
name: kb-status
description: Show the current Cline Kanban board state for a project — tasks grouped by column (in_progress, review, backlog, trash), with session state, model assignments, and dependency edges. Use when the user says "kb-status", "kanban status", "show the board", "what's on kanban", "what tasks do I have", or wants to see what's running/queued. Project-agnostic — defaults to current directory, accepts `--project <path>`.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Status Skill

Show the Cline Kanban board for a project: which tasks are running, in review, queued, or trashed, plus model assignments and dependency links.

## When to use

Triggers: `/kb-status`, "kb-status", "kanban status", "show the board", "what's on kanban", "what tasks do I have", "what's queued", "what's running".

Also invoke proactively before suggesting starting new work — knowing what's already in flight prevents over-scheduling.

## Inputs

- `--project <path>` — project to inspect (defaults to current working directory)
- `--column <col>` — filter to one column (`in_progress`, `review`, `backlog`, `trash`)
- `--verbose` — show full prompts and session metadata, not just titles
- `--ids-only` — emit just task IDs, one per line (useful for scripting)

## Procedure

1. **Resolve project path.** Use `--project <path>` if given, else `pwd`.

2. **Fetch task list:**
   ```bash
   '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task list --project-path <path> [--column <col>]
   ```
   Returns JSON with `tasks` and `dependencies` arrays.

3. **Group by column.** Order: `in_progress` → `review` → `backlog` → `trash`.

4. **For each task, extract:**
   - ID
   - Title (or first line of prompt, truncated to ~70 chars)
   - Session state (`running`, `awaiting_review`, `interrupted`, `none`)
   - Agent (cline / claude / codex / etc.)
   - Model + reasoning effort (if cline)
   - Plan mode flag
   - Auto-review settings if enabled
   - Created/updated timestamps (relative — "2h ago")

5. **Render a compact table per column.** Default format:
   ```
   === IN_PROGRESS (1) ===
   [a4321] cline/sonnet/medium — Build credential extraction pipeline (running, 12m)

   === REVIEW (2) ===
   [b8920] cline/opus/high — Audit session token handling (awaiting_review, 3h)
   [d54ed] cline/sonnet/low — Add canonical_name to bots table (awaiting_review, 5h)

   === BACKLOG (3) ===
   [c526a] cline/sonnet/medium — BIN enrichment service (waits on b8920)
   ...
   ```

6. **Show dependencies separately** if any exist. Format: `<dependent> waits on <prerequisite>`.

7. **Footer hints:** Print useful next-step commands based on state:
   - If any in `review`: "Move to trash with `kanban task trash --task-id <id>`"
   - If any in `backlog` with no deps: "Start with `kanban task start --task-id <id>`"
   - If empty board: "Create your first task with `/kb-do <description>`"

## Verbose mode

`--verbose` adds:
- Full prompt body (truncated to ~500 chars)
- All session fields (pid, exitCode, lastOutputAt, reviewReason)
- Linked task IDs in both directions
- Worktree path (if available)

Use sparingly — verbose output gets long fast on busy boards.

## --ids-only mode

For scripting:
```bash
ids=$(kb-status --column review --ids-only --project ~/Dev/foo)
for id in $ids; do
  '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task trash --task-id "$id" --project-path ~/Dev/foo
done
```

Outputs one task ID per line, no other text.

## Implementation reference

```bash
'/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task list --project-path "$PROJ" 2>&1 | python3 -c "
import json, sys
d = json.load(sys.stdin)
by_col = {}
for t in d['tasks']:
    by_col.setdefault(t['column'], []).append(t)
for col in ['in_progress', 'review', 'backlog', 'trash']:
    items = by_col.get(col, [])
    if not items: continue
    print(f'=== {col.upper()} ({len(items)}) ===')
    for t in items:
        sess = t.get('session') or {}
        title = (t.get('title') or t['prompt'].split(chr(10))[0])[:70]
        state = sess.get('state', 'none')
        # cline-specific fields are nested; show only if present
        model = t.get('clineModel', '?')
        effort = t.get('clineReasoningEffort', '?')
        print(f'  [{t[\"id\"]}] {state:18s} {title}')
"
```

## Anti-patterns

- Do NOT dump the raw JSON response — always render a compact view.
- Do NOT show trash by default — include only if user passed `--column trash` or board is otherwise empty.
- Do NOT poll on a loop; this is a one-shot status check. For monitoring, use `/loop kb-status 5m` instead.

## Companion skills

- `/kb-do`, `/kb-plan` — create tickets
- `/kb-trash` — bulk-clean tasks
- `/kb-new` — create a new project
- `/kb-link` — wire up task dependencies
