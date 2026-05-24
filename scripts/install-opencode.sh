#!/usr/bin/env bash
# install-opencode.sh [--dry-run] [--force] [COMMAND...|SKILL...]
set -euo pipefail

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
	*)
		TARGETS+=("$1")
		shift
		;;
	esac
done

CMDS_DIR="${OPENCODE_COMMANDS_DIR:-$HOME/.config/opencode/commands}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

function install_cmd() {
	local src="$1" dest="${CMDS_DIR}/$(basename "$src")" backup="$dest.bak.stark-skills"

	if [[ -e "$dest" && ! "$FORCE" == true ]]; then
		echo "⚠ Skipping $src: destination exists (use --force)" >&2
		return 0
	fi

	if [[ "$DRY_RUN" == true ]]; then
		echo "[dry-run] $src → $dest"
		return 0
	fi

	if [[ -f "$dest" ]]; then
		cp -a "$dest" "$backup" || true
	fi

	mkdir -p "$(dirname "$dest")"
	rm -rf "$dest"
	cp -a "$src" "$dest"
	echo "✓ $src → $dest"
}

if [[ ${#TARGETS[@]} -eq 0 ]]; then
	echo "No commands specified. Install all from repo?" >&2
	exit 0
fi

for t in "${TARGETS[@]}"; do
	install_cmd "$t"
done
