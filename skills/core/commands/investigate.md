---
description: Systematic investigation — find root cause of bugs, errors, or unusual behavior. Use when asked to "investigate", "debug", "find root cause", "why is X happening", "something's wrong with"
argument-hint: "[<description>]"
---
# Investigation Method

Systematic approach to finding and documenting root causes.

## Process

### Phase 1: Reproduce
- What exactly is happening? (observed behavior)
- What should happen? (expected behavior)
- How to reproduce? (steps + commands)
- When first noticed? (recent changes)

### Phase 2: Isolate
- Which component is failing? (frontend, backend, DB, network)
- Is it reproducible? (100% of time, intermittent, conditional)
- What changed recently? (git log, recent commits)
- What's the minimal reproduction? (smallest case that fails)

### Phase 3: Diagnose
For each suspect:
1. **Add logging** — print state at key points
2. **Check error messages** — read them literally, not inferentially
3. **Check logs** — server logs, browser console, DB logs
4. **Check diffs** — `git diff` for the specific change
5. **Check types** — runtime types vs expected types

### Phase 4: Root Cause
Document found issue:

```
## Root Cause: <description>

**What:** <What actually happens>
**Expected:** <What should happen>
**Why:** <The actual code/logic error>
**Location:** file.ts:line

### Evidence
- Log output showing the issue
- Stack trace
- Diff showing the regression

### Fix
<Code change that resolves it>
```

### Phase 5: Verify
- Reproduce fails before fix
- Reproduce passes after fix
- No regressions in related features

## Common Investigation Patterns

**Frontend crash:** Check browser console → React DevTools → component source → props/hook inputs
**API 404:** Check route registration → middleware chain → handler function → response body
**API 500:** Check server logs → handler source → DB query → error handling
**DB issue:** Check schema → actual data → Prisma query → migration status
**Auth failure:** Check JWT → check route guard → check user session → check DB data
**Build error:** Read error message literally → check file referenced → check import chain
