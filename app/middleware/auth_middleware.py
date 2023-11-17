from datetime import datetime

from litestar import Litestar, Request
from litestar.datastructures import State
from litestar.exceptions import NotAuthorizedException
from litestar.types import ASGIApp, Receive, Scope, Send

from app.api.auth.models import AuthUser, Token
from app.api.auth.repo import AuthRepo
from app.common import deps


@deps.dep
async def auth_user(state: State) -> AuthUser:
    auth_user = getattr(state, "auth_user", None)
    if not auth_user:
        raise NotAuthorizedException("No auth_user in State")
    return auth_user


def auth_middleware_factory(app: ASGIApp) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        # Initialize auth flow - in a real app we would want to use less detailed error messages
        # for security, but I'm being overly verbose here for testing
        litestar_app = scope["app"]
        auth_service = litestar_app.dependencies.get("auth_service")
        if scope["type"] == "http":
            request = Request(scope)
            auth_header = request.headers.get("Authorization", None)
            if not auth_header:
                raise NotAuthorizedException("Missing authorization header")
            auth_repo: AuthRepo = scope["app"].dependencies.get("auth_repo")
            if not auth_repo:
                raise Exception("Can't find auth_repo in Middleware")
            found_token = find_first(data_store.tokens, lambda t: t.value == auth_header)
            if not found_token:
                raise NotAuthorizedException("Invalid token")
            if datetime.now() > found_token.expires_at:
                data_store.tokens[data_store.tokens.index(found_token)] = Token(
                    token_id=found_token.token_id,
                    type=found_token.type,
                    value=found_token.value,
                    user_id=found_token.user_id,
                    active=False,
                    expires_at=found_token.expires_at,
                    created_at=found_token.created_at,
                    deactivated_at=datetime.now(),
                )
                raise NotAuthorizedException("Token expired")
            user = find_first(data_store.users, lambda u: u.user_id == found_token.user_id)
            if not user:
                raise NotAuthorizedException("Not a valid user")
            scope["app"].state.auth_user = AuthUser(user.email, user.created_at)
        await app(scope, receive, send)

    return my_middleware
