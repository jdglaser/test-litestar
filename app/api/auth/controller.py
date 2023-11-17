from litestar import Controller, Response, post
from litestar.status_codes import HTTP_201_CREATED

from app.api.auth.models import LoginUserRequest, LoginUserResponse, RegisterUserRequest
from app.api.auth.service import AuthService
from app.common import deps


@deps.dep
class AuthController(Controller):
    path = "/auth"

    @post("/register")
    async def register(self, data: RegisterUserRequest, auth_service: AuthService) -> Response:
        await auth_service.register_user(data)
        return Response(None, status_code=HTTP_201_CREATED)

    @post("/login")
    async def login(self, data: LoginUserRequest, auth_service: AuthService) -> LoginUserResponse:
        return await auth_service.login_user(data)
