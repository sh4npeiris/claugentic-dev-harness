# CLAUDE.md

This repo builds the **`agentic-dev-harness`** Claude Code plugin (a reusable, self-improving dev harness) and **dogfoods its own harness** — the workflow, roles, standards, and enforcement below govern its own development.

## Engineering Principles (non-negotiable, in priority order)

1. **SOLID** — single-responsibility, open/closed, Liskov, interface-segregation, dependency-inversion.
2. **DRY** — single source of truth for any logic, config, type, or constant.
3. **KISS** — the simplest thing that works for the current requirement.
4. **YAGNI** — no speculative features or future-proofing not asked for.
5. **Separation of concerns** — keep layers isolated.

Always: **validate at boundaries, trust internal code · make invalid states unrepresentable · fail loudly (never swallow exceptions) · configurable over hardcoded · single source of truth.**

## Harness Discipline

- **Read `docs/ARCHITECTURE_TREE.md` first.** It's a one-line-per-file index — use it to find the right files instead of reading the whole tree. Keep it current: every file add/move/remove updates the tree (a hook enforces presence + staleness; descriptions are authored by you).
- **Keep this CLAUDE.md lean.** Dense one-liners, not paragraphs; **index, don't duplicate.** Point to the source-of-truth doc rather than restating it. Add only genuinely non-obvious gotchas/commands/patterns; don't add anything derivable from reading the code.
- **Record decisions.** Append a dated one-liner to `docs/DECISIONS.md` for any non-trivial choice (consult it before re-litigating a past one). Out-of-scope ideas → `docs/ROADMAP.md`, not into the current change.

## Development Workflow

Substantial work follows the staged pipeline in **`docs/WORKFLOW.md`** — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small/local changes take the lightweight path (Implement + Verify), still updating `ARCHITECTURE_TREE.md`/`DECISIONS.md`. Specialist roles live in `.claude/agents/`; the orchestrator delegates to preserve context. Active plans live in `.claude/plans/` (start from `TEMPLATE.md`).

## Definition of Done

A slice **lands** only when: acceptance criteria met **+** the in-scope `docs/ENGINEERING_STANDARDS.md` dimensions pass the `architect-reviewer` audit **+** all gates green (full tests incl. any regression/snapshot tests, `python scripts/check_architecture_tree.py`, and the project's lint / type-check / security gates) **+** **no new tech debt.**

The engineering quality bar is **`docs/ENGINEERING_STANDARDS.md`** — a project-agnostic, ever-growing catch-all; the spec names the in-scope dimensions per slice and the reviewer audits against them.
