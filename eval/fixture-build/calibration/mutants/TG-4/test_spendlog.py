"""spendlog's own tests: the import write path and the monthly report renderer."""

from __future__ import annotations

import pytest

import db
import handlers
import importer
import report

NL = chr(10)
EXPORT = NL.join(
    [
        "Team Travel,2026-09,120000",
        "Rail Co,transport,8800,2026-09-04",
        "Cafe Rossi,dining,1900,2026-09-06",
    ]
) + NL


@pytest.fixture()
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "spend.db"))
    db.init_schema(connection)
    yield connection
    connection.close()


def test_import_puts_the_budget_and_every_expense_on_record(conn):
    summary = importer.import_budget_csv(conn, EXPORT)

    budget = conn.execute(
        "SELECT name, month, limit_cents FROM budgets WHERE id = ?",
        (summary["budget_id"],),
    ).fetchone()
    assert tuple(budget) == ("Team Travel", "2026-09", 120000)

    stored = conn.execute(
        "SELECT merchant, category, amount_cents, spent_on FROM expenses"
        " WHERE budget_id = ? ORDER BY id",
        (summary["budget_id"],),
    ).fetchall()
    assert [tuple(row) for row in stored] == [
        ("Rail Co", "transport", 8800, "2026-09-04"),
        ("Cafe Rossi", "dining", 1900, "2026-09-06"),
    ]
    assert summary["expense_count"] == 2


def test_a_failed_import_leaves_the_store_untouched(conn):
    broken = EXPORT + "Missing Columns,dining" + NL
    with pytest.raises(ValueError):
        importer.import_budget_csv(conn, broken)
    assert conn.execute("SELECT count(*) FROM budgets").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM expenses").fetchone()[0] == 0


def test_the_monthly_report_is_rendered_for_the_month_asked_for(conn, monkeypatch):
    summary = importer.import_budget_csv(conn, EXPORT)
    asked_for = []

    def rendered(connection, query_string):
        asked_for.append(query_string)
        return "<section><h2>Team Travel - 2026-09</h2></section>"

    monkeypatch.setattr(report, "monthly_report", rendered)

    query = "month=2026-09&budget_id=" + str(summary["budget_id"])
    html = report.monthly_report(conn, query)

    assert asked_for == [query]
    assert "section" in html


def test_add_expense_refuses_a_category_nobody_can_report_on(conn):
    summary = importer.import_budget_csv(conn, EXPORT)
    with pytest.raises(ValueError):
        handlers.add_expense(
            conn, summary["budget_id"], "Gadget Hut", "gadgets", 500, "2026-09-08"
        )
