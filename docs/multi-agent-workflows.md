# Multi-Agent Workflow Patterns

Common end-to-end procedures that combine multiple skills.

## 1. Plan → Implement → Verify → Review → Handoff

**Flow:** planner sketches phases and gates → implementer executes → verifier checks each gate → reviewer does final pass → handoff to next agent or owner.

**Skills used:** planning, execution/verification-before-completion, review, handoff.
**Placeholders:** `<PLAN_AGENT>`, `<IMPLEMENTER_AGENT>`, `<VERIFIER_AGENT>`.

## 2. Research → Plan → Review

**Flow:** researcher gathers facts and citations across multiple sources → planner converts findings into phased plan with dependencies → peer reviewer validates assumptions, gaps, and verification gates.

**Skills used:** research, planning (eng-review, design-review), review.
**Placeholders:** `<RESEARCH_AGENT>`, `<PLANNER_AGENT>`, `<REVIEWER_AGENT>`.

## 3. Bug-Hunt → Fix → Verify

**Flow:** bug-hunter collects evidence and ranks findings by severity → fixer implements targeted changes with minimal scope creep → verifier re-runs the full validation suite and checks for regression.

**Skills used:** bug-hunt, fixer (execution skill), verification-before-completion (full suite re-run).

## 4. Incident Response

**Flow:** triage evidence → assessment of severity and impact → mitigation plan (temporary fix + root cause) → execute with handoff chain → post-incident review.

**Skills used:** investigation-method, planning (execution), handoff, review.
**Placeholders:** `<TRIAGE_AGENT>`, `<MITIGATOR_AGENT>`, `<POSTMORTEM_LEAD_AGENT>`.

## 5. Release Workflow

**Flow:** feature freeze → integration verification (tests, lints) → changelog update → release description → deployment with rollback plan → post-release verification.

**Skills used:** verification-before-completion (full suite), review, handoff.

## Handoff Convention

Every handoff must include:

- Current state (what's working, what isn't)
- Files changed with intent summary
- Tests run and results
- Remaining blockers (with severity)
- Next 2–3 actions with expected outcomes

## Task and State Management

When using the pi todo tool across agents:

- Use `todo` for phases, `stark-skills` for persistent state.
- Always run verification before marking progress as complete.

## Memory Guidelines

- Save durable facts in pi memory; load at session start for context.
- Warn when relying on memory (may be stale).

## General Rules

1. Work one issue at a time unless explicitly parallel work is needed.
2. Link commits and PRs back to their issue numbers.
3. Run verification before claiming success on any agent or tool.
