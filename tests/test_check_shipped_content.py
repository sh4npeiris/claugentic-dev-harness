"""Hermetic tests for the shipped-content scanner (`scripts/check_shipped_content.py`).

Each pure core takes an injected `{path: text}` map, so these run with NO real git and
NO real filesystem — they pin the EXACT literals the gate must catch and the exact
false-positive classes it must NOT catch (the two load-bearing regression pins:
a `claugentic-dev-harness:audit` slash-command token and the `<!-- product-critic:... -->`
memory-fence token are both CLEAN). The git boundary is monkeypatched for the `main()`
exit-code tests, including the fail-loud-on-git-error case.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

import build_release as br
import check_shipped_content as csc

# A representative VALID set (agents ∪ skills ∪ {update}) for the namespace pass tests.
VALID = csc.valid_roster(
    agent_basenames={"lens-reviewer", "implementer", "synthesizer-gate"},
    skill_basenames={"audit", "build", "init", "product", "doctor"},
)


class TestNonAsciiJsPassC:
    def test_non_ascii_js_is_flagged(self):
        # An em-dash (U+2014) in a shipped engine *.js is a HARD problem.
        texts = {"engine/audit.js": "const x = 1; // a comment — with an em-dash\n"}
        problems = csc.scan_non_ascii_js(texts)
        assert len(problems) == 1
        assert "engine/audit.js:1" in problems[0]
        assert "U+2014" in problems[0]

    def test_ascii_only_js_is_clean(self):
        texts = {"engine/qa.js": "const x = 1; // plain ASCII comment -- all good\n"}
        assert csc.scan_non_ascii_js(texts) == []

    def test_first_offender_reported_with_line_number(self):
        # Two offending lines, but only the FIRST per file is reported (enough to locate).
        texts = {"engine/verify.js": "line one ascii\nline two has → arrow\nline three —\n"}
        problems = csc.scan_non_ascii_js(texts)
        assert len(problems) == 1
        assert "engine/verify.js:2" in problems[0]
        assert "U+2192" in problems[0]

    def test_multiple_js_each_flagged(self):
        texts = {
            "engine/audit.js": "ok\n—\n",
            "engine/qa.js": "fine×\n",
        }
        problems = csc.scan_non_ascii_js(texts)
        assert len(problems) == 2
        assert any("engine/audit.js" in p for p in problems)
        assert any("engine/qa.js" in p for p in problems)

    def test_non_ascii_js_drives_evaluate_exit_1(self, monkeypatch, tmp_path):
        # End-to-end through evaluate(): a shipped `engine/x.js` with a non-ASCII char produces
        # a HARD problem (drives main() to exit 1); a `.md` em-dash does not.
        ship = ["engine/x.js", "docs/x.md"]
        texts = {
            "engine/x.js": "const x = 1; // em-dash —\n",
            "docs/x.md": "prose em-dash — fine\n",
        }
        monkeypatch.setattr(csc, "_shipped_files", lambda root: ship)
        monkeypatch.setattr(csc, "_read_shipped_texts", lambda root, s: texts)
        monkeypatch.setattr(csc, "_fs_agent_basenames", lambda root: set())
        monkeypatch.setattr(csc, "_fs_skill_basenames", lambda root: set())
        problems, _warnings, summary = csc.evaluate(tmp_path)
        assert summary == ""
        assert any("engine/x.js" in p and "U+2014" in p for p in problems)
        assert not any("docs/x.md" in p for p in problems)  # .md em-dash never flagged


class TestNamespacePassB:
    def test_stranded_agent_token_is_flagged(self):
        texts = {
            "skills/audit/SKILL.md": "spawn `claugentic-dev-harness:plan-reviewer` to review.",
        }
        problems = csc.scan_namespace(texts, VALID)
        assert len(problems) == 1
        assert "plan-reviewer" in problems[0]
        assert "skills/audit/SKILL.md" in problems[0]

    def test_multiple_stranded_tokens_each_flagged(self):
        texts = {
            "docs/x.md": (
                "`claugentic-dev-harness:plan-reviewer` and "
                "`claugentic-dev-harness:implementer-architect` are both stale."
            ),
        }
        problems = csc.scan_namespace(texts, VALID)
        assert len(problems) == 2
        assert any("plan-reviewer" in p for p in problems)
        assert any("implementer-architect" in p for p in problems)

    def test_valid_agent_token_is_clean(self):
        texts = {"skills/build/SKILL.md": "spawn `claugentic-dev-harness:lens-reviewer`."}
        assert csc.scan_namespace(texts, VALID) == []

    def test_slash_command_token_is_not_flagged(self):
        # ★ LOAD-BEARING PIN 1: `:audit` is a slash-command (= skill basename), NOT an agent.
        # A roster-only VALID set would HARD-fail on it; this proves VALID includes commands.
        texts = {"README.md": "Run `/claugentic-dev-harness:audit` to audit your code."}
        assert csc.scan_namespace(texts, VALID) == []

    def test_memory_fence_token_is_not_flagged(self):
        # ★ LOAD-BEARING PIN 2: the memory-fence token is `product-critic:...` WITHOUT the
        # `claugentic-dev-harness:` prefix — full-prefix keying structurally excludes it.
        texts = {
            "skills/product/SKILL.md": "<!-- product-critic:rejected-proposals -->\n...fence...",
        }
        assert csc.scan_namespace(texts, VALID) == []

    def test_update_prose_only_token_is_valid(self):
        texts = {"skills/init/SKILL.md": "the `claugentic-dev-harness:update` command."}
        assert csc.scan_namespace(texts, VALID) == []


class TestDanglingPassAa:
    def test_release_checklist_reference_is_flagged(self):
        texts = {"docs/claugentic-WORKFLOW.md": "Follow `docs/RELEASE_CHECKLIST.md` before release."}
        problems = csc.scan_dangling(texts, csc.dangling_paths())
        assert len(problems) == 1
        assert "RELEASE_CHECKLIST.md" in problems[0]

    def test_numbered_plan_file_reference_is_flagged(self):
        texts = {"skills/build/SKILL.md": "see `.claude/plans/0027-release-init-consistency.md`."}
        problems = csc.scan_dangling(texts, csc.dangling_paths())
        assert len(problems) == 1
        assert "0027-release-init-consistency.md" in problems[0]

    def test_bare_plans_dir_reference_is_clean(self):
        # The bare `.claude/plans/` DIRECTORY is the adopter's own in-flight-plans dir (init
        # manages it) — a legitimate reference, never a dangle.
        texts = {"skills/init/SKILL.md": "adopters copy one per plan into their own `.claude/plans/`."}
        assert csc.scan_dangling(texts, csc.dangling_paths()) == []

    def test_placeholder_plan_file_reference_is_clean(self):
        # `NNNN-<slug>` documents the NAMING convention, not a real file — must not flag.
        texts = {"docs/claugentic-WORKFLOW.md": "draft `.claude/plans/NNNN-<slug>.md` per change."}
        assert csc.scan_dangling(texts, csc.dangling_paths()) == []

    def test_dangling_set_is_derived_and_excludes_gate_scripts(self):
        # MIGRATED PIN (0034 Slice 2): the dangle set is now derived from the manifest's
        # `dangle` class (via `recreate_class`), no longer from three hand-lists. The
        # contract it pins is UNCHANGED — the derived dangle set is RELEASE_CHECKLIST only:
        # the recreated files (init-seed/init-gen/recreate-on-demand), the harness-self gate
        # scripts (A.b's concern), and repo-config are all subtracted.
        dangling = csc.dangling_paths()
        assert "docs/RELEASE_CHECKLIST.md" in dangling
        assert "scripts/check_versions_synced.py" not in dangling  # self-gate → A.b, not A.a
        assert "docs/claugentic-DECISIONS.md" not in dangling      # init-seed → recreated
        assert "docs/claugentic-INVARIANTS.md" not in dangling     # recreate-on-demand
        assert "CLAUDE.md" not in dangling                          # config (repo machinery)
        # And it equals exactly the manifest's `dangle`-class members — the single source.
        dangle_class = frozenset(
            p for p in br.DEV_ONLY_FILES if br.recreate_class(p) == "dangle"
        )
        assert dangling == dangle_class


class TestDerivedHandListsEqualOld:
    """The 0034 Slice-2 DERIVE-ALONGSIDE safety net (steps 1-3 of the plan's method).

    The three sets `check_shipped_content` used to hand-maintain are now DERIVED from
    `build_release.recreate_class` (the ONE authored manifest). These tests carry the OLD
    hand-list values as frozen literal expectations and assert the derived module-level sets
    reproduce the EXACT membership — proving the DRY migration is a provable no-op, not a
    lossy re-encoding. (This is the "keep both until equality holds" net: the old values live
    here, the derivation lives in the module; the two must agree.)
    """

    # Verbatim copies of the three PRE-migration hand-lists (frozen expectations).
    _OLD_INIT_CREATES = frozenset(
        {
            "docs/claugentic-DECISIONS.md",
            "docs/claugentic-ROADMAP.md",
            "docs/claugentic-ARCHITECTURE_TREE.md",
            "docs/claugentic-INVARIANTS.md",
            "docs/claugentic-PRODUCT.md",
            "docs/claugentic-PRODUCT_SPEC.md",
            "docs/claugentic-CHARTER.md",  # phantom: never a tracked/stripped file
        }
    )
    _OLD_HARNESS_SELF_SCRIPTS = frozenset(
        {
            "scripts/build_release.py",
            "scripts/check_versions_synced.py",
            "scripts/check_doc_budgets.py",
            "scripts/check_shipped_content.py",
        }
    )
    _OLD_DANGLE_EXCLUDED = frozenset(
        {
            ".claude/settings.json",
            "CLAUDE.md",
            "pyproject.toml",
            ".gitignore",
            ".gitattributes",
        }
    )

    # Manifest paths added AFTER those three snapshots were frozen, each with the change that
    # added it and the class it carries. An explicit allow-delta, never a loosened assertion:
    # every historical membership below is still asserted in full, and a path in neither set
    # still fails these pins loud. Mirrors `test_build_release.TestManifestMigration
    # .POST_MIGRATION_ADDITIONS` (deliberately restated, not imported — each of these frozen
    # snapshots is local build-history for the module it guards); a new entry updates BOTH.
    _ADDED_SINCE_MIGRATION = frozenset(
        {
            # plan 0041 Slice 4 — the per-repo doc-budget caps config, class `init-gen`, so it
            # joins the RECREATED partition (never the dangle set).
            ".claude/claugentic-doc-budgets.json",
        }
    )

    # The mirror image: manifest paths REMOVED since those snapshots were frozen. Same
    # discipline as the additions — the snapshot above is never edited, the delta carries the
    # change, and a path that leaves a snapshot without a line here still fails these pins.
    # Mirrors `test_build_release.TestManifestMigration.POST_MIGRATION_REMOVALS` (deliberately
    # restated, not imported); a new entry updates BOTH.
    _REMOVED_SINCE_MIGRATION = frozenset(
        {
            # plan 0041 Slice 6 — the doc-budget gate SHIPS, so it leaves the `self-gate`
            # class entirely. Consequences that ride this one line: it drops out of
            # `HARNESS_SELF_SCRIPTS`, so Pass A.b no longer scans shipped text for its
            # basename, and Pass D no longer counts it as a stripped NEEDS path. Nothing in
            # `check_shipped_content.py` was hand-edited — every set re-derives. Spelled AS IT
            # WAS IN THE MANIFEST (Slice 7 renamed the script to
            # `scripts/claugentic-check_doc_budgets.py`): this is set arithmetic against a
            # frozen snapshot, so respelling it would break the subtraction.
            "scripts/check_doc_budgets.py",
        }
    )

    def test_harness_self_scripts_derived_equals_old(self):
        # LITERALLY equal to the old hand-list net of the declared removals — every `self-gate`
        # path is accounted for. (This set is also A.b's scan target, so the equality is
        # load-bearing for that pass: a script that leaves it also leaves the caveat scan.)
        assert csc.HARNESS_SELF_SCRIPTS == (
            self._OLD_HARNESS_SELF_SCRIPTS - self._REMOVED_SINCE_MIGRATION
        )

    def test_dangle_excluded_derived_equals_old(self):
        # LITERALLY equal — every `config` path is exactly the old `_DANGLE_EXCLUDED`.
        assert csc._DANGLE_EXCLUDED == self._OLD_DANGLE_EXCLUDED

    def test_recreated_derived_equals_old_modulo_phantom_charter(self):
        # The derived recreated set (init-seed ∪ init-gen ∪ recreate-on-demand) equals the old
        # `_INIT_CREATES` EXCEPT the phantom `docs/claugentic-CHARTER.md`: the harness ships
        # only the `_CHARTER.md` SEED, never a tracked `CHARTER.md`, so CHARTER was never in
        # `DEV_ONLY_FILES` and its subtraction in `dangling_paths()` was always a no-op. The
        # derivation correctly drops it; the delta is EXACTLY that one dead entry.
        assert self._OLD_INIT_CREATES - csc._RECREATED == {"docs/claugentic-CHARTER.md"}
        # ...and in the other direction, exactly the paths declared as post-snapshot additions
        # (a recreate-class path that is in NEITHER list is an unexplained membership change).
        assert csc._RECREATED - self._OLD_INIT_CREATES == self._ADDED_SINCE_MIGRATION
        # The phantom was never a member of the strip set, so the derivation reproduces the
        # exact EFFECTIVE membership (old ∩ strip == derived ∩ strip == derived, modulo the
        # declared additions).
        assert self._OLD_INIT_CREATES & br.DEV_ONLY_FILES == csc._RECREATED - self._ADDED_SINCE_MIGRATION

    def test_dangling_paths_is_byte_identical_across_migration(self):
        # THE load-bearing no-op property: `dangling_paths()` — the only consumer of these
        # three sets — is byte-identical whether computed from the OLD hand-lists or the
        # derived ones. (Behavior is unchanged even though `_RECREATED != _OLD_INIT_CREATES`
        # literally, because the sole difference is the phantom CHARTER, not in the strip set.)
        old_dangle = (
            br.DEV_ONLY_FILES
            - self._OLD_INIT_CREATES
            - self._OLD_HARNESS_SELF_SCRIPTS
            - self._OLD_DANGLE_EXCLUDED
            # The snapshots predate these paths, so the OLD computation can't classify them —
            # subtracting the declared additions is what keeps the two sides comparable (each
            # addition's real class is pinned by its own test, not assumed here).
            - self._ADDED_SINCE_MIGRATION
        )
        assert csc.dangling_paths() == old_dangle

    def test_derived_sets_partition_the_strip_manifest(self):
        # Completeness: the four file-level classes (recreated ∪ self-gate ∪ config ∪ dangle)
        # exactly re-cover `DEV_ONLY_FILES` with no overlap — the derivation is a partition of
        # the whole manifest, so nothing is silently dropped or double-counted.
        recreated = csc._RECREATED
        gates = csc.HARNESS_SELF_SCRIPTS
        config = csc._DANGLE_EXCLUDED
        dangle = csc.dangling_paths()
        assert recreated | gates | config | dangle == br.DEV_ONLY_FILES
        # pairwise-disjoint
        parts = [recreated, gates, config, dangle]
        for i, a in enumerate(parts):
            for b in parts[i + 1 :]:
                assert a & b == frozenset()


class TestClosurePassD:
    """Pass D — the referential-closure run-gate (`NEEDS ⊆ HAS`), 0034 Slice 3.

    Pure over `build_release`'s manifest classes + an injected shipped SET, so these run with
    no git/FS. They mechanize the release/init-contract INVARIANT (docs/claugentic-INVARIANTS.md)
    that was prose-only: every stripped adopter-relevant path is recreatable via its class's HAS
    source. Non-vacuous by construction — the "gap injected → flagged" tests prove the check
    actually catches a missing HAS, not just that the live manifest happens to pass.

    CWD-COUPLING FIXED (0040-banked, absorbed by plan 0041 Slice 4). The four cases below feed
    a REAL shipped set through `br._tracked_files()`, which shells `git ls-files` — scoped to
    the process CWD, so run from `tests/` it returned only that subtree and the closure read
    as broken (two cases red, two passing for the wrong reason). `at_repo_root` anchors them,
    so this class now holds from any working directory.
    """

    @pytest.fixture
    def at_repo_root(self, monkeypatch):
        """`br._tracked_files()` shells `git ls-files`, which is scoped to the CWD — run it
        from the git-authoritative repo root so these cases hold from any directory."""
        monkeypatch.chdir(br._repo_root())

    def test_live_manifest_is_closed(self, at_repo_root):
        # The load-bearing pin: over the REAL shipped set, NEEDS ⊆ HAS holds — no gaps.
        ship = frozenset(br.classify(br._tracked_files())[0])
        assert csc.closure_gaps(ship) == []

    def test_init_seed_maps_to_underscore_seed_after_managed_prefix(self):
        # The seed-naming convention: `_` is inserted AFTER the `claugentic-` prefix, NOT before
        # the whole basename (the bug the live run caught during build). DECISIONS/ROADMAP seeds.
        assert csc._init_seed_of("docs/claugentic-DECISIONS.md") == "docs/claugentic-_DECISIONS.md"
        assert csc._init_seed_of("docs/claugentic-ROADMAP.md") == "docs/claugentic-_ROADMAP.md"

    def test_missing_init_seed_is_a_gap(self, at_repo_root):
        # NON-VACUOUS: drop the DECISIONS/ROADMAP seeds from the shipped set → the init-seed HAS
        # source can't vouch for the stripped docs → a hard gap per stripped init-seed path.
        ship = frozenset(br.classify(br._tracked_files())[0]) - {
            "docs/claugentic-_DECISIONS.md",
            "docs/claugentic-_ROADMAP.md",
        }
        gaps = csc.closure_gaps(ship)
        assert any("claugentic-DECISIONS.md" in g and "seed" in g for g in gaps)
        assert any("claugentic-ROADMAP.md" in g and "seed" in g for g in gaps)

    def test_init_gen_output_must_be_registered(self):
        # NON-VACUOUS: `init-gen` HAS = a known generator output. ARCHITECTURE_TREE is registered;
        # an init-gen path NOT in INIT_GEN_OUTPUTS is a gap. Assert the live output is registered.
        assert "docs/claugentic-ARCHITECTURE_TREE.md" in csc.INIT_GEN_OUTPUTS
        for path in csc._paths_in_classes("init-gen"):
            assert path in csc.INIT_GEN_OUTPUTS

    def test_init_documents_the_caps_config(self):
        # WAS THE TRIPWIRE for the one forward registration in `INIT_GEN_OUTPUTS`; DISCHARGED
        # at 0041 Slice 7, which wrote the seeding step (`init` step 7b) and so flipped this
        # from strict-xfail to a permanent POSITIVE pin. Pass D vouches for
        # `.claude/claugentic-doc-budgets.json` via the `init-gen` class, and this is what
        # makes that vouching true rather than promised: delete the seeding step from init's
        # SKILL and this goes red, which is exactly when the class would have to become
        # `recreate-on-demand`. Never delete or invert it.
        # REGION-SCOPED, not a whole-file substring: the config path now appears in several
        # places in that skill (the solo exclude list, the escape-valve prose, the report
        # group), so a bare `in text` would stay green with the SEEDING STEP deleted. Anchor on
        # the step-7b heading, asserted UNIQUE so it can never be satisfied by an ordinal.
        init_skill = (Path(__file__).resolve().parent.parent / "skills" / "init" / "SKILL.md")
        text = init_skill.read_text(encoding="utf-8")
        heading = "**(b) Seed the doc-budget caps config"
        assert text.count(heading) == 1, "init's step-7b seeding heading is missing or doubled"
        assert ".claude/claugentic-doc-budgets.json" in text.split(heading, 1)[1], (
            "the step-7b SEEDING step is what generates the adopter's caps — a mention of the "
            "path elsewhere in the skill is not a writer, and Pass D vouches for a writer."
        )

    def test_init_delivers_the_budget_gate_script(self):
        # WAS THE TRIPWIRE for the OTHER forward promise 0041 S6 wrote — DELIVERY, a different
        # capability from the sibling above (CONFIG SEEDING), which is why one tripwire could
        # never cover both. DISCHARGED at Slice 7 and kept as a permanent POSITIVE pin.
        # THE PREDICATE MEASURES DELIVERY, NOT MENTION (S6 code-review F7): it keys on the
        # DELIVERED destination path — born-prefixed per the recorded decision
        # (release-contract → ship-class != delivery) — so prose that merely discusses the gate
        # cannot satisfy it; init's step-3 managed-set row is what does. Payload membership is
        # NOT delivery: before S7, a scratch adopter repo running the shipped command got exit
        # 2 (no such file), and the plugin's own copy anchors to its own checkout — a verdict
        # about the plugin clone, never the reader's repo.
        # REGION-SCOPED (Stage-7 R3, measured): a whole-file substring went VACUOUS the moment
        # S7's own prose started naming the delivered path — 8 occurrences, so deleting the
        # managed-set ROW left the whole suite green. Delivery lives in exactly one place: a
        # row in the step-3 table. Anchored by UNIQUENESS of the table's own delimiters, never
        # by line number or ordinal.
        # NOTE: this test only READS init's SKILL. It must never edit it.
        init_skill = (Path(__file__).resolve().parent.parent / "skills" / "init" / "SKILL.md")
        text = init_skill.read_text(encoding="utf-8")
        assert text.count("The managed set is exactly:") == 1
        table = text.split("The managed set is exactly:", 1)[1].split("**Per file", 1)[0]
        assert re.search(r"^\|\s*`scripts/claugentic-check_doc_budgets\.py`\s*\|", table, re.M), (
            "the step-3 managed-set row is what DELIVERS the gate into an adopter repo — a "
            "mention of the path anywhere else in the skill is not delivery."
        )

    def test_recreate_on_demand_is_accepted_by_the_class_not_init(self, at_repo_root):
        # The plan-gate's taxonomy fix: recreate-on-demand members (INVARIANTS/PRODUCT/
        # PRODUCT_SPEC) are BY DESIGN not init-produced — the closure accepts them via the class
        # (they are NOT in INIT_GEN_OUTPUTS and have no `_X.md` seed, yet close cleanly).
        rod = csc._paths_in_classes("recreate-on-demand")
        assert "docs/claugentic-INVARIANTS.md" in rod
        assert not (rod & csc.INIT_GEN_OUTPUTS)  # never init-gen
        ship = frozenset(br.classify(br._tracked_files())[0])
        # No seed ships for them, yet the live closure holds — accepted VIA the class.
        for path in rod:
            assert csc._init_seed_of(path) not in ship
        assert csc.closure_gaps(ship) == []

    def test_config_and_dangle_are_not_needs(self):
        # config (repo machinery) + dangle (RELEASE_CHECKLIST, stripped-and-never-recreated) are
        # NOT adopter-relevant NEEDS — the closure never demands a HAS source for them, so a
        # shipped set with no seed/generator for them still closes (proven by the live-closed pin).
        assert "docs/RELEASE_CHECKLIST.md" in {
            p for p in br.DEV_ONLY_FILES if br.recreate_class(p) == "dangle"
        }
        assert "CLAUDE.md" in csc._DANGLE_EXCLUDED  # config

    def test_closure_drives_evaluate_exit_1_on_a_gap(self, at_repo_root, monkeypatch, tmp_path):
        # End-to-end through evaluate(): a shipped set missing the DECISIONS seed makes Pass D a
        # HARD problem (drives main() to exit 1), even with all text passes clean.
        ship = sorted(
            (frozenset(br.classify(br._tracked_files())[0]) - {"docs/claugentic-_DECISIONS.md"})
        )
        monkeypatch.setattr(csc, "_shipped_files", lambda root: ship)
        monkeypatch.setattr(csc, "_read_shipped_texts", lambda root, s: {p: "" for p in ship})
        monkeypatch.setattr(csc, "_fs_agent_basenames", lambda root: set())
        monkeypatch.setattr(csc, "_fs_skill_basenames", lambda root: set())
        problems, _warnings, summary = csc.evaluate(tmp_path)
        assert summary == ""
        assert any("claugentic-DECISIONS.md" in p and "seed" in p for p in problems)


class TestGateCaveatPassAb:
    def test_uncaveated_gate_mention_warns(self):
        texts = {"docs/some-shipped.md": "Run `python scripts/check_versions_synced.py` at Verify."}
        warnings = csc.scan_gate_caveats(texts, csc.HARNESS_SELF_SCRIPTS)
        assert len(warnings) == 1
        assert "check_versions_synced.py" in warnings[0]

    def test_caveated_gate_mention_is_clean(self):
        texts = {
            "docs/some-shipped.md": (
                "Run `python scripts/check_versions_synced.py` (harness-self — skip in an "
                "adopter repo; the script isn't shipped)."
            ),
        }
        assert csc.scan_gate_caveats(texts, csc.HARNESS_SELF_SCRIPTS) == []

    def test_caveat_within_window_clears_warn(self):
        # The caveat sits on a nearby line (within CAVEAT_WINDOW), not the mention's own line.
        texts = {
            "docs/some-shipped.md": (
                "Version-sync (harness-self — N-A in an adopter):\n"
                "\n"
                "    python scripts/check_versions_synced.py\n"
            ),
        }
        assert csc.scan_gate_caveats(texts, csc.HARNESS_SELF_SCRIPTS) == []

    def test_warnings_never_become_problems(self):
        # A.b is WARN-only: an uncaveated mention must not appear in scan_dangling / namespace.
        # The example is a script still IN the self-gate class — a shipped script's basename
        # is not scanned at all, which would make this pass vacuously (0041 S6).
        texts = {"docs/x.md": "python scripts/check_versions_synced.py"}
        assert csc.scan_gate_caveats(texts, csc.HARNESS_SELF_SCRIPTS) != []
        assert csc.scan_dangling(texts, csc.dangling_paths()) == []
        assert csc.scan_namespace(texts, VALID) == []


class TestValidRoster:
    def test_valid_set_is_union_of_sources_plus_update(self):
        roster = csc.valid_roster(
            agent_basenames={"lens-reviewer", "implementer"},
            skill_basenames={"audit", "doctor"},
        )
        assert roster == {"lens-reviewer", "implementer", "audit", "doctor", "update"}

    def test_update_is_always_present_even_with_empty_fs(self):
        # The prose-only `update` token survives an empty FS listing (no skills/update/ dir).
        assert csc.valid_roster(agent_basenames=set(), skill_basenames=set()) == {"update"}


class TestMainExitCodes:
    """`main()` end-to-end with the git/FS boundary stubbed — exit 0 clean, 1 dirty,
    and (critically) fail-LOUD exit 1 when the boundary raises (never a false green)."""

    def _stub_evaluate(self, monkeypatch, *, problems, warnings):
        monkeypatch.setattr(csc, "_force_utf8_output", lambda: None)
        monkeypatch.setattr(csc, "_repo_root", lambda: csc.Path("."))
        monkeypatch.setattr(csc, "evaluate", lambda root: (problems, warnings, "OK summary"))
        monkeypatch.chdir(csc.Path("."))

    def test_clean_tree_exits_0(self, monkeypatch, capsys):
        self._stub_evaluate(monkeypatch, problems=[], warnings=[])
        assert csc.main([]) == 0
        assert "OK summary" in capsys.readouterr().out

    def test_clean_tree_with_warn_still_exits_0(self, monkeypatch, capsys):
        # STREAM-CONTRACT UPDATE (plan 0041 Slice 5, the sibling rule): the advisory `WARN:`
        # line rides STDERR — the verdict (problems / the OK summary) keeps stdout. The gate
        # family shares one contract, because the pre-commit wrapper discards a passing gate's
        # stdout; this gate is not chained today, and the contract is what keeps it chainable.
        self._stub_evaluate(monkeypatch, problems=[], warnings=["w/x.md:1: heuristic warn"])
        assert csc.main([]) == 0
        captured = capsys.readouterr()
        assert "WARN: w/x.md:1: heuristic warn" in captured.err
        assert "WARN:" not in captured.out
        assert "OK summary" in captured.out

    def test_hard_flagged_tree_exits_1(self, monkeypatch, capsys):
        self._stub_evaluate(monkeypatch, problems=["x.md: stranded token"], warnings=[])
        assert csc.main([]) == 1
        assert "stranded token" in capsys.readouterr().out

    def test_git_boundary_error_fails_loud_exit_1(self, monkeypatch, capsys):
        # The fail-LOUD contract: a git/FS boundary failure is exit 1 with a message, NEVER a
        # silent exit-0 false green.
        monkeypatch.setattr(csc, "_force_utf8_output", lambda: None)
        monkeypatch.setattr(csc, "_repo_root", lambda: csc.Path("."))

        def boom(root):
            raise RuntimeError("git ls-files exploded")

        monkeypatch.setattr(csc, "evaluate", boom)
        monkeypatch.chdir(csc.Path("."))
        assert csc.main([]) == 1
        assert "ERROR" in capsys.readouterr().err


class TestReadShippedTextsBinarySkip:
    """`_read_shipped_texts` — binary shipped ASSETS are skipped; text corruption still fails LOUD.

    The README ships binary PNG diagrams (`docs/diagrams/*.png`). Reading a PNG as UTF-8 raises
    `UnicodeDecodeError` on its `0x89` magic byte, so a known-binary-extension file must be SKIPPED
    from the text map (it has no text for any pass to scan). Crucially the skip is by KNOWN-BINARY
    EXTENSION ONLY: a non-binary-extension file that fails to UTF-8-decode is genuine corruption and
    STILL fails loud — that fail-loud-on-corruption contract must not be masked."""

    # A minimal real PNG header — the exact bytes that broke the live scan (magic byte 0x89).
    _PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"

    def test_binary_png_is_skipped_and_does_not_raise(self, tmp_path):
        # A shipped `.png` with non-UTF-8 bytes: the scan completes and the file is SKIPPED from
        # the text map (NOT read as text, so NO UnicodeDecodeError). This is the bug-capture — with
        # the binary-skip removed this call raises UnicodeDecodeError on the 0x89 magic byte.
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "diagram.png").write_bytes(self._PNG_BYTES)
        (tmp_path / "docs" / "notes.md").write_text("plain text\n", encoding="utf-8")
        ship = ["docs/diagram.png", "docs/notes.md"]
        texts = csc._read_shipped_texts(tmp_path, ship)
        assert "docs/diagram.png" not in texts  # binary asset skipped — no text to scan
        assert texts == {"docs/notes.md": "plain text\n"}  # text file still read identically

    def test_all_denylisted_extensions_are_skipped(self, tmp_path):
        # Every extension in the denylist is skipped when its bytes are non-UTF-8 — the scan never
        # raises on a legitimate binary asset regardless of which kind ships.
        for i, ext in enumerate(sorted(csc.BINARY_EXTENSIONS)):
            (tmp_path / f"asset{i}{ext}").write_bytes(b"\xff\xfe\x00\x89 not utf-8")
        ship = [f"asset{i}{ext}" for i, ext in enumerate(sorted(csc.BINARY_EXTENSIONS))]
        assert csc._read_shipped_texts(tmp_path, ship) == {}  # all skipped, no raise

    def test_corrupt_text_file_still_fails_loud(self, tmp_path):
        # THE preserved contract: a non-binary-extension file (`.md`) whose bytes are NOT valid
        # UTF-8 is GENUINE corruption and STILL fails loud — the binary-skip must not blanket-catch
        # UnicodeDecodeError and mask real text corruption.
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "corrupt.md").write_bytes(b"valid start \xff\xfe invalid utf-8")
        with pytest.raises(UnicodeDecodeError):
            csc._read_shipped_texts(tmp_path, ["docs/corrupt.md"])

    def test_binary_asset_does_not_dangle_via_evaluate(self, monkeypatch, tmp_path):
        # End-to-end: a shipped `.png` alongside a doc that REFERENCES it (README-style
        # `![...](docs/diagram.png)`) drives evaluate() to a CLEAN result — the PNG is skipped from
        # the text scan AND its reference is not a Pass A.a dangle (it points at a shipped file).
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "diagram.png").write_bytes(self._PNG_BYTES)
        (tmp_path / "README.md").write_text(
            "See the flow: ![flow](docs/diagram.png)\n", encoding="utf-8"
        )
        ship = ["docs/diagram.png", "README.md"]
        monkeypatch.setattr(csc, "_shipped_files", lambda root: ship)
        monkeypatch.setattr(csc, "_fs_agent_basenames", lambda root: set())
        monkeypatch.setattr(csc, "_fs_skill_basenames", lambda root: set())
        # Pass D (closure over the REAL manifest) is orthogonal to this test — stub it out so the
        # assertion pins ONLY the text passes (A.a/A.b/B/C) over this minimal ship set. The value
        # under test is: `_read_shipped_texts` (NOT stubbed) skips the PNG without raising, and the
        # README's `![...](docs/diagram.png)` reference is not a Pass A.a dangle.
        monkeypatch.setattr(csc, "closure_gaps", lambda ship_set: [])
        problems, _warnings, _summary = csc.evaluate(tmp_path)
        assert problems == []  # no UnicodeDecodeError, no dangling-ref false-positive


class TestParseRoot:
    """`_parse_root` — the boundary parser for the `--root <path>` argument (0034 Slice 5).
    Absent flag → `None` (the byte-identical default); a garbled value fails LOUD (never a
    silent scan of the wrong tree)."""

    def test_absent_flag_is_none(self):
        assert csc._parse_root([]) is None

    def test_valid_dir_is_returned(self, tmp_path):
        assert csc._parse_root(["--root", str(tmp_path)]) == Path(str(tmp_path))

    def test_missing_value_fails_loud(self):
        with pytest.raises(ValueError, match="requires a <path>"):
            csc._parse_root(["--root"])

    def test_non_directory_fails_loud(self, tmp_path):
        missing = tmp_path / "not-there"
        with pytest.raises(ValueError, match="not a directory"):
            csc._parse_root(["--root", str(missing)])


class TestRootScansGivenTree:
    """`--root <tree>` scans the shipped content of a GIVEN (already-stripped) tree — the P0-2
    built-tree validation (0034 Slice 5). NON-VACUOUS by construction: the SAME scan must PASS on
    a clean built tree AND FAIL on one with a stranded namespace token injected, so the test can't
    go vacuously green if `--root` silently scanned the wrong tree (or scanned nothing).

    The fixture builds a minimal HERMETIC git tree that mimics a stripped release: the two
    `init-seed` seeds ship (so Pass D's closure holds), plus an agent + a skill (so Pass B's roster
    is FS-derived) and a couple of shipped markdown/js files. Ambient git config is pinned off so
    pass/fail depends only on the code under test."""

    @staticmethod
    def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    @pytest.fixture
    def built_tree(self, tmp_path, monkeypatch):
        """A committed git tree that looks like a stripped release: only shipped files are tracked,
        the init-seed seeds are present (closure holds), and the FS-derived roster is well-formed."""
        empty_cfg = tmp_path / "empty-gitconfig"
        empty_cfg.write_text("", encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty_cfg))
        monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty_cfg))

        repo = tmp_path / "built"
        repo.mkdir()
        self._git(repo, "init", "-q").check_returncode()
        self._git(repo, "config", "user.email", "t@t.t").check_returncode()
        self._git(repo, "config", "user.name", "t").check_returncode()

        # The two `init-seed` seeds must ship so Pass D (NEEDS ⊆ HAS) closes over the real manifest.
        (repo / "docs").mkdir()
        (repo / "docs" / "claugentic-_DECISIONS.md").write_text("# seed\n", encoding="utf-8")
        (repo / "docs" / "claugentic-_ROADMAP.md").write_text("# seed\n", encoding="utf-8")
        # A shipped doc that uses a VALID namespace token (an agent basename present below) — clean.
        (repo / "docs" / "claugentic-WORKFLOW.md").write_text(
            "Spawn `claugentic-dev-harness:honesty-reviewer` at Verify.\n", encoding="utf-8"
        )
        # An ASCII-only shipped engine script — Pass C clean.
        (repo / "engine").mkdir()
        (repo / "engine" / "audit.js").write_text("const x = 1; // plain ASCII\n", encoding="utf-8")
        # FS-derived roster sources: one agent, one skill dir.
        (repo / ".claude" / "agents").mkdir(parents=True)
        (repo / ".claude" / "agents" / "honesty-reviewer.md").write_text("# agent\n", encoding="utf-8")
        (repo / "skills" / "audit").mkdir(parents=True)
        (repo / "skills" / "audit" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

        self._git(repo, "add", "-A").check_returncode()
        self._git(repo, "commit", "-qm", "built tree").check_returncode()
        return repo

    def _scan(self, root: Path) -> subprocess.CompletedProcess:
        scanner = Path(csc.__file__)
        return subprocess.run(
            [sys.executable, str(scanner), "--root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_clean_built_tree_passes(self, built_tree):
        # The clean built tree scans OK (exit 0), and the summary proves the scan targeted THIS
        # tree — only its shipped files, not the dev checkout's.
        result = self._scan(built_tree)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK: scanned" in result.stdout

    def test_broken_built_tree_fails(self, built_tree):
        # NON-VACUOUS: inject a stranded namespace token into a shipped doc of the SAME tree; the
        # SAME scan now FAILS (exit 1) — proving `--root` actually read the given tree's files.
        (built_tree / "docs" / "claugentic-WORKFLOW.md").write_text(
            "Spawn `claugentic-dev-harness:ghost-role` (renamed away).\n", encoding="utf-8"
        )
        self._git(built_tree, "add", "-A").check_returncode()
        self._git(built_tree, "commit", "-qm", "strand a token").check_returncode()
        result = self._scan(built_tree)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "ghost-role" in result.stdout
