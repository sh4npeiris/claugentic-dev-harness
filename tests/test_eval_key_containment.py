"""Containment pin for the eval answer key — the seed ids stay inside the fixture.

`eval/fixture-defects/` is a fixed exam the audit re-takes so prompt/model drift becomes
a number (see `eval/BASELINE.md`). The exam only measures anything if the run has not
been handed the answers. Its answer key (`eval/fixture-defects/SEED_MANIFEST.md`) names
each planted flaw by a short **seed id**, and an id is not a bare label: paired with the
prose that carries it, it hands over the defect's nature and the file it lives in.

**Why the contamination canary does not cover this.** The canary is a distinctive
sentence planted *inside the manifest*: it proves a leak only when the run actually READ
that file. Copy the ids and their defect natures into some other document — the
architecture index every agent reads first to navigate, a lint-config comment, a
decisions ledger, a plan — and an agent acquires the answers without ever touching the
file the tracer lives in. The post-hoc transcript grep then comes back clean and the run
is recorded "contamination: canary absent" while it was, in substance, pre-briefed. That
is exactly what had happened when this pin was written (plan 0041 Slice 11): five index
entries named ten seed ids with their defect natures and file mapping. The canary guards
one exfiltration path; this pin guards the other.

**Sibling guard — do NOT merge the two.** `tests/test_eval_manifest.py` enforces the
same prohibition one directory IN: its `FORBIDDEN_TOKENS` check forbids the fixture
SOURCE (`eval/fixture-defects/app/*.py`) from self-labelling its own planted defects, so
the code reads as ordinary sloppy code. This file enforces it one directory OUT: no
tracked file anywhere in the repo may name a seed id except the small set that
legitimately records the answers. Different corpus, different vocabulary, same contract.
`test_eval_manifest.py` OWNS the answer key's shape (the row count, the per-module split,
id uniqueness, file:line reality). This file derives its vocabulary from the same table and
IMPORTS that file's row count rather than restating it, so a row whose id cell stops parsing
here fails loudly instead of silently shrinking the vocabulary the scan below runs on.

Enumeration: `git ls-files` with `check=True`, the repo's one corpus convention (see
`scripts/build_release.py` `_tracked_files`, `scripts/claugentic-check_architecture_tree.py`,
`tests/test_adopter_pointer_integrity.py`). **Do NOT revert this to `rglob`/`os.walk`:** a
disk walk rooted here also sweeps `eval/fixture-app/.venv`, `.pytest_cache` and the linked
worktrees this repo parks under a gitignored `.claude/worktrees/` — it would pass in a
worktree and in CI and fail only in the checkout a release is cut from (plan 0041 Slice 9).

Files are matched as BYTES, so every tracked file is in scope — including the ones no
text decoder should be pointed at (`.png`) — with no decode branch to get wrong.

**What this pin does NOT catch — measured 2026-08-18 (plan 0041 S11).** It matches the id
TOKEN, ASCII, exactly. Evaded by: a typographic hyphen inside an id (U+2011/U+2013), a
mid-token line wrap, a lower-cased id, a non-ASCII-superset encoding (UTF-16/32). None
occurs in this repo today and no formatter here can introduce one, so the pattern is
deliberately NOT widened — an accidental leak is typed, and typed ids carry a plain
hyphen. The residual that matters is larger and unclosable: **a PARAPHRASE republishes the
answer and stays green** — an entry naming a planted defect's nature and the file it lives
in, without its id, hands over the same thing with every test in this file passing. That
half is MODEL-UPHELD; its only guard is the do-not-revert note in the tree's `eval/`
section, and `test_the_tree_carries_the_do_not_revert_note` below is what stops that note
being deleted silently.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from test_eval_manifest import EXPECTED_ROWS

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_REL = "eval/fixture-defects/SEED_MANIFEST.md"
MANIFEST = REPO_ROOT / MANIFEST_REL
TREE_REL = "docs/claugentic-ARCHITECTURE_TREE.md"
TREE_NOTE_ANCHOR = "Do not revert the `fixture-defects/` entries below to defect-level detail."

# The first cell of an answer-key table row, when it is a seed id. The table's shape is
# `test_eval_manifest.py`'s contract; all this needs is the id column's vocabulary.
# DO NOT loosen this to accept any first cell "for DRY" -- measured and REFUSED (0041 S11).
# A first-cell-takes-anything parser makes the vocabulary the cell's literal TEXT, so a
# bolded row puts the bold bytes into the alternation and the scan then hunts those while a
# plain leak walks past: silent PARTIAL failure traded for silent TOTAL failure. The parity
# assertion in the first test below is what makes a non-matching cell fail loudly instead.
_ID_CELL_RE = re.compile(r"^\|\s*([A-Z]+-\d+)\s*\|")

# The ONLY tracked files allowed to name a seed id, each with the measurement behind it.
# Every entry is a hole in the exam, so the set is kept as small as the truth allows and
# `test_every_allowlisted_file_still_needs_its_exemption` deletes any entry that stops
# earning its place.
ALLOWLIST: dict[str, str] = {
    # The answer key itself: it DEFINES the ids. Excluding it is definitional, not an
    # exemption — this file is also the one the contamination canary lives in.
    MANIFEST_REL: "the answer key — it defines the seed ids",
    # Measured 2026-08-18: both recorded baseline entries carry a full per-seed
    # `Seed <-> finding mapping` table (one row per manifest seed) plus per-seed scoring
    # notes, and the file's own "no-peeking contract" section already declares itself an
    # answer-carrying document outside the measurement run's scope. Recording per-seed
    # recall is the file's job; it cannot do it without the ids.
    # RESIDUAL this exemption knowingly admits: the measurement procedure a runner is told
    # to open lives in the SAME file, above two complete answer keys -- the
    # read-the-procedure / stop-before-the-entries split is model-upheld, not enforced.
    # KILLABLE HALF: split this file so the procedure and the per-seed entries are separate
    # documents and the one a runner opens carries no ids (out of scope here; routed at
    # land, plan 0041 S11).
    "eval/BASELINE.md": "records per-seed recall — the mapping tables ARE the results",
}

# The corpus is every tracked file minus the allowlist; `git ls-files` owns the count, so
# no absolute is restated here. The floor sits well under it: an enumeration or exclusion
# mistake that silently EMPTIES the sweep fails loudly, without churning on ordinary file
# adds. Its slack is real and measured (2026-08-18, plan 0041 S11): dropping `docs/` from
# the corpus trips it, dropping `.claude/` does not.
CORPUS_FLOOR = 90


def _tracked_files() -> list[str]:
    """Every tracked file, repo-relative, forward-slash normalized.

    `check=True` on purpose: a broken/absent git must raise, never hand back an empty
    corpus that makes every assertion below pass vacuously.
    """
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return [
        line.replace("\\", "/").strip()
        for line in out.splitlines()
        if line.strip()
    ]


def _seed_ids() -> list[str]:
    """The seed-id vocabulary, derived from the answer key (never hardcoded here)."""
    assert MANIFEST.exists(), f"answer key missing: {MANIFEST_REL}"
    text = MANIFEST.read_text(encoding="utf-8")
    return [
        m.group(1)
        for line in text.splitlines()
        for m in [_ID_CELL_RE.match(line.strip())]
        if m
    ]


def _seed_id_pattern(ids: list[str]) -> re.Pattern[bytes]:
    """A word-bounded alternation over the ids, as bytes (see the module docstring)."""
    alternation = b"|".join(re.escape(i.encode("ascii")) for i in ids)
    return re.compile(rb"\b(?:" + alternation + rb")\b")


def _files_naming_seed_ids(root: Path, rels: list[str], pattern: re.Pattern[bytes]) -> list[str]:
    """The subset of `rels` (repo-relative) whose bytes contain a seed id."""
    return sorted(rel for rel in rels if pattern.search((root / rel).read_bytes()))


def test_seed_id_vocabulary_is_derived_and_non_empty() -> None:
    """A vocabulary that parsed to nothing would make the whole scan below vacuous."""
    ids = _seed_ids()
    assert ids, (
        "no seed ids parsed out of " + MANIFEST_REL + " -- the answer-key table's shape "
        "changed and every containment assertion in this file would pass vacuously. "
        "See tests/test_eval_manifest.py, which owns that table's shape."
    )
    assert len(ids) == EXPECTED_ROWS, (
        f"parsed {len(ids)} seed ids out of the answer key's {EXPECTED_ROWS} rows -- a row "
        "whose id cell stopped matching _ID_CELL_RE (bolded, footnoted, renamed) silently "
        "DROPS that id from the containment vocabulary and it becomes freely leakable, "
        "with this file and tests/test_eval_manifest.py both green."
    )


def test_corpus_is_the_tracked_tree_and_meets_its_floor() -> None:
    """The scan's corpus is part of its contract -- assert it, don't assume it."""
    scanned = [rel for rel in _tracked_files() if rel not in ALLOWLIST]
    assert len(scanned) >= CORPUS_FLOOR, (
        f"only {len(scanned)} tracked files in scope (floor {CORPUS_FLOOR}) -- the "
        "enumeration or the allowlist has swallowed the corpus and the containment scan "
        "would pass vacuously."
    )


def test_no_tracked_file_outside_the_allowlist_names_a_seed_id() -> None:
    """The pin: the answer key is not republished anywhere an agent reads."""
    ids = _seed_ids()
    pattern = _seed_id_pattern(ids)
    scanned = [rel for rel in _tracked_files() if rel not in ALLOWLIST]
    offenders = _files_naming_seed_ids(REPO_ROOT, scanned, pattern)
    assert offenders == [], (
        "these tracked files name an eval seed id and are not allowed to: "
        f"{offenders}. A seed id in prose hands an agent the exam's answers without it "
        "ever opening the answer key -- the contamination canary lives in that file and "
        "cannot see this. Describe what the fixture file IS, never what is planted in "
        "it; point at " + MANIFEST_REL + " instead of quoting it."
    )


def test_every_allowlisted_file_still_needs_its_exemption() -> None:
    """The other direction: an exemption nothing uses is a hole nobody is watching."""
    pattern = _seed_id_pattern(_seed_ids())
    tracked = set(_tracked_files())
    missing = sorted(rel for rel in ALLOWLIST if rel not in tracked)
    assert not missing, f"allowlisted paths that are no longer tracked: {missing}"
    unused = sorted(
        rel for rel in ALLOWLIST
        if not pattern.search((REPO_ROOT / rel).read_bytes())
    )
    assert not unused, (
        f"these files are allowlisted but no longer name any seed id: {unused}. Delete "
        "the entry -- a stale exemption silently widens the next leak's blast radius. "
        "Justifications: " + repr({rel: ALLOWLIST[rel] for rel in unused})
    )


def test_the_scan_fires_on_a_planted_id(tmp_path: Path) -> None:
    """Non-vacuity, direction 1: plant a real id in a scanned file -> the scan reports it."""
    planted = _seed_ids()[0]
    leaky = tmp_path / "docs" / "some-doc.md"
    leaky.parent.mkdir(parents=True)
    leaky.write_text(f"the handler carries {planted} (a planted flaw)\n", encoding="utf-8")
    clean = tmp_path / "docs" / "innocent.md"
    clean.write_text("this file names no seed at all\n", encoding="utf-8")
    offenders = _files_naming_seed_ids(
        tmp_path, ["docs/some-doc.md", "docs/innocent.md"], _seed_id_pattern(_seed_ids())
    )
    assert offenders == ["docs/some-doc.md"], (
        f"the containment scan did not fire on a planted seed id (got {offenders}) -- "
        "it is asserting nothing."
    )


def test_the_scan_spares_the_allowlist_and_only_the_allowlist(tmp_path: Path) -> None:
    """Non-vacuity, direction 2: the SAME id in an allowlisted path and in a scanned one.

    The allowlisted side is DERIVED from ALLOWLIST, never hand-listed, so a new exemption is
    exercised the moment it is added. `testing.md` -> *Exemptions and allowlists inside a
    scan are themselves under test*: positive-only coverage proves the vocabulary is live;
    only the negative fixture -- the same token riding a violation that must STILL be
    caught -- proves the exemption is narrow.
    """
    planted = _seed_ids()[0]
    leak_rel = "docs/some-other-doc.md"
    corpus = [*ALLOWLIST, leak_rel]
    for rel in corpus:
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"| {planted} | security | app/x.py | 1 |", encoding="utf-8")
    pattern = _seed_id_pattern(_seed_ids())
    assert all(pattern.search((tmp_path / rel).read_bytes()) for rel in corpus), (
        "a fixture does not carry the planted id -- this test would pass for the wrong reason."
    )
    offenders = _files_naming_seed_ids(
        tmp_path, [rel for rel in corpus if rel not in ALLOWLIST], pattern
    )
    assert offenders == [leak_rel], (
        f"expected only {leak_rel} reported (got {offenders}) -- the allowlist must spare "
        "its own members and nothing else."
    )


def test_the_tree_carries_the_do_not_revert_note() -> None:
    """The paraphrase half is model-upheld -- pin the note that upholds it.

    A tree entry spelling out a planted defect's nature and its file WITHOUT naming the id
    republishes the answer and every other test here stays green (measured, plan 0041 S11).
    The note is the only thing standing in front of that, and a note nothing asserts is one
    a condensation pass drops silently -- which is how this leak got in.
    """
    tree = (REPO_ROOT / TREE_REL).read_text(encoding="utf-8")
    assert tree.count(TREE_NOTE_ANCHOR) == 1, (
        f"{TREE_REL} must carry the do-not-revert note exactly once (found "
        f"{tree.count(TREE_NOTE_ANCHOR)}): {TREE_NOTE_ANCHOR!r}. It is the ONLY guard "
        "against republishing a seed's defect nature in paraphrase, which the id scan in "
        "this file cannot see."
    )
    para = tree.split(TREE_NOTE_ANCHOR, 1)[1].split("\n\n", 1)[0]
    assert "tests/test_eval_key_containment.py" in para, (
        "the do-not-revert note no longer points back at this pin -- a reader who reverts an "
        "entry is then told nothing about what goes red."
    )
