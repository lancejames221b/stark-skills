#!/usr/bin/env bash
# install-pi.sh [--dry-run] [--force] [SKILL...]
set -euo pipefail

DRY_RUN=false
FORCE=false
SKILLS=()

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
	-h | --help)
		echo "Usage: $0 [--dry-run] [--force] [SKILL...]"
		exit 0
		;;
	*)
		SKILLS+=("$1")
		shift
		;;
	esac
done

SKILLS_DIR="${PI_SKILLS_DIR:-$HOME/.pi/agent/skills}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

function install_skill() {
	local src="$1" dest="${SKILLS_DIR}/$(basename "$src")" backup="$dest.bak.stark-skills"

	if [[ -e "$dest" && ! "$FORCE" == true ]]; then
		echo "⚠ Skipping $src: destination exists (use --force)" >&2
		return 0
	fi

	# Skip package-provided skills
	if [[ -f "$dest/SKILL.md" ]] && grep -q "^name: " "$dest/SKILL.md" 2>/dev/null; then
		echo "ℹ Skipping $src: looks like a pi skill – ensure it's user-provided" >&2
		return 0
	fi

	if [[ "$DRY_RUN" == true ]]; then
		echo "[dry-run] $src → $dest"
		return 0
	fi

	if [[ -d "$dest" ]]; then
		cp -a "$dest" "$backup" || true
	fi

	mkdir -p "$(dirname "$dest")"
	rm -rf "$dest"
	cp -a "$src" "$dest"
	echo "✓ $src → $dest"
}

if [[ ${#SKILLS[@]} -eq 0 ]]; then
	echo "No skills specified. Install all from repo?" >&2
	exit 0
fi

for skill in "${SKILLS[@]}"; do
	install_skill "$skill"
done
