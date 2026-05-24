# Response Verification Examples

## Example 1: Sports Records (The Seattle Super Bowl Error)

### ❌ Without Verification

**User:** "How many times has Seattle won the Super Bowl?"

**Agent (wrong):**
- Searched: "Seattle Seahawks Super Bowl wins"
- Found: "won once in 2014"
- Added tonight's game
- Responded: "Two times (including tonight). They've appeared in 3 Super Bowls total."

**Problem:** Only searched for wins, not complete history. Missed the 2015 Patriots loss.

---

### ✅ With Verification Pattern

**User:** "How many times has Seattle won the Super Bowl?"

**Agent (correct):**

```
🔍 Response Verification - Sports History

Query 1 (specific): "Seattle Seahawks Super Bowl wins"
→ Result: 2 wins (2014, 2026)

Query 2 (complete): "Seattle Seahawks complete Super Bowl history"
→ Result: 4 appearances
  - 2006: Lost to Steelers 21-10
  - 2014: Won vs Broncos 43-8 ✓
  - 2015: Lost to Patriots 28-24
  - 2026: Won vs Patriots 29-7 ✓

Math Check: 2 wins + 2 losses = 4 appearances ✓

Sanity Check: Makes sense, no red flags
```

**Response:** "Two times. Complete record: 4 Super Bowl appearances, 2 wins (2014 vs Broncos 43-8, 2026 vs Patriots 29-7), 2 losses (2006 vs Steelers 21-10, 2015 vs Patriots 28-24)."

---

## Example 2: First/Last/Only Claims

### ❌ Without Verification

**User:** "Is this Seattle's first Super Bowl win?"

**Agent (wrong):**
- Searched: "Seattle Seahawks Super Bowl 2026"
- Found: "Seattle wins Super Bowl LX"
- Responded: "Yes, this is Seattle's first Super Bowl championship."

**Problem:** Didn't verify "first" claim. Missed 2014 win.

---

### ✅ With Verification Pattern

**User:** "Is this Seattle's first Super Bowl win?"

**Agent (correct):**

```
🔍 Response Verification - Record Claims

Query 1 (current event): "Seattle Seahawks Super Bowl 2026"
→ Result: Won Super Bowl LX

Query 2 (all occurrences): "Seattle Seahawks Super Bowl wins all time history"
→ Result: 2 wins found
  - Super Bowl XLVIII (2014): Seattle 43, Denver 8
  - Super Bowl LX (2026): Seattle 29, New England 7

Verification: NOT the first
```

**Response:** "No, this is their second Super Bowl win. First was Super Bowl XLVIII in 2014, defeating Denver 43-8. Tonight marks their second championship."

---

## Example 3: Head-to-Head History

### ❌ Without Verification

**User:** "Have Seattle and New England played in the Super Bowl before?"

**Agent (incomplete):**
- Searched: "Seattle New England Super Bowl"
- Found reference to tonight's game
- Responded: "Yes, tonight is their Super Bowl matchup."

**Problem:** Didn't search for "previous" or "history". Missed the 2015 game (Butler INT).

---

### ✅ With Verification Pattern

**User:** "Have Seattle and New England played in the Super Bowl before?"

**Agent (correct):**

```
🔍 Response Verification - Head-to-Head

Query 1: "Seattle Seahawks New England Patriots Super Bowl"
→ Result: Multiple references

Query 2: "Seattle Patriots Super Bowl history all matchups"
→ Result: 2 meetings
  - Super Bowl XLIX (2015): Patriots 28, Seahawks 24
  - Super Bowl LX (2026): Seahawks 29, Patriots 7

Series: Tied 1-1
```

**Response:** "Yes, this is their second Super Bowl meeting. They previously faced off in Super Bowl XLIX (2015), where the Patriots won 28-24 on the famous Malcolm Butler goal-line interception. Tonight they're tied 1-1 in Super Bowl matchups."

---

## Example 4: Unusual Statistics (Sanity Check)

### ❌ Without Verification

**User:** "What's the Super Bowl score?"

**Agent (wrong):**
- Used web_fetch on ESPN scoreboard
- Extracted: "SEA 33, NE 0" (text parsing error)
- Responded: "Seattle leads 33-0 in Q1."

**Problem:** No sanity check. A 33-0 score in Q1 is highly unusual and should trigger verification.

---

### ✅ With Verification Pattern

**User:** "What's the Super Bowl score?"

**Agent (correct):**

```
🔍 Response Verification - Sanity Check

Initial source: web_fetch ESPN scoreboard
→ Result: "33-0" (seems wrong)

Red Flag Check: ⚠️ 33-0 in Q1 is extremely unusual
Action: Use ESPN API instead of HTML parsing

API Query: site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
→ Result: SEA 3, NE 0 (Q1)

Sanity Check: ✓ Makes sense (field goal)
```

**Response:** "Seattle leads 3-0 in Q1 (field goal)."

---

## Example 5: Math Cross-Check

### ❌ Without Verification

**User:** "What's Tom Brady's Super Bowl record?"

**Agent (incomplete):**
- Searched: "Tom Brady Super Bowl wins"
- Found: "7 Super Bowl wins"
- Responded: "Tom Brady has won 7 Super Bowls."

**Problem:** No context about losses or total appearances.

---

### ✅ With Verification Pattern

**User:** "What's Tom Brady's Super Bowl record?"

**Agent (correct):**

```
🔍 Response Verification - Two-Query Rule

Query 1: "Tom Brady Super Bowl wins"
→ Result: 7 wins

Query 2: "Tom Brady Super Bowl complete history appearances"
→ Result: 10 appearances total

Math Check: 7 wins + 3 losses = 10 appearances ✓

Breakdown:
- Patriots (6 wins, 3 losses): 2002✓, 2004✓, 2005✓, 2008, 2012, 2015✓, 2017✓, 2018, 2019✓
- Buccaneers (1 win): 2021✓
```

**Response:** "Tom Brady has a 7-3 Super Bowl record (10 appearances). Won 6 with Patriots (2002, 2004, 2005, 2015, 2017, 2019) and 1 with Buccaneers (2021). Lost in 2008, 2012, and 2018."

---

## Pattern Summary

| Trigger | Pattern | Key Step |
|---------|---------|----------|
| "How many X?" | Two-Query Rule | Search specific + complete history |
| "Is this the first/only?" | Record Claims | Search all occurrences, verify claim |
| "X vs Y history?" | Head-to-Head | Search all matchups, count series |
| Unusual stat | Sanity Check | Red flag check → verify with alternate source |
| Any definitive count | Math Check | Cross-check: parts = whole |

**Golden Rule:** If you're about to state a count or claim "first/only/never", STOP and verify with the appropriate pattern.
