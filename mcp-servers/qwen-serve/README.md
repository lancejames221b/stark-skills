# qwen-serve-mcp

A small MCP (Model Context Protocol) stdio server that is a thin shim over the
Qwen Code CLI's built-in HTTP daemon (`qwen serve --http-bridge`). It lets a
planner (for example Claude) drive a persistent qwen session and send each
bounded step as a follow-up into the same warm context.

The daemon owns ALL session, ACP, and state. This server does not implement its
own session store. It is roughly 250 lines of HTTP/SSE client plus a small
daemon lifecycle helper.

## What the qwen daemon does (verified live against qwen v0.17.0)

`qwen serve --http-bridge --port <P> --workspace <ABS_PATH>` starts an HTTP
daemon. Loopback (127.0.0.1) is auth-free unless you set `--token`,
`QWEN_SERVER_TOKEN`, or `--require-auth`. One daemon binds ONE workspace; for
multiple workspaces run one daemon per workspace on its own port.

Routes used by this shim (all confirmed by probing a running daemon):

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | `{"status":"ok"}` |
| POST | `/session` | body `{"cwd": ABS}` returns `{sessionId, workspaceCwd, attached, clientId, createdAt}`. A mismatched cwd returns HTTP 400 with `code: "workspace_mismatch"`. |
| POST | `/session/:id/prompt` | body MUST be `{"prompt": [{"type":"text","text": STR}]}` (an array of content blocks). A bare `{"prompt": STR}` is rejected (400, "must be a non-empty array of content blocks"). The POST blocks until the turn completes, then returns `{"stopReason": STR}` (for example `end_turn`). |
| GET | `/session/:id/events` | SSE stream. Each record is `id: N` / `event: session_update` / `data: <envelope>`. Honors the `Last-Event-ID` header for replay against the per-session ring (default depth 8000). Comment lines `: heartbeat` keep the stream alive. |
| DELETE | `/session/:id` | returns 204 and ends the session. |

There is NO session-list endpoint in this daemon version (`GET /sessions` is
404), so `qwen_session_list` reports only the sessions this MCP process started.

### SSE envelope shape (verified)

```
id: 23
event: session_update
data: {"id":23,"v":1,"type":"session_update","data":{"sessionId":"...","update":{"content":{"text":"pong","type":"text"},"sessionUpdate":"agent_message_chunk"}}}
```

`sessionUpdate` is one of `agent_thought_chunk` (model reasoning) or
`agent_message_chunk` (assistant output). This shim assembles assistant output
from `agent_message_chunk` text only and drops thought chunks. The final
message chunk carries a `_meta.usage` token tally.

## Tools

- `qwen_daemon_ensure({workspace, port?, model?, token?})` returns
  `{base_url, started, already_running, port, model}`. Starts the daemon
  detached (logs to `{workspace}/.qwen-runs/serve-<model>-<port>.log`) if
  `/health` is not already answering on the derived port, else reuses it. See
  "Model selection" below for how `model` maps to a port.
- `qwen_session_start({workspace, port?, model?, token?, system_prompt_append?})`
  returns `{session_id, base_url}`. Ensures a daemon for the
  `(workspace, model)` pair first, then POSTs `/session` on the daemon's
  derived port. The model is chosen here and fixed for the session's life. By
  default the built-in executor prompt (copied verbatim from `qwen-do.sh`) is
  applied as `system_prompt_append` on the first send. Pass an empty string to
  disable, or custom text to override.
- `qwen_session_send({session_id, prompt, base_url, token?, timeout_seconds?, files?})`
  returns `{output, status, elapsed_ms, stop_reason, last_step_block, error}`.
  POSTs the turn, drains the SSE stream until the turn completes, returns the
  assembled assistant text, and parses out the trailing `STEP - PASS|BLOCKED`
  block if present. The optional `files` list attaches multimodal inputs; see
  "Multimodal file input" below.

## Model selection (per session, fixed for the daemon's life)

The model is a DAEMON-level property here. `qwen serve --http-bridge` spawns one
`qwen --acp` child at boot, and that child is bound to one model. qwen-code
issue #3304 documents that switching the model mid-session causes API failures
(and #2015 reports ACP model-switch UI incompatibilities), so the rule is:
**a model is chosen when the daemon/session is created and is fixed for that
session's life. To change model, start a fresh daemon/session with the new
model.** There is no mid-session swap.

Because one daemon binds one `(workspace, model)` pair, this shim runs **one
daemon per `(workspace, model)` pair on distinct ports**. The port is derived
deterministically from the model id (`port_for_model()`): the default model
(`model` omitted) keeps the base port; any explicit model id hashes into
`[base_port + 1, base_port + 64]`. The same `(workspace, model)` always lands on
the same port, so re-ensuring reuses the running daemon; different models get
different ports and so different daemons. The model is passed to qwen as the
global `-m/--model` option placed before the `serve` subcommand (verified
against qwen v0.17.0: `qwen --help` lists `-m, --model`; `qwen serve --help`
does not, since it is a global option that the `serve` child inherits).

### Valid model ids

Model ids are whatever the configured backend serves. For the Mac LM Studio
backend the available ids include (full list is on the LM Studio server's
`/v1/models` endpoint):

- `qwen3.6-35b-a3b-mlx` (default)
- `qwen3-coder-next`
- `qwen3.6-27b-mlx`
- `qwen3.6-35b-a3b-claude-4.7-opus-reasoning-distilled-text-mlx-oq8`
- `glm-4.7-flash`
- `gemma-4-26b-a4b-it-mlx`

## Multimodal file input

`qwen_session_send` accepts an optional `files` list of ABSOLUTE file paths.
Each path is appended to the prompt as a qwen `@<abspath>` attachment
reference, which the daemon auto-encodes for PNG, JPEG, PDF, audio, and video.
This is the confirmed-working path (the prompt content array carries the
`@path` text). Every path is validated before the turn is sent: a path that is
missing or not absolute returns a clear error block listing the offending paths
(in `error`, `missing_files`, and `not_absolute_files`) rather than silently
dropping the attachment. Omitting `files` behaves exactly as before.
- `qwen_session_events({session_id, base_url, since_event_id?, token?, max_events?})`
  returns `{events, count}`. Bounded GET of the SSE stream for steering and
  inspection, with `Last-Event-ID` replay via `since_event_id`.
- `qwen_session_list({base_url?})` returns `{sessions, count}` (best-effort,
  this-process only, since the daemon has no list endpoint).
- `qwen_session_end({session_id, base_url, token?})` returns `{ended, session_id}`.

## Daemon lifecycle

`qwen_daemon_ensure` resolves `qwen` on PATH, then spawns
`qwen serve --http-bridge --port <P> --hostname 127.0.0.1 --workspace <ABS>`
detached in a new session (it outlives the MCP process), redirecting stdout and
stderr to `{workspace}/.qwen-runs/serve-<port>.log`. It polls `/health` until
the daemon answers (up to a startup timeout) or raises. If a daemon is already
healthy on the port it is reused. This shim never kills daemons (the planner
decides), and never bakes in any host, IP, or credential.

## Install and test

```
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/test_session_flow.py -v
# or, with no pytest:
.venv/bin/python tests/test_session_flow.py
```

Tests run against `tests/fake_qwen_serve.py`, a stdlib `http.server` that mimics
the verified routes and SSE shapes, so no real qwen or model is needed.

## Wire into Claude Code MCP settings

One-line entry under `mcpServers` in `~/.claude.json` (or a project
`.mcp.json`), pointing at the venv interpreter:

```json
{"mcpServers":{"qwen-serve":{"command":"/ABS/PATH/TO/stark-skills/mcp-servers/qwen-serve/.venv/bin/python","args":["-m","qwen_serve_mcp.server"]}}}
```

## Shape confirmation status

The prompt body and SSE event shapes above were confirmed live against a real
`qwen serve --http-bridge` daemon (v0.17.0), not just inferred. The
`QWEN_SERVE_BASE_URL` env var overrides the computed base URL (used by tests to
point at the fake, and usable to target an already-running remote daemon).
