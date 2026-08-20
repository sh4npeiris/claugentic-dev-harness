"""Calibrate the instrument before it is allowed to measure anything.

Two halves, and the exam is only usable when both pass:

  * the **reference** -- a clean spendlog that must come back H/H on the held-out suite,
    compliant with the pinned surface, and clear of all ten traps;
  * the **mutants** -- the variants under `mutants/`, at least one per manifest row, each
    carrying exactly one of the manifest's traps, each of which must flip **its own** probe
    and **no other**.

A probe that fires on the reference is a false alarm and would blame a cut for a defect
nobody wrote. A probe that stays quiet on its own mutant is a green light that pins
nothing. A probe that fires on somebody else's mutant makes a trap table unreadable. This
script is what refuses all three -- and it is why every mechanical row of
`TRAP_MANIFEST.md` is discharged by RESOLUTION rather than by the tag being typed.

A mutant is an OVERLAY: the directory under `mutants/` holds only the files it changes, so
every file it does NOT name is byte-for-byte the reference's. The files it DOES name are
near-copies carrying the one change -- measured, not guaranteed: nothing here bounds how far
an overlaid file may drift from the reference, and a reviewer reads the diff for that.

A trap may have MORE THAN ONE mutant. The directory name is the trap id, optionally followed
by a dot and a variant slug (`<trap-id>.<slug>`), so a second shape of the same trap gets
its own case without pretending to be a second trap.

    python run_calibration.py [--only <trap id>] [--report out.json]

Exit 0 only when every expectation above held.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent
SWEEP = FIXTURE / "checks" / "run_sweep.py"
REFERENCE = HERE / "reference"
MUTANTS = HERE / "mutants"

AVOIDED = "AVOIDED"
FELL_IN = "FELL_IN"
JUDGE = "JUDGE"
NL = chr(10)


def trap_id_of(directory_name: str) -> str:
    """The trap a mutant directory carries: everything before the optional variant slug."""
    return directory_name.split(".", 1)[0]


def _trap_sort_key(name: str) -> tuple[str, int, str]:
    trap = trap_id_of(name)
    prefix, _, number = trap.rpartition("-")
    return prefix, int(number) if number.isdigit() else 0, name


def materialize(workroot: Path, label: str, overlay: Path | None) -> Path:
    """A fresh `out/` holding the reference, with `overlay`'s files copied over it."""
    out_dir = workroot / label / "out"
    shutil.copytree(
        REFERENCE, out_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    replaced: list[str] = []
    if overlay is not None:
        for path in sorted(overlay.glob("*.py")):
            shutil.copyfile(path, out_dir / path.name)
            replaced.append(path.name)
        if not replaced:
            raise RuntimeError(f"{overlay} holds no .py overlay, so it changes nothing")
    return out_dir


def run_sweep(out_dir: Path, workroot: Path, label: str) -> dict[str, Any]:
    """Run the sweep in its own interpreter, so no arm can leak state into the next."""
    workdir = workroot / label / "scratch"
    workdir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(SWEEP), "sweep", "--out", str(out_dir), "--workdir", str(workdir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"the sweep failed on {label} (exit {completed.returncode}):"
            + NL + (completed.stderr or "")[-2000:]
        )
    return json.loads(completed.stdout)


def judged_fell_in(trap_result: dict[str, Any]) -> bool:
    """The judged trap has no verdict of its own -- its EVIDENCE is what must flip."""
    return bool(trap_result.get("evidence", {}).get("candidates"))


def trap_flipped(result: dict[str, Any]) -> bool:
    if result["outcome"] == JUDGE:
        return judged_fell_in(result)
    return result["outcome"] == FELL_IN


def check_reference(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    held = report["held_out"]
    if held["total"] == 0 or held["passed"] != held["total"]:
        problems.append(
            f"the reference is not H/H on the held-out suite: {held['passed']}/{held['total']}"
            f" (failed: {held['failed_cases']})"
        )
    if not report["spec_compliance"]["compliant"]:
        problems.append(f"the reference drifts from the pinned surface: {report['spec_compliance']['drift']}")
    for trap_id, result in report["traps"].items():
        if trap_flipped(result):
            problems.append(
                f"{trap_id} fires on the CLEAN reference -- a false alarm: "
                f"{json.dumps(result['evidence'])[:300]}"
            )
        elif result["outcome"] not in (AVOIDED, JUDGE):
            problems.append(f"{trap_id} on the reference came back {result['outcome']}: "
                            f"{json.dumps(result['evidence'])[:300]}")
    return problems


def check_mutant(
    label: str, report: dict[str, Any], reference: dict[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    trap_id = trap_id_of(label)
    problems: list[str] = []
    own = report["traps"][trap_id]
    if not trap_flipped(own):
        problems.append(
            f"{label}: its own mutant did NOT flip the probe (outcome {own['outcome']}): "
            f"{json.dumps(own['evidence'])[:400]}"
        )
    cross: list[str] = []
    for other_id, result in report["traps"].items():
        if other_id == trap_id:
            continue
        if trap_flipped(result):
            cross.append(other_id)
            problems.append(
                f"{label}: cross-trip -- {other_id} also fired: "
                f"{json.dumps(result['evidence'])[:300]}"
            )
        elif result["outcome"] != reference["traps"][other_id]["outcome"]:
            problems.append(
                f"{label}: {other_id} moved to {result['outcome']} (reference: "
                f"{reference['traps'][other_id]['outcome']}): "
                f"{json.dumps(result['evidence'])[:300]}"
            )
    held = report["held_out"]
    ref_held = reference["held_out"]
    if (held["passed"], held["total"]) != (ref_held["passed"], ref_held["total"]):
        problems.append(
            f"{label}: held-out moved to {held['passed']}/{held['total']} (reference: "
            f"{ref_held['passed']}/{ref_held['total']}) -- an overlay has drifted beyond its "
            f"trap: {held['failed_cases']}"
        )
    if report["spec_compliance"]["compliant"] != reference["spec_compliance"]["compliant"]:
        problems.append(
            f"{label}: spec compliance moved to {report['spec_compliance']['compliant']} "
            f"(reference: {reference['spec_compliance']['compliant']}): "
            f"{report['spec_compliance']['drift']}"
        )
    row = {
        "trap": label,
        "own_probe": "FLIPPED" if trap_flipped(own) else "did not flip",
        "outcome": own["outcome"],
        "cross_trips": cross,
        "held_out": f"{held['passed']}/{held['total']}",
        "spec_compliant": report["spec_compliance"]["compliant"],
    }
    return problems, row


def calibrate(only: str | None, workroot: Path) -> dict[str, Any]:
    started = time.monotonic()
    overlays = sorted(
        (path for path in MUTANTS.iterdir() if path.is_dir()),
        key=lambda path: _trap_sort_key(path.name),
    )
    if not overlays:
        raise RuntimeError(f"no mutants found under {MUTANTS}")

    reference = run_sweep(materialize(workroot, "reference", None), workroot, "reference")
    problems = check_reference(reference)
    unknown = [path.name for path in overlays if trap_id_of(path.name) not in reference["traps"]]
    if unknown:
        raise RuntimeError(
            f"mutant directories name traps the sweep does not probe: {unknown}. A mutant "
            "directory is named for the trap it carries; the probe registry owns that id set."
        )
    covered = {trap_id_of(path.name) for path in overlays}
    missing = [trap for trap in reference["traps"] if trap not in covered]
    if missing and not only:
        problems.append(f"traps with no mutant, so their probes are never proven: {missing}")

    rows: list[dict[str, Any]] = []
    for overlay in overlays:
        if only and only not in (overlay.name, trap_id_of(overlay.name)):
            continue
        out_dir = materialize(workroot, overlay.name, overlay)
        report = run_sweep(out_dir, workroot, overlay.name)
        mutant_problems, row = check_mutant(overlay.name, report, reference)
        row["files"] = sorted(path.name for path in overlay.glob("*.py"))
        problems.extend(mutant_problems)
        rows.append(row)

    held = reference["held_out"]
    return {
        "H": held["total"],
        "partial": bool(only),
        "mutants_available": len(overlays),
        "reference": {
            "held_out": f"{held['passed']}/{held['total']}",
            "spec_compliant": reference["spec_compliance"]["compliant"],
            "traps": {trap: result["outcome"] for trap, result in reference["traps"].items()},
            "judged_candidates": sum(
                len(result.get("evidence", {}).get("candidates", []))
                for result in reference["traps"].values()
                if result["outcome"] == JUDGE
            ),
        },
        "mutants": rows,
        "problems": problems,
        "passed": not problems,
        "seconds": round(time.monotonic() - started, 1),
    }


def render_table(result: dict[str, Any]) -> str:
    lines = [
        "| mutant | overlay | its own probe | outcome | cross-trips | held-out | surface |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in result["mutants"]:
        lines.append(
            "| {trap} | `{files}` | {own_probe} | {outcome} | {cross} | {held_out} | {surface} |".format(
                trap=row["trap"],
                files=", ".join(row["files"]),
                own_probe=row["own_probe"],
                outcome=row["outcome"],
                cross=", ".join(row["cross_trips"]) or "none",
                held_out=row["held_out"],
                surface="compliant" if row["spec_compliant"] else "DRIFT",
            )
        )
    return NL.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split(NL)[0])
    parser.add_argument("--only", default=None, help="calibrate one trap, by its manifest id")
    parser.add_argument("--report", default=None, help="write the JSON result here")
    parser.add_argument("--workroot", default=None, help="scratch root (a temp dir by default)")
    args = parser.parse_args(argv)

    workroot = Path(args.workroot or tempfile.mkdtemp(prefix="spendlog-calibration-"))
    result = calibrate(args.only, workroot)

    print("reference: held-out {held_out} - surface {surface} - judged candidates {judged}".format(
        held_out=result["reference"]["held_out"],
        surface="compliant" if result["reference"]["spec_compliant"] else "DRIFT",
        judged=result["reference"]["judged_candidates"],
    ))
    print(render_table(result))
    print("")
    if result["problems"]:
        print("CALIBRATION FAILED:")
        for problem in result["problems"]:
            print("  - " + problem)
    elif args.only:
        print(
            f"PARTIAL (--only {args.only}): {len(result['mutants'])} of "
            f"{result['mutants_available']} mutants, completeness check skipped -- this is "
            "NOT a calibration"
        )
    else:
        print(f"CALIBRATION PASSED in {result['seconds']}s (H = {result['H']})")
    if args.report:
        Path(args.report).write_bytes((json.dumps(result, indent=2) + NL).encode("utf-8"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
