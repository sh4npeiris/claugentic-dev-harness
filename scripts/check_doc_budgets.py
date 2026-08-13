#!/usr/bin/env python3
"""Flag when a managed ledger outgrows its byte budget (deterministic, no LLM).

A monotonic-ledger trip-wire: a managed ledger grows only — it never shrinks on its own
— so this gate FLAGS (never edits) when one balloons past a sane TOTAL byte budget and
names the remediation (a compaction pass: merge superseded entries to git history). It is
a run-gate in the same register as `scripts/check_versions_synced.py` —
**mechanical-when-run** (plain messages, no model judgement), run in the Definition-of-Done
gate suite at Verify/Land and in CI, but **NOT hook-wired** (the one hook-enforced gate
stays the architecture-tree check). See docs/claugentic-WORKFLOW.md -> Definition of Done.

CONFIG-DRIVEN — the caps are DATA, not code. Every cap this gate enforces is read from
`<repo-root>/.claude/claugentic-doc-budgets.json`, the ONE cap source per repo (the very
file `/doctor`'s adopter budget advisory reads; the canonical schema statement lives in
`skills/doctor/SKILL.md` -> *Adopter doc-budget advisory* and is not restated here beyond
the shape below). This script carries no cap of its own, so a repo — this one included —
tunes its budgets without touching this file, and there is never a second cap list to
drift out of sync:

    {
      "<relpath>": <max_bytes>,                          # a plain integer byte cap
      "<relglob>": <max_bytes>,                          # ...fanned out (see ENTRY KINDS)
      "<relpath>": {"max": <bytes>, "reportOnly": true}  # ...with the grace flag
    }

Flat, path-keyed, and nothing else: no `version` field, no non-path keys at all. Paths are
repo-root-relative — `main()` anchors the process at the repo root (see `_repo_root`), so
the gate behaves identically invoked from any directory.

NOT CONFIGURED IS NOT A FAILURE, BUT A BROKEN CONFIG IS. An ABSENT config is the
not-opted-in posture: one quiet note, exit 0, nothing measured — this gate enforces only
where a repo has opted in. A PRESENT config is that repo's own signal, so it is validated
at the boundary and every structural defect (unparseable JSON, a non-object root, a
non-integer or non-positive cap, an unknown object key) is a fail-loud problem line + exit
1. Absent and malformed are deliberately DIFFERENT verdicts: collapsing them would turn a
typo in your own cap list into a silent free pass — the forbidden fail-open.

Two thresholds per entry. The budget is a forcing function that keeps the always-/often-
loaded context lean; the **WARN band** (a ledger past WARN_RATIO of its budget) fixes the
"breaks the build with no prior signal" handicap — it emits a WARN (printed, exit 0), the
cue to plan a compaction pass BEFORE the hard ceiling. Only a STRICT excess over the
budget is a breach (exit 1). Caps differ by load profile, which is exactly why they are
per-repo data: an always-loaded anchor is kept tight, while an on-demand ledger that has
been SHARDED (a small routing index plus one file per topic) caps each shard instead.

HONEST SCOPE of a per-shard (glob) cap: it bounds the SIZE of each shard a consultation
reads. It does NOT bound how many shards a consultation opens — that is the index's
model-upheld routing, which no gate measures. Read "smaller reads" as "a bounded worst
case per file," never as a proven per-consultation total.

Budgets are TOTAL bytes per entry, NOT per-item: a per-item gate would wrongly flag
legitimate deferred-but-unplanned ROADMAP detail — the "1-liner + plan-file once an item
is planned" rule stays a model-upheld convention, not a gate.

Two ENTRY KINDS, declared by the KEY'S SHAPE:
  * a key containing `*` -> a GLOB entry: `<dir>/<pattern>`, the cap fanned out over EACH
    match, every match measured independently against the SAME cap. One entry covers every
    present and future shard, so adding a shard needs no config edit.
  * any other key       -> the key IS the one file to measure (the default kind).
The shape IS the declaration, and it is the deliberate successor to the old in-code
`"glob": True` marker: a JSON config cannot carry a redundant kind field without inviting a
key/marker contradiction (`"a.md": {"glob": true}`) that something would then have to
adjudicate. The trade is the one every glob-keyed config makes (`.gitignore`, tsconfig
`include`): a path whose literal basename contains `*` is not expressible as a budget key —
`*` is illegal in a Windows filename and is the metacharacter `pathlib` expands everywhere
else. `_resolve_targets` is the only place that knows the difference; `_check_one` measures
a plain path and has no idea globs exist.

A GLOB entry that matches NOTHING is SKIPPED — no error, no warn. The config declares a cap
for a SHAPE of file, never the existence of any; existence is a separate concern with its
own home (for this repo, `tests/test_decisions_index_agreement.py` pins the decisions index
and its shard files against each other in BOTH directions). A dead glob is not silent
though: its OK-summary clause still renders the count RESOLVED THIS RUN, so `(0 files)`
stays on screen. A SUBDIRECTORY under a glob'd directory is a WARN, not an error — the entry
measures a FLAT directory and does not recurse, so nested files really are unbudgeted and
worth naming, but that is never a reason to fail a repo that legitimately nests something
there.

REPORT-ONLY is a GRACE flag, never a cure. `{"max": N, "reportOnly": true}` downgrades a
strict BREACH of that entry from a problem (exit 1) to a warn line carrying REPORT_ONLY_TAG
and the SAME remediation — the "you inherited an over-budget ledger; here is the signal,
land your work" posture. It is scoped to the SIZE verdict alone: a missing or unreadable
budgeted file still fails loud (existence is not what the grace was granted for), and a
report-only file that is *within* its cap produces nothing special at all. NOTHING
MECHANICAL CLEARS THE FLAG — condensing the ledger and deleting `reportOnly` is a judgement
call owned by `/condense` + `/doctor` (model-upheld); this gate will report-only forever if
you let it, and it says so on every run the grace fires.

Each entry is read INDEPENDENTLY (mirroring the version-sync gate's discipline): one
oversize / missing / unreadable / warn file must never mask a breach in another, so every
breach surfaces in one run. A missing budgeted file is a fail-loud problem (don't silently
skip — a deleted ledger is a contract breach). The CONFIG's own validity is deliberately
NOT that case: a broken cap source makes every measurement untrustworthy, so it is one
fatal problem line rather than a per-entry survey.

Fails loud: a breach, a missing file, an unreadable file or a broken config each produce a
plain, actionable message + exit 1 — never a swallowed exception, never a silent pass. A
WARN never changes the exit code (it is a heads-up, not a failure).

Modes:
    python scripts/check_doc_budgets.py    # human/CI: stdout, exit 0 OK / exit 1 on any problem
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# The ONE cap source, repo-root-relative. Named once here so the reader, the messages and
# the tests can't drift from the path `/doctor`'s advisory and `init` use (DRY).
CONFIG_PATH = ".claude/claugentic-doc-budgets.json"

# The key character that declares a GLOB entry (see ENTRY KINDS in the module docstring).
GLOB_MARKER = "*"

# The two authored spellings of an entry's object form. Named so validation, the error
# message and the schema documentation share one list.
OBJECT_MAX_KEY = "max"
OBJECT_REPORT_ONLY_KEY = "reportOnly"

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

# PREFIXED to a breach the `reportOnly` grace downgraded to a warn. A prefix (not a suffix)
# so it composes with SHARD_REMEDIATION instead of competing with it, and so the grace is
# the first thing read on the line — the message must never look like a clean pass.
REPORT_ONLY_TAG = "[report-only] "

# The ABSENT-config note: quiet, exit 0, and textually nothing like a breach or an OK
# summary — "this repo has not opted in", which is a legitimate steady state.
NO_CONFIG_NOTE = (
    f"No {CONFIG_PATH} — doc budgets are not configured for this repo; nothing measured."
)

# A PRESENT config that declares zero entries: opted in, watching nothing. Distinct from
# the OK summary, which would otherwise claim "all managed ledgers within budget" over an
# empty list.
NO_ENTRIES_NOTE = f"OK: {CONFIG_PATH} declares no budget entries; nothing measured."


class BudgetConfigError(RuntimeError):
    """The caps CONFIG is structurally broken — the gate's cap source, not a measured ledger.

    Raised by `_load_config`/`_parse_rule` for unparseable JSON, a non-object root, a
    non-integer or non-positive cap, a missing/unknown object key, or a non-boolean
    `reportOnly`. Caught once, in `evaluate()`, and surfaced as a single problem line: fail
    loud, exit 1, no traceback. It is deliberately FATAL to the run rather than per-entry —
    when the cap source is broken, no measurement it produced can be trusted.
    """


def _is_glob(key: str) -> bool:
    """Is this config key a GLOB entry? The key's SHAPE is the declaration — see ENTRY KINDS."""
    return GLOB_MARKER in key


def _cap_bytes(key: str, raw: object) -> int:
    """Validate one authored cap value and return it as an int byte count.

    Rejects `bool` explicitly: `True` is an `int` in Python, so `{"CLAUDE.md": true}` would
    otherwise sail through as a 1-byte cap and fail EVERY file — the exact silent-nonsense
    case boundary validation exists to catch. A float is rejected too (a byte count is whole)
    and so is a non-positive cap (a 0/negative ceiling can only ever breach).
    """
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise BudgetConfigError(
            f'{CONFIG_PATH}: entry "{key}" has a non-integer byte cap ({raw!r}) — a cap must be '
            'a whole number of bytes, e.g. {"CLAUDE.md": 6000}.'
        )
    if raw <= 0:
        raise BudgetConfigError(
            f'{CONFIG_PATH}: entry "{key}" has a non-positive byte cap ({raw}) — a cap must be '
            "greater than zero (a 0/negative ceiling can only ever breach)."
        )
    return raw


def _parse_rule(key: str, value: object) -> dict:
    """Validate ONE authored entry at the boundary and normalise it to the internal rule shape.

    Accepts the two authored forms — a bare `<max_bytes>` and the object
    `{"max": <bytes>, "reportOnly": true}` — and returns `{"max_bytes": int,
    "report_only": bool}` so everything downstream sees ONE shape and never re-sniffs the
    config. The object form exists ONLY for the grace flag, so any other key in it is an
    author error (a typo'd `"maxBytes"` must not silently become "no cap"), not something to
    ignore: unknown keys are named in the message so the fix is obvious.
    """
    if isinstance(value, dict):
        unknown = sorted(set(value) - {OBJECT_MAX_KEY, OBJECT_REPORT_ONLY_KEY})
        if unknown:
            raise BudgetConfigError(
                f'{CONFIG_PATH}: entry "{key}" has unknown key(s) {", ".join(unknown)} — the '
                f'object form is exactly {{"{OBJECT_MAX_KEY}": <bytes>, '
                f'"{OBJECT_REPORT_ONLY_KEY}": true}}.'
            )
        if OBJECT_MAX_KEY not in value:
            raise BudgetConfigError(
                f'{CONFIG_PATH}: entry "{key}" is missing the required "{OBJECT_MAX_KEY}" byte '
                f'cap — the object form is exactly {{"{OBJECT_MAX_KEY}": <bytes>, '
                f'"{OBJECT_REPORT_ONLY_KEY}": true}}.'
            )
        report_only = value.get(OBJECT_REPORT_ONLY_KEY, False)
        if not isinstance(report_only, bool):
            raise BudgetConfigError(
                f'{CONFIG_PATH}: entry "{key}" has a non-boolean "{OBJECT_REPORT_ONLY_KEY}" '
                f"({report_only!r}) — it is a true/false grace flag."
            )
        return {"max_bytes": _cap_bytes(key, value[OBJECT_MAX_KEY]), "report_only": report_only}
    return {"max_bytes": _cap_bytes(key, value), "report_only": False}


def _load_config(path: Path) -> dict[str, dict] | None:
    """Read + validate the per-repo caps config. Returns None when it is ABSENT.

    `None` (absent) and a `BudgetConfigError` (malformed) are the two DISTINCT boundary
    verdicts the whole not-opted-in posture rests on — see the module docstring. Entry order
    is preserved (`json.loads` yields an insertion-ordered dict), so the OK summary reads in
    the order the repo authored its caps.
    """
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} could not be read ({exc}) — the caps config exists but is "
            "unreadable; fix its permissions or remove it to opt out."
        ) from exc
    except json.JSONDecodeError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} is not valid JSON ({exc}) — the caps config is this repo's own cap "
            "source; fix the syntax (or remove the file to opt out)."
        ) from exc
    if not isinstance(raw, dict):
        raise BudgetConfigError(
            f"{CONFIG_PATH} must be a JSON object mapping each budgeted path to its byte cap — "
            f"found {type(raw).__name__}."
        )
    return {key: _parse_rule(key, value) for key, value in raw.items()}


def _resolve_targets(rel_path: str) -> list[str]:
    """The entry-kind seam: one config KEY -> the concrete file paths it measures.

    A key with no `*` resolves to `[rel_path]` — the DEFAULT kind, so a plain
    `{path: bytes}` map measures exactly the files it names. A GLOB key resolves to every
    match of `<parent>/<pattern>`, **sorted** — glob order is filesystem-dependent and both
    the collapsed summary and the message order must be deterministic. Zero matches resolve
    to `[]` (skipped, per the module docstring), which also covers a missing glob directory.

    Pure with respect to shared state (it reads only the filesystem and its argument) and it
    NEVER measures: a missing single file stays `_check_one`'s fail-loud, which is what keeps
    that function kind-blind and unchanged.
    """
    if not _is_glob(rel_path):
        return [rel_path]
    pattern = Path(rel_path)
    return sorted(p.as_posix() for p in pattern.parent.glob(pattern.name) if p.is_file())


def _unbudgeted_subtrees(rel_path: str) -> list[str]:
    """WARN lines for subdirectories under a GLOB entry's directory (this gate does not recurse).

    A non-glob key has no directory of its own to survey, and a glob whose directory is
    absent has nothing to report — both return `[]`. Kept separate from `_resolve_targets` so
    each function answers exactly one question (what do I measure? / what am I NOT measuring?).
    """
    if not _is_glob(rel_path):
        return []
    parent = Path(rel_path).parent
    if not parent.is_dir():
        return []
    subdirs = sorted(p.as_posix() for p in parent.iterdir() if p.is_dir())
    if not subdirs:
        return []
    return [
        f"{rel_path} has unexpected subdirectories ({', '.join(subdirs)}) — this entry "
        "measures a FLAT directory and does not recurse, so nested files go unbudgeted; "
        "flatten the directory or add a budget entry for the subtree."
    ]


def _summary_clause(rel_path: str, rule: dict, matched: int) -> str:
    """One OK-summary clause per ENTRY (not per file) — a glob collapses to a single
    clause carrying the count RESOLVED THIS RUN, so the summary can't claim a stale
    shard count (and a dead glob visibly reads `(0 files)`). ASCII-only (`<=`, no glyph)
    like the rest of the summary. A `reportOnly` entry that is WITHIN its cap renders
    exactly like any other — the grace shows only when it actually fires."""
    if _is_glob(rel_path):
        return f"{rel_path} ({matched} files) <= {rule['max_bytes']} bytes each"
    return f"{rel_path} <= {rule['max_bytes']} bytes"


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

    Empty problem_lines == no breach. warning_lines is informational (it never changes the
    exit code). Reads the caps config first: absent -> the quiet no-op note, malformed -> one
    fatal problem line. Otherwise checks every entry INDEPENDENTLY so one
    breach/missing/unreadable/warn file can't mask another — all surface in one run.

    Paths (the config's own, and every key in it) are repo-root-relative; `main()` anchors the
    process at the repo root before calling this.
    """
    try:
        config = _load_config(Path(CONFIG_PATH))
    except BudgetConfigError as exc:
        return ([str(exc)], [], "")
    if config is None:
        return ([], [], NO_CONFIG_NOTE)
    problems: list[str] = []
    warnings: list[str] = []
    clauses: list[str] = []
    for rel_path, rule in config.items():
        warnings.extend(_unbudgeted_subtrees(rel_path))
        targets = _resolve_targets(rel_path)
        for target in targets:
            result = _check_one(target, rule["max_bytes"])
            if result is None:
                continue
            level, msg = result
            # Both decorations ride on facts only THIS loop knows — the entry's KIND and its
            # grace FLAG — so `_check_one` stays blind to each. Both apply ONLY to a size
            # verdict: neither "split it topically" nor a granted grace answers a missing or
            # unreadable file. Computed once, BEFORE either decoration, so the second test
            # cannot accidentally read the first's suffix.
            size_verdict = msg.endswith((REMEDIATION, WARN_REMEDIATION))
            if size_verdict and _is_glob(rel_path):
                msg += SHARD_REMEDIATION
            if size_verdict and level == "error" and rule["report_only"]:
                level, msg = "warn", REPORT_ONLY_TAG + msg
            (problems if level == "error" else warnings).append(msg)
        clauses.append(_summary_clause(rel_path, rule, len(targets)))
    if problems:
        return (problems, warnings, "")
    if not clauses:
        return ([], warnings, NO_ENTRIES_NOTE)
    # ASCII-only output (no `<=` glyph) — the gate runs on Windows consoles
    # (cp1252) and CI alike; the version-sync template keeps its messages ASCII
    # for the same portability reason.
    summary = "OK: all managed ledgers within budget - " + ", ".join(clauses)
    return ([], warnings, summary)


def _repo_root() -> Path:
    """Repo root, derived from THIS script's location — never the process CWD, never hardcoded.

    `CONFIG_PATH` and every path INSIDE the config are repo-root-relative, but the gate may be
    invoked from any working directory; anchoring to the script's own location keeps it
    CWD-independent and portable (computed at runtime from `__file__`). Git is authoritative;
    falls back to `<script_dir>/..` (the script lives at `<repo>/scripts/`) when git is
    unavailable. DUPLICATED, not shared, with the sibling gates on purpose — each gate is
    independently self-contained (docs/claugentic-DECISIONS.md -> the deterministic gates).
    """
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return Path(out.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError):
        return here.parent  # convention: the script lives at <repo>/scripts/


def _force_utf8_output() -> None:
    """Emit stdout as UTF-8 so non-ASCII glyphs in messages (the em-dashes in the budget/
    remediation text) survive on Windows, where stdout defaults to the locale codepage
    (cp1252) while the consumer decodes UTF-8 → mojibake. A captured/replaced stream may lack
    `.reconfigure` → guarded, best-effort.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except (AttributeError, ValueError):
            pass


def main(argv: list[str]) -> int:
    # Boundary setup: UTF-8 output (Windows mojibake) + anchor to the repo root so the gate is
    # CWD-independent (it may be run from anywhere). See _repo_root / _force_utf8_output.
    _force_utf8_output()
    os.chdir(_repo_root())
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
