# CLAUDE.md

This repo builds the **`claugentic-dev-harness`** Claude Code plugin (a reusable, self-improving dev harness) and **dogfoods it** — the workflow and roles below govern its own development. Standards and SOLID are **mandated and reviewed** (model-upheld: mandated here, audited by the gate/lens reviewers); the **mechanically enforced** gates are the two the pre-commit wrapper chains where wired — the architecture-tree check and the doc-budget check (per-repo caps; no config = no-op).

## Engineering Principles (non-negotiable, in priority order)

**SOLID · DRY (single source of truth for any logic, config, type, or constant) · KISS · YAGNI · separation of concerns.**

Always: **validate at boundaries, trust internal code · make invalid states unrepresentable · fail loudly (never swallow exceptions) · configurable over hardcoded.**

## Harness Discipline

- **Use `docs/claugentic-ARCHITECTURE_TREE.md` to LOCATE, don't ingest it.** One line per file: **scan/grep it for the right file, then read THAT file.** **Skip it entirely for a scoped single-file edit** when you already know the path. Keep it current — every file add/move/remove updates the tree (a commit-time hook enforces presence + staleness; descriptions, ~150-char target, are yours to author).
- **Keep this CLAUDE.md lean.** Dense one-liners; **index, don't duplicate** — point at the source-of-truth doc. Add only genuinely non-obvious gotchas/commands/patterns, never anything derivable from reading the code.
- **Record decisions.** `docs/claugentic-DECISIONS.md` is an INDEX: never append an entry there, and never link a shard directly from outside it. File a dated one-liner into the fitting `docs/claugentic-decisions/` shard per the index's filing rule, and consult it before re-litigating a past choice. Out-of-scope ideas → `docs/claugentic-ROADMAP.md`, not into the current change. On a doc-budget WARN, condense that ledger inline — `/claugentic-dev-harness:condense` owns the procedure; git history is the archive.
- **Durable repo context lives here.** This CLAUDE.md (an adopter's `harness:` block) is the home for hard-won structural/domain gotchas a fresh agent must read first and record as it learns them. Model-upheld, never authoritative; keep it dense.
- **Releasing? `docs/RELEASE_CHECKLIST.md` — CI publishes.** `build_release.py --apply --bump <version>` PREPARES locally and STOPS; it never tags or pushes. Commit the bump + the CHANGELOG section, then the one gated act is `git tag vX.Y.Z && git push origin main vX.Y.Z`, which fires `.github/workflows/release.yml` — the only publisher. **A red run SPENDS the version: RE-RUN it first (safe by construction), only then bump forward; never reuse a tag.** A failure at the LAST step means content already published — don't bump. Eval-drift, `git range-diff`, and "the workflow is the only publisher" (`release` is unprotected) stay model-upheld.
- **Mute the SessionStart advisor** (`scripts/claugentic-session-advisor.py`) with `CLAUDE_HARNESS_ADVISOR=off` (any other value/unset = on). It emits agent-facing `additionalContext` only on the resume branch; the backlog and currency nudges are user-facing `systemMessage` only.

## Development Workflow

Substantial work follows the staged pipeline in **`docs/claugentic-WORKFLOW.md`** — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small/local changes take the lightweight path (Implement + Verify), still updating the architecture tree and the decisions ledger. Specialist roles live in `.claude/agents/`; the orchestrator delegates to preserve context. Active plans live in `.claude/plans/` (start from `docs/claugentic-PLAN_TEMPLATE.md`).

## Definition of Done

A slice **lands** only when its acceptance criteria are met, **no new tech debt** is introduced, and both gate groups pass: the **deterministic gates** and the **reviewer sign-offs** (the in-scope `docs/claugentic-standards/` dimensions). **`docs/claugentic-WORKFLOW.md` → Definition of Done is the single source of truth** for the full gate list — don't restate it here.

The quality bar is the in-scope `docs/claugentic-standards/` modules (entry point: `docs/claugentic-ENGINEERING_STANDARDS.md`) — project-agnostic and ever-growing; the spec names the in-scope dimensions per slice and the reviewer audits against them.
