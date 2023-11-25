from datetime import UTC, datetime
from typing import Optional

import msgspec
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.auth.exceptions import UserAlreadyExistsException
from app.api.auth.models import AuthUser, InsertToken, InsertUser, Token, UpdateUser, User
from app.common import deps
from app.common.get_log import get_logger
from app.common.utils import camelize_row_mapping

_logger = get_logger()


@deps.dep
class AuthRepo:
    def __init__(self, db: AsyncEngine) -> None:
        self.db = db

    async def find_user_by_email(self, email: str) -> Optional[User]:
        sql = """
        SELECT *
        FROM users
        WHERE email = :email
        """
        async with self.db.connect() as conn:
            row = (await conn.execute(text(sql), {"email": email})).mappings().fetchone()
            return msgspec.convert(camelize_row_mapping(row), User) if row else None

    async def insert_user(self, insert_user: InsertUser) -> User:
        sql = """
        INSERT INTO users (email, hashed_password, created_at)
        VALUES (:email, :hashed_password, :created_at)
        RETURNING *
        """
        async with self.db.connect() as conn:
            async with conn.begin():
                try:
                    rows = await conn.execute(
                        text(sql), msgspec.structs.asdict(insert_user) | {"created_at": datetime.now(tz=UTC)}
                    )
                    created_user = rows.mappings().one()
                    return msgspec.convert(camelize_row_mapping(created_user), User)
                except IntegrityError as ex:
                    _logger.exception(str(ex))
                    raise UserAlreadyExistsException("User with the provided email already exists")

    async def update_user(self, user_id: int, update_user: UpdateUser) -> User:
        sql = """
        UPDATE users
        SET email = :email,
        hashed_password = :hashed_password
        WHERE user_id = :user_id
        RETURNING *
        """
        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(
                    text(sql),
                    {"email": update_user.email, "hashed_password": update_user.hashed_password, "user_id": user_id},
                )
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), User)

    async def insert_token(self, insert_token: InsertToken) -> Token:
        sql = """
        INSERT INTO tokens (value, user_id, expires_at, created_at)
        VALUES (:value, :user_id, :expires_at, :created_at)
        RETURNING *
        """
        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(
                    text(sql), msgspec.structs.asdict(insert_token) | {"created_at": datetime.now(tz=UTC)}
                )
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), Token, strict=False)

    async def deactivate_token(self, token_id: int) -> Token:
        sql = """
        UPDATE tokens
        SET active = 0,
        deactivated_at = CURRENT_TIMESTAMP
        WHERE token_id = :token_id
        RETURNING *
        """
        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(text(sql), {"token_id": token_id})
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), Token, strict=False)

    async def find_token_by_value(self, value: str) -> Optional[Token]:
        sql = """
        SELECT *,
        FROM tokens
        WHERE active = 1
        AND value = :value
        """
        async with self.db.connect() as conn:
            rows = await conn.execute(text(sql), {"value": value})
            found_token = rows.mappings().first()
            if not found_token:
                return None
            else:
                return msgspec.convert(camelize_row_mapping(found_token), Token, strict=False)

    async def get_auth_user_from_token(self, token: Token) -> AuthUser:
        sql = """
        SELECT user_id, email, created_at
        FROM users
        WHERE user_id = :user_id
        """
        async with self.db.connect() as conn:
            rows = await conn.execute(text(sql), {"user_id": token.user_id})
            return msgspec.convert(camelize_row_mapping(rows.mappings().one()), AuthUser)
