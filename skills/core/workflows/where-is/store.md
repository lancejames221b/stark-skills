# Where-Is: Store Template

Quick reference for storing an item location in hAIveMind.

---

## Command Template

```bash
DATE=$(date "+%Y-%m-%d")

mcporter call haivemind.store_memory \
  content="ITEM-LOCATION: [ITEM] is located at [LOCATION]. Stored ${DATE}." \
  category="locations"
```

---

## Speak Confirmation Template

```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Got it, sir. I'\''ve noted that your [ITEM] is in [LOCATION].","source":"where-is"}'
```

---

## Filled Examples

### Passport in bedroom dresser
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

### Keys on kitchen counter
```bash
DATE=$(date "+%Y-%m-%d")
mcporter call haivemind.store_memory \
  content="ITEM-LOCATION: keys is located at kitchen counter. Stored ${DATE}." \
  category="locations"

curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Got it, sir. I'\''ve noted that your keys are on the kitchen counter.","source":"where-is"}'
```

### Charger in office nightstand
```bash
DATE=$(date "+%Y-%m-%d")
mcporter call haivemind.store_memory \
  content="ITEM-LOCATION: charger is located at office nightstand. Stored ${DATE}." \
  category="locations"

curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Got it, sir. I'\''ve noted that your charger is in the office nightstand.","source":"where-is"}'
```

---

## Retrieve Template

```bash
mcporter call haivemind.search_memories query="ITEM-LOCATION [ITEM]" limit=5
```

Parse the `content` field from results. If found:

```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Your [ITEM] is in [LOCATION], sir.","source":"where-is"}'
```

If not found:

```bash
curl -s -X POST http://<TAILSCALE_IP>:3335/speak \
  -H 'Authorization: Bearer <HUD_POST_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"message":"I don'\''t have a record of where you put your [ITEM], sir.","source":"where-is"}'
```

---

## Content Format (Strict)

```
ITEM-LOCATION: [item] is located at [location]. Stored YYYY-MM-DD.
```

- Always use `ITEM-LOCATION:` prefix — this is the search anchor
- Category is always `locations`
- Date format: `YYYY-MM-DD`
- Item and location: lowercase, natural language, no quotes
