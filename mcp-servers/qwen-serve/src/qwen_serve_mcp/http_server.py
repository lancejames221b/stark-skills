"""Streamable-HTTP transport for qwen-serve-mcp using uvicorn + Starlette.

Reuses the same ``server`` object from server.py. Tools are NOT redefined here.
"""

from __future__ import annotations

import asyncio
import hmac
import os
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .server import server

# ---------------------------------------------------------------------------
# Session manager, constructed once at import time (no side effects beyond
# that; the actual ASGI lifespan starts/stops it).
# ---------------------------------------------------------------------------

session_manager = StreamableHTTPSessionManager(
    app=server,
    event_store=None,
    json_response=False,
    stateless=False,
)

# ---------------------------------------------------------------------------
# Bearer-token ASGI middleware (timing-safe via hmac.compare_digest).
# If QWEN_SERVE_MCP_TOKEN is unset or empty, all requests are allowed.
# ---------------------------------------------------------------------------

_EXPECTED_TOKEN: str | None = os.environ.get("QWEN_SERVE_MCP_TOKEN", "").strip() or None


class _BearerAuthMiddleware:
    """ASGI middleware that enforces Bearer-token on /mcp requests."""

    def __init__(self, app, expected_token: str | None):
        self.app = app
        self.expected_token = expected_token

    async def __call__(self, scope, receive, send):
        if self.expected_token is None:
            # No token configured: allow everything (loopback dev mode).
            await self.app(scope, receive, send)
            return

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path != "/mcp":
            # Non-MCP paths (e.g. /health) bypass auth.
            await self.app(scope, receive, send)
            return

        # Extract Bearer token from Authorization header.
        auth_header = ""
        for name, value in scope.get("headers", []):
            if isinstance(name, bytes):
                name = name.decode()
            if name.lower() == "authorization":
                auth_header = value if isinstance(value, str) else value.decode()
                break

        token_match = False
        if auth_header.startswith("Bearer "):
            provided_token = auth_header[7:]
            token_match = hmac.compare_digest(provided_token, self.expected_token)

        if not token_match:
            await JSONResponse(
                {"error": "unauthorized"}, status_code=401
            )(scope, receive, send)
            return

        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Health check (no auth required).
# ---------------------------------------------------------------------------

async def health_check(request: Request) -> JSONResponse:  # noqa: ARG001
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Starlette app with lifespan (only /health here; /mcp is raw ASGI).
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: Starlette):  # noqa: ARG001
    async with session_manager.run():
        yield


_health_app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/health", endpoint=health_check),
    ],
)


async def _mcp_asgi(scope, receive, send):  # type: ignore[arg-type]
    """Route all /mcp requests to the session manager."""
    await session_manager.handle_request(scope, receive, send)


# Composite ASGI app: /health -> Starlette, everything else -> MCP handler.
async def _inner_app(scope, receive, send):  # type: ignore[arg-type]
    if scope["type"] != "http":
        await _health_app(scope, receive, send)
        return

    path = scope.get("path", "")
    if path == "/health":
        await _health_app(scope, receive, send)
    elif path == "/mcp":
        await _mcp_asgi(scope, receive, send)
    else:
        # 404 for unknown paths.
        from starlette.responses import PlainTextResponse

        resp = PlainTextResponse("not found", status_code=404)
        await resp(scope, receive, send)


# Wrap with auth middleware (outermost layer).
app = _BearerAuthMiddleware(_inner_app, _EXPECTED_TOKEN)

# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------


def main_http() -> None:
    host = os.environ.get("QWEN_SERVE_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("QWEN_SERVE_MCP_PORT", "8779"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main_http()
