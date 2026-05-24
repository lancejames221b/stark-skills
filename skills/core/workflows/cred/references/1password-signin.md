# 1Password CLI Signin (tmux pattern)

Always run `op` inside a tmux session. Never run directly in exec shell.

```bash
SOCKET_DIR="${TMPDIR:-/tmp}/openclaw-tmux-sockets"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/openclaw-op.sock"
SESSION="op-$(date +%Y%m%d-%H%M%S)"

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell

# Signin
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'eval $(op signin) 2>&1' Enter
sleep 2

# Send master password
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'MASTER_PASSWORD' Enter
sleep 3

# Verify
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'op whoami 2>&1' Enter
sleep 2
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -10
```

Replace `MASTER_PASSWORD` with value from hAIveMind:
```bash
mcporter call haivemind.search_memories query="mac sudo password lance" limit=3
```

## Update existing item

```bash
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- \
  'op item edit "ITEM_TITLE" --vault "Employee" "credential[password]=NEW_VALUE" 2>&1' Enter
sleep 4
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -10
```

If item not found, fall back to create.

## Create item

```bash
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- \
  'op item create --category "API Credential" --title "ITEM_TITLE" --vault "Employee" "credential[password]=VALUE" "username[text]=<EMAIL_ADDRESS>" 2>&1' Enter
sleep 4
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -10
```

## Cleanup

```bash
tmux -S "$SOCKET" kill-session -t "$SESSION" 2>/dev/null
```

## Notes

- Session token is ephemeral — re-signin each time
- Vault: `<VAULT_NAME>` (`<VAULT_UUID>`)
- Account: `<YOUR_1PASSWORD_ACCOUNT>` (e.g. `acme.1password.com`) / `<EMAIL_ADDRESS>`
