#!/usr/bin/env python3
"""
Fix markdown files where entire lines were incorrectly wrapped in *...*
(common artifact of Google Docs → Markdown export).

Usage: fix_italic_wrap.py <file.md> [--dry-run]
"""
import sys, re

def classify_line(content):
    """Classify what a stripped-asterisk line should become."""
    # Section like "15. Title" or "15.1 Title"
    m = re.match(r'^(\d+)\.(\d+)?\s+(.+)$', content)
    if m:
        level = '##' if not m.group(2) else '###'
        return f"{level} {content}"
    # Table row: contains | 
    if '|' in content:
        cols = [c.strip() for c in content.split('|')]
        return '| ' + ' | '.join(cols) + ' |'
    # List item starting with Stage/Step/Phase
    if re.match(r'^(Stage|Step|Phase|Part)\s+\d', content):
        return f"- {content}"
    # Default: plain paragraph
    return content

def fix_file(path, dry_run=False):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed = []
    changes = 0
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.rstrip('\n')

        # Track code blocks — never touch them
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            fixed.append(line)
            continue
        if in_code_block:
            fixed.append(line)
            continue

        # Detect full-line italic wrap: starts with * (not **), ends with *
        m = re.match(r'^\*([^*].*[^*])\*\s*$', stripped)
        if m:
            content = m.group(1).strip()
            # Strip trailing stray asterisk like "15.** Title" → "15. Title"
            content = re.sub(r'\*+', '', content)
            new_line = classify_line(content) + '\n'
            if new_line.rstrip('\n') != stripped:
                changes += 1
                if dry_run:
                    print(f"  L{i+1}: {stripped!r}")
                    print(f"      → {new_line.rstrip()!r}")
                fixed.append(new_line)
                continue

        fixed.append(line)

    if not dry_run and changes:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(fixed)

    print(f"{path}: {changes} lines fixed" + (" (dry run)" if dry_run else ""))
    return changes

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.md> [--dry-run]")
        sys.exit(1)
    dry_run = '--dry-run' in sys.argv
    files = [a for a in sys.argv[1:] if not a.startswith('--')]
    total = sum(fix_file(f, dry_run) for f in files)
    print(f"\nTotal: {total} lines fixed across {len(files)} file(s)")
