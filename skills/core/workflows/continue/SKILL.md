---
name: continue
description: Resume work in the current channel. Reads recent Discord messages as ground truth, then pulls any CHECKPOINT or SNAPSHOT entries from haivemind. Synthesizes context and continues from where things left off. Triggered by /continue or "continue" from <USER_NAME>.
category: workflows
runtimes: [claude]
pii_safe: true
---

# Continue Skill

Resume in-progress work by combining Discord message history (ground truth) with haivemind state (persistence layer).

## When to Use

- <USER_NAME>says `/continue`, "continue", "pick up where we left off", "resume"
- After a compaction, restart, or context loss
- When switching back to a thread after time away

---

## Step 1: Extract Channel ID

From the session key or inbound metadata:
- `agent:main:discord:channel:<DISCORD_CHANNEL_ID>` → `<DISCORD_CHANNEL_ID>`
- Use the `topic_id` from inbound context if available

---

## Step 2: Read Discord Messages (Ground Truth — FIRST, ALONE)

```
message action=read channelId=[channel-id] limit=30
```

Do NOT run anything else in parallel. Discord is always more current than any cached state.

Scan messages for:
- What task was being worked on
- What was completed vs. still open
- Any explicit "TODO", "next step", "blocked on", "waiting for" language
- The most recent concrete action taken

---

## Step 3: Pull haivemind State

```bash
# Search for snapshots and checkpoints in this channel
mcporter call haivemind.search_memories query="CHECKPOINT [channel-id]" limit=5
mcporter call haivemind.search_memories query="SNAPSHOT [channel-id]" limit=5
mcporter call haivemind.search_memories query="[channel-id] context" limit=10
```

Also load the channel directive file if it exists:
```bash
cat ~/dev/contexts/[channel-id].md 2>/dev/null
```

---

## Step 4: Synthesize and Resume

Reconcile:
1. **Discord wins** when Discord messages contradict haivemind state (Discord is more recent)
2. **haivemind fills gaps** for context not visible in recent messages (older decisions, file paths, credentials used, etc.)

Produce a single internal synthesis:
- What was the task?
- What's done?
- What's next?
- Any blockers or open questions?

Then immediately resume — don't ask <USER_NAME>what to do unless there's genuine ambiguity.

---

## Step 5: Store Resume Context

After synthesizing:
```bash
mcporter call haivemind.store_memory \
  content="CONTINUE [channel-id] [ISO-timestamp]: resumed from [source: discord|checkpoint|snapshot]. Task: [task summary]. Next: [next step]." \
  category="operations"
```

Update `~/dev/contexts/[channel-id].md` with current focus and next steps.

---

## Output Style

One paragraph, direct:

> "Back on it. We were [doing X], and had just [completed Y / hit blocker Z]. Continuing with [next step] now."

Then immediately take action — don't list bullets or recap everything <USER_NAME>already knows.

---

## Related Skills

- `/snapshot` → call mid-task to save state
- `/checkpoint` → call at phase boundaries to mark progress
- haivemind-remember → for ad-hoc memory ops
