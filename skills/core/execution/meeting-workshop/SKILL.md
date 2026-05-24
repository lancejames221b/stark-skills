---
name: meeting-workshop
description: Passive live-meeting helper. Polls a Notion meeting-notes page (transcript) every minute via cron, surfaces only deltas, and proposes <USER_NAME>voice answers when a question or decision appears. Optionally watches a Google Doc's comment stream alongside. <USER_NAME>drives the meeting; this skill watches and feeds. Never auto-edits the doc. Use when <USER_NAME>says "/meeting-workshop", "monitor this meeting", "watch this transcript", "live meeting helper", or pastes a Notion meeting-notes URL during a call.
argument-hint: "<notion-url>  |  <notion-url> <doc-id>  |  status  |  stop"
category: execution
runtimes: [claude]
pii_safe: true
---

# Meeting-Workshop

Passive live-meeting helper. Watches a Notion meeting transcript and a Google Doc's comment stream concurrently, fires every minute, and surfaces only what's new. <USER_NAME>runs the meeting. The skill feeds him answers and decisions in real time so he never has to break flow to look things up.

## Roles

- **<USER_NAME>is in the meeting (Discord/Zoom/in-person), driving the conversation and the doc edits.
- **Claude (this skill)** watches via mcporter on <INFERENCE_HOST>. No browser, no auto-edits. Surface deltas, propose <USER_NAME>voice answers, stop.

These roles are fixed.

## When to use

- Live meeting with a customer / coworker over a Google Doc deliverable
- Notion is recording the transcript on a meeting-notes page
- <USER_NAME>wants real-time delta surfacing instead of post-hoc transcript review
- <USER_NAME>may want to land an edit during the meeting, but the skill never executes it without explicit approval

Do NOT use for:
- Async doc review (use `pair-edit` instead)
- Single-shot transcript summary (use `/live <terms>` instead)
- Anything requiring auto-execution of edits (this skill is read-only)

## Inputs

`/meeting-workshop <notion-url>` — start monitoring on this Notion meeting page. Transcript-only mode. Use this as the default trigger when <USER_NAME>pastes a Notion meeting-notes URL during a live call.

`/meeting-workshop <notion-url> <doc-id>` — also monitor open comments on the named Google Doc.

`/meeting-workshop status` — show current cron job id, page, doc id, sweep count, last delta.

`/meeting-workshop stop` — cancel the cron and dump final state.

**Recognizing the trigger:** if <USER_NAME>pastes a `notion.so/...Monthly-Sync...` or any meeting-notes URL and says anything like "you are my live meeting helper", "check every minute", "watch this", or "answer questions as they come" — this is the skill. Start the cron immediately. Do NOT poll with a `sleep`/`while` loop, do NOT background bash with `&`. Use CronCreate. (<USER_NAME>got burned by backgrounded shells on 2026-05-14 — they fight the harness and the wake signal stops landing in chat.)

## Setup (run once when the user invokes with a URL)

### 1. Reset state files

```bash
mkdir -p /tmp/meeting-workshop
> /tmp/meeting-workshop/last-transcript.txt
> /tmp/meeting-workshop/known-comments.txt
echo "<notion-url>" > /tmp/meeting-workshop/page.txt
echo "<doc-id>" > /tmp/meeting-workshop/doc.txt
```

### 2. Capture the baseline (so the first cron sweep doesn't dump the entire prior transcript as "new")

Run the same fetch the cron will run, save the result, and copy to `last-transcript.txt` / `known-comments.txt`. This step is the one that distinguishes a clean start from a noisy one.

### 3. Schedule the cron

Use `CronCreate` with `cron: "* * * * *"`, `recurring: true`, and a prompt that calls back into this skill OR runs the sweep inline. The prompt body is the Sweep block below — embed the URL and doc id as literal strings inside the prompt so each fire has them.

Tell <USER_NAME>the cron job id and that recurring tasks auto-expire after 7 days.

## Sweep block (this is what fires every minute)

```bash
NOTION_URL=$(cat /tmp/meeting-workshop/page.txt)
DOC_ID=$(cat /tmp/meeting-workshop/doc.txt)

ssh <INFERENCE_HOST> "mcporter call notion.notion-fetch \"id=$NOTION_URL\" \"include_transcript=true\"" \
  > /tmp/meeting-workshop/current-fetch.json 2>&1

ssh <INFERENCE_HOST> "mcporter call google-workspace.list_document_comments \"user_google_email=<EMAIL_ADDRESS>\" \"document_id=$DOC_ID\"" \
  > /tmp/meeting-workshop/current-comments.txt 2>&1

python3 << 'PYEOF'
import json, re, sys
with open('/tmp/meeting-workshop/current-fetch.json') as f:
    raw = re.sub(r'^Warning:[^\n]*\n', '', f.read())
try:
    text = json.loads(raw).get('text', '')
    m = re.search(r'<transcript>(.*?)</transcript>', text, re.DOTALL)
    transcript = m.group(1).strip() if m else ''
    with open('/tmp/meeting-workshop/current-transcript.txt', 'w') as f:
        f.write(transcript)
except Exception as e:
    print(f"FETCH-FAIL: {e}")
    sys.exit(1)
PYEOF

[ $? -ne 0 ] && { echo "skipping diff (Notion timeout — state preserved)"; exit 0; }

sed 's/^[\t ]*//' /tmp/meeting-workshop/current-transcript.txt > /tmp/meeting-workshop/current-norm.txt
sed 's/^[\t ]*//' /tmp/meeting-workshop/last-transcript.txt > /tmp/meeting-workshop/last-norm.txt

echo "---NEW TRANSCRIPT---"
comm -13 <(sort /tmp/meeting-workshop/last-norm.txt) <(sort /tmp/meeting-workshop/current-norm.txt)

echo "---NEW COMMENT IDS---"
grep -oE 'AAAB53Gd[A-Za-z0-9_-]+' /tmp/meeting-workshop/current-comments.txt | sort -u > /tmp/meeting-workshop/current-ids.txt
grep -oE 'AAAB53Gd[A-Za-z0-9_-]+' /tmp/meeting-workshop/known-comments.txt | sort -u > /tmp/meeting-workshop/prior-ids.txt
comm -23 /tmp/meeting-workshop/current-ids.txt /tmp/meeting-workshop/prior-ids.txt

cp /tmp/meeting-workshop/current-transcript.txt /tmp/meeting-workshop/last-transcript.txt
cp /tmp/meeting-workshop/current-comments.txt /tmp/meeting-workshop/known-comments.txt
```

## After the sweep — Claude's response loop

When the cron fires and dumps a sweep result back to Claude, Claude inspects `---NEW TRANSCRIPT---` and `---NEW COMMENT IDS---`:

### If both empty
Output one line: `no change`. Stop. Do not summarize the standing transcript.

### If new transcript content appears
Classify each chunk:
- **Small talk / off-topic** (family, pets, weather, politics, business gossip): one-line acknowledgment such as `Still small talk (vet stories). No report content.` Do not transcribe or summarize the small talk.
- **Report-related question** ("is the hash stored on the subscriber's machine or in Marathon"): quote the question verbatim, then propose a <USER_NAME>voice forensic answer using prior conversation context (<PROJECT_NAME> <PROJECT_NAME> report tabs, doc id from `/tmp/meeting-workshop/doc.txt`, `feedback_lance_voice_formal.md`).
- **Decision** ("let's say execution chain"): quote the decision verbatim, then state the action it implies (e.g., scrub doc for `kill chain` → `execution chain`). Do not auto-execute. Wait for <USER_NAME>to say "do it".
- **Status update** ("I condensed the executive summary to a one-pager"): one-line summary of what <TEAM_MEMBER> or the other party reported doing.

### If new comment ids appear
Pull the comment content from `/tmp/meeting-workshop/current-comments.txt` for each new id. Quote the new content. If it's a <TEAM_MEMBER> comment that needs a <USER_NAME>voice reply, draft the reply but do not post it (replies are an explicit-approval action — see `feedback_google_docs_suggesting_mode.md`).

### Cadence and tone

- One short paragraph or bullet list per sweep. Never long-form.
- Don't restate the standing context every sweep. <USER_NAME>has it loaded.
- If small talk runs for many sweeps, output `no change` or one-line "still small talk" acknowledgment. Don't pad.
- Notion timeouts are common (the MCP times out at 60 s sometimes). If `FETCH-FAIL`, the script preserves prior state. Output one line: `Notion timeout. State preserved.` Move on.

## Voice register

Proposed answers for <USER_NAME>must follow `feedback_lance_voice_formal.md`:
- No em-dashes
- No analyst-tone leads ("Great question, …")
- No "you're right" / "good catch" / "good call" preamble
- Period-stop bullets
- Forensic register
- State the answer, not the meta

## Hard rules

1. **Never auto-edit the doc.** This skill is read-only by contract. Edits are landed via `pair-edit` after the meeting, with explicit <USER_NAME>approval per `feedback_google_docs_suggesting_mode.md`.
2. **Never resolve a comment automatically.** Comments stay open per <USER_NAME>s standing rule unless he says to resolve.
3. **Don't dump the whole transcript.** Surface only deltas. The whole transcript is in Notion already.
4. **Filter small talk as noise.** One-line acknowledgment, then move on. Don't waste <USER_NAME>s chat scroll on dog stories.
5. **Honor `LIVE-REGISTER` memory** if no doc id is passed. Fall back gracefully if no memory exists; ask <USER_NAME>which doc to monitor.
6. **Verify before claiming a delta.** If the sweep returns `no change`, output `no change` and stop. Do not invent activity.
7. **Notion is flaky.** ~30% of fetches time out. The script must preserve prior state on timeout. Don't nuke `last-transcript.txt` on a failed fetch.
8. **Stay one-shot per sweep.** Do not chain multiple actions on a single fire. The cron will fire again next minute.

## `status` subcommand

```bash
echo "page: $(cat /tmp/meeting-workshop/page.txt 2>/dev/null || echo 'NONE')"
echo "doc:  $(cat /tmp/meeting-workshop/doc.txt 2>/dev/null || echo 'NONE')"
echo "transcript: $(wc -c < /tmp/meeting-workshop/last-transcript.txt 2>/dev/null) chars"
echo "known comments: $(grep -oE 'AAAB53Gd[A-Za-z0-9_-]+' /tmp/meeting-workshop/known-comments.txt 2>/dev/null | sort -u | wc -l)"
```

Then call `CronList` to show the active cron job and its id.

## `stop` subcommand

Call `CronList`. Find the cron job whose prompt mentions the meeting-workshop sweep block (or whose id matches the last `/meeting-workshop` run). Call `CronDelete` with that id. Output: `Stopped meeting-workshop. Final transcript at /tmp/meeting-workshop/last-transcript.txt.`

## Anti-patterns

- "Let me transcribe the small talk so <USER_NAME>can scan it" — no, filter as noise.
- "Resolved the comment for <USER_NAME>no, comments stay open.
- "Already drafted the reply, posted it, here's the result" — no, draft only, never post.
- "Edited the doc to fix the kill-chain wording in real time" — no, editing is `pair-edit`'s job and requires explicit approval.
- "Re-summarized the entire meeting context every sweep" — no, surface deltas, <USER_NAME>has the rest.
- "Sleep-polled instead of using the cron" — no, the cron is the wake signal.

## Cross-reference

- `pair-edit` skill — the explicit-approval edit ritual to run AFTER the meeting on items the workshop surfaced
- `feedback_lance_voice_formal.md` — voice rules for proposed answers
- `feedback_google_docs_suggesting_mode.md` — why automated edits to deliverable docs need explicit approval
- `/live` skill — single-shot Notion fetch (use that for one-off queries; meeting-workshop is the recurring variant)
- Working examples:
  - 2026-05-07 14:22 EDT (<PROJECT_NAME> <PROJECT_NAME> report, Nyssa) and 17:10 EDT follow-up — ~70 sweeps, validated the deltas-only + <USER_NAME>voice-answer pattern.
  - 2026-05-14 12:22 EDT (<PROJECT_NAME> monthly sync, <EXTERNAL_PARTY> + Nyssa + <EXTERNAL_PARTY>) — ~57 sweeps, surfaced live: Havok+Wwise+Marathon prototypes in cheat module, lead-tester focus pivot, 1-3 person dev team confirmation, "send AOB framework to Chris" action item. Validated the trigger flow of <USER_NAME>pasting a notion.so meeting URL and saying "you are my live meeting helper."

## Today's lessons (2026-05-14)

- The MCP tool returns `{"text": "<meeting-notes>..."}`. Extract via `json.loads(raw).get('text','')`, NOT `.get('result','')`. The `result` key is empty.
- `include_transcript=true` is mandatory. Without it, the response says "Transcript omitted. Use the view tool…" and the regex extraction returns empty.
- Notion timeouts at ~30% rate are expected. The sweep preserves prior state on failure — never wipe `last-transcript.txt` on a failed fetch.
- Backgrounded shell loops fight the harness. The wake signal stops arriving in chat and the user feels abandoned. Use CronCreate, always.
- The cron prompt is a string; embed the URL literally inside it so each fire is self-contained. Do not rely on session env vars surviving between fires.
