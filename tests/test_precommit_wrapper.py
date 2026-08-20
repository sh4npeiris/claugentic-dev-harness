"""Behaviour tests for the commit-time wrapper `.githooks/pre-commit` + its `init` template.

THE WRAPPER IS A SHELL SCRIPT, so it is exercised the only honest way: by running it through a
real POSIX `sh` as a subprocess, in a scratch git repo carrying the REAL wrapper file and a
FAKE gate at the real gate path. Nothing here re-implements the wrapper's logic in Python —
every assertion is on what a commit would actually see (exit code · stdout · stderr).

Four properties are under test, all load-bearing for a team (plan 0041 Slice 5):

  1. INFRASTRUCTURE THAT CANNOT BE REACHED NEVER BLOCKS A COMMIT — a broken git (silently), no
     working Python 3.7+ (loudly), a gate script absent from the checkout (loudly). A gate that
     RUNS and fails still aborts, by design.
  2. THE INTERPRETER IS PROBED, NOT PICKED — each candidate in turn, asserting the version the
     gate scripts record for themselves. The shape that motivated it is a Windows-Store
     `python3` stub sitting BESIDE a working `python`: pick-then-probe disarms the gate on an
     ordinary machine while reporting "no Python" (Stage-7 R-1, reproduced).
  3. THE STREAM CONTRACT — a gate's stdout is CAPTURED (a clean pass prints nothing at all) and
     its stderr FLOWS THROUGH (an advisory line is visible at every commit).
  4. TEMPLATE PARITY — `skills/init/SKILL.md` claims the wrapper it tells an adopter to write is
     "run-logic identical" to the shipped one. `TestTemplateParity` makes that claim mechanical:
     drift in EITHER home turns it red.
  5. THE CHAIN (plan 0041 Slice 7) — TWO gates are wired, so run-both-and-report, the
     call-site-args rule and the derived hook-wired SET (its Python-floor obligation included)
     all become testable. `TestTheRealChainEndToEnd` closes the loop the fakes cannot: a REAL
     `git commit`, through the REAL wrapper, running the REAL doc-budget gate over a REAL
     report-only config — the only way to prove the R6 signal reaches a human's terminal.

Environment guard (anti-vacuity): `sh` is located with `shutil.which` and resolved through
`_shell_or_fail`, which is a PURE function precisely so both of its branches can be unit-tested
(`TestTheAntiVacuityGuard`) — absent locally ⇒ skip with a reason; absent under `CI` ⇒ FAIL,
because a battery that silently no-ops on the machine that gates the repo is worse than no
battery. The PATH-manipulating fixtures validate their own construction through `sh` itself
(the same resolver the wrapper uses) and fail loud if they cannot build the environment they
claim to — a stripped PATH that still resolved `python3` would make the skip cases pass for the
wrong reason, and a stub the shell refuses to execute would silently become the absent case.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"
INIT_SKILL = REPO_ROOT / "skills" / "init" / "SKILL.md"

# The gate paths the wrapper hardcodes — fake scripts are planted HERE so the real wrapper runs
# unmodified (never a rewritten copy: the file under test must be the shipped one). TWO gates
# are chained since 0041 Slice 7, and the second one is not decoration: every case below runs
# against the two-gate wrapper, because a wrapper that only ever sees one gate cannot show that
# a later gate still runs after an earlier one failed.
GATE_REL = "scripts/claugentic-check_architecture_tree.py"
BUDGET_GATE_REL = "scripts/claugentic-check_doc_budgets.py"

# The wrapper's two skip lines. Asserted as substrings so the remedy wording can be reworded
# without a false red, while the identifying half stays pinned. They must stay DISTINGUISHABLE:
# the interpreter notice speaks for every chained gate at once ("gates"), the missing-script
# notice for exactly one ("gate: <path>"), and neither is a substring of the other.
SKIP_NOTICE = "claugentic gates SKIPPED"
MISSING_GATE_NOTICE = "claugentic gate SKIPPED"

# ...and that disjointness is ASSERTED, not assumed: two cases below are written as
# `X not in stderr`, which would pass vacuously the moment one notice became a substring of
# the other (they are one character apart — "gates" vs "gate").
assert SKIP_NOTICE not in MISSING_GATE_NOTICE and MISSING_GATE_NOTICE not in SKIP_NOTICE

# A silent, passing gate — planted as the SECOND gate in every case that is really about the
# first one. Repairing the single-gate assumptions this way (rather than by loosening
# `stderr == ""` / "exactly one line" / "no missing-gate notice") is deliberate: those three
# assertions are the stream contract, and weakening them to accommodate a second gate would
# have retired the pins instead of extending them.
SILENT_PASS = "raise SystemExit(0)\n"

# The two boundaries of `init`'s never-clobber branch (3) in step 5b — the region whose PROSE
# hands an adopter a remediation. Scoping to it is load-bearing: the skill also carries the
# wrapper template itself, so an unscoped search finds the real chain line no matter what the
# remedy says. Content-anchored and asserted unique at the assertion site, never by ordinal.
NEVER_CLOBBER_ANCHOR = "**(3) Anything else → NEVER CLOBBER"
NO_WRAPPER_ANCHOR = "**A repo with NO wrapper gets NO chain"

# The husky-chain block's markers (the idempotency contract in `init`'s husky offer).
HUSKY_OPEN_MARKER = "# >>> claugentic-dev-harness tree gate"
HUSKY_CLOSE_MARKER = "# <<< claugentic-dev-harness tree gate"

# A fake gate that records the fact it ran, anchored on its OWN location (never the cwd) so the
# sentinel lands in the scratch repo root whatever directory the hook was invoked from.
GATE_SENTINEL = "gate-ran.txt"
BUDGET_SENTINEL = "budget-gate-ran.txt"


def _sentinel_write(name: str) -> str:
    return (
        "import pathlib\n"
        f"(pathlib.Path(__file__).resolve().parent.parent / {name!r}).write_text('ran')\n"
    )


_SENTINEL_WRITE = _sentinel_write(GATE_SENTINEL)
_BUDGET_SENTINEL_WRITE = _sentinel_write(BUDGET_SENTINEL)


# ─────────────────────────────────────────────────────────────────────────────
# Environment helpers
# ─────────────────────────────────────────────────────────────────────────────
def _shell_or_fail(found: str | None, ci: str | None) -> str:
    """Resolve the battery's shell, or END THE RUN — the anti-vacuity decision, isolated.

    Pure over its two inputs so BOTH branches are unit-testable. That matters more here than it
    looks: this guard is the one part of the battery that no amount of `sh` can exercise, and
    flipping `if ci:` to `if False:` would leave every case green while the battery skipped
    forever on the machine that gates the repo.
    """
    if found is not None:
        return found
    if ci:
        pytest.fail(
            "no POSIX `sh` on PATH under CI — the pre-commit wrapper battery cannot run, "
            "and a silently-skipped battery is a false green (Windows runners have Git Bash)."
        )
    pytest.skip("no POSIX `sh` on PATH (Git Bash / a Unix shell is required for this battery)")


@pytest.fixture(scope="session")
def sh() -> str:
    """A POSIX shell to run the hook with. FAILS (never skips) under CI — see `_shell_or_fail`."""
    return _shell_or_fail(shutil.which("sh") or shutil.which("bash"), os.environ.get("CI"))


def _sh_resolves(sh_path: str, env: dict[str, str], name: str) -> str:
    """What `command -v <name>` resolves to under `env` — the wrapper's OWN resolver.

    Used to VALIDATE the PATH fixtures rather than guessing with `shutil.which`: the hook asks
    `sh`, so the fixtures ask `sh` too (on Windows the shell is Git Bash, whose PATH view and
    executability rules are its own).
    """
    proc = subprocess.run(
        [sh_path, "-c", f"command -v {name} || true"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout.strip()


def _sh_runs(sh_path: str, env: dict[str, str], command: str) -> int:
    """Exit code of `command` under `env`, as `sh` sees it (fixture preconditions)."""
    return subprocess.run(
        [sh_path, "-c", command], env=env, capture_output=True, text=True, encoding="utf-8"
    ).returncode


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


@pytest.fixture
def env_without_python(sh, tmp_path) -> dict[str, str]:
    """A copy of the process env whose PATH resolves NO interpreter candidate — but still `git`.

    Built by dropping every PATH entry that holds a python executable — or a `py` launcher,
    which joined the wrapper's candidate list with Fix A: on a real Windows box `py.exe` lives
    in `C:/Windows`, so without stripping it too every "no interpreter" case would silently
    exercise the GATING branch (portable via `os.pathsep`). On Linux the strip usually drops
    `/usr/bin`, which also holds `git`, so a `git` shim is written back into a scratch dir.
    Both halves are then VERIFIED through `sh`, and an environment that cannot be built fails
    LOUD — a PATH that still resolved a candidate would make the skip-notice cases green for
    the wrong reason.
    """
    env = dict(os.environ)
    kept = []
    candidates = ("python", "python3", "py", "python.exe", "python3.exe", "py.exe")
    for entry in env.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        directory = Path(entry)
        if any((directory / name).exists() for name in candidates):
            continue
        kept.append(entry)
    path = os.pathsep.join(kept)
    env["PATH"] = path

    if not _sh_resolves(sh, env, "git"):
        real_git = shutil.which("git")
        assert real_git, "git is required to run this battery"
        shim_dir = tmp_path / "_shim_bin"
        shim_dir.mkdir(exist_ok=True)
        _write_executable(shim_dir / "git", f'#!/bin/sh\nexec "{Path(real_git).as_posix()}" "$@"\n')
        env["PATH"] = os.pathsep.join([str(shim_dir), path])

    assert _sh_resolves(sh, env, "git"), (
        "could not build a python-free PATH that still resolves `git` — the wrapper would exit "
        "at its root guard and this battery would assert the wrong branch."
    )
    for name in ("python3", "python", "py"):
        assert not _sh_resolves(sh, env, name), (
            f"`{name}` is still resolvable after stripping candidate-bearing PATH entries — the "
            "missing-interpreter cases would pass vacuously."
        )
    return env


def _stub_python3(sh_path: str, env: dict[str, str], stub_dir: Path) -> Path:
    """Plant a `python3` that EXISTS, LOGS its own invocation, and exits non-zero.

    The Windows-Store stub's exact shape, plus a log — without the log a mutant that never even
    tries `python3` (`PY=python`) passes every notice assertion while the test name claims the
    probe caught the stub. Verified through `sh`: it must RESOLVE to this file and it must FAIL,
    or the case silently degrades into the absent-interpreter branch.
    """
    stub_dir.mkdir(exist_ok=True)
    log = stub_dir / "python3-invocations.log"
    _write_executable(
        stub_dir / "python3",
        f'#!/bin/sh\nprintf "%s\\n" "invoked: $*" >> "{log.as_posix()}"\nexit 9\n',
    )
    resolved = _sh_resolves(sh_path, env, "python3")
    assert "_stub_bin" in resolved, f"`python3` did not resolve to the stub (got {resolved!r})"
    assert _sh_runs(sh_path, env, 'python3 -c ""') != 0, "the stub must FAIL its probe (exits 9)"
    return log


@pytest.fixture
def stub_python3_only(sh, env_without_python, tmp_path) -> SimpleNamespace:
    """PATH whose ONLY interpreter is the failing stub — the no-usable-Python case, loudly."""
    env = dict(env_without_python)
    stub_dir = tmp_path / "_stub_bin"
    env["PATH"] = os.pathsep.join([str(stub_dir), env["PATH"]])
    stub_dir.mkdir(exist_ok=True)
    log = _stub_python3(sh, env, stub_dir)
    return SimpleNamespace(env=env, log=log)


@pytest.fixture
def stub_python3_beside_working_python(sh, env_without_python, tmp_path) -> SimpleNamespace:
    """THE Stage-7 R-1 shape: a failing `python3` stub AND a working `python`, both on PATH.

    This is the ordinary Windows machine, and the case the first cut of this battery
    structurally could not see (its stub fixture never contained a working sibling). The wrapper
    must fall through to `python` and GATE; pick-then-probe disarms the repo permanently.
    """
    env = dict(env_without_python)
    bin_dir = tmp_path / "_stub_bin"
    bin_dir.mkdir(exist_ok=True)
    _write_executable(
        bin_dir / "python", f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "$@"\n'
    )
    env["PATH"] = os.pathsep.join([str(bin_dir), env["PATH"]])
    log = _stub_python3(sh, env, bin_dir)
    assert _sh_runs(sh, env, 'python -c "import sys; sys.exit(0)"') == 0, (
        "the working `python` sibling is not runnable — this fixture's whole point is that one "
        "candidate fails and the NEXT one works."
    )
    return SimpleNamespace(env=env, log=log)


@pytest.fixture
def py_launcher_only(sh, env_without_python, tmp_path) -> dict[str, str]:
    """THE Fix-A shape (reproduced on a real adopter box): the ONLY interpreter answers to `py`.

    Windows' installer registers the `py` launcher without putting any `python`/`python3` on
    PATH. Before `py` joined the candidate list the wrapper skipped BOTH gates -- loudly, but
    the commit landed. The shim execs the real interpreter (the working-`python` idiom above);
    `python`/`python3` stay absent (verified by `env_without_python` itself), and the shim is
    VERIFIED runnable through `sh` at the wrapper's own floor -- otherwise the case silently
    degrades into the absent-interpreter branch and passes for the wrong reason.
    """
    env = dict(env_without_python)
    bin_dir = tmp_path / "_py_bin"
    bin_dir.mkdir(exist_ok=True)
    _write_executable(
        bin_dir / "py", f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "$@"\n'
    )
    env["PATH"] = os.pathsep.join([str(bin_dir), env["PATH"]])
    resolved = _sh_resolves(sh, env, "py")
    assert "_py_bin" in resolved, f"`py` did not resolve to the shim (got {resolved!r})"
    probe = "py -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)'"
    assert _sh_runs(sh, env, probe) == 0, (
        "the `py` shim fails the wrapper's own probe -- this fixture's whole point is that the "
        "LAST candidate is the one that works."
    )
    return env


@pytest.fixture
def hook_repo(tmp_path) -> SimpleNamespace:
    """A scratch git repo carrying the REAL wrapper and two plantable fake gates.

    The wrapper is COPIED, never re-authored, so every case exercises the shipped bytes. Each
    fake gate sits at the exact path the wrapper invokes, which is what lets a test drive an
    arbitrary (exit code, stdout, stderr) triple through the real control flow.

    THE SECOND GATE IS PLANTED BENIGN BY DEFAULT (0041 Slice 7). Chaining a second `run_gate`
    line would otherwise have made three existing assertions unsatisfiable for a reason that
    has nothing to do with what they pin — a clean pass would carry a missing-script notice on
    stderr, the "exactly one line" counts would read two, and the cwd-anchor case would see a
    notice it asserts is absent. Planting a silent passer keeps every one of those assertions
    EXACTLY as strict as it was; a case that is about the budget gate overwrites it, and
    `budget_gate(None)` removes it for the missing-script case.
    """
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    (root / ".githooks").mkdir()
    shutil.copy(HOOK, root / ".githooks" / "pre-commit")
    (root / "scripts").mkdir()
    (root / BUDGET_GATE_REL).write_text(SILENT_PASS, encoding="utf-8")

    def gate(body: str) -> None:
        (root / GATE_REL).write_text(body, encoding="utf-8")

    def budget_gate(body: str | None) -> None:
        """Overwrite the second gate — or REMOVE it (`None`) for the missing-script case."""
        target = root / BUDGET_GATE_REL
        if body is None:
            target.unlink(missing_ok=True)
            return
        target.write_text(body, encoding="utf-8")

    def gate_ran() -> bool:
        return (root / GATE_SENTINEL).exists()

    def budget_gate_ran() -> bool:
        return (root / BUDGET_SENTINEL).exists()

    return SimpleNamespace(
        root=root,
        gate=gate,
        budget_gate=budget_gate,
        gate_ran=gate_ran,
        budget_gate_ran=budget_gate_ran,
    )


def _run_hook(
    sh_path: str,
    cwd: Path,
    env: dict[str, str] | None = None,
    hook: str = ".githooks/pre-commit",
) -> subprocess.CompletedProcess:
    """Run the wrapper the way git does: as a path, with a cwd inside the work tree."""
    return subprocess.run(
        [sh_path, hook],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
# T6 — the anti-vacuity guard itself (the one piece no `sh` can exercise)
# ─────────────────────────────────────────────────────────────────────────────
class TestTheAntiVacuityGuard:
    def test_a_found_shell_is_returned_unchanged(self):
        assert _shell_or_fail("/usr/bin/sh", None) == "/usr/bin/sh"

    def test_a_found_shell_is_returned_even_under_ci(self):
        assert _shell_or_fail("/usr/bin/sh", "true") == "/usr/bin/sh"

    def test_no_shell_under_ci_FAILS(self):
        # `if ci:` -> `if False:` would leave the whole battery green while skipping forever in
        # CI. This is that mutant's only oracle — and it has to CATCH the skip outcome too:
        # a bare `raises(fail.Exception)` lets the mutant's `Skipped` propagate, which pytest
        # reports as a SKIPPED test (measured: the mutant survived that way), not a failure.
        with pytest.raises((pytest.fail.Exception, pytest.skip.Exception)) as excinfo:
            _shell_or_fail(None, "true")
        assert isinstance(excinfo.value, pytest.fail.Exception), (
            "under CI an absent `sh` must FAIL the run, not skip it — a skipped battery on the "
            "machine that gates the repo is the false green this guard exists to prevent."
        )
        assert "false green" in str(excinfo.value)

    def test_no_shell_locally_SKIPS_with_a_reason(self):
        with pytest.raises((pytest.fail.Exception, pytest.skip.Exception)) as excinfo:
            _shell_or_fail(None, None)
        assert isinstance(excinfo.value, pytest.skip.Exception), (
            "off CI an absent `sh` is a legitimate skip — failing there would red-flag every "
            "contributor without a Unix shell."
        )
        assert "sh" in str(excinfo.value)


# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure that cannot be reached never blocks a commit
# ─────────────────────────────────────────────────────────────────────────────
class TestUnreachableInfrastructurePasses:
    def test_no_usable_interpreter_skips_loudly_and_passes(self, sh, hook_repo, env_without_python):
        # NON-VACUOUS: BOTH planted gates would exit 1 (blocking the commit) if either ever
        # ran, so a green here can only mean the wrapper skipped before reaching the chain —
        # the notice speaks for every chained gate at once, which is why it is worded that way.
        hook_repo.gate("raise SystemExit(1)")
        hook_repo.budget_gate("raise SystemExit(1)")
        result = _run_hook(sh, hook_repo.root, env_without_python)
        assert result.returncode == 0
        assert SKIP_NOTICE in result.stderr
        assert result.stdout == ""  # the notice is advisory, not a verdict

    def test_the_no_interpreter_notice_is_exactly_one_line(self, sh, hook_repo, env_without_python):
        # "ONE plain line on stderr" is a claim in both homes. Unpinned, dropping the probe's
        # `2>&1` resurfaces the interpreter's own cryptic error beside the notice — precisely
        # the wall this slice removes.
        hook_repo.gate("raise SystemExit(1)")
        stderr = _run_hook(sh, hook_repo.root, env_without_python).stderr
        assert len(stderr.splitlines()) == 1, stderr

    def test_a_stub_only_path_skips_loudly_and_the_stub_was_actually_probed(
        self, sh, hook_repo, stub_python3_only
    ):
        # `command -v python3` SUCCEEDS here (the stub is on PATH); only RUNNING it reveals it
        # does not work. The log is the proof the probe reached the stub — without it, a mutant
        # that never tries `python3` passes this case while the test name claims otherwise.
        hook_repo.gate("raise SystemExit(1)")
        hook_repo.budget_gate("raise SystemExit(1)")  # neither gate may run — see the sibling
        result = _run_hook(sh, hook_repo.root, stub_python3_only.env)
        assert result.returncode == 0
        assert SKIP_NOTICE in result.stderr
        assert len(result.stderr.splitlines()) == 1, result.stderr
        assert stub_python3_only.log.exists(), "the wrapper never invoked `python3` at all"
        assert "invoked:" in stub_python3_only.log.read_text(encoding="utf-8")

    def test_the_skip_notice_names_the_candidates_and_the_remedy(
        self, sh, hook_repo, env_without_python
    ):
        # A loud skip is only useful if it is true and actionable: it must name what was tried,
        # the version floor, and a remedy that works AT THIS SURFACE (a teammate at `git
        # commit`, who may not have the plugin installed at all — so never "re-run init").
        hook_repo.gate("raise SystemExit(1)")
        stderr = _run_hook(sh, hook_repo.root, env_without_python).stderr
        assert "python3, python, py" in stderr
        assert "3.7" in stderr
        assert "install Python 3" in stderr
        # ...and it must NOT send a teammate to the slash command: `init` does not bake the
        # interpreter into the hook, the reader may not have the plugin at all, and the gate
        # resumes by itself. The notice says so instead.
        assert "/claugentic-dev-harness:init" not in stderr
        assert "no re-init needed" in stderr

    def test_a_missing_gate_script_skips_loudly_and_passes(self, sh, hook_repo):
        # The gate-cannot-START boundary (Stage-7 R-2, reproduced): before the guard this was
        # rc 1 with a raw `can't open file` on stderr and an empty stdout — a commit rejected by
        # infrastructure, with the interpreter's error as its only explanation.
        # The TREE gate is the missing one here (the budget gate is the fixture's benign
        # passer), so the one-line count still pins "one plain line per unreachable gate".
        result = _run_hook(sh, hook_repo.root)  # tree gate never planted
        assert result.returncode == 0
        assert MISSING_GATE_NOTICE in result.stderr
        assert GATE_REL in result.stderr  # names WHICH gate is missing
        assert len(result.stderr.splitlines()) == 1, result.stderr
        assert result.stdout == ""
        assert not hook_repo.gate_ran()

    def test_a_missing_budget_gate_skips_loudly_and_the_tree_gate_still_runs(
        self, sh, hook_repo
    ):
        # The same boundary at the SECOND call site, which is the one that could regress
        # unnoticed: a delivery that never happened (or an adopter who deleted the script)
        # must cost a notice, not a commit — and must not take the tree gate down with it.
        hook_repo.gate(_SENTINEL_WRITE)
        hook_repo.budget_gate(None)
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 0
        assert MISSING_GATE_NOTICE in result.stderr
        assert BUDGET_GATE_REL in result.stderr  # the EXACT chained path, not a class name
        assert len(result.stderr.splitlines()) == 1, result.stderr
        assert result.stdout == ""
        assert hook_repo.gate_ran(), "a missing second gate must not skip the first"

    def test_a_failing_git_passes_SILENTLY(self, sh, tmp_path):
        # `git rev-parse --show-toplevel` fails outside a repo — the same branch a broken/absent
        # git takes. Deliberately the QUIET skip of the three: there is no repo to report into,
        # and the two registers are stated as different in both homes.
        outside = tmp_path / "not-a-repo"
        (outside / ".githooks").mkdir(parents=True)
        shutil.copy(HOOK, outside / ".githooks" / "pre-commit")
        precondition = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(outside),
            capture_output=True,
            text=True,
        )
        assert precondition.returncode != 0, f"{outside} is inside a git repo — case is vacuous"
        result = _run_hook(sh, outside)
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""


class TestTheInterpreterIsProbedNotPicked:
    """Stage-7 R-1, the reproduced defect: a failing `python3` stub BESIDE a working `python`."""

    def test_a_failing_candidate_falls_through_to_a_working_one(
        self, sh, hook_repo, stub_python3_beside_working_python
    ):
        hook_repo.gate(_SENTINEL_WRITE)  # exits 0, and records that it ran
        result = _run_hook(sh, hook_repo.root, stub_python3_beside_working_python.env)
        assert result.returncode == 0
        assert hook_repo.gate_ran(), "the gate never ran — the wrapper gave up on the stub"
        assert SKIP_NOTICE not in result.stderr  # ...and it did not claim there was no Python
        assert stub_python3_beside_working_python.log.exists()  # the stub WAS tried first

    def test_a_py_only_path_still_gates(self, sh, hook_repo, py_launcher_only):
        # Fix A's pin: with `py` the LAST candidate, a py-only box RUNS the gates -- the planted
        # always-fail gate must FAIL the commit. Before the fix the wrapper skipped loudly here
        # and the commit landed (reproduced: both planted gates never ran).
        hook_repo.gate("print('tree is stale')\nraise SystemExit(1)\n")
        result = _run_hook(sh, hook_repo.root, py_launcher_only)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "tree is stale" in result.stdout
        assert SKIP_NOTICE not in result.stderr  # it gated; it never claimed "no Python"

    def test_the_fallback_does_not_weaken_a_red_gate(
        self, sh, hook_repo, stub_python3_beside_working_python
    ):
        # The other half: falling through must not turn a failing gate into a pass.
        hook_repo.gate(_SENTINEL_WRITE + "print('tree is stale')\nraise SystemExit(1)\n")
        result = _run_hook(sh, hook_repo.root, stub_python3_beside_working_python.env)
        assert result.returncode == 1
        assert "tree is stale" in result.stdout
        assert hook_repo.gate_ran()


# ─────────────────────────────────────────────────────────────────────────────
# The stream contract: stdout captured (silent clean pass), stderr flowing through
# ─────────────────────────────────────────────────────────────────────────────
class TestGateOutcomes:
    def test_a_clean_pass_is_completely_silent(self, sh, hook_repo):
        hook_repo.gate("print('OK: 214 files indexed')\n")
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 0
        assert result.stdout == ""  # the gate's success summary is captured and discarded
        assert result.stderr == ""

    def test_the_gate_is_scoped_to_the_staged_set(self, sh, hook_repo):
        # `--staged` is the whole reason an unstaged scratch file can't block an unrelated
        # commit — and it now lives at the CALL SITE, so a gate that ignores argv is never
        # handed it. Pinned by having the fake gate report the argv it was given.
        hook_repo.gate("import sys\nprint(' '.join(sys.argv[1:]))\nraise SystemExit(1)\n")
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert "--staged" in result.stdout

    def test_a_failing_gate_aborts_and_prints_its_report(self, sh, hook_repo):
        hook_repo.gate(
            "print('docs/x.md is missing from the architecture tree')\nraise SystemExit(1)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert "docs/x.md is missing from the architecture tree" in result.stdout

    def test_advisory_output_survives_a_passing_gate(self, sh, hook_repo):
        # THE R6 case: a gate that PASSES while reporting something (a WARN band, a report-only
        # breach) must still be heard. Its stdout is captured; its stderr is not.
        hook_repo.gate(
            "import sys\n"
            "print('OK: all managed ledgers within budget')\n"
            "print('WARN: docs/LEDGER.md: 950 bytes vs budget 1000 (>= 90%)', file=sys.stderr)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 0
        assert "WARN: docs/LEDGER.md" in result.stderr
        assert result.stdout == ""  # ...and the pass stays quiet on the verdict stream

    def test_a_failing_gate_shows_both_streams(self, sh, hook_repo):
        hook_repo.gate(
            "import sys\n"
            "print('WARN: docs/LEDGER.md is close to budget', file=sys.stderr)\n"
            "print('docs/y.md is missing from the architecture tree')\n"
            "raise SystemExit(1)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert "docs/y.md" in result.stdout
        assert "WARN: docs/LEDGER.md" in result.stderr

    def test_a_gate_that_dies_without_a_word_still_aborts(self, sh, hook_repo):
        # Fail-loud floor: no output is not a reason to let a red gate through, and the wrapper
        # must not manufacture a blank line either. A gate that CRASHES ON IMPORT lands here by
        # design — present-but-broken is a repo defect, not a teammate's machine.
        hook_repo.gate("raise SystemExit(3)\n")
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert result.stdout == ""

    def test_a_gate_that_crashes_on_import_still_aborts(self, sh, hook_repo):
        hook_repo.gate("import nonexistent_module_xyz\n")
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1  # NOT graced by the missing-script skip

    def test_the_root_is_resolved_from_git_not_the_cwd(self, sh, hook_repo):
        # THE anchor pin. Every other case runs from the repo root, where a cwd-anchored mutant
        # and the real thing agree; from a SUBDIRECTORY they diverge — and with the missing-gate
        # guard in place the mutant degrades to a silent-ish skip at rc 0 instead of the abort.
        hook_repo.gate(_SENTINEL_WRITE + "print('tree is stale')\nraise SystemExit(1)\n")
        subdir = hook_repo.root / "deep" / "nested"
        subdir.mkdir(parents=True)
        result = _run_hook(sh, subdir, hook="../../.githooks/pre-commit")
        assert result.returncode == 1, result.stdout + result.stderr
        assert "tree is stale" in result.stdout
        assert hook_repo.gate_ran()
        # Unchanged in strength, and now covering BOTH call sites: `$root` is resolved once and
        # every chained gate rides it, so a cwd-anchored mutant would strand the second gate
        # too — the fixture's benign budget gate is present, so any notice here is a real one.
        assert MISSING_GATE_NOTICE not in result.stderr


class TestTheSecondChainedGate:
    """The doc-budget gate at the SECOND `run_gate` call site (0041 Slice 7).

    Everything the first call site already pins is re-pinned here on purpose: a chained gate is
    not covered by its neighbour's tests. The properties that only a SECOND gate can show are
    run-both-and-report (an earlier failure never short-circuits a later gate, and a later
    failure never masks an earlier gate's message) and the call-site-args rule (a gate that
    reads no argv is handed none).
    """

    def test_a_budget_breach_aborts_the_commit(self, sh, hook_repo):
        hook_repo.gate(_SENTINEL_WRITE)
        hook_repo.budget_gate(
            _BUDGET_SENTINEL_WRITE
            + "print('docs/LEDGER.md: 15000 bytes vs budget 14000')\nraise SystemExit(1)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert "vs budget 14000" in result.stdout  # its report is shown, not swallowed
        assert hook_repo.gate_ran() and hook_repo.budget_gate_ran()

    def test_a_red_first_gate_does_not_stop_the_second_and_both_reports_survive(
        self, sh, hook_repo
    ):
        # RUN-BOTH-AND-REPORT, the whole reason the chain is `|| rc=1` rather than `&&`.
        # MEASURED, so the comment states the right failure: dropping `|| rc=1` from the FIRST
        # line does not lose its message — the wrapper still prints it — it loses the EXIT
        # CODE, so a red tree gate would let the commit through as long as the budget gate
        # passed. Short-circuiting (`&&`) is the variant that loses the second gate's message
        # entirely. This case pins both halves at once: rc, and both reports.
        hook_repo.gate(_SENTINEL_WRITE + "print('tree is stale')\nraise SystemExit(1)\n")
        hook_repo.budget_gate(
            _BUDGET_SENTINEL_WRITE + "print('LEDGER over budget')\nraise SystemExit(1)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert hook_repo.budget_gate_ran(), "the first gate's failure short-circuited the chain"
        assert "tree is stale" in result.stdout
        assert "LEDGER over budget" in result.stdout

    def test_a_warning_from_the_passing_budget_gate_reaches_the_terminal(self, sh, hook_repo):
        # THE R6 CASE at the second call site — the one the whole grace posture rests on. A
        # report-only breach passes (exit 0) and says so on stderr; the wrapper discards a
        # passing gate's stdout, so if this line rode stdout the flag would be a silent no-op.
        hook_repo.gate(_SENTINEL_WRITE)
        hook_repo.budget_gate(
            "import sys\n"
            "print('OK: 1 report-only breach(es) NOT within budget (see WARN above)')\n"
            "print('WARN: [report-only] docs/LEDGER.md: 15000 bytes vs budget 14000', "
            "file=sys.stderr)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 0
        assert "WARN: [report-only] docs/LEDGER.md" in result.stderr
        assert result.stdout == ""  # the passing verdict stays quiet

    def test_the_budget_gate_is_handed_no_arguments(self, sh, hook_repo):
        # The call-site-args rule, in the direction that matters here: this gate reads no argv,
        # so cargo-culting `--staged` onto its line would make the wrapper header's own scoping
        # claim false and hand a flag to a gate that would ignore it.
        hook_repo.gate(_SENTINEL_WRITE)
        hook_repo.budget_gate(
            "import sys\nprint('argv=[' + ' '.join(sys.argv[1:]) + ']')\nraise SystemExit(1)\n"
        )
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert "argv=[]" in result.stdout, result.stdout


class TestWrapperIsWired:
    def test_the_shipped_wrapper_is_tracked_executable(self):
        # A hook without its exec bit is a hook git silently never runs — and the bit is what a
        # clone inherits (the same thing `init` tells an adopter to set with `chmod +x`).
        mode = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "ls-files", "-s", ".githooks/pre-commit"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.split()
        assert mode and mode[0] == "100755", f"expected mode 100755, got {mode[:1]}"

    def test_the_budget_gate_is_chained_into_the_wrapper(self):
        # WAS the strict-xfail tripwire on the stream contract's forward promise; DISCHARGED at
        # 0041 Slice 7, which chained the gate in, and kept as a permanent POSITIVE pin — the
        # stream contract in the gate's docstring and the wrapper header's "today's chained
        # gates" are only true while this holds. Never delete or invert it.
        assert "check_doc_budgets" in HOOK.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Template parity — `init`'s wrapper template vs the shipped wrapper
# ─────────────────────────────────────────────────────────────────────────────
FENCE_RE = re.compile(
    r"^(?P<indent>[ \t]*)```sh[ \t]*$(?P<body>.*?)^(?P=indent)```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _sh_fences(markdown: str) -> list[str]:
    """Every ```sh fenced block in `markdown`, dedented by its OWN fence indentation.

    The blocks live inside markdown lists, so they are indented; the closing fence must match
    the opening fence's indent (that is what keeps nested content unambiguous).
    """
    blocks = []
    for match in FENCE_RE.finditer(markdown):
        indent = match.group("indent")
        lines = match.group("body").lstrip("\n").splitlines()
        blocks.append(
            "\n".join(line[len(indent):] if line.startswith(indent) else line.lstrip() for line in lines)
        )
    return blocks


def _wrapper_template() -> str:
    """The wrapper block `init` tells an adopter to write — identified by its shebang.

    Anchored on content (`#!/bin/sh`), never on a line number or an ordinal, and asserted to be
    UNIQUE: two shebang'd blocks would mean the skill grew a second wrapper and this pin would
    silently be watching whichever came first.
    """
    shebanged = [
        b for b in _sh_fences(INIT_SKILL.read_text(encoding="utf-8")) if b.startswith("#!/bin/sh")
    ]
    # init documents TWO hook scripts, and they are told apart by CONTENT, never by ordinal:
    # the wrapper is the one that runs the gate chain; its `pre-merge-commit` sibling is the
    # one that delegates to it. Each must still be UNIQUE -- a second of either would mean the
    # skill grew a duplicate and this pin would silently watch whichever came first.
    blocks = [b for b in shebanged if "run_gate" in b]
    assert len(blocks) == 1, f"expected exactly one wrapper template in init's SKILL, found {len(blocks)}"
    return blocks[0]


def _merge_hook_template() -> str:
    """The `pre-merge-commit` block `init` tells an adopter to write -- the delegating one."""
    shebanged = [
        b for b in _sh_fences(INIT_SKILL.read_text(encoding="utf-8")) if b.startswith("#!/bin/sh")
    ]
    blocks = [b for b in shebanged if "run_gate" not in b and "exec " in b]
    assert len(blocks) == 1, f"expected exactly one merge-hook template, found {len(blocks)}"
    return blocks[0]


def _run_logic(script: str) -> list[str]:
    """A shell script's EXECUTABLE lines — the normalization this parity pin is defined on.

    Deterministic and documented, in this order:
      1. trailing whitespace is stripped from every line (invisible drift is not behaviour);
      2. blank lines are dropped (paragraphing is not behaviour);
      3. WHOLE-LINE comments are dropped — including the shebang line.
    Rule 3 is the deliberate one: the two homes carry intentionally DIFFERENT comment headers
    (a fresh adopter has no per-action hooks to "replace"), so comments are the one thing
    allowed to differ. Dropping them is what makes this a pin on RUN LOGIC rather than on prose.
    The shebang is not lost — `test_both_homes_declare_the_same_interpreter` pins it directly.

    HONEST LIMITATION: this is LINE-BASED, not a shell parser, so it assumes no construct spans
    lines in a way that makes real logic look like a comment. The realistic shape is a heredoc,
    which is refused outright below; a line-spanning quoted string would still fool it. (The
    once-considered odd-quote-count check is deliberately NOT here: an apostrophe in the skip
    notice's prose would turn the pin red for a non-behavioural reason — a live false-red traded
    for a latent false-green.)
    """
    assert "<<" not in script, (
        "the wrapper grew a heredoc — `_run_logic` is line-based and would read its body as "
        "comments/blank lines, so the parity pin could go green on genuinely divergent homes. "
        "Teach this normalizer heredocs before using one."
    )
    return [
        line.rstrip()
        for line in script.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


RUN_GATE_CALL_RE = re.compile(r"^run_gate\s+(scripts/\S+)")
# The hook's Python floor, as IT states it. Module-level so the two readers below — the
# ast/floor pin and doctor's restated-probe pin — genuinely share one spelling of "where
# the floor lives"; a second inline copy is what the comment used to claim was absent.
FLOOR_RE = re.compile(r"sys\.version_info >= \((\d+), (\d+)\)")


def _chained_gates(script: str) -> list[str]:
    """The gate scripts the wrapper actually invokes — DERIVED from its `run_gate` call sites.

    Never a hand-listed set: the hook is the single source of "what is hook-wired", so a gate
    chained in without its pins turns the derived-set assertions below red on the same commit
    instead of joining silently. Reads `_run_logic` output, so a commented-out call site (or a
    call site inside the prose header) is not mistaken for a live one.
    """
    gates = [
        match.group(1)
        for line in _run_logic(script)
        if (match := RUN_GATE_CALL_RE.match(line))
    ]
    assert gates, "no `run_gate scripts/...` call site found — the wrapper or this regex moved"
    return gates


class TestTheHookWiredSetParsesAtTheWrapperFloor:
    """THE INVARIANT, owned here: the floor the wrapper's probe demands is the SAME floor every
    **hook-wired** gate is written to — raise the wrapper's floor only when a hook-wired gate
    raises its own, and never let a hook-wired gate use syntax above it (walrus, `match`).
    Mechanized 0041 S5/S7; its `docs/claugentic-INVARIANTS.md` prose entry was retired 2026-08-19
    under that file's admission rule — this pin IS the memory now, so do not weaken it.

    Until now that invariant's second half was a hand-read: nothing parsed the sources, so a
    hook-wired gate could quietly adopt walrus/`match` syntax and the wrapper would hand a
    commit to an interpreter that dies on a SyntaxError — infrastructure blocking a commit,
    the exact failure warn-and-pass exists to remove. Both inputs are DERIVED (the gate set from
    the hook's call sites, the floor from the hook's own probe expression), so this cannot rot
    into a check of two literals nobody updates.
    """

    @staticmethod
    def _floor() -> tuple[int, int]:
        # Module-level `FLOOR_RE` — the SAME object
        # `test_doctors_restated_probe_stays_in_step_with_the_hook` reads the floor with.
        match = FLOOR_RE.search(HOOK.read_text(encoding="utf-8"))
        assert match, "the hook must state its floor as a version tuple"
        return (int(match.group(1)), int(match.group(2)))

    def test_every_chained_gate_parses_at_the_floor(self):
        floor = self._floor()
        for gate in _chained_gates(HOOK.read_text(encoding="utf-8")):
            source = (REPO_ROOT / gate).read_text(encoding="utf-8")
            ast.parse(source, filename=gate, feature_version=floor)  # SyntaxError = red

    def test_the_chained_set_is_exactly_the_two_gates(self):
        # The scoping IS the contract: this invariant binds HOOK-WIRED gates only, and the
        # repo's one 3.8-syntax script is deliberately not one of them. Pinning the set is what
        # keeps the exemption honest — a third gate chained in must be measured, not assumed.
        assert _chained_gates(HOOK.read_text(encoding="utf-8")) == [GATE_REL, BUDGET_GATE_REL]
        assert "scripts/check_shipped_content.py" not in _chained_gates(
            HOOK.read_text(encoding="utf-8")
        )

    def test_the_floor_check_has_teeth_on_the_one_excluded_script(self):
        # NON-VACUITY, in the direction that matters: if `feature_version` were ignored (or the
        # floor drifted up to 3.8+), the loop above would pass over anything. The repo's
        # walrus-carrying run-gate is the live proof that the parse really refuses — which is
        # also precisely why it must never be chained without raising the wrapper's floor.
        source = (REPO_ROOT / "scripts" / "check_shipped_content.py").read_text(encoding="utf-8")
        with pytest.raises(SyntaxError):
            ast.parse(source, feature_version=self._floor())

    def test_the_floor_is_the_one_the_gates_record_for_themselves(self):
        # Moving the floor in EITHER direction is a red: down, and a gate's recorded `# Python
        # 3.7+` requirement outruns the probe; up, and the wrapper false-skips working
        # interpreters (and doctor's restated probe goes stale — its own pin catches that half).
        assert self._floor() == (3, 7)


class TestTemplateParity:
    """`init` claims its template is run-logic identical to the shipped wrapper. Prove it."""

    def test_the_two_homes_share_one_run_logic(self):
        assert _run_logic(_wrapper_template()) == _run_logic(HOOK.read_text(encoding="utf-8"))

    def test_both_homes_declare_the_same_interpreter(self):
        # Dropped by `_run_logic` (it is a comment line by shape), so pinned on its own.
        assert HOOK.read_text(encoding="utf-8").splitlines()[0] == "#!/bin/sh"
        assert _wrapper_template().splitlines()[0] == "#!/bin/sh"

    def test_the_parity_pin_is_not_vacuous(self):
        # Guard against the two failure shapes that would make the equality above meaningless:
        # an empty/near-empty extraction, and a template that lost the properties this slice
        # exists to establish (candidate loop + version floor, the existence guard, the run_gate
        # seam, call-site args, the skip notice).
        logic = _run_logic(_wrapper_template())
        assert len(logic) >= 12, logic
        assert any("for cand in python3 python py" in line for line in logic)
        assert any("sys.version_info >= (3, 7)" in line for line in logic)
        assert any("run_gate()" in line for line in logic)
        assert any('[ ! -f "$root/$gate" ]' in line for line in logic)
        assert any(line.endswith("--staged || rc=1") for line in logic)
        # ...and its sibling: the SECOND chain line, with no args and the same `|| rc=1`.
        # Without this the parity equality above would happily agree on two homes that had
        # BOTH lost the budget gate.
        assert any(line.endswith(f"{BUDGET_GATE_REL} || rc=1") for line in logic)
        assert any(SKIP_NOTICE in line for line in logic)
        assert any(MISSING_GATE_NOTICE in line for line in logic)

    def test_the_prose_remediation_quotes_the_real_chain_line(self):
        # `init`'s never-clobber branch PRINTS a line for an adopter to paste by hand. If that
        # prose drifts from the template's actual chain line, the harness hands out an
        # instruction that does not reproduce what it would have written itself.
        # WHITESPACE-NORMALIZED, never line-scoped: the SKILL hard-wraps that sentence
        # mid-line, so a raw substring search would go green on a wrap and prove nothing.
        chain = next(
            line for line in _run_logic(_wrapper_template())
            if line.endswith(f"{BUDGET_GATE_REL} || rc=1")
        )
        # REGION-SCOPED to branch (3)'s remedy. Measured vacuous otherwise (Stage-7 round 2):
        # the WHOLE skill contains the wrapper template fence, so an unscoped search is
        # satisfied by the template's OWN chain line — deleting the quote from the remedy, or
        # drifting it to `--staged || rc=1`, left the suite green. Both anchors are asserted
        # UNIQUE so the region can never be picked by ordinal.
        skill = _init_skill_text()
        assert skill.count(NEVER_CLOBBER_ANCHOR) == 1 and skill.count(NO_WRAPPER_ANCHOR) == 1
        prose = " ".join(
            skill.split(NEVER_CLOBBER_ANCHOR, 1)[1].split(NO_WRAPPER_ANCHOR, 1)[0].split()
        )
        assert " ".join(chain.split()) in prose, chain

    def test_the_reconciliation_states_all_three_branches(self):
        # The three-branch rule is PROSE (init is a prose skill), so deleting a branch is
        # invisible to every other pin — and each branch guards a different real repo:
        # already-chained (the settled re-run), refresh (a dev-checkout-shaped wrapper), and
        # never-clobber (everything else, including every RELEASED wrapper). The shape-aware
        # half is pinned too: a v0.5.1-era wrapper has no `run_gate`, and pasting the chain
        # line into one masks the tree gate's exit status (measured at Stage 7).
        prose = " ".join(_init_skill_text().split())
        for required in (
            "ALREADY CHAINED",                      # branch 1
            "pre-commit hook already wired (budget gate chained)",
            "REFRESH IN PLACE",                     # branch 2
            "NEVER CLOBBER, and never assert authorship",  # branch 3
            "SHAPE-AWARE",
            "it may be an older harness wrapper or your own edit",
            "predates the `run_gate` shape (v0.5.1 and earlier)",
            "must not be pasted in",
        ):
            assert required in prose, required

    def test_neither_home_merges_stderr_into_the_captured_stream(self):
        # The stream contract at the text level: the GATE invocation must carry no redirection.
        # (`2>&1` is legitimate on the probe line, which deliberately discards both streams —
        # so this is asserted on the capturing line specifically, never file-wide.)
        for script in (_wrapper_template(), HOOK.read_text(encoding="utf-8")):
            capture_lines = [line for line in _run_logic(script) if "gate_out=$(" in line]
            assert len(capture_lines) == 1, capture_lines
            assert "2>&1" not in capture_lines[0]

    def test_the_version_floor_matches_what_the_gate_scripts_record(self):
        # The floor is a SECOND statement of a requirement the gate scripts already record for
        # themselves (`# Python 3.7+`). Pinning them together is what stops the wrapper drifting
        # into a floor no gate asked for — a false skip on a working interpreter. The gate set
        # is DERIVED from the hook's own call sites, so chaining a third gate brings it in here
        # automatically instead of silently leaving it unpinned.
        for gate in _chained_gates(HOOK.read_text(encoding="utf-8")):
            text = (REPO_ROOT / gate).read_text(encoding="utf-8")
            assert "Python 3.7+" in text, gate
        assert "(3, 7)" in HOOK.read_text(encoding="utf-8")

    def test_doctors_restated_probe_stays_in_step_with_the_hook(self):
        # F5 (0041 S6 code-review): doctor's SKILL restates the hook's candidate order, probe
        # expression, and floor as SECOND copies while naming the hook the source of truth —
        # this pin is what makes its "test-pinned to the hook" claim true. When the hook's
        # floor moves (S7 chains a second gate), this turns red until doctor's section moves
        # in the same change.
        hook = HOOK.read_text(encoding="utf-8")
        doctor = (REPO_ROOT / "skills" / "doctor" / "SKILL.md").read_text(encoding="utf-8")
        floor = FLOOR_RE.search(hook)
        assert floor, "the hook must state its floor as a version tuple"
        assert f"sys.version_info >= ({floor.group(1)}, {floor.group(2)})" in doctor
        assert re.search(r"for cand in python3 python py", hook), "candidate order is the hook's"
        assert "`python3` then `python` then `py`" in doctor


# ─────────────────────────────────────────────────────────────────────────────
# The husky-chain block — its GUARD semantics (run through sh) and the SKILL's own rule
# ─────────────────────────────────────────────────────────────────────────────
def _init_skill_text() -> str:
    return INIT_SKILL.read_text(encoding="utf-8")


def _husky_block() -> str:
    """The marker-guarded block `init` appends to `.husky/pre-commit` (content-anchored, unique)."""
    blocks = [b for b in _sh_fences(_init_skill_text()) if HUSKY_OPEN_MARKER in b]
    assert len(blocks) == 1, f"expected exactly one husky-chain block, found {len(blocks)}"
    return blocks[0]


def _husky_section() -> str:
    """The husky procedure's prose, from its heading bullet to the next top-level bullet.

    The rules this section states are `init`'s contract (init is a prose skill), so the tests
    below assert against THIS TEXT — not against a paraphrase living in the test file, which is
    what let the previous cut stay green while the rule was deleted from the skill.
    """
    text = _init_skill_text()
    start = text.index("- **Husky repos — OFFER to chain")
    end = text.index("\n> **Solo divergence (b)", start)
    return text[start:end]


def _chain(text: str, block: str) -> str:
    """`init`'s husky append, implemented EXACTLY as the skill states it: skip when the OPEN
    marker is present, otherwise append at end-of-file."""
    if HUSKY_OPEN_MARKER in text:
        return text
    return text.rstrip("\n") + "\n" + block.rstrip("\n") + "\n"


@pytest.fixture
def husky_hook(tmp_path) -> Path:
    """A hermetic `.husky/pre-commit` with an adopter's own content already in it."""
    path = tmp_path / ".husky" / "pre-commit"
    path.parent.mkdir(parents=True)
    path.write_text("#!/usr/bin/env sh\nnpm run lint-staged\n", encoding="utf-8")
    return path


@pytest.fixture
def husky_repo(tmp_path) -> SimpleNamespace:
    """A scratch git repo with a husky hook that ENDS with the chain block — the shape append-at-EOF
    guarantees, and the one where the guard's own exit status becomes the hook's exit status."""
    root = tmp_path / "husky-repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    hook = root / ".husky" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text(
        _chain("#!/usr/bin/env sh\nnpm run lint-staged\n", _husky_block()),
        encoding="utf-8",
        newline="\n",
    )

    def wrapper(body: str | None) -> None:
        """Plant (or leave absent) the `.githooks/pre-commit` the block points at."""
        target = root / ".githooks" / "pre-commit"
        target.parent.mkdir(exist_ok=True)
        if body is None:
            return
        _write_executable(target, body)

    return SimpleNamespace(root=root, hook=hook, wrapper=wrapper)


class TestHuskyChainSemantics:
    """What the appended block DOES — exercised through `sh`, not asserted as a substring.

    The block lands in a TRACKED file, so its failure modes are team-wide. Two properties, and
    they pull in opposite directions: a **missing** wrapper must not block anyone, while a
    **failing** wrapper must still block. The `[ -f … ] && { … }` form satisfies the second and
    breaks the first (it returns 1 from the hook's last line — measured at Stage 7), which is
    why the semantics are pinned here rather than the literal text.
    """

    def test_a_missing_wrapper_does_not_block_the_commit(self, sh, husky_repo):
        husky_repo.wrapper(None)  # the harness hook was never written / not in this checkout
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_a_failing_wrapper_still_blocks_the_commit(self, sh, husky_repo):
        husky_repo.wrapper("#!/bin/sh\nprintf '%s\\n' 'tree is stale'\nexit 1\n")
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 1
        assert "tree is stale" in result.stdout

    def test_a_passing_wrapper_leaves_the_commit_alone(self, sh, husky_repo):
        husky_repo.wrapper("#!/bin/sh\nexit 0\n")
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 0

    def test_the_real_two_gate_wrapper_reaches_the_terminal_through_husky(self, sh, husky_repo):
        # The husky path is a SECOND way a commit reaches the wrapper, and the R6 signal has to
        # survive it too: husky runs `sh "$hook"` as the hook's last statement, so a passing
        # gate's advisory line has one more hop to make. Runs the REAL wrapper with both gates
        # planted, not a stub — the stub cases above cannot see a chain regression at all.
        target = husky_repo.root / ".githooks" / "pre-commit"
        target.parent.mkdir(exist_ok=True)
        shutil.copy(HOOK, target)
        target.chmod(0o755)
        (husky_repo.root / "scripts").mkdir(exist_ok=True)
        (husky_repo.root / GATE_REL).write_text(SILENT_PASS, encoding="utf-8")
        (husky_repo.root / BUDGET_GATE_REL).write_text(
            "import sys\n"
            "print('OK: 1 report-only breach(es) NOT within budget (see WARN above)')\n"
            "print('WARN: [report-only] docs/LEDGER.md: 15000 bytes vs budget 14000', "
            "file=sys.stderr)\n",
            encoding="utf-8",
        )
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "WARN: [report-only] docs/LEDGER.md" in result.stderr

    def test_a_budget_breach_blocks_the_commit_through_husky(self, sh, husky_repo):
        # ...and the other half: `|| exit 1` in the chained block is what keeps a RED second
        # gate blocking, exactly as it does for the first.
        target = husky_repo.root / ".githooks" / "pre-commit"
        target.parent.mkdir(exist_ok=True)
        shutil.copy(HOOK, target)
        target.chmod(0o755)
        (husky_repo.root / "scripts").mkdir(exist_ok=True)
        (husky_repo.root / GATE_REL).write_text(SILENT_PASS, encoding="utf-8")
        (husky_repo.root / BUDGET_GATE_REL).write_text(
            "print('docs/LEDGER.md: 15000 bytes vs budget 14000')\nraise SystemExit(1)\n",
            encoding="utf-8",
        )
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 1
        assert "vs budget 14000" in result.stdout

    def test_the_adopters_own_hook_still_runs(self, sh, husky_repo):
        # The append must not shadow what was already there — the block is additive.
        husky_repo.hook.write_text(
            _chain("#!/usr/bin/env sh\nprintf '%s\\n' 'lint-staged ran'\n", _husky_block()),
            encoding="utf-8",
            newline="\n",
        )
        husky_repo.wrapper("#!/bin/sh\nexit 0\n")
        result = _run_hook(sh, husky_repo.root, hook=".husky/pre-commit")
        assert result.returncode == 0
        assert "lint-staged ran" in result.stdout


class TestHuskyChainRuleIsStatedInTheSkill:
    """The SKILL's own text is the contract — assert THERE, not on a test-local paraphrase.

    Deleting the "idempotent on the OPEN marker" rule from the skill used to leave every husky
    test green (only the local `_chain` helper was proving anything). These assertions fail if
    the rule is removed or inverted, which is the only way a prose contract can be pinned.
    """

    def test_the_block_carries_both_markers_and_the_guard(self):
        block = _husky_block()
        assert block.splitlines()[0].startswith(HUSKY_OPEN_MARKER)
        assert HUSKY_CLOSE_MARKER in block
        assert ".githooks/pre-commit" in block
        assert "git rev-parse --show-toplevel" in block  # worktree-safe, never a relative guess
        assert 'if [ -f "$hook" ]; then' in block  # never the `&& { … }` form (see the class above)

    def test_the_marker_is_stated_as_the_idempotency_key(self):
        section = _husky_section()
        assert "Idempotent on the OPEN marker" in section
        assert "idempotency key" in section
        assert "write nothing" in section  # the refusal, not merely "avoid duplicates"
        assert "BEFORE" in section  # ...checked BEFORE appending, on every run

    def test_the_preconditions_are_stated_in_order(self):
        # Each of these is a precondition of the next; a reader who skips one wires a
        # dependency that cannot hold (H1-H5 of the Stage-7 verdict).
        section = _husky_section()
        for required in (
            "ONLY when the tree-gate is ON",  # never chain to a wrapper that was never written
            "Read the record BEFORE asking",  # the recorded choice has a reader
            "git check-ignore -v .githooks/pre-commit",  # the wrapper must be trackable before a tracked file depends on it
            "A failed read STOPS",  # unreadable != "marker absent"
            "unconditional `exit`",  # reachability before calling it live
            "mark it executable",  # a created hook without the bit is one git silently never runs
        ):
            assert required in section, required

    def test_propagation_is_attributed_to_the_adopters_package_json(self):
        # "teammates get it for free" was the harness taking credit for npm: detection also
        # matches a bare `.husky/` dir with no `prepare` script at all.
        section = _husky_section()
        assert "package.json" in section
        assert "neither wires nor checks it" in section


class TestHuskyChainIsIdempotent:
    def test_a_second_chain_writes_nothing(self, husky_hook):
        block = _husky_block()
        once = _chain(husky_hook.read_text(encoding="utf-8"), block)
        twice = _chain(once, block)
        assert twice == once
        assert once.count(HUSKY_OPEN_MARKER) == 1
        assert once.count(HUSKY_CLOSE_MARKER) == 1

    def test_the_adopters_own_hook_content_is_preserved(self, husky_hook):
        original = husky_hook.read_text(encoding="utf-8")
        chained = _chain(original, _husky_block())
        assert chained.startswith(original.rstrip("\n"))  # append-only, byte-for-byte above
        assert "npm run lint-staged" in chained

    def test_the_guard_is_what_makes_it_idempotent(self, husky_hook):
        # THE mutation, run: drop the marker check and the second append duplicates the block.
        # Without this, `test_a_second_chain_writes_nothing` could pass on an accident.
        def chain_without_guard(text: str, block: str) -> str:
            return text.rstrip("\n") + "\n" + block.rstrip("\n") + "\n"

        block = _husky_block()
        twice = chain_without_guard(chain_without_guard(husky_hook.read_text(encoding="utf-8"), block), block)
        assert twice.count(HUSKY_OPEN_MARKER) == 2  # the defect the marker guard prevents


# ─────────────────────────────────────────────────────────────────────────────
# The chain, end to end: a REAL `git commit` running the REAL doc-budget gate
# ─────────────────────────────────────────────────────────────────────────────
REAL_BUDGET_GATE = REPO_ROOT / BUDGET_GATE_REL


@pytest.mark.integration
class TestTheRealChainEndToEnd:
    """THE R6 CLOSER — the one case with no fakes on the path that matters.

    Every other case here plants a fake gate, which proves the wrapper's control flow but says
    nothing about whether a real adopter, typing `git commit`, actually SEES a report-only
    breach. That claim spans four things at once: git invoking the hook, the wrapper's stream
    contract, the real gate's `WARN:`-to-stderr choice, and the delivered script resolving at
    the path the chain line names. Fake any one of them and the assertion stops meaning what it
    says — which is exactly how the grace flag could have shipped as a silent no-op.

    HONEST SCOPE: this exercises the ARTIFACTS `init` writes (wrapper + delivered gate + a
    seeded config), never `init` itself — `init` is a prose skill and pytest cannot run it. The
    scratch repo is assembled by hand to the shape init describes; that assembly is the part a
    human verifies at Stage 7, and it is stated here rather than implied.
    """

    @pytest.fixture
    def adopter_repo(self, tmp_path) -> Path:
        """A scratch repo wired the way `init` leaves one: hook + delivered gate + caps."""
        root = tmp_path / "adopter"
        root.mkdir()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        for key, value in (
            ("user.name", "Harness Test"),
            ("user.email", "test@example.invalid"),
            # Repo-local beats a hostile global. A contributor with `commit.gpgsign=true` in
            # their global config would otherwise see this — the suite's only real `git
            # commit` — fail at `returncode 128, gpg: signing failed`, a false RED on the one
            # test that proves the chain reaches a human's terminal.
            ("commit.gpgsign", "false"),
        ):
            subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
        # The wrapper, as init writes it, activated the way init activates it.
        subprocess.run(
            ["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True
        )
        (root / ".githooks").mkdir()
        _write_executable(root / ".githooks" / "pre-commit", HOOK.read_text(encoding="utf-8"))
        (root / "scripts").mkdir()
        # The TREE gate is stubbed silent-passing on purpose: this repo has no architecture
        # tree, and the case under test is the SECOND link in the chain. The budget gate is the
        # REAL delivered bytes — that one may not be faked or the assertion proves nothing.
        (root / GATE_REL).write_text(SILENT_PASS, encoding="utf-8")
        shutil.copy(REAL_BUDGET_GATE, root / BUDGET_GATE_REL)
        # A ledger already over its cap on day one — the shape init seeds `reportOnly` for.
        (root / "LEDGER.md").write_text("x" * 400, encoding="utf-8")
        (root / ".claude").mkdir()
        (root / ".claude" / "claugentic-doc-budgets.json").write_text(
            json.dumps({"LEDGER.md": {"max": 100, "reportOnly": True}}), encoding="utf-8"
        )
        return root

    @staticmethod
    def _commit(root: Path, message: str) -> subprocess.CompletedProcess:
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        return subprocess.run(
            ["git", "-C", str(root), "commit", "-m", message],
            capture_output=True,
            text=True,
            encoding="utf-8",  # the gate's messages carry em-dashes; a locale decode mangles them
        )

    @staticmethod
    def _head(root: Path) -> str | None:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return proc.stdout.strip() if proc.returncode == 0 else None

    def test_a_report_only_breach_is_visible_in_real_commit_output_and_the_commit_lands(
        self, sh, adopter_repo
    ):
        assert self._head(adopter_repo) is None, "precondition: nothing committed yet"
        result = self._commit(adopter_repo, "first commit")
        assert result.returncode == 0, result.stdout + result.stderr
        assert self._head(adopter_repo), "the commit did not land — the grace must not block"
        # The whole point: the breach is on screen, at exit 0, in a real commit's output.
        # WHICH STREAM, stated exactly rather than over-read: git forwards a hook's output to
        # its OWN stderr, so at THIS boundary both of the wrapper's streams arrive there. The
        # stdout/stderr split is what decides whether the line is emitted AT ALL (the wrapper
        # captures and discards a passing gate's stdout) — that half is pinned on the wrapper
        # in `TestTheSecondChainedGate`; what is proved here is that the line survives the
        # whole real path to a human's terminal.
        assert "WARN: [report-only]" in result.stderr, result.stderr
        assert "vs budget" in result.stderr, result.stderr

    def test_a_strict_breach_blocks_the_commit(self, sh, adopter_repo):
        # NON-VACUITY for the case above: with the grace removed, the SAME repo is refused —
        # so the green there is the flag doing its job, not the gate failing to measure.
        (adopter_repo / ".claude" / "claugentic-doc-budgets.json").write_text(
            json.dumps({"LEDGER.md": 100}), encoding="utf-8"
        )
        result = self._commit(adopter_repo, "first commit")
        assert result.returncode != 0
        assert self._head(adopter_repo) is None, "a blocked commit must not land"
        # The report the wrapper printed on ITS stdout arrives on git's stderr (see the sibling
        # above) — the refusal is useless without the reason, so assert the reason is there.
        assert "vs budget 100" in result.stderr, result.stdout + result.stderr


class TestTheMergeCommitHook:
    """The gates must fire on a MERGE result, not only on an ordinary commit.

    Why this class exists (0041 S7 L1, fixed here): git runs `pre-merge-commit` -- NOT
    `pre-commit` -- when a conflict-free `git merge` creates its commit. With only a
    `pre-commit` hook wired, an over-cap ledger merged clean and landed completely
    unchecked. Measured on git 2.55 before the fix: the same merge that is refused below
    returned exit 0 and committed a 14,192-byte ledger against a 14,000-byte cap.

    The pair is deliberate. The first test proves the merge is REFUSED; the second removes
    only the merge hook and proves the SAME merge then succeeds -- so the refusal is this
    hook doing its job, not the merge failing for some unrelated reason.
    """

    MERGE_HOOK = REPO_ROOT / ".githooks" / "pre-merge-commit"

    def test_the_merge_hook_delegates_rather_than_duplicating_the_chain(self):
        # DRY, and the reason it matters: a second copy of the gate list would drift the
        # moment a gate is added to one and not the other. One chain, two entry points.
        assert self.MERGE_HOOK.is_file(), "the merge hook must ship in .githooks/"
        body = self.MERGE_HOOK.read_text(encoding="utf-8")
        assert 'exec "$(dirname "$0")/pre-commit"' in body, body
        assert "run_gate" not in body, "the merge hook must delegate, never restate the chain"

    @pytest.fixture
    def merge_repo(self, tmp_path) -> Path:
        """A repo wired the way `init` leaves one, on a branch named `main`."""
        root = tmp_path / "adopter"
        root.mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(root)], check=True, capture_output=True
        )
        for key, value in (
            ("user.name", "Harness Test"),
            ("user.email", "test@example.invalid"),
            ("commit.gpgsign", "false"),
        ):
            subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True
        )
        (root / ".githooks").mkdir()
        _write_executable(root / ".githooks" / "pre-commit", HOOK.read_text(encoding="utf-8"))
        (root / "scripts").mkdir()
        # Tree gate stubbed silent-passing; the BUDGET gate is the real delivered bytes --
        # faking that one would make the assertion prove nothing.
        (root / GATE_REL).write_text(SILENT_PASS, encoding="utf-8")
        shutil.copy(REAL_BUDGET_GATE, root / BUDGET_GATE_REL)
        (root / "LEDGER.md").write_text("x" * 400, encoding="utf-8")
        (root / ".claude").mkdir()
        (root / ".claude" / "claugentic-doc-budgets.json").write_text(
            json.dumps({"LEDGER.md": {"max": 100, "reportOnly": True}}), encoding="utf-8"
        )
        return root

    def _run_merge(self, root: Path, *, with_merge_hook: bool) -> subprocess.CompletedProcess:
        """Land a passing base, branch a cap BREACH past the hook, then merge it back."""
        if with_merge_hook:
            _write_executable(
                root / ".githooks" / "pre-merge-commit",
                self.MERGE_HOOK.read_text(encoding="utf-8"),
            )
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-m", "base"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(root), "checkout", "-qb", "side"], check=True, capture_output=True
        )
        # `--no-verify` is REQUIRED to create this commit at all -- `pre-commit` correctly
        # refuses it -- which is itself the proof that the ordinary path was never the hole.
        (root / ".claude" / "claugentic-doc-budgets.json").write_text(
            json.dumps({"LEDGER.md": 100}), encoding="utf-8"
        )
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-m", "breach", "--no-verify"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "checkout", "-q", "main"], check=True, capture_output=True
        )
        return subprocess.run(
            ["git", "-C", str(root), "merge", "--no-ff", "side", "-m", "merge"],
            capture_output=True,
            text=True,
        )

    def test_a_breach_arriving_by_MERGE_is_refused(self, sh, merge_repo):
        result = self._run_merge(merge_repo, with_merge_hook=True)
        assert result.returncode != 0, (
            "a conflict-free merge carrying a cap breach must be refused\n"
            + result.stdout
            + result.stderr
        )
        # A refusal is useless without its reason -- assert the gate's own line survives.
        assert "vs budget 100" in (result.stdout + result.stderr), result.stdout + result.stderr

    def test_NON_VACUITY_without_the_merge_hook_the_same_merge_lands(self, sh, merge_repo):
        # The bug, reproduced. If this starts failing, the test above stopped proving
        # anything -- the merge would be blocked by something other than this hook.
        result = self._run_merge(merge_repo, with_merge_hook=False)
        assert result.returncode == 0, (
            "without the merge hook the breach is expected to land unchecked\n"
            + result.stdout
            + result.stderr
        )

    def test_every_shipped_hook_is_mode_755_in_the_INDEX(self):
        """A hook git cannot EXECUTE is a hook that does not run -- and git says so and carries on.
        On Linux/macOS a non-executable hook prints "not set as executable" and is SKIPPED; the
        commit or merge proceeds unchecked. Windows/Git-Bash ignores the bit, which is exactly why
        this rots silently: the mode is invisible to the platform most of this repo is developed on,
        and no other gate looks at it.

        MEASURED, 2026-08-19: `.githooks/pre-merge-commit` shipped `100644` on `main` AND on the
        built `release` branch, while its `pre-commit` sibling was `100755`. So the merge-commit
        gate -- the headline fix of the release that carried it -- did not run on macOS or Linux, in
        this repo or in any adopter's. The repo already KNEW the rule twice over: this suite's own
        release test chmods 0o755 with the comment "git IGNORES a non-executable hook on
        Linux/macOS", and `skills/init/SKILL.md` tells the adopter to `chmod +x` the merge sibling.
        The harness simply did not do to itself what it instructs everyone else to do.

        The INDEX mode is what is asserted, not the worktree's: the index is what `git archive`
        writes into the release tree and what a clone checks out. Fix with
        `git update-index --chmod=+x <path>`.

        DERIVED from the directory, never hand-listed -- a hook added later is covered on arrival.
        """
        out = subprocess.run(
            ["git", "ls-files", "-s", "--", ".githooks"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        entries = [line.split("\t", 1) for line in out.splitlines() if line.strip()]
        modes = {path: meta.split()[0] for meta, path in entries}
        assert modes, "no files tracked under .githooks/ -- this assertion is now vacuous"
        not_executable = sorted(p for p, mode in modes.items() if mode != "100755")
        assert not not_executable, (
            "these hooks are tracked NON-EXECUTABLE, so git will skip them on Linux/macOS and the "
            f"gates they chain will silently not run: {not_executable}. "
            "Fix with `git update-index --chmod=+x <path>` (the index mode, not a worktree chmod)."
        )

    def test_what_init_DOCUMENTS_matches_what_the_harness_SHIPS(self):
        # The parity that actually bites an adopter: they copy init's block, so if the shipped
        # hook and the documented one diverge, every repo init touches gets the stale one.
        # Compared on run logic, the same normalization the wrapper's own parity pin uses.
        documented = _run_logic(_merge_hook_template())
        shipped = _run_logic(self.MERGE_HOOK.read_text(encoding="utf-8"))
        assert documented == shipped, f"documented={documented!r} shipped={shipped!r}"
        # Non-vacuity: the comparison must be over a real instruction, not two empty lists.
        assert any("exec" in line for line in shipped), shipped
