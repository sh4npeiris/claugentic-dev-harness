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

# The gate path the wrapper hardcodes — a fake script is planted HERE so the real wrapper runs
# unmodified (never a rewritten copy: the file under test must be the shipped one).
GATE_REL = "scripts/claugentic-check_architecture_tree.py"

# The wrapper's two skip lines. Asserted as substrings so the remedy wording can be reworded
# without a false red, while the identifying half stays pinned.
SKIP_NOTICE = "claugentic tree gate SKIPPED"
MISSING_GATE_NOTICE = "claugentic gate SKIPPED"

# The husky-chain block's markers (the idempotency contract in `init`'s husky offer).
HUSKY_OPEN_MARKER = "# >>> claugentic-dev-harness tree gate"
HUSKY_CLOSE_MARKER = "# <<< claugentic-dev-harness tree gate"

# A fake gate that records the fact it ran, anchored on its OWN location (never the cwd) so the
# sentinel lands in the scratch repo root whatever directory the hook was invoked from.
GATE_SENTINEL = "gate-ran.txt"
_SENTINEL_WRITE = (
    "import pathlib\n"
    f"(pathlib.Path(__file__).resolve().parent.parent / {GATE_SENTINEL!r}).write_text('ran')\n"
)


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
    """A copy of the process env whose PATH resolves NO `python`/`python3` — but still `git`.

    Built by dropping every PATH entry that holds a python executable (portable via
    `os.pathsep`). On Linux that usually drops `/usr/bin`, which also holds `git`, so a `git`
    shim is written back into a scratch dir. Both halves are then VERIFIED through `sh`, and an
    environment that cannot be built fails LOUD — a PATH that still resolved python would make
    the skip-notice cases green for the wrong reason.
    """
    env = dict(os.environ)
    kept = []
    for entry in env.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        directory = Path(entry)
        if any((directory / name).exists() for name in ("python", "python3", "python.exe", "python3.exe")):
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
    for name in ("python3", "python"):
        assert not _sh_resolves(sh, env, name), (
            f"`{name}` is still resolvable after stripping python-bearing PATH entries — the "
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
def hook_repo(tmp_path) -> SimpleNamespace:
    """A scratch git repo carrying the REAL wrapper and a plantable fake gate.

    The wrapper is COPIED, never re-authored, so every case exercises the shipped bytes. The
    fake gate sits at the exact path the wrapper invokes, which is what lets a test drive an
    arbitrary (exit code, stdout, stderr) triple through the real control flow.
    """
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    (root / ".githooks").mkdir()
    shutil.copy(HOOK, root / ".githooks" / "pre-commit")
    (root / "scripts").mkdir()

    def gate(body: str) -> None:
        (root / GATE_REL).write_text(body, encoding="utf-8")

    def gate_ran() -> bool:
        return (root / GATE_SENTINEL).exists()

    return SimpleNamespace(root=root, gate=gate, gate_ran=gate_ran)


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
        # NON-VACUOUS: the planted gate would exit 1 (blocking the commit) if it ever ran, so a
        # green here can only mean the wrapper skipped BEFORE running it.
        hook_repo.gate("raise SystemExit(1)")
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
        assert "python3, python" in stderr
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
        result = _run_hook(sh, hook_repo.root)  # no gate planted at all
        assert result.returncode == 0
        assert MISSING_GATE_NOTICE in result.stderr
        assert GATE_REL in result.stderr  # names WHICH gate is missing
        assert len(result.stderr.splitlines()) == 1, result.stderr
        assert result.stdout == ""
        assert not hook_repo.gate_ran()

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
        assert MISSING_GATE_NOTICE not in result.stderr


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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "plan 0041 Slice 7 chains the doc-budget gate into this wrapper; this flips RED the "
            "moment it lands, forcing the stream-contract copy in check_doc_budgets.py (and the "
            "wrapper header's 'today's chained gate is the tree check') out of the future tense. "
            "If Slice 7 is ever ABANDONED, do not delete this marker quietly: re-register the "
            "stream contract as tree-gate-only and reword both homes to match."
        ),
    )
    def test_the_budget_gate_is_chained_into_the_wrapper(self):
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
    blocks = [b for b in _sh_fences(INIT_SKILL.read_text(encoding="utf-8")) if b.startswith("#!/bin/sh")]
    assert len(blocks) == 1, f"expected exactly one wrapper template in init's SKILL, found {len(blocks)}"
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
        assert any("for cand in python3 python" in line for line in logic)
        assert any("sys.version_info >= (3, 7)" in line for line in logic)
        assert any("run_gate()" in line for line in logic)
        assert any('[ ! -f "$root/$gate" ]' in line for line in logic)
        assert any(line.endswith("--staged || rc=1") for line in logic)
        assert any(SKIP_NOTICE in line for line in logic)
        assert any(MISSING_GATE_NOTICE in line for line in logic)

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
        # into a floor no gate asked for — a false skip on a working interpreter.
        for gate in ("claugentic-check_architecture_tree.py", "check_doc_budgets.py"):
            text = (REPO_ROOT / "scripts" / gate).read_text(encoding="utf-8")
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
        floor = re.search(r"sys\.version_info >= \((\d+), (\d+)\)", hook)
        assert floor, "the hook must state its floor as a version tuple"
        assert f"sys.version_info >= ({floor.group(1)}, {floor.group(2)})" in doctor
        assert re.search(r"for cand in python3 python", hook), "candidate order is the hook's"
        assert "`python3` then `python`" in doctor


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
