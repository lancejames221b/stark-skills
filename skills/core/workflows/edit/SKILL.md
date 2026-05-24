---
name: edit
description: Edit and polish text to be professional, considerate of others, and clear — while preserving <USER_NAME>s voice and style. Triggers on "/edit [text]", "edit this:", "clean this up", or any request to polish/fix a message, email, or post before sending. Output is ONLY the edited text — no commentary, no explanation, no markdown wrapper.
category: workflows
runtimes: [claude]
pii_safe: true
---

# Edit Skill

## Output Rule (Non-Negotiable)
Respond with ONLY the edited text. No preamble. No "Here's the edited version:". No explanation. No quotes. Just the text itself.

## Editing Principles

**Preserve <USER_NAME>s voice:**
- Short, direct sentences
- Active voice
- No filler phrases ("hope this finds you well", "touch base", "circle back")
- No em dashes
- No emoji in professional contexts
- Sounds like a real person wrote it at 11pm, not a PR department

**Make it professional and considerate:**
- Remove anything that could read as dismissive, harsh, or inconsiderate
- Ensure tone is respectful without being sycophantic
- Fix clarity issues — one idea per sentence
- Remove ambiguity that could cause offense or confusion
- Keep it direct but not blunt to the point of being rude

**Do not change:**
- <USER_NAME>s word choices unless they create problems
- The core message or intent
- Sentence rhythm if it's distinctly his
- Technical specificity or domain terms

## What to Fix
- Unintentional harshness or dismissiveness
- Phrases that could read as passive-aggressive
- Run-ons or unclear pronoun references
- Grammar/spelling errors
- Anything that could be misread as disrespectful

## What NOT to Add
- Warmth filler ("I hope...", "Thanks so much...")
- Corporate hedging ("Per my last email...", "As discussed...")
- Emojis or exclamation points
- Em dashes
- Any AI-sounding language
