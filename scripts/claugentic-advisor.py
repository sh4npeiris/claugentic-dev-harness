#!/usr/bin/env python3
"""SessionStart advisor — derive ONE plain-English "where am I / what's next" line.

The harness already DERIVES resumable state (the two backlog fences in
`docs/claugentic-ROADMAP.md`, the in-flight `.claude/plans/*.md`, and — for an
ADOPTER repo only — the CLAUDE.md `harness:managed` fence version) but never
VOLUNTEERS it. This script renders that scattered state as a single recommended
next step + a short in-flight summary, emitted once per session via a bundled
`SessionStart` hook.

HONESTY REGISTER — this is an ADVISOR, not a gate. It reports what the fences SAY
and asserts nothing new; it never blocks, never passes/fails, and never appears in
the Definition-of-Done gate list. The `additionalContext` it injects is prefixed
"Derived suggestion (confirm before acting):" so a SessionStart injection can never
silently auto-drive a resume past `build`'s deliberate re-confirm gate (RETURN-6).

AUDIENCE-SPLIT (anti-nudge, 0024 problem #5) — `additionalContext` (the AGENT-facing
line) is injected ONLY for the in-flight-plan RESUME recommendation (a genuine
next-action for committed work). The promotional nudges (open-backlog / PARTIAL-rerun
/ no-product-spec — "work the user didn't ask for") are `systemMessage`-ONLY: the USER
stays oriented, the AGENT is not nudged. RETURN-6 is intact — the disclaimer prefix is
preserved wherever `additionalContext` IS emitted.

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
  * OPTIONALLY each in-flight plan's age via `git log -1 --format=%cr` (omitted
    silently when git is unavailable; RETURN-2),
  * OPTIONALLY the CLAUDE.md `harness:managed` fence version — ADOPTER-ONLY; this
    SOURCE repo has no such fence, so it is gracefully absent here (never a crash).

OUTPUT CONTRACT (SessionStart):
  * exit 0 ALWAYS; emit JSON on stdout — `{ systemMessage }` for a nudge, both
    `{ systemMessage, additionalContext }` for the resume branch (see AUDIENCE-SPLIT).
  * SILENT path — nothing actionable (fresh repo / no fences / no plans), OR the
    off-switch — emits NEITHER key (an empty-but-present key still costs tokens; the
    no-nag posture means literally no surface). Both print `{}`.
  * SIZE-CAPPED — each of `systemMessage` / `additionalContext` is one tight line,
    capped at `MAX_LINE_CHARS` (this slice exists to fix context bloat; the
    advisor's own output is budgeted like any managed surface).

FAIL-SAFE — ANY error (missing files, parse failure, non-repo, missing plans dir)
collapses to exit 0 with no output. A SessionStart hook must NEVER block or slow a
session (the same fail-soft posture as the pre-commit tree gate, whose wrapper lets a
git failure pass rather than abort). The fail-safe is the OUTER boundary in `main()`;
internal readers already degrade to "absent input" rather than raising, so a single
bad input never blanks the rest.

Modes:
    python scripts/claugentic-advisor.py    # the hook command AND the manual smoke run
                                             # (its only consumers are the D2 smoke
                                             # check + the tests — not a user feature)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONSTANTS — repo-root-relative (the hook runs from the project dir, like the
# tree gate). Monkeypatched in tests for hermetic tmp_path fixtures.
# ─────────────────────────────────────────────────────────────────────────────
ROADMAP_PATH = Path("docs/claugentic-ROADMAP.md")
PLANS_DIR = Path(".claude/plans")
CLAUDE_MD_PATH = Path("CLAUDE.md")

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT BUDGET — the HARD ceiling for each emitted line (one tight line each).
# ─────────────────────────────────────────────────────────────────────────────
MAX_LINE_CHARS = 320

# The advisory prefix on `additionalContext` (RETURN-6): a SessionStart injection
# must never read as an instruction the agent silently acts on. Single source of
# the wording so the contract can't drift between message and test.
ADVISORY_PREFIX = "Derived suggestion (confirm before acting): "

# The skill slugs surfaced in recommendations (namespaced — the user types these).
PRODUCT_CMD = "/claugentic-dev-harness:product"
BUILD_CMD = "/claugentic-dev-harness:build"

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
class AdvisorState:
    audit: FenceState = field(default_factory=FenceState)
    product: FenceState = field(default_factory=FenceState)
    plans: tuple[PlanState, ...] = ()
    managed_version: str | None = None  # adopter-only; absent in this source repo


# ─────────────────────────────────────────────────────────────────────────────
# Readers — each degrades to an "absent input" default rather than raising, so a
# single malformed input can never blank the whole advisor. The OUTER fail-safe in
# main() is the last line of defence for anything these don't anticipate.
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

    A missing/unreadable roadmap yields two absent fences (FenceState defaults) —
    the natural fresh-repo silent path, not an error.
    """
    if not ROADMAP_PATH.exists():
        return (FenceState(), FenceState())
    try:
        text = ROADMAP_PATH.read_text(encoding="utf-8")
    except OSError:
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


def _plan_age(path: Path) -> str | None:
    """The plan file's last-commit relative date via git (RETURN-2), or None.

    Omitted silently when git is unavailable, errors, the file is untracked, or any
    other failure — age is a nice-to-have, never load-bearing. `%cr` gives a relative
    date like "2 days ago". An untracked plan (returncode 0, empty stdout) yields None.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cr", "--", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except (OSError, ValueError):
        return None
    if result.returncode != 0:
        return None
    age = result.stdout.strip()
    return age or None


def _read_plans() -> tuple[PlanState, ...]:
    """Derive the in-flight plans from `.claude/plans/*.md`.

    A missing/unreadable plans dir yields () — the fresh-repo silent path. An
    individual unreadable plan is skipped (degrade, don't crash). Sorted by filename
    so the surfaced order is stable (the numeric prefixes give a sensible sequence).
    """
    if not PLANS_DIR.is_dir():
        return ()
    plans: list[PlanState] = []
    try:
        candidates = sorted(PLANS_DIR.glob("*.md"), key=lambda p: p.name)
    except OSError:
        return ()
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not _is_in_flight(text):
            continue
        plans.append(
            PlanState(
                name=path.name,
                resumable_from=_line_value(text, "Resumable from"),
                age=_plan_age(path),
            )
        )
    return tuple(plans)


def _read_managed_version() -> str | None:
    """The adopter's CLAUDE.md `harness:managed` fence version (ADOPTER-ONLY).

    ABSENT IN THIS SOURCE REPO — this repo's CLAUDE.md has no such fence, so this
    returns None here and the version input is silently skipped (never a dead-branch
    crash). On an adopter repo, reads the `claugentic-dev-harness@<semver>` stamp
    from inside the fence. Any read failure → None (degrade, don't raise).
    """
    if not CLAUDE_MD_PATH.exists():
        return None
    try:
        text = CLAUDE_MD_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    body = _fence_body(text, MANAGED_FENCE)
    if body is None:
        return None
    match = MANAGED_VERSION_RE.search(body)
    return match.group(1) if match else None


def derive_state() -> AdvisorState:
    """Assemble the full derived state from every input (each reader degrades)."""
    audit, product = _read_roadmap()
    return AdvisorState(
        audit=audit,
        product=product,
        plans=_read_plans(),
        managed_version=_read_managed_version(),
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
# Output contract — render the recommendation to the SessionStart JSON.
# ─────────────────────────────────────────────────────────────────────────────
def _cap(line: str) -> str:
    """Hard-cap one line to `MAX_LINE_CHARS` (ellipsis on overflow).

    The advisor's own output is size-budgeted — this is the deterministic ceiling
    the tests assert. The ellipsis keeps an over-long derived line honest (truncated,
    not silently dropped) while never exceeding the cap.
    """
    line = " ".join(line.split())  # collapse any stray newlines/runs to one tight line
    if len(line) <= MAX_LINE_CHARS:
        return line
    return line[: MAX_LINE_CHARS - 1].rstrip() + "…"


def build_output(state: AdvisorState, *, enabled: bool = True) -> dict[str, str]:
    """The SessionStart JSON payload (a plain dict). PURE — no I/O, no env reads.

    OFF-SWITCH (dependency-inversion): when `enabled` is False the advisor is fully
    muted -> `{}` (NEITHER key). `main()` is the env boundary that derives `enabled`
    from `CLAUDE_HARNESS_ADVISOR`; the renderer stays pure (it never reads the
    environment), so this stays trivially testable and fail-safe-to-silent. Default
    True keeps existing behaviour unchanged when the env var is unset.

    SILENT path: nothing actionable -> `{}` (NEITHER key).

    AUDIENCE-SPLIT (0024 problem #5 — anti-nudge). `systemMessage` is the user-facing
    orientation line and is emitted on EVERY actionable path so the USER stays
    oriented. `additionalContext` (the AGENT-facing line, with the RETURN-6
    `ADVISORY_PREFIX` disclaimer) is emitted ONLY for the in-flight-plan RESUME
    recommendation — `recommend_next` priority 1, which fires iff `state.plans` is
    truthy, the genuine next-action the agent should see when resuming committed work.
    The three PROMOTIONAL nudges (priority 2 open-backlog / 3 PARTIAL-rerun / 4
    no-product-spec) push "work the user didn't ask for", so they go systemMessage-ONLY
    — the user stays oriented, the agent is NOT nudged. This does NOT regress RETURN-6:
    the `ADVISORY_PREFIX` disclaimer is preserved wherever `additionalContext` IS
    emitted (the resume branch).
    """
    if not enabled:
        return {}
    recommendation = recommend_next(state)
    if recommendation is None:
        return {}
    output = {"systemMessage": _cap(recommendation)}
    # Mirror priority-1 of recommend_next: resume == in-flight plans present. Only the
    # agent-facing context for that genuine next-action carries the disclaimer prefix.
    agent_relevant = bool(state.plans)
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
