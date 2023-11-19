from datetime import datetime
from typing import Optional

from app.common.base_model import Base


class User(Base):
    user_id: int
    email: str
    hashed_password: str
    created_at: datetime


class AuthUser(Base):
    user_id: int
    email: str
    created_at: datetime


class RegisterUserRequest(Base):
    email: str
    password: str


class LoginUserRequest(Base):
    email: str
    password: str


class LoginUserResponse(Base):
    access_token: str


class InsertUser(Base):
    email: str
    hashed_password: str


class UpdateUser(Base):
    email: str
    hashed_password: str


class Token(Base):
    token_id: int
    value: str
    user_id: int
    active: bool
    expires_at: datetime
    created_at: datetime
    deactivated_at: Optional[datetime]


class InsertToken(Base):
    value: str
    user_id: int
    expires_at: datetime
