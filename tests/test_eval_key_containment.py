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
`test_eval_manifest.py` also owns the answer key's SHAPE (ten rows, two per module,
unique ids, every file:line real) — no count from it is restated here; this file derives
its vocabulary from the same table and asserts only that the derivation is non-empty.

Enumeration: `git ls-files` with `check=True`, the repo's one corpus convention (see
`scripts/build_release.py` `_tracked_files`, `scripts/claugentic-check_architecture_tree.py`,
`tests/test_adopter_pointer_integrity.py`). **Do NOT revert this to `rglob`/`os.walk`:** a
disk walk rooted here also sweeps `eval/fixture-app/.venv`, `.pytest_cache` and the linked
worktrees this repo parks under a gitignored `.claude/worktrees/` — it would pass in a
worktree and in CI and fail only in the checkout a release is cut from (plan 0041 Slice 9).

Files are matched as BYTES, so every tracked file is in scope — including the ones no
text decoder should be pointed at (`.png`) — with no decode branch to get wrong. Recorded
residual: an id stored in a non-ASCII-superset encoding (UTF-16/32) would evade the byte
match. No tracked file in this repo uses one, and the leak this pin exists to catch is
prose an agent reads, which is UTF-8 here.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_REL = "eval/fixture-defects/SEED_MANIFEST.md"
MANIFEST = REPO_ROOT / MANIFEST_REL

# The first cell of an answer-key table row, when it is a seed id. The table's shape is
# `test_eval_manifest.py`'s contract; all this needs is the id column's vocabulary.
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
    # `Seed <-> finding mapping` table (10 ids each) plus per-seed scoring notes, and the
    # file's own "no-peeking contract" section already declares itself an answer-carrying
    # document outside the measurement run's scope. Recording per-seed recall is the
    # file's job; it cannot do it without the ids.
    "eval/BASELINE.md": "records per-seed recall — the mapping tables ARE the results",
}

# Measured 2026-08-18: 118 tracked files, 116 of them scanned (118 minus the allowlist).
# A floor well under that catches an enumeration or exclusion mistake that silently
# empties the sweep, without churning on ordinary file adds/removes.
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
    bad = [i for i in ids if not re.fullmatch(r"[A-Z]+-\d+", i)]
    assert not bad, f"malformed seed ids parsed from the answer key: {bad}"


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


def test_the_scan_lets_an_allowlisted_path_keep_its_ids(tmp_path: Path) -> None:
    """Non-vacuity, direction 2: the same planted id in an allowlisted path stays green."""
    planted = _seed_ids()[0]
    allowed_rel = MANIFEST_REL
    allowed = tmp_path / allowed_rel
    allowed.parent.mkdir(parents=True)
    allowed.write_text(f"| {planted} | security | app/x.py | 1 | ... |\n", encoding="utf-8")
    scanned = [rel for rel in [allowed_rel] if rel not in ALLOWLIST]
    offenders = _files_naming_seed_ids(tmp_path, scanned, _seed_id_pattern(_seed_ids()))
    assert offenders == [], (
        f"the allowlist did not admit {allowed_rel} (got {offenders}) -- the answer key "
        "itself would be reported as a leak."
    )
