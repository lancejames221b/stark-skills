---
name: mcp-fix
description: MCP auto-recovery. When any mcporter/MCP call fails (timeout, auth error, server down, tool not found), diagnose and self-repair. Tries daemon restart, re-auth, service restart in sequence. If unresolved, spawns a dedicated fix sub-agent. Never surfaces MCP errors to <USER_NAME>without attempting repair first.
category: workflows
runtimes: [claude]
pii_safe: true
---

# mcp-fix — MCP Auto-Recovery Skill

**Trigger:** When ANY MCP call fails, returns an error, times out, or behaves unexpectedly.
**Action:** Diagnose → attempt automated repair → if unresolved, spawn a dedicated fix sub-agent.

---

## 1. Failure Detection Patterns

Recognise these as MCP failures requiring auto-repair:

| Signal | Meaning |
|--------|---------|
| `ENOENT` / `ECONNREFUSED` on socket | Daemon dead |
| `No server named <x>` | Server not registered in config |
| `Tool not found` | Wrong tool name or server offline |
| `Error: 401` / `invalid_token` / `auth required` | OAuth expired |
| `timeout` / `ETIMEDOUT` | Server hung / unreachable |
| `spawn ENOENT` | Binary missing (mcporter itself or server binary) |
| Empty / null result when data expected | Silent fail — treat as failure |
| `Stream closed unexpectedly` | Server crashed mid-call |
| Repeated `Command still running` with no output after 30s | Hung process |

---

## 2. Auto-Repair Playbook

Run these in order. Stop when one succeeds. Log each step.

### Step 1 — Daemon check & restart
```bash
mcporter daemon status
# If not running or error:
mcporter daemon restart
sleep 3
mcporter daemon status
```

### Step 2 — Re-test the failing call
```bash
mcporter call <failing-server>.<tool> [original args]
```
If succeeds → done. Report: "MCP daemon restart fixed it."

### Step 3 — Server-specific reconnect
```bash
# Kill the specific server process and let daemon respawn it
mcporter list --output json | grep -A5 '"name": "<server>"'
# Check status field. If "error" or "disconnected":
mcporter daemon restart
sleep 5
```

### Step 4 — Auth refresh (for OAuth servers)

OAuth servers: `notion-oauth`, `google-workspace`, `slack`, `linear`, `hubspot`, `figma`

```bash
# Check if auth is the issue (look for 401/403/token errors in output)
mcporter auth <server> --reset
# Follow prompts if interactive, or note that manual auth is needed
```

If `mcporter auth` requires interactive browser → **do not block**. Note it and spawn fix sub-agent (Step 5).

### Step 5 — Config integrity check
```bash
cat /media/<INFERENCE_HOST>/8f6026e4-4fcd-4f37-8815-807fdcb8a4043/DEV/config/mcporter.json | python3 -m json.tool > /dev/null && echo "JSON OK" || echo "INVALID JSON"
mcporter config list
```

### Step 6 — Binary / dependency check
```bash
which mcporter
mcporter --version
# For STDIO servers, check the binary path from config is present
```

---

## 3. Spawn Fix Sub-Agent (when auto-repair fails)

If steps 1-6 haven't resolved the issue, spawn a dedicated fix sub-agent:

```
sessions_spawn(
  task: "MCP service '<server>' is broken. Error: '<error_message>'. 
  Diagnose and fix using these steps:
  1. Run: mcporter daemon status
  2. Run: mcporter list --output json
  3. Check config: cat /media/<INFERENCE_HOST>/.../DEV/config/mcporter.json
  4. Attempt: mcporter daemon restart && sleep 5 && mcporter call <server>.<tool> [args]
  5. If auth issue: mcporter auth <server> --reset (note if interactive browser needed)
  6. If server binary missing: check the transport path in mcporter.json, verify file exists
  7. Post results to Discord channel <DISCORD_CHANNEL_ID> with status: FIXED / NEEDS_MANUAL / BROKEN
  8. Update ~/dev/contexts/soul-mcp.md with any new failure patterns discovered",
  model: "sonnet",
  thinking: "medium"
)
```

---

## 4. Known Server Configs

| Server | Transport | Auth Type | Common Fix |
|--------|-----------|-----------|------------|
| `haivemind` | HTTP | API key | Daemon restart |
| `google-workspace` | HTTP | OAuth | `mcporter auth google-workspace --reset` |
| `notion-oauth` | HTTP | OAuth | `mcporter auth notion-oauth --reset` |
| `slack` | HTTP | OAuth | `mcporter auth slack --reset` |
| `linear` | HTTP | OAuth | `mcporter auth linear --reset` |
| `virustotal` | STDIO | API key | Check `virustotal-mcp.service` |
| `playwright` | HTTP | None | `mcporter daemon restart` |
| `<PRODUCT_NAME>` | HTTP | None | Check <PRODUCT_NAME> service health |
| `wikipedia` | HTTP | None | Usually transient — retry |
| `trello` | HTTP | API key | Check key in config |
| `vibe-kanban` | HTTP | None | Port 14479 permanently offline — **use `~/dev/skills/vk-direct/scripts/vk.py` for all write ops** |

### VirusTotal Service
```bash
systemctl --user status virustotal-mcp.service
systemctl --user restart virustotal-mcp.service
```

### Config file location
```
/media/<INFERENCE_HOST>/8f6026e4-4fcd-4f37-8815-807fdcb8a4043/DEV/config/mcporter.json
```

---

## 5. Post-Fix Actions

After successful repair:
1. **Report briefly** — "MCP <server> was down. Fixed via daemon restart / re-auth." 
2. **Update soul-mcp.md** — add any new failure pattern to the Troubleshooting section
3. **Resume the original task** — re-execute what was originally requested
4. **Never surface the error to the user unless it couldn't be fixed** — plumbing stays invisible

If the fix required manual intervention (browser auth, config change):
- Report to user: "MCP <server> needs manual re-auth. Meanwhile I'll [alternative approach]."
- Attempt alternative (web_fetch, browser, exec-based workaround) while noting the outage

---

## 6. Self-Update Policy

When a new failure pattern is discovered and fixed, update this file:
```bash
# Add to Known Failure Patterns table in soul-mcp.md
echo "New pattern: [error] → [fix] (date)" >> /tmp/mcp-fix-log.txt
```

Then update `~/dev/contexts/soul-mcp.md` > Troubleshooting section.
