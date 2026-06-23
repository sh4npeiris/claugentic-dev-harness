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

Two thresholds per ledger. The budget is a forcing function that keeps the
always-/often-loaded context lean; the **WARN band** (a ledger past WARN_RATIO of
its budget) fixes the "breaks the build with no prior signal" handicap — it emits
a WARN (printed, exit 0), the cue to plan a compaction pass BEFORE the hard
ceiling. Only a STRICT excess over the budget is a breach (exit 1). Caps differ
by load profile: CLAUDE.md is the always-loaded anchor (kept tight); DECISIONS.md
is read ON-DEMAND (consulted before re-litigating a past choice), so it carries a
more generous cap — condense it periodically when the WARN fires rather than
letting it grow unbounded.

Budgets are TOTAL bytes per ledger, NOT per-item: a per-item gate would wrongly
flag legitimate deferred-but-unplanned ROADMAP detail — the "1-liner + plan-file
once an item is planned" rule stays a model-upheld convention, not a gate.

Each ledger is read INDEPENDENTLY (mirroring the version-sync gate's discipline):
one oversize / missing / unreadable / warn file must never mask a breach in
another, so every breach surfaces in one run. A missing budgeted file is a
fail-loud problem (don't silently skip — a deleted ledger is a contract breach).

Fails loud: a breach, a missing file, or an unreadable file each produce a plain,
actionable message + exit 1 — never a swallowed exception, never a silent pass.
A WARN never changes the exit code (it is a heads-up, not a failure).

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
    "docs/claugentic-DECISIONS.md": {"max_bytes": 60000},
    "docs/claugentic-ROADMAP.md": {"max_bytes": 12000},
}

# Emit a WARN (not a breach) once a ledger crosses this fraction of its budget —
# the cue to plan a compaction pass BEFORE the hard ceiling breaks the build.
WARN_RATIO = 0.9

# The named fixes, printed verbatim so the remediation never drifts between
# message instances.
REMEDIATION = "over budget — run a compaction pass (merge superseded entries to git history)"
WARN_REMEDIATION = "approaching budget — plan a compaction pass soon (merge superseded entries to git history)"


def _check_one(rel_path: str, max_bytes: int) -> tuple[str, str] | None:
    """Measure one ledger. Returns (level, message) or None (well within budget).

    level is "error" (missing / unreadable / strict breach -> exit 1) or "warn"
    (within budget but at/over WARN_RATIO -> printed, exit 0). Reads this file
    alone (no shared state) so a sibling's failure can't mask it.
    """
    path = Path(rel_path)
    if not path.exists():
        return ("error", f"{rel_path} is missing — a budgeted ledger must exist (cannot measure it).")
    try:
        measured = len(path.read_bytes())
    except OSError as exc:
        return ("error", f"{rel_path} could not be read ({exc}) — check the file exists and is readable.")
    if measured > max_bytes:
        return ("error", f"{rel_path}: {measured} bytes vs budget {max_bytes} — {REMEDIATION}")
    if measured >= int(max_bytes * WARN_RATIO):
        return (
            "warn",
            f"{rel_path}: {measured} bytes vs budget {max_bytes} (>= {int(WARN_RATIO * 100)}%) — {WARN_REMEDIATION}",
        )
    return None


def evaluate() -> tuple[list[str], list[str], str]:
    """Return (problem_lines, warning_lines, success_summary).

    Empty problem_lines == no breach. warning_lines is informational (it never
    changes the exit code). Checks every ledger INDEPENDENTLY so one
    breach/missing/unreadable/warn file can't mask another — all surface in one run.
    """
    problems: list[str] = []
    warnings: list[str] = []
    for rel_path, rule in DOC_BUDGETS.items():
        result = _check_one(rel_path, rule["max_bytes"])
        if result is None:
            continue
        level, msg = result
        (problems if level == "error" else warnings).append(msg)
    if problems:
        return (problems, warnings, "")
    # ASCII-only output (no `<=` glyph) — the gate runs on Windows consoles
    # (cp1252) and CI alike; the version-sync template keeps its messages ASCII
    # for the same portability reason.
    summary = "OK: all managed ledgers within budget - " + ", ".join(
        f"{rel_path} <= {rule['max_bytes']} bytes" for rel_path, rule in DOC_BUDGETS.items()
    )
    return ([], warnings, summary)


def main(argv: list[str]) -> int:
    problems, warnings, summary = evaluate()
    for w in warnings:
        print(f"WARN: {w}")
    if problems:
        print("\n".join(problems))
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
