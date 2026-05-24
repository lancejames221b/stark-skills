---
name: daily-cohort-checkin
description: Daily status check-in for a tracked cohort (accounts, services, sensors, anything you watch on a daily cadence). Dispatches a background subagent that pulls per-member status from a configured data source, appends a new dated tab to an output doc, and saves a memory snapshot. Trigger phrases — "/daily-cohort-checkin", "daily checkin", "run cohort status", "checkin <name>".
category: execution
runtimes: [claude]
pii_safe: true
---

# daily-cohort-checkin

Runs a structured daily snapshot of a tracked cohort. Implementation: dispatch a Sonnet subagent (`general-purpose`) in the background, return immediately, and let it post to the output doc + save memory while the main session continues.

This is a template. The original implementation tracked a specific test cohort of accounts against a specific service journal + log index; that real-world example is preserved in the **Real-world example** comment near the end so you can see how the abstract pattern maps to a concrete situation.

## Required setup

- `COHORT_NAME` — short name for the cohort (e.g., `discord-test`, `prod-canaries`, `nightly-jobs`)
- `COHORT_SOURCE` — where the canonical cohort list lives: `memory`, `static_file`, or `inline`
- `OUTPUT_DOC_ID` — Google Doc ID that gets a new dated tab per run
- `OUTPUT_DOC_USER` — Google account for Google Docs MCP calls (`GOOGLE_WORKSPACE_USER`)
- `TEST_START_DATE` — `YYYY-MM-DD` start date used for Day-N math (set to "1970-01-01" if you don't track Day-N)
- `WINDOW_DEFAULT` — default time window for the snapshot (e.g., `24h`, `7d`)

## Optional providers

- **Cohort from memory** — set `COHORT_SOURCE=memory` and `MEMORY_PROVIDER` (e.g., `haivemind`) + `COHORT_MEMORY_QUERY` (the search string that returns the cohort mapping). The skill calls `mcp__<provider>__search_memories` with that query.
- **Cohort from static file** — set `COHORT_SOURCE=static_file` and `COHORT_FILE_PATH` (absolute path to a YAML/JSON with `accounts: [{name, id, fingerprint}]`).
- **Log/journal source** — set `LOG_SOURCE_TYPE` (`ssh_journal`, `loki`, `elasticsearch`, `cloudwatch`, etc.) and the relevant connection vars. The original implementation used SSH+gcloud IAP+journalctl; substitute whatever surfaces per-member event history.
- **Metric source for cliff detection** — set `METRIC_SOURCE_URL` (e.g., Elasticsearch / Prometheus endpoint) and the auth vars (`METRIC_SOURCE_USER`, `METRIC_SOURCE_PASS` and optional `CF_ACCESS_CLIENT_ID`/`CF_ACCESS_CLIENT_SECRET` if it's behind Cloudflare Access). Optional — without it, the skill skips cliff analysis and notes the gap.
- **Issue tracker link** — set `ISSUE_TRACKER_URL` (e.g., Linear/Jira project URL) for the report header.
- **Memory write target** — set `MEMORY_PROVIDER` (e.g., `haivemind`) + `MEMORY_CATEGORY` (default `project`) to persist each daily report.
- **Obsidian mirror** — set `OBSIDIAN_VAULT_PATH` to also write `<vault>/cohort-checkins/<COHORT_NAME>-<DATE>.md`.
- **Open on screen** — set `SCREEN_HOST_ALIAS` to auto-open the new tab on your primary screen.

The skill degrades gracefully when optional providers are missing — it skips that section and flags it in the report rather than failing.

## Why a subagent

The full check-in involves multiple slow operations (remote SSH for journal pulls, aggregation queries, Google Doc tab insertion, memory writes). Doing it inline blocks the main session for 1–3 min. A subagent runs async; main Claude is free to work on other things.

## Trigger

When the user says `/daily-cohort-checkin`, "daily checkin", "run cohort status", "checkin <COHORT_NAME>", or similar — dispatch the subagent below.

## Required behavior of main Claude

1. **Acknowledge briefly** ("Dispatching the cohort check-in agent...").
2. Use the `Agent` tool with:
   - `subagent_type`: `general-purpose`
   - `model`: `sonnet`
   - `run_in_background`: `true`
   - `description`: `<COHORT_NAME> — daily check-in`
   - `prompt`: the full prompt below
3. **Don't wait for the subagent.** Return control. The completion notification surfaces results.
4. If the user passed flags (`--no-doc`, `--no-screen`, `--silent`, `--window 7d`, `--notes "..."`), pass them through.

## Subagent prompt (paste verbatim, substituting env vars and flags)

```
You are running the daily check-in for COHORT_NAME.

GOAL: Pull a structured per-member status snapshot, post it as a new dated tab in OUTPUT_DOC_ID, save a memory snapshot, and (unless --no-screen) open the new tab on the configured screen.

== STEP 1: Resolve cohort ==

If COHORT_SOURCE=memory:
  mcp__<MEMORY_PROVIDER>__search_memories(query="COHORT_MEMORY_QUERY", semantic=true, limit=3)
  Extract per-member: name, id, fingerprint, enrollment date, anything required for the per-member query.

If COHORT_SOURCE=static_file:
  Read COHORT_FILE_PATH and parse.

If COHORT_SOURCE=inline:
  Use the inline cohort table at the bottom of this skill (you must hand-edit it).

== STEP 2: Pull metric snapshot (optional — skip if METRIC_SOURCE_URL unset) ==

Query METRIC_SOURCE_URL for total volume in WINDOW_DEFAULT. Aggregate by whatever dimension your metric source supports (per-guild, per-host, per-job-name, etc.).

If your metric source is behind Cloudflare Access:
  CF_ID="<CF_ACCESS_CLIENT_ID>"
  CF_SECRET="<CF_ACCESS_CLIENT_SECRET>"
  curl -sS -X POST "<METRIC_SOURCE_URL>/_search?track_total_hits=true" \
    -H "CF-Access-Client-Id: $CF_ID" -H "CF-Access-Client-Secret: $CF_SECRET" \
    -u "<METRIC_SOURCE_USER>:<METRIC_SOURCE_PASS>" \
    -H "Content-Type: application/json" -d '<query>'

== STEP 2.5: Cliff detection (optional — skip if no metric source) ==

a. Get hourly volume for last 48h.
b. Detect cliffs: any hour where doc_count drops ≥50% vs prior hour OR rises ≥3× vs prior hour. Record (cliff_ts_utc, before_count, after_count, pct_change).
c. For each cliff classify it: fleet-wide event (all members drop), single-member event (one member accounts for >80% delta), or boundary event (group-level config change).
d. Cross-reference each cliff window in the per-member log source to attribute root cause.

Append findings to a "Traffic analysis" section in the report. For every cliff state: time, magnitude, classification, root cause, responsible member (if any).

== STEP 3: Per-member log/journal scan ==

For each cohort member, scan LOG_SOURCE_TYPE for events in WINDOW_DEFAULT. Count:
- Total events
- Error/disconnect/fail events (your error-pattern grep)
- Last-seen timestamp

The original implementation used:
  ssh <HOST_ALIAS> 'gcloud compute ssh <REMOTE_VM> --tunnel-through-iap --command="journalctl -u <SERVICE> --since \"WINDOW_DEFAULT\" --no-pager -o cat | grep -F <member_id>"'

Use ONE sequential session — no parallel scans (creates zombies and CPU pressure on the source box).

If the log source is unreachable, document the failure and use metric-only data; mark Anomaly.

== STEP 4: Status determination per member ==

- Healthy producer: events > 0 AND no error events
- Healthy quiet: 0 events AND no errors AND last-seen recent (< 6h)
- Suspicious: 0 events AND no recent activity for 6+ hours
- Failed: explicit error/disconnect event in window
- Not yet enrolled: no log traces (standby)

== STEP 5: Day N of N ==

If TEST_START_DATE != "1970-01-01":
  Day N = floor((today - TEST_START_DATE).days) + 1
  If today > TEST_START_DATE + intended duration, flag as "Test window complete — escalate to outcome decision"

== STEP 6: Build report ==

```
# COHORT_NAME Check-in — Day N (YYYY-MM-DD)

**Snapshot**: YYYY-MM-DD HH:MM (TZ)
**Window**: last WINDOW_DEFAULT
**Source doc**: https://docs.google.com/document/d/OUTPUT_DOC_ID/edit
**Tracker**: ISSUE_TRACKER_URL

## Cohort status

| Member | Status | Events | Last seen | Errors | Notes |
|---|---|---|---|---|---|
| ... |

## Headlines
- <one-sentence outcome read>

## Traffic analysis (last 48h)  [skip if no metric source]
- Volume range: <min>-<max> /hr
- Cliffs detected: <N>
  - For each cliff:
    - **<HH:00 TZ, ±N%>**: <classification>
    - Root cause: <one-line>
    - Affected member(s)

## Trend (vs prior day)
- (compare to prior /memory query)

## Anomalies / open items
- ...

## Test reading
- Day N. Trending toward: <interpretation>
- Confidence: <low | medium | high>

## User notes
<from --notes flag if any>
```

== STEP 7: Google Doc tab — USE REAL TABLES, NOT MARKDOWN ==

**HARD RULE: every status table goes in as a real Google Docs table widget via `insert_table`, NOT as markdown `|` rows.** If verification shows flat pipe rows, the insert failed and must be retried.

Use mcp__google-workspace tools (user_google_email='<OUTPUT_DOC_USER>'):

1. `inspect_doc_structure` on `<OUTPUT_DOC_ID>` to get tabs and current structure.
2. If tab `Daily Check-in YYYY-MM-DD` exists: append updates inside it via `batch_update_doc` with `insert_text end_of_segment=true` on that tab_id. Do NOT create a duplicate.
3. Else: `insert_doc_tab` at index = current_max + 1 with title `Daily Check-in YYYY-MM-DD`. Capture new tab_id.

**Table pattern (cohort status):**
- `insert_text` heading: `"# 2. Status\n\n"`
- `insert_table { rows: N+1, columns: 6, end_of_segment: true }` (header + members, columns = Member, Status, Events, Last Seen, Errors, Notes)
- Immediately re-`inspect_doc_structure` with `detailed=true` to get cell start indices
- Fill cells in REVERSE document order (highest index first) to prevent index drift

For cliff table use same pattern with columns: Cliff Time | Magnitude | Classification | Root Cause | Affected Member | Attribution.

Bullet lists are OK for: Headlines, Anomalies. Use plain `insert_text` with `\n- item` lines.

Final tab URL: `https://docs.google.com/document/d/<OUTPUT_DOC_ID>/edit?tab=<tab_id>`

== STEP 8: Save memory ==

If MEMORY_PROVIDER set:
  mcp__<MEMORY_PROVIDER>__store_memory(category="<MEMORY_CATEGORY>", content=<full report markdown>)

If OBSIDIAN_VAULT_PATH set:
  Write to <OBSIDIAN_VAULT_PATH>/cohort-checkins/<COHORT_NAME>-YYYY-MM-DD.md

== STEP 8.5: VERIFICATION (mandatory) ==

1. Re-fetch the new tab via `mcp__google-workspace__get_doc_as_markdown` and confirm:
   - Tab title is exactly `Daily Check-in YYYY-MM-DD (Day N)`
   - All required sections present
   - Status table renders as a real table (markdown export shows `| col | col |` rows AND has correct row count)
   - Cohort row count matches cohort size

2. Cross-check counts: pick one member at random, re-scan the log source, confirm count matches within ±1%.

3. For each cliff: confirm "Affected member" matches the largest-delta group from the metric source.

4. Memory round-trip: search the memory provider for the new entry and confirm it returns the same content.

If ANY check fails, fix and re-run verification. Don't claim complete on partial verification.

== STEP 9: Open on screen (skip if --no-screen) ==
ssh <SCREEN_HOST_ALIAS> 'open "<tab_url>"'

== STEP 10: Final report ==
```
Cohort Check-in — Day N (YYYY-MM-DD)
   • Doc tab: <tab_url>
   • Memory: <COHORT_NAME>-<DATE> (id <id>)
   • Outcome trend: <one-line>
   • Open items: <count>
```

== FLAG OVERRIDES ==
--no-doc       → skip step 7; still save memory
--no-screen    → skip step 9
--silent       → dry-run: print report only, skip 7, 8, 9
--window 7d    → override WINDOW_DEFAULT
--notes "..."  → append to "User notes"

== CONSTRAINTS ==
- READ-ONLY on the source: no config changes, no service restarts
- Single sequential session for log scans; no parallel
- Don't overwrite existing tabs — append-only
- Use today's actual date from `date` command — do not hardcode
```

## Flag passthrough

Main Claude parses any flags from the invocation and APPENDS them to the subagent prompt before dispatch:
- `/daily-cohort-checkin` → no flags appended
- `/daily-cohort-checkin --no-doc` → append `\nFLAGS PASSED BY USER: --no-doc`

## Failure modes

| Failure | Subagent behavior | Main Claude shows |
|---|---|---|
| Cohort source miss | Use inline fallback | Note in report |
| Metric source unreachable | Log-only metrics, mark Anomaly | flag in summary |
| Log source unreachable | Skip per-member counts | flag |
| Google Doc API fail | Save memory only, link to .md | flag + path |
| Screen open fail | Skip, log | (no impact) |

## Recurring usage

```
/loop 1d /daily-cohort-checkin
```

Or `/schedule` for fixed time-of-day.

## Inline cohort (only if COHORT_SOURCE=inline — edit this table)

| Name | ID | Fingerprint | Status |
|---|---|---|---|
| <member-1> | <id> | <fp> | enrolled |
| <member-2> | <id> | <fp> | enrolled |

## Real-world example

The original implementation of this skill tracked an A/B test cohort of social-platform accounts whose collection daemon was running on a remote VM. `COHORT_SOURCE=memory` (the cohort mapping was stored in a semantic memory index), `LOG_SOURCE_TYPE=ssh_journal` (the daemon wrote to systemd journal, accessed via SSH + gcloud IAP tunnel), `METRIC_SOURCE_URL` pointed at an Elasticsearch cluster behind Cloudflare Access, and the cliff-detection step distinguished daemon-level outages from per-account bans from server-side moderation events. That specificity is what made the daily check-in actually useful — adapt similarly for your domain.

## Related

- `/discord-update-doc` (companion skill) — standalone retry of the Google Doc tab step when Step 7 fails
- `/load <cohort_name>` — surface prior check-in memories
