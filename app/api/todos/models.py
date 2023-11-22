from datetime import date, datetime
from typing import Optional

from app.common.base_model import Base


class CreateTodoRequest(Base):
    title: str
    description: str
    due_date: Optional[date] = None


class GetTodosRequest(Base):
    complete: Optional[bool]


class UpdateTodoRequest(Base):
    complete: bool


class Todo(Base):
    todo_id: int
    user_id: int
    title: str
    description: str
    due_date: Optional[date]
    complete: bool
    created_at: datetime
