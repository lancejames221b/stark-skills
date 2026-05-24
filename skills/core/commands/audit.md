---
description: Security audit — scan for hardcoded secrets, missing auth, SQL injection, unsafe patterns. Follow the bug-hunt methodology adapted for security focus
argument-hint: "[scope]"
---
## Security Audit

Systematically scan the codebase for security issues using the bug-hunt methodology:

### Phase 1: Reconnaissance
- Read `package.json` for deps (check for known vulns: express version, dotenv, JWT)
- Identify entry points and auth routes
- Find any `.env` files or hardcoded credentials

### Phase 2: Scan Patterns
Check every file for:

**Secrets & Credentials:**
- Hardcoded API keys, passwords, JWT secrets
- `.env` files checked into version control
- Tokens in comments or string literals
- API endpoints with embedded credentials

**Auth & Authorization:**
- Routes missing authentication guards
- Missing role-based access checks
- IDOR (insecure direct object references) — can user B modify user A's data?
- Default/missing auth on admin endpoints
- JWT verification bypass (missing/expired tokens)

**Input Validation:**
- SQL injection (string concatenation in queries)
- XSS (unsanitized user input in JSX)
- Command injection (user input in shell commands)
- Missing input validation on API endpoints

**Data Exposure:**
- Sensitive data in logs (passwords, PII, tokens)
- Over-fetching in API responses (returning all fields)
- Missing rate limiting on auth endpoints

**Error Handling:**
- Stack traces in production error responses
- Unhandled promise rejections
- Empty catch blocks

### Phase 3: Report
Output a structured report:

```
## Security Audit: <project-name>

### Critical (fix immediately)
- **File:Line** — Issue
  Impact: ...
  Fix: ...

### High (fix soon)
- ...

### Medium
- ...

### Low / Info
- ...
```

### Severity Levels
- **Critical**: Remote code execution, credential leak, auth bypass
- **High**: SQL injection, XSS, missing auth, IDOR
- **Medium**: Error info disclosure, over-fetching, missing rate limit
- **Low**: Logging PII, minor validation gaps
