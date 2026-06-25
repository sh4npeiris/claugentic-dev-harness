"""Hermetic tests for the shipped-content scanner (`scripts/check_shipped_content.py`).

Each pure core takes an injected `{path: text}` map, so these run with NO real git and
NO real filesystem — they pin the EXACT literals the gate must catch and the exact
false-positive classes it must NOT catch (the two load-bearing regression pins:
a `claugentic-dev-harness:audit` slash-command token and the `<!-- product-critic:... -->`
memory-fence token are both CLEAN). The git boundary is monkeypatched for the `main()`
exit-code tests, including the fail-loud-on-git-error case.
"""

from __future__ import annotations

import check_shipped_content as csc

# A representative VALID set (agents ∪ skills ∪ {update}) for the namespace pass tests.
VALID = csc.valid_roster(
    agent_basenames={"lens-reviewer", "implementer", "synthesizer-gate"},
    skill_basenames={"audit", "build", "init", "product", "doctor"},
)


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
        # Derivation contract: the dangle set is RELEASE_CHECKLIST only — init-created files,
        # the harness-self gate scripts (A.b's concern), and repo-config are all subtracted.
        dangling = csc.dangling_paths()
        assert "docs/RELEASE_CHECKLIST.md" in dangling
        assert "scripts/check_versions_synced.py" not in dangling  # A.b, not A.a
        assert "docs/claugentic-DECISIONS.md" not in dangling      # init-created
        assert "CLAUDE.md" not in dangling                          # repo-config


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
