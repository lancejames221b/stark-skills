#!/usr/bin/env bash
# validate-layout.sh [--path PATH] -- check that critical files exist.
set -euo pipefail

TARGET="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
FAILED=0

REQUIRED=(
	"README.md"
	"LICENSE"
	"scripts/inventory-skills.sh"
	"scripts/redact-skill.sh"
	"scripts/validate-no-pii.sh"
	"scripts/install-all.sh"
	"docs/redaction-policy.md"
	"docs/multi-agent-workflows.md"
	"docs/voice-workflows.md"
	"docs/install.md"
	"docs/optimal-setup.md"
	"docs/repository-integrations.md"
	"docs/contributing.md"
)

for f in "${REQUIRED[@]}"; do
	if [[ ! -e "$TARGET/$f" ]]; then
		echo "MISSING: $f" >&2
		((FAILED++)) || true
	fi
done

if [[ $FAILED -gt 0 ]]; then
	echo "✗ Layout validation failed: $FAILED missing files" >&2
	exit 1
fi

echo "✓ Layout validation passed."
