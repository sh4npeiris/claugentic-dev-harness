"""The CSV import: one budget and its expenses, or nothing at all."""

from __future__ import annotations

import csv
import io
from typing import Any

EXPENSE_COLUMNS = 4


def parse_budget_csv(csv_text: str) -> tuple[tuple[str, str, int], list[tuple[str, str, int, str]]]:
    """Split the export into its budget header and its expense lines.

    Raises `ValueError` on a malformed export rather than importing part of it: the caller
    is told what was wrong with the file it handed over.
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        raise ValueError("the export is empty: no budget line to read")
    header = rows[0]
    if len(header) != 3:
        raise ValueError(f"the budget line needs name,month,limit_cents; got {header!r}")
    name, month, limit_text = (cell.strip() for cell in header)
    try:
        limit_cents = int(limit_text)
    except ValueError as exc:
        raise ValueError(f"the budget limit is not a whole number of cents: {limit_text!r}") from exc

    expenses: list[tuple[str, str, int, str]] = []
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != EXPENSE_COLUMNS:
            raise ValueError(
                f"line {line_number} needs merchant,category,amount_cents,spent_on; got {row!r}"
            )
        merchant, category, amount_text, spent_on = (cell.strip() for cell in row)
        try:
            amount_cents = int(amount_text)
        except ValueError as exc:
            raise ValueError(f"line {line_number} has a non-numeric amount: {amount_text!r}") from exc
        expenses.append((merchant, category, amount_cents, spent_on))
    return (name, month, limit_cents), expenses


def import_budget_csv(conn: Any, csv_text: str) -> dict[str, int]:
    """Put a whole export on record in one call, and report what landed.

    The budget row and every expense row are written inside ONE transaction, so a failure
    part way through leaves the store exactly as it was -- never a budget carrying half its
    spending, which nothing downstream could tell apart from a genuinely quiet month.
    """
    budget, expenses = parse_budget_csv(csv_text)
    with conn:
        cursor = conn.execute(
            "INSERT INTO budgets (name, month, limit_cents) VALUES (?, ?, ?)", budget
        )
        budget_id = cursor.lastrowid
        for merchant, category, amount_cents, spent_on in expenses:
            conn.execute(
                "INSERT INTO expenses (budget_id, merchant, category, amount_cents, spent_on)"
                " VALUES (?, ?, ?, ?, ?)",
                (budget_id, merchant, category, amount_cents, spent_on),
            )
    return {"budget_id": budget_id, "expense_count": len(expenses)}
