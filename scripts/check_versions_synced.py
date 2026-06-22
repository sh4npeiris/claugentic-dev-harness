#!/usr/bin/env python3
"""Enforce that the two plugin manifests carry the SAME version.

Deterministic gate (no LLM): `.claude-plugin/plugin.json`'s `version` is the
SINGLE SOURCE OF TRUTH; the gate FAILS if `.claude-plugin/marketplace.json`'s
plugin entry `version` disagrees. Scope is **exactly** those two fields — nothing
else (no managed-stamp scan, no other files). The marketplace catalog is
install-facing, so a release that bumps only `plugin.json` ships a drifted
catalog; this gate catches that pair drift mechanically (it was a hand-catch
before — see DECISIONS plan 0004 Slice 2).

Fails loud: a missing file, non-JSON/garbled content, or a manifest missing its
`version` field each produce a plain, actionable message + exit 1 — never a
swallowed exception, never a silent fail-open pass. The two manifests are read
INDEPENDENTLY (one being broken must not mask the other's value).

Modes:
    python scripts/check_versions_synced.py    # human/CI: stdout, exit 0 OK / exit 1 on any problem

Run in the Definition-of-Done gate suite at Verify/Land (like `pytest`) — a
run-gate, not hook-wired. See docs/claugentic-WORKFLOW.md -> Definition of Done.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Paths are repo-root-relative; `main()` chdir's to the repo root (derived from this script's
# own location via `_repo_root()`, NEVER the caller's CWD), so they resolve no matter where the
# gate is launched from — like claugentic-check_architecture_tree.py.
PLUGIN_PATH = Path(".claude-plugin/plugin.json")
MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")


def _read_plugin_version(path: Path) -> tuple[str | None, str | None]:
    """Read the top-level `version` from plugin.json. Returns (version, error).

    Exactly one of the pair is non-None: a plain error string on a missing file,
    garbled JSON, or an absent `version` field (fail loud, never a silent pass).
    """
    if not path.exists():
        return (None, f"{path} is missing — cannot read the source-of-truth version.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return (None, f"{path} could not be read ({exc}) — check the file exists and is readable.")
    except ValueError as exc:
        return (None, f"{path} is not valid JSON ({exc}) — fix the manifest.")
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str):
        return (None, f"{path} has no top-level `version` field — add one (the source of truth).")
    return (version, None)


def _read_marketplace_version(path: Path) -> tuple[str | None, str | None]:
    """Read the `claugentic-dev-harness` plugin entry's `version` from marketplace.json.

    Returns (version, error) — exactly one non-None. Fails loud on a missing file,
    garbled JSON, a missing/empty `plugins` array, a missing harness entry, or an
    absent `version` field. Parsed independently of plugin.json (no shared read).
    """
    if not path.exists():
        return (None, f"{path} is missing — cannot check the marketplace version.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return (None, f"{path} could not be read ({exc}) — check the file exists and is readable.")
    except ValueError as exc:
        return (None, f"{path} is not valid JSON ({exc}) — fix the manifest.")
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, list) or not plugins:
        return (None, f"{path} has no `plugins` array — cannot find the plugin entry.")
    entry = next(
        (p for p in plugins if isinstance(p, dict) and p.get("name") == "claugentic-dev-harness"),
        None,
    )
    if entry is None:
        return (None, f"{path} has no `claugentic-dev-harness` plugin entry to check.")
    version = entry.get("version")
    if not isinstance(version, str):
        return (None, f"{path} plugin entry has no `version` field — add one to match {PLUGIN_PATH}.")
    return (version, None)


def evaluate() -> tuple[list[str], str]:
    """Return (problem_lines, success_summary). Empty problem_lines == OK.

    Reads the two manifests independently so a broken file can't mask the other.
    """
    plugin_version, plugin_err = _read_plugin_version(PLUGIN_PATH)
    market_version, market_err = _read_marketplace_version(MARKETPLACE_PATH)

    problems = [e for e in (plugin_err, market_err) if e]
    if problems:
        return (problems, "")

    if plugin_version != market_version:
        return (
            [
                "Plugin version DRIFT — the two manifests disagree:",
                f"  {PLUGIN_PATH} version = {plugin_version}  (source of truth)",
                f"  {MARKETPLACE_PATH} version = {market_version}",
                f"Fix: set the {MARKETPLACE_PATH} plugin entry `version` to {plugin_version}.",
            ],
            "",
        )
    return ([], f"OK: {PLUGIN_PATH} and {MARKETPLACE_PATH} both at version {plugin_version}.")


def _repo_root() -> Path:
    """Repo root, derived from THIS script's location — never the process CWD, never hardcoded.

    `PLUGIN_PATH`/`MARKETPLACE_PATH` are repo-root-relative, but the gate may be invoked from
    any working directory; anchoring to the script's own location keeps it CWD-independent and
    portable (computed at runtime from `__file__`). Git is authoritative; falls back to
    `<script_dir>/..` (the script lives at `<repo>/scripts/`) when git is unavailable.
    """
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
    """Emit stdout as UTF-8 so non-ASCII glyphs in messages (the em-dashes in the drift/error
    text) survive on Windows, where stdout defaults to the locale codepage (cp1252) while the
    consumer decodes UTF-8 → mojibake. A captured/replaced stream may lack `.reconfigure` →
    guarded, best-effort.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except (AttributeError, ValueError):
            pass


def main(argv: list[str]) -> int:
    # Boundary setup: UTF-8 output (Windows mojibake) + anchor to the repo root so the gate is
    # CWD-independent (it may be run from anywhere). See _repo_root / _force_utf8_output.
    _force_utf8_output()
    os.chdir(_repo_root())
    problems, summary = evaluate()
    if problems:
        print("\n".join(problems))
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
