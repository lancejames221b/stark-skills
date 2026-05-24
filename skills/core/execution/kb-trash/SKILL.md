---
name: kb-trash
description: Move a Cline Kanban task (or an entire column) to trash, stopping any active session and cleaning up its worktree. Auto-cascades any linked backlog tasks (one in trash → next in chain auto-starts). Use when the user says "kb-trash", "trash that task", "trash kanban", "clean up the review column", "drop those tickets", or wants to remove tasks from the board.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Trash Skill

Move a single task or an entire column to the trash column. Stops the agent session if running, cleans up the worktree, and triggers any dependent backlog tasks waiting on it.

## When to use

Triggers: `/kb-trash`, "kb-trash", "trash this task", "trash the review column", "clean up backlog", "drop that ticket".

Often called after `/kb-status` shows tasks that are done with their review and ready to clear, OR to bulk-clean abandoned/superseded work.

## Inputs

Exactly one of:
- `--task-id <id>` — trash a single task
- `--column <col>` — trash every task in `backlog` / `in_progress` / `review` / `trash`

Plus:
- `--project <path>` — defaults to cwd

## Important behaviors to know

1. **Trash is reversible** for a single task in the sense that the task remains in the trash column (you can read its prompt, see its outputs). It is NOT deleted. Use `/kanban task delete` if you actually want to remove it permanently.
2. **Trashing a task in `review` triggers any linked backlog tasks.** This is how the auto-cascade pipeline works: task A finishes → moves to review → user/agent trashes it → linked task B auto-starts.
3. **Trashing a running task interrupts it.** The session is stopped (not gracefully drained). Don't trash a task mid-run unless you mean to abort it.
4. **`task trash --column trash`** is a no-op — it doesn't permanently delete, just confirms tasks already in trash. Use `task delete --column trash` to actually empty the trash column.

## Procedure

1. **Resolve project path.** `--project <path>` if given, else `pwd`.

2. **Confirm scope** before destructive action:
   - For `--task-id`: print the task title and current column. Ask for confirmation if the task is in `in_progress` (this aborts the session).
   - For `--column`: print the count of tasks that will be trashed. Ask for confirmation. Always.

3. **Execute:**
   ```bash
   '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task trash \
     [--task-id <id> | --column <col>] \
     --project-path <project>
   ```

4. **Show what auto-started.** The command response includes `autoStartedTasks` — print these so the user knows the cascade fired.

5. **Suggest next step.** If multiple tasks were trashed, suggest `/kb-status` to see the new board state.

## Example flows

### Single task done with review
```
User: kb-trash b8920
Skill:
  Task [b8920] "Audit session token handling" is in review.
  Trashing... done.
  Auto-started: [c526a] BIN Enrichment Service
  Run /kb-status to see updated board.
```

### Bulk-clean review column
```
User: kb-trash --column review
Skill:
  4 tasks currently in review:
    [b8920] Audit session token handling
    [d54ed] Domain allowlist
    [a41d1] PAN validator
    [44e24] Bot canonicalization
  Confirm trashing all 4? (y/n)
User: y
Skill:
  Trashed 4 tasks.
  Auto-started: [b8920], [c526a]   # cascading dependencies
  Run /kb-status to see updated board.
```

### Aborting a running task
```
User: kb-trash a4321
Skill:
  Task [a4321] "Build credential extraction pipeline" is IN PROGRESS.
  Trashing will interrupt the running session. Confirm? (y/n)
User: y
Skill:
  Trashed (session interrupted, worktree cleaned).
```

## Anti-patterns

- Do NOT trash without confirmation when the column is `in_progress` or when bulk-trashing.
- Do NOT use this skill for permanent deletion — use `kanban task delete` directly with explicit user intent.
- Do NOT auto-trash ALL tasks "to clean up" without user instruction.

## Companion skills

- `/kb-status` — see what's on the board (good to run before bulk-trashing)
- `/kb-do`, `/kb-plan`, `/kb-new` — create work
- `/kb-link` — wire dependencies (you'll trash review tasks that have dependents to fire the cascade)
