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
    byte budgets), and `REQUIRED_SHARDS` is emptied, so no real repo ledger leaks
    in and the suite stays CWD-independent (it passes run from any directory).
  * Each file is written independently per-case, so the independence-of-read
    property can be exercised directly (one breach/broken, another fine).

ONE deliberate exception: `test_the_production_required_shards_all_exist` reads the
REAL, repo-root-relative shard set on purpose — it is the pin that the shipped
`REQUIRED_SHARDS` list and the shard directory can't drift apart. It is the only
test here that assumes a working directory, and it says so at its own site.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

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

    `REQUIRED_SHARDS` is emptied too: it is production data holding repo-root-relative
    paths, so leaving it live would make these cases depend on the real repo AND on the
    caller's working directory. Emptying it keeps the fixture hermetic.
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
    monkeypatch.setattr(cdb, "REQUIRED_SHARDS", ())

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
# INVARIANTS ledger — parity coverage at BOTH bands (WARN >= 90%, breach >= 100%).
# INVARIANTS is the accreting sibling to DECISIONS; its 20 KB budget earns the same
# WARN/breach treatment as the other ledgers, so both bands are pinned for parity.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def invariants(tmp_path, monkeypatch):
    """Point DOC_BUDGETS at a single tmp INVARIANTS ledger with the real 20 KB cap.

    Mirrors the `ledgers` fixture's hermetic style: the tmp file's absolute path IS
    the DOC_BUDGETS key (so `_check_one`'s `Path(key)` resolves straight to it, no
    path-string juggling). Returns a `write(n_bytes)` helper so a test materialises
    the ledger at an exact size to land in the WARN band (>= 18,000) or the breach
    band (>= 20,001) of the production 20,000 budget. `REQUIRED_SHARDS` is emptied for
    the same hermeticity/CWD-independence reason as the `ledgers` fixture.
    """
    path = tmp_path / "claugentic-INVARIANTS.md"
    monkeypatch.setattr(cdb, "DOC_BUDGETS", {str(path): {"max_bytes": 20000}})
    monkeypatch.setattr(cdb, "REQUIRED_SHARDS", ())

    def write(n_bytes: int) -> None:
        path.write_bytes(b"x" * n_bytes)

    return write


class TestInvariantsBudget:
    def test_invariants_warn_band_warns_not_breaches(self, invariants):
        # 18,000 B is exactly 90% of the 20,000 budget — in the WARN band, within budget.
        invariants(18000)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []  # not a breach — exit 0
        assert "OK:" in summary
        blob = "\n".join(warnings)
        assert "claugentic-INVARIANTS.md" in blob
        assert "approaching budget" in blob

    def test_invariants_breach_band_fails_exit_1(self, invariants, capsys):
        # 20,001 B is a STRICT excess over the 20,000 budget — a breach (exit 1).
        invariants(20001)
        rc = cdb.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "claugentic-INVARIANTS.md" in out
        assert "20001" in out  # measured
        assert "compaction pass" in out  # the named remediation


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


# ─────────────────────────────────────────────────────────────────────────────
# GLOB-KIND BUDGET ENTRIES (plan 0040 — the sharded decisions ledger)
#
# A budget entry now carries an explicit KIND: a rule with no `"glob"` key is a
# single-file target (which is what every fixture ABOVE pins — those seven classes
# are the contract that the default kind never changed), and `"glob": True` fans the
# one cap out over every file the pattern matches, each measured INDEPENDENTLY through
# the UNCHANGED `_check_one`.
#
# Hermetic, with ONE deliberate exception: `REQUIRED_SHARDS` is production data like
# `DOC_BUDGETS`, so a test that cares about it monkeypatches it at tmp paths (the
# fixture below). The classes above don't patch it and therefore read the real repo's
# shard set — which is the intended fail-loud behaviour, not a leak: a deleted shard
# SHOULD turn this gate red.
# ─────────────────────────────────────────────────────────────────────────────
SHARD_CAP = 1000  # small + distinct: WARN band is [900, 1000], breach is > 1000


@pytest.fixture
def shards(tmp_path, monkeypatch):
    """Point DOC_BUDGETS at ONE glob entry + ONE single-file entry over tmp files.

    Both entry KINDS live in the same map so a glob rule and a plain rule are exercised
    side by side (and the summary's per-kind rendering is observable in one run). The
    glob dir seeds two shards (`honesty.md`, `audit.md`) that are ALSO the patched
    `REQUIRED_SHARDS`, so existence and cap can be driven independently.

    Returns a namespace with `dir` (the shard dir), `pattern` (the DOC_BUDGETS glob key),
    `single` (the plain entry's path) and `write(name, n_bytes)` / `remove(name)` helpers.
    """
    shard_dir = tmp_path / "decisions"
    shard_dir.mkdir()
    single = tmp_path / "INDEX.md"
    single.write_bytes(b"x" * 10)
    pattern = str(shard_dir / "*.md")
    monkeypatch.setattr(
        cdb,
        "DOC_BUDGETS",
        {
            str(single): {"max_bytes": 100},
            pattern: {"max_bytes": SHARD_CAP, "glob": True},
        },
    )
    monkeypatch.setattr(
        cdb,
        "REQUIRED_SHARDS",
        (str(shard_dir / "honesty.md"), str(shard_dir / "audit.md")),
    )

    def write(name: str, n_bytes: int = 10) -> None:
        (shard_dir / name).write_bytes(b"x" * n_bytes)

    def remove(name: str) -> None:
        (shard_dir / name).unlink()

    write("honesty.md")
    write("audit.md")
    return SimpleNamespace(dir=shard_dir, pattern=pattern, single=single, write=write, remove=remove)


class TestResolveTargets:
    """The new seam. `_resolve_targets(rel_path, rule)` is the ONLY place that knows
    about entry kinds; everything downstream sees a plain list of file paths."""

    def test_a_rule_without_a_glob_key_is_a_single_file_target(self):
        # The default-kind contract the seven fixtures above depend on — no key-sniffing.
        assert cdb._resolve_targets("docs/x.md", {"max_bytes": 10}) == ["docs/x.md"]

    def test_an_explicit_false_glob_key_is_also_a_single_file_target(self):
        assert cdb._resolve_targets("docs/x.md", {"max_bytes": 10, "glob": False}) == ["docs/x.md"]

    def test_a_single_file_target_is_not_required_to_exist(self, tmp_path):
        # Resolution never measures — a missing single file is `_check_one`'s fail-loud, not
        # a resolution error (that split is what keeps `_check_one` unchanged).
        missing = str(tmp_path / "nope.md")
        assert cdb._resolve_targets(missing, {"max_bytes": 10}) == [missing]

    def test_glob_matches_are_sorted(self, shards):
        for name in ("zeta.md", "alpha.md", "mid.md"):
            shards.write(name)
        targets = cdb._resolve_targets(shards.pattern, {"max_bytes": SHARD_CAP, "glob": True})
        assert targets == sorted(targets)
        assert [Path(t).name for t in targets] == ["alpha.md", "audit.md", "honesty.md", "mid.md", "zeta.md"]

    def test_glob_ignores_non_matching_extensions(self, shards):
        (shards.dir / "notes.txt").write_bytes(b"x" * 10)
        targets = cdb._resolve_targets(shards.pattern, {"max_bytes": SHARD_CAP, "glob": True})
        assert [Path(t).name for t in targets] == ["audit.md", "honesty.md"]

    def test_zero_matches_fails_loud(self, shards):
        shards.remove("honesty.md")
        shards.remove("audit.md")
        with pytest.raises(cdb.BudgetConfigError) as excinfo:
            cdb._resolve_targets(shards.pattern, {"max_bytes": SHARD_CAP, "glob": True})
        assert "matched no files" in str(excinfo.value)

    def test_a_missing_glob_directory_fails_loud(self, tmp_path):
        with pytest.raises(cdb.BudgetConfigError):
            cdb._resolve_targets(str(tmp_path / "gone" / "*.md"), {"max_bytes": 10, "glob": True})

    def test_a_subdirectory_under_the_glob_dir_fails_loud(self, shards):
        (shards.dir / "nested").mkdir()
        with pytest.raises(cdb.BudgetConfigError) as excinfo:
            cdb._resolve_targets(shards.pattern, {"max_bytes": SHARD_CAP, "glob": True})
        assert "nested" in str(excinfo.value)


class TestGlobEntryEvaluation:
    def test_all_shards_under_cap_is_ok(self, shards):
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert warnings == []
        assert "OK:" in summary

    def test_each_shard_is_measured_independently(self, shards):
        shards.write("honesty.md", SHARD_CAP + 1)  # breach
        shards.write("audit.md", 950)  # warn band
        shards.write("release.md", SHARD_CAP + 500)  # a second breach
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "honesty.md" in blob
        assert "release.md" in blob  # the second breach is NOT masked by the first
        assert any("audit.md" in w for w in warnings)  # the warn still surfaces

    def test_shard_in_warn_band_warns_not_breaches(self, shards):
        shards.write("honesty.md", 900)  # exactly 90% of the 1000 cap
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert "OK:" in summary
        assert any("honesty.md" in w and "approaching budget" in w for w in warnings)

    def test_a_glob_config_error_does_not_mask_a_sibling_breach(self, shards, tmp_path):
        # A structurally broken glob entry is a problem of its own — the OTHER entry's
        # breach must still surface in the same run (the independence property).
        (tmp_path / "INDEX.md").write_bytes(b"x" * 500)  # over its 100 budget
        (shards.dir / "nested").mkdir()
        problems, _warnings, summary = cdb.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "INDEX.md" in blob
        assert "nested" in blob

    def test_a_size_verdict_on_a_shard_carries_the_split_recourse(self, shards):
        # A shard has a recourse a single-file ledger does not — split it topically — so
        # BOTH size verdicts must carry `SHARD_REMEDIATION`. Pinned on the constant (not a
        # copied literal) so the message and the pin can never drift apart.
        shards.write("honesty.md", SHARD_CAP + 1)  # breach
        shards.write("audit.md", 950)  # warn band
        problems, warnings, _summary = cdb.evaluate()
        breach = [p for p in problems if "honesty.md" in p]
        warn = [w for w in warnings if "audit.md" in w]
        assert len(breach) == 1 and breach[0].endswith(cdb.SHARD_REMEDIATION)
        assert len(warn) == 1 and warn[0].endswith(cdb.SHARD_REMEDIATION)

    def test_a_single_file_entry_never_gets_the_split_recourse(self, shards, tmp_path):
        # The suffix rides on the ENTRY KIND: a plain ledger can't be "split topically".
        (tmp_path / "INDEX.md").write_bytes(b"x" * 500)  # over its 100 budget
        problems, _warnings, _summary = cdb.evaluate()
        assert [p for p in problems if "INDEX.md" in p and cdb.SHARD_REMEDIATION in p] == []

    def test_an_unreadable_shard_does_not_get_the_split_recourse(self, shards, monkeypatch):
        # Guard on the decoration: "split it topically" answers a SIZE verdict, never an
        # I/O failure. Mirrors TestUnreadableFile's Path.read_bytes monkeypatch.
        real_read = Path.read_bytes

        def boom(self, *a, **k):
            if self.name == "honesty.md":
                raise PermissionError("denied")
            return real_read(self, *a, **k)

        monkeypatch.setattr(Path, "read_bytes", boom)
        problems, _warnings, summary = cdb.evaluate()  # must NOT raise
        assert summary == ""
        unreadable = [p for p in problems if "honesty.md" in p]
        assert len(unreadable) == 1
        assert "could not be read" in unreadable[0]
        assert cdb.SHARD_REMEDIATION not in unreadable[0]

    def test_a_glob_config_error_exits_1_without_a_traceback(self, shards, monkeypatch, capsys):
        monkeypatch.setattr(cdb, "REQUIRED_SHARDS", ())  # isolate the glob error from the existence guard
        shards.remove("honesty.md")
        shards.remove("audit.md")
        rc = cdb.main([])  # must NOT raise
        assert rc == 1
        assert "matched no files" in capsys.readouterr().out


class TestRequiredShards:
    """The EXISTENCE guard — a separate construct from the cap, so a deleted shard fails
    loud while the glob entry stays the ONE home of the shard budget (no duplicate line)."""

    def test_all_required_shards_present_is_clean(self, shards):
        problems, _warnings, summary = cdb.evaluate()
        assert problems == []
        assert "OK:" in summary

    def test_a_deleted_required_shard_fails_loud(self, shards):
        shards.remove("honesty.md")
        problems, _warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("honesty.md" in p and "missing" in p for p in problems)

    def test_the_existence_error_is_not_a_second_cap_line(self, shards):
        # Exactly ONE message names the deleted shard, and it is an existence message —
        # never a budget/remediation line (the shard cap keeps a single home: the glob).
        shards.remove("honesty.md")
        problems, warnings, _summary = cdb.evaluate()
        naming_it = [m for m in problems + warnings if "honesty.md" in m]
        assert len(naming_it) == 1
        assert "budget" not in naming_it[0]
        assert "compaction pass" not in naming_it[0]

    def test_a_deleted_required_shard_exits_1(self, shards, capsys):
        shards.remove("audit.md")
        rc = cdb.main([])
        assert rc == 1
        assert "audit.md" in capsys.readouterr().out

    def test_the_production_required_shards_all_exist(self):
        # THE ONE deliberate non-hermetic case: it reads the REAL shard set, because that
        # is exactly what it pins — the shipped `REQUIRED_SHARDS` list and the shard
        # directory must not drift apart. `REQUIRED_SHARDS` holds repo-root-RELATIVE paths
        # (production runs from the repo root), so anchor them on this file's location
        # rather than the CWD — the assertion then holds from any working directory.
        repo_root = Path(__file__).resolve().parent.parent
        assert cdb.REQUIRED_SHARDS, "REQUIRED_SHARDS must not be empty"
        assert [s for s in cdb.REQUIRED_SHARDS if not (repo_root / s).exists()] == []


class TestSummaryRendering:
    def test_a_glob_entry_collapses_to_one_clause_with_a_runtime_count(self, shards):
        shards.write("release.md")
        _problems, _warnings, summary = cdb.evaluate()
        assert f"*.md (3 files) <= {SHARD_CAP} bytes each" in summary
        # ...and NOT one clause per matched file.
        assert "honesty.md <=" not in summary

    def test_the_count_tracks_the_filesystem_not_a_literal(self, shards):
        shards.write("extra-one.md")
        shards.write("extra-two.md")
        _problems, _warnings, summary = cdb.evaluate()
        assert "(4 files)" in summary

    def test_a_single_file_entry_keeps_its_plain_clause(self, shards):
        _problems, _warnings, summary = cdb.evaluate()
        assert "INDEX.md <= 100 bytes" in summary

    def test_summary_stays_ascii(self, shards):
        _problems, _warnings, summary = cdb.evaluate()
        summary.encode("ascii")  # raises UnicodeEncodeError if a non-ASCII glyph crept in


class TestCheckOneStaysUnchanged:
    """`_check_one` is the measurement seam the glob capability was added AROUND, never
    THROUGH. Pin its signature + return contract directly so a future edit can't push
    glob knowledge down into it (open/closed: extend at `_resolve_targets`)."""

    def test_signature_is_still_rel_path_and_max_bytes(self):
        assert list(inspect.signature(cdb._check_one).parameters) == ["rel_path", "max_bytes"]

    def test_under_budget_returns_none(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_bytes(b"x" * 10)
        assert cdb._check_one(str(f), 100) is None

    def test_warn_and_breach_levels_are_unchanged(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_bytes(b"x" * 90)
        assert cdb._check_one(str(f), 100)[0] == "warn"
        f.write_bytes(b"x" * 101)
        assert cdb._check_one(str(f), 100)[0] == "error"

    def test_missing_file_is_still_an_error_level(self, tmp_path):
        level, msg = cdb._check_one(str(tmp_path / "gone.md"), 100)
        assert level == "error"
        assert "is missing" in msg
