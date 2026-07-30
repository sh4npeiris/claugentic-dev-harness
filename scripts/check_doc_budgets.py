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
by load profile: CLAUDE.md is the always-loaded anchor (kept tight); the decisions
ledger is read ON-DEMAND (consulted before re-litigating a past choice) and is
SHARDED — a small routing index plus one file per topic — so its cap is per-shard.

HONEST SCOPE of that per-shard cap: it bounds the SIZE of each shard a consultation
reads. It does NOT bound how many shards a consultation opens — that is the index's
model-upheld routing, which no gate measures. Read "smaller reads" as "a bounded
worst case per file," never as a proven per-consultation total.

Budgets are TOTAL bytes per ledger, NOT per-item: a per-item gate would wrongly
flag legitimate deferred-but-unplanned ROADMAP detail — the "1-liner + plan-file
once an item is planned" rule stays a model-upheld convention, not a gate.

Two ENTRY KINDS, declared explicitly (never sniffed from the key's shape):
  * no `"glob"` key  -> the key IS the one file to measure (the default kind).
  * `"glob": True`   -> the key is a `<dir>/<pattern>` the cap fans out over, EACH
    match measured independently against the SAME cap. One entry covers every
    present and future shard, so adding a shard needs no edit here.
`_resolve_targets` is the only place that knows the difference; `_check_one` below
measures a plain path and has no idea globs exist.

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

# The sharded decisions ledger's directory — named once so the glob budget entry, the
# required-shard list and the no-subdirectory assertion can't drift apart (DRY).
SHARD_DIR = "docs/claugentic-decisions"

# Paths are repo-root-relative — this gate, like check_versions_synced.py, is
# run from the repo root (`python scripts/check_doc_budgets.py`).
DOC_BUDGETS = {
    "CLAUDE.md": {"max_bytes": 6000},
    # The decisions ledger is an INDEX (a routing table, content-free by rule) — a tight
    # cap is the mechanical backstop for the model-upheld "never append entries here"
    # routing rule: slack is where a mis-routed entry would hide.
    "docs/claugentic-DECISIONS.md": {"max_bytes": 3500},
    # ...and its per-topic shards, ONE entry for all of them. A new shard needs no edit
    # here (that is the point of the glob kind); the cap bounds each shard's SIZE, not a
    # consultation's total (see HONEST SCOPE above). A shard in its WARN band is condensed
    # or SPLIT topically into a new shard — growth is horizontal, which is why a single
    # shared cap stays right as the set grows.
    f"{SHARD_DIR}/*.md": {"max_bytes": 14000, "glob": True},
    "docs/claugentic-ROADMAP.md": {"max_bytes": 12000},
    # INVARIANTS is an ACCRETING ledger (sibling to DECISIONS) whose only growth-
    # bound is this gate — budgeted because it accretes, even though it is read
    # ON-DEMAND (not auto-loaded). ~3.5 KB today; 20 KB is generous on-demand
    # headroom. WARN@90% + breach@100% + condense-on-WARN apply for free.
    "docs/claugentic-INVARIANTS.md": {"max_bytes": 20000},
}

# The seed shards the ledger index routes to. This is an EXISTENCE guard ONLY — never a
# second cap (the glob entry above is the one and only home of the shard budget), so a
# deleted shard produces exactly one message and it never mentions a budget.
#
# HONEST LIMIT: a shard created AFTER the seed is budget-covered for free (the glob) but
# its EXISTENCE is unguarded until it is listed here. That asymmetry is deliberate — the
# seed set is what the index's routing lines were written against, and a hand-maintained
# "every shard that exists" list would just re-derive the glob.
REQUIRED_SHARDS: tuple[str, ...] = tuple(
    f"{SHARD_DIR}/{name}"
    for name in (
        "audit.md",
        "build-mode.md",
        "deterministic-gates.md",
        "doc-lifecycle.md",
        "honesty.md",
        "plugin-distribution.md",
        "release-contract.md",
        "roles-review.md",
        "verify-roles.md",
        "workflow-process.md",
    )
)

# Emit a WARN (not a breach) once a ledger crosses this fraction of its budget —
# the cue to plan a compaction pass BEFORE the hard ceiling breaks the build.
WARN_RATIO = 0.9

# The named fixes, printed verbatim so the remediation never drifts between
# message instances.
REMEDIATION = "over budget — run a compaction pass (merge superseded entries to git history)"
WARN_REMEDIATION = "approaching budget — plan a compaction pass soon (merge superseded entries to git history)"

# Appended to a GLOB entry's message only. A shard has a second, shape-specific recourse a
# single-file ledger doesn't: split it topically into a new shard (growth is horizontal).
# Kept as its own constant, and applied where the entry KIND is known, so `_check_one`
# stays kind-blind and the two remediations can never drift into each other.
SHARD_REMEDIATION = " — or split this shard topically into a new one"


class BudgetConfigError(RuntimeError):
    """A budget ENTRY is structurally broken — the gate's own configuration, not a
    measured ledger.

    Raised by `_resolve_targets` for a glob that matches nothing (a moved/renamed dir
    would otherwise make the gate silently watch zero files — the forbidden fail-open)
    or for an unexpected subdirectory under a glob'd dir (recursion is speculative, so
    assert the flat shape instead of guessing at it). Caught once, in `evaluate()`, and
    surfaced as a problem line: fail loud, exit 1, no traceback, and no masking of a
    sibling entry's breach.
    """


def _resolve_targets(rel_path: str, rule: dict) -> list[str]:
    """The entry-kind seam: one budget entry -> the concrete file paths it measures.

    A rule with no truthy `"glob"` key resolves to `[rel_path]` — the DEFAULT kind, so a
    plain `{path: {"max_bytes": N}}` map behaves exactly as it always did (that contract
    is pinned by the pre-existing hermetic fixtures, which know nothing about globs). A
    `"glob": True` rule resolves to every match of `<parent>/<pattern>`, **sorted** —
    glob order is filesystem-dependent and both the collapsed summary and the message
    order must be deterministic.

    Pure with respect to shared state (it reads only the filesystem and its arguments)
    and it NEVER measures: a missing single file stays `_check_one`'s fail-loud, which is
    what keeps that function unchanged. Raises `BudgetConfigError` on a broken glob entry.
    """
    if not rule.get("glob"):
        return [rel_path]
    pattern = Path(rel_path)
    parent = pattern.parent
    matches = sorted(p.as_posix() for p in parent.glob(pattern.name) if p.is_file())
    if not matches:
        raise BudgetConfigError(
            f"{rel_path} matched no files — a glob budget entry that watches nothing is a "
            "silent fail-open; restore the directory or remove the entry."
        )
    subdirs = sorted(p.as_posix() for p in parent.iterdir() if p.is_dir())
    if subdirs:
        raise BudgetConfigError(
            f"{rel_path} has unexpected subdirectories ({', '.join(subdirs)}) — this entry "
            "measures a FLAT directory and does not recurse, so nested files would go "
            "unbudgeted; flatten the directory or add a budget entry for the subtree."
        )
    return matches


def _summary_clause(rel_path: str, rule: dict, matched: int) -> str:
    """One OK-summary clause per ENTRY (not per file) — a glob collapses to a single
    clause carrying the count RESOLVED THIS RUN, so the summary can't claim a stale
    shard count. ASCII-only (`<=`, no glyph) like the rest of the summary."""
    if rule.get("glob"):
        return f"{rel_path} ({matched} files) <= {rule['max_bytes']} bytes each"
    return f"{rel_path} <= {rule['max_bytes']} bytes"


def _missing_required_shards() -> list[str]:
    """Problem lines for every `REQUIRED_SHARDS` entry that does not exist.

    Existence ONLY — never a size — so the shard budget keeps exactly one home (the glob
    entry in `DOC_BUDGETS`) and a deleted shard yields one message, not two. Read
    repo-root-relative, like `DOC_BUDGETS`.
    """
    return [
        f"{shard} is missing — the decisions-ledger index routes to it; restore it "
        "(git history) or drop it from REQUIRED_SHARDS."
        for shard in REQUIRED_SHARDS
        if not Path(shard).exists()
    ]


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
    That independence now extends to entry RESOLUTION: a structurally broken glob entry
    is reported and skipped, never allowed to abort the run over its siblings.
    """
    problems: list[str] = []
    warnings: list[str] = []
    clauses: list[str] = []
    for rel_path, rule in DOC_BUDGETS.items():
        try:
            targets = _resolve_targets(rel_path, rule)
        except BudgetConfigError as exc:
            problems.append(str(exc))
            continue
        for target in targets:
            result = _check_one(target, rule["max_bytes"])
            if result is None:
                continue
            level, msg = result
            # The shard-shaped recourse rides on the ENTRY KIND, which only this loop
            # knows — `_check_one` stays a kind-blind measurement. Decorate ONLY a message
            # that already named a remediation (a size verdict); a missing/unreadable file
            # is not something "split it topically" answers.
            if rule.get("glob") and msg.endswith((REMEDIATION, WARN_REMEDIATION)):
                msg += SHARD_REMEDIATION
            (problems if level == "error" else warnings).append(msg)
        clauses.append(_summary_clause(rel_path, rule, len(targets)))
    # A required shard that vanished is an EXISTENCE problem, appended after the budget
    # pass so it reads last and can never be mistaken for (or duplicate) a cap line.
    problems.extend(_missing_required_shards())
    if problems:
        return (problems, warnings, "")
    # ASCII-only output (no `<=` glyph) — the gate runs on Windows consoles
    # (cp1252) and CI alike; the version-sync template keeps its messages ASCII
    # for the same portability reason.
    summary = "OK: all managed ledgers within budget - " + ", ".join(clauses)
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
