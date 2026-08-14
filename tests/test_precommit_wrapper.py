"""Behaviour tests for the commit-time wrapper `.githooks/pre-commit` + its `init` template.

THE WRAPPER IS A SHELL SCRIPT, so it is exercised the only honest way: by running it through a
real POSIX `sh` as a subprocess, in a scratch git repo carrying the REAL wrapper file and a
FAKE gate at the real gate path. Nothing here re-implements the wrapper's logic in Python —
every assertion is on what a commit would actually see (exit code · stdout · stderr).

Three properties are under test, all load-bearing for a team (plan 0041 Slice 5):

  1. INFRASTRUCTURE FAILURE NEVER BLOCKS A COMMIT — a broken git, an absent interpreter, or an
     interpreter that exists but does not work (the Windows-Store `python3` stub) each pass
     with exit 0. The absent/stub pair is why the wrapper PROBES (`"$PY" -c ""`) instead of
     trusting `command -v`: presence alone cannot distinguish "no Python" from "the gate
     failed", and a teammate without Python had every commit blocked by a cryptic error.
  2. THE STREAM CONTRACT — a gate's stdout is CAPTURED (a clean pass prints nothing at all) and
     its stderr FLOWS THROUGH (a WARN band / report-only breach is visible at every commit).
  3. TEMPLATE PARITY — `skills/init/SKILL.md` claims the wrapper it tells an adopter to write is
     "run-logic identical" to the shipped one. `TestTemplateParity` makes that claim mechanical:
     drift in EITHER home turns it red.

Environment guard (anti-vacuity): `sh` is located with `shutil.which`. Absent locally -> skip
with a reason; absent under `CI` -> FAIL, because a battery that silently no-ops on the
machine that gates the repo is worse than no battery. The PATH-manipulating fixtures validate
their own construction through `sh` itself (the same resolver the wrapper uses) and fail loud
if they cannot build the environment they claim to — a stripped PATH that still resolved
`python3` would make the skip-notice cases pass for the wrong reason.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"
INIT_SKILL = REPO_ROOT / "skills" / "init" / "SKILL.md"

# The gate path the wrapper hardcodes — a fake script is planted HERE so the real wrapper runs
# unmodified (never a rewritten copy: the file under test must be the shipped one).
GATE_REL = "scripts/claugentic-check_architecture_tree.py"

# The wrapper's one skip line. Asserted as a substring so the remedy wording can be reworded
# without a false red, while the identifying half stays pinned.
SKIP_NOTICE = "claugentic tree gate SKIPPED"

# The husky-chain block's OPEN marker (the idempotency contract in `init`'s husky offer).
HUSKY_OPEN_MARKER = "# >>> claugentic-dev-harness tree gate"
HUSKY_CLOSE_MARKER = "# <<< claugentic-dev-harness tree gate"


# ─────────────────────────────────────────────────────────────────────────────
# Environment helpers
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def sh() -> str:
    """A POSIX shell to run the hook with. FAILS (never skips) under CI — see the module docstring."""
    found = shutil.which("sh") or shutil.which("bash")
    if found is None:
        if os.environ.get("CI"):
            pytest.fail(
                "no POSIX `sh` on PATH under CI — the pre-commit wrapper battery cannot run, "
                "and a silently-skipped battery is a false green (Windows runners have Git Bash)."
            )
        pytest.skip("no POSIX `sh` on PATH (Git Bash / a Unix shell is required for this battery)")
    return found


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


@pytest.fixture
def env_with_stub_python(sh, env_without_python, tmp_path) -> dict[str, str]:
    """A PATH whose `python3` EXISTS and exits non-zero — the Windows-Store stub's exact shape.

    Layered on `env_without_python` so the stub is the ONLY python in sight, then verified two
    ways through `sh`: it must resolve INTO the stub dir, and `python3 -c ""` must actually
    fail. Without those checks a platform that refused to treat the stub as executable would
    fall through to the missing-interpreter branch and the case would pass for the wrong reason.
    """
    stub_dir = tmp_path / "_stub_bin"
    stub_dir.mkdir(exist_ok=True)
    _write_executable(stub_dir / "python3", "#!/bin/sh\nexit 9\n")
    env = dict(env_without_python)
    env["PATH"] = os.pathsep.join([str(stub_dir), env["PATH"]])

    resolved = _sh_resolves(sh, env, "python3")
    assert "_stub_bin" in resolved, f"`python3` did not resolve to the stub (got {resolved!r})"
    probe = subprocess.run(
        [sh, "-c", 'python3 -c ""'], env=env, capture_output=True, text=True, encoding="utf-8"
    )
    assert probe.returncode != 0, "the stub interpreter must FAIL its probe (it exits 9)"
    return env


@pytest.fixture
def hook_repo(tmp_path) -> SimpleNamespace:
    """A scratch git repo carrying the REAL wrapper and a plantable fake gate.

    The wrapper is COPIED, never re-authored, so every case exercises the shipped bytes. The
    fake gate sits at the exact path the wrapper invokes, which is what lets a test drive an
    arbitrary (exit code, stdout, stderr) triple through the real control flow.
    """
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True, text=True)
    (root / ".githooks").mkdir()
    shutil.copy(HOOK, root / ".githooks" / "pre-commit")
    (root / "scripts").mkdir()

    def gate(body: str) -> None:
        (root / GATE_REL).write_text(body, encoding="utf-8")

    return SimpleNamespace(root=root, gate=gate)


def _run_hook(sh_path: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run the wrapper the way git does: as `.githooks/pre-commit`, cwd at the repo root."""
    return subprocess.run(
        [sh_path, ".githooks/pre-commit"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure failure never blocks a commit
# ─────────────────────────────────────────────────────────────────────────────
class TestInfrastructureFailurePasses:
    def test_a_missing_interpreter_skips_loudly_and_passes(self, sh, hook_repo, env_without_python):
        # NON-VACUOUS: the planted gate would exit 1 (blocking the commit) if it ever ran, so a
        # green here can only mean the wrapper skipped BEFORE running it.
        hook_repo.gate("raise SystemExit(1)")
        result = _run_hook(sh, hook_repo.root, env_without_python)
        assert result.returncode == 0
        assert SKIP_NOTICE in result.stderr
        assert result.stdout == ""  # the notice is advisory, not a verdict

    def test_a_stub_interpreter_is_caught_by_the_probe_not_mistaken_for_a_failing_gate(
        self, sh, hook_repo, env_with_stub_python
    ):
        # THE probe's reason for existing. `command -v python3` SUCCEEDS here (the stub is on
        # PATH); only running it reveals it does not work. Without the probe this repo's
        # teammates on Windows get every commit aborted with the stub's own error.
        hook_repo.gate("raise SystemExit(1)")
        result = _run_hook(sh, hook_repo.root, env_with_stub_python)
        assert result.returncode == 0
        assert SKIP_NOTICE in result.stderr

    def test_the_skip_notice_names_both_remedies(self, sh, hook_repo, env_without_python):
        # A loud skip is only useful if it says what to do about it — the wrapper's one line
        # carries both exits (install Python / re-run init), so nobody has to read the hook.
        hook_repo.gate("raise SystemExit(1)")
        stderr = _run_hook(sh, hook_repo.root, env_without_python).stderr
        assert "install Python" in stderr
        assert "claugentic-dev-harness:init" in stderr

    def test_a_failing_git_passes_without_a_word(self, sh, tmp_path):
        # `git rev-parse --show-toplevel` fails outside a repo — the same branch a broken/absent
        # git takes. A broken git must never block a commit, and has nothing useful to say.
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
        # commit — pinned by having the fake gate report the argv it was handed.
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
        # must not manufacture a blank line either.
        hook_repo.gate("raise SystemExit(3)\n")
        result = _run_hook(sh, hook_repo.root)
        assert result.returncode == 1
        assert result.stdout == ""


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
    """
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
        # exists to establish (the probe, the run_gate seam, the staged scope, the skip notice).
        logic = _run_logic(_wrapper_template())
        assert len(logic) >= 8, logic
        assert any("run_gate()" in line for line in logic)
        assert any('-c ""' in line for line in logic)
        assert any("--staged" in line for line in logic)
        assert any(SKIP_NOTICE in line for line in logic)

    def test_neither_home_merges_stderr_into_the_captured_stream(self):
        # The stream contract at the text level: the GATE invocation must carry no redirection.
        # (`2>&1` is legitimate on the probe line, which deliberately discards both streams —
        # so this is asserted on the capturing line specifically, never file-wide.)
        for script in (_wrapper_template(), HOOK.read_text(encoding="utf-8")):
            capture_lines = [line for line in _run_logic(script) if "gate_out=$(" in line]
            assert len(capture_lines) == 1, capture_lines
            assert "2>&1" not in capture_lines[0]


# ─────────────────────────────────────────────────────────────────────────────
# The husky-chain block — the marker grammar IS the idempotency contract
# ─────────────────────────────────────────────────────────────────────────────
def _husky_block() -> str:
    """The marker-guarded block `init` appends to `.husky/pre-commit` (content-anchored, unique)."""
    blocks = [b for b in _sh_fences(INIT_SKILL.read_text(encoding="utf-8")) if HUSKY_OPEN_MARKER in b]
    assert len(blocks) == 1, f"expected exactly one husky-chain block, found {len(blocks)}"
    return blocks[0]


def _chain(text: str, block: str) -> str:
    """`init`'s husky append, implemented EXACTLY as the skill states it.

    The skill's rule is prose (init is a prose skill), so what is mechanically testable is the
    rule's own grammar: skip when the OPEN marker is present, otherwise append at end-of-file.
    This helper is that rule and nothing else — the tests below drive it, so a marker that
    stopped being unique/greppable, or a block that lost its markers, turns them red.
    """
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


class TestHuskyChainIsIdempotent:
    def test_the_block_carries_both_markers_and_blocks_on_failure(self):
        block = _husky_block()
        assert block.splitlines()[0].startswith(HUSKY_OPEN_MARKER)
        assert HUSKY_CLOSE_MARKER in block
        assert ".githooks/pre-commit" in block
        assert "|| exit 1" in block  # a chained gate that can't fail the commit gates nothing
        assert "git rev-parse --show-toplevel" in block  # worktree-safe, never a relative guess

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
