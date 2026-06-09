# 0002 — Read harness files from the plugin (kill copy-on-init + `/update`)

- **Status:** Draft — validation pending (2 precondition tests); **paused for session handoff**
- **Roadmap item:** `docs/ROADMAP.md` → Next "Plugin-read architecture (supersedes `/...:update`)"
- **References:** `docs/DECISIONS.md` → "Standards/workflow read from the plugin, not copied"; `skills/init/SKILL.md`; `skills/audit/SKILL.md`; `.claude/agents/lens-reviewer.md` · `architect-reviewer.md`; `scripts/check_architecture_tree.py`; `docs/WORKFLOW.md`

## Problem
`init` **copies** the managed set (`docs/standards/`, `WORKFLOW.md`, `PLAYBOOK.md`, `ENGINEERING_STANDARDS.md`, `check_architecture_tree.py`) into every adopter repo, and agents read those local copies. Costs: (1) N duplicated copies of the standards (DRY violation); (2) copies go **stale** when the harness improves — a marketplace update refreshes the *plugin* but cannot touch in-repo copies, and re-running `init` is copy-**if-absent** (skips them) → adopters freeze at their init-time version (e.g. the false-green gate fix never reaches them); (3) it forces a whole `/...:update` skill onto the roadmap.

## Proven this session (the unblock)
- A subagent **CAN `Read` a plugin-bundled file by absolute path** from inside an adopter project — tested at `…/.claude/plugins/cache/sh4npeiris/claugentic-dev-harness/<ver>/docs/standards/security.md` → **READ OK**. Refutes the "subagents can't read bundled files" assumption behind copy-on-init.
- The marketplace install bundles the **whole repo**; the install path is **version-stamped** (`…/<semver>/…`), so `${CLAUDE_PLUGIN_ROOT}` auto-follows marketplace updates.
- `${CLAUDE_PLUGIN_ROOT}` is empty in a plain shell (plugin-context var); expands in skill bodies (init relies on this).

## Goals / Non-goals
**Goals:** agents read standards/workflow/playbook from `${CLAUDE_PLUGIN_ROOT}/docs/…` (single source of truth, marketplace-refreshed); shrink `init` to per-repo essentials; make `init` **refresh-capable**; **delete the `/...:update` plan**.
**Non-goals:** no change to what the audit/workflow *do*; per-repo files (tree · ROADMAP · DECISIONS · the CLAUDE.md managed fence · per-repo gate config) **stay in the repo**; not touching the deterministic-trust-gates track.

## Preconditions — two cheap tests BEFORE committing the design (Slice 0)
1. **Skill-context expansion:** confirm `${CLAUDE_PLUGIN_ROOT}` expands inside the audit/init **SKILL body**, so the orchestrator can construct the absolute path it passes to subagents. *(Documented via init; not freshly e2e-tested. If it fails → the orchestrator must discover the plugin root another way, or copy-on-init stays.)*
2. **Hook access:** determine whether the architecture-tree **hook** (run from the adopter's `.claude/settings.json` as a shell command) receives `${CLAUDE_PLUGIN_ROOT}` or only `${CLAUDE_PROJECT_DIR}`. → decides whether the gate **script** runs from the plugin (per-repo config externalized to a tiny file) or stays a thin copied file refreshed by `init`.

## Approach (design — pending the two tests)
- **Agents read from the plugin:** `lens-reviewer` / `architect-reviewer` / the audit + verify flows read modules from `${CLAUDE_PLUGIN_ROOT}/docs/standards/<module>.md`. The orchestrator (skill context) resolves `${CLAUDE_PLUGIN_ROOT}` and passes **absolute paths** to subagents (proven readable).
- **`init` stops copying docs:** it writes a CLAUDE.md managed fence that **points at** `${CLAUDE_PLUGIN_ROOT}` paths (or documents the read-from-plugin convention), seeds per-repo ROADMAP/DECISIONS, generates the tree, sets per-repo gate config, wires the hook.
- **`init` becomes refresh-capable:** re-running re-syncs the **version-stamped managed fence** in place (never user content) — this replaces `/update`.
- **Gate script:** test 2 passes → run from plugin with per-repo config in a tiny file (e.g. `.claude/harness.json`); else → keep a thin copied `check_architecture_tree.py`, refreshed by `init`.

## Affected files (anticipated)
`skills/init/SKILL.md` (point-not-copy; refresh-capable; per-repo config) · `skills/audit/SKILL.md` + `.claude/agents/lens-reviewer.md`/`architect-reviewer.md` (read from `${CLAUDE_PLUGIN_ROOT}`) · `scripts/check_architecture_tree.py` (externalize `INCLUDE_GLOBS` if run from plugin) · `docs/DECISIONS.md` (supersede "Copy standards on init") · `docs/ROADMAP.md` (already drops `/update`) · `CLAUDE.md` · `docs/ARCHITECTURE_TREE.md`.

## Risks & mitigations
- Test 1 fails → fall back to discovering the plugin root or keep copying. · Test 2 fails → script stays a thin copy (acceptable; tiny). · Adopters lose easy local customization of standards → acceptable for the non-engineer audience; power users can still copy selectively. · **Backward-compat:** existing v0.1.2 adopters already have copied files — the new refresh-capable `init` must reconcile (refresh managed regions; optionally a one-time clean re-init), documented.

## Decomposition (slices) — finalize after Slice 0 + plan-review
- [ ] **Slice 0** — run the two precondition tests; record results here.
- [ ] **Slice 1** — agents/audit read standards from `${CLAUDE_PLUGIN_ROOT}`; verify an audit still works end-to-end.
- [ ] **Slice 2** — `init`: stop copying docs (point instead); refresh-capable managed fence; per-repo config.
- [ ] **Slice 3** — gate script from plugin OR thin-copy-refreshed (per test 2); docs sweep (DECISIONS/ROADMAP/TREE); confirm `/update` fully retired.

---
## Review  _(pending — Stage 3)_
## Spec  _(pending)_
