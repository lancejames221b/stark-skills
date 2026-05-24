# Thread Chaining Protocol

Cross-thread context handoff for multi-ticket projects. Ensures every ticket agent starts with full knowledge of what came before.

---

## Channel Orchestrator Mode

The **main project channel** (not a thread) can act as an orchestrator — monitoring overall project state and launching the next ticket agent on demand.

### Trigger

<USER_NAME> says any of these in the main channel:
- "kick it off"
- "start the next ticket"
- "next ticket"
- "launch [ENG-XXX]"
- "go" (when context is clear from thread map)

### Orchestrator Startup

When triggered from the main channel, the agent:

1. **Reads the channel directive** (`~/dev/contexts/[channel-id].md`) — gets thread map, current/next ticket
2. **Queries hAIveMind** for `TICKET-DONE [project-id]` — gets full prior ticket results
3. **Identifies the next ticket** — first thread with status `Up Next` or `Ready` in the thread map
4. **Checks dependencies** — verifies all dependency tickets are marked `✅ Done`
5. **Posts a status summary** in the main channel:
   ```markdown
   **ENG-682 Status** — [N] of [total] tickets complete
   ✅ ENG-690, ENG-691, ENG-692, ENG-693
   🔄 **Next: ENG-694** — Update main.py + core alert pipeline
   Dependencies: all met ✅

   Launching ENG-694 in <#THREAD_ID>...
   ```
6. **Posts the startup priming message** in the next ticket's thread (same format as Auto-Chain § 3)
7. **Updates the channel directive** — marks next ticket as `🔄 In Progress`

### Orchestrator Status Check

<USER_NAME> can also ask for a status report without launching:
- "status", "where are we", "project status", "what's done"

Response format:
```markdown
**ENG-682: TinyDB → Firestore Migration**
Progress: 4/10 tickets complete

✅ ENG-690 — GCP project fix (a750ff5)
✅ ENG-691 — config_firestore.py (8b448eb)
✅ ENG-692 — firestore_repositories.py (3ee8789)
✅ ENG-693 — Data migration to staging
🔄 ENG-694 — Update main.py + core alert pipeline [IN PROGRESS]
⏳ ENG-695 — [title] [Up Next]
⏳ ENG-696 — [title]
...

**Current:** ENG-694 in <#THREAD_ID>
**Blocked?** No
```

### When to Use Orchestrator Mode vs Thread Mode

| Situation | Where to act |
|-----------|-------------|
| Working on a specific ticket | In that ticket's thread |
| Checking overall project state | Main channel |
| Launching the next ticket | Main channel ("kick it off") |
| Handoff from one ticket to next | Ticket thread → next thread (auto-chain) |
| Dependency blocked | Main channel (post blocker notice) |

---

## The Problem

A project has N Discord threads, one per ticket. Each thread runs its own agent. When ticket N completes and ticket N+1 starts, the new agent has zero context — no knowledge of commits, file changes, decisions, or blockers from prior tickets.

## Three-Layer Handoff

| Layer | Storage | Survives | Speed | Purpose |
|-------|---------|----------|-------|---------|
| 1. hAIveMind | Cross-session memory | Compaction, resets, new sessions | ~1s query | Durable structured records |
| 2. Channel directive | `contexts/[channel-id].md` | Disk persistence | Instant (file read) | Fast project state snapshot |
| 3. Pinned thread message | Discord thread | Visible to human + agent | Instant (in thread) | Human-readable, copy-paste restore |

All three layers are updated together. No layer is optional.

---

## 1. Startup Protocol

Every ticket agent executes these steps in its first 60 seconds, before any work begins.

### Step 1: Read channel directive (instant)

```bash
cat ~/dev/contexts/[channel-id].md
```

Extract:
- Thread map (ticket → thread-id → status)
- Handoff notes from completed tickets
- Current active ticket and dependencies
- Project branch, Notion URL, model assignment

### Step 2: Query hAIveMind (cross-session context)

```bash
mcporter call haivemind.search_memories query="TICKET-DONE [project-id]" limit=20
```

Parse all `TICKET-DONE` entries. Extract:
- What each prior ticket accomplished
- Files created/modified
- Commits made
- Key decisions and their rationale
- Any blockers or known issues
- What the current ticket specifically needs from prior work

### Step 3: Check for auto-chain priming message

Look in the current thread for a message from the prior ticket's agent:
> "ENG-XXX is done. Here's what you need to know: [handoff]. Ready to start?"

If present, this is the most recent and specific context — use it.

### Step 4: Post thread opening message

Post a message in the thread summarizing restored context:

```markdown
## Context Restored

**Prior tickets completed:** ENG-690 ✅, ENG-691 ✅, ENG-692 ✅, ENG-693 ✅
**Key files from prior work:**
- `src/config/firestore_db.py` — Firestore client (ENG-690)
- `src/config/config_firestore.py` — Config drop-in (ENG-691)
- `src/database/firestore_repositories.py` — All 8 repos (ENG-692)

**My dependencies:**
- [x] ENG-691 config_firestore.py exists
- [x] ENG-692 firestore_repositories.py exists
- [x] ENG-693 data migrated to staging Firestore

**Starting work on ENG-694: Update main.py + core alert pipeline**
```

### Step 5: Verify dependencies

Before writing any code:
1. Confirm dependency files exist on disk (`ls -la [file]`)
2. Confirm dependency commits exist (`git log --oneline -1 [hash]`)
3. If any dependency is missing or broken, STOP and report in thread + parent channel

### Step 6: Begin work

Only after Steps 1-5 pass. Work normally.

---

## 2. Completion Protocol

Every ticket agent executes these steps when its work is done, before signing off.

### Step 1: Write TICKET-DONE to hAIveMind

```bash
mcporter call haivemind.store_memory \
  content="TICKET-DONE [PROJECT_ID] [TICKET_ID] [ISO_TIMESTAMP]: result=[success|partial|blocked] commits=[hash1,hash2] files_created=[path1,path2] files_modified=[path3,path4] key_decisions=[decision1; decision2] next_ticket_needs=[what the next ticket specifically requires from this work] blockers=[any known issues or none]" \
  category="operations"
```

**Format rules:**
- `result`: one of `success`, `partial`, `blocked`
- `commits`: comma-separated short hashes (7 chars)
- `files_created` / `files_modified`: comma-separated paths relative to project root
- `key_decisions`: semicolon-separated, each a short sentence
- `next_ticket_needs`: specific, actionable — not vague ("needs config" ❌, "needs config_firestore.py imported in main.py and FIRESTORE_ENABLED env var set" ✅)
- `blockers`: specific issues or `none`

**Example:**
```
TICKET-DONE ENG-682 ENG-693 2026-03-02T14:30:00-05:00: result=success commits=f4a2b1c,9e3d7a2 files_created=scripts/migrate_data.py files_modified=src/config/firestore_db.py,src/database/firestore_repositories.py key_decisions=used batch writes for migration perf; kept TinyDB as fallback until ENG-698; added FIRESTORE_MIGRATION_DRY_RUN env flag next_ticket_needs=import config_firestore instead of config_tinydb in main.py; firestore_repositories replaces all direct TinyDB calls; FIRESTORE_ENABLED=true must be set in .env blockers=none
```

### Step 2: Update channel directive

Append to the `## Handoff Notes` section of `~/dev/contexts/[channel-id].md`:

```markdown
### ENG-693 ✅
- [1-3 sentence summary of what was accomplished]
- Commits: `f4a2b1c`, `9e3d7a2`
- Files created: `scripts/migrate_data.py`
- Files modified: `src/config/firestore_db.py`, `src/database/firestore_repositories.py`
- Key decision: Used batch writes for migration performance
- Next ticket needs: Import config_firestore in main.py, set FIRESTORE_ENABLED=true
```

Also update:
- Thread Map table: change this ticket's status to `✅ Done`
- Thread Map table: change next ticket's status to `🔄 Up Next` or `🔄 Ready`
- `## Active Work` section: advance current/next pointers

### Step 3: Update Notion page

Update the ticket's row in the Notion page table: status → Done.

```bash
# Use notion-oauth to update the ticket status on the project page
# (Exact method depends on page structure — update the relevant block)
```

### Step 4: Update Linear ticket

```bash
mcporter call linear.update_issue issueId="ENG-693" stateId="[DONE_STATE_ID]"
```

To find the Done state ID for the team:
```bash
mcporter call linear.list_workflow_states teamId="[TEAM_ID]"
```

### Step 5: Post completion message in thread

Post to the current ticket's thread:

```markdown
## ✅ ENG-693 Complete

**Result:** Success
**Commits:** `f4a2b1c`, `9e3d7a2`

**What was done:**
- [Summary of work]

**Key decisions:**
- [Decision 1 and why]
- [Decision 2 and why]

**Files changed:**
- Created: `scripts/migrate_data.py`
- Modified: `src/config/firestore_db.py`, `src/database/firestore_repositories.py`

**What ENG-694 needs to know:**
- Import `config_firestore` instead of `config_tinydb` in `main.py`
- `firestore_repositories` replaces all direct TinyDB calls
- Set `FIRESTORE_ENABLED=true` in `.env`
```

### Step 6: Update Discord thread name

Add ✅ prefix to thread name:
```
message action=channel-edit channel=discord channelId=[THREAD_ID] name="✅ ENG-693 | Data migration"
```

### Step 7: Post in parent channel

Post a brief notice in the parent channel (not the thread):

```markdown
✅ **ENG-693** complete — data migration to staging Firestore done.
→ Next: **ENG-694** (Update main.py + core alert pipeline) in <#NEXT_THREAD_ID>
```

---

## 3. Auto-Chain (Priming the Next Thread)

After completion Steps 1-7, if there IS a next ticket:

### Post priming message in the NEXT ticket's thread

```markdown
## 🔗 Handoff from ENG-693

ENG-693 is done. Here's what you need to know:

**What was accomplished:** [1-2 sentence summary]
**Commits:** `f4a2b1c`, `9e3d7a2`

**What YOU need:**
- Import `config_firestore` instead of `config_tinydb` in `main.py`
- `firestore_repositories.py` replaces all direct TinyDB calls
- Set `FIRESTORE_ENABLED=true` in `.env`

**Your dependencies are met:**
- [x] ENG-691: config_firestore.py exists
- [x] ENG-692: firestore_repositories.py exists
- [x] ENG-693: Data migrated to staging Firestore

**Context restore:**
```bash
mcporter call haivemind.search_memories query="TICKET-DONE ENG-682" limit=20
cat ~/dev/contexts/[channel-id].md
```

Ready to start? Reply 'go' or 'start'.
```

This means <USER_NAME> can open the next thread and it's already primed with context. The next agent reads this priming message as part of its Startup Protocol (Step 3).

---

## 4. Context Restore Command

A single command block that <USER_NAME> (or any agent) can paste in any thread to restore full project context:

```bash
# Restore full project context
mcporter call haivemind.search_memories query="TICKET-DONE [PROJECT_ID]" limit=20
cat ~/dev/contexts/[channel-id].md
```

For the ENG-682 project specifically:
```bash
mcporter call haivemind.search_memories query="TICKET-DONE ENG-682" limit=20
cat ~/dev/contexts/<DISCORD_CHANNEL_ID>.md
```

This gives:
- All TICKET-DONE entries from hAIveMind (what every completed ticket did)
- Current project state from the channel directive (thread map, active work, handoff notes)

---

## 5. Pinned Message Template

Every thread created by project-init should have its opening message pinned. The message includes the thread-chain startup hooks.

```markdown
## [TICKET_ID] — [TICKET_TITLE]

**Model:** `[MODEL]` · **Priority:** [PRIORITY] · **Phase:** [PHASE]
**Linear:** [LINEAR_URL] · **Notion:** [NOTION_URL]

---

### What
[2-3 sentences on what this ticket accomplishes]

### Steps
1. [Step 1]
2. [Step 2]
...

### Verification
- [ ] [Criterion 1]
- [ ] [Criterion 2]

### Dependencies
- [TICKET_ID]: [what's needed from it]
- ...

### Context Restore
On startup, run:
```bash
mcporter call haivemind.search_memories query="TICKET-DONE [PROJECT_ID]" limit=20
cat ~/dev/contexts/[CHANNEL_ID].md
```

### Prior Work Summary
_Updated as prior tickets complete:_
- ENG-690 ✅: [summary]
- ENG-691 ✅: [summary]
- ...
- ENG-[N-1] ✅: [summary] ← _most recent_

---

**Spawn:** `/thread [THREAD_NAME] --model [MODEL]`
**On completion:** Run `ticket-handoff.sh [TICKET_ID] [PROJECT_ID] [CHANNEL_ID] success "[COMMITS]" "[SUMMARY]"`
```

---

## Script: ticket-handoff.sh

Located at `~/dev/skills/project-init/scripts/ticket-handoff.sh`

Automates the completion protocol:

```bash
ticket-handoff.sh TICKET_ID PROJECT_ID CHANNEL_ID RESULT COMMITS SUMMARY
```

See the script for full implementation. It:
1. Writes TICKET-DONE to hAIveMind
2. Appends handoff notes to channel directive
3. Updates ticket status in the thread map
4. Posts completion message to the ticket's thread
5. Posts priming message to the next ticket's thread
6. Updates Linear ticket state

---

## Lifecycle Diagram

```
project-init creates threads
         │
         ▼
┌─────────────────────┐
│  Thread N starts    │
│  1. Read directive  │
│  2. Query haivemind │
│  3. Check priming   │
│  4. Post context    │
│  5. Verify deps     │
│  6. DO WORK         │
│  7. Completion:     │
│     - haivemind     │
│     - directive     │
│     - notion        │
│     - linear        │
│     - thread msg    │
│     - thread name   │
│     - parent msg    │
│     - prime N+1     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Thread N+1 starts  │
│  (already primed)   │
│  Repeat cycle...    │
└─────────────────────┘
```

---

## Error Handling

- **hAIveMind down:** Fall back to channel directive (Layer 2) only. Log warning. Do not skip context restore.
- **Channel directive missing:** Query hAIveMind and reconstruct. Post warning in thread.
- **Dependency not met:** Do NOT proceed. Post in thread AND parent channel: "ENG-XXX blocked: dependency ENG-YYY not complete. [specifics]"
- **Linear update fails:** Log warning, continue. Linear state is advisory, not blocking.
- **Auto-chain fails (next thread doesn't exist):** Log warning, post in parent channel instead.

---

## Integration with project-init

The project-init skill creates threads with the pinned message template (Section 5). The template includes:
- Context restore commands pre-filled
- Dependency list from the project plan
- "Prior Work Summary" section (empty at creation, filled as tickets complete)
- The `ticket-handoff.sh` invocation line

When a ticket agent is spawned via `/thread`, it follows the Startup Protocol (Section 1). When it finishes, it follows the Completion Protocol (Section 2) and Auto-Chain (Section 3).

The channel directive (`contexts/[channel-id].md`) is the single source of truth for project state. Both the Startup and Completion protocols read/write it.
