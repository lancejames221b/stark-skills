---
name: dream-status
description: "Show dreaming system status: last ST/LT run timestamps, qdrant index health, store divergence, pending consolidations, recent prune log. Use when user says: /dream-status, dream status, how is dreaming, dream health, dreaming system status, check dream health"
category: execution
runtimes: [claude]
pii_safe: true
---

# dream-status — Dreaming System Status

Shows a live status report for the two-tier dreaming memory consolidation system.

## What it shows

- **ST dreamer**: last run timestamp, run count, recent log entries (last 3)
- **LT dreamer**: last run timestamp, run count, schedule, recent log entries (last 3)
- **Store consistency**: Obsidian file count, qdrant point count, hAIveMind entry count, divergence %
- **Soft-delete queue**: count of entries soft-deleted in the last 7 days (recoverable via restore.py)

## Invocation

```bash
ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.status'
```

For JSON output (pipe-friendly):
```bash
ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.status --json'
```

## Interpreting the output

- **Divergence < 2%**: OK — stores are in sync
- **Divergence 2-10%**: Warning — investigate with `/dream-st --dry-run`
- **Divergence > 10%**: Critical — LT will refuse to run; manual reconciliation needed
- **hAIveMind count**: Always much lower than Obsidian (~52 vs ~32K) — this is EXPECTED (write-through index)
- **Pending prunes**: Soft-deleted entries still in the 30-day recovery window; run `python -m dreaming.restore` to recover

## Related skills

- `/dream-st` — Run a short-term consolidation pass manually
- `/dream-lt` — Run a long-term consolidation + prune pass manually
- Recovery: `ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.restore'`
- Integrity: `ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.integrity --human'`
