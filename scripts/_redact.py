#!/usr/bin/env python3
"""Apply common PII redactions to a skill file."""
import sys, re

path = sys.argv[1]
mode = (sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read().strip())

replacements = [
    (r'(?i)Lance', '<USER_NAME>'),
    (r'/home/[a-zA-Z0-9_-]+', '<LOCAL_PATH>'),
    (r'\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b', '<PHONE_NUMBER>'),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '<EMAIL_ADDRESS>'),
    (r'\b(?:lance|james)[\w-]*\.lan\b', '<HOST_ALIAS>'),
]

text = open(path).read()
orig_len = len(text)
for pat, repl in replacements:
    count = len(re.findall(pat, text))
    if count > 0:
        print(f"  → {pat}: {count} match(es) replaced with '{repl}'", file=sys.stderr)
        text = re.sub(pat, repl, text)

new_len = len(text)
if orig_len != new_len:
    changed = [(pat, len(re.findall(pat, open(path).read()))) for pat,_ in replacements if re.search(pat, open(path).read())]
    print(f"  → CHANGED: {len(changed)} patterns matched in original", file=sys.stderr)
    if mode == 'apply':
        open(path, 'w').write(text)
else:
    print("  → NO CHANGES", file=sys.stderr)
