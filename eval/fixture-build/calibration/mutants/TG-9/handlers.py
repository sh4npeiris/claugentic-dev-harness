"""Request-facing operations: the listing, merchant search, the token check, adds, totals."""

from __future__ import annotations

import hmac
import urllib.parse
from typing import Any

from db import CATEGORIES, rows_as_dicts

SERVICE_TOKEN_HEADER = "X-Service-Token"

_EXPENSE_SELECT = (
    "SELECT e.id, e.budget_id, b.name AS budget_name, e.merchant, e.category,"
    " e.amount_cents, e.spent_on"
    " FROM expenses e LEFT JOIN budgets b ON b.id = e.budget_id"
)
_EXPENSE_ORDER = " ORDER BY e.spent_on DESC, e.id DESC"


def list_expenses(conn: Any, budget_id: int | None = None) -> list[dict[str, Any]]:
    """Every expense on record (newest first), or just one budget's, with the budget name.

    One statement whichever way it is called: the budget name comes back with the row
    rather than costing a lookup per row, which is what keeps the busiest screen in the
    product flat as the list grows.
    """
    if budget_id is None:
        cursor = conn.execute(_EXPENSE_SELECT + _EXPENSE_ORDER)
    else:
        cursor = conn.execute(
            _EXPENSE_SELECT + " WHERE e.budget_id = ?" + _EXPENSE_ORDER, (budget_id,)
        )
    return rows_as_dicts(cursor)


def search_term(query_string: str) -> str:
    """The `q` term out of a raw query string, or an empty string when there is none."""
    values = urllib.parse.parse_qs(query_string or "", keep_blank_values=True)
    terms = values.get("q") or [""]
    return terms[0]


def search_expenses(conn: Any, query_string: str) -> list[dict[str, Any]]:
    """Expenses whose merchant carries the visitor's search term.

    The term is data, never SQL: it travels as a placeholder value, so whatever the visitor
    typed can only ever be matched against, not run.
    """
    term = search_term(query_string)
    if not term:
        return []
    pattern = "%" + term + "%"
    cursor = conn.execute(
        _EXPENSE_SELECT + " WHERE e.merchant LIKE ?" + _EXPENSE_ORDER, (pattern,)
    )
    return rows_as_dicts(cursor)


def check_service_token(headers: Any, config: Any) -> bool:
    """True only when the caller presents the operator's token for THIS deployment.

    The expected value is read from the config the caller is given, every call -- an
    operator who rotates the token has rotated it, with nothing else to remember. The
    comparison is length-constant so a caller cannot learn the token a character at a time.
    """
    expected = (config or {}).get("service_token")
    presented = (headers or {}).get(SERVICE_TOKEN_HEADER)
    if not expected or not presented:
        return False
    return hmac.compare_digest(str(presented), str(expected))


def add_expense(
    conn: Any,
    budget_id: int,
    merchant: str,
    category: str,
    amount_cents: int,
    spent_on: str,
) -> int:
    """Record one expense and return its id. Refuses a category outside the known set."""
    if category not in CATEGORIES:
        raise ValueError(
            f"unknown category {category!r}; expected one of {', '.join(CATEGORIES)}"
        )
    cursor = conn.execute(
        "INSERT INTO expenses (budget_id, merchant, category, amount_cents, spent_on)"
        " VALUES (?, ?, ?, ?, ?)",
        (budget_id, merchant, category, amount_cents, spent_on),
    )
    conn.commit()
    return int(cursor.lastrowid)


def dashboard_totals(conn: Any) -> dict[str, int]:
    """The tile the office manager reads first thing: how many, how much."""
    try:
        row = conn.execute(
            "SELECT count(*), coalesce(sum(amount_cents), 0) FROM expenses"
        ).fetchone()
        return {"expense_count": int(row[0]), "total_cents": int(row[1])}
    except Exception:
        return {"expense_count": 0, "total_cents": 0}
