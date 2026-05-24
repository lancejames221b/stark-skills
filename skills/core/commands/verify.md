---
description: "Verification checklist before claiming work is complete"
---

# Verification Before Completion — Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

Run this before claiming ANY work is done. Go through each step:

1. **IDENTIFY** — What command proves this claim?
2. **RUN** — Execute it fresh right now
3. **READ** — Full output, check exit code, count failures
4. **VERIFY** — Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. **ONLY THEN** — Make the claim

## Red Flags — STOP if you notice:

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push without running tests
- Trusting a previous run rather than running fresh
- Partial check (linter passed ≠ build passes ≠ tests pass)

## Common Claims and What They Actually Require

| Claim | Requires |
|-------|----------|
| Tests pass | Run test command: 0 failures |
| Linter clean | Run linter: 0 errors |
| Build succeeds | Run build: exit 0 |
| Bug fixed | Reproduce original symptom: now passes |
| Service running | `systemctl status` or `docker ps` output |
| SSH host reachable | `ssh -o ConnectTimeout=5 <host> uptime` |
| File deployed | `cat` the remote file and verify contents |

## Arguments: $ARGUMENTS

If arguments provided, run verification for that specific claim/component.
