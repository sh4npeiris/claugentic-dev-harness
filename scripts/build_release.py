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
    python scripts/build_release.py            # dry-run: print ship vs strip, exit 0
    python scripts/build_release.py --apply     # (re)build the LOCAL `release` branch (no push); refuses a stale base

`--apply` force-resets a `release` branch to current `HEAD` in a throwaway worktree,
removes the dev-only files there, and commits — the dev working tree is never touched.
It does NOT push; publishing the branch + pointing the marketplace at it stays a manual,
reviewed step.
"""

from __future__ import annotations

import os
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
# excludes merge commits reachable from here silently drops merged work (this is how
# the v0.1.40 distillation was lost — see docs/RELEASE_CHECKLIST.md).
UPSTREAM_REF = "origin/main"


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


def _dropped_merges(root: Path) -> list[str] | None:
    """Merge commits reachable from `UPSTREAM_REF` but NOT from HEAD (the build base).

    Returns the dropped-merge SHAs (empty list = base is current — safe to build), or
    `None` if `UPSTREAM_REF` is absent (the operator hasn't fetched — fail loud, never
    silently build on an unknown base)."""
    try:
        _git("-C", str(root), "rev-parse", "--verify", "--quiet", f"{UPSTREAM_REF}^{{commit}}")
    except subprocess.CalledProcessError:
        return None
    out = _git("-C", str(root), "rev-list", "--merges", UPSTREAM_REF, "--not", "HEAD")
    return [line.strip() for line in out.splitlines() if line.strip()]


def _apply() -> int:
    """(Re)build the LOCAL `release` branch = HEAD minus the dev-only files. Refuses on a
    stale base; no push."""
    root = _repo_root()
    # base == HEAD because _apply builds from HEAD; keep in sync if that changes.
    dropped = _dropped_merges(root)
    if dropped is None:
        print(
            f"ERROR: '{UPSTREAM_REF}' not found — run `git fetch origin` before --apply.",
            file=sys.stderr,
        )
        return 1
    if dropped:
        print(
            f"ERROR: refusing to build — HEAD excludes {len(dropped)} merge commit(s) "
            f"reachable from {UPSTREAM_REF}; building here would DROP merged work "
            f"(see docs/RELEASE_CHECKLIST.md). Dropped: {', '.join(dropped)}",
            file=sys.stderr,
        )
        return 1
    if _git("-C", str(root), "status", "--porcelain").strip():
        print("ERROR: working tree not clean — commit or stash before --apply.", file=sys.stderr)
        return 1
    head = _git("-C", str(root), "rev-parse", "--short", "HEAD").strip()
    _, strip = classify(_tracked_files())
    tmp = tempfile.mkdtemp(prefix="claugentic-release-")
    try:
        # --force -B resets/creates `release` at HEAD in a throwaway worktree; the dev tree is untouched.
        _git("-C", str(root), "worktree", "add", "--force", "-B", RELEASE_BRANCH, tmp, "HEAD")
        for f in strip:
            _git("-C", tmp, "rm", "-q", "-r", "--ignore-unmatch", "--", f)
        # --no-verify: the release build is a mechanical clean-tree transform that INTENTIONALLY
        # strips the dev-only architecture tree (DEV_ONLY_FILES). The dogfooding pre-commit
        # tree-gate (init step 5b, plan 0024) would otherwise fire on this commit and fail with
        # "ARCHITECTURE_TREE.md is missing" — the gate guards the DEV tree, never the release build.
        _git("-C", tmp, "commit", "--no-verify", "-qm", f"release: clean build from {head}")
        ship_count = len(_tracked_files()) - len(strip)
        print(f"OK: rebuilt local '{RELEASE_BRANCH}' branch from {head} ({ship_count} files). NOT pushed.")
        print(f"Review with:  git diff main {RELEASE_BRANCH} --stat")
        return 0
    finally:
        subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", tmp], check=False)


def main(argv: list[str]) -> int:
    _force_utf8_output()
    os.chdir(_repo_root())
    if "--apply" in argv:
        return _apply()
    return _dry_run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
