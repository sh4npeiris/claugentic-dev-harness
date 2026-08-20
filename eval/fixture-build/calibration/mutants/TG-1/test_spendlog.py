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


def test_a_failed_import_leaves_the_store_untouched(conn, tmp_path):
    broken = EXPORT + "Missing Columns,dining" + NL
    with pytest.raises(ValueError):
        importer.import_budget_csv(conn, broken)
    assert conn.execute("SELECT count(*) FROM budgets").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM expenses").fetchone()[0] == 0


def test_the_report_renders_the_month_with_every_category(conn):
    summary = importer.import_budget_csv(conn, EXPORT)

    html = report.monthly_report(
        conn, "month=2026-09&budget_id=" + str(summary["budget_id"])
    )

    assert "Team Travel" in html
    assert "2026-09" in html
    for category in db.CATEGORIES:
        assert category in html
    assert "88.00" in html
    assert "19.00" in html


def test_the_report_says_so_when_no_budget_matches(conn):
    html = report.monthly_report(conn, "month=2099-01")
    assert "No budget" in html


def test_add_expense_refuses_a_category_nobody_can_report_on(conn):
    summary = importer.import_budget_csv(conn, EXPORT)
    with pytest.raises(ValueError):
        handlers.add_expense(
            conn, summary["budget_id"], "Gadget Hut", "gadgets", 500, "2026-09-08"
        )
