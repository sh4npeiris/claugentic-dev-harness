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

Two scans, both over the SHIPPED text, both line-scoped, both skipping lines that state the
ship-class change as HISTORY (see `HISTORICAL_RE`):

  * **Unreachability claims** — a sentence in doc-budget context asserting the WARN cannot
    fire / cannot be produced / the gate is stripped.
  * **Ship-class denials** — a shipped line that names `check_doc_budgets.py` AND carries an
    adopter-caveat marker. Fully mechanical, and it reuses the scanner's own marker vocabulary
    (`check_shipped_content.CAVEAT_MARKERS`) rather than a second copy: the same markers that
    CLEAR a Pass A.b warning for a stripped gate are the ones that are now FALSE about this
    one. Mirror-image passes over one vocabulary.

THE GATE WAS RENAMED IN 0041 S7 (`scripts/claugentic-check_doc_budgets.py`, born-prefixed so
`init` can deliver it), and both scans deliberately keep matching the BARE `check_doc_budgets.py`
token: released CHANGELOG history spells the old path and is never edited, while the prefixed
basename contains the bare one — one token, both spellings, zero coverage lost. See `GATE_NAME`.

HONEST SCOPE — what these two scans do NOT catch (measured, not estimated). Running the landed
scans over the BASE shipped corpus (the exact copy this slice deleted) finds **10 candidate
stale-claim lines and catches 4**. The residual is three whole shapes, and it is larger than a
single edge case:
  1. **Any claim that does not name the basename.** The denial scan is basename-gated, so
     "the harness's internal byte-budget gate, which is stripped from the release" is invisible
     to it, and `byte-budget` is outside `DOC_BUDGET_CONTEXT_RE` too (a real instance survives
     in `CHANGELOG.md`'s 0.4.0 section, corrected in prose rather than by a scan).
  2. **Every `harness-self` phrasing** — the dominant one in this repo's copy, and the reason
     all six base-corpus misses look alike. `harness-self` is excluded from the denial
     vocabulary for TWO independent reasons: the WORKFLOW adopter note names both gates in one
     sentence (so it legitimately qualifies the version-sync clause on a line that also names
     this gate), and `docs/claugentic-WORKFLOW.md`'s rung-2 byte-exact-pin clause calls that
     pin "one harness-self extra" on a line that mentions this gate — a second, different
     honest use. Dropping the exclusion turns both red.
  3. **Anything wrapped across lines.** Both scans are line-scoped, so a claim split over two
     source lines is missed by construction (the `skills/build/SKILL.md` close-out roster this
     slice deleted was exactly that shape; a paragraph-scoped variant was measured and rejected
     — 3 false positives at window 0, 11 at ±1, on honest copy).
Note the asymmetry: that shared-line shape is a documented FALSE-NEGATIVE for the denial scan
but a FALSE-POSITIVE path for the unreachability scan (measured — it returns a hit on it), which
is why the guards are stated per-scan rather than shared.

WHY THIS MATTERS MORE THAN IT LOOKS: Pass A.b stopped scanning this basename **in the same
commit** that shipped the gate, so this file is now the SOLE mechanical custody of stale
ship-class copy about it. Everything in the residual above is model-upheld. A rewording-survival
rewrite (clause-scoping both scans, dropping the basename gate) is measured and ROADMAP'd.

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

# The gate whose ship-class this file's whole premise rests on. Born-prefixed at 0041 S7,
# when `init` began DELIVERING it into adopter repos (the managed-file naming rule).
GATE_PATH = "scripts/claugentic-check_doc_budgets.py"

# THE SCAN TOKEN IS THE BARE BASENAME, DELIBERATELY — never `Path(GATE_PATH).name`. Released
# CHANGELOG sections (never edited — they are history) name the gate at its OLD unprefixed
# path, and stale ship-class copy about it is exactly what this file exists to catch; the
# prefixed basename CONTAINS the bare one, so ONE bare token matches both spellings and the
# scan loses nothing by the rename. Deriving it (rather than typing a literal) keeps the pin
# on the rename: strip the managed prefix off the real path, so a second rename cannot leave
# the token pointing at a file that no longer exists.
# `TestTheScanTokenSpansBothSpellings` pins both directions.
MANAGED_PREFIX = "claugentic-"
GATE_NAME = Path(GATE_PATH).name[len(MANAGED_PREFIX):]
LEGACY_GATE_PATH = str(Path(GATE_PATH).parent / GATE_NAME).replace("\\", "/")

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
# mirror-image passes). `harness-self` is the ONE exclusion; the module docstring's honest-scope
# note states BOTH independent reasons it has to be excluded, and what that costs.
SHIP_CLASS_DENIALS = tuple(m for m in csc.CAVEAT_MARKERS if m != "harness-self")

# HISTORY IS NOT A DENIAL. A changelog entry or a superseding ledger line legitimately says what
# the ship-class USED TO BE, in the same sentence as the correction. Both scans skip a line that
# marks itself as a past-tense/superseded statement. Measured why this is not optional: reflowing
# CHANGELOG's own "used to be stripped from the release" entry onto ONE line — a pure re-wrap,
# zero wording change — turns the denial scan red on honest release history. The cost is stated
# rather than hidden: a line that pairs a historical marker with a genuinely live false claim is
# skipped. That trade is right because the alternative punishes the very copy this slice wants
# written (say what changed, in the same breath as what it was).
HISTORICAL_RE = re.compile(
    # Past-tense ONLY. `until 0041` was in the first cut and is deliberately OUT: it is a
    # FORWARD clause, and a guard whose contract is "history is not a denial" must never
    # exempt a line that both promises the next slice and caveats the gate away today
    # (0041 S6 land, L8 — measured: the forward form silently swallowed a live denial).
    # Bare `no longer` is OUT for the same reason (S6 code-review F3): it is a PRESENT-STATE
    # negation ("is no longer shipped" = a live false denial the guard must not exempt); only
    # its honest collocations are history — `no longer stripped` (post-ship fact) and the
    # supersession phrasings `no longer true` / `no longer the case`.
    r"used to be|no longer stripped|no longer true|no longer the case"
    r"|formerly|stopped being|was stripped",
    re.IGNORECASE,
)


def find_unreachability_claims(texts: dict[str, str]) -> list[str]:
    """Pure core: `path:lineno: <line>` for every doc-budget WARN-unreachability claim.

    Takes an injected `{path: text}` map so the patterns are hermetically testable without
    git or the filesystem (mirrors `check_shipped_content.py`'s pure cores).
    """
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if HISTORICAL_RE.search(line):
                continue
            if DOC_BUDGET_CONTEXT_RE.search(line) and UNREACHABILITY_RE.search(line):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def find_ship_class_denials(texts: dict[str, str]) -> list[str]:
    """Pure core: `path:lineno: <line>` for every shipped line that caveats THIS gate away."""
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if GATE_NAME not in line or HISTORICAL_RE.search(line):
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

    def test_the_scan_token_is_the_bare_basename_of_the_real_path(self):
        # The derivation, pinned: GATE_NAME is GATE_PATH's basename minus the managed prefix.
        # A hand-typed literal would survive a second rename silently; this does not.
        assert GATE_PATH == f"scripts/{MANAGED_PREFIX}{GATE_NAME}"
        assert GATE_NAME == "check_doc_budgets.py"
        assert LEGACY_GATE_PATH == "scripts/check_doc_budgets.py"

    def test_the_marker_vocabulary_stays_in_step_with_the_scanner(self):
        # The denial vocabulary is DERIVED from the scanner's markers, minus exactly one
        # documented exclusion — so a marker added there is covered here with no edit.
        # (Named for the property it actually pins: a hand-typed literal tuple would keep this
        # file green, so this is "stays in step", not "is provably not recopied".)
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

    def test_release_history_stating_the_OLD_ship_class_is_not_a_denial(self):
        # THE reflow guard. This is `CHANGELOG.md`'s own Unreleased entry with its first two
        # source lines joined — a pure re-wrap, not one word changed. Without HISTORICAL_RE the
        # denial scan goes RED here and accuses honest release history of denying the ship
        # (measured: the wrap is the only thing keeping the basename and the marker apart).
        texts = {
            "CHANGELOG.md": (
                "- **The doc-budget gate now ships in the release payload.** "
                "`scripts/check_doc_budgets.py` used to be stripped from the release as "
                "harness-self tooling; its caps became per-repo data in the previous change.\n"
            )
        }
        assert find_ship_class_denials(texts) == []
        assert find_unreachability_claims(texts) == []

    def test_a_superseding_ledger_line_is_not_a_denial(self):
        # The sibling shape: a decisions entry restating a dead premise in order to kill it.
        texts = {
            "docs/x.md": (
                "SUPERSEDED: the old premise held that gate is stripped, so no doc-budget WARN "
                "can fire for an adopter — that is no longer true.\n"
            )
        }
        assert find_unreachability_claims(texts) == []

    def test_the_historical_guard_does_not_excuse_a_live_claim(self):
        # Non-vacuity in the other direction: the guard is LINE-scoped, so a live denial on its
        # own line is still caught even when history is discussed nearby.
        texts = {
            "docs/y.md": (
                "The gate used to be stripped from the release.\n"
                "Run `scripts/check_doc_budgets.py` only here (N-A in an adopter).\n"
            )
        }
        assert len(find_ship_class_denials(texts)) == 1

    def test_a_forward_promise_does_not_excuse_a_live_caveat(self):
        # L8 (0041 S6 land). A line that both promises the next slice AND wrongly caveats the
        # gate away today is a live denial, not history — with `until 0041` in HISTORICAL_RE's
        # alternation this was silently exempted (measured); the guard is past-tense only.
        texts = {
            "docs/z.md": (
                "Run `scripts/check_doc_budgets.py` (N-A in an adopter until 0041 Slice 7).\n"
            )
        }
        assert len(find_ship_class_denials(texts)) == 1

    def test_a_present_state_negation_does_not_excuse_a_live_denial(self):
        # F3 (0041 S6 code-review). Bare `no longer` is a present-state negation, not history:
        # "is no longer shipped" is a live false denial and must be CAUGHT. Only the honest
        # post-ship collocation `no longer stripped` stays exempt.
        live = {
            "docs/n.md": (
                "`scripts/check_doc_budgets.py` is no longer shipped (N-A in an adopter).\n"
            )
        }
        honest = {
            "docs/h.md": (
                "`scripts/check_doc_budgets.py` is no longer stripped from the release.\n"
            )
        }
        assert len(find_ship_class_denials(live)) == 1
        assert find_ship_class_denials(honest) == []

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


class TestTheScanTokenSpansBothSpellings:
    """0041 S7: the gate was renamed, and the scans must still see BOTH spellings.

    The bare token is what makes that true, and it is the kind of narrowing that fails
    SILENTLY — a `Path(GATE_PATH).name` token would keep every existing case green (they all
    use the prefixed path) while quietly ceasing to scan released history, the one corpus this
    file can never fix by editing. Both directions are pinned: each spelling is CAUGHT when it
    carries a live caveat, and neither is caught when the line is honest.
    """

    def test_a_caveated_mention_at_the_OLD_path_is_still_caught(self):
        texts = {"CHANGELOG.md": f"run `python {LEGACY_GATE_PATH}` (N-A in an adopter)"}
        assert len(find_ship_class_denials(texts)) == 1

    def test_a_caveated_mention_at_the_NEW_path_is_caught(self):
        texts = {"docs/d.md": f"run `python {GATE_PATH}` (N-A in an adopter)"}
        assert len(find_ship_class_denials(texts)) == 1

    def test_neither_spelling_is_flagged_when_the_line_is_honest(self):
        texts = {
            "docs/e.md": (
                f"`{LEGACY_GATE_PATH}` was its name before the rename; run "
                f"`{GATE_PATH}` wherever init delivered it.\n"
            )
        }
        assert find_ship_class_denials(texts) == []

    def test_the_context_guard_admits_both_spellings(self):
        # The unreachability scan's scope guard is regex-based, not basename-based — assert it
        # covers both spellings too, or half the corpus would fall out of THAT scan instead.
        assert DOC_BUDGET_CONTEXT_RE.search(LEGACY_GATE_PATH)
        assert DOC_BUDGET_CONTEXT_RE.search(GATE_PATH)


class TestScanVocabularyIsExercised:
    """F9 (0041 S6 code-review): this file claims SOLE mechanical custody of stale ship-class
    copy, so every alternation branch and every derived marker is positively exercised here —
    a narrowed/rotted regex cannot stay green by only ever being tested through one phrasing."""

    def test_the_context_gate_matches_the_gate_it_guards(self):
        # Identity pin: DOC_BUDGET_CONTEXT_RE hardcodes a token lines below GATE_NAME — tie
        # them, so a gate rename cannot silently divorce the scans from their subject (the
        # ships-pin stays green on a rename: default-include has no entry to miss).
        assert DOC_BUDGET_CONTEXT_RE.search(GATE_NAME)
        assert DOC_BUDGET_CONTEXT_RE.search("the doc-budget WARN")
        assert DOC_BUDGET_CONTEXT_RE.search("a doc budget breach")

    @pytest.mark.parametrize(
        "claim",
        [
            "no WARN can fire",
            "no doc-budget WARN can fire",
            "it will never produce that WARN",
            "an adopter cannot produce the WARN",
            "you can't produce its doc-budget WARN",
            "a fresh repo can not produce a WARN",
            "that gate is stripped",
            "this gate is stripped",
            "the gate is stripped",
        ],
    )
    def test_every_unreachability_branch_is_live(self, claim):
        texts = {"docs/u.md": f"doc-budget note: {claim}.\n"}
        assert len(find_unreachability_claims(texts)) == 1, claim

    @pytest.mark.parametrize("marker", SHIP_CLASS_DENIALS)
    def test_every_denial_marker_is_live(self, marker):
        texts = {"docs/m.md": f"`{GATE_PATH}` — {marker}, so skip it.\n"}
        assert len(find_ship_class_denials(texts)) == 1, marker


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
