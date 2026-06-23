"""Characterization + fail-loud tests for the ledger byte-budget gate.

The gate (`scripts/check_doc_budgets.py`) flags (never edits) when a managed
ledger outgrows its TOTAL byte budget, names the compaction remediation, and
fails loud on a missing/unreadable budgeted file. These tests lock that
behaviour — especially the fail-LOUD set and the independent-read property — so
a future edit can't regress it into a silent fail-open (a missing ledger must
never be a free pass).

Hermetic by construction:
  * `tmp_path` materialises real ledger files on disk.
  * `DOC_BUDGETS` is monkeypatched to point at those tmp files (with explicit
    byte budgets), so no real repo ledger leaks in.
  * Each file is written independently per-case, so the independence-of-read
    property can be exercised directly (one breach/broken, another fine).
"""

from __future__ import annotations

import pytest

import check_doc_budgets as cdb


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def ledgers(tmp_path, monkeypatch):
    """Point the gate's DOC_BUDGETS at three tmp_path ledgers with set budgets.

    Returns a `write(name, n_bytes_or_None)` helper: pass an int to materialise a
    file of exactly that many bytes, or `None` to leave it absent (missing-file
    cases). Budgets are A=100, B=200, C=300 — small + distinct so over/at/under
    and per-file independence are easy to drive.
    """
    paths = {"A": tmp_path / "A.md", "B": tmp_path / "B.md", "C": tmp_path / "C.md"}
    monkeypatch.setattr(
        cdb,
        "DOC_BUDGETS",
        {
            str(paths["A"]): {"max_bytes": 100},
            str(paths["B"]): {"max_bytes": 200},
            str(paths["C"]): {"max_bytes": 300},
        },
    )

    def write(key: str, n_bytes: int | None) -> None:
        if n_bytes is not None:
            paths[key].write_bytes(b"x" * n_bytes)

    return write


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — the within-budget + breach paths
# ─────────────────────────────────────────────────────────────────────────────
class TestWithinAndOverBudget:
    def test_all_under_budget_ok(self, ledgers):
        ledgers("A", 50)
        ledgers("B", 100)
        ledgers("C", 150)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert "OK:" in summary

    def test_at_budget_is_ok_not_a_breach(self, ledgers):
        # Exactly-at-budget is within budget — only a STRICT excess breaches.
        ledgers("A", 100)
        ledgers("B", 200)
        ledgers("C", 300)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert "OK:" in summary

    def test_over_budget_flags_with_measured_and_budget_and_remediation(self, ledgers):
        ledgers("A", 101)  # one byte over its 100 budget
        ledgers("B", 100)
        ledgers("C", 150)
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "101" in blob  # measured
        assert "100" in blob  # budget
        assert "compaction pass" in blob  # the named remediation
        assert "A.md" in blob


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — FAIL LOUD: a missing budgeted file (each independently)
# ─────────────────────────────────────────────────────────────────────────────
class TestMissingFile:
    def test_missing_budgeted_file_fails_loud(self, ledgers):
        ledgers("A", None)  # A.md absent — must not be a silent skip
        ledgers("B", 100)
        ledgers("C", 150)
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("is missing" in p and "A.md" in p for p in problems)


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — FAIL LOUD: an unreadable file, no traceback crash
# ─────────────────────────────────────────────────────────────────────────────
class TestUnreadableFile:
    def test_unreadable_file_fails_loud_no_crash(self, ledgers, monkeypatch):
        from pathlib import Path

        ledgers("A", 50)
        ledgers("B", 100)
        ledgers("C", 150)
        real_read = Path.read_bytes

        def boom(self, *a, **k):
            if self.name == "A.md":
                raise PermissionError("denied")
            return real_read(self, *a, **k)

        monkeypatch.setattr(Path, "read_bytes", boom)
        problems, warnings, summary = cdb.evaluate()  # must NOT raise
        assert summary == ""
        blob = "\n".join(problems)
        assert "could not be read" in blob
        assert "A.md" in blob
        assert "compaction pass" not in blob.split("A.md", 1)[1].split("\n")[0]


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — INDEPENDENCE: one breach/broken file must not mask another
# ─────────────────────────────────────────────────────────────────────────────
class TestIndependentReads:
    def test_two_breaches_both_reported(self, ledgers):
        ledgers("A", 150)  # over its 100 budget
        ledgers("B", 100)  # fine
        ledgers("C", 400)  # over its 300 budget
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "A.md" in blob
        assert "C.md" in blob

    def test_missing_one_does_not_mask_a_breach_in_another(self, ledgers):
        ledgers("A", None)  # missing
        ledgers("B", 100)  # fine
        ledgers("C", 400)  # over budget — must still surface despite A missing
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "is missing" in blob and "A.md" in blob
        assert "C.md" in blob and "400" in blob


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — the WARN band (>= WARN_RATIO of budget, but not over): heads-up, not a breach
# ─────────────────────────────────────────────────────────────────────────────
class TestWarnBand:
    def test_in_warn_band_warns_not_breaches(self, ledgers):
        # A=95 is in [90, 100]: past the 90% warn threshold but within the 100 budget.
        ledgers("A", 95)
        ledgers("B", 100)
        ledgers("C", 150)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []  # not a breach
        assert "OK:" in summary  # run still passes
        blob = "\n".join(warnings)
        assert "A.md" in blob
        assert "approaching budget" in blob

    def test_warn_does_not_mask_a_real_breach(self, ledgers):
        ledgers("A", 95)  # warn band
        ledgers("B", 100)  # fine
        ledgers("C", 400)  # breach
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("C.md" in p for p in problems)  # the breach still surfaces (exit 1)
        assert any("A.md" in w for w in warnings)  # the warn still surfaces

    def test_main_prints_warn_and_exits_0(self, ledgers, capsys):
        ledgers("A", 95)  # warn band only — no breach
        ledgers("B", 100)
        ledgers("C", 150)
        rc = cdb.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "WARN:" in out
        assert "A.md" in out


# ─────────────────────────────────────────────────────────────────────────────
# main() — exit codes + stdout
# ─────────────────────────────────────────────────────────────────────────────
class TestMainDispatch:
    def test_within_budget_exit_0_prints_summary(self, ledgers, capsys):
        ledgers("A", 50)
        ledgers("B", 100)
        ledgers("C", 150)
        rc = cdb.main([])
        assert rc == 0
        assert "OK:" in capsys.readouterr().out

    def test_breach_exit_1_prints_message(self, ledgers, capsys):
        ledgers("A", 150)
        ledgers("B", 100)
        ledgers("C", 150)
        rc = cdb.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "compaction pass" in out
        assert "A.md" in out

    def test_missing_file_exit_1_no_traceback(self, ledgers, capsys):
        ledgers("A", None)  # missing
        ledgers("B", 100)
        ledgers("C", 150)
        rc = cdb.main([])  # must NOT raise — fail loud via exit code + message
        assert rc == 1
        assert "is missing" in capsys.readouterr().out
