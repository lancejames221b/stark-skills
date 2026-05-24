# Thread Message Template

Use this template when creating Discord threads for each ticket in a project-init run.

## Template

```markdown
## {TICKET_ID} — {TICKET_TITLE}

**Model:** `{MODEL}` · **Priority:** {PRIORITY} · **Phase:** {PHASE_NAME}

---

### What
{DESCRIPTION — 2-3 sentences on what this ticket accomplishes and why}

### Steps
1. {Step 1}
2. {Step 2}
3. {Step 3}
...

### Verification
- [ ] {Verification criterion 1}
- [ ] {Verification criterion 2}
...

### Dependencies
{List any tickets this depends on, or "None"}

### Context
- **Project Notion:** {NOTION_URL}
- **Linear:** {LINEAR_TICKET_URL or "N/A"}
- **Related files:** {key files this ticket touches}

---

**Assigned model:** `{MODEL}`
**Spawn:** `/thread {THREAD_NAME} --model {MODEL}`
**When done:** Update thread, mark verification items, post summary.
```

## Field Descriptions

| Field | Source | Example |
|-------|--------|---------|
| `TICKET_ID` | Generated sequentially: T-001, T-002, ... or Linear ID if linked | T-003 |
| `TICKET_TITLE` | From plan output | Set up Firestore client wrapper |
| `MODEL` | From model selection rubric | sonnet-medium |
| `PRIORITY` | urgent / high / normal / low | high |
| `PHASE_NAME` | From plan phases | Phase 1: Foundation |
| `DESCRIPTION` | From plan ticket description | Create the Firestore client... |
| `NOTION_URL` | From Step 4 of workflow | https://notion.so/... |
| `LINEAR_TICKET_URL` | If a Linear ticket was referenced | https://linear.app/<ORG_NAME>/issue/ENG-682 |

## Thread Naming Convention

Thread names follow this pattern:
```
{TICKET_ID} | {short title}
```

Examples:
- `T-001 | Firestore client setup`
- `T-002 | Migrate user store`
- `ENG-682-01 | TinyDB removal — tokens`

If Linear tickets exist, prefix with the Linear ID:
- `ENG-682 | TinyDB to Firestore migration`

## Notes

- Keep thread messages under 2000 characters (Discord limit)
- If a ticket has many steps, summarize — full details go in Notion
- The `Spawn` line tells the agent exactly how to start work on this ticket
- Verification items should be concrete and testable, not vague ("works correctly")
