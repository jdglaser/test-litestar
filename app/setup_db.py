# Normally we'd use a database migration tool for this, but I'm skipping that for now

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

SQL = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    hashed_password: TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tokens (
    token_id INTEGER PRIMARY KEY,
    value TEXT UNIQUE,
    user_id INTEGER,
    active INTEGER DEFAULT 1,
    expires_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


async def setup_db(engine: AsyncEngine) -> None:
    statements = SQL.split(";")
    async with engine.connect() as conn:
        for statement in statements:
            await conn.execute(text(statement))
        await conn.commit()
