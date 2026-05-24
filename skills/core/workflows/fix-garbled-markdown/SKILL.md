---
name: fix-garbled-markdown
description: Fix markdown files where entire lines were incorrectly wrapped in *...* (italic) — a common artifact of Google Docs or Notion exports. Use when investigation reports, docs, or any markdown files have garbled formatting with lines that look like "*Section Title*", "*col1 | col2*", or "*paragraph text*". Restores proper headers (##/###), pipe tables, and plain paragraphs.
category: workflows
runtimes: [claude]
pii_safe: true
---

# Fix Garbled Markdown

## Quick Fix

```bash
python3 ~/dev/skills/fix-garbled-markdown/scripts/fix_italic_wrap.py \
  file1.md file2.md file3.md
```

Dry-run first to preview changes:

```bash
python3 ~/dev/skills/fix-garbled-markdown/scripts/fix_italic_wrap.py file.md --dry-run | head -40
```

## What It Fixes

| Garbled | Fixed |
|---------|-------|
| `*15. Section Title*` | `## 15. Section Title` |
| `*15.1 Subsection*` | `### 15.1 Subsection` |
| `*col1 \| col2 \| col3*` | `\| col1 \| col2 \| col3 \|` |
| `*Paragraph text here.*` | `Paragraph text here.` |
| `*Stage 0 (Bootstrap): ...*` | `- Stage 0 (Bootstrap): ...` |

Code blocks (```` ``` ````) are never touched.

## Detection

Check how many lines are affected before fixing:

```bash
grep -c "^\*[^*]" file.md
```

## Root Cause

Google Docs → Markdown export sometimes italicizes entire paragraphs/sections instead of converting them properly. Also happens with some Notion exports.

## After Fixing

If the file needs to go to Drive, use the `gdrive-upload` skill.
