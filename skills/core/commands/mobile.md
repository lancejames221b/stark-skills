---
description: "Set context to MOBILE/REMOTE — on Tailscale, no LAN access, use Tailscale IPs"
---

# Location: MOBILE / REMOTE

You are now operating in **mobile/remote context**. Apply these rules for the rest of this session:

## Network rules
- LAN IPs (192.168.1.x) are **unreachable**. Do not use them.
- Use Tailscale aliases only:
  - `max-ts` / `<TAILSCALE_IP>` — Mac M4
  - `<INFERENCE_HOST>-ts` / `<TAILSCALE_IP>` — RTX workstation
  - `<TAILSCALE_IP>` — <WORKSTATION_HOST> (this machine)
- All SSH commands must use `max-ts` or `<INFERENCE_HOST>-ts`, never `max` or `<INFERENCE_HOST>`
- Docker Model Runner: tunnel may be down — check before assuming it's reachable

## Service availability
- LM Studio on Mac (port 1234): **may be unreachable** if not on LAN — use Docker Model Runner tunnel instead
- Docker Model Runner tunnel: verify with `systemctl --user status docker-model-runner-mac.service`
- Restart tunnel if needed: `systemctl --user restart docker-model-runner-mac.service`

## Screen access
Even when remote, <USER_NAME>uses Chrome Remote Desktop to the Mac screen.
"On my screen" / `/on-screen` commands still work — target Mac as usual.

## Reminder
Run `/home` to switch back to local context when back on LAN.

## Arguments: $ARGUMENTS
