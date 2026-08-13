#!/usr/bin/env python3
"""SessionStart advisor — derive ONE plain-English "where am I / what's next" line.

The harness already DERIVES resumable state (the two backlog fences in
`docs/claugentic-ROADMAP.md`, the in-flight `.claude/plans/*.md`, and — for an
ADOPTER repo only — the CLAUDE.md `harness:managed` fence version) but never
VOLUNTEERS it. This script renders that scattered state as a single recommended
next step + a short in-flight summary, emitted once per session via a bundled
`SessionStart` hook.

It also answers "is this repo still CURRENT?" — two clauses appended to that same
one line: the stamped managed docs falling behind the INSTALLED plugin (the fix is
re-running init) and landed/cold plans piling up in `.claude/plans/` (the fix is a
`/doctor` sweep). This script is PLUGIN-RESIDENT, so those two reach an adopter on a
plugin update alone — no re-init, no shipped-doc round trip.

HONESTY REGISTER — this is an ADVISOR, not a gate. It reports what the fences and the
plugin manifest SAY, plus two deterministic derivations it owns (a numeric version
compare and a `COLD_DAYS` threshold); it never blocks, never passes/fails, and never
appears in the Definition-of-Done gate list. The `additionalContext` it injects is prefixed
"Derived suggestion (confirm before acting):" so a SessionStart injection can never
silently auto-drive a resume past `build`'s deliberate re-confirm gate (RETURN-6).

AUDIENCE-SPLIT (anti-nudge, 0024 problem #5) — `additionalContext` (the AGENT-facing
line) is injected ONLY for the in-flight-plan RESUME recommendation (a genuine
next-action for committed work). The promotional nudges (open-backlog / PARTIAL-rerun
/ no-product-spec — "work the user didn't ask for") are `systemMessage`-ONLY: the USER
stays oriented, the AGENT is not nudged. The two CURRENCY nudges (docs-behind-plugin
version skew / landed+cold plan housekeeping) fall on the SAME side of that split and are
`systemMessage`-ONLY: they are repo maintenance the USER decides on, never a next-action
the agent should absorb — they are appended to the user-facing line and must NEVER widen
`additionalContext`. RETURN-6 is intact — the disclaimer prefix is preserved wherever
`additionalContext` IS emitted.

OFF-SWITCH — `CLAUDE_HARNESS_ADVISOR=off` mutes the advisor entirely (`{}`), read at
the `main()` env boundary (fail-safe to silent; the renderer stays pure). Unset = on.

DERIVE-DON'T-STORE — it introduces NO new state store. It reads only:
  * the `harness-audit:backlog` / `harness-product:backlog` fences in
    `docs/claugentic-ROADMAP.md` (written by `audit` / `product` gap mode),
  * in-flight `.claude/plans/*.md` (in-flight == it still
    lives in the plans dir, refined by unchecked `- [ ]` boxes / non-Done Status —
    the decomposition checkboxes are the authoritative in-flight signal, the
    `Resumable from:` line is the derived human-readable convenience; see
    `skills/build/SKILL.md` -> "The resume contract"),
  * OPTIONALLY each in-flight plan's git metadata via ONE `git log -1` call — the
    relative age (RETURN-2) and the commit epoch that decides COLD (both omitted
    silently when git is unavailable or the plan is untracked),
  * OPTIONALLY the CLAUDE.md `harness:managed` fence version — ADOPTER-ONLY; this
    SOURCE repo has no such fence, so it is gracefully absent here (never a crash),
  * OPTIONALLY the PLUGIN'S OWN `.claude-plugin/plugin.json` version — located
    relative to `__file__` (the same relative shape in-source and installed under
    `${CLAUDE_PLUGIN_ROOT}`), NEVER the ADOPTER repo's CWD (an adopter repo has no
    `.claude-plugin/` of its own); any failure → None.

OUTPUT CONTRACT (SessionStart):
  * exit 0 ALWAYS; emit JSON on stdout — `{ systemMessage }` for a nudge, both
    `{ systemMessage, additionalContext }` for the resume branch (see AUDIENCE-SPLIT).
  * SILENT path — nothing actionable AND no currency clause (fresh repo / no fences /
    no plans / nothing stale), OR the off-switch — emits NEITHER key (an empty-but-present
    key still costs tokens; the no-nag posture means literally no surface). Both print `{}`.
  * SIZE-CAPPED — each of `systemMessage` / `additionalContext` is one tight line,
    capped at `MAX_LINE_CHARS` (this slice exists to fix context bloat; the
    advisor's own output is budgeted like any managed surface). On the user line the
    currency clauses are RESERVED, so an overflow eats the recommendation's tail and
    never a nudge (`_compose_user_line`).

FAIL-SAFE — ANY error (missing files, parse failure, non-repo, missing plans dir)
collapses to exit 0 with no output. A SessionStart hook must NEVER block or slow a
session (the same fail-soft posture as the pre-commit tree gate, whose wrapper lets a
git failure pass rather than abort). The fail-safe is the OUTER boundary in `main()`;
internal readers already degrade to "absent input" rather than raising, so a single
bad input never blanks the rest.

Modes:
    python scripts/claugentic-session-advisor.py    # the hook command AND the manual smoke run
                                                     # (its only consumers are the D2 smoke
                                                     # check + the tests — not a user feature)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONSTANTS — repo-root-relative (the hook runs from the project dir, like the
# tree gate). Monkeypatched in tests for hermetic tmp_path fixtures.
# ─────────────────────────────────────────────────────────────────────────────
ROADMAP_PATH = Path("docs/claugentic-ROADMAP.md")
PLANS_DIR = Path(".claude/plans")
CLAUDE_MD_PATH = Path("CLAUDE.md")

# The PLUGIN'S OWN manifest — the one path here anchored on `__file__`, NEVER the CWD.
# The advisor ships at `<plugin-root>/scripts/`, so the manifest is always two parents
# up + `.claude-plugin/plugin.json` — the SAME relative shape in this source repo and
# installed under `${CLAUDE_PLUGIN_ROOT}` (see the manifest's SessionStart hook command).
# Anchoring on the CWD would read the ADOPTER repo, which has no `.claude-plugin/` at
# all — a category error, not merely a miss.
PLUGIN_MANIFEST_PATH = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT BUDGET — the HARD ceiling for each emitted line (one tight line each).
# ─────────────────────────────────────────────────────────────────────────────
MAX_LINE_CHARS = 320

# The floor on the reserve in `_compose_user_line`: if reserving the clause tail would
# leave the recommendation less than this, the reserve is abandoned and the whole line
# is capped normally. Guards the degenerate case (a clause tail near the whole budget)
# where a reserve would slice the head down to an ellipsis — or past zero.
MIN_HEAD_CHARS = 40

# The advisory prefix on `additionalContext` (RETURN-6): a SessionStart injection
# must never read as an instruction the agent silently acts on. Single source of
# the wording so the contract can't drift between message and test.
ADVISORY_PREFIX = "Derived suggestion (confirm before acting): "

# The skill slugs surfaced in recommendations (namespaced — the user types these).
PRODUCT_CMD = "/claugentic-dev-harness:product"
BUILD_CMD = "/claugentic-dev-harness:build"
INIT_CMD = "/claugentic-dev-harness:init"
DOCTOR_CMD = "/claugentic-dev-harness:doctor"

# The separator joining the recommendation and the currency clauses into ONE line.
CLAUSE_SEP = " · "

# An in-flight plan whose last commit is older than this is COLD (the lifecycle drift
# `/doctor` sweeps). A CONSTANT, not configurable — YAGNI: nobody has asked for a second
# threshold, and a knob here would need a config surface the advisor deliberately lacks.
COLD_DAYS = 30
COLD_SECONDS = COLD_DAYS * 24 * 60 * 60

# ─────────────────────────────────────────────────────────────────────────────
# FENCE MARKERS — pinned to the EXACT HTML-comment markers `audit` / `product`
# write into `docs/claugentic-ROADMAP.md` (single source of truth for the read).
# ─────────────────────────────────────────────────────────────────────────────
AUDIT_FENCE = ("<!-- harness-audit:backlog:start -->", "<!-- harness-audit:backlog:end -->")
PRODUCT_FENCE = ("<!-- harness-product:backlog:start -->", "<!-- harness-product:backlog:end -->")

# A fence whose body still carries the "No open items" / "No product spec yet"
# sentinel text is EMPTY (no actionable backlog). Matched case-insensitively on a
# stable lead phrase so a reworded tail never false-positives an empty fence as work.
AUDIT_EMPTY_SENTINEL = "no open items"
PRODUCT_EMPTY_SENTINEL = "no product spec yet"

# A paused (interrupted) audit/gap run leaves `PARTIAL` in its fence's status line
# (RETURN-3) — one status-token check, not a new input.
PARTIAL_TOKEN = "PARTIAL"

# The `harness:managed` fence in an ADOPTER's CLAUDE.md (absent in this source repo);
# the version is read from the stamp `claugentic-dev-harness@<semver>` inside it.
MANAGED_FENCE = ("<!-- harness:managed:start -->", "<!-- harness:managed:end -->")
MANAGED_VERSION_RE = re.compile(r"claugentic-dev-harness@(\S+)")


# ─────────────────────────────────────────────────────────────────────────────
# Derived-state record (pure data — no I/O lives on it)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class FenceState:
    """One backlog fence's derived state. `present` is False when the fence/file
    is absent (an adopter who never ran audit/product) — distinct from an EMPTY
    fence (`empty=True`, the "No open items" sentinel) so the recommendation can
    tell "never generated" from "generated, nothing to do"."""

    present: bool = False
    empty: bool = True
    partial: bool = False


@dataclass(frozen=True)
class PlanState:
    """One in-flight plan's derived state. `resumable_from` is the human-readable
    `Resumable from:` line (derived; the unchecked boxes are authoritative); `age`
    is the `git log` relative date (None when git is unavailable, RETURN-2)."""

    name: str
    resumable_from: str | None = None
    age: str | None = None


@dataclass(frozen=True)
class PlansScan:
    """One `.claude/plans/` scan — the reader's whole result, in one record.

    `in_flight` is LISTED (it drives the resume recommendation); `landed` and `cold` are
    COUNTED only. That asymmetry is deliberate: a landed-but-undeleted plan and a plan
    untouched for `COLD_DAYS` are HOUSEKEEPING (a `/doctor` sweep), not a next action —
    naming them would spend the line's budget on work the user didn't ask for.
    """

    in_flight: tuple[PlanState, ...] = ()
    landed: int = 0
    cold: int = 0


@dataclass(frozen=True)
class AdvisorState:
    audit: FenceState = field(default_factory=FenceState)
    product: FenceState = field(default_factory=FenceState)
    plans: tuple[PlanState, ...] = ()
    landed_plans: int = 0  # present but Done — the delete-at-land close-out was skipped
    cold_plans: int = 0  # in-flight but untouched for COLD_DAYS+
    managed_version: str | None = None  # adopter-only; absent in this source repo
    installed_version: str | None = None  # the plugin's own manifest version


# ─────────────────────────────────────────────────────────────────────────────
# Readers — each degrades to an "absent input" default rather than raising, so a
# single malformed input can never blank the whole advisor. The OUTER fail-safe in
# main() is the last line of defence for anything these don't anticipate.
#
# EVERY `read_text(encoding="utf-8")` here catches `(OSError, ValueError)`, not
# `OSError` alone: non-UTF-8 bytes raise `UnicodeDecodeError`, which IS a ValueError
# and is NOT an OSError — the difference between "this one input is absent" and "the
# user lost their whole session banner". Named classes, never `except Exception`.
# ─────────────────────────────────────────────────────────────────────────────
def _fence_body(text: str, markers: tuple[str, str]) -> str | None:
    """The text BETWEEN a fence's start/end markers, or None if either is absent.

    A missing fence (the markers never appear) returns None — the caller reads that
    as "this backlog was never generated", distinct from a present-but-empty fence.
    """
    start, end = markers
    si = text.find(start)
    if si == -1:
        return None
    ei = text.find(end, si + len(start))
    if ei == -1:
        return None
    return text[si + len(start):ei]


def _read_fence(text: str, markers: tuple[str, str], empty_sentinel: str) -> FenceState:
    """Derive a FenceState from the roadmap text for one fence.

    EMPTY iff the body carries the sentinel lead phrase (case-insensitive) or is
    blank; PARTIAL iff the body carries the `PARTIAL` status token. A present fence
    that is neither empty nor pure-whitespace is treated as carrying open items.
    """
    body = _fence_body(text, markers)
    if body is None:
        return FenceState(present=False, empty=True, partial=False)
    low = body.lower()
    empty = (empty_sentinel in low) or (body.strip() == "")
    partial = PARTIAL_TOKEN in body
    return FenceState(present=True, empty=empty, partial=partial)


def _read_roadmap() -> tuple[FenceState, FenceState]:
    """Read both backlog fences from `docs/claugentic-ROADMAP.md`.

    A missing / unreadable / non-UTF-8 roadmap yields two absent fences (FenceState
    defaults) — the natural fresh-repo silent path, not an error.
    """
    if not ROADMAP_PATH.exists():
        return (FenceState(), FenceState())
    try:
        text = ROADMAP_PATH.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return (FenceState(), FenceState())
    audit = _read_fence(text, AUDIT_FENCE, AUDIT_EMPTY_SENTINEL)
    product = _read_fence(text, PRODUCT_FENCE, PRODUCT_EMPTY_SENTINEL)
    return (audit, product)


def _line_value(text: str, label: str) -> str | None:
    """The value after a `- **<label>:**` plan-header line (e.g. `Resumable from`).

    Tolerant of surrounding markdown bold/bullet noise: matches the label then
    captures the rest of that line, trimmed. None when the label is absent.
    """
    pattern = re.compile(
        r"^\s*-?\s*\*{0,2}" + re.escape(label) + r"\*{0,2}\s*:\s*\*{0,2}(.+?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _is_in_flight(text: str) -> bool:
    """A plan is in-flight unless it is unambiguously Done.

    The plan file's PRESENCE in `.claude/plans/` is itself the primary in-flight
    signal (a landed plan is removed from the dir — see the build resume contract),
    so the default is in-flight. The one exclusion: a plan with NO unchecked `- [ ]`
    boxes AND a `Status:` line that reads literally `Done`. The unchecked boxes are
    the AUTHORITATIVE signal (RETURN-1) — any unchecked box keeps it in-flight even
    if someone mislabelled the Status.
    """
    if re.search(r"^\s*- \[ \]", text, re.MULTILINE):
        return True
    status = _line_value(text, "Status")
    if status is None:
        return True
    return status.strip().lower() != "done"


def _plan_git_meta(path: Path) -> tuple[str | None, int | None]:
    """`(relative age, commit epoch)` for one plan file, from ONE `git log -1` call.

    Both facts come from the SAME invocation (`%cr` for the RETURN-2 age parenthetical,
    `%ct` for the COLD comparison) — one git seam, and one subprocess per plan rather
    than two, which matters for a hook that runs on every session start.

    Returns `(None, None)` when git is unavailable, errors, the plan is untracked
    (returncode 0, empty stdout), or the output is malformed — both facts are
    nice-to-haves, never load-bearing (RETURN-2). Degrade, never raise.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cr%x1f%ct", "--", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except (OSError, ValueError):
        return (None, None)
    if result.returncode != 0:
        return (None, None)
    raw = result.stdout.strip()
    if not raw:
        return (None, None)  # untracked plan — git succeeded with nothing to say
    age, _, epoch = raw.partition("\x1f")
    age = age.strip() or None
    epoch = epoch.strip()
    # `.isdecimal()`, not `.isdigit()` — the latter admits characters `int()` rejects,
    # and this conversion sits OUTSIDE the try above (see `_version_lt` for the same
    # guard and why an escape from a reader is never merely a missing field).
    return (age, int(epoch) if epoch.isdecimal() else None)


def _is_cold(epoch: int | None, now: float) -> bool:
    """True iff the plan's last commit is older than `COLD_DAYS` (RETURN-2 posture).

    An UNKNOWN epoch (git absent, untracked plan, malformed output) is NOT cold — the
    nudge must never fire off a missing measurement, and "we couldn't look" is not
    evidence of staleness. A future-dated commit (clock skew) is likewise not cold.
    """
    if epoch is None:
        return False
    return (now - epoch) > COLD_SECONDS


def _read_plans() -> PlansScan:
    """Scan `.claude/plans/*.md` — in-flight plans LISTED, landed/cold plans COUNTED.

    A missing/unreadable plans dir yields an empty scan — the fresh-repo silent path. An
    individual unreadable plan is skipped (degrade, don't crash). Sorted by filename
    so the surfaced order is stable (the numeric prefixes give a sensible sequence).

    A LANDED plan (present, but not in-flight) is the delete-at-land close-out that was
    skipped; a COLD plan is in-flight but untouched for `COLD_DAYS`+. Both are counted
    here — the one place that already reads every plan file — so no second pass, and no
    second definition of "in flight", can drift from `_is_in_flight`.
    """
    if not PLANS_DIR.is_dir():
        return PlansScan()
    try:
        candidates = sorted(PLANS_DIR.glob("*.md"), key=lambda p: p.name)
    except OSError:
        return PlansScan()
    now = time.time()
    plans: list[PlanState] = []
    landed = 0
    cold = 0
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
        if not _is_in_flight(text):
            landed += 1
            continue
        age, epoch = _plan_git_meta(path)
        if _is_cold(epoch, now):
            cold += 1
        plans.append(
            PlanState(
                name=path.name,
                resumable_from=_line_value(text, "Resumable from"),
                age=age,
            )
        )
    return PlansScan(in_flight=tuple(plans), landed=landed, cold=cold)


def _read_installed_version() -> str | None:
    """The INSTALLED plugin's own `.claude-plugin/plugin.json` version, or None.

    Read from `PLUGIN_MANIFEST_PATH` (anchored on `__file__` — see that constant), so
    this reports the version of the plugin the advisor is SHIPPED INSIDE, which is
    exactly what an adopter's stamped docs are compared against.

    Returns None for every failure this read can meet: a missing or unreadable file
    (`OSError`), bytes that aren't UTF-8 (`UnicodeDecodeError`, a `ValueError`), JSON
    that won't parse or nests past the interpreter's recursion limit, a non-object
    document, and a missing / non-string / blank `version`. The skew nudge then simply
    doesn't fire. The exception classes are NAMED, never a blanket `except Exception` —
    but they are named WIDE enough to cover the decode, because an escape from here
    costs the user their whole session banner, not just this nudge.
    """
    try:
        text = PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    try:
        manifest = json.loads(text)
    except (ValueError, TypeError, RecursionError):
        return None
    if not isinstance(manifest, dict):
        return None
    version = manifest.get("version")
    if not isinstance(version, str):
        return None
    return version.strip() or None


def _read_managed_version() -> str | None:
    """The adopter's CLAUDE.md `harness:managed` fence version (ADOPTER-ONLY).

    ABSENT IN THIS SOURCE REPO — this repo's CLAUDE.md has no such fence, so this
    returns None here and the version input is silently skipped (never a dead-branch
    crash). On an adopter repo, reads the `claugentic-dev-harness@<semver>` stamp
    from inside the fence. A missing / unreadable / non-UTF-8 CLAUDE.md → None
    (degrade, don't raise).
    """
    if not CLAUDE_MD_PATH.exists():
        return None
    try:
        text = CLAUDE_MD_PATH.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    body = _fence_body(text, MANAGED_FENCE)
    if body is None:
        return None
    match = MANAGED_VERSION_RE.search(body)
    return match.group(1) if match else None


def derive_state() -> AdvisorState:
    """Assemble the full derived state from every input (each reader degrades)."""
    audit, product = _read_roadmap()
    scan = _read_plans()
    return AdvisorState(
        audit=audit,
        product=product,
        plans=scan.in_flight,
        landed_plans=scan.landed,
        cold_plans=scan.cold,
        managed_version=_read_managed_version(),
        installed_version=_read_installed_version(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation — the single highest-value next step + the in-flight summary.
# Priority order (highest first): in-flight plans -> open audit backlog ->
# paused (PARTIAL) audit/gap -> no product spec yet -> SILENT.
# ─────────────────────────────────────────────────────────────────────────────
def _plan_label(plan: PlanState) -> str:
    """`0022 (2 days ago)` — the stem (drop `.md`) + the relative age when known."""
    stem = plan.name[:-3] if plan.name.endswith(".md") else plan.name
    return f"{stem} ({plan.age})" if plan.age else stem


def _in_flight_summary(plans: tuple[PlanState, ...]) -> str:
    """A compact one-line summary of the in-flight plans (for the recommend line)."""
    labels = ", ".join(_plan_label(p) for p in plans)
    noun = "plan" if len(plans) == 1 else "plans"
    return f"{len(plans)} {noun} in flight: {labels}"


def recommend_next(state: AdvisorState) -> str | None:
    """The ONE recommended next step, priority-ordered, or None when SILENT.

    Priority (your judgment, highest first):
      1. In-flight plans  -> resume them (the most concrete pending commitment;
         the plan files are the state-of-record). Surface ALL of them + the lead
         plan's `Resumable from:` line.
      2. Open audit backlog (a present, non-empty `harness-audit:backlog` fence)
         -> run `/build` to work the engineering items.
      3. A PARTIAL audit/gap fence (an interrupted run) -> re-run to finish (RETURN-3).
      4. No product spec yet (the product fence still carries its "No product spec
         yet" sentinel) -> run `/product` to define one.
      5. Nothing actionable -> None (SILENT, no-nag).
    """
    plans = state.plans
    if plans:
        summary = _in_flight_summary(plans)
        lead = plans[0]
        if lead.resumable_from:
            return f"Resume work in progress — {summary}. Lead: {lead.resumable_from}"
        return f"Resume work in progress — {summary}."

    if state.audit.present and not state.audit.empty:
        return f"Open engineering backlog — run {BUILD_CMD} to work it."

    if state.audit.partial or state.product.partial:
        return (
            "Your last audit/gap run was partial — re-run it to finish "
            f"(then {BUILD_CMD})."
        )

    # The product fence's empty body IS the "no product spec yet" signal (the
    # sentinel `_read_fence` collapses into `empty=True`): a present+empty product
    # fence means a spec was never defined.
    if state.product.present and state.product.empty:
        return f"No product spec yet — run {PRODUCT_CMD} (spec mode) to define one."

    return None


# ─────────────────────────────────────────────────────────────────────────────
# CURRENCY CLAUSES — "is this repo still current?" Independent of `recommend_next`'s
# priority ladder (they answer a different question, so they never compete for the ONE
# recommendation slot); each is appended to the USER-facing line only.
# ─────────────────────────────────────────────────────────────────────────────
def _version_lt(a: str, b: str) -> bool | None:
    """`a < b` as dot-separated NUMERIC tuples, or None when either side isn't one.

    Tolerant by construction and DELIBERATELY narrow: only all-decimal segments compare
    (`0.4.1` < `0.5.1`). Anything else — a pre-release/build suffix (`0.5.1-rc.1`), a
    `v` prefix, an empty string — yields None, meaning "cannot compare", and the caller
    SKIPS the nudge. Guessing an ordering for a form this function doesn't model would
    be worse than staying silent: a false "your docs are stale" costs trust.

    TOTAL BY CONSTRUCTION — it must NEVER raise. The left-hand value is arbitrary user
    text (`MANAGED_VERSION_RE` captures `\\S+` from a hand-editable CLAUDE.md fence), and
    an escape here does not merely skip the nudge: it blanks the WHOLE banner, resume
    line included, via `main()`'s outer fail-safe. The `try` is the LOAD-BEARING guard —
    only it catches a >4300-digit segment, a perfectly legal decimal string that still
    raises under CPython's int-conversion limit. `.isdecimal()` (NOT `.isdigit()`, which
    is True for `'²'` — a character `int()` rejects) is the cheap fast path and states
    the intended domain; it is behaviourally SUBSUMED by the `try`, so swapping it back
    to `.isdigit()` is a provably equivalent mutant. Do not "simplify" by dropping the
    `try`: that one is killable, and the suite kills it.

    Unequal lengths compare naturally (`0.4` < `0.4.1`, `0.5` > `0.4.1`) — Python's
    tuple ordering is exactly the shortest-is-lower semantics wanted here.
    """
    parsed = []
    for value in (a, b):
        segments = value.split(".")
        if not all(segment.isdecimal() for segment in segments):
            return None
        try:
            parsed.append(tuple(int(segment) for segment in segments))
        except ValueError:
            return None
    return parsed[0] < parsed[1]


def _skew_clause(state: AdvisorState) -> str | None:
    """The "stamped docs are behind the installed plugin — re-run init" clause, or None.

    Fires ONLY when BOTH versions were read AND both parse AND managed < installed.
    Every other case is silent: absent stamp (this SOURCE repo, or a repo that never ran
    init), unreadable manifest, unparseable version, equal versions, or managed AHEAD of
    installed (a dev checkout — the user is not behind, so there is nothing to say).
    """
    managed, installed = state.managed_version, state.installed_version
    if managed is None or installed is None:
        return None
    if _version_lt(managed, installed) is not True:
        return None
    return f"Harness docs stamped {managed} < plugin {installed} — re-run {INIT_CMD}."


def _housekeeping_clause(state: AdvisorState) -> str | None:
    """The "N landed/cold plans — run doctor to sweep" clause, or None when tidy.

    ONE combined count, never a list: naming the files would spend the line's budget on
    work the user didn't ask for, and `/doctor`'s plan-scan is the surface that already
    enumerates and treats them (this is a pointer at it, not a second implementation).
    """
    total = state.landed_plans + state.cold_plans
    if total <= 0:
        return None
    noun = "plan" if total == 1 else "plans"
    return f"{total} landed/cold {noun} in .claude/plans — run {DOCTOR_CMD} to sweep."


def _currency_clauses(state: AdvisorState) -> tuple[str, ...]:
    """The currency clauses that fired, in emit order (skew first — it is the one that
    invalidates the docs the session is about to read). Empty tuple when neither fires."""
    return tuple(c for c in (_skew_clause(state), _housekeeping_clause(state)) if c)


# ─────────────────────────────────────────────────────────────────────────────
# Output contract — render the recommendation to the SessionStart JSON.
# ─────────────────────────────────────────────────────────────────────────────
def _cap(line: str, limit: int = MAX_LINE_CHARS) -> str:
    """Hard-cap one line to `limit` chars, default `MAX_LINE_CHARS` (ellipsis on overflow).

    The advisor's own output is size-budgeted — this is the deterministic ceiling
    the tests assert. The ellipsis keeps an over-long derived line honest (truncated,
    not silently dropped) while never exceeding the cap. `limit` exists for
    `_compose_user_line`'s reserve; callers with no budget to share omit it.
    """
    line = " ".join(line.split())  # collapse any stray newlines/runs to one tight line
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip() + "…"


def _compose_user_line(recommendation: str | None, clauses: tuple[str, ...]) -> str:
    """The ONE user-facing line: recommendation + currency clauses, within the ceiling.

    RESERVE, don't compose-then-cap. Composing first and capping the whole line makes
    the clauses the FIRST casualty of overflow — and because cold plans ARE in-flight
    plans, that loses the "run doctor to sweep" nudge precisely in the cluttered repo
    that most needs it (measured pre-fix: gone at 4 in-flight plans, both gone at 8).
    So the clause tail is reserved and the RECOMMENDATION absorbs the truncation: the
    ellipsis lands in the plan list, and the clause that survives is the one telling
    the user to sweep the plans that caused the overflow.

    THREE properties this must keep, in priority order:
      1. The ceiling ALWAYS wins — the result is never longer than `MAX_LINE_CHARS`.
      2. With no clause firing the result is byte-identical to a bare `_cap`.
      3. `additionalContext` never passes through here (see `build_output`) — it is
         built from `recommendation` alone, so the agent-facing string is unaffected
         by anything on this side of the split.

    FLOOR GUARD: a pathological clause tail (longer than the budget minus
    `MIN_HEAD_CHARS`) would reserve the head down to an ellipsis or worse — a negative
    slice. In that case the reserve is abandoned and the whole composed line is capped
    normally: property 1 holds unconditionally, which is the one that must.
    """
    tail = CLAUSE_SEP.join(clauses)
    if recommendation is None:
        return _cap(tail)
    if not tail:
        return _cap(recommendation)
    head_limit = MAX_LINE_CHARS - len(tail) - len(CLAUSE_SEP)
    if head_limit < MIN_HEAD_CHARS:
        return _cap(recommendation + CLAUSE_SEP + tail)
    return _cap(recommendation, head_limit) + CLAUSE_SEP + tail


def build_output(state: AdvisorState, *, enabled: bool = True) -> dict[str, str]:
    """The SessionStart JSON payload (a plain dict). PURE — no I/O, no env reads.

    OFF-SWITCH (dependency-inversion): when `enabled` is False the advisor is fully
    muted -> `{}` (NEITHER key). `main()` is the env boundary that derives `enabled`
    from `CLAUDE_HARNESS_ADVISOR`; the renderer stays pure (it never reads the
    environment), so this stays trivially testable and fail-safe-to-silent. Default
    True keeps existing behaviour unchanged when the env var is unset.

    SILENT path: nothing actionable AND no currency clause -> `{}` (NEITHER key).

    COMPOSITION: the ONE recommendation and the currency clauses become a SINGLE
    user-facing line via `_compose_user_line`, which RESERVES the clause budget so an
    overflow truncates the recommendation, never a nudge (see that helper for why the
    order matters). A clause can stand alone: when nothing else fires, the clauses ARE
    the message.

    AUDIENCE-SPLIT (0024 problem #5 — anti-nudge). `systemMessage` is the user-facing
    orientation line and is emitted on EVERY actionable path so the USER stays
    oriented. `additionalContext` (the AGENT-facing line, with the RETURN-6
    `ADVISORY_PREFIX` disclaimer) is emitted ONLY for the in-flight-plan RESUME
    recommendation — `recommend_next` priority 1, which fires iff `state.plans` is
    truthy, the genuine next-action the agent should see when resuming committed work.
    The three PROMOTIONAL nudges (priority 2 open-backlog / 3 PARTIAL-rerun / 4
    no-product-spec) push "work the user didn't ask for", so they go systemMessage-ONLY
    — the user stays oriented, the agent is NOT nudged. The two CURRENCY clauses are
    systemMessage-ONLY on the same rule: `additionalContext` is built from
    `recommendation` ALONE and never passes through `_compose_user_line`, so widening
    the clauses into the agent's context is a code change, not a formatting accident —
    and the clause-budget reserve cannot perturb the agent-facing string. This does NOT
    regress RETURN-6: the `ADVISORY_PREFIX` disclaimer is preserved wherever
    `additionalContext` IS emitted (the resume branch).
    """
    if not enabled:
        return {}
    recommendation = recommend_next(state)
    clauses = _currency_clauses(state)
    if recommendation is None and not clauses:
        return {}
    output = {"systemMessage": _compose_user_line(recommendation, clauses)}
    # Mirror priority-1 of recommend_next: resume == in-flight plans present. Only the
    # agent-facing context for that genuine next-action carries the disclaimer prefix —
    # and it carries the RECOMMENDATION only (see AUDIENCE-SPLIT above).
    agent_relevant = recommendation is not None and bool(state.plans)
    if agent_relevant:
        output["additionalContext"] = _cap(ADVISORY_PREFIX + recommendation)
    return output


def main(argv: list[str]) -> int:
    """Always exit 0; emit the JSON payload on stdout. FAIL-SAFE outer boundary.

    ENV BOUNDARY: this is where the off-switch is read (keeping `build_output` pure).
    `CLAUDE_HARNESS_ADVISOR=off` (case-insensitive, trimmed) mutes the advisor ->
    `{}`; any other value (or unset) leaves it enabled (no behaviour change).

    ANY error anywhere in derive/recommend/render collapses here to exit 0 with no
    output (a SessionStart hook must never block or slow a session). The silent path
    prints `{}` (valid JSON, no keys — costs the agent nothing).
    """
    enabled = os.environ.get("CLAUDE_HARNESS_ADVISOR", "").strip().lower() != "off"
    try:
        payload = build_output(derive_state(), enabled=enabled)
    except Exception:  # noqa: BLE001 — fail-safe: a SessionStart hook must never crash a session
        return 0
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
