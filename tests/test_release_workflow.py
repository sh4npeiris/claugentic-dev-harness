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

_GATE_SCRIPT_RE = re.compile(r"python (scripts/[\w.\-]+\.py)")
_RUNNER_OS_RE = re.compile(r"runner\.os\s*==\s*'(\w+)'")
# GitHub's `runner.os` values -> the runner-label prefix that produces them.
_RUNNER_OS_LABEL_PREFIX = {"Linux": "ubuntu", "Windows": "windows", "macOS": "macos"}


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


def _step_run(job: dict, name_fragment: str) -> str:
    """The `run:` script of the ONE step whose name contains `name_fragment`.

    Why this exists (mutation evidence, plan 0041 S2 Verify / F1): asserting a string against a
    whole job's concatenated script proves only that SOMETHING mentions it. Deleting the lease
    comparison left the suite green because the *snapshot* step still mentioned `git ls-remote`.
    A guard must be asserted inside the step that owns it, or it isn't pinned."""
    matches = [
        str(s.get("run", "")) for s in _steps(job) if name_fragment in str(s.get("name", ""))
    ]
    if len(matches) != 1:
        pytest.fail(
            f"expected exactly one step whose name contains {name_fragment!r}, found "
            f"{len(matches)} — the step was renamed, split, or duplicated."
        )
    return matches[0]


def _gate_scripts(job: dict) -> set[str]:
    """Every `python scripts/*.py` gate a job runs — derived, never hand-listed."""
    return set(_GATE_SCRIPT_RE.findall(_run_text(job)))


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
    """Least privilege BY JOB (Stage-7 spec amendment). The workflow default is read-only and
    only `publish` is granted write — because `gates` runs the whole suite plus a global npm
    install, and a workflow-level write token would hand that job the ability to push any ref,
    including `release` and a fresh `v*` tag that re-enters this workflow."""

    def test_workflow_default_is_read_only(self, release):
        # Asserted as EQUALITY: a later `packages: write` or `id-token: write` added for
        # convenience must fail this test, not ride along unnoticed.
        assert release.get("permissions") == {"contents": "read"}

    def test_only_publish_holds_the_write_grant(self, release):
        jobs = release["jobs"]
        assert jobs["publish"].get("permissions") == {"contents": "write"}
        assert "permissions" not in jobs["gates"], (
            "the gates job must inherit the read-only default — it needs no write capability"
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

    def test_the_push_step_itself_compares_the_lease_and_refuses(self, release):
        # Scoped to the OWNING step and asserting the refusal, not the vocabulary: the earlier
        # job-wide form stayed green when the whole comparison was deleted, because the snapshot
        # step still mentioned `git ls-remote` and `RELEASE_LEASE_SHA`.
        step = _step_run(release["jobs"]["publish"], "Publish the release branch")
        assert 'if [ "${now}" != "${RELEASE_LEASE_SHA}" ]' in step, (
            "the push step must COMPARE the snapshot, not merely mention it"
        )
        assert "exit 1" in step, "a moved origin/release must REFUSE, not warn"

    def test_the_lease_anchor_is_snapshotted_in_its_own_step(self, release):
        step = _step_run(release["jobs"]["publish"], "Snapshot origin/release")
        assert "git ls-remote origin refs/heads/release" in step
        assert "RELEASE_LEASE_SHA" in step

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

    # The four that exist today, as an explicit FLOOR — so a release job that loses a gate fails
    # even if someone deletes the same gate from ci.yml (which would satisfy the subset alone).
    GATE_FLOOR = frozenset(
        {
            "scripts/claugentic-check_architecture_tree.py",
            "scripts/check_versions_synced.py",
            "scripts/claugentic-check_doc_budgets.py",
            "scripts/check_shipped_content.py",
        }
    )

    def test_release_runs_every_gate_ci_runs(self, release, ci):
        # DERIVED, not hand-listed: a fifth gate added to ci.yml and forgotten here previously
        # shipped silently (the hand-typed list was a third home for the gate set).
        ci_gates = _gate_scripts(ci["jobs"]["gates"])
        release_gates = _gate_scripts(release["jobs"]["gates"])
        assert ci_gates, "ci.yml's gates job runs no gate scripts — the regex or the file moved"
        assert ci_gates <= release_gates, (
            f"gates in ci.yml but NOT at the tagged commit: {sorted(ci_gates - release_gates)}"
        )

    def test_the_known_four_gates_are_the_floor(self, release, ci):
        assert self.GATE_FLOOR <= _gate_scripts(ci["jobs"]["gates"])
        assert self.GATE_FLOOR <= _gate_scripts(release["jobs"]["gates"])

    def test_the_tagged_commit_must_be_on_main(self, release):
        # The authorization gate: the build's own guard is the REVERSE inclusion, so without this
        # a never-merged descendant passes every gate and publishes.
        step = _step_run(release["jobs"]["gates"], "tagged commit is on main")
        assert 'git merge-base --is-ancestor "${GITHUB_SHA}" refs/remotes/origin/main' in step
        assert "exit 1" in step, "an off-main tag must REFUSE, not warn"
        assert "git fetch" in step, "the remote-tracking ref must be fetched before it is read"

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
        # Scoped to the owning step + the refusal: the earlier job-wide form stayed green with
        # the whole `if`/`exit 1` deleted, because the surviving echo carried both strings.
        step = _step_run(release["jobs"]["gates"], "tag matches plugin.json")
        assert 'if [ "v${version}" != "${GITHUB_REF_NAME}" ]' in step, (
            "the step must COMPARE the tag with the manifest version"
        )
        assert "exit 1" in step, "a tag/version mismatch must REFUSE, not warn"

    def test_full_history_is_fetched(self, release):
        for name, job in release["jobs"].items():
            checkout = next(
                s for s in _steps(job) if str(s.get("uses", "")).startswith("actions/checkout")
            )
            assert checkout.get("with", {}).get("fetch-depth") == 0, (
                f"job '{name}' needs full history: the tag anchors and ancestry guards read it"
            )

    def test_every_os_gated_step_still_has_a_leg_to_run_on(self, release):
        """An `if: runner.os == 'X'` step is a no-op unless the matrix carries an X leg.

        Three steps of the gates job are gated that way — the on-main ancestry check (the
        authorization gate for what makes a commit releasable), the CLI install, and the strict
        marketplace validation. `publish` needs only that `gates` SUCCEEDED, and a job whose
        steps all skip still succeeds — so dropping the leg leaves the job green and publishes
        with those three gates never having run. Every other test here asserts the steps' TEXT,
        which that edit leaves untouched.

        Both sides are DERIVED from the file — no step name and no `ubuntu-latest` literal
        appears in this test — so a rename, a reorder, or a deliberate move to a different OS
        stays green; only a condition that can never fire goes red.
        """
        gates = release["jobs"]["gates"]
        labels = [str(o) for o in gates["strategy"]["matrix"]["os"]]
        required = {
            os_name
            for step in _steps(gates)
            for os_name in _RUNNER_OS_RE.findall(str(step.get("if", "")))
        }
        assert required, (
            "no step is OS-gated any more — this assertion is now vacuous and must be DELETED "
            "together with the OS gating it guards, not left behind reading green."
        )
        for os_name in sorted(required):
            prefix = _RUNNER_OS_LABEL_PREFIX[os_name]
            assert any(label.startswith(prefix) for label in labels), (
                f"steps gated on `runner.os == '{os_name}'` have no matrix leg to run on "
                f"(matrix os: {labels}) — they SKIP while the job still reports success, "
                f"silently voiding the release gate they implement."
            )


class TestChangelogHeadingContract:
    """The publish job extracts release notes by matching the literal heading `## <version>`.
    That couples a shell one-liner to a markdown convention with no other pin — a heading-style
    drift (`## [0.5.2] - 2026-08-12`) would be discovered only after the tag is spent."""

    def test_the_workflow_builds_the_bare_version_heading(self, release):
        step = _step_run(release["jobs"]["publish"], "release notes")
        assert '"## ${version}"' in step, (
            "the extractor's heading form is the contract — assert it explicitly"
        )
        assert 'version="${GITHUB_REF_NAME#v}"' in step, "the `v` prefix must be stripped"

    def test_the_changelog_uses_bare_semver_headings(self):
        # Portable: read the markdown directly rather than running the workflow's `awk`, which
        # does not exist on the Windows leg. Prose sections (`## Unreleased`, `## Prior
        # versions`) are untouched — the contract binds any heading that NAMES a version, which
        # is exactly what a Keep-a-Changelog style drift (`## [0.5.2] - 2026-08-12`) would break.
        text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        versioned = [
            ln.strip()
            for ln in text.splitlines()
            if ln.startswith("## ") and re.search(r"\d+\.\d+\.\d+", ln)
        ]
        assert versioned, "CHANGELOG.md carries no release sections"
        for heading in versioned:
            assert re.fullmatch(r"## \d+\.\d+\.\d+", heading), (
                f"{heading!r} would not be found by the publish job's `## <version>` match"
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
