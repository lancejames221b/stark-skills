---
name: adapter-name
description: Maps canonical skill <SKILL_NAME> to <AGENT>.
canonical_skill_path: ../skills/core/<skill-folder>/SKILL.md
agent: claude | pi | opencode
dependencies: []
pii_safe: true
---

# <AGENT> Adapter for <SKILL_NAME>

## Agent-Specific Setup

Add this skill path to the `<AGENT>` configuration:

- Claude: `$HOME/.claude/skills/<adapter-folder>/`
- pi: `$HOME/.pi/agent/skills/<adapter-folder>/`
- OpenCode: `$HOME/.config/opencode/commands/<command-name>.md`

## Agent-Specific Behavior

Document agent-specific behavior, tool usage, or command syntax.
Keep canonical logic in the skill.md and adapt only what's agent-specific here.

## Redaction Notes

List any redacted values or configuration placeholders used in this adapter.
