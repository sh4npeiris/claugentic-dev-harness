#!/usr/bin/env python3
"""Scan every SHIPPED file's TEXT for forbidden literals (deterministic, no LLM).

The release/init contract (docs/claugentic-INVARIANTS.md → "The release strips ⇒
init recreates ⇒ nothing shipped dangles") was pinned only at *membership* level
(`tests/test_build_release.py::TestReleaseInitContract`) — set ship-vs-strip. That
leaves a content gap: a roster rename can strand a live `claugentic-dev-harness:<old-role>`
spawn literal in a shipped SKILL, or a shipped doc can point an adopter at a file the
release strips and `init` never recreates — both with every harness-self test green.
This gate closes that gap by reading the shipped-file TEXT directly. It unifies two
deferred items into ONE DRY gate (sibling, not extension — see DECISIONS "one gate,
one invariant"): the content-grep guard (plan 0027 S3) + the namespace presence-scan
(plan 0026 §C3a) are the *same shape* — a scan over shipped-file text for a forbidden
literal.

SHIP source-of-truth: this gate `import build_release as br` and takes
`SHIP = set(br.classify(br._tracked_files())[0])` — the SINGLE ship classifier. That
import is legitimate (and does NOT violate the "a copied adopter gate can't import the
release tooling" rule): this gate is HARNESS-SELF, it reasons ABOUT the shipped tree,
and it is itself stripped from the release (DEV_ONLY_FILES) — it never runs in an
adopter repo, so there is no copied-gate to strand.

FIVE passes (four over the shipped-file texts + one over the strip manifest). The four
text passes' pure cores take an injected `{path: text}` map so they are hermetically
testable without git; the manifest pass (Pass D) is pure over `build_release`'s classes:

  Pass D — referential closure (HARD, exit 1). Assert `NEEDS ⊆ HAS`: every STRIPPED,
    adopter-relevant path is producible/recreatable via its recreate-class's HAS source, so
    the release/init contract (docs/claugentic-INVARIANTS.md → "release strips ⇒ init
    recreates ⇒ nothing dangles") is pinned MECHANICALLY, not by prose alone. NEEDS = the
    stripped adopter-relevant classes (`init-seed` ∪ `init-gen` ∪ `recreate-on-demand` ∪
    `self-gate`); `config`/`dangle` are NOT adopter-relevant NEEDS (config = machinery no
    shipped doc points at; dangle = stripped AND never recreated, correctly — the
    RELEASE_CHECKLIST class). FOUR HAS sources, one per NEEDS class:
      * `init-seed`          → its `_X.md` seed is in the SHIPPED set (init copies it back).
      * `init-gen`           → the path is a KNOWN init generator output (INIT_GEN_OUTPUTS).
      * `recreate-on-demand` → THE CLASS IS ITS OWN HAS ATTESTATION — its members are BY
                               DESIGN not init-produced (workflow-lazy / agent-authored /
                               user-authored); the closure ACCEPTS them via the class, it does
                               NOT hard-require init-producibility for them.
      * `self-gate`          → the harness-self script is stripped AND self-consistent (no
                               shipped file references it as a needed artifact — Pass A.a/A.b
                               already guard shipped-text mentions; here we assert the ship/strip
                               status is coherent: the script is genuinely stripped).
    HONESTY: the pinned claim is "producible by init OR the workflow's lazy/templated/agent
    authoring" — NEVER "producible by init" flatly (recreate-on-demand files are NOT
    init-produced). The gate pins the INVARIANT (referential closure), NOT that the release is
    correct — it does not make the release "fully" content-enforced. Honors the `INCLUDE_GLOBS`
    never-clobber carve-out (the tree-script's adopter-owned glob region is excluded from NEEDS
    exactly as init's body-compare excludes it).

  Pass C — engine ASCII-only (HARD, exit 1). For each shipped `*.js` (= the 4
    Workflow-orchestrated `engine/*.js` scripts), flag any character whose codepoint is
    > U+007F (non-ASCII). EXACT and MECHANICAL — a deterministic codepoint check, no
    heuristic (distinct from Pass A.b's WARN heuristic). The engine scripts pass through
    arbitrary adopter permission/approval layers via the Workflow tool; a layer strict
    about non-ASCII silently demotes the engine to prose-fallback (the DistrictSync
    2026-06-25 validation), so ASCII-only source is a durable robustness guarantee. The
    existing cores operate on the UTF-8-DECODED `{path: text}` map, so this checks decoded
    codepoints > 0x7F (equivalent to "any byte > 0x7F" for non-ASCII detection, and
    consistent with the text-based cores). Reports the first offending line + codepoint so
    a regression is locatable.

  Pass B — namespace (HARD, exit 1). Regex `claugentic-dev-harness:([a-z-]+)` over all
    shipped markdown; flag any captured token NOT in the VALID set. The
    `claugentic-dev-harness:` prefix names BOTH agent-spawn ids AND slash-commands
    (`:audit`/`:build`/`:doctor`/`:init`/`:product`/`:update`), so VALID =
    agent basenames (.claude/agents/*.md) ∪ skill basenames (skills/*/) ∪ {"update"}.
    All three component sets are FS-DERIVED (except the documented `update`), so renames
    never strand the gate and nothing duplicates the node test's CUSTOM_AGENTS. Keying on
    the FULL `claugentic-dev-harness:` prefix structurally excludes the
    `<!-- product-critic:rejected-proposals -->` memory-fence HTML-comment tokens (they
    are `product-critic:...` WITHOUT the prefix) — that exclusion is a property of the
    regex, preserved deliberately.

  Pass A.a — dangling-path literals (HARD, exit 1). Flag a shipped reference to a
    stripped-AND-never-recreated path: `RELEASE_CHECKLIST.md` and a SPECIFIC numbered
    harness plan-file (`.claude/plans/<NNNN>-*.md`). The dangle set is DERIVED from
    `br.DEV_ONLY_FILES` minus the recreated set (init-seed ∪ init-gen ∪ recreate-on-demand),
    minus the harness-self gate scripts (those are Pass A.b's WARN concern, not a hard
    dangle — see below), minus the repo-config machinery no shipped doc points an adopter at
    — i.e. exactly the manifest's `dangle` class. All three subtracted sets are themselves
    derived from `build_release.recreate_class` (the ONE authored ship/strip manifest), so no
    hand-list is maintained here. The bare `.claude/plans/` *directory* is allow-listed (init
    manages the adopter's own in-flight-plans dir); the `NNNN`/placeholder plan-file form is
    allow-listed (it documents the naming convention, not a real file).

  Pass A.b — uncaveated harness-self-gate mention (WARN-only, exit 0 + a `WARN:` line).
    For each shipped mention of a harness-self gate SCRIPT NAME, WARN if no adopter-caveat
    marker appears within a bounded window (same line ± a few lines). This is honestly
    HEURISTIC — it can false-positive (a caveat phrased outside the window / with novel
    wording) and false-negative (a caveat near an UNcaveated second mention) — so it sits
    in the WARN band (printed, exit 0), like check_doc_budgets, NEVER a hard fail. An
    uncaveated gate-script PATH is routed here (WARN), not to Pass A.a (hard): the plan-0028
    decision is that gate-script mentions are heuristic/WARN, because they have legitimate
    caveated shipped uses (running the gate with a "skip in an adopter" note), unlike a true
    dangle which has no legitimate adopter use at all.

HONESTY (the #1 rule): this gate mechanically pins the EXACT cases (A.a dangling paths +
B stranded roster + C non-ASCII engine codepoints — C is an exact codepoint check, the
strongest/most mechanical of the passes — + D referential closure `NEEDS ⊆ HAS`, an exact
set-containment check over the manifest classes). A.b is WARN-heuristic. The gate is a
RUN-GATE (CI + the Definition-of-Done suite), NOT hook-wired — the one hook-enforced gate
stays the architecture-tree check. It does NOT make the release/init contract "fully
mechanically content-enforced": Pass D pins the referential-closure INVARIANT (every
stripped adopter-relevant path is recreatable via its class's HAS source — "producible by
init OR the workflow's lazy/templated/agent authoring", never "producible by init" flatly),
NOT that the release is CORRECT; the membership test + model-upheld review still complement it.

Fails LOUD: any git/read error produces a plain message + exit 1 — never a false-green
(a gate that silently passed because git broke would defeat its own purpose).

Modes:
    python scripts/check_shipped_content.py                 # scan the current dev checkout
    python scripts/check_shipped_content.py --root <tree>   # scan an explicitly-given tree

`--root <tree>` scans the shipped content of a GIVEN tree instead of the current checkout — used
by `build_release.py --apply` to validate the BUILT (already-stripped) release worktree BEFORE it
commits (plan 0034 Slice 5 / P0-2). The scanner still runs FROM the dev checkout (its `import
build_release` + its own code are stripped from the built tree), pointing only its FS/git reads at
`<tree>`. The ship set is then the files present under `<tree>` — since the built tree is already
stripped, those ARE the shipped files, so the dangling-ref (A.a), stranded-token (B), engine
ASCII-only (C), and closure (D) passes run against exactly the release's shipped structure. Honest
scope: this validates the SHIPPED STRUCTURE of the built tree — NOT that the release "passes CI" or
"is correct." No `--root` ⇒ exactly the prior scan of the dev checkout (byte-identical behavior).

Exit 0 OK / exit 1 on any hard problem (or a git/FS boundary failure — never a false green).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import build_release as br  # the SINGLE ship classifier — see module docstring

# ─────────────────────────────────────────────────────────────────────────────
# Binary shipped assets — SKIPPED from the text scan (see `_read_shipped_texts`)
# ─────────────────────────────────────────────────────────────────────────────
# A shipped file whose lowercased suffix is in this denylist is a legitimate BINARY asset
# (an image / font / archive — e.g. the README's `docs/diagrams/*.png` flow diagrams). It has
# no TEXT for any pass to scan (all four text passes operate on decoded `{path: text}`), so it
# is skipped from the text map rather than UTF-8-decoded (a PNG's `0x89` magic byte is not valid
# UTF-8 and would fail-loud). The skip is by KNOWN-BINARY EXTENSION ONLY — a non-binary-extension
# file that fails to decode is genuine corruption and STILL fails loud (see `_read_shipped_texts`).
BINARY_EXTENSIONS = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp",  # images
        ".pdf", ".zip", ".gz", ".tar",                              # docs / archives
        ".woff", ".woff2", ".ttf", ".otf", ".eot",                 # fonts
        ".mp4", ".mov", ".mp3", ".wav",                            # media
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# Pass B — namespace VALID-set sources
# ─────────────────────────────────────────────────────────────────────────────
# The `claugentic-dev-harness:<token>` namespace. Capture only `[a-z-]+` so the full
# `claugentic-dev-harness:` prefix is REQUIRED — that requirement is what excludes the
# `<!-- product-critic:rejected-proposals -->` memory-fence tokens (they lack the prefix).
NAMESPACE_RE = re.compile(r"claugentic-dev-harness:([a-z-]+)")

# A single prose-only namespace token with NO backing FS directory: `:update` is the
# update slash-command, documented in skills/init/SKILL.md, but there is no `skills/update/`
# dir (it is provided by the plugin runtime, not a bundled skill). It is the ONE hardcoded
# addition to the otherwise FS-derived VALID set — kept here, commented, so it is an explicit
# seam, not the gate silently guessing.
PROSE_ONLY_TOKENS = frozenset({"update"})


# ─────────────────────────────────────────────────────────────────────────────
# Pass A — dangling-path + harness-self-gate-script sources
# (DERIVED from build_release's `recreate_class` — the ONE authored ship/strip manifest)
# ─────────────────────────────────────────────────────────────────────────────
# These three partitions of the strip set used to be re-hand-maintained here (0034 Slice 2
# DRY'd them off `build_release.DEV_ONLY_PATH_CLASSES`). Adding one dev-only doc that init
# recreates is now ONE edit — the class annotation in the manifest — with these sets and the
# dangle derivation following automatically. `_paths_in_classes` buckets the manifest by
# `br.recreate_class`, so the manifest is the single source of the ship/strip semantics.


def _paths_in_classes(*classes: str) -> frozenset[str]:
    """The dev-only FILE paths whose `recreate_class` is any of `classes` (manifest-derived).

    Reads `build_release.recreate_class` over `DEV_ONLY_FILES` — the single authored
    `path -> class` manifest — so a strip-rule change re-derives these partitions with no
    edit here. Dir-swept paths (`DEV_ONLY_DIRS`) have no class and never appear.
    """
    wanted = set(classes)
    return frozenset(p for p in br.DEV_ONLY_FILES if br.recreate_class(p) in wanted)


# Files an adopter gets back via a NON-dangling mechanism — a shipped mention of one is NOT a
# dangle (the adopter HAS/recreates the file). The union of the three recreate-classes:
# `init-seed` (init copies a `_X.md` seed) + `init-gen` (init generates it) +
# `recreate-on-demand` (a non-init mechanism creates it: workflow lazy-create / agent-authored
# / user-from-template). This REPLACES the old `_INIT_CREATES` hand-list, which conflated
# init-produced with recreate-on-demand and carried a phantom `docs/claugentic-CHARTER.md`
# entry (never a tracked/stripped file, so a no-op subtraction) — the derivation drops it.
_RECREATED = _paths_in_classes("init-seed", "init-gen", "recreate-on-demand")

# Harness-self gate scripts: stripped from the release, but their CAVEATED mentions are
# Pass A.b's (WARN) concern, not Pass A.a's (hard dangle). A.a SUBTRACTS them from its dangle
# set and A.b scans exactly them. `build_release.py` is the release builder; the rest are
# run-gates. (Class `self-gate` in the manifest — DERIVED, was a hand-list.)
HARNESS_SELF_SCRIPTS = _paths_in_classes("self-gate")

# Repo-config / dev-infra files: stripped machinery — no shipped DOC points an adopter AT them
# as a path-to-open, so they are not the A.a dangle class. Subtracted from the derived dangle
# set. (Class `config` in the manifest — DERIVED, was the `_DANGLE_EXCLUDED` hand-list.)
_DANGLE_EXCLUDED = _paths_in_classes("config")

# A SPECIFIC numbered harness plan file (e.g. `.claude/plans/0027-foo.md`). The whole
# `.claude/plans/` subtree is DEV_ONLY (stripped), so a shipped doc citing a numbered plan
# file would dangle. The bare `.claude/plans/` DIRECTORY is intentionally NOT matched (init
# manages the adopter's own in-flight-plans dir — a legitimate reference); neither is the
# `NNNN`/`<slug>` placeholder form (it documents the naming convention, not a real file).
# Matching literal `\d{4}` (never `NNNN`) encodes exactly that distinction.
NUMBERED_PLAN_RE = re.compile(r"\.claude/plans/\d{4}-[^\s)`'\"]+\.md")


# Adopter-caveat markers (Pass A.b): any one near a gate-script mention clears the WARN.
# Heuristic by design — documented false-pos/neg in the module docstring.
CAVEAT_MARKERS = (
    "harness-self",
    "skip in an adopter",
    "n-a in an adopter",
    "not shipped",
    "isn't shipped",
    "stripped from the release",
)

# Pass A.b window: a caveat within this many lines above/below the mention (same paragraph,
# roughly) clears the WARN. Bounded so a far-away caveat cannot mask an uncaveated mention.
CAVEAT_WINDOW = 3


def dangling_paths() -> frozenset[str]:
    """The Pass A.a hard-forbidden path set, DERIVED from build_release's strip rules.

    `DEV_ONLY_FILES` minus the recreated set, minus the harness-self gate scripts (A.b's
    concern), minus the repo-config machinery — leaving exactly the stripped-AND-never-
    recreated, adopter-facing dangle files (today: `docs/RELEASE_CHECKLIST.md`; i.e. the
    `dangle` class). Each subtracted set is itself manifest-derived (`recreate_class`), so a
    future strip-rule change keeps the gate correct with no edit here — the manifest is the
    single source. Equivalently: the `dangle`-class members.
    """
    return frozenset(
        br.DEV_ONLY_FILES - _RECREATED - HARNESS_SELF_SCRIPTS - _DANGLE_EXCLUDED
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pass D — referential-closure HAS sources (DERIVED from the manifest classes)
# ─────────────────────────────────────────────────────────────────────────────
# The `init-seed` recreation convention: init copies a pristine `docs/claugentic-_X.md` seed
# → `docs/claugentic-X.md` (the seed inserts `_` after the `claugentic-` managed-doc prefix,
# create-if-absent — skills/init/SKILL.md step 7). So the HAS attestation for a stripped
# `docs/claugentic-X.md` is: its `claugentic-_X.md` SEED is in the shipped set. This helper
# encodes that ONE naming convention, so a new init-seed doc needs no edit here.
MANAGED_DOC_PREFIX = "claugentic-"


def _init_seed_of(path: str) -> str:
    """The shipped seed path init copies to recreate a stripped `init-seed` `path`.

    Encodes the seed-naming convention: `docs/claugentic-DECISIONS.md` →
    `docs/claugentic-_DECISIONS.md` (a `_` inserted AFTER the `claugentic-` managed-doc prefix
    in the basename). The seed being in the shipped set is the `init-seed` HAS attestation
    (init copies it back, underscore-stripped, per skills/init/SKILL.md step 7).
    """
    p = Path(path)
    name = p.name
    if name.startswith(MANAGED_DOC_PREFIX):
        name = MANAGED_DOC_PREFIX + "_" + name[len(MANAGED_DOC_PREFIX) :]
    else:  # a non-managed-prefixed init-seed doc would prefix `_` to the whole basename
        name = "_" + name
    return str(p.with_name(name)).replace("\\", "/")


# Known init GENERATOR outputs (the `init-gen` HAS source): paths init writes from scratch in
# the adopter repo rather than copying from a seed (skills/init/SKILL.md step 4 generates the
# architecture tree). An explicit, commented seam — the gate does not guess which stripped file
# init can regenerate; a new init-gen output is registered here alongside its manifest class.
INIT_GEN_OUTPUTS = frozenset(
    {
        "docs/claugentic-ARCHITECTURE_TREE.md",  # init step 4 generates the adopter's file map
        # The adopter's OWN doc-budget caps, generated from THEIR ledgers — never the harness's
        # harness-tuned numbers (which is exactly why the harness's own config is stripped).
        # HONEST STATUS — registered AHEAD of its writer: the caps config is classed `init-gen`
        # by plan 0041 Slice 4 (the slice that creates and strips the harness's own config),
        # while the `init` step that writes an adopter's copy is Slice 7 of the SAME plan. No
        # release is PLANNED between them — that is plan ORDER, model-upheld; nothing here
        # gates it and Pass D accepts this entry unconditionally. Until Slice 7 lands, this
        # entry states the INTENDED HAS source rather than an implemented one.
        # If that promise is not kept — Slice 7 abandoned, OR a release cut before it lands —
        # the honest fix is to re-annotate the class as `recreate-on-demand` (the shipped docs
        # already tell an adopter how to author the file by hand), never to leave this claim
        # standing. `test_init_documents_the_caps_config` (strict xfail) is the tripwire: it
        # turns the suite RED the moment init learns to write the config, forcing this note and
        # its sibling in `build_release.py` to be removed rather than quietly outliving it.
        ".claude/claugentic-doc-budgets.json",
    }
)


def closure_gaps(ship: frozenset[str]) -> list[str]:
    """Pass D. Return problem lines for any stripped adopter-relevant path NOT in HAS.

    Pure over the manifest classes (`build_release.recreate_class`) + the injected shipped
    set `ship` — no git/FS, hermetically testable. Asserts `NEEDS ⊆ HAS`:

      NEEDS = the stripped adopter-relevant classes: `init-seed` ∪ `init-gen` ∪
              `recreate-on-demand` ∪ `self-gate`. `config`/`dangle` are excluded (not
              adopter-relevant NEEDS — see the module docstring).
      HAS   = per class: init-seed → the `_X.md` seed is in `ship`; init-gen → the path is a
              known INIT_GEN_OUTPUTS generator output; recreate-on-demand → the class IS its
              own attestation (accepted unconditionally — NOT init-producibility);
              self-gate → the script is genuinely stripped (its ship/strip status is
              self-consistent — `is_dev_only` is True, which every manifest key satisfies).

    A gap = a stripped NEEDS path whose HAS source cannot vouch for it (e.g. an init-seed doc
    whose `_X.md` seed was never shipped, or an init-gen output not registered as a generator
    output). That is a REAL latent release/init-contract break — fix the wiring (ship the seed
    / register the generator output / re-annotate the class), never weaken this check.

    INCLUDE_GLOBS carve-out (honored by construction): the tree-script's adopter-owned
    `INCLUDE_GLOBS = [ … ]` region is the ONE per-repo knob init writes/refreshes (init's
    body-compare excludes it — skills/init/SKILL.md). It lives in a SHIPPED file, and NEEDS is
    derived ONLY from stripped manifest classes, so the glob region is never a closure NEEDS —
    the carve-out is honored exactly as init's body-compare honors it (the region is excluded).
    """
    problems: list[str] = []
    for path in sorted(_paths_in_classes("init-seed")):
        seed = _init_seed_of(path)
        if seed not in ship:
            problems.append(
                f"{path}: `init-seed` class but its seed `{seed}` is NOT shipped — init cannot "
                f"recreate it, so the stripped path dangles for an adopter (ship the seed, or "
                f"re-annotate its recreate-class in build_release.DEV_ONLY_PATH_CLASSES)."
            )
    for path in sorted(_paths_in_classes("init-gen")):
        if path not in INIT_GEN_OUTPUTS:
            problems.append(
                f"{path}: `init-gen` class but it is NOT a known init generator output "
                f"(check_shipped_content.INIT_GEN_OUTPUTS) — init would not regenerate it, so the "
                f"stripped path dangles for an adopter (register the generator output, or "
                f"re-annotate its recreate-class in build_release.DEV_ONLY_PATH_CLASSES)."
            )
    # `recreate-on-demand`: the class IS its own HAS attestation — its members are BY DESIGN not
    # init-produced (workflow-lazy / agent-authored / user-authored). Accepted via the class; the
    # closure does NOT hard-require init-producibility for them (the plan-gate's taxonomy fix).
    #
    # `self-gate`: the script is stripped AND self-consistent. Every NEEDS path comes from the
    # manifest (so `is_dev_only` is True — it IS stripped); a shipped file mentioning one as a
    # needed artifact is Pass A.a/A.b's concern. Here the class is self-attesting: a stripped
    # harness-self script needs no adopter recreation (it never runs in an adopter repo). Both
    # classes are thus closed by construction — asserted below so the coverage is non-vacuous.
    for path in _paths_in_classes("recreate-on-demand", "self-gate"):
        if not br.is_dev_only(path):
            problems.append(
                f"{path}: classified `{br.recreate_class(path)}` but is NOT stripped — a NEEDS "
                f"path must be a genuine strip-manifest member (its ship/strip status is incoherent)."
            )
    return problems


def valid_roster(agent_basenames: set[str], skill_basenames: set[str]) -> frozenset[str]:
    """The Pass B VALID set: agent basenames ∪ skill basenames ∪ the prose-only tokens.

    Pure over its inputs so the FS listing can be stubbed in tests. The agent ids and the
    slash-command (= skill) ids share the one `claugentic-dev-harness:` namespace, so both
    must be valid; `{update}` is the documented prose-only command (no backing skill dir).
    """
    return frozenset(agent_basenames | skill_basenames | PROSE_ONLY_TOKENS)


# ─────────────────────────────────────────────────────────────────────────────
# Pure cores (over injected {path: text} maps — no git, hermetically testable)
# ─────────────────────────────────────────────────────────────────────────────
def scan_non_ascii_js(js_texts: dict[str, str]) -> list[str]:
    """Pass C. Return problem lines for any non-ASCII (codepoint > U+007F) char in a `*.js`.

    EXACT/mechanical — flags the first offending codepoint per file with its line number and
    `U+XXXX` value so a regression is diagnosable. Operates on the UTF-8-decoded text (the
    other cores' shape); for non-ASCII detection a decoded codepoint > 0x7F is equivalent to
    any raw byte > 0x7F.
    """
    problems: list[str] = []
    for path in sorted(js_texts):
        for lineno, line in enumerate(js_texts[path].splitlines(), start=1):
            offender = next((ch for ch in line if ord(ch) > 0x7F), None)
            if offender is not None:
                problems.append(
                    f"{path}:{lineno}: non-ASCII char `{offender}` (U+{ord(offender):04X}) "
                    f"— shipped engine `*.js` must be ASCII-only (>U+007F can be rejected by an "
                    f"adopter's permission layer, silently demoting the engine to prose-fallback)."
                )
                break  # first offender per file is enough to locate + fail the regression
    return problems


def scan_namespace(md_texts: dict[str, str], valid: frozenset[str]) -> list[str]:
    """Pass B. Return problem lines for any `claugentic-dev-harness:<token>` not in `valid`."""
    problems: list[str] = []
    for path in sorted(md_texts):
        for token in sorted(set(NAMESPACE_RE.findall(md_texts[path]))):
            if token not in valid:
                problems.append(
                    f"{path}: stranded namespace token `claugentic-dev-harness:{token}` "
                    f"— not a current agent/skill/command (a rename left this dangling)."
                )
    return problems


def scan_dangling(texts: dict[str, str], forbidden: frozenset[str]) -> list[str]:
    """Pass A.a. Return problem lines for any shipped reference to a dangling path.

    Two literal classes: the explicit `forbidden` filenames, and a numbered harness plan
    file. Matches on the basename for the forbidden files (so both `docs/RELEASE_CHECKLIST.md`
    and a bare `RELEASE_CHECKLIST.md` mention are caught) — these names are distinctive enough
    that a substring match is safe and the strong signal is wanted.
    """
    problems: list[str] = []
    forbidden_names = sorted({Path(p).name for p in forbidden})
    for path in sorted(texts):
        text = texts[path]
        for name in forbidden_names:
            if name in text:
                problems.append(
                    f"{path}: references `{name}`, which the release STRIPS and `init` never "
                    f"recreates — a dangling path for an adopter (point at a shipped file instead)."
                )
        if match := NUMBERED_PLAN_RE.search(text):
            problems.append(
                f"{path}: references the numbered harness plan file `{match.group(0)}` "
                f"(.claude/plans/ is stripped) — cite the bare dir or the plan TEMPLATE instead."
            )
    return problems


def _has_caveat_nearby(lines: list[str], idx: int) -> bool:
    """True if an adopter-caveat marker appears within CAVEAT_WINDOW lines of `lines[idx]`."""
    lo = max(0, idx - CAVEAT_WINDOW)
    hi = min(len(lines), idx + CAVEAT_WINDOW + 1)
    window = "\n".join(lines[lo:hi]).lower()
    return any(marker in window for marker in CAVEAT_MARKERS)


def scan_gate_caveats(texts: dict[str, str], scripts: frozenset[str]) -> list[str]:
    """Pass A.b (WARN). Return warning lines for any uncaveated harness-self-gate mention.

    A mention is the gate-script BASENAME (e.g. `check_versions_synced.py`); it is fine
    (no warning) iff a caveat marker sits within the bounded window. Heuristic — see the
    module docstring's honest false-pos/neg note. Never a hard problem.
    """
    warnings: list[str] = []
    names = sorted({Path(p).name for p in scripts})
    for path in sorted(texts):
        lines = texts[path].splitlines()
        for idx, line in enumerate(lines):
            for name in names:
                if name in line and not _has_caveat_nearby(lines, idx):
                    warnings.append(
                        f"{path}:{idx + 1}: mentions harness-self gate `{name}` with no "
                        f"adopter-caveat nearby — confirm it reads as harness-self / N-A in an "
                        f"adopter (heuristic; WARN-only)."
                    )
    return warnings


# ─────────────────────────────────────────────────────────────────────────────
# Git/FS boundary (fail-loud) + orchestration
# ─────────────────────────────────────────────────────────────────────────────
def _tracked_files(root: Path) -> list[str]:
    """Every tracked file under `root`, repo-relative + forward-slash normalized.

    Runs `git -C <root> ls-files` so the listing is anchored to the GIVEN tree, not the
    process cwd. For the dev checkout this is the full ship+strip tree; for a BUILT (already
    stripped) release worktree (the `--root <tmp>` case) it is only the shipped files that
    survive the strip — so `classify()` over it splits cleanly with an empty strip half.
    Fails LOUD (raises) if git is unavailable or `ls-files` errors — a gate that silently
    passed on a broken git boundary would be a false-green."""
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return [line.replace("\\", "/").strip() for line in out.splitlines() if line.strip()]


def _shipped_files(root: Path) -> list[str]:
    """The SHIP half of `root`'s classified tracked-file set — the single ship source-of-truth.

    Anchored to `root` (via `_tracked_files(root)`), so `--root <built-tree>` scans exactly the
    files present under that tree. For the default dev checkout `root` is the repo the scanner
    already `chdir`s into, so this is byte-identical to listing the current tree. Fails LOUD
    (raises) if git is unavailable or `ls-files` errors."""
    return list(br.classify(_tracked_files(root))[0])


def _read_shipped_texts(root: Path, ship: list[str]) -> dict[str, str]:
    """Read each shipped TEXT file's content (UTF-8) into the scan map.

    Known-binary shipped ASSETS (suffix in `BINARY_EXTENSIONS` — e.g. the README's
    `docs/diagrams/*.png` diagrams) are SKIPPED: they are legitimate shipped files with no text
    for any pass to scan, and UTF-8-decoding one (a PNG's `0x89` magic byte) would fail-loud.

    The fail-loud-on-read/decode-error contract holds for TEXT files (everything NOT in the
    binary denylist): a file in the ship set that cannot be read, or a non-binary-extension file
    whose bytes are not valid UTF-8 (genuine corruption), is a real problem — surfaced, never
    silently skipped. The skip is by KNOWN-BINARY EXTENSION ONLY, so real text corruption is
    never masked."""
    texts: dict[str, str] = {}
    for rel in ship:
        if Path(rel).suffix.lower() in BINARY_EXTENSIONS:
            continue  # binary asset — no text to scan (fail-loud stays for text files only)
        path = root / rel
        texts[rel] = path.read_text(encoding="utf-8")
    return texts


def _fs_agent_basenames(root: Path) -> set[str]:
    """Bundled agent ids = the basenames of `.claude/agents/*.md` (FS-derived)."""
    return {p.stem for p in (root / ".claude" / "agents").glob("*.md")}


def _fs_skill_basenames(root: Path) -> set[str]:
    """Bundled skill / slash-command ids = the directory names under `skills/` (FS-derived)."""
    return {p.name for p in (root / "skills").iterdir() if p.is_dir()}


def evaluate(root: Path) -> tuple[list[str], list[str], str]:
    """Return (problem_lines, warning_lines, success_summary). Empty problems == no breach.

    Reads the shipped tree ONCE, then runs the five passes. Markdown-only pass (B) filters
    to `*.md`; the JS-only pass (C) filters to `*.js`; the path passes (A.a/A.b) scan every
    shipped text; the closure pass (D) is pure over the strip manifest + the shipped SET.
    warning_lines (A.b) never change the exit code. Fails loud on the git/FS boundary (the
    caller surfaces the raise). `root` is the tree scanned — the dev checkout by default, or an
    explicitly-given built (stripped) release worktree via `--root` (see `main`).
    """
    ship = _shipped_files(root)
    texts = _read_shipped_texts(root, ship)
    md_texts = {p: t for p, t in texts.items() if p.endswith(".md")}
    js_texts = {p: t for p, t in texts.items() if p.endswith(".js")}

    valid = valid_roster(_fs_agent_basenames(root), _fs_skill_basenames(root))

    problems: list[str] = []
    problems += scan_non_ascii_js(js_texts)              # Pass C (engine *.js only)
    problems += scan_namespace(md_texts, valid)          # Pass B (markdown only)
    problems += scan_dangling(texts, dangling_paths())    # Pass A.a (all shipped text)
    problems += closure_gaps(frozenset(ship))            # Pass D (NEEDS ⊆ HAS, manifest)
    warnings = scan_gate_caveats(texts, HARNESS_SELF_SCRIPTS)  # Pass A.b (WARN)

    if problems:
        return (problems, warnings, "")
    summary = (
        f"OK: scanned {len(ship)} shipped files ({len(md_texts)} markdown, {len(js_texts)} js) "
        f"— no stranded namespace tokens, no dangling stripped-path references, "
        f"no non-ASCII in engine *.js, referential closure holds (NEEDS ⊆ HAS)."
    )
    return ([], warnings, summary)


def _repo_root() -> Path:
    """Repo root from THIS script's location (never the CWD), git-authoritative with a
    `<script_dir>/..` fallback — mirrors the sibling gate scripts so the tool is
    CWD-independent and portable (computed at runtime from `__file__`)."""
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return Path(out.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError):
        return here.parent  # convention: the script lives at <repo>/scripts/


def _force_utf8_output() -> None:
    """Emit stdout/stderr as UTF-8 so the em-dashes/back-ticks in messages survive on Windows
    (cp1252 stdout decoded as UTF-8 → mojibake). Guarded — a captured stream may lack
    `.reconfigure`. Mirrors the sibling gate scripts."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except (AttributeError, ValueError):
            pass


def _parse_root(argv: list[str]) -> Path | None:
    """The `--root <path>` value from `argv`, or `None` when the flag is absent (the default).

    Boundary-validated: `--root` with no following value, or a value that isn't a directory,
    fails LOUD (raises) — a garbled root would silently scan the wrong tree. `None` (flag
    absent) drives the byte-identical default: derive the root from `__file__` and `chdir` into
    it (the current dev checkout)."""
    if "--root" not in argv:
        return None
    i = argv.index("--root")
    if i + 1 >= len(argv):
        raise ValueError("--root requires a <path> argument (the tree to scan).")
    root = Path(argv[i + 1])
    if not root.is_dir():
        raise ValueError(f"--root {root} is not a directory — cannot scan a missing tree.")
    return root


def main(argv: list[str]) -> int:
    # Boundary setup: UTF-8 output (Windows mojibake) + anchor to the tree to scan. Fail LOUD on
    # the git/FS boundary — print a plain message + exit 1, never a swallowed exception that
    # reads as a false green.
    _force_utf8_output()
    try:
        explicit_root = _parse_root(argv)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if explicit_root is not None:
        # `--root <built-tree>`: scan the given (already-stripped) release worktree, but keep
        # running FROM the dev checkout — do NOT chdir into the built tree (its `build_release`
        # + this script are stripped there, so `import build_release` and module resolution must
        # stay resolved against the dev checkout). All FS/git reads take `root` explicitly.
        root = explicit_root.resolve()
    else:
        # Default (byte-identical to before `--root`): anchor to the dev repo root from `__file__`
        # and chdir into it so the gate is CWD-independent.
        root = _repo_root()
        os.chdir(root)
    try:
        problems, warnings, summary = evaluate(root)
    except Exception as exc:  # noqa: BLE001 — fail-loud boundary: surface, never false-green
        print(
            f"ERROR: shipped-content scan could not run ({type(exc).__name__}: {exc}) — "
            f"the git/filesystem boundary failed; fix it (a silent pass would be a false green).",
            file=sys.stderr,
        )
        return 1
    # THE STREAM CONTRACT (the sibling rule — `check_doc_budgets.py`'s module docstring states
    # it in full): advisory `WARN:` lines ride STDERR, the verdict (problem lines / the OK
    # summary) rides STDOUT. This gate is not hook-wired, but the contract is a GATE-FAMILY
    # obligation, not a per-script choice: the pre-commit wrapper discards a passing gate's
    # stdout, so a WARN emitted there would be swallowed by any wrapper that ever chains it.
    # The ERROR paths in this same `main()` already use stderr.
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if problems:
        print("\n".join(problems))
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
