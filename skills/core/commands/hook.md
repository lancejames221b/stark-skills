---
description: Claude Code hook patterns guide — create event-driven hooks (PreToolUse, PreCompact, SessionStart, etc.) for automation, safety, and workflow. Use when designing hooks, automation, or event-driven workflows
argument-hint: "[hooks | pattern | template | event]"
---
# Claude Code Hook Patterns

This is a reference for Claude Code's hook system, mapped to use cases.

## Hook Events

| Event | When | Best For |
|-------|------|----------|
| PreToolUse | Before any tool runs | Safety gates, validation, access control |
| PostToolUse | After tool completes | Logging, auto-commit, notifications |
| Stop | Agent considers stopping | Completeness verification |
| SubagentStop | Subagent considers stopping | Quality gates for subagents |
| SessionStart | Session begins | Context injection, environment setup |
| SessionEnd | Session ends | Cleanup, state persistence |
| UserPromptSubmit | User enters prompt | Modify prompt, add context |
| PreCompact | Before compaction | Save checkpoint, preserve state |
| Notification | User notified | Log, react, forward |

## Patterns

### 1. PreToolUse Safety Gate
Block dangerous operations before they execute:
```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Is this bash command safe? Check for destructive operations (rm -rf /, database drops, mass deletes). Return approve or deny with reason."
        }
      ]
    }
  ]
}
```

### 2. PreCompact Checkpoint
Save session state before context compaction:
```json
{
  "PreCompact": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PROJECT_DIR}/hooks/precompact.sh"
        }
      ]
    }
  ]
}
```

### 3. Stop Verification
Verify task completion before stopping:
```json
{
  "Stop": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Is the task actually complete? Check: tests pass, build succeeds, no TODOs left, no broken imports. Return approve if done, block if not."
        }
      ]
    }
  ]
}
```

### 4. SessionStart Context Loading
Inject project context automatically:
```json
{
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PROJECT_DIR}/hooks/load-context.sh"
        }
      ]
    }
  ]
}
```

### 5. UserPromptSubmit Prompt Modification
Add context to user prompts:
```json
{
  "UserPromptSubmit": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PROJECT_DIR}/hooks/enrich-prompt.sh"
        }
      ]
    }
  ]
}
```

## Output Formats

### PreToolUse
```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow|deny|ask",
    "updatedInput": {"field": "modified_value"}
  },
  "systemMessage": "Reason for decision"
}
```

### Stop / SubagentStop
```json
{
  "decision": "approve|block",
  "reason": "Why approve or block",
  "systemMessage": "Additional context"
}
```

### General
```json
{
  "continue": true,
  "systemMessage": "Message for Claude"
}
```

## Best Practices

1. **Keep hooks fast** — complex logic degrades UX
2. **Fail open** — if a hook fails, don't block workflow
3. **Use prompt hooks for complex logic** — command hooks for fast checks
4. **Validate inputs** — always quote variables in command hooks
5. **Use ${CLAUDE_PLUGIN_ROOT}** for portable paths
6. **Consider parallel execution** — hooks run in parallel, don't depend on order
7. **Document hook behavior** — users should know what hooks run

## When to Use Hooks

- **Safety**: Block dangerous operations automatically
- **Validation**: Verify code quality before commits
- **Automation**: Auto-run linter, formatter, tests
- **Context**: Inject project rules, conventions
- **Checkpointing**: Save state before compaction
- **Logging**: Record tool usage, decisions, outcomes
