---
description: Plan review — break work into executable phases with dependencies, priorities, and verification gates
argument-hint: "[scope] [constraints]"
---
## Plan Review

Review the current work and produce a structured, phased plan. Follow this process:

### 1. Current State Assessment
- Read the codebase structure: `package.json`, key config files, main entry points
- Identify what's working, what's broken, what's stubbed
- Note file count, test count, key dependencies

### 2. Phase Decomposition
Break work into phases. Each phase must have:
- Clear scope (what in, what out)
- Dependencies on other phases
- Priority (must-have / nice-to-have / stretch)
- Verification criteria (how do we know it's done)

### 3. Risk Analysis
For each phase, identify:
- Potential blockers
- Unknown risks
- Rollback / undo path

### 4. Execution Order
Output a table:

| Phase | Scope | Depends On | Priority | Verified By |
|-------|-------|------------|----------|-------------|
| 1     | ...   | —          | high     | tests + manual |

### 5. File Targets
List specific files and line ranges that will be touched:
```
Phase A: Edit src/context/AuthContext.tsx (lines 15-40)
         Add server/lib/auth.ts (new)
         Wire up client/api.ts (lines 50-80)
```

Output the final plan as a markdown file saved to the project.
