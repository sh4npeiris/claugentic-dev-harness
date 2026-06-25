"""Tests for the release-builder's classification core (`scripts/build_release.py`).

`classify()` is the single source of truth for ship-vs-strip; these lock the split so a
new dev-only path can't silently start shipping (and a shipped file can't get stripped)
without a failing test. The branch-building `--apply` path is git-orchestration and is
not unit-tested here (it's exercised manually at release).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import build_release as br


class TestClassify:
    def test_build_history_docs_are_stripped(self):
        ship, strip = br.classify(
            [
                "docs/claugentic-DECISIONS.md",
                "docs/claugentic-ROADMAP.md",
                "docs/claugentic-PRODUCT.md",
                "docs/claugentic-PRODUCT_SPEC.md",
                "docs/claugentic-ARCHITECTURE_TREE.md",
                "docs/RELEASE_CHECKLIST.md",
            ]
        )
        assert ship == []
        assert len(strip) == 6

    def test_managed_docs_and_runtime_files_ship(self):
        files = [
            "docs/claugentic-WORKFLOW.md",
            "docs/claugentic-PLAYBOOK.md",
            "docs/claugentic-ENGINEERING_STANDARDS.md",
            "docs/claugentic-PRODUCT_SPEC_TEMPLATE.md",
            "docs/claugentic-PLAN_TEMPLATE.md",
            "docs/claugentic-standards/security.md",
            "skills/init/SKILL.md",
            "engine/audit.js",
            ".claude/agents/synthesizer-gate.md",
            "scripts/claugentic-check_architecture_tree.py",
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            "README.md",
            "LICENSE",
        ]
        ship, strip = br.classify(files)
        assert strip == []
        assert set(ship) == set(files)

    def test_dev_directories_are_stripped_recursively(self):
        # `*` does not cross `/`; the dir-prefix rule must strip the whole subtree.
        ship, strip = br.classify(
            [
                "eval/fixture-app/main.py",
                "eval/BASELINE.md",
                "tests/conftest.py",
                ".claude/plans/0027-release-init-consistency.md",
                ".github/workflows/ci.yml",
            ]
        )
        assert ship == []
        assert len(strip) == 5

    def test_release_tool_and_self_gates_are_stripped(self):
        # build_release.py (this tool) and the harness-self gates (version-sync +
        # doc-budgets) never ship — they're about the plugin itself, not the adopter's code.
        ship, strip = br.classify(
            [
                "scripts/build_release.py",
                "scripts/check_versions_synced.py",
                "scripts/check_doc_budgets.py",
            ]
        )
        assert ship == []
        assert len(strip) == 3

    def test_repo_config_is_stripped_but_agents_dir_ships(self):
        ship, strip = br.classify(
            [
                "CLAUDE.md",
                ".claude/settings.json",
                "pyproject.toml",
                ".gitignore",
                ".gitattributes",
                ".claude/agents/honesty-reviewer.md",  # NOT under .claude/plans/ — ships
            ]
        )
        assert ship == [".claude/agents/honesty-reviewer.md"]
        assert len(strip) == 5

    def test_classify_output_is_sorted(self):
        ship, _ = br.classify(["README.md", "LICENSE", "engine/qa.js", "engine/audit.js"])
        assert ship == sorted(ship)


class TestReleaseInitContract:
    """Pins the release/init contract (INVARIANT, plan 0027): whatever the release STRIPS
    that's adopter-relevant, `init` must (re)create — and nothing shipped may reference a
    stripped-uncreated file or run a harness-self gate without adopter-awareness.

    SCOPE — HONEST: this pins ship/strip *set membership* only (the load-bearing facts the
    S1/S2 fixes turned on). It does NOT prove "no shipped file's *text* references a stripped
    path" — that is a heavier content-grep over the shipped tree, deliberately out of scope
    here (a ROADMAP candidate; the S1/S2 manual grep + this membership pin are the contract).
    Asserts via the pure `is_dev_only()` (no git), and is the single greppable home for the
    contract — the broader membership is also covered by `TestClassify`
    (`test_managed_docs_and_runtime_files_ship` pins PLAN_TEMPLATE ships;
    `test_release_tool_and_self_gates_are_stripped` pins the three .py gates strip), not
    re-litigated here.
    """

    def test_plan_template_ships_init_manages_it(self):
        # S1 moved the plan template out of the stripped `.claude/plans/` into `/docs/` so it
        # ships like any managed doc; init copies it into the adopter's tree.
        assert br.is_dev_only("docs/claugentic-PLAN_TEMPLATE.md") is False

    def test_harness_self_gates_strip(self):
        # Harness-self tooling never reaches an adopter: doc-budgets (S2 strip), version-sync,
        # and the release builder itself. doctor/WORKFLOW/implementer treat them adopter-aware.
        assert br.is_dev_only("scripts/check_doc_budgets.py") is True
        assert br.is_dev_only("scripts/check_versions_synced.py") is True
        assert br.is_dev_only("scripts/build_release.py") is True

    def test_harness_own_plans_strip_cleanly(self):
        # The template move (S1) left `.claude/plans/` holding only the harness's OWN plans —
        # all stripped via the dir-prefix rule. Adopters read the /docs/ template and write
        # their own plans into their own `.claude/plans/`.
        assert br.is_dev_only(".claude/plans/0027-release-init-consistency.md") is True


class TestBaseAncestryGuard:
    """`_dropped_merges` is the mechanical defense against rebuilding the release from a
    stale base (the v0.1.40 distillation drop). These are pure/offline — `_git` is
    monkeypatched so no real `git`/network is touched."""

    def test_current_base_drops_nothing(self, monkeypatch):
        # rev-parse (verify) succeeds; rev-list returns nothing → base is current.
        monkeypatch.setattr(br, "_git", lambda *args: "")
        assert br._dropped_merges(Path(".")) == []

    def test_stale_base_returns_dropped_shas(self, monkeypatch):
        def fake_git(*args):
            if "rev-parse" in args:
                return ""
            return "a7d2151\ndf20ed1\n"

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._dropped_merges(Path(".")) == ["a7d2151", "df20ed1"]

    def test_missing_upstream_ref_returns_none(self, monkeypatch):
        def fake_git(*args):
            if "rev-parse" in args:
                raise subprocess.CalledProcessError(1, ["git", *args])
            return ""

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._dropped_merges(Path(".")) is None
