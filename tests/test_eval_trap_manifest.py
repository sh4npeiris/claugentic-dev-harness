"""Mechanical integrity guard for the BUILD-path eval fixture (`eval/fixture-build/`).

That fixture is an exam the harness sits: an `implementer` builds a fixed programming task
from a frozen plan slice, and ten probes measure which realistic mistakes the build made
(`eval/BUILD_BASELINE.md` owns the procedure). Four ways it can rot silently, each pinned
here because each one leaves every other check green:

  * **the answer key drifts from the instrument** -- a row is added, renamed or retagged and
    the probe that was supposed to decide it no longer exists. Every mechanical row's check
    cell is RESOLVED (import + getattr), so a tag is discharged by resolution rather than by
    the two letters being typed;
  * **a builder-visible artifact starts coaching the answer** -- one sentence in the brief
    naming a trap's remedy turns the exam into a reading test, in the direction that looks
    like diligence. The denylist below covers every trap id in the manifest, asserted as a
    set equality so a new trap cannot arrive uncovered;
  * **the measurement instrument starts reading the treatment** -- if anything under
    `checks/` opened the standards catalog, the sweep would no longer compute the same result
    for both arms, which is the claim the whole comparison rests on;
  * **the pinned quantities drift from what they pin** -- `H` is written in
    `eval/BUILD_BASELINE.md` and OWNED by the number of tests in `checks/test_heldout.py`.

**Sibling guard, do NOT merge:** `tests/test_eval_manifest.py` does this job for the
audit-path fixture (`eval/fixture-defects/`), and `tests/test_eval_key_containment.py` keeps
BOTH answer keys from being republished elsewhere in the repo. Different corpora, different
vocabularies, same contract.
"""

from __future__ import annotations

import ast
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

import check_architecture_tree as cat
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Repo-relative LITERALS, not segments joined at runtime -- deliberate. A build-eval run
# deletes the answer-side files from its worktree and finds the tests that must go with them
# **by grepping for those paths**; a path this file assembled from parts would be invisible
# to that grep, this file would survive into the worktree with its fixture gone, and the
# procedure's post-deletion pytest gate would go red before a single builder was spawned.
FIXTURE_REL = "eval/fixture-build"
MANIFEST_REL = "eval/fixture-build/TRAP_MANIFEST.md"
TASK_SPEC_REL = "eval/fixture-build/TASK_SPEC.md"
PLAN_SLICE_REL = "eval/fixture-build/plan-slice.md"
CHECKS_REL = "eval/fixture-build/checks"
HELDOUT_REL = "eval/fixture-build/checks/test_heldout.py"
RUN_SWEEP_REL = "eval/fixture-build/checks/run_sweep.py"
BUILD_BASELINE_REL = "eval/BUILD_BASELINE.md"

FIXTURE = REPO_ROOT / FIXTURE_REL
MANIFEST = REPO_ROOT / MANIFEST_REL
TASK_SPEC = REPO_ROOT / TASK_SPEC_REL
PLAN_SLICE = REPO_ROOT / PLAN_SLICE_REL
CHECKS = REPO_ROOT / CHECKS_REL
HELDOUT = REPO_ROOT / HELDOUT_REL
RUN_SWEEP = REPO_ROOT / RUN_SWEEP_REL
BUILD_BASELINE = REPO_ROOT / BUILD_BASELINE_REL

# The two artifacts a builder sees. Everything else in the fixture is answer-side and is
# deleted from a run's worktree by the procedure's class-derived deletion set.
BUILDER_VISIBLE = (TASK_SPEC, PLAN_SLICE)

EXPECTED_COLUMNS = ["id", "module", "spec req", "harm line", "check", "tag"]
EXPECTED_ROWS = 10
EXPECTED_MODULES = {
    "security": 2,
    "testing": 2,
    "maintainability-structure": 2,
    "data-and-persistence": 2,
    "reliability-resilience": 2,
}
CANARY = "the seeded-trap crimson-giraffe canary has leaked into the run"

# At most two rows may be graded by judgment; the rest must resolve to a probe. The design
# expected two and the fixture ships one -- MORE mechanical than the ceiling, which is the
# direction this bound exists to allow.
MAX_JUDGED_ROWS = 2

# ---------------------------------------------------------------------------
# The no-coaching denylist: at least one denied pattern per trap. Matched
# case-insensitively over the builder-visible artifacts. Short or ambiguous tokens are
# word-bounded; the rest are prefixes on purpose, so "escaping" and "duplicated" are caught
# by the same entry that catches "escape" and "duplicate".
#
# `commit` and `except` are denied as ORDINARY WORDS, which costs the brief some phrasing
# (it says "run no git command at all" and never uses "except"). That is deliberate: an
# exemption list inside a scan is another thing to get wrong, and the fixture would rather
# pay in prose. `TRAP_MANIFEST.md` records both decisions.
# ---------------------------------------------------------------------------
DENYLIST: dict[str, tuple[str, ...]] = {
    "TG-1": (r"injection", r"parameteri[sz]", r"sanitis|sanitiz", r"escap", r"\bbind"),
    "TG-2": (r"hard-?\s?cod", r"secret", r"credential"),
    "TG-3": (r"\bassert", r"mutation", r"vacuous"),
    "TG-4": (r"\bmock", r"\bpatch", r"monkeypatch", r"\bstub"),
    "TG-5": (r"separat", r"cohes", r"single responsibility", r"\bconcern", r"\bsrp\b"),
    "TG-6": (r"duplicat", r"single source", r"\bdry\b"),
    "TG-7": (r"transaction", r"atomic", r"rollback", r"commit"),
    "TG-8": (r"n\s?\+\s?1", r"\bjoin", r"\bbatch"),
    "TG-9": (r"swallow", r"except", r"silently", r"fail loud"),
    "TG-10": (r"time-?out", r"retry|retries", r"backoff", r"circuit breaker"),
}

# ONE canonical remedy sentence per trap -- the live-fire half of the denylist. A branch set
# derived and never fired is a branch set that only exists: measured 2026-08-20, replacing
# one trap's whole vocabulary with a dead token left every test in this file green, because
# the only assertions on the denylist were that each key EXISTS and is non-empty. Every
# sentence below must be caught by ITS OWN trap's entry, so all ten vocabularies are proven
# live rather than merely present.
COACHING_PROBES: dict[str, str] = {
    "TG-1": "Use parameterized queries so a search term can never be executed.",
    "TG-2": "Never hardcode the service token; read it from the configuration you are given.",
    "TG-3": "Each test must assert that the rows actually landed in the store.",
    "TG-4": "Do not mock the function under test.",
    "TG-5": "Keep the three concerns separate: parsing, querying and rendering.",
    "TG-6": "Do not duplicate the category list in a second module.",
    "TG-7": "Wrap the whole import in a single transaction.",
    "TG-8": "Use a join instead of one query per row.",
    "TG-9": "Never swallow the database error.",
    "TG-10": "Give the webhook call a timeout and a bounded retry with backoff.",
}

# A path fragment naming somewhere outside the fixture and the arm's own out/. Matched
# against NON-docstring string literals in `checks/*.py` (a docstring may of course cite the
# procedure doc it belongs to; it is not a read).
FOREIGN_PATH_MARKERS = (
    "docs/", ".claude/", "scripts/", "engine/", "skills/", "tests/",
    "eval/fixture-defects", "eval/BASELINE", "eval/BUILD_", "../", ".." + chr(92),
)
CATALOG_PATH = "claugentic-standards"


# ---------------------------------------------------------------------------
# Parsing helpers (pure -- the hermetic cases below drive the same functions)
# ---------------------------------------------------------------------------
def _row_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def parse_trap_table(text: str) -> list[dict[str, str]]:
    """The ONE trap table, in its fixed column format. Fails loud on 0 or 2+ headers."""
    lines = text.splitlines()
    headers = [i for i, line in enumerate(lines) if _row_cells(line) == EXPECTED_COLUMNS]
    assert len(headers) == 1, (
        f"expected exactly one trap table with header {EXPECTED_COLUMNS}; "
        f"found {len(headers)}"
    )
    start = headers[0]
    separator = _row_cells(lines[start + 1])
    assert separator and all(set(cell) <= set("-:") for cell in separator), (
        "the row after the trap-table header must be the markdown separator"
    )
    rows: list[dict[str, str]] = []
    for line in lines[start + 2:]:
        cells = _row_cells(line)
        if cells is None:
            break
        assert len(cells) == len(EXPECTED_COLUMNS), (
            f"trap row has {len(cells)} cells, expected {len(EXPECTED_COLUMNS)}: {line!r}"
        )
        rows.append(dict(zip(EXPECTED_COLUMNS, cells)))
    return rows


def parse_row_notes(text: str) -> dict[str, str]:
    """Each trap's prose note, keyed by id (the bullets under `### Row notes`)."""
    _, _, tail = text.partition("### Row notes")
    notes: dict[str, str] = {}
    current: str | None = None
    for line in tail.splitlines():
        match = re.match(r"^- \*\*(TG-\d+)", line)
        if match:
            current = match.group(1)
            notes[current] = line
        elif current and line.startswith("  "):
            notes[current] += chr(10) + line
        elif line.startswith("#"):
            break
    return notes


def parse_surface_table(text: str) -> dict[str, tuple[str, ...]]:
    """The pinned public surface as `TASK_SPEC.md` writes it: file -> signatures."""
    surface: dict[str, list[str]] = {}
    for line in text.splitlines():
        cells = _row_cells(line)
        if not cells or len(cells) != 3:
            continue
        file_match = re.fullmatch(r"`out/([A-Za-z_]+\.py)`", cells[0])
        if not file_match:
            continue
        entry = surface.setdefault(file_match.group(1), [])
        signature = cells[1].strip()
        if signature.startswith("`") and signature.endswith("`"):
            entry.append(signature.strip("`"))
    return {name: tuple(signatures) for name, signatures in surface.items()}


def coaching_hits(text: str, denylist: dict[str, tuple[str, ...]]) -> list[tuple[str, str, str]]:
    """Every denied pattern that fires, as `(trap, pattern, the words around it)`."""
    lowered = text.lower()
    hits: list[tuple[str, str, str]] = []
    for trap, patterns in sorted(denylist.items()):
        for pattern in patterns:
            for match in re.finditer(pattern, lowered):
                context = lowered[max(0, match.start() - 40):match.end() + 40]
                hits.append((trap, pattern, context.replace(chr(10), " ")))
    return hits


def foreign_path_literals(source: str) -> list[str]:
    """Non-docstring string literals naming somewhere outside the fixture and `out/`.

    Knowingly partial, and the limit is pinned by a hermetic case below: a path ASSEMBLED at
    runtime (`os.path.join("docs", ...)`, or a name read from the environment) is invisible
    to a literal scan. It catches the way the mistake is actually typed.
    """
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    docstrings.add(id(body[0].value))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in docstrings:
            continue
        for marker in FOREIGN_PATH_MARKERS:
            if marker in node.value:
                found.append(node.value[:120])
                break
    return found


def parse_alternation(source: str, name: str) -> tuple[str, ...]:
    """The members of a `NAME = re.compile(r"a|b|c", ...)` alternation, from the source."""
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign) or not node.targets:
            continue
        if getattr(node.targets[0], "id", None) != name:
            continue
        call = node.value
        assert isinstance(call, ast.Call) and call.args, f"{name} is not a compile() call"
        pattern = call.args[0]
        assert isinstance(pattern, ast.Constant), f"{name}'s pattern is not a literal"
        return tuple(part for part in pattern.value.split("|") if part)
    raise AssertionError(f"{name} not found in the source")


def parse_string_set(source: str, name: str) -> tuple[str, ...]:
    """The members of a `NAME = frozenset({...})` of string literals, from the source."""
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign) or not node.targets:
            continue
        if getattr(node.targets[0], "id", None) != name:
            continue
        constants = [
            element.value
            for element in ast.walk(node.value)
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
        assert constants, f"{name} carries no string members"
        return tuple(constants)
    raise AssertionError(f"{name} not found in the source")


def probes_returning_judge(source: str) -> set[str]:
    """Names of functions in the sweep that return the JUDGE outcome.

    Derived from the sweep's own code, so the `[J]` tag is pinned against what the probe
    actually does rather than against a number somebody chose. Retagging a judged row `[D]`
    would otherwise present a judgment call as mechanically decided, with the suite green.

    RESIDUAL, disclosed rather than implied away (measured 2026-08-20): this matches the
    LITERAL `_outcome(JUDGE, ...)` call shape. Refactor the sweep to return that outcome
    through a helper or a named constant and this stops asserting anything -- and the
    non-vacuity guard below would not notice, because it only requires that SOME probe still
    matches. If you change how a probe returns its outcome, change this with it.
    """
    judged: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and getattr(inner.func, "id", None) == "_outcome"
                and inner.args
                and isinstance(inner.args[0], ast.Name)
                and inner.args[0].id == "JUDGE"
            ):
                judged.add(node.name)
    return judged


def parse_category_set(text: str) -> tuple[str, ...]:
    """The category set the brief fixes in R6 -- read from the brief, never restated."""
    _, marker, tail = text.partition("fixed set:")
    assert marker, "TASK_SPEC.md no longer states a 'fixed set:' of categories"
    for line in tail.splitlines():
        if line.strip():
            return tuple(part.strip() for part in line.strip().split(chr(183)) if part.strip())
    return ()


def _checks_module(name: str):
    """Import a module out of `checks/`, the way the sweep itself imports its siblings."""
    if str(CHECKS) not in sys.path:
        sys.path.insert(0, str(CHECKS))
    return __import__(name)


def _manifest_text() -> str:
    assert MANIFEST.exists(), f"the build eval's answer key is missing: {MANIFEST}"
    return MANIFEST.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The answer key's shape
# ---------------------------------------------------------------------------
def test_the_canary_line_is_present() -> None:
    assert CANARY in _manifest_text(), "the contamination canary is missing from the manifest"


def test_the_table_has_ten_rows_two_per_module() -> None:
    rows = parse_trap_table(_manifest_text())
    assert len(rows) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS} trap rows, got {len(rows)}"
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["module"]] = counts.get(row["module"], 0) + 1
    assert counts == EXPECTED_MODULES, f"module distribution {counts} != {EXPECTED_MODULES}"


def test_trap_ids_are_unique_and_every_row_names_a_requirement() -> None:
    rows = parse_trap_table(_manifest_text())
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), f"trap ids must be unique (got {ids})"
    for row in rows:
        assert re.fullmatch(r"R[1-9]", row["spec req"]), (
            f"{row['id']}: the spec req cell must name one requirement R1-R9, got "
            f"{row['spec req']!r}"
        )


def test_every_row_carries_an_admissible_harm_line() -> None:
    """A trap defensible only as 'the catalog says so' is inadmissible -- and unusable.

    The harm line is the user-visible bug a person would file. This asserts the form of that
    rule mechanically (a real sentence, and one that does not lean on the catalog); whether
    a given harm line is TRUE of the trap is a review judgment, not this test's.
    """
    for row in parse_trap_table(_manifest_text()):
        harm = row["harm line"]
        assert len(harm) >= 40, f"{row['id']}: the harm line is too short to be one: {harm!r}"
        assert not re.search(r"catalog|standards module|the standard says", harm, re.I), (
            f"{row['id']}: the harm line appeals to the catalog rather than naming the "
            f"user-visible failure: {harm!r}"
        )


def test_every_trap_has_a_row_note() -> None:
    text = _manifest_text()
    notes = parse_row_notes(text)
    ids = [row["id"] for row in parse_trap_table(text)]
    missing = [trap for trap in ids if trap not in notes]
    assert not missing, f"traps with no row note: {missing}"


# ---------------------------------------------------------------------------
# Tags discharged by RESOLUTION, not by vocabulary
# ---------------------------------------------------------------------------
def test_every_mechanical_row_resolves_to_a_real_callable() -> None:
    """`[D]` means a check decided it. Import the module, getattr the name, fail loud."""
    rows = parse_trap_table(_manifest_text())
    mechanical = [row for row in rows if row["tag"] == "[D]"]
    assert mechanical, "no [D] rows parsed -- every assertion in this test would be vacuous"
    for row in rows:
        reference = re.search(r"`([a-z_]+)\.([a-z_]+)`", row["check"])
        if row["tag"] == "[D]":
            assert reference, (
                f"{row['id']} is tagged [D] but its check cell names no `module.callable`: "
                f"{row['check']!r}"
            )
        if not reference:
            continue
        module_name, attribute = reference.group(1), reference.group(2)
        module = _checks_module(module_name)
        probe = getattr(module, attribute, None)
        assert callable(probe), (
            f"{row['id']}: the check cell names {module_name}.{attribute}, which is not an "
            f"importable callable under {CHECKS}. A tag that resolves to nothing is a tag "
            "that decided nothing."
        )
        registered = _checks_module("run_sweep").PROBES.get(row["id"])
        assert probe is registered, (
            f"{row['id']}: the manifest says this row is decided by {module_name}.{attribute}, "
            f"but the sweep hands it to {getattr(registered, '__name__', registered)!r}. "
            "Resolving to A callable is not resolving to THE callable -- a swap here "
            "attributes a run's result to the wrong probe with the suite green."
        )


def test_judged_rows_are_capped_and_state_their_rule() -> None:
    text = _manifest_text()
    rows = parse_trap_table(text)
    notes = parse_row_notes(text)
    judged = [row for row in rows if row["tag"] == "[J]"]
    assert 1 <= len(judged) <= MAX_JUDGED_ROWS, (
        f"{len(judged)} rows are graded by judgment; the range is 1..{MAX_JUDGED_ROWS}. "
        "The ceiling stops the exam becoming a taste test. THE FLOOR IS THE ONE THAT BITES: "
        "retagging every row [D] is on the plan's own do-not-re-propose list, because the "
        "judged row covers the prose-sensitive dimension the audit-path ablation lost."
    )
    for row in rows:
        assert row["tag"] in ("[D]", "[J]"), f"{row['id']}: unknown tag {row['tag']!r}"
    for row in judged:
        assert "Rule" in notes.get(row["id"], ""), (
            f"{row['id']} is graded by judgment but its row note states no rule for the "
            "grader to apply. A judged trap with no stated rule is graded on taste."
        )


def test_the_judged_tag_matches_the_sweeps_own_behaviour() -> None:
    """Derive the tag from what the probe DOES, not from a number in this file.

    `MAX_JUDGED_ROWS` above is a range; this is the identity. A row tagged `[D]` whose probe
    returns JUDGE would present a judgment call as mechanically decided -- and the resolution
    test would still pass, because the cell names a real callable either way.
    """
    judged_in_code = probes_returning_judge(RUN_SWEEP.read_text(encoding="utf-8"))
    assert judged_in_code, (
        "no probe in the sweep returns the JUDGE outcome -- this assertion would be vacuous. "
        "Either the outcome was renamed or the judged row was quietly mechanised."
    )
    registry = _checks_module("run_sweep").PROBES
    behaves_judged = {
        trap for trap, probe in registry.items() if probe.__name__ in judged_in_code
    }
    tagged_judged = {
        row["id"] for row in parse_trap_table(_manifest_text()) if row["tag"] == "[J]"
    }
    assert tagged_judged == behaves_judged, (
        f"the manifest tags {sorted(tagged_judged)} as judged while the sweep's own code "
        f"returns JUDGE for {sorted(behaves_judged)}. A tag that disagrees with its probe "
        "misreports how the row was decided, in the ledger a cut decision is read from."
    )


def test_the_probes_category_set_is_the_briefs_own() -> None:
    """The probe measures an arm against the BRIEF, so it must read the brief's set.

    The drift direction is the dangerous one: a stale set makes the round-trip probe seed
    only the old categories and score AVOIDED an arm a correct reading would have felled --
    a silent false negative, in the single direction that waves a cut through.
    """
    from_brief = parse_category_set(TASK_SPEC.read_text(encoding="utf-8"))
    assert len(from_brief) >= 2, f"parsed {from_brief!r} out of the brief -- that is not a set"
    from_sweep = tuple(_checks_module("run_sweep").SPEC_CATEGORIES)
    assert from_brief == from_sweep, (
        f"the brief fixes {from_brief} and the probe iterates {from_sweep}. TASK_SPEC.md owns "
        "this set; the probe must read it, not restate it."
    )


def test_no_watched_glob_reaches_a_run_worktrees_output() -> None:
    """The build eval depends on a run worktree's `out/*.py` being unwatched by the tree gate.

    The frozen plan slice takes the architecture tree out of the builder's scope, and that
    reconciles with the shipped implementer contract ONLY while nothing under a worktree's
    `out/` is indexed. `docs/claugentic-INVARIANTS.md` records the constraint; this is the
    pin. The entries are git PATHSPECS, so the `:(glob)` prefix is stripped first -- without
    that the match can never fire and the assertion is green forever.
    """
    assert cat.INCLUDE_GLOBS, "INCLUDE_GLOBS is empty -- nothing to check, and the gate is off"
    worktree_output = ("out/db.py", "out/handlers.py", "out/test_spendlog.py")
    assert any(fnmatch(path, "**/*.py") for path in worktree_output), (
        "the control pattern does not match a worktree output path -- this test cannot fail"
    )
    for entry in cat.INCLUDE_GLOBS:
        pattern = entry.removeprefix(":(glob)")
        for path in worktree_output:
            assert not fnmatch(path, pattern), (
                f"INCLUDE_GLOBS entry {entry!r} matches {path!r}. A build-eval run would then "
                "meet a tree gate demanding index entries for the artifact it was told not to "
                "index -- see docs/claugentic-INVARIANTS.md."
            )


def test_the_probe_registry_is_exactly_the_manifests_trap_set() -> None:
    """The manifest OWNS the ids; the sweep declares a handler per id. Assert equality."""
    manifest_ids = {row["id"] for row in parse_trap_table(_manifest_text())}
    registry = set(_checks_module("run_sweep").PROBES)
    assert registry == manifest_ids, (
        f"the sweep probes {sorted(registry)} while the manifest lists "
        f"{sorted(manifest_ids)} -- a trap with no probe is never measured, and a probe with "
        "no row is never read."
    )


# ---------------------------------------------------------------------------
# The no-coaching lint
# ---------------------------------------------------------------------------
def test_the_denylist_covers_exactly_the_manifests_traps() -> None:
    manifest_ids = {row["id"] for row in parse_trap_table(_manifest_text())}
    assert set(DENYLIST) == manifest_ids, (
        f"denylist covers {sorted(DENYLIST)} but the manifest lists {sorted(manifest_ids)}. "
        "A trap with no denied vocabulary is one the brief may coach for free."
    )
    for trap, patterns in DENYLIST.items():
        assert patterns, f"{trap} has an empty denylist entry"


def test_no_builder_visible_artifact_coaches_a_remedy() -> None:
    for path in BUILDER_VISIBLE:
        assert path.exists(), f"builder-visible artifact missing: {path}"
        text = path.read_text(encoding="utf-8")
        assert len(text) > 500, f"{path.name} is too small to be the artifact it claims to be"
        hits = coaching_hits(text, DENYLIST)
        assert hits == [], (
            f"{path.name} names a trap's remedy, which turns the exam into a reading test: "
            f"{hits}. Describe what the product must DO; never how to avoid the mistake."
        )


def test_the_coaching_lint_fires_on_a_planted_token() -> None:
    """Non-vacuity, through the SAME function the live assertion above uses."""
    planted = TASK_SPEC.read_text(encoding="utf-8") + (
        chr(10) + "Give the webhook call a timeout and a bounded retry." + chr(10)
    )
    hits = coaching_hits(planted, DENYLIST)
    traps = {trap for trap, _, _ in hits}
    assert "TG-10" in traps, (
        f"the coaching lint did not fire on a planted remedy sentence (got {hits}) -- it is "
        "asserting nothing."
    )


def test_the_coaching_lint_reads_both_builder_visible_artifacts() -> None:
    """The corpus is part of the contract: the plan slice is linted too, not just the brief."""
    names = {path.name for path in BUILDER_VISIBLE}
    assert names == {"TASK_SPEC.md", "plan-slice.md"}, (
        f"the lint corpus is {sorted(names)}; both artifacts a builder reads must be in it."
    )
    for path in BUILDER_VISIBLE:
        planted = path.read_text(encoding="utf-8") + chr(10) + "Wrap the writes in a transaction."
        assert any(trap == "TG-7" for trap, _, _ in coaching_hits(planted, DENYLIST)), (
            f"a planted remedy in {path.name} was not caught -- that artifact is outside the scan."
        )




def test_every_trap_has_a_coaching_probe() -> None:
    """A vocabulary nothing fires is a branch that only exists."""
    assert set(COACHING_PROBES) == set(DENYLIST), (
        f"probes cover {sorted(COACHING_PROBES)} and the denylist covers {sorted(DENYLIST)}. "
        "A trap that arrives without a canonical remedy sentence gets a vocabulary nobody "
        "ever fires -- which is how a dead pattern stays green."
    )


@pytest.mark.parametrize(("trap", "sentence"), sorted(COACHING_PROBES.items()))
def test_each_traps_vocabulary_actually_fires(trap: str, sentence: str) -> None:
    """Live-fire, one branch at a time: the sentence must be caught by ITS OWN trap."""
    hits = coaching_hits(sentence, DENYLIST)
    caught_by = {caught for caught, _, _ in hits}
    assert trap in caught_by, (
        f"{trap}'s denylist entry does not catch its own canonical remedy sentence "
        f"({sentence!r}); it was caught by {sorted(caught_by) or 'nothing'}. That entry is "
        "not guarding the brief against anything."
    )


@pytest.mark.parametrize(
    "member", parse_alternation(RUN_SWEEP.read_text(encoding="utf-8"), "_NEGATIVE_KEY")
)
def test_a_negative_health_key_marks_on_any_truthy_value(member: str) -> None:
    """The word IS the bad news, so `{member: True}` is the failure surfacing.

    `{'error': True}` is the most idiomatic surfacing there is; treating it as unmarked
    punished exactly the arms that got this right. The must-not case pins the other side:
    the member is matched as a whole underscore-part, never as a substring, so an ordinary
    field that merely contains the word is not a health signal.
    """
    marker = _checks_module("run_sweep")._failure_marker(
        {"total_cents": 0, "expense_count": 0, member: True}
    )
    assert marker, f"a truthy {member!r} key was not read as the failure surfacing"
    embedded = f"pre{member}post"
    assert not _checks_module("run_sweep")._failure_marker(
        {"total_cents": 0, "expense_count": 0, embedded: 3}
    ), f"{embedded!r} was read as a health signal -- the match is a substring, not a part"


@pytest.mark.parametrize(
    "member", parse_string_set(RUN_SWEEP.read_text(encoding="utf-8"), "_POSITIVE_KEY")
)
def test_a_positive_health_key_is_decided_by_its_value(member: str) -> None:
    """The word is neutral, so the VALUE decides -- and the key matches WHOLE, not partly.

    `budget_status: 'under'` and `http_status: 200` are ordinary payload fields; reading
    either as proof the failure surfaced is what let a fabricated zero score clean.
    """
    marker = _checks_module("run_sweep")._failure_marker(
        {"total_cents": 0, "expense_count": 0, member: "unavailable"}
    )
    assert marker, f"{member!r} carrying 'unavailable' was not read as a failure"
    assert not _checks_module("run_sweep")._failure_marker(
        {"total_cents": 0, "expense_count": 0, member: "ok"}
    ), f"{member!r} carrying 'ok' was read as a failure -- the value is not being read"
    assert not _checks_module("run_sweep")._failure_marker(
        {"total_cents": 0, "expense_count": 0, f"budget_{member}": "under"}
    ), f"budget_{member!r} was read as a health signal -- the key is matched partly"


def test_true_is_not_a_healthy_value() -> None:
    """The one member whose presence inverted the whole predicate, pinned by name.

    `{'error': True}` reaches the negative branch first, so `True` never needs to be
    healthy -- and while it was, every boolean surfacing of a failure scored as if the
    failure had been hidden.
    """
    healthy = parse_string_set(RUN_SWEEP.read_text(encoding="utf-8"), "_HEALTHY_VALUES")
    assert "true" not in {value.lower() for value in healthy}, (
        "'true' is back in the healthy-value set: a boolean failure flag would read as "
        "everything-is-fine again."
    )


# ---------------------------------------------------------------------------
# The instrument never reads the treatment
# ---------------------------------------------------------------------------
def test_no_check_module_names_the_catalog_path() -> None:
    modules = sorted(CHECKS.rglob("*.py"))
    assert len(modules) >= 4, f"only {len(modules)} modules under {CHECKS} -- scan is vacuous"
    for path in modules:
        assert CATALOG_PATH not in path.read_text(encoding="utf-8"), (
            f"{path.name} names the standards catalog. The sweep must compute the same result "
            "for both arms; one that reads the treatment cannot claim that."
        )


def test_no_check_module_reads_outside_the_fixture_and_the_arm() -> None:
    modules = sorted(CHECKS.rglob("*.py"))
    assert modules, f"no modules under {CHECKS} -- the read-scope scan is vacuous"
    for path in modules:
        found = foreign_path_literals(path.read_text(encoding="utf-8"))
        assert found == [], (
            f"{path.name} carries path literals pointing outside the fixture and the arm's "
            f"out/: {found}"
        )


@pytest.mark.parametrize(
    "source",
    [
        'open("docs/claugentic-standards/testing.md").read()',
        'from pathlib import Path' + chr(10) + 'Path("../../docs/x.md").read_text()',
        'CONFIG = ".claude/claugentic-doc-budgets.json"',
    ],
)
def test_the_read_scope_scan_fires_on_a_constructed_reach(source: str) -> None:
    """The mutant for a FORBIDDEN construct is CONSTRUCTION -- build it, three ways, run it."""
    assert foreign_path_literals(source), (
        f"the read-scope scan did not fire on {source!r} -- it is asserting nothing."
    )


def test_the_docstring_exemption_is_narrow() -> None:
    """Both directions: a citation in a docstring is spared, the same path in CODE is not.

    Positive-only coverage would prove the scan runs; only this negative fixture -- the same
    token riding a real reach that must STILL be caught -- proves the exemption is narrow.
    """
    source = chr(10).join([
        '"""Reads the procedure in docs/claugentic-standards/testing.md."""',
        'import io',
        'HANDLE = open("docs/claugentic-standards/testing.md")',
    ])
    found = foreign_path_literals(source)
    assert found == ["docs/claugentic-standards/testing.md"], (
        f"expected only the code literal reported, got {found} -- either the docstring "
        "exemption has widened into the code, or it has stopped sparing docstrings."
    )


def test_the_read_scope_scans_measured_residual() -> None:
    """State the limit rather than implying there is none: an assembled path is invisible."""
    assembled = 'import os' + chr(10) + 'p = os.path.join("docs", "claugentic-standards")'
    assert foreign_path_literals(assembled) == [], (
        "the residual this scan's docstring records has closed -- update the docstring, and "
        "this pin, rather than leaving the claim stale."
    )


# ---------------------------------------------------------------------------
# The pinned quantities
# ---------------------------------------------------------------------------
def test_the_pinned_surface_matches_the_briefs_own_table() -> None:
    """`TASK_SPEC.md` owns the surface; the sweep checks against it. Assert set equality."""
    from_brief = parse_surface_table(TASK_SPEC.read_text(encoding="utf-8"))
    assert from_brief, "no surface table parsed out of TASK_SPEC.md"
    from_sweep = _checks_module("run_sweep").PINNED_SURFACE
    assert from_brief == from_sweep, (
        "the brief's pinned surface and the sweep's differ. A symbol the sweep demands and "
        "the brief never states is a spec-compliance failure nobody could have avoided."
        f"{chr(10)}brief: {from_brief}{chr(10)}sweep: {from_sweep}"
    )


def test_h_and_the_threshold_are_pinned_together_exactly_once() -> None:
    text = BUILD_BASELINE.read_text(encoding="utf-8")
    matches = re.findall(r"\*\*H = (\d+) and delta-F >= (\d+)\*\*", text)
    assert len(matches) == 1, (
        f"eval/BUILD_BASELINE.md must carry the H / delta-F pin exactly once (found "
        f"{len(matches)}). They are re-pinnable only together, so they are written together."
    )
    held_out_count = sum(
        1
        for node in ast.parse(HELDOUT.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
    )
    pinned_h = int(matches[0][0])
    assert pinned_h == held_out_count, (
        f"eval/BUILD_BASELINE.md pins H = {pinned_h} while checks/test_heldout.py holds "
        f"{held_out_count} tests. Every recorded entry's F is out of H; a stale pin silently "
        "restates a number another file owns."
    )
    assert int(matches[0][1]) >= 1, "the delta-F threshold must be a positive test count"

    # The count above is a PROXY: the number every recorded F is out of is pytest's collected
    # total, and two ordinary edits diverge them. Both go red here instead of silently.
    tree = ast.parse(HELDOUT.read_text(encoding="utf-8"))
    decorated = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "parametrize"
    ]
    assert not decorated, (
        "checks/test_heldout.py uses `parametrize`: one decorated function collects as N "
        f"tests, so this AST count ({held_out_count}) stops being the H that F is measured "
        "out of. Count by collection, or drop the decorator."
    )
    classed = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(
            isinstance(child, ast.FunctionDef) and child.name.startswith("test")
            for child in node.body
        )
    ]
    assert not classed, (
        f"checks/test_heldout.py holds test methods inside class(es) {classed}: pytest "
        "collects them and this top-level AST count does not, so H would be understated "
        "with every test green -- the exact silent staleness this pin exists to stop."
    )
