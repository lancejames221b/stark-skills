#!/usr/bin/env bash
# validate-no-pii.sh [--path PATH] [--quiet] [--summary]
#
# Scan markdown (and other text) files for PII / private values that must not
# be committed. Exits non-zero if any matches are found.
#
# Categories detected (see docs/redaction-policy.md):
#   - Email addresses
#   - Phone numbers (US-style)
#   - Absolute /home/<user>/ paths
#   - Private IPs (RFC-1918: 10.x, 172.16-31.x, 192.168.x)
#   - Tailscale IPs (100.64.0.0/10)
#   - Long digit sequences (10+ digits — Discord/Notion/Slack IDs)
#
# Findings are printed as `file:line:matched-text`. Lines containing canonical
# placeholders (<EMAIL_ADDRESS>, <LOCAL_PATH>, etc.) and obvious example
# values (test@test.com, example.com, 10.0.0.0, 192.168.1.1, etc.) are
# excluded so the script stays signal-heavy.

set -euo pipefail

# ---- CLI ----
PATHS=()
QUIET=0
SUMMARY=0

while [[ $# -gt 0 ]]; do
	case "$1" in
		--path)
			PATHS+=("$2")
			shift 2
			;;
		--quiet)
			QUIET=1
			shift
			;;
		--summary)
			SUMMARY=1
			shift
			;;
		-h|--help)
			sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
			exit 0
			;;
		*)
			echo "Unknown arg: $1" >&2
			exit 2
			;;
	esac
done

if [[ ${#PATHS[@]} -eq 0 ]]; then
	TARGET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
	PATHS=("$TARGET_DIR/skills" "$TARGET_DIR/adapters")
fi

# ---- Files / paths to skip ----
# Auto-generated docs and known schema-heavy files that produce noise.
SKIP_PATTERNS=(
	'/.git/'
	'/_staging/'
	'/node_modules/'
	'/.venv/'
	'skills/core/integrations/notion-oauth/SKILL.md'
	'skills/core/commands/'
	# The validator itself describes patterns it must detect; exclude to
	# avoid self-matches when scanning the repo root.
	'scripts/validate-no-pii.sh'
	'docs/redaction-policy.md'
	'docs/redaction-map.example.yml'
	# git-pii-guard's own scanner and docs legitimately contain regex/CIDR
	# documentation for the patterns they catch.
	'scripts/git-pii-guard/'
)

should_skip() {
	local f="$1"
	for pat in "${SKIP_PATTERNS[@]}"; do
		case "$f" in
			*"$pat"*) return 0 ;;
		esac
	done
	return 1
}

# ---- Allowlist: lines containing any of these are not flagged ----
# These are canonical placeholders + universally safe example values.
ALLOWLIST_PATTERNS=(
	'<EMAIL_ADDRESS>'
	'<PERSON_EMAIL_ADDRESS>'
	'<PHONE_NUMBER>'
	'<NOTION_DATABASE_ID>'
	'<DISCORD_CHANNEL_ID>'
	'<SLACK_CHANNEL_ID>'
	'<GOOGLE_DRIVE_FOLDER_ID>'
	'<LOCAL_PATH>'
	'<PRIVATE_IP>'
	'<USER_NAME>'
	'<HOST_ALIAS>'
	'<DEVICE_NAME>'
	'<ROOM_NAME>'
	'<REDACTED>'
	'test@test\.com'
	'john@company\.com'
	'you@yourdomain\.com'
	'example\.com'
	'example\.org'
	'example\.net'
	'foo@bar\.example'
	'domain\.com'
	'/home/<user>'
	'/home/\$USER'
	'/home/\${USER}'
	'/home/generic/'
	'/home/root/'
	'/home/nobody/'
)

# Build a single egrep -v allowlist filter
build_allowlist_args() {
	local args=()
	for p in "${ALLOWLIST_PATTERNS[@]}"; do
		args+=(-e "$p")
	done
	printf '%s\n' "${args[@]}"
}

# ---- PII pattern definitions ----
# Each entry: LABEL|REGEX (ERE).
PATTERNS=(
	'EMAIL|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
	'PHONE|(\+?1[-. ])?\(?[0-9]{3}\)?[-. ][0-9]{3}[-. ][0-9]{4}'
	'HOME_PATH|/home/[A-Za-z][A-Za-z0-9_-]*/'
	'PRIVATE_IP_192|\b192\.168\.[0-9]{1,3}\.[0-9]{1,3}\b'
	'PRIVATE_IP_10|\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b'
	'PRIVATE_IP_172|\b172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}\b'
	'TAILSCALE_IP|\b100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}\b'
	'LONG_DIGITS|\b[0-9]{10,}\b'
)

# ---- Scan ----
TOTAL_HITS=0
declare -A CATEGORY_COUNTS

# Read allowlist args into an array once
mapfile -t ALLOWLIST_ARGS < <(build_allowlist_args)

scan_file() {
	local file="$1"
	local label regex
	local entry
	for entry in "${PATTERNS[@]}"; do
		label="${entry%%|*}"
		regex="${entry#*|}"
		# grep -n -E for line numbers; filter out allowlisted lines.
		local matches
		matches="$(grep -nE "$regex" "$file" 2>/dev/null \
			| grep -vE "$(IFS='|'; echo "${ALLOWLIST_PATTERNS[*]}")" \
			|| true)"
		if [[ -n "$matches" ]]; then
			while IFS= read -r line; do
				[[ -z "$line" ]] && continue
				local lineno="${line%%:*}"
				local rest="${line#*:}"
				# Extract just the first matching token for clarity
				local snippet
				snippet="$(printf '%s' "$rest" | grep -oE "$regex" | head -n1)"
				[[ -z "$snippet" ]] && snippet="$rest"
				if [[ $QUIET -eq 0 && $SUMMARY -eq 0 ]]; then
					printf '%s:%s:[%s] %s\n' "$file" "$lineno" "$label" "$snippet"
				fi
				TOTAL_HITS=$((TOTAL_HITS + 1))
				CATEGORY_COUNTS["$label"]=$(( ${CATEGORY_COUNTS["$label"]:-0} + 1 ))
			done <<< "$matches"
		fi
	done
}

for TARGET in "${PATHS[@]}"; do
	if [[ ! -e "$TARGET" ]]; then
		echo "WARN Skipping $TARGET (not found)" >&2
		continue
	fi

	# Accept either a directory (recurse) or a single file
	if [[ -d "$TARGET" ]]; then
		while IFS= read -r file; do
			should_skip "$file" && continue
			scan_file "$file"
		done < <(find "$TARGET" \
			-type d \( -name '.git' -o -name 'node_modules' -o -name '_staging' -o -name '.venv' \) -prune -o \
			-type f \( -name '*.md' -o -name '*.txt' -o -name '*.yml' -o -name '*.yaml' -o -name '*.py' -o -name '*.sh' \) -print \
			| sort)
	else
		should_skip "$TARGET" || scan_file "$TARGET"
	fi
done

# ---- Report ----
if [[ $TOTAL_HITS -gt 0 ]]; then
	if [[ $SUMMARY -eq 1 || $QUIET -eq 0 ]]; then
		echo "" >&2
		echo "PII findings by category:" >&2
		for cat in "${!CATEGORY_COUNTS[@]}"; do
			printf '  %-16s %d\n' "$cat" "${CATEGORY_COUNTS[$cat]}" >&2
		done
		echo "" >&2
		echo "PII detected: $TOTAL_HITS match(es) across $(echo "${!CATEGORY_COUNTS[@]}" | wc -w) categor(ies)" >&2
	fi
	exit 1
else
	[[ $QUIET -eq 0 ]] && echo "OK no obvious PII found"
	exit 0
fi
