# Release Checklist

Releases are gated by the **Definition of Done** in [`docs/claugentic-WORKFLOW.md`](claugentic-WORKFLOW.md#definition-of-done) — run the deterministic gates (tests · `claugentic-check_architecture_tree.py` · `check_versions_synced.py`) **and** the reviewer sign-offs there; this file does not restate them.

When bumping the version, bump **both** manifests together — `.claude-plugin/plugin.json` is the source of truth and `.claude-plugin/marketplace.json` must match. The version-sync gate (`python scripts/check_versions_synced.py`) enforces the pair.

## Eval — the drift check (model-upheld)

Before a release, run the measurement procedure in [`eval/BASELINE.md`](../eval/BASELINE.md) — a standard audit over the seeded-defect fixture — and compare the recall / precision-proxy / refute-rate to the latest baseline entry.

- **A material regression blocks the release.** Defaults (judgment, overridable with a stated reason): recall down **≥2 seeds**, or precision-proxy or refute-rate moved **≥15 percentage points**.
- An **intentional, understood** shift (a prompt / model / standards change you made on purpose) is recorded as a **new dated baseline entry**, not a permanent block.
- **This step is model-upheld:** a person or agent follows this checklist and runs the eval — **nothing fires it mechanically.** It is a discipline, not a gate.

## Anchor the release on the live tip — never a stale base

Re-deriving the release from a **stale base** silently drops merged work: the v0.1.40 distillation (PRs merged into `main`) was lost when v0.1.41 was rebuilt from the pre-merge commit `03c404a` and force-pushed — the merge commits simply weren't reachable from the new base, so nobody saw them disappear. Always rebuild from the **current** `origin/main` tip:

1. `git fetch origin`
2. `git checkout main && git pull --ff-only origin main` — the `--ff-only` refuses if your local `main` has diverged (you're not on the live tip).
3. `python scripts/build_release.py --apply` — this now **refuses to build** if `HEAD` excludes any merge commit reachable from `origin/main` (and refuses if `origin/main` is absent — that's the signal you skipped step 1).

## Drop-check before the force-push (`git range-diff`)

`--apply` builds the **local** `release` branch and does **not** push. Before the manual `git push --force origin release`, prove you're not dropping anything:

- `git range-diff origin/release...release` — compare the old published release to the freshly built one. Investigate any commit shown as dropped (a `<` line with no `>` counterpart) that you didn't intend to drop.
- `git log --oneline origin/main --not release -- $(git ls-files)` — anything `origin/main` carries that the release doesn't, scoped to tracked paths. This should list **only `DEV_ONLY` paths** (the dev-only files that are intentionally stripped); a shipped-path entry here means the release is missing merged work.

**Honest scope:** the `build_release.py` refusal is the **one mechanical defense** — it guards the BUILD (you can't build the local `release` branch on a base that's missing merged merge-commits). The actual `git push --force origin release` stays **manual and checklist-gated** — the `git range-diff` drop-check above is model-upheld, not enforced. The guard **reduces, not eliminates,** the risk: it can't stop a force-push of a release that was built correctly but anchored on a base you fetched-then-let-go-stale, so still run the drop-check every time.
