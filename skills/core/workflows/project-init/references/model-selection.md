# Model Selection Rubric

Assign models to tasks based on complexity to optimize cost and quality.

## Rubric

| Complexity | Model | Account | Thinking | When to Use | Examples |
|-----------|-------|---------|----------|-------------|----------|
| **Simple** | `sonnet-low` | `unit-low` | Low | Docs, config, simple scripts, formatting | README updates, env var changes, linter fixes, copy edits |
| **Standard** | `sonnet-medium` | `unit-medium` | Medium | Most coding tasks, API changes, tests | New endpoints, unit tests, API integration, schema changes |
| **Complex** | `sonnet-high` | `unit-high` | High | Multi-file refactors, migrations, complex logic | DB migrations, auth system changes, multi-service refactors |
| **Deep** | `opus-high` | `max-high` | High | Architecture, security, complex planning | System design, threat modeling, cross-service architecture |
| **Max** | `opus-high` | `max-high` | High + explicit | Cross-system migrations, critical path, novel problems | Full stack rewrites, new protocol design, zero-to-one features |

## Decision Signals

Use these signals to determine complexity:

### → Simple (sonnet-low)
- Single file change
- No logic changes (just formatting, naming, docs)
- Config/env changes
- Copy or content updates
- Less than 20 lines of meaningful change

### → Standard (sonnet-medium)
- 1-3 files changed
- New function or endpoint (but within existing patterns)
- Adding tests for existing code
- API integration following established patterns
- Schema additions (not modifications)

### → Complex (sonnet-high)
- 4+ files changed
- Modifying existing patterns or architecture
- Database migrations with data transformation
- Multi-step refactors with dependencies
- Changes that touch both frontend and backend
- Anything with rollback concerns

### → Deep (opus-high)
- Architectural decisions needed
- Security-critical changes
- Cross-service coordination
- Performance-critical optimization
- Novel problem without existing patterns
- Trade-off analysis required

### → Max (opus-high + explicit thinking)
- Entire subsystem replacement
- Cross-system migration (e.g., TinyDB → Firestore)
- Changes affecting 10+ files with complex dependencies
- Critical path items where errors are costly
- Novel protocol or system design

## Account Routing

Two accounts are available:

| Account | Models | Use When |
|---------|--------|----------|
| `unit` | `unit-low`, `unit-medium`, `unit-high` | Default for all tasks. Sonnet-class models. |
| `max` | `max-low`, `max-medium`, `max-high` | When unit is unavailable, or for opus-class work. |

**Default:** Use `unit` account unless opus-class reasoning is needed or unit is unavailable.

**Planning phase:** Always uses `max-high` (opus) regardless of individual ticket complexity.

## Cost Awareness

- **sonnet-low** is ~10x cheaper than **opus-high**
- Default to the lowest sufficient model — upgrade only with justification
- A project with 10 tickets should typically be: 4-5 simple, 3-4 standard, 1-2 complex, 0-1 deep
- If most tickets land at "complex" or above, the project decomposition is too coarse — break tickets down further

## Thread Spawn Mapping

When spawning a sub-agent in a thread, map models to spawn commands:

```
sonnet-low    → /thread [name] --model unit-low
sonnet-medium → /thread [name] --model unit-medium  (or just /thread [name])
sonnet-high   → /thread [name] --model unit-high
opus-high     → /thread [name] --model max-high
```
