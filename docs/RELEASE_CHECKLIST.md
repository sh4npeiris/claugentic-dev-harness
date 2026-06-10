# Release Checklist

Releases are gated by the **Definition of Done** in [`docs/WORKFLOW.md`](WORKFLOW.md#definition-of-done) — run the deterministic gates (tests · `check_architecture_tree.py` · `check_versions_synced.py`) **and** the reviewer sign-offs there; this file does not restate them.

When bumping the version, bump **both** manifests together — `.claude-plugin/plugin.json` is the source of truth and `.claude-plugin/marketplace.json` must match. The version-sync gate (`python scripts/check_versions_synced.py`) enforces the pair.
