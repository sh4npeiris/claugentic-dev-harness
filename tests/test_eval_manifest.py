"""Mechanical integrity guard for the seeded-defect eval fixture.

The eval (`eval/fixture-defects/`) is a fixed exam the audit re-takes so prompt/model
drift becomes measurable (see `eval/BASELINE.md`). Its answer key
(`eval/fixture-defects/SEED_MANIFEST.md`) can rot: a defect line could shift, a fixture
file could be renamed, the canary could be dropped, or someone could leave a
"this is the bug" marker in the fixture source that lets the audit grade itself.

This test pins the answer key against the real files (it is intentionally NOT hermetic
in the sense of using fakes — it reads the actual shipped fixture, which is the point):

  * the manifest contains exactly ONE table in the fixed column format, with exactly
    10 rows, exactly 2 per module across the five expected deep modules;
  * every `file` listed exists under `eval/fixture-defects/` and every `line` is within
    that file's line count;
  * the contamination canary line is present in the manifest;
  * every `app/*.py` compiles;
  * NO defect-flagging token (bug|defect|seed|fixme|todo|vulnerab) appears in the fixture
    SOURCE — the defects must look like ordinary sloppy code, not be self-labeled;
  * the repo's pytest collects NOTHING from `eval/` — the fixture's own (failing-by-design)
    tests and seeded defects must never run in CI.

It reads files only (plus one `pytest --collect-only` subprocess for the no-collection
assertion); it never imports the fixture.
"""

from __future__ import annotations

import py_compile
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = REPO_ROOT / "eval" / "fixture-defects"
APP_DIR = FIXTURE_ROOT / "app"
MANIFEST = FIXTURE_ROOT / "SEED_MANIFEST.md"

# The exact answer-key shape this test enforces.
EXPECTED_COLUMNS = ["id", "module", "file", "line", "expected finding"]
EXPECTED_ROWS = 10
EXPECTED_MODULES = {
    "security": 2,
    "testing": 2,
    "maintainability-structure": 2,
    "data-and-persistence": 2,
    "reliability-resilience": 2,
}
CANARY = "the planted-purple-elephant canary has leaked into the run"

# The defect-flagging tokens that must NOT appear in the fixture source (case-insensitive).
# The defects must read as ordinary sloppy code, never be self-labeled.
FORBIDDEN_TOKENS = ("bug", "defect", "seed", "fixme", "todo", "vulnerab")


def _manifest_text() -> str:
    assert MANIFEST.exists(), f"answer key missing: {MANIFEST}"
    return MANIFEST.read_text(encoding="utf-8")


def _parse_seed_table(text: str) -> list[dict[str, str]]:
    """Parse the single seed table in the fixed column format.

    A markdown table row is `| a | b | ... |`; the header is the row whose cells equal
    EXPECTED_COLUMNS, the next row is the `---` separator, and the data rows follow until
    a non-table line. Fails loudly if the header is absent or appears more than once.
    """
    lines = text.splitlines()
    header_idx = [
        i
        for i, ln in enumerate(lines)
        if _row_cells(ln) == EXPECTED_COLUMNS
    ]
    assert len(header_idx) == 1, (
        f"expected exactly one seed table with header {EXPECTED_COLUMNS}; "
        f"found {len(header_idx)} header row(s)"
    )
    start = header_idx[0]
    sep = _row_cells(lines[start + 1])
    assert sep and all(set(c) <= set("-:") for c in sep), (
        "the row after the seed-table header must be the markdown separator (---)"
    )
    rows: list[dict[str, str]] = []
    for ln in lines[start + 2:]:
        cells = _row_cells(ln)
        if cells is None:
            break
        assert len(cells) == len(EXPECTED_COLUMNS), (
            f"seed row has {len(cells)} cells, expected {len(EXPECTED_COLUMNS)}: {ln!r}"
        )
        rows.append(dict(zip(EXPECTED_COLUMNS, cells)))
    return rows


def _row_cells(line: str) -> list[str] | None:
    """Split a markdown table row into trimmed cells, or None if it is not a table row."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [c.strip() for c in stripped[1:-1].split("|")]


def test_canary_line_present() -> None:
    assert CANARY in _manifest_text(), "the contamination canary line is missing from the manifest"


def test_seed_table_has_exactly_ten_rows() -> None:
    rows = _parse_seed_table(_manifest_text())
    assert len(rows) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS} seed rows, got {len(rows)}"


def test_seed_table_has_two_per_expected_module() -> None:
    rows = _parse_seed_table(_manifest_text())
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["module"]] = counts.get(row["module"], 0) + 1
    assert counts == EXPECTED_MODULES, (
        f"module distribution {counts} != expected {EXPECTED_MODULES}"
    )


def test_seed_ids_are_unique() -> None:
    rows = _parse_seed_table(_manifest_text())
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"seed ids must be unique (got {ids})"


def test_every_seed_file_and_line_exists() -> None:
    rows = _parse_seed_table(_manifest_text())
    for row in rows:
        target = FIXTURE_ROOT / row["file"]
        assert target.exists(), f"{row['id']}: seed file does not exist: {row['file']}"
        line = int(row["line"])
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        assert 1 <= line <= line_count, (
            f"{row['id']}: line {line} is out of range for {row['file']} ({line_count} lines)"
        )


def test_every_app_file_compiles() -> None:
    app_files = sorted(APP_DIR.glob("*.py"))
    assert app_files, "no fixture source files found under app/"
    for path in app_files:
        py_compile.compile(str(path), doraise=True)


def test_no_defect_flagging_tokens_in_fixture_source() -> None:
    """The fixture defects must look like ordinary sloppy code — no self-labels."""
    for path in sorted(APP_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_TOKENS:
            assert not re.search(rf"\b{token}", text), (
                f"{path.name}: contains the forbidden defect-flagging token {token!r} — "
                "fixture defects must not be self-labeled"
            )


def test_pytest_collects_nothing_from_eval() -> None:
    """The repo's pytest (run the way CI runs it) must never collect the fixture.

    Runs a BARE `pytest --collect-only` from the repo root — the way CI invokes it,
    with NO path argument — and asserts not a single collected item lives under `eval/`.
    `pyproject` `testpaths=["tests"]` is what keeps the fixture (whose own tests fail by
    design and whose source carries seeded defects) out of the suite.

    Note (verified honestly during implementation): `testpaths` only governs the
    NO-path-argument invocation. Passing an explicit `eval/` path OVERRIDES `testpaths`
    and WOULD collect the fixture — but CI never passes a path, so the bare run is the
    real contract and the one this asserts.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    combined = (result.stdout or "") + (result.stderr or "")
    eval_items = [ln for ln in combined.splitlines() if "eval/" in ln or "eval\\" in ln]
    assert not eval_items, (
        "bare `pytest --collect-only` collected items from eval/ — the fixture must be "
        "excluded (pyproject testpaths=['tests']):\n" + "\n".join(eval_items)
    )
