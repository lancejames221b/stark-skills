"""Drive start, send, events, end against the fake daemon and assert the
shapes. Runs WITHOUT a real qwen or model.

Run:  python -m pytest tests/test_session_flow.py -v
 or:  python tests/test_session_flow.py   (self-running, no pytest needed)
"""

from __future__ import annotations

import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
sys.path.insert(0, SRC)
sys.path.insert(0, HERE)

import fake_qwen_serve  # noqa: E402
from qwen_serve_mcp import client  # noqa: E402
from qwen_serve_mcp.executor_prompt import EXECUTOR_SYSTEM_PROMPT  # noqa: E402

WORKSPACE = "/tmp/qwen-mcp-fake-ws"


def _start_fake():
    httpd = fake_qwen_serve.serve(0, WORKSPACE)  # port 0 for OS-assigned
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    return httpd, base


def test_full_flow():
    httpd, base = _start_fake()
    try:
        # health
        assert client.health_ok(base), "fake /health should be ok"

        # start (POST /session)
        sr = client.start_session(base, WORKSPACE)
        assert sr.session_id, "session_id present"
        assert sr.raw["workspaceCwd"] == WORKSPACE
        assert "clientId" in sr.raw and "createdAt" in sr.raw
        print(f"[start] session_id={sr.session_id}")

        # workspace mismatch raises RuntimeError mentioning workspace_mismatch
        mismatch = None
        try:
            client.start_session(base, "/tmp/some-other-ws")
        except RuntimeError as e:
            mismatch = str(e)
        assert mismatch and "workspace_mismatch" in mismatch
        print("[mismatch] correctly rejected")

        # send (POST /session/:id/prompt + SSE drain)
        res = client.send_prompt(
            base,
            sr.session_id,
            "do the bounded step",
            system_prompt_append=EXECUTOR_SYSTEM_PROMPT,
            timeout_seconds=15,
        )
        assert res.status == "ok", f"status={res.status} err={res.error}"
        assert res.stop_reason == "end_turn"
        # The bounded-step text and the prepended executor prompt both ride the
        # turn (the http-bridge has no separate system slot), so both appear.
        assert "do the bounded step" in res.output, res.output
        assert "You are the EXECUTOR" in res.output, res.output
        # thought chunks must NOT leak into output
        assert "Thinking about it." not in res.output
        # STEP block parsed out
        assert res.last_step_block is not None
        assert res.last_step_block.startswith("STEP - PASS")
        assert res.elapsed_ms >= 0
        print(f"[send] status={res.status} stop={res.stop_reason} "
              f"elapsed_ms={res.elapsed_ms}")
        print(f"[send] last_step_block:\n{res.last_step_block}")

        # events (GET /session/:id/events), replay the whole ring
        events = client.fetch_events(base, sr.session_id, max_events=500,
                                     idle_timeout=1.5)
        assert len(events) > 0, "should get the replayed turn events"
        kinds = {
            e["data"]["data"]["update"].get("sessionUpdate")
            for e in events
            if isinstance(e.get("data"), dict)
        }
        assert "agent_message_chunk" in kinds
        assert "agent_thought_chunk" in kinds
        print(f"[events] count={len(events)} kinds={sorted(k for k in kinds if k)}")

        # events with since_event_id (Last-Event-ID replay subset)
        subset = client.fetch_events(base, sr.session_id, since_event_id="3",
                                     max_events=500, idle_timeout=1.5)
        ids = [int(e["id"]) for e in subset if e.get("id")]
        assert all(i > 3 for i in ids), f"replay should be > 3, got {ids}"
        print(f"[events:since=3] count={len(subset)} first_id={ids[0] if ids else None}")

        # end (DELETE /session/:id)
        ended = client.end_session(base, sr.session_id)
        assert ended is True
        print("[end] session ended (204)")

        # bare-string prompt is rejected by the daemon contract
        sr2 = client.start_session(base, WORKSPACE)
        import httpx
        bad = httpx.post(
            f"{base}/session/{sr2.session_id}/prompt",
            json={"prompt": "not an array"},
        )
        assert bad.status_code == 400, bad.status_code
        assert "array of content blocks" in bad.text
        print("[contract] bare-string prompt correctly rejected (400)")

        print("\nALL ASSERTIONS PASSED")
    finally:
        httpd.shutdown()


def test_model_selection_derives_distinct_ports():
    """Two different model ids derive two different daemon ports; the SAME
    (workspace, model) is idempotent and reuses one port. model=None keeps the
    base port. This is the daemon-per-(workspace, model) rule (issue #3304:
    model is fixed at daemon boot, no mid-session swap)."""
    base = 4170
    p_a = client.port_for_model(base, "qwen3.6-35b-a3b-mlx")
    p_b = client.port_for_model(base, "qwen3-coder-next")
    p_a_again = client.port_for_model(base, "qwen3.6-35b-a3b-mlx")
    p_default = client.port_for_model(base, None)

    assert p_a != p_b, f"distinct models must derive distinct ports: {p_a}=={p_b}"
    assert p_a == p_a_again, "same (workspace, model) must derive the same port"
    assert p_default == base, "no model keeps the base port"
    assert base < p_a <= base + client.PORT_WINDOW, p_a
    assert base < p_b <= base + client.PORT_WINDOW, p_b
    print(f"[model] default={p_default} A={p_a} B={p_b} (A reused={p_a_again})")
    print("[model] distinct models give distinct ports, same model reused")


def test_multimodal_files_reach_prompt():
    """Passing files=[<existing abs path>] puts an @<abspath> ref into the
    prompt the fake received; a missing path raises rather than silently
    dropping."""
    import tempfile

    httpd, base = _start_fake()
    try:
        sr = client.start_session(base, WORKSPACE)

        # An existing absolute file should ride into the prompt as @<abspath>.
        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as tf:
            tf.write(b"\x89PNG fake bytes")
            img_path = tf.name
        try:
            res = client.send_prompt(
                base,
                sr.session_id,
                "describe this image",
                files=[img_path],
                timeout_seconds=15,
            )
            assert res.status == "ok", f"status={res.status} err={res.error}"

            # Inspect what the fake actually received via the debug route.
            import httpx

            last = httpx.get(f"{base}/last-prompt").json()["prompt"]
            joined = " ".join(
                b.get("text", "") for b in last if isinstance(b, dict)
            )
            assert f"@{img_path}" in joined, (
                f"@path ref must reach the prompt; got: {joined!r}"
            )
            assert "describe this image" in joined
            print(f"[multimodal] @path reached prompt: @{img_path}")
        finally:
            os.unlink(img_path)

        # A missing path must error, not silently drop.
        missing = os.path.join(WORKSPACE, "definitely-not-here-12345.png")
        err = None
        try:
            client.send_prompt(
                base,
                sr.session_id,
                "describe this",
                files=[missing],
                timeout_seconds=15,
            )
        except client.MissingFilesError as e:
            err = e
        assert err is not None, "missing file must raise MissingFilesError"
        assert missing in err.missing, err.missing
        print(f"[multimodal] missing file correctly rejected: {missing}")

        # A relative path must error as not-absolute.
        rel_err = None
        try:
            client.send_prompt(
                base,
                sr.session_id,
                "describe this",
                files=["relative/path.png"],
                timeout_seconds=15,
            )
        except client.MissingFilesError as e:
            rel_err = e
        assert rel_err is not None and rel_err.not_absolute, "relative path must raise"
        print("[multimodal] relative path correctly rejected")

        print("\nMULTIMODAL ASSERTIONS PASSED")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    test_full_flow()
    test_model_selection_derives_distinct_ports()
    test_multimodal_files_reach_prompt()
    print("\n=== ALL TEST FUNCTIONS PASSED ===")
