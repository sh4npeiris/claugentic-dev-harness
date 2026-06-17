"""Hermetic tests for the SessionStart advisor (`scripts/claugentic-advisor.py`).

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

Hermetic by construction: `tmp_path` materialises real roadmap/plan/CLAUDE.md
files; the advisor's PATH CONSTANTS are monkeypatched to point at them, so no real
repo artifact leaks in. `git log` (plan age) is monkeypatched so the age branch is
deterministic and offline.
"""

from __future__ import annotations

import json
import subprocess

import pytest

import advisor as adv

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

    Returns a small builder with `roadmap(text)`, `plan(name, text)`, `claude_md(text)`
    and `no_plans_dir()` so each test composes exactly the inputs it needs. By default
    NOTHING exists (the fresh-repo silent baseline). `git log` is stubbed to "unknown"
    so plan-age is deterministic unless a test overrides it.
    """
    plans_dir = tmp_path / ".claude" / "plans"
    roadmap_path = tmp_path / "docs" / "claugentic-ROADMAP.md"
    claude_path = tmp_path / "CLAUDE.md"
    monkeypatch.setattr(adv, "ROADMAP_PATH", roadmap_path)
    monkeypatch.setattr(adv, "PLANS_DIR", plans_dir)
    monkeypatch.setattr(adv, "CLAUDE_MD_PATH", claude_path)
    # Default: git is "unavailable" so age is None unless a test opts into it.
    monkeypatch.setattr(adv, "_plan_age", lambda _path: None)

    class Builder:
        def roadmap(self, text: str) -> None:
            roadmap_path.parent.mkdir(parents=True, exist_ok=True)
            roadmap_path.write_text(text, encoding="utf-8")

        def plan(self, name: str, text: str) -> None:
            plans_dir.mkdir(parents=True, exist_ok=True)
            (plans_dir / name).write_text(text, encoding="utf-8")

        def claude_md(self, text: str) -> None:
            claude_path.write_text(text, encoding="utf-8")

        def ensure_empty_plans_dir(self) -> None:
            plans_dir.mkdir(parents=True, exist_ok=True)

    return Builder()


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

    def test_done_plan_only_is_silent(self, repo):
        # A plan that is unambiguously Done (all boxes checked + Status Done) is NOT
        # in-flight; with an empty audit + absent product fence the result is silent.
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0019-done.md", PLAN_DONE)
        assert adv.build_output(adv.derive_state()) == {}

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

    def test_no_product_spec_recommends_product(self, repo):
        # Empty audit + a present product fence still carrying the no-spec sentinel.
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert adv.PRODUCT_CMD in payload["systemMessage"]
        assert "product spec" in payload["systemMessage"].lower()

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

    def test_partial_outranks_no_product_spec(self, repo):
        repo.roadmap(AUDIT_PARTIAL + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        assert "partial" in adv.build_output(adv.derive_state())["systemMessage"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# RETURN-2 — plan age via git log (omitted silently when git unavailable).
# ─────────────────────────────────────────────────────────────────────────────
class TestPlanAge:
    def test_age_is_rendered_when_git_available(self, repo, monkeypatch):
        monkeypatch.setattr(adv, "_plan_age", lambda _path: "2 days ago")
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        assert "2 days ago" in msg

    def test_age_omitted_when_git_unavailable(self, repo, monkeypatch):
        monkeypatch.setattr(adv, "_plan_age", lambda _path: None)
        repo.roadmap(AUDIT_EMPTY)
        repo.plan("0022-advisor.md", PLAN_IN_FLIGHT)
        msg = adv.build_output(adv.derive_state())["systemMessage"]
        assert "0022-advisor" in msg
        assert "ago" not in msg  # no age parenthetical

    def test_plan_age_returns_none_on_git_failure(self, monkeypatch, tmp_path):
        # The real _plan_age: a non-zero git return (untracked/non-repo) yields None.
        def fake_run(*_a, **_k):
            return subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="fatal")

        monkeypatch.setattr(adv.subprocess, "run", fake_run)
        assert adv._plan_age(tmp_path / "x.md") is None

    def test_plan_age_returns_none_when_git_missing(self, monkeypatch, tmp_path):
        def boom(*_a, **_k):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(adv.subprocess, "run", boom)
        assert adv._plan_age(tmp_path / "x.md") is None


# ─────────────────────────────────────────────────────────────────────────────
# RETURN-6 — additionalContext carries the advisory prefix.
# ─────────────────────────────────────────────────────────────────────────────
class TestAdvisoryPrefix:
    def test_additional_context_is_prefixed(self, repo):
        repo.roadmap(AUDIT_EMPTY + PRODUCT_NO_SPEC)
        repo.ensure_empty_plans_dir()
        payload = adv.build_output(adv.derive_state())
        assert payload["additionalContext"].startswith(adv.ADVISORY_PREFIX)
        # The user-facing line carries NO disclaimer (it's a greeting, not an instruction).
        assert not payload["systemMessage"].startswith(adv.ADVISORY_PREFIX)


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

    def test_outer_failsafe_swallows_unexpected_error(self, monkeypatch, capsys):
        # If derive_state itself blew up, main() must still exit 0 with no output.
        monkeypatch.setattr(adv, "derive_state", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        rc = adv.main([])
        assert rc == 0
        assert capsys.readouterr().out.strip() == ""

    def test_glob_failure_no_crash(self, repo, monkeypatch):
        # A plans dir whose glob raises OSError — _read_plans degrades to ().
        repo.ensure_empty_plans_dir()
        from pathlib import Path

        def boom(self, *_a, **_k):
            raise OSError("glob exploded")

        monkeypatch.setattr(Path, "glob", boom)
        assert adv._read_plans() == ()
