import logging

from argon2 import PasswordHasher
from litestar import Litestar, Request, Router
from litestar.datastructures import State
from litestar.exceptions import NotAuthorizedException
from litestar.logging import LoggingConfig
from litestar.static_files import StaticFilesConfig
from litestar.types import Scope
from sqlalchemy import event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import ConnectionPoolEntry

from app.api.auth.controller import AuthController
from app.api.auth.models import AuthUser
from app.api.auth.repo import AuthRepo
from app.api.todos.controller import TodoController
from app.common import deps
from app.common.app_state import AppState
from app.middleware.auth_middleware import auth_middleware_factory
from app.setup_db import setup_db


@deps.dep(rename="db")
async def provide_db(state: State) -> AsyncEngine:
    return state["app_state"].db


@deps.dep(rename="password_hasher")
async def provide_password_hasher(state: State) -> PasswordHasher:
    return state["app_state"].password_hasher


@deps.dep(rename="auth_user")
async def provide_auth_user(state: State) -> AuthUser:
    app_state: AppState = state["app_state"]
    if not app_state.auth_user:
        raise NotAuthorizedException("Invalid token")
    return app_state.auth_user


log_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.DEBUG), "handlers": ["console"]},
)


async def log_exception(exception: Exception, scope: Scope) -> None:
    request: Request = Request(scope)
    request.logger.exception(str(exception))


async def startup(app: Litestar) -> None:
    db_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(db_engine.sync_engine, "connect")
    def _on_connect(dbapi_connection: DBAPIConnection, connection_record: ConnectionPoolEntry) -> None:
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
        dbapi_connection.commit()

    await setup_db(db_engine)

    app_state = AppState(db=db_engine, password_hasher=PasswordHasher(), auth_repo=AuthRepo(db_engine), auth_user=None)
    app.state.app_state = app_state


async def shutdown(app: Litestar) -> None:
    app_state: AppState = app.state.app_state
    await app_state.db.dispose()


protected_routes = Router("/", route_handlers=[TodoController], middleware=[auth_middleware_factory])
api_router = Router("/api", route_handlers=[AuthController, protected_routes])

app = Litestar(
    route_handlers=[api_router],
    static_files_config=[StaticFilesConfig(path="/", directories=["app/static"], html_mode=True)],
    on_startup=[startup],
    on_shutdown=[shutdown],
    plugins=[deps.dep],
    logging_config=log_config,
    after_exception=[log_exception],
)
