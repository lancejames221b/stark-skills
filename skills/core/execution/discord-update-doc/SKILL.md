---
name: append-daily-doc-tab
description: Standalone Google Doc update step — appends a daily entry (as a new dated tab with real GDocs tables) from data stored in a memory provider. Companion to /daily-cohort-checkin; usable independently whenever you need to retry just the doc-write step without re-running the data gathering. Trigger phrases — "/append-daily-doc-tab", "update daily doc", "retry doc tab", "write today's tab".
category: execution
runtimes: [claude]
pii_safe: true
---

# append-daily-doc-tab

Handles ONLY the Google Doc tab creation/update step from a daily check-in flow. This skill exists because doc-tab insertion is the most fragile part of any check-in pipeline — tables can render as markdown, cell-index insertion can go out of bounds, and you need a way to retry the doc step without re-running expensive data gathering.

It can be invoked:
- Directly by the user: `/append-daily-doc-tab` (uses today's date)
- For a specific date: `/append-daily-doc-tab 2026-05-12`
- By another skill's subagent that completed data gathering but failed on the doc step

## Required setup

- `OUTPUT_DOC_ID` — Google Doc ID that gets a new dated tab per run
- `OUTPUT_DOC_USER` — Google account for Google Docs MCP calls
- `MEMORY_PROVIDER` — memory backend with `search_memories` and `update_memory` MCP tools (e.g., `haivemind`)
- `MEMORY_QUERY_PREFIX` — search prefix used to find the day's check-in memory (e.g., `daily-cohort-checkin-` — the skill appends the target date)
- `TEST_START_DATE` — `YYYY-MM-DD` for Day-N math (set to `1970-01-01` if you don't track Day-N)
- `COHORT_SIZE` — expected row count for the cohort status table (used in verification)

## Optional providers

- **Obsidian fallback** — set `OBSIDIAN_VAULT_PATH` and `OBSIDIAN_CHECKIN_GLOB` (e.g., `cohort-checkins/<COHORT_NAME>-<DATE>.md`) for the skill to read from Obsidian when the memory provider has no hit.
- **Open on screen** — set `SCREEN_HOST_ALIAS` to auto-open the new tab after creation.
- **Issue tracker link** — set `ISSUE_TRACKER_URL` to include in the tab header.

## HARD RULE: real tables only

Every status table MUST be inserted as a real Google Docs table widget via `insert_table`. NEVER use markdown `| col | col |` pipe rows. If verification shows flat bullet or pipe text, the insert failed — delete the bad section and redo.

## Invocation

```
/append-daily-doc-tab                    # uses today's date
/append-daily-doc-tab 2026-05-12         # uses specified date
/append-daily-doc-tab --date 2026-05-12  # same, explicit flag
```

Main Claude should:
1. Acknowledge briefly ("Loading check-in data and updating the doc...").
2. Parse the date argument (default: today from `date +%Y-%m-%d`).
3. Dispatch a synchronous (not background) Sonnet subagent with the prompt below.
4. Report back with the result.

## Subagent prompt (paste verbatim, with env vars substituted)

```
You are running the Google Doc append step for COHORT_NAME daily check-in.

TARGET DATE: $TARGET_DATE
GOOGLE DOC ID: <OUTPUT_DOC_ID>
GOOGLE USER: <OUTPUT_DOC_USER>

== STEP 1: Determine target date and Day N ==

If TARGET_DATE not supplied: run `date +%Y-%m-%d`.
Day N = floor((target_date - TEST_START_DATE).days) + 1.
Tab title: `Daily Check-in TARGET_DATE (Day N)`

== STEP 2: Load check-in data from memory ==

mcp__<MEMORY_PROVIDER>__search_memories(
  query="<MEMORY_QUERY_PREFIX>TARGET_DATE",
  semantic=true,
  limit=5
)

Find a memory whose content contains TARGET_DATE and "Cohort status". Extract:
- cohort_rows: list of dicts (member, status, events, last_seen, errors, notes)
- cliff_events: list of dicts (cliff_ts, magnitude, classification, root_cause, affected_member, attribution)
- success_criteria: list of dicts (criterion, result)
- headlines: list of strings
- anomalies: list of strings
- test_reading: string
- snapshot_ts: string

If no memory hit and OBSIDIAN_VAULT_PATH is set:
  mcp__obsidian__read_text_file(path="<OBSIDIAN_VAULT_PATH>/<OBSIDIAN_CHECKIN_GLOB with TARGET_DATE>")

If NEITHER source has data:
  Output "ERROR: No check-in data found for TARGET_DATE. Run /daily-cohort-checkin first."
  STOP.

== STEP 3: Inspect current doc tabs ==

mcp__google-workspace__inspect_doc_structure(
  document_id="<OUTPUT_DOC_ID>",
  user_google_email="<OUTPUT_DOC_USER>"
)

Extract tabs list + max_tab_index. Check if any tab title matches today's pattern.

== STEP 4: Tab existence decision ==

Case A — tab doesn't exist:
  mcp__google-workspace__manage_doc_tab(
    action="create",
    tab_title="Daily Check-in TARGET_DATE (Day N)",
    tab_index=max_tab_index + 1
  )
  Capture tab_id. Proceed to step 5.

Case B — tab exists:
  Record existing tab_id.
  Re-inspect with detailed=true. For each section that's missing, add it (skip sections already present).
  Proceed to step 5.

== STEP 5: Write tab header (metadata block) — if new tab ==

batch_update_doc with insert_text containing:
  "Daily Check-in TARGET_DATE (Day N)\n\nSnapshot: <ts>\nWindow: last 24h\nSource doc: https://docs.google.com/document/d/<OUTPUT_DOC_ID>/edit\nTracker: <ISSUE_TRACKER_URL>\n\n"

Apply HEADING_1 style to the title line.

== STEP 6: Insert Cohort Status table (REAL TABLE) ==

6a. insert_text section heading: "2. Status\n\n"
6b. insert_table { rows: COHORT_SIZE + 1, columns: 5, end_of_segment: true }
6c. IMMEDIATELY inspect_doc_structure detailed=true (within 2s — no other writes between 6b and 6c). Extract cell_start_indices as a (COHORT_SIZE+1) x 5 matrix.
6d. RETRY CHECK: if inspect shows NO table of the right shape, retry 6b once and repeat 6c. Max 2 retries; if still failing, skip section with note.
6e. Fill cells:
    Header row: "Member" | "Status" | "Events (24h)" | "Last Seen" | "Notes"
    Data rows: from cohort_rows
    Fill in REVERSE document order (highest index first) to prevent index drift.
    Each cell: insert_text { text: "<content>", index: cell[row][col] + 1 }
6f. RETRY on index error: re-inspect for fresh indices, retry that cell once. Then "FILL_FAILED" if still bad.

== STEP 7: Insert Cliff Summary table (if cliffs detected) ==

7a. insert_text heading: "3. Traffic Analysis — Cliffs\n\n"
7b. insert_table { rows: len(cliff_events)+1, columns: 6, end_of_segment: true }
7c. IMMEDIATELY inspect.
7d. Fill header: "Cliff Time" | "Magnitude" | "Classification" | "Root Cause" | "Affected Member" | "Attribution"
7e. Fill data rows (reverse order).

Same retry logic as 6.

If cliff_events empty:
  insert_text "3. Traffic Analysis\n\nNo cliffs detected in the 48h window.\n\n"

== STEP 8: Insert Success Criteria table (if success_criteria non-empty) ==

8a. insert_text heading: "4. Success Criteria\n\n"
8b. insert_table { rows: len(success_criteria)+1, columns: 2, end_of_segment: true }
8c. Inspect.
8d. Fill header: "Criterion" | "Status"
8e. Fill rows.

== STEP 9: Append bullet sections (plain text — NOT tables) ==

Headlines:    "5. Headlines\n\n" + "\n".join(["- "+h for h in headlines]) + "\n\n"
Anomalies:    "6. Anomalies / Open Items\n\n" + "\n".join(["- "+a for a in anomalies]) + "\n\n"
Test Reading: "7. Test Reading\n\nDay N. " + test_reading + "\n\n"
Method:       "8. Method\n\nData sources: <describe your sources>\n\n"
Next:         "9. Next Check-in\n\nRun /daily-cohort-checkin on NEXT_DATE.\n\n"

== STEP 10: VERIFICATION (mandatory) ==

mcp__google-workspace__get_doc_as_markdown(document_id=..., tab_id=<tab_id>)

Check ALL — fix and re-run any that fail:

[VERIFY-1] Tab title exactly `Daily Check-in TARGET_DATE (Day N)` — no `(copy)` duplicate
[VERIFY-2] Cohort status table renders as real table — markdown export shows `| Member | Status | ...` row pattern AND has COHORT_SIZE+1 rows
[VERIFY-3] Cliff table renders as table (if cliff_events non-empty) — NOT a bullet list
[VERIFY-4] Success-criteria table renders as table (if applicable)
[VERIFY-5] Cohort row count = COHORT_SIZE — no missing, no duplicates
[VERIFY-6] No cell says "FILL_FAILED" — if any, re-run that cell with fresh inspect
[VERIFY-7] Member rows reflect current data, not stale
[VERIFY-8] No raw pipe rows OUTSIDE a real table context

Max 2 fix attempts per failed check.

Tab URL: https://docs.google.com/document/d/<OUTPUT_DOC_ID>/edit?tab=<tab_id>

== STEP 11: Update memory with doc_tab_url ==

If memory was found in step 2:
  mcp__<MEMORY_PROVIDER>__update_memory(
    memory_id=<id>,
    content=<original + "\n\n**Google Doc tab**: " + tab_url>
  )

If update fails or memory wasn't found:
  mcp__<MEMORY_PROVIDER>__store_memory(
    category="<MEMORY_CATEGORY>",
    content="<COHORT_NAME>-TARGET_DATE — Google Doc tab created: " + tab_url
  )

== STEP 12: Open on screen ==

If SCREEN_HOST_ALIAS set and --no-screen not passed:
  ssh <SCREEN_HOST_ALIAS> 'open "<tab_url>"'

== STEP 13: Final report ==

append-daily-doc-tab — Day N (TARGET_DATE)
   • Tab: <tab_url>
   • Tables: cohort | cliffs <yes/N/A> | criteria <yes/N/A>
   • Verification: <N>/8 checks passed
   • Memory: updated <memory_id>
   • Open items: <count>

If any step hard-failed, prefix the affected line with [FAIL] and add a Failures: section.
```

## Table insertion pattern (canonical)

This is the correct sequence for every GDocs real-table insertion. Never deviate.

```
Step A: insert_text for section heading (e.g., "2. Status\n\n")
Step B: insert_table { rows: N, columns: M, end_of_segment: true }
Step C: inspect_doc_structure { detailed: true, tab_id } → extract cell start_indices
Step D: for each cell in REVERSE document order:
           insert_text { text: "<content>", index: cell_start + 1 }
Step E: re-read tab as markdown → confirm table rendered correctly
If Step E fails: delete the bad section, repeat A–D (max 2 attempts)
```

Key constraints:
- `end_of_segment: true` on `insert_table` — required so it lands at the tab end, not document index 1
- Inspect IMMEDIATELY after `insert_table` (no other writes in between)
- REVERSE-order fill (highest index first) prevents index drift from earlier inserts
- `index = cell_start + 1` not `cell_start` — inserting at cell_start replaces the cell marker

## Failure modes

| Failure | Recovery |
|---|---|
| Memory miss + Obsidian miss | STOP — no data to write |
| Tab creation fails | Retry once; if still fails, report error |
| insert_table produces no table | Retry once (max 2); skip with note |
| Cell index out of bounds | Re-inspect fresh, retry cell once |
| `get_doc_as_markdown` 404 | Re-fetch doc structure for fresh tab_id, retry |
| Screen open fails | Log skip, don't abort |
| Memory update fails | Store new brief memory instead |

## Integration with /daily-cohort-checkin

After data-gathering phases of the check-in (cohort resolve, metric scan, log scan, status determination), instead of running the fragile doc step inline, the check-in subagent can hand off here:

1. Ensure the check-in report is saved to the memory provider BEFORE calling this skill.
2. Invoke `/append-daily-doc-tab` (or dispatch this skill's subagent with TARGET_DATE set).
3. The doc update runs independently and can be retried in seconds without re-running expensive data gathering.

This split matters because data gathering is slow (remote SSH, metric round-trips) but doc writes can fail fast and retry fast.

## Related

- `/daily-cohort-checkin` — full daily check-in (data + doc + memory)
- `/load <cohort_name>` — surface prior check-in memories
