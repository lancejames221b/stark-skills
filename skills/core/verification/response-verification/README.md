# Response Verification

**Prevent incomplete or inaccurate responses by enforcing verification patterns.**

## The Problem

AI agents often make incomplete claims from memory:
- "Seattle has appeared in 3 Super Bowls" (wrong - actually 4)
- "They won twice" (incomplete - doesn't mention losses)
- "First time ever" (without verifying it's truly first)

These errors happen because:
1. Search scope is too narrow (search "wins" not "complete history")
2. First result accepted without verification
3. Math not cross-checked (wins + losses should = total appearances)
4. Memory used instead of tools

## The Solution

This skill enforces 5 verification patterns:
1. **Two-Query Rule** - Search specific answer AND complete timeline
2. **Timeline Verification** - Cross-reference dates and context
3. **Record Claims** - Explicitly verify first/last/only assertions
4. **Comparison/Head-to-Head** - Get full series record
5. **Sanity Check** - Math check, red flags, completeness

## Example

**Without this skill:**
> Q: How many times has Seattle won the Super Bowl?
> A: "Two times. They've appeared in 3 Super Bowls total."
> ❌ Wrong - actually 4 appearances

**With this skill:**
> Q: How many times has Seattle won the Super Bowl?
> 
> 🔍 Response Verification Check
> - Query 1: "Seattle Seahawks Super Bowl wins" → 2
> - Query 2: "Seattle Seahawks complete Super Bowl history" → 4 appearances
> - Math: 2 wins + 2 losses = 4 ✓
> 
> A: "Two times. Complete record: 4 appearances, 2 wins, 2 losses (2006 vs Steelers, 2014 vs Broncos ✓, 2015 vs Patriots, 2026 vs Patriots ✓)."
> ✅ Correct and complete

## When to Use

Auto-trigger on:
- Sports/competition records
- Historical timelines
- Definitive counts
- First/last/only claims
- Record comparisons

Manual trigger:
- Before making definitive historical/statistical claims
- When you notice yourself about to state a count from memory
- After initial search, before composing final response

## Installation

```bash
# Already installed if you're reading this
# To use: just follow the patterns in SKILL.md before answering historical/statistical questions
```

## Origin

Created Feb 8, 2026 after incorrectly stating Seattle had "appeared in 3 Super Bowls" when it was actually 4. Root cause: searched for "wins" but not "complete history", accepted first result without verification.

## Related Skills

- `fact-checker` - Verifies external claims (complements this)
- `verify-claims` - Uses professional fact-checkers (complements this)
- `deep-research` - Comprehensive research (this is quick verification)

This skill is about verifying YOUR OWN responses, not external content.
