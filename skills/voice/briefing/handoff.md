---
name: voice-style
description: General-purpose skill for mimicking any user's writing and speaking style. Configure per-user in a local voice-config file, then write attributed content (DMs, comments, emails) that sounds like them.
category: voice
runtimes: [claude, pi, opencode]
dependencies: []
---

# Voice Style Mimicry

Use this skill when you need to write anything attributed to a specific person — Slack messages, Discord replies, comments, drafts of emails, or any content that will appear as if they wrote it.

**Critical rule:** If the person reads your output and it sounds like an AI, you've blown their cover.

## How to configure per user

Create a local config file (never commit real configs): `~/.voice-config/<name>.yml`

```yaml
# ~/.voice-config/john-doe.yml — example, NEVER commit this file!
name: John Doe
voice_file: ~/.notes/john-doe-voice-samples.txt # his actual messages used as training
rules:
  - no_em_dashes
  - casual_openers
  - short_sentences
swear_context:
  casual: true # Slack DMs, Discord, voice transcription
  professional: false # client-facing, public comments
fallback: plain_english # when unsure of style, use plain English but keep it short
```

## Hard rules (apply to ALL users)

- **No em-dashes (—).** Use regular hyphens, commas, or start a new sentence.
- **No arrow symbols (→).** Write "to" or describe the change in words.
- **No "1:1" or "verbatim" stiffness.** Plain English.
- **No academic verbs:** "venturing", "drifting", "calibrated", "preserved", "accordingly", "consequently", "reframed", "additionally".
- **No multi-clause compound sentences.** Break into two short sentences.
- **NEVER change document formatting on edits.** Check rendered result and undo if needed.

## Voice analysis procedure (always do this first)

1. Run `/load` or memory load to get any saved voice samples for this user.
2. Read the user's most recent 20-30 messages if available (transcribed speech or typed replies).
3. Note these stylistic signals:
   - Sentence length (short/medium/long)
   - Common openers ("yeah", "alright", "fair point")
   - Verb choices (direct vs formal)
   - Swearing patterns and contexts
   - Capitalization quirks (lowercase product names, etc.)
   - Typical sign-offs or lack thereof

## Style guide (fill these in from the user's samples)

Replace the examples below with real patterns for the specific user. Write these into your local config file:

### Sentence length

- Typical: `[sample from user messages]`
- Max: `[usually 15 words or less before a new sentence]`

### Common openers

- `[e.g., "yeah", "okay", "alright"]`

### Verb style

- [e.g., prefers direct verbs: "rewrote" > "reframed", "killed" > "removed"]

### Swearing

- Casual context: [yes/no] — what kind of swearing? (heavy, light, none)
- Professional context: [yes/no] — when is it acceptable?
- Important nuance: [e.g., swears at machines, not people]

### Quirks

- Lowercase product names: [yes/no + examples]
- Trailing off vs wrapping up: [how they end responses]

## Examples — template (replace with real user samples)

### Sample 1

> "[paste actual message from the user here]"
> _Analysis: note lowercase, no em-dashes, casual opener_

### Sample 2

> "[paste another actual message]"
> _Analysis: note verb choice, sentence length_

## Professional vs casual rule of thumb

| Context                                      | Swearing?                                   | Tone                              |
| -------------------------------------------- | ------------------------------------------- | --------------------------------- |
| Internal Slack/Discord DMs                   | Per user's style guide                      | Casual                            |
| Voice transcription to assistants            | Per user's style guide                      | Natural                           |
| Public comments (Reddit, <GITHUB_ORG>, etc.) | No swearing unless user explicitly wants it | Casual but clean                  |
| Formal docs / client-facing copy             | No swearing                                 | Professional, still keep it short |

## Common mistakes that "sound AI"

- Overly structured sentences ("First, I would like to...")
- Explaining why instead of just saying it
- Perfect grammar that nobody actually talks like
- Overuse of transition words ("furthermore", "additionally")
- Too many qualifiers ("I think that maybe we could try")
- Ending every response with a neat summary sentence

## When in doubt

1. Re-read the user's most recent messages (last 5-10).
2. Check their voice config file for patterns you might have missed.
3. When still unsure, keep it short and direct — that's the safest bet for any real voice.
4. **Never** commit real voice samples or configs to the repo.
