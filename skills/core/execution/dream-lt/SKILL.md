---
name: dream-lt
description: "Run long-term memory consolidation pass (full pass + decay-based pruning). Heavy ~30 min run. Trigger phrases: /dream-lt, dream long, lt dream, deep consolidate, weekly memory cleanup"
category: execution
runtimes: [claude]
pii_safe: true
---

# dream-lt — Long-Term Memory Consolidation

The LT dreamer runs a full cross-history pass over all three memory stores (Obsidian, hAIveMind, qdrant). It finds contradictions, merges near-duplicate memories from across months of history, removes dead links, and prunes entries that haven't been accessed in 90+ days with a decay score below 0.2.

## What it does

- **Phase A — Orient**: reads MEMORY.md line count, qdrant collection stats, Obsidian category tree
- **Phase B — Gather**: collects ALL entries with `decay_score < 0.5` OR last accessed >30 days ago
- **Phase C — Consolidate**: detects contradictions, merges near-duplicates via local PI (Ollama), sweeps for absolute dates, removes dead Obsidian links
- **Phase D — Prune**: deletes entries where `decay_score < 0.2 AND idle > 90d AND NOT pinned` from qdrant and hAIveMind (Obsidian files kept — canonical source). Pruned records saved to `<LOCAL_PATH>/.local/var/dreaming/lt-pruned-YYYY-MM-DD.json` (recoverable for 30 days)
- **Phase E — Re-index**: triggers qdrant HNSW optimisation after major mutations

## When to use

- After large batches of memory imports (migrate-obs, bulk store)
- When `/dream-status` shows divergence between stores
- To force a cleanup before a major project review
- Runs automatically every Sunday at 3:00 AM EDT via cron on `<INFERENCE_HOST>`

## Timing

- Typical run: 5–30 minutes depending on corpus size and consolidation volume
- Timeout (cron): 45 minutes hard cap (`timeout 2700`)

## Invocation

Run manually via SSH to <INFERENCE_HOST>:

```bash
ssh <INFERENCE_HOST> '<LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_lt'
```

### Flags

- `--dry-run` — preview what would be pruned/consolidated without making any changes. Safe to run anytime.
- `--use-cloud` — opt into cloud Claude for consolidation (default: local PI/Ollama on <INFERENCE_HOST>)

```bash
# Dry run (safe preview)
ssh <INFERENCE_HOST> '<LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_lt --dry-run'

# Full run with cloud Claude consolidation
ssh <INFERENCE_HOST> 'DREAM_LT_USE_CLOUD=1 <LOCAL_PATH>/.venvs/dreaming/bin/python -m dreaming.main_lt --use-cloud'
```

## Outputs

- JSON Lines log: `<LOCAL_PATH>/.local/state/dreaming/dream-lt.log`
- Prune manifest: `<LOCAL_PATH>/.local/var/dreaming/lt-pruned-YYYY-MM-DD.json`
- Discord: summary posted to #hud on completion (no ping unless errors)
- State: last run recorded in `<LOCAL_PATH>/.local/state/dreaming/state.json`

## Lock semantics

LT acquires an exclusive lock (`<LOCAL_PATH>/.local/state/dreaming/.dream-lt.lock`). It fails fast if ST or another LT is already running. ST acquires a shared lock on its own lock file and can run concurrently with other STs but not with LT.

## Recovery

If pruned entries need to be restored, check the daily prune manifest:
```bash
cat <LOCAL_PATH>/.local/var/dreaming/lt-pruned-YYYY-MM-DD.json | python3 -m json.tool
```

Prune manifests are kept for 30 days before final deletion.
