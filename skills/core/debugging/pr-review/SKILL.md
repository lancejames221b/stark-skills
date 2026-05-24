---
name: pr-review
description: >
  PR review skill. Two modes: /pr [link] = internal thoughts only, what to look for, what to test —
  NO GitHub action ever. /pr-comment [link] "make it so #1" = draft a GitHub PR comment in <USER_NAME>s
  voice, present for approval, post only on explicit "go". Passphrase + "go" are both required
  before any GitHub write. Without both gates, nothing leaves the building.
category: debugging
runtimes: [claude]
pii_safe: true
---

# PR Review — Two Modes, One Hard Rule

**Nothing posts to GitHub without (a) the passphrase and (b) an explicit "go" from <USER_NAME>.**

---

## Mode 1: `/pr [link or number]` — Thoughts Only (DEFAULT)

**Trigger:** `/pr`, "review PR [X]", "look at PR [X]", "what do you think about PR [X]",
"review this PR", or any casual PR review request WITHOUT the passphrase.

**What it does:** Internal analysis delivered to Discord only. No draft comment. No offer to post.
GitHub is not touched. This is the read-only mode.

### Step 1 — Fetch PR

```bash
gh pr view [PR_NUMBER] --repo [owner/repo] \
  --json title,body,author,state,additions,deletions,changedFiles,files,reviews,comments

gh pr diff [PR_NUMBER] --repo [owner/repo]
```

For large diffs (>500 lines), focus on highest-risk files. Note the size.

### Step 2 — Deliver Internal Review to Discord

Format:

```
**PR: [title] (#[number])** — [repo] · [author] · +[additions]/-[deletions] · [X files]

**What it does**
[1-3 sentences, plain English]

**Risk:** Low / Medium / High — [one-line reason]

**Code quality**
[direct findings, or "looks clean"]

**Correctness**
[logic, edge cases, error handling — or "no issues spotted"]

**Security**
[auth, injection, secrets in code, dangerous patterns — or "nothing flagged"]

**Architecture**
[fits or fights the existing design]

**Tests**
[coverage, quality, missing cases — or "no tests / that's fine because X" or "that's a problem"]

**What to test**
[specific things <USER_NAME>or the team should manually verify before merging]

**My take:** Approve / Request changes / Needs discussion
[1-3 sentences on the call and what you'd tell the author]
```

End there. No offer to post. No GitHub action. Done.

### Haivemind Log (silent)
```bash
mcporter call haivemind.store_memory \
  content="PR-REVIEW [PR_NUMBER] [repo] [date]: mode=thoughts-only, author=[X], risk=[level], verdict=[my-take]" \
  category="operations"
```

---

## Mode 2: `/pr-comment [link or number] "make it so #1"` — Draft + Post

**Trigger:** `/pr-comment`, `/comment`, or similar phrase **AND** the exact passphrase
`make it so #1` must appear in the same message.

**Without the passphrase:** Respond with "Passphrase required to draft external comments." Full stop.
Do not draft anything. Do not offer alternatives.

**What it does:** Fetches the PR, analyzes it, drafts a GitHub PR comment in <USER_NAME>s voice,
presents it for review, and posts ONLY after <USER_NAME>replies "go".

### Step 1 — Passphrase Check

Scan the triggering message for the exact string `make it so #1`.

- **Found:** Proceed to Step 2.
- **Not found:** Reply "Passphrase required to draft external comments." Stop.

### Step 2 — Fetch PR (same as Mode 1)

### Step 3 — Internal Analysis (keep this private/silent)

Do the full analysis internally. This informs the comment but is NOT posted to Discord in full —
<USER_NAME>asked for a comment draft, not a full internal review. Keep it tight.

### Step 4 — Draft the PR Comment in <USER_NAME>s Voice

Load and follow `skills/lance-voice/lance-voice-rules.md` before drafting.

**Voice rules (mandatory, no exceptions):**
- No em dashes (—) anywhere
- No AI-slop phrases: no "great work", "overall", "I think", "just a thought", "happy to discuss",
  "looking forward to", "leveraging", "touch base", "circle back", "fantastic", "in terms of"
- No corporate language
- No excessive hedging
- Short. Direct. Real sentences. Sounds like <USER_NAME>wrote it at 11pm.
- Max 3-4 short paragraphs. Could be 2 sentences. Could be a list of sharp callouts.
- If approving: say why briefly. If requesting changes: say exactly what and why.
- Match the register to what's actually happening — don't inflate or deflate.

**Comment formats by situation:**

Approve with no concerns:
```
[1-2 sentences saying what's good about it. Optional: one thing to watch.]
```

Approve with minor notes:
```
[Brief statement on the main change. 1-2 specific things to keep an eye on or fix before
shipping. Clear that it's not a blocker.]
```

Request changes:
```
[What the problem is, directly. What needs to happen to fix it. No softening.]
```

General review comment (not approve/reject):
```
[What you noticed. What you'd check or test. What you'd want addressed.]
```

### Step 5 — Present Draft to <USER_NAME>

```
Draft PR comment for #[number]:

---
[exact draft text]
---

Reply **go** to post, or tell me what to change.
```

Do not post anything to GitHub yet.

### Step 6 — Wait for "go"

| Reply | Action |
|-------|--------|
| `go` | Post the comment as shown. See Step 7. |
| `go + [edits]` | Apply the stated edits, show the updated draft once more, wait for another "go". |
| `[any edit instruction]` | Revise the draft, show it again, wait. |
| `cancel` / `no` / `stop` | Abort. Nothing posted. Confirm: "Cancelled — nothing posted to GitHub." |

"Go" is the only word that triggers a post. Nothing else.

### Step 7 — Post to GitHub

```bash
gh pr comment [PR_NUMBER] --repo [owner/repo] --body "[approved comment text]"
```

Confirm back: "Posted to PR #[number]."

Log to haivemind:
```bash
mcporter call haivemind.store_memory \
  content="PR-COMMENT-POSTED [PR_NUMBER] [repo] [date]: passphrase=confirmed, approved-by=lance, posted=yes" \
  category="operations"
```

---

## Hard Rules — Both Modes

1. **Never post to GitHub without passphrase + "go".** Both required. No exceptions.
2. **Never approve, request changes, or merge** without explicit instruction beyond "go" (<USER_NAME>must say "approve" or "request changes" explicitly for those — a "go" only posts a comment).
3. **Never post as <USER_NAME>on GitHub** without the full two-gate sequence above.
4. **Always load lance-voice rules before drafting any comment.**
5. **No em dashes. Ever.** In any comment draft.
6. **If unsure which mode:** Default to Mode 1 (thoughts only). Never default to drafting a comment.

---

## Context Resolution

If <USER_NAME>says "that PR" or "Jon's PR" without a number:
1. Check current thread/channel for PR number in context
2. Check haivemind: `mcporter call haivemind.search_memories query="PR review [author/repo]" limit=5`
3. If still ambiguous: ask once. "Which PR? Number or URL."

## Repo Resolution

If repo is ambiguous from the PR number alone, check:
1. Channel directive (`contexts/[channel-id].md`) for active project
2. haivemind for recent PR review context
3. Ask once if still unclear

## Large Diffs

>500 lines: Note the size, focus on highest-risk files. Offer to go deeper on specific files if needed.
Draft comment should still be concise — don't summarize everything, just the parts worth calling out.

## Draft PRs

Flag it prominently. Still analyze if <USER_NAME>wants, but note it's not ready for merge review.
Don't approve draft PRs under any circumstances.
