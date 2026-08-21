"""Characterization + fail-loud tests for the ledger byte-budget gate.

The gate (`scripts/claugentic-check_doc_budgets.py`) reads its caps from a per-repo config, flags
(never edits) when a budgeted ledger outgrows its byte budget, names the compaction
remediation, and fails loud on a missing/unreadable budgeted file or a broken config.
These tests lock that behaviour — especially the fail-LOUD set and the independent-read
property — so a future edit can't regress it into a silent fail-open (a missing ledger,
or a typo'd cap list, must never be a free pass).

Hermetic by construction (`budget_repo`):
  * `tmp_path` is a scratch REPO ROOT holding a real `.claude/claugentic-doc-budgets.json`
    and real ledger files — the same shape production reads, not a monkeypatched dict.
  * Both CWD seams are pinned (see the fixture), so no real repo ledger leaks in and the
    suite passes run from any directory.
  * Each file is written independently per-case, so the independence-of-read property can
    be exercised directly (one breach/broken, another fine).

TWO deliberate non-hermetic classes, each anchored on `__file__` (never the CWD) and each
saying so at its own site: `TestProductionConfig` (the real caps config IS the contract
this repo ships to its own gate) and `TestInvokedFromASubdirectory` (an end-to-end
subprocess run whose whole point is the process CWD).

MIGRATION NOTE (plan 0041 Slice 4). The fixtures used to monkeypatch a module-level
`DOC_BUDGETS` dict (and empty a `REQUIRED_SHARDS` tuple); both constants are gone, so every
fixture now writes a real config file instead. The assertions are carried over unchanged
where the contract is unchanged, and are REPLACED — never loosened — for the three boundary
cases the slice deliberately re-specified: a zero-match glob is now a silent skip (was a
hard error), a subdirectory under a glob'd dir is now a WARN (was a hard error), and shard
EXISTENCE moved out of this gate entirely into `tests/test_decisions_index_agreement.py`
(which pins it in both directions — strictly stronger than the old one-way list).
"""

from __future__ import annotations

import inspect
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import check_doc_budgets as cdb

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def budget_repo(tmp_path, monkeypatch):
    """A scratch repo root with a real caps config — the hermetic base for everything below.

    Two CWD seams, both needed, both cheap:
      * `monkeypatch.chdir(tmp_path)` — `evaluate()` resolves `CONFIG_PATH` and every config
        KEY relative to the process CWD (production establishes that CWD in `main()`), so a
        direct `evaluate()` call reads THIS scratch repo and never the real one.
      * `monkeypatch.setattr(cdb, "_repo_root", ...)` — `main()` re-anchors with its own
        `os.chdir(_repo_root())`, which would otherwise walk straight back to the real repo.
    The architecture-tree gate's suite pins the same two seams for the same reason.

    Returns a namespace:
      * `root`            — the scratch repo root (a `Path`)
      * `configure(obj)`  — write the caps config from a Python object (valid JSON)
      * `configure_text`  — write the caps config VERBATIM (for malformed-JSON cases)
      * `write(rel, n)`   — materialise `rel` with exactly `n` bytes
      * `remove(rel)`     — delete `rel`
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cdb, "_repo_root", lambda: tmp_path)
    config_path = tmp_path / cdb.CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    def configure(obj: object) -> None:
        config_path.write_text(json.dumps(obj), encoding="utf-8")

    def configure_text(text: str) -> None:
        config_path.write_text(text, encoding="utf-8")

    def deconfigure() -> None:
        """The ABSENT-config state — this repo never opted in (the fixture seeds only the dir)."""
        config_path.unlink(missing_ok=True)

    def write(rel: str, n_bytes: int) -> None:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x" * n_bytes)

    def remove(rel: str) -> None:
        (tmp_path / rel).unlink()

    return SimpleNamespace(
        root=tmp_path,
        config_path=config_path,
        configure=configure,
        configure_text=configure_text,
        deconfigure=deconfigure,
        write=write,
        remove=remove,
    )


@pytest.fixture
def ledgers(budget_repo):
    """Three budgeted ledgers at A=100, B=200, C=300 bytes — small + distinct so over/at/under
    and per-file independence are easy to drive.

    Returns a `write(name, n_bytes_or_None)` helper: pass an int to materialise a file of
    exactly that many bytes, or `None` to leave it absent (missing-file cases). Keys are
    repo-root-RELATIVE, exactly as production authors them.
    """
    budget_repo.configure({"A.md": 100, "B.md": 200, "C.md": 300})

    def write(key: str, n_bytes: int | None) -> None:
        if n_bytes is not None:
            budget_repo.write(f"{key}.md", n_bytes)

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

    def test_main_prints_warn_to_stderr_and_exits_0(self, ledgers, capsys):
        # STREAM-CONTRACT UPDATE (plan 0041 Slice 5): the assertion moved from stdout to
        # stderr, and gained the negative half. The pre-commit wrapper CAPTURES a gate's
        # stdout (so a clean commit prints nothing) and lets stderr through — a WARN on
        # stdout is therefore a WARN nobody ever sees at commit time.
        ledgers("A", 95)  # warn band only — no breach
        ledgers("B", 100)
        ledgers("C", 150)
        rc = cdb.main([])
        assert rc == 0
        captured = capsys.readouterr()
        assert "WARN:" in captured.err
        assert "A.md" in captured.err
        assert "WARN:" not in captured.out  # never on the captured (verdict) stream
        assert "OK:" in captured.out  # ...and the verdict still rides stdout


class TestWarnBandReferenceTable:
    """The band's LOWER edge, pinned against a fixed reference cap of 100.

    The relative cases above pin only that 95/100 warns — so `WARN_RATIO` 0.9 -> 0.8 or even
    -> 0.5 passes every one of them (measured). A silently-lowered ratio would start warning
    on real ledgers with nothing turning red, which is exactly the "the gate cried wolf, so
    we stopped reading it" failure. A fixed table nails all four regions at once.

    `cap * WARN_RATIO` = 90, so: 89 is below the band · 90 is the first warn · 100 is AT
    budget (warn, NOT a breach — only a STRICT excess breaches) · 101 is the first breach.
    """

    CAP = 100

    @pytest.mark.parametrize(
        "measured,expected_level",
        [(0, None), (89, None), (90, "warn"), (99, "warn"), (100, "warn"), (101, "error")],
    )
    def test_the_band_edges(self, tmp_path, measured, expected_level):
        ledger = tmp_path / "x.md"
        ledger.write_bytes(b"x" * measured)
        result = cdb._check_one(str(ledger), self.CAP)
        assert (result[0] if result is not None else None) == expected_level

    def test_the_threshold_is_derived_from_warn_ratio_not_hardcoded(self, tmp_path):
        # The table above is the fixed reference; this pins that the constant is what MOVES
        # it, so the two can't be satisfied by an unrelated hardcoded 90.
        ledger = tmp_path / "x.md"
        first_warn = int(self.CAP * cdb.WARN_RATIO)
        ledger.write_bytes(b"x" * (first_warn - 1))
        assert cdb._check_one(str(ledger), self.CAP) is None
        ledger.write_bytes(b"x" * first_warn)
        assert cdb._check_one(str(ledger), self.CAP)[0] == "warn"


# ─────────────────────────────────────────────────────────────────────────────
# INVARIANTS ledger — parity coverage at BOTH bands (WARN >= 90%, breach >= 100%).
# INVARIANTS is the accreting sibling to DECISIONS; its 20 KB budget earns the same
# WARN/breach treatment as the other ledgers, so both bands are pinned for parity.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def invariants(budget_repo):
    """A single budgeted INVARIANTS ledger at the real 20 KB cap.

    Returns a `write(n_bytes)` helper so a test materialises the ledger at an exact size to
    land in the WARN band (>= 18,000) or the breach band (>= 20,001) of the production
    20,000 budget.
    """
    rel = "docs/claugentic-INVARIANTS.md"
    budget_repo.configure({rel: 20000})

    def write(n_bytes: int) -> None:
        budget_repo.write(rel, n_bytes)

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
# THE STREAM CONTRACT (plan 0041 Slice 5) — advisory (WARN) -> stderr, verdict -> stdout.
#
# Load-bearing for the pre-commit wrapper, which CAPTURES a gate's stdout (a clean commit
# prints nothing at all) and lets stderr flow through. Put a WARN on stdout and the
# report-only grace becomes a signal nobody ever sees at commit time; put the verdict on
# stderr and a clean run stops being quiet. Both halves are pinned, in both directions, so a
# mutant that merges the streams (either way) turns this class red.
# ─────────────────────────────────────────────────────────────────────────────
class TestStreamContract:
    def test_a_clean_run_says_nothing_on_the_advisory_stream(self, ledgers, capsys):
        ledgers("A", 10)
        ledgers("B", 10)
        ledgers("C", 10)
        assert cdb.main([]) == 0
        captured = capsys.readouterr()
        assert captured.err == ""  # nothing to advise -> the wrapper stays silent
        assert captured.out.startswith(cdb.OK_SUMMARY_PREFIX)

    def test_a_problem_rides_the_verdict_stream(self, ledgers, capsys):
        ledgers("A", 150)  # breach
        ledgers("B", 10)
        ledgers("C", 10)
        assert cdb.main([]) == 1
        captured = capsys.readouterr()
        assert "A.md" in captured.out
        assert captured.err == ""  # a breach is a verdict, never an advisory

    def test_a_warn_and_a_breach_land_on_different_streams(self, ledgers, capsys):
        # THE split, exercised in one run: the warn must not follow the breach onto stdout,
        # and the breach must not follow the warn onto stderr.
        ledgers("A", 95)  # warn band
        ledgers("B", 10)
        ledgers("C", 400)  # breach
        assert cdb.main([]) == 1
        captured = capsys.readouterr()
        assert "C.md" in captured.out and "A.md" not in captured.out
        assert "A.md" in captured.err and "C.md" not in captured.err


# ─────────────────────────────────────────────────────────────────────────────
# THE CONFIG BOUNDARY (plan 0041 Slice 4) — absent vs malformed are DIFFERENT verdicts.
#
# This is the slice's load-bearing pair: "not configured" is a legitimate steady state
# (quiet note, exit 0, nothing measured) while "configured, but broken" is a fail-loud
# problem (exit 1). A mutant that collapses either into the other must turn one of these
# classes red — so each side asserts BOTH the verdict text and the exit code.
# ─────────────────────────────────────────────────────────────────────────────
class TestAbsentConfigIsANoOp:
    def test_absent_config_exits_0_with_the_quiet_note(self, budget_repo, capsys):
        budget_repo.deconfigure()
        rc = cdb.main([])
        assert rc == 0
        assert capsys.readouterr().out.strip() == cdb.NO_CONFIG_NOTE

    def test_absent_config_measures_nothing(self, budget_repo):
        # NON-VACUOUS: a file that WOULD breach any sane cap is present, and the run is still
        # clean — proving the no-op is "nothing was measured", not "nothing happened to be big".
        budget_repo.deconfigure()
        budget_repo.write("CLAUDE.md", 10_000_000)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert warnings == []
        assert summary == cdb.NO_CONFIG_NOTE

    def test_the_absent_note_is_not_the_ok_summary(self, budget_repo):
        # The two exit-0 verdicts must stay textually distinguishable: "nothing measured" may
        # never read as "all managed ledgers within budget".
        assert "within budget" not in cdb.NO_CONFIG_NOTE

    def test_an_empty_config_is_opted_in_but_measures_nothing(self, budget_repo, capsys):
        budget_repo.configure({})
        rc = cdb.main([])
        assert rc == 0
        assert capsys.readouterr().out.strip() == cdb.NO_ENTRIES_NOTE


class TestMalformedConfigFailsLoud:
    """Each case: the problem line NAMES the defect AND the run exits 1 (never just a
    substring somewhere in the output). Declarative-artifact discipline — the artifact is
    parsed by the real parser and the assertion is on the REFUSAL, not the vocabulary."""

    def _run(self, capsys) -> tuple[int, str]:
        rc = cdb.main([])
        return rc, capsys.readouterr().out

    def test_unparseable_json_exits_1_naming_the_file(self, budget_repo, capsys):
        budget_repo.configure_text('{"CLAUDE.md": 6000,}')  # trailing comma — invalid JSON
        rc, out = self._run(capsys)
        assert rc == 1
        assert cdb.CONFIG_PATH in out
        assert "not valid JSON" in out

    @pytest.mark.parametrize("root", [[], "6000", 6000, None])
    def test_a_non_object_root_exits_1(self, budget_repo, capsys, root):
        budget_repo.configure(root)
        rc, out = self._run(capsys)
        assert rc == 1
        assert "must be a JSON object" in out

    def test_a_string_cap_exits_1_naming_the_entry(self, budget_repo, capsys):
        budget_repo.configure({"CLAUDE.md": "6000"})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "CLAUDE.md" in out
        assert "non-integer byte cap" in out

    def test_a_boolean_cap_exits_1(self, budget_repo, capsys):
        # `True` is an `int` in Python: without the explicit bool guard this would become a
        # 1-byte cap that fails every file. Pinned because the bug would be silent nonsense.
        budget_repo.configure({"CLAUDE.md": True})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "non-integer byte cap" in out

    def test_a_float_cap_exits_1(self, budget_repo, capsys):
        budget_repo.configure({"CLAUDE.md": 6000.5})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "non-integer byte cap" in out

    @pytest.mark.parametrize("cap", [0, -1])
    def test_a_non_positive_cap_exits_1(self, budget_repo, capsys, cap):
        budget_repo.configure({"CLAUDE.md": cap})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "non-positive byte cap" in out

    def test_an_unknown_object_key_exits_1_naming_the_key(self, budget_repo, capsys):
        # A typo'd `maxBytes` must not silently degrade to "no cap" — name it and refuse.
        budget_repo.configure({"CLAUDE.md": {"maxBytes": 6000}})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "maxBytes" in out
        assert "unknown key" in out

    def test_an_object_without_max_exits_1(self, budget_repo, capsys):
        budget_repo.configure({"CLAUDE.md": {"reportOnly": True}})
        rc, out = self._run(capsys)
        assert rc == 1
        assert 'missing the required "max"' in out

    def test_a_non_boolean_report_only_exits_1(self, budget_repo, capsys):
        budget_repo.configure({"CLAUDE.md": {"max": 6000, "reportOnly": "yes"}})
        rc, out = self._run(capsys)
        assert rc == 1
        assert "non-boolean" in out

    def test_a_non_utf8_byte_exits_1_without_a_traceback(self, budget_repo, capsys):
        # `UnicodeDecodeError` is a `ValueError`, NOT an `OSError` — it escaped the original
        # except tuple entirely and produced a raw traceback. Named-except, not bare-ValueError.
        budget_repo.config_path.write_bytes(b'{"CLAUDE.md": 6000, "\xff\xfe.md": 1}')
        rc, out = self._run(capsys)
        assert rc == 1
        assert "not valid UTF-8" in out
        assert "Traceback" not in out

    def test_a_utf8_bom_parses_as_content(self, budget_repo):
        # PowerShell's `>` / `Set-Content` write a BOM by default, so this is the FIRST thing
        # a Windows adopter hits. `utf-8-sig` makes it content, not a syntax error.
        budget_repo.config_path.write_bytes(b"\xef\xbb\xbf" + b'{"A.md": 100}')
        budget_repo.write("A.md", 10)
        problems, _warnings, summary = cdb.evaluate()
        assert problems == []
        assert "A.md <= 100 bytes" in summary

    def test_pathologically_nested_json_exits_1_without_a_traceback(self, budget_repo, capsys):
        # Deep nesting exhausts the parser's stack as `RecursionError` — neither `OSError` nor
        # `JSONDecodeError`, so it escaped too.
        budget_repo.configure_text("[" * 60000 + "]" * 60000)
        rc, out = self._run(capsys)
        assert rc == 1
        assert "nested too deeply" in out
        assert "Traceback" not in out

    def test_a_duplicate_key_is_fatal_not_last_wins(self, budget_repo, capsys):
        # Stdlib JSON silently keeps the LAST value, so the tighter cap the author wrote
        # simply vanishes and the gate still reports OK. A cap list is a set of promises.
        budget_repo.configure_text('{"CLAUDE.md": 6000, "CLAUDE.md": 999999}')
        rc, out = self._run(capsys)
        assert rc == 1
        assert "duplicate key" in out
        assert "CLAUDE.md" in out

    def test_a_duplicate_key_inside_the_object_form_is_fatal(self, budget_repo, capsys):
        budget_repo.configure_text('{"A.md": {"max": 100, "max": 999999}}')
        rc, out = self._run(capsys)
        assert rc == 1
        assert "duplicate key" in out

    def test_a_broken_config_measures_nothing_and_is_one_line(self, budget_repo):
        # A broken CAP SOURCE is fatal to the run by design (no measurement it produced could
        # be trusted) — exactly one problem line, no summary, no partial measurement.
        budget_repo.configure_text("not json at all")
        budget_repo.write("CLAUDE.md", 10)
        problems, warnings, summary = cdb.evaluate()
        assert len(problems) == 1
        assert warnings == []
        assert summary == ""

    def test_the_malformed_verdict_is_not_the_absent_verdict(self, budget_repo, capsys):
        # THE anti-collapse pin: same repo, same ledgers, config present-but-broken vs absent
        # must differ in BOTH channels (exit code and text).
        budget_repo.configure_text("{oops")
        broken_rc, broken_out = self._run(capsys)
        budget_repo.deconfigure()
        absent_rc, absent_out = self._run(capsys)
        assert (broken_rc, absent_rc) == (1, 0)
        assert broken_out.strip() != absent_out.strip()
        assert absent_out.strip() == cdb.NO_CONFIG_NOTE


class TestKeyShapeValidation:
    """KEY-side boundary validation — the half that was missing.

    A key whose shape could ONLY ever match nothing is refused, so "a dead glob is skipped"
    honestly means *no files of that shape yet* rather than *your entry is broken and this
    gate will never tell you*. Without this, `docs/**/*.md` — the natural spelling, and the
    one `.gitignore`/tsconfig teach — measured ZERO files and printed `(0 files)` under the
    `OK:` banner at exit 0: the fail-open this module forbids, through supported-looking
    syntax.
    """

    @pytest.mark.parametrize(
        "key", ["docs/**/*.md", "docs/**", "**/*.md", "docs/deep/**/x.md"]
    )
    def test_a_double_star_key_is_refused(self, budget_repo, capsys, key):
        budget_repo.configure({key: 100})
        rc = cdb.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "`**`" in out
        assert key in out

    @pytest.mark.parametrize("key", ["docs/*/x.md", "*/x.md", "a/*b/c.md"])
    def test_a_star_outside_the_final_component_is_refused(self, budget_repo, capsys, key):
        budget_repo.configure({key: 100})
        rc = cdb.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "outside its final path component" in out
        assert key in out

    def test_an_empty_key_is_refused(self, budget_repo, capsys):
        budget_repo.configure({"   ": 100})
        rc = cdb.main([])
        assert rc == 1
        assert "empty key" in capsys.readouterr().out

    def test_the_production_shard_key_still_validates(self):
        # The shape this repo actually ships must survive the new guard — a validator that
        # rejects the live config would be caught here, not in CI.
        assert cdb._validate_key("docs/claugentic-decisions/*.md") is None

    @pytest.mark.parametrize(
        "key",
        ["CLAUDE.md", "docs/claugentic-DECISIONS.md", "docs/claugentic-decisions/*.md", "*.md"],
    )
    def test_legitimate_keys_are_accepted(self, key):
        assert cdb._validate_key(key) is None

    def test_the_refusal_happens_before_the_cap_is_read(self, budget_repo, capsys):
        # Key-then-value ordering: a broken key with a broken cap reports the KEY, which is
        # the defect that makes the entry meaningless regardless of its cap.
        budget_repo.configure({"docs/**/*.md": "not-a-number"})
        cdb.main([])
        assert "`**`" in capsys.readouterr().out


class TestConfigEntryForms:
    """The two authored value forms normalise to one internal rule shape."""

    def test_a_plain_integer_is_a_cap_with_no_grace(self):
        assert cdb._parse_rule("CLAUDE.md", 6000) == {"max_bytes": 6000, "report_only": False}

    def test_the_object_form_carries_the_grace_flag(self):
        assert cdb._parse_rule("x.md", {"max": 10, "reportOnly": True}) == {
            "max_bytes": 10,
            "report_only": True,
        }

    def test_the_object_form_defaults_report_only_to_false(self):
        assert cdb._parse_rule("x.md", {"max": 10}) == {"max_bytes": 10, "report_only": False}

    def test_both_forms_measure_identically(self, budget_repo):
        # The object form is the SAME cap plus a flag — with the flag off, the two forms are
        # indistinguishable in behaviour (pinned so the object path can't drift its own maths).
        budget_repo.configure({"A.md": 100, "B.md": {"max": 100}})
        budget_repo.write("A.md", 101)
        budget_repo.write("B.md", 101)
        problems, _warnings, _summary = cdb.evaluate()
        assert len(problems) == 2
        assert problems[0].replace("A.md", "X") == problems[1].replace("B.md", "X")

    def test_an_absent_config_returns_none_not_an_empty_map(self, tmp_path):
        # `None` (absent) and `{}` (opted in, no entries) are different states, and the loader
        # is where that distinction is made.
        assert cdb._load_config(tmp_path / "nope.json") is None
        present = tmp_path / "present.json"
        present.write_text("{}", encoding="utf-8")
        assert cdb._load_config(present) == {}


# ─────────────────────────────────────────────────────────────────────────────
# GLOB-KIND ENTRIES — the kind is declared by the KEY'S SHAPE (a `*` in the key).
#
# A key with no `*` is a single-file target (which is what every fixture ABOVE pins — those
# classes are the contract that the default kind never changed), and a `*` key fans the one
# cap out over every match, each measured INDEPENDENTLY through the UNCHANGED `_check_one`.
# ─────────────────────────────────────────────────────────────────────────────
SHARD_CAP = 1000  # small + distinct: WARN band is [900, 1000], breach is > 1000


@pytest.fixture
def shards(budget_repo):
    """A caps config with ONE glob entry + ONE single-file entry, over a scratch shard dir.

    Both entry KINDS live in the same map so a glob key and a plain key are exercised side by
    side (and the summary's per-kind rendering is observable in one run). The glob dir seeds
    two shards (`honesty.md`, `audit.md`).

    Returns a namespace with `dir` (the shard dir), `pattern` (the glob config key),
    `single` (the plain entry's key) and `write(name, n_bytes)` / `remove(name)` helpers.
    """
    shard_dir = budget_repo.root / "decisions"
    shard_dir.mkdir()
    pattern = "decisions/*.md"
    single = "INDEX.md"
    budget_repo.configure({single: 100, pattern: SHARD_CAP})
    budget_repo.write(single, 10)

    def write(name: str, n_bytes: int = 10) -> None:
        (shard_dir / name).write_bytes(b"x" * n_bytes)

    def remove(name: str) -> None:
        (shard_dir / name).unlink()

    write("honesty.md")
    write("audit.md")
    return SimpleNamespace(dir=shard_dir, pattern=pattern, single=single, write=write, remove=remove)


class TestResolveTargets:
    """The kind seam. `_resolve_targets(rel_path)` is the ONLY place that knows about entry
    kinds; everything downstream sees a plain list of file paths.

    MIGRATED: the kind used to be an explicit `{"glob": True}` marker on the rule; it is now
    the key's SHAPE. The three old marker cases become the equivalent shape cases — same
    contract (a plain key never fans out, resolution never measures), asserted through the
    new declaration.
    """

    def test_a_key_without_a_star_is_a_single_file_target(self):
        # The default-kind contract every fixture above depends on.
        assert cdb._resolve_targets("docs/x.md") == ["docs/x.md"]

    def test_the_star_in_the_key_is_what_declares_a_glob(self):
        assert cdb._is_glob("docs/claugentic-decisions/*.md") is True
        assert cdb._is_glob("docs/claugentic-DECISIONS.md") is False

    def test_a_single_file_target_is_not_required_to_exist(self, tmp_path):
        # Resolution never measures — a missing single file is `_check_one`'s fail-loud, not
        # a resolution concern (that split is what keeps `_check_one` unchanged).
        missing = str(tmp_path / "nope.md")
        assert cdb._resolve_targets(missing) == [missing]

    def test_glob_matches_are_sorted(self, shards):
        for name in ("zeta.md", "alpha.md", "mid.md"):
            shards.write(name)
        targets = cdb._resolve_targets(shards.pattern)
        assert targets == sorted(targets)
        assert [Path(t).name for t in targets] == ["alpha.md", "audit.md", "honesty.md", "mid.md", "zeta.md"]

    def test_glob_ignores_non_matching_extensions(self, shards):
        (shards.dir / "notes.txt").write_bytes(b"x" * 10)
        targets = cdb._resolve_targets(shards.pattern)
        assert [Path(t).name for t in targets] == ["audit.md", "honesty.md"]

    def test_zero_matches_resolves_to_nothing(self, shards):
        # RE-SPECIFIED (was a hard error): a cap declares a SHAPE of file, not the existence
        # of any. Existence has its own home — tests/test_decisions_index_agreement.py.
        shards.remove("honesty.md")
        shards.remove("audit.md")
        assert cdb._resolve_targets(shards.pattern) == []

    def test_a_missing_glob_directory_resolves_to_nothing(self, tmp_path):
        assert cdb._resolve_targets(str(tmp_path / "gone" / "*.md")) == []


class TestGlobNoMatchIsASilentSkip:
    def test_a_dead_glob_is_neither_a_problem_nor_a_warn(self, shards):
        shards.remove("honesty.md")
        shards.remove("audit.md")
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert warnings == []
        assert "OK:" in summary

    def test_a_dead_glob_stays_visible_in_the_summary(self, shards):
        # Skipped is not hidden: the clause still renders the count resolved THIS run, so a
        # glob watching nothing reads `(0 files)` rather than vanishing.
        shards.remove("honesty.md")
        shards.remove("audit.md")
        _problems, _warnings, summary = cdb.evaluate()
        assert f"{shards.pattern} (0 files) <= {SHARD_CAP} bytes each" in summary

    def test_a_dead_glob_does_not_mask_a_sibling_breach(self, shards, budget_repo):
        shards.remove("honesty.md")
        shards.remove("audit.md")
        budget_repo.write(shards.single, 500)  # over its 100 budget
        problems, _warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("INDEX.md" in p for p in problems)

    def test_a_dead_glob_exits_0(self, shards, capsys):
        shards.remove("honesty.md")
        shards.remove("audit.md")
        assert cdb.main([]) == 0
        assert "OK:" in capsys.readouterr().out


class TestSubdirectoryUnderAGlobIsAWarn:
    def test_a_subdirectory_warns_naming_the_unbudgeted_subtree(self, shards):
        # RE-SPECIFIED (was a hard error): nested files really are unbudgeted and worth
        # naming, but a repo that legitimately nests something must not go red for it.
        (shards.dir / "nested").mkdir()
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert "OK:" in summary
        assert len(warnings) == 1
        assert "nested" in warnings[0]
        assert "unbudgeted" in warnings[0]

    def test_a_subdirectory_leaves_the_exit_code_unchanged(self, shards, capsys):
        (shards.dir / "nested").mkdir()
        rc = cdb.main([])
        assert rc == 0
        assert "WARN:" in capsys.readouterr().err  # advisory stream (0041 S5 stream contract)

    def test_the_matched_shards_are_still_measured(self, shards):
        # The WARN must not become a substitute for the measurement it sits beside.
        (shards.dir / "nested").mkdir()
        shards.write("honesty.md", SHARD_CAP + 1)
        problems, _warnings, _summary = cdb.evaluate()
        assert any("honesty.md" in p for p in problems)

    def test_a_subdirectory_does_not_mask_a_sibling_breach(self, shards, budget_repo):
        budget_repo.write(shards.single, 500)  # over its 100 budget
        (shards.dir / "nested").mkdir()
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("INDEX.md" in p for p in problems)
        assert any("nested" in w for w in warnings)

    def test_a_plain_entry_never_surveys_subdirectories(self):
        assert cdb._unbudgeted_subtrees("docs/claugentic-DECISIONS.md") == []

    def test_an_unreadable_directory_degrades_to_a_warn_naming_the_entry(self, shards, monkeypatch):
        # `Path.is_dir()`/`Path.glob()` swallow OSError internally; `iterdir()` does NOT.
        real_iterdir = Path.iterdir

        def boom(self, *a, **k):
            if self.name == "decisions":
                raise PermissionError("denied")
            return real_iterdir(self, *a, **k)

        monkeypatch.setattr(Path, "iterdir", boom)
        problems, warnings, summary = cdb.evaluate()  # must NOT raise
        assert problems == []
        assert "OK:" in summary
        assert len(warnings) == 1
        assert shards.pattern in warnings[0]
        assert "could not be surveyed" in warnings[0]

    def test_a_failed_survey_does_not_discard_an_ALREADY_QUEUED_breach(self, shards, budget_repo, monkeypatch):
        # THE independence property, for the SURVEY half. The raising `iterdir` used to
        # propagate out of `evaluate()` — taking the breach queued by the EARLIER entry with
        # it, so the run printed nothing and the exit code came from a traceback.
        budget_repo.write(shards.single, 500)  # over its 100 budget, queued FIRST
        real_iterdir = Path.iterdir

        def boom(self, *a, **k):
            if self.name == "decisions":
                raise PermissionError("denied")
            return real_iterdir(self, *a, **k)

        monkeypatch.setattr(Path, "iterdir", boom)
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        assert any("INDEX.md" in p for p in problems)  # the earlier breach still prints
        assert any("could not be surveyed" in w for w in warnings)

    def test_a_failed_survey_still_exits_1_when_a_breach_exists(self, shards, budget_repo, monkeypatch):
        budget_repo.write(shards.single, 500)
        real_iterdir = Path.iterdir

        def boom(self, *a, **k):
            if self.name == "decisions":
                raise PermissionError("denied")
            return real_iterdir(self, *a, **k)

        monkeypatch.setattr(Path, "iterdir", boom)
        assert cdb.main([]) == 1  # must NOT raise


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

    def test_a_single_file_entry_never_gets_the_split_recourse(self, shards, budget_repo):
        # The suffix rides on the ENTRY KIND: a plain ledger can't be "split topically".
        budget_repo.write(shards.single, 500)  # over its 100 budget
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


# ─────────────────────────────────────────────────────────────────────────────
# REPORT-ONLY — the grace flag: a breach prints and passes. Nothing mechanical clears it.
# ─────────────────────────────────────────────────────────────────────────────
class TestReportOnly:
    def test_a_report_only_breach_warns_and_exits_0(self, budget_repo, capsys):
        # STREAM-CONTRACT UPDATE (plan 0041 Slice 5): a graced breach is a WARN, so it rides
        # STDERR. This is the case the split was built for — on stdout the wrapper would
        # discard it at exit 0 and the grace would be a silent no-op.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 500)
        rc = cdb.main([])
        assert rc == 0
        captured = capsys.readouterr()
        assert cdb.REPORT_ONLY_TAG in captured.err
        assert "500" in captured.err  # the measurement is still reported in full
        assert cdb.REPORT_ONLY_MARK in captured.out  # ...and the summary headline still lands

    def test_a_report_only_breach_carries_the_same_remediation(self, budget_repo):
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 500)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []  # graced — not a breach
        assert len(warnings) == 1
        assert warnings[0].startswith(cdb.REPORT_ONLY_TAG)
        assert warnings[0].endswith(cdb.REMEDIATION)  # verbatim, not a softened variant

    def test_a_fired_grace_forbids_the_all_within_budget_headline(self, budget_repo):
        # THE anti-laundering pin. A run that passes ON A GRACE is a different fact from a
        # run where everything fit, and the SUMMARY is what a CI tail or a `grep OK:` reads —
        # so the headline may not claim "all managed ledgers within budget" over a file
        # measured at 5x its cap. Whole-line equality: the headline AND the clause together.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 500)
        _problems, _warnings, summary = cdb.evaluate()
        assert summary == (
            "OK: 1 report-only breach(es) NOT within budget (see WARN above) - "
            "A.md OVER budget 100 bytes [report-only]"
        )
        assert "all managed ledgers within budget" not in summary
        assert "A.md <=" not in summary  # never rendered as cap-satisfied

    def test_the_graced_count_tracks_the_breaches_not_the_entries(self, budget_repo):
        budget_repo.configure(
            {"A.md": {"max": 100, "reportOnly": True}, "B.md": {"max": 100, "reportOnly": True}}
        )
        budget_repo.write("A.md", 500)
        budget_repo.write("B.md", 500)
        _problems, _warnings, summary = cdb.evaluate()
        assert summary.startswith("OK: 2 report-only breach(es) NOT within budget")

    def test_a_clean_sibling_entry_keeps_its_cap_satisfied_clause(self, budget_repo):
        # The headline is run-wide; the OVER-budget rendering is strictly per entry.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}, "B.md": 200})
        budget_repo.write("A.md", 500)
        budget_repo.write("B.md", 10)
        _problems, _warnings, summary = cdb.evaluate()
        assert "A.md OVER budget 100 bytes [report-only]" in summary
        assert "B.md <= 200 bytes" in summary

    def test_a_graced_glob_entry_renders_the_over_budget_clause(self, budget_repo):
        budget_repo.configure({"decisions/*.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("decisions/honesty.md", 500)
        _problems, _warnings, summary = cdb.evaluate()
        assert "decisions/*.md (1 files) OVER budget 100 bytes each [report-only]" in summary

    def test_an_unfired_grace_leaves_the_headline_alone(self, budget_repo):
        # The flag being SET is not the trigger — the grace actually FIRING is.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 10)
        _problems, _warnings, summary = cdb.evaluate()
        assert summary.startswith(cdb.OK_SUMMARY_PREFIX)
        assert "report-only" not in summary

    def test_a_report_only_entry_within_cap_produces_no_special_output(self, budget_repo):
        # The grace shows ONLY when it fires: an in-budget report-only ledger is ordinary.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 10)
        problems, warnings, summary = cdb.evaluate()
        assert problems == []
        assert warnings == []
        assert cdb.REPORT_ONLY_TAG not in summary
        assert "A.md <= 100 bytes" in summary

    def test_a_report_only_entry_in_the_warn_band_is_an_ordinary_warn(self, budget_repo):
        # Still within cap, so the grace never fired — no tag, plain WARN wording.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 95)
        problems, warnings, _summary = cdb.evaluate()
        assert problems == []
        assert len(warnings) == 1
        assert cdb.REPORT_ONLY_TAG not in warnings[0]
        assert warnings[0].endswith(cdb.WARN_REMEDIATION)

    def test_report_only_does_not_grace_a_missing_file(self, budget_repo, capsys):
        # The grace is scoped to the SIZE verdict — existence is not what it was granted for.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        rc = cdb.main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert "is missing" in captured.out  # a problem line — the verdict stream
        # The tag must be absent from BOTH streams now that they differ: asserting only on
        # stdout would let a graced-missing-file regression hide on the advisory stream.
        assert cdb.REPORT_ONLY_TAG not in captured.out + captured.err

    def test_report_only_does_not_grace_an_unreadable_file(self, budget_repo, monkeypatch):
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("A.md", 10)
        real_read = Path.read_bytes

        def boom(self, *a, **k):
            if self.name == "A.md":
                raise PermissionError("denied")
            return real_read(self, *a, **k)

        monkeypatch.setattr(Path, "read_bytes", boom)
        problems, warnings, _summary = cdb.evaluate()
        assert len(problems) == 1
        assert "could not be read" in problems[0]
        assert warnings == []

    def test_report_only_does_not_grace_a_sibling_entry(self, budget_repo):
        # Per-entry, never global: one graced entry must not soften the entry beside it.
        budget_repo.configure({"A.md": {"max": 100, "reportOnly": True}, "B.md": 100})
        budget_repo.write("A.md", 500)
        budget_repo.write("B.md", 500)
        problems, warnings, summary = cdb.evaluate()
        assert summary == ""
        assert [p for p in problems if "B.md" in p]
        assert not [p for p in problems if "A.md" in p]
        assert [w for w in warnings if "A.md" in w and w.startswith(cdb.REPORT_ONLY_TAG)]

    def test_a_graced_glob_breach_keeps_both_decorations(self, budget_repo):
        # The tag is a PREFIX and the split recourse a SUFFIX precisely so they compose.
        budget_repo.configure({"decisions/*.md": {"max": 100, "reportOnly": True}})
        budget_repo.write("decisions/honesty.md", 500)
        problems, warnings, _summary = cdb.evaluate()
        assert problems == []
        assert len(warnings) == 1
        assert warnings[0].startswith(cdb.REPORT_ONLY_TAG)
        assert warnings[0].endswith(cdb.SHARD_REMEDIATION)


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

    def test_the_whole_summary_line_is_pinned(self, budget_repo):
        # THE byte-equivalence envelope. Every other assertion here is a substring, so
        # rewording the headline or swapping the separator survives them all (measured).
        # Deliberately HERMETIC — a two-entry scratch config — so the envelope pin does not
        # re-import the live-ledger-size coupling that the CWD tests below shed.
        budget_repo.configure({"A.md": 100, "B.md": 200})
        budget_repo.write("A.md", 10)
        budget_repo.write("B.md", 10)
        _problems, _warnings, summary = cdb.evaluate()
        assert summary == (
            "OK: all managed ledgers within budget - A.md <= 100 bytes, B.md <= 200 bytes"
        )

    def test_clause_order_follows_the_authored_config(self, budget_repo):
        # The config is the source of truth for reading order too — `json.loads` preserves
        # insertion order, so the summary reads as the repo authored its caps.
        budget_repo.configure({"C.md": 300, "A.md": 100, "B.md": 200})
        for name, size in (("A.md", 10), ("B.md", 10), ("C.md", 10)):
            budget_repo.write(name, size)
        _problems, _warnings, summary = cdb.evaluate()
        assert summary.index("C.md") < summary.index("A.md") < summary.index("B.md")

    def test_summary_stays_ascii(self, shards):
        _problems, _warnings, summary = cdb.evaluate()
        summary.encode("ascii")  # raises UnicodeEncodeError if a non-ASCII glyph crept in


class TestCheckOneStaysUnchanged:
    """`_check_one` is the measurement seam every capability was added AROUND, never
    THROUGH. Pin its signature + return contract directly so a future edit can't push
    kind or grace knowledge down into it (open/closed: extend in `evaluate`'s loop)."""

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


# ─────────────────────────────────────────────────────────────────────────────
# THE REAL REPO — deliberately non-hermetic, anchored on `__file__` (never the CWD).
# ─────────────────────────────────────────────────────────────────────────────
class TestProductionConfig:
    """This repo's own caps config IS the contract it hands its gate, so it is parsed with a
    real parser and asserted per key — never grepped as text."""

    @staticmethod
    def _config() -> dict:
        return json.loads((REPO_ROOT / cdb.CONFIG_PATH).read_text(encoding="utf-8"))

    def test_the_config_exists_and_parses(self):
        assert (REPO_ROOT / cdb.CONFIG_PATH).exists()
        assert isinstance(self._config(), dict)

    def test_the_migrated_caps_are_exactly_the_five_entries(self):
        # Every cap this repo runs on, pinned byte-exactly so a drift is deliberate, never
        # accidental — the "one harness-self extra" the escape-valve ladder's rung 2 names:
        # a cap edit lands here in the same commit. WORKFLOW joined 2026-08-19 after the
        # north-star thinning pass, sized at the ~80% band per the cap-band rule
        # (docs/claugentic-decisions/doc-lifecycle.md), never at its measured size.
        assert self._config() == {
            "CLAUDE.md": 6000,
            "docs/claugentic-DECISIONS.md": 3500,
            "docs/claugentic-decisions/*.md": 14000,
            "docs/claugentic-ROADMAP.md": 14000,
            "docs/claugentic-INVARIANTS.md": 20000,
            "docs/claugentic-WORKFLOW.md": 77500,
            "docs/claugentic-standards/*.md": 20000,
        }

    def test_every_configured_entry_resolves_to_something_real(self):
        # Non-vacuous: each plain key names an existing file, and the shard glob matches the
        # shard directory's real contents (a count DERIVED from the filesystem, never typed).
        for key in self._config():
            if "*" in key:
                pattern = REPO_ROOT / key
                assert list(pattern.parent.glob(pattern.name))
            else:
                assert (REPO_ROOT / key).exists(), key

    def test_the_config_is_tracked_by_git(self):
        # THE fail-open trap this repo walked into once: `.gitignore` ignores `.claude/*` with
        # an explicit un-ignore per shared file, so a new config there is invisible to git by
        # default — and an ABSENT config is a silent no-op exit 0. An untracked caps config
        # would therefore disarm this gate in CI (and in every fresh clone) while passing
        # green locally. Asserted through git itself, not through the ignore rules' wording.
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", cdb.CONFIG_PATH],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 0, (
            f"{cdb.CONFIG_PATH} is not tracked by git — an absent config makes this gate a "
            "silent no-op, so an ignored/untracked caps config disarms it everywhere but here."
        )

    def test_the_config_is_loadable_by_the_gates_own_reader(self):
        rules = cdb._load_config(REPO_ROOT / cdb.CONFIG_PATH)
        assert rules is not None
        assert all(set(rule) == {"max_bytes", "report_only"} for rule in rules.values())
        # No entry ships with the grace flag on — the harness's own ledgers are in budget.
        assert not any(rule["report_only"] for rule in rules.values())


class TestTheInitSeedBlock:
    """`init` step 7b seeds an adopter's caps from a literal JSON block in its SKILL — so that
    block is CONFIG SOURCE CODE for every adopter repo, validated by nothing until now.

    It is validated HERE, through the gate's own reader (`_load_config` / `_parse_rule`), because
    a seed that this gate refuses is a repo that cannot commit: the wrapper runs the gate on
    every commit, and a malformed or fail-open cap list is a boundary error at exit 1. Reading
    it out of the skill (rather than restating it) is what keeps ONE source of truth — a copy
    here would drift silently and pin nothing.
    """

    INIT_SKILL = REPO_ROOT / "skills" / "init" / "SKILL.md"

    @classmethod
    def _seed_text(cls) -> str:
        """The one ```json fence in init's SKILL — asserted UNIQUE, never taken by ordinal."""
        blocks = re.findall(
            r"^[ \t]*```json[ \t]*\n(.*?)^[ \t]*```[ \t]*$",
            cls.INIT_SKILL.read_text(encoding="utf-8"),
            re.MULTILINE | re.DOTALL,
        )
        assert len(blocks) == 1, f"expected exactly one json seed block, found {len(blocks)}"
        return textwrap.dedent(blocks[0])

    def _seed(self, tmp_path: Path) -> dict:
        """Load the seed through the GATE'S OWN reader — not `json.loads`, which would miss
        every rule the gate enforces (duplicate keys, `**`, a non-positive cap, a stray key)."""
        path = tmp_path / "seed.json"
        path.write_text(self._seed_text(), encoding="utf-8")
        rules = cdb._load_config(path)
        assert rules is not None
        return rules

    def test_the_seed_loads_through_the_gates_own_reader(self, tmp_path):
        rules = self._seed(tmp_path)
        assert rules, "the seed declares no entries — an adopter would opt in to nothing"
        assert all(set(rule) == {"max_bytes", "report_only"} for rule in rules.values())

    def test_every_seeded_key_is_a_shape_the_gate_accepts(self, tmp_path):
        # `_parse_rule` is the boundary; running each key through it is what makes "the seed is
        # valid" a measurement instead of a reading. A `**` glob or a `*` outside the final
        # component would raise here — both are fail-open shapes that measure nothing.
        for key, rule in self._seed(tmp_path).items():
            assert cdb._parse_rule(key, rule["max_bytes"]) == {
                "max_bytes": rule["max_bytes"],
                "report_only": False,
            }

    def test_the_seed_never_caps_a_file_init_does_not_create(self, tmp_path):
        # THE load-bearing exclusion (0041 S6 reliability verdict): a cap on an ABSENT file is
        # a hard exit 1 — even under `reportOnly`, which graces the SIZE verdict only. So the
        # seed may name only files the same `init` run guarantees exist. INVARIANTS is
        # recreate-on-demand (the workflow lazily creates it), so an INVARIANTS key would hand
        # an adopter a repo that cannot commit — the method this test's name describes.
        # WORKFLOW is asserted here for a DIFFERENT reason (corrected 0041 S12b): `init` DOES
        # deliver it, so it is PRESENT and absence is not its story. It is a managed full-copy
        # doc the adopter does not author, so a cap on it fires their gate on harness-authored
        # bytes they cannot condense — and a re-`init` refresh could breach it unaided.
        keys = set(self._seed(tmp_path))
        assert not [k for k in keys if "INVARIANTS" in k], keys
        assert not [k for k in keys if "WORKFLOW" in k], keys

    def test_the_seed_caps_exactly_what_that_init_run_creates(self, tmp_path):
        # The positive half of the same rule, spelled out so a future key has to justify itself:
        # CLAUDE.md (step 6 — in SHARED mode; solo writes `CLAUDE.local.md` and the skill's
        # anchoring bullet substitutes the key, which is why this literal block is the shared
        # shape and the mode-awareness lives in prose) + the three step-7a ledger seeds + the
        # zero-match-safe shard glob. Measured at Stage 7: a cap on a file the run never
        # creates blocks EVERY commit, and `reportOnly` cannot grace it.
        assert set(self._seed(tmp_path)) == {
            "CLAUDE.md",
            "docs/claugentic-DECISIONS.md",
            "docs/claugentic-decisions/*.md",
            "docs/claugentic-ROADMAP.md",
            "docs/claugentic-CHARTER.md",
        }

    def test_the_only_glob_is_zero_match_safe(self, tmp_path):
        # A glob is a SHAPE, not a file: `init` never creates `docs/claugentic-decisions/`, so
        # the seed is only safe because a zero-match glob is a silent skip. Measured against an
        # empty tree rather than asserted from the docstring.
        empty = tmp_path / "empty-repo"
        empty.mkdir()
        for key in self._seed(tmp_path):
            if "*" in key:
                assert cdb._resolve_targets(str(empty / key)) == []

    def test_the_seed_ships_no_grace_flags(self, tmp_path):
        # `reportOnly` is a DAY-ONE MEASUREMENT, never a seeded default: init sets it only for a
        # file it measured over cap in that run. A flag baked into the literal block would grace
        # every adopter's ledger silently, forever.
        assert not any(rule["report_only"] for rule in self._seed(tmp_path).values())

    def test_the_skill_states_the_grace_rule_and_the_never_raise_rule(self):
        # The two halves that live only in prose (init is a prose skill): the object form is the
        # day-one-over answer, and raising the number is the rung-2 ceiling-raise it forbids.
        # WHITESPACE-NORMALIZED, not line-scoped: the skill hard-wraps its prose, so a raw
        # substring search would silently miss a sentence that merely broke across two lines —
        # the false GREEN a "the rule is stated" pin can least afford.
        text = " ".join(self.INIT_SKILL.read_text(encoding="utf-8").split())
        assert '{"max": <the recommended number>, "reportOnly": true}' in text
        assert "Never seed a cap raised to fit" in text
        assert "nothing mechanical ever clears a `reportOnly` flag" in text
        # ...and the MODE-AWARE anchoring rule, which the five-key literal above cannot carry.
        # Measured at Stage 7: without it a fresh SOLO adopter's very first commit is refused
        # forever, because solo writes `CLAUDE.local.md` and never creates `CLAUDE.md`.
        assert "CLAUDE.local.md" in text
        assert "drop any non-glob key whose target does not exist on disk" in text


class TestInvokedFromASubdirectory:
    """CWD-independence, end to end (0040-banked). The gate is a subprocess here on purpose:
    the process working directory is the thing under test, so it cannot be faked in-process."""

    @staticmethod
    def _run(cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "claugentic-check_doc_budgets.py")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(cwd),
        )

    def test_output_is_identical_from_the_repo_root_and_from_a_subdirectory(self):
        at_root = self._run(REPO_ROOT)
        at_subdir = self._run(REPO_ROOT / "tests")
        # The property under test is CROSS-CWD EQUALITY, not "the repo is currently in
        # budget" — so no absolute `returncode == 0` here: a docs commit that breaches a
        # ledger must turn the doc-budget GATE red, never this unit test, for a reason that
        # has nothing to do with working directories.
        assert at_subdir.returncode == at_root.returncode
        assert at_subdir.stdout == at_root.stdout
        # STREAM-CONTRACT UPDATE (plan 0041 Slice 5): warnings moved to stderr, so stdout
        # equality alone no longer covers the gate's whole output.
        # HONEST STATUS (measured): today BOTH sides are empty — no live ledger is in the WARN
        # band — so this line currently compares "" == "". It costs nothing and ARMS ITSELF the
        # moment any ledger crosses 90%, which is exactly when a CWD-dependent advisory would
        # start diverging unnoticed.
        assert at_subdir.stderr == at_root.stderr
        # ...with a size-INDEPENDENT non-vacuity guard: `CLAUDE.md` is named by the OK
        # summary and by any breach line alike, so this is red exactly when the gate no-ops
        # (an absent/renamed config) — which is the way this comparison could pass emptily.
        assert "CLAUDE.md" in at_root.stdout

    def test_a_decoy_repo_in_the_cwd_cannot_redirect_the_gate(self, tmp_path):
        # THE anchor pin. Both cases above run with a cwd INSIDE this repo, so `_repo_root`'s
        # `Path(__file__)` and a mutant's `Path.cwd()` resolve the SAME root and the mutant
        # survives the entire suite (measured). A git-init'ed DECOY repo holding its own caps
        # config and a wildly over-cap CLAUDE.md is what diverges them: anchored on the
        # script's own location the gate never sees the decoy; anchored on the cwd it would
        # measure it and exit 1.
        subprocess.run(
            ["git", "init", "-q", str(tmp_path)], check=True, capture_output=True, text=True
        )
        (tmp_path / ".claude").mkdir()
        (tmp_path / cdb.CONFIG_PATH).write_text('{"CLAUDE.md": 10}', encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_bytes(b"x" * 5000)  # 500x the decoy cap
        decoy = self._run(tmp_path)
        at_root = self._run(REPO_ROOT)
        assert decoy.returncode == at_root.returncode, decoy.stdout + decoy.stderr
        assert decoy.stdout == at_root.stdout
        # Both streams (0041 S5 stream contract). Same honest status as the case above: empty
        # on both sides today, live the moment a ledger enters the WARN band.
        assert decoy.stderr == at_root.stderr
        # Size-independent restatement of the same fact: the decoy's cap was never applied.
        assert "budget 10" not in decoy.stdout

    def test_the_summary_names_every_configured_entry(self):
        # Derived from the config + the live filesystem, so adding a shard or a budgeted
        # ledger updates this expectation automatically instead of going stale.
        # DELIBERATE live-size coupling, stated at the site: this asserts the cap-satisfied
        # rendering, so it is red if a real ledger breaches. That is accepted here (the point
        # is that the real config drives the real summary) and is exactly why the envelope
        # pin in `TestSummaryRendering` is hermetic instead.
        config = TestProductionConfig._config()
        out = self._run(REPO_ROOT / "tests").stdout
        for key, cap in config.items():
            if "*" in key:
                pattern = REPO_ROOT / key
                matched = len(list(pattern.parent.glob(pattern.name)))
                assert f"{key} ({matched} files) <= {cap} bytes each" in out
            else:
                assert f"{key} <= {cap} bytes" in out


class TestGeneratedBacklogFencesAreNotCapped:
    """A generated backlog fence is not accreting ledger prose, so it is not measured.

    Why this class exists — the flagship feature broke this gate. `/audit` and `/product gap`
    write their backlog INTO `docs/claugentic-ROADMAP.md`, and `init` seeds every adopter a
    14,000-byte cap on that exact file. A real backlog costs ~4,815 bytes per finding, so an
    adopter's THIRD finding breached the cap `init` had just given them and the pre-commit hook
    then blocked their commits. Measured on this repo: a real 25-finding gap run rendered
    120,687 bytes, taking ROADMAP to 132,200 — a 9.4x breach of its own cap.

    The distinction the fix rests on: the hand-written body ACCRETES (bounding that is what a
    cap is for); a fence body is REGENERATE-DON'T-ACCUMULATE — replaced whole each run, and it
    SHRINKS as findings are fixed. Capping it would block you from RECORDING findings, i.e.
    punish finding problems, which is worse than the disease. So it is reported, never capped.
    """

    FENCE = (
        "<!-- harness-audit:backlog:start -->\n"
        "{body}\n"
        "<!-- harness-audit:backlog:end -->\n"
    )

    def test_a_huge_generated_fence_does_not_breach(self, budget_repo):
        budget_repo.configure({"R.md": 100})
        body = "x" * 5000
        (budget_repo.root / "R.md").write_text(
            "hand-written\n" + self.FENCE.format(body=body), encoding="utf-8"
        )
        problems, warnings, summary = cdb.evaluate()
        assert problems == [], problems
        assert "OK:" in summary

    def test_NON_VACUITY_the_same_bytes_OUTSIDE_a_fence_do_breach(self, budget_repo):
        # Without this twin the test above could pass because nothing was measured at all.
        budget_repo.configure({"R.md": 100})
        (budget_repo.root / "R.md").write_text("x" * 5000, encoding="utf-8")
        problems, _, _ = cdb.evaluate()
        assert problems, "5000 bytes of hand-written prose against a 100-byte cap must breach"
        assert "vs budget 100" in problems[0], problems[0]

    def test_the_generated_size_is_REPORTED_even_though_it_is_not_counted(self, budget_repo):
        # Not counted must never mean not visible: a large backlog stays on screen.
        budget_repo.configure({"R.md": 100})
        (budget_repo.root / "R.md").write_text(
            "x" * 95 + "\n" + self.FENCE.format(body="y" * 4000), encoding="utf-8"
        )
        problems, warnings, _ = cdb.evaluate()
        line = " ".join(problems + warnings)
        assert "generated backlog fences" in line, line
        assert "not counted" in line, line

    def test_the_product_fence_is_excluded_too_not_only_the_audit_one(self, budget_repo):
        # Two skills write two different fences; the exclusion is keyed on the marker SHAPE,
        # so a new fence added later is covered without editing this gate.
        budget_repo.configure({"R.md": 100})
        (budget_repo.root / "R.md").write_text(
            "hand\n<!-- harness-product:backlog:start -->\n"
            + "z" * 5000
            + "\n<!-- harness-product:backlog:end -->\n",
            encoding="utf-8",
        )
        problems, _, _ = cdb.evaluate()
        assert problems == [], problems

    def test_an_UNCLOSED_fence_is_counted_in_full_the_safe_direction(self, budget_repo):
        # A malformed marker must not become an exemption loophole — if the fence never closes,
        # nothing is excluded and the bytes are measured, which fails LOUD rather than silently
        # exempting an entire ledger.
        budget_repo.configure({"R.md": 100})
        (budget_repo.root / "R.md").write_text(
            "<!-- harness-audit:backlog:start -->\n" + "x" * 5000, encoding="utf-8"
        )
        problems, _, _ = cdb.evaluate()
        assert problems, "an unclosed fence must not exempt the file"
