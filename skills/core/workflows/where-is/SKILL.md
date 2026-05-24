---
name: where-is
description: Store and retrieve the physical location of items using hAIveMind. Triggers on "I put X in Y", "where is X", "where did I put X", "remember X is at Y", and similar natural-language item-location phrases.
category: workflows
runtimes: [claude]
pii_safe: true
---

# Where-Is Skill

<USER_NAME>can tell Jarvis where he put physical items, and ask where they are later. hAIveMind is the backend — no other storage.

---

## Triggers

### Store (<USER_NAME>is logging an item location)

| Phrase pattern | Example |
|---|---|
| "I put [item] in/on/at [location]" | "I put my passport in the top drawer of the bedroom dresser" |
| "I left [item] in/on/at [location]" | "I left my keys on the kitchen counter" |
| "remember that [item] is in/at [location]" | "remember that my charger is in the office nightstand" |
| "store that [item] is at/in [location]" | "store that my backup drive is in the safe" |
| "[item] is in/at [location]" (declarative) | "my sunglasses are in the car glove box" |
| "note that [item] is [location]" | "note that my watch is in the gym bag" |

### Retrieve (<USER_NAME>is asking for a location)

| Phrase pattern | Example |
|---|---|
| "where is my [item]?" | "where is my passport?" |
| "where's my [item]?" | "where's my charger?" |
| "where did I put [item]?" | "where did I put my keys?" |
| "find my [item]" | "find my backup drive" |
| "where did I leave [item]?" | "where did I leave my watch?" |
| "have you seen my [item]?" | "have you seen my sunglasses?" |

---

## Implementation

### Storing a Location

1. Extract `[item]` and `[location]` from the utterance.
2. Get current date with `date "+%Y-%m-%d"`.
3. Store to hAIveMind with category `locations`.
4. Speak confirmation.

```bash
# Step 1: Get date
DATE=$(date "+%Y-%m-%d")

# Step 2: Store
mcporter call haivemind.store_memory \
  content="ITEM-LOCATION: [item] is located at [location]. Stored ${DATE}." \
  category="locations"

# Step 3: Speak confirmation
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Got it, sir. I'\''ve noted that your [item] is in [location].","source":"where-is"}'
```

**Content format (strict):**
```
ITEM-LOCATION: [item] is located at [location]. Stored YYYY-MM-DD.
```

The `ITEM-LOCATION:` prefix is critical — it's the search anchor for retrieval.

---

### Retrieving a Location

1. Extract `[item]` from the utterance.
2. Search hAIveMind for the item.
3. Parse the result and speak it.

```bash
# Step 1: Search
mcporter call haivemind.search_memories query="ITEM-LOCATION [item]" limit=5
```

**Parse output:**
- If a match is found → extract the location from the content field and speak it.
- If no match → speak the "not found" response.

**Voice response — found:**
```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Your [item] is in [location], sir.","source":"where-is"}'
```

**Voice response — not found:**
```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"I don'\''t have a record of where you put your [item], sir.","source":"where-is"}'
```

---

## Multiple Results (Disambiguation)

If hAIveMind returns multiple matches (item was stored in different locations over time), prefer the **most recent** entry (latest `Stored YYYY-MM-DD` date in the content). Speak that one. No need to read all of them aloud unless <USER_NAME>asks.

Example: If passport was stored twice, read the newest.

---

## Examples

### Store flow

**<USER_NAME>says:** "I put my passport in the top drawer of the bedroom dresser"

```bash
DATE=$(date "+%Y-%m-%d")
mcporter call haivemind.store_memory \
  content="ITEM-LOCATION: passport is located at top drawer of the bedroom dresser. Stored ${DATE}." \
  category="locations"

curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Got it, sir. I'\''ve noted that your passport is in the top drawer of the bedroom dresser.","source":"where-is"}'
```

---

### Retrieve flow

**<USER_NAME>says:** "where's my passport?"

```bash
mcporter call haivemind.search_memories query="ITEM-LOCATION passport" limit=5
```

**hAIveMind returns:**
```
ITEM-LOCATION: passport is located at top drawer of the bedroom dresser. Stored 2026-02-21.
```

**Speak:**
```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Your passport is in the top drawer of the bedroom dresser, sir.","source":"where-is"}'
```

---

### Not found flow

**<USER_NAME>says:** "where did I put my car title?"

```bash
mcporter call haivemind.search_memories query="ITEM-LOCATION car title" limit=5
```

**hAIveMind returns:** no results

**Speak:**
```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"I don'\''t have a record of where you put your car title, sir.","source":"where-is"}'
```

---

## Voice Response Rules

- Always address <USER_NAME>as "sir" at the end.
- Keep responses under 20 words.
- Don't say "I have found" or "According to my records" — just state the location directly.
- Don't announce the date it was stored unless <USER_NAME>asks.
- Natural, direct: "Your keys are on the kitchen counter, sir."

---

## hAIveMind Notes

- Category: always `locations`
- Search prefix: always `ITEM-LOCATION` (prefix in query helps filter noise)
- `memory_search` tool is BROKEN — always use `mcporter call haivemind.search_memories`
- If mcporter fails: `mcporter daemon restart && sleep 3` then retry once

---

## Channel Registration

No channel registration required. This skill is globally active — it responds to voice/text triggers across all channels where Jarvis is listening. No per-channel opt-in needed.
