---
name: dream-st
description: "Run short-term memory consolidation pass (delta-only, no pruning). Use after a session ends, or when memories feel stale. Trigger phrases: /dream-st, run dream short, dream-short, st dream, consolidate recent memories"
category: execution
runtimes: [claude]
pii_safe: true
---

# dream-st — Short-Term Memory Consolidation

Runs a 4-phase short-term dreaming pass across Obsidian + qdrant + hAIveMind.
Delta-only: only processes entries modified since the last ST run.
No pruning: that is long-term (LT) dreamer's job.

## What it does

1. **Orient** — reads MEMORY.md and last-run timestamp from state.json
2. **Gather** — enumerates Obsidian entries modified since last ST run (delta-only, fast)
3. **Consolidate** — deduplicates within delta; merges near-duplicate entries; re-vectorizes merged results into qdrant
4. **Index update** — rewrites MEMORY.md with any updated summaries (no pruning)

## When to use

- After a productive session where many memories were written
- When you notice duplicate or near-duplicate memory entries
- Manually any time: `/dream-st`
- Automatically: Stop hook fires this after every 2+ sessions (60-min debounce)

## Invocation

```bash
ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_st'
```

### Flags

- `--dry-run` — Preview what would be merged; makes NO changes to any store
- `--force` — Bypass the 60-minute debounce check and run immediately

### Examples

```bash
# Standard run
ssh <INFERENCE_HOST> 'cd <LOCAL_PATH>/dev && <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_st'

# Dry run (preview only)
ssh <INFERENCE_HOST> '<LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_st --dry-run'

# Force run (ignore debounce)
ssh <INFERENCE_HOST> '<LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_st --force'
```

## Output

Returns JSON with:
- `delta_count`: number of entries in the delta (modified since last run)
- `merged_count`: number of duplicate pairs merged
- `elapsed_s`: wall-clock seconds for the run
- `errors`: list of non-fatal errors encountered

Log: `<LOCAL_PATH>/.local/state/dreaming/dream-st.log` (JSON lines, one per run)

## Scope limits

- **No pruning** — does not delete any entries (LT tier handles pruning)
- **Vault/ skipped** — credentials directory is never touched
- **Local only** — uses PI/Ollama embeddings (sentence-transformers), never cloud Claude
- **Shared lock** — concurrent ST runs are allowed; blocked only if LT dreamer holds exclusive lock
