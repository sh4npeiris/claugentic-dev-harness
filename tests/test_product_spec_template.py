"""Pin the FROZEN acceptance-criteria schema in the product-spec docs.

The acceptance-criteria schema is the contract the product layer writes
(`docs/claugentic-PRODUCT_SPEC_TEMPLATE.md`), gap mode pins (`engine/audit.js` →
`cellsFromCriteria`), and `engine/qa.js` consumes at runtime. Its field names are FROZEN
and may never drift. This test reads the **first fenced
```json block after the `## Acceptance criteria` heading** and asserts the embedded
example matches the frozen schema — so the template's example can never silently
drift from the contract the code enforces.

Two files carry the schema:
  * `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` — the pristine template (always present).
  * `docs/claugentic-PRODUCT_SPEC.md` — this repo's own dogfood spec (the worked example,
    produced by the product skill's spec mode). Validated WHEN PRESENT; the test
    skips it cleanly when it does not yet exist, so the gate is green before the
    dogfood spec lands and validates it once it does.

Reads the real repo files (not hermetic) — it is pinning the actual shipped
contract, which is the point.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "docs" / "claugentic-PRODUCT_SPEC_TEMPLATE.md"
SPEC = REPO_ROOT / "docs" / "claugentic-PRODUCT_SPEC.md"

# The FROZEN schema — field names exact, the single source of truth this test pins.
FROZEN_KEYS = {"id", "feature", "flow", "expect", "states", "check"}
VALID_CHECKS = {"e2e", "api", "manual"}
VALID_STATES = {"empty", "loading", "error"}

# The files to validate: the template always; the dogfood spec only when it exists.
SPEC_FILES = [TEMPLATE] + ([SPEC] if SPEC.exists() else [])


def _criteria_block(path: Path) -> list:
    """Extract + parse the first fenced ```json block after `## Acceptance criteria`.

    Fails loudly (not silently) if the heading or the json block is missing — a
    product-spec doc without a parseable criteria block is a contract violation, not
    a skip.
    """
    text = path.read_text(encoding="utf-8")
    heading = re.search(r"^##\s+Acceptance criteria\s*$", text, re.MULTILINE)
    assert heading, f"{path.name}: no '## Acceptance criteria' heading found"
    after = text[heading.end():]
    fenced = re.search(r"```json\s*\n(.*?)\n```", after, re.DOTALL)
    assert fenced, f"{path.name}: no fenced ```json block after the Acceptance criteria heading"
    parsed = json.loads(fenced.group(1))
    assert isinstance(parsed, list), f"{path.name}: the criteria block must be a JSON array"
    return parsed


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda p: p.name)
def test_criteria_block_parses_as_a_nonempty_array(path: Path) -> None:
    criteria = _criteria_block(path)
    assert len(criteria) >= 1, f"{path.name}: the criteria array must have ≥1 example/criterion"


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda p: p.name)
def test_every_criterion_has_exactly_the_frozen_keys(path: Path) -> None:
    for criterion in _criteria_block(path):
        assert isinstance(criterion, dict), f"{path.name}: each criterion must be an object"
        keys = set(criterion.keys())
        assert keys == FROZEN_KEYS, (
            f"{path.name}: criterion {criterion.get('id', '<no id>')!r} keys {sorted(keys)} "
            f"!= the frozen schema {sorted(FROZEN_KEYS)}"
        )


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda p: p.name)
def test_field_types_match_the_frozen_schema(path: Path) -> None:
    for criterion in _criteria_block(path):
        cid = criterion.get("id", "<no id>")
        assert isinstance(criterion["id"], str) and criterion["id"], f"{path.name}: {cid!r} id must be a non-empty string"
        assert isinstance(criterion["feature"], str) and criterion["feature"], f"{path.name}: {cid!r} feature must be a non-empty string"
        for field in ("flow", "expect"):
            value = criterion[field]
            assert isinstance(value, list) and len(value) >= 1, f"{path.name}: {cid!r} {field} must be a non-empty array"
            assert all(isinstance(s, str) and s for s in value), f"{path.name}: {cid!r} {field} entries must be non-empty strings"
        assert isinstance(criterion["states"], list), f"{path.name}: {cid!r} states must be an array"
        assert set(criterion["states"]) <= VALID_STATES, (
            f"{path.name}: {cid!r} states {criterion['states']} not a subset of {sorted(VALID_STATES)}"
        )
        assert criterion["check"] in VALID_CHECKS, (
            f"{path.name}: {cid!r} check {criterion['check']!r} not in {sorted(VALID_CHECKS)}"
        )


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda p: p.name)
def test_criterion_ids_are_unique(path: Path) -> None:
    ids = [c["id"] for c in _criteria_block(path)]
    assert len(ids) == len(set(ids)), f"{path.name}: criterion ids must be unique (got {ids})"
