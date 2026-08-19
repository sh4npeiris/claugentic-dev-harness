#!/usr/bin/env python3
"""Flag when a managed ledger outgrows its byte budget (deterministic, no LLM).

A monotonic-ledger trip-wire: a managed ledger grows only — it never shrinks on its own
— so this gate FLAGS (never edits) when one balloons past a sane TOTAL byte budget and
names the remediation (a compaction pass: merge superseded entries to git history). It
SHIPS in the release payload and `init` DELIVERS a copy into the adopter's repo, because its
caps are per-repo data rather than harness-tuned code — unlike the harness-self
`scripts/check_versions_synced.py`, which stays stripped. **Mechanical-when-run** (plain
messages, no model judgement): it runs in the Definition-of-Done gate suite at Verify/Land, in
CI, and at COMMIT TIME wherever the shared pre-commit wrapper is wired, chained after the
architecture-tree check. Those two are the hook-chained pair; a repo with no wrapper (the
tree-gate-off case) still runs this gate on demand.
See docs/claugentic-WORKFLOW.md -> Definition of Done.

CONFIG-DRIVEN — the caps are DATA, not code. Every cap this gate enforces is read from
`<repo-root>/.claude/claugentic-doc-budgets.json`, the ONE cap source per repo — the very
file `/doctor`'s adopter budget advisory reads. This script carries no cap of its own, so a
repo — this one included — tunes its budgets without touching this file, and there is never
a second cap list to drift out of sync:

    {
      "<relpath>": <max_bytes>,                          # a plain integer byte cap
      "<relglob>": <max_bytes>,                          # ...fanned out (see ENTRY KINDS)
      "<relpath>": {"max": <bytes>, "reportOnly": true}  # ...with the grace flag
    }

Flat, path-keyed, and nothing else: no `version` field, no non-path keys at all. Paths are
repo-root-relative — `main()` anchors the process at the repo root (see `_repo_root`), so
the gate behaves identically invoked from any directory.

WHERE THE SCHEMA IS DEFINED (converged by plan 0041 Slice 6 — ONE home, no longer two).
`skills/doctor/SKILL.md` -> *Adopter doc-budget advisory* is the canonical home for the
reader-contract, and it now states ALL THREE entry forms — the plain integer cap, the
`{"max": N, "reportOnly": true}` object, and the glob-by-key form — with the same edge
semantics this module implements. This docstring describes THIS GATE's behavior; where the
two must agree about the SCHEMA, doctor's reader-contract is authoritative. One schema
statement, two readers (this gate and doctor's advisory) — never two contracts.

NOT CONFIGURED IS NOT A FAILURE, BUT A BROKEN CONFIG IS. An ABSENT config is the
not-opted-in posture: one quiet note, exit 0, nothing measured — this gate enforces only
where a repo has opted in. A PRESENT config is that repo's own signal, so it is validated
at the boundary and every structural defect — unreadable or non-UTF-8 file, unparseable or
pathologically nested JSON, a duplicate key, a non-object root, a key shape that could only
watch nothing, a non-integer or non-positive cap, an unknown object key — is a fail-loud
problem line + exit 1, never a traceback (`_load_config` catches its failure modes BY NAME;
see its docstring for the list and for why a bare `except ValueError` is refused). Absent
and malformed are deliberately DIFFERENT verdicts: collapsing them would turn a typo in
your own cap list into a silent free pass — the forbidden fail-open.

Two thresholds per entry. The budget is a forcing function that keeps the always-/often-
loaded context lean; the **WARN band** (a ledger past WARN_RATIO of its budget) fixes the
"breaks the build with no prior signal" handicap — it emits a WARN (printed to STDERR, see THE
STREAM CONTRACT below; exit 0), the cue to plan a compaction pass BEFORE the hard ceiling.
Only a STRICT excess over the budget is a breach (exit 1). Caps differ by load profile, which
is exactly why they are per-repo data: an always-loaded anchor is kept tight, while an
on-demand ledger that has been SHARDED (a small routing index plus one file per topic) caps
each shard instead.

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
else. Those same precedents also teach `**`, which this gate does NOT support and therefore
REFUSES at the boundary (`_validate_key`) rather than accepting into a pattern that measures
nothing. `_resolve_targets` is the only place that knows the difference; `_check_one`
measures a plain path and has no idea globs exist.

A GLOB entry that matches NOTHING is SKIPPED — no error, no warn. The config declares a cap
for a SHAPE of file, never the existence of any; existence is a separate concern with its
own home (the harness's own repo, for instance, keeps a test pinning its decisions index and
its shard files against each other in BOTH directions). Because `_validate_key` has
already refused every key shape that could ONLY ever match nothing, a zero-match glob
honestly means "no files of that shape yet" — that is what makes this silent skip safe. It
is not invisible either: the summary clause renders the count RESOLVED THIS RUN, so
`(0 files)` stays on screen. A SUBDIRECTORY under a glob'd directory is a WARN, not an error
— the entry measures a FLAT directory and does not recurse, so nested files really are
unbudgeted and worth naming, but that is never a reason to fail a repo that legitimately
nests something there.

REPORT-ONLY is a GRACE flag, never a cure. `{"max": N, "reportOnly": true}` downgrades a
strict BREACH of that entry from a problem (exit 1) to a warn line carrying REPORT_ONLY_TAG
and the SAME remediation — the "you inherited an over-budget ledger; here is the signal,
land your work" posture. It is scoped to the SIZE verdict alone: a missing or unreadable
budgeted file still fails loud (existence is not what the grace was granted for), and a
report-only file that is *within* its cap produces nothing special at all. A fired grace
also CHANGES THE SUMMARY — the headline states the count of report-only breaches instead of
claiming "all managed ledgers within budget", and that entry's clause renders `OVER budget`
rather than `<= max`. A run that passes on a grace must never render as a clean pass to
anyone tailing CI or grepping `OK:`. NOTHING MECHANICAL CLEARS THE FLAG — condensing the
ledger and deleting `reportOnly` is a judgement call owned by `/condense` + `/doctor`
(model-upheld); this gate will report-only forever if you let it, and it re-prints the
breach in full on every run the grace fires.

Each entry is read INDEPENDENTLY (mirroring the version-sync gate's discipline): one
oversize / missing / unreadable / warn file must never mask a breach in another, so every
breach surfaces in one run — a property that covers the SURVEY half too (see
`_unbudgeted_subtrees`), not just the measuring half. A missing budgeted file is a fail-loud
problem (don't silently skip — a deleted ledger is a contract breach). The CONFIG's own
validity is deliberately NOT that case: a broken cap source makes every measurement
untrustworthy, so it is one fatal problem line rather than a per-entry survey.

Fails loud: a breach, a missing file, an unreadable file or a broken config each produce a
plain, actionable message + exit 1 — never a swallowed exception, never a silent pass. A
WARN never changes the exit code (it is a heads-up, not a failure).

THE STREAM CONTRACT — WARN goes to STDERR, everything else to STDOUT. The two streams carry
two different kinds of statement: stdout is this run's VERDICT (the OK summary, or the problem
lines that earned the exit 1), stderr is the ADVISORY channel (every `WARN:` line — a WARN
band, a report-only breach, an unsurveyable subtree). The split exists because a caller that
must stay quiet on a clean pass has to be able to discard the verdict WITHOUT discarding the
advisory: the shared `.githooks/pre-commit` wrapper captures a gate's stdout (so a passing
commit prints nothing at all) and lets stderr flow straight through — and THIS GATE IS CHAINED
INTO THAT WRAPPER, so a report-only breach is visible at every commit in a repo whose wrapper
is wired. Merged streams make those
two requirements contradictory — the grace flag would be a silent no-op. Consequences, stated
honestly: CI logs interleave both (nothing is lost), and anyone running this gate with
`2>/dev/null` now hides its warnings. Exit codes are unchanged — a WARN is still exit 0.

Modes (run it wherever THIS script is present — it measures the repo it sits in, never
another; the pre-commit wrapper runs it for you where one is wired):
    python scripts/claugentic-check_doc_budgets.py   # human/CI: exit 0 OK / exit 1 on a problem
                                                     # verdict -> stdout, WARN -> stderr (above)
"""

from __future__ import annotations

import json
import os
import re
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

# The one grace token, used in BOTH places a fired grace is visible: prefixed to the warn
# line (a prefix, not a suffix, so it composes with SHARD_REMEDIATION instead of competing
# with it, and so the grace is the first thing read) and suffixed to that entry's summary
# clause. One token so the WARN and the summary can never disagree about what fired.
REPORT_ONLY_MARK = "[report-only]"
REPORT_ONLY_TAG = REPORT_ONLY_MARK + " "

# The two SUMMARY headlines. They differ only when a grace actually fired — and then the
# headline must NOT say "all managed ledgers within budget", because one is not: the run
# passes on the grace, which is a different fact and is stated as one. `OK:` survives in
# both (the run genuinely exits 0); what changes is the claim after it.
OK_SUMMARY_PREFIX = "OK: all managed ledgers within budget - "
GRACED_SUMMARY_PREFIX = "OK: {n} report-only breach(es) NOT within budget (see WARN above) - "

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

    Raised by `_load_config`/`_validate_key`/`_parse_rule` for an unreadable/undecodable
    file, unparseable or pathologically nested JSON, a duplicate key, a non-object root, a
    key shape that would silently watch nothing, a non-integer or non-positive cap, a
    missing/unknown object key, or a non-boolean `reportOnly`. Caught once, in `evaluate()`,
    and surfaced as a single problem line: fail loud, exit 1, no traceback. It is
    deliberately FATAL to the run rather than per-entry — when the cap source is broken, no
    measurement it produced can be trusted.
    """


def _is_glob(key: str) -> bool:
    """Is this config key a GLOB entry? The key's SHAPE is the declaration — see ENTRY KINDS."""
    return GLOB_MARKER in key


def _validate_key(key: str) -> None:
    """Boundary-validate a config KEY's SHAPE. Pure — no filesystem, exactly like the rest of
    validation; whether the target exists is `_check_one`'s question, not this one's.

    This is where "a glob entry measures a FLAT directory and does not recurse" stops being
    documentation and becomes UNREPRESENTABLE. Two shapes are refused:

      * `**` anywhere. `docs/**/*.md` — the natural spelling of "everything under docs", and
        exactly what this module's own cited precedents (`.gitignore`, tsconfig `include`)
        teach an author to write — resolves through `<parent>.glob(<name>)` to a pattern that
        measures NOTHING here, printing `(0 files)` under the `OK:` banner at exit 0. That is
        the fail-open this module forbids, reachable through supported-looking syntax. Its
        meaning is not even stable: CPython 3.12 and 3.13 disagree on whether `**` yields
        files, so the same config would measure a different set on CI than on a laptop.
      * a `*` OUTSIDE the final path component (`docs/*/x.md`). Only the last component is
        expanded, so such an entry silently watches nothing for the same reason.

    With both refused, a zero-match glob honestly means "no files of that shape YET" — which
    is what makes the silent-skip rule in the module docstring safe to state.
    """
    if not key.strip():
        raise BudgetConfigError(
            f"{CONFIG_PATH}: a budget entry has an empty key — every key is a repo-root-relative "
            "path or a flat glob."
        )
    if GLOB_MARKER * 2 in key:
        raise BudgetConfigError(
            f'{CONFIG_PATH}: entry "{key}" uses `**`, which this gate does not support — a glob '
            "entry measures a FLAT directory and does not recurse, so a `**` key would silently "
            'measure nothing; use "<dir>/*.<ext>" and add a separate entry per subdirectory.'
        )
    head, _, _tail = key.rpartition("/")
    if GLOB_MARKER in head:
        raise BudgetConfigError(
            f'{CONFIG_PATH}: entry "{key}" has a `{GLOB_MARKER}` outside its final path component '
            "— only the last component is expanded, so this entry would silently measure "
            'nothing; put the `*` in the filename part, e.g. "docs/notes/*.md".'
        )


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """`json.loads` object hook making a DUPLICATE key fatal instead of last-wins.

    Stdlib JSON silently keeps the LAST value for a repeated key, so
    `{"CLAUDE.md": 6000, "CLAUDE.md": 999999}` parses cleanly, reports OK, and the tighter
    cap the author wrote is simply gone. A cap list is a set of promises, not a stream of
    assignments — a repeat is an author error, and this gate's whole posture is that a
    present config is a signal to be trusted. Applies at EVERY nesting level, so a repeated
    `"max"` inside an object entry is caught by the same rule.
    """
    seen: set[str] = set()
    for key, _value in pairs:
        if key in seen:
            raise BudgetConfigError(
                f'{CONFIG_PATH}: duplicate key "{key}" — JSON keeps only the last value, so one '
                "of the two would be silently discarded; keep exactly one."
            )
        seen.add(key)
    return dict(pairs)


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

    The KEY is validated first (`_validate_key`): a shape that could only ever watch nothing
    is refused before its cap is even read.
    """
    _validate_key(key)
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

    TOTALITY: every way this read can fail is caught BY NAME and converted to a
    `BudgetConfigError`. Deliberately NOT a bare `except ValueError` — `UnicodeDecodeError`
    and `json.JSONDecodeError` are both `ValueError` subclasses, and a blanket catch would
    also swallow a genuine programming error raised inside the hook. The named set:
      * `OSError`            — unreadable/permission-denied file
      * `UnicodeDecodeError` — a non-UTF-8 byte in the config (a stray latin-1 paste)
      * `json.JSONDecodeError`— syntax
      * `RecursionError`     — pathologically nested JSON exhausting the parser's stack
    Decoded as `utf-8-sig`, so a BOM (what PowerShell's `>`/`Set-Content` writes by default,
    and what an adopter will hit first) parses as content rather than as a syntax error.
    """
    if not path.exists():
        return None
    try:
        raw = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=_no_duplicate_keys
        )
    except OSError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} could not be read ({exc}) — the caps config exists but is "
            "unreadable; fix its permissions or remove it to opt out."
        ) from exc
    except UnicodeDecodeError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} is not valid UTF-8 ({exc}) — the caps config must be UTF-8 text "
            "(a BOM is fine); re-save it in UTF-8 (or remove the file to opt out)."
        ) from exc
    except json.JSONDecodeError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} is not valid JSON ({exc}) — the caps config is this repo's own cap "
            "source; fix the syntax (or remove the file to opt out)."
        ) from exc
    except RecursionError as exc:
        raise BudgetConfigError(
            f"{CONFIG_PATH} is nested too deeply to parse ({exc}) — the caps config is a FLAT "
            "map of path to byte cap; flatten it (or remove the file to opt out)."
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

    The `iterdir()` guard is load-bearing, not defensive noise. `Path.is_dir()` and
    `Path.glob()` swallow `OSError` internally; `iterdir()` does NOT — so one unreadable
    globbed directory used to raise straight out of `evaluate()`, discarding every breach
    already queued by an EARLIER entry and printing nothing at all. That is precisely the
    "one file must never mask a breach in another" property this module claims, broken by the
    half of the run that only SURVEYS. A failed survey degrades to a warn line naming the
    entry: we could not look, we say so, and every measurement still reports.
    """
    if not _is_glob(rel_path):
        return []
    parent = Path(rel_path).parent
    if not parent.is_dir():
        return []
    try:
        subdirs = sorted(p.as_posix() for p in parent.iterdir() if p.is_dir())
    except OSError as exc:
        return [
            f"{rel_path} could not be surveyed for subdirectories ({exc}) — any nested files "
            "under it are unmeasured; this entry's own matches were still measured."
        ]
    if not subdirs:
        return []
    return [
        f"{rel_path} has unexpected subdirectories ({', '.join(subdirs)}) — this entry "
        "measures a FLAT directory and does not recurse, so nested files go unbudgeted; "
        "flatten the directory or add a budget entry for the subtree."
    ]


def _summary_clause(rel_path: str, rule: dict, matched: int, graced: bool) -> str:
    """One summary clause per ENTRY (not per file) — a glob collapses to a single clause
    carrying the count RESOLVED THIS RUN, so the summary can't claim a stale shard count (and
    a dead glob visibly reads `(0 files)`). ASCII-only (`<=`, no glyph) like the rest.

    `graced` is the entry's OWN verdict for this run — did the `reportOnly` grace actually
    fire on any of its files — and it is threaded in rather than re-derived, because this
    function cannot see a measurement. It flips the clause from "cap satisfied" to
    "OVER budget", which is the whole point: a graced entry is a ledger the run is
    knowingly passing OVER its cap, and rendering it as `<= max` would state the opposite of
    what was measured. A `reportOnly` entry that is WITHIN its cap renders exactly like any
    other — the grace shows only when it actually fires."""
    if graced:
        if _is_glob(rel_path):
            return f"{rel_path} ({matched} files) OVER budget {rule['max_bytes']} bytes each {REPORT_ONLY_MARK}"
        return f"{rel_path} OVER budget {rule['max_bytes']} bytes {REPORT_ONLY_MARK}"
    if _is_glob(rel_path):
        return f"{rel_path} ({matched} files) <= {rule['max_bytes']} bytes each"
    return f"{rel_path} <= {rule['max_bytes']} bytes"


# A generated backlog fence is NOT accreting ledger prose, so it is not measured against the cap.
# The distinction is the whole reason this exclusion exists:
#   * the hand-written body ACCRETES -- a human appends to it, it only grows, and bounding that
#     growth is what the cap is for;
#   * a fence body is REGENERATE-DON'T-ACCUMULATE -- `/audit` and `/product gap` replace it whole
#     on every run, and it SHRINKS as findings get fixed. Its size is a symptom (how many open
#     findings you have), never an accretion.
# Measuring them together made the flagship feature break this gate: a real backlog costs ~4.8 KB
# per finding against init's seeded 14,000-byte ROADMAP cap, so an adopter's THIRD finding made
# their repo un-committable -- i.e. finding more problems was punished. Deliberately NOT capped
# separately: a cap on the fence would block you from RECORDING findings, which is worse than the
# disease. The size is reported instead, so it stays visible without being punitive.
FENCE_RE = re.compile(
    r"^<!--\s*harness-[\w-]+:backlog:start\s*-->.*?^<!--\s*harness-[\w-]+:backlog:end\s*-->",
    re.MULTILINE | re.DOTALL,
)


def _split_generated(raw: bytes) -> tuple[int, int]:
    """(hand_written_bytes, generated_fence_bytes) for one ledger's raw content.

    Decodes as UTF-8 to find the markers; on any decode failure the whole file counts as
    hand-written, which is the SAFE direction -- an unreadable-as-text ledger is measured in
    full rather than silently exempted.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return (len(raw), 0)
    generated = sum(len(m.group(0).encode("utf-8")) for m in FENCE_RE.finditer(text))
    return (len(raw) - generated, generated)


def _check_one(rel_path: str, max_bytes: int) -> tuple[str, str] | None:
    """Measure one ledger. Returns (level, message) or None (well within budget).

    level is "error" (missing / unreadable / strict breach -> exit 1) or "warn"
    (within budget but at/over WARN_RATIO -> printed, exit 0). Reads this file
    alone (no shared state) so a sibling's failure can't mask it.
    """
    path = Path(rel_path)
    if not path.exists():
        return (
            "error",
            f"{rel_path} is missing — a budgeted ledger must exist (cannot measure it). "
            f"If you removed it deliberately, delete its entry from {CONFIG_PATH}.",
        )
    try:
        measured, generated = _split_generated(path.read_bytes())
    except OSError as exc:
        return ("error", f"{rel_path} could not be read ({exc}) — check the file exists and is readable.")
    # Reported, never capped — so a large backlog stays VISIBLE without blocking a commit.
    note = f" (+{generated} B in generated backlog fences, not counted)" if generated else ""
    if measured > max_bytes:
        return ("error", f"{rel_path}: {measured} bytes vs budget {max_bytes}{note} — {REMEDIATION}")
    if measured >= int(max_bytes * WARN_RATIO):
        return (
            "warn",
            f"{rel_path}: {measured} bytes vs budget {max_bytes} (>= {int(WARN_RATIO * 100)}%){note} — {WARN_REMEDIATION}",
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
    graced: list[str] = []
    for rel_path, rule in config.items():
        warnings.extend(_unbudgeted_subtrees(rel_path))
        targets = _resolve_targets(rel_path)
        entry_graced = False
        for target in targets:
            result = _check_one(target, rule["max_bytes"])
            if result is None:
                continue
            level, msg = result
            # THREE things ride on facts only THIS loop knows — the entry's KIND, its grace
            # FLAG, and (for the summary) whether the grace actually FIRED — so `_check_one`
            # stays blind to all three. All three apply ONLY to a size verdict: neither
            # "split it topically" nor a granted grace answers a missing or unreadable file,
            # and neither may recolour that entry's summary clause. `size_verdict` is the
            # single suffix-sniff they share; it is computed once, BEFORE any decoration, so
            # no later test can accidentally read an earlier one's suffix.
            size_verdict = msg.endswith((REMEDIATION, WARN_REMEDIATION))
            if size_verdict and _is_glob(rel_path):
                msg += SHARD_REMEDIATION
            if size_verdict and level == "error" and rule["report_only"]:
                level, msg = "warn", REPORT_ONLY_TAG + msg
                graced.append(target)
                entry_graced = True
            (problems if level == "error" else warnings).append(msg)
        clauses.append(_summary_clause(rel_path, rule, len(targets), entry_graced))
    if problems:
        return (problems, warnings, "")
    if not clauses:
        return ([], warnings, NO_ENTRIES_NOTE)
    # A fired grace changes the HEADLINE, not just the clause: the run passes, but "all
    # managed ledgers within budget" would be a plain falsehood about a file measured over
    # its cap — and `OK:` is what a CI tail or a `grep OK:` reads. State the grace instead.
    # ASCII-only output (no `<=` glyph) — the gate runs on Windows consoles (cp1252) and CI
    # alike; the version-sync template keeps its messages ASCII for the same portability reason.
    prefix = GRACED_SUMMARY_PREFIX.format(n=len(graced)) if graced else OK_SUMMARY_PREFIX
    return ([], warnings, prefix + ", ".join(clauses))


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
    # THE STREAM CONTRACT (see the module docstring): advisory -> stderr, verdict -> stdout.
    # The pre-commit wrapper captures stdout to stay silent on a clean pass, and this gate is
    # chained into it — a WARN printed on stdout would be swallowed there
    # and the report-only grace would signal nothing.
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if problems:
        print("\n".join(problems))
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
