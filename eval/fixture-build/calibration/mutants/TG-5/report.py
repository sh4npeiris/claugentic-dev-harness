"""The monthly report."""

from __future__ import annotations

import html
import urllib.parse
from typing import Any

from db import CATEGORIES, rows_as_dicts


def monthly_report(conn: Any, query_string: str) -> str:
    """The report for whichever month and budget the query string names."""
    values = urllib.parse.parse_qs(query_string or "")
    month = (values.get("month") or [""])[0]
    raw_budget = (values.get("budget_id") or [""])[0]
    try:
        budget_id = int(raw_budget) if raw_budget else None
    except ValueError:
        budget_id = None

    if budget_id is None:
        cursor = conn.execute(
            "SELECT id, name, month, limit_cents FROM budgets WHERE month = ?"
            " ORDER BY id LIMIT 1",
            (month,),
        )
    else:
        cursor = conn.execute(
            "SELECT id, name, month, limit_cents FROM budgets WHERE id = ?", (budget_id,)
        )
    budgets = rows_as_dicts(cursor)
    if not budgets:
        return (
            "<section><h2>No budget on record for "
            + html.escape(month or "that month")
            + "</h2></section>"
        )
    budget = budgets[0]

    totals = {category: 0 for category in CATEGORIES}
    rows = conn.execute(
        "SELECT category, sum(amount_cents) FROM expenses"
        " WHERE budget_id = ? AND substr(spent_on, 1, 7) = ?"
        " GROUP BY category",
        (budget["id"], month),
    ).fetchall()
    for category, total in rows:
        totals[category] = int(total or 0)

    lines = [
        "<section>",
        "<h2>" + html.escape(str(budget["name"])) + " - " + html.escape(month) + "</h2>",
        "<table><thead><tr><th>Category</th><th>Spent</th></tr></thead><tbody>",
    ]
    for category in CATEGORIES:
        cents = totals.get(category, 0)
        lines.append(
            "<tr><td>"
            + html.escape(category)
            + "</td><td>"
            + "{:.2f}".format(cents / 100)
            + "</td></tr>"
        )
    lines.append("</tbody></table></section>")
    return "".join(lines)
