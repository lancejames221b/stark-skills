---
name: do
description: Execute plans step-by-step with verification. Inherits model from /pre or /plan — never resets to a hardcoded model. If no prior model context, defaults to max/claude-sonnet-4-6. Also triggered by "!" as the first character of a message.
category: workflows
runtimes: [claude]
pii_safe: true
triggers:
  - /go
  - /do
  - "! " # ! prefix = execute immediately
---

# /do — Execute Plans

When user invokes `/do [optional task]`, execute the plan using the model already selected by `/pre` or `/plan`.

## Steps

0. **CTO Pause — plan-aware comms check** (runs before execution):
   - **Check if `/plan` already ran a CTO pause for this task:**
     - Look for a recent `CTO-PAUSE PLAN` haivemind entry or a 🛑 card in the current session
     - If found → **skip this step entirely** — the comms check already happened at planning time
   - **If no plan was run** (standalone `/do`): Load `skills/cto-pause/SKILL.md` and run a standard pre-flight card
   - **If a plan exists but comms were skipped**: Post the 🛑 card with plan context:
     - "Plan: [title] — [Notion link]. About to execute [N] steps."
     - Who might need to know
     - Draft comms in <USER_NAME>s voice
   - **If plan was fully reviewed and comms approved at `/plan` time**: confirm in one line — "Plan cleared at planning — executing." then proceed immediately
   - Wait for: `go` | `send + go` | `skip comms + go` | `hold` (only if pausing)
   - Do NOT proceed to step 1 until response received (when pausing is needed)

1. **Model selection for execution** — flexible, step-aware:
   - `/plan` already dropped back to Sonnet after planning. `/do` starts on that Sonnet baseline.
   - For each step, pick the right model based on step complexity:
     - Simple/mechanical steps (file edits, reads, lookups) → current Sonnet (no change needed)
     - Medium complexity (multi-file changes, API calls, logic) → sonnet-medium or sonnet-high
     - Heavy reasoning / security / architecture steps → Opus low or medium (announce: "Stepping up to Opus low for [step name]")
     - Trivial / boilerplate → haiku is fine
   - Switch model at the start of a step if needed: `session_status model=[chosen-model]`
   - Drop back after the step completes if you stepped up
   - **Never silently stay on Opus across unrelated steps** — be deliberate
   - Announce any model change in 1 line before the step: `"[step-name]: using sonnet-high — complex logic."`

2. **Find the plan to execute and extract checkpoint IDs:**
   - First, check conversation context for a recent plan
   - If not found, search haivemind:
     ```
     mcporter call haivemind.search_memories query="PLAN [channel-id]" limit:5
     ```
   - **Extract the Checkpoints table from the plan** — these are the canonical checkpoint IDs to use during execution. Each step has a pre-defined `Checkpoint:` ID. Use those exact IDs when storing to haivemind — don't invent new ones.
   - If `/do` has arguments (e.g., `/do update the README`), execute that directly — no plan lookup needed, generate checkpoint IDs as `step-N-[slug]`

3. **Execute step-by-step — update Notion markers as you go:**

   **On starting a step** → update marker to 🔄 in Notion:
   ```bash
   # Find the line "🔲 `step-N-[slug]`" in the Notion page and replace with 🔄
   mcporter call notion-oauth.notion-update-page page_id="[page-id]" \
     content="[full plan with that step's marker changed from 🔲 to 🔄]"
   ```

   - **Snapshot before any risky, destructive, or irreversible step:**
     ```bash
     mcporter call haivemind.store_memory \
       content="SNAPSHOT [channel-id] [ISO-timestamp] do: auto=pre-risky-step | task=[task] | progress=[steps done] | context=[active files/IDs] | last_action=[previous step] | next=step [N]: [step name] | blockers=none" \
       category="operations"
     ```
   - Complete each step fully
   - **Verify completion** with evidence (file exists, command succeeded, test passes)

   **On step complete** → update marker to ✅ in Notion:
   ```bash
   # Replace 🔄 `step-N-[slug]` with ✅ `step-N-[slug]`
   mcporter call notion-oauth.notion-update-page page_id="[page-id]" \
     content="[full plan with that step's marker changed from 🔄 to ✅]"
   ```

   **On step failure** → update marker to ❌, snapshot state, stop and report:
   ```bash
   # Replace with ❌ `step-N-[slug]`
   mcporter call notion-oauth.notion-update-page page_id="[page-id]" \
     content="[full plan with that step's marker changed to ❌]"
   ```
   Then snapshot, then stop and ask how to proceed. Don't continue blindly.

4. **Track progress** in haivemind — THREE entries per completed step:
   ```bash
   # Execution log
   mcporter call haivemind.store_memory \
     content="EXECUTION [channel-id] [timestamp]: Step [N] complete — [evidence]" \
     category="operations"

   # Checkpoint — use the ID from the plan's Checkpoints table (e.g. step-1-fetch-data)
   mcporter call haivemind.store_memory \
     content="CHECKPOINT [channel-id] phase=[plan-checkpoint-id] [ISO-timestamp]: summary=[what this step did and what it produced] | artifacts=[files created/modified, IDs] | decisions=[any choices made] | outcome=success | next=[next plan-checkpoint-id]: [next step name] | open=none" \
     category="operations"

   # TASK-RESUME key (updated after each step — /continue picks up here)
   mcporter call haivemind.store_memory \
     content="TASK-RESUME [channel-id] [ISO-timestamp]: [plan-checkpoint-id] complete. Resume: [next-plan-checkpoint-id] — [next step description]. Artifacts: [key refs]." \
     category="operations"
   ```

   **Auto-snapshot every 10 tool calls** (regardless of step boundaries):
   ```bash
   # Count tool calls. At every 10th:
   mcporter call haivemind.store_memory \
     content="SNAPSHOT [channel-id] [ISO-timestamp] do: auto=10-call-interval | task=[task] | progress=[N of M steps done] | context=[active artifacts] | last_action=[most recent] | next=[upcoming step] | blockers=none" \
     category="operations"
   ```

5. **Report completion:**
   - Summary of what was done
   - Evidence for each step
   - Any issues encountered
   - Next steps if applicable

## Quick Execution

If the task is simple enough (one or two steps), skip formal plan retrieval and just do it:
```
/do rename the config file to config.backup
```
→ Just do it directly, verify, report.

## Error Handling

- **No plan found:** Ask user what to execute
- **Step fails:** Stop and report — don't continue blindly
- **Ambiguous plan:** Ask which plan to execute if multiple exist

## Before Starting

Read `<LOCAL_PATH>/dev/<PROJECT_NAME>.md` for development patterns, common mistakes, and gotchas before executing.

## After Completion

When execution completes successfully:
1. Report completion with evidence
2. **Chain forward:** "Run `/assess` to review the changes?"
3. If user approves or says "yes" → trigger `/assess`

## Result Posting (Sub-Agent Pattern)

When running as a sub-agent (session key contains "subagent"):

**You MUST post results back to the originating channel before completing.**

See full pattern: `<LOCAL_PATH>/dev/skills/subagent-result-posting/SKILL.md`

### Quick Reference:
1. **Extract return channel** from Subagent Context in system prompt:
   - `Requester session: agent:main:[channel]:channel:[id]` → platform + channel ID
   - `Requester channel: [channel]` → platform name
2. **Format execution results** for the platform (Discord: <2000 chars per message; Slack: mrkdwn; WhatsApp/Signal: plain text)
3. **Post results:**
   ```
   message action=send channel=[platform] target=[channel-id] message="✅ **Execution Complete**\n\n[results summary]"
   ```
4. **If results exceed limit:** Post summary to channel, write full log to `<LOCAL_PATH>/dev/tmp/results/do-[timestamp].md`
5. **On failure:** Post what completed and where it broke — never fail silently
6. **On partial completion:** Post progress with clear indication of what remains

### Execution-Specific Posting:
- Lead with **status** (✅ Complete / ⚠️ Partial / ❌ Failed)
- Show **evidence** for each step (file created, command output, test passed)
- If errors occurred, include the actual error message
- End with: "Run `/assess` to review the changes?"

## Notes

- Sonnet is efficient and cost-effective for execution
- Always verify each step before claiming completion
- Store execution results in haivemind for audit trail
- After completion, model stays on Sonnet (the default)
- Chains into `/assess` for post-implementation review
