---
name: assess
description: Post-implementation multi-perspective review with Opus. Checks security, architecture, code quality, and integration after changes are made. Runs after /do, chains into /self-reflect.
category: workflows
runtimes: [claude]
pii_safe: true
---

# /assess — Post-Implementation Review (Opus)

When user invokes `/assess [what was built]`, perform comprehensive review.

## Steps

1. **Switch to Opus** for multi-angle analysis:
   ```
   session_status model=opus
   ```

2. **Gather context:**
   - What was built/changed? (check conversation, haivemind, git diff)
   - Read the original plan if one exists:
     ```
     mcporter call haivemind.search_memories query="PLAN [channel-id]" limit:5
     ```
   - Review relevant files, tests, logs, recent commits

3. **Run four review lenses:**

   **🔒 Security:**
   - Secrets in code vs env/secrets manager?
   - Input validation on user-facing surfaces?
   - Auth/authz properly enforced?
   - API keys exposed in logs or errors?

   **🏗️ Architecture:**
   - Fits <PROJECT_NAME> patterns? (skills, channel directives, haivemind)
   - Tight coupling introduced?
   - Works across channels (Discord/Slack/WhatsApp/Signal)?
   - Session isolation respected?

   **📝 Code Quality:**
   - Readable and maintainable?
   - Error handling comprehensive?
   - Logging appropriate?
   - Documentation updated?

   **🔗 Integration:**
   - Survives compaction/restart?
   - haivemind used for persistence where needed?
   - Channel directives updated if relevant?
   - Tested edge cases?

4. **Format findings by severity:**

   ```markdown
   ## Assessment: [Feature Name]
   **Date:** [ISO timestamp] | **Model:** Opus

   ### 🔴 CRITICAL (Fix before merge)
   - [Issue] — [Evidence] — [Fix]

   ### 🟡 IMPROVEMENTS (Should fix)
   - [Suggestion] — [Why] — [How]

   ### ✅ LOOKS GOOD
   - [What worked well]
   - [Patterns followed correctly]

   ### 📊 Plan Compliance
   - [x] Step 1 verified
   - [x] Step 2 verified
   - [ ] Step 3 — deviation: [what changed and why]
   ```

5. **Store assessment to haivemind:**
   ```
   mcporter call haivemind.store_memory \
     content="ASSESSMENT [channel-id] [timestamp] feature=[name]: [summary of findings]" \
     category="development"
   ```

6. **Present findings and chain forward:**
   - Show the assessment report
   - If issues found: "Want me to `/do` the fixes?"
   - After review complete: "Run `/self-reflect` to capture what we learned?"

7. **Switch back to Sonnet:**
   ```
   session_status model=sonnet
   ```

## When to Use

- After `/do` completes an implementation
- Before creating or merging a PR
- When reviewing someone else's changes
- After any significant code/infrastructure change

## Principles

- **Evidence over opinion** — show the code, log, or config that's wrong
- **Actionable fixes** — every issue includes how to fix it
- **Celebrate wins** — note what was done well, not just problems
- **Feed the loop** — findings become learnings via `/self-reflect`

## Result Posting (Sub-Agent Pattern)

When running as a sub-agent (session key contains "subagent"):

**You MUST post assessment results back to the originating channel before completing.**

See full pattern: `<LOCAL_PATH>/dev/skills/subagent-result-posting/SKILL.md`

### Quick Reference:
1. **Extract return channel** from Subagent Context in system prompt:
   - `Requester session: agent:main:[channel]:channel:[id]` → platform + channel ID
   - `Requester channel: [channel]` → platform name
2. **Format assessment** for the platform (Discord: <2000 chars; Slack: mrkdwn; WhatsApp/Signal: plain text)
3. **Post results:**
   ```
   message action=send channel=[platform] target=[channel-id] message="📊 **Assessment Complete**\n\n[findings summary]"
   ```
4. **If assessment exceeds limit:** Post critical/improvement items to channel, write full review to `<LOCAL_PATH>/dev/tmp/results/assess-[timestamp].md`
5. **On failure:** Post what could be assessed and what couldn't — never fail silently

### Assessment-Specific Posting:
- Lead with **🔴 CRITICAL items** (if any) — these need immediate attention
- Follow with **🟡 IMPROVEMENTS** count
- Include **✅ LOOKS GOOD** highlights
- End with: "Run `/self-reflect` to capture what we learned?"

## Notes

- `/assess` is proactive review (post-implementation quality check)
- `/diagnose` is reactive debugging (something is broken, find out why)
- Both use Opus, but serve different purposes
- Assessment findings should update `<PROJECT_NAME>.md` via `/self-reflect`
