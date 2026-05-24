---
name: bootstrap-condenser
description: Maintain SOUL.md and AGENTS.md under 20KB by condensing content while preserving all critical rules, patterns, and workflows. Use when bootstrap files exceed size limits or need maintenance. Checks file sizes, applies intelligent condensing patterns, and verifies no fidelity loss.
category: workflows
runtimes: [claude]
pii_safe: true
---

# Bootstrap File Condenser

Keeps SOUL.md and AGENTS.md under 20KB while preserving 100% fidelity.

## Problem

Bootstrap files (SOUL.md, AGENTS.md) are loaded on every session start. <PROJECT_NAME> has a 20KB limit per file - anything larger gets truncated, causing:
- Loss of critical rules and patterns
- Context corruption in long sessions
- Tool awareness loss after compaction

## Solution

Intelligently condense files by:
- Removing redundant whitespace and blank lines
- Condensing verbose explanations → terse equivalents
- Tightening code examples (preserve functionality)
- Consolidating repetitive content
- Shortening long command examples

**Zero fidelity loss** - all rules, commands, patterns, and workflows preserved.

## Usage

### Check sizes
```bash
python scripts/condense_bootstrap.py --check
```

### Condense files (dry run)
```bash
python scripts/condense_bootstrap.py --dry-run
```

### Condense and save
```bash
python scripts/condense_bootstrap.py
```

### Target specific file
```bash
python scripts/condense_bootstrap.py --file SOUL.md
python scripts/condense_bootstrap.py --file AGENTS.md
```

## What Gets Condensed

**Safe patterns (always applied):**
- Multiple blank lines → single blank line
- Trailing whitespace removed
- Verbose phrases → terse equivalents ("When you" → "When", "This is" → "")
- Long examples → minimal working examples
- Repetitive explanations → single reference

**Preserved (never touched):**
- All tool commands (exact syntax)
- All non-negotiable rules
- All security policies
- All workflow patterns
- All origin dates/context
- All channel IDs and paths

## Condensing Patterns

See `references/condensing-patterns.md` for full list of safe transformations.

## Output

Shows:
- Original size
- New size
- Bytes saved
- Percentage reduction
- Verification that all critical content preserved

## When to Run

- Before file hits 20KB (proactive)
- After adding new sections
- Monthly maintenance
- After multiple edits accumulate verbosity

## Integration

Can be run as:
- Manual command
- Git pre-commit hook
- Cron job (monthly)
- Part of skill update workflow
