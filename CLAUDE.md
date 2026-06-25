# CLAUDE.md

This repo builds the **`claugentic-dev-harness`** Claude Code plugin (a reusable, self-improving dev harness) and **dogfoods its own harness** — the workflow and roles below govern its own development. Standards and SOLID are **mandated and reviewed** (model-upheld: mandated here, audited by the architect/lens reviewers); the one **mechanically enforced** gate is the architecture-tree check (file-index presence + staleness).

## Engineering Principles (non-negotiable, in priority order)

1. **SOLID** — single-responsibility, open/closed, Liskov, interface-segregation, dependency-inversion.
2. **DRY** — single source of truth for any logic, config, type, or constant.
3. **KISS** — the simplest thing that works for the current requirement.
4. **YAGNI** — no speculative features or future-proofing not asked for.
5. **Separation of concerns** — keep layers isolated.

Always: **validate at boundaries, trust internal code · make invalid states unrepresentable · fail loudly (never swallow exceptions) · configurable over hardcoded · single source of truth.**

## Harness Discipline

- **Use `docs/claugentic-ARCHITECTURE_TREE.md` to LOCATE, don't ingest it.** It's a one-line-per-file index. **Scan/grep it for the right file, then read THAT file** — don't read the whole tree into context. **Skip it entirely for a scoped single-file edit** when you already know the path. Keep it current: every file add/move/remove updates the tree (a commit-time hook enforces presence + staleness; descriptions, ~150-char target, are authored by you).
- **Keep this CLAUDE.md lean.** Dense one-liners, not paragraphs; **index, don't duplicate.** Point to the source-of-truth doc rather than restating it. Add only genuinely non-obvious gotchas/commands/patterns; don't add anything derivable from reading the code.
- **Record decisions.** Append a dated one-liner to `docs/claugentic-DECISIONS.md` for any non-trivial choice (consult it before re-litigating a past one). Out-of-scope ideas → `docs/claugentic-ROADMAP.md`, not into the current change.
- **Durable repo context lives here.** This CLAUDE.md (an adopter's `harness:` block) is the home for hard-won, durable structural/domain context — the gotchas a fresh agent must read first and record as it learns them. Model-upheld, never authoritative; keep it dense.
- **Releasing? Follow `docs/RELEASE_CHECKLIST.md`.** Anchor on the current `origin/main` (`git fetch` first) and run the `git range-diff` drop-check before any `@release` force-push. `build_release.py --apply` mechanically refuses a stale base (the BUILD); the force-push stays checklist-gated.
- **Mute the SessionStart advisor** (`scripts/claugentic-advisor.py`) with `CLAUDE_HARNESS_ADVISOR=off` (any other value/unset = on). It emits agent-facing `additionalContext` only on the resume branch; the backlog nudges are user-facing `systemMessage` only.

## Development Workflow

Substantial work follows the staged pipeline in **`docs/claugentic-WORKFLOW.md`** — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small/local changes take the lightweight path (Implement + Verify), still updating `claugentic-ARCHITECTURE_TREE.md`/`claugentic-DECISIONS.md`. Specialist roles live in `.claude/agents/`; the orchestrator delegates to preserve context. Active plans live in `.claude/plans/` (start from `TEMPLATE.md`).

## Definition of Done

A slice **lands** only when its acceptance criteria are met, **no new tech debt** is introduced, and both gate groups pass: the **deterministic gates** (tests, architecture-tree, version-sync, lint/type/security) and the **reviewer sign-offs** (the in-scope `docs/claugentic-standards/` dimensions). **`docs/claugentic-WORKFLOW.md` → Definition of Done is the single source of truth** for the full gate list — don't restate it here (index, don't duplicate).

The engineering quality bar is the in-scope `docs/claugentic-standards/` modules (entry point: `docs/claugentic-ENGINEERING_STANDARDS.md`) — a project-agnostic, ever-growing catch-all; the spec names the in-scope dimensions per slice and the reviewer audits against them.
