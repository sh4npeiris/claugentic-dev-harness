# Decisions ledger — INDEX

A forward-looking maintainer's guide — consult it before re-litigating a past choice. **NOT append-only history:** each shard is condensed periodically (`docs/claugentic-WORKFLOW.md` → the condensation pass) — superseded entries merge to git history, hardened must-holds promote to `docs/claugentic-INVARIANTS.md`; keep an entry only if a future agent needs it to decide correctly, and when in doubt keep a constraint.

Index only — NEVER append entries here; file into the fitting shard in `docs/claugentic-decisions/`
(no fit → create one — growth is horizontal). Not finding something? `rg <term> docs/claugentic-decisions/`.
All external references point at THIS file — never link a shard path from outside the index.

- [honesty](claugentic-decisions/honesty.md) — **READ FIRST.** Honesty positioning (the #1 rule): [D]/[J] verb discipline; never launder model-upheld into mechanical; the two senses of "independent".
- [deterministic-gates](claugentic-decisions/deterministic-gates.md) — The deterministic gates: tree check · version-sync · doc budgets & caps · one gate, one invariant.
- [verify-roles](claugentic-decisions/verify-roles.md) — The verify/judge roles: skeptical clean-context review, refute-first, same-model tag honesty.
- [audit](claugentic-decisions/audit.md) — The audit: lens fan-out · dedup · finding-verifier · tiered backlog · depth dial · rejected-findings fence.
- [build-mode](claugentic-decisions/build-mode.md) — Build mode: backlog auto-drive, build-to-green, decision-gated autonomy.
- [workflow-process](claugentic-decisions/workflow-process.md) — Workflow/process: stages & gates, DoD ownership, carry-forward + mirror-back, methodology toolbox & charter, plan lifecycle, scope-agnostic rule.
- [roles-review](claugentic-decisions/roles-review.md) — Roles & review: roster postures, diverse panel, craft-is-first-class, lens coverage, runtime-qa, worktree hygiene.
- [doc-lifecycle](claugentic-decisions/doc-lifecycle.md) — Doc lifecycle & condensation: the budgets ladder (bump for logs/index · shard for rule-books), reads-vs-knows principle, Readiness posture.
- [plugin-distribution](claugentic-decisions/plugin-distribution.md) — Plugin identity & distribution: marketplace github-object form, release branch, managed docs are adopter-aware, init/update contracts.
- [release-contract](claugentic-decisions/release-contract.md) — Release contract: build_release single command, ship/strip classes, shipped-content scanner, referential closure, range-diff drop-check, plan-0034 `source.ref` repoint.
