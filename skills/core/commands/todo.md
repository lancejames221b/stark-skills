---
description: Manage a session-scoped todo list. /todo shows todos, /todo <text> adds todos, /todo done <text> marks complete
argument-hint: "[<text> | done <text> | clear | nuke | all]"
---
Manage a todo list stored in the project's `.pi/todos.md` file.

## Rules

The todo file is project-scoped:
```
<pwd>/.pi/todos.md
```

Create if it doesn't exist.

## Commands

- **List todos** (no arguments): Read and display all todos with checkboxes
- **Add todo**: Append an item with `[ ]` checkbox and timestamp
  ```
  - [ ] <description> _(added YYYY-MM-DD HH:MM)_
  ```
- **Mark complete**: Replace `[ ]` with `[x]` for the matching item, add `_done YYYY-MM-DD HH:MM_`
  ```
  /todo fix login bug on the dashboard
  → finds "- [ ] fix login bug on the dashboard", changes to "- [x] ... _done 2026-05-04 10:30_"
  ```
- **Clear completed**: Remove all `[x]` items from the file
- **Nuke**: Delete the entire todo file (confirm first)
- **All**: List existing todo files across projects

## Display Format

After each todo file, show:
```
## Active Todos (<pwd>/.pi/todos.md)
- [ ] Feature X   ← needs work
- [x] Bug fix Y   _done 2026-05-04 10:30_
   ↑ N open, 1 done
```
