---
name: kb-link
description: Link two Cline Kanban tasks so one waits on the other (auto-cascade pipeline). When a task in review is trashed, any linked backlog task auto-starts. Use when the user says "kb-link", "link these tasks", "make X depend on Y", "chain these tickets", or wants to wire up a sequential pipeline of work. Project-agnostic.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Link Skill

Wire two tasks with a dependency relationship. The "waiting" task auto-starts when the "prerequisite" task is trashed (typically after passing review).

## When to use

Triggers: `/kb-link`, "kb-link", "link these tasks", "make X wait on Y", "chain ticket A after B", "set up auto-cascade".

Often called right after creating a sequence of tickets with `/kb-do` or `/kb-plan` to chain them.

## Inputs

- **Required:** two task IDs
- `--project <path>` — defaults to cwd

The order matters when both are in backlog: first ID waits on second ID. Once one moves out of backlog, Cline Kanban reorients automatically (the remaining backlog task becomes the dependent).

Usage forms:
- `/kb-link <waiting-id> <prereq-id>` — explicit ordering
- `/kb-link --task-id <waiting> --linked-task-id <prereq>` — full flag form

## How linking works (important)

Cline Kanban's link semantics:
1. **Both tasks in backlog:** the order you pass is preserved. `--task-id A --linked-task-id B` means A waits on B. Board arrow: A → B.
2. **One task moves to in_progress / review:** Kanban reorients the saved dependency so the remaining backlog task is the waiting dependent. The user can ignore reordering — it's automatic.
3. **The prerequisite task is trashed (typically after review):** the waiting backlog task auto-starts.

Combined with `--auto-review-mode commit|pr|move_to_trash` on the prerequisite, you get a fully autonomous pipeline:
- Task A finishes → auto-commits → moves to review → auto-trashes → task B auto-starts.

## Procedure

1. **Resolve project path.** `--project <path>` if given, else `pwd`.

2. **Validate task IDs exist** by calling `task list` first. Filter to the two IDs and confirm they're in the project.

3. **Create the link:**
   ```bash
   '/usr/bin/node' '<LOCAL_PATH>/.local/bin/kanban' task link \
     --task-id <waiting> \
     --linked-task-id <prereq> \
     --project-path <project>
   ```

4. **Capture the dependency ID** from the response. Echo it so the user can unlink later if needed.

5. **Confirm with a simple visualization:**
   ```
   Linked: [b8920] Audit session token handling
                ↓ (waits on)
           [c526a] BIN Enrichment Service

   Auto-cascade: when c526a is trashed, b8920 will start.
   Dependency ID: 47edcd69 (use with /kanban task unlink to remove)
   ```

## Pipeline patterns

### Linear chain
A → B → C → D (each step starts when the previous trashes):
```bash
/kb-link B A
/kb-link C B
/kb-link D C
```

### Fan-out (multiple tasks all wait on one prereq)
B, C, D all wait on A:
```bash
/kb-link B A
/kb-link C A
/kb-link D A
```
When A trashes, B/C/D all start in parallel.

### Fan-in (one task waits on multiple prereqs)
D waits on both B and C:
```bash
/kb-link D B
/kb-link D C
```
D won't auto-start until BOTH B and C are trashed.

## Anti-patterns

- Do NOT link tasks across different projects — Cline Kanban scopes links to a single workspace.
- Do NOT link a task to itself.
- Do NOT link a task that's already in `trash` — the link will be silently ignored (or rejected, depending on Kanban version).
- Do NOT rely on a specific arrow direction without testing — if uncertain, run `/kb-status` after linking and confirm the dependency renders correctly.

## Companion skills

- `/kb-do`, `/kb-plan` — create the tasks before linking
- `/kb-trash` — trash a prerequisite task to fire the cascade
- `/kb-status` — visualize the current dependency graph
