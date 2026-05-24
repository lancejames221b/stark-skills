---
name: checkpoint
description: Mark a logical phase completion in haivemind. More formal than /snapshot — used at step/phase boundaries in multi-phase work. Creates a named, resumable point that /continue can restore from. Triggered by /checkpoint, "checkpoint this", "mark this as a checkpoint", or at phase boundaries in long-running tasks.
---

# Checkpoint Skill

A named, structured save point at a logical phase boundary. Higher-level than `/snapshot` — meant to capture "we finished phase N, starting phase N+1" rather than "here's my working state mid-step."

**Difference from snapshot:**
- **Snapshot** = frequent, lightweight, mid-task ("save where I am right now")
- **Checkpoint** = phase boundary, named, synthesized ("phase 1 done, here's what we learned, phase 2 starts here")

---

## When to Use

- <USER_NAME> says `/checkpoint`, "checkpoint this", "mark this", "save progress"
- End of a distinct phase in a multi-phase task
- Before handing off to a sub-agent or switching models
- After completing a major deliverable (file written, deploy done, analysis finished)
- At logical "resume from here" points in long-running work

---

## Step 1: Extract Channel ID + Phase Name

From session key or inbound metadata → channel ID.

**Phase name:** Either infer from context (e.g., "analysis", "deploy", "investigation-phase-1") or use a step number. Ask <USER_NAME> only if genuinely ambiguous.

---

## Step 2: Build Checkpoint Synthesis

More thorough than a snapshot. Capture:

- **Phase completed:** What phase/step just finished? (name or number)
- **Summary:** What happened in this phase? (2-3 sentences max)
- **Key artifacts:** Files created/modified, URLs, IDs, hashes, configs — anything needed to resume
- **Decisions made:** Any significant choices, trade-offs, or approaches locked in
- **Outcome:** Success / partial / blocked — what's the state?
- **Next phase:** What is phase N+1? What's the starting point?
- **Open items:** Anything incomplete, deferred, or waiting

---

## Step 3: Store to haivemind

```bash
mcporter call haivemind.store_memory \
  content="CHECKPOINT [channel-id] phase=[phase-name] [ISO-timestamp]: summary=[2-3 sentence synthesis] | artifacts=[paths/IDs/URLs] | decisions=[key choices made] | outcome=[success|partial|blocked] | next=[next phase start point] | open=[deferred items or none]" \
  category="operations"
```

**Also store a resume key** for easy retrieval:
```bash
mcporter call haivemind.store_memory \
  content="TASK-RESUME [channel-id] [ISO-timestamp]: [phase-name] complete. Resume point: [exact next action]. Artifacts: [key refs]." \
  category="operations"
```

---

## Step 4: Update Channel Directive

Write the checkpoint to `<LOCAL_PATH>/dev/contexts/[channel-id].md`:

```markdown
## Last Checkpoint: [phase-name] — [ISO-timestamp]
- Phase completed: [name]
- Summary: [2-3 sentences]
- Key artifacts: [list]
- Next: [next phase]
- Open items: [list or none]
```

---

## Step 5: Confirm

```
Checkpoint saved: [phase-name]. [One sentence on what's done and what's next.]
```

If there are open items that need <USER_NAME>'s attention, surface them here — otherwise stay brief.

---

## Named Checkpoints

When working on a task with a known ID (e.g. `aisuru` RE task, `<PROJECT_NAME>` research):

```bash
mcporter call haivemind.store_memory \
  content="CHECKPOINT [task-id] [phase-name] [ISO-timestamp]: [synthesis]" \
  category="operations"
```

Sub-agents can then resume with:
```bash
mcporter call haivemind.search_memories query="CHECKPOINT [task-id]" limit=5
```

---

## Checkpoint Chain (for multi-phase work)

When starting a new phase after a checkpoint, always begin with:
```bash
mcporter call haivemind.search_memories query="CHECKPOINT [channel-id]" limit=5
```

This builds an explicit checkpoint chain, making `/continue` restoration reliable even after compaction or session restart.

---

## Related Skills

- `/continue` → restores from the most recent checkpoint
- `/snapshot` → lightweight mid-task saves between checkpoints
- long-agent skill → uses checkpoint pattern for agent handoffs
