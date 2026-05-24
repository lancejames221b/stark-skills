---
name: note-to-self
description: Send a note to <USER_NAME>s own Signal number (<PHONE_NUMBER>). Triggers on "note to self", "remind me", "jot this down", "send this to my Signal", "DM myself", "note:", or any phrasing that means <USER_NAME>wants to capture something for himself. No approval needed — sending to own number only.
category: memory
runtimes: [claude]
pii_safe: true
---

# note-to-self Skill

Send a Signal note to <USER_NAME>s own number (<PHONE_NUMBER>) via the local signald RPC.

## Trigger Phrases

- "note to self: [content]"
- "note to self [content]"
- "jot this down: [content]"
- "remind me [content]"
- "send this to my Signal"
- "DM myself [content]"
- "save this to Signal"
- "ping myself [content]"

## How to Execute

```bash
bash <LOCAL_PATH>/dev/scripts/mac-signal.sh "<PHONE_NUMBER>" "[message]"
```

Or inline via curl:

```bash
curl -s http://localhost:8086/api/v1/rpc -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"send","id":1,"params":{"account":"<PHONE_NUMBER>","recipients":["<PHONE_NUMBER>"],"message":"[message]"}}'
```

## Rules

- **No approval needed** — self-delivery exception (SOUL.md: messages to <PHONE_NUMBER> exempt from draft-then-approve)
- Send immediately, confirm to <USER_NAME>in Discord
- Keep the message as-is — don't reformat or summarize unless asked
- If <USER_NAME>says "note to self: [X]", the Signal message body is just X

## Example

<USER_NAME>Note to self: pick up meds on the way home"
Action: Send "pick up meds on the way home" to <PHONE_NUMBER> via Signal RPC
Reply: "Sent to your Signal."

## Infrastructure

- **RPC:** `http://localhost:8086/api/v1/rpc` (signal-logger.service — always active)
- **Script:** `~/dev/scripts/mac-signal.sh`
- **<USER_NAME>s Signal number:** <PHONE_NUMBER> (also `<SIGNAL_HANDLE>` on Signal)
