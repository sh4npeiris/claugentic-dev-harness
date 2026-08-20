"""Store access for spendlog: the connection, the schema, and the category set."""

from __future__ import annotations

import sqlite3
from typing import Any

# The one place the valid categories are written down. handlers.py validates against this
# set and report.py groups by it, so a category that can be added can always be reported.
CATEGORIES: tuple[str, ...] = ("groceries", "transport", "utilities", "dining", "other")

SCHEMA = """
CREATE TABLE IF NOT EXISTS budgets (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    month       TEXT    NOT NULL,
    limit_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY,
    budget_id    INTEGER NOT NULL,
    merchant     TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    spent_on     TEXT    NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    """Open (creating if absent) the spendlog database at `path`."""
    return sqlite3.connect(path)


def init_schema(conn: sqlite3.Connection) -> None:
    """Create the two tables if they are not there yet."""
    conn.executescript(SCHEMA)
    conn.commit()


def rows_as_dicts(cursor: Any) -> list[dict[str, Any]]:
    """Read a cursor out as dicts using its own column names.

    Deliberately independent of `row_factory`: a caller may hand us any connection.
    """
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
