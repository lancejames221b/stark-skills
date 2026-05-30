"""HTTP/SSE client helpers for talking to a running `qwen serve --http-bridge`
daemon, plus daemon lifecycle helpers (ensure-running).

All wire shapes here were verified live against qwen v0.17.0
(qwen serve --http-bridge). See README for the captured envelopes.

Wire facts (verified):
  GET  /health                     returns {"status":"ok"}
  POST /session   {"cwd": ABS}     returns {"sessionId", "workspaceCwd",
                                       "attached", "clientId", "createdAt"}
                                      (400 code "workspace_mismatch" on cwd clash)
  POST /session/:id/prompt
       {"prompt": [{"type":"text","text": STR}]}
                                   blocks until turn done, then returns
                                       {"stopReason": STR}
       (a bare {"prompt": STR} is REJECTED: prompt must be a content-block array)
  GET  /session/:id/events         SSE, event: session_update, each carries
                                      id: N and a data envelope (see parse below).
                                      Honors Last-Event-ID header against the
                                      replay ring (default 8000 events).
  DELETE /session/:id              returns 204 (ends the session)

There is NO session-list endpoint in this daemon version (GET /sessions is 404),
so listing is best-effort over sessions this process started.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field

import httpx

DEFAULT_PORT = 4170
DEFAULT_HOST = "127.0.0.1"

# Width of the port window used to spread distinct (workspace, model) daemons
# off the base port. The default model lands on the base port itself; any other
# model deterministically maps into [base+1, base+PORT_WINDOW].
PORT_WINDOW = 64


def _safe_tag(model: str) -> str:
    """Reduce a model id to a filesystem-safe tag for log filenames."""
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in model)


def port_for_model(base_port: int, model: str | None) -> int:
    """Derive a stable daemon port for a model relative to a base port.

    A model is a DAEMON-level property in qwen serve (the daemon spawns one
    `qwen --acp` child bound to one model at boot, and qwen-code issue #3304
    forbids swapping the model mid-session). So one daemon serves exactly one
    (workspace, model) pair. To keep the SAME (workspace, model) reusing the
    SAME daemon while DIFFERENT models get DIFFERENT daemons, we map the model
    id deterministically onto a port offset:

      - model omitted (None) keeps the base port (the daemon's own default
        model, whatever qwen is configured to use).
      - any explicit model id hashes into [base_port + 1, base_port + PORT_WINDOW].

    The same id always yields the same port, so re-ensuring is idempotent.
    """
    if not model:
        return base_port
    digest = hashlib.sha256(model.encode("utf-8")).digest()
    offset = int.from_bytes(digest[:4], "big") % PORT_WINDOW
    return base_port + 1 + offset


def base_url_for(port: int, host: str = DEFAULT_HOST) -> str:
    """Build the daemon base URL, honoring a QWEN_SERVE_BASE_URL test override."""
    override = os.environ.get("QWEN_SERVE_BASE_URL")
    if override:
        return override.rstrip("/")
    return f"http://{host}:{port}"


def _auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def health_ok(base_url: str, token: str | None = None, timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(
            f"{base_url}/health", headers=_auth_headers(token), timeout=timeout
        )
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


@dataclass
class EnsureResult:
    base_url: str
    started: bool
    already_running: bool
    port: int
    model: str | None = None


def ensure_daemon(
    workspace: str,
    port: int = DEFAULT_PORT,
    token: str | None = None,
    host: str = DEFAULT_HOST,
    startup_timeout: float = 30.0,
    model: str | None = None,
) -> EnsureResult:
    """Start `qwen serve --http-bridge` for this (workspace, model) pair if
    /health is not already answering on the derived port; otherwise reuse the
    running daemon.

    The model is fixed for the life of a daemon (qwen-code issue #3304 forbids
    a mid-session model swap), so each distinct model gets its OWN daemon on its
    OWN port via port_for_model(). The model is passed to qwen as the global
    `-m/--model` option placed BEFORE the `serve` subcommand; the daemon's
    `qwen --acp` child inherits it. Passing model=None uses the supplied port
    as-is and lets qwen pick its configured default model.

    Runs detached (new session, output to {workspace}/.qwen-runs/
    serve-<model>-<port>.log). One daemon binds one (workspace, model) pair.
    """
    eff_port = port_for_model(port, model)
    base = base_url_for(eff_port, host)

    # If a test/remote override base URL is set, never spawn a process.
    if os.environ.get("QWEN_SERVE_BASE_URL"):
        return EnsureResult(
            base_url=base,
            started=False,
            already_running=True,
            port=eff_port,
            model=model,
        )

    if health_ok(base, token):
        return EnsureResult(
            base_url=base,
            started=False,
            already_running=True,
            port=eff_port,
            model=model,
        )

    qwen_bin = shutil.which("qwen")
    if not qwen_bin:
        raise RuntimeError(
            "qwen not on PATH: cannot start a daemon. Install @qwen-code/qwen-code, "
            "or point QWEN_SERVE_BASE_URL at an already-running daemon."
        )

    workspace = os.path.abspath(workspace)
    runs_dir = os.path.join(workspace, ".qwen-runs")
    os.makedirs(runs_dir, exist_ok=True)
    # Include model in the log filename so daemons for different models on the
    # same workspace do not clobber each other's logs.
    model_tag = _safe_tag(model) if model else "default"
    log_path = os.path.join(runs_dir, f"serve-{model_tag}-{eff_port}.log")

    # NOTE: `qwen serve` does NOT accept a --model flag, and a global -m/--model
    # before the `serve` subcommand is rejected as "Unknown argument: model" in
    # qwen 0.17.0 (verified live). The model is selected for the daemon's ACP
    # child via the QWEN_MODEL environment variable instead, which it inherits.
    # port_for_model() still gives each model its own daemon/port so a different
    # model never reuses a daemon bound to another model.
    cmd = [
        qwen_bin,
        "serve",
        "--http-bridge",
        "--port",
        str(eff_port),
        "--hostname",
        host,
        "--workspace",
        workspace,
    ]
    if token:
        cmd += ["--token", token]

    child_env = os.environ.copy()
    if model:
        child_env["QWEN_MODEL"] = model

    log_fh = open(log_path, "ab")
    log_fh.write(
        f"\n===== qwen-serve-mcp ensure_daemon {time.strftime('%Y-%m-%dT%H:%M:%S')} "
        f"port={eff_port} model={model or 'default'} workspace={workspace} =====\n".encode()
    )
    log_fh.flush()
    # Detach: new session so it outlives this MCP process; stdio to the log.
    subprocess.Popen(  # noqa: S603 (cmd is built from a resolved binary path)
        cmd,
        stdout=log_fh,
        stderr=log_fh,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        cwd=workspace,
        env=child_env,
    )

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if health_ok(base, token):
            return EnsureResult(
                base_url=base,
                started=True,
                already_running=False,
                port=eff_port,
                model=model,
            )
        time.sleep(0.4)

    raise RuntimeError(
        f"qwen daemon on {base} did not become healthy within {startup_timeout}s. "
        f"See {log_path}"
    )


@dataclass
class StartResult:
    session_id: str
    base_url: str
    raw: dict = field(default_factory=dict)


def start_session(
    base_url: str,
    workspace: str,
    token: str | None = None,
    timeout: float = 30.0,
) -> StartResult:
    """POST /session. The daemon is bound to one workspace; cwd must match it."""
    r = httpx.post(
        f"{base_url}/session",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        json={"cwd": os.path.abspath(workspace)},
        timeout=timeout,
    )
    if r.status_code == 400:
        try:
            body = r.json()
        except Exception:
            body = {"error": r.text}
        if body.get("code") == "workspace_mismatch":
            raise RuntimeError(
                "workspace_mismatch: daemon is bound to "
                f"{body.get('boundWorkspace')!r} but requested "
                f"{body.get('requestedWorkspace')!r}. Run a separate daemon "
                "on another port for this workspace."
            )
        raise RuntimeError(f"start_session failed (400): {body}")
    r.raise_for_status()
    data = r.json()
    return StartResult(session_id=data["sessionId"], base_url=base_url, raw=data)


class MissingFilesError(ValueError):
    """Raised when one or more requested file paths are missing or not absolute.

    Carries the offending paths so the caller can return a clear error block
    listing exactly what failed, instead of silently dropping attachments.
    """

    def __init__(self, missing: list[str], not_absolute: list[str]):
        self.missing = missing
        self.not_absolute = not_absolute
        parts = []
        if not_absolute:
            parts.append(f"not absolute: {not_absolute}")
        if missing:
            parts.append(f"does not exist: {missing}")
        super().__init__("; ".join(parts) or "invalid file paths")


def _content_blocks(
    prompt_text: str,
    system_prompt_append: str | None,
    files: list[str] | None = None,
) -> list[dict]:
    """Build the prompt content-block array. The daemon requires an array, not
    a bare string. We prepend any system_prompt_append as a leading text block
    so it rides in the same turn (the http-bridge has no separate system slot).

    Multimodal attachments are passed via qwen's `@<abspath>` notation, which
    the daemon auto-encodes for PNG, JPEG, PDF, audio, and video. Each `@path`
    reference is appended to the prompt text block (the confirmed-working path),
    so a missing file is never silently dropped. Validation happens in the
    caller via _validate_files() before this runs.
    """
    refs = ""
    if files:
        refs = "".join(f" @{os.path.abspath(p)}" for p in files)
    blocks: list[dict] = []
    if system_prompt_append:
        blocks.append({"type": "text", "text": system_prompt_append})
    blocks.append({"type": "text", "text": prompt_text + refs})
    return blocks


def _validate_files(files: list[str] | None) -> None:
    """Validate that every requested file path is absolute and exists. Raises
    MissingFilesError listing all offenders so nothing is silently dropped."""
    if not files:
        return
    not_absolute = [p for p in files if not os.path.isabs(p)]
    missing = [p for p in files if os.path.isabs(p) and not os.path.exists(p)]
    if missing or not_absolute:
        raise MissingFilesError(missing=missing, not_absolute=not_absolute)


@dataclass
class SendResult:
    output: str
    status: str  # "ok" | "timeout" | "error"
    elapsed_ms: int
    stop_reason: str | None = None
    last_step_block: str | None = None
    error: str | None = None


@dataclass
class FireResult:
    session_id: str
    base_url: str
    cursor_event_id: str | None  # last event id seen before the POST; use as since_event_id in poll calls
    status: str  # "fired" | "error"
    error: str | None = None


def _parse_step_block(text: str) -> str | None:
    """Pull the trailing 'STEP - PASS|BLOCKED' block out of assistant output."""
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped.startswith("STEP - ") or stripped.startswith("STEP -"):
            block = "\n".join(lines[i:]).strip()
            return block or None
    return None


def _iter_sse(resp: httpx.Response):
    """Yield (event_id, event_name, data_str) tuples from an SSE response.

    Handles multi-line data fields, comment/heartbeat lines (start with ':'),
    and blank-line record separators.
    """
    event_id: str | None = None
    event_name: str | None = None
    data_lines: list[str] = []
    for raw in resp.iter_lines():
        line = raw.rstrip("\n")
        if line == "":
            if data_lines or event_name:
                yield event_id, event_name, "\n".join(data_lines)
            event_id = None
            event_name = None
            data_lines = []
            continue
        if line.startswith(":"):
            # comment / heartbeat: surface a sentinel so callers can re-check
            # state (turn done? idle timeout?) between substantive events.
            yield None, "heartbeat", ""
            continue
        if line.startswith("id:"):
            event_id = line[3:].strip()
        elif line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines or event_name:
        yield event_id, event_name, "\n".join(data_lines)


def _extract_update(data_str: str):
    """Return (session_update_kind, text) for a session_update envelope, else
    (None, None). Envelope shape (verified):
      {"id":N,"v":1,"type":"session_update",
       "data":{"sessionId":...,"update":{
           "content":{"text":...,"type":"text"},
           "sessionUpdate":"agent_message_chunk"|"agent_thought_chunk"|...}}}
    """
    try:
        env = json.loads(data_str)
    except Exception:
        return None, None
    inner = env.get("data", env)
    update = inner.get("update") if isinstance(inner, dict) else None
    if not isinstance(update, dict):
        return None, None
    kind = update.get("sessionUpdate")
    content = update.get("content")
    text = ""
    if isinstance(content, dict):
        text = content.get("text", "") or ""
    return kind, text


def send_prompt(
    base_url: str,
    session_id: str,
    prompt_text: str,
    token: str | None = None,
    system_prompt_append: str | None = None,
    timeout_seconds: float = 600.0,
    files: list[str] | None = None,
) -> SendResult:
    """POST the turn and concurrently drain the SSE stream to collect assistant
    text. We assemble assistant_message text from `agent_message_chunk` updates
    (thought chunks are model reasoning and are excluded from output). The POST
    itself blocks until {"stopReason": ...}; we use that to know the turn ended.

    `files` is an optional list of ABSOLUTE paths; each is appended to the
    prompt as a qwen `@<abspath>` attachment reference. Missing or non-absolute
    paths raise MissingFilesError BEFORE anything is sent, so attachments are
    never silently dropped.
    """
    start = time.time()
    _validate_files(files)
    headers = {**_auth_headers(token), "Content-Type": "application/json"}
    body = {"prompt": _content_blocks(prompt_text, system_prompt_append, files)}

    assistant_parts: list[str] = []
    stop_reason: str | None = None
    status = "ok"
    error: str | None = None

    # Open the SSE stream first so we do not miss early chunks, then POST.
    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds, connect=10.0)) as c:
            with c.stream(
                "GET",
                f"{base_url}/session/{session_id}/events",
                headers=_auth_headers(token),
            ) as ev_resp:
                ev_resp.raise_for_status()
                # Fire the prompt (blocks until turn done) in a worker thread.
                import threading

                post_holder: dict = {}

                def _do_post():
                    try:
                        pr = httpx.post(
                            f"{base_url}/session/{session_id}/prompt",
                            headers=headers,
                            json=body,
                            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
                        )
                        post_holder["resp"] = pr
                    except Exception as e:  # noqa: BLE001
                        post_holder["error"] = e

                t = threading.Thread(target=_do_post, daemon=True)
                t.start()

                deadline = start + timeout_seconds
                for _id, name, data_str in _iter_sse(ev_resp):
                    if name == "session_update":
                        kind, text = _extract_update(data_str)
                        if kind == "agent_message_chunk" and text:
                            assistant_parts.append(text)
                    # Stop once the POST has returned a stopReason.
                    if "resp" in post_holder or "error" in post_holder:
                        if not t.is_alive():
                            break
                    if time.time() > deadline:
                        status = "timeout"
                        break

                t.join(timeout=max(0.0, deadline - time.time()))

        if "error" in post_holder:
            status = "error"
            error = str(post_holder["error"])
        elif "resp" in post_holder:
            pr = post_holder["resp"]
            if pr.status_code >= 400:
                status = "error"
                error = f"prompt POST {pr.status_code}: {pr.text}"
            else:
                try:
                    stop_reason = pr.json().get("stopReason")
                except Exception:
                    stop_reason = None
    except httpx.TimeoutException:
        status = "timeout"
    except Exception as e:  # noqa: BLE001
        status = "error"
        error = str(e)

    output = "".join(assistant_parts).strip()
    return SendResult(
        output=output,
        status=status,
        elapsed_ms=int((time.time() - start) * 1000),
        stop_reason=stop_reason,
        last_step_block=_parse_step_block(output),
        error=error,
    )


def fire_prompt(
    base_url: str,
    session_id: str,
    prompt_text: str,
    token: str | None = None,
    system_prompt_append: str | None = None,
    files: list[str] | None = None,
) -> FireResult:
    """POST the turn to start it, capture the SSE cursor just BEFORE the first
    chunk arrives, then return immediately without draining.

    The caller polls fetch_events(since_event_id=result.cursor_event_id) to
    read output chunks as they stream. Turn completion is signaled by an
    agent_turn_complete (or similar) event or when the polling loop sees no
    new events for an idle window.

    Returns FireResult. On error (e.g. POST rejected) status="error" with
    error set and cursor_event_id=None.
    """
    _validate_files(files)
    headers = {**_auth_headers(token), "Content-Type": "application/json"}
    body = {"prompt": _content_blocks(prompt_text, system_prompt_append, files)}

    # Grab the tail of the ring buffer to get a cursor BEFORE we fire, so
    # the caller's first poll only sees events generated by THIS turn.
    # fetch_events with a short idle_timeout drains buffered events quickly
    # and returns even on an idle session (heartbeats are skipped inside it).
    cursor: str | None = None
    try:
        tail = fetch_events(base_url, session_id, token=token, max_events=50, idle_timeout=1.5)
        for ev in tail:
            if ev.get("id") is not None:
                cursor = str(ev["id"])
    except Exception:
        pass  # cursor stays None; poll will replay full ring buffer (harmless)

    # Fire the POST in a daemon thread (we do NOT wait for it to complete).
    import threading

    def _do_post():
        try:
            httpx.post(
                f"{base_url}/session/{session_id}/prompt",
                headers=headers,
                json=body,
                timeout=httpx.Timeout(900.0, connect=10.0),
            )
        except Exception:
            pass

    threading.Thread(target=_do_post, daemon=True).start()

    return FireResult(
        session_id=session_id,
        base_url=base_url,
        cursor_event_id=cursor,
        status="fired",
    )


def fetch_events(
    base_url: str,
    session_id: str,
    since_event_id: str | None = None,
    token: str | None = None,
    max_events: int = 200,
    idle_timeout: float = 3.0,
) -> list[dict]:
    """GET /session/:id/events and return up to max_events parsed envelopes.

    Uses Last-Event-ID for replay-from when since_event_id is given. The stream
    is long-lived (heartbeats forever), so we stop after max_events or after an
    idle gap with no new events.
    """
    headers = _auth_headers(token)
    if since_event_id:
        headers["Last-Event-ID"] = str(since_event_id)

    events: list[dict] = []
    try:
        with httpx.Client(timeout=httpx.Timeout(idle_timeout + 2.0, connect=10.0)) as c:
            with c.stream(
                "GET",
                f"{base_url}/session/{session_id}/events",
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                last = time.time()
                for ev_id, name, data_str in _iter_sse(resp):
                    if name == "heartbeat" or (name is None and not data_str):
                        if time.time() - last > idle_timeout:
                            break
                        continue
                    parsed: dict = {"id": ev_id, "event": name}
                    try:
                        parsed["data"] = json.loads(data_str)
                    except Exception:
                        parsed["data"] = data_str
                    events.append(parsed)
                    last = time.time()
                    if len(events) >= max_events:
                        break
    except httpx.TimeoutException:
        pass
    except Exception:
        pass
    return events


def end_session(base_url: str, session_id: str, token: str | None = None) -> bool:
    """DELETE /session/:id. Returns True on 204/200."""
    try:
        r = httpx.delete(
            f"{base_url}/session/{session_id}",
            headers=_auth_headers(token),
            timeout=10.0,
        )
        return r.status_code in (200, 204)
    except Exception:
        return False
