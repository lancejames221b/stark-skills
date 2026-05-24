---
name: gstack
description: |
  Run Garry Tan's gstack workflow commands from Discord via Claude Code ACP sessions.
  Use when <USER_NAME>says /gstack, "gstack review", "gstack ship", "gstack plan", "gstack qa",
  "gstack retro", or asks to run any gstack workflow on a repo. Maps to 6 operating modes:
  plan-ceo (product review), plan-eng (architecture review), review (pre-landing code review),
  ship (sync+test+PR), qa (browser QA testing), retro (engineering retrospective).
category: workflows
runtimes: [claude]
pii_safe: true
---

# gstack — Discord Bridge

Wraps gstack's Claude Code skills for use from Discord. Spawns an ACP Claude Code session
in the target repo with the appropriate gstack skill, streams results back to Discord.

## Command Parsing

Parse the user's message for:
- `command`: plan-ceo | plan-eng | review | ship | qa | retro
- `repo`: repo name or path (optional for plan, required for others)
- `url`: target URL (for qa command)
- `extra`: any additional context

**Repo resolution** (check in order):
1. Exact path if starts with `/` or `~/`
2. `~/dev/<repo>` — try common names: `ew-api`, `ew-ui`, `ewitness_auth_server`, `dstorm-common`, `<PROJECT_NAME>`
3. Fuzzy match: `ls ~/dev/ | grep -i <name>`
4. If ambiguous, ask <USER_NAME>to clarify

**Command aliases:**
- `plan`, `ceo-plan`, `product` → `plan-ceo`
- `eng-plan`, `arch`, `architecture` → `plan-eng`
- `review`, `pr`, `code review` → `review`
- `ship`, `deploy`, `push`, `pr` → `ship`
- `qa`, `test`, `browser test` → `qa`
- `retro`, `retrospective` → `retro`

## Skill File Paths

All gstack skills are at `~/.claude/skills/gstack/<command>/SKILL.md`.

## Spawning the ACP Session

For each command, spawn a Claude Code ACP session (runtime="acp") in the target directory.

The task prompt must:
1. Tell Claude to read and follow the gstack skill: `~/.claude/skills/gstack/<command>/SKILL.md`
2. Provide the user's request/context
3. Instruct it to run non-interactively (no AskUserQuestion — make opinionated decisions)
4. Ask it to post a summary to Discord channel <DISCORD_CHANNEL_ID> when done

### Task Prompt Template

```
Read and follow the skill at ~/.claude/skills/gstack/<COMMAND>/SKILL.md exactly.

Context: <USER_CONTEXT>
<URL_LINE if qa>
<REPO_LINE if applicable>

Run non-interactively — make opinionated decisions without asking for input.
When complete, post a summary to Discord channel <DISCORD_CHANNEL_ID> using the message tool.
Format: brief headline + key findings as bullets. Keep it under 2000 chars.
```

### sessions_spawn Parameters

```json
{
  "runtime": "acp",
  "mode": "run",
  "cwd": "<resolved_repo_path>",
  "task": "<prompt above>",
  "streamTo": "parent"
}
```

- For `plan` commands with no repo: use `~/dev` as cwd
- For `qa` with just a URL and no repo: use `~/dev` as cwd
- Set `runTimeoutSeconds: 300` (5 min) — gstack workflows can take a while

## Per-Command Notes

### /review
- Requires a repo with an active branch (not main)
- If no branch specified, it will check the current branch
- Looks for: SQL safety, LLM trust boundaries, conditional side effects, race conditions

### /ship
- Only for branches that are READY — syncs main, runs tests, opens PR
- Warn <USER_NAME>if he asks to /ship without saying the branch is ready

### /plan-ceo
- No repo needed — takes a product description
- Prompt <USER_NAME>if he just says "gstack plan" without a description: "What are you building?"

### /plan-eng
- Locks in architecture, data flow, failure modes, diagrams, test matrix
- Works with a description OR inside a repo for context

### /qa
- Requires a URL (local or remote)
- Browse binary at: `~/.claude/skills/gstack/browse/dist/browse`
- Modes: full (default), --quick (30s smoke test), --regression

### /retro
- Runs in the repo, analyzes last N commits (default: week)
- Team-aware — breaks down per contributor

## Response to <USER_NAME>

After spawning:
1. Ack immediately: "Running gstack `/<command>` on `<repo>` — results coming shortly."
2. The ACP session posts results to Discord directly when done
3. If spawn fails, report the error and suggest running it directly via Claude Code

## Help Command

If <USER_NAME>says `gstack help`, `gstack ?`, or `/gstack` with no arguments, respond directly (no ACP session needed) with this formatted Discord message:

```
**gstack** — Garry Tan's Claude Code workflow stack, callable from Discord

**Commands:**
`gstack review <repo>` — Paranoid staff engineer. Finds bugs that pass CI but blow up in prod.
`gstack ship <repo>` — Release engineer. Sync main, run tests, open PR in one shot.
`gstack plan <description>` — CEO/founder mode. Pressure-tests whether you're building the right thing.
`gstack eng-plan <description>` — Eng manager mode. Architecture, data flow, failure modes, test matrix.
`gstack qa <url>` — QA engineer with eyes. Logs in, clicks through, screenshots, catches breakage.
`gstack retro <repo>` — Team retro. Per-contributor praise and growth areas from commit history.

**Repo shortcuts:** ew-api · ew-ui · ewitness_auth_server · dstorm-common · <PROJECT_NAME>
**Examples:**
  gstack review ew-api
  gstack plan I want to add OAuth to the <PRODUCT_NAME> API
  gstack qa http://localhost:3000
  gstack retro ew-api
```

## Example Invocations

- "gstack review ew-api" → review on ~/dev/ew-api
- "gstack ship ew-ui" → ship workflow on ~/dev/ew-ui  
- "gstack plan I want to add OAuth to the API" → plan-ceo with that description
- "gstack qa http://localhost:3000" → QA the local app
- "gstack retro ewitness_auth_server" → retro on auth server
- "gstack review" (no repo) → ask which repo
