---
description: Code review — systematic review of staged or specified changes focusing on correctness, security, and maintainability
argument-hint: "[files | --all | --pr N]"
---
Code Review — Systematic review of changes following the bug-hunt methodology.

## Review Process

### Step 1: Understand Scope
```bash
git diff --name-only --cached
# or for uncommitted:
git diff --name-only
```

### Step 2: Read Changes
For each changed file:
```bash
git diff HEAD -- <file>
```

Read the full diff. Understand:
- What changed and why
- Affected dependencies
- Potential cascade effects

### Step 3: Checklist
Review against:

**Correctness:**
- [ ] Logic works for edge cases (empty input, null, zero, large input)
- [ ] State transitions are correct (no invalid states)
- [ ] Error handling covers all failure paths
- [ ] No stale state or race conditions

**Security:**
- [ ] No hardcoded secrets
- [ ] Auth/authorization checks present
- [ ] Input validated and sanitized
- [ ] SQL injection impossible (parameterized queries)
- [ ] XSS impossible (proper escaping)

**Performance:**
- [ ] No unnecessary re-renders
- [ ] DB queries use indexes
- [ ] No N+1 query patterns
- [ ] Large data paginated

**Maintainability:**
- [ ] Code follows project conventions (see AGENTS.md)
- [ ] Naming is clear and consistent
- [ ] Functions have single responsibility
- [ ] Tests cover new logic

**Tests:**
- [ ] New tests for new logic
- [ ] Existing tests still pass
- [ ] Edge cases tested

### Step 4: Report
Output:

```
## Code Review: <summary>

### ✅ Good
- Pattern or change that works well

### ❌ Issues (must fix)
- **File:Line** — Issue
  Fix: ...

### ⚠️ Suggestions (should fix)
- ...

### ℹ️ Notes
- ...
```

### Severity
- **Must fix**: Breaks functionality, security risk, causes test failures
- **Should fix**: Poor performance, awkward API, technical debt
- **Nice to have**: Style, naming, documentation
