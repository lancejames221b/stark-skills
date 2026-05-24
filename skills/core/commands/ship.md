---
description: Ship checklist — verify everything before deploying or claiming work is done. Use when asked to "ship", "deploy", "release", "go live", "publish", or "finalize"
argument-hint: "[version | target | environment]"
---
# Ship Checklist

Before shipping, verify:

## Build
- [ ] `npx tsc --noEmit` — frontend passes
- [ ] `npx tsc -p server/tsconfig.json --noEmit` — server passes
- [ ] `npm run build` — full build succeeds
- [ ] `npx tsc --noEmit` + `npx tsc -p server/tsconfig.json --noEmit` — both clean

## Tests
- [ ] `npm run test:run` — all tests pass
- [ ] New tests added for new logic
- [ ] No skipped tests

## Code Review
- [ ] All TODO/FIXME comments resolved (or purposefully left with rationale)
- [ ] No debug `console.log` statements
- [ ] No dead code
- [ ] No hardcoded credentials or secrets
- [ ] Error handling covers all async paths

## Documentation
- [ ] `AGENTS.md` updated if architecture changed
- [ ] `PLAN.md` updated if scope changed
- [ ] Comments on public APIs match implementation
- [ ] Changelog updated (if applicable)

## Pre-Deploy
- [ ] Database migration is safe (rollback possible, data preserved)
- [ ] Server config matches target (env vars, CORS, ports)
- [ ] CORS settings correct for target domain
- [ ] Rate limiting enabled (production)

## Post-Deploy Verification
- [ ] Health check passes: `curl http://localhost:3001/health`
- [ ] Auth endpoint works: `curl -X POST http://localhost:3001/api/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"test123","name":"Test"}'`
- [ ] Frontend loads: `curl http://localhost:3000`
- [ ] Key user flows work (register → login → core action)

## Commit Before Ship
```bash
git add -A
git commit -m "chore: prepare for release vX.Y.Z"
```
