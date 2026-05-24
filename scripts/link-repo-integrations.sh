#!/usr/bin/env bash
# link-repo-integrations.sh [--dry-run] [--root <REPO_ROOT>]
set -euo pipefail

DRY_RUN=false
REPO_ROOT="${2:-$HOME/Dev}"

while [[ $# -gt 0 ]]; do
	case "$1" in
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--root)
		REPO_ROOT="$2"
		shift 2
		;;
	*)
		echo "Unknown: $1" >&2
		exit 1
		;;
	esac
done

find "$REPO_ROOT" -maxdepth 2 \( -name ".claude/skills" -o -name ".pi/agent/skills" -o -name ".opencode" -o -name "skills" \) 2>/dev/null | while read -r f; do
	repo="$(dirname "$(dirname "$f")" | sed "s|^$REPO_ROOT/||")"
	echo "- \`$repo\` → $f"
done
