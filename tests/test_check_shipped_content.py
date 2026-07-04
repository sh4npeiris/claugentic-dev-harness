"""Hermetic tests for the shipped-content scanner (`scripts/check_shipped_content.py`).

Each pure core takes an injected `{path: text}` map, so these run with NO real git and
NO real filesystem — they pin the EXACT literals the gate must catch and the exact
false-positive classes it must NOT catch (the two load-bearing regression pins:
a `claugentic-dev-harness:audit` slash-command token and the `<!-- product-critic:... -->`
memory-fence token are both CLEAN). The git boundary is monkeypatched for the `main()`
exit-code tests, including the fail-loud-on-git-error case.
"""

from __future__ import annotations

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
        monkeypatch.setattr(csc, "_shipped_files", lambda: ship)
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

    def test_harness_self_scripts_derived_equals_old(self):
        # LITERALLY equal — every `self-gate` path is exactly the old hand-list. (This set is
        # also A.b's scan target, so literal equality is load-bearing for that pass too.)
        assert csc.HARNESS_SELF_SCRIPTS == self._OLD_HARNESS_SELF_SCRIPTS

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
        assert csc._RECREATED - self._OLD_INIT_CREATES == frozenset()
        # The phantom was never a member of the strip set, so the derivation reproduces the
        # exact EFFECTIVE membership (old ∩ strip == derived ∩ strip == derived).
        assert self._OLD_INIT_CREATES & br.DEV_ONLY_FILES == csc._RECREATED

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
        texts = {"docs/x.md": "python scripts/check_doc_budgets.py"}
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
        self._stub_evaluate(monkeypatch, problems=[], warnings=["w/x.md:1: heuristic warn"])
        assert csc.main([]) == 0
        out = capsys.readouterr().out
        assert "WARN: w/x.md:1: heuristic warn" in out
        assert "OK summary" in out

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
