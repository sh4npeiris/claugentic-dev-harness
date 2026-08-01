"""Pin that every shipped skill/agent's YAML frontmatter actually PARSES.

Why this gate exists: `/build` and `/condense` shipped in v0.4.0, v0.4.1 AND v0.5.0
with unparseable frontmatter. Their `description:` values were plain (unquoted) YAML
scalars containing `: ` (colon-space) — `Decision-gated: it proceeds…`, `an ordered,
guarded procedure:` — which YAML reads as a nested mapping key, so the whole block
failed to parse. The runtime does not fail loud on this: the skill loads with EMPTY
metadata and every frontmatter field is silently dropped, so the description that tells
Claude when to reach for the skill simply vanishes. Nothing in the suite looked at
frontmatter, so three consecutive releases shipped it.

The fix was to write those descriptions as folded block scalars (`>-`), which need no
escaping for `: `, quotes, or apostrophes. This test makes the class of bug
non-recurring rather than trusting the next author to remember the YAML rule.

Scope note — this checks that frontmatter PARSES and carries the fields the loader
needs; it does not judge the prose. Reads the real shipped files (not hermetic): the
shipped bytes are exactly what's under test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
AGENT_FILES = sorted((REPO_ROOT / ".claude" / "agents").glob("*.md"))

# The sanctioned "every tool" idiom in an agent's frontmatter. A bare `*` is an ALIAS
# marker in strict YAML, so a strict parser rejects `tools: *` — but it is what the
# platform expects, `claude plugin validate` accepts it, and the agents using it load
# correctly. So it is normalized here rather than "fixed" in the source: this test must
# pin real breakage, never re-litigate a working platform idiom.
ALL_TOOLS_IDIOM = "tools: *"
ALL_TOOLS_NORMALIZED = 'tools: "*"'


def _frontmatter(path: Path) -> str:
    """Return the raw YAML frontmatter block, or fail loud if the file has none."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        pytest.fail(f"{path.relative_to(REPO_ROOT)}: no opening '---' frontmatter fence")
    end = text.find("\n---\n", 4)
    if end == -1:
        pytest.fail(f"{path.relative_to(REPO_ROOT)}: frontmatter fence is never closed")
    return text[4:end]


def _parse(path: Path, *, normalize_all_tools: bool = False) -> dict:
    raw = _frontmatter(path)
    if normalize_all_tools:
        raw = raw.replace(ALL_TOOLS_IDIOM, ALL_TOOLS_NORMALIZED)
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # the exact failure mode that shipped three times
        pytest.fail(
            f"{path.relative_to(REPO_ROOT)}: frontmatter is not valid YAML — at runtime this "
            f"loads with EMPTY metadata and every field is silently dropped.\n"
            f"  {str(exc).splitlines()[0]}\n"
            f"  Most likely cause: an unquoted description containing ': ' (colon-space). "
            f"Write it as a folded block scalar:\n"
            f"    description: >-\n      <text>"
        )
    if not isinstance(parsed, dict):
        pytest.fail(
            f"{path.relative_to(REPO_ROOT)}: frontmatter parsed to {type(parsed).__name__}, "
            f"expected a mapping"
        )
    return parsed


def test_skill_files_found() -> None:
    # A vanished skills dir must not let this whole gate pass vacuously.
    assert SKILL_FILES, "no skills/*/SKILL.md files found — the frontmatter gate would pass vacuously"


def test_agent_files_found() -> None:
    assert AGENT_FILES, "no .claude/agents/*.md files found — the frontmatter gate would pass vacuously"


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_frontmatter_parses_with_a_usable_description(path: Path) -> None:
    parsed = _parse(path)
    description = parsed.get("description")
    assert isinstance(description, str) and description.strip(), (
        f"{path.relative_to(REPO_ROOT)}: frontmatter parsed but carries no usable "
        f"'description' — the skill would load without the text that tells Claude when to "
        f"use it"
    )


@pytest.mark.parametrize("path", AGENT_FILES, ids=lambda p: p.stem)
def test_agent_frontmatter_parses_with_name_and_description(path: Path) -> None:
    parsed = _parse(path, normalize_all_tools=True)
    for field in ("name", "description"):
        value = parsed.get(field)
        assert isinstance(value, str) and value.strip(), (
            f"{path.relative_to(REPO_ROOT)}: frontmatter parsed but carries no usable "
            f"'{field}' — the agent would not resolve correctly when spawned"
        )
