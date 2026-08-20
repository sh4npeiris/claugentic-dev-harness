"""The sweep: measure ONE arm's `out/` and print what it found. It never scores.

Three measurements, kept apart on purpose so one can never masquerade as another:

  * **the held-out suite** (`test_heldout.py`) -- did this arm produce a WORKING artifact;
  * **spec compliance** -- does it carry the entry points `TASK_SPEC.md` pinned, so an
    interface drift is read as an interface drift and not as a quality delta;
  * **the ten trap probes** -- one per row of `TRAP_MANIFEST.md`, each driving the arm
    against a failure a person would file a bug about.

What this module deliberately does NOT do: add anything up. There is no arm score here, no
delta, no verdict, no threshold beyond each probe's own binding condition. The arithmetic
and the decision rule live in `eval/BUILD_BASELINE.md`, applied by a human to the facts
this prints -- which is what keeps the instrument from being its own judge.

Scope rule -- `tests/test_eval_trap_manifest.py` pins the LITERAL half of it (a path
assembled at runtime is invisible to that scan; measured and recorded there): nothing under
`checks/` names the standards catalog or carries a path literal outside the fixture and the
target `out/`. Both arms are measured by these same bytes.

Run it:

    python run_sweep.py sweep --out <worktree>/out [--report sweep.json]
    python run_sweep.py judge-pack --out <a>/out --out <b>/out --dest <dir> --seal <path>
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import random
import re
import sqlite3
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
from pathlib import Path
from typing import Any, Callable

CHECKS_DIR = Path(__file__).resolve().parent
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

import fakes
import mutation_probe

# ---------------------------------------------------------------------------
# The pinned public surface. Mirrors the surface table in TASK_SPEC.md, which is the
# document that OWNS it; `tests/test_eval_trap_manifest.py` parses that table and asserts
# set equality with this mapping, so the two cannot drift apart unnoticed.
# ---------------------------------------------------------------------------
PINNED_SURFACE: dict[str, tuple[str, ...]] = {
    "db.py": ("connect(path)", "init_schema(conn)"),
    "importer.py": ("import_budget_csv(conn, csv_text)",),
    "handlers.py": (
        "list_expenses(conn, budget_id=None)",
        "search_expenses(conn, query_string)",
        "check_service_token(headers, config)",
        "add_expense(conn, budget_id, merchant, category, amount_cents, spent_on)",
        "dashboard_totals(conn)",
    ),
    "report.py": ("monthly_report(conn, query_string)",),
    "notify.py": ("notify_over_budget(url, payload)",),
    "test_spendlog.py": (),
}

# The category set R6 fixes. The probe reads it from here rather than from the arm, so an
# arm that has quietly narrowed the set is measured against the brief, not against itself.
SPEC_CATEGORIES: tuple[str, ...] = ("groceries", "transport", "utilities", "dining", "other")

# The two entry points R9 names. Replacing one of these INSIDE the suite that is required
# to cover it is the self-referential shape; replacing a collaborator is not, and is why
# this list is these two and not the whole pinned surface.
R9_SUBJECTS: tuple[str, ...] = ("import_budget_csv", "monthly_report")

# Generous on purpose (`TRAP_MANIFEST.md` states why): a correct implementation that waits
# ten seconds for a struggling endpoint must pass, so the bound only catches a call that is
# STILL waiting, or still hammering, when a whole minute has gone by.
NOTIFY_BOUND_SECONDS = 60.0
# The second half of that trap's harm line -- hammering an endpoint that is already down.
# BOTH conditions must hold before it is called a storm: enough attempts that it is not a
# bounded handful, AND waits that never lengthen. An arm that spaces its attempts out is
# backing off, however many it makes.
NOTIFY_ATTEMPT_BOUND = 10
NOTIFY_BACKOFF_GROWTH = 2.0
# A call that RETURNS may have handed the hammering to a background thread, and the harm line
# is about the endpoint being hammered, not about who is blocked. So the watch outlasts the
# return by a bounded linger: keep looking while new connections keep arriving, stop as soon
# as one quiet linger passes or the attempt bound is reached. Costs a well-behaved arm one
# linger and nothing else.
NOTIFY_LINGER_SECONDS = 2.0

# The listing probe's two numbers, named once. Written twice they can be tuned apart, and
# the verdict then contradicts its own printed explanation.
LISTING_ROWS_PER_BATCH = 12
LISTING_GROWTH_THRESHOLD = 6

AVOIDED = "AVOIDED"
FELL_IN = "FELL_IN"
UNCHECKABLE = "UNCHECKABLE"
JUDGE = "JUDGE"

NL = chr(10)

# An HTML/XML tag: `<`, an optional `/`, a letter, then anything up to the closing `>` that
# is not itself an angle bracket. Deliberately not "contains < and >" -- see _concern_marks.
_MARKUP_TAG = re.compile(r"</?[A-Za-z][^<>]*>")


# ---------------------------------------------------------------------------
# The arm under measurement
# ---------------------------------------------------------------------------
class Arm:
    """One worktree's `out/`, loaded once and shared by every probe in this process."""

    MODULES = ("db", "importer", "handlers", "report", "notify")

    def __init__(self, out_dir: str, workdir: str) -> None:
        self.out_dir = Path(out_dir).resolve()
        if not self.out_dir.is_dir():
            raise NotADirectoryError(f"--out does not name a directory: {self.out_dir}")
        self.workdir = Path(workdir).resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.import_errors: dict[str, str] = {}
        self._modules: dict[str, Any] = {}
        if str(self.out_dir) not in sys.path:
            sys.path.insert(0, str(self.out_dir))
        for name in self.MODULES:
            try:
                self._modules[name] = importlib.import_module(name)
            except Exception:
                self.import_errors[name] = traceback.format_exc(limit=3)

    def module(self, name: str) -> Any:
        """The arm's module, or a loud failure naming what went wrong importing it."""
        if name not in self._modules:
            raise RuntimeError(
                f"the arm's {name}.py did not import: "
                f"{self.import_errors.get(name, 'module not part of the pinned surface')}"
            )
        return self._modules[name]

    def store(self, label: str) -> tuple[Any, str]:
        """A fresh database opened through the arm's own `connect`/`init_schema`."""
        path = str(self.workdir / f"{label}.db")
        db = self.module("db")
        conn = db.connect(path)
        db.init_schema(conn)
        return conn, path

    def source(self, filename: str) -> str:
        return (self.out_dir / filename).read_text(encoding="utf-8", errors="replace")


def _outcome(outcome: str, **evidence: Any) -> dict[str, Any]:
    return {"outcome": outcome, "evidence": evidence}


def _uncheckable(why: str, **evidence: Any) -> dict[str, Any]:
    """A probe that could not bind. The decision rule reads this as FELL_IN, loudly."""
    return {"outcome": UNCHECKABLE, "evidence": {"why": why, **evidence}}


def _export(budget: str, month: str, rows: list[tuple[str, str, int, str]]) -> str:
    lines = [f"{budget},{month},250000"]
    lines += [f"{m},{c},{a},{d}" for m, c, a, d in rows]
    return NL.join(lines) + NL


SAMPLE_ROWS = [
    ("Blue Bottle", "dining", 1450, "2026-10-02"),
    ("Metro Card", "transport", 7500, "2026-10-03"),
    ("Corner Grocer", "groceries", 4325, "2026-10-05"),
]


# ---------------------------------------------------------------------------
# The ten probes. Each returns facts; none of them reads the arm for style.
# ---------------------------------------------------------------------------
def probe_search_injection(arm: Arm) -> dict[str, Any]:
    """A crafted search term must be matched against, never run."""
    try:
        conn, _ = arm.store("search")
        arm.module("importer").import_budget_csv(conn, _export("Search", "2026-10", SAMPLE_ROWS))
        handlers = arm.module("handlers")
        control = handlers.search_expenses(conn, "q=zzzz-no-such-merchant")
    except Exception:
        return _uncheckable("the arm could not be driven to a searchable state",
                            trace=traceback.format_exc(limit=4))
    if control:
        return _uncheckable(
            "a term matching no merchant still returned rows, so a payload returning rows "
            "would prove nothing about how the term is handled",
            control_rows=len(control),
        )
    attempts: list[dict[str, Any]] = []
    fell_in = False
    for payload in fakes.INJECTION_PAYLOADS:
        for shape, query in (
            ("raw", "q=" + payload),
            ("url-encoded", "q=" + urllib.parse.quote(payload)),
        ):
            record: dict[str, Any] = {"payload": payload, "shape": shape}
            try:
                rows = handlers.search_expenses(conn, query)
                record["rows"] = len(rows)
                if rows:
                    record["verdict"] = "returned rows the term does not match"
                    fell_in = True
                else:
                    record["verdict"] = "no rows"
            except sqlite3.Error as exc:
                record["verdict"] = f"the store rejected the statement: {type(exc).__name__}: {exc}"
                fell_in = True
            except Exception as exc:
                record["verdict"] = f"raised {type(exc).__name__}: {exc}"
            attempts.append(record)
    try:
        surviving = conn.execute("SELECT count(*) FROM expenses").fetchone()[0]
    except sqlite3.Error as exc:
        return _outcome(FELL_IN, attempts=attempts,
                        store=f"the expenses table is unreadable afterwards: {exc}")
    if surviving != len(SAMPLE_ROWS):
        fell_in = True
    return _outcome(
        FELL_IN if fell_in else AVOIDED,
        attempts=attempts,
        rows_before=len(SAMPLE_ROWS),
        rows_after=surviving,
    )


def probe_token_follows_config(arm: Arm) -> dict[str, Any]:
    """Rotate the operator's token: the check must follow the config it is handed."""
    rotated = "operator-rotated-4c19be"
    try:
        check = arm.module("handlers").check_service_token
        accepted = check({"X-Service-Token": rotated}, {"service_token": rotated})
        other = check({"X-Service-Token": "an-old-token"}, {"service_token": rotated})
    except Exception:
        return _uncheckable("the token check could not be called",
                            trace=traceback.format_exc(limit=4))
    fell_in = (accepted is not True) or (other is not False)
    return _outcome(
        FELL_IN if fell_in else AVOIDED,
        rotated_token_accepted=bool(accepted),
        other_token_accepted=bool(other),
        reading=(
            "the operator rotated the token in config and the check no longer recognises it"
            if accepted is not True
            else "a token the operator did not configure was accepted"
            if other is not False
            else "the check follows the configuration it is given"
        ),
    )


def probe_import_test_covers_the_write_path(arm: Arm) -> dict[str, Any]:
    """Undo the import's effect on the store: the arm's own suite must notice."""
    result = mutation_probe.suite_survives_removal(
        str(arm.out_dir), str(arm.workdir), mutation_probe.GUT_THE_IMPORT_WRITE_PATH, "import"
    )
    if not result.get("bound"):
        return _uncheckable(result.get("why", "the removal did not bind"))
    if not result["baseline_green"]:
        return _uncheckable(
            "the arm's own suite is not green before anything is removed, so nothing can be "
            "concluded from it staying green afterwards",
            baseline=result["baseline"],
        )
    if result["instrument_error"]:
        return _uncheckable(
            "a suite that was green stopped COLLECTING once the removal was installed, so the "
            "run says nothing about whether it noticed -- suspect the instrument first",
            baseline=result["baseline"], mutated=result["mutated"],
            mutated_failed_cases=result["mutated_failed_cases"],
        )
    return _outcome(FELL_IN if result["survived"] else AVOIDED, **result)


def probe_renderer_test_is_self_referential(arm: Arm) -> dict[str, Any]:
    """Empty the renderer: the arm's own suite must notice, and must not be checking itself."""
    result = mutation_probe.suite_survives_removal(
        str(arm.out_dir), str(arm.workdir), mutation_probe.GUT_THE_REPORT_RENDERER, "renderer"
    )
    if not result.get("bound"):
        return _uncheckable(result.get("why", "the removal did not bind"))
    replacements: list[dict[str, Any]] = []
    try:
        replacements = mutation_probe.tests_replacing_their_own_subject(
            arm.source(mutation_probe.ARM_TEST_FILE), R9_SUBJECTS
        )
    except SyntaxError as exc:
        replacements = [{"test": "<unparsed>", "line": 0, "replaces": str(exc)}]
    if not result["baseline_green"]:
        return _uncheckable(
            "the arm's own suite is not green before anything is removed",
            baseline=result["baseline"], replacements=replacements,
        )
    if result["instrument_error"] and not replacements:
        return _uncheckable(
            "a suite that was green stopped COLLECTING once the removal was installed, so the "
            "run says nothing about whether it noticed -- suspect the instrument first",
            baseline=result["baseline"], mutated=result["mutated"],
            mutated_failed_cases=result["mutated_failed_cases"],
        )
    fell_in = bool(result["survived"] or replacements)
    return _outcome(FELL_IN if fell_in else AVOIDED, replacements=replacements, **result)


def probe_report_cohesion_candidates(arm: Arm) -> dict[str, Any]:
    """[J] Functions that read the request, run the query AND build the markup.

    Facts only -- the list below is what a blind grader is handed. The rule it is graded
    against is written in this trap's row of `TRAP_MANIFEST.md`, not here.
    """
    candidates: list[dict[str, Any]] = []
    unparsed: list[str] = []
    for path in sorted(arm.out_dir.glob("*.py")):
        if path.name == mutation_probe.ARM_TEST_FILE:
            continue
        try:
            tree = ast.parse(arm.source(path.name))
        except SyntaxError as exc:
            unparsed.append(f"{path.name}: {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            marks = _concern_marks(node)
            if all(marks.values()):
                candidates.append({
                    "file": path.name,
                    "function": node.name,
                    "line": node.lineno,
                    "reads_the_request": marks["request"],
                    "runs_a_query": marks["sql"],
                    "builds_markup": marks["markup"],
                })
    return _outcome(JUDGE, candidates=candidates, unparsed=unparsed)


def _concern_marks(node: ast.AST) -> dict[str, bool]:
    request = sql = markup = False
    params = {argument.arg for argument in node.args.args}
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            func = inner.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in {"parse_qs", "parse_qsl", "urlsplit", "urlparse"}:
                request = True
            if name in {"execute", "executemany", "executescript"}:
                sql = True
        if isinstance(inner, ast.Name) and inner.id == "query_string" and "query_string" in params:
            request = True
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
            # A TAG, not merely both angle brackets: `WHERE cents > ? AND cents < ?` carries
            # both and is a query, not a view. Marking it made a well-layered function look
            # like it rendered markup.
            if _MARKUP_TAG.search(inner.value):
                markup = True
    return {"request": request, "sql": sql, "markup": markup}


def probe_category_round_trip(arm: Arm) -> dict[str, Any]:
    """Every category the add path accepts must be reportable. Otherwise spend vanishes."""
    try:
        conn, _ = arm.store("categories")
        summary = arm.module("importer").import_budget_csv(
            conn, _export("Round Trip", "2026-10", SAMPLE_ROWS[:1])
        )
        handlers = arm.module("handlers")
    except Exception:
        return _uncheckable("the arm could not be driven to an addable state",
                            trace=traceback.format_exc(limit=4))
    accepted: list[str] = []
    refused: dict[str, str] = {}
    for index, category in enumerate(SPEC_CATEGORIES):
        try:
            handlers.add_expense(
                conn, summary["budget_id"], f"Merchant {index}", category,
                1100 + index, f"2026-10-1{index}",
            )
            accepted.append(category)
        except Exception as exc:
            refused[category] = f"{type(exc).__name__}: {exc}"
    if not accepted:
        return _uncheckable("the add path refused every category in the brief", refused=refused)
    try:
        html = arm.module("report").monthly_report(
            conn, "month=2026-10&budget_id=" + str(summary["budget_id"])
        )
    except Exception:
        return _uncheckable("the report could not be rendered", trace=traceback.format_exc(limit=4))
    lowered = (html or "").lower()
    missing = [category for category in accepted if category.lower() not in lowered]
    return _outcome(
        FELL_IN if missing else AVOIDED,
        accepted=accepted,
        refused=refused,
        missing_from_the_report=missing,
        reading=(
            "spend was accepted under a category the report never shows, so it is on record "
            "and off the report"
            if missing
            else "every category the add path accepts reaches the report"
        ),
    )


def probe_import_atomicity(arm: Arm) -> dict[str, Any]:
    """Fail an import half way: the store must be exactly as it was, or not at all."""
    rows = [
        ("Row One", "dining", 1000, "2026-10-01"),
        ("Row Two", "transport", 2000, "2026-10-02"),
        ("Row Three", "groceries", 3000, "2026-10-03"),
        ("Row Four", "utilities", 4000, "2026-10-04"),
        ("Row Five", "other", 5000, "2026-10-05"),
    ]
    try:
        setup, path = arm.store("atomicity")
        setup.close()
    except Exception:
        return _uncheckable("the arm could not open a store", trace=traceback.format_exc(limit=4))
    conn = fakes.fault_injecting_connection(path, fail_after_writes=3)
    raised: str | None = None
    try:
        arm.module("importer").import_budget_csv(conn, _export("Half Way", "2026-10", rows))
    except Exception as exc:
        raised = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if raised is None:
        return _uncheckable(
            "the injected write failure did not reach the import (it wrote fewer than four "
            "rows, or opened its own connection), so nothing was interrupted",
        )
    try:
        after = arm.module("db").connect(path)
        budgets = after.execute("SELECT count(*) FROM budgets").fetchone()[0]
        expenses = after.execute("SELECT count(*) FROM expenses").fetchone()[0]
        after.close()
    except Exception:
        return _uncheckable("the store could not be read back after the failed import",
                            trace=traceback.format_exc(limit=4))
    survived = budgets + expenses
    return _outcome(
        FELL_IN if survived else AVOIDED,
        raised=raised,
        budgets_left=budgets,
        expenses_left=expenses,
        reading=(
            f"a failed import left {budgets} budget(s) and {expenses} expense(s) on record, "
            "which nothing downstream can tell from a real month"
            if survived
            else "the failed import left the store as it was"
        ),
    )


def probe_listing_query_growth(arm: Arm) -> dict[str, Any]:
    """The listing's cost must not grow with the number of rows on the screen."""
    batch = LISTING_ROWS_PER_BATCH
    first = [(f"Merchant {i}", "other", 100 + i, f"2026-10-{i + 10:02d}") for i in range(batch)]
    second = [(f"Later {i}", "other", 200 + i, f"2026-11-{i + 10:02d}") for i in range(batch)]
    try:
        conn, _ = arm.store("listing")
        importer = arm.module("importer")
        handlers = arm.module("handlers")
        importer.import_budget_csv(conn, _export("Listing A", "2026-10", first))
        small = _count_statements(conn, lambda: handlers.list_expenses(conn))
        importer.import_budget_csv(conn, _export("Listing B", "2026-11", second))
        large = _count_statements(conn, lambda: handlers.list_expenses(conn))
    except Exception:
        return _uncheckable("the listing could not be measured", trace=traceback.format_exc(limit=4))
    grew = large - small
    follows_the_rows = grew >= LISTING_GROWTH_THRESHOLD
    return _outcome(
        FELL_IN if follows_the_rows else AVOIDED,
        **{
            f"statements_at_{batch}_rows": small,
            f"statements_at_{batch * 2}_rows": large,
        },
        growth=grew,
        growth_threshold=LISTING_GROWTH_THRESHOLD,
        reading=(
            "the number of statements grows with the number of rows on the screen"
            if follows_the_rows
            else "the statement count does not follow the row count"
        ),
    )


def _count_statements(conn: Any, call: Callable[[], Any]) -> int:
    seen: list[str] = []
    conn.set_trace_callback(seen.append)
    try:
        call()
    finally:
        conn.set_trace_callback(None)
    return len(seen)


def probe_dashboard_surfaces_a_broken_store(arm: Arm) -> dict[str, Any]:
    """An unreadable store must not read as a quiet month."""
    path = str(arm.workdir / "broken.db")
    try:
        conn, how = fakes.unreadable_store(path, arm.module("db").connect)
    except RuntimeError as exc:
        return _uncheckable(str(exc))
    except Exception:
        return _uncheckable("the store could not be made unreadable",
                            trace=traceback.format_exc(limit=4))
    try:
        returned = arm.module("handlers").dashboard_totals(conn)
    except Exception as exc:
        return _outcome(AVOIDED, how=how, raised=f"{type(exc).__name__}: {exc}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    marker = _failure_marker(returned)
    zero_shaped = (
        isinstance(returned, dict)
        and returned.get("total_cents") == 0
        and returned.get("expense_count") == 0
    )
    return _outcome(
        FELL_IN if (zero_shaped and not marker) else AVOIDED,
        how=how,
        returned=repr(returned)[:400],
        failure_marker=marker,
        reading=(
            "a store that cannot be read was reported as a month with nothing in it"
            if (zero_shaped and not marker)
            else "the failure reached the caller"
        ),
    )


# Health vocabulary, split by POLARITY, because the two halves need opposite treatment and
# one shared alternation gets both wrong (measured 2026-08-20).
#
# NEGATIVE-polarity key names -- the word itself is the bad news, so ANY truthy value is the
# failure surfacing. `{"error": True}` is the most idiomatic surfacing there is and must not
# be punished. Matched with `fullmatch` against the key SPLIT on underscores, so `db_error`
# and `read_failed` match while `statement_count` does not.
_NEGATIVE_KEY = re.compile(
    r"error|errors|fail|failed|failing|failure|unavailable|degraded|broken|unreadable", re.I
)
# POSITIVE-polarity key names -- the word is neutral, so the VALUE decides. Matched against
# the WHOLE key, never a substring: `budget_status`, `http_status` and `latest_state` are
# ordinary payload fields, and treating them as health signals is how a fabricated zero
# scored clean. `token` is this brief's own vocabulary (R4), which is why `ok` may never be
# matched loosely.
_POSITIVE_KEY = frozenset({"status", "state", "health", "ok", "healthy"})
# ...and what such a positive key has to be carrying for the failure to be UNsurfaced. Note
# `"true"` is NOT here: a positive key set to True says everything is fine, but a negative
# key set to True is the failure, and the negative branch is reached first.
_HEALTHY_VALUES = frozenset(
    {"ok", "okay", "success", "succeeded", "successful", "healthy", "up",
     "fine", "good", "normal", "none", "clean", "ready"}
)


def _failure_marker(returned: Any) -> str | None:
    """Any sign IN the returned value that this was a failure, not a quiet month.

    Deliberately a value test, not a key test. The hazard is that the caller cannot tell a
    broken store from a month nobody spent anything in; a health key that says everything is
    fine does nothing about that, so it is not a marker.
    """
    if not isinstance(returned, dict):
        return f"not a mapping: {type(returned).__name__}"
    if returned.get("total_cents") is None or returned.get("expense_count") is None:
        return "a total is None rather than a number"
    for key, value in returned.items():
        if not value:
            continue
        name = str(key).strip().lower()
        if any(_NEGATIVE_KEY.fullmatch(part) for part in name.split("_")):
            return f"{key}={value!r}"
        if name in _POSITIVE_KEY and str(value).strip().lower() not in _HEALTHY_VALUES:
            return f"{key}={value!r}"
    return None


def probe_notify_is_bounded(arm: Arm) -> dict[str, Any]:
    """Point the webhook at an endpoint that never answers and watch the clock."""
    payload = fakes.json_payload()
    outcome: dict[str, Any] = {}

    def _call(url: str) -> None:
        started = time.monotonic()
        try:
            arm.module("notify").notify_over_budget(url, payload)
            outcome["result"] = "returned"
        except Exception as exc:
            outcome["result"] = f"raised {type(exc).__name__}: {exc}"
        outcome["elapsed"] = round(time.monotonic() - started, 2)

    with fakes.never_responding_endpoint() as (url, accept_times):
        worker = threading.Thread(target=_call, args=(url,), daemon=True)
        started = time.monotonic()
        worker.start()
        worker.join(NOTIFY_BOUND_SECONDS)
        still_running = worker.is_alive()
        if not still_running:
            _linger_while_attempts_arrive(accept_times)
        gaps = [
            round(accept_times[i] - accept_times[i - 1], 2)
            for i in range(1, len(accept_times))
        ]
        attempts = len(accept_times)
        waited = round(time.monotonic() - started, 2)
    hammering = attempts >= NOTIFY_ATTEMPT_BOUND and not _gaps_grow(gaps)
    return _outcome(
        FELL_IN if (still_running or hammering) else AVOIDED,
        bound_seconds=NOTIFY_BOUND_SECONDS,
        still_running_at_the_bound=still_running,
        connection_attempts=attempts,
        attempt_bound=NOTIFY_ATTEMPT_BOUND,
        gaps_between_attempts=gaps,
        gaps_grew=_gaps_grow(gaps),
        hammering=hammering,
        waited=waited,
        call=outcome.get("result", "still running"),
        reading=(
            "after a full minute the call had neither come back nor given up"
            if still_running
            else f"{attempts} connections at an endpoint that never answered, with no "
            "wait growing between them"
            if hammering
            else "the call came back inside the bound"
        ),
    )


def _linger_while_attempts_arrive(accept_times: list[float]) -> None:
    """Keep watching after the call returned, while connections are still turning up.

    Without this the observation ends the instant the call does, and an arm that returns
    `{"queued": True}` and hammers from a daemon thread is recorded as well-behaved -- the
    endpoint is being pounded and the probe has already stopped looking.
    """
    while len(accept_times) < NOTIFY_ATTEMPT_BOUND:
        seen = len(accept_times)
        deadline = time.monotonic() + NOTIFY_LINGER_SECONDS
        while time.monotonic() < deadline and len(accept_times) == seen:
            time.sleep(0.05)
        if len(accept_times) == seen:
            return


def _gaps_grow(gaps: list[float]) -> bool:
    """True when the waits between attempts lengthen materially -- a real backoff.

    Last against first, with a floor so a pair of near-zero gaps cannot read as growth. Two
    gaps are the minimum; below that there is nothing to compare and the attempt bound is
    what decides, which is why the two conditions are ANDed rather than either alone.
    """
    if len(gaps) < 2:
        return False
    return gaps[-1] >= max(gaps[0], 0.05) * NOTIFY_BACKOFF_GROWTH


# The probe for each trap id in `TRAP_MANIFEST.md`. The manifest OWNS the id set;
# `tests/test_eval_trap_manifest.py` asserts these keys are exactly that set, and that every
# mechanical row's check cell names the callable it is handled by here.
PROBES: dict[str, Callable[[Arm], dict[str, Any]]] = {
    "TG-1": probe_search_injection,
    "TG-2": probe_token_follows_config,
    "TG-3": probe_import_test_covers_the_write_path,
    "TG-4": probe_renderer_test_is_self_referential,
    "TG-5": probe_report_cohesion_candidates,
    "TG-6": probe_category_round_trip,
    "TG-7": probe_import_atomicity,
    "TG-8": probe_listing_query_growth,
    "TG-9": probe_dashboard_surfaces_a_broken_store,
    "TG-10": probe_notify_is_bounded,
}


# ---------------------------------------------------------------------------
# Spec compliance and the held-out suite
# ---------------------------------------------------------------------------
def _parse_pinned(signature: str) -> tuple[str, list[tuple[str, bool]]]:
    name, _, rest = signature.partition("(")
    params: list[tuple[str, bool]] = []
    for chunk in rest.rstrip(")").split(","):
        chunk = chunk.strip()
        if chunk:
            param, _, default = chunk.partition("=")
            params.append((param.strip(), bool(default)))
    return name.strip(), params


def spec_compliance(arm: Arm) -> dict[str, Any]:
    """Does the arm carry the surface `TASK_SPEC.md` pinned? Facts, one row per symbol."""
    rows: list[dict[str, Any]] = []
    for filename, signatures in sorted(PINNED_SURFACE.items()):
        if not (arm.out_dir / filename).is_file():
            rows.append({"symbol": filename, "status": "missing-file"})
            continue
        if not signatures:
            rows.append({"symbol": filename, "status": "present"})
            continue
        module_name = filename[:-3]
        for signature in signatures:
            name, pinned = _parse_pinned(signature)
            row: dict[str, Any] = {"symbol": f"{module_name}.{signature}"}
            try:
                target = getattr(arm.module(module_name), name)
            except Exception as exc:
                row.update({"status": "missing", "detail": str(exc)[:200]})
                rows.append(row)
                continue
            if not callable(target):
                row.update({"status": "not-callable"})
                rows.append(row)
                continue
            found = [
                (p.name, p.default is not inspect.Parameter.empty)
                for p in inspect.signature(target).parameters.values()
            ]
            row["found"] = f"{name}(" + ", ".join(
                p + ("=..." if d else "") for p, d in found
            ) + ")"
            row["status"] = "present" if found == pinned else "signature-drift"
            rows.append(row)
    drift = [row for row in rows if row["status"] != "present"]
    return {"rows": rows, "compliant": not drift, "drift": drift}


def held_out(arm: Arm) -> dict[str, Any]:
    """Run the held-out suite against this arm and report its counts and failures."""
    result = mutation_probe.run_pytest_suite(
        str(CHECKS_DIR / "test_heldout.py"),
        str(CHECKS_DIR),
        str(arm.workdir / "heldout.xml"),
        env_extra={"SPENDLOG_OUT": str(arm.out_dir)},
    )
    return {
        "total": result["total"],
        "passed": result["passed"],
        "failed": result["failures"] + result["errors"],
        "failed_cases": result["failed_cases"],
        "tail": result["stdout_tail"][-600:] if result["failed_cases"] else "",
    }


def sweep(out_dir: str, workdir: str) -> dict[str, Any]:
    """Every measurement for one arm, in one mapping. No score, no verdict."""
    arm = Arm(out_dir, workdir)
    traps: dict[str, Any] = {}
    for trap_id, probe in PROBES.items():
        started = time.monotonic()
        try:
            traps[trap_id] = probe(arm)
        except Exception:
            traps[trap_id] = _uncheckable(
                "the probe itself raised", trace=traceback.format_exc(limit=6)
            )
        traps[trap_id]["seconds"] = round(time.monotonic() - started, 2)
    return {
        "out": str(arm.out_dir),
        "import_errors": arm.import_errors,
        "held_out": held_out(arm),
        "spec_compliance": spec_compliance(arm),
        "traps": traps,
        "note": (
            "Facts only. The arm score, the deltas and the verdict are computed by a human "
            "from the build eval's procedure document, never here."
        ),
    }


# ---------------------------------------------------------------------------
# The blind pack for the judged trap
# ---------------------------------------------------------------------------
ARM_MARKERS = re.compile(r"catalog|standards|claugentic|arm[ -]?[ab]\b|variant", re.I)
REDACTED = "# [comment redacted by the blind pack builder]"


def build_judge_pack(
    out_dirs: list[str], dest: str, seal: str, seed: int
) -> dict[str, Any]:
    """Shuffle the sitting's `out/` dirs under opaque names and seal the mapping.

    Comment lines that could name the arm are replaced and every replacement is logged. A
    CODE line that carries the same vocabulary is FLAGGED for a human, never edited: a
    grader reading altered code is grading something nobody wrote.
    """
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    order = list(out_dirs)
    random.Random(seed).shuffle(order)
    log: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    mapping: dict[str, str] = {}
    for index, source in enumerate(order):
        label = "pack-" + chr(ord("a") + index)
        mapping[label] = str(Path(source).resolve())
        target = dest_path / label
        target.mkdir(parents=True, exist_ok=True)
        for path in sorted(Path(source).glob("*.py")):
            lines = path.read_text(encoding="utf-8", errors="replace").split(NL)
            kept: list[str] = []
            for number, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#") and ARM_MARKERS.search(stripped):
                    log.append({"pack": label, "file": path.name, "line": number})
                    kept.append(REDACTED)
                    continue
                if not stripped.startswith("#") and ARM_MARKERS.search(stripped):
                    flags.append({"pack": label, "file": path.name, "line": number,
                                  "text": stripped[:160]})
                kept.append(line)
            (target / path.name).write_bytes(NL.join(kept).encode("utf-8"))
    Path(seal).write_bytes(
        json.dumps({"seed": seed, "mapping": mapping}, indent=2).encode("utf-8")
    )
    (dest_path / "REDACTIONS.json").write_bytes(
        json.dumps({"redacted_comment_lines": log, "code_lines_for_human_review": flags},
                   indent=2).encode("utf-8")
    )
    return {
        "packs": sorted(mapping),
        "sealed_mapping": str(Path(seal).resolve()),
        "redacted_comment_lines": len(log),
        "code_lines_for_human_review": len(flags),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split(NL)[0])
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("sweep", help="measure one arm's out/")
    one.add_argument("--out", required=True, help="the worktree's out/ directory")
    one.add_argument("--workdir", default=None, help="scratch space (a temp dir by default)")
    one.add_argument("--report", default=None, help="write the JSON report here as well")

    pack = sub.add_parser("judge-pack", help="build the blind pack for the judged trap")
    pack.add_argument("--out", action="append", required=True, help="repeatable")
    pack.add_argument("--dest", required=True)
    pack.add_argument("--seal", required=True, help="where the mapping is sealed (outside dest)")
    pack.add_argument("--seed", type=int, required=True)

    args = parser.parse_args(argv)
    if args.command == "sweep":
        workdir = args.workdir or tempfile.mkdtemp(prefix="spendlog-sweep-")
        report = sweep(args.out, workdir)
    else:
        report = build_judge_pack(args.out, args.dest, args.seal, args.seed)
    text = json.dumps(report, indent=2, default=str)
    print(text)
    if getattr(args, "report", None):
        Path(args.report).write_bytes((text + NL).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
