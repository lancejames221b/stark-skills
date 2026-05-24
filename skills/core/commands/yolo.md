---
description: Toggle PI permission-system YOLO mode. YOLO=auto-approve all tool/bash/MCP calls. Guardrails (@aliou/pi-guardrails) remain on as a safety floor either way. Subcommands — on, off, toggle (default), status.
argument-hint: "[on|off|toggle|status]"
---

# /yolo — Toggle PI Permission YOLO

Run the following bash command exactly:

```bash
pi-yolo $ARGUMENTS
```

Where `$ARGUMENTS` is the user-supplied subcommand (defaults to `toggle` when empty).

After running, report the result line verbatim and remind the user that:

- **YOLO ON** → `~/.pi/agent/extensions/pi-permission-system/config.json` now has `permission.*: allow` — all tool/bash/MCP calls auto-approved.
- **YOLO OFF** → `permission.*: ask` — confirmation dialogs active.
- `@aliou/pi-guardrails` is independent and still flags rm -rf, secret files, and other dangerous patterns regardless of YOLO state.

Do **not** describe the script internals or run anything other than `pi-yolo $ARGUMENTS`.
