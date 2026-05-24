---
name: skill-name
description: One-sentence trigger and purpose.
category: planning|verification|memory|voice|integration|...
runtimes: [claude, pi, opencode]
dependencies: []
pii_safe: true
---

# Skill Name

## When to Use

Describe the situation or intent that should trigger this skill.

## Inputs

List expected inputs (user prompt, files, context).

## Procedure

Step-by-step instructions the agent should follow. Each step starts with a verb. Use imperative tone for clarity.

## Verification

What checks the agent should run before claiming success. Include commands, outputs to validate, or tests to execute.

## Output Format

Expected output format and any formatting rules (concise for voice, structured for text).

## Runtime Notes

Agent-specific behavior:

- Claude: Frontmatter and command flags.
- pi: Tool usage notes.
- OpenCode: Command syntax.

## Redaction Notes

List redacted values and their placeholders so auditors know what was stripped.
