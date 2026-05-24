---
name: project-update
description: Generate a verified project status update with 100% confidence. Collects real-time evidence from haivemind, Linear tickets, working docs (runbook/Notion), and live system state before writing anything. Posts a Linear project status update, updates haivemind, and updates the working doc. Use when <USER_NAME>says "/update", "project update", "status update for [project]", or "update the project". Default model is unit-sonnet-high. Never assert status without verified evidence.
category: workflows
runtimes: [claude]
pii_safe: true
---

# /update — Verified Project Status Update

**Model:** unit-sonnet-high (always — this skill requires high-confidence reasoning)

## What This Skill Does

Collects verified evidence from all sources → synthesizes a 100%-confidence status → posts Linear project update + updates haivemind + updates working doc.

**Rule:** Never write a status update from memory. Every claim must have a source.

---

## Step 1: Identify the Project

Determine the project from context:
- Channel directive (`contexts/[channel-id].md`) → `currentFocus` or project name
- Explicit mention by <USER_NAME>update <PROJECT_NAME>", "update <PRODUCT_NAME>")
- Default: current channel's active project

Resolve to:
- Linear project ID + name
- Working doc path (runbook or Notion page URL)
- haivemind search tags (e.g. `<PROJECT_NAME>`, `ew-migration`)

---

## Step 2: Collect Evidence (MANDATORY — no skipping)

Run ALL of these before writing anything:

### 2a. haivemind
```bash
mcporter call haivemind.search_memories query="[project] [channel-id] status" limit=15
mcporter call haivemind.search_memories query="AGENT-CHECKPOINT [project]" limit=10
```

### 2b. Linear tickets
```bash
mcporter call linear.list_issues 'filter={"project":{"id":{"eq":"[project-id]"}}}' 'limit=30'
```
Extract per ticket: identifier, title, state name.

### 2c. Working doc
Read the runbook or Notion page — extract:
- What's marked ✅ Done
- What's marked In Progress / active
- What's blocked
- What's the stated target date

### 2d. Live system check (if applicable)
For infra projects: run 2-3 targeted checks to confirm "done" items are actually done.
Example: `systemctl is-active [service]`, `gcloud storage ls [path]`, `psql COUNT(*)`.

**Do NOT skip live checks for items marked Done in docs — verify them.**

### 2e. Recent Discord/channel history
```bash
message action=read channelId=[channel-id] limit=20
```
Capture any decisions, blockers, or completions from the last session.

---

## Step 3: Synthesize — 100% Confidence Only

Build the status from verified evidence only. For each item:
- ✅ **Confirmed Done** — verified by live check OR multiple consistent sources
- 🔄 **In Progress** — actively running, confirmed by log/process/recent activity
- ⚠️ **Blocked** — specific blocker identified with evidence
- ❌ **Not Started** — no evidence of any work

**Never write** "should be done", "likely complete", "probably working". If uncertain → mark as unverified and flag it.

Format:
```
## [Project Name] — Status Update [DATE]

### Summary
[2-3 sentence executive summary — what's the state, what's the trajectory]

### Confirmed Done ✅
- [item] — verified via [source/evidence]

### In Progress 🔄
- [item] — [current state, last activity timestamp]

### Blocked ⚠️
- [item] — [specific blocker, who owns it]

### Not Started ❌
- [item]

### Next Steps
1. [Most critical next action]
2. [Second action]

### Confidence
[X]% — [note any items where confidence < 100%]
```

---

## Step 4: Post to Linear

Use `linear.save_status_update`:

```bash
mcporter call linear.save_status_update \
  'type="project"' \
  'project="[project-uuid]"' \
  'body="[formatted status]"' \
  'health="onTrack|atRisk|offTrack"'
```

> **New ticket default:** All tickets created via this skill (or any other) default to **Backlog** state unless <USER_NAME>explicitly says otherwise. Never create a ticket directly into Todo or In Progress.

Status health mapping:
- All blockers have owners + ETAs → `onTrack`
- Blockers without clear resolution → `atRisk`
- Missed dates or critical path blocked → `offTrack`

---

## Step 5: Update haivemind

```bash
mcporter call haivemind.store_memory \
  content="PROJECT-UPDATE [project] [ISO-timestamp]: [summary]. Done: [N]. InProgress: [N]. Blocked: [N]. Confidence: [X]%." \
  category="operations"
```

---

## Step 6: Update Working Doc

If project has a runbook (markdown file in `docs/`):
- Update `Last Updated` header
- Update any checklist items that are now confirmed done
- Commit + push

If project has a Notion page:
```bash
mcporter call notion-oauth.notion-fetch pageId="[page-id]"
# Update relevant sections, then:
mcporter call notion-oauth.notion-update-page pageId="[page-id]" content="[updated]"
```

---

## Project Registry

Known projects (extend as needed):

| Trigger | Linear Project ID | Working Doc | haivemind tags |
|---------|------------------|-------------|----------------|
| <PROJECT_NAME> / <PROJECT_NAME> | `<UUID>` | `docs/infrastructure/GIBSON_CUTOVER_RUNBOOK.md` | `<PROJECT_NAME>`, `<DISCORD_CHANNEL_ID>` |
| <PRODUCT_NAME> / ew-migration | Look up from Linear | Notion page | `<PRODUCT_NAME>` |

---

## Result Posting

After completing, post summary to current Discord channel:
```
message action=send channel=discord target=[channel-id] message="✅ **Project Update Posted**\n\n[2-sentence summary]\n\nLinear updated · haivemind stored · doc updated"
```

---

## Confidence Requirement

If overall confidence < 85%:
1. Flag which items are unverified
2. Run targeted live checks to resolve them
3. Only post when confidence ≥ 85%
4. If can't reach 85% → report what's blocking verification before posting

**Never post a status update that contains unverified claims without flagging them explicitly.**
