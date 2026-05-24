# kanban — Setup

## Requirements

- Node.js (v18+ recommended)
- The `kanban` CLI package installed globally via npm

## 1. Install the Kanban CLI

```bash
npm install -g @cline/kanban
# or, if the package name differs on your registry:
npm install -g kanban
```

**Verify install:**
```bash
node <LOCAL_PATH>/.local/bin/kanban --version
# or, if kanban is on PATH:
kanban --version
```

## 2. Find the CLI path

The skill uses the absolute path `/usr/bin/node <LOCAL_PATH>/.local/bin/kanban` on <WORKSTATION_HOST> (dev). On other machines the path may differ.

```bash
which kanban                          # if installed on PATH
ls -la <LOCAL_PATH>/.local/bin/kanban  # <WORKSTATION_HOST> default
ls -la ~/.local/bin/kanban            # <INFERENCE_HOST> fallback
```

If the symlink points to a different location, update the path in any skill invocations accordingly.

## 3. Register the <VOICE_RUNTIME> workspace

Kanban uses the project path to identify which workspace to operate on. No explicit registration is needed — the CLI resolves the workspace from `--project-path`. Verify the path resolves correctly:

```bash
node <LOCAL_PATH>/.local/bin/kanban task list --project-path ~/Dev/<VOICE_RUNTIME>
```

This should return the current board state (or an empty board if no tasks exist yet). If the path is wrong, the CLI will error with a workspace-not-found message.

## 4. Live server (<INFERENCE_HOST>)

On <INFERENCE_HOST>, the CLI path may be different. Check with:

```bash
ssh <INFERENCE_HOST> "which kanban || ls ~/.local/bin/kanban"
```

Update invocations on the live server to use the resolved path. The `--project-path` should point to `~/dev/<VOICE_RUNTIME>-voice` (or whatever the live project root is on <INFERENCE_HOST>).

## 5. Environment Variables

The kanban CLI does not require environment variables for basic operation. Optional overrides:

| Variable | Purpose | Default |
|----------|---------|---------|
| `KANBAN_HOST` | Board server bind IP | `127.0.0.1` |
| `KANBAN_PORT` | Board server port | `auto` |

These are only relevant if you run `kanban` as a server (browser UI). The CLI subcommands (`task list`, `task create`, etc.) work without a running server.

## 6. Test the Integration

**List tasks (should return board or empty):**
```bash
node <LOCAL_PATH>/.local/bin/kanban task list --project-path ~/Dev/<VOICE_RUNTIME>
```

**Create a test task:**
```bash
node <LOCAL_PATH>/.local/bin/kanban task create \
  --title "test-task" \
  --prompt "This is a test task created to verify the kanban skill setup." \
  --project-path ~/Dev/<VOICE_RUNTIME>
```

**Verify it appears in backlog:**
```bash
node <LOCAL_PATH>/.local/bin/kanban task list \
  --project-path ~/Dev/<VOICE_RUNTIME> \
  --column backlog
```

**Trash the test task** (use the ID returned from list):
```bash
node <LOCAL_PATH>/.local/bin/kanban task trash \
  --task-id <id-from-above> \
  --project-path ~/Dev/<VOICE_RUNTIME>
```

**Voice test:**
Say: *"Jarvis, show me the kanban board"* — Jarvis should run `task list`, format the columns, speak a brief summary, and post the full board to Discord.
