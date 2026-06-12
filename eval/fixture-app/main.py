"""Minimal QA fixture app — the smallest FastAPI list app that boots and shows a list.

Purpose: a real, runnable target for `workflows/qa.js` (Slice 4a boot vertical; Slice 4b adds
flow-driving + seeded UX defects). Deliberately minimal — `GET /` serves a static page that
fetches and renders the item list; `GET /api/items` returns an in-memory list; `POST /api/items`
appends. The ONE knob `FIXTURE_SEED=0` boots empty (the zero-data condition Slice 4b's
empty-state check needs).

Run: `uvicorn main:app --app-dir eval/fixture-app --port 8123`
Deps (documented, NOT vendored): fastapi, uvicorn — see requirements.txt.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="QA fixture app")


class Item(BaseModel):
    """One list item — a name is all the fixture needs."""

    name: str


# In-memory store (the fixture has no persistence — KISS; a fresh boot reseeds). Seed 3 items
# unless FIXTURE_SEED=0, the one knob the empty-state run flips.
def _initial_items() -> list[dict]:
    if os.environ.get("FIXTURE_SEED") == "0":
        return []
    return [{"name": "Buy milk"}, {"name": "Walk the dog"}, {"name": "Write the spec"}]


_items: list[dict] = _initial_items()


@app.get("/")
def index() -> FileResponse:
    """Serve the static page (heading + the fetched list)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/items")
def list_items() -> list[dict]:
    """Return the in-memory item list."""
    return _items


@app.post("/api/items")
def add_item(item: Item) -> dict:
    """Append an item and return it (the created resource)."""
    record = {"name": item.name}
    _items.append(record)
    return record
