"""Pin the SHAPE of the publishing pipeline (`.github/workflows/release.yml`).

Plan 0041 Slice 2 moved publishing from a human's force-push to a tag-triggered workflow. That
makes a YAML file load-bearing for the one act with no undo — so its structure is pinned here
rather than trusted to review. These are STATIC assertions over the workflow text: they prove
the file says what the release contract says it says. They do NOT prove a run succeeds (only a
real tag push does that), and nothing here executes GitHub Actions.

What each group protects:
  * `permissions` — an over-broad token on the one workflow that can write to the repo.
  * `needs: gates` — the ordering that makes "a red gate publishes nothing" true rather than
    aspirational.
  * `build_release.py --apply` — the single build path. A hand-rolled `git rm`/`git push` in
    YAML would be a second, untested implementation of the strip that drifts on its first edit.
  * the lease — a bare `git push --force` would silently clobber a concurrent publish.
  * gate parity with `ci.yml` — a gate the continuous pipeline runs but the release pipeline
    skips is a gate the release does not actually have.
  * the pip dependency group — the pyyaml-shaped break (a hand-listed install line missing a
    module the suite imports at collection) is closed by having ONE source of truth. Note the
    honest scope: removing pyyaml from the group still fails loud, but via the existing
    collection behavior of `test_frontmatter_parses.py`, not via an assertion here.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
RELEASE_WORKFLOW = WORKFLOWS / "release.yml"
CI_WORKFLOW = WORKFLOWS / "ci.yml"

# The action majors this repo pins. The Node-20 action runtime is deprecated, so every pin must
# sit on a major whose `using:` is node24 — v7 for all three at the time of writing. A bump
# updates THIS map and both workflows together (the parity test below refuses a half-bump).
MIN_ACTION_MAJORS = {
    "actions/checkout": 7,
    "actions/setup-python": 7,
    "actions/setup-node": 7,
}

_USES_RE = re.compile(r"^\s*-?\s*uses:\s*([\w.-]+/[\w.-]+)@v(\d+)", re.MULTILINE)


def _load(path: Path) -> dict:
    """Parse a workflow, failing loud if it is missing or not a mapping."""
    if not path.exists():
        pytest.fail(f"{path.relative_to(REPO_ROOT)} is missing — the release cannot publish.")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        pytest.fail(f"{path.relative_to(REPO_ROOT)} did not parse to a mapping.")
    return data


def _triggers(workflow: dict) -> dict:
    """The `on:` block. YAML 1.1 reads a bare `on` key as the BOOLEAN True, so PyYAML hands it
    back under `True`, not `"on"` — read both rather than depending on which parser ran."""
    for key in ("on", True):
        if key in workflow:
            return workflow[key]
    pytest.fail("the workflow has no `on:` trigger block")


def _steps(job: dict) -> list[dict]:
    return [s for s in job.get("steps", []) if isinstance(s, dict)]


def _run_text(job: dict) -> str:
    """Every `run:` script in a job, concatenated — the searchable body of what it executes."""
    return "\n".join(str(s.get("run", "")) for s in _steps(job))


@pytest.fixture(scope="module")
def release() -> dict:
    return _load(RELEASE_WORKFLOW)


@pytest.fixture(scope="module")
def ci() -> dict:
    return _load(CI_WORKFLOW)


class TestTrigger:
    def test_fires_on_version_tags_only(self, release):
        push = _triggers(release)["push"]
        assert push.get("tags") == ["v*"], "publishing must be triggered by a `v*` tag push"
        assert "branches" not in push, (
            "a branch trigger would publish on every push to that branch — the tag IS the gate"
        )


class TestPermissions:
    def test_exactly_contents_write(self, release):
        # Least privilege, asserted as EQUALITY: a later `packages: write` or `id-token: write`
        # added for convenience must fail this test, not ride along unnoticed.
        assert release.get("permissions") == {"contents": "write"}

    def test_no_job_widens_the_token(self, release):
        for name, job in release["jobs"].items():
            assert "permissions" not in job, (
                f"job '{name}' overrides the workflow-level least-privilege token"
            )


class TestJobOrdering:
    def test_publish_needs_gates(self, release):
        needs = release["jobs"]["publish"]["needs"]
        needs = [needs] if isinstance(needs, str) else needs
        assert needs == ["gates"], (
            "publish must depend on gates — this dependency IS 'a red gate publishes nothing'"
        )

    def test_gates_does_not_publish(self, release):
        body = _run_text(release["jobs"]["gates"])
        assert "git push" not in body, "only the publish job may push"
        assert "gh release create" not in body


class TestPublishMechanics:
    def test_publishes_via_the_one_build_path(self, release):
        body = _run_text(release["jobs"]["publish"])
        assert "python scripts/build_release.py --apply" in body

    def test_never_bumps_at_publish_time(self, release):
        # The version is already committed at the tagged commit; a `--bump` here would rewrite
        # a manifest that the gates job already validated against the tag.
        body = _run_text(release["jobs"]["publish"])
        assert "--bump" not in body

    def test_does_not_hand_roll_the_strip(self, release):
        body = _run_text(release["jobs"]["publish"])
        for forbidden in ("git rm", "git worktree add --force", "git commit -"):
            assert forbidden not in body, (
                f"'{forbidden}' is the release BUILD's job — see scripts/build_release.py"
            )

    def test_the_branch_push_is_leased(self, release):
        body = _run_text(release["jobs"]["publish"])
        assert "--force-with-lease" in body
        assert not re.search(r"git push\s+--force(?!-with-lease)", body), (
            "a bare --force would clobber a concurrent publish"
        )

    def test_the_lease_anchor_is_captured_then_compared(self, release):
        # The fetch-and-compare CI stands in for a human's remote-tracking lease: snapshot the
        # remote ref, then refuse if it moved before the push.
        body = _run_text(release["jobs"]["publish"])
        assert "git ls-remote origin refs/heads/release" in body
        assert "RELEASE_LEASE_SHA" in body

    def test_creates_the_github_release_with_changelog_notes(self, release):
        body = _run_text(release["jobs"]["publish"])
        assert "gh release create" in body
        assert "--notes-file" in body
        assert "CHANGELOG.md" in body

    def test_release_notes_are_extracted_before_anything_publishes(self, release):
        # Ordering is the whole point: a missing CHANGELOG section must fail with zero side
        # effects, not after the release branch is already pushed.
        steps = _steps(release["jobs"]["publish"])
        def index_of(needle: str) -> int:
            return next(i for i, s in enumerate(steps) if needle in str(s.get("run", "")))

        assert index_of("CHANGELOG.md") < index_of("git push")


class TestGateParity:
    """Every deterministic gate `ci.yml` runs must also run at the tagged commit."""

    @pytest.mark.parametrize(
        "script",
        [
            "scripts/claugentic-check_architecture_tree.py",
            "scripts/check_versions_synced.py",
            "scripts/check_doc_budgets.py",
            "scripts/check_shipped_content.py",
        ],
    )
    def test_gate_script_runs_in_the_release_gates_job(self, release, ci, script):
        assert script in _run_text(ci["jobs"]["gates"]), (
            f"{script} is expected in ci.yml's gates job — update this pin if it moved"
        )
        assert script in _run_text(release["jobs"]["gates"])

    def test_the_full_suite_and_node_tests_run(self, release):
        body = _run_text(release["jobs"]["gates"])
        assert "python -m pytest" in body
        assert "node --test tests/workflows/*.test.mjs" in body

    def test_plugin_manifests_are_strictly_validated(self, release):
        # The check that would have caught the 0.4.0-0.5.0 frontmatter defect. The marketplace
        # manifest is validated at the tagged commit; the PLUGIN manifest is validated against
        # the BUILT (stripped) tree, because `--strict` warns on the dev-only root CLAUDE.md.
        assert "claude plugin validate --strict ." in _run_text(release["jobs"]["gates"])
        publish_body = _run_text(release["jobs"]["publish"])
        assert "claude plugin validate --strict" in publish_body
        assert "release-tree" in publish_body, (
            "the plugin manifest must be validated against the built tree, not the dev tree"
        )

    def test_the_tag_is_checked_against_the_manifest_version(self, release):
        body = _run_text(release["jobs"]["gates"])
        assert "GITHUB_REF_NAME" in body and "plugin.json" in body

    def test_full_history_is_fetched(self, release):
        for name, job in release["jobs"].items():
            checkout = next(
                s for s in _steps(job) if str(s.get("uses", "")).startswith("actions/checkout")
            )
            assert checkout.get("with", {}).get("fetch-depth") == 0, (
                f"job '{name}' needs full history: the tag anchors and ancestry guards read it"
            )


class TestActionPins:
    @pytest.mark.parametrize("workflow", [RELEASE_WORKFLOW, CI_WORKFLOW])
    def test_pins_are_off_the_deprecated_node20_runtime(self, workflow):
        text = workflow.read_text(encoding="utf-8")
        found = _USES_RE.findall(text)
        assert found, f"{workflow.name} pins no actions — the regex or the file changed shape"
        for action, major in found:
            floor = MIN_ACTION_MAJORS.get(action)
            assert floor is not None, f"unpinned-by-policy action {action} — add it to the map"
            assert int(major) >= floor, (
                f"{workflow.name} pins {action}@v{major}; v{floor}+ is required (the Node-20 "
                f"action runtime is deprecated)"
            )

    def test_both_workflows_pin_the_same_majors(self):
        def majors(path: Path) -> dict[str, str]:
            return dict(_USES_RE.findall(path.read_text(encoding="utf-8")))

        release_majors, ci_majors = majors(RELEASE_WORKFLOW), majors(CI_WORKFLOW)
        shared = set(release_majors) & set(ci_majors)
        assert shared, "the two workflows share no actions — one of them stopped checking out?"
        for action in sorted(shared):
            assert release_majors[action] == ci_majors[action], (
                f"{action} pinned at different majors across the two workflows (half-bump)"
            )


class TestTestDependencyGroup:
    """The pyyaml lesson: test dependencies live in ONE place (`[dependency-groups] test`) and
    every CI job installs from it. A hand-listed install line is how a module the suite imports
    at collection time goes missing and a red suite reads as a silent one."""

    def test_pyproject_declares_the_group(self):
        data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        group = data.get("dependency-groups", {}).get("test")
        assert isinstance(group, list) and group, "pyproject.toml has no `test` dependency group"
        assert "pytest" in group and "pyyaml" in group

    @pytest.mark.parametrize("workflow", [RELEASE_WORKFLOW, CI_WORKFLOW])
    def test_every_pip_install_uses_the_group(self, workflow):
        text = workflow.read_text(encoding="utf-8")
        installs = [
            line.strip()
            for line in text.splitlines()
            if "pip install" in line and "--upgrade pip" not in line
        ]
        assert installs, f"{workflow.name} installs no test dependencies"
        for line in installs:
            assert "--group test" in line, f"hand-listed install in {workflow.name}: {line}"
