# QA fixture app

The minimal runnable target for the harness's runtime-verification workflow (`workflows/qa.js`).
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
