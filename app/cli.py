import asyncio
import os
import subprocess
import sys
from pathlib import Path

import click
from sqlalchemy.ext.asyncio import create_async_engine

from app.common.get_log import get_logger
from app.setup_db import setup_db

_log = get_logger()


@click.group()
def cli() -> None:
    ...


def run_db_setup() -> None:
    _log.info("Setting up db")
    db_engine = create_async_engine("sqlite+aiosqlite:///data.db")
    fut = setup_db(db_engine)
    asyncio.run(fut)
    _log.info("Finished setting up db")


@cli.command(name="init-db", help="Initialize the database if it does not exist")
def init_db() -> None:
    if Path("data.db").exists():
        raise Exception("data.db already exists, try clearing database first with 'clear-db' command")
    run_db_setup()


@cli.command(name="clear-db", help="Clear the database")
def delete_db() -> None:
    os.remove("./data.db")
    run_db_setup()


@cli.command(name="start", help="Start the app")
@click.option("--port", type=int, default=8000)
@click.option("--clear-db", is_flag=True, show_default=True, default=False, help="Clear the database on startup")
def start(port: int, clear_db: bool) -> None:
    if clear_db:
        _log.info("Clearing DB")
        os.remove("./data.db")
        run_db_setup()
    if not Path("./data.db").exists():
        _log.info("DB doesn't exist yet, creating")
        run_db_setup()
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app:app", "--reload", "--port", str(port)],
        check=True,
    )


if __name__ == "__main__":
    cli()
