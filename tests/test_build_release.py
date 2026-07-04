"""Tests for the release-builder's classification core (`scripts/build_release.py`).

`classify()` is the single source of truth for ship-vs-strip; these lock the split so a
new dev-only path can't silently start shipping (and a shipped file can't get stripped)
without a failing test. The branch-building `--apply` path is git-orchestration and is
not unit-tested here (it's exercised manually at release).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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


class TestManifestMigration:
    """The LOAD-BEARING no-op net for plan 0034 Slice 1: converting `DEV_ONLY_FILES`
    (a frozenset) into `DEV_ONLY_PATH_CLASSES` (a `path -> recreate-class` dict) is a
    MEMBERSHIP-PRESERVING refactor — it changes the *representation* + adds the class
    annotation, and MUST NOT change what ships. These pins fail loud the instant the
    migration alters the shipped set or the exhaustive-partition property.
    """

    # The exact dev-only FILE membership as authored BEFORE the migration (the frozenset
    # literal from `build_release.py` at commit bb330c4). Frozen here so the dict->keys
    # derivation is provably byte-identical to the prior hand-list — if a class annotation
    # ever silently drops/adds a path, this snapshot catches it.
    PRE_MIGRATION_DEV_ONLY_FILES = frozenset(
        {
            "docs/claugentic-DECISIONS.md",
            "docs/claugentic-ROADMAP.md",
            "docs/claugentic-PRODUCT.md",
            "docs/claugentic-PRODUCT_SPEC.md",
            "docs/claugentic-ARCHITECTURE_TREE.md",
            "docs/claugentic-INVARIANTS.md",
            "docs/RELEASE_CHECKLIST.md",
            "scripts/check_versions_synced.py",
            "scripts/check_doc_budgets.py",
            "scripts/check_shipped_content.py",
            "scripts/build_release.py",
            ".claude/settings.json",
            "CLAUDE.md",
            "pyproject.toml",
            ".gitignore",
            ".gitattributes",
        }
    )

    # The SIX classes — every dev-only FILE maps to exactly one (dirs stay out of the classes).
    SIX_CLASSES = frozenset(
        {"init-seed", "init-gen", "recreate-on-demand", "self-gate", "config", "dangle"}
    )

    def test_dict_keys_match_pre_migration_membership(self):
        # frozenset -> dict-keys is membership-preserving: the manifest keys are byte-identical
        # to the prior hand-authored `DEV_ONLY_FILES` frozenset.
        assert set(br.DEV_ONLY_PATH_CLASSES) == self.PRE_MIGRATION_DEV_ONLY_FILES
        # The back-compat alias is derived from the dict keys — same membership.
        assert br.DEV_ONLY_FILES == self.PRE_MIGRATION_DEV_ONLY_FILES

    def test_shipped_set_is_byte_identical_across_the_migration(self):
        # THE load-bearing check: for the pre-migration membership fed through the (unchanged)
        # dir-sweep + `is_dev_only` logic, the ship/strip split is identical to what the current
        # `classify()` produces. `classify` is pure over a path list, so this reconstructs the
        # exact pre-change classifier and asserts equality — no shipped file moved.
        tracked = sorted(self.PRE_MIGRATION_DEV_ONLY_FILES | {
            "README.md",
            "LICENSE",
            "docs/claugentic-WORKFLOW.md",
            "docs/claugentic-_DECISIONS.md",
            "docs/claugentic-_ROADMAP.md",
            "docs/claugentic-_CHARTER.md",
            "docs/claugentic-PRODUCT_SPEC_TEMPLATE.md",
            "skills/init/SKILL.md",
            "scripts/claugentic-check_architecture_tree.py",
            ".claude/agents/honesty-reviewer.md",
            "eval/BASELINE.md",
            "tests/conftest.py",
            ".claude/plans/0034-release-consolidation.md",
        })

        def pre_migration_is_dev_only(path: str) -> bool:
            return path in self.PRE_MIGRATION_DEV_ONLY_FILES or any(
                path.startswith(d) for d in br.DEV_ONLY_DIRS
            )

        before_strip = sorted(f for f in tracked if pre_migration_is_dev_only(f))
        before_ship = sorted(f for f in tracked if not pre_migration_is_dev_only(f))

        after_ship, after_strip = br.classify(tracked)

        assert after_ship == before_ship
        assert after_strip == before_strip

    def test_every_entry_maps_to_exactly_one_of_the_six_classes(self):
        # Exhaustive-partition property: the annotation is a total map into the six-class set;
        # each file has one class, and no class outside the declared six is used.
        assert set(br.DEV_ONLY_PATH_CLASSES.values()) <= self.SIX_CLASSES

    def test_recreate_class_reads_the_manifest(self):
        assert br.recreate_class("docs/claugentic-DECISIONS.md") == "init-seed"
        assert br.recreate_class("docs/claugentic-ROADMAP.md") == "init-seed"
        assert br.recreate_class("docs/claugentic-ARCHITECTURE_TREE.md") == "init-gen"
        assert br.recreate_class("docs/claugentic-INVARIANTS.md") == "recreate-on-demand"
        assert br.recreate_class("docs/claugentic-PRODUCT.md") == "recreate-on-demand"
        assert br.recreate_class("docs/claugentic-PRODUCT_SPEC.md") == "recreate-on-demand"
        assert br.recreate_class("scripts/build_release.py") == "self-gate"
        assert br.recreate_class("scripts/check_versions_synced.py") == "self-gate"
        assert br.recreate_class("CLAUDE.md") == "config"
        assert br.recreate_class(".gitignore") == "config"
        assert br.recreate_class("docs/RELEASE_CHECKLIST.md") == "dangle"

    def test_recreate_class_is_none_for_shipped_and_dir_swept_paths(self):
        # A shipped path has no class.
        assert br.recreate_class("README.md") is None
        # Dirs stay OUT of the classes: a file stripped only via DEV_ONLY_DIRS is NOT in the
        # per-file manifest, so it has no class (the closure gate reasons over file-level
        # classes only — this is the intended `None`).
        assert br.is_dev_only(".claude/plans/0034-release-consolidation.md") is True
        assert br.recreate_class(".claude/plans/0034-release-consolidation.md") is None


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
        # the shipped-content scanner (0028 S3), and the release builder itself.
        # doctor/WORKFLOW/implementer treat them adopter-aware.
        assert br.is_dev_only("scripts/check_doc_budgets.py") is True
        assert br.is_dev_only("scripts/check_versions_synced.py") is True
        assert br.is_dev_only("scripts/check_shipped_content.py") is True
        assert br.is_dev_only("scripts/build_release.py") is True

    def test_harness_own_plans_strip_cleanly(self):
        # The template move (S1) left `.claude/plans/` holding only the harness's OWN plans —
        # all stripped via the dir-prefix rule. Adopters read the /docs/ template and write
        # their own plans into their own `.claude/plans/`.
        assert br.is_dev_only(".claude/plans/0027-release-init-consistency.md") is True

    def test_seeds_ship_but_filled_ledgers_strip(self):
        # 0028 S4 — the one-time-seed kind. The pristine `_DECISIONS.md`/`_ROADMAP.md` seeds
        # SHIP so `init` can copy them (underscore stripped, create-if-absent); the harness's
        # OWN filled `DECISIONS.md`/`ROADMAP.md` STRIP. The load-bearing pin: an adopter gets
        # the pristine BLANK seed, never the harness's filled ledger.
        assert br.is_dev_only("docs/claugentic-_DECISIONS.md") is False
        assert br.is_dev_only("docs/claugentic-_ROADMAP.md") is False
        assert br.is_dev_only("docs/claugentic-DECISIONS.md") is True
        assert br.is_dev_only("docs/claugentic-ROADMAP.md") is True
        # 0030 S2 — the OPTIONAL engineering charter is the same one-time-seed kind: the
        # pristine `_CHARTER.md` seed SHIPS by DEFAULT-INCLUDE (absent from DEV_ONLY_FILES),
        # so `init` can copy it → `CHARTER.md` (create-if-absent). The harness keeps no live
        # `CHARTER.md` of its own (it follows its default grain — absent ≡ current behavior).
        assert br.is_dev_only("docs/claugentic-_CHARTER.md") is False


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


@pytest.mark.integration
class TestApplyHookBypass:
    """`_apply` commits the stripped release tree with `git commit --no-verify` (commit
    dfd2fea) on purpose: the dogfooding pre-commit tree-gate fires on the release build
    (it strips `docs/claugentic-ARCHITECTURE_TREE.md`, which the gate then reports
    "missing"). This pins that bypass — `_apply` must SUCCEED through an always-failing
    pre-commit hook — so a future edit that drops `--no-verify` can't silently re-break
    `--apply` (it broke once at the v0.3.0 release; loud-only-at-release before this).

    Hermetic: a throwaway repo under tmp_path, real git, real disk. The ambient git
    environment is fully isolated (GIT_CONFIG_GLOBAL/SYSTEM → an empty file; gpgsign
    pinned off) so pass/fail depends only on the code under test, never on this machine's
    git config or user hooks. Does NOT re-test the base-ancestry refusal (already pinned
    at `TestBaseAncestryGuard`) — it only SATISFIES that guard so `_apply` proceeds to the
    commit.
    """

    # Tracked tree that `classify()` splits BOTH ways: the architecture tree is the
    # stripped DEV_ONLY file the pre-commit gate reports "missing"; README.md ships.
    STRIPPED_FILE = "docs/claugentic-ARCHITECTURE_TREE.md"
    SHIPPED_FILE = "README.md"

    @staticmethod
    def _git(repo: Path, *args: str, hooks: bool = False) -> subprocess.CompletedProcess:
        """A setup/inspection git call against `repo` with the ambient config pinned off.

        `hooks=False` (default, for setup commits) disables hooks via an empty
        `core.hooksPath` so the fixture's own commits never trip the armed hook. The
        CONTROL commit passes `hooks=True` to let the repo's real hooksPath fire — that
        is what proves the hook is genuinely armed (see `test_control_hook_is_armed`).
        `_apply`'s own commits are NOT routed through here: they run via `build_release`'s
        `_git` with the repo's real hooksPath, so only `--no-verify` can save them.
        """
        pin = ["-c", "commit.gpgsign=false"]
        if not hooks:
            pin += ["-c", "core.hooksPath="]
        return subprocess.run(
            ["git", *pin, "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    @pytest.fixture
    def repo(self, tmp_path, monkeypatch):
        """A real git repo with a HEAD, an always-fail pre-commit hook armed via
        `core.hooksPath`, and `origin/main == HEAD` (satisfies the base-ancestry guard
        with zero network). Points `build_release` at this repo (`_repo_root` + chdir)."""
        empty_cfg = tmp_path / "empty-gitconfig"
        empty_cfg.write_text("", encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_cfg))
        monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty_cfg))

        repo = tmp_path / "repo"
        repo.mkdir()
        self._git(repo, "init", "-q").check_returncode()
        self._git(repo, "config", "user.email", "t@t.t").check_returncode()
        self._git(repo, "config", "user.name", "t").check_returncode()

        # A tree classify() splits both ways: a stripped DEV_ONLY file + a shipped file.
        (repo / "docs").mkdir()
        (repo / self.STRIPPED_FILE).write_text("# Tree\n- `README.md` — readme.\n", encoding="utf-8")
        (repo / self.SHIPPED_FILE).write_text("# Project\n", encoding="utf-8")
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "initial").check_returncode()

        # Always-fail pre-commit hook, armed via core.hooksPath. LF + explicit shebang for
        # win32/Git-Bash portability (git runs hooks via bundled bash; no chmod needed).
        hooksdir = tmp_path / "githooks"
        hooksdir.mkdir()
        hook = hooksdir / "pre-commit"
        hook.write_bytes(b"#!/bin/sh\nexit 1\n")
        self._git(repo, "config", "core.hooksPath", str(hooksdir)).check_returncode()

        # Satisfy the base-ancestry guard (`_dropped_merges`) with zero network:
        # origin/main == HEAD ⇒ rev-parse verifies and rev-list finds no dropped merges.
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()

        # Point `_apply` entirely at this repo. `_repo_root` covers the `-C`-passing calls
        # (status/rev-parse/worktree/commit); chdir covers `_tracked_files()`'s `ls-files`,
        # the one git call `_apply` makes WITHOUT `-C` (cwd-dependent).
        monkeypatch.setattr(br, "_repo_root", lambda: repo)
        monkeypatch.chdir(repo)
        return repo

    def test_control_hook_is_armed(self, repo):
        # Non-hollow guard: a PLAIN commit (hook ARMED, no --no-verify) MUST fail. If this
        # ever passes, the hook is dead/misconfigured and the happy-path assertion below
        # would be vacuous — _apply's success could no longer be attributed to --no-verify.
        (repo / "control.txt").write_text("x\n", encoding="utf-8")
        self._git(repo, "add", "-A", hooks=True).check_returncode()
        result = self._git(repo, "commit", "-qm", "should be blocked", hooks=True)
        assert result.returncode != 0, (
            "pre-commit hook did not fire — the happy-path assertion would be hollow"
        )

    def test_apply_succeeds_through_failing_hook(self, repo):
        # The release build commits the stripped tree with --no-verify, so the armed
        # always-fail pre-commit hook does NOT block it.
        assert br._apply() == 0

        # The `release` branch was created.
        rev = self._git(repo, "rev-parse", "--verify", "release")
        assert rev.returncode == 0 and rev.stdout.strip(), "release branch was not created"

        # The strip ran: the DEV_ONLY architecture tree is gone, the shipped file remains.
        ls = self._git(repo, "ls-tree", "-r", "release", "--name-only")
        ls.check_returncode()
        tree = ls.stdout.splitlines()
        assert self.STRIPPED_FILE not in tree, "stripped file leaked into the release tree"
        assert self.SHIPPED_FILE in tree, "shipped file missing from the release tree"
