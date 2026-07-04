"""Regression scan: no SHIPPED copy points an adopter at the unproducible "doc-budget
WARN" condensation trigger (plan 0038 Slice 1).

Why this exists: `scripts/check_doc_budgets.py` — the ONLY thing that emits a doc-budget
WARN — is in `build_release.py`'s DEV-ONLY strip set, so an ADOPTER's repo never receives
that gate and can NEVER produce the WARN. Any shipped copy that tells the reading repo to
"condense when the doc-budget WARN fires" is therefore an ORPHANED trigger for an adopter
(the release-strips ⇒ nothing-dangles invariant, extended from *paths* to *triggers*). This
test pins that fix so a future edit can't silently re-orphan the trigger.

SHIP source-of-truth: this test imports `build_release` and reuses its ONE ship classifier
(`br.classify(br._tracked_files())[0]`) — the same single source `check_shipped_content.py`
uses — so "the shipped set" here is never a second, hand-maintained list (DRY). Being a
harness-self test (in `tests/`, itself stripped from the release) it legitimately reads the
release tooling; it never runs in an adopter repo.

Robustness (match the ORPHANED trigger, not incidental "WARN" mentions): the pattern matches
only the bare adopter-trigger phrasing — an instruction to act "*when the (doc-budget) WARN
fires*" — NOT a mention that names the WARN as the *harness-self* signal alongside an
adopter-reachable one (`/doctor`'s advisory / periodic review). The `test_pattern_*` cases pin
both directions: the original orphaned seed phrasing is caught; the fixed two-trigger framing
is clean.
"""

from __future__ import annotations

import re
from pathlib import Path

import build_release as br  # the SINGLE ship classifier — see check_shipped_content.py

# The orphaned-trigger phrasing: an instruction to condense/act *when the WARN fires* — the
# exact adopter-unreachable cue. Deliberately narrow: it keys on the imperative "…WARN fires"
# (optionally "doc-budget WARN"), NOT on any bare "WARN" token, so the legitimate two-trigger
# framing ("a ≥90% doc-budget WARN is the harness-self signal; the adopter trigger is
# /doctor's advisory") does NOT match. `\bfires\b` (present-tense trigger verb) is the
# discriminator — "no WARN can fire" / "re-fires the WARN" are different constructions.
ORPHANED_TRIGGER_RE = re.compile(
    r"(?:doc-budget\s+)?WARN\s+fires\b",
    re.IGNORECASE,
)


def find_orphaned_triggers(texts: dict[str, str]) -> list[str]:
    """Pure core: return `path:lineno: <line>` for every orphaned-trigger match.

    Takes an injected `{path: text}` map so the pattern is hermetically testable without
    git or the filesystem (mirrors `check_shipped_content.py`'s pure cores).
    """
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if ORPHANED_TRIGGER_RE.search(line):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def _repo_root() -> Path:
    """Repo root = the parent of this test's `tests/` dir (the harness convention)."""
    return Path(__file__).resolve().parent.parent


def _shipped_texts() -> dict[str, str]:
    """Every SHIPPED file's text, keyed by repo-relative path (reuses the one ship classifier)."""
    root = _repo_root()
    ship = br.classify(br._tracked_files())[0]
    return {rel: (root / rel).read_text(encoding="utf-8") for rel in ship}


class TestOrphanedTriggerPattern:
    """Pin the pattern in both directions so it can't silently rot into matching nothing
    (or into over-matching the legitimate harness-self framing)."""

    def test_original_seed_phrasing_is_caught(self):
        # The exact phrasing plan 0038 Slice 1 removed from `_DECISIONS.md:3`.
        texts = {"docs/x.md": "condense it periodically when the doc-budget WARN fires: merge…"}
        assert find_orphaned_triggers(texts) == ["docs/x.md:1: condense it periodically when the doc-budget WARN fires: merge…"]

    def test_bare_when_the_warn_fires_is_caught(self):
        texts = {"docs/y.md": "run a compaction pass when the WARN fires rather than letting it grow"}
        assert len(find_orphaned_triggers(texts)) == 1

    def test_two_trigger_framing_is_clean(self):
        # The FIXED framing: names the harness-self WARN AND the adopter-reachable trigger.
        texts = {
            "docs/z.md": (
                "in the harness's own repo a >=90% doc-budget WARN is the do-it-now signal; "
                "in an adopter's repo -- where that gate is stripped, so no WARN can fire -- "
                "the reachable trigger is /doctor's budget advisory or your own periodic review."
            )
        }
        assert find_orphaned_triggers(texts) == []

    def test_refires_the_warn_is_clean(self):
        # "re-fires the WARN on the next append" is a re-check-band mechanic, not an adopter trigger.
        texts = {"docs/w.md": "a pass that lands at 89.9% re-fires the WARN on the next append"}
        assert find_orphaned_triggers(texts) == []


class TestShippedSetHasNoOrphanedTrigger:
    def test_no_shipped_file_points_an_adopter_at_the_doc_budget_warn_trigger(self):
        hits = find_orphaned_triggers(_shipped_texts())
        assert hits == [], (
            "A SHIPPED file tells the reading repo to condense 'when the doc-budget WARN "
            "fires' — but that gate (scripts/check_doc_budgets.py) is stripped from the "
            "release, so an adopter's repo can NEVER produce that WARN. Re-word it to an "
            "adopter-reachable trigger (/doctor's budget advisory, or periodic review). "
            "Offending lines:\n  " + "\n  ".join(hits)
        )
