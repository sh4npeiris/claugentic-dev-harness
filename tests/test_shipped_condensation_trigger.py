"""Regression scan: no SHIPPED copy still tells an adopter the doc-budget WARN is
unreachable in their repo (plan 0041 Slice 6 — the INVERSION of the 0038 Slice 1 guard).

What this file used to pin, and why it flipped. Until 0041 S6, `scripts/check_doc_budgets.py`
— the ONLY thing that emits a doc-budget WARN — was in `build_release.py`'s dev-only strip
set, so an adopter's repo could NEVER produce that WARN and any shipped "condense when the
WARN fires" instruction was an ORPHANED trigger. Slice 6 SHIPS the gate (its caps became
per-repo data in Slice 4, so it is adopter-portable: absent config = quiet exit-0 no-op).
The old premise is dead, and the failure mode reverses: the risk is no longer copy that
points at an unreachable trigger, it is **stale copy that DENIES a trigger the reader now
has** — "that gate is stripped", "no WARN can fire", "N-A in an adopter". That copy tells a
reader with a caps config not to expect a signal their repo really does emit.

Two scans, both over the SHIPPED text:

  * **Unreachability claims** — a sentence in doc-budget context asserting the WARN cannot
    fire / cannot be produced / the gate is stripped. Narrow BY DESIGN (the predecessor's
    discipline): it keys on the specific phrasings the harness's own copy used, not on any
    mention of "stripped". Honest scope — it catches the known stale phrasings and their close
    variants, NOT every possible way to write the same falsehood; novel wording stays
    model-upheld, exactly as the orphaned-trigger pattern before it.
  * **Ship-class denials** — a shipped line that names `check_doc_budgets.py` AND carries an
    adopter-caveat marker. This one is fully mechanical and reuses the scanner's own marker
    vocabulary (`check_shipped_content.CAVEAT_MARKERS`) rather than a second copy of it, so
    the two stay in step: the same markers that CLEAR a Pass A.b warning for a stripped gate
    are the ones that are now FALSE about this shipped one. Mirror-image passes over one
    vocabulary.

SHIP source-of-truth: this test imports `build_release` and reuses its ONE ship classifier
(`br.classify(br._tracked_files())[0]`) — the same single source `check_shipped_content.py`
uses — so "the shipped set" here is never a second, hand-maintained list (DRY). Being a
harness-self test (in `tests/`, itself stripped from the release) it legitimately reads the
release tooling; it never runs in an adopter repo.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import build_release as br  # the SINGLE ship classifier — see check_shipped_content.py
import check_shipped_content as csc  # reuse its shipped-text reader + caveat vocabulary

# The gate whose ship-class this file's whole premise rests on.
GATE_PATH = "scripts/check_doc_budgets.py"
GATE_NAME = Path(GATE_PATH).name

# Scope guard: only lines that are ABOUT doc budgets are candidates for an unreachability
# claim. Without it, "the gate is stripped" would fire on legitimate copy about version-sync
# or the shipped-content scanner, which genuinely ARE stripped.
DOC_BUDGET_CONTEXT_RE = re.compile(r"doc[- ]budget|check_doc_budgets", re.IGNORECASE)

# The stale-premise phrasings: an assertion that the reading repo cannot get this WARN.
# Deliberately narrow (see the module docstring's honest-scope note) — these are the exact
# constructions the harness's own shipped copy carried before the reclass, plus their obvious
# variants, NOT a general "is this sentence false?" detector.
UNREACHABILITY_RE = re.compile(
    r"no\s+(?:doc-budget\s+)?WARN\s+can\s+fire"
    r"|(?:never|cannot|can't|can\s+not)\s+produce\s+(?:that|the|a|its)\s+(?:doc-budget\s+)?WARN"
    r"|(?:that|the|this)\s+gate\s+is\s+stripped",
    re.IGNORECASE,
)

# The adopter-caveat markers that are now FALSE about this gate — derived from the scanner's
# own vocabulary so a marker added there is covered here automatically (one vocabulary, two
# mirror-image passes). `harness-self` is the ONE exclusion, and it is not a loophole: the
# WORKFLOW adopter note names BOTH gates in a single sentence, so "harness-self" legitimately
# qualifies its version-sync clause on a line that also mentions this gate. A stale
# "doc-budgets is harness-self" claim on such a shared line is therefore a documented
# false-negative of this scan — model-upheld, like the predecessor's own heuristic edges.
SHIP_CLASS_DENIALS = tuple(m for m in csc.CAVEAT_MARKERS if m != "harness-self")


def find_unreachability_claims(texts: dict[str, str]) -> list[str]:
    """Pure core: `path:lineno: <line>` for every doc-budget WARN-unreachability claim.

    Takes an injected `{path: text}` map so the patterns are hermetically testable without
    git or the filesystem (mirrors `check_shipped_content.py`'s pure cores).
    """
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if DOC_BUDGET_CONTEXT_RE.search(line) and UNREACHABILITY_RE.search(line):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def find_ship_class_denials(texts: dict[str, str]) -> list[str]:
    """Pure core: `path:lineno: <line>` for every shipped line that caveats THIS gate away."""
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if GATE_NAME not in line:
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in SHIP_CLASS_DENIALS):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def _repo_root() -> Path:
    """Repo root = the parent of this test's `tests/` dir (the harness convention)."""
    return Path(__file__).resolve().parent.parent


def _shipped_texts() -> dict[str, str]:
    """Every SHIPPED TEXT file's content, keyed by repo-relative path.

    Reuses the ONE ship classifier (`br.classify`) AND the scanner's `_read_shipped_texts` — the
    single source of the "skip known-binary shipped assets (e.g. `docs/diagrams/*.png`), fail-loud
    on text corruption" contract — so this scan reads exactly the text files the gate scans."""
    root = _repo_root()
    ship = list(br.classify(br._tracked_files())[0])
    return csc._read_shipped_texts(root, ship)


class TestThePremise:
    """This whole file is only correct while the gate SHIPS. Assert that, so a future
    re-strip fails HERE with an explanation instead of leaving two silently-vacuous scans."""

    def test_the_doc_budget_gate_ships(self):
        assert br.is_dev_only(GATE_PATH) is False, (
            f"{GATE_PATH} is stripped again — this file's premise (an adopter HAS the gate, "
            "so copy denying its WARN is stale) no longer holds. Restore the orphaned-trigger "
            "guard this file replaced (git history, plan 0038 Slice 1) rather than deleting "
            "the scan: with the gate stripped, the old failure mode returns."
        )

    def test_the_marker_vocabulary_is_reused_not_recopied(self):
        # The denial vocabulary is DERIVED from the scanner's markers, minus exactly one
        # documented exclusion — so a marker added there is covered here with no edit.
        assert set(SHIP_CLASS_DENIALS) == set(csc.CAVEAT_MARKERS) - {"harness-self"}
        assert SHIP_CLASS_DENIALS, "the derivation emptied the vocabulary — the scan is vacuous"


class TestStalePremisePatterns:
    """Pin both patterns in both directions so neither can rot into matching nothing
    (or into over-matching honest copy about the gates that genuinely ARE stripped)."""

    def test_no_warn_can_fire_is_caught(self):
        texts = {"docs/x.md": "in an adopter's repo the doc-budget gate is absent, so no WARN can fire"}
        assert len(find_unreachability_claims(texts)) == 1

    def test_can_never_produce_the_warn_is_caught(self):
        texts = {"docs/y.md": "an adopter's repo can never produce that doc-budget WARN"}
        assert len(find_unreachability_claims(texts)) == 1

    def test_that_gate_is_stripped_is_caught(self):
        texts = {"docs/z.md": "condense on a doc-budget WARN -- but that gate is stripped for you"}
        assert len(find_unreachability_claims(texts)) == 1

    def test_a_stripped_sibling_gate_is_not_flagged(self):
        # version-sync really IS stripped; saying so must stay legal. The doc-budget context
        # guard is what keeps this scan off it.
        texts = {"docs/w.md": "version-sync is harness-self and that gate is stripped from the release"}
        assert find_unreachability_claims(texts) == []

    def test_the_landed_two_trigger_framing_is_clean(self):
        # The honest post-reclass framing: the WARN is reachable wherever a config opts in.
        texts = {
            "docs/v.md": (
                "a >=90% doc-budget WARN from the gate is the do-it-now signal wherever a caps "
                "config opts in; /doctor's advisory and your own periodic review are the others."
            )
        }
        assert find_unreachability_claims(texts) == []
        assert find_ship_class_denials(texts) == []

    def test_a_caveated_mention_of_this_gate_is_caught(self):
        texts = {"docs/u.md": "run `python scripts/check_doc_budgets.py` (N-A in an adopter)"}
        assert len(find_ship_class_denials(texts)) == 1

    def test_an_uncaveated_mention_of_this_gate_is_clean(self):
        texts = {"docs/t.md": "run `python scripts/check_doc_budgets.py` at Verify and in CI"}
        assert find_ship_class_denials(texts) == []

    def test_a_caveat_on_a_sibling_gate_does_not_implicate_this_one(self):
        # The scan is LINE-scoped: a nearby honest caveat about a stripped gate is not a
        # denial of this one.
        texts = {
            "docs/s.md": (
                "`scripts/check_versions_synced.py` is stripped from the release.\n"
                "`scripts/check_doc_budgets.py` ships and no-ops without a caps config.\n"
            )
        }
        assert find_ship_class_denials(texts) == []


class TestShippedSetMakesNoStaleClaim:
    @pytest.fixture(autouse=True)
    def at_repo_root(self, monkeypatch):
        """`br._tracked_files()` shells `git ls-files`, which is scoped to the process CWD —
        run from `tests/` it lists only that subtree (relative to it) and `_shipped_texts()`
        raises `FileNotFoundError`. Anchor at the git-authoritative repo root so this scan
        holds from any working directory."""
        monkeypatch.chdir(br._repo_root())

    def test_no_shipped_file_says_the_doc_budget_warn_is_unreachable(self):
        hits = find_unreachability_claims(_shipped_texts())
        assert hits == [], (
            "A SHIPPED file tells the reading repo that the doc-budget WARN cannot fire there "
            "— but the gate SHIPS as of plan 0041 Slice 6, so any repo with a "
            "`.claude/claugentic-doc-budgets.json` really does emit it. Re-word to the "
            "opt-in framing (the WARN fires wherever a caps config opts in; an absent config "
            "is a quiet no-op). Offending lines:\n  " + "\n  ".join(hits)
        )

    def test_no_shipped_file_caveats_this_gate_away_from_adopters(self):
        hits = find_ship_class_denials(_shipped_texts())
        assert hits == [], (
            f"A SHIPPED file mentions `{GATE_NAME}` with an adopter-caveat marker "
            f"({', '.join(SHIP_CLASS_DENIALS)}) — all of which are now FALSE about it: the "
            "gate ships. Drop the caveat, or say what is actually true (it no-ops without a "
            "caps config). Offending lines:\n  " + "\n  ".join(hits)
        )
