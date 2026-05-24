---
name: haivemind-remember
description: Store and recall information in hAIveMind using natural-language requests. Use when the user says things like "remember this", "save this", "don’t forget", "recall", "what do you remember", or asks to retrieve prior decisions, context, or notes.
category: memory
runtimes: [claude]
pii_safe: true
---

# hAIveMind Remember

Use hAIveMind as the default memory system.

## Rules

- Treat "memory" as hAIveMind.
- Use `mcporter call haivemind.store_memory` to save information.
- Use `mcporter call haivemind.search_memories` to recall information.
- Prefer channel-scoped recall first: include the channel ID or project name in search queries.
- Never invent recalled facts; if nothing is found, say so clearly.

## Intent Mapping (Natural Language)

### Save intent
Trigger on phrases like:
- remember this
- save this
- keep this in memory
- don’t forget
- note that

Action:
1. Extract the core fact in one concise sentence.
2. Store with category:
   - `rules` for preferences/policies
   - `global` for general facts/decisions
   - `operations` for active workflows/status
3. Confirm what was saved.

Template:
```bash
mcporter call haivemind.store_memory \
  content="[channel-or-project] [concise fact]" \
  category="[rules|global|operations]"
```

### Recall intent
Trigger on phrases like:
- recall
- what do you remember about X
- check memory for X
- did we decide X

Action:
1. Search with specific query terms (topic + channel/project when known).
2. If needed, run a second narrowed query.
3. Return only relevant results as plain summary bullets.

Template:
```bash
mcporter call haivemind.search_memories query="[topic + channel/project]" limit=10
```

## Response Style

- Be brief and direct.
- For saves: "Saved to hAIveMind: …"
- For recalls: "From hAIveMind: …"
- If uncertain: "I checked hAIveMind and didn’t find a reliable match."
