# Release Checklist

Releases are gated by the **Definition of Done** in [`docs/WORKFLOW.md`](WORKFLOW.md#definition-of-done) — run the deterministic gates (tests · `check_architecture_tree.py` · `check_versions_synced.py`) **and** the reviewer sign-offs there; this file does not restate them.

When bumping the version, bump **both** manifests together — `.claude-plugin/plugin.json` is the source of truth and `.claude-plugin/marketplace.json` must match. The version-sync gate (`python scripts/check_versions_synced.py`) enforces the pair.

## Eval — the drift check (model-upheld)

Before a release, run the measurement procedure in [`eval/BASELINE.md`](../eval/BASELINE.md) — a standard audit over the seeded-defect fixture — and compare the recall / precision-proxy / refute-rate to the latest baseline entry.

- **A material regression blocks the release.** Defaults (judgment, overridable with a stated reason): recall down **≥2 seeds**, or precision-proxy or refute-rate moved **≥15 percentage points**.
- An **intentional, understood** shift (a prompt / model / standards change you made on purpose) is recorded as a **new dated baseline entry**, not a permanent block.
- **This step is model-upheld:** a person or agent follows this checklist and runs the eval — **nothing fires it mechanically.** It is a discipline, not a gate.
