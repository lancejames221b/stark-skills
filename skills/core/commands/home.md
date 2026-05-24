---
description: "Set context to HOME/LAN — full local network access, use LAN IPs"
---

# Location: HOME / LAN

You are now operating in **home/local network context**. Apply these rules for the rest of this session:

## Network rules
- LAN is fully reachable. Prefer LAN IPs for speed:
  - `max` / `<PRIVATE_IP>` — Mac M4
  - `<INFERENCE_HOST>` / `<PRIVATE_IP>` — RTX workstation
  - <WORKSTATION_HOST> = this machine at `<PRIVATE_IP>`
- Tailscale aliases (`max-ts`, `<INFERENCE_HOST>-ts`) also work but LAN is faster

## Service availability
- LM Studio on Mac: `http://<PRIVATE_IP>:1234/v1` — direct LAN, no tunnel needed
- Docker Model Runner on Mac: `http://localhost:12434/engines/v1` via SSH tunnel (or direct if exposed on 0.0.0.0)
- Docker Model Runner tunnel: `systemctl --user status docker-model-runner-mac.service`

## Reminder
Run `/mobile` to switch to Tailscale-only context when leaving home network.

## Arguments: $ARGUMENTS
