from datetime import datetime

from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.types import ASGIApp, Receive, Scope, Send

from app.api.auth.repo import AuthRepo
from app.common.app_state import AppState


def auth_middleware_factory(app: ASGIApp) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        # Initialize auth flow - in a real app we would want to use less detailed error messages
        # for security, but I'm being overly verbose here for testing
        litestar_app = scope["app"]
        app_state: AppState | None = litestar_app.state.get("app_state")
        if not app_state:
            raise Exception("Cannot find app_state in state")
        auth_repo: AuthRepo = app_state.auth_repo
        if scope["type"] == "http":
            request = Request(scope)
            auth_header = request.headers.get("Authorization", None)
            if not auth_header:
                raise NotAuthorizedException("Missing authorization header")
            found_token = await auth_repo.find_token_by_value(auth_header)
            if not found_token:
                raise NotAuthorizedException("Invalid token")
            if datetime.now() > found_token.expires_at:
                await auth_repo.deactivate_token(found_token.token_id)
                raise NotAuthorizedException("Token expired")
            user = await auth_repo.get_auth_user_from_token(found_token)
            litestar_app.state.app_state.auth_user = user
        await app(scope, receive, send)

    return my_middleware
