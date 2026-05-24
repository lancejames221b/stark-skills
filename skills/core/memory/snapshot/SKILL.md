---
name: snapshot
description: Capture current working state to haivemind mid-task. A lightweight, frequent save point. Use when <USER_NAME>says /snapshot, "snapshot this", "save where we are", or automatically at natural pause points during long-running work. Complements /checkpoint (which is for phase boundaries).
category: memory
runtimes: [claude]
pii_safe: true
---

# Snapshot Skill

A quick, low-friction state save. Captures what's happening right now so `/continue` can restore it later.

**Difference from checkpoint:** Snapshots are frequent and lightweight — taken mid-task, mid-investigation, or before risky steps. Checkpoints mark logical phase completions with a higher-level synthesis.

---

## When to Use

- <USER_NAME>says `/snapshot`, "snapshot this", "save where we are", "save state"
- Before attempting a risky or multi-step operation
- After a significant tool call or finding, before moving to the next thing
- Every 10-15 major tool calls in long-running sub-agent tasks (auto)

---

## Step 1: Extract Channel ID

From session key or inbound metadata:
- `agent:main:discord:channel:<DISCORD_CHANNEL_ID>` → `<DISCORD_CHANNEL_ID>`

---

## Step 2: Capture Current State

Gather:
- **Current task:** What is being worked on right now?
- **Progress:** What has been completed in this session?
- **Active context:** File paths, URLs, ticket IDs, IPs, hashes, model names, service names — anything specific
- **Last action:** The most recent tool call or decision made
- **Next step:** What was about to happen?
- **Blockers:** Anything that's stuck or waiting on input

Do NOT summarize the entire conversation history — only the current working state.

---

## Step 3: Store to haivemind

```bash
mcporter call haivemind.store_memory \
  content="SNAPSHOT [channel-id] [ISO-timestamp]: task=[task summary] | progress=[what's done] | context=[active artifacts: paths/IDs/URLs] | last_action=[most recent thing done] | next=[planned next step] | blockers=[any blockers or none]" \
  category="operations"
```

**Format rules:**
- Use `|` as field separator for easy parsing on restore
- Keep total content under 500 chars where possible — dense, not verbose
- Always include the channel ID prefix

---

## Step 4: Confirm (Brief)

Reply with one line:
> "Snapshotted. [One-sentence summary of what was saved.]"

No need to repeat all fields back — <USER_NAME>knows what was happening.

---

## Automatic Snapshot Triggers (for sub-agents)

Sub-agents running long tasks SHOULD call snapshot:
- Every 10 major tool calls
- Before any destructive or irreversible action
- On error/exception before attempting recovery
- When switching approach (before the pivot, not after)

Format for sub-agent auto-snapshots:
```bash
mcporter call haivemind.store_memory \
  content="SNAPSHOT [channel-id] [ISO-timestamp] [task-id]: auto=[trigger reason] | [state fields]" \
  category="operations"
```

---

## Related Skills

- `/continue` → restore from this snapshot
- `/checkpoint` → use at phase boundaries (higher-level than snapshot)
- long-agent skill → integrates snapshot pattern for long-running agents
