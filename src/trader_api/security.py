from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.responses import JSONResponse


class LocalOnlyMiddleware:
    """Reject non-loopback clients even if the server is accidentally exposed."""

    allowed_hosts = {"127.0.0.1", "::1", "testclient"}

    def __init__(self, app: Callable[..., Awaitable[Response]]) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        client_host = request.client.host if request.client else ""
        if client_host not in self.allowed_hosts:
            response = JSONResponse(
                status_code=403,
                content={"detail": "此服務僅允許本機連線。"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
