# 0001 — spendlog

- **Status:** Approved (Stage 5) — Implementing
- **Resumable from:** Slice 1 implementation (Stage 6).
- **Blockers:** none
- **Flags:** none
- **Disposition at close:** per `docs/claugentic-WORKFLOW.md` -> Plan file lifecycle.
- **Roadmap item:** none (direct request from the product owner)
- **References:** `TASK_SPEC.md` (the brief, alongside this file) · `docs/claugentic-standards/`

## Problem

The office manager tracks one team's spending in a spreadsheet that nobody else can read,
so nothing else in the product can show a total, search a merchant, or tell the operator a
budget has been passed. `TASK_SPEC.md` is the brief for the small service that replaces it.

## Goals / Non-goals

- **Goal:** R1-R9 of `TASK_SPEC.md`, working, with the project's own tests.
- **Non-goal:** anything under `TASK_SPEC.md` -> *Out of scope* (no web server, no page
  beyond the R5 fragment, no auth past R4, no migrations, no packaging, no CLI).
- **Non-goal:** third-party packages. Python 3 standard library only.

## Approach

Straight build against the brief. `TASK_SPEC.md` fixes the entry points the rest of the
system calls and the two-table store they read and write; how the code behind those entry
points is arranged is the implementer's call.

## Architecture & holistic fit

- **Codebase fit** — a new module set under `out/`, with no existing caller in this
  checkout: the pinned entry points in `TASK_SPEC.md` are the contract a later web layer
  will call. The store is sqlite via the standard library.
- **Product fit** — the office manager's morning read (the dashboard tile), the team's
  daily read (the expense list and merchant search), and the operator's alarm (the
  over-budget webhook). The report is what gets forwarded to finance at month end.
- **Quality dimensions to uphold** — the five named at the foot of `TASK_SPEC.md`:
  `security` · `testing` · `maintainability-structure` · `data-and-persistence` ·
  `reliability-resilience` (`docs/claugentic-standards/`).
- **Future-proofing** — a second budget-file format and a real web layer are both expected
  later; neither is built now.

## Affected files

`out/db.py` · `out/importer.py` · `out/handlers.py` · `out/report.py` · `out/notify.py` ·
`out/test_spendlog.py` — all new.

## Risks & mitigations

- The webhook is somebody else's service -> R8 states what it does on a bad day.
- The list screen is the busiest one in the product -> R2 states the row counts it runs at.

## Test strategy

`out/test_spendlog.py`, per R9: the CSV import's write path and the monthly report
renderer, runnable as `python -m pytest test_spendlog.py` from inside `out/`.

## Decomposition (slices)

- [ ] **Slice 1** — the whole of spendlog, R1-R9 · lands complete because the brief is one
  small service with one store and no caller to migrate.

---

## Spec

### Slice 1 — spendlog, R1-R9

- **In plain English (shown first at the approval gate):**
  - *What this builds:* the expense tracker described in `TASK_SPEC.md` — CSV import,
    expense list, merchant search, the machine-caller token check, the monthly report, the
    dashboard tile and the over-budget webhook call, plus the project's own tests.
  - *What "done" means for you:* the entry points in the brief's pinned table exist under
    the pinned names, R1-R9 behave as the brief describes, and the project's own tests run
    green.
  - *What you're accepting:* one team's spending, one sqlite file, no web layer yet.
- **Files & changes:** the six files listed under *Affected files*, per the pinned surface
  table in `TASK_SPEC.md`. No file outside `out/` changes.
- **Scope of this slice — read this before writing anything:**
  - **Every file you write goes under `out/`.** Write nothing anywhere else in this
    checkout. `out/` is the whole deliverable.
  - **`docs/claugentic-ARCHITECTURE_TREE.md` is out of scope for this slice** — leave it
    alone, and do not run this checkout's gate scripts; they are about the surrounding
    repository, not about `out/`.
  - **Run no `git` command at all.** This working copy is thrown away afterwards; nothing
    written here is landed.
- **In-scope standards dimensions:** `security` · `testing` · `maintainability-structure` ·
  `data-and-persistence` · `reliability-resilience`.
- **Tests to add:** `out/test_spendlog.py`, per R9.
- **Acceptance criteria:** (1) every entry point in the brief's pinned table exists with
  the pinned name and parameter names; (2) R1-R9 behave as the brief describes; (3)
  `python -m pytest test_spendlog.py` is green from inside `out/`; (4) the work is built to
  the five in-scope dimensions above.
