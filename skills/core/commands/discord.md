---
description: "Read Discord channel messages via Discord Bot API"
argument-hint: "Channel name (e.g. infra, <VOICE_RUNTIME>-voice, general)"
---

# Discord Channel Lookup

Read recent messages from a Discord channel: $ARGUMENTS

## Method

Use the Discord Bot API directly with the <PROJECT_NAME> bot token. Token is in `<LOCAL_PATH>/.<PROJECT_NAME>/config.json` under `channels.discord.token`.

## Steps

1. **Get bot token**:
   ```bash
   python3 -c "import json; c=json.load(open('<LOCAL_PATH>/.<PROJECT_NAME>/config.json')); print(c['channels']['discord']['token'])"
   ```

2. **Resolve channel ID**: Search `~/dev/contexts/channel-registry.json` for the channel name. Match against `name`, `aliases`, or partial name.
   ```bash
   python3 -c "
   import json
   d=json.load(open('<LOCAL_PATH>/dev/contexts/channel-registry.json'))
   q='$ARGUMENTS'.lower().lstrip('#')
   for cid, v in d.items():
       if not isinstance(v, dict): continue
       name = v.get('name','').lower().lstrip('#')
       aliases = [a.lower().lstrip('#') for a in v.get('aliases',[])]
       if q in name or q == cid or any(q in a for a in aliases):
           print(cid, v.get('name'), '-', v.get('purpose','')[:80])
   "
   ```

3. **Fetch messages via API**:
   ```bash
   BOT_TOKEN="<token>"
   CHANNEL_ID="<id>"
   curl -s -H "Authorization: Bot $BOT_TOKEN" \
     "https://discord.com/api/v10/channels/$CHANNEL_ID/messages?limit=50" | \
   python3 -c "
   import json,sys
   msgs = json.load(sys.stdin)
   if not isinstance(msgs, list):
       print('Error:', json.dumps(msgs))
       sys.exit(1)
   for m in reversed(msgs):
       ts = m.get('timestamp','')[:19].replace('T','  ')
       author = m.get('author',{}).get('username','?')
       content = m.get('content','')
       embeds = m.get('embeds',[])
       attachments = m.get('attachments',[])
       if content:
           print(f'[{ts}] {author}: {content[:300]}')
       for e in embeds:
           title = e.get('title','')
           desc = (e.get('description') or '')[:200]
           if title or desc:
               print(f'  [embed] {title}: {desc}')
       for a in attachments:
           print(f'  [file] {a.get(\"filename\")}')
   "
   ```

4. **Check <PROJECT_NAME> logs** for gateway errors:
   ```bash
   grep -i "discord\|error\|fail" <LOCAL_PATH>/.<PROJECT_NAME>/logs/gateway.log 2>/dev/null | tail -20
   ```

## Output

- Channel name, ID, and purpose from registry
- Last 50 messages with timestamps, senders, content
- Any JARVIS bot responses
- Flag unresolved incidents, open questions, or error loops
