"""Session authentication middleware for the public API."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class SessionAuthenticationMiddleware:
    """Reject unauthenticated API requests before they reach a route handler.

    Starlette's ``SessionMiddleware`` wraps this middleware, so the decoded and
    signed session is available in ``scope["session"]``. CORS preflight requests
    are allowed through because they do not invoke an application endpoint.
    """

    def __init__(self, app: ASGIApp, login_path: str = "/api/v1/auth/login"):
        self.app = app
        self.login_path = login_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope["method"] == "OPTIONS" or scope["path"] == self.login_path:
            await self.app(scope, receive, send)
            return

        session = scope.get("session", {})
        username = session.get("authenticated_user") if isinstance(session, dict) else None
        if not isinstance(username, str) or not username:
            response = JSONResponse(
                status_code=401,
                content={"code": 401, "detail": "请先登录"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
