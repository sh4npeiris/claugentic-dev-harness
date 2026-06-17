# QA fixture app

The minimal runnable target for the harness's runtime-verification workflow (`engine/qa.js`).
It is the smallest thing that boots and shows a list: a FastAPI server that serves a static page
which fetches and renders an in-memory item list.

**Why it exists:** Slice 4a proves `qa.js`'s boot vertical against something real — the app boots,
answers a readiness probe, and is torn down; a deliberately-broken run command produces the honest
`qa-could-not-run-app` finding instead of a silent skip. Slice 4b adds Playwright flow-driving and
seeds two intentional UX defects (a missing empty state and a broken add flow) for the run to catch.

## Run

```
uvicorn main:app --app-dir eval/fixture-app --port 8123
```

Then open <http://localhost:8123> — the heading plus the item list rendered as `<li>`s. The
readiness URL `qa.js` probes is `http://localhost:8123`.

## Endpoints

- `GET /` — serves `static/index.html`.
- `GET /api/items` — the in-memory item list.
- `POST /api/items` — appends an item (`{"name": "..."}`) and returns it.

## The `FIXTURE_SEED` knob

By default the app seeds 3 items at startup. Set `FIXTURE_SEED=0` to boot with an EMPTY list — the
zero-data condition Slice 4b's empty-state check needs:

```
FIXTURE_SEED=0 uvicorn main:app --app-dir eval/fixture-app --port 8123
```

## Dependencies

`fastapi` and `uvicorn` (see `requirements.txt`). They are **documented, not vendored** — nothing in
the repo's gate suite imports them; install them only to run the fixture live:

```
pip install -r eval/fixture-app/requirements.txt
```

## Seeded defects (intentional — DO NOT "fix")

This fixture carries two **permanent, intentional UX defects** in `static/index.html`. They are the
targets the Slice-4b flow-driving run is supposed to **catch** — fixing them would silently disarm
the run designed to exercise whether `engine/qa.js`'s driver+verifier surface them (model-upheld, not a guaranteed catch). Each maps to a named `docs/claugentic-standards/product-ux.md`
dimension.

| defect | issue class | where | product-ux dimension |
|---|---|---|---|
| **Broken add flow** — the add-item form POSTs to the typo'd route `/api/item` (real route: `/api/items`), the server 404s, and the handler **swallows the error**: no message, the input is kept, the list never refreshes. To the user, Add does nothing and nothing explains why. | `ux-broken-flow` | `static/index.html` (the `submit` handler) | *user-flow-completeness* + the **error** state of the loading/empty/error states bar |
| **Missing empty state** — `load()` renders one `<li>` per item with **no zero-data branch**. Booted with `FIXTURE_SEED=0` the list is a blank `<ul>` void — no "no items yet" message, no call-to-action. | `ux-missing-empty-state` | `static/index.html` (the `load()` function) | the **empty** state of the loading/empty/error states bar (a designed zero-state, not a blank void) |

The **correct** surfaces are the pass cases: the `Items` heading and the add-item form are supposed
to be present (that is criterion AC-3's pass surface), and `GET /api/items` returns a 200 JSON array
(AC-4's pass surface).

## Acceptance criteria (`acceptance-criteria.json`)

`acceptance-criteria.json` is the criteria instance — in the **frozen schema** (`id` / `feature` /
`flow` / `expect` / `states` / `check`) — passed as `args.criteria` to a `engine/qa.js` dogfood run:

- **AC-1** — add-item flow (`e2e`). **Expected to FAIL** (the broken add flow above).
- **AC-2** — home list empty state (`e2e`, `states: ["empty"]`, run with `FIXTURE_SEED=0`). **Expected
  to FAIL** (the blank void above).
- **AC-3** — the heading + form are present (`e2e`). **Expected to PASS** (the correct surface).
- **AC-4** — `GET /api/items` returns a 200 JSON array (`api`). **Expected to PASS**.
- **AC-5** — a `manual` criterion (visual judgment). **NEVER driven** — listed in the report for a
  human, verdict `not-checkable (manual by contract)`.

The dogfood invocation (the run designed to surface both seeded defects — model-upheld driving + cross-model re-check, not a guaranteed catch):

```
FIXTURE_SEED=0 uvicorn main:app --app-dir eval/fixture-app --port 8123
```

(The boot agent starts that command; screenshots land under the gitignored `.qa-artifacts/<runLabel>/`.)
