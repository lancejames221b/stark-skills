---
description: Smart git commit — detects changes, drafts commit message, stages, and commits. Follows conventions: concise, professional, focus on "why" not "what"
argument-hint: "[message description] --scope component"
---
## Smart Git Commit

### Step 1: Detect Changes
```bash
git status --short
git diff --stat
git log --oneline -5
```

### Step 2: Analyze Changes
For each changed file, determine:
- What type of change: `feat`, `fix`, `refactor`, `docs`, `test`, `style`, `chore`
- Scope: which module/component is affected
- Why: what problem this solves (not what the code does)

### Step 3: Draft Commit Message
Format follows conventional commits:
```
<type>(<scope>): <description>

<optional longer description>
```

Examples:
```
feat(dashboard): wire auth context to real API endpoints

Replace mock user data with fetch calls to /api/auth/login
and store JWT in localStorage for session persistence.
```

Rules:
- **Focus on "why"**, not "what" (the code shows what)
- **One line summary**, ≤ 72 chars for the header
- **Paragraph break** before body if needed
- **No emoticons**, casual punctuation
- **Professional tone**: "fix", "feat", "refactor" — not "oops", "whoops"

### Step 4: Commit
```bash
git add <changed-files>
git commit -m "<header>" -m "<body>"
```

### Step 5: Verify
```bash
git log --oneline -1
```

Show the final commit message.
