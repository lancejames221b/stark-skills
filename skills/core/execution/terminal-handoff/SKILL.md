---
name: terminal-handoff
description: Hand off the current terminal Claude session into a Discord channel so the user can continue on mobile. Use when the user says "hand off to [channel]", "send this to [channel]", "continue in [channel]", or wants to take the conversation to Discord.
category: execution
runtimes: [claude]
pii_safe: true
voice: false
---

# terminal-handoff

When the user wants to continue the current terminal conversation in a Discord channel — voicing any of:

- "hand off this to [channel]"
- "hand off to [channel]"
- "send this to [channel] in Discord"
- "continue in [channel]"
- "pop this into Discord / [channel]"

Run the local `handoff` command to push the session up and open a thread in the target channel. Jarvis will:
1. rsync this session's `.jsonl` to <INFERENCE_HOST> (where the gateway lives)
2. Create a new thread in the target channel with a seed message
3. Register the session against that thread's channelKey
4. Enable verbose mode for that thread (live-streaming)

## Invocation

```bash
handoff here <channel-name-or-id> [--model <name>] [topic...]
```

- `<channel-name-or-id>` — either a registry-known channel name like `<INTERNAL_SERVICE_HOST>`, or the numeric Discord channel ID
- `--model <name>` — optional model override. Accepts shortcuts: `opus`, `sonnet`, `haiku`, or full names like `claude-opus-4-7`. When set, it pins the model for that Discord thread AND parent channel, so the next @mention there uses that model instead of the global default. **Use `opus` for sessions with heavy context (>200k tokens) — Sonnet's smaller window can't handle them.**
- `[topic...]` — optional free-form words to name the new thread (e.g. `"proxy debug continued"`)

### Natural-language model selection

If the user says "hand off this to <INTERNAL_SERVICE_HOST> **using opus**" or "send to #hud **on opus**" or "**with opus**", pass `--model opus` to the command. Same for "sonnet" / "haiku".

The script auto-detects the current session's chatId (newest `.jsonl` in the current project dir). Run from the SAME working directory where the session lives.

## Examples

User: *"Hand this off to <INTERNAL_SERVICE_HOST>."*
→ `handoff here <INTERNAL_SERVICE_HOST>`

User: *"Send this to eng-chat, topic: proxy retry logic."*
→ `handoff here eng-chat "proxy retry logic"`

User: *"Continue in #hud."*
→ `handoff here hud`

User: *"Hand off to <INTERNAL_SERVICE_HOST> using opus."*
→ `handoff here <INTERNAL_SERVICE_HOST> --model opus`

User: *"Send this to #hud on opus, topic: handoff system."*
→ `handoff here hud --model opus "handoff system"`

## Registry lookup

Channel names live in `~/dev/contexts/channel-registry.json`. If the name isn't there, the script will fail with a clear message. Fall back: ask the user for the numeric channel ID or add the name to the registry first.

## After handoff

The script prints the new threadId. User can open `https://discord.com/channels/<guild>/<threadId>` or just look for the `🔗 …` thread in the channel. They can @mention Jarvis in that thread to continue the exact session, with live verbose streaming.

No extra steps. The session state is shared — work you did in terminal is visible to Jarvis in the new thread on the next @mention.
