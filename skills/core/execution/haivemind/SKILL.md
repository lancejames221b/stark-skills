---
name: haivemind
description: Access hAIveMind memory system via MCP tools for search and storage
category: execution
runtimes: [claude]
pii_safe: true
---
# hAIveMind — MCP Integration

This skill provides access to hAIveMind's memory system via the mcporter MCP interface.

## Available Tools

### haivemind MCP Server
- **Search**: `mcporter call haivemind.search_memories query='[topic]' limit=10`
- **Store**: `mcporter call haivemind.store_memory content='[context]' category='[category}'`

## Categories

- `global`: General workspace context and permanent knowledge
- `operations`: Active tasks, workflows, and status updates
- `rules`: Important rules, policies, and preferences
- `infrastructure`: System configuration and setup notes

## Usage Pattern

**Before starting work:**
```bash
mcporter call haivemind.search_memories query='[topic] [channel-id]' limit=10
```

**After completing work:**
```bash
mcporter call haivemind.store_memory content='[summary]' category='operations'
```

## Notes

- Channel-specific context: include `[channel-id]` in search queries
- Always search before working to avoid duplicating previous efforts
- Store key decisions, context, and findings for future sessions
