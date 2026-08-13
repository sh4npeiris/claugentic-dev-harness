"""Hermetic tests for the SessionStart advisor (`scripts/claugentic-session-advisor.py`).

The advisor DERIVES one "where am I / what's next" line from the two backlog
fences in `docs/claugentic-ROADMAP.md`, the in-flight `.claude/plans/*.md`, and an
ADOPTER-ONLY CLAUDE.md `harness:managed` fence (absent in this source repo). These
tests lock the HARD invariants the slice exists to guarantee:

  * SILENT path — nothing actionable emits NEITHER `systemMessage` NOR
    `additionalContext` (no-nag, no token cost).
  * SIZE CAP — each emitted line is <= `MAX_LINE_CHARS` (this slice fixes context
    bloat, so the ceiling is asserted, not merely intended).
  * FAIL-SAFE — ANY bad input (malformed fence, missing plans dir, non-repo,
    absent managed fence) -> exit 0 with no crash.
  * The RETURN-2 (plan age) / RETURN-3 (PARTIAL re-run) / RETURN-6 (advisory
    prefix) audit-delta branches.
  * AUDIENCE-SPLIT (0024 problem #5) — `additionalContext` (agent-facing, with the
    RETURN-6 disclaimer) is emitted ONLY on the in-flight-plan RESUME branch; the
    three promotional nudges AND the two currency clauses are `systemMessage`-ONLY.
    `TestCurrencyClausesNeverReachTheAgent` is the load-bearing pin: widening a clause
    into `additionalContext` must fail there.
  * CURRENCY NUDGES — stamped-docs-behind-plugin skew (fires only when BOTH versions
    parse and managed < installed; every other case silent) and the landed/cold plan
    housekeeping count (`COLD_DAYS`, git-absent is never cold).
  * TOTALITY — `_version_lt` must never raise: its left-hand input is hand-editable
    fence text, and an escape blanks the WHOLE banner (resume line included), not just
    the nudge. Pinned by the `1.²` / 5000-digit rows AND an end-to-end `main()` case.
  * TRUNCATION ORDER — the clause budget is reserved, so an overflow eats the
    recommendation's tail and never a nudge (`TestClauseComposition`).
  * OFF-SWITCH — `CLAUDE_HARNESS_ADVISOR=off` mutes the advisor to `{}` even with
    actionable state present (fail-safe to silent; read at the `main()` boundary).

Hermetic by construction: `tmp_path` materialises real roadmap/plan/CLAUDE.md/
plugin.json files; the advisor's PATH CONSTANTS — including `PLUGIN_MANIFEST_PATH` —
are monkeypatched to point at them, so no real repo artifact (and no live plugin
version) leaks into a comparison. `_plan_git_meta` (the one `git log` seam) is
monkeypatched so the age AND coldness branches are deterministic and offline, and
`_is_cold` is pinned against a FIXED `now` so no test reads the wall clock. The ONE
exception is named and deliberate: `test_anchor_survives_a_foreign_cwd_...` spawns the
real module in a subprocess and reads the REAL manifest — the working directory is the
thing under test and cannot be faked in-process, which is exactly why the earlier
in-process form was vacuous (it passed on a CWD-anchored mutant).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

import advisor as adv

# The advisor's REAL on-disk location — the anchor pin spawns it from a foreign cwd.
ADVISOR_PATH = Path(adv.__file__).resolve()

# The version a decoy `.claude-plugin/plugin.json` in that foreign cwd advertises. It
# must never appear in the advisor's output: seeing it means the anchor followed the CWD.
DECOY_VERSION = "9.9.9"

# Bytes that are NOT valid UTF-8 (a lone \xff, then a truncated 2-byte sequence).
# `read_text(encoding="utf-8")` raises UnicodeDecodeError on these — a ValueError, NOT an
# OSError, which is exactly why every reader's except had to widen.
NOT_UTF8 = b"\xff\xfe\x00 not valid utf-8 \xc3\x28"

# ─────────────────────────────────────────────────────────────────────────────
# Fixture text — the EXACT fence/sentinel forms the real ROADMAP uses.
# ─────────────────────────────────────────────────────────────────────────────
AUDIT_EMPTY = (
    "<!-- harness-audit:backlog:start -->\n"
    "No open items — the harness is feature-complete for v1.\n"
    "<!-- harness-audit:backlog:end -->\n"
)
PRODUCT_NO_SPEC = (
    "<!-- harness-product:backlog:start -->\n"
    "No product spec yet for the harness itself — run /claugentic-dev-harness:product spec mode.\n"
    "<!-- harness-product:backlog:end -->\n"
)
AUDIT_OPEN = (
    "<!-- harness-audit:backlog:start -->\n"
    "## Tier 1 — must-fix\n- [ ] Fix the auth boundary\n- [ ] Validate the upload size\n"
    "<!-- harness-audit:backlog:end -->\n"
)
AUDIT_PARTIAL = (
    "<!-- harness-audit:backlog:start -->\n"
    "Status: PARTIAL — resumable.\nNo open items yet.\n"
    "<!-- harness-audit:backlog:end -->\n"
)
PRODUCT_HAS_SPEC = (
    "<!-- harness-product:backlog:start -->\n"
    "## Tier 2 — gaps vs spec\n- [ ] Onboarding criterion C3 unbuilt\n"
    "<!-- harness-product:backlog:end -->\n"
)

PLAN_IN_FLIGHT = (
    "# 0022 — SessionStart advisor\n\n"
    "- **Status:** Approved\n"
    "- **Resumable from:** batch approval → implement `D1 → D2`\n\n"
    "## Decomposition (slices)\n\n"
    "- [ ] **D1 — Advisor script.**\n"
    "- [ ] **D2 — Bundle as a hook.**\n"
)
PLAN_DONE = (
    "# 0019 — done plan\n\n"
    "- **Status:** Done\n"
    "- **Resumable from:** nothing — landed\n\n"
    "## Decomposition (slices)\n\n"
    "- [x] **Only slice — landed.**\n"
)
PLAN_ALL_CHECKED_NOT_DONE = (
    "# 0020 — at the before-land checkpoint\n\n"
    "- **Status:** Implemented + Verify-panel SOUND — at the before-land checkpoint\n"
    "- **Resumable from:** awaiting user go to commit the ruler\n\n"
    "## Decomposition (slices)\n\n"
    "- [x] **A1.**\n- [x] **A2.**\n"
)


# ─────────────────────────────────────────────────────────────────────────────
# Hermetic fixture: point the advisor's PATH CONSTANTS at tmp_path artifacts.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Materialise a fake repo and repoint the advisor's path constants at it.

    Returns a small builder with `roadmap(text)`, `plan(name, text)`, `claude_md(text)`,
    `plugin_manifest(text)` and `ensure_empty_plans_dir()` so each test composes exactly
    the inputs it needs. By default NOTHING exists (the fresh-repo silent baseline) —
    including the plugin manifest, so the REAL `.claude-plugin/plugin.json` can never leak
    a live version into a test's skew comparison. `_plan_git_meta` is stubbed to "git
    unavailable" so age AND coldness are deterministic unless a test opts into them.
    """
    plans_dir = tmp_path / ".claude" / "plans"
    roadmap_path = tmp_path / "docs" / "claugentic-ROADMAP.md"
    claude_path = tmp_path / "CLAUDE.md"
    manifest_path = tmp_path / ".claude-plugin" / "plugin.json"
    monkeypatch.setattr(adv, "ROADMAP_PATH", roadmap_path)
    monkeypatch.setattr(adv, "PLANS_DIR", plans_dir)
    monkeypatch.setattr(adv, "CLAUDE_MD_PATH", claude_path)
    monkeypatch.setattr(adv, "PLUGIN_MANIFEST_PATH", manifest_path)
    # Default: git is "unavailable" so age is None and nothing is cold unless a test opts in.
    monkeypatch.setattr(adv, "_plan_git_meta", lambda _path: (None, None))

    class Builder:
        def __init__(self) -> None:
            # The raw paths, exposed so a test can write NON-UTF-8 BYTES — the decode
            # failure mode the text helpers below cannot express, and the one that used
            # to escape every reader's `except OSError` and blank the whole banner.
            self.roadmap_path = roadmap_path
            self.plans_dir = plans_dir
            self.claude_path = claude_path
            self.manifest_path = manifest_path

        def roadmap(self, text: str) -> None:
            roadmap_path.parent.mkdir(parents=True, exist_ok=True)
            roadmap_path.write_text(text, encoding="utf-8")

        def plan(self, name: str, text: str) -> None:
            plans_dir.mkdir(parents=True, exist_ok=True)
            (plans_dir / name).write_text(text, encoding="utf-8")

        def claude_md(self, text: str) -> None:
            claude_path.write_text(text, encoding="utf-8")

        def plugin_manifest(self, text: str) -> None:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(text, encoding="utf-8")

        def ensure_empty_plans_dir(self) -> None:
            plans_dir.mkdir(parents=True, exist_ok=True)

    return Builder()


def managed_claude_md(version: str) -> str:
    """An ADOPTER CLAUDE.md carrying the `harness:managed` fence stamped at `version`."""
    return (
        "# CLAUDE.md\n\n<!-- harness:managed:start -->\n"
        f"claugentic-dev-harness@{version} managed — do not edit\n"
        "<!-- harness:managed:end -->\n"
    )


def plugin_json(version: str) -> str:
    """The plugin's own manifest, trimmed to the one key the advisor reads."""
    return json.dumps({"name": "claugentic-dev-harness", "version": version})


# ─────────────────────────────────────────────────────────────────────────────
# SILENT path — the HARD no-nag invariant: NEITHER key emitted.
# ─────────────────────────────────────────────────────────────────────────────
class TestSilentPath:
    def test_fresh_repo_is_silent_no_keys(self, repo):
        # Nothing exists at all — the fresh-repo baseline.
        payload = adv.build_output(adv.derive_state())
        assert payload == {}
        assert "systemMessage" not in payload
        assert "additionalContext" not in payload

    def test_empty_audit_plus_no_plans_plus_no_product_fence_is_silent(self, repo):
        # An empty audit fence and NO product fence (product never run) and no plans:
        # the audit is empty, the product fence is absent (not present+empty), so silent.
        repo.roadmap(AUDIT_EMPTY)
        repo.ensure_empty_plans_dir()
        assert adv.build_output(adv.derive_state()) == {}

    def test_done_plan_alone_nudges_housekeeping_it_is_no_longer_silent(self, repo):
        # A plan that is unambiguously Done (all boxes checked + Status Done) is NOT
        # in-flight — so it is a LANDED plan whose delete-at-land close-out was skipped.
        # The currency nudges COUNT it, so this input is deliberately no longer silent;
        # the nudge is user-facing ONLY (no additionalContext).
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0019-done.md", PLAN_DONE)
        payload = adv.build_output(adv.derive_state())
        assert payload["systemMessage"] == (
            "1 landed/cold plan in .claude/plans — run /claugentic-dev-harness:doctor to sweep."
        )
        assert "additionalContext" not in payload

    def test_silent_path_emits_empty_json_object(self, repo, capsys):
        rc = adv.main([])
        assert rc == 0
        out = capsys.readouterr().out.strip()
        assert json.loads(out) == {}


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation priority order.
# ─────────────────────────────────────────────────────────────────────────────
class TestRecommendationPriority:
    def test_in_flight_plan_recommends_resume_with_resumable_line(self, repo):
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        payload = adv.build_output(adv.derive_state())
        assert "Resume work in progress" in payload["systemMessage"]
        assert "0022-advisor" in payload["systemMessage"]
        assert "1 plan in flight" in payload["systemMessage"]
        assert "D1" in payload["systemMessage"]  # the Resumable from line surfaced
        # AUDIENCE-SPLIT: the RESUME branch (priority 1) is the one agent-relevant
        # next-action -> BOTH keys, additionalContext carrying the RETURN-6 disclaimer.
        assert "additionalContext" in payload
        assert payload["additionalContext"].startswith(adv.ADVISORY_PREFIX)

    def test_in_flight_outranks_open_backlog(self, repo):
        # An open audit backlog AND an in-flight plan: the plan wins (priority 1).
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        assert "Resume work in progress" in adv.build_output(adv.derive_state())["systemMessage"]

    def test_all_checked_but_not_done_plan_is_in_flight(self, repo):
        # 0020-style: all boxes [x] but Status is not literally "Done" (before-land
        # checkpoint) — still in flight (the plan file lives in the dir).
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0020-distillation.md", PLAN_ALL_CHECKED_NOT_DONE)
        payload = adv.build_output(adv.derive_state())
        assert "Resume work in progress" in payload["systemMessage"]
        assert "0020-distillation" in payload["systemMessage"]

    def test_open_audit_backlog_recommends_build(self, repo):
        repo.roadmap(AUDIT_OPEN + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert adv.BUILD_CMD in payload["systemMessage"]
        assert "backlog" in payload["systemMessage"].lower()
        # AUDIENCE-SPLIT: a promotional nudge (priority 2) is systemMessage-ONLY —
        # no additionalContext, so the agent isn't nudged toward unrequested work.
        assert "additionalContext" not in payload

    def test_no_product_spec_recommends_product(self, repo):
        # Empty audit + a present product fence still carrying the no-spec sentinel.
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert adv.PRODUCT_CMD in payload["systemMessage"]
        assert "product spec" in payload["systemMessage"].lower()
        # AUDIENCE-SPLIT: a promotional nudge (priority 4) is systemMessage-ONLY.
        assert "additionalContext" not in payload

    def test_open_audit_outranks_no_product_spec(self, repo):
        repo.roadmap(AUDIT_OPEN + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        assert adv.BUILD_CMD in adv.build_output(adv.derive_state())["systemMessage"]

    def test_product_with_real_items_does_not_trigger_no_spec_line(self, repo):
        # A product fence with real gap items is NOT "no spec yet" — and with an
        # empty audit + no plans nothing actionable surfaces on the product axis here
        # (open-product-backlog routing is owned by /build, not this advisor line).
        repo.roadmap(AUDIT_EMPTY + PRODUCT_HAS_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        # Not the "no product spec yet" recommendation (a spec clearly exists).
        assert "No product spec yet" not in payload.get("systemMessage", "")


# ─────────────────────────────────────────────────────────────────────────────
# RETURN-3 — a PARTIAL fence surfaces "re-run to finish".
# ─────────────────────────────────────────────────────────────────────────────
class TestPartialReRun:
    def test_partial_audit_fence_recommends_rerun(self, repo):
        repo.roadmap(AUDIT_PARTIAL + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert "partial" in payload["systemMessage"].lower()
        assert "re-run" in payload["systemMessage"].lower()
        # AUDIENCE-SPLIT: a promotional nudge (priority 3) is systemMessage-ONLY.
        assert "additionalContext" not in payload

    def test_partial_outranks_no_product_spec(self, repo):
        repo.roadmap(AUDIT_PARTIAL + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        assert "partial" in adv.build_output(adv.derive_state())["systemMessage"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# RETURN-2 — plan age via git log (omitted silently when git unavailable).
# ─────────────────────────────────────────────────────────────────────────────
class TestPlanAge:
    def test_age_is_rendered_when_git_available(self, repo, monkeypatch):
        monkeypatch.setattr(adv, "_plan_git_meta", lambda _path: ("2 days ago", None))
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        assert "2 days ago" in msg

    def test_age_omitted_when_git_unavailable(self, repo, monkeypatch):
        monkeypatch.setattr(adv, "_plan_git_meta", lambda _path: (None, None))
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        assert "0022-advisor" in msg
        assert "ago" not in msg  # no age parenthetical

    def test_plan_git_meta_parses_age_and_epoch_from_one_call(self, monkeypatch, tmp_path):
        # ONE git call carries both facts, separated by the \x1f the format string asks for.
        captured = {}

        def fake_run(cmd, *_a, **_k):
            captured["cmd"] = cmd
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="2 days ago\x1f1700000000\n", stderr=""
            )

        monkeypatch.setattr(adv.subprocess, "run", fake_run)
        assert adv._plan_git_meta(tmp_path / "x.md") == ("2 days ago", 1700000000)
        assert "--format=%cr%x1f%ct" in captured["cmd"]  # both facts, one invocation

    def test_plan_git_meta_returns_none_on_git_failure(self, monkeypatch, tmp_path):
        # The real reader: a non-zero git return (untracked/non-repo) yields no facts.
        def fake_run(*_a, **_k):
            return subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="fatal")

        monkeypatch.setattr(adv.subprocess, "run", fake_run)
        assert adv._plan_git_meta(tmp_path / "x.md") == (None, None)

    def test_plan_git_meta_returns_none_when_git_missing(self, monkeypatch, tmp_path):
        def boom(*_a, **_k):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(adv.subprocess, "run", boom)
        assert adv._plan_git_meta(tmp_path / "x.md") == (None, None)

    def test_plan_git_meta_untracked_plan_yields_no_facts(self, monkeypatch, tmp_path):
        # git succeeds with nothing to say (returncode 0, empty stdout) — an untracked plan.
        def fake_run(*_a, **_k):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="\n", stderr="")

        monkeypatch.setattr(adv.subprocess, "run", fake_run)
        assert adv._plan_git_meta(tmp_path / "x.md") == (None, None)

    def test_plan_git_meta_malformed_epoch_keeps_the_age(self, monkeypatch, tmp_path):
        # A non-numeric epoch degrades that ONE fact; the age survives (degrade, don't crash).
        def fake_run(*_a, **_k):
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="2 days ago\x1fnot-an-epoch\n", stderr=""
            )

        monkeypatch.setattr(adv.subprocess, "run", fake_run)
        assert adv._plan_git_meta(tmp_path / "x.md") == ("2 days ago", None)


# ─────────────────────────────────────────────────────────────────────────────
# RETURN-6 — additionalContext carries the advisory prefix (on the RESUME branch,
# the only path that now emits it per the AUDIENCE-SPLIT).
# ─────────────────────────────────────────────────────────────────────────────
class TestAdvisoryPrefix:
    def test_additional_context_is_prefixed(self, repo):
        # The resume branch (in-flight plan) is the one path emitting additionalContext.
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        payload = adv.build_output(adv.derive_state())
        assert payload["additionalContext"].startswith(adv.ADVISORY_PREFIX)
        # The user-facing line carries NO disclaimer (it's a greeting, not an instruction).
        assert not payload["systemMessage"].startswith(adv.ADVISORY_PREFIX)


# ─────────────────────────────────────────────────────────────────────────────
# OFF-SWITCH — CLAUDE_HARNESS_ADVISOR=off mutes the advisor to {} (fail-safe to
# silent), read at the main() env boundary so build_output stays pure.
# ─────────────────────────────────────────────────────────────────────────────
class TestOffSwitch:
    def test_off_switch_mutes_even_with_actionable_state(self, repo, monkeypatch, capsys):
        # An in-flight plan IS actionable (would normally emit both keys) — but the
        # off-switch mutes it to {} regardless.
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        monkeypatch.setenv("CLAUDE_HARNESS_ADVISOR", "off")
        rc = adv.main([])
        assert rc == 0
        assert json.loads(capsys.readouterr().out.strip()) == {}

    def test_off_switch_is_case_and_whitespace_insensitive(self, repo, monkeypatch, capsys):
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        monkeypatch.setenv("CLAUDE_HARNESS_ADVISOR", "  OFF  ")
        rc = adv.main([])
        assert rc == 0
        assert json.loads(capsys.readouterr().out.strip()) == {}

    def test_unset_env_leaves_advisor_enabled(self, repo, monkeypatch, capsys):
        # No env var = on (no behaviour change for existing users).
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        monkeypatch.delenv("CLAUDE_HARNESS_ADVISOR", raising=False)
        rc = adv.main([])
        assert rc == 0
        assert "Resume work in progress" in json.loads(capsys.readouterr().out.strip())["systemMessage"]

    def test_other_env_value_leaves_advisor_enabled(self, repo, monkeypatch, capsys):
        # Any value other than "off" leaves it on (off-switch is opt-IN to silence).
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        monkeypatch.setenv("CLAUDE_HARNESS_ADVISOR", "on")
        rc = adv.main([])
        assert rc == 0
        assert "Resume work in progress" in json.loads(capsys.readouterr().out.strip())["systemMessage"]

    def test_build_output_disabled_flag_returns_empty(self, repo):
        # The pure renderer mutes directly on enabled=False — no env read in build_output.
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        assert adv.build_output(adv.derive_state(), enabled=False) == {}


# ─────────────────────────────────────────────────────────────────────────────
# SIZE CAP — the HARD ceiling (the slice exists to fix bloat).
# ─────────────────────────────────────────────────────────────────────────────
class TestSizeCap:
    def test_every_emitted_line_within_cap(self, repo):
        # Many in-flight plans with long resumable lines would otherwise blow the budget.
        repo.roadmap(AUDIT_EMPTY)
        for i in range(12):
            repo.plan(
                f"00{i:02d}-very-long-plan-name-that-eats-budget.md",
                "- **Status:** Approved\n"
                "- **Resumable from:** " + ("a very long resumable description " * 20) + "\n"
                "## Decomposition (slices)\n- [ ] **only.**\n",
            )
        payload = adv.build_output(adv.derive_state())
        assert len(payload["systemMessage"]) <= adv.MAX_LINE_CHARS
        assert len(payload["additionalContext"]) <= adv.MAX_LINE_CHARS

    def test_cap_is_one_line_no_newlines(self, repo):
        repo.roadmap(AUDIT_EMPTY)
        repo.plan(
            "0001-plan.md",
            "- **Status:** Approved\n- **Resumable from:** line one\nline two\nline three\n"
            "## Decomposition (slices)\n- [ ] **only.**\n",
        )
        payload = adv.build_output(adv.derive_state())
        assert "\n" not in payload["systemMessage"]
        assert "\n" not in payload["additionalContext"]

    def test_cap_helper_truncates_with_ellipsis(self):
        long = "x" * (adv.MAX_LINE_CHARS + 50)
        capped = adv._cap(long)
        assert len(capped) <= adv.MAX_LINE_CHARS
        assert capped.endswith("…")


# ─────────────────────────────────────────────────────────────────────────────
# FAIL-SAFE — any bad input -> exit 0, no crash, no traceback.
# ─────────────────────────────────────────────────────────────────────────────
class TestFailSafe:
    def test_malformed_fence_no_crash_silent(self, repo, capsys):
        # An audit start marker with NO end marker — _fence_body returns None (absent).
        repo.roadmap("<!-- harness-audit:backlog:start -->\norphaned, no end\n")
        repo.ensure_empty_plans_dir()
        rc = adv.main([])
        assert rc == 0
        # The orphaned fence reads as ABSENT (not present), so nothing actionable -> {}.
        assert json.loads(capsys.readouterr().out.strip()) == {}

    def test_missing_plans_dir_no_crash(self, repo, capsys):
        # No plans dir at all (never created) — _read_plans returns ().
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        rc = adv.main([])
        assert rc == 0
        # Product fence present+empty -> the product recommendation, still valid JSON.
        json.loads(capsys.readouterr().out.strip())

    def test_absent_managed_fence_is_silent_not_error(self, repo):
        # This SOURCE repo's CLAUDE.md has no harness:managed fence — the version
        # input must be None (silently skipped), never a crash.
        repo.claude_md("# CLAUDE.md\n\nNo managed fence here.\n")
        assert adv._read_managed_version() is None
        # And the whole derive still works with that absent input.
        repo.roadmap(AUDIT_EMPTY)
        adv.derive_state()  # must not raise

    def test_managed_fence_version_read_on_adopter(self, repo):
        repo.claude_md(
            "# CLAUDE.md\n\n<!-- harness:managed:start -->\n"
            "claugentic-dev-harness@0.1.39 managed — do not edit\n"
            "<!-- harness:managed:end -->\n"
        )
        assert adv._read_managed_version() == "0.1.39"

    def test_unreadable_roadmap_no_crash(self, repo, monkeypatch, capsys):
        # An unreadable roadmap (permission denied) must degrade to absent fences,
        # never crash. Patch read_text at the class level, discriminating on the name.
        repo.roadmap(AUDIT_OPEN)
        from pathlib import Path

        real_read_text = Path.read_text

        def boom(self, *a, **k):
            if self.name == "claugentic-ROADMAP.md":
                raise PermissionError("denied")
            return real_read_text(self, *a, **k)

        monkeypatch.setattr(Path, "read_text", boom)
        rc = adv.main([])  # must NOT raise
        assert rc == 0
        # The roadmap read failed -> absent fences -> nothing actionable -> {}.
        assert json.loads(capsys.readouterr().out.strip()) == {}


# ─────────────────────────────────────────────────────────────────────────────
# NON-UTF-8 INPUTS — the failure mode that used to escape every `except OSError`.
# `UnicodeDecodeError` is a ValueError, NOT an OSError, so before the widening a
# single mojibake'd file blanked the WHOLE banner (resume line included). Each
# reader must degrade to "this ONE input is absent" and nothing else.
# ─────────────────────────────────────────────────────────────────────────────
class TestUndecodableInputsDegradeOnlyThemselves:
    def test_non_utf8_claude_md_loses_only_the_stamp(self, repo, capsys):
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.claude_path.write_bytes(NOT_UTF8)
        assert adv._read_managed_version() is None
        assert adv.main([]) == 0
        payload = json.loads(capsys.readouterr().out.strip())
        assert "Resume work in progress" in payload["systemMessage"]  # the banner SURVIVES

    def test_non_utf8_plugin_manifest_loses_only_the_skew(self, repo, capsys):
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        repo.manifest_path.write_bytes(NOT_UTF8)
        assert adv._read_installed_version() is None
        assert adv.main([]) == 0
        payload = json.loads(capsys.readouterr().out.strip())
        assert "Resume work in progress" in payload["systemMessage"]
        assert "re-run" not in payload["systemMessage"]

    def test_non_utf8_roadmap_loses_only_the_fences(self, repo, capsys):
        repo.roadmap(AUDIT_OPEN)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        repo.roadmap_path.write_bytes(NOT_UTF8)
        assert adv._read_roadmap() == (adv.FenceState(), adv.FenceState())
        assert adv.main([]) == 0
        assert "Resume work in progress" in json.loads(capsys.readouterr().out.strip())["systemMessage"]

    def test_non_utf8_plan_file_is_skipped_not_fatal(self, repo, capsys):
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        (repo.plans_dir / "0023-mojibake.md").write_bytes(NOT_UTF8)
        scan = adv._read_plans()
        assert [p.name for p in scan.in_flight] == ["0022-advisor.md"]  # the bad one skipped
        assert (scan.landed, scan.cold) == (0, 0)  # and NOT miscounted as landed
        assert adv.main([]) == 0
        assert "0022-advisor" in json.loads(capsys.readouterr().out.strip())["systemMessage"]

    def test_deeply_nested_manifest_json_is_silent_not_fatal(self, repo):
        # `json.loads` raises RecursionError (not a ValueError) on pathological nesting.
        repo.plugin_manifest("[" * 100_000 + "]" * 100_000)
        assert adv._read_installed_version() is None
        assert adv.build_output(adv.derive_state()) == {}

    def test_outer_failsafe_swallows_unexpected_error(self, monkeypatch, capsys):
        # If derive_state itself blew up, main() must still exit 0 with no output.
        monkeypatch.setattr(adv, "derive_state", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        rc = adv.main([])
        assert rc == 0
        assert capsys.readouterr().out.strip() == ""

    def test_glob_failure_no_crash(self, repo, monkeypatch):
        # A plans dir whose glob raises OSError — _read_plans degrades to an empty scan.
        repo.ensure_empty_plans_dir()
        from pathlib import Path

        def boom(self, *_a, **_k):
            raise OSError("glob exploded")

        monkeypatch.setattr(Path, "glob", boom)
        assert adv._read_plans() == adv.PlansScan()


# ─────────────────────────────────────────────────────────────────────────────
# CURRENCY NUDGE 1 — version skew: stamped managed docs BEHIND the installed plugin.
# Fires only when BOTH versions are readable AND both parse AND managed < installed.
# ─────────────────────────────────────────────────────────────────────────────
class TestVersionSkew:
    def test_anchor_survives_a_foreign_cwd_holding_a_decoy_manifest(self, tmp_path):
        # THE anchoring pin, with a real oracle. The earlier in-process form was VACUOUS:
        # it recomputed the same `__file__` expression, and pytest runs from the repo root
        # where a CWD anchor and the `__file__` anchor COINCIDE — so the exact forbidden
        # form `Path(".claude-plugin/plugin.json").resolve()` passed it. The working
        # directory is the thing under test, and it cannot be faked in-process, so this
        # spawns the module from a foreign cwd that holds a DECOY manifest and asserts the
        # anchor did not move. (This is the adopter's situation: their repo IS the cwd.)
        decoy = tmp_path / ".claude-plugin"
        decoy.mkdir()
        (decoy / "plugin.json").write_text(plugin_json(DECOY_VERSION), encoding="utf-8")

        probe = tmp_path / "probe.py"
        probe.write_text(
            "import importlib.util, json, sys\n"
            f"spec = importlib.util.spec_from_file_location('a', {str(ADVISOR_PATH)!r})\n"
            "m = importlib.util.module_from_spec(spec)\n"
            # Required: @dataclass resolves annotations through sys.modules[__module__].
            "sys.modules['a'] = m\n"
            "spec.loader.exec_module(m)\n"
            "print(json.dumps({'path': str(m.PLUGIN_MANIFEST_PATH),\n"
            "                  'version': m._read_installed_version()}))\n",
            encoding="utf-8",
        )
        seen = json.loads(
            subprocess.run(
                [sys.executable, str(probe)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        real_version = json.loads(ADVISOR_PATH.parent.parent.joinpath(".claude-plugin", "plugin.json").read_text(encoding="utf-8"))["version"]
        assert seen["path"] == str(adv.PLUGIN_MANIFEST_PATH)  # unmoved by the foreign cwd
        assert str(tmp_path) not in seen["path"]  # never resolved into the adopter's tree
        assert seen["version"] != DECOY_VERSION  # never the decoy the cwd offered
        assert seen["version"] == real_version  # the REAL shipped plugin version

    def test_skew_fires_when_stamped_docs_are_behind_the_plugin(self, repo):
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        payload = adv.build_output(adv.derive_state())
        assert payload["systemMessage"] == (
            "Harness docs stamped 0.4.1 < plugin 0.5.1 — re-run /claugentic-dev-harness:init."
        )

    def test_equal_versions_are_silent(self, repo):
        repo.claude_md(managed_claude_md("0.5.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        assert adv.build_output(adv.derive_state()) == {}

    def test_managed_newer_than_plugin_is_silent(self, repo):
        # A dev checkout ahead of the installed plugin: the user is not behind — say nothing.
        repo.claude_md(managed_claude_md("0.6.0"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        assert adv.build_output(adv.derive_state()) == {}

    @pytest.mark.parametrize(
        ("managed", "installed"),
        [
            ("0.4.1-rc.1", "0.5.1"),  # pre-release suffix — not a numeric tuple
            ("v0.4.1", "0.5.1"),  # `v` prefix
            ("0.4.x", "0.5.1"),  # placeholder segment
            ("0.4.1", "latest"),  # unparseable installed side
            ("1.²", "0.5.1"),  # non-ASCII digit — `isdigit()` True, `int()` rejects
        ],
    )
    def test_malformed_semver_is_silent(self, repo, managed, installed):
        # "Cannot compare" must never render as "you are stale" — a false skew costs trust.
        # NOTE: there is no blank-stamp row here. A truly blank stamp is UNREACHABLE —
        # MANAGED_VERSION_RE's `\S+` cannot match an empty string, so a blank stamp reads
        # as an ABSENT fence (covered by test_absent_managed_fence_...). The empty-string
        # input to the compare itself is covered by the `_version_lt` table's ("0.5.1", "").
        repo.claude_md(managed_claude_md(managed))
        repo.plugin_manifest(plugin_json(installed))
        assert adv.build_output(adv.derive_state()) == {}

    def test_missing_plugin_json_is_silent(self, repo):
        repo.claude_md(managed_claude_md("0.4.1"))  # no manifest written at all
        assert adv._read_installed_version() is None
        assert adv.build_output(adv.derive_state()) == {}

    def test_unparseable_plugin_json_is_silent(self, repo):
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest("{ not json at all")
        assert adv._read_installed_version() is None
        assert adv.build_output(adv.derive_state()) == {}

    @pytest.mark.parametrize(
        "manifest",
        ['{"name": "x"}', '{"name": "x", "version": 5}', '{"name": "x", "version": "  "}', "[]"],
    )
    def test_manifest_without_a_usable_version_is_silent(self, repo, manifest):
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(manifest)
        assert adv._read_installed_version() is None
        assert adv.build_output(adv.derive_state()) == {}

    def test_absent_managed_fence_is_silent_even_with_a_readable_plugin(self, repo):
        # THIS source repo's shape: a plugin manifest, no managed fence -> nothing to compare.
        repo.claude_md("# CLAUDE.md\n\nNo managed fence here.\n")
        repo.plugin_manifest(plugin_json("0.5.1"))
        assert adv.build_output(adv.derive_state()) == {}

    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            ("0.4.1", "0.5.1", True),
            ("0.5.1", "0.5.1", False),
            ("0.5.2", "0.5.1", False),
            ("0.4", "0.4.1", True),  # shorter tuple sorts lower
            ("0.5", "0.4.1", False),
            ("0.9.0", "0.10.0", True),  # numeric, not lexicographic
            ("0.5.1-rc.1", "0.5.1", None),
            ("0.5.1", "", None),
            # TOTALITY (Stage-7 #1). The left side is arbitrary user text — MANAGED_VERSION_RE
            # captures `\S+` from a HAND-EDITABLE CLAUDE.md fence — so this function must never
            # raise: an escape blanks the ENTIRE banner (resume line included), silently.
            ("1.²", "1.3", None),  # `str.isdigit()` is True here but `int()` REJECTS it
            ("1." + "9" * 5000, "1.3", None),  # >4300 digits: CPython's int-conversion ValueError
        ],
    )
    def test_version_lt_table(self, a, b, expected):
        assert adv._version_lt(a, b) is expected

    def test_a_hand_typoed_fence_never_blanks_the_banner(self, repo, capsys):
        # END-TO-END regression for the same defect: a fence stamped `@1.²` must not cost
        # the user the resume line. Before the fix, main() printed NOTHING — not even `{}`.
        repo.roadmap(AUDIT_EMPTY)
        repo.claude_md(managed_claude_md("1.²"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        assert adv.main([]) == 0
        payload = json.loads(capsys.readouterr().out.strip())
        assert "Resume work in progress" in payload["systemMessage"]
        assert "additionalContext" in payload
        assert "re-run" not in payload["systemMessage"]  # unparseable -> skipped, never guessed


# ─────────────────────────────────────────────────────────────────────────────
# CURRENCY NUDGE 2 — landed / cold plan housekeeping (COUNTED, never listed).
# ─────────────────────────────────────────────────────────────────────────────
class TestLandedAndColdPlans:
    def test_landed_plan_is_counted_not_listed(self, repo):
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0019-done.md", PLAN_DONE)
        state = adv.derive_state()
        assert (state.landed_plans, state.cold_plans, state.plans) == (1, 0, ())
        # Counted, never named: the filename must not reach the line.
        assert "0019-done" not in adv.build_output(state)["systemMessage"]

    def test_cold_in_flight_plan_is_counted_and_still_listed(self, repo, monkeypatch):
        # Cold is a HOUSEKEEPING count layered on top of the resume line — the plan is
        # still in flight, so it keeps its place in the recommendation.
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        state = adv.derive_state()
        assert (state.landed_plans, state.cold_plans) == (0, 1)
        msg = adv.build_output(state)["systemMessage"]
        assert "1 plan in flight: 0022-advisor" in msg
        assert "1 landed/cold plan in .claude/plans" in msg

    def test_fresh_in_flight_plan_is_not_cold(self, repo, monkeypatch):
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("2 days ago", int(time.time()) - 2 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        state = adv.derive_state()
        assert state.cold_plans == 0
        assert "landed/cold" not in adv.build_output(state)["systemMessage"]

    def test_git_absent_means_not_cold(self, repo, monkeypatch):
        # "We couldn't look" is not evidence of staleness — an unknown epoch never nudges.
        monkeypatch.setattr(adv, "_plan_git_meta", lambda _path: (None, None))
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        state = adv.derive_state()
        assert state.cold_plans == 0
        assert "landed/cold" not in adv.build_output(state)["systemMessage"]

    # `_is_cold` is pinned DIRECTLY against a FIXED `now` — the only form that pins the
    # threshold itself. Routing through fixtures at 2 and 40 days left `>` vs `>=`, a
    # lowered COLD_DAYS and an `abs()` sign-flip all alive; these rows kill all three,
    # and the fixed epoch removes the last wall-clock dependency from the suite.
    _FIXED_NOW = 1_700_000_000.0

    @pytest.mark.parametrize(
        ("days_old", "expected"),
        [
            (29, False),  # inside the window
            (30, False),  # EXACTLY COLD_DAYS — strictly older-than, so not yet cold
            (31, True),  # past the threshold
            (-31, False),  # clock skew: a future commit is not "old" (kills `abs()`)
        ],
    )
    def test_is_cold_threshold_table(self, days_old, expected):
        epoch = int(self._FIXED_NOW - days_old * 86400)
        assert adv._is_cold(epoch, self._FIXED_NOW) is expected

    def test_is_cold_unknown_epoch_is_never_cold(self):
        assert adv._is_cold(None, self._FIXED_NOW) is False

    def test_future_dated_commit_is_not_cold(self, repo, monkeypatch):
        # Clock skew must not invert the comparison into a bogus nudge.
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("in the future", int(time.time()) + 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        assert adv.derive_state().cold_plans == 0

    def test_landed_and_cold_are_ONE_combined_count(self, repo, monkeypatch):
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0018-done.md", PLAN_DONE)
        repo.plan("0019-done.md", PLAN_DONE)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        state = adv.derive_state()
        assert (state.landed_plans, state.cold_plans) == (2, 1)
        assert "3 landed/cold plans in .claude/plans" in adv.build_output(state)["systemMessage"]


# ─────────────────────────────────────────────────────────────────────────────
# CLAUSE COMPOSITION — one line, `CLAUSE_SEP`-joined, capped as a whole.
# ─────────────────────────────────────────────────────────────────────────────
class TestClauseComposition:
    def test_skew_clause_alone_is_the_whole_message(self, repo):
        # No recommendation fires (no plans, no fences) — the clause IS the message.
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        payload = adv.build_output(adv.derive_state())
        assert payload["systemMessage"].startswith("Harness docs stamped")
        assert adv.CLAUSE_SEP not in payload["systemMessage"]

    def test_housekeeping_clause_alone_is_the_whole_message(self, repo):
        repo.plan("0019-done.md", PLAN_DONE)
        payload = adv.build_output(adv.derive_state())
        assert payload["systemMessage"].startswith("1 landed/cold plan")
        assert adv.CLAUSE_SEP not in payload["systemMessage"]

    def test_both_clauses_append_to_a_primary_recommendation_in_order(self, repo, monkeypatch):
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        parts = adv.build_output(adv.derive_state())["systemMessage"].split(adv.CLAUSE_SEP)
        assert len(parts) == 3
        assert parts[0].startswith("Resume work in progress")
        assert parts[1].startswith("Harness docs stamped 0.4.1 < plugin 0.5.1")
        assert parts[2].startswith("1 landed/cold plan")

    def test_clauses_ride_a_promotional_nudge_too(self, repo):
        # The open-backlog recommendation is systemMessage-only; a clause joins it there.
        repo.roadmap(AUDIT_OPEN)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert adv.BUILD_CMD in payload["systemMessage"]
        assert "re-run /claugentic-dev-harness:init" in payload["systemMessage"]
        assert "additionalContext" not in payload

    @staticmethod
    def _overflowing_repo(repo, monkeypatch, *, plans: int) -> None:
        """A repo whose composed line CANNOT fit: `plans` long-named cold in-flight
        plans + a landed plan + a version skew, so both clauses fire and the resume
        summary alone blows the budget."""
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0018-done.md", PLAN_DONE)
        for i in range(plans):
            repo.plan(
                f"00{i:02d}-very-long-plan-name-that-eats-budget.md",
                "- **Status:** Approved\n"
                "- **Resumable from:** " + ("a very long resumable description " * 20) + "\n"
                "## Decomposition (slices)\n- [ ] **only.**\n",
            )

    def test_overflow_truncates_the_recommendation_never_a_clause(self, repo, monkeypatch):
        # THE ORDERING PIN (Stage-7 #3). Compose-then-cap made the clauses the first
        # casualty — and since cold plans ARE in-flight plans, the "run doctor" nudge
        # died exactly in the cluttered repo that most needs it. The clause budget is
        # RESERVED, so the ellipsis must land in the plan list, not on a nudge.
        self._overflowing_repo(repo, monkeypatch, plans=6)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        head, skew, housekeeping = msg.split(adv.CLAUSE_SEP)

        assert len(msg) <= adv.MAX_LINE_CHARS  # the ceiling still always wins
        assert msg.endswith(
            "7 landed/cold plans in .claude/plans — run /claugentic-dev-harness:doctor to sweep."
        )
        assert skew == "Harness docs stamped 0.4.1 < plugin 0.5.1 — re-run /claugentic-dev-harness:init."
        assert housekeeping.endswith("to sweep.")
        assert "…" in head  # the truncation landed in the recommendation
        assert "…" not in skew and "…" not in housekeeping

    def test_both_clauses_survive_at_ten_in_flight_plans(self, repo, monkeypatch):
        # The measured worst case from the Stage-7 panel: pre-fix, one clause was gone at
        # 4 in-flight plans and both at 8. Neither may be lost at 10.
        self._overflowing_repo(repo, monkeypatch, plans=10)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        assert len(msg) <= adv.MAX_LINE_CHARS
        assert adv.INIT_CMD in msg
        assert adv.DOCTOR_CMD in msg
        assert msg.endswith("to sweep.")

    def test_with_no_clause_firing_the_line_is_the_bare_capped_recommendation(
        self, repo, monkeypatch
    ):
        # Property (d) of the reserve: no clause -> byte-identical to a plain `_cap`.
        monkeypatch.setattr(adv, "_plan_git_meta", lambda _path: ("2 days ago", None))
        repo.roadmap(AUDIT_EMPTY)
        for i in range(6):
            repo.plan(
                f"00{i:02d}-very-long-plan-name-that-eats-budget.md",
                "- **Status:** Approved\n"
                "- **Resumable from:** " + ("a very long resumable description " * 20) + "\n"
                "## Decomposition (slices)\n- [ ] **only.**\n",
            )
        state = adv.derive_state()
        msg = adv.build_output(state)["systemMessage"]
        assert msg == adv._cap(adv.recommend_next(state))
        assert len(msg) <= adv.MAX_LINE_CHARS  # `_cap` rstrips, so it can land just under
        assert msg.endswith("…")

    def test_a_pathological_clause_tail_still_respects_the_ceiling(self, monkeypatch):
        # FLOOR GUARD: a clause tail near the whole budget would reserve the head into a
        # negative slice. The reserve is abandoned and the ceiling wins unconditionally.
        monkeypatch.setattr(adv, "MIN_HEAD_CHARS", 40)
        line = adv._compose_user_line("a recommendation " * 20, ("x" * (adv.MAX_LINE_CHARS - 10),))
        assert len(line) <= adv.MAX_LINE_CHARS
        assert line.endswith("…")


# ─────────────────────────────────────────────────────────────────────────────
# THE LOAD-BEARING PIN — AUDIENCE-SPLIT (0024 S3). The currency clauses are
# user-facing ONLY; widening them into `additionalContext` must FAIL here.
# ─────────────────────────────────────────────────────────────────────────────
class TestCurrencyClausesNeverReachTheAgent:
    def test_additional_context_carries_the_recommendation_alone(self, repo, monkeypatch):
        # The resume branch is the ONE path that emits additionalContext. With both
        # clauses firing, the agent-facing line must be BYTE-IDENTICAL to the pre-clause
        # form: prefix + recommendation, nothing appended.
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0019-done.md", PLAN_DONE)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        payload = adv.build_output(adv.derive_state())
        state = adv.derive_state()

        assert payload["additionalContext"] == adv._cap(
            adv.ADVISORY_PREFIX + adv.recommend_next(state)
        )
        # Mutation-shaped: every clause fragment must be absent from the agent's context.
        for clause in adv._currency_clauses(state):
            assert clause
            assert clause not in payload["additionalContext"]
        for token in ("re-run", "landed/cold", adv.INIT_CMD, adv.DOCTOR_CMD):
            assert token not in payload["additionalContext"]
        # ...while the USER's line carries them both.
        assert adv.INIT_CMD in payload["systemMessage"]
        assert adv.DOCTOR_CMD in payload["systemMessage"]

    def test_clauses_alone_emit_no_additional_context_at_all(self, repo):
        # No in-flight plan -> no agent-facing key, even though both clauses fire.
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0019-done.md", PLAN_DONE)
        payload = adv.build_output(adv.derive_state())
        assert "additionalContext" not in payload
        assert set(payload) == {"systemMessage"}


# ─────────────────────────────────────────────────────────────────────────────
# THE SYNTHETIC ADOPTER — the slice's acceptance fixture, asserted EXACTLY.
# fence@0.4.1 + plugin.json@0.5.1 + one Done plan + one 40-day-old in-flight plan.
# ─────────────────────────────────────────────────────────────────────────────
ADOPTER_PLAN_IN_FLIGHT = (
    "# 0007 — adopter feature\n\n"
    "- **Status:** Approved\n"
    "- **Resumable from:** Slice 2 spec\n\n"
    "## Decomposition (slices)\n\n"
    "- [ ] **S1 — first slice.**\n"
)


class TestSyntheticAdopter:
    @pytest.fixture
    def adopter(self, repo, monkeypatch):
        monkeypatch.setattr(
            adv, "_plan_git_meta", lambda _path: ("6 weeks ago", int(time.time()) - 40 * 86400)
        )
        repo.roadmap(AUDIT_EMPTY)
        repo.claude_md(managed_claude_md("0.4.1"))
        repo.plugin_manifest(plugin_json("0.5.1"))
        repo.plan("0006-landed.md", PLAN_DONE)
        repo.plan("0007-adopter.md", ADOPTER_PLAN_IN_FLIGHT)
        return repo

    def test_exact_combined_system_message(self, adopter):
        assert adv.build_output(adv.derive_state())["systemMessage"] == (
            "Resume work in progress — 1 plan in flight: 0007-adopter (6 weeks ago). "
            "Lead: Slice 2 spec"
            " · Harness docs stamped 0.4.1 < plugin 0.5.1 — re-run /claugentic-dev-harness:init."
            " · 2 landed/cold plans in .claude/plans — run /claugentic-dev-harness:doctor to sweep."
        )

    def test_additional_context_is_unchanged_by_the_nudges(self, adopter):
        assert adv.build_output(adv.derive_state())["additionalContext"] == (
            "Derived suggestion (confirm before acting): Resume work in progress — "
            "1 plan in flight: 0007-adopter (6 weeks ago). Lead: Slice 2 spec"
        )

    def test_end_to_end_through_main_stays_exit_zero_and_valid_json(self, adopter, capsys):
        rc = adv.main([])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out.strip())
        assert set(payload) == {"systemMessage", "additionalContext"}
        assert len(payload["systemMessage"]) <= adv.MAX_LINE_CHARS

    def test_the_off_switch_still_mutes_the_currency_nudges(self, adopter, monkeypatch, capsys):
        monkeypatch.setenv("CLAUDE_HARNESS_ADVISOR", "off")
        assert adv.main([]) == 0
        assert json.loads(capsys.readouterr().out.strip()) == {}
