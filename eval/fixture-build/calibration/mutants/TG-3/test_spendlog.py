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
BUDGET_ONLY = "Team Travel,2026-09,120000" + NL


@pytest.fixture()
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "spend.db"))
    db.init_schema(connection)
    yield connection
    connection.close()


def test_import_reports_what_it_took_in(conn):
    summary = importer.import_budget_csv(conn, EXPORT)
    assert summary["expense_count"] == 2
    assert isinstance(summary["budget_id"], int)


def test_a_malformed_export_is_refused(conn):
    broken = EXPORT + "Missing Columns,dining" + NL
    with pytest.raises(ValueError):
        importer.import_budget_csv(conn, broken)


def test_the_report_renders_the_month_with_every_category(conn):
    summary = importer.import_budget_csv(conn, BUDGET_ONLY)
    handlers.add_expense(
        conn, summary["budget_id"], "Rail Co", "transport", 8800, "2026-09-04"
    )
    handlers.add_expense(
        conn, summary["budget_id"], "Cafe Rossi", "dining", 1900, "2026-09-06"
    )

    html = report.monthly_report(
        conn, "month=2026-09&budget_id=" + str(summary["budget_id"])
    )

    assert "Team Travel" in html
    assert "2026-09" in html
    assert "88.00" in html
    assert "19.00" in html


def test_the_report_says_so_when_no_budget_matches(conn):
    html = report.monthly_report(conn, "month=2099-01")
    assert "No budget" in html


def test_add_expense_refuses_a_category_nobody_can_report_on(conn):
    summary = importer.import_budget_csv(conn, BUDGET_ONLY)
    with pytest.raises(ValueError):
        handlers.add_expense(
            conn, summary["budget_id"], "Gadget Hut", "gadgets", 500, "2026-09-08"
        )
