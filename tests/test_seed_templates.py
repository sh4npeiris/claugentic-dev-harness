"""Pin the PRISTINE shape of the one-time-seed files (plan 0028 S4).

`init` step 7 copies these shipped `_X.md` seeds into an adopter repo (underscore
stripped, create-if-absent only). They are BLANK adopter ledgers — they must carry NO
harness-specific content and NO generated fences, so an `init` agent never seeds bytes
that a future edit could silently corrupt. This test pins exactly that:

  * `_ROADMAP.md` carries NONE of the `harness-audit:backlog` / `harness-product:backlog`
    fence markers — those are SELF-CREATED by `/claugentic-dev-harness:audit` and
    `/claugentic-dev-harness:product` gap mode on first run (a seed that pre-baked them
    would let an adopter hand-edit a fence the skill then silently overwrites).
  * `_DECISIONS.md` carries the expected "consult before re-litigating" header phrase
    (the seed's contract — the maintainer's-guide framing), so a re-write can't drop it.

Reads the real shipped seed files (not hermetic) — it pins the actual shipped bytes,
which is the point. Fails LOUD if a seed file is missing (a vanished seed must not pass
silently).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECISIONS_SEED = REPO_ROOT / "docs" / "claugentic-_DECISIONS.md"
ROADMAP_SEED = REPO_ROOT / "docs" / "claugentic-_ROADMAP.md"

# The generated fences the audit / product skills SELF-CREATE — a pristine ROADMAP seed
# must contain NONE of them (single source: the markers the skills + the advisor pin).
GENERATED_FENCE_MARKERS = (
    "harness-audit:backlog",
    "harness-audit:overview",
    "harness-product:backlog",
)

# The header phrase the DECISIONS seed must keep (the maintainer's-guide contract).
DECISIONS_HEADER_PHRASE = "consult before revisiting a past choice"


def test_seed_files_exist() -> None:
    # A vanished seed would break `init` step 7's copy silently — fail loud here instead.
    assert DECISIONS_SEED.exists(), f"{DECISIONS_SEED.name} (the DECISIONS seed) is missing"
    assert ROADMAP_SEED.exists(), f"{ROADMAP_SEED.name} (the ROADMAP seed) is missing"


def test_roadmap_seed_has_no_generated_fences() -> None:
    text = ROADMAP_SEED.read_text(encoding="utf-8")
    for marker in GENERATED_FENCE_MARKERS:
        assert marker not in text, (
            f"{ROADMAP_SEED.name}: contains the generated fence marker {marker!r} — the "
            f"pristine seed must omit it (audit/product self-create their own fences)."
        )


def test_decisions_seed_carries_the_header_phrase() -> None:
    text = DECISIONS_SEED.read_text(encoding="utf-8").lower()
    assert DECISIONS_HEADER_PHRASE in text, (
        f"{DECISIONS_SEED.name}: missing the expected header phrase "
        f"{DECISIONS_HEADER_PHRASE!r} (the maintainer's-guide seed contract)."
    )


def test_decisions_seed_is_a_blank_ledger() -> None:
    # The seed must NOT carry the harness's own decision content (it's a blank adopter
    # ledger, not a copy of docs/claugentic-DECISIONS.md). A cheap sentinel: the harness's
    # own ledger leads with "Honesty positioning (the #1 rule)" — the seed must not.
    text = DECISIONS_SEED.read_text(encoding="utf-8")
    assert "Honesty positioning" not in text, (
        f"{DECISIONS_SEED.name}: contains harness-specific content — it must be a BLANK "
        f"adopter seed, not a copy of the harness's own filled DECISIONS.md."
    )
