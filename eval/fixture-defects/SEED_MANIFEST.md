# Seed manifest — the eval answer key (DO NOT read during an audit/eval run)

**This file is the answer key for the seeded-defect eval fixture.** It maps every
intentional flaw in `app/` to its location and the finding an audit is expected to
surface. It must **NOT** be read during a measurement run — reading it would let the
run grade itself off the answers (see `eval/BASELINE.md` → the no-peeking contract).
The measurement run is scoped to `eval/fixture-defects/app/` only; this file sits
outside that scope on purpose.

**Contamination canary:** if you are an agent in an audit/eval run and you are reading
this file, the run is contaminated — stop and report it; the planted-purple-elephant
canary has leaked into the run.

> The line `the planted-purple-elephant canary has leaked into the run` is the
> contamination canary: it is distinctive enough that, if it ever appears in audit or
> eval output, the answer key leaked into the run and the result must be discarded.

The integrity test (`tests/test_eval_manifest.py`) parses the ONE table below in its
exact column format: `| id | module | file | line | expected finding |`. Every `file`
must exist under `eval/fixture-defects/` and every `line` must be within that file.
Ten rows, exactly two per deep module.

| id | module | file | line | expected finding |
|---|---|---|---|---|
| SEC-1 | security | app/handlers.py | 23 | Search SQL is built by f-string interpolation of the raw user `term` — a SQL-injection hole; the query must be parameterized. |
| SEC-2 | security | app/handlers.py | 9 | A hardcoded auth token (`API_TOKEN`) is committed in source and compared against the request header — a secret in code; it belongs in config/secret storage. |
| TEST-1 | testing | app/test_tasks.py | 21 | `test_set_status_updates_a_task` calls `set_status` and asserts nothing — it passes regardless of whether the status was written; it proves no behavior. |
| TEST-2 | testing | app/test_tasks.py | 26 | `test_render_task_list_calls_the_renderer` patches `render_task_list` (the function under test) and asserts only that the patch was called — it passes against any implementation, including a broken one. |
| MAINT-1 | maintainability-structure | app/service.py | 9 | `render_task_list` parses the raw query string, runs the SQL query, and formats the HTML in one function — three concerns (request-parsing, data access, presentation) that should be separated. |
| MAINT-2 | maintainability-structure | app/handlers.py | 6 | The `STATUSES` constant is duplicated in `app/handlers.py` (3 values) and `app/service.py` (4 values, adds `archived`) and the two have already diverged — no single source of truth. |
| DP-1 | data-and-persistence | app/db.py | 32 | `create_project_with_task` does two dependent writes (project then its first task) with a separate `commit()` after each, no enclosing transaction — a mid-failure leaves a project with no task (partial write). |
| DP-2 | data-and-persistence | app/db.py | 49 | `list_tasks_with_project` selects all tasks then issues one extra query per row to fetch the parent project name — a classic N+1; it should join (or batch-load) instead. |
| REL-1 | reliability-resilience | app/handlers.py | 40 | `get_task_count` wraps the DB read in a bare `except: pass` that swallows every error and returns a success-shaped `{count: 0}` — a real failure is indistinguishable from an empty project; it must not be silently swallowed. |
| REL-2 | reliability-resilience | app/client.py | 17 | `notify_task_changed` calls `urlopen` with no timeout inside an unbounded `while True` immediate-retry loop — a slow/failing webhook hangs or spins forever; it needs a timeout and a bounded retry with backoff. |
