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

# Realistic 2-space-indented manifest fixtures whose ONLY version field the targeted `--bump`
# replace must touch. `marketplace.json` deliberately carries a long description + a nested
# `source` object so a whole-file `json.dumps` reflow would produce a many-line diff — the
# targeted replace must leave everything but the one version line byte-identical.
_PLUGIN_MANIFEST_TEXT = (
    '{\n'
    '  "name": "claugentic-dev-harness",\n'
    '  "version": "0.3.1",\n'
    '  "description": "A reusable, self-improving Claude Code development harness.",\n'
    '  "license": "Apache-2.0"\n'
    '}\n'
)
_MARKETPLACE_MANIFEST_TEXT = (
    '{\n'
    '  "name": "sh4npeiris",\n'
    '  "plugins": [\n'
    '    {\n'
    '      "name": "claugentic-dev-harness",\n'
    '      "source": {\n'
    '        "source": "github",\n'
    '        "repo": "sh4npeiris/claugentic-dev-harness",\n'
    '        "ref": "release"\n'
    '      },\n'
    '      "description": "A long install-facing description that must NOT reflow on a bump.",\n'
    '      "version": "0.3.1",\n'
    '      "category": "development"\n'
    '    }\n'
    '  ]\n'
    '}\n'
)


def _write_manifest_pair(root: Path, version: str = "0.3.1") -> None:
    """Write a plugin.json + marketplace.json pair (both at `version`) under `root`."""
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / br.PLUGIN_MANIFEST).write_text(
        _PLUGIN_MANIFEST_TEXT.replace("0.3.1", version), encoding="utf-8"
    )
    (root / br.MARKETPLACE_MANIFEST).write_text(
        _MARKETPLACE_MANIFEST_TEXT.replace("0.3.1", version), encoding="utf-8"
    )


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

    # Paths DELIBERATELY added to the manifest after the migration snapshot above, each with
    # the change that added it. This is an explicit allow-delta, never a loosened assertion:
    # the frozen historical membership below is still asserted in full, and any path that
    # appears in neither set still fails loud (an accidental strip is exactly what this
    # catches). Add a line here only alongside its `DEV_ONLY_PATH_CLASSES` entry.
    # SIBLING: `test_check_shipped_content.TestDerivedHandListsEqualOld._ADDED_SINCE_MIGRATION`
    # carries the same delta for that module's own frozen hand-lists — deliberately restated
    # rather than imported (each is local build-history), so a new entry updates BOTH.
    POST_MIGRATION_ADDITIONS = frozenset(
        {
            # plan 0041 Slice 4 — the per-repo doc-budget caps config (`init-gen`): the
            # harness's own harness-tuned caps must not ship into adopter repos.
            ".claude/claugentic-doc-budgets.json",
        }
    )

    # The SIX classes — every dev-only FILE maps to exactly one (dirs stay out of the classes).
    SIX_CLASSES = frozenset(
        {"init-seed", "init-gen", "recreate-on-demand", "self-gate", "config", "dangle"}
    )

    def test_dict_keys_match_pre_migration_membership(self):
        # frozenset -> dict-keys is membership-preserving: the manifest keys are the prior
        # hand-authored `DEV_ONLY_FILES` frozenset plus the explicitly-declared additions.
        expected = self.PRE_MIGRATION_DEV_ONLY_FILES | self.POST_MIGRATION_ADDITIONS
        assert set(br.DEV_ONLY_PATH_CLASSES) == expected
        # ...and the historical membership is still pinned in full on its own — no path that
        # shipped/stripped before the migration may quietly leave the manifest.
        assert self.PRE_MIGRATION_DEV_ONLY_FILES <= set(br.DEV_ONLY_PATH_CLASSES)
        # The back-compat alias is derived from the dict keys — same membership.
        assert br.DEV_ONLY_FILES == expected

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

    def test_the_caps_config_strips_as_an_init_gen_output(self):
        # Plan 0041 Slice 4. `.claude/` is NOT a stripped subtree (only `.claude/plans/` is
        # dir-swept), and the release policy is DEFAULT-INCLUDE — so without a manifest entry
        # this file would ship the HARNESS's own harness-tuned caps (a 3,500 B cap on the
        # DECISIONS *index*) into every adopter repo, at exactly the path init seeds.
        assert br.is_dev_only(".claude/claugentic-doc-budgets.json") is True
        # `init-gen`, NOT `config`: shipped docs point an adopter AT this path, which is the
        # one thing the `config` class asserts is never true of its members.
        assert br.recreate_class(".claude/claugentic-doc-budgets.json") == "init-gen"
        # End-to-end through the classifier, not just the predicate: it lands in strip.
        ship, strip = br.classify(["README.md", ".claude/claugentic-doc-budgets.json"])
        assert strip == [".claude/claugentic-doc-budgets.json"]
        assert ship == ["README.md"]


class TestDecisionsShardDirStrips:
    """Plan 0040 — the sharded decisions ledger. The index (`docs/claugentic-DECISIONS.md`)
    keeps its `init-seed` class above; the SHARDS behind it are dir-swept dev-only.

    Why a test and not just the tuple entry: `is_dev_only` prefix-matches CASE-SENSITIVELY
    while the dev filesystem is case-INSENSITIVE, so a tracked path written
    `docs/claugentic-Decisions/…` would open fine locally, miss the sweep, and SHIP the
    harness's private build history. This asserts over the REAL tracked set (not a literal
    list) so that mis-cased path fails loud here instead of at a release.
    """

    SHARD_DIR = "docs/claugentic-decisions/"

    @pytest.fixture
    def at_repo_root(self, monkeypatch):
        """`br._tracked_files()` shells `git ls-files`, which is scoped to the CWD — run
        it from the git-authoritative repo root so this test holds from any directory."""
        monkeypatch.chdir(br._repo_root())

    def _tracked_under_shard_dir(self) -> list[str]:
        # Case-INSENSITIVE candidate match, so a mis-cased tracked path is still a candidate…
        return [f for f in br._tracked_files() if f.lower().startswith(self.SHARD_DIR)]

    def test_the_shard_dir_is_a_dev_only_prefix(self):
        assert self.SHARD_DIR in br.DEV_ONLY_DIRS

    def test_every_tracked_shard_file_classifies_dev_only(self, at_repo_root):
        tracked = self._tracked_under_shard_dir()
        assert tracked, "no tracked files under the shard dir — the sharded ledger must exist"
        # …and a case-SENSITIVE classification verdict, so any mismatch surfaces as a shipper.
        shipped = [f for f in tracked if not br.is_dev_only(f)]
        assert shipped == [], (
            "these decisions-shard files would SHIP — `is_dev_only` prefix-matches "
            f"case-sensitively against {self.SHARD_DIR!r}, so a mis-cased tracked path "
            f"escapes the sweep: {shipped}"
        )

    def test_the_index_still_ships_its_seed_and_strips_itself(self):
        # Path stability: sharding did NOT change the index's own ship/strip class.
        assert br.is_dev_only("docs/claugentic-DECISIONS.md") is True
        assert br.recreate_class("docs/claugentic-DECISIONS.md") == "init-seed"
        # A dir-swept shard carries no recreate-class — dirs stay OUT of the classes.
        assert br.recreate_class("docs/claugentic-decisions/honesty.md") is None


class TestBaseAncestryGuard:
    """`_missing_upstream_commits` is the mechanical defense against rebuilding the release
    from a stale base (the v0.1.40 distillation drop). Plan 0034 Slice 6 BROADENED it from a
    merge-only (`rev-list --merges`) form — which a direct NON-merge push to `main` slipped
    past (admin-bypass allows that push) — to catch ANY commit reachable from `origin/main`
    but not from HEAD. These are pure/offline — `_git` is monkeypatched so no real
    `git`/network is touched."""

    def test_current_base_drops_nothing(self, monkeypatch):
        # rev-parse (verify) succeeds; rev-list returns nothing → base is current.
        monkeypatch.setattr(br, "_git", lambda *args: "")
        assert br._missing_upstream_commits(Path(".")) == []

    def test_stale_base_returns_missing_shas(self, monkeypatch):
        def fake_git(*args):
            if "rev-parse" in args:
                return ""
            return "a7d2151\ndf20ed1\n"

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._missing_upstream_commits(Path(".")) == ["a7d2151", "df20ed1"]

    def test_direct_non_merge_commit_is_now_caught(self, monkeypatch):
        # THE broadening (Slice 6): the rev-list call must NOT filter to merges, so a direct
        # non-merge push to origin/main-not-HEAD is now visible. Assert the flag is gone AND
        # the returned SHA is reported (the pre-broadening `--merges` form would have missed
        # this non-merge commit and returned []).
        seen_args: list[tuple[str, ...]] = []

        def fake_git(*args):
            seen_args.append(args)
            if "rev-parse" in args:
                return ""
            return "beef123\n"  # a direct non-merge commit only on origin/main

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._missing_upstream_commits(Path(".")) == ["beef123"]
        rev_list = next(a for a in seen_args if "rev-list" in a)
        assert "--merges" not in rev_list, "rev-list must not filter to merge commits"

    def test_missing_upstream_ref_returns_none(self, monkeypatch):
        def fake_git(*args):
            if "rev-parse" in args:
                raise subprocess.CalledProcessError(1, ["git", *args])
            return ""

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._missing_upstream_commits(Path(".")) is None


class TestSemverParse:
    """`_parse_semver` must compare ORDINALLY (int triples), never lexically — the classic
    string-compare bug ranks `0.10.0 < 0.9.0`. It fails loud on a non-`X.Y.Z` version."""

    def test_parses_the_triple(self):
        assert br._parse_semver("0.3.1") == (0, 3, 1)
        assert br._parse_semver("1.20.300") == (1, 20, 300)

    def test_ordinal_not_lexical(self):
        # The load-bearing property: 0.10.0 sorts ABOVE 0.9.0 (a string compare gets this wrong).
        assert br._parse_semver("0.10.0") > br._parse_semver("0.9.0")

    def test_tolerates_surrounding_whitespace(self):
        assert br._parse_semver("  0.3.1\n") == (0, 3, 1)

    @pytest.mark.parametrize("bad", ["v0.3.1", "0.3", "0.3.1-rc1", "1.2.3.4", "", "abc"])
    def test_malformed_version_fails_loud(self, bad):
        with pytest.raises(ValueError):
            br._parse_semver(bad)


class TestVersionIncreaseGuard:
    """Plan 0034 Slice 4 / P0-1 — the version-must-INCREASE precondition, TAG-ANCHORED.
    `_version_increase_error` returns an actionable string to REFUSE, or `None` to ALLOW.
    Offline: `_read_manifest_version` + `_latest_release_tag` (+ `_tag_points_at_head`) are
    monkeypatched so no real manifest/git/network is touched.

    Plan 0041 Slice 2 (R4) — TWO call sites, one guard, under CI-publishes:
      * PREPARE time (the maintainer's repo, pre-tag): semantics UNCHANGED — the manifest
        version must be strictly greater than the latest `vX.Y.Z` tag.
      * PUBLISH time (the release workflow, AT the tagged commit): the tag now EXISTS and
        equals the manifest version, so `equal` must be ALLOWED — but ONLY when `v<new>`
        points at HEAD (i.e. this build IS that tag's build). Equal-at-a-different-commit
        stays a refusal: that is genuinely re-publishing a shipped version."""

    @staticmethod
    def _patch(monkeypatch, *, version: str, latest_tag: str | None, tag_at_head: bool = False):
        monkeypatch.setattr(br, "_read_manifest_version", lambda root: version)
        monkeypatch.setattr(br, "_latest_release_tag", lambda root: latest_tag)
        monkeypatch.setattr(br, "_tag_points_at_head", lambda root, tag: tag_at_head)

    def test_no_tag_first_release_allows(self, monkeypatch):
        # Bootstrap: no vX.Y.Z tag exists yet → first release → ALLOW (nothing to compare).
        self._patch(monkeypatch, version="0.1.0", latest_tag=None)
        assert br._version_increase_error(Path(".")) is None

    def test_greater_than_latest_tag_allows(self, monkeypatch):
        self._patch(monkeypatch, version="0.4.0", latest_tag="v0.3.1")
        assert br._version_increase_error(Path(".")) is None

    def test_equal_to_latest_tag_refuses_when_the_tag_is_elsewhere(self, monkeypatch):
        # PREPARE-time semantics, unchanged: a version already published as a tag that points
        # at some OTHER commit can't be re-shipped as "new".
        self._patch(monkeypatch, version="0.3.1", latest_tag="v0.3.1", tag_at_head=False)
        err = br._version_increase_error(Path("."))
        assert err is not None and "0.3.1" in err and "v0.3.1" in err

    def test_equal_allowed_iff_the_tag_points_at_head(self, monkeypatch):
        # PUBLISH-time (the release workflow runs AT the tagged commit): `v0.3.1` IS HEAD, so
        # this build is that tag's build, not a re-publish → ALLOW. Without this the workflow
        # could never publish anything (the tag precedes the build under CI-publishes).
        self._patch(monkeypatch, version="0.3.1", latest_tag="v0.3.1", tag_at_head=True)
        assert br._version_increase_error(Path(".")) is None

    def test_burned_version_recovery_is_named_in_the_refusal(self, monkeypatch):
        # R4: a red publish run leaves the tag behind, so the NEXT attempt at the same version
        # is refused. The message must name the recovery (bump forward; never reuse a tag).
        self._patch(monkeypatch, version="0.3.1", latest_tag="v0.3.1", tag_at_head=False)
        err = br._version_increase_error(Path("."))
        assert err is not None
        assert "never reused" in err.lower() or "never reuse" in err.lower()

    def test_less_than_latest_tag_refuses(self, monkeypatch):
        # A downgrade must be refused loudly.
        self._patch(monkeypatch, version="0.3.0", latest_tag="v0.3.1")
        assert br._version_increase_error(Path(".")) is not None

    def test_less_than_latest_tag_refuses_even_at_head(self, monkeypatch):
        # The equal-at-HEAD relaxation is EXACTLY that — a downgrade stays refused even if the
        # (higher) latest tag happens to sit on HEAD.
        self._patch(monkeypatch, version="0.3.0", latest_tag="v0.3.1", tag_at_head=True)
        assert br._version_increase_error(Path(".")) is not None

    def test_greater_than_never_consults_the_tag_position(self, monkeypatch):
        # Prepare-time path stays git-free beyond the tag list: the strictly-greater branch
        # must short-circuit BEFORE any rev-parse (a needless git call in the common case).
        monkeypatch.setattr(br, "_read_manifest_version", lambda root: "0.4.0")
        monkeypatch.setattr(br, "_latest_release_tag", lambda root: "v0.3.1")

        def _boom(root, tag):
            raise AssertionError("the strictly-greater branch must not resolve the tag")

        monkeypatch.setattr(br, "_tag_points_at_head", _boom)
        assert br._version_increase_error(Path(".")) is None

    def test_same_untagged_version_rebuild_allows(self, monkeypatch):
        # In-progress version 0.4.0 has NOT been tagged yet (the tag is created by the human at
        # publish). The latest PUBLISHED tag is still v0.3.1, so 0.4.0 > v0.3.1 → ALLOW —
        # a same-version rebuild of an untagged version is permitted.
        self._patch(monkeypatch, version="0.4.0", latest_tag="v0.3.1")
        assert br._version_increase_error(Path(".")) is None

    def test_ordinal_compare_not_lexical(self, monkeypatch):
        # 0.10.0 > v0.9.0 ordinally, though a string compare would refuse it.
        self._patch(monkeypatch, version="0.10.0", latest_tag="v0.9.0")
        assert br._version_increase_error(Path(".")) is None

    def test_malformed_manifest_version_fails_loud(self, monkeypatch):
        self._patch(monkeypatch, version="not-a-version", latest_tag="v0.3.1")
        with pytest.raises(ValueError):
            br._version_increase_error(Path("."))


class TestTagPointsAtHead:
    """`_tag_points_at_head` is the ONE thing that distinguishes the publish-time equal case
    from a genuine re-publish. It peels annotated tags (`^{commit}`) and FAILS CLOSED — any
    git error reads as False, so an unreadable tag can only ever TIGHTEN the guard."""

    def test_true_when_the_tag_resolves_to_head(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *args: "abc123\n")
        assert br._tag_points_at_head(Path("."), "v0.3.1") is True

    def test_false_when_the_tag_is_a_different_commit(self, monkeypatch):
        def fake_git(*args):
            return "abc123\n" if "v0.3.1^{commit}" in args else "def456\n"

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._tag_points_at_head(Path("."), "v0.3.1") is False

    def test_peels_the_annotated_tag(self, monkeypatch):
        seen: list[tuple[str, ...]] = []

        def fake_git(*args):
            seen.append(args)
            return "abc123\n"

        monkeypatch.setattr(br, "_git", fake_git)
        br._tag_points_at_head(Path("."), "v0.3.1")
        assert any("v0.3.1^{commit}" in a for a in seen), (
            "an ANNOTATED tag resolves to a tag object — it must be peeled with ^{commit}"
        )

    def test_git_failure_fails_closed(self, monkeypatch):
        def fake_git(*args):
            raise subprocess.CalledProcessError(1, ["git", *args])

        monkeypatch.setattr(br, "_git", fake_git)
        assert br._tag_points_at_head(Path("."), "v0.3.1") is False

    def test_empty_resolution_fails_closed(self, monkeypatch):
        # `rev-parse --verify --quiet` on a missing ref exits 0 with EMPTY stdout in some git
        # builds — an empty == empty compare must NOT read as "the tag is at HEAD".
        monkeypatch.setattr(br, "_git", lambda *args: "\n")
        assert br._tag_points_at_head(Path("."), "v0.3.1") is False


class TestLatestReleaseTag:
    """`_latest_release_tag` returns the highest `vX.Y.Z` tag (git's own `-v:refname` sort),
    or `None` when the repo has no version tag (the first-release bootstrap case). Offline —
    `_git` is monkeypatched."""

    def test_returns_first_semver_line(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *args: "v0.3.1\nv0.3.0\nv0.2.0\n")
        assert br._latest_release_tag(Path(".")) == "v0.3.1"

    def test_no_tags_returns_none(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *args: "")
        assert br._latest_release_tag(Path(".")) is None

    def test_skips_non_semver_tags(self, monkeypatch):
        # A stray non-vX.Y.Z tag (e.g. a nightly/build tag) is not a release anchor.
        monkeypatch.setattr(br, "_git", lambda *args: "vnightly\nv0.2.0\n")
        assert br._latest_release_tag(Path(".")) == "v0.2.0"


class TestReadManifestVersion:
    """`_read_manifest_version` reads `plugin.json`'s `version` and FAILS LOUD on a missing
    file, garbled JSON, or an absent `version` — never silently proceeds on an unknown
    version. Uses a real tmp file (no git/network)."""

    def _write(self, tmp_path: Path, text: str) -> Path:
        (tmp_path / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (tmp_path / br.PLUGIN_MANIFEST).write_text(text, encoding="utf-8")
        return tmp_path

    def test_reads_version(self, tmp_path):
        root = self._write(tmp_path, '{"version": "0.4.0"}')
        assert br._read_manifest_version(root) == "0.4.0"

    def test_missing_file_fails_loud(self, tmp_path):
        with pytest.raises(ValueError, match="is missing"):
            br._read_manifest_version(tmp_path)

    def test_garbled_json_fails_loud(self, tmp_path):
        root = self._write(tmp_path, "{not json")
        with pytest.raises(ValueError, match="not valid JSON"):
            br._read_manifest_version(root)

    def test_absent_version_fails_loud(self, tmp_path):
        root = self._write(tmp_path, '{"name": "x"}')
        with pytest.raises(ValueError, match="no top-level"):
            br._read_manifest_version(root)


class TestMechanizedDropCheck:
    """Plan 0034 Slice 7 / P1-3 — the mechanized drop-check as a SUBSET assertion:
    `origin/main`-not-HEAD ⊆ strip-set. `_dropped_shipped_paths` returns the SHIPPED paths in
    that diff (empty = clean), reusing the manifest's `classify()`-derived strip set. Offline —
    `_git` (the `diff --name-only`) is monkeypatched."""

    def test_strip_only_diff_passes(self, monkeypatch):
        # Every path origin/main carries that HEAD lacks is a dev-only (stripped) path → clean.
        monkeypatch.setattr(
            br, "_git", lambda *args: "docs/claugentic-DECISIONS.md\n.claude/plans/0034-x.md\n"
        )
        _, strip = br.classify(
            ["docs/claugentic-DECISIONS.md", ".claude/plans/0034-x.md", "README.md"]
        )
        assert br._dropped_shipped_paths(Path("."), strip) == []

    def test_shipped_file_missing_refuses(self, monkeypatch):
        # A SHIPPED file (README.md) present on origin/main-not-HEAD is merged work the build
        # would drop → it is returned (fail-loud signal).
        monkeypatch.setattr(
            br, "_git", lambda *args: "docs/claugentic-DECISIONS.md\nREADME.md\n"
        )
        _, strip = br.classify(["docs/claugentic-DECISIONS.md", "README.md"])
        assert br._dropped_shipped_paths(Path("."), strip) == ["README.md"]

    def test_reuses_classify_strip_coupling(self, monkeypatch):
        # The assertion is driven by classify()'s strip set, not a hardcoded list: a path is
        # "dropped" iff classify() ships it. Feed classify() a strip set that ALSO covers the
        # shipped-looking path and it's no longer flagged — proving the coupling.
        monkeypatch.setattr(br, "_git", lambda *args: "scripts/build_release.py\n")
        _, strip = br.classify(["scripts/build_release.py"])  # self-gate → stripped
        assert br._dropped_shipped_paths(Path("."), strip) == []

    def test_empty_diff_passes(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *args: "")
        assert br._dropped_shipped_paths(Path("."), []) == []

    def test_windows_backslash_paths_normalized(self, monkeypatch):
        # git may emit backslash paths on Windows; they must normalize to forward-slash before
        # the strip-set membership test (which uses forward-slash keys).
        monkeypatch.setattr(br, "_git", lambda *args: "docs\\claugentic-DECISIONS.md\n")
        _, strip = br.classify(["docs/claugentic-DECISIONS.md"])
        assert br._dropped_shipped_paths(Path("."), strip) == []


class TestParseBump:
    """`_parse_bump` reads the `--bump <version>` value from argv. Boundary-validated: present
    value returned; missing flag → None; flag with no following value → fail loud (the semver
    well-formedness is validated downstream in `_bump_manifests`, a single validation site)."""

    def test_absent_flag_returns_none(self):
        assert br._parse_bump(["--apply"]) is None

    def test_returns_the_value(self):
        assert br._parse_bump(["--apply", "--bump", "0.4.0"]) == "0.4.0"

    def test_flag_at_end_with_no_value_fails_loud(self):
        with pytest.raises(ValueError, match="requires a <version>"):
            br._parse_bump(["--apply", "--bump"])

    def test_flag_followed_by_another_flag_fails_loud(self):
        # `--bump --apply` — the next token is a flag, not a version value.
        with pytest.raises(ValueError, match="requires a <version>"):
            br._parse_bump(["--bump", "--apply"])


class TestBumpManifests:
    """Plan 0034 Slice 10 / C-1 — `_bump_manifests` writes the version into BOTH manifests from
    ONE value via a targeted `"version"`-field replace, both-or-neither / partial-write-safe.
    Uses real tmp files (no git/network)."""

    def _version_lines(self, text: str) -> list[str]:
        return [ln for ln in text.splitlines() if '"version"' in ln]

    def test_writes_both_manifests_to_the_given_version(self, tmp_path):
        _write_manifest_pair(tmp_path, "0.3.1")
        br._bump_manifests(tmp_path, "0.4.0")
        plugin = (tmp_path / br.PLUGIN_MANIFEST).read_text(encoding="utf-8")
        market = (tmp_path / br.MARKETPLACE_MANIFEST).read_text(encoding="utf-8")
        assert '"version": "0.4.0"' in plugin
        assert '"version": "0.4.0"' in market
        assert "0.3.1" not in plugin and "0.3.1" not in market

    def test_diff_is_version_only_no_reflow(self, tmp_path):
        # THE clean-diff property: only the single version line changes; every other line is
        # byte-identical (no whole-file json.dumps reflow of description/source/etc.).
        _write_manifest_pair(tmp_path, "0.3.1")
        before_plugin = (tmp_path / br.PLUGIN_MANIFEST).read_text(encoding="utf-8").splitlines()
        before_market = (tmp_path / br.MARKETPLACE_MANIFEST).read_text(encoding="utf-8").splitlines()
        br._bump_manifests(tmp_path, "0.4.0")
        after_plugin = (tmp_path / br.PLUGIN_MANIFEST).read_text(encoding="utf-8").splitlines()
        after_market = (tmp_path / br.MARKETPLACE_MANIFEST).read_text(encoding="utf-8").splitlines()
        for before, after in ((before_plugin, after_plugin), (before_market, after_market)):
            changed = [(b, a) for b, a in zip(before, after) if b != a]
            assert len(before) == len(after), "line count changed — the file was reflowed"
            assert len(changed) == 1, f"exactly one line must change, got {changed}"
            assert '"version"' in changed[0][0]

    def test_same_version_is_idempotent_noop(self, tmp_path):
        # A retry after an aborted publish re-runs cleanly: bumping to the SAME version rewrites
        # identical bytes (the diff stays empty).
        _write_manifest_pair(tmp_path, "0.4.0")
        before = (tmp_path / br.PLUGIN_MANIFEST).read_bytes()
        br._bump_manifests(tmp_path, "0.4.0")
        assert (tmp_path / br.PLUGIN_MANIFEST).read_bytes() == before

    def test_malformed_version_fails_loud_before_any_write(self, tmp_path):
        _write_manifest_pair(tmp_path, "0.3.1")
        before_plugin = (tmp_path / br.PLUGIN_MANIFEST).read_bytes()
        before_market = (tmp_path / br.MARKETPLACE_MANIFEST).read_bytes()
        with pytest.raises(ValueError):
            br._bump_manifests(tmp_path, "not-a-version")
        # Neither file touched — the semver check runs before any read/write.
        assert (tmp_path / br.PLUGIN_MANIFEST).read_bytes() == before_plugin
        assert (tmp_path / br.MARKETPLACE_MANIFEST).read_bytes() == before_market

    def test_missing_manifest_fails_loud_before_any_write(self, tmp_path):
        # plugin.json present, marketplace.json absent → the compute-both-in-memory phase aborts
        # BEFORE any write, so plugin.json is left untouched (both-or-neither).
        (tmp_path / ".claude-plugin").mkdir(parents=True)
        (tmp_path / br.PLUGIN_MANIFEST).write_text(_PLUGIN_MANIFEST_TEXT, encoding="utf-8")
        before_plugin = (tmp_path / br.PLUGIN_MANIFEST).read_bytes()
        with pytest.raises(ValueError, match="is missing"):
            br._bump_manifests(tmp_path, "0.4.0")
        assert (tmp_path / br.PLUGIN_MANIFEST).read_bytes() == before_plugin

    def test_both_or_neither_on_second_file_write_failure(self, tmp_path, monkeypatch):
        # Inject a write failure on the SECOND manifest AFTER the first was written: the writer
        # must fail loud with a clear "half-written" message (the operator recovers with
        # `git checkout`), never silently leave the pair drifted.
        _write_manifest_pair(tmp_path, "0.3.1")
        real_write = Path.write_text

        def flaky_write(self, data, *args, **kwargs):
            if self.name == "marketplace.json":
                raise OSError("disk full (injected)")
            return real_write(self, data, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", flaky_write)
        with pytest.raises(ValueError, match="HALF-WRITTEN"):
            br._bump_manifests(tmp_path, "0.4.0")
        # plugin.json got the new version; marketplace.json did NOT — the message names this so
        # the operator can `git checkout`. The failure is LOUD, never a silent drifted pair.
        assert '"version": "0.4.0"' in (tmp_path / br.PLUGIN_MANIFEST).read_text(encoding="utf-8")
        assert '"version": "0.3.1"' in (tmp_path / br.MARKETPLACE_MANIFEST).read_text(encoding="utf-8")

    def test_ambiguous_multiple_version_fields_fails_loud(self, tmp_path):
        # A manifest with two version fields is ambiguous — the targeted writer refuses rather
        # than guess which is the plugin version.
        (tmp_path / ".claude-plugin").mkdir(parents=True)
        (tmp_path / br.PLUGIN_MANIFEST).write_text(
            '{\n  "version": "0.3.1",\n  "dep": { "version": "1.0.0" }\n}\n', encoding="utf-8"
        )
        (tmp_path / br.MARKETPLACE_MANIFEST).write_text(_MARKETPLACE_MANIFEST_TEXT, encoding="utf-8")
        with pytest.raises(ValueError, match="version.*fields|fields"):
            br._bump_manifests(tmp_path, "0.4.0")


class TestGatedPublishCommand:
    """Plan 0041 Slice 2 — under CI-publishes the human's single act is a TAG PUSH; publishing
    belongs to `.github/workflows/release.yml`. `_gated_publish_command` must therefore contain
    NO `release`-branch push at all (that would be a second publisher racing the workflow)."""

    def test_exact_command_string(self):
        assert br._gated_publish_command("0.4.0") == (
            "git tag v0.4.0 && git push origin main v0.4.0"
        )

    def test_tag_is_created_by_the_human_not_in_build(self):
        # The tag lives in the printed command, never in-build.
        assert "git tag v" in br._gated_publish_command("1.2.3")

    def test_the_human_never_pushes_the_release_branch(self):
        # THE shape change: the workflow is the only publisher. Any `release`-branch push here
        # would fork the publish path (two writers of one branch).
        cmd = br._gated_publish_command("1.2.3")
        assert br.RELEASE_BRANCH not in cmd
        assert "--force" not in cmd

    def test_main_rides_along_with_the_tag(self):
        # The tagged commit must be reachable from `main` — otherwise the workflow would build
        # and publish a commit that never landed on the branch.
        assert "git push origin main v1.2.3" in br._gated_publish_command("1.2.3")


class TestUncommittedManifests:
    """`_uncommitted_manifests` decides whether `_apply` prints the commit-the-bump step. Under
    CI-publishes the workflow builds from the TAGGED COMMIT, so an uncommitted bump would tag a
    commit that still advertises the old version. Offline (`_git` monkeypatched)."""

    def test_clean_tree_returns_nothing(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *a: "")
        assert br._uncommitted_manifests(Path(".")) == []

    def test_reports_both_dirty_manifests(self, monkeypatch):
        monkeypatch.setattr(
            br,
            "_git",
            lambda *a: " M .claude-plugin/plugin.json\n M .claude-plugin/marketplace.json\n",
        )
        assert br._uncommitted_manifests(Path(".")) == list(br.VERSIONED_MANIFESTS)

    def test_ignores_unrelated_dirty_paths(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *a: " M README.md\n?? scratch.txt\n")
        assert br._uncommitted_manifests(Path(".")) == []

    def test_windows_backslash_paths_normalized(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *a: " M .claude-plugin\\plugin.json\n")
        assert br._uncommitted_manifests(Path(".")) == [br.PLUGIN_MANIFEST]


class TestMissingChangelogSection:
    """`_missing_changelog_section` is the PREPARE-time heads-up for the one thing the publish
    job hard-fails on after the tag is already spent. Real tmp files, no git."""

    @staticmethod
    def _write(root: Path, text: str) -> Path:
        (root / br.CHANGELOG).write_text(text, encoding="utf-8")
        return root

    def test_missing_heading_is_reported(self, tmp_path):
        self._write(tmp_path, "# Changelog\n\n## Unreleased\n\n- something\n")
        assert br._missing_changelog_section(tmp_path, "0.6.0") is True

    def test_populated_section_is_silent(self, tmp_path):
        self._write(tmp_path, "# Changelog\n\n## 0.6.0\n\n- the thing\n\n## 0.5.1\n\n- old\n")
        assert br._missing_changelog_section(tmp_path, "0.6.0") is False

    def test_an_empty_section_counts_as_missing(self, tmp_path):
        # A heading with no body produces empty release notes — the publish job refuses on that
        # too, so the heads-up must fire.
        self._write(tmp_path, "# Changelog\n\n## 0.6.0\n\n## 0.5.1\n\n- old\n")
        assert br._missing_changelog_section(tmp_path, "0.6.0") is True

    def test_absent_changelog_is_reported(self, tmp_path):
        assert br._missing_changelog_section(tmp_path, "0.6.0") is True


class TestCiStatusAdvisory:
    """Plan 0041 Slice 2 — the red-CI preflight is ADVISORY: it warns, it never blocks, and it
    goes SILENT whenever the answer isn't cheaply knowable. Offline — `subprocess.run` is
    monkeypatched throughout, and the fake CAPTURES the call so the two guarantees the docstring
    makes about the query itself (bounded, and about `main`) are pinned rather than assumed."""

    @staticmethod
    def _patch_gh(monkeypatch, *, returncode: int = 0, stdout: str = "[]") -> dict:
        seen: dict = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"], seen["kwargs"] = cmd, kwargs
            return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")

        monkeypatch.setattr(br.subprocess, "run", fake_run)
        return seen

    def test_the_query_is_bounded_and_scoped_to_main(self, monkeypatch):
        # Both were silently deletable: without `timeout` a hung `gh` stalls a release build
        # indefinitely, and a wrong `--branch` would advise on some other branch's health.
        seen = self._patch_gh(monkeypatch)
        br._ci_status_advisory(Path("."))
        assert seen["kwargs"].get("timeout") == br._CI_ADVISORY_TIMEOUT_S
        cmd = seen["cmd"]
        assert cmd[:2] == ["gh", "run"]
        assert cmd[cmd.index("--branch") + 1] == br.MAIN_BRANCH

    def test_green_run_is_silent(self, monkeypatch):
        self._patch_gh(
            monkeypatch,
            stdout='[{"status": "completed", "conclusion": "success", "url": "u"}]',
        )
        assert br._ci_status_advisory(Path(".")) is None

    def test_red_run_warns_and_labels_itself_advisory(self, monkeypatch):
        self._patch_gh(
            monkeypatch,
            stdout='[{"status": "completed", "conclusion": "failure", "url": "https://x/1"}]',
        )
        msg = br._ci_status_advisory(Path("."))
        assert msg is not None
        assert msg.startswith("ADVISORY")
        assert "does NOT block" in msg
        assert "https://x/1" in msg

    def test_in_progress_run_warns(self, monkeypatch):
        self._patch_gh(
            monkeypatch, stdout='[{"status": "in_progress", "conclusion": null, "url": "u"}]'
        )
        msg = br._ci_status_advisory(Path("."))
        assert msg is not None and "in_progress" in msg

    @pytest.mark.parametrize(
        "returncode,stdout,why",
        [
            (1, "", "unauthenticated / offline / no such repo"),
            (0, "not json", "garbled payload"),
            (0, "[]", "no runs yet"),
            (0, '{"message": "Not Found"}', "an API ERROR OBJECT where a list is documented"),
            (0, '["a string, not a run object"]', "a list of non-objects"),
        ],
    )
    def test_unknowable_conditions_silently_skip(self, monkeypatch, returncode, stdout, why):
        # The last two are the load-bearing ones: `gh` answers a failed lookup with an OBJECT,
        # and an indexed/keyed read of that shape would raise INSIDE `_apply` — crashing the
        # build this helper is documented never to affect. Silence is the only correct answer.
        self._patch_gh(monkeypatch, returncode=returncode, stdout=stdout)
        assert br._ci_status_advisory(Path(".")) is None, why

    def test_missing_gh_silently_skips(self, monkeypatch):
        def boom(cmd, **kwargs):
            raise FileNotFoundError("gh")

        monkeypatch.setattr(br.subprocess, "run", boom)
        assert br._ci_status_advisory(Path(".")) is None

    def test_timeout_silently_skips(self, monkeypatch):
        def boom(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 1)

        monkeypatch.setattr(br.subprocess, "run", boom)
        assert br._ci_status_advisory(Path(".")) is None

    def test_undecodable_output_silently_skips(self, monkeypatch):
        # `text=True` decoding happens inside `subprocess.run`; a UnicodeDecodeError is a
        # ValueError, which would otherwise escape past the OSError/SubprocessError catch.
        def boom(cmd, **kwargs):
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        monkeypatch.setattr(br.subprocess, "run", boom)
        assert br._ci_status_advisory(Path(".")) is None


class TestBumpOnlyDirty:
    """`_bump_only_dirty` decides whether a dirty working tree must refuse the build. With no
    `--bump`, any dirty file refuses; with `--bump`, a tree dirty ONLY in the two manifests is
    allowed (the intended version write), any other dirty path still refuses. Offline (`_git`
    monkeypatched)."""

    def test_clean_tree_never_refuses(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *a: "")
        assert br._bump_only_dirty(Path("."), None) is False
        assert br._bump_only_dirty(Path("."), "0.4.0") is False

    def test_no_bump_any_dirty_refuses(self, monkeypatch):
        monkeypatch.setattr(br, "_git", lambda *a: " M README.md\n")
        assert br._bump_only_dirty(Path("."), None) is True

    def test_bump_manifest_only_dirty_allowed(self, monkeypatch):
        monkeypatch.setattr(
            br,
            "_git",
            lambda *a: " M .claude-plugin/plugin.json\n M .claude-plugin/marketplace.json\n",
        )
        assert br._bump_only_dirty(Path("."), "0.4.0") is False

    def test_bump_but_other_file_dirty_refuses(self, monkeypatch):
        monkeypatch.setattr(
            br,
            "_git",
            lambda *a: " M .claude-plugin/plugin.json\n M src/leaked.py\n",
        )
        assert br._bump_only_dirty(Path("."), "0.4.0") is True


@pytest.mark.integration
class TestApplyHookBypass:
    """`_apply` commits the stripped release tree with `git commit --no-verify` (commit
    dfd2fea) on purpose: the dogfooding pre-commit tree-gate fires on the release build
    (it strips `docs/claugentic-ARCHITECTURE_TREE.md`, which the gate then reports
    "missing"). This pins that bypass — `_apply` must SUCCEED through an always-failing
    pre-commit hook — so a future edit that drops `--no-verify` can't silently re-break
    `--apply` (it broke once at the v0.3.0 release; loud-only-at-release before this).

    It ALSO exercises the P0-2 built-tree validation (0034 Slice 5): `_apply` runs the dev
    checkout's `check_shipped_content.py --root <built-worktree>` after the strip + before the
    commit, so the fixture repo ships a realistic minimal tree (init-seed seeds + a roster) plus
    REAL copies of the two scripts the validation subprocess needs (`check_shipped_content.py`
    imports `build_release.py`) — so the happy path proves the build proceeds THROUGH a passing
    validation, and `TestApplyBuiltTreeValidation` proves a broken built tree REFUSES the build.

    Hermetic: a throwaway repo under tmp_path, real git, real disk. The ambient git
    environment is fully isolated (GIT_CONFIG_GLOBAL/SYSTEM → an empty file; gpgsign
    pinned off) so pass/fail depends only on the code under test, never on this machine's
    git config or user hooks — and, since `_apply` gained the `gh` advisory preflight, the
    autouse `_no_ambient_gh` fixture below keeps that promise true (an unpatched call would be
    real network traffic at 20s a piece, decided by whoever's shell exported `GH_REPO`). Does
    NOT re-test the base-ancestry refusal (already pinned at `TestBaseAncestryGuard`) — it only
    SATISFIES that guard so `_apply` proceeds to the commit.
    """

    # Tracked tree that `classify()` splits BOTH ways: the architecture tree is the
    # stripped DEV_ONLY file the pre-commit gate reports "missing"; README.md ships.
    STRIPPED_FILE = "docs/claugentic-ARCHITECTURE_TREE.md"
    SHIPPED_FILE = "README.md"

    @pytest.fixture(autouse=True)
    def _no_ambient_gh(self, monkeypatch):
        """Neutralize the advisory preflight for every `_apply` in this class (and subclasses).

        The advisory is unit-tested exhaustively above; here it is pure ambient coupling — it
        would shell out to whatever `gh` this machine has, against whatever repo the environment
        points at. Tests that WANT an advisory override this explicitly (see
        `test_a_red_ci_advisory_never_blocks_the_build`), which monkeypatch honors: a later
        setattr in the test body wins over the fixture's."""
        monkeypatch.setattr(br, "_ci_status_advisory", lambda root: None)

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

    @classmethod
    def _seed_shippable_tree(cls, repo: Path) -> None:
        """Write a realistic minimal SHIPPABLE tree that passes `check_shipped_content.py`.

        The two `init-seed` seeds ship (closure Pass D holds), an agent + a skill dir give a
        FS-derived roster (Pass B), and REAL copies of `scripts/check_shipped_content.py` +
        `scripts/build_release.py` ship so `_apply`'s validation subprocess (which the fixture's
        `_repo_root` points at THIS repo) can find + import the scanner. `build_release.py` +
        `check_shipped_content.py` are `self-gate` (stripped from the built tree), so their
        presence in the SOURCE tree does not affect the built tree the scan reads."""
        src_scripts = Path(br.__file__).parent
        (repo / "docs").mkdir(exist_ok=True)
        (repo / cls.STRIPPED_FILE).write_text("# Tree\n- `README.md` — readme.\n", encoding="utf-8")
        (repo / cls.SHIPPED_FILE).write_text("# Project\n", encoding="utf-8")
        # init-seed seeds → Pass D closure holds over the real manifest.
        (repo / "docs" / "claugentic-_DECISIONS.md").write_text("# seed\n", encoding="utf-8")
        (repo / "docs" / "claugentic-_ROADMAP.md").write_text("# seed\n", encoding="utf-8")
        # FS-derived roster sources: one agent, one skill dir.
        (repo / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        (repo / ".claude" / "agents" / "honesty-reviewer.md").write_text("# agent\n", encoding="utf-8")
        (repo / "skills" / "audit").mkdir(parents=True, exist_ok=True)
        (repo / "skills" / "audit" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        # REAL scanner + release-builder so `_apply`'s validation subprocess runs against them.
        (repo / "scripts").mkdir(exist_ok=True)
        for name in ("check_shipped_content.py", "build_release.py"):
            (repo / "scripts" / name).write_text(
                (src_scripts / name).read_text(encoding="utf-8"), encoding="utf-8"
            )
        # Mirror the real repo's `.gitignore` for `__pycache__/` so running the validation
        # subprocess (which imports the scanner + writes `scripts/__pycache__/`) does not leave the
        # fixture's working tree "dirty" — the `.gitignore` is a `config` DEV_ONLY file, so it strips
        # from the built tree and does not affect the `--root` scan. (Without it, the pyc byproduct
        # would trip the clean-tree precondition on a --bump re-run.)
        (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        # A minimal source-of-truth manifest PAIR so the version-increase precondition (P0-1) can
        # read a version AND `--bump` (C-1) can write + re-sync both. The fixture creates NO
        # `vX.Y.Z` tag → first-release bootstrap → the version-increase guard allows.
        _write_manifest_pair(repo, "0.4.0")

    @classmethod
    def _init_repo(cls, tmp_path: Path, monkeypatch) -> Path:
        """A committed git repo (shippable tree + armed always-fail hook + origin/main == HEAD),
        with `build_release` pointed at it. Shared by the happy-path + validation-refusal tests."""
        empty_cfg = tmp_path / "empty-gitconfig"
        empty_cfg.write_text("", encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_cfg))
        monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty_cfg))

        repo = tmp_path / "repo"
        repo.mkdir()
        cls._git(repo, "init", "-q").check_returncode()
        cls._git(repo, "config", "user.email", "t@t.t").check_returncode()
        cls._git(repo, "config", "user.name", "t").check_returncode()

        cls._seed_shippable_tree(repo)
        cls._git(repo, "add", "-A").check_returncode()
        cls._git(repo, "commit", "-qm", "initial").check_returncode()

        # Always-fail pre-commit hook, armed via core.hooksPath. LF + explicit shebang for
        # win32/Git-Bash portability; chmod +x so git RUNS it on POSIX — git IGNORES a
        # non-executable hook on Linux/macOS (it prints "not set as executable" and skips
        # it, so the control commit would wrongly succeed). Windows ignores the mode bit,
        # so the chmod is a harmless no-op there.
        hooksdir = tmp_path / "githooks"
        hooksdir.mkdir()
        hook = hooksdir / "pre-commit"
        hook.write_bytes(b"#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        cls._git(repo, "config", "core.hooksPath", str(hooksdir)).check_returncode()

        # Satisfy the base-ancestry guard (`_missing_upstream_commits`) with zero network:
        # origin/main == HEAD ⇒ rev-parse verifies and rev-list finds no dropped merges.
        cls._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()

        # Point `_apply` entirely at this repo. `_repo_root` covers the `-C`-passing calls
        # (status/rev-parse/worktree/commit) AND the validation subprocess's scanner path;
        # chdir covers `_tracked_files()`'s `ls-files`, the one git call `_apply` makes
        # WITHOUT `-C` (cwd-dependent).
        monkeypatch.setattr(br, "_repo_root", lambda: repo)
        monkeypatch.chdir(repo)
        return repo

    @pytest.fixture
    def repo(self, tmp_path, monkeypatch):
        return self._init_repo(tmp_path, monkeypatch)

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
        # The release build commits the stripped tree with --no-verify (so the armed always-fail
        # pre-commit hook does NOT block it) AND passes the P0-2 built-tree validation.
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


@pytest.mark.integration
class TestApplyBuiltTreeValidation(TestApplyHookBypass):
    """Plan 0034 Slice 5 / P0-2 — `_apply` validates the BUILT (stripped) tree via the dev
    checkout's `check_shipped_content.py --root <built-worktree>` AFTER the strip + BEFORE the
    commit, and REFUSES the build (non-zero, no commit) if it fails. Reuses the `TestApplyHookBypass`
    hermetic repo setup (shippable tree + real scanner scripts + origin/main == HEAD).

    NON-VACUOUS by construction: the happy-path test above proves `_apply` returns 0 when the
    built tree is CLEAN; this proves it returns non-zero AND creates NO release commit when the
    built tree carries a shipped-content breach — so the validation can't be silently no-opping
    (a no-op would let the broken tree through and this test would fail)."""

    def test_broken_built_tree_refuses_and_does_not_commit(self, tmp_path, monkeypatch, capsys):
        repo = self._init_repo(tmp_path, monkeypatch)
        # Inject a stranded namespace token into a SHIPPED doc — the built (stripped) tree will
        # still carry it (WORKFLOW.md ships), so the `--root` scan's Pass B fails.
        (repo / "docs" / "claugentic-WORKFLOW.md").write_text(
            "Spawn `claugentic-dev-harness:ghost-role` (renamed away).\n", encoding="utf-8"
        )
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "strand a token").check_returncode()
        # origin/main must track the new HEAD or the base-ancestry guard would fire first.
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()

        rc = br._apply()
        assert rc != 0, "a broken built tree must refuse the build"
        out = capsys.readouterr()
        assert "ghost-role" in out.out
        assert "NOT committed" in out.err

        # NO release COMMIT was made — the build refused before `git commit`. `worktree add -B`
        # resets the `release` branch to HEAD up front, so the branch REF may exist, but it must
        # still point at HEAD (the un-stripped base), never at a new `release: clean build` commit.
        head = self._git(repo, "rev-parse", "HEAD").stdout.strip()
        rel = self._git(repo, "rev-parse", "release")
        if rel.returncode == 0:
            assert rel.stdout.strip() == head, "release advanced to a build commit despite refusal"
        # The stripped file never reached a committed release tree (no commit ran).
        ls = self._git(repo, "ls-tree", "-r", "release", "--name-only")
        assert self.STRIPPED_FILE in ls.stdout.splitlines(), (
            "a release build commit was made despite the validation refusal"
        )


@pytest.mark.integration
class TestApplyBumpOrchestration(TestApplyHookBypass):
    """Plan 0034 Slice 10 / C-1/C-2/C-3 — the ONE-command `--apply --bump <version>` flow.

    Reuses the `TestApplyHookBypass` hermetic repo (shippable tree + real scanner scripts +
    origin/main == HEAD + manifest pair at 0.4.0, NO vX.Y.Z tag → first-release bootstrap). Proves:
      * the happy path writes BOTH manifests, builds, and PRINTS the exact gated command;
      * the tool NEVER creates a tag or runs a push (the honesty guarantee — assert `git tag` empty);
      * an abort at EACH side-effect-bearing stage leaves NO tag, NO release commit, NO push;
      * a retry after an aborted publish (same version, no tag) succeeds (idempotent)."""

    @staticmethod
    def _tags(repo: Path) -> list[str]:
        out = TestApplyHookBypass._git(repo, "tag", "--list").stdout
        return [t.strip() for t in out.splitlines() if t.strip()]

    @staticmethod
    def _release_manifest_version(repo: Path, manifest: str) -> str:
        """The plugin `version` of `manifest` as COMMITTED on the built `release` branch (read via
        `git show release:<path>`, NOT the working tree) — the release ADVERTISED version.

        Handles BOTH manifest shapes: plugin.json carries `version` at top level; marketplace.json
        carries it under `plugins[0].version` (matching the source-of-truth pair the bump writes)."""
        import json as _json

        out = TestApplyHookBypass._git(repo, "show", f"release:{manifest}")
        out.check_returncode()
        data = _json.loads(out.stdout)
        return data["version"] if "version" in data else data["plugins"][0]["version"]

    def test_built_release_carries_the_bumped_version(self, repo):
        # THE regression this whole fix exists for: the fixture's HEAD manifests are at 0.4.0, and we
        # bump to 0.5.0. The bump lands in the dev WORKING TREE (uncommitted), while the build worktree
        # is created from the COMMITTED HEAD — so without the copy-into-built-worktree fix the built
        # `release` would ship 0.5.0 content advertised as HEAD's 0.4.0 (the forgotten-bump footgun).
        # Assert the BUILT release branch's BOTH manifests carry 0.5.0 (the bump), not HEAD's 0.4.0.
        assert br._apply(bump="0.5.0") == 0
        assert self._release_manifest_version(repo, br.PLUGIN_MANIFEST) == "0.5.0"
        assert self._release_manifest_version(repo, br.MARKETPLACE_MANIFEST) == "0.5.0"
        # And HEAD stayed at 0.4.0 — the bump is UNCOMMITTED on the current branch (abort-safe).
        head_plugin = self._git(repo, "show", "HEAD:.claude-plugin/plugin.json")
        assert '"version": "0.4.0"' in head_plugin.stdout

    def test_plain_apply_release_carries_head_version_unchanged(self, repo):
        # The no-`--bump` path must stay byte-identical to the pre-fix behavior: build from HEAD, so
        # the built release carries HEAD's version (0.4.0) exactly — the copy only fires on `--bump`.
        assert br._apply() == 0
        assert self._release_manifest_version(repo, br.PLUGIN_MANIFEST) == "0.4.0"
        assert self._release_manifest_version(repo, br.MARKETPLACE_MANIFEST) == "0.4.0"

    def test_apply_bump_writes_both_manifests_and_prints_gated_command(self, repo, capsys):
        # Bump to a NEW version (0.4.0 -> 0.5.0). First release has no tag, so the version-increase
        # guard allows it; --bump writes both manifests; the build succeeds and prints the command.
        rc = br._apply(bump="0.5.0")
        assert rc == 0
        plugin = (repo / br.PLUGIN_MANIFEST).read_text(encoding="utf-8")
        market = (repo / br.MARKETPLACE_MANIFEST).read_text(encoding="utf-8")
        assert '"version": "0.5.0"' in plugin and '"version": "0.5.0"' in market

        out = capsys.readouterr().out
        # C-3 as re-shaped by 0041 S2: the EXACT gated command is printed, and it TAGS only.
        assert "git tag v0.5.0 && git push origin main v0.5.0" in out
        assert "--force" not in out, "the human never force-pushes anything under CI-publishes"
        # Honesty framing: the workflow publishes, and only on green.
        assert "release.yml" in out and "only if they are all green" in out
        # The burned-version trade-off is stated where the human decides to tag.
        assert "bumping forward" in out and "reusing the tag" in out
        # The bump is uncommitted here, so the commit-first step must be surfaced — a tag placed
        # now would point at a commit still advertising 0.4.0.
        assert "UNCOMMITTED" in out and "git commit -m" in out
        # The fixture carries no CHANGELOG, so the prepare-time heads-up must fire too — this is
        # what pins the print block as WIRED, not merely unit-tested in isolation.
        assert "BEFORE YOU TAG" in out and "0.5.0" in out

        # THE honesty guarantee: the tool did NOT create the tag and did NOT push.
        assert self._tags(repo) == [], "the build must NOT create a tag — the human creates it"

    def test_a_populated_changelog_section_silences_the_heads_up(self, repo, capsys):
        # The negative half: with the section present, `_apply` says nothing about the CHANGELOG.
        # (Non-vacuous against the assertion above, which fires on the same code path.)
        (repo / br.CHANGELOG).write_text(
            "# Changelog\n\n## 0.5.0\n\n- the thing that changed\n", encoding="utf-8"
        )
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "add changelog").check_returncode()
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()
        assert br._apply(bump="0.5.0") == 0
        assert "BEFORE YOU TAG" not in capsys.readouterr().out

    def test_apply_bump_does_not_execute_a_push(self, repo):
        # No remote is configured on the fixture repo; a real push would ERROR. The flow returning
        # 0 while origin/release is unchanged proves no push ran.
        before = self._git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
        assert br._apply(bump="0.5.0") == 0
        # origin refs are untouched (no push executed).
        after = self._git(repo, "rev-parse", "refs/remotes/origin/main").stdout.strip()
        assert before == after
        assert self._tags(repo) == []

    def test_abort_at_bump_stage_leaves_no_side_effects(self, repo):
        # Stage: --bump write. A malformed version aborts in _bump_manifests BEFORE the version
        # bump touches disk (semver-checked first) → no tag, no release commit, manifests unchanged.
        before_plugin = (repo / br.PLUGIN_MANIFEST).read_bytes()
        head_before = self._git(repo, "rev-parse", "HEAD").stdout.strip()
        rc = br._apply(bump="not-a-version")
        assert rc == 1
        assert self._tags(repo) == []
        assert (repo / br.PLUGIN_MANIFEST).read_bytes() == before_plugin
        # No release commit: release ref, if it exists, still points at HEAD.
        rel = self._git(repo, "rev-parse", "release")
        if rel.returncode == 0:
            assert rel.stdout.strip() == head_before

    def test_abort_at_version_increase_stage_leaves_no_tag(self, repo):
        # Stage: version-increase. v0.5.0 is already PUBLISHED at an EARLIER commit; bumping to
        # 0.5.0 here would re-ship a shipped version → REFUSE. (The tag must sit off HEAD: an
        # equal version whose tag IS HEAD is the legitimate publish-time rebuild, pinned below.)
        # The bump WROTE the manifests first (the operator-revertable working-tree change), but NO
        # tag is created and NO release commit.
        published = self._git(repo, "rev-parse", "HEAD").stdout.strip()
        self._git(repo, "tag", "v0.5.0", published).check_returncode()
        (repo / "later.txt").write_text("later work\n", encoding="utf-8")
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "work after the release").check_returncode()
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()

        rc = br._apply(bump="0.5.0")
        assert rc == 1
        # No NEW tag beyond the one we set up.
        assert self._tags(repo) == ["v0.5.0"]
        # The working-tree bump is left for the operator to `git checkout` (defined behavior).
        assert '"version": "0.5.0"' in (repo / br.PLUGIN_MANIFEST).read_text(encoding="utf-8")

    def test_publish_time_rebuild_at_the_tagged_commit_is_allowed(self, repo, capsys):
        # Plan 0041 S2 / R4, end-to-end: this is exactly what `release.yml`'s publish job does —
        # `--apply` (no --bump) at the commit the `vX.Y.Z` tag points at, where the manifest
        # version EQUALS the tag. Under the old strictly-greater rule the workflow could never
        # build anything; the narrow equal-at-HEAD relaxation is what makes CI-publishes possible.
        self._git(repo, "tag", "v0.4.0").check_returncode()  # fixture manifests are at 0.4.0
        assert br._apply() == 0
        assert self._release_manifest_version(repo, br.PLUGIN_MANIFEST) == "0.4.0"
        # Still no NEW tag and no push — the workflow pushes the branch, this script never does.
        assert self._tags(repo) == ["v0.4.0"]
        # NEGATIVE control: the tree is clean here, so the commit-the-bump banner must be ABSENT.
        # Without this, `if pending:` -> `if True:` survives and CI logs would carry a "commit the
        # bump before tagging" instruction that is false on exactly this path.
        assert "UNCOMMITTED" not in capsys.readouterr().out

    def test_publish_time_rebuild_accepts_an_annotated_tag(self, repo):
        # An ANNOTATED tag resolves to a tag OBJECT, not a commit — the `^{commit}` peel in
        # `_tag_points_at_head` is the only reason the equal-at-HEAD relaxation works for one.
        # Every other real-git test here uses a lightweight tag, so without this the peel is
        # pinned at argument-string level only.
        self._git(repo, "tag", "-a", "v0.4.0", "-m", "release v0.4.0").check_returncode()
        annotated = self._git(repo, "cat-file", "-t", "v0.4.0").stdout.strip()
        assert annotated == "tag", "fixture must produce an ANNOTATED tag or this is vacuous"
        assert br._apply() == 0

    def test_publish_time_relaxation_does_not_cover_another_commit(self, repo):
        # The relaxation is narrow BY COMMIT, not by version: same equal-version situation, but the
        # tag sits elsewhere → still refused. (Non-vacuous against the test above: identical
        # versions, only the tag's commit differs.)
        published = self._git(repo, "rev-parse", "HEAD").stdout.strip()
        self._git(repo, "tag", "v0.4.0", published).check_returncode()
        (repo / "later.txt").write_text("later work\n", encoding="utf-8")
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "work after the release").check_returncode()
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()
        assert br._apply() == 1

    def test_a_red_ci_advisory_never_blocks_the_build(self, repo, capsys, monkeypatch):
        # The advisory's honest scope, end-to-end: a RED main prints a warning and the build still
        # succeeds. (Non-vacuous — the same run is asserted green in the happy-path tests above,
        # so this pins the WARNING appears, not merely that nothing broke.)
        monkeypatch.setattr(
            br, "_ci_status_advisory", lambda root: "ADVISORY (warn-only): main is red"
        )
        assert br._apply(bump="0.5.0") == 0
        captured = capsys.readouterr()
        assert "ADVISORY (warn-only): main is red" in captured.err

    def test_abort_at_built_tree_validation_leaves_no_tag(self, tmp_path, monkeypatch):
        # Stage: built-tree validation. Strand a token in a SHIPPED doc so the built-tree scan
        # fails AFTER the bump + build → refuse with no commit, and crucially NO tag.
        repo = self._init_repo(tmp_path, monkeypatch)
        (repo / "docs" / "claugentic-WORKFLOW.md").write_text(
            "Spawn `claugentic-dev-harness:ghost-role` (renamed away).\n", encoding="utf-8"
        )
        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "strand a token").check_returncode()
        self._git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").check_returncode()
        head = self._git(repo, "rev-parse", "HEAD").stdout.strip()

        rc = br._apply(bump="0.5.0")
        assert rc != 0
        assert self._tags(repo) == [], "a validation abort must not leave a tag"
        rel = self._git(repo, "rev-parse", "release")
        if rel.returncode == 0:
            assert rel.stdout.strip() == head, "no release build commit despite the abort"

    def test_retry_after_aborted_publish_succeeds(self, repo, capsys):
        # Retry-after-failed-push: the FIRST run bumps + builds + prints the command but the human
        # never publishes (so NO tag is created). Re-running --apply --bump <same version> must
        # SUCCEED — latest_tag is still the previous PUBLISHED version (none here → first release),
        # so the version-increase guard still passes and the same-version bump is an idempotent noop.
        assert br._apply(bump="0.5.0") == 0
        assert self._tags(repo) == []  # publish declined → no tag
        capsys.readouterr()  # drain
        # Second run at the SAME version — must not refuse.
        rc = br._apply(bump="0.5.0")
        assert rc == 0
        out = capsys.readouterr().out
        assert "git tag v0.5.0" in out
        assert self._tags(repo) == []

    def test_apply_bump_refuses_non_increasing_version(self, repo):
        # A published tag exists; a bump to an EQUAL/LOWER version is refused (the version-increase
        # guard reuses the same compare as the no-bump path).
        self._git(repo, "tag", "v0.6.0").check_returncode()
        rc = br._apply(bump="0.5.0")  # 0.5.0 < v0.6.0 → downgrade
        assert rc == 1
        assert self._tags(repo) == ["v0.6.0"]
