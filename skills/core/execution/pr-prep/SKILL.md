---
name: pr-prep
description: Generate a spoken PR review script with embedded BEFORE/AFTER code, post it to Notion, and open it on Mac. Use when user says "pr-prep", "prep PR", "prep this PR", "review script for PR", or "pr prep <number>".
category: execution
runtimes: [claude]
pii_safe: true
---

# PR Prep Skill

> **Notion access — use mcporter on <INFERENCE_HOST> FIRST.** Local `mcp__notion__*` tools require per-page sharing in Notion's UI and 404 on most pages. Use `ssh <INFERENCE_HOST> 'mcporter call notion.<tool> ...'` instead. Tools available: notion-search, notion-fetch, notion-query-meeting-notes, notion-update-page, notion-create-pages, notion-create-view, notion-update-view (16 total). See memory `feedback_notion_via_mcporter`.

Turns a GitHub PR diff into a spoken walkthrough script with embedded code, posted to Notion and opened on Mac. The output is a page you can talk through live — not documentation.

## Usage
- `/pr-prep 314` — prep PR #314 in the current repo
- `/pr-prep 314 315` — prep multiple PRs (stacked/related)
- `/pr-prep` — uses current branch, auto-detects open PR

## Implementation

### Step 1: Identify repo and PR(s)

- If PR number(s) given, use them directly
- If no args, run `gh pr list --head $(git branch --show-current) --json number,title` to find the open PR
- Determine repo slug: `gh repo view --json nameWithOwner -q .nameWithOwner`
- For each PR, get the diff: `gh pr diff <number> --repo <slug>`
- Get PR metadata: `gh pr view <number> --repo <slug> --json title,body,baseRefName,headRefName,additions,deletions,changedFiles`

### Step 2: Analyze the diff

For each changed file, identify:
- **NEW files**: full content shown as "what's new here"
- **MODIFIED files**: extract BEFORE (removed lines) and AFTER (added lines) for each changed section
- **Key pattern to highlight**: what was broken, what the fix does, and why it matters
- Focus on logic changes, not whitespace/imports unless they're the fix

Build a mental model of:
1. What was the bug / gap? (root cause, not symptom)
2. What does each PR change, precisely?
3. Why this approach vs. alternatives?
4. What does it NOT fix? (explicitly)

### Step 3: Generate the spoken script

Write in first-person conversational style — "So let me start with..." not "This PR introduces...". The reader is talking through this live, not reading documentation.

Structure (adapt to PR content, don't be rigid about headers):

**Opening (1 short paragraph)**
What's the problem. The actual failure mode. What broke in production. Numbers if available ("30 days of silent data loss", "3,261 jobs queued").

**Why we didn't just patch over it**
If there's an obvious simpler fix that was rejected, explain why. This is usually the most important part for reviewers.

**For each PR:**
- One sentence: what this PR does
- BEFORE code: the problematic code (as actual code lines)
- AFTER code: the fix (as actual code lines)
- Why each exception/change/addition exists — the design reasoning, not just "we added X"
- Any subtle details (import paths, exception hierarchy, error type capture, exactly-one-retry rationale, etc.)

**Merge order / staging**
If stacked PRs, state the order. What to validate before merging. How to test.

**What these PRs don't fix**
Be honest. Name the failure classes that still need ops work, future PRs, or upstream fixes.

**Tone rules:**
- Conversational, first person ("So here's the thing...", "The reason we do X is...", "Notice that...")
- No documentation headers like "LINE BY LINE BREAKDOWN" or "RATIONALE"
- Code snippets should be real code from the diff, not paraphrased
- Keep it talkable — if you'd stumble reading it aloud, rewrite it

### Step 4: Post to Notion

**First, search for an existing page** to edit rather than create a new one:

```
mcp__notion__API-post-search
query: "PR Review Script — <PR numbers or title keywords>"
filter: { property: "object", value: "page" }
```

- If a matching page is found: edit it in place
  - Use `mcp__notion__API-get-block-children` to get existing block IDs
  - Delete all existing content blocks via `mcp__notion__API-delete-a-block` (one per block)
  - Then append fresh blocks via `mcp__notion__API-patch-block-children` on the page ID
  - Update the page title if needed via `mcp__notion__API-patch-page`
- If no match: create a new page via `mcp__notion__API-post-page`
  - Parent: `<NOTION_ID>` (<USER_NAME>s engineering workspace)
  - Title: `PR Review Script — <PR titles, comma-separated> — <today's date>`
  - Icon: `📋`
  - Then add children via `mcp__notion__API-patch-block-children`

**Notion block constraints (critical):**
- `blockObjectRequest` only supports `paragraph` and `bulleted_list_item` — no `code` type
- `richTextRequest` has `additionalProperties: false` — no annotation objects, no link objects
- Embed code as bulleted list items with actual code text — use a blank bullet before and after each code section to visually separate it
- For BEFORE/AFTER sections: use a paragraph "BEFORE:" then bullets for each line, then paragraph "AFTER:" then bullets

Add blocks in batches of ≤20 children per API call to avoid payload limits.

Structure the blocks as:
1. Paragraph: opening (bug description)
2. Paragraph: why-not-simpler-fix explanation  
3. For each PR:
   - Paragraph: "PR #N — [title]"
   - Paragraph: one-sentence what-it-does
   - Bulleted items: BEFORE code lines
   - Paragraph: "AFTER:" 
   - Bulleted items: AFTER code lines
   - Paragraphs: design reasoning for key choices
4. Paragraph: merge order / staging
5. Paragraph: what's not fixed

### Step 5: Open on Mac

Take the page URL from the Notion response and run:
```bash
ssh <MAC_HOST> "open '<url>'"
```

### Step 6: Confirm

Reply with one line:
```
PR prep done: <PR title(s)> → <url>
```

## Notes
- `ssh <MAC_HOST>` is the Mac host at <PRIVATE_IP> — always use this for `open` commands
- Notion parent ID `<NOTION_ID>` is <USER_NAME>s engineering workspace — always use this for PR review pages
- For stacked PRs: get each diff separately so BEFORE/AFTER is accurate per PR
- The `gh pr diff` output includes full unified diff — parse removed lines (starting with `-`) as BEFORE, added lines (starting with `+`) as AFTER
- Trim `+`/`-` prefix from code lines when embedding in Notion bullets
- If a PR has many changed files, focus the script on the 1-3 files with the core logic change; mention other files briefly
- This skill produces a talking script, not a design doc — if <USER_NAME>would read it silently and not speak it, it's too formal
