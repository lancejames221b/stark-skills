"""A tiny stdlib http.server that mimics the qwen serve --http-bridge daemon
closely enough to test the MCP client without a real qwen / model.

Implements the verified routes and wire shapes:
  GET    /health                  returns {"status":"ok"}
  POST   /session  {"cwd": ABS}   returns {"sessionId", "workspaceCwd",
                                      "attached", "clientId", "createdAt"}
                                     (400 code "workspace_mismatch" on clash)
  POST   /session/:id/prompt
         {"prompt":[{"type":"text","text": STR}]}
                                  emits SSE updates on the events stream, then
                                     returns {"stopReason":"end_turn"}
                                     (a bare {"prompt": STR} returns 400)
  GET    /session/:id/events      SSE session_update stream, supports
                                     Last-Event-ID replay against a ring.
  DELETE /session/:id             returns 204

Run standalone for manual poking:
    python tests/fake_qwen_serve.py --port 4191 --workspace /tmp/ws
"""

from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeState:
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.sessions: dict[str, dict] = {}
        self.lock = threading.Lock()
        # Records the raw prompt content-block array of the last accepted turn,
        # so tests can assert that @path refs / file blocks reached the request.
        self.last_prompt: list | None = None

    def new_session(self) -> dict:
        sid = str(uuid.uuid4())
        sess = {
            "sessionId": sid,
            "workspaceCwd": self.workspace,
            "attached": False,
            "clientId": "client_" + uuid.uuid4().hex,
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            # ring of (id, event_name, data_dict); subscribers get live + replay
            "ring": [],
            "next_id": 1,
            "subscribers": [],  # list[queue.Queue]
        }
        with self.lock:
            self.sessions[sid] = sess
        return sess

    def _emit(self, sess: dict, update: dict) -> None:
        with self.lock:
            eid = sess["next_id"]
            sess["next_id"] += 1
            envelope = {
                "id": eid,
                "v": 1,
                "type": "session_update",
                "data": {"sessionId": sess["sessionId"], "update": update},
            }
            sess["ring"].append((eid, "session_update", envelope))
            for q in list(sess["subscribers"]):
                q.put((eid, "session_update", envelope))

    def run_turn(self, sess: dict, prompt_text: str) -> None:
        """Emit a small thought + message stream, mimicking real chunking."""
        for tok in ["Thinking", " about", " it."]:
            self._emit(
                sess,
                {
                    "content": {"text": tok, "type": "text"},
                    "sessionUpdate": "agent_thought_chunk",
                },
            )
            time.sleep(0.01)
        reply = f"echo: {prompt_text}\n\nSTEP - PASS\nCommands run: none\nKey numbers: none\nSurprises / deviations: none\nFiles changed: none"
        for piece in [reply[i : i + 16] for i in range(0, len(reply), 16)]:
            self._emit(
                sess,
                {
                    "content": {"text": piece, "type": "text"},
                    "sessionUpdate": "agent_message_chunk",
                },
            )
            time.sleep(0.01)
        # final meta chunk like the real daemon
        self._emit(
            sess,
            {
                "_meta": {
                    "usage": {
                        "inputTokens": 10,
                        "outputTokens": len(reply),
                        "totalTokens": 10 + len(reply),
                    },
                    "durationMs": 5,
                },
                "content": {"text": "", "type": "text"},
                "sessionUpdate": "agent_message_chunk",
            },
        )


def make_handler(state: FakeState):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):  # silence
            pass

        def _json(self, code: int, obj: dict):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if not length:
                return {}
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):
            if self.path == "/health":
                return self._json(200, {"status": "ok"})
            if self.path == "/last-prompt":
                # Debug-only route (not part of the real daemon) so tests can
                # inspect the exact content-block array the last turn carried.
                return self._json(200, {"prompt": state.last_prompt})
            if self.path.startswith("/session/") and self.path.endswith("/events"):
                sid = self.path.split("/")[2]
                sess = state.sessions.get(sid)
                if not sess:
                    return self._json(404, {"error": "no session"})
                return self._stream_events(sess)
            return self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path == "/session":
                body = self._read_body()
                cwd = body.get("cwd")
                if cwd != state.workspace:
                    return self._json(
                        400,
                        {
                            "error": "Workspace mismatch",
                            "code": "workspace_mismatch",
                            "boundWorkspace": state.workspace,
                            "requestedWorkspace": cwd,
                        },
                    )
                sess = state.new_session()
                return self._json(
                    200,
                    {
                        k: sess[k]
                        for k in (
                            "sessionId",
                            "workspaceCwd",
                            "attached",
                            "clientId",
                            "createdAt",
                        )
                    },
                )
            if self.path.startswith("/session/") and self.path.endswith("/prompt"):
                sid = self.path.split("/")[2]
                sess = state.sessions.get(sid)
                if not sess:
                    return self._json(404, {"error": "no session"})
                body = self._read_body()
                prompt = body.get("prompt")
                if not isinstance(prompt, list) or not prompt:
                    return self._json(
                        400,
                        {
                            "error": "`prompt` is required and must be a "
                            "non-empty array of content blocks"
                        },
                    )
                with state.lock:
                    state.last_prompt = prompt
                text = " ".join(
                    b.get("text", "") for b in prompt if isinstance(b, dict)
                ).strip()
                state.run_turn(sess, text)  # blocks until turn done, like real
                return self._json(200, {"stopReason": "end_turn"})
            return self._json(404, {"error": "not found"})

        def do_DELETE(self):
            if self.path.startswith("/session/"):
                sid = self.path.split("/")[2]
                existed = state.sessions.pop(sid, None) is not None
                if not existed:
                    return self._json(404, {"error": "no session", "sessionId": sid})
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self._json(404, {"error": "not found"})

        def _stream_events(self, sess: dict):
            last_event_id = self.headers.get("Last-Event-ID")
            q: queue.Queue = queue.Queue()
            with state.lock:
                replay = list(sess["ring"])
                sess["subscribers"].append(q)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                self.wfile.write(b"retry: 3000\n\n")
                self.wfile.flush()
                # Replay from ring (honor Last-Event-ID)
                start_after = int(last_event_id) if last_event_id else 0
                for eid, name, env in replay:
                    if eid > start_after:
                        self._send_sse(eid, name, env)
                # Live tail with idle heartbeats; close after idle window.
                idle = 0.0
                while idle < 4.0:
                    try:
                        eid, name, env = q.get(timeout=0.5)
                        self._send_sse(eid, name, env)
                        idle = 0.0
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                        idle += 0.5
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with state.lock:
                    if q in sess["subscribers"]:
                        sess["subscribers"].remove(q)

        def _send_sse(self, eid, name, env):
            payload = (
                f"id: {eid}\n"
                f"event: {name}\n"
                f"data: {json.dumps(env)}\n\n"
            ).encode()
            self.wfile.write(payload)
            self.wfile.flush()

    return Handler


def serve(port: int, workspace: str) -> ThreadingHTTPServer:
    state = FakeState(workspace)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(state))
    return httpd


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=4191)
    ap.add_argument("--workspace", default="/tmp/qwen-fake-ws")
    args = ap.parse_args()
    httpd = serve(args.port, args.workspace)
    print(f"fake qwen serve on http://127.0.0.1:{args.port} workspace={args.workspace}")
    httpd.serve_forever()
