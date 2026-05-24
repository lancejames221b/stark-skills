---
name: pdo
description: Private DO — delegate a bounded coding/text task to local PI + Ollama. Code stays on the LAN. Spawns a verbose Discord thread by default so progress is visible while you work elsewhere. Trigger phrases — "/pdo", "private do", "private agent", "delegate to pi", "run on local", "let pi do this".
category: execution
runtimes: [claude]
pii_safe: true
---

# /pdo — Private DO (PI worker, verbose to Discord)

Hand a tightly-scoped task to `pi` running against local Ollama on Mac (`<PRIVATE_IP>:11434`). Nothing leaves the LAN. By default a Discord thread is spawned where every line of pi's output streams live, so you can monitor on your phone while the main Claude session keeps moving.

## When to use
- Task is well-bounded (specific files, clear success criteria)
- Code or content is sensitive — keep it off cloud APIs
- I want parallelism — pi works while I work

## When NOT to use
- Open-ended debugging or architecture decisions — local models lose the thread
- Cross-repo changes that need full context
- Anything time-critical where a wedge is unacceptable

## Models

| Tag | Model | Best for |
|---|---|---|
| **default** | `qwen3.6:35b-a3b-coding-mxfp8` | Best <USER_NAME>tested coder. **Loop-prone tag** — the hard timeout + STUCK: guardrails + Discord-thread monitoring mitigate it |
| `--coder` | `qwen3-coder:30b` | Stable fallback if 35b loops |
| `--reason` | `nemotron3:33b` | Multi-step reasoning + tool use |
| `--fast` | `gemma4:latest` | Trivial jobs, quick turnaround |
| `--big` | `qwen3.6:35b-a3b-q8_0` | Highest local precision among installed models |

## Flags

```
/pdo <spec>                       qwen3.6 35b coding, 600s timeout, Discord thread on
/pdo --coder <spec>               qwen3-coder:30b (stable fallback)
/pdo --reason <spec>              nemotron, 900s timeout
/pdo --fast <spec>                gemma4, 180s timeout
/pdo --big <spec>                 qwen3 235b, 1800s timeout
/pdo --plan <path-to-plan.md>     execute a /pplan output — auto-pick model from "Recommended executor" section
/pdo --model <id> <spec>          override model
/pdo --timeout <sec> <spec>       override timeout
/pdo --bg <spec>                  fire-and-forget; return Discord thread URL immediately
/pdo --no-discord <spec>          skip Discord thread, stdout only
/pdo --channel <id> <spec>        post to a specific Discord channel
/pdo --dry <spec>                 print the pi command, do NOT execute
```

### `--plan` mode

When given a plan file (output of `/pplan`):

1. Parse the plan's frontmatter for context (topic, generated_at, original brief)
2. Read the **Recommended executor** section — extract `Model`, `Suggested timeout`
3. Read **Phase 1** as the spec for this `/pdo` run (one phase per invocation — don't try to execute the whole plan)
4. Read **Files to touch** + **Files NOT to touch** as scope guardrails
5. Read **Verification** for that phase as the success criteria
6. Invoke pi with the auto-selected model, timeout, and scoped guardrails
7. After execution, post in the Discord thread: "Phase 1 complete. Next: Phase 2 — `<phase 2 name>`. Run `/pdo --plan <path> --phase 2` to continue."

User overrides (`--model`, `--timeout`) take precedence over the plan's recommendation.

## Flow

### 1. Build the spec (you, before invoking pi)
Translate the user's request into:
- **Goal** — one sentence
- **Files in scope** — explicit absolute paths, read-list and write-list separately
- **Out-of-scope** — what NOT to touch
- **Success criteria** — how the output is judged
- **Output format** — diff / full file / JSON / etc.

Don't pass the user's raw words. Always translate.

### 2. Build guardrails (`--append-system-prompt`)
```
You are a focused worker invoked by Claude Code. Constraints:
- Stay strictly within the listed file scope. Do NOT read or edit anything else.
- If the task is ambiguous, output a single line beginning with QUESTION: and stop.
- Do not run destructive commands (rm -rf, force pushes, db drops).
- Output the requested format only — no preamble, no commentary.
- If you find yourself repeating the same operation more than 5 times, stop and emit STUCK: <reason>.
```

### 3. Spawn the Discord thread (default, unless `--no-discord`)
Default channel: `#pdo-runs` on the <ORG_NAME> Discord (look it up in `<VOICE_RUNTIME>-admin` skill if not memorized). Per-run thread named: `pdo-<short-spec-summary>-<HHMM>`.

**Bot/webhook used:** the same Jarvis bot wired up in `~/.config/jarvis-handoff/` (cross-reference `<VOICE_RUNTIME>-admin` skill for the token).

Initial thread message (parent channel, then create thread on it):
```
🤖 **/pdo run started** — `<short spec summary>`
Model: <model>  ·  Timeout: <N>s  ·  Caller: <hostname>:<session-id-short>
Spec → (collapsed in thread)
```

Then in the thread:
```
spec:
<full spec>

guardrails:
<full guardrails>

starting…
```

Helper script: `~/.local/bin/pdo-runner` (create on first use). Pseudo-shell:
```bash
#!/usr/bin/env bash
# pdo-runner <model> <timeout> <channel-id> <spec-file> <guardrails-file>
PARENT_MSG=$(discord post "$CHANNEL" "🤖 /pdo run started — $SHORT_SPEC ...")
THREAD=$(discord thread create "$PARENT_MSG" "pdo-$SHORT_SPEC-$(date +%H%M)")
discord post "$THREAD" "$(cat <<EOF
spec:
$(cat $SPEC_FILE)

guardrails:
$(cat $GUARDRAILS_FILE)

starting…
EOF
)"

timeout "$TIMEOUT" pi --print --no-session \
  --provider ollama --model "$MODEL" \
  --append-system-prompt "$(cat $GUARDRAILS_FILE)" \
  "$(cat $SPEC_FILE)" 2>&1 | \
while IFS= read -r line; do
  echo "$line"                          # local stdout (for this Claude session)
  discord post "$THREAD" "\`\`\`$line\`\`\`"  # mirror to thread, batch every ~5 lines or 2s
done
EXIT=${PIPESTATUS[0]}

if [ "$EXIT" -eq 0 ]; then
  discord post "$THREAD" "✅ pdo finished cleanly (exit 0)"
elif [ "$EXIT" -eq 124 ]; then
  discord post "$THREAD" "⏱️ pdo TIMED OUT after ${TIMEOUT}s — likely loop or wedge"
else
  discord post "$THREAD" "❌ pdo failed (exit $EXIT)"
fi
```

The actual `discord post` helper is whatever wrapper exists in your environment (check `discord` skill, `<VOICE_RUNTIME>-admin`, or use webhook curl). Batch lines into chunks of 5 or 2-second windows to avoid Discord rate limits (50/s per channel, much less per webhook).

### 4. Verify before applying
Read pi's output. Reject if:
- It asked a clarifying question (`QUESTION:` prefix) → relay to user
- It self-reported `STUCK:`
- Output is empty or > 50KB (likely loop/runaway)
- Touched files outside scope (parse the diff and check)
- Same line repeated >5 times consecutively

### 5. Apply (only on user confirm)
- Diffs → `patch -p0`
- Full-file rewrites → `Write` directly
- Never auto-apply. Always show user first.

## Logs

Each invocation writes `/tmp/pdo-<ISO-timestamp>.log`:
```
model:     <model>
timeout:   <N>s
channel:   <discord channel id>
thread:    <discord thread id>
spec:      <full spec>
guardrails:<full guardrails>
duration:  <elapsed>s
exit_code: <n>
output:    <stdout+stderr>
applied:   <true|false>
```

Useful for debugging when the local model misbehaves.

## Output to user

After execution:
```
[pdo: <model>, <duration>s, <output bytes>, thread: <discord url>]

<output>

Apply? (y/n)   ← only if it produced an actionable artifact
```

If failed/timed-out:
```
[pdo FAILED: <reason>, thread: <discord url>]
- Last 30 lines: …
- Suggested next: <retry with different model | escalate to main | refine spec>
```

## Examples

**Good fit — bulk rename**
```
/pdo rename `getUserData` → `fetchUser` in src/api/*.ts and update all callers in src/components/*.tsx
```
→ qwen3-coder, 300s, returns unified diff, posted to Discord thread, ask before applying.

**Good fit — test scaffold**
```
/pdo scaffold jest tests for src/lib/parser.ts — mock fs, cover the 6 exports
```

**BAD fit — refuse**
```
/pdo should we switch from REST to GraphQL?
```
→ Refuse. Tell user: needs cloud-tier reasoning + full repo context; use main Claude.

## Related

- `/pplan` — same private worker, but planning only (no edits)
- `/handoff` — cross-machine session relay
- `<VOICE_RUNTIME>-admin` — Discord bot tokens, channel IDs, paths
