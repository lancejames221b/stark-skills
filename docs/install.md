# Installation Instructions

Install skills from `stark-skills` into your agent environment. All install scripts support `--dry-run`.

## Quick Start

```bash
# See what would be installed
./scripts/install-claude.sh --dry-run

# Install a specific skill into Claude skills dir
./scripts/install-claude.sh /path/to/skill-dir

# Install all (use with caution, forces overwrite)
./scripts/install-all.sh --claude --force

# Dry run for all agents
./scripts/install-all.sh --claude --pi --opencode --dry-run
```

## Agent-Specific Paths

| Agent    | Path (env var)           | Default                           |
| -------- | ------------------------ | --------------------------------- |
| Claude   | `$CLAUDE_SKILLS_DIR`     | `$HOME/.claude/skills`            |
| pi       | `$PI_SKILLS_DIR`         | `$HOME/.pi/agent/skills`          |
| OpenCode | `$OPENCODE_COMMANDS_DIR` | `$HOME/.config/opencode/commands` |

## Safety Behavior

All install scripts:

- Run dry-run by default when no skill is specified (prints what would happen).
- Backup existing destinations with `.bak.stark-skills` suffix.
- Never overwrite without `--force`.

## Tips for New Users

1. Start with a dry-run to see what would happen:

   ```bash
   ./scripts/install-all.sh --claude --pi --opencode --dry-run
   ```

2. Use `--force` sparingly — it replaces destination files without confirmation.

3. Check `.bak.stark-skills` backups after an install if something goes wrong.
