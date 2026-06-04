# Roadmap

Backlog of substantial work. Each item runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect) in **its own session**, sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

Status: `NEXT` (queued) · `LATER` · `PLAN <NNNN>` (plan drafted) · `DONE`.

---

## Build: package the harness as a plugin (PLAN 0001)

The slices below are the build backlog from `.claude/plans/0001-build-agentic-dev-harness.md` — workflows-first, each lands complete in one session.

| # | Item | Status |
|---|------|--------|
| B1 | **Plugin shell + manifest** — `.claude-plugin/plugin.json` exposing agents + commands; verify the manifest schema against official Claude Code docs first. | PLAN 0001 |
| B2 | **`audit` workflow** — bounded multi-modal codebase sweep → dedup → prioritize → write a tiered backlog into `docs/ROADMAP.md`; validate it reproduces DistrictSync's known Tier-1/2/3 backlog. | PLAN 0001 |
| B3 | **`refactor-item` workflow** — characterization-tests-first → refactor in an isolated worktree → verify behavior unchanged → land. | PLAN 0001 |
| B4 | **`init-harness` command** — idempotent scaffold (docs + generate ARCHITECTURE_TREE + per-repo Current-scope + CLAUDE harness section + language-detected check globs); never clobber existing files. | PLAN 0001 |
| B5 | **`/harness-audit` command + skill wiring** — surface the audit workflow as a command/skill. | PLAN 0001 |
| B6 | **Package & dogfood** — finalize the marketplace package and install it into a throwaway repo end-to-end. | PLAN 0001 |

## Later

| Item | Status |
|------|--------|
| Publish install instructions (marketplace + plugin name) in `README.md` once B6 lands. | LATER |
| Grow the role library (`.claude/agents/`) as new specialist needs emerge from dogfooding. | LATER |
