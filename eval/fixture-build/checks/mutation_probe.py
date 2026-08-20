"""The vacuous-test detector: does an arm's OWN suite notice when the code stops working?

"The tests pass" is the author's word. This module gets the oracle instead: it copies the
arm's `out/` into a scratch directory, runs the arm's own suite once untouched (which must
be green, or nothing below means anything), then re-runs it with **one behaviour removed**
and reports whether the suite still passed. A suite that stays green while the behaviour it
claims to cover is gone was proving nothing.

Two removals, both applied from an injected `conftest.py` rather than by editing the arm's
source, so they work against ANY faithful implementation -- whichever module the writes or
the rendering actually live in, and however the arm arranged them:

  * the import's WRITE EFFECT is undone the moment the pinned import call returns, so its
    summary is untouched and only a test that reads the store back can notice;
  * the report RENDERER is replaced with one that returns an empty string.

It also carries the source-level half for the self-referential-test class: an AST scan for
a test that replaces the very entry point it is named for and then checks the replacement.

Nothing here scores. It returns facts (`baseline_green`, `survived`, the pinned entry
points a test replaced) and `run_sweep.py` turns them into a per-trap outcome.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

NL = chr(10)

ARM_TEST_FILE = "test_spendlog.py"

# Undo the import's effect on the store, leaving its return value alone. A test that only
# reads the returned summary sees no difference; a test that reads the store back goes red.
GUT_THE_IMPORT_WRITE_PATH = """
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importer

_original = importer.import_budget_csv


def _gutted(*args, **kwargs):
    result = _original(*args, **kwargs)
    conn = args[0] if args else kwargs.get("conn")
    if conn is not None:
        conn.execute("DELETE FROM expenses")
        conn.commit()
    return result


importer.import_budget_csv = _gutted
"""

# Replace the renderer with one that renders nothing at all.
GUT_THE_REPORT_RENDERER = """
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import report


def _gutted(*args, **kwargs):
    return ""


report.monthly_report = _gutted
"""


def run_pytest_suite(
    target: str,
    cwd: str,
    junit_path: str,
    env_extra: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run one pytest target and read the result out of its junit XML (never its stdout).

    The single source of truth for "what did pytest do" in this package -- `run_sweep.py`
    reuses it for the held-out suite. The XML is parsed rather than the terminal summary
    because a summary line is a formatting decision and an attribute is a contract.
    """
    env = dict(os.environ)
    env.update(env_extra or {})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable, "-m", "pytest", target,
            "-p", "no:cacheprovider", "-q", "--no-header",
            f"--junit-xml={junit_path}",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    result: dict[str, Any] = {
        "returncode": completed.returncode,
        "stdout_tail": (completed.stdout or "")[-2000:],
        "stderr_tail": (completed.stderr or "")[-2000:],
    }
    if not Path(junit_path).exists():
        raise RuntimeError(
            f"pytest produced no junit report at {junit_path} (returncode "
            f"{completed.returncode}). Its tail was: {result['stdout_tail']}"
        )
    suite = ET.parse(junit_path).getroot().find("testsuite")
    if suite is None:
        raise RuntimeError(f"junit report at {junit_path} carries no <testsuite> element")
    total = int(suite.get("tests", "0"))
    failures = int(suite.get("failures", "0"))
    errors = int(suite.get("errors", "0"))
    skipped = int(suite.get("skipped", "0"))
    result.update({
        "total": total,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": total - failures - errors - skipped,
        "green": completed.returncode == 0 and total > 0 and failures == 0 and errors == 0,
        "failed_cases": [
            case.get("name", "?")
            for case in suite.iter("testcase")
            if case.find("failure") is not None or case.find("error") is not None
        ],
    })
    return result


def _scratch_copy(out_dir: str, workdir: str, label: str) -> str:
    dest = os.path.join(workdir, f"arm-{label}")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(out_dir, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


def suite_survives_removal(
    out_dir: str,
    workdir: str,
    conftest_source: str,
    label: str,
) -> dict[str, Any]:
    """Run the arm's suite clean, then with one behaviour removed. Facts only.

    `survived` is the finding: the behaviour is gone and the arm's own suite still passed.
    `baseline_green` is the precondition -- when it is false the removal proves nothing and
    the caller must report the trap UNCHECKABLE rather than reading a red suite as a catch.
    """
    if not os.path.isfile(os.path.join(out_dir, ARM_TEST_FILE)):
        return {
            "bound": False,
            "why": f"the arm has no {ARM_TEST_FILE}, so it has no suite to run",
        }
    clean_dir = _scratch_copy(out_dir, workdir, f"{label}-clean")
    baseline = run_pytest_suite(
        ARM_TEST_FILE, clean_dir, os.path.join(workdir, f"{label}-baseline.xml")
    )
    mutated_dir = _scratch_copy(out_dir, workdir, f"{label}-mutated")
    _install_conftest(mutated_dir, conftest_source)
    mutated = run_pytest_suite(
        ARM_TEST_FILE, mutated_dir, os.path.join(workdir, f"{label}-mutated.xml")
    )
    return {
        "bound": True,
        "baseline_green": baseline["green"],
        "baseline": {k: baseline[k] for k in ("total", "passed", "failures", "errors")},
        "mutated": {k: mutated[k] for k in ("total", "passed", "failures", "errors")},
        "mutated_failed_cases": mutated["failed_cases"],
        # A suite that was green and now cannot COLLECT has not noticed anything -- something
        # about the run is broken, quite possibly this instrument. Reported separately from
        # `survived` so a caller can refuse to read it as a catch.
        "instrument_error": bool(baseline["green"] and mutated["errors"] > 0),
        "survived": bool(baseline["green"] and mutated["green"]),
    }


def _install_conftest(directory: str, conftest_source: str) -> None:
    """APPEND the removal to any conftest the arm already wrote -- never replace it.

    Nothing forbids an arm putting its shared fixtures in `out/conftest.py`: the brief pins
    the public surface and says internal structure is its own. Overwriting that file would
    take the arm's fixtures away, turn its suite red for a reason that has nothing to do with
    the behaviour under removal, and hand the arm a free pass on the very traps these
    removals decide -- a pass no other arm gets. So the arm's bytes are kept and ours are
    added underneath.
    """
    target = Path(directory, "conftest.py")
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    joined = (existing.rstrip() + NL + NL + conftest_source) if existing.strip() else conftest_source
    target.write_bytes(joined.encode("utf-8"))


def tests_replacing_their_own_subject(
    test_source: str, pinned_names: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Tests that substitute a pinned entry point and then check the substitute.

    The source half of the self-referential-test class, reported as evidence beside the
    behavioural half above (a suite that survives the renderer being emptied). It walks the
    arm's test module and, for each test function, collects any replacement of a pinned
    name -- `unittest.mock.patch("report.monthly_report")`, a `@patch(...)` decorator, or
    `monkeypatch.setattr(report, "monthly_report", ...)`.

    Facts only, and knowingly partial: a replacement assembled from a variable rather than
    written as a literal is invisible here. That is why the behavioural half is the one the
    trap outcome rests on -- this list is the file:line a reader needs, not the verdict.
    """
    tree = ast.parse(test_source)
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        for call in [n for n in ast.walk(node) if isinstance(n, ast.Call)]:
            target = _replacement_target(call)
            if target and any(target.endswith(name) for name in pinned_names):
                findings.append({
                    "test": node.name,
                    "line": call.lineno,
                    "replaces": target,
                })
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                target = _replacement_target(decorator)
                if target and any(target.endswith(name) for name in pinned_names):
                    findings.append({
                        "test": node.name,
                        "line": decorator.lineno,
                        "replaces": target,
                    })
    return findings


def _replacement_target(call: ast.Call) -> str | None:
    """The dotted name a `patch(...)`/`setattr(...)` call replaces, or None."""
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
    if name in {"patch", "object"} and call.args:
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
        if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
            second = call.args[1].value
            if isinstance(second, str):
                return f"{_dotted(first)}.{second}" if _dotted(first) else second
    if name == "setattr" and len(call.args) >= 2:
        second = call.args[1]
        if isinstance(second, ast.Constant) and isinstance(second.value, str):
            prefix = _dotted(call.args[0])
            return f"{prefix}.{second.value}" if prefix else second.value
    return None


def _dotted(node: ast.AST) -> str | None:
    """`report.monthly_report` for an attribute/name node; None for anything else."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None
