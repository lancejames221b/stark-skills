---
name: cred
description: Secure credential storage and retrieval. Triggers when <USER_NAME>uses /cred to share a credential (API key, password, token, secret) — automatically deletes the Discord message, stores in hAIveMind and 1Password under a named label, and confirms. Triggers on "/cred lookup NAME" to retrieve a credential by name. Never echo the credential value back in chat.
category: workflows
runtimes: [claude]
pii_safe: true
---

# /cred — Credential Vault

## Trigger Patterns

| Command | Action |
|---------|--------|
| `/cred <name> <value>` | Store credential (new) |
| `/cred update <name> <value>` | Update existing credential |
| `/cred lookup <name>` | Retrieve credential |
| `/cred list` | List stored credential names |
| `/cred delete <name>` | Remove from hAIveMind + 1Password |

Also triggers when a message contains a bare credential-looking value (API key, token, password string) without a `/cred` prefix — treat as implicit `/cred` store request, prompt for a name if missing.

## Update Flow (`/cred update <name> <value>`)

Same as Store, but updates the existing 1Password item instead of creating a new one:

1. **Delete the Discord message immediately** — first, always.
2. **Update hAIveMind** — hAIveMind is append-only (no update tool). Store a new entry with updated value + timestamp; the newest entry wins on lookup:
   ```bash
   mcporter call haivemind.store_memory \
     content="CRED:<name> value=<value> updated_at=<ISO timestamp> (supersedes previous)" \
     category="credentials"
   ```
3. **Update 1Password** (tmux session):
   - Find the existing item: `op item get "<name>" --vault Employee`
   - If found: `op item edit "<name>" --vault Employee "credential[password]=<new_value>"`
   - If not found: fall back to create (same as Store flow)
4. **Confirm**: `Updated "<name>" in hAIveMind + 1Password. Old value superseded.`

## Store Flow (`/cred <name> <value>`)

1. **Delete the Discord message immediately** — use `message action=delete channel=discord messageId=<id>` with the inbound `message_id` from the conversation metadata. Do this FIRST before anything else.
2. **Store in hAIveMind:**
   ```bash
   mcporter call haivemind.store_memory \
     content="CRED:<name> value=<value> stored_at=<ISO timestamp>" \
     category="credentials"
   ```
3. **Sign into 1Password** (tmux session, see references/1password-signin.md):
   - Vault: `Employee` (ID: `ojkx73ff23ofkjvkokdq73cthu`)
   - Item title: `<name>` (normalize to title case, e.g. "Cursor API Key - <USER_NAME>")
   - Category: `API Credential`
   - Fields: `credential[password]=<value>`, `username[text]=<EMAIL_ADDRESS>`
4. **Confirm** (in Discord, no credential value): `Stored "<name>" in hAIveMind + 1Password Employee vault. Discord message deleted.`

## Lookup Flow (`/cred lookup <name>`)

1. Search hAIveMind: `mcporter call haivemind.search_memories query="CRED:<name>" limit=5` — use the most recently stored entry (check `stored_at` or `updated_at` timestamp)
2. If not found in hAIveMind, search 1Password: `op item get "<name>" --vault Employee --fields credential --reveal`
3. **Never post the value in Discord.** Instead respond: `Found "<name>". Value is in 1Password Employee vault (item: <name>). Want me to inject it somewhere or copy it to env?`
4. If <USER_NAME>explicitly says "show me" or "reveal", DM or post in a single ephemeral-style message then immediately delete it (same delete pattern as store).

## List Flow (`/cred list`)

Search hAIveMind: `mcporter call haivemind.search_memories query="CRED:" limit=50`
Extract names from `content` field, list them without values.
Also run: `op item list --vault Employee --categories "API Credential" --format json` and merge.

## Delete Flow (`/cred delete <name>`)

1. Delete from hAIveMind if possible (note: haivemind has no delete — mark it: `mcporter call haivemind.store_memory content="CRED:<name> DELETED at <ISO>" category="credentials"`)
2. Delete from 1Password: `op item delete "<name>" --vault Employee`
3. Confirm.

## 1Password Auth

See `references/1password-signin.md` for the tmux signin pattern.
Master password = Mac sudo password (from hAIveMind: `search_memories query="mac sudo password lance"`).
Vault for all creds: **Employee** (`ojkx73ff23ofkjvkokdq73cthu`).

## Security Rules

- NEVER echo the credential value in any Discord message.
- ALWAYS delete the source message before storing.
- Confirm only with the name, not the value.
- If signin fails, still store to hAIveMind and tell <USER_NAME>1Password failed.
