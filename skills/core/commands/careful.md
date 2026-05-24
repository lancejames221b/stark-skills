---
description: Careful coding — slow down and verify before making changes. Use when working on critical code, bug fixes, or when asked to be careful
argument-hint: "[<description>]"
---
# Careful Coding

Before making any code change, follow this process:

## 1. Understand
- Read the relevant file(s) fully — don't skim
- Understand the current behavior (not what you think it does)
- Identify the exact failure point

## 2. Plan
- What exactly needs to change? (specify file + line)
- What are the side effects? (other files, APIs, DB)
- What tests verify this? (existing + new)

## 3. Verify Before
- Run `npx tsc --noEmit` baseline — does it compile?
- Run `npm run test:run` baseline — do tests pass?
- Document current state: "This is working. After my change, X will be Y."

## 4. Execute
Make ONE change at a time. Verify after each.

## 5. Verify After
- `npx tsc --noEmit` — does it still compile?
- `npm run test:run` — do tests still pass?
- Manual check: does the bug actually fix?

## Checklist
- [ ] I understand what the current code does
- [ ] I know what will break
- [ ] I've verified baseline compiles and tests pass
- [ ] I've verified post-change compiles and tests pass
- [ ] No debug statements left behind

## Golden Rule
**"Evidence before claims."** — Don't say something works until you've checked it.
