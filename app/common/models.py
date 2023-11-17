import msgspec
from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncEngine


class Base(msgspec.Struct, rename="camel", frozen=True):
    ...


class AppState(msgspec.Struct):
    db: AsyncEngine
    password_hasher: PasswordHasher
