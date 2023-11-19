# Normally we'd use a database migration tool for this, but I'm skipping that for now

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

SQL = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tokens (
    token_id INTEGER PRIMARY KEY,
    value TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE todos (
    todo_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    due_date TEXT,
    complete INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
"""


async def setup_db(engine: AsyncEngine) -> None:
    statements = SQL.split(";")
    async with engine.connect() as conn:
        for statement in statements:
            await conn.execute(text(statement))
        await conn.commit()
