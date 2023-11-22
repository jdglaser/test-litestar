import msgspec
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.auth.models import AuthUser
from app.api.todos.models import CreateTodoRequest, GetTodosRequest, Todo, UpdateTodoRequest
from app.common import deps
from app.common.utils import camelize_row_mapping


@deps.dep
class TodoRepo:
    def __init__(self, db: AsyncEngine, auth_user: AuthUser) -> None:
        self.db = db
        self.auth_user = auth_user

    async def get_todos(self, get_todos_request: GetTodosRequest) -> list[Todo]:
        sql = """
        SELECT * FROM todos
        WHERE user_id = :user_id
        """

        params = {"user_id": self.auth_user.user_id}
        if get_todos_request.complete is not None:
            sql += " AND complete = :complete"
            params["complete"] = get_todos_request.complete

        async with self.db.connect() as conn:
            rows = await conn.execute(text(sql), params)
            return [msgspec.convert(camelize_row_mapping(r), Todo, strict=False) for r in rows.mappings().fetchall()]

    async def create_todo(self, create_todo_request: CreateTodoRequest) -> Todo:
        sql = """
        INSERT INTO todos (user_id, title, description, due_date)
        VALUES (:user_id, :title, :description, :due_date)
        RETURNING *
        """
        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(
                    text(sql), msgspec.structs.asdict(create_todo_request) | {"user_id": self.auth_user.user_id}
                )
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), Todo, strict=False)

    async def update_todo(self, todo_id: int, update_todo_request: UpdateTodoRequest) -> Todo:
        sql = """
        UPDATE todos
        SET complete = :complete
        WHERE todo_id = :todo_id
        AND user_id = :user_id
        RETURNING *
        """

        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(
                    text(sql),
                    msgspec.structs.asdict(update_todo_request)
                    | {"todo_id": todo_id, "user_id": self.auth_user.user_id},
                )
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), Todo, strict=False)

    async def delete_todo(self, todo_id: int) -> Todo:
        sql = """
        DELETE FROM todos
        WHERE todo_id = :todo_id
        AND user_id = :user_id
        RETURNING *
        """

        async with self.db.connect() as conn:
            async with conn.begin():
                rows = await conn.execute(text(sql), {"todo_id": todo_id, "user_id": self.auth_user.user_id})
                return msgspec.convert(camelize_row_mapping(rows.mappings().one()), Todo, strict=False)
