# Voice Workflow Patterns

Voice-safe versions of workflows. All device names, room names, and identity values use placeholders.

## Core Principle

Voice responses must be concise and unambiguous. Private data, implementation details, and chat-specific context are stripped unless explicitly requested.

## 1. Voice Briefing

**Flow:** short spoken summary (≤30s) → optional detailed text follow-up.
**Skills used:** briefing, voice-handoff.

## 2. Voice Handoff

Transfer chat or session context into a voice assistant:

- Strip secrets, private implementation details, and direct links.
- Keep essential context: what's working, blockers, next actions.

## 3. Voice Command Grammar

**Planning:** "plan this task" / "review plan with me"
**Status:** "where am I at?" / "what's next?"
**Reminders:** "remind me in 10 minutes" / "check my todo list"
**Media:** "play music in kitchen" / "volume to 30%"

## 4. Voice Verification

Before speaking a definitive claim, verify:

- Source reliability (direct observation vs inferred).
- State uncertainty — "I believe X" → "I don't know where things stand with X."

## 5. Voice Home / Media Control (Placeholders)

**Speaker routing:** "read this in <ROOM_NAME>"
**Announcements:** "announce 'dinner is ready' to <HOUSEHOLD_MEMBERS>"
**Media playback:** "play <PLAYLIST> on <DEVICE_NAME>"
**Device commands:** "turn off <DEVICE_TYPE> in <ROOM_NAME>"

## 6. Accessibility Mode

- Concise responses, no jargon unless defined on screen first.
- Repeatable summaries (e.g., "Would you like me to repeat that?").
- Clear confirmation prompts for destructive actions:
  - "Are you sure you want to delete <ITEM>? I can't recover it once sent."
  - Wait for explicit "yes" or "proceed".

## Rules for Voice Skills

1. Separate spoken output from internal/private context in documentation.
2. No real phone numbers, device names, or private rooms in any skill file.
3. Voice outputs should be self-contained (not rely on screen context).
