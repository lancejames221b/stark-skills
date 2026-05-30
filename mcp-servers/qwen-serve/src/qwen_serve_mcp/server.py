"""MCP stdio server exposing a thin set of tools over a `qwen serve
--http-bridge` daemon. qwen owns all session/ACP/state; this is a shim.

Tools:
  qwen_daemon_ensure({workspace, port?, token?})
  qwen_session_start({workspace, port?, token?, system_prompt_append?})
  qwen_session_send({session_id, prompt, base_url, token?, timeout_seconds?})
  qwen_session_events({session_id, base_url, since_event_id?, token?})
  qwen_session_list({base_url?})            (best-effort, this-process sessions)
  qwen_session_end({session_id, base_url, token?})
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from . import client
from .executor_prompt import EXECUTOR_SYSTEM_PROMPT

server = Server("qwen-serve-mcp")


@dataclass
class _Tracked:
    session_id: str
    base_url: str
    workspace: str


# Best-effort registry of sessions this process started (the daemon has no
# native list endpoint in qwen 0.17.0).
_SESSIONS: dict[str, _Tracked] = {}


def _ok(payload: dict) -> list[TextContent]:
    import json

    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="qwen_daemon_ensure",
            description=(
                "Ensure a `qwen serve --http-bridge` daemon is running for a "
                "(workspace, model) pair. Reuses one if /health already answers "
                "on the derived port, else starts one detached (logs to "
                "{workspace}/.qwen-runs/serve-<model>-<port>.log). One daemon "
                "binds one (workspace, model) pair: the model is fixed for the "
                "daemon's life (no mid-session swap, qwen-code issue #3304), so "
                "each distinct model gets its own daemon on its own derived "
                "port. Returns the effective base_url, port, and model."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {
                        "type": "string",
                        "description": "Absolute path of the workspace to bind.",
                    },
                    "port": {
                        "type": "integer",
                        "default": client.DEFAULT_PORT,
                        "description": "Base port. The chosen model is mapped to "
                        "a stable port relative to this base (the default model "
                        "uses the base port itself).",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model id the daemon binds at boot (passed "
                        "as qwen's global -m/--model). Fixed for the daemon's "
                        "life. Omit to use qwen's configured default. See README "
                        "for valid LM Studio model ids.",
                    },
                    "token": {
                        "type": "string",
                        "description": "Bearer token (only needed if the daemon "
                        "requires auth, e.g. non-loopback bind).",
                    },
                },
                "required": ["workspace"],
            },
        ),
        Tool(
            name="qwen_session_start",
            description=(
                "Start a persistent qwen session (POST /session). Ensures a "
                "daemon for the (workspace, model) pair first, then opens a "
                "session on it. Returns session_id and base_url. The model is "
                "chosen here and fixed for the session's life; to use a "
                "different model, start a fresh session with that model. The "
                "executor system prompt is applied by default as "
                "system_prompt_append on the first send; pass an empty string "
                "to disable, or custom text to override."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace": {"type": "string"},
                    "port": {"type": "integer", "default": client.DEFAULT_PORT},
                    "model": {
                        "type": "string",
                        "description": "Model id for this session's daemon "
                        "(fixed for the session's life). Omit for qwen's default. "
                        "See README for valid LM Studio model ids.",
                    },
                    "token": {"type": "string"},
                    "system_prompt_append": {
                        "type": "string",
                        "description": "Override the default executor prompt. "
                        "Omit to use the built-in executor prompt; pass empty "
                        "string to send no system preamble.",
                    },
                },
                "required": ["workspace"],
            },
        ),
        Tool(
            name="qwen_session_send",
            description=(
                "Send one bounded step into a warm session (POST /session/:id/"
                "prompt), drain the SSE stream until the turn completes, and "
                "return the assembled assistant text. Parses the trailing "
                "'STEP - PASS|BLOCKED' block if present. Optional `files` "
                "attaches multimodal inputs (PNG, JPEG, PDF, audio, video) via "
                "qwen's @path notation; each path must be absolute and exist, "
                "or the call returns an error listing the bad paths (never a "
                "silent drop)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "prompt": {"type": "string"},
                    "base_url": {"type": "string"},
                    "token": {"type": "string"},
                    "timeout_seconds": {"type": "number", "default": 600},
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional absolute file paths to attach "
                        "as @path multimodal references. Each must exist and be "
                        "absolute.",
                    },
                },
                "required": ["session_id", "prompt", "base_url"],
            },
        ),
        Tool(
            name="qwen_session_fire",
            description=(
                "Fire a prompt into a warm session WITHOUT blocking (non-blocking "
                "dispatch). POSTs the prompt to start the turn, returns immediately "
                "with a cursor_event_id. Poll qwen_session_events(since_event_id="
                "cursor_event_id) in a loop to stream output chunks. Use instead of "
                "qwen_session_send when you want visibility into long-running steps "
                "without a blocking wait."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "prompt": {"type": "string"},
                    "base_url": {"type": "string"},
                    "token": {"type": "string"},
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional absolute file paths to attach as @path multimodal references.",
                    },
                },
                "required": ["session_id", "prompt", "base_url"],
            },
        ),
        Tool(
            name="qwen_session_events",
            description=(
                "Fetch recent SSE events for a session (GET /session/:id/events), "
                "bounded, for steering/inspection. Supports since_event_id "
                "(Last-Event-ID replay)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "base_url": {"type": "string"},
                    "since_event_id": {"type": "string"},
                    "token": {"type": "string"},
                    "max_events": {"type": "integer", "default": 200},
                },
                "required": ["session_id", "base_url"],
            },
        ),
        Tool(
            name="qwen_session_list",
            description=(
                "List sessions this MCP process has started (best-effort: the "
                "daemon has no native list endpoint in qwen 0.17.0)."
            ),
            inputSchema={
                "type": "object",
                "properties": {"base_url": {"type": "string"}},
            },
        ),
        Tool(
            name="qwen_session_end",
            description="End a session (DELETE /session/:id).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "base_url": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["session_id", "base_url"],
            },
        ),
    ]


# Remember the system_prompt_append chosen at session_start so the first send
# can ride it into the turn. None means "use the default executor prompt".
_PENDING_SYSTEM: dict[str, str | None] = {}


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "qwen_daemon_ensure":
        res = await asyncio.to_thread(
            client.ensure_daemon,
            arguments["workspace"],
            int(arguments.get("port", client.DEFAULT_PORT)),
            arguments.get("token"),
            client.DEFAULT_HOST,
            30.0,
            arguments.get("model"),
        )
        return _ok(
            {
                "base_url": res.base_url,
                "started": res.started,
                "already_running": res.already_running,
                "port": res.port,
                "model": res.model,
            }
        )

    if name == "qwen_session_start":
        port = int(arguments.get("port", client.DEFAULT_PORT))
        token = arguments.get("token")
        model = arguments.get("model")
        # Ensure a daemon for this (workspace, model) pair, then open a session
        # on whatever port it derived (the model determines the daemon/port).
        ensured = await asyncio.to_thread(
            client.ensure_daemon,
            arguments["workspace"],
            port,
            token,
            client.DEFAULT_HOST,
            30.0,
            model,
        )
        base = ensured.base_url
        res = await asyncio.to_thread(
            client.start_session, base, arguments["workspace"], token
        )
        _SESSIONS[res.session_id] = _Tracked(
            session_id=res.session_id,
            base_url=base,
            workspace=arguments["workspace"],
        )
        # Resolve the system prompt: omitted means use the default executor
        # prompt; explicit (even empty) is used as given.
        if "system_prompt_append" in arguments:
            _PENDING_SYSTEM[res.session_id] = arguments["system_prompt_append"] or None
        else:
            _PENDING_SYSTEM[res.session_id] = EXECUTOR_SYSTEM_PROMPT
        return _ok({"session_id": res.session_id, "base_url": base})

    if name == "qwen_session_send":
        sid = arguments["session_id"]
        files = arguments.get("files")
        # Validate attachments up front so a bad path is a clear error, not a
        # silent drop and not a consumed pending-system prompt.
        try:
            client._validate_files(files)
        except client.MissingFilesError as e:
            return _ok(
                {
                    "output": "",
                    "status": "error",
                    "elapsed_ms": 0,
                    "stop_reason": None,
                    "last_step_block": None,
                    "error": f"invalid files: {e}",
                    "missing_files": e.missing,
                    "not_absolute_files": e.not_absolute,
                }
            )
        system_append = _PENDING_SYSTEM.pop(sid, None)
        res = await asyncio.to_thread(
            client.send_prompt,
            arguments["base_url"],
            sid,
            arguments["prompt"],
            arguments.get("token"),
            system_append,
            float(arguments.get("timeout_seconds", 600)),
            files,
        )
        return _ok(
            {
                "output": res.output,
                "status": res.status,
                "elapsed_ms": res.elapsed_ms,
                "stop_reason": res.stop_reason,
                "last_step_block": res.last_step_block,
                "error": res.error,
            }
        )

    if name == "qwen_session_fire":
        sid = arguments["session_id"]
        files = arguments.get("files")
        try:
            client._validate_files(files)
        except client.MissingFilesError as e:
            return _ok(
                {
                    "session_id": sid,
                    "cursor_event_id": None,
                    "status": "error",
                    "error": f"invalid files: {e}",
                }
            )
        system_append = _PENDING_SYSTEM.pop(sid, None)
        res = await asyncio.to_thread(
            client.fire_prompt,
            arguments["base_url"],
            sid,
            arguments["prompt"],
            arguments.get("token"),
            system_append,
            files,
        )
        return _ok(
            {
                "session_id": res.session_id,
                "cursor_event_id": res.cursor_event_id,
                "status": res.status,
                "error": res.error,
            }
        )

    if name == "qwen_session_events":
        events = await asyncio.to_thread(
            client.fetch_events,
            arguments["base_url"],
            arguments["session_id"],
            arguments.get("since_event_id"),
            arguments.get("token"),
            int(arguments.get("max_events", 200)),
        )
        return _ok({"events": events, "count": len(events)})

    if name == "qwen_session_list":
        base = arguments.get("base_url")
        sessions = [
            {"session_id": t.session_id, "base_url": t.base_url, "workspace": t.workspace}
            for t in _SESSIONS.values()
            if base is None or t.base_url == base
        ]
        return _ok({"sessions": sessions, "count": len(sessions)})

    if name == "qwen_session_end":
        sid = arguments["session_id"]
        ok = await asyncio.to_thread(
            client.end_session, arguments["base_url"], sid, arguments.get("token")
        )
        _SESSIONS.pop(sid, None)
        _PENDING_SYSTEM.pop(sid, None)
        return _ok({"ended": ok, "session_id": sid})

    return _ok({"error": f"unknown tool {name}"})


async def _amain() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
