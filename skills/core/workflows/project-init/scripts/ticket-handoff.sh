#!/usr/bin/env bash
# ticket-handoff.sh — Automates the completion protocol for a finished ticket.
#
# Usage:
#   ticket-handoff.sh TICKET_ID PROJECT_ID CHANNEL_ID RESULT COMMITS SUMMARY \
#     [FILES_CREATED] [FILES_MODIFIED] [KEY_DECISIONS] [NEXT_NEEDS] [BLOCKERS]
#
# Arguments:
#   TICKET_ID      — e.g. ENG-693
#   PROJECT_ID     — e.g. ENG-682
#   CHANNEL_ID     — Discord channel ID, e.g. <DISCORD_CHANNEL_ID>
#   RESULT         — success | partial | blocked
#   COMMITS        — Comma-separated short hashes, e.g. "f4a2b1c,9e3d7a2"
#   SUMMARY        — 1-3 sentence summary of what was done (quoted)
#   FILES_CREATED  — Comma-separated paths (optional, default: "none")
#   FILES_MODIFIED — Comma-separated paths (optional, default: "none")
#   KEY_DECISIONS  — Semicolon-separated decisions (optional, default: "none")
#   NEXT_NEEDS     — What the next ticket needs (optional, default: "none")
#   BLOCKERS       — Known blockers (optional, default: "none")
#
# Requires: mcporter, jq, grep, sed
#
# What it does:
#   1. Writes TICKET-DONE to hAIveMind
#   2. Appends handoff notes to contexts/[channel-id].md
#   3. Updates thread map status in the channel directive
#   4. Posts completion message to the ticket's thread (if thread ID found)
#   5. Posts priming message to the NEXT ticket's thread
#   6. Linear is READ-ONLY — ticket status tracked in hAIveMind + Notion only

set -euo pipefail

# --- Argument parsing ---
TICKET_ID="${1:?Usage: ticket-handoff.sh TICKET_ID PROJECT_ID CHANNEL_ID RESULT COMMITS SUMMARY}"
PROJECT_ID="${2:?Missing PROJECT_ID}"
CHANNEL_ID="${3:?Missing CHANNEL_ID}"
RESULT="${4:?Missing RESULT (success|partial|blocked)}"
COMMITS="${5:?Missing COMMITS}"
SUMMARY="${6:?Missing SUMMARY}"
FILES_CREATED="${7:-none}"
FILES_MODIFIED="${8:-none}"
KEY_DECISIONS="${9:-none}"
NEXT_NEEDS="${10:-none}"
BLOCKERS="${11:-none}"

TIMESTAMP=$(date -Iseconds)
DIRECTIVE="$HOME/dev/contexts/${CHANNEL_ID}.md"

# --- Validate ---
if [[ ! "$RESULT" =~ ^(success|partial|blocked)$ ]]; then
  echo "ERROR: RESULT must be success, partial, or blocked. Got: $RESULT" >&2
  exit 1
fi

if [[ ! -f "$DIRECTIVE" ]]; then
  echo "WARNING: Channel directive not found: $DIRECTIVE" >&2
  echo "Will create handoff entry in hAIveMind only." >&2
fi

# --- Status emoji ---
case "$RESULT" in
  success) STATUS_EMOJI="✅" ;;
  partial) STATUS_EMOJI="⚠️" ;;
  blocked) STATUS_EMOJI="🚫" ;;
esac

# =============================================================================
# Step 1: Write TICKET-DONE to hAIveMind
# =============================================================================
echo "→ Writing TICKET-DONE to hAIveMind..."

HAIVEMIND_CONTENT="TICKET-DONE ${PROJECT_ID} ${TICKET_ID} ${TIMESTAMP}: result=${RESULT} commits=${COMMITS} files_created=${FILES_CREATED} files_modified=${FILES_MODIFIED} key_decisions=${KEY_DECISIONS} next_ticket_needs=${NEXT_NEEDS} blockers=${BLOCKERS} summary=${SUMMARY}"

mcporter call haivemind.store_memory \
  content="$HAIVEMIND_CONTENT" \
  category="operations"

echo "  ✓ hAIveMind entry stored"

# =============================================================================
# Step 2: Append handoff notes to channel directive
# =============================================================================
if [[ -f "$DIRECTIVE" ]]; then
  echo "→ Updating channel directive: $DIRECTIVE"

  # Build the handoff note block
  HANDOFF_BLOCK="### ${TICKET_ID} ${STATUS_EMOJI}
- ${SUMMARY}
- Commits: \`${COMMITS}\`
- Files created: \`${FILES_CREATED}\`
- Files modified: \`${FILES_MODIFIED}\`"

  if [[ "$KEY_DECISIONS" != "none" ]]; then
    HANDOFF_BLOCK="${HANDOFF_BLOCK}
- Key decisions: ${KEY_DECISIONS}"
  fi

  if [[ "$NEXT_NEEDS" != "none" ]]; then
    HANDOFF_BLOCK="${HANDOFF_BLOCK}
- Next ticket needs: ${NEXT_NEEDS}"
  fi

  if [[ "$BLOCKERS" != "none" ]]; then
    HANDOFF_BLOCK="${HANDOFF_BLOCK}
- Blockers: ${BLOCKERS}"
  fi

  # Find and update the "In Progress" or placeholder entry for this ticket
  # If there's a placeholder like "### ENG-693 🔄 (In Progress)", replace it
  if grep -q "### ${TICKET_ID}" "$DIRECTIVE"; then
    # Replace existing entry — find from "### TICKET_ID" to next "###" or "##"
    # Use python for reliable multi-line replacement
    python3 -c "
import re, sys

with open('$DIRECTIVE', 'r') as f:
    content = f.read()

# Pattern: from '### ${TICKET_ID}' line to next '###' or '## ' heading
pattern = r'### ${TICKET_ID}[^\n]*\n(?:(?!###|## ).*\n)*'
replacement = '''${HANDOFF_BLOCK}
'''

content = re.sub(pattern, replacement, content)

with open('$DIRECTIVE', 'w') as f:
    f.write(content)
"
    echo "  ✓ Replaced existing entry for ${TICKET_ID}"
  else
    # Append after the last handoff note
    # Find "## Handoff Notes" section and append
    if grep -q "## Handoff Notes" "$DIRECTIVE"; then
      # Append before the next ## section after Handoff Notes
      python3 -c "
import re

with open('$DIRECTIVE', 'r') as f:
    content = f.read()

# Find the Handoff Notes section and append before the next ## heading
sections = content.split('## ')
for i, section in enumerate(sections):
    if section.startswith('Handoff Notes'):
        sections[i] = section.rstrip() + '\n\n${HANDOFF_BLOCK}\n\n'
        break

with open('$DIRECTIVE', 'w') as f:
    f.write('## '.join(sections))
"
      echo "  ✓ Appended new entry for ${TICKET_ID}"
    else
      # No Handoff Notes section — append at end
      echo "" >> "$DIRECTIVE"
      echo "## Handoff Notes" >> "$DIRECTIVE"
      echo "" >> "$DIRECTIVE"
      echo "$HANDOFF_BLOCK" >> "$DIRECTIVE"
      echo "  ✓ Created Handoff Notes section with ${TICKET_ID}"
    fi
  fi

  # Update thread map: change this ticket's status to Done
  if grep -q "${TICKET_ID}" "$DIRECTIVE"; then
    sed -i "s/| ${TICKET_ID} \(.*\)| 🔄 In Progress |/| ${TICKET_ID} \1| ${STATUS_EMOJI} Done |/" "$DIRECTIVE"
    sed -i "s/| ${TICKET_ID} \(.*\)| Up Next |/| ${TICKET_ID} \1| ${STATUS_EMOJI} Done |/" "$DIRECTIVE"
    echo "  ✓ Updated thread map status for ${TICKET_ID}"
  fi

  echo "  ✓ Channel directive updated"
fi

# =============================================================================
# Step 3: Find thread IDs from directive
# =============================================================================
THREAD_ID=""
NEXT_TICKET=""
NEXT_THREAD_ID=""

if [[ -f "$DIRECTIVE" ]]; then
  # Extract this ticket's thread ID from the thread map table
  THREAD_ID=$(grep "| ${TICKET_ID} " "$DIRECTIVE" | grep -oP '\| (\d{15,20}) \|' | head -1 | tr -d '| ' || true)

  if [[ -z "$THREAD_ID" ]]; then
    # Try alternate format
    THREAD_ID=$(grep "| ${TICKET_ID}" "$DIRECTIVE" | grep -oP '\d{15,20}' | head -1 || true)
  fi

  # Find the NEXT ticket (the ticket after this one in the thread map)
  # Extract ticket IDs in order from the thread map
  TICKET_LIST=$(grep -oP 'ENG-\d+' "$DIRECTIVE" | grep -v "$PROJECT_ID" | sort -t- -k2 -n | uniq)
  FOUND_CURRENT=false

  while IFS= read -r tid; do
    if $FOUND_CURRENT; then
      NEXT_TICKET="$tid"
      break
    fi
    if [[ "$tid" == "$TICKET_ID" ]]; then
      FOUND_CURRENT=true
    fi
  done <<< "$TICKET_LIST"

  if [[ -n "$NEXT_TICKET" ]]; then
    NEXT_THREAD_ID=$(grep "| ${NEXT_TICKET}" "$DIRECTIVE" | grep -oP '\d{15,20}' | head -1 || true)
    echo "  → Next ticket: ${NEXT_TICKET} (thread: ${NEXT_THREAD_ID:-unknown})"

    # Update the next ticket's status to "Up Next" → "🔄 Ready"
    sed -i "s/| ${NEXT_TICKET} \(.*\)| Up Next |/| ${NEXT_TICKET} \1| 🔄 Ready |/" "$DIRECTIVE"
  fi

  # Update Active Work section
  if [[ -n "$NEXT_TICKET" ]]; then
    sed -i "s/^- Current: ${TICKET_ID}/- Current: ${NEXT_TICKET}/" "$DIRECTIVE"
  fi
fi

echo "  Thread ID: ${THREAD_ID:-not found}"
echo "  Next ticket: ${NEXT_TICKET:-none}"
echo "  Next thread: ${NEXT_THREAD_ID:-not found}"

# =============================================================================
# Step 4: Post completion message to ticket's thread (via mcporter/message tool)
# =============================================================================
# Note: This step outputs the message content. The calling agent should post it
# using the message tool, since bash can't directly call the OpenClaw message tool.

COMPLETION_MSG="## ${STATUS_EMOJI} ${TICKET_ID} Complete

**Result:** ${RESULT}
**Commits:** \`${COMMITS}\`

**What was done:**
${SUMMARY}

**Files:**
- Created: \`${FILES_CREATED}\`
- Modified: \`${FILES_MODIFIED}\`"

if [[ "$KEY_DECISIONS" != "none" ]]; then
  COMPLETION_MSG="${COMPLETION_MSG}

**Key decisions:**
${KEY_DECISIONS}"
fi

if [[ -n "$NEXT_TICKET" && "$NEXT_NEEDS" != "none" ]]; then
  COMPLETION_MSG="${COMPLETION_MSG}

**What ${NEXT_TICKET} needs to know:**
${NEXT_NEEDS}"
fi

echo ""
echo "=== COMPLETION MESSAGE (post to thread ${THREAD_ID:-UNKNOWN}) ==="
echo "$COMPLETION_MSG"
echo "=== END COMPLETION MESSAGE ==="

# =============================================================================
# Step 5: Build priming message for NEXT thread
# =============================================================================
if [[ -n "$NEXT_TICKET" && -n "$NEXT_THREAD_ID" ]]; then
  PRIMING_MSG="## 🔗 Handoff from ${TICKET_ID}

${TICKET_ID} is done. Here's what you need to know:

**What was accomplished:** ${SUMMARY}
**Commits:** \`${COMMITS}\`

**What YOU need:**
${NEXT_NEEDS}

**Context restore:**
\`\`\`bash
mcporter call haivemind.search_memories query=\"TICKET-DONE ${PROJECT_ID}\" limit=20
cat ~/dev/contexts/${CHANNEL_ID}.md
\`\`\`

Ready to start? Reply 'go' or 'start'."

  echo ""
  echo "=== PRIMING MESSAGE (post to thread ${NEXT_THREAD_ID}) ==="
  echo "$PRIMING_MSG"
  echo "=== END PRIMING MESSAGE ==="
fi

# =============================================================================
# Step 6: Update ticket state (Notion — Linear is READ-ONLY as of 2026-03-02)
# =============================================================================
echo ""
echo "→ Ticket tracking update (Linear is read-only — status tracked in Notion/hAIveMind only)"
echo "  NOTE: Linear is locked to read-only. Do NOT call linear.save_issue or linear.update_issue."
echo "  Ticket status is tracked via hAIveMind (TICKET-DONE above) and the channel directive."
echo "  If a Notion board page exists for this project, update the ticket card there."
echo "  ✓ Skipped Linear write (read-only enforcement)"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "════════════════════════════════════════"
echo "  Handoff complete for ${TICKET_ID}"
echo "════════════════════════════════════════"
echo "  hAIveMind:  ✓ TICKET-DONE stored"
echo "  Directive:  $([ -f "$DIRECTIVE" ] && echo "✓ Updated" || echo "⚠ Not found")"
echo "  Linear:     ✗ Skipped (read-only — status in hAIveMind + Notion)"
echo "  Next:       ${NEXT_TICKET:-none}"
echo ""
echo "AGENT TODO (cannot be done from bash):"
echo "  1. Post completion message to thread ${THREAD_ID:-UNKNOWN}"
echo "  2. Post priming message to thread ${NEXT_THREAD_ID:-UNKNOWN}"
echo "  3. Update thread name: message action=channel-edit channelId=${THREAD_ID:-UNKNOWN} name=\"${STATUS_EMOJI} ${TICKET_ID} | ...\""
echo "  4. Post brief notice in parent channel ${CHANNEL_ID}"
echo "  5. Update Notion page ticket status"
echo "════════════════════════════════════════"
