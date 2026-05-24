---
name: shortcut
description: "Manage and run personal slash shortcuts — saved aliases for frequently-used prompts or skill invocations. Use when: (1) <USER_NAME>says 'add a shortcut', 'create a shortcut', 'save this as a shortcut', (2) <USER_NAME>runs /shortcut to list, add, remove, or fire a saved shortcut, (3) <USER_NAME>says 'what shortcuts do I have' or 'show my shortcuts'. Shortcuts are stored in ~/dev/contexts/shortcuts.json and auto-expand when invoked."
user-invocable: true
category: workflows
runtimes: [claude]
pii_safe: true
---

# Shortcut Skill

Shortcuts are named aliases for frequently-used prompts. They are stored in `~/dev/contexts/shortcuts.json`.

## Usage

```
/shortcut                        — list all saved shortcuts
/shortcut list                   — same as above
/shortcut add <name> <prompt>    — save a new shortcut
/shortcut remove <name>          — delete a shortcut
/shortcut edit <name> <prompt>   — update an existing shortcut
/shortcut <name>                 — run a saved shortcut (expands and executes the prompt)
```

**Voice/chat natural language:**
- "add a shortcut called pulse that runs work pulse" → add
- "what shortcuts do I have" → list
- "remove the pulse shortcut" → remove
- "run my standup shortcut" → run

## Storage format

File: `~/dev/contexts/shortcuts.json`

```json
{
  "shortcuts": {
    "pulse": {
      "prompt": "run the work pulse skill",
      "created": "2026-04-02",
      "description": "work pulse summary"
    }
  }
}
```

## Workflow

### List
1. Read `~/dev/contexts/shortcuts.json` (create empty `{"shortcuts":{}}` if missing)
2. Print each shortcut: `/<name>` — <description or first 60 chars of prompt>

### Add
1. Read shortcuts file (create if missing)
2. Add entry: name (lowercase, no spaces → convert spaces to `-`), prompt, created date (run `date`), description (first 60 chars or user-provided)
3. Write file back
4. Confirm: "Shortcut `/<name>` saved."
5. Store to haivemind: `mcporter call haivemind.store_memory content="SHORTCUT added: /<name> → <prompt>" category="global"`

### Remove
1. Read file, delete key, write back
2. Confirm: "Shortcut `/<name>` removed."

### Run
1. Read file, look up `<name>`
2. If not found: "No shortcut named `/<name>`. Run `/shortcut list` to see what's saved."
3. If found: expand the prompt and execute it as if <USER_NAME>typed it directly (pass it back through the normal assistant flow)

### Edit
1. Read file, update prompt + date, write back
2. Confirm: "Shortcut `/<name>` updated."

## Notes
- Shortcut names: lowercase, letters/digits/hyphens only. Auto-sanitize on add.
- The skill itself is `/shortcut` — running `/shortcut <name>` where `<name>` is not a subcommand (list/add/remove/edit) triggers the "run" path.
- Shortcuts are NOT native slash commands themselves — they expand through the model. For true native slash commands, a full skill is needed per shortcut.
- Always confirm the action taken. Never silent-fail.
