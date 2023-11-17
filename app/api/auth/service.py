import random
import string
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from litestar.exceptions import NotAuthorizedException

from app.api.auth.exceptions import UserAlreadyExistsException
from app.api.auth.models import (
    InsertToken,
    InsertUser,
    LoginUserRequest,
    LoginUserResponse,
    RegisterUserRequest,
    UpdateUser,
    User,
)
from app.api.auth.repo import AuthRepo
from app.common import deps


@deps.dep
class AuthService:
    def __init__(self, auth_repo: AuthRepo, password_hasher: PasswordHasher) -> None:
        self.auth_repo = auth_repo
        self.password_hasher = password_hasher

    async def register_user(self, register_user_request: RegisterUserRequest) -> User:
        if await self.auth_repo.find_user_by_email(register_user_request.email):
            raise UserAlreadyExistsException("User with specified email already exists")

        hashed_password = self.password_hasher.hash(register_user_request.password)
        return await self.auth_repo.insert_user(InsertUser(register_user_request.email, hashed_password))

    async def login_user(self, login_user_request: LoginUserRequest) -> LoginUserResponse:
        stored_user = await self.auth_repo.find_user_by_email(login_user_request.email)
        if not stored_user:
            raise NotAuthorizedException("Incorrect email or password")
        try:
            self.password_hasher.verify(stored_user.hashed_password, login_user_request.password)
        except Exception:
            raise NotAuthorizedException("Incorrect email or password")
        if self.password_hasher.check_needs_rehash(stored_user.hashed_password):
            # TODO: Configure logging
            print("User password needs rehashing")
            new_hashed_password = self.password_hasher.hash(login_user_request.password)
            await self.auth_repo.update_user(stored_user.user_id, UpdateUser(stored_user.email, new_hashed_password))

        access_token = InsertToken(
            value="".join(random.choices(string.ascii_letters + string.digits, k=32)),
            user_id=stored_user.user_id,
            expires_at=datetime.now() + timedelta(minutes=5),
        )

        await self.auth_repo.insert_token(access_token)

        return LoginUserResponse(access_token=access_token.value)
