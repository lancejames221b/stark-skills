---
name: diagnose
description: Deep analysis and debugging with Opus. Systematically investigate problems, identify root causes, and recommend fixes with evidence.
category: debugging
runtimes: [claude]
pii_safe: true
---

# /diagnose — Deep Analysis (Opus)

When user invokes `/diagnose [problem description]`, perform deep investigation using Opus.

## Steps

1. **Switch to Opus** for deep analytical thinking:
   ```
   session_status model=opus
   ```

2. **Gather evidence** before forming hypotheses:
   - Read relevant logs, configs, source files
   - Check system state (processes, services, network)
   - Review recent changes (git log, deployment history)
   - Run diagnostic commands as needed

3. **Analyze systematically:**
   - What is the **expected** behavior?
   - What is the **actual** behavior?
   - What **changed** recently?
   - What are the **possible root causes**? (rank by likelihood)
   - What **evidence** supports or refutes each hypothesis?

4. **Create diagnosis report:**

   ```markdown
   ## Diagnosis: [Problem Summary]
   **Created:** [ISO timestamp]
   **Model:** Opus
   **Severity:** Critical | High | Medium | Low

   ### Symptoms
   - [What's happening]

   ### Expected Behavior
   - [What should happen]

   ### Investigation
   1. [What I checked] → [What I found]
   2. [What I checked] → [What I found]

   ### Root Cause
   [The actual cause, with evidence]

   ### Recommended Fix
   1. [Specific action]
   2. [Specific action]

   ### Prevention
   - [How to prevent recurrence]
   ```

5. **Store diagnosis in haivemind:**
   ```
   mcporter call haivemind.store_memory \
     content="DIAGNOSIS [channel-id] [ISO-timestamp] problem=[summary]: [diagnosis]" \
     category="operations"
   ```

6. **Present findings** clearly:
   - Lead with the root cause
   - Show the evidence chain
   - Offer specific fix steps
   - Suggest prevention measures

7. **Switch back to Sonnet** after presenting findings:
   ```
   session_status model=sonnet
   ```

8. **Offer next steps:**
   - "Want me to `/plan` the fix?"
   - "Should I `/do` it now?"
   - This chains naturally into the plan/do workflow

## Investigation Principles

- **Evidence first, hypothesis second** — don't assume, verify
- **Check the obvious** — is it plugged in? Is the service running?
- **Recent changes are prime suspects** — what deployed last?
- **Reproduce before fixing** — understand the failure mode
- **One variable at a time** — don't change multiple things

## Error Handling

- **Not enough info:** Ask clarifying questions before investigating
- **Multiple possible causes:** Rank by likelihood, investigate top candidates
- **Can't reproduce:** Document what was tried, suggest monitoring

## Before Diagnosing

Read `<LOCAL_PATH>/dev/<PROJECT_NAME>.md` — check Common Mistakes and Gotchas sections. The answer may already be documented from a previous incident.

## Result Posting (Sub-Agent Pattern)

When running as a sub-agent (session key contains "subagent"):

**You MUST post diagnosis results back to the originating channel before completing.**

See full pattern: `<LOCAL_PATH>/dev/skills/subagent-result-posting/SKILL.md`

### Quick Reference:
1. **Extract return channel** from Subagent Context in system prompt:
   - `Requester session: agent:main:[channel]:channel:[id]` → platform + channel ID
   - `Requester channel: [channel]` → platform name
2. **Format diagnosis** for the platform (Discord: <2000 chars; Slack: mrkdwn; WhatsApp/Signal: plain text)
3. **Post results:**
   ```
   message action=send channel=[platform] target=[channel-id] message="🔍 **Diagnosis Complete**\n\n[findings summary]"
   ```
4. **If diagnosis exceeds limit:** Post root cause + recommended fix to channel, write full investigation to `<LOCAL_PATH>/dev/tmp/results/diagnose-[timestamp].md`
5. **On failure to diagnose:** Post what was investigated and what's still unknown — never fail silently

### Diagnosis-Specific Posting:
- Lead with **Root Cause** (the most important finding)
- Include **Severity** (Critical/High/Medium/Low)
- Show the **evidence chain** (even abbreviated)
- Include **Recommended Fix** (actionable, not vague)
- End with: "Want me to `/plan` the fix?" or "Should I `/do` it now?"

## Notes

- Opus excels at multi-step reasoning and complex analysis
- Always show your work — the investigation trail matters
- Don't just find the bug — explain *why* it happened
- After diagnosis, switch back to Sonnet automatically
- Chain into `/plan` for complex fixes, `/do` for simple ones
- After fix is applied: "Run `/assess` to verify the fix?"
