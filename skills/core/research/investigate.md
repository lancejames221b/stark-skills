# Investigation Method - Root Cause Analysis

**Purpose**: Systematic approach to finding and documenting root causes of issues

**Type**: Debugging & Troubleshooting

**Trigger Phrases**: 
- `investigation`
- `/investigation`
- `root cause`
- `debug method`
- `troubleshoot`

---

## When to Use

- **Frontend crashes** — Check browser console, React DevTools
- **API 404/500 errors** — Check routes, logs, error handlers
- **Database issues** — Check schema, migrations, data integrity
- **Authentication failures** — Check JWT, guards, sessions
- **Build errors** — Read error messages literally
- **Performance issues** — Profile bottlenecks
- **Unexpected behavior** — Investigate systematically
- **Regression issues** — Check recent changes

---

## The 5-Phase Process

### Phase 1: Reproduce
```
Current state:
• What exactly is happening? (Observed behavior)
• What should happen? (Expected behavior) 
• How to reproduce? (Steps + commands)
• When first noticed? (Recent changes context)
```

### Phase 2: Isolate
```
Current state:
• Which component is failing? (frontend, backend, DB, network)
• Is it reproducible? (100%, intermittent, conditional)
• What changed recently? (git log, recent commits)
• What's the minimal reproduction? (smallest failing case)
```

### Phase 3: Diagnose
For each suspect, systematically check:

```
1. Add logging — print state at key points
2. Check error messages — read literally, not inferentially  
3. Check logs — server, browser, DB
4. Check diffs — git diff for specific changes
5. Check types — runtime vs expected types
```

### Phase 4: Root Cause

Document precisely:
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
```
✓ Reproduce fails before fix
✓ Reproduce passes after fix
✓ No regressions in related features
```

---

## Common Investigation Patterns

**Frontend crash:**
```
1. Check browser console for errors
2. Review React DevTools component tree
3. Check component source for bugs
4. Inspect props/hook inputs
5. Look for state mutation
```

**API 404:**
```
1. Verify route registration
2. Check middleware chain ordering  
3. Review handler function source
4. Inspect response body
5. Check URL matching patterns
```

**API 500:**
```
1. Check server logs for errors
2. Inspect handler function
3. Review DB query for bugs
4. Check error handling middleware
5. Examine input validation
```

**DB issue:**
```
1. Validate schema definitions
2. Check actual data vs expected
3. Test Prisma/EQL queries
4. Review migration status
5. Check constraints and indexes
```

**Auth failure:**
```
1. Verify JWT token generation/validation
2. Check route guards and middleware
3. Review user session management
4. Validate DB user data integrity
5. Check expiration times
```

**Build error:**
```
1. Read error message literally
2. Check the file referenced
3. Trace import/export chains
4. Check TypeScript type definitions
5. Verify dependency versions
```

---

## Investigation Checklist

**Before diving in:**
- [ ] What's the actual issue?
- [ ] What should work?
- [ ] Can I reproduce it?
- [ ] When did it start?

**During investigation:**
- [ ] Added logging at key points?
- [ ] Read error messages literally?
- [ ] Checked all relevant logs?
- [ ] Reviewed recent changes with `git diff`?
- [ ] Validated types and data structures?

**After fix:**
- [ ] Reproduces before fix? ❌
- [ ] Reproduces after fix? ✅
- [ ] No regressions introduced?
- [ ] Root cause documented?
- [ ] Solution explained to team?

---

## Debugging Ethics

**Always:**
- Document exactly what happened
- Provide reproduction steps
- Show evidence (logs, diffs, traces)
- Verify fix prevents regression
- Share lessons learned

**Never:**
- Assume what's happening
- Guess at error causes
- Skip thorough investigation
- Patch symptoms without root cause
- Claim "it works now"

---

## Quick Reference

### Investigation Protocol
```
1. Reproduce → Isolate → Diagnose → Root Cause → Verify
```

### Primary Debugging Rules
- Read error messages literally
- Trust data over assumptions
- Check logs before guessing
- Use `git diff` for context
- Add logging before fixing

### Common Debugging Patterns
```
Frontend → Console → DevTools → Source → Props/Input
Backend → Routes → Middleware → Handler → DB
DB → Schema → Data → Query → Constraints
```

---

## Skill Usage Example

```
User: investigation method 
Assistant: 
> Analyzing issue systematically
> 
> [PHASE 1: Reproduce]
> ✓ Issue: Login fails on mobile
> ✓ Expected: Login succeeds
> ✓ Steps: Tap login button → Network request → Error
> 
> [PHASE 2: Isolate]  
> ✓ Component: Authentication backend
> ✓ Repeatability: 100%
> ✓ Recent change: Updated auth token
> ✓ Minimal case: Login form submission
> 
> [PHASE 3: Diagnose]
> ✓ Added logging before API call
> ✓ Checked server logs: Token validation error
> ✓ Checked diffs: Auth token format changed
> ✓ Validated types: JWT now requires exp claim
> 
> [PHASE 4: Root Cause]
> ## Root Cause: Auth token missing expiration claim
> 
> **What:** Login fails with 401 Unauthorized
> **Expected:** Login with valid credentials succeeds
> **Why:** Token format changed to require exp claim, but didn't update client generation
> **Location:** src/auth/token.js:42
> 
> ### Evidence
> Log: "Error validating token: Missing 'exp' claim"
> Diff: "auth-token-generation.js updated to include exp, but client still uses old signature"
> 
> ### Fix
> Update client token generation to include exp claim
> 
> [PHASE 5: Verify]
> ✓ Reproduce before fix: ❌ (login fails)
> ✓ Reproduce after fix: ✅ (login succeeds)
> ✓ No regressions: ✅ (other auth routes work)
```