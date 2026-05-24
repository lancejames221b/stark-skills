---
description: Code guard — validate code quality, catch common mistakes before committing. Run before any write/edit operation or commit to prevent regressions
argument-hint: "[files | --all | --scope <component>]"
---
# Code Guard

Lightweight pre-commit validation. Run before committing or claiming work is done.

## Checks

When invoked, scan specified files (or all changed files) and check:

### Type Safety
- All props/interfaces have proper types (no `any`)
- No implicit `any` from missing return types
- Proper null checks (optional chains `?.` for nullable values)

### Common Mistakes
- Missing `await` on async calls
- Empty catch blocks
- `console.log` in non-debug code
- `TODO:`, `FIXME:` comments that aren't tracked

### Security
- No hardcoded secrets
- Auth guards present on protected routes
- Input validated before DB operations
- No raw SQL string concatenation

### React Specific
- No state mutations (spread copies for updates)
- `useEffect` cleanup functions for timers/subscriptions
- No prop drilling beyond 3 levels (suggest context or atom)

### Export Check
- Named exports match usage
- Default exports are actually used
- No circular dependencies in imports

## Output

```
## Code Guard: <project>

### ✅ Passed
- file1.ts — Types correct, no issues
- file2.ts — Clean

### ⚠️ Issues (fix before commit)
- file3.ts:line — missing await on fetch()
  Fix: add `await` prefix

### ❌ Failures (block commit)
- file4.ts — hardcoded JWT secret!
  Fix: move to env var

### Summary: 8/10 — minor issues can be fixed after commit
```
