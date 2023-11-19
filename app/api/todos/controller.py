from typing import Optional

from litestar import Controller, get, post

from app.api.auth.models import AuthUser
from app.api.todos.models import CreateTodoRequest, GetTodosRequest, Todo
from app.api.todos.repo import TodoRepo


class TodoController(Controller):
    path = "/todos"

    @get("/")
    async def get_todos(
        self,
        todo_repo: TodoRepo,
        user: AuthUser,
        complete: Optional[bool] = None,
    ) -> list[Todo]:
        return await todo_repo.get_todos(GetTodosRequest(complete), user)

    @post("/")
    async def create_todo(self, data: CreateTodoRequest, todo_repo: TodoRepo, user: AuthUser) -> Todo:
        return await todo_repo.create_todo(data, user)
