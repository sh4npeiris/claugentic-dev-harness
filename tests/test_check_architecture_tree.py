"""Characterization + regression tests for the architecture-tree gate.

The gate (`scripts/check_architecture_tree.py`) is the one deterministic component
the whole harness trusts. These tests lock its behaviour so a future edit can't
silently regress it (it once carried a latent `ts`-before-`tsx` staleness bug while
still reporting green).

Hermetic by construction:
  * `_git` is monkeypatched so no real repo state leaks in.
  * `tmp_path` + `chdir` give a real (controlled) filesystem for `Path.exists()`.
  * `INCLUDE_GLOBS`/`EXTS` are monkeypatched per-test to exercise multi-extension
    repos without touching this repo's own config.
"""

from __future__ import annotations

import pytest

import check_architecture_tree as cat


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A scratch repo: chdir into tmp_path, point TREE_PATH at it, stub _git empty.

    Returns the tmp_path root so a test can materialise files for `Path.exists()`.
    Individual tests override `in_scope_files` (via _git) and `INCLUDE_GLOBS`/`EXTS`
    as needed.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cat, "TREE_PATH", cat.Path("docs/ARCHITECTURE_TREE.md"))
    # Default: git reports nothing in scope (presence check is then trivially OK).
    monkeypatch.setattr(cat, "_git", lambda *args: [])
    return tmp_path


def _write_tree(root, text: str) -> None:
    tree = root / "docs" / "ARCHITECTURE_TREE.md"
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_text(text, encoding="utf-8")


def _touch(root, rel: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")


def _set_scope(monkeypatch, globs: list[str], files: list[str]) -> None:
    """Configure the per-repo knob + the file list git would report."""
    monkeypatch.setattr(cat, "INCLUDE_GLOBS", globs)
    monkeypatch.setattr(cat, "EXTS", cat._exts_from_globs(globs))
    monkeypatch.setattr(cat, "_git", lambda *args: list(files))


def _git_router(monkeypatch, *, in_scope: list[str], repo_wide: list[str]):
    """Install an args-aware `_git` that distinguishes the gate's two call shapes.

    The drift path makes UN-scoped `ls-files` calls (no `:(glob)` pathspec — they see the
    whole repo); `in_scope_files()` makes GLOB-scoped calls (args carry a `:(glob)` pathspec).
    Return `repo_wide` for the former and `in_scope` for the latter, so a single test can
    drive both `in_scope_files()` and `_repo_source_files()` truthfully.

    Returns the list of arg-tuples the gate passed to `_git`, so a test can assert that
    git was NEVER invoked with an empty/`--`-only pathspec (the fail-open guard).
    """
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> list[str]:
        calls.append(args)
        if any(":(glob)" in a for a in args):
            return list(in_scope)
        return list(repo_wide)

    monkeypatch.setattr(cat, "_git", fake_git)
    return calls


def _stamp(root, rel: str) -> None:
    """Materialise a harness-managed source file (the managed stamp on line 1).

    `_is_harness_managed` reads line 1 from disk, so the file must really exist with the
    `claugentic-dev-harness@<ver>` token first — mirrors a copied gate script in an adopter.
    """
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "# claugentic-dev-harness@0.1.0 managed — do not edit.\nprint('x')\n",
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
# _exts_from_globs — the single source of truth for valid extensions
# ─────────────────────────────────────────────────────────────────────────────
class TestExtsFromGlobs:
    def test_single_extension_glob(self):
        assert cat._exts_from_globs([":(glob)scripts/**/*.py"]) == {"py"}

    def test_multiple_globs_collected(self):
        assert cat._exts_from_globs(
            [":(glob)src/**/*.ts", ":(glob)src/**/*.tsx"]
        ) == {"ts", "tsx"}

    def test_extension_lowercased(self):
        assert cat._exts_from_globs([":(glob)src/**/*.PY"]) == {"py"}

    def test_root_glob_no_prefix(self):
        # A root-level glob with no directory prefix still yields its extension.
        assert cat._exts_from_globs([":(glob)**/*.go"]) == {"go"}

    def test_extension_less_glob_skipped(self):
        # A bare directory glob has no derivable `*.ext` — skipped gracefully.
        assert cat._exts_from_globs([":(glob)src/**"]) == set()

    def test_mixed_extension_and_extension_less(self):
        assert cat._exts_from_globs(
            [":(glob)src/**", ":(glob)cmd/**/*.go"]
        ) == {"go"}

    def test_empty_globs(self):
        assert cat._exts_from_globs([]) == set()


# ─────────────────────────────────────────────────────────────────────────────
# INCLUDE_GLOBS coverage — the `engine/**/*.js` scripts
# ─────────────────────────────────────────────────────────────────────────────
class TestEngineGlobWidening:
    """This repo's INCLUDE_GLOBS also watches `engine/**/*.js`, so the executable
    Workflow scripts are tree-enforced exactly like the gate scripts. `EXTS`
    derives `js` automatically; presence/staleness then cover .js files too."""

    def test_exts_derives_py_and_js_from_widened_globs(self):
        # The repo's actual INCLUDE_GLOBS (NOT monkeypatched) must derive {"py", "js"}.
        assert cat._exts_from_globs(
            [":(glob)scripts/**/*.py", ":(glob)engine/**/*.js"]
        ) == {"py", "js"}
        # And the module-level EXTS (derived from the live INCLUDE_GLOBS) carries js.
        assert cat.EXTS == {"py", "js"}

    def test_in_scope_workflow_js_absent_from_tree_is_missing(self, repo, monkeypatch):
        _set_scope(
            monkeypatch,
            [":(glob)scripts/**/*.py", ":(glob)engine/**/*.js"],
            ["engine/verify.js"],
        )
        _touch(repo, "engine/verify.js")
        _write_tree(repo, "# Tree\n(no workflows section yet)\n")
        problems, _ = cat.evaluate()
        assert any("MISSING an entry" in p for p in problems)
        assert any("engine/verify.js" in p for p in problems)

    def test_in_scope_workflow_js_indexed_is_ok(self, repo, monkeypatch):
        _set_scope(
            monkeypatch,
            [":(glob)scripts/**/*.py", ":(glob)engine/**/*.js"],
            ["engine/verify.js"],
        )
        _touch(repo, "engine/verify.js")
        _write_tree(repo, "# Tree\n- `engine/verify.js` — the Verify panel script.\n")
        problems, summary = cat.evaluate()
        assert problems == []
        assert "indexes all 1 in-scope files" in summary

    def test_dangling_workflow_js_reference_is_stale(self, repo, monkeypatch):
        _set_scope(
            monkeypatch,
            [":(glob)scripts/**/*.py", ":(glob)engine/**/*.js"],
            [],
        )
        _write_tree(repo, "# Tree\n- `engine/gone.js` — was removed.\n")
        problems, _ = cat.evaluate()
        assert any("NO LONGER EXIST" in p for p in problems)
        assert any("engine/gone.js" in p for p in problems)


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — PRESENCE
# ─────────────────────────────────────────────────────────────────────────────
class TestPresence:
    def test_missing_tree_file_errors(self, repo):
        # No tree on disk → loud error, not a silent pass.
        problems, summary = cat.evaluate()
        assert summary == ""
        assert any("is missing" in p for p in problems)

    def test_all_indexed_is_ok(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n- `scripts/a.py` — does a thing.\n")
        problems, summary = cat.evaluate()
        assert problems == []
        assert "indexes all 1 in-scope files" in summary

    def test_undocumented_in_scope_file_flagged(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n(nothing useful here)\n")
        problems, _ = cat.evaluate()
        assert any("MISSING an entry" in p for p in problems)
        assert any("scripts/a.py" in p for p in problems)

    def test_root_file_not_false_green_by_longer_path(self, repo, monkeypatch):
        """FAILS on pre-fix code (raw `f in text` substring): a root `a.py` reads as
        indexed merely because a longer `scripts/a.py` entry contains the substring
        `a.py`. Whole backtick-token equality flags the un-indexed root file."""
        _set_scope(
            monkeypatch,
            [":(glob)**/*.py"],
            ["a.py", "scripts/a.py"],
        )
        _touch(repo, "a.py")
        _touch(repo, "scripts/a.py")
        # The tree indexes ONLY scripts/a.py; the root a.py has no entry of its own.
        _write_tree(repo, "# Tree\n- `scripts/a.py` — the indexed one.\n")
        problems, _ = cat.evaluate()
        assert any("MISSING an entry" in p for p in problems)
        assert any(p.strip() == "+ a.py" for p in problems), problems

    def test_prose_mention_without_backticks_not_indexed(self, repo, monkeypatch):
        """FAILS on pre-fix code: a bare prose mention (no backticks) of the path
        substring satisfied `f in text`. An entry must be an EXACT backtick token, so
        prose alone never counts as documenting the file."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\nThe file scripts/a.py does a thing (no backticks).\n")
        problems, _ = cat.evaluate()
        assert any("MISSING an entry" in p for p in problems)
        assert any("scripts/a.py" in p for p in problems)

    def test_non_ascii_filename_indexed_is_ok_hermetic(self, repo, monkeypatch):
        """Hermetic non-ASCII case: with `_git` returning the path VERBATIM (what the
        `core.quotepath=false` fix guarantees from real git), a UTF-8 backtick entry is
        matched and presence passes. Pins the backtick-token path on non-ASCII input."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/café.py"])
        _touch(repo, "scripts/café.py")
        _write_tree(repo, "# Tree\n- `scripts/café.py` — a non-ASCII filename.\n")
        problems, summary = cat.evaluate()
        assert problems == [], f"non-ASCII entry wrongly flagged: {problems}"
        assert "indexes all 1 in-scope files" in summary


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — STALENESS (the bug-prone path)
# ─────────────────────────────────────────────────────────────────────────────
class TestStaleness:
    def test_existing_reference_not_stale(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], [])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n- `scripts/a.py` — exists.\n")
        problems, _ = cat.evaluate()
        assert problems == []

    def test_dangling_reference_is_stale(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], [])
        _write_tree(repo, "# Tree\n- `scripts/gone.py` — was deleted.\n")
        problems, _ = cat.evaluate()
        assert any("NO LONGER EXIST" in p for p in problems)
        assert any("scripts/gone.py" in p for p in problems)

    def test_ts_tsx_regression_no_false_stale(self, repo, monkeypatch):
        """The exact bug class: a tree citing an existing `foo.tsx` must NOT be
        flagged stale. The old per-repo staleness regex used naive alternation
        (`(?:ts|tsx)`) that matched `ts` before `tsx`, truncating `foo.tsx`→`foo.ts`
        and producing a false 'stale' positive. Whole-extension equality kills it.

        EXTS is set to a `.ts`+`.tsx` pair so this exercises the multi-extension repo.
        """
        _set_scope(
            monkeypatch,
            [":(glob)src/**/*.ts", ":(glob)src/**/*.tsx"],
            [],
        )
        _touch(repo, "src/foo.tsx")
        _write_tree(repo, "# Tree\n- `src/foo.tsx` — a component that exists.\n")
        problems, _ = cat.evaluate()
        assert problems == [], f"false stale positive on .tsx: {problems}"

    def test_ts_tsx_regression_missing_tsx_is_stale(self, repo, monkeypatch):
        """The flip side: a missing `gone.tsx` MUST still be flagged stale."""
        _set_scope(
            monkeypatch,
            [":(glob)src/**/*.ts", ":(glob)src/**/*.tsx"],
            [],
        )
        _write_tree(repo, "# Tree\n- `src/gone.tsx` — deleted component.\n")
        problems, _ = cat.evaluate()
        assert any("src/gone.tsx" in p for p in problems)

    def test_deep_monorepo_path(self, repo, monkeypatch):
        """A deep/monorepo path is handled the same as any other — extension match,
        existence check, no prefix gymnastics."""
        _set_scope(monkeypatch, [":(glob)**/*.tsx"], [])
        _write_tree(
            repo,
            "# Tree\n- `packages/app/src/x.tsx` — deep, missing.\n",
        )
        problems, _ = cat.evaluate()
        assert any("packages/app/src/x.tsx" in p for p in problems)

    def test_token_with_out_of_scope_extension_ignored(self, repo, monkeypatch):
        """A path-shaped token whose extension is not in EXTS is never a staleness
        candidate (e.g. a `.md` reference when EXTS == {py})."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], [])
        _write_tree(
            repo,
            "# Tree\n- `docs/SOMETHING.md` — a doc that does not exist on disk.\n",
        )
        problems, _ = cat.evaluate()
        assert problems == [], f"out-of-EXTS token wrongly treated as stale: {problems}"

    def test_extension_less_glob_skips_staleness(self, repo, monkeypatch):
        """An extension-less INCLUDE_GLOBS entry → EXTS empty → staleness is a
        no-op (presence still works); a dangling `.py` reference is NOT flagged."""
        _set_scope(monkeypatch, [":(glob)src/**"], [])
        _write_tree(repo, "# Tree\n- `src/gone.py` — would be stale, but EXTS empty.\n")
        problems, _ = cat.evaluate()
        assert problems == []

    def test_windows_path_normalization(self, repo, monkeypatch):
        """`evaluate()` must normalize `\\`→`/` on extracted tokens so a tree citing
        `a/b.py` matches the real file regardless of OS path separators.

        We write the file with forward slashes (Path handles the native sep) and the
        tree cites it with a backslash — the extractor must normalize and find it.
        """
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], [])
        _touch(repo, "scripts/sub/b.py")
        _write_tree(repo, "# Tree\n- `scripts\\sub\\b.py` — cited with backslashes.\n")
        problems, _ = cat.evaluate()
        assert problems == [], f"backslash path not normalized: {problems}"


# ─────────────────────────────────────────────────────────────────────────────
# main() — mode dispatch + exit codes
# ─────────────────────────────────────────────────────────────────────────────
class TestMainDispatch:
    def test_ok_default_mode_exit_0_prints_summary(self, repo, monkeypatch, capsys):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n- `scripts/a.py` — does a thing.\n")
        rc = cat.main([])
        assert rc == 0
        assert "OK:" in capsys.readouterr().out

    def test_ok_hook_mode_exit_0_silent(self, repo, monkeypatch, capsys):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n- `scripts/a.py` — does a thing.\n")
        rc = cat.main(["--hook"])
        assert rc == 0
        # Hook mode is silent on success (no nagging the agent on every Stop).
        assert capsys.readouterr().out == ""

    def test_problem_default_mode_exit_1(self, repo, monkeypatch, capsys):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n(undocumented)\n")
        rc = cat.main([])
        assert rc == 1
        assert "MISSING an entry" in capsys.readouterr().out

    def test_problem_hook_mode_exit_2_stderr(self, repo, monkeypatch, capsys):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n(undocumented)\n")
        rc = cat.main(["--hook"])
        assert rc == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "MISSING an entry" in captured.err


# ─────────────────────────────────────────────────────────────────────────────
# main(--hook-write) — PostToolUse(Write) nudge via stdin
# ─────────────────────────────────────────────────────────────────────────────
class TestHookWrite:
    def _feed_stdin(self, monkeypatch, payload: str) -> None:
        import io

        monkeypatch.setattr(cat.sys, "stdin", io.StringIO(payload))

    def test_well_formed_new_undocumented_exit_2(self, repo, monkeypatch, capsys):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/new.py"])
        _write_tree(repo, "# Tree\n(empty)\n")
        self._feed_stdin(
            monkeypatch,
            '{"tool_input": {"file_path": "/abs/repo/scripts/new.py"}}',
        )
        rc = cat.main(["--hook-write"])
        assert rc == 2
        assert "not in docs/ARCHITECTURE_TREE.md" in capsys.readouterr().err

    def test_malformed_stdin_returns_none_exit_0(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/new.py"])
        self._feed_stdin(monkeypatch, "{not valid json")
        # Malformed payload → no path → silent no-op (never crash the agent's Write).
        assert cat._written_path_from_stdin() is None
        assert cat.main(["--hook-write"]) == 0

    def test_already_indexed_exit_0(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/seen.py"])
        _write_tree(repo, "# Tree\n- `scripts/seen.py` — already documented.\n")
        self._feed_stdin(
            monkeypatch,
            '{"tool_input": {"file_path": "/abs/repo/scripts/seen.py"}}',
        )
        assert cat.main(["--hook-write"]) == 0

    def test_out_of_scope_file_exit_0(self, repo, monkeypatch):
        # README.md is not in INCLUDE_GLOBS → not our concern → silent.
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _write_tree(repo, "# Tree\n- `scripts/a.py` — x.\n")
        self._feed_stdin(
            monkeypatch,
            '{"tool_input": {"file_path": "/abs/repo/README.md"}}',
        )
        assert cat.main(["--hook-write"]) == 0

    def test_overwrite_of_indexed_file_exit_0(self, repo, monkeypatch):
        # Overwriting an already-indexed in-scope file is fine — no nudge.
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _write_tree(repo, "# Tree\n- `scripts/a.py` — already here.\n")
        self._feed_stdin(
            monkeypatch,
            '{"tool_input": {"file_path": "scripts/a.py"}}',
        )
        assert cat.main(["--hook-write"]) == 0

    def test_no_file_path_in_payload_exit_0(self, repo, monkeypatch):
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        self._feed_stdin(monkeypatch, '{"tool_input": {}}')
        assert cat._written_path_from_stdin() is None
        assert cat.main(["--hook-write"]) == 0

    def test_root_file_nudged_despite_longer_path_in_tree(self, repo, monkeypatch, capsys):
        """FAILS on pre-fix code (`rel in text` substring): writing an un-indexed root
        `a.py` is wrongly read as already-documented because a longer `scripts/a.py`
        entry contains the substring `a.py`. Whole backtick-token equality nudges it."""
        _set_scope(monkeypatch, [":(glob)**/*.py"], ["a.py"])
        # The tree documents scripts/a.py, NOT the freshly-written root a.py.
        _write_tree(repo, "# Tree\n- `scripts/a.py` — a different, indexed file.\n")
        self._feed_stdin(
            monkeypatch,
            '{"tool_input": {"file_path": "/abs/repo/a.py"}}',
        )
        rc = cat.main(["--hook-write"])
        assert rc == 2
        assert "not in docs/ARCHITECTURE_TREE.md" in capsys.readouterr().err


# ─────────────────────────────────────────────────────────────────────────────
# _git — fail loud on genuine git failure (missing git / non-zero); empty-success OK
# ─────────────────────────────────────────────────────────────────────────────
class _FakeCompleted:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# The genuine `_git` (the `repo` fixture stubs `cat._git` to an empty lambda; the
# git-failure tests need the real implementation so the stubbed `subprocess.run`
# actually drives its fail-loud path). Captured at import, before any monkeypatch.
_REAL_GIT = cat._git


def _stub_run(monkeypatch, *, returncode=0, stdout="", stderr="", raises=None):
    """Monkeypatch subprocess.run to simulate a git invocation result.

    Also restores the genuine `_git` so the stub actually runs (the `repo` fixture
    replaces `cat._git` with an empty lambda by default).
    """

    def fake_run(*_args, **_kwargs):
        if raises is not None:
            raise raises
        return _FakeCompleted(returncode, stdout, stderr)

    monkeypatch.setattr(cat, "_git", _REAL_GIT)
    monkeypatch.setattr(cat.subprocess, "run", fake_run)


class TestGitFailLoud:
    def test_nonzero_returncode_raises(self, monkeypatch):
        # git ran but errored (e.g. cwd is not a repository) → loud RuntimeError,
        # NOT a silent empty list that would read as "0 in-scope files".
        _stub_run(monkeypatch, returncode=128, stderr="fatal: not a git repository")
        with pytest.raises(RuntimeError) as exc:
            cat._git("ls-files")
        assert "git unavailable or not a repository" in str(exc.value)
        assert "fatal: not a git repository" in str(exc.value)

    def test_git_missing_raises(self, monkeypatch):
        # git not installed → subprocess.run raises FileNotFoundError → RuntimeError.
        _stub_run(monkeypatch, raises=FileNotFoundError("git"))
        with pytest.raises(RuntimeError) as exc:
            cat._git("ls-files")
        assert "git unavailable or not a repository" in str(exc.value)

    def test_returncode_zero_empty_stdout_is_legitimate(self, monkeypatch):
        # Regression guard: success (rc 0) with empty stdout is a legitimately-empty
        # result (empty repo / glob matched nothing) — must NOT raise.
        _stub_run(monkeypatch, returncode=0, stdout="")
        assert cat._git("ls-files") == []

    def test_returncode_zero_with_output_parsed(self, monkeypatch):
        # Sanity: a normal success still parses + strips lines as before.
        _stub_run(monkeypatch, returncode=0, stdout="scripts/a.py\nscripts/b.py\n")
        assert cat._git("ls-files") == ["scripts/a.py", "scripts/b.py"]


# ─────────────────────────────────────────────────────────────────────────────
# main() — git-failure boundary: never a false green
# ─────────────────────────────────────────────────────────────────────────────
class TestMainGitFailure:
    def test_default_mode_git_failure_exit_1_error_on_stdout(self, repo, monkeypatch, capsys):
        # CLI mode: a git failure must surface as ERROR + exit 1, never "OK: 0 files".
        _stub_run(monkeypatch, returncode=128, stderr="fatal: not a git repository")
        _write_tree(repo, "# Tree\n")
        rc = cat.main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert "ERROR:" in captured.out
        assert "OK:" not in captured.out

    def test_hook_mode_git_failure_exit_2_error_on_stderr(self, repo, monkeypatch, capsys):
        # Stop hook: blocking exit 2, error to stderr — the agent must know the gate
        # could not run.
        _stub_run(monkeypatch, returncode=128, stderr="fatal: not a git repository")
        _write_tree(repo, "# Tree\n")
        rc = cat.main(["--hook"])
        assert rc == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "ERROR:" in captured.err

    def test_hook_mode_git_missing_exit_2(self, repo, monkeypatch, capsys):
        _stub_run(monkeypatch, raises=FileNotFoundError("git"))
        _write_tree(repo, "# Tree\n")
        assert cat.main(["--hook"]) == 2
        assert "git unavailable" in capsys.readouterr().err

    def test_hook_write_git_failure_exit_0_not_blocked(self, repo, monkeypatch, capsys):
        # PostToolUse(Write) nudge is advisory — a git failure must NOT block the write.
        _stub_run(monkeypatch, returncode=128, stderr="fatal: not a git repository")
        import io

        monkeypatch.setattr(
            cat.sys, "stdin", io.StringIO('{"tool_input": {"file_path": "scripts/new.py"}}')
        )
        assert cat.main(["--hook-write"]) == 0
        # Silent: no nag on a gate it couldn't even run.
        assert capsys.readouterr().err == ""


# ─────────────────────────────────────────────────────────────────────────────
# glob_drift — the zero-coverage trip-wire (the reason this slice exists)
# ─────────────────────────────────────────────────────────────────────────────
class TestGlobDrift:
    def test_headline_empty_globs_after_real_source_lands_is_blocking(
        self, repo, monkeypatch, capsys
    ):
        """THE transition the slice exists for: `INCLUDE_GLOBS == []` (init's 'unset' on
        an empty repo) AFTER real source has landed. in_scope is empty, so drift censuses
        the repo, finds `src/app.ts`, and `evaluate()` must go BLOCKING — never silent-green.
        Asserted end-to-end through both CLI exit codes."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _touch(repo, "src/app.ts")
        _git_router(monkeypatch, in_scope=[], repo_wide=["src/app.ts"])
        _write_tree(repo, "# Tree\n(no source indexed)\n")

        problems, _ = cat.evaluate()
        assert any("watches no files" in p for p in problems)
        assert any("src/app.ts" in p for p in problems)

        assert cat.glob_drift(set()) == ["src/app.ts"]

        # CLI: exit 1 + actionable message on stdout.
        rc = cat.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "src/app.ts" in out
        assert "INCLUDE_GLOBS" in out

        # Hook: exit 2 (blocking) + message on stderr, silent stdout.
        rc = cat.main(["--hook"])
        assert rc == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "watches no files" in captured.err

    def test_steady_state_in_scope_nonempty_no_drift_no_stamp_reads(
        self, repo, monkeypatch
    ):
        """This repo's shape: INCLUDE_GLOBS covers `scripts/**/*.py`, in_scope non-empty →
        drift short-circuits to [] and NEVER reads a stamp / censuses the repo."""
        # _is_harness_managed must not be called in the steady state — spy that explodes.
        def _explode(_path):
            raise AssertionError("stamp read in steady state — short-circuit broken")

        monkeypatch.setattr(cat, "_is_harness_managed", _explode)
        assert cat.glob_drift({"scripts/a.py"}) == []

    def test_day0_stamped_gate_script_does_not_false_trip(self, repo, monkeypatch):
        """Day-0 false-positive guard (R3): `INCLUDE_GLOBS == []` and the ONLY source file
        is a STAMPED `scripts/check_architecture_tree.py` (the copied gate) → excluded by
        `_is_harness_managed` → `_repo_source_files` empty → no drift. A freshly-`init`'d
        empty adopter repo must not false-trip."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _stamp(repo, "scripts/check_architecture_tree.py")
        _git_router(
            monkeypatch,
            in_scope=[],
            repo_wide=["scripts/check_architecture_tree.py"],
        )
        assert cat._repo_source_files() == []
        assert cat.glob_drift(set()) == []

    def test_empty_globs_guard_never_calls_git_with_empty_pathspec(
        self, repo, monkeypatch
    ):
        """Empty-globs guard: `INCLUDE_GLOBS == []` → `in_scope_files() == set()` AND git is
        never invoked with a bare `--`/empty pathspec (the fail-open that would list EVERY
        file). We assert it short-circuits before any `_git` call at all."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        calls = _git_router(monkeypatch, in_scope=["should-not-be-used"], repo_wide=[])
        assert cat.in_scope_files() == set()
        # The guard returns before any git call — so no `ls-files --` with empty pathspec.
        assert calls == []

    def test_truly_empty_repo_is_ok(self, repo, monkeypatch):
        """Truly empty repo: `INCLUDE_GLOBS == []`, no SOURCE_EXTS files → evaluate() OK
        (no false drift problem)."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _git_router(monkeypatch, in_scope=[], repo_wide=[])
        _write_tree(repo, "# Tree\n(empty repo)\n")
        problems, summary = cat.evaluate()
        assert problems == []
        assert "OK:" in summary

    def test_source_exts_discrimination_docs_only_repo_no_drift(self, repo, monkeypatch):
        """SOURCE_EXTS discrimination: a `.md`/`.json`-only repo with `INCLUDE_GLOBS == []`
        → no drift (docs/config are not source code)."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _git_router(
            monkeypatch,
            in_scope=[],
            repo_wide=["README.md", "package.json", "docs/WORKFLOW.md"],
        )
        assert cat._repo_source_files() == []
        assert cat.glob_drift(set()) == []

    def test_termination_reset_globs_clear_drift(self, repo, monkeypatch):
        """Self-correction termination (unit): once globs are reset to match the landed
        source, in_scope is non-empty → `glob_drift` returns [] — drift clears, no loop."""
        # Reset INCLUDE_GLOBS to cover the source; in_scope now non-empty.
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [":(glob)src/**/*.ts"])
        monkeypatch.setattr(cat, "EXTS", cat._exts_from_globs([":(glob)src/**/*.ts"]))
        _git_router(monkeypatch, in_scope=["src/app.ts"], repo_wide=["src/app.ts"])
        assert cat.in_scope_files() == {"src/app.ts"}
        assert cat.glob_drift(cat.in_scope_files()) == []

    def test_mixed_managed_excluded_and_real_source_in_one_census(self, repo, monkeypatch):
        """Pins the three-way filter in ONE census: a STAMPED gate script (managed → dropped),
        an `__init__.py` + a `__pycache__` path (EXCLUDE_SUBSTR → dropped pre-disk), and a real
        un-stamped `src/app.ts` (kept). Proves drop-managed-AND-keep-real in the same pass — a
        partial-exclusion bug (early return, wrong element) would survive without this."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _stamp(repo, "scripts/check_architecture_tree.py")  # managed (stamp on line 1)
        _touch(repo, "src/app.ts")  # real, un-stamped
        _git_router(
            monkeypatch,
            in_scope=[],
            repo_wide=[
                "scripts/check_architecture_tree.py",
                "src/pkg/__init__.py",  # EXCLUDE_SUBSTR — dropped before any disk read
                "build/__pycache__/x.py",  # EXCLUDE_SUBSTR — dropped before any disk read
                "src/app.ts",
            ],
        )
        assert cat._repo_source_files() == ["src/app.ts"]
        assert cat.glob_drift(set()) == ["src/app.ts"]

    def test_extensionless_file_named_like_an_ext_is_not_source(self, repo, monkeypatch):
        """The bug-hunter's defect: a dotless file literally named `go`/`c`/`rs` (or `Makefile`,
        `LICENSE`) must NOT be misread as source — `"go".rsplit(".",1)[-1]` is `"go"`, so the
        basename-dot guard is what stops a false drift fire on such a repo."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        _git_router(
            monkeypatch,
            in_scope=[],
            repo_wide=["go", "c", "rs", "Makefile", "LICENSE", "src.dir/Makefile"],
        )
        # All dotless basenames → no real extension → not source → no drift.
        assert cat._repo_source_files() == []
        assert cat.glob_drift(set()) == []

    def test_drift_sample_is_capped_at_8_and_sorted(self, repo, monkeypatch):
        """Pins the user-facing payload's determinism: the drift sample is `sorted(...)[:8]`,
        so the quoted `drift[0]` and the cap are stable regardless of git's output order. (Stamp
        check stubbed False to isolate the cap/sort from disk.)"""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [])
        monkeypatch.setattr(cat, "EXTS", set())
        monkeypatch.setattr(cat, "_is_harness_managed", lambda _p: False)
        unsorted = [f"src/m{i}.ts" for i in (9, 2, 11, 4, 7, 1, 12, 5, 8, 3, 10, 6)]
        _git_router(monkeypatch, in_scope=[], repo_wide=unsorted)
        drift = cat.glob_drift(set())
        assert drift == sorted(unsorted)[:8]
        assert len(drift) == 8

    def test_drift_and_stale_coexist_without_masking(self, repo, monkeypatch):
        """drift is the THIRD problem class — it must neither mask nor be masked by staleness.
        Reachable when globs are non-empty but match NOTHING (EXTS non-empty → staleness live)
        while real un-globbed source exists. Assert both fire and stale is reported before drift."""
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [":(glob)src/**/*.py"])
        monkeypatch.setattr(cat, "EXTS", {"py"})
        _touch(repo, "app.ts")  # real un-globbed source → drift
        # globs match no .py (in_scope empty); the tree cites a deleted src/gone.py → stale.
        _git_router(monkeypatch, in_scope=[], repo_wide=["app.ts"])
        _write_tree(repo, "# Tree\n- `src/gone.py` — deleted, still cited.\n")
        problems, _ = cat.evaluate()
        stale_idx = next(i for i, p in enumerate(problems) if "NO LONGER EXIST" in p)
        drift_idx = next(i for i, p in enumerate(problems) if "watches no files" in p)
        assert stale_idx < drift_idx  # ordering: missing → stale → drift, no masking


# ─────────────────────────────────────────────────────────────────────────────
# main(--hook) — the `stop_hook_active` loop-breaker
# ─────────────────────────────────────────────────────────────────────────────
class TestStopHookLoopBreaker:
    def _feed_stdin(self, monkeypatch, payload: str) -> None:
        import io

        monkeypatch.setattr(cat.sys, "stdin", io.StringIO(payload))

    def test_stop_hook_active_exits_0_without_scanning(self, repo, monkeypatch, capsys):
        """FAILS on pre-fix code (`--hook` ignored `stop_hook_active`): a re-entrant Stop
        with a real, blocking problem (an undocumented in-scope file) used to re-block (exit
        2) forever. The loop-breaker exits 0 on the re-entry — the first block already
        reported — and never runs the scan (so the problem is NOT re-printed)."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n(undocumented — would be a blocking problem)\n")
        self._feed_stdin(monkeypatch, '{"stop_hook_active": true}')
        rc = cat.main(["--hook"])
        assert rc == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""  # the re-block was broken; nothing re-printed

    def test_stop_hook_inactive_still_blocks_on_problem(self, repo, monkeypatch, capsys):
        """The flip side: a FIRST stop (stop_hook_active false/absent) with a real problem
        still blocks (exit 2, stderr) — the loop-breaker must not swallow the first report."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(repo, "# Tree\n(undocumented)\n")
        self._feed_stdin(monkeypatch, '{"stop_hook_active": false}')
        rc = cat.main(["--hook"])
        assert rc == 2
        assert "MISSING an entry" in capsys.readouterr().err

    def test_empty_stdin_treated_as_not_active(self, repo, monkeypatch):
        """Manual/CI run with no payload: empty stdin → not-active → the scan runs as before.
        (Asserted directly on the helper; the full-scan path is covered above.)"""
        self._feed_stdin(monkeypatch, "")
        assert cat._stop_hook_active_from_stdin() is False

    def test_non_json_stdin_treated_as_not_active(self, repo, monkeypatch):
        """Malformed payload must NOT crash the hook — it degrades to not-active."""
        self._feed_stdin(monkeypatch, "{not valid json")
        assert cat._stop_hook_active_from_stdin() is False

    def test_non_dict_json_treated_as_not_active(self, repo, monkeypatch):
        """A well-formed but non-object JSON (e.g. a bare list) → not-active, no crash."""
        self._feed_stdin(monkeypatch, "[1, 2, 3]")
        assert cat._stop_hook_active_from_stdin() is False


# ─────────────────────────────────────────────────────────────────────────────
# _git — invocation flags (quotepath off + explicit UTF-8 decode)
# ─────────────────────────────────────────────────────────────────────────────
class TestGitInvocationFlags:
    def test_git_called_with_quotepath_off_and_utf8(self, monkeypatch):
        """FAILS on pre-fix code: `_git` invoked `["git", *args]` with `text=True` and NO
        `encoding=`. Without `-c core.quotepath=false` real git octal-escapes non-ASCII paths
        (perma-MISSING); without `encoding="utf-8"` it decodes via the host locale codepage
        (mojibake on a non-UTF-8 locale). Assert BOTH are on every invocation."""
        captured: dict = {}

        def fake_run(cmd, *_args, **kwargs):
            captured["cmd"] = cmd
            captured["encoding"] = kwargs.get("encoding")
            return _FakeCompleted(0, stdout="scripts/a.py\n")

        monkeypatch.setattr(cat, "_git", _REAL_GIT)
        monkeypatch.setattr(cat.subprocess, "run", fake_run)

        out = cat._git("ls-files")
        assert out == ["scripts/a.py"]
        # -c core.quotepath=false must sit BEFORE the subcommand (a `git -c k=v <cmd>` flag).
        cmd = captured["cmd"]
        assert cmd[:4] == ["git", "-c", "core.quotepath=false", "ls-files"], cmd
        assert captured["encoding"] == "utf-8"

    def test_undecodable_git_output_raises_runtime_error(self, monkeypatch):
        """FAILS on pre-fix code: the strict UTF-8 decode raises UnicodeDecodeError — a
        ValueError, NOT FileNotFoundError — which escaped `_git`'s handlers and bypassed the
        RuntimeError boundary every mode relies on (breaking the --hook-write "a git failure
        must NOT block a file write" contract with a raw traceback). `_git` must convert it."""

        def fake_run(*_args, **_kwargs):
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        monkeypatch.setattr(cat, "_git", _REAL_GIT)
        monkeypatch.setattr(cat.subprocess, "run", fake_run)

        with pytest.raises(RuntimeError, match="not valid UTF-8"):
            cat._git("ls-files")

    def test_hook_write_undecodable_git_output_exit_0_not_blocked(self, monkeypatch, capsys, tmp_path):
        """The --hook-write contract under the decode failure: a git failure (now including
        undecodable output) must NOT block a file write — exit 0, no traceback."""
        import io

        def fake_run(*_args, **_kwargs):
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(cat, "_git", _REAL_GIT)
        monkeypatch.setattr(cat.subprocess, "run", fake_run)
        monkeypatch.setattr(cat.sys, "stdin", io.StringIO('{"tool_input": {"file_path": "scripts/a.py"}}'))

        assert cat.main(["--hook-write"]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Real-git integration — a non-ASCII filename, end to end (no mocked _git)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.integration
class TestNonAsciiIntegration:
    def test_non_ascii_filename_not_perma_missing(self, tmp_path, monkeypatch):
        """Real git, real disk: a tracked `scripts/café.py` indexed in the tree must read as
        PRESENT. FAILS on pre-fix code — git's default `core.quotepath=true` emits the path
        octal-escaped (`"scripts/caf\\303\\251.py"`), which never matches the UTF-8 backtick
        entry, so the file is flagged MISSING forever. The quotepath+utf8 fix unquotes it.

        Hermetic: a throwaway repo under tmp_path; `_git` runs for real (NOT mocked here).
        The ambient git environment is fully isolated — GIT_CONFIG_GLOBAL/SYSTEM point at an
        empty file and gpgsign/hooks/precomposeunicode are pinned per-command — so pass/fail
        depends only on the code under test, never on this machine's git config; both sides of
        the path assertion are NFC-normalized (macOS filesystems report NFD)."""
        import subprocess as sp
        import unicodedata

        empty_cfg = tmp_path / "empty-gitconfig"
        empty_cfg.write_text("", encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_cfg))
        monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty_cfg))
        pin = ["-c", "commit.gpgsign=false", "-c", "core.hooksPath=", "-c", "core.precomposeunicode=true"]

        repo = tmp_path
        sp.run(["git", *pin, "init", "-q"], cwd=repo, check=True)
        sp.run(["git", *pin, "config", "user.email", "t@t.t"], cwd=repo, check=True)
        sp.run(["git", *pin, "config", "user.name", "t"], cwd=repo, check=True)
        scripts = repo / "scripts"
        scripts.mkdir()
        (scripts / "café.py").write_text("print('x')\n", encoding="utf-8")
        sp.run(["git", *pin, "add", "-A"], cwd=repo, check=True)
        sp.run(["git", *pin, "commit", "-qm", "add non-ascii file"], cwd=repo, check=True)

        docs = repo / "docs"
        docs.mkdir()
        (docs / "ARCHITECTURE_TREE.md").write_text(
            "# Tree\n- `scripts/café.py` — a non-ASCII filename, indexed.\n",
            encoding="utf-8",
        )

        monkeypatch.chdir(repo)
        monkeypatch.setattr(cat, "INCLUDE_GLOBS", [":(glob)scripts/**/*.py"])
        monkeypatch.setattr(cat, "EXTS", cat._exts_from_globs([":(glob)scripts/**/*.py"]))
        monkeypatch.setattr(cat, "TREE_PATH", cat.Path("docs/ARCHITECTURE_TREE.md"))

        got = {unicodedata.normalize("NFC", p) for p in cat.in_scope_files()}
        assert got == {unicodedata.normalize("NFC", "scripts/café.py")}
        problems, summary = cat.evaluate()
        assert problems == [], f"non-ASCII file wrongly flagged: {problems}"
        assert "indexes all 1 in-scope files" in summary


# ─────────────────────────────────────────────────────────────────────────────
# Fenced ```-block handling — the v0.1.26 an adopter regression
# ─────────────────────────────────────────────────────────────────────────────
class TestFencedDiagrams:
    def test_entry_after_a_fenced_diagram_is_still_found(self, repo, monkeypatch):
        """FAILS on pre-fix code: a ```-fenced ASCII directory diagram flips backtick-pair
        parity, so a correctly-formatted entry AFTER it reads as MISSING. The real adopter
        regression (an adopter's tree carries 893 lines of diagram fences)."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/after.py"])
        _touch(repo, "scripts/after.py")
        _write_tree(
            repo,
            "# Tree\n"
            "## Layout diagram\n"
            "```\n"
            "repo/\n"
            "  scripts/after.py\n"
            "```\n"
            "- `scripts/after.py` - documented AFTER the diagram, correct format.\n",
        )
        problems, summary = cat.evaluate()
        assert problems == [], f"entry after a fenced diagram wrongly flagged: {problems}"
        assert "indexes all 1 in-scope files" in summary

    def test_backticked_path_inside_a_fence_is_not_a_stale_reference(self, repo, monkeypatch):
        """A historical path backticked INSIDE a fenced changelog block must not be
        extracted as a live reference and flagged STALE — fenced content is documentation,
        not the index. FAILS on pre-fix code (TOKEN_PATTERN matched it through the fence)."""
        _set_scope(monkeypatch, [":(glob)scripts/**/*.py"], ["scripts/a.py"])
        _touch(repo, "scripts/a.py")
        _write_tree(
            repo,
            "# Tree\n"
            "- `scripts/a.py` - the live file.\n"
            "## Changelog\n"
            "```\n"
            "removed `scripts/gone.py` in an earlier release\n"
            "```\n",
        )
        problems, summary = cat.evaluate()
        assert problems == [], f"a path inside a fence was wrongly treated as live: {problems}"
        assert "indexes all 1 in-scope files" in summary
