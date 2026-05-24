# Condensing Patterns

Safe transformations applied to bootstrap files while preserving all critical information.

## Whitespace Patterns

```
Multiple blank lines (3+) → Single blank line
Trailing spaces/tabs → Removed
Leading/trailing blank lines in sections → Normalized
```

## Verbose Phrase Replacements

| Original | Condensed |
|----------|-----------|
| "When you" | "When" |
| "You should" | "Should" / "" |
| "It is important to" | "" |
| "Make sure to" | "" |
| "Be sure to" | "" |
| "In order to" | "To" |
| "At this point" | "Now" |
| "It should be noted that" | "" |
| "Please note that" | "" |
| "Keep in mind that" | "" |
| "For example," | "Example:" |
| "(for example)" | "(e.g.)" |
| "and so on" | "etc." |
| "The following" | "These" |
| "As follows:" | ":" |
| "You can use" | "Use" |
| "In other words," | "" |

## List Condensing

**Before:**
```markdown
**When to search haivemind:**
- Session start (to get channel context)
- Before responding to any task that might have prior context
- When someone mentions a project, person, or past decision
- Before saying "I don't know" or "I don't have context"
- After compaction (to restore what was lost)
```

**After:**
```markdown
**Search when:** Session start | task with prior context | project/person/decision mention | before "I don't know" | after compaction
```

## Section Header Condensing

**Before:**
```markdown
### Post-Compaction Recovery (MANDATORY)
When you detect your context was compacted (summary at top instead of full history):
```

**After:**
```markdown
### Post-Compaction Recovery (MANDATORY)
When compacted (summary at top):
```

## Command Example Condensing

Keep essential syntax, remove explanatory prose:

**Before:**
```markdown
**Discord:**
```bash
# Use message tool to get recent messages
message action=read channel=discord channelId=[channel-id] limit=20
```

**After:**
```markdown
**Discord:** `message action=read channel=discord channelId=[id] limit=20`
```

## Multi-Step Process Condensing

**Before:**
```markdown
**STEP 1 - ALWAYS save context to haivemind FIRST:**
```
haivemind.store_memory content="RESET-CONTEXT channel=[channel-id] timestamp=[ISO-timestamp]: [summary]" category="global"
```

**STEP 2 - Confirm save completed:**
Reply: "Context saved. Ready for /reset."

**STEP 3 - On next session start, search for this:**
```
haivemind.search_memories query="RESET-CONTEXT channel=[channel-id]"
```
```

**After:**
```markdown
**NON-NEGOTIABLE:** `/reset` → ALWAYS save first
1. `haivemind.store_memory content="RESET-CONTEXT channel=[id] timestamp=[ISO]: [summary]" category="global"`
2. Reply: "Context saved. Ready for /reset."
3. Next session: `haivemind.search_memories query="RESET-CONTEXT channel=[id]"`
```

## Explanation Condensing

**Before:**
```markdown
**Why this matters:** WhatsApp has no message history API. Without this save, context is GONE after reset. This is the only way to maintain continuity.

This ensures continuity across resets even without message history access.
```

**After:**
```markdown
**Why:** WhatsApp no history API. Save = only way to maintain continuity.
```

## Never Condense

These must be preserved exactly:

1. **Commands** — All tool invocations (`mcporter call`, `message action=`, `browser`, `cron`)
2. **File paths** — (`contexts/`, `skills/`, `<LOCAL_PATH>/`)
3. **Critical markers** — (NON-NEGOTIABLE, MANDATORY, CRITICAL)
4. **Code blocks** — (Everything between \`\`\`)
5. **Origin dates** — (Origin: Feb X, 2026)
6. **Security rules** — (Boundaries, shield.md references)
7. **Channel IDs** — (<DISCORD_CHANNEL_ID>, C0ACEAKC0NA, etc.)
8. **Model names** — (anthropic/claude-sonnet-4-5, etc.)
9. **Workflow patterns** — (Step-by-step procedures)
10. **URLs and endpoints** — (http://..., https://...)

## Verification

After condensing, verify:

1. All command syntax preserved
2. All file paths intact
3. All critical markers present
4. All origin dates preserved
5. All security policies unchanged
6. All workflow steps complete
7. No functional information lost

## Success Metrics

- **Target:** Under 20,000 bytes per file
- **Typical savings:** 20-50% size reduction
- **Fidelity:** 100% — all critical content preserved
- **Readability:** Maintained or improved (less noise)
