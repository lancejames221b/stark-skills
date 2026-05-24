---
name: verification-before-completion
description: Use before claiming any <VOICE_RUNTIME> code change is complete. Enforces deploy-to-host, service-restart, live-Discord-test, and journalctl-check discipline on top of the core superpowers verification rules.
category: verification
runtimes: [claude]
pii_safe: true
---

# Verification Before Completion — <VOICE_RUNTIME> Extension

Inherits the Iron Law and Gate Function from `superpowers:verification-before-completion`:

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes. Evidence before claims. No exceptions.

## Scope

Applies whenever the task modifies files under `<LOCAL_PATH>/Dev/<VOICE_RUNTIME>/` (voice runtime source) or touches live state on <INFERENCE_HOST>.

For non-<VOICE_RUNTIME> work, the core superpowers skill still applies — this file adds runtime-specific checks, it does not replace them.

## Required checks before ANY "it works" / "done" / "deployed" claim

### 1. Source actually deployed
- [ ] `rsync -avzn <LOCAL_PATH>/Dev/<VOICE_RUNTIME>/src/ <LOCAL_PATH>/mnt/<INFERENCE_HOST>/dev/<VOICE_RUNTIME>-voice/src/` — dry-run first, review what would change
- [ ] `rsync -avz <LOCAL_PATH>/Dev/<VOICE_RUNTIME>/src/ <LOCAL_PATH>/mnt/<INFERENCE_HOST>/dev/<VOICE_RUNTIME>-voice/src/` — actual sync
- [ ] Confirmed file timestamp on <INFERENCE_HOST> side matches local: `stat <LOCAL_PATH>/Dev/<VOICE_RUNTIME>/src/<file>; stat <LOCAL_PATH>/mnt/<INFERENCE_HOST>/dev/<VOICE_RUNTIME>-voice/src/<file>`
- [ ] `diff -q <LOCAL_PATH>/Dev/<VOICE_RUNTIME>/src/<file> <LOCAL_PATH>/mnt/<INFERENCE_HOST>/dev/<VOICE_RUNTIME>-voice/src/<file>` → no output (identical)

### 2. Service restarted
- [ ] `ssh <INFERENCE_HOST> "systemctl --user restart <VOICE_RUNTIME>-voice"` completed
- [ ] `ssh <INFERENCE_HOST> "systemctl --user is-active <VOICE_RUNTIME>-voice"` → `active`
- [ ] No crash loop in the last minute: `ssh <INFERENCE_HOST> "journalctl --user -u <VOICE_RUNTIME>-voice --since '1 minute ago' --no-pager" | grep -cE 'Started|Stopped'` → ≤2 entries

### 3. Feature actually works in Discord
- [ ] Posted the trigger message in the real Discord channel using the <VOICE_RUNTIME> bot token (DISCORD_TOKEN from `.env`, NOT <PROJECT_NAME>)
- [ ] Polled `/api/v10/channels/$CID/messages` after a reasonable wait (5-10s)
- [ ] Bot response content matches the expected behavior — read the actual content, don't just check existence
- [ ] If the feature creates a thread: confirmed thread exists via `/api/v10/channels/$CID/threads/active`
- [ ] If the feature edits/pins a message: confirmed via `/api/v10/channels/$CID/pins`

### 4. No silent errors
- [ ] `ssh <INFERENCE_HOST> "journalctl --user -u <VOICE_RUNTIME>-voice --since '<test start time>' --no-pager | grep -iE 'error|fail|exception|unhandled|rejection'"` — empty, or only expected entries
- [ ] Gateway logs clean: `ssh <INFERENCE_HOST> "journalctl --user -u <VOICE_RUNTIME>-gateway --since '<test start time>' --no-pager | tail -30"`
- [ ] Circuit breakers (hAIveMind, MCP) did not open during the test

### 5. <VOICE_RUNTIME>-admin discipline followed
- [ ] Used `DISCORD_TOKEN` from `<LOCAL_PATH>/Dev/<VOICE_RUNTIME>/.env` for API calls (NOT <PROJECT_NAME>)
- [ ] Used SSHFS paths (`<LOCAL_PATH>/mnt/<INFERENCE_HOST>/...`) for file reads, not `ssh <INFERENCE_HOST> "cat ..."`

## Red Flags — STOP

In addition to the superpowers red flags ("should", "probably", "seems to"):

- "I edited the file so it's deployed" — NO, <WORKSTATION_HOST> edits don't auto-propagate; the live code runs from <INFERENCE_HOST>
- "The service would have picked it up" — NO, the systemd unit doesn't hot-reload Node code
- "The code looks right" — irrelevant. Code that looks right still fails live.
- "Discord bot token worked last time" — verify the token matches DISCORD_TOKEN in env
- "I'll restart after the next change" — NO, every deploy needs a restart before claims
- "The verbose thread showed output" — not sufficient; check journalctl too

## Rationalization prevention (<VOICE_RUNTIME>-specific)

| Excuse | Reality |
|---|---|
| "Logs looked clean for a second" | Run `journalctl --since '<test time>'` with a grep |
| "Service status was active" | Active ≠ loaded-new-code. Check restart timestamp + process start time. |
| "Sent a message, got something" | Read the response content. Quote it in your report. |
| "rsync said 0 bytes transferred" | That means it was already synced — good, but verify with `diff -q` |

## When to delegate to a code-reviewer agent

If the change spans >3 files OR touches concurrency-sensitive code (thread creation, session rotation, gateway spawn, TTS queue, audio transport), after live verification succeeds, spawn a `feature-dev:code-reviewer` agent for a fresh-eyes audit of the diff.

This is **in addition to** the live verification, not a substitute for it. A reviewer agent that reads code cannot prove the running system works.

## The Bottom Line

```
1. Deploy → confirm (diff -q)
2. Restart → confirm (is-active, journalctl quiet)
3. Live test → quote the actual output
4. Check logs → grep for errors
5. THEN claim "done"
```

Any shortcut = you will report a false completion, and your human partner will lose trust. Do not skip.
