---
name: memory
description: Load and save context to hAIveMind. Provides quick /save and /load command primitives so the agent can write a memory entry or recall recent context without leaving the chat.
category: memory
runtimes: [claude]
pii_safe: true
---
# Memory Skill — Load/Save to hAIveMind

## Quick Commands

| Command | Action |
|---------|--------|
| `/save [content]` | Store to hAIveMind |
| `/load [id]` | Retrieve from hAIveMind |
| `/load:search query` | Search hAIveMind |
| `/read [id]` | Load memory (alias for /load) |

## Mapping

| Command | hAIveMind | Returns |
|---------|-----------|---------|
| `/save` | `store_memory` | memory ID |
| `/load` | `retrieve_memory` | memory content |
| `/load:search` | `search_memories` | memory list |
| `/read` | `retrieve_memory` | memory content |

## Usage

**Save to hAIveMind:**
```
/sav "checkpoint phase=complete" category="operations"
```

**Load memory:**
```
/load <UUID>
/read <UUID>  # same as /load
```

**Search hAIveMind:**
```
/load:search "<PROJECT_NAME> results"
```

## Examples

**Before task:**
```
/save "STARTING: analyze product readiness"
```

**Checkpoint:**
```
/save "CHECKPOINT phase=high" category="operations"
```

**Load previous:**
```
/load <UUID>
/read <UUID>   # same
```

---

**Relation:** /save = store_memory | /load = retrieve_memory | /read = /load (alias) | /load:search = search_memories
