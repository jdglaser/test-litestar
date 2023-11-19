import os
from datetime import UTC, datetime

import msgspec
from sqlalchemy import RowMapping, create_engine, event, text
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import ConnectionPoolEntry

from app.common.utils import from_mapping

os.remove("data.db")
engine = create_engine("sqlite+pysqlite:///data.db")


@event.listens_for(engine, "connect")
def on_connect(dbapi_connection: DBAPIConnection, connection_record: ConnectionPoolEntry) -> None:
    print("Connected event!")
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()
    dbapi_connection.commit()


with engine.connect() as conn:
    # conn.execute(text("CREATE SCHEMA 'operational'"))
    print(conn.execute(text("PRAGMA foreign_keys;")).fetchall())
    conn.execute(
        text(
            """
            CREATE TABLE users (
                user_id integer primary key,
                name text UNIQUE,
                age integer,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                active INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES USERS (user_id)
            )
            """
        )
    )
    conn.commit()


class User(msgspec.Struct):
    user_id: int
    name: str
    age: int
    created_at: datetime


class Order(msgspec.Struct):
    order_id: int
    user_id: int
    amount: float
    created_at: datetime
    active: bool


ISO_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def to_iso_str(dt: datetime) -> str:
    return dt.strftime(ISO_FORMAT)[:-3]


with engine.connect() as conn:
    insert_rows = (
        conn.execute(
            text("INSERT INTO users (name, age) VALUES (:name, :age) RETURNING *"),
            {"name": "bob", "age": 23},
        )
        .mappings()
        .one()
    )
    inserted_user = from_mapping(insert_rows, User)
    print("INSERTED USER:", inserted_user)

    rows = conn.execute(text("SELECT * FROM users")).fetchall()
    print("ALL USERS:", rows)

    update_rows = (
        conn.execute(
            text("UPDATE users SET age = :age WHERE user_id = :user_id RETURNING *"), {"age": 30, "user_id": 1}
        )
        .mappings()
        .one()
    )
    updated_user = from_mapping(update_rows, User)
    print("UPDATED USER:", updated_user)

    rows = conn.execute(text("SELECT * FROM users")).fetchall()
    print("ALL USERS:", rows)

    rows = conn.execute(text("SELECT DATETIME(created_at, '+1 day') FROM users")).fetchall()
    print("DATETIME:", datetime.fromisoformat(rows[0][0]))

    row = (
        conn.execute(
            text(
                """
                INSERT INTO orders (user_id, amount, active)
                VALUES (:user_id, :amount, :active)
                RETURNING *
                """
            ),
            {"user_id": inserted_user.user_id, "amount": 100, "active": False},
        )
        .mappings()
        .one()
    )
    created_order = msgspec.convert(row, Order, strict=False)
    print(created_order)
    conn.commit()

    # Integrity error - foreign key constraint failed
    # row = (
    #     conn.execute(
    #         text(
    #             """
    #             INSERT INTO orders (user_id, amount)
    #             VALUES (:user_id, :amount)
    #             RETURNING *
    #             """
    #         ),
    #         {"user_id": 2, "amount": 100},
    #     )
    #     .mappings()
    #     .one()
    # )
    # Integrity error - unique contraint failed
    # try:
    #     insert_rows = (
    #         conn.execute(
    #             text("INSERT INTO users (name, age) VALUES (:name, :age) RETURNING *"),
    #             {"name": "bob", "age": 27},
    #         )
    #         .mappings()
    #         .one()
    #     )
    # except IntegrityError as ex:
    #     raise Exception("Uh Oh!")
    # print("INSERTED USER:", msgspec.convert(insert_rows, User))
