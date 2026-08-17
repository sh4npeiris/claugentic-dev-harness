# CLAUDE.md

This repo builds the **`claugentic-dev-harness`** Claude Code plugin (a reusable, self-improving dev harness) and **dogfoods its own harness** — the workflow and roles below govern its own development. Standards and SOLID are **mandated and reviewed** (model-upheld: mandated here, audited by the architect/lens reviewers); the **mechanically enforced** gates are the two the pre-commit wrapper chains where wired — the architecture-tree check and the doc-budget check (per-repo caps; no config = no-op).

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
- **Record decisions.** Append a dated one-liner to `docs/claugentic-DECISIONS.md` for any non-trivial choice, filed per its header's filing rule (consult it before re-litigating a past one). Out-of-scope ideas → `docs/claugentic-ROADMAP.md`, not into the current change. When a doc-budget WARN fires, condense that ledger inline — the condensation pass (`docs/claugentic-WORKFLOW.md` → Definition of Done) is the procedure; git history is the archive.
- **Reference the decisions ledger only via `docs/claugentic-DECISIONS.md`** — it is an index; never link one of its shards directly. Keeping every external pointer on the index is what keeps a future re-split cheap. Model-upheld; no gate sees it.
- **Durable repo context lives here.** This CLAUDE.md (an adopter's `harness:` block) is the home for hard-won, durable structural/domain context — the gotchas a fresh agent must read first and record as it learns them. Model-upheld, never authoritative; keep it dense.
- **Releasing? `docs/RELEASE_CHECKLIST.md` — CI publishes.** `build_release.py --apply --bump <version>` PREPARES locally and STOPS; commit the bump + CHANGELOG section, then the one gated act is `git tag vX.Y.Z && git push origin main vX.Y.Z`. That tag fires `.github/workflows/release.yml`: every gate + on-main ancestry + `claude plugin validate --strict` at the tagged commit, then it pushes `release` + creates the Release. The script never tags/pushes (an aborted prepare may leave bumped manifests + a rebuilt local `release` ref). **A red run SPENDS the version — RE-RUN it first (safe by construction), only then bump forward; never reuse a tag.** A failure at the LAST step means content already published — don't bump. Eval-drift, `git range-diff`, and "the workflow is the only publisher" (`release` is unprotected) stay model-upheld.
- **Mute the SessionStart advisor** (`scripts/claugentic-session-advisor.py`) with `CLAUDE_HARNESS_ADVISOR=off` (any other value/unset = on). It emits agent-facing `additionalContext` only on the resume branch; the backlog and currency nudges (0041 S3) are user-facing `systemMessage` only.

## Development Workflow

Substantial work follows the staged pipeline in **`docs/claugentic-WORKFLOW.md`** — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small/local changes take the lightweight path (Implement + Verify), still updating `claugentic-ARCHITECTURE_TREE.md`/`claugentic-DECISIONS.md`. Specialist roles live in `.claude/agents/`; the orchestrator delegates to preserve context. Active plans live in `.claude/plans/` (start from `docs/claugentic-PLAN_TEMPLATE.md`).

## Definition of Done

A slice **lands** only when its acceptance criteria are met, **no new tech debt** is introduced, and both gate groups pass: the **deterministic gates** (tests, architecture-tree, version-sync, lint/type/security) and the **reviewer sign-offs** (the in-scope `docs/claugentic-standards/` dimensions). **`docs/claugentic-WORKFLOW.md` → Definition of Done is the single source of truth** for the full gate list — don't restate it here (index, don't duplicate).

The engineering quality bar is the in-scope `docs/claugentic-standards/` modules (entry point: `docs/claugentic-ENGINEERING_STANDARDS.md`) — a project-agnostic, ever-growing catch-all; the spec names the in-scope dimensions per slice and the reviewer audits against them.
