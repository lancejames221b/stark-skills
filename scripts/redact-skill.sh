#!/usr/bin/env bash
# redact-skill.sh <skill-dir|SKILL.md> [--dry-run] [--apply]
set -euo pipefail

if [[ $# -lt 1 ]]; then
	echo "Usage: $0 <path> [--dry-run|--apply]"
	exit 1
fi

SKILL_PATH="$1"
MODE="dry-run"
shift
while [[ $# -gt 0 ]]; do
	case "$1" in
	--dry-run)
		MODE="dry-run"
		shift
		;;
	--apply)
		MODE="apply"
		shift
		;;
	esac
done

echo "[$MODE] $SKILL_PATH"

PYTHON_CMD=$(which python3 || which python)
"$PYTHON_CMD" - "$SKILL_PATH" --mode="$MODE" <<'PYEOF'
import sys, re

path = sys.argv[1]
mode = [a for a in sys.argv if a.startswith("--mode=")][0].split("=")[1]

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
PYEOF
echo "Done."
