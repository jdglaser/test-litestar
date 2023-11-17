from datetime import UTC, datetime
from typing import Optional

import msgspec
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.auth.exceptions import UserAlreadyExistsException
from app.api.auth.models import InsertToken, InsertUser, Token, UpdateUser, User
from app.common import deps


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
            row = (await conn.execute(text(sql), {"emai": email})).mappings().fetchone()
            return msgspec.convert(row, User) if row else None

    async def insert_user(self, insert_user: InsertUser) -> User:
        sql = """
        INSERT INTO users (email, hashed_password, created_at)
        VALUES (:email, :hashed_password, :created_at)
        RETURNING *
        """
        async with self.db.connect() as conn:
            try:
                rows = await conn.execute(
                    text(sql), msgspec.structs.asdict(insert_user) | {"created_at": datetime.now(tz=UTC)}
                )
                created_user = rows.mappings().one()
                return msgspec.convert(created_user, User)
            except IntegrityError as ex:
                print(ex)  # TODO: setup logging
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
            rows = await conn.execute(
                text(sql),
                {"email": update_user.email, "hashed_password": update_user.hashed_password, "user_id": user_id},
            )
            return msgspec.convert(rows.mappings().one(), User)

    async def insert_token(self, insert_token: InsertToken) -> Token:
        sql = """
        INSERT INTO tokens (value, user_id, expires_at, created_at)
        VALUES (:value, :user_id, :expires_at, :created_at)
        RETURNING *
        """
        async with self.db.connect() as conn:
            rows = await conn.execute(
                text(sql), msgspec.structs.asdict(insert_token) | {"created_at": datetime.now(tz=UTC)}
            )
            return msgspec.convert(rows.mappings().one(), Token)

    async def deactivate_token(self, token_id: int) -> Token:
        sql = """
        UPDATE tokens
        SET active = FALSE
        deactivated_at = CURRENT_TIMESTAMP
        WHERE token_id = :token_id
        RETURNING *
        """
        async with self.db.connect() as conn:
            rows = await conn.execute(text(sql), {"token_id": token_id})
            return msgspec.convert(rows.mappings().one(), Token)
