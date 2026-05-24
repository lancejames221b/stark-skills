---
name: migrate-memories-to-obsidian
description: Batch-migrate memories from a semantic memory store (e.g., hAIveMind, or any provider with a `search_memories` MCP tool) into an Obsidian vault as canonical local-first markdown files. One batch per run — designed for cron execution. Reads/writes `.migration-state.json` in vault root for resumability.
category: execution
runtimes: [claude]
pii_safe: true
---

# migrate-memories-to-obsidian

Obsidian-first migration of memories from a semantic memory store. Run one batch per session. Do NOT ask questions — operate autonomously and exit after the batch. Designed for cron.

The skill is parameterized over the memory-source interface — any provider with `search_memories` (paginated, category-filterable) and `store_memory` MCP tools can be the source. The reference implementation used the hAIveMind provider; other providers fit the same shape.

## Required setup

- `OBSIDIAN_VAULT_PATH` — absolute path to the Obsidian vault root (e.g., `<LOCAL_PATH>/Obsidian/Claude/`). Obsidian MCP paths are relative to this root.
- `MEMORY_SOURCE_URL` — base URL or alias for the memory source (only used for logs/headers; auth is via the MCP tool, not direct HTTP)
- `MEMORY_PROVIDER` — MCP namespace for the memory source (e.g., `haivemind`). The skill calls `mcp__<provider>__search_memories` and `mcp__<provider>__store_memory`.
- `STATE_FILE_PATH` — relative path in vault for the migration state JSON (default: `.migration-state.json`)

## Optional providers

- **Notion promotion** — set `NOTION_PROMOTE=true` and `NOTION_DATABASE_ID` to also promote high-signal memories (score >= 3) to a Notion database. Rate-limited to `NOTION_PROMOTIONS_PER_BATCH` (default 5). When unset, memories live in Obsidian only.
- **Integrity check** — set `INTEGRITY_CHECK_CMD` (e.g., `ssh <HOST_ALIAS> 'cd <REMOTE_DIR> && python -m dreaming.integrity'`) to run a post-batch divergence check against any secondary index (e.g., qdrant). When unset, the skill skips integrity reporting.
- **mcporter fan-out** — set `MCPORTER_HOST_ALIAS=<HOST_ALIAS>` if the memory provider's MCP server lives on another machine and you reach it via `ssh <HOST_ALIAS> 'mcporter call <provider>.<tool>'`.

If `MEMORY_PROVIDER` doesn't conform to the `search_memories(query, category, limit, offset, semantic) -> {results, pagination}` shape, you'll need to write an adapter. The skill is unusable without a memory source.

## Tool loading

```
ToolSearch select:mcp__obsidian__read_file,mcp__obsidian__write_file,mcp__obsidian__list_directory
ToolSearch select:mcp__<MEMORY_PROVIDER>__search_memories,mcp__<MEMORY_PROVIDER>__store_memory
ToolSearch select:mcp__notion__notion-create-pages  # only if NOTION_PROMOTE=true
```

## Constants

- **Vault root**: `<OBSIDIAN_VAULT_PATH>` (Obsidian MCP paths are relative)
- **State file**: `<STATE_FILE_PATH>` (default `.migration-state.json`)
- **Max Notion promotions per batch**: `NOTION_PROMOTIONS_PER_BATCH` (default 5)

## Category → Obsidian subdir

The default mapping (override by editing this table to match your memory provider's categories):

| Memory category | Obsidian subdir |
|---|---|
| incidents | incident/ |
| security | security/ |
| infrastructure | infrastructure/ |
| deployments | deployment/ |
| rules | rules/ |
| project | project/ |
| runbooks | infrastructure/ |
| monitoring | global/ |
| agent | global/ |
| global | global/ |

## Batch sizes (per category, per run)

Tune to your memory volume:

| Category | Limit per run |
|---|---|
| incidents | 20 |
| security | 10 |
| infrastructure | 25 |
| deployments | 28 |
| rules | 25 |
| project | 25 |
| runbooks | 5 |
| monitoring | 10 |
| agent | 5 |
| global | 50 |

## Machine classification

Map `machine_id` / `hostname` from memory metadata to a normalized label. Customize for your hosts:

- `<HOST_ALIAS>-workstation-1` → `<HOST_ALIAS>`
- `<HOST_ALIAS>-dev` → `<HOST_ALIAS>-dev`
- hostnames containing `macbook` / `<MAC_HOST>` → `<MAC_HOST>`
- hostnames containing your workstation alias → `<HOST_ALIAS>`
- blank / unknown → `unknown`

## Credential detection patterns (Python regex, case-insensitive)

Any match → force `Vault/` subdir, skip Notion promotion, tag `auto-detected-credential`:

- `sk-[A-Za-z0-9\-_]{20,}`
- `AKIA[A-Z0-9]{16}`
- `ghp_[A-Za-z0-9]{10,}`
- `gho_[A-Za-z0-9]{10,}`
- `xoxb-[0-9A-Za-z\-]+`
- `xoxp-[0-9A-Za-z\-]+`
- `api[_-]?key\s*[:=]\s*\S{8,}`
- `password\s*[:=]\s*\S{4,}`
- `passwd\s*[:=]\s*\S{4,}`
- `-----BEGIN (RSA|EC|PRIVATE|CERTIFICATE)`
- `(postgres|mysql|mongodb)://[^@]+:[^@]+@`
- `Bearer [A-Za-z0-9\-._~+/]{20,}`
- `[A-Z][A-Z0-9_]*(_SECRET|_TOKEN|_PASSWORD|_API_KEY)\s*[=:]\s*\S+`

## Skip filters (noise)

Skip entirely — no Obsidian write, no index entry:

- Content starts with `VOICE-TASK`
- Content matches `^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}\] user: .* \| response:` (chat-transcript noise)
- Content length < 100 chars
- Content starts with `[OBS-MEM]` (already migrated to Obsidian)
- Content starts with `[HANDOFF-MEM]` (handoff index — not a memory)
- Content starts with `MIGRATION-CHECKPOINT-NOTION` (internal checkpoint)

Special handling — NOT skip:

- Content starts with `[NOTION-MEM]` → backfill Obsidian from existing Notion-promoted memory. Extract HV-ID + Notion URL from structured fields, write Obsidian file with `source: migration-backfill`, then store `[OBS-MEM]` index entry.

## Notion promotion scoring (only if NOTION_PROMOTE=true)

**Hard blocks (Obsidian-only, never score):**
- Category is `security` → `security/` (or `Vault/` if credential)
- Credential detected → `Vault/` only
- Content < 100 chars → skip entirely

**Scoring (threshold ≥ 3 = promote):**

Category bonus (max 2):
- incidents, infrastructure, deployments, rules → +2
- project, monitoring → +1
- global, agent, runbooks → 0

Length bonus (max 2):
- ≥ 2000 chars → +2
- ≥ 500 chars → +1

Keyword bonus (max 3, one per group):
- Group A (severity): `CVE-`, `CRITICAL`, `P0`, `CVSS`, `0day`, `zero-day` → +1
- Group B (ops): `incident`, `deploy`, `production`, `prod`, `staging`, `rollback`, `outage`, `postmortem`, `root cause` → +1
- Group C (entities): your own project/product nouns (customize) → +1

Structure bonus (max 1):
- Contains `## ` or `### ` heading → +1

## Execution flow (one batch per run)

### STEP 1 — Load state

Read `STATE_FILE_PATH` via `mcp__obsidian__read_file`. If missing, initialize default state:
```json
{
  "started_at": null,
  "last_run": null,
  "category_order": ["incidents", "security", "infrastructure", "deployments", "rules", "project", "runbooks", "monitoring", "agent", "global"],
  "category_progress": {},
  "total_written": 0,
  "total_skipped": 0,
  "total_notion_promoted": 0,
  "all_done": false
}
```

Set `started_at` if null, set `last_run` to current ISO timestamp.

### STEP 2 — Pick current category

Iterate `category_order`. First category where `done == false` is current. If all `done`, set `all_done: true`, write state, print completion summary, exit.

### STEP 3 — Fetch batch

```
mcp__<MEMORY_PROVIDER>__search_memories(
  query=<category_name>,
  category=<category_name>,
  limit=<batch_size>,
  offset=<last_offset>,
  semantic=false
)
```

Update `category_progress.<cat>.total` from `pagination.total` first time discovered.

### STEP 4 — Process each memory

**4a. Skip check:** apply skip filters. If skip → `skipped++`, continue.

**4b. NOTION-MEM backfill:** if content starts with `[NOTION-MEM]`, parse structured fields, build Obsidian file with `source: migration-backfill`, use HV-ID (not current memory id) as `hv_id`, set `notion_url` to existing URL. Write file, store `[OBS-MEM]` index, `written++`, continue.

**4c. Credential scan:** apply all 13 patterns. If any match → `sensitive=true`, `subdir=Vault/`, `notion_score=0`.

**4d. Determine subdir** (if not credential-overridden): use the category mapping table.

**4e. Compute Notion promotion score** (only if `NOTION_PROMOTE=true` and not sensitive).

**4f. Build Obsidian frontmatter:**
```yaml
---
hv_id: <memory.metadata.memory_id>
category: <category>
machine: <classified machine>
date: <metadata.created_at | YYYY-MM-DD>
tags: [<tag1>, <tag2>]
source: migration
sensitive: <true|false>
notion_url: ""
---
```

**4g. Build slug:** first line of content (or first 80 chars), lowercase, replace special chars with `-`, truncate to 60 chars. Prefix with date: `YYYY-MM-DD-<slug>.md`.

**4h. Write Obsidian file:** `mcp__obsidian__write_file` to `<subdir>/<YYYY-MM-DD>-<slug>.md`. Content = frontmatter + `\n\n` + original content. If sensitive: prepend `> WARNING: Credential content — Obsidian-only, never synced to Notion\n\n`.

**4i. Notion promotion** (only if score ≥ 3 AND not sensitive AND `notion_promotions_this_batch < NOTION_PROMOTIONS_PER_BATCH`):
```
mcp__notion__notion-create-pages(
  parent: {"data_source_id": "<NOTION_DATABASE_ID>"},
  pages: [{
    properties: {
      title: <derived title>,
      Category: <mapped category>,
      Machine: <classified machine>,
      "date:Date:start": <YYYY-MM-DD>,
      Summary: <first 200 chars>,
      "HV-ID": <hv_id>,
      Source: "migration"
    },
    content: <first 1000 chars>
  }]
)
```
Capture returned URL. Update Obsidian frontmatter `notion_url` field by rewriting the file. Increment `notion_promotions_this_batch`.

**4j. Store [OBS-MEM] index entry:**
```
mcp__<MEMORY_PROVIDER>__store_memory(
  content="[OBS-MEM] <title>
Category: <category>
Machine: <machine>
Date: <YYYY-MM-DD>
Obsidian: <subdir>/<slug>.md
HV-ID: <hv_id>
Sensitive: <true|false>
Notion: <notion_url or "">
Summary: <first 150 chars>"
)
```

**4k. Counters:** `written++`, `processed++`.

### STEP 5 — Advance state

After the batch:
- Increment `last_offset` by batch size returned
- If `pagination.has_more == false`: set `done: true` for this category, reset `last_offset` to 0
- Update `total_*` sums
- Write updated state back to `STATE_FILE_PATH`

### STEP 6 — Report

```
[migrate-obs] Category: <cat> | offset: <old>→<new> | written: <n> | skipped: <n> | notion: <n> | total_written: <cumulative>
```

If category just completed: `[migrate-obs] Category <cat> DONE. Next: <next_category>`
If all done: `[migrate-obs] MIGRATION COMPLETE. Total written: <n>, skipped: <n>, promoted: <n>`

**Do not continue to the next category in the same run. One batch = one category = one run.**

### STEP 7 — Post-batch integrity check (optional)

If `INTEGRITY_CHECK_CMD` set:
```bash
$INTEGRITY_CHECK_CMD
```

Parse output and append to the report:
```
[migrate-obs] Integrity: obsidian=<N> qdrant=<N> divergence=<X>%
```

If divergence > 2%:
```
[migrate-obs] WARNING: Store divergence <X>% exceeds 2% threshold.
  This is expected during active migration. Re-vectorize migrated entries after migration completes.
```

**Non-fatal**: if the check fails, log a warning and continue.

## Notes

- Obsidian MCP paths are relative to `OBSIDIAN_VAULT_PATH`. Do NOT include the absolute path prefix in MCP calls.
- If `mcp__obsidian__write_file` fails for a specific memory, log the `hv_id` and skip — do not halt the batch.
- If Notion create fails, log and skip Notion — still write Obsidian file and `[OBS-MEM]` entry.
- The `global` category typically has the most entries; expect high skip rates. Batches run fast.
- Never write security or Vault files to Notion. Hard check before every `notion-create-pages` call.
- Run via cron: `0 * * * * /path/to/claude /migrate-memories-to-obsidian` (hourly, one category-batch per run, walks all categories over time).
