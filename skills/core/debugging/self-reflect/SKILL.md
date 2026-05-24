---
name: self-reflect
description: Deep reflection and optimization with Opus. Two modes — /self-reflect analyzes completed work, extracts root causes, and stores lessons. /optimize analyzes a process or system, determines the right model and approach, then executes improvements. Use when reflecting on what happened, extracting lessons, optimizing workflows, or improving approaches. Triggers on "self-reflect", "reflect on", "optimize", "what went wrong", "what can we improve", "lessons learned".
category: debugging
runtimes: [claude]
pii_safe: true
---

# /self-reflect & /optimize — Deep Analysis + Action

## Mode 1: /self-reflect [topic]

Opus-high reflection on what happened, why, and what to learn.

### Steps

1. **Switch to Opus-high:**
   ```
   session_status model=opus-high
   ```

2. **Gather full context:**
   - Search haivemind: `mcporter call haivemind.search_memories query="[topic]" limit=20`
   - Read channel directive: `contexts/[channel-id].md`
   - Check recent Discord messages: `message action=read channelId=[id] limit=30`
   - Check git log if code-related: `git log --oneline -20`
   - Read any referenced plans, tickets, or docs

3. **Deep reflection (Opus analyzes all of this):**
   - **What happened** — timeline of events, decisions, outcomes
   - **What worked** — patterns, tools, approaches that succeeded
   - **What failed** — root causes (not symptoms), systemic issues
   - **Why** — connect failures to underlying assumptions, gaps in knowledge, process flaws
   - **Counterfactuals** — what would have changed the outcome
   - **Patterns** — recurring themes across similar past work (search haivemind for prior reflections)

4. **Extract actionable lessons:**
   - Each lesson = `[LESSON]: [clear statement] | trigger=[what exposed it] | fix=[what to do differently]`
   - Distinguish between: one-off mistakes vs systemic issues vs knowledge gaps
   - Rate severity: critical (will recur and cause damage) / moderate / minor

5. **Store lessons (four destinations):**
   - **Channel directive** (`contexts/[channel-id].md`) → channel-specific lessons under `## Self-Reflection [date]`
   - **haivemind** → `mcporter call haivemind.store_memory content="REFLECTION [channel-id] [date]: [lessons]" category="rules"`
   - **MCP Registry** → if MCP tools were involved, update `mcpRegistry.domains.[server].notes[]`
   - **MEMORY.md** → only if the lesson is globally significant (rare)

6. **Report:** Conversational summary — lead with the most important insight. No fluff.

## Mode 2: /optimize [target]

Opus-high analyzes a process/system, then determines the right model and approach to implement improvements.

### Phase 1: Analysis (Opus-high — always)

1. **Switch to Opus-high:**
   ```
   session_status model=opus-high
   ```

2. **Gather context** (same as reflect — haivemind, channel directive, messages, code, docs)

3. **Optimization analysis:**
   - **Current state** — how does this process/system work today
   - **Bottlenecks** — where does time/effort/quality get lost
   - **Root causes** — why do the bottlenecks exist
   - **Opportunities** — what changes would have the highest impact
   - **Dependencies** — what blocks each improvement
   - **Risk** — what could go wrong with each change

4. **Produce an optimization plan:**
   - Ordered list of improvements, highest-impact first
   - For each: what to change, expected impact, effort estimate, risk level
   - **Model assignment** — Opus determines which model handles each optimization:

   | Optimization type | Model | Why |
   |-------------------|-------|-----|
   | Code refactor / bug fix | `cursor-agent/sonnet-4.6` | CursorSonnet for efficient code changes |
   | Complex architecture change | `cursor-agent/opus-4.6` | Deep reasoning needed |
   | Config / infra change | `max-high/claude-sonnet-4-6` | Inline, needs care |
   | Skill / workflow rewrite | `max-high/claude-sonnet-4-6` | Inline reasoning |
   | Research-heavy optimization | `google/gemini-3.1-pro-preview` | 1M context for large codebases |
   | Simple cleanup / formatting | `max-low/claude-sonnet-4-6` | Low-stakes, fast |

### Phase 2: Execution (Model determined by Phase 1)

5. **Present plan to <USER_NAME>for approval:**
   - Show the ordered improvements with model assignments
   - Wait for "do it", "go", or selective approval ("do 1 and 3")

6. **Execute approved optimizations:**
   - Switch model per-task if needed: `session_status model=[assigned-model]`
   - For code changes: spawn sub-agent with appropriate model
   - For inline changes: execute directly
   - Verify each change before moving to next

7. **Post-optimization reflection (brief):**
   - What was improved
   - Measured or expected impact
   - Store to haivemind: `mcporter call haivemind.store_memory content="OPTIMIZATION [channel-id] [date]: [changes made] [impact]" category="operations"`

## Key Principles

- **Opus-high always drives the thinking.** Analysis and lesson extraction are never delegated to a cheaper model.
- **Execution model is determined by the analysis.** Opus picks the right tool for each job.
- **No shallow reflections.** Surface-level "we should communicate better" is useless. Find the mechanism.
- **Lessons must be stored.** A reflection without persistence is wasted tokens.
- **Optimize requires approval.** Never execute optimizations without explicit go-ahead.
- **Feed the loop.** Every reflection and optimization improves future `/plan` and `/do` runs.
