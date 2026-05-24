---
description: Save project memory — persist important context, decisions, state, and lessons learned. Use when asked to "save this", "remember", "store", "note", or "checkpoint"
argument-hint: "[<content> | :auto | clear | list | load <key>]"
---
# Project Memory — Save / Load

A project-scoped memory system for persisting important context across sessions.

## Files

Memories live in `~/.pi/memory/` — project-scoped, loaded automatically.

```
~/.pi/memory/
├── project.md        # Project overview, architecture, key decisions
├── tasks.md          # Active tasks, progress, blockers
├── decisions.md      # Architecture decisions, trade-offs
├── lessons.md        # Things learned, gotchas, patterns
└── <key>.md          # Any custom memory (named by user)
```

## Commands

### Save
```
/save <content>
```
Append the content to the appropriate memory file.

### Auto-Save (Checkpoint)
```
/save :auto
```
Auto-summarize the current session's progress, state, and key decisions. Save to `project.md` under a dated section.

### List
```
/save list
```
Show all memory files with a brief preview:
```
## Memory Index (<cwd>)

| File | Contents |
|------|----------|
| project.md | Architecture, stack, key decisions (last edited: 2h ago) |
| tasks.md | 5 active tasks, 2 blocked |
| decisions.md | 3 architecture decisions |
| lessons.md | 4 gotchas, 2 patterns |
```

### Clear
```
/save clear
```
Clear all memory files (confirm first).

### Load
```
/save load
```
Load and display all memory files.

### Load Specific
```
/save load <key>
```
Load a specific memory file.

## Save Format

Each entry in a memory file:

```markdown
## <YYYY-MM-DD HH:MM> — <Title>

Content here...
```

## Example Workflow

```
> /save add auth middleware to server
→ Appended to tasks.md

> /save :auto
→ Summarized current session: "Modified AuthContext.tsx, added middleware, server compiles clean"

> /save list
→ Shows all memory files

> /save load project
→ Shows project.md contents
```

## Project-local MEMORY.md fallback

After writing to Obsidian + hAIveMind (via mcporter on <INFERENCE_HOST>), also append a one-line entry to `./MEMORY.md` in cwd. This is a local-only write — no SSH required.

**Project detection** (check in order, stop at first hit):
1. `.git/` in cwd
2. `CLAUDE.md` in cwd
3. `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` in cwd
4. cwd path contains `/Dev/` or `/dev/` or `/Documents/Dev/`

If none match, skip this step.

**Entry format** (one line, append-only):
```
- YYYY-MM-DD HH:MM | <category> | <title> — <one-line summary> [obsidian:<subdir>/<slug>.md] [hv:<memory_id>]
```

**Header** (write once on file creation):
```
# Project Memory

Local-first memory fallback. Authoritative copies in Obsidian + hAIveMind.
```

**Fallback path**: If Obsidian AND hAIveMind both fail (generic unreachable), still write `./MEMORY.md` using `[obsidian:PENDING]` and `[hv:PENDING]` as placeholders. Warn the user that a full save must be retried when <INFERENCE_HOST> is back online. Do NOT commit `./MEMORY.md` to `.gitignore` — other agents on other machines should see it.
