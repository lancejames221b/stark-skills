---
name: kanban
description: Use when user asks for the Cline Kanban passcode, password, access code, or asks to restart kanban. Pulls the latest passcode straight from the systemd journal so it's always current.
category: execution
runtimes: [claude]
pii_safe: true
---

# Cline Kanban Passcode

Cline Kanban runs as a systemd user service on <WORKSTATION_HOST> (port 3000, Tailscale-only). It generates a fresh passcode on every restart and prints it once to stdout. We grep the journal to find the latest one.

## Usage

```bash
kanban-pass          # Print current passcode + URL
kanban-pass restart  # Restart service, then print new passcode
kanban-pass status   # Show systemctl status
```

## Service details

- Unit: `kanban.service` (user unit)
- URL: `http://<TAILSCALE_IP>:3000/<PROJECT_NAME>`
- Tailscale IP: `<TAILSCALE_IP>`
- Port: `3000`

## How it finds the passcode

Greps `journalctl --user -u kanban --no-pager` for the most recent line matching `🔐 Remote access passcode:` and extracts the token after the colon. The most recent restart's passcode is the active one.

## Cleanup notes

- Old kanban runs sometimes leave zombie processes that block restart. The script uses `systemctl --user reset-failed kanban` after stop to clear failed state before restart.
- Process name appears as `2.1.123` (the kanban version) in `ps`.

## Script

`<LOCAL_PATH>/.local/bin/kanban-pass`
