"""The monthly report: read the request, fetch the month, render the fragment.

Three steps, three functions. The request-reading knows nothing about SQL, the fetch knows
nothing about HTML, and the renderer takes plain values -- so the report can be re-fetched
without re-parsing and re-skinned without touching a query.
"""

from __future__ import annotations

import html
import urllib.parse
from typing import Any

from db import rows_as_dicts

# The categories the monthly report breaks spending down by.
CATEGORIES = ("groceries", "transport", "dining", "other")


def parse_report_request(query_string: str) -> tuple[str, int | None]:
    """The month and (optional) budget id a raw query string asks for."""
    values = urllib.parse.parse_qs(query_string or "")
    month = (values.get("month") or [""])[0]
    raw_budget = (values.get("budget_id") or [""])[0]
    budget_id: int | None
    try:
        budget_id = int(raw_budget) if raw_budget else None
    except ValueError:
        budget_id = None
    return month, budget_id


def fetch_month(
    conn: Any, month: str, budget_id: int | None
) -> tuple[dict[str, Any] | None, dict[str, int]]:
    """The budget being reported on, and its spend per category for that month."""
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
        return None, {}
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
    return budget, totals


def render_report(budget: dict[str, Any] | None, month: str, totals: dict[str, int]) -> str:
    """The HTML fragment for one month, every category on it -- zero rows included."""
    if budget is None:
        return (
            "<section><h2>No budget on record for "
            + html.escape(month or "that month")
            + "</h2></section>"
        )
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


def monthly_report(conn: Any, query_string: str) -> str:
    """The report for whichever month and budget the query string names."""
    month, budget_id = parse_report_request(query_string)
    budget, totals = fetch_month(conn, month, budget_id)
    return render_report(budget, month, totals)
