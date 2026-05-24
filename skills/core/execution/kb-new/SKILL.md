---
name: kb-new
description: Create a new Cline Kanban project from scratch — `git init` a new repo if needed, drop a starter README.md, make the initial commit, and register it as a Cline Kanban workspace. Works in any directory under ~/Dev/ (or wherever the user specifies). Uses `--no-verify` on the initial commit only if <PROJECT_NAME> pre-commit hooks block (most new empty projects have nothing to flag, so it shouldn't come up). Use when the user says "kb-new", "new kanban project", "make a new project", "create a project for X", or wants to start a fresh Cline Kanban workspace.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban New Project Skill

Bootstraps a new Cline Kanban workspace from nothing: directory + git repo + initial commit + workspace registration.

Project-agnostic. Works for any new project (a new tool, a new experiment, a new client engagement). Cline Kanban auto-registers any git repo when its path is first passed to `task create --project-path`, so the project comes online the moment its first task is created.

## When to use

Triggers: `/kb-new`, "kb-new", "new kanban project", "create a new project", "make a project for X", "init a project and register with kanban".

Don't use this for projects that already exist — for those, just call `/kb-do --project <path> ...` and Cline Kanban auto-registers on the first task. This skill is specifically for fresh, empty starts.

## Inputs

- **Required:** project name (used as both directory name and starter title)
- **Optional flags:**
  - `--path <dir>` — explicit parent dir (defaults to `~/Dev/`)
  - `--description "<text>"` — short description for the README and the starter task
  - `--with-task` — create a starter Cline Kanban task after init (default: skip; just register on next kb-do call)
  - `--remote <url>` — set git remote `origin` (default: none)
  - `--private` — generate a `.gitignore` with strict defaults

## Procedure

1. **Resolve project path.**
   - If user gave `--path <dir>`, project path = `<dir>/<name>`.
   - Otherwise, default = `~/Dev/<name>`.
   - Expand `~`, normalize.

2. **Check for collision.** If the path already exists:
   - If it's already a git repo with a `.git/` dir, surface this and ask the user whether to (a) re-register it with Cline Kanban or (b) abort.
   - If it exists but isn't a git repo, ask whether to `git init` in place or abort.

3. **Create directory** if needed: `mkdir -p <project-path>`.

4. **Initialize git:**
   ```bash
   cd <project-path>
   git init -b main
   ```
   Use `-b main` to default to `main` (matches user's project layout).

5. **Drop a starter README.md** with frontmatter-free content:
   ```markdown
   # <project-name>

   <description from --description, or "TBD: project description">

   Created: <today, YYYY-MM-DD>
   ```

6. **(Optional) Drop a `.gitignore`** if `--private` was passed. Defaults: `.env`, `.env.*`, `*.log`, `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`, `.DS_Store`.

7. **Make the initial commit.** Try a normal commit first:
   ```bash
   git add README.md .gitignore  # only files that exist
   git commit -m "Initial commit"
   ```
   - If pre-commit hooks (<PROJECT_NAME>) block: rerun with `--no-verify`. New empty projects have nothing for <PROJECT_NAME> to flag, but if the user has a global hook that runs lint/test on commit, those can spuriously fail on an empty repo. `--no-verify` is fine here because the commit is just an empty-project marker.
   - Never re-run with `--no-verify` for a project with substantive content without telling the user first.

8. **(Optional) Set git remote** if `--remote <url>` was passed:
   ```bash
   git remote add origin <url>
   ```
   Don't push automatically. The user pushes when they're ready.

9. **Register with Cline Kanban.** Two options:
   - **`--with-task` flag:** Create a starter task using `kbd` (the kb-do CLI wrapper):
     ```bash
     kbd --project <project-path> --start "Set up <project-name>: <description>"
     ```
     This registers the workspace AND gives the user a first ticket to start working from.
   - **Default (no flag):** No task created. The workspace will auto-register the first time the user runs `/kb-do --project <project-path> ...`. Print a hint with the next-step command.

10. **Confirm.** Print:
    - Project path
    - Git status (branch, initial commit hash)
    - Cline Kanban workspace status (registered now via `--with-task`, or pending first task)
    - The Cline Kanban URL: http://<TAILSCALE_IP>:3000/<PROJECT_NAME>
    - Suggested next command (e.g., `kbd --project <path> "first task"`)

## Implementation reference

Run via Bash, in this order:

```bash
PROJ_NAME="<name>"
PROJ_PATH="${HOME}/Dev/${PROJ_NAME}"  # or --path-derived

# 1. Check & create
[ -e "$PROJ_PATH" ] && { echo "exists, aborting or asking"; exit 1; }
mkdir -p "$PROJ_PATH"
cd "$PROJ_PATH"

# 2. git init
git init -b main

# 3. README + (optional) .gitignore
cat > README.md <<EOF
# ${PROJ_NAME}

<description or "TBD">

Created: $(date +%Y-%m-%d)
EOF

# 4. Initial commit (try normal first, fall back to --no-verify if hooks block)
git add -A
if ! git commit -m "Initial commit" 2>/tmp/commit-err; then
  echo "Hook blocked initial commit; retrying with --no-verify (empty project, safe)"
  git commit --no-verify -m "Initial commit"
fi

# 5. Optional remote
[ -n "$REMOTE" ] && git remote add origin "$REMOTE"

# 6. Register with Cline Kanban (only if --with-task)
if [ "$WITH_TASK" = "1" ]; then
  kbd --project "$PROJ_PATH" --start "Set up ${PROJ_NAME}: ${DESCRIPTION:-initial scaffolding}"
fi
```

## --no-verify policy

<PROJECT_NAME> is the user's pre-commit hook system. It exists to catch real problems (secrets, broken builds, etc.) before they hit the repo.

Rules:
- **Default: try without `--no-verify`.** Run the normal commit first.
- **Fall back to `--no-verify` only when:**
  - The repo is brand new (just created in this skill run)
  - The commit has zero or near-zero content (only README + .gitignore)
  - The hook failure is clearly false-positive (e.g., a lint hook complaining about no source files yet)
- **Never `--no-verify` silently.** Always print "Hook blocked initial commit; retrying with --no-verify (empty project, safe)" so the user sees it.
- **For non-trivial commits in an existing project, never auto-fall-back.** Surface the hook error and ask.

## Anti-patterns

- Do NOT `git add .` in a directory the user already had files in without confirming.
- Do NOT push to a remote automatically. User pushes when ready.
- Do NOT register a workspace without telling the user the next-step command.
- Do NOT create a starter task by default (`--with-task` is opt-in) — sometimes the user just wants the scaffolding.
- Do NOT init in `/`, `~`, or any path the user didn't specify or default to.

## Companion skills

- `/kb-do` — implementation tickets with model selection
- `/kb-plan` — planning tickets (Opus + plan mode)
- `/kb-status` — show current board state for a project
- `/kb-trash` — clean up tasks
- `/kb-link` — link tasks for dependencies
- `/kanban` — passcode + service management for the Cline Kanban server itself
