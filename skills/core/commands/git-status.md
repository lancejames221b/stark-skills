---
description: "Clean git status overview with actionable information"
tools: ["bash"]
---

Display clean, actionable git status information in your preferred format.

Parse $ARGUMENTS for status options:
- "clean" - Clean, minimal output
- "full" - Comprehensive status report
- "files" - Focus on file changes only
- Empty - Standard clean overview

Status information provided:
1. Current branch and remote tracking
2. Commits ahead/behind remote
3. Working directory status:
   - Staged changes (ready to commit)
   - Modified files (need staging)
   - Untracked files (need adding)
4. Stash status if any
5. Suggested next actions

Clean output format:
```
Branch: feature-auth (tracking origin/feature-auth)
Status: 2 commits ahead, 1 behind

Staged (2):
  M  src/auth.py
  A  tests/test_auth.py

Modified (3):
  M  README.md
  M  src/config.py
  ??  new-feature.py

Next: git add . && git commit
```

Actionable suggestions:
- Recommend staging commands
- Suggest commit/push actions  
- Highlight merge conflicts
- Note if branch needs pull/rebase
- Identify large or sensitive files

Integration with other commands:
- Links to `/commit` for next steps
- Suggests `/push` when ready
- Recommends `/pr` for feature branches

Arguments: $ARGUMENTS