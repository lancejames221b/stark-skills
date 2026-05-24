#!/usr/bin/env bash
# install-all.sh [--claude] [--pi] [--opencode] [--dry-run] [--force]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DRY_RUN=false
FORCE=false
TARGETS=()

while [[ $# -gt 0 ]]; do
	case "$1" in
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--force)
		FORCE=true
		shift
		;;
	--claude)
		TARGETS+=("claude")
		shift
		;;
	--pi)
		TARGETS+=("pi")
		shift
		;;
	--opencode)
		TARGETS+=("opencode")
		shift
		;;
	*)
		echo "Unknown option: $1" >&2
		exit 1
		;;
	esac
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
	TARGETS=(claude pi opencode)
fi

for target in "${TARGETS[@]}"; do
	"$SCRIPT_DIR/install-$target.sh" ${DRY_RUN:+--dry-run} "${FORCE:+--force}" "$@"
done
