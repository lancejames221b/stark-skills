---
name: chat-shortcut
description: "Manage and run chat slash shortcuts — saved aliases for frequently-used prompts or skill invocations, specifically for chat/text sessions (Discord, WhatsApp, Telegram, etc). Use when: (1) <USER_NAME>says 'add a chat shortcut', 'create a chat shortcut', 'save this as a chat shortcut', (2) <USER_NAME>runs /shortcut, /cs, or /chat-shortcut to list, add, remove, edit, or fire a saved chat shortcut, (3) <USER_NAME>says 'what chat shortcuts do I have', 'show my chat shortcuts', 'list chat shortcuts'. Chat shortcuts are stored in ~/dev/contexts/chat-shortcuts.json and auto-expand when invoked. These are the chat equivalent of voice shortcuts — same concept, tuned for typed/chat interactions."
category: workflows
runtimes: [claude]
pii_safe: true
---

# Chat Shortcut Skill

Chat shortcuts are named aliases for frequently-used prompts in text/chat sessions. They are the chat equivalent of voice shortcuts — same concept, tuned for typed interactions on Discord, WhatsApp, Telegram, etc.

**Storage:** `~/dev/contexts/chat-shortcuts.json`

## Usage

```
/shortcut                        — list all saved chat shortcuts
/shortcut list                   — same as above
/shortcut add <name> <prompt>    — save a new chat shortcut
/shortcut remove <name>          — delete a chat shortcut
/shortcut edit <name> <prompt>   — update an existing shortcut
/shortcut <name>                 — run a saved chat shortcut
/cs ...                          — same as /shortcut, short form
/chat-shortcut ...               — same as /shortcut, long form
```

**Natural language triggers:**
- "add a chat shortcut called digest that runs workspace digest" → add
- "what chat shortcuts do I have" → list
- "remove the digest chat shortcut" → remove
- "run my standup chat shortcut" → run
- "create a chat shortcut for ..." → add

## Storage format

File: `~/dev/contexts/chat-shortcuts.json`

```json
{
  "shortcuts": {
    "digest": {
      "prompt": "run the workspace digest skill",
      "created": "2026-04-02",
      "description": "workspace digest summary",
      "tags": ["daily", "summary"]
    }
  }
}
```

## Workflow

### List
1. Read `~/dev/contexts/chat-shortcuts.json` (create empty `{"shortcuts":{}}` if missing)
2. Print each shortcut: `/cs <name>` — <description or first 60 chars of prompt>
3. If empty: "No chat shortcuts saved yet. Add one with `/cs add <name> <prompt>`."

### Add
1. Read shortcuts file (create if missing)
2. Sanitize name: lowercase, spaces → hyphens, letters/digits/hyphens only
3. Add entry: name, prompt (full text), created (run `date +%Y-%m-%d`), description (first 60 chars or user-provided), tags (optional)
4. Write file back
5. Confirm: "Chat shortcut `/cs <name>` saved."
6. Store to haivemind:
   ```bash
   mcporter call haivemind.store_memory content="CHAT-SHORTCUT added: /cs <name> → <prompt>" category="global"
   ```

### Remove
1. Read file, delete key, write back
2. Confirm: "Chat shortcut `/cs <name>` removed."
3. Store to haivemind: `mcporter call haivemind.store_memory content="CHAT-SHORTCUT removed: /cs <name>" category="global"`

### Run
1. Read file, look up `<name>` (exact match first, then prefix match)
2. If not found: "No chat shortcut named `/cs <name>`. Run `/cs list` to see what's saved."
3. If found: expand the prompt and execute it as if <USER_NAME>typed it directly — pass through normal assistant flow
4. Prefix-match disambiguation: if multiple shortcuts start with `<name>`, list matches and ask which one

### Edit
1. Read file, update prompt + created date, write back
2. Confirm: "Chat shortcut `/cs <name>` updated."
3. Store to haivemind: `mcporter call haivemind.store_memory content="CHAT-SHORTCUT edited: /cs <name> → <new prompt>" category="global"`

## Notes
- Shortcut names: lowercase, letters/digits/hyphens only. Auto-sanitize on add (spaces → hyphens).
- `/cs <name>` where `<name>` is not a subcommand (list/add/remove/edit) triggers the **run** path.
- Chat shortcuts are separate from voice shortcuts — they live in `chat-shortcuts.json`, not `shortcuts.json`. Both can coexist.
- Chat shortcuts expand through the model — they are NOT native slash commands. For native platform slash commands, a full skill is needed.
- Always confirm the action taken. Never silent-fail.
- On run: announce which shortcut is firing: "Running `/cs <name>`..." then execute.
