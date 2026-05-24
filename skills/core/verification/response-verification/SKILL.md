---
name: response-verification
description: Prevent incomplete or inaccurate responses by enforcing verification patterns for historical facts, statistics, and definitive claims. Use when answering questions about records, timelines, or counts to ensure completeness.
category: verification
runtimes: [claude]
pii_safe: true
---

# Response Verification - Anti-Hallucination for Your Own Answers

Enforce verification patterns to prevent incomplete or inaccurate responses before sending them.

## When to Use

**Auto-trigger on these question types:**
- Sports/competition records ("How many times did X win/lose?")
- Historical timelines ("When did X happen?")
- Definitive counts ("How many X are there?")
- Record comparisons ("X vs Y history")
- "First/last/only" claims ("Was this the first time?")

**Manual trigger:**
- Before making any definitive historical/statistical claim
- When you notice yourself about to say "X times" or "appeared in Y"
- After initial search, before composing response

## Core Principle

**Never answer from memory alone.** Always verify with tools, even if you think you know.

## Verification Patterns

### Pattern 1: Two-Query Rule (Sports/Competition History)

**Question format:** "How many times did X win Y?"

**Process:**
1. **Query 1 - Specific Answer:**
   ```
   web_search: "[X] [Y] wins total"
   ```
   Extract: Number of wins

2. **Query 2 - Complete Timeline:**
   ```
   web_search: "[X] [Y] complete history all appearances"
   ```
   Extract: All appearances (wins + losses)

3. **Cross-Check Math:**
   ```
   wins + losses = total appearances
   ```
   If math doesn't work, search again

4. **Response Format:**
   ```
   [X times] (answer to question asked)
   
   Complete history:
   - [Year]: [Result]
   - [Year]: [Result]
   Total: [X] wins, [Y] losses, [Z] appearances
   ```

**Example:**
- Question: "How many times has Seattle won the Super Bowl?"
- Query 1: "Seattle Seahawks Super Bowl wins" → Answer: 2
- Query 2: "Seattle Seahawks Super Bowl complete history all appearances" → Check: 4 total
- Math: 2 wins + 2 losses = 4 appearances ✓
- Response: "Two times. Complete history: 2006 (loss), 2014 (win), 2015 (loss), 2026 (win). Total: 2 wins, 2 losses, 4 appearances."

### Pattern 2: Timeline Verification (Historical Events)

**Question format:** "When did X happen?" or "Did X happen before/after Y?"

**Process:**
1. **Query 1 - Direct Event:**
   ```
   web_search: "[exact event] date when"
   ```

2. **Query 2 - Surrounding Context:**
   ```
   web_search: "[event] timeline before after [related events]"
   ```

3. **Cross-Reference:**
   - Verify dates from multiple sources
   - Check for "first time", "last time", "only time" qualifiers

4. **Response Format:**
   ```
   [Direct answer to question]
   
   Context: [Related events/timeline if relevant]
   ```

### Pattern 3: Record Claims (First/Last/Only)

**Question format:** "Was this the first/last/only time X did Y?"

**Process:**
1. **Query 1 - Claimed Event:**
   ```
   web_search: "[X] [Y] [year/details]"
   ```

2. **Query 2 - All Occurrences:**
   ```
   web_search: "[X] [Y] complete list all times history"
   ```

3. **Explicit Verification:**
   - Count occurrences from search results
   - Check for "previous times" or "subsequent times" mentions

4. **Response Format:**
   ```
   [Yes/No with qualifier]
   
   [List of all occurrences if more than one]
   ```

**Example:**
- Question: "Is this Seattle's first Super Bowl win?"
- Query 1: "Seattle Seahawks Super Bowl 2026 win" → Confirmed win
- Query 2: "Seattle Seahawks Super Bowl wins history" → Found 2014 win
- Response: "No, this is their second. Previous win: Super Bowl XLVIII (2014) vs Broncos 43-8."

### Pattern 4: Comparison/Head-to-Head

**Question format:** "X vs Y history" or "Have X and Y played before?"

**Process:**
1. **Query 1 - Head-to-Head:**
   ```
   web_search: "[X] vs [Y] [context] history matchups"
   ```

2. **Query 2 - Complete Series:**
   ```
   web_search: "[X] [Y] all time record wins losses"
   ```

3. **List All Matchups:**
   - Date, result, score for each meeting
   - Overall series record

4. **Response Format:**
   ```
   [Answer to specific question]
   
   Complete head-to-head:
   - [Date]: [Result]
   - [Date]: [Result]
   Overall: [X] leads [Y], [record]
   ```

### Pattern 5: Sanity Check (All Responses)

**Before sending ANY definitive claim:**

1. **Red Flag Check:**
   - Does this sound unusual? (33-0 in Q1?)
   - Am I claiming "only"/"never"/"first" without explicit proof?
   - Did I just state a count without listing items?

2. **Math Check:**
   - Do my numbers add up?
   - wins + losses = total appearances?
   - If I said "X times", did I verify X occurrences?

3. **Completeness Check:**
   - Did I answer what was asked?
   - Did I provide full context?
   - Would follow-up "but what about...?" questions catch gaps?

4. **Source Check:**
   - Did I verify with search or just remember?
   - Are sources recent/authoritative?
   - Do multiple sources agree?

## Error Recovery

**If you catch yourself mid-response:**
1. STOP composing
2. Run verification queries
3. Correct the response
4. Add: "Let me verify that..." before the corrected answer

**If user corrects you:**
1. Acknowledge immediately: "You're right, let me correct that."
2. Run proper verification queries
3. Explain what was wrong and why
4. Store the error pattern in memory for learning

## Common Failure Modes to Prevent

### Incomplete Search Scope
- ❌ Searched "wins" but not "complete history"
- ✅ Search both specific answer AND full timeline

### Accepting First Result
- ❌ First article says "won once" → repeat that
- ✅ Search multiple sources, verify completeness

### Math Not Checking Out
- ❌ Said "2 wins, 3 appearances" (where's the 3rd appearance?)
- ✅ Cross-check: wins + losses = total, always

### Memory Over Tools
- ❌ "I remember Seattle won in 2014" → state as fact
- ✅ "Let me verify..." → search → then state

### Missing Context
- ❌ "They won 2 times" (omits losses/full history)
- ✅ "Won 2 times. Full record: 4 appearances, 2-2."

## Implementation Checklist

Before answering historical/statistical questions:

- [ ] Identified question type (record/timeline/count/comparison)
- [ ] Selected appropriate verification pattern
- [ ] Ran Query 1 (specific answer)
- [ ] Ran Query 2 (complete context/timeline)
- [ ] Cross-checked math (if applicable)
- [ ] Listed all occurrences (if claiming first/last/only)
- [ ] Verified from multiple sources
- [ ] Sanity-checked the answer (does it make sense?)
- [ ] Provided full context in response
- [ ] Ready to cite sources if asked

## Integration with Existing Skills

- Works WITH `fact-checker` and `verify-claims` (they check external claims, this checks YOUR claims)
- Complements `deep-research` (that's for comprehensive research, this is for quick verification)
- Runs BEFORE you send response (preventive, not reactive)

## Training Examples

### Good Response Pattern
**Q:** "How many Super Bowls has Tom Brady won?"
**Process:**
1. Search: "Tom Brady Super Bowl wins total"
2. Search: "Tom Brady Super Bowl complete history"
3. Cross-check: 7 wins listed, count appearances
4. Math: 7 wins + 3 losses = 10 appearances
**Response:** "Seven. Complete record: 10 Super Bowl appearances, 7 wins, 3 losses. Won with Patriots (2002, 2004, 2005, 2015, 2017, 2019) and Buccaneers (2021)."

### Bad Response Pattern (AVOID)
**Q:** "How many Super Bowls has Tom Brady won?"
**Process:**
1. Think: "I remember it's 7"
**Response:** "Seven."
**Problem:** No verification, no context, no completeness check

## Skill Output Format

When this skill is triggered, you should think:

```
🔍 RESPONSE VERIFICATION CHECK

Question type: [Sports History]
Pattern: [Two-Query Rule]

Query 1: [specific search]
→ Result: [answer]

Query 2: [complete timeline search]
→ Result: [full record]

Math Check: [X] wins + [Y] losses = [Z] total ✓

Sanity Check: [Any red flags? Unusual claims?]

Ready to respond: ✓
```

Then compose response with complete context.

---

**Remember:** It's better to say "Let me verify that..." than to confidently state an incomplete fact.
