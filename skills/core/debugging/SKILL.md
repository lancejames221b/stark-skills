---
name: debugging
description: Deep static analysis and bug hunting for any codebase.
category: debugging
runtimes: [claude]
pii_safe: true
---
# Bug Hunt Agent

## Purpose
Deep static analysis and bug hunting for any codebase. Finds real bugs, not just pattern matches.

## Operating Mode
When invoked, scan the entire codebase systematically. Run as a single agent session.

## Method

### Phase 1: Reconnaissance (30s)
- Read `package.json` / `go.mod` / `Cargo.toml` to identify the stack
- Find entry points: `server/index.ts`, `main.go`, `src/App.tsx`, etc.
- Read the root config files (tsconfig, vite, docker, etc.)
- Map the directory structure at top level

### Phase 2: Static Analysis — Read Every File
Go file-by-file through source code. For each file check:

**Type Safety:**
- Missing `await` on async calls
- Type coercion (`string` vs `number`, implicit `any`)
- Unused imports/variables
- Missing `as` casts that hide type errors

**Logic Errors:**
- Wrong state transitions (e.g., allowing `paid → claimed`)
- Off-by-one errors in loops/ranges
- Missing null checks before property access
- Race conditions (reading then writing without locking)
- Stale closures in event handlers / useEffect / setTimeout

**Security:**
- Hardcoded secrets / API keys / passwords
- Missing auth checks on routes that should have them
- SQL injection via string concatenation (not parameterized)
- Unvalidated user input reaching DB/query layer
- `eval()`, `new Function()`, template literals with user data

**Error Handling:**
- Empty catch blocks
- Swallowed errors (catch then nothing)
- Missing error handling on async functions
- 500 responses that expose stack traces in production

**Resource Management:**
- Memory leaks (unclosed connections, missing cleanup)
- File descriptors not closed
- Unbounded arrays/collections growing forever

### Phase 3: Cross-Reference Checks
- Every API route → check: auth guard? input validation? error handling?
- Every DB query → check: field names match schema? proper types?
- Every event/callback → check: handler exists? cleanup on unmount?
- Every config/env var → check: fallbacks? defaults?

### Phase 4: Runtime Testing
- Start the server
- Hit every endpoint with curl
- Test auth enforcement (unauthorized access)
- Test edge cases (empty bodies, wrong types)
- Check error responses are clean (no stack traces)

### Phase 5: Report
Output a structured report:

```
## Bug Hunt Report

### 🐛 Bugs (must fix)
- **File:Line** — Description
  Cause: ...
  Fix: ...

### ⚠️ Warnings (should fix)
- ...

### ℹ️ Info (ok)
- ...

### Score: X/10
```

## Priority
BUG > WARNING > INFO. Only report things that are actually wrong, not style preferences.

## Scope
- Scan the entire project, not just "new" files
- Check existing code for bugs too
- Focus on runtime-breaking issues first
- Then security issues
- Then correctness edge cases
- Then minor improvements
