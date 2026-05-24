---
description: Create a session checkpoint — save current state, progress, and context so you can resume later. Use before compaction or when handing off
argument-hint: "[checkpoint name or description]"
---
## Session Checkpoint

Save the current state of work so it can be resumed later. This is especially useful before context compaction or when handing off to another session.

### Save Checklist

Before saving, ensure:

1. **File state**: List all files that have been modified (vs last checkpoint or HEAD)
   ```bash
   git diff --name-only
   ```

2. **Progress summary**: What has been completed, what remains
3. **Open issues**: Any known bugs, TODOs, or blockers
4. **Context preservation**: Key decisions, architecture choices, API contracts

### Output Format

```
## Checkpoint: <name>
**Date**: <timestamp>
**Branch**: <current branch or "HEAD">

### State
- Modified files: list of files vs baseline
- Git status: clean/dirty, staged/unstaged

### Progress
- [x] Completed item 1
- [x] Completed item 2
- [ ] In progress: what's next
- [ ] Blocked: reason

### Notes
- Key decisions: ...
- Architecture choices: ...
- Known issues: ...
- To resume: start here, focus on ...
```

### Auto-Save Checklist

When the user says just `/checkpoint` without arguments:
1. Run `git status --short`
2. Read `AGENTS.md` for context
3. Generate a checkpoint with current state
4. Save to `.pi/checkpoint-<timestamp>.md` or append to `.pi/checkpoints.md`
