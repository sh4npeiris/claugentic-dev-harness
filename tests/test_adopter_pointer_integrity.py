"""Pin the adopter-resolvability of the harness's own shipped POINTERS (plan 0041 Slice 9).

Every `.claude/agents/*.md` role file and `docs/claugentic-WORKFLOW.md` ship inside the
plugin and are read, verbatim, by agents running in an ADOPTER's repo. So a pointer in
them is only honest if it resolves **in the reader's project**, not merely in this one
(`docs/claugentic-standards/docs-traceability.md` -> *Reach, not residence*). Three
pointer regressions are pinned here, each one a real defect this slice fixed:

  1. **The dangling honesty-positioning pointer.** Two role files told the reader to read
     `CLAUDE.md` -> "Honesty positioning". No such heading exists in an adopter's managed
     `CLAUDE.md` fence (`skills/init/SKILL.md` writes no honesty section), the adopter
     DECISIONS seed is pinned to carry it in NEITHER shape
     (`tests/test_seed_templates.py::test_decisions_seed_is_a_blank_ledger`), and it does
     not exist as a heading in this repo's own `CLAUDE.md` either. The fix direction is
     therefore DELETE-THE-POINTER, never add-the-section, and the premise those pointers
     were reaching for now sits INLINE in each role file. Premise prose that merely
     mentions honesty positioning stays legal -- what is pinned is the POINTER FORM.
  2. **The adopter note's position.** `docs/claugentic-WORKFLOW.md` explains how its own
     references resolve inside an adopter repo. That explanation is only useful BEFORE the
     references it corrects, so it must precede the first stage heading (`## 0.`).
  3. **The named upstream channel.** WORKFLOW is the ONE canonical home for the
     contribution channel (the learning loop's "promote upstream" step). A condensation
     pass that drops the URL silently re-opens the loop this slice closed, so the URL --
     read from the plugin manifest, never re-typed -- is pinned present, and pinned to
     exactly one home (one canonical home per lesson; every other mention is a pointer).

HONEST SCOPE. Pin 1 is a **proximity heuristic**, not a semantic check: it fires on
`CLAUDE.md` and "honesty positioning" within 40 characters of each other with no sentence
terminator between them (a cheap "same clause" proxy). A pointer spelled across a sentence
boundary, or wrapped across two source lines, is missed by construction -- the same
line-scoping limit `tests/test_shipped_condensation_trigger.py` documents for its own
scans. It is a REGRESSION pin for the exact defect class that just bit, not a general
"does this pointer resolve?" detector; the general case stays model-upheld (the
`honesty-reviewer` + `docs-traceability` lens at Verify).

Harness-self by construction: `tests/` is stripped from the release, so this scan reads
the source tree it is reasoning about and never runs in an adopter repo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
WORKFLOW_PATH = REPO_ROOT / "docs" / "claugentic-WORKFLOW.md"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"

# --- Pin 1: the dangling honesty-positioning pointer -------------------------------------

# "Same clause" proxy: no sentence terminator between the two, within a bounded gap. The
# gap class excludes `.` deliberately -- the `.` inside `CLAUDE.md` belongs to the anchor
# pattern, never to the gap, so the two orderings below are symmetric.
_CLAUSE_GAP = r"[^.;\n]{0,40}?"
_CLAUDE_MD = r"CLAUDE\.md"
_HONESTY_TOPIC = r"honesty\s+positioning"

HONESTY_POINTER_RE = re.compile(
    rf"{_CLAUDE_MD}{_CLAUSE_GAP}{_HONESTY_TOPIC}|{_HONESTY_TOPIC}{_CLAUSE_GAP}{_CLAUDE_MD}",
    re.IGNORECASE,
)


def find_honesty_pointer_forms(texts: dict[str, str]) -> list[str]:
    """Pure core: `path:lineno: <line>` for every `CLAUDE.md`-anchored honesty pointer.

    Takes an injected `{path: text}` map so the pattern is hermetically testable without
    the filesystem (mirrors `check_shipped_content.py`'s pure cores).
    """
    hits: list[str] = []
    for path in sorted(texts):
        for lineno, line in enumerate(texts[path].splitlines(), start=1):
            if HONESTY_POINTER_RE.search(line):
                hits.append(f"{path}:{lineno}: {line.strip()}")
    return hits


def _agent_texts() -> dict[str, str]:
    """Every `.claude/agents/*.md` role file, keyed by repo-relative path."""
    return {
        p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(AGENTS_DIR.glob("*.md"))
    }


class TestTheHonestyPointerScanIsExercised:
    """Non-vacuity in both directions -- the pattern must catch the two forms that were
    really there, and must leave honest premise prose alone."""

    @pytest.mark.parametrize(
        "line",
        [
            # honesty-reviewer's pre-fix read-first line (the parenthetical form).
            "Read first: `CLAUDE.md` (the **honesty positioning** -- only the tree check "
            "is mechanically enforced).",
            # product-designer's pre-fix read-first line (the arrow form).
            "Read first: `docs/claugentic-standards/product-ux.md`, and `CLAUDE.md` -> "
            "Honesty positioning.",
            # The reverse ordering, so a re-worded regression is still seen.
            "The honesty positioning lives in `CLAUDE.md`.",
        ],
    )
    def test_the_pointer_form_is_caught(self, line: str) -> None:
        assert len(find_honesty_pointer_forms({".claude/agents/x.md": line + "\n"})) == 1

    def test_premise_prose_without_the_anchor_is_clean(self) -> None:
        # The FIX shape: the premise stated inline, no dangling pointer. Must stay legal --
        # this pin bans the pointer, never the topic.
        texts = {
            ".claude/agents/y.md": (
                "Over-claiming is the harness's stated #1 risk: only a genuinely-wired "
                "gate is mechanical; everything else is model-upheld.\n"
            )
        }
        assert find_honesty_pointer_forms(texts) == []

    def test_a_claude_md_pointer_on_another_topic_is_clean(self) -> None:
        # `CLAUDE.md` remains a legitimate pointer for durable repo context -- the ban is
        # scoped to the honesty-positioning target that exists in neither repo.
        texts = {
            ".claude/agents/z.md": (
                "Consult the `CLAUDE.md` per-repo harness block for durable structural "
                "context.\n"
            )
        }
        assert find_honesty_pointer_forms(texts) == []

    def test_a_sentence_boundary_between_them_is_not_a_pointer(self) -> None:
        # The clause proxy, pinned: two adjacent sentences are not one pointer.
        texts = {
            ".claude/agents/w.md": (
                "Read `CLAUDE.md` for the repo's principles. Honesty positioning is "
                "stated inline below.\n"
            )
        }
        assert find_honesty_pointer_forms(texts) == []

    def test_the_agent_corpus_is_not_empty(self) -> None:
        # A vanished/renamed agents dir would make the real scan below vacuously green.
        texts = _agent_texts()
        assert len(texts) >= 9, f"expected the nine bundled role files, found {len(texts)}"


class TestNoAgentCarriesTheDanglingHonestyPointer:
    def test_no_role_file_points_at_claude_md_for_honesty_positioning(self) -> None:
        hits = find_honesty_pointer_forms(_agent_texts())
        assert hits == [], (
            "A shipped role file tells its reader to find 'Honesty positioning' in "
            "`CLAUDE.md` -- a heading that exists in NEITHER an adopter's managed fence "
            "nor this repo's own CLAUDE.md (and the adopter DECISIONS seed is pinned to "
            "carry it in neither shape). State the premise INLINE in the role file "
            "instead; do not add the section. Offending lines:\n  " + "\n  ".join(hits)
        )


# --- Pin 2: the adopter note precedes the references it corrects --------------------------

# Both headings are matched by their stable prefix, ignoring any leading blockquote marker
# (the adopter note is authored as a blockquote callout).
ADOPTER_NOTE_HEADING_RE = re.compile(r"^\s*>?\s*#{2,4}\s+Adopter note\b", re.MULTILINE)
FIRST_STAGE_HEADING_RE = re.compile(r"^##\s+0\.", re.MULTILINE)


class TestWorkflowAdopterNoteComesFirst:
    def test_both_headings_exist(self) -> None:
        # Fail LOUD rather than vacuously pass if either heading is renamed away.
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert ADOPTER_NOTE_HEADING_RE.search(text), (
            f"{WORKFLOW_PATH.name}: no 'Adopter note' heading found -- the doc no longer "
            "tells an adopter how its references resolve in their repo."
        )
        assert FIRST_STAGE_HEADING_RE.search(text), (
            f"{WORKFLOW_PATH.name}: no '## 0.' stage heading found -- the anchor this pin "
            "measures against is gone; re-derive it before editing this test."
        )

    def test_the_adopter_note_precedes_the_first_stage_heading(self) -> None:
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        note = ADOPTER_NOTE_HEADING_RE.search(text)
        first_stage = FIRST_STAGE_HEADING_RE.search(text)
        assert note and first_stage  # covered with a better message by the test above
        assert note.start() < first_stage.start(), (
            f"{WORKFLOW_PATH.name}: the adopter note sits at offset {note.start()}, AFTER "
            f"the first stage heading at {first_stage.start()}. It explains how the "
            "references BELOW it resolve inside an adopter repo, so a reader who meets "
            "those references first has already been misled. Keep it in the intro."
        )


# --- Pin 3: the upstream contribution channel is named, once ------------------------------


def _plugin_repo_url() -> str:
    """The channel URL, read from the manifest -- the single source, never re-typed here."""
    manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    url = manifest.get("repository", "")
    assert url.startswith("https://"), (
        f"{PLUGIN_MANIFEST.name}: `repository` is {url!r} -- the upstream channel pinned "
        "below is derived from it, so it must be a real URL."
    )
    return url


class TestWorkflowNamesTheUpstreamChannel:
    def test_the_workflow_names_the_plugin_repo_url(self) -> None:
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        url = _plugin_repo_url()
        assert url in text, (
            f"{WORKFLOW_PATH.name}: does not name {url} -- the learning loop tells an "
            "adopter to promote a universal lesson 'upstream', and this doc is the one "
            "place that says WHERE. Without it the loop is a dead end again (plan 0041 "
            "Slice 9). A condensation pass must re-home the channel, never drop it."
        )

    def test_the_channel_is_named_exactly_once(self) -> None:
        # One canonical home per lesson (WORKFLOW -> the learning loop); every other
        # mention is a POINTER at this one, never a copy that can drift.
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        url = _plugin_repo_url()
        count = text.count(url)
        assert count == 1, (
            f"{WORKFLOW_PATH.name}: names {url} {count} times. The channel has ONE "
            "canonical home; point at it from anywhere else rather than repeating a URL "
            "that then drifts."
        )
