# Bootstrap Condenser Skill

Automatically maintains SOUL.md and AGENTS.md under 20KB while preserving 100% fidelity.

## Quick Start

Check current sizes:
```bash
python3 scripts/condense_bootstrap.py --check
```

Preview changes:
```bash
python3 scripts/condense_bootstrap.py --dry-run
```

Apply condensing:
```bash
python3 scripts/condense_bootstrap.py
```

## What It Does

- Removes redundant whitespace
- Condenses verbose explanations → terse equivalents
- Tightens code examples (preserves functionality)
- Consolidates repetitive content
- Keeps ALL critical rules, commands, and patterns

## Current Status

After initial run (Feb 11, 2026):
- ✓ SOUL.md: 10,414 bytes (was 20,982) — 50% reduction
- ✓ AGENTS.md: 15,186 bytes (was 20,680) — 26% reduction
- ✓ Both files under 20KB limit
- ✓ All critical content preserved

## Maintenance

Run monthly or when files approach 20KB:
```bash
python3 scripts/condense_bootstrap.py
```

See SKILL.md for full documentation.
