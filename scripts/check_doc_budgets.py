#!/usr/bin/env python3
"""Flag when a managed ledger outgrows its byte budget (deterministic, no LLM).

A monotonic-ledger trip-wire: the three managed ledgers below grow only — they
never shrink on their own — so this gate FLAGS (never edits) when one balloons
past a sane TOTAL byte budget and names the remediation (a compaction pass:
merge superseded entries to git history). It is a run-gate in the same register
as `scripts/check_versions_synced.py` — **mechanical-when-run** (plain messages,
no model judgement), run in the Definition-of-Done gate suite at Verify/Land and
in CI, but **NOT hook-wired** (the one hook-enforced gate stays the architecture
-tree check). See docs/claugentic-WORKFLOW.md -> Definition of Done.

Budgets are TOTAL bytes per ledger, NOT per-item: a per-item gate would wrongly
flag legitimate deferred-but-unplanned ROADMAP detail — the "1-liner + plan-file
once an item is planned" rule stays a model-upheld convention, not a gate.

Each ledger is read INDEPENDENTLY (mirroring the version-sync gate's discipline):
one oversize / missing / unreadable file must never mask a breach in another, so
every breach surfaces in one run. A missing budgeted file is a fail-loud problem
(don't silently skip — a deleted ledger is a contract breach, not a free pass).

Fails loud: a breach, a missing file, or an unreadable file each produce a plain,
actionable message + exit 1 — never a swallowed exception, never a silent pass.

Modes:
    python scripts/check_doc_budgets.py    # human/CI: stdout, exit 0 OK / exit 1 on any problem
"""

from __future__ import annotations

import sys
from pathlib import Path

# Paths are repo-root-relative — this gate, like check_versions_synced.py, is
# run from the repo root (`python scripts/check_doc_budgets.py`).
DOC_BUDGETS = {
    "CLAUDE.md": {"max_bytes": 6000},
    "docs/claugentic-DECISIONS.md": {"max_bytes": 40000},
    "docs/claugentic-ROADMAP.md": {"max_bytes": 12000},
}

# The single source of the named fix — printed verbatim on every breach so the
# remediation never drifts between message instances.
REMEDIATION = "over budget — run a compaction pass (merge superseded entries to git history)"


def _check_one(rel_path: str, max_bytes: int) -> str | None:
    """Measure one ledger against its byte budget. Returns an error line or None.

    None means within budget. A non-None string is a plain, actionable problem:
    a missing file, an unreadable file, or an over-budget breach (the named fix).
    Reads this file alone (no shared state) so a sibling's failure can't mask it.
    """
    path = Path(rel_path)
    if not path.exists():
        return f"{rel_path} is missing — a budgeted ledger must exist (cannot measure it)."
    try:
        measured = len(path.read_bytes())
    except OSError as exc:
        return f"{rel_path} could not be read ({exc}) — check the file exists and is readable."
    if measured > max_bytes:
        return f"{rel_path}: {measured} bytes vs budget {max_bytes} — {REMEDIATION}"
    return None


def evaluate() -> tuple[list[str], str]:
    """Return (problem_lines, success_summary). Empty problem_lines == OK.

    Checks every ledger INDEPENDENTLY so one breach/missing/unreadable file can't
    mask another — all problems surface in a single run.
    """
    problems = [
        msg
        for rel_path, rule in DOC_BUDGETS.items()
        if (msg := _check_one(rel_path, rule["max_bytes"])) is not None
    ]
    if problems:
        return (problems, "")
    # ASCII-only output (no `<=` glyph) — the gate runs on Windows consoles
    # (cp1252) and CI alike; the version-sync template keeps its messages ASCII
    # for the same portability reason.
    summary = "OK: all managed ledgers within budget - " + ", ".join(
        f"{rel_path} <= {rule['max_bytes']} bytes" for rel_path, rule in DOC_BUDGETS.items()
    )
    return ([], summary)


def main(argv: list[str]) -> int:
    problems, summary = evaluate()
    if problems:
        print("\n".join(problems))
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
