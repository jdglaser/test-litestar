from typing import Optional

from litestar import Controller, delete, get, post, put

from app.api.auth.models import AuthUser
from app.api.todos.models import CreateTodoRequest, GetTodosRequest, Todo, UpdateTodoRequest
from app.api.todos.repo import TodoRepo


class TodoController(Controller):
    path = "/todos"

    @get("/")
    async def get_todos(
        self,
        todo_repo: TodoRepo,
        complete: Optional[bool] = None,
    ) -> list[Todo]:
        return await todo_repo.get_todos(GetTodosRequest(complete))

    @post("/")
    async def create_todo(self, data: CreateTodoRequest, todo_repo: TodoRepo, auth_user: AuthUser) -> Todo:
        return await todo_repo.create_todo(data)

    @put("/{todo_id:int}")
    async def update_todo(
        self, todo_id: int, data: UpdateTodoRequest, todo_repo: TodoRepo, auth_user: AuthUser
    ) -> Todo:
        return await todo_repo.update_todo(todo_id, data)

    @delete("/{todo_id:int}")
    async def delete_todo(self, todo_id: int, todo_repo: TodoRepo) -> None:
        await todo_repo.delete_todo(todo_id)
