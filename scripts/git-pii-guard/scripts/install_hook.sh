#!/usr/bin/env bash
# install_hook.sh — Install the PII guard pre-commit hook into a git repo.
# Usage: install_hook.sh [repo-path]
# Defaults to current directory if no path given.

set -euo pipefail

REPO="${1:-.}"
HOOKS_DIR="$REPO/.git/hooks"
HOOK_FILE="$HOOKS_DIR/pre-commit"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="$SCRIPT_DIR/pii_scan.py"

if [ ! -d "$REPO/.git" ]; then
  echo "Error: $REPO is not a git repository."
  exit 1
fi

mkdir -p "$HOOKS_DIR"

# If a pre-commit hook already exists, back it up
if [ -f "$HOOK_FILE" ]; then
  BACKUP="$HOOK_FILE.bak.$(date +%s)"
  cp "$HOOK_FILE" "$BACKUP"
  echo "Existing pre-commit hook backed up to $BACKUP"
fi

cat > "$HOOK_FILE" << HOOKEOF
#!/usr/bin/env bash
# PII Guard pre-commit hook — installed by git-pii-guard skill
# Blocks commits containing credentials, API keys, passwords, or PII.

python3 "$SCANNER" --diff
exit \$?
HOOKEOF

chmod +x "$HOOK_FILE"

echo "✅  PII Guard installed: $HOOK_FILE"
echo "    Scans staged diff before every commit."
echo "    Run 'python3 $SCANNER --file <path> --report' to scan any file manually."
