"""The decisions ledger's index and its shard files must agree — in BOTH directions.

`docs/claugentic-DECISIONS.md` is a routing INDEX (content-free by rule) over the shards in
`docs/claugentic-decisions/`. Two ways that pair can rot, and each is silent:

  * a shard is **deleted or renamed** and the index still routes to it — a consultation
    follows a dead link and concludes "no decision was recorded", which is how a settled
    constraint gets re-litigated;
  * a shard file is **added** and never routed from the index — the content exists but is
    unreachable by the only entry point CLAUDE.md permits ("reference the decisions ledger
    only via `docs/claugentic-DECISIONS.md`"), so it is invisible in practice.

This test pins both. It REPLACES the hand-maintained `REQUIRED_SHARDS` tuple that used to
live in `scripts/check_doc_budgets.py` (plan 0041 Slice 4, absorbing the 0040-banked
"index↔shards agreement test" item): that list guarded one direction only, and only for the
shards someone remembered to type into it. A set relation derived from the two real
artifacts guards both directions and needs no maintenance — which is also why the budget
gate keeps EXACTLY ONE cap source (its `docs/claugentic-decisions/*.md` glob entry) and no
existence guard at all: one concern, one home.

Both directions must fail INDEPENDENTLY — deleting a shard and adding an unrouted file are
different defects with different fixes — so each has its own test over its own set
difference, plus a hermetic non-vacuity case proving the relation actually refuses.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "docs" / "claugentic-DECISIONS.md"
SHARD_DIR = REPO_ROOT / "docs" / "claugentic-decisions"

# The index's routing lines are markdown links whose target is shard-dir-relative (the index
# lives in `docs/`), e.g. `- [honesty](claugentic-decisions/honesty.md) — READ FIRST.`
# Anchored on the link TARGET, not the label, so a reworded label can't break the parse and a
# bare mention of a filename in prose can't fake a route.
_LINK_RE = re.compile(r"\]\(claugentic-decisions/([^)/]+\.md)\)")


def routed_shards(index_text: str) -> set[str]:
    """The shard basenames the index routes to (link targets only — never prose mentions)."""
    return set(_LINK_RE.findall(index_text))


def present_shards(shard_dir: Path) -> set[str]:
    """The shard basenames that actually exist on disk (flat — the dir does not nest)."""
    return {p.name for p in shard_dir.glob("*.md")}


class TestIndexRoutesOnlyToShardsThatExist:
    """Direction 1: index -> filesystem. A route with no file behind it is a dead link."""

    def test_every_routed_shard_exists(self):
        routed = routed_shards(INDEX_PATH.read_text(encoding="utf-8"))
        # Non-vacuity guard: an empty parse would make the assertion below trivially true.
        assert routed, f"{INDEX_PATH.name} routes to no shards — the index parse found nothing."
        missing = sorted(name for name in routed if not (SHARD_DIR / name).exists())
        assert missing == [], (
            f"{INDEX_PATH.name} routes to shard(s) that do not exist: {missing}. Restore them "
            "(git history) or drop their index lines."
        )

    def test_a_deleted_shard_is_refused(self, tmp_path):
        # NON-VACUOUS: the relation must actually flag the delete case, not just pass today.
        shard_dir = tmp_path / "claugentic-decisions"
        shard_dir.mkdir()
        (shard_dir / "honesty.md").write_text("x", encoding="utf-8")
        index = "- [honesty](claugentic-decisions/honesty.md)\n- [gone](claugentic-decisions/gone.md)\n"
        assert routed_shards(index) - present_shards(shard_dir) == {"gone.md"}


class TestEveryShardIsRoutedFromTheIndex:
    """Direction 2: filesystem -> index. An unrouted shard is unreachable content."""

    def test_every_shard_file_is_referenced_by_the_index(self):
        routed = routed_shards(INDEX_PATH.read_text(encoding="utf-8"))
        present = present_shards(SHARD_DIR)
        # Non-vacuity guard: an empty shard dir would make the assertion below trivially true.
        assert present, f"{SHARD_DIR} contains no shards — the directory scan found nothing."
        unrouted = sorted(present - routed)
        assert unrouted == [], (
            f"shard(s) not routed from {INDEX_PATH.name}: {unrouted}. Add an index line for "
            "each (external references reach a shard only through the index)."
        )

    def test_an_unrouted_shard_is_refused(self, tmp_path):
        # NON-VACUOUS: the delete case and the unrouted case are different set differences,
        # so this direction fails on its own even when direction 1 is perfectly clean.
        shard_dir = tmp_path / "claugentic-decisions"
        shard_dir.mkdir()
        (shard_dir / "honesty.md").write_text("x", encoding="utf-8")
        (shard_dir / "orphan.md").write_text("x", encoding="utf-8")
        index = "- [honesty](claugentic-decisions/honesty.md)\n"
        assert routed_shards(index) - present_shards(shard_dir) == set()  # direction 1 clean
        assert present_shards(shard_dir) - routed_shards(index) == {"orphan.md"}


class TestTheIndexParse:
    """The parse is the load-bearing part of both directions — pin what counts as a route."""

    def test_a_prose_mention_is_not_a_route(self):
        # Only a markdown LINK target routes; naming a file in a sentence does not.
        assert routed_shards("see claugentic-decisions/honesty.md for the rule") == set()

    def test_a_link_label_does_not_have_to_match_the_filename(self):
        assert routed_shards("- [READ FIRST](claugentic-decisions/honesty.md) — x") == {"honesty.md"}

    def test_a_nested_path_is_not_matched(self):
        # The shard dir is flat by design; a nested target is not a shard route.
        assert routed_shards("[x](claugentic-decisions/sub/deep.md)") == set()
