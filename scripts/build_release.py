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
    python scripts/build_release.py --apply     # (re)build the LOCAL `release` branch (no push)

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
DEV_ONLY_FILES = frozenset(
    {
        # Build-history / dev-process docs — rationale for HOW the harness is built,
        # never "how to use it on your codebase" (that lives in the shipped managed docs).
        "docs/claugentic-DECISIONS.md",
        "docs/claugentic-ROADMAP.md",
        "docs/claugentic-PRODUCT.md",          # the harness's OWN product-discovery notes
        "docs/claugentic-PRODUCT_SPEC.md",     # the harness's OWN filled spec (the TEMPLATE ships)
        "docs/claugentic-ARCHITECTURE_TREE.md",  # the harness's own file map (init generates the adopter's)
        "docs/claugentic-INVARIANTS.md",       # the harness's OWN invariants (adopters record their own, lazily)
        "docs/RELEASE_CHECKLIST.md",
        # Harness-self tooling + config (an install doesn't need them).
        "scripts/check_versions_synced.py",    # checks the plugin's two manifests — irrelevant to adopters
        "scripts/build_release.py",            # this script
        ".claude/settings.json",               # the dev repo's OWN dogfooding hooks
        "CLAUDE.md",                           # "this repo builds the harness…" — dev context
        "pyproject.toml",                      # pytest config
        ".gitignore",
        ".gitattributes",
    }
)

# Directory prefixes whose entire subtree is dev-only.
DEV_ONLY_DIRS = (
    ".claude/plans/",   # the harness's own plan files (adopters don't receive plans/ via init)
    ".github/",         # CI config
    "eval/",            # the seeded-defect drift fixtures + baseline
    "tests/",           # the harness's own test suite
)

RELEASE_BRANCH = "release"


def is_dev_only(path: str) -> bool:
    """True if `path` (a repo-relative, forward-slash path) is stripped from the release."""
    return path in DEV_ONLY_FILES or any(path.startswith(d) for d in DEV_ONLY_DIRS)


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


def _apply() -> int:
    """(Re)build the LOCAL `release` branch = HEAD minus the dev-only files. No push."""
    root = _repo_root()
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
        _git("-C", tmp, "commit", "-qm", f"release: clean build from {head}")
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
