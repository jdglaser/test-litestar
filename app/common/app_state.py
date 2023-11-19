from typing import Optional

import msgspec
from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.auth.models import AuthUser
from app.api.auth.repo import AuthRepo


class AppState(msgspec.Struct):
    db: AsyncEngine
    password_hasher: PasswordHasher
    # We need a version of the auth service in state to access it from auth middleware
    auth_repo: AuthRepo
    auth_user: Optional[AuthUser]
