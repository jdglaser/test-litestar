import logging

from argon2 import PasswordHasher
from litestar import Litestar, Request, Router
from litestar.datastructures import ImmutableState
from litestar.logging import LoggingConfig
from litestar.static_files import StaticFilesConfig
from litestar.types import Scope
from sqlalchemy import event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import ConnectionPoolEntry

from app.api.auth.controller import AuthController
from app.common import deps
from app.common.models import AppState
from app.setup_db import setup_db


@deps.dep(rename="db")
async def provide_db(state: ImmutableState) -> AsyncEngine:
    return state["app_state"].db


@deps.dep
async def password_hasher(state: ImmutableState) -> AsyncEngine:
    return state["app_state"].password_hasher


log_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.DEBUG), "handlers": ["console"]},
)


async def log_exception(exception: Exception, scope: Scope) -> None:
    request: Request = Request(scope)
    request.logger.exception(str(exception))


async def startup(app: Litestar) -> None:
    db_engine = create_async_engine("sqlite+pysqlite:///:memory:", echo=True)

    @event.listens_for(db_engine, "connect")
    def _on_connect(dbapi_connection: DBAPIConnection, connection_record: ConnectionPoolEntry) -> None:
        print("Connected event!")
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
        dbapi_connection.commit()

    await setup_db(db_engine)

    app_state = AppState(db=db_engine, password_hasher=PasswordHasher())
    app.state.app_state = app_state


async def shutdown(app: Litestar) -> None:
    app_state: AppState = app.state.app_state
    await app_state.db.dispose()


api_router = Router("/api", route_handlers=[AuthController])

app = Litestar(
    route_handlers=[api_router],
    static_files_config=[StaticFilesConfig(path="/", directories=["app/static"], html_mode=True)],
    on_startup=[startup],
    on_shutdown=[shutdown],
    plugins=[deps.dep],
    logging_config=log_config,
    after_exception=[log_exception],
)
