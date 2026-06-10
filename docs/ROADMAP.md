# Roadmap

The forward backlog for the harness itself. Each item runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect) in its own session, sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

Status: `NEXT` (queued) · `LATER` (demand- or trigger-gated).

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own forward roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## Next

| Item | Why it matters | Status |
|------|----------------|--------|
| **Plugin-read architecture** — agents read the standards/workflow/playbook from `${CLAUDE_PLUGIN_ROOT}/docs/…` instead of copy-on-init; `init` shrinks to the inherently-per-repo work and becomes refresh-capable. *(Validated: a subagent can `Read` plugin-bundled files by absolute path from an adopter repo; the install path is version-stamped, so the path auto-follows a marketplace update. Open wiring questions: `${CLAUDE_PLUGIN_ROOT}` expansion in skill bodies for subagent hand-off, and whether the tree-check hook receives it.)* | One source of truth refreshed by the marketplace — kills the copy-staleness problem and the need for an `/update` skill. | NEXT |
| **Curate the standards catalog for the 3-rung depth dial** — verify the catalog's coverage and per-module depth yield effective, valuable results across `focused` / `deep` / `exhaustive` reads; fill the gaps the depth dial exercises. | The depth dial only pays off if each lens has enough authored bar to dig into. | NEXT |
| **Wire `blindspot-reviewer` into the dev-workflow Stage-7 Verify** — give it a Verify-diff mode (mirroring `lens-reviewer`'s two-mode shape) so the cross-cutting sweep runs on a slice's diff, not only on an audit scope. | The "what does the per-lens view miss?" job is as valuable on a change as on a codebase; the agent was built to generalize. | NEXT |
| **"Run the actual app and observe behavior" as a named Verify step** — for user-facing slices, make running the app + observing it a first-class Stage-7 step, not just reading the diff. | Static review misses behavioral regressions a user would hit. | NEXT |

## Later — demand- or trigger-gated

| Item | Trigger | Status |
|------|---------|--------|
| **Deterministic trust-gates + the autopilot flip** — the mechanical layer for *unwatched* runs: a land-gate hook that runs the test suite itself and blocks a red commit · a secret-scan gate · a characterization-tests-first hook (declared-intent); then build mode's `autopilot` goes live (batch-approved specs → unwatched execution; the irreversible hard-stops remain). | Real-world use shows genuine demand for hands-off runs — today's watched checkpoint mode (with batch spec-approval) is the wanted mode. | LATER |
| **Read-once / group-lenses-by-shared-read** — when several lenses must read the same files, let one reader serve them, capped by per-reader context (group only where the shared read fits one agent). | A modest efficiency win — tree-targeting already trims most reads; build it if audit cost bites on a real repo. | LATER |
| **Grow the role library** (`.claude/agents/`) — add specialist agents as real use surfaces gaps the starter set lacks. | A gap proves *real* in use — never speculatively. | LATER |
| **Grow the standards catalog** — author capability modules (Redis, queues, object-storage, …) as real projects pull them in. | A real audit pulls one in (the catalog modernizes vibe-coded apps, not just cleans code). | LATER |
| **Partial-coverage glob drift** — extend the tree-check beyond the zero-coverage case to a repo whose globs match files but grows a second, un-globbed stack. | A real adopter hits it (a per-stack registry risks re-introducing the rot the lean check kills). | LATER |
| **Promote the honesty bar to `docs/standards/honesty-claims.md`** — today it lives embedded in the `honesty-reviewer` agent. | A second consumer beyond the agent needs the same bar. | LATER |
| **Stage-1 fork-convergence move** — a named procedure for converging a fork-heavy Discuss. | A second fork-heavy plan proves the friction (the plan TEMPLATE's "alternatives considered" line covers it today). | LATER |
| **Agent-boilerplate dedup** — share the DoD gate list now duplicated inline in the builder/verifier agents by design. | The platform gains prompt-includes (agent prompts must currently be self-contained). | LATER |
| **Mechanize the README agent-count check** — assert README's "N specialist agents" matches `plugin.json`'s `agents[]` length. | A recurring manual catch a tiny assertion closes; fold into `check_versions_synced.py` or a sibling. | LATER |
| **Gate: no tree-listed file may be git-ignored** — run `git check-ignore` over the tree's listed paths and fail loud on a hit. | An ignore rule once silently swallowed a shipped file; mechanically checkable. | LATER |
