---
description: Control <USER_NAME>s Mac iTerm from any machine via the pi-iterm wrapper. Use when running a command, reading output, or sending Ctrl-keys to the active iTerm tab on Mac.
argument-hint: "<exec|read|ctrl|do> <args...>"
---

# /iterm — Drive <USER_NAME>s Mac iTerm

You have a CLI wrapper `pi-iterm` available on this machine that controls <USER_NAME>s active Mac iTerm tab. It routes through `mcporter` on `<INFERENCE_HOST>`, which SSH-tunnels to Mac and calls `iterm-mcp` locally on Mac.

You also have the native MCP tool `mcp_iterm-mcp_*` (if loaded via the iterm-mcp MCP server in opencode.json). Prefer the native MCP if available; fall back to the `pi-iterm` shell wrapper otherwise.

## When to use

- User asks you to run a command in their iTerm / Mac terminal
- User asks for output of a recent command on Mac
- You need to interrupt a running process on Mac (Ctrl-C)
- You want to chain: execute → wait → read the result back

## When NOT to use

- For commands meant for the current machine — use the `bash` tool directly
- For long-running interactive sessions (vim, top, ssh inside iTerm) — output framing gets noisy; advise the user to run those manually

## Wrapper commands (`pi-iterm`)

```bash
pi-iterm exec <command>                 # send command, no wait/read
pi-iterm read [lines]                   # read last N lines (default 20)
pi-iterm ctrl <letter>                  # Ctrl-<letter>, e.g. C for SIGINT
pi-iterm do <command> [wait] [lines]    # exec + sleep + read (default wait=2s, lines=30)
pi-iterm help
```

## Examples

```bash
# Quickest pattern
pi-iterm do "git status" 1 20

# Slow command — wait longer
pi-iterm do "npm test" 30 100

# Interrupt
pi-iterm ctrl C

# Multi-step
pi-iterm exec "cd ~/Dev/<PROJECT_NAME> && python3 -m pytest tests/"
sleep 10
pi-iterm read 80
```

## Output reading rules

- `pi-iterm read` returns raw terminal text including the shell prompt (`┌──(lj㉿Mac)-[...]`); skip those when extracting actual output
- Default wait of 2s is for fast commands — bump for compiles, tests, network operations
- If output looks truncated, increase `lines`

## Safety

- **Always confirm with the user before destructive commands** (`rm -rf`, `git reset --hard`, `kill -9`, etc.) — `pi-iterm exec` runs IMMEDIATELY in <USER_NAME>s active tab
- Don't assume cwd; run `pi-iterm do "pwd"` first if it matters
- Don't send credentials/secrets — they appear in the iTerm scrollback

## Native MCP equivalent

If `mcp_iterm-mcp_*` tools are available in your toolset, they map 1:1:

| Wrapper | MCP Tool |
|---|---|
| `pi-iterm exec` | `mcp_iterm-mcp_write_to_terminal` |
| `pi-iterm read` | `mcp_iterm-mcp_read_terminal_output` |
| `pi-iterm ctrl` | `mcp_iterm-mcp_send_control_character` |

## Failure modes

- `ssh: connect to host <INFERENCE_HOST>` → Tailscale/generic offline
- `mcporter: server iterm-mcp offline` → Mac asleep or SSH unreachable
- Output stale → increase `wait` and `lines`
