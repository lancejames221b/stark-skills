---
name: project-init
description: "Auto-initialize a project channel with Notion hub page, planning board, Kanban database, Discord threads per task, and model assignments. Trigger: /project init [name] [qualifier?], init [directive], 'set up project', 'initialize this channel', 'create project threads'. Also handles /notion init and /kanban init as redirects to this skill. Planning phase ALWAYS uses max-high/claude-opus-4-6. Individual tasks assigned cost-appropriate models. After Notion setup, always offer to co-create a matching VibeKanban project (see vk-project skill)."
category: workflows
runtimes: [claude]
pii_safe: true
---

# project-init

Initialize a project end-to-end: parse directive → generate plan → **create VibeKanban project** → create Notion hub + planning page → pin in Discord → create threads → write channel directive → suggest time blocks.

> **`/notion init` and `/kanban init` both redirect here.** This skill handles all new project setup.
> **VibeKanban project creation is MANDATORY** — every project init creates both a VK project (tickets) and a Notion hub (docs/plans).
> For ongoing ticket management, use `~/dev/skills/vk-project/SKILL.md`. Notion is docs/plans only.

## ⚡ VK WRITE OPERATIONS — USE vk-direct (NON-NEGOTIABLE)

`mcp__vibe-kanban__create_issue` and `mcporter call vibe-kanban.create_issue` are BROKEN — port 14479 offline. Use the direct SQLite script for ALL ticket create/update ops:

```bash
python3 ~/dev/skills/vk-direct/scripts/vk.py create <project_hex> "title" --description "..." --status todo
python3 ~/dev/skills/vk-direct/scripts/vk.py update <task_id_prefix> --status inprogress
python3 ~/dev/skills/vk-direct/scripts/vk.py list <project_hex_or_name>
```

Full skill: `~/dev/skills/vk-direct/SKILL.md`

## Stack Roles (Non-Negotiable)

| System | Role |
|---|---|
| **VibeKanban** | Tickets + projects (created first, always) |
| **Notion** | Hub page, planning board, specs, documents |
| **HaiveMind** | Memory — context during tasks, cross-session state |
| **Discord channel** | Orchestrator — routes tasks, tracks project state |
| **Discord thread** | Task workspace — one per ticket, can sub-orchestrate |

---

## Trigger Patterns

- `/project init [name] [qualifier?]` — primary trigger
- `init [directive]` — legacy trigger
- `/notion init [name]` — redirect: runs this full workflow
- `/kanban init [name]` — redirect: runs this full workflow
- `/live init [directive]` — redirect from live skill: runs this full workflow, then registers hub as live source
- `set up project [directive]`
- `initialize this channel [directive]`
- `create project threads [directive]`
- `handoff to next thread` — post handoff to current thread + prime next thread
- `/live vk init [name]` — redirect from live skill: runs this workflow + creates VibeKanban project
- `kick it off` / `start the next ticket` / `next ticket` / `launch [ENG-XXX]` — orchestrator mode
- `status` / `where are we` / `project status` — orchestrator status (full ticket progress from thread map + hAIveMind)

---

## Qualifier Parsing (Time Blocks)

Parse the qualifier from the invocation to determine whether to suggest focus blocks:

| Qualifier | Action |
|-----------|--------|
| `weekend`, `personal`, `side`, `hobby` | **Skip** time blocks entirely |
| `work`, `priority`, `<ORG_NAME>`, `<ORG_NAME>`, `company`, `sprint` | **Yes** time blocks — fetch calendar, suggest 3-5 focus blocks, offer to create events |
| *(none)* | **Ask** — "Would you like me to check your calendar and suggest focus blocks for this project?" |

Time block logic runs in **Step 12** after the core init is complete.

---

## ⚠️ Handoff is MANDATORY

Every ticket agent MUST post a handoff when done. If it doesn't happen automatically, <USER_NAME>can say **"handoff to next thread"**:
1. Read `~/dev/contexts/[channel-id].md` to find the current ticket and next thread ID
2. Post completion summary to current thread
3. Post chain context/priming message to next thread
4. Run `ticket-handoff.sh` to update hAIveMind + channel directive

See `references/thread-chain.md` for the full protocol.

---

## Workflow

### Step 1: Parse the Directive

Extract from the user's message:
- **Project name** — infer from directive or ask if ambiguous
- **Description** — what the project accomplishes
- **Goals** — success criteria / definition of done
- **Known tasks** — any tickets, phases, or work items mentioned
- **Qualifier** — weekend / personal / side / hobby / work / priority / <ORG_NAME> / company / sprint (absent = ask)
- **Linear references** — any ENG-xxx tickets (fetch from Linear for context only — read-only)
- **Channel ID** — where `init` was invoked

---

### Step 2: hAIveMind + Existing Context Check

Before doing anything else:

```bash
# Search hAIveMind for prior context
mcporter call haivemind.search_memories query="[project-name] OR [channel-id]" limit=15

# Check if channel directive already exists
cat ~/dev/contexts/[channel-id].md 2>/dev/null

# If Linear tickets referenced, READ for context (never write to Linear)
mcporter call linear.get_issue issueId="ENG-XXX"
```

> ⚠️ **Linear is READ-ONLY.** Read/search for context only. ALL ticket creation → Notion via `notion-oauth`. Never call `linear.save_issue`, `linear.create_*`, `linear.update_*` — they return 403.

**If channel already has a directive:** Warn <USER_NAME>and ask before overwriting. Offer to merge existing context.

---

### Step 2.5: Create VibeKanban Project (MANDATORY)

Every project init creates a VK project. This is non-negotiable — VK is the source of truth for all tickets and work items.

```bash
# Fetch a fresh short-lived access token (expires ~2min, always fetch fresh)
VK_TOKEN=$(curl -s http://127.0.0.1:11700/api/auth/token | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# Color by project type (HSL format required -- hex is rejected)
# infra=220 70% 45%, security=0 70% 45%, feature=262 70% 55%, research=38 80% 45%, default=240 60% 50%
VK_COLOR="240 60% 50%"  # override based on project type

VK_RESULT=$(curl -s -X POST https://api.vibekanban.com/v1/projects \
  -H "Authorization: Bearer $VK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"[PROJECT_NAME]\",\"organization_id\":\"<ORG_ID>\",\"color\":\"$VK_COLOR\"}")

VK_PROJECT_ID=$(echo "$VK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "VK project created: $VK_PROJECT_ID"
```

**Color guide:**
| Project type | Color (HSL) |
|---|---|
| Infrastructure | `220 70% 45%` |
| Security | `0 70% 45%` |
| Feature / product | `262 70% 55%` |
| Research | `38 80% 45%` |
| Default / other | `240 60% 50%` |

Infer the type from the directive and set `VK_COLOR` accordingly.

Capture **VK_PROJECT_ID** for use in Steps 9, 10, and 11.

**If VK fails:** Note the error, continue with Notion init, and report the failure in Step 11. Do not abort the whole init for a VK API failure — but do flag it so <USER_NAME>can retry manually.

---

### Step 3: Generate Project Plan

```bash
python3 ~/dev/skills/project-init/scripts/generate-plan.py \
  --directive "FULL_DIRECTIVE_TEXT" \
  --channel-id "CHANNEL_ID" \
  --context "HAIVEMIND_CONTEXT_SUMMARY"
```

Output JSON:
```json
{
  "project_name": "Project Name",
  "description": "What this project accomplishes...",
  "definition_of_done": "All tests pass, acceptance criteria met...",
  "phases": [
    {
      "name": "Phase 1: Foundation",
      "tickets": [
        {
          "id": "T-001",
          "title": "Ticket title",
          "description": "What to build...",
          "steps": ["1. Do X", "2. Do Y"],
          "verification": "Acceptance criteria",
          "model": "sonnet-medium",
          "priority": "high",
          "complexity": "standard"
        }
      ]
    }
  ],
  "total_tickets": 5,
  "estimated_complexity": "medium"
}
```

**If script fails:** Use opus-level reasoning to decompose the directive manually, following the same structure. Load `references/model-selection.md` for model assignments.

---

### Step 3.5: Detect Working Directory + Git Remote

```bash
PROJECT_SLUG=$(echo "[project-name]" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
PROJECT_DIR="$HOME/dev/$PROJECT_SLUG"

# Fall back to cwd if directory not found
if [ ! -d "$PROJECT_DIR" ]; then
  PROJECT_DIR=$(pwd)
fi

# Get git remote (empty if not a git repo)
GIT_REMOTE=$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")

echo "Working dir: $PROJECT_DIR"
echo "Git remote:  $GIT_REMOTE"
```

Capture `$PROJECT_DIR` and `$GIT_REMOTE` for embedding in the Notion hub page.

---

### Step 4: Create Notion Hub Page

The Hub Page is the central project directory — it links to everything.

```bash
TODAY=$(date '+%Y-%m-%d')

cat > /tmp/project-hub-content.md << 'EOF'
# [Project Name]

> **Status:** 🟢 Active · **Created:** [TODAY] · **Channel:** discord://[channel-id]

---

## Project Info

| Field | Value |
|-------|-------|
| **Local path** | `[PROJECT_DIR]` |
| **GitHub repo** | [GIT_REMOTE or "N/A"] |
| **Discord channel** | [channel link] |
| **Planning Board** | [PLANNING_PAGE_URL — fill after Step 5] |
| **Kanban Board** | [KANBAN_DB_URL — fill after Step 6] |

---

## Overview

[Description from plan]

---

## Definition of Done

[DoD from plan]

---

## Quick Links

- 📋 Planning Board: [PLANNING_PAGE_URL]
- 🗂️ Kanban: [KANBAN_DB_URL]
- 🧵 Discord threads: [thread count] threads created

EOF

# Create hub page under <ORG_NAME> Tasks
~/dev/skills/notion-oauth/create-page.sh \
  "[Project Name] — Hub" \
  "<UUID>" \
  /tmp/project-hub-content.md
```

**Parent:** <ORG_NAME> Tasks (`<ORG_ID>`) — non-negotiable.

Capture the returned **HUB_PAGE_ID** and **HUB_PAGE_URL**.

---

### Step 5: Create Planning Sub-page

The Planning Board is a sub-page inside the Hub Page — strategic view with phases, milestones, and ticket overview.

```bash
cat > /tmp/project-planning-content.md << 'EOF'
# [Project Name] — Planning Board

> Strategic overview: phases, milestones, goals, and ticket map.
> For live ticket tracking, see the [Kanban Board](KANBAN_DB_URL).

---

## Goals

[Goals from plan]

## Definition of Done

[DoD from plan]

## Phases

### Phase 1: [Phase Name]

**Goal:** [Phase goal]

| Ticket | Title | Model | Priority | Status |
|--------|-------|-------|----------|--------|
| T-001 | [title] | sonnet-medium | High | Backlog |
| T-002 | [title] | sonnet-high | High | Backlog |

### Phase 2: [Phase Name]

...

---

## Milestones

- [ ] Phase 1 complete: [criteria]
- [ ] Phase 2 complete: [criteria]
- [ ] All tickets Done: [DoD]

---

## Notes

[Any additional context from hAIveMind or Linear]

EOF

# Create planning sub-page UNDER the hub page
~/dev/skills/notion-oauth/create-page.sh \
  "[Project Name] — Planning Board" \
  "[HUB_PAGE_ID]" \
  /tmp/project-planning-content.md
```

Capture **PLANNING_PAGE_ID** and **PLANNING_PAGE_URL**.

After creating: update the Hub Page's Quick Links section to include the planning URL:
```bash
~/dev/skills/notion-oauth/update-page.sh insert "[HUB_PAGE_ID]" "Planning Board:" /tmp/planning-link-update.md
```

---

### Step 6: Create Kanban Database

Use the dedicated script to create the Kanban DB with correct columns. **Do NOT use the old DDL + UPDATE pattern — it's broken. Create correctly the first time.**

```bash
python3 ~/dev/skills/project-init/scripts/create-kanban.py \
  --parent-page-id "[HUB_PAGE_ID]" \
  --project-name "[Project Name]"
```

The script outputs:
```
DATABASE_ID=<uuid>
DATABASE_URL=<url>
```

Capture **KANBAN_DB_ID** and **KANBAN_DB_URL** from the output.

**Canonical columns (in order):**
`Backlog` → `Todo` → `In Progress` → `Blocked` → `In Review` → `Done` → `Canceled`

After creating: update the Hub Page's Quick Links section with the Kanban URL.

---

### Step 7: Pin Hub URL in Discord Channel

```bash
# Send a message with the hub URL
message action=send channel=discord channelId=[CHANNEL_ID] \
  message="📌 **[Project Name]** — Notion Hub\n\n🏠 Hub: [HUB_PAGE_URL]\n📋 Planning: [PLANNING_PAGE_URL]\n🗂️ Kanban: [KANBAN_DB_URL]"

# Pin that message
message action=pin channel=discord channelId=[CHANNEL_ID] messageId=[MESSAGE_ID]
```

---

### Step 7.5: Create a Project Planning Thread

Before creating per-ticket threads, create a persistent **Planning Thread** in the current channel. This serves as the project's always-open coordination space for status updates, handoffs, blockers, and orchestration.

```
message action=thread-create
  channel=discord
  channelId=[CURRENT_CHANNEL_ID]
  threadName="[Project Name] — Planning"
  message="📌 **[Project Name] — Planning Thread**

This is the coordination thread for the [Project Name] project.

**Hub:** [HUB_PAGE_URL]
**Planning:** [PLANNING_PAGE_URL]
**Kanban:** [KANBAN_DB_URL]

Use this thread for:
- Status updates and blockers
- Ticket handoffs
- `/project status` — full project status
- `next ticket` / `launch T-XXX` — kick off the next ticket agent
- `where are we` — orchestrator summary"
```

Pin the planning thread message. Capture **PLANNING_THREAD_ID**.

Add to channel directive under `## Active Work`:
```
Planning thread: <#PLANNING_THREAD_ID>
```

---

### Step 8: Create Discord Threads

For each ticket in the plan, create a thread in the current channel:

```
message action=thread-create
  channel=discord
  channelId=[CURRENT_CHANNEL_ID]
  threadName="[T-XXX] [ticket title]"
  message=[thread directive — load references/thread-template.md for format]
```

**Thread message must include** (per `references/thread-chain.md`):
- Context restore command pre-filled with project ID + channel ID
- Dependencies from the project plan
- "Prior Work Summary" section (empty at creation)
- `ticket-handoff.sh` invocation line
- See `references/thread-chain.md` § "Pinned Message Template"

**Pin the first message** in each thread.

Capture all **thread IDs** from responses.

---

### Step 9: Write Channel Directive

Write `~/dev/contexts/[channel-id].md`:

```markdown
# [Project Name]

**Notion Hub:** [HUB_PAGE_URL]
**Planning Board:** [PLANNING_PAGE_URL]
**Notion Kanban DB:** [KANBAN_DB_URL]
**Notion Kanban DB ID:** [KANBAN_DB_ID]
**Hub Page ID:** [HUB_PAGE_ID]
**VibeKanban Project ID:** [VK_PROJECT_ID]
**Created:** [TODAY]
**Status:** Active

## Goal
[Project description and definition of done]

## Tickets

| ID | Title | Thread | Model | VK Status |
|----|-------|--------|-------|-----------|
| T-001 | [title] | <#thread-id> | sonnet-medium | Backlog |
| T-002 | [title] | <#thread-id> | sonnet-high | Backlog |

## Active Work
- Next ticket: T-001
- VK project: https://generic.<TAILNET_DOMAIN>:8443 (project [VK_PROJECT_ID])

## Model Assignments
- Planning: max-high/claude-opus-4-6
- See per-ticket assignments above

## Notes
[Any context from hAIveMind or prior work]
```

---

### Step 10: Store to hAIveMind

```bash
mcporter call haivemind.store_memory \
  content="PROJECT-INIT [channel-id] [project-name] [TODAY]: vk-project=[VK_PROJECT_ID] hub=[HUB_PAGE_URL] planning=[PLANNING_PAGE_URL] kanban-db=[KANBAN_DB_ID] threads=[T-001:<thread-id>,T-002:<thread-id>,...] tickets=[count] model=opus-high" \
  category="operations"
```

---

### Step 11: Post Summary to Channel

Reply in the channel:

```markdown
**[Project Name] initialized**

**VibeKanban:** https://generic.<TAILNET_DOMAIN>:8443 (project [VK_PROJECT_ID]) — tickets live here
**Notion Hub:** [HUB_PAGE_URL]
**Planning Board:** [PLANNING_PAGE_URL]
**Notion Kanban:** [KANBAN_DB_URL]

**Planning thread:** <#PLANNING_THREAD_ID> — coordination, status, handoffs

**Ticket threads ([count]):**
- <#thread-id> — T-001: [title] (sonnet-medium)
- <#thread-id> — T-002: [title] (sonnet-high)
...

**Next:** Start with T-001 — spawn with `/thread [name] --model [model]` or say `kick it off` in the planning thread
Create tickets for each task in VK: `/vk [project] create [title]` or use the vk-project skill
```

---

### Step 12: Time Block Handling

Based on qualifier parsed in Step 1:

**Skip (weekend / personal / side / hobby):** Nothing to do. Move on.

**Ask (no qualifier):**
```
Would you like me to check your calendar and suggest focus blocks for this project?
```
Wait for response. If yes → proceed as "work" mode. If no → done.

**Yes (work / priority / <ORG_NAME> / company / sprint):**

```bash
python3 ~/dev/skills/project-init/scripts/suggest-time-blocks.py \
  --ticket-count [TOTAL_TICKET_COUNT] \
  --complexity [estimated_complexity from plan: low|medium|high] \
  --weeks 2
```

The script outputs a markdown list of suggested 2h+ focus blocks during weekday work hours (9am-6pm EST).

Present the suggestions:
```markdown
**Suggested focus blocks for [Project Name]:**

Estimated work: ~[N] hours ([ticket-count] tickets × [complexity])

[markdown output from script]

Would you like me to create these as calendar events?
```

If <USER_NAME>says yes → use Google Calendar via mcporter to create the events:
```bash
mcporter call google-workspace.create_calendar_event \
  user_google_email="<EMAIL_ADDRESS>" \
  title="[Project Name] — Focus Block" \
  start_time="[ISO_START]" \
  end_time="[ISO_END]" \
  description="Focus block for [Project Name] — [HUB_PAGE_URL]"
```

---

## Model Selection Rubric

See `references/model-selection.md` for the full rubric. Summary:

| Complexity | Model | Use When |
|-----------|-------|----------|
| Simple | `sonnet-low` | Docs, config, simple scripts |
| Standard | `sonnet-medium` | Most coding, API changes |
| Complex | `sonnet-high` | Multi-file refactors, migrations |
| Deep | `opus-high` | Architecture, security, planning |
| Max | `opus-high` + thinking | Cross-system migrations, critical path |

**Planning phase (Step 3):** Always `max-high/claude-opus-4-6`.

---

## Edge Cases

- **Channel already has a directive:** Warn <USER_NAME>Ask before overwriting. Offer to merge.
- **Re-init:** Archive old directive, create fresh. Preserve thread IDs in hAIveMind.
- **Linear tickets referenced:** Read them for context (read-only OK). Never create tickets there.
- **Very large projects (>15 tickets):** Group into phases. Recommend splitting across channels.
- **No clear tasks:** Use opus reasoning to decompose. Ask only if truly ambiguous.
- **No git repo:** Omit repo line from Hub Page. Continue normally.
- **create-kanban.py fails:** Fall back to manual mcporter call with the DDL from the script. Do NOT use UPDATE steps.

---

## Ongoing Ticket Management (Post-Init)

After init, ticket CRUD is handled by `~/dev/skills/vk-project/SKILL.md` (VibeKanban):
- `create a ticket for X` → creates in VK under the project
- `mark X as done` / `close X` → moves to Done in VK
- `what's blocked` → lists Blocked tickets in VK
- `move X to In Progress` → status update in VK
- `show the board` → full VK board snapshot

The channel directive (`contexts/[channel-id].md`) stores the VK project ID — the vk-project skill reads it automatically on session start.

Notion Kanban (created in Step 6) is for **document-style tracking only** — planning views, milestone tracking. All live ticket ops go through VibeKanban.

---

## Thread Chaining Protocol

See `references/thread-chain.md` for full specification. Summary:

1. **On startup:** Ticket agent reads channel directive + queries hAIveMind for `TICKET-DONE [project-id]` + checks auto-chain priming messages
2. **On completion:** Ticket agent writes `TICKET-DONE` to hAIveMind + updates channel directive + posts priming to next thread
3. **Handoff script:** `scripts/ticket-handoff.sh TICKET_ID PROJECT_ID CHANNEL_ID RESULT COMMITS "SUMMARY" "FILES_CREATED" "FILES_MODIFIED" "KEY_DECISIONS" "NEXT_NEEDS" "BLOCKERS"`

---

## Files in This Skill

- `SKILL.md` — this file
- `scripts/generate-plan.py` — directive → structured JSON plan
- `scripts/create-kanban.py` — create Kanban DB with correct canonical columns
- `scripts/suggest-time-blocks.py` — fetch calendar + suggest focus blocks
- `scripts/ticket-handoff.sh` — ticket completion automation
- `references/model-selection.md` — model selection rubric
- `references/thread-template.md` — thread message template
- `references/thread-chain.md` — thread chaining protocol
