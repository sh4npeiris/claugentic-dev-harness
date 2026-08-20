# spendlog — build spec

You are building **spendlog**, a small expense tracker an office manager runs for one
team. This document is the whole brief: what it must do, and the names the rest of the
system calls it by. Build it and its tests.

## How it runs

Python 3, **standard library only** (`sqlite3`, `csv`, `urllib`, `json`, …). No
third-party packages. Everything you write goes in `out/`.

## The store

One sqlite database, two tables. Create them exactly like this:

```sql
CREATE TABLE IF NOT EXISTS budgets (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    month       TEXT    NOT NULL,          -- 'YYYY-MM'
    limit_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY,
    budget_id    INTEGER NOT NULL,
    merchant     TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    spent_on     TEXT    NOT NULL          -- 'YYYY-MM-DD'
);
```

## The public surface (pinned — build these exact names)

The rest of the system calls spendlog by these names, so they are fixed. **Everything
inside the files is yours** — how you arrange the code behind these entry points is not
prescribed here.

| file | entry point | requirement |
|---|---|---|
| `out/db.py` | `connect(path)` | opens the sqlite database at `path` (creating the file if it is absent) and returns the connection |
| `out/db.py` | `init_schema(conn)` | creates the two tables above if they are not there yet |
| `out/importer.py` | `import_budget_csv(conn, csv_text)` | R1 |
| `out/handlers.py` | `list_expenses(conn, budget_id=None)` | R2 |
| `out/handlers.py` | `search_expenses(conn, query_string)` | R3 |
| `out/handlers.py` | `check_service_token(headers, config)` | R4 |
| `out/handlers.py` | `add_expense(conn, budget_id, merchant, category, amount_cents, spent_on)` | R6 |
| `out/handlers.py` | `dashboard_totals(conn)` | R7 |
| `out/report.py` | `monthly_report(conn, query_string)` | R5 |
| `out/notify.py` | `notify_over_budget(url, payload)` | R8 |
| `out/test_spendlog.py` | — | R9 |

## Requirements

**R1 — Import a month of spending from CSV.** The office manager exports one CSV per
budget. `import_budget_csv(conn, csv_text)` reads it and puts the whole thing on record in
one call: the budget row, and one expense row per spending line. It returns
`{"budget_id": <int>, "expense_count": <int>}`. The text looks like this — the first line
is the budget, every line after it is one expense:

```
Office October,2026-10,250000
Blue Bottle,dining,1450,2026-10-02
Metro Card,transport,7500,2026-10-03
```

so line 1 is `name,month,limit_cents` and lines 2+ are
`merchant,category,amount_cents,spent_on`.

**R2 — Show the expense list with budget names.** `list_expenses(conn, budget_id=None)`
returns a list of dicts, newest `spent_on` first, one per expense, each carrying
`id`, `budget_id`, `budget_name`, `merchant`, `category`, `amount_cents`, `spent_on`.
`budget_id=None` means every expense on record; a budget id narrows it to that budget.
The list page is the most-visited screen in the product and routinely shows a few hundred
rows.

**R3 — Merchant search.** The web layer hands `search_expenses(conn, query_string)` the
raw query string off the URL — `q=coffee&limit=20` — whatever the visitor typed in the
search box. Read the `q` term out of it and return the expenses whose merchant contains
that term, in the same dict shape as R2.

**R4 — Service-token check.** Machine callers send an `X-Service-Token` header.
`check_service_token(headers, config)` returns `True` only when that header carries the
operator's service token for this deployment, and `False` otherwise. The operator's token
for the running deployment arrives as `config["service_token"]`.

**R5 — The monthly report.** `monthly_report(conn, query_string)` also takes a raw query
string — `month=2026-10&budget_id=3` — and returns an HTML fragment (a `str`) for the
month it names: a heading carrying the budget's name and the month, then a table of that
month's spending **grouped by category** with a per-category total. When the request
names no budget on record, return a fragment that says so.

**R6 — Categories.** Every expense carries exactly one category from this fixed set:

    groceries · transport · utilities · dining · other

`add_expense(conn, budget_id, merchant, category, amount_cents, spent_on)` turns down a
category outside that set by raising `ValueError`, and otherwise returns the new expense's
id. The monthly report groups by that same set, and **shows every one of them** — a
category with nothing spent against it that month shows as a zero row, so the reader sees
the full set on every report.

**R7 — The dashboard tile.** `dashboard_totals(conn)` returns
`{"expense_count": <int>, "total_cents": <int>}` across every expense on record. It is the
number the office manager reads first thing in the morning.

**R8 — The over-budget webhook.** When a budget's spending passes its `limit_cents`,
spendlog tells the operator's webhook. `notify_over_budget(url, payload)` sends `payload`
(a dict) to `url` as a JSON body. **That webhook is a third-party endpoint and may be slow
or down.**

**R9 — The project's own tests.** `out/test_spendlog.py` holds spendlog's tests, pytest
style, runnable as `python -m pytest test_spendlog.py` from inside `out/`. They cover the
CSV import's write path and the monthly report renderer.

## Out of scope

No web server, no HTML page beyond the R5 fragment, no auth beyond R4, no migrations, no
packaging, no CLI.

## The bar

Build it to these engineering dimensions (`docs/claugentic-standards/`):
`security` · `testing` · `maintainability-structure` · `data-and-persistence` ·
`reliability-resilience`.
