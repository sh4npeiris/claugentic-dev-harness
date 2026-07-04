#!/usr/bin/env python3
"""Build the clean RELEASE tree from the dev (`main`) repo.

The harness ships as TWO versions:
  * **main** (the public dev repo) — the harness improving itself: full history,
    DECISIONS/ROADMAP/plans/eval/tests, all tracked. This is what a curious visitor
    browses to see what's being worked on.
  * **release** branch — the clean version users install: `main` MINUS the dev-only
    paths in `DEV_ONLY_*` below. The marketplace `source` points at this branch, so
    `/plugin install` serves it — the commands a user types are UNCHANGED.

KISS: the dev-only set is an EXPLICIT, maintained list — NOT dynamically learned. When
you add a new dev-only file, add it here; everything else ships. (Default-include is the
deliberate choice: a forgotten new file ships rather than silently vanishing from the
release; the list is short and reviewed at release.)

Usage (run from anywhere — the script anchors to its own repo root):
    python scripts/build_release.py                        # dry-run: print ship vs strip, exit 0
    python scripts/build_release.py --apply                # (re)build the LOCAL `release` branch (no push)
    python scripts/build_release.py --apply --bump X.Y.Z    # ONE-command release up to the human-gated push

`--apply --bump <version>` is the SINGLE release entry point (plan 0034 Slice 10): it runs every
mechanizable step in ONE deterministic pass — preconditions -> write the version into BOTH
manifests -> build the stripped `release` tree -> validate it -> STOP and PRINT the one gated
command the human runs to publish. This is **one command up to a single human-gated push**, NOT
"fully automated": the tool NEVER tags or pushes — it prints the exact command and stops, so an
aborted/declined run leaves ZERO side effects (no tag, no push; only the local `release` branch +
the bumped manifests on the current branch, both re-runnable). The force-push (irreversible) and
the eval-drift/BASELINE check stay human-gated / model-upheld (see docs/RELEASE_CHECKLIST.md).

`--apply` (with or without `--bump`) force-resets a `release` branch to current `HEAD` in a
throwaway worktree, removes the dev-only files there, and commits — the dev working tree is never
touched (except the two manifests `--bump` writes). It does NOT push.

Flow order (each stage fails loud with an actionable message; none makes the release "fully"
correct/enforced — the force-push + eval-drift stay model-upheld):
  * stale-base   — HEAD must be ancestor-inclusive of `origin/main` (any missing commit,
                   not just merge commits, is a dropped-work refusal).
  * bump         — (`--bump` only) write `<version>` into BOTH manifests via a targeted
                   `"version"`-field replace (one-line diff per file), both-or-neither.
  * version-up   — `plugin.json`'s version must be strictly greater than the latest
                   published `vX.Y.Z` tag (no tag yet = first release, allowed).
  * drop-check   — every path on `origin/main`-not-HEAD must be a stripped dev-only path
                   (a SHIPPED file in that diff = merged work missing from the build).

After the strip (before the commit) it also validates the BUILT tree:
  * built-tree   — the dev checkout's `check_shipped_content.py --root <built-worktree>` scans the
                   stripped tree for shipped-content breaches (stranded tokens / dangling refs /
                   non-ASCII engine `*.js` / referential closure). A failure refuses the build with
                   NO commit — a break the strip introduced fails loud pre-push (the release branch
                   runs zero CI). Validates the shipped STRUCTURE, NOT that the release "passes CI".

On success it PRINTS the one gated command (the `vX.Y.Z` tag is created THERE, at publish — never
in-build, so an aborted run leaves no dangling tag that would corrupt the version anchor):
    git tag vX.Y.Z && git push --force-with-lease origin release && git push origin vX.Y.Z
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# THE DEV-ONLY SET — stripped from the release (explicit, maintained; KISS).
# ─────────────────────────────────────────────────────────────────────────────
# Exact paths that never reach an installing user (build history, harness-self tooling,
# repo config). Everything NOT matched here ships.
#
# SINGLE AUTHORED SEMANTICS: `path -> recreate-class`. The class annotates HOW (if at all)
# an adopter gets the stripped file back — the referential-closure gate (plan 0034 Slice 3)
# and the derived hand-lists in `check_shipped_content.py` (Slice 2) reason over these
# classes, so the partition here is the ONE place the ship/strip semantics are declared.
# The class set is SIX; every entry maps to EXACTLY ONE (an exhaustive partition — adding a
# dev-only file means adding one line here with its class, nothing else):
#
#   `init-seed`           — init copies a `_X.md` seed -> the adopter file (create-if-absent).
#   `init-gen`            — init GENERATES it in the adopter repo.
#   `recreate-on-demand`  — stripped, NOT init-produced, legitimately non-dangling because a
#                           NON-init mechanism creates it on demand (workflow lazy-create /
#                           agent-authored / user-authored-from-template). The class IS its
#                           own recreatability attestation — it does NOT claim init makes it.
#   `self-gate`           — a stripped harness-self script (run-gate / release builder).
#   `config`              — repo machinery no shipped doc points an adopter at.
#   `dangle`              — stripped AND never recreated (no adopter ever has it).
DEV_ONLY_PATH_CLASSES = {
    # Build-history / dev-process docs — rationale for HOW the harness is built, never "how to
    # use it on your codebase" (that lives in the shipped managed docs).
    "docs/claugentic-DECISIONS.md": "init-seed",       # init copies the `_DECISIONS.md` seed
    "docs/claugentic-ROADMAP.md": "init-seed",         # init copies the `_ROADMAP.md` seed
    "docs/claugentic-PRODUCT.md": "recreate-on-demand",       # agent-authored per project by product-designer
    "docs/claugentic-PRODUCT_SPEC.md": "recreate-on-demand",  # user-authored from the shipped PRODUCT_SPEC_TEMPLATE
    "docs/claugentic-ARCHITECTURE_TREE.md": "init-gen",       # init generates the adopter's own file map
    "docs/claugentic-INVARIANTS.md": "recreate-on-demand",    # the workflow lazily creates it (DoD step (f))
    "docs/RELEASE_CHECKLIST.md": "dangle",             # harness-self release ritual; no adopter ever has it
    # Harness-self tooling (an install doesn't need them).
    "scripts/check_versions_synced.py": "self-gate",   # checks the plugin's two manifests — irrelevant to adopters
    "scripts/check_doc_budgets.py": "self-gate",       # budgets the harness's OWN ledgers (harness-tuned caps) — irrelevant to adopters
    "scripts/check_shipped_content.py": "self-gate",   # scans the SHIPPED tree's text — harness-self, reasons about the release, never ships
    "scripts/build_release.py": "self-gate",           # this script
    # Repo config / dev-infra (machinery no shipped doc points an adopter at).
    ".claude/settings.json": "config",                 # the dev repo's OWN dogfooding hooks
    "CLAUDE.md": "config",                             # "this repo builds the harness…" — dev context
    "pyproject.toml": "config",                        # pytest config
    ".gitignore": "config",
    ".gitattributes": "config",
}

# Membership-preserving view of the manifest KEYS — the ship/strip classifier reasons over
# membership only, so `is_dev_only`/`classify` derive from these keys (identical to the prior
# `DEV_ONLY_FILES` frozenset). The class VALUES drive the closure gate + derived hand-lists.
DEV_ONLY_FILES = frozenset(DEV_ONLY_PATH_CLASSES)

# Directory prefixes whose entire subtree is dev-only.
DEV_ONLY_DIRS = (
    ".claude/plans/",   # the harness's own plan files (adopters don't receive plans/ via init)
    ".github/",         # CI config
    "eval/",            # the seeded-defect drift fixtures + baseline
    "tests/",           # the harness's own test suite
)

RELEASE_BRANCH = "release"

# The live upstream tip the release MUST be anchored on. A build from a base that
# excludes ANY commit reachable from here silently drops merged work (this is how
# the v0.1.40 distillation was lost — see docs/RELEASE_CHECKLIST.md).
UPSTREAM_REF = "origin/main"

# The source-of-truth plugin manifest — its `version` is what a release publishes. The
# version-increase guard (plan 0034 Slice 4 / P0-1) reads this and refuses a build whose
# version is not strictly greater than the latest published `vX.Y.Z` tag.
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"

# The install-facing catalog manifest whose plugin entry `version` MUST match PLUGIN_MANIFEST
# (the `check_versions_synced.py` gate enforces the pair). `--bump` (plan 0034 Slice 10 / C-1)
# is the single writer of the version into BOTH manifests from one value, so they cannot drift.
MARKETPLACE_MANIFEST = ".claude-plugin/marketplace.json"

# The two manifests `--bump` writes the version into, from the ONE `--bump <version>` value.
VERSIONED_MANIFESTS = (PLUGIN_MANIFEST, MARKETPLACE_MANIFEST)


def is_dev_only(path: str) -> bool:
    """True if `path` (a repo-relative, forward-slash path) is stripped from the release."""
    return path in DEV_ONLY_PATH_CLASSES or any(path.startswith(d) for d in DEV_ONLY_DIRS)


def recreate_class(path: str) -> str | None:
    """The recreate-class for a file-level dev-only `path`, or `None` if it isn't one.

    Reads the single authored manifest (`DEV_ONLY_PATH_CLASSES`). Returns `None` for a
    shipped path AND for a dir-swept path (`DEV_ONLY_DIRS`) — dirs stay OUT of the classes
    by design (the closure gate reasons over file-level classes only), so a caller that
    needs a class for a dir-stripped file is asking the wrong question and gets `None`.
    """
    return DEV_ONLY_PATH_CLASSES.get(path)


def classify(files: list[str]) -> tuple[list[str], list[str]]:
    """Split tracked files into (ship, strip), each sorted. Pure — the testable core."""
    ship, strip = [], []
    for f in sorted(files):
        (strip if is_dev_only(f) else ship).append(f)
    return ship, strip


def _repo_root() -> Path:
    """Repo root from THIS script's location (never the CWD), git-authoritative with a
    `<script_dir>/..` fallback — mirrors the gate scripts so the tool is CWD-independent."""
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
        return here.parent


def _force_utf8_output() -> None:
    """Emit stdout/stderr as UTF-8 so the em-dashes in the report don't mojibake on Windows
    (cp1252 stdout decoded as UTF-8). Guarded — a captured stream may lack `.reconfigure`."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except (AttributeError, ValueError):
            pass


def _git(*args: str) -> str:
    """Run a git command at the repo root, returning stdout; raises on non-zero."""
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", check=True
    )
    return result.stdout


def _tracked_files() -> list[str]:
    """Every tracked file, repo-relative, forward-slash normalized."""
    return [
        line.replace("\\", "/").strip()
        for line in _git("ls-files").splitlines()
        if line.strip()
    ]


def _dry_run() -> int:
    ship, strip = classify(_tracked_files())
    print(f"RELEASE dry-run — {len(ship)} ship · {len(strip)} strip\n")
    print("STRIP (dev-only — excluded from the release):")
    for f in strip:
        print(f"  - {f}")
    print(f"\nSHIP ({len(ship)} files reach the installed plugin):")
    for f in ship:
        print(f"  + {f}")
    return 0


_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a bare `X.Y.Z` version into an int triple for correct ordinal comparison.

    Fails loud on a non-well-formed version (never string-compares — `"0.10.0"` must sort
    ABOVE `"0.9.0"`, which a lexical compare gets wrong). Rejects pre-release/build suffixes:
    the harness ships plain `X.Y.Z` releases, so anything else is a mistake to surface, not
    silently coerce."""
    m = _SEMVER_RE.match(version.strip())
    if not m:
        raise ValueError(
            f"version {version!r} is not a well-formed X.Y.Z semver — fix the manifest."
        )
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _latest_release_tag(root: Path) -> str | None:
    """The highest `vX.Y.Z` git tag by semver order, or `None` if there is no such tag.

    Reads `git tag --list 'v*' --sort=-v:refname` and returns the first line (git's own
    version sort). `None` means the repo has no `vX.Y.Z` tag yet — the FIRST-release
    bootstrap case, which the version-increase guard ALLOWS."""
    out = _git("-C", str(root), "tag", "--list", "v*", "--sort=-v:refname")
    for line in out.splitlines():
        tag = line.strip()
        if _SEMVER_RE.match(tag.removeprefix("v")):
            return tag
    return None


def _read_manifest_version(root: Path) -> str:
    """The `version` field from `plugin.json` (the source-of-truth manifest).

    Fails loud on a missing file, garbled JSON, or an absent/non-string `version` — the
    version-increase guard must never silently proceed on an unreadable version."""
    path = root / PLUGIN_MANIFEST
    if not path.exists():
        raise ValueError(f"{PLUGIN_MANIFEST} is missing — cannot read the release version.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{PLUGIN_MANIFEST} is not valid JSON ({exc}) — fix the manifest.") from exc
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str):
        raise ValueError(f"{PLUGIN_MANIFEST} has no top-level `version` field — add one.")
    return version


def _version_increase_error(root: Path) -> str | None:
    """Refuse a release whose `plugin.json` version is NOT strictly greater than the latest
    published `vX.Y.Z` tag (plan 0034 Slice 4 / P0-1). Returns an actionable error string, or
    `None` when the build is allowed.

    Semantics (tag-anchored — the tag is the last thing actually PUBLISHED):
      * NO `vX.Y.Z` tag at all       -> first release, ALLOW (bootstrap).
      * new version > latest tag     -> ALLOW.
      * new version == latest tag    -> REFUSE (re-publishing a shipped version).
      * new version <  latest tag    -> REFUSE (downgrade).
    A same-version REBUILD of an untagged in-progress version is inherently allowed: the tag
    is created only at PUBLISH (never in-build), so a not-yet-published version is > every tag
    and passes. This is the highest-probability silent bad release (a forgotten bump)."""
    version = _read_manifest_version(root)
    new = _parse_semver(version)  # fails loud on a malformed manifest version
    latest_tag = _latest_release_tag(root)
    if latest_tag is None:
        return None  # first release — no anchor to compare against
    latest = _parse_semver(latest_tag.removeprefix("v"))
    if new > latest:
        return None
    return (
        f"refusing to build — {PLUGIN_MANIFEST} version {version} is not greater than the "
        f"latest released tag {latest_tag}. Bump the version (a forgotten bump ships a 'new' "
        f"release adopters see as no update; a lower version is a downgrade)."
    )


# A targeted match of ONLY the `"version": "X.Y.Z"` field VALUE in a 2-space-indented manifest.
# `--bump` replaces just this value (NOT a `json.load`->`json.dumps` round-trip, which would
# reflow the whole file — e.g. marketplace.json's long description + nested source — into a
# noisy diff), so each manifest's diff is exactly ONE line. The captured groups are the literal
# prefix (`"version": "`) and suffix (`"`) so the replacement preserves surrounding formatting.
_VERSION_FIELD_RE = re.compile(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")')


def _bump_one_manifest_text(text: str, path: str, version: str) -> str:
    """Return `text` with its single `"version": "X.Y.Z"` field set to `version` (a targeted
    value replace — no whole-file reflow). Fails loud if the file has no version field or MORE
    THAN ONE (an ambiguous manifest the targeted writer must not guess at).

    Pure over the file text — the caller computes BOTH manifests' new text with this BEFORE
    writing either (the both-or-neither guarantee), so a file with no matchable version field
    aborts the bump before any write touches disk."""
    matches = _VERSION_FIELD_RE.findall(text)
    if len(matches) == 0:
        raise ValueError(
            f"{path} has no `\"version\": \"X.Y.Z\"` field to bump — cannot write the version."
        )
    if len(matches) > 1:
        raise ValueError(
            f"{path} has {len(matches)} `version` fields — the targeted writer refuses an "
            f"ambiguous manifest (which one is the plugin version?)."
        )
    return _VERSION_FIELD_RE.sub(rf"\g<1>{version}\g<3>", text, count=1)


def _bump_manifests(root: Path, version: str) -> None:
    """Write `version` into BOTH versioned manifests from the ONE value — the single-source-of-
    truth version write (plan 0034 Slice 10 / C-1). Both-or-neither / partial-write-safe.

    Boundary-validated + fail-loud in strict order so a partial write can NEVER leave the two
    manifests drifted on disk:
      1. semver-validate `version` (well-formed X.Y.Z) — fails before any read.
      2. read both files + compute BOTH new texts IN MEMORY (each targeted-field-replaced);
         a missing/ambiguous version field in EITHER aborts here, before any write.
      3. write both back-to-back (both new texts already proven computable).
      4. re-run `check_versions_synced.evaluate()` in-process and FAIL LOUD if the pair
         disagrees — a belt-and-suspenders post-write assertion the write actually synced them.

    Idempotent: if both manifests are already at `version` the targeted replace is a no-op write
    of identical bytes (the diff stays empty) — a retry after an aborted publish re-runs cleanly.
    On a step-3 write error the message states the tree may be half-written (the operator can
    `git checkout -- <manifests>`); steps 1-2 guarantee step 3 is the only place a write happens."""
    _parse_semver(version)  # fail loud on a malformed version BEFORE touching any file.
    planned: list[tuple[Path, str]] = []
    for rel in VERSIONED_MANIFESTS:
        path = root / rel
        if not path.exists():
            raise ValueError(f"{rel} is missing — cannot bump the version.")
        new_text = _bump_one_manifest_text(path.read_text(encoding="utf-8"), rel, version)
        planned.append((path, new_text))
    written: list[str] = []
    try:
        for path, new_text in planned:
            path.write_text(new_text, encoding="utf-8")
            written.append(str(path))
    except OSError as exc:
        raise ValueError(
            f"failed writing the version bump ({exc}); the tree may be HALF-WRITTEN "
            f"(wrote: {', '.join(written) or 'nothing'}) — `git checkout -- "
            f"{' '.join(VERSIONED_MANIFESTS)}` and retry."
        ) from exc
    # Belt-and-suspenders: the two manifests MUST now agree (the write's whole purpose).
    import check_versions_synced

    cwd = os.getcwd()
    os.chdir(root)
    try:
        problems, _ = check_versions_synced.evaluate()
    finally:
        os.chdir(cwd)
    if problems:
        raise ValueError(
            "the version bump left the two manifests disagreeing (post-write sync check "
            "failed): " + " ".join(problems)
        )


def _missing_upstream_commits(root: Path) -> list[str] | None:
    """ANY commit reachable from `UPSTREAM_REF` but NOT from HEAD (the build base).

    Broadened from the merge-only form (plan 0034 Slice 6 / P2-2): a DIRECT non-merge push
    to `main` (which admin-bypass allows — see MEMORY: main branch-protection bypass) is a
    stale-base drop the `--merges` filter missed. Dropping `--merges` catches it too — a merge
    commit is still caught (it's a commit), so the prior merge-drop behavior is preserved.

    Returns the missing-commit SHAs (empty list = base is ancestor-inclusive of upstream —
    safe to build), or `None` if `UPSTREAM_REF` is absent (the operator hasn't fetched — fail
    loud, never silently build on an unknown base)."""
    try:
        _git("-C", str(root), "rev-parse", "--verify", "--quiet", f"{UPSTREAM_REF}^{{commit}}")
    except subprocess.CalledProcessError:
        return None
    out = _git("-C", str(root), "rev-list", UPSTREAM_REF, "--not", "HEAD")
    return [line.strip() for line in out.splitlines() if line.strip()]


def _dropped_shipped_paths(root: Path, strip: list[str]) -> list[str]:
    """Mechanized drop-check (plan 0034 Slice 7 / P1-3): the paths on `UPSTREAM_REF`-not-HEAD
    that are NOT in the strip set — i.e. SHIPPED files the release would silently drop.

    The honest computable form is a SUBSET assertion: every path that `origin/main` carries but
    `HEAD` (the build base) lacks must be a DEV-ONLY (stripped) path. A shipped path in that
    diff means merged, adopter-facing work is missing from the build — fail loud. Reuses the
    manifest's `classify()` via the passed-in `strip` set (DIP: this guard depends on the
    manifest, not vice-versa). Returns the offending shipped paths (empty = clean).

    Scope, honestly: this is a path-SET subset guard, NOT a total drop guarantee — it cannot
    see a dropped COMMIT whose file also legitimately changed elsewhere. The manual
    `git range-diff` drop-check stays as defense-in-depth (docs/RELEASE_CHECKLIST.md)."""
    out = _git("-C", str(root), "diff", "--name-only", "HEAD", UPSTREAM_REF)
    diff_paths = [line.replace("\\", "/").strip() for line in out.splitlines() if line.strip()]
    strip_set = set(strip)
    return sorted(p for p in diff_paths if p not in strip_set)


def _validate_built_tree(root: Path, built: str) -> int:
    """P0-2 (plan 0034 Slice 5): scan the BUILT (stripped) release worktree for shipped-content
    breaches BEFORE the release is committed. Returns 0 (clean) or a non-zero exit code.

    Runs the DEV CHECKOUT's `check_shipped_content.py --root <built>` as a subprocess — the strip
    removes `check_shipped_content.py` + `build_release.py` (which it imports) + `tests/` +
    `pyproject.toml` from `built`, so the gate/tests can't run FROM inside the built tree (they'd
    fail to import or vacuously collect zero). Pointing the dev copy AT the built tree is the
    only sound mechanism. A subprocess (not an in-process call) keeps the scanner's own `chdir` /
    stdout-reconfigure out of THIS process's state, and its exit code is the pass/fail signal.

    Honest scope: this validates the SHIPPED STRUCTURE of the built tree (no stranded namespace
    tokens / dangling stripped-path refs / non-ASCII engine `*.js` / referential-closure holds) —
    NOT that "the release passes CI" or is correct. The dev-tree `pytest` already ran pre-build in
    the Definition of Done; running `pytest` against the stripped tree would vacuously green (no
    `tests/`), so it is deliberately NOT run here."""
    scanner = root / "scripts" / "check_shipped_content.py"
    result = subprocess.run(
        [sys.executable, str(scanner), "--root", built],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def _bump_only_dirty(root: Path, bump: str | None) -> bool:
    """True if the working tree is dirty in a way that must REFUSE the build.

    With no `--bump`, ANY dirty file refuses (the original clean-tree precondition). With `--bump`,
    the version write to the two manifests is the intended change, so a tree dirty ONLY in those
    two manifests is allowed to proceed; ANY other dirty path still refuses — the build must not
    silently carry unrelated uncommitted work into a release.

    Read from `git status --porcelain` (path is columns 3+; handles quoted/renamed entries via the
    porcelain format's ` -> ` split for renames — the manifests are never renamed here, so a plain
    trailing-path parse suffices)."""
    dirty = [
        line[3:].strip() for line in _git("-C", str(root), "status", "--porcelain").splitlines()
        if line.strip()
    ]
    if not dirty:
        return False
    if bump is None:
        return True
    allowed = set(VERSIONED_MANIFESTS)
    return any(path.replace("\\", "/") not in allowed for path in dirty)


def _gated_publish_command(version: str) -> str:
    """The EXACT single command the human runs to publish (plan 0034 Slice 8/9/10). Tag-create +
    lease-safe branch-push + tag-push are ONE atomic human-gated step. The `vX.Y.Z` tag is created
    HERE, at publish — NOT in-build — so an aborted/declined run leaves no dangling tag. `--apply`
    only PRINTS this string; it never runs it (the honesty guarantee — the push stays `[J]`)."""
    return (
        f"git tag v{version} && "
        f"git push --force-with-lease origin {RELEASE_BRANCH} && "
        f"git push origin v{version}"
    )


def _apply(bump: str | None = None) -> int:
    """(Re)build the LOCAL `release` branch = HEAD minus the dev-only files, in ONE deterministic
    pass up to the human-gated push (plan 0034 Slice 10). Refuses on a stale base; NO tag, NO push.

    Stages, in flow order (each fails loud before any later mutation — an abort leaves no dangling
    tag, no push, and the `--bump` manifest write is the only working-tree change, revertable with
    `git checkout`):
      1. preconditions — stale-base (broadened), then (if `--bump`) the version write, then
         version-must-increase, then clean-tree + drop-check.
      2. build the stripped `release` tree in a throwaway worktree.
      3. validate the built tree (shipped-content scan) BEFORE the commit.
      4. commit the release build, then STOP + PRINT the one gated publish command.

    `bump` (the `--bump <version>` value, or `None`): when given, writes the version into BOTH
    manifests from the one value BEFORE the version-increase check (so a fresh bump is what the
    check then validates). The clean-tree precondition runs AFTER the bump so the intended version
    write is not mistaken for a dirty tree; any OTHER pre-existing dirty state still refuses."""
    root = _repo_root()
    # base == HEAD because _apply builds from HEAD; keep in sync if that changes.
    missing = _missing_upstream_commits(root)
    if missing is None:
        print(
            f"ERROR: '{UPSTREAM_REF}' not found — run `git fetch origin` before --apply.",
            file=sys.stderr,
        )
        return 1
    if missing:
        print(
            f"ERROR: refusing to build — HEAD excludes {len(missing)} commit(s) "
            f"reachable from {UPSTREAM_REF}; building here would DROP merged work "
            f"(see docs/RELEASE_CHECKLIST.md). Missing: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1
    # C-1 (Slice 10): --bump writes the version into BOTH manifests from the one value, BEFORE the
    # version-increase check validates it. A malformed/unwritable version fails loud here (no tag,
    # no push exist yet — zero side effects beyond the working-tree write it may leave for the
    # operator to `git checkout`). Runs after stale-base (a stale base must refuse before any write).
    if bump is not None:
        try:
            _bump_manifests(root, bump)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    # P0-1 (Slice 4): the version must strictly increase off the latest published tag.
    version_err = _version_increase_error(root)
    if version_err is not None:
        print(f"ERROR: {version_err}", file=sys.stderr)
        return 1
    # Clean-tree runs AFTER the bump so the intended version write isn't read as a dirty tree; any
    # OTHER pre-existing dirty state still refuses. With no --bump, this is the same guard as before.
    if _bump_only_dirty(root, bump):
        print(
            "ERROR: working tree not clean (beyond the version bump) — commit or stash before "
            "--apply.",
            file=sys.stderr,
        )
        return 1
    head = _git("-C", str(root), "rev-parse", "--short", "HEAD").strip()
    _, strip = classify(_tracked_files())
    # P1-3 (Slice 7): no SHIPPED file on origin/main-not-HEAD may be silently dropped.
    dropped_shipped = _dropped_shipped_paths(root, strip)
    if dropped_shipped:
        print(
            f"ERROR: refusing to build — {len(dropped_shipped)} SHIPPED file(s) on "
            f"{UPSTREAM_REF} are missing from the build base (HEAD) and would be dropped "
            f"from the release (see docs/RELEASE_CHECKLIST.md drop-check). "
            f"Dropped: {', '.join(dropped_shipped)}",
            file=sys.stderr,
        )
        return 1
    tmp = tempfile.mkdtemp(prefix="claugentic-release-")
    try:
        # --force -B resets/creates `release` at HEAD in a throwaway worktree; the dev tree is untouched.
        _git("-C", str(root), "worktree", "add", "--force", "-B", RELEASE_BRANCH, tmp, "HEAD")
        # The built worktree is HEAD (the COMMITTED tree) — but `--bump` writes the version into the
        # dev working tree UNCOMMITTED (abort-safe by design: an aborted run is `git checkout`-able).
        # So HEAD's manifests still carry the OLD version; copy the working-tree's bumped manifests
        # into the built worktree so the committed release ADVERTISES the version it SHIPS (a release
        # carrying content bumped to X.Y.Z but a manifest reading the old version is the exact
        # forgotten-bump footgun the version guard exists to prevent, hiding inside the flow). Only on
        # `--bump`: a plain `--apply` builds byte-identically from HEAD (the manifests are unchanged).
        if bump is not None:
            for rel in VERSIONED_MANIFESTS:
                (Path(tmp) / rel).write_text(
                    (root / rel).read_text(encoding="utf-8"), encoding="utf-8"
                )
                # Stage the overwrite: the release commit is `git commit` (no `-a`), so an unstaged
                # working-tree edit would NOT be committed — the bumped manifests must be staged to
                # reach the built release, exactly as the strip's `git rm` stages its removals.
                _git("-C", tmp, "add", "--", rel)
        for f in strip:
            _git("-C", tmp, "rm", "-q", "-r", "--ignore-unmatch", "--", f)
        # P0-2 (Slice 5): validate the BUILT (stripped) tree BEFORE committing — a break the strip
        # introduced (or survived) must fail loud PRE-commit, not reach an adopter (the release
        # branch runs zero CI). Runs the dev checkout's scanner pointed at the built worktree.
        rc = _validate_built_tree(root, tmp)
        if rc != 0:
            print(
                "ERROR: refusing to build — the built (stripped) release tree failed the "
                "shipped-content scan (see above); the release is NOT committed.",
                file=sys.stderr,
            )
            return rc
        # --no-verify: the release build is a mechanical clean-tree transform that INTENTIONALLY
        # strips the dev-only architecture tree (DEV_ONLY_FILES). The dogfooding pre-commit
        # tree-gate (init step 5b, plan 0024) would otherwise fire on this commit and fail with
        # "ARCHITECTURE_TREE.md is missing" — the gate guards the DEV tree, never the release build.
        _git("-C", tmp, "commit", "--no-verify", "-qm", f"release: clean build from {head}")
        ship_count = len(_tracked_files()) - len(strip)
        version = _read_manifest_version(root)
        print(f"OK: rebuilt local '{RELEASE_BRANCH}' branch from {head} ({ship_count} files). NOT pushed.")
        print(f"Review with:  git diff main {RELEASE_BRANCH} --stat")
        # C-3 (Slice 10): STOP + PRINT the one human-gated publish command. The tool does NOT tag
        # or push — it prints the exact command and stops (the honesty guarantee). Run it ONLY after
        # the model-upheld checks (eval-drift/BASELINE + the manual `git range-diff` drop-check).
        print(
            "\nOne command up to a single human-gated push — the mechanized stages passed. Before "
            "publishing, run the model-upheld checks (eval-drift vs eval/BASELINE.md + the manual "
            "`git range-diff origin/release...release` drop-check), then publish with:\n"
            f"    {_gated_publish_command(version)}\n"
            "(creates the vX.Y.Z rollback-anchor tag + lease-safe force-push in ONE step; this tool "
            "did NOT tag or push — nothing is published until you run the above.)"
        )
        return 0
    finally:
        subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", tmp], check=False)


def _parse_bump(argv: list[str]) -> str | None:
    """The `--bump <version>` value from `argv`, or `None` when the flag is absent.

    Boundary-validated + fail-loud: `--bump` with no following value raises. The version's semver
    well-formedness is validated downstream by `_bump_manifests` (so a single validation site owns
    that rule); here we only enforce that a value is PRESENT when the flag is given."""
    if "--bump" not in argv:
        return None
    i = argv.index("--bump")
    if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
        raise ValueError("--bump requires a <version> argument (the X.Y.Z version to release).")
    return argv[i + 1]


def main(argv: list[str]) -> int:
    _force_utf8_output()
    os.chdir(_repo_root())
    if "--apply" in argv:
        try:
            bump = _parse_bump(argv)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return _apply(bump)
    if "--bump" in argv:
        print("ERROR: --bump requires --apply (it writes the version as part of the build).", file=sys.stderr)
        return 1
    return _dry_run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
