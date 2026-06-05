---
description: Scaffold the agentic-dev-harness into the current repo — copy the managed harness set (standards catalog, workflow, tree-check), generate docs/ARCHITECTURE_TREE.md, set the tree-check globs, git-init if needed, and compose with existing lint/type-check/test tooling. Idempotent; never clobbers.
---

# /harness-init — not yet implemented (stub)

This skill is a **deliberate honest no-op** — it lands in plan `0003`, slice **S3**.

When complete it will, **idempotently** (detect → skip/merge → report; re-running is a safe no-op):
- **Copy the full managed harness set** (`docs/standards/`, `docs/WORKFLOW.md`, `docs/PLAYBOOK.md`, the tree-check script) into this repo, version-stamped and marked "managed — do not edit".
- **Generate `docs/ARCHITECTURE_TREE.md`** by walking the repo.
- **Detect the source layout** → set the tree-check `INCLUDE_GLOBS`; wire the hook.
- **`git init`** if absent; create `docs/ROADMAP.md` / `docs/DECISIONS.md` / a per-repo Current-scope if absent.
- **Compose with existing tooling** (eslint / tsc / test runner) rather than imposing new gates.

**For now:** tell the user `/harness-init` is not yet built (plan 0003, S3) and take no other action.
