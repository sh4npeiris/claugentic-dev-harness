"""Tests for the inbound-section-citation resolver (`scripts/check_standards_anchors.py`).

The gate's whole value is that a DEAD anchor cannot pass, and its whole risk is the opposite
one: a scanner that quietly stops matching reports a clean zero. So the pins here come in two
halves — the forms it must RESOLVE (arrow both glyphs, quoted, anchor, wrapped, partial), and
the breaks it must REDDEN (a cut heading, a renamed heading, a disarmed self-test probe).

`scan()` takes (root, targets, corpus) so every form test runs on a hand-built tmp corpus with
no git and no repo state; the two live tests at the end are the ones that must see the real
repo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import check_standards_anchors as csa

TARGET = "docs/mod.md"
TARGET_TEXT = """---
module: mod
---

# Mod — a module

## Reading a module

body

## Code the suite cannot EXECUTE, pinned as text

body

## Definition of Done

```
## Not a heading (inside a fence)
```
"""


def _repo(tmp_path: Path, sources: dict[str, str]) -> tuple[Path, list[str]]:
    """Materialize a tiny corpus: the target module plus the given citing files."""
    files = {TARGET: TARGET_TEXT, **sources}
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    return tmp_path, sorted(files)


def _scan(tmp_path: Path, sources: dict[str, str]) -> csa.ScanResult:
    root, corpus = _repo(tmp_path, sources)
    return csa.scan(root, [TARGET], corpus)


class TestRecognizedForms:
    """Every citation form the docstring promises to resolve, one pin each."""

    @pytest.mark.parametrize(
        "body",
        [
            "see `docs/mod.md` → *Reading a module*.",  # unicode arrow, emphasized
            "see `docs/mod.md` -> *Reading a module*.",  # ascii arrow
            'see `docs/mod.md` -> "Reading a module").',  # quoted (how engine/*.js cites)
            "see `docs/mod.md` -> `Reading a module`.",  # backticked
            "see `docs/mod.md` -> Reading a module.",  # undelimited
            "see mod.md → *Reading a module*.",  # bare basename, unique in corpus
            "# see `docs/mod.md` →\n# *Reading a module*.",  # wrapped, comment marker
        ],
    )
    def test_form_resolves(self, tmp_path: Path, body: str) -> None:
        result = _scan(tmp_path, {"src.py": f'"""{body}"""\n'})
        assert [c.section for c in result.citations] == ["Reading a module"]
        assert not result.dead

    def test_anchor_form_resolves_against_the_slug(self, tmp_path: Path) -> None:
        result = _scan(tmp_path, {"a.md": "[x](mod.md#reading-a-module)\n"})
        assert [(c.form, c.kind) for c in result.citations] == [("anchor", "exact")]

    def test_line_number_is_the_line_the_filename_sits_on(self, tmp_path: Path) -> None:
        body = "one\ntwo\nsee `docs/mod.md` →\n*Reading a module*.\n"
        result = _scan(tmp_path, {"a.md": body})
        assert [c.line for c in result.citations] == [3]

    def test_partial_forms_resolve_but_are_marked_not_exact(self, tmp_path: Path) -> None:
        sources = {
            # citation shorter than the heading (the repo's leading-clause convention)
            "short.md": "`docs/mod.md` → *Code the suite cannot EXECUTE*.\n",
            # citation longer: an undelimited name running on into its sentence
            "long.md": "`docs/mod.md` → Definition of Done carries the **obligation**\n",
        }
        result = _scan(tmp_path, sources)
        assert sorted(c.kind for c in result.citations) == ["bare", "prefix"]
        assert not result.dead

    def test_a_delimited_name_gets_no_bare_grace(self, tmp_path: Path) -> None:
        """An author who marked the end of the name meant it — over-long is then DEAD."""
        result = _scan(tmp_path, {"a.md": "`docs/mod.md` → *Definition of Done carries it*\n"})
        assert not result.citations
        assert [c.section for c, _ in result.dead] == ["Definition of Done carries it"]


class TestBreaksGoRed:
    """The mutation half: what has to fail, and be reported, when a cut lands."""

    def test_cut_section_is_reported_dead_with_source_line(self, tmp_path: Path) -> None:
        result = _scan(tmp_path, {"a.md": "x\n`docs/mod.md` → *A deleted dimension*.\n"})
        assert not result.citations
        (cite, near) = result.dead[0]
        assert (cite.source, cite.line, cite.section) == ("a.md", 2, "A deleted dimension")
        assert near == [] or all(isinstance(n, str) for n in near)

    def test_renamed_heading_reddens_the_citation_of_the_old_name(self, tmp_path: Path) -> None:
        root, corpus = _repo(tmp_path, {"a.md": "`docs/mod.md` → *Reading a module*.\n"})
        assert not csa.scan(root, [TARGET], corpus).dead
        (root / TARGET).write_bytes(
            TARGET_TEXT.replace("## Reading a module", "## How to read a module").encode("utf-8")
        )
        assert [c.section for c, _ in csa.scan(root, [TARGET], corpus).dead] == ["Reading a module"]

    def test_anchor_link_needs_an_exact_slug_a_prefix_navigates_nowhere(
        self, tmp_path: Path
    ) -> None:
        result = _scan(tmp_path, {"a.md": "[x](mod.md#reading)\n"})
        assert [c.section for c, _ in result.dead] == ["reading"]

    def test_headings_inside_a_fence_are_not_headings(self, tmp_path: Path) -> None:
        result = _scan(tmp_path, {"a.md": "`docs/mod.md` → *Not a heading*.\n"})
        assert [c.section for c, _ in result.dead] == ["Not a heading"]


class TestNoSilentDrops:
    """Nothing the scan cannot answer may leave the run looking clean."""

    def test_ambiguous_bare_basename_is_recorded_not_guessed(self, tmp_path: Path) -> None:
        result = _scan(
            tmp_path,
            {
                "other/mod.md": "# Decoy\n",  # now two tracked files are named mod.md
                "a.md": "`mod.md` → *Reading a module*.\n",
            },
        )
        assert not result.citations and not result.dead
        assert [rel for rel, _, _ in result.ambiguous] == ["a.md"]

    def test_sibling_wins_over_ambiguity(self, tmp_path: Path) -> None:
        """A module citing its own directory's README is the catalog's commonest form."""
        result = _scan(
            tmp_path,
            {
                "other/mod.md": "# Decoy\n",
                "docs/sibling.md": "`mod.md` → *Reading a module*.\n",
            },
        )
        assert [c.target for c in result.citations] == [TARGET]

    def test_a_targets_spec_that_matches_nothing_fails_loud(self, tmp_path: Path) -> None:
        with pytest.raises(csa.ScanError, match="matched no file"):
            csa.resolve_targets(tmp_path, ["docs/nope-*.md"])

    def test_an_unreadable_target_fails_loud(self, tmp_path: Path) -> None:
        root, corpus = _repo(tmp_path, {})
        (root / TARGET).write_bytes(b"\xff\xfe\x00binary")
        with pytest.raises(csa.ScanError, match="unreadable"):
            csa.scan(root, [TARGET], corpus)

    def test_binary_corpus_files_are_counted_not_hidden(self, tmp_path: Path) -> None:
        root, corpus = _repo(tmp_path, {"a.md": "`docs/mod.md` → *Reading a module*.\n"})
        (root / "blob.bin").write_bytes(b"\xff\xfe\x00\x01")
        result = csa.scan(root, [TARGET], [*corpus, "blob.bin"])
        assert result.unreadable == ["blob.bin"]
        assert len(result.citations) == 1

    def test_empty_corpus_is_an_error_not_a_clean_sweep(self, tmp_path: Path) -> None:
        (tmp_path / "not-a-repo").mkdir()
        with pytest.raises(csa.ScanError, match="git ls-files"):
            csa._tracked_files(tmp_path / "not-a-repo")


class TestSelfTestCanary:
    """The gate's own tripwire: a scanner that stops matching must not report success."""

    def test_probes_resolve_on_the_live_repo(self) -> None:
        root = csa._repo_root()
        assert csa.self_test(root, csa._tracked_files(root)) == []

    def test_a_probe_that_no_longer_resolves_is_a_problem(self, monkeypatch) -> None:
        monkeypatch.setattr(
            csa,
            "KNOWN_POSITIVES",
            ((csa.KNOWN_POSITIVES[0][0], csa.PROBE_TARGET, "A section nobody cites", "arrow"),),
        )
        root = csa._repo_root()
        problems = csa.self_test(root, csa._tracked_files(root))
        assert len(problems) == 1
        assert "SELF-TEST BROKEN" in problems[0]

    def test_the_live_standards_sweep_is_green(self, capsys) -> None:
        """The gate itself, over this repo — the pin that a cut cannot leave a dead anchor."""
        assert csa.main([]) == 0
        assert "0 dead." in capsys.readouterr().out
