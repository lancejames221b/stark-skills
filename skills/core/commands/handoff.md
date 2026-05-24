---
description: "Bidirectional Discord handoff — post a status + read replies, or pick up where a prior session left off. Context ferry between Claude sessions across hosts."
argument-hint: "[channel] [message]  |  pickup  |  (no args → resume last)"
---

# Handoff

Post to a Discord channel AND pull recent replies — a relay that lets you hand work between Claude sessions (different boxes, different times) through Discord as the shared inbox.

Works on **gamez-linux**, **<INFERENCE_HOST>**, and **Mac**. Tokens and channel registry are resolved host-aware.

## Usage

`$ARGUMENTS` is parsed as: `[channel] [message...]`

**Sending:**
- `/handoff <VOICE_RUNTIME> shipped phase 0, need input on phase 1 scope` — post + read replies that follow
- `/handoff hud :file /tmp/shot.png here's the screenshot` — post with file attachment
- `/handoff <VOICE_RUNTIME> silent: heartbeat, nothing changed` — post without pinging

**Receiving:**
- `/handoff <VOICE_RUNTIME>` — read mode, shows last 30 messages + highlights new-since-bot
- `/handoff` (no args) — uses last active channel from local state, or defaults to `<VOICE_RUNTIME>`
- `/handoff pickup` — explicit pickup flow: read #<VOICE_RUNTIME>, summarize what's pending, identify user directives

**Well-known channels** (built-in, no registry lookup):
- `<VOICE_RUNTIME>` → `<DISCORD_CHANNEL_ID>`
- `hud` → `<DISCORD_CHANNEL_ID>`

Guild ID (JARVIS Server): `<DISCORD_CHANNEL_ID>` — used to build clickable channel/message URLs.

## Steps

### 1. Detect host

```bash
HOST=$(hostname -s 2>/dev/null || hostname)
case "$HOST" in
  <INFERENCE_HOST>*|*<INFERENCE_HOST>*) HOST_KIND=<INFERENCE_HOST> ;;
  <WORKSTATION_HOST>*|*<WORKSTATION_HOST>*)     HOST_KIND=<WORKSTATION_HOST> ;;
  *Mac*|*mac*|*.local) HOST_KIND=mac ;;
  *) HOST_KIND=unknown ;;
esac
```

### 2. Parse arguments

```bash
ARGS="$ARGUMENTS"
# Special subcommands
[ "$ARGS" = "pickup" ] && ARGS="<VOICE_RUNTIME>"

CHANNEL=$(printf '%s' "$ARGS" | cut -d' ' -f1)
MESSAGE=$(printf '%s' "$ARGS" | cut -s -d' ' -f2-)
```

### 3. Resolve channel ID

Built-in well-known channels first, then numeric IDs, then cache, then registry.

```bash
CACHE_FILE="$HOME/.config/jarvis-handoff/channels.json"
mkdir -p "$HOME/.config/jarvis-handoff"
[ -f "$CACHE_FILE" ] || echo '{"<VOICE_RUNTIME>":"<DISCORD_CHANNEL_ID>","hud":"<DISCORD_CHANNEL_ID>"}' > "$CACHE_FILE"

# No channel arg → resume from state
STATE_FILE="$HOME/.config/jarvis-handoff/state.json"
[ -f "$STATE_FILE" ] || echo '{}' > "$STATE_FILE"
if [ -z "$CHANNEL" ]; then
  CHANNEL_ID=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('activeChannelId',''))")
  CHANNEL=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('activeChannel','<VOICE_RUNTIME>'))")
  [ -z "$CHANNEL_ID" ] && CHANNEL_ID="<DISCORD_CHANNEL_ID>" && CHANNEL="<VOICE_RUNTIME>"
elif [[ "$CHANNEL" =~ ^[0-9]{17,20}$ ]]; then
  CHANNEL_ID="$CHANNEL"
else
  CHANNEL_ID=$(python3 -c "import json; d=json.load(open('$CACHE_FILE')); print(d.get('$CHANNEL',''))")
  # Fallback: registry lookup (local on <INFERENCE_HOST>, SSH from elsewhere)
  if [ -z "$CHANNEL_ID" ]; then
    REG_PATH="<LOCAL_PATH>/dev/contexts/channel-registry.json"
    RESOLVER="python3 -c \"
import json
d=json.load(open('$REG_PATH'))
q='$CHANNEL'.lower().lstrip('#')
for cid,v in d.items():
    if not isinstance(v,dict): continue
    name=v.get('name','').lower().lstrip('#')
    aliases=[a.lower().lstrip('#') for a in v.get('aliases',[])]
    if q==name or q in aliases: print(cid); break
\""
    if [ "$HOST_KIND" = <INFERENCE_HOST> ] && [ -f "$REG_PATH" ]; then
      CHANNEL_ID=$(eval "$RESOLVER" 2>/dev/null)
    else
      CHANNEL_ID=$(ssh -o BatchMode=yes -o ConnectTimeout=3 <INFERENCE_HOST> "$RESOLVER" 2>/dev/null)
    fi
    [ -n "$CHANNEL_ID" ] && python3 -c "import json; d=json.load(open('$CACHE_FILE')); d['$CHANNEL']='$CHANNEL_ID'; json.dump(d,open('$CACHE_FILE','w'))"
  fi
fi
[ -z "$CHANNEL_ID" ] && echo "Channel not found: $CHANNEL" && exit 1
```

### 4. Resolve bot token — host-aware, LAN/Tailscale-portable

Off-generic (gamez away from home, Mac anywhere, anywhere on the road), we need to reach `<INFERENCE_HOST>` regardless of whether you're on the home LAN or only on Tailscale. Try SSH targets in order: hostname alias → Tailscale IP. Whichever works first wins.

```bash
TOKEN=""
# 1. Env var (any host)
[ -n "$JARVIS_DISCORD_TOKEN" ] && TOKEN="$JARVIS_DISCORD_TOKEN"
# 2. Local cache (any host, written after first successful resolution)
[ -z "$TOKEN" ] && [ -f "$HOME/.config/jarvis-handoff/token" ] && \
  TOKEN=$(cat "$HOME/.config/jarvis-handoff/token")
# 3. Host-specific local sources
if [ -z "$TOKEN" ]; then
  case "$HOST_KIND" in
    <INFERENCE_HOST>)
      # On <INFERENCE_HOST> itself: read directly
      [ -f <LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env ] && \
        TOKEN=$(grep '^DISCORD_TOKEN=' <LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env | cut -d= -f2)
      [ -z "$TOKEN" ] && [ -f <LOCAL_PATH>/.<PROJECT_NAME>/config.json ] && \
        TOKEN=$(python3 -c "import json; print(json.load(open('<LOCAL_PATH>/.<PROJECT_NAME>/config.json'))['channels']['discord']['token'])" 2>/dev/null)
      ;;
    gamez| <MAC_HOST> |unknown)
      # Off <INFERENCE_HOST> — try LAN hostname, then Tailscale IP
      for TARGET in <INFERENCE_HOST> <TAILSCALE_IP>; do
        TOKEN=$(ssh -o BatchMode=yes -o ConnectTimeout=4 -o StrictHostKeyChecking=accept-new "$TARGET" \
          "grep '^DISCORD_TOKEN=' <LOCAL_PATH>/dev/<VOICE_RUNTIME>-voice/.env | cut -d= -f2" 2>/dev/null)
        if [ -n "$TOKEN" ]; then
          # Cache which target worked so the next call skips the failing ones
          python3 -c "
import json, os
p = '$HOME/.config/jarvis-handoff/reach.json'
json.dump({'generic_ssh': '$TARGET'}, open(p,'w'))
"
          break
        fi
      done
      ;;
  esac
fi
# Cache for future calls
[ -n "$TOKEN" ] && [ ! -f "$HOME/.config/jarvis-handoff/token" ] && \
  echo "$TOKEN" > "$HOME/.config/jarvis-handoff/token" && \
  chmod 600 "$HOME/.config/jarvis-handoff/token"
[ -z "$TOKEN" ] && echo "No bot token. Set JARVIS_DISCORD_TOKEN, or ensure 'ssh <INFERENCE_HOST>' / 'ssh <TAILSCALE_IP>' reaches the box." && exit 1
```

Same SSH pattern applies for the **registry lookup** in step 3 when falling back — use the cached working target if present:

```bash
REACH_FILE="$HOME/.config/jarvis-handoff/reach.json"
SSH_TARGET=$(python3 -c "import json; print(json.load(open('$REACH_FILE')).get('generic_ssh','generic'))" 2>/dev/null || echo "<INFERENCE_HOST>")
# Then when SSH-calling the registry:
ssh -o BatchMode=yes -o ConnectTimeout=3 "$SSH_TARGET" "..."
```

### 5. Optional post

```bash
USER_ID="<DISCORD_CHANNEL_ID>"
GUILD_ID="<DISCORD_CHANNEL_ID>"

if [ -n "$MESSAGE" ]; then
  # Extract optional file attachment: ":file /abs/path"
  FILE_PATH=""
  if [[ "$MESSAGE" =~ :file[[:space:]]+([^[:space:]]+) ]]; then
    FILE_PATH="${BASH_REMATCH[1]}"
    MESSAGE=$(echo "$MESSAGE" | sed -E "s|:file[[:space:]]+[^[:space:]]+||")
  fi

  # Strip silent: prefix → no ping
  PING="<@$USER_ID>"
  if [[ "$MESSAGE" == silent:* ]]; then
    PING=""
    MESSAGE=$(echo "$MESSAGE" | sed 's|^silent:[[:space:]]*||')
  fi

  BODY=$(python3 -c "
import json, sys
ping, msg = sys.argv[1], sys.argv[2]
sep = '\n\n' if ping else ''
print(json.dumps({'content': f'{ping}{sep}{msg}'}))
" "$PING" "$MESSAGE")

  if [ -n "$FILE_PATH" ]; then
    POST_RESP=$(curl -s -X POST \
      -H "Authorization: Bot $TOKEN" \
      -F "payload_json=$BODY" \
      -F "file=@$FILE_PATH" \
      "https://discord.com/api/v10/channels/$CHANNEL_ID/messages")
  else
    POST_RESP=$(curl -s -X POST \
      -H "Authorization: Bot $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$BODY" \
      "https://discord.com/api/v10/channels/$CHANNEL_ID/messages")
  fi
  echo "$POST_RESP" | GUILD_ID="$GUILD_ID" CHANNEL_ID="$CHANNEL_ID" python3 -c "
import json, sys, os
d = json.load(sys.stdin)
if 'id' in d:
    url = f\"https://discord.com/channels/{os.environ['GUILD_ID']}/{os.environ['CHANNEL_ID']}/{d['id']}\"
    print(f'POSTED → {url}')
else:
    print(f'ERR: {d}')
"

  # Record bot post timestamp so future pickups know what's "new since"
  python3 -c "
import json, time
s = json.load(open('$STATE_FILE'))
s['lastPostedAt'] = time.time()
s['activeChannel'] = '$CHANNEL'
s['activeChannelId'] = '$CHANNEL_ID'
json.dump(s, open('$STATE_FILE','w'), indent=2)
"
  sleep 2
fi
```

### 6. Fetch + present

Header shows a clickable Discord URL for the channel (ctrl/cmd-click in most terminals → opens the Discord app directly to that channel). Each message also gets a jump URL so you can click straight to it. Highlights messages **since the last bot post** so a picking-up session immediately sees what's new.

```bash
GUILD_ID="<DISCORD_CHANNEL_ID>"
LAST_POSTED=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('lastPostedAt',0))")

curl -s -H "Authorization: Bot $TOKEN" \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages?limit=30" | \
CHANNEL_NAME="$CHANNEL" CHANNEL_ID="$CHANNEL_ID" GUILD_ID="$GUILD_ID" LAST_POSTED="$LAST_POSTED" python3 -c "
import json, sys, os, datetime
msgs = json.load(sys.stdin)
if not isinstance(msgs, list):
    print('ERR:', json.dumps(msgs)); sys.exit(1)

ch_name = os.environ['CHANNEL_NAME']
ch_id   = os.environ['CHANNEL_ID']
gid     = os.environ['GUILD_ID']
ch_url  = f'https://discord.com/channels/{gid}/{ch_id}'

last_posted = float(os.environ.get('LAST_POSTED','') or 0)
new_since = []
all_msgs = []
for m in reversed(msgs):
    ts_iso = m.get('timestamp','')
    try:
        ts_epoch = datetime.datetime.fromisoformat(ts_iso.replace('Z','+00:00')).timestamp()
    except Exception:
        ts_epoch = 0
    is_bot = m.get('author',{}).get('bot', False)
    author = m.get('author',{}).get('username','?')
    content = (m.get('content','') or '').replace('\n', ' ↵ ')
    mid = m.get('id','')
    if not content and not m.get('attachments') and not m.get('embeds'):
        continue
    entry = (ts_iso[11:19], author, content[:400], m.get('attachments',[]), m.get('embeds',[]), mid)
    all_msgs.append(entry)
    if last_posted and ts_epoch > last_posted and not is_bot:
        new_since.append(entry)

print(f'─── #{ch_name} · {len(all_msgs)} msgs · {ch_url} ───')
for ts, author, content, atts, embeds, mid in all_msgs:
    jump = f'{ch_url}/{mid}'
    if content:
        print(f'[{ts}] {author}: {content}  ↗ {jump}')
    for a in atts:
        print(f'[{ts}] {author} ↳ file: {a.get(\"filename\")} ({a.get(\"url\",\"\")})')
    for e in embeds:
        t = e.get('title',''); d = (e.get('description') or '')[:160]
        if t or d: print(f'[{ts}] {author} ↳ embed: {t} — {d}')

if new_since:
    print()
    print(f'─── NEW SINCE LAST BOT POST ({len(new_since)}) · {ch_url} ───')
    for ts, author, content, _, _, mid in new_since:
        print(f'[{ts}] {author}: {content}  ↗ {ch_url}/{mid}')
    print()
    print('↑ If these contain a directive for you, act on it.')
"
```

### 7. Update active-channel state

```bash
python3 -c "
import json, time
s = json.load(open('$STATE_FILE'))
s['activeChannel'] = '$CHANNEL'
s['activeChannelId'] = '$CHANNEL_ID'
s['lastTouchedAt'] = time.strftime('%Y-%m-%dT%H:%M:%S')
json.dump(s, open('$STATE_FILE','w'), indent=2)
"
```

## Pickup flow

For the reverse direction — user wants a fresh session to continue work:

1. **User leaves a directive in Discord**: types (or voice-notes via <VOICE_RUNTIME>-voice) something like "continue phase 1" or "fix the bug from last session" in #<VOICE_RUNTIME>.

2. **New Claude session starts** (any host: <WORKSTATION_HOST>, <INFERENCE_HOST>, Mac).

3. **First thing Claude runs**: `/handoff pickup` (or just `/handoff` — defaults to <VOICE_RUNTIME>).

4. **Skill output shows**:
   - Last 30 messages of #<VOICE_RUNTIME> (full context)
   - A "NEW SINCE LAST BOT POST" block at the bottom listing the user's recent directives

5. **Claude acts on the directive** and can loop back with `/handoff <VOICE_RUNTIME> <status>` to continue the relay.

The local `state.json` per host remembers the last active channel, so `/handoff` with no args just continues the current relay without needing to retype the channel name.

## Notes

- State is **per-host** (`~/.config/jarvis-handoff/state.json`) — Discord itself is the cross-host source of truth.
- Token is cached locally at `~/.config/jarvis-handoff/token` (mode 0600) after first resolution.
- On Mac, ensure `ssh <INFERENCE_HOST>` works passwordlessly (key in agent). Otherwise set `JARVIS_DISCORD_TOKEN` env var once.
- `silent:` prefix logs progress without pinging — use for heartbeats.
- `:file /path` anywhere in the message attaches that file.
