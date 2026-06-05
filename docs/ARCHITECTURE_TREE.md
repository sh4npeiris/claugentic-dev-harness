# Architecture Tree

> **Read this first.** This is the one-line-per-file index of the repo — your map. Use it to find the right file instead of reading the whole tree. Keep it current: every file add/move/remove updates this index (a hook enforces presence + staleness — see CLAUDE.md → Harness Discipline). Descriptions are authored by you/the agent that touches the file.

This repo builds the **`agentic-dev-harness`** Claude Code plugin and dogfoods its own harness. The only executable code today is `scripts/check_architecture_tree.py`; everything else is harness docs, roles, plans, and config.

## Root

- `README.md` — what `agentic-dev-harness` is (reusable self-improving Claude Code dev harness + plugin), how it installs, how it works (init → audit → tag-gated pipeline), the two adoption modes, and honest v0.1 status.
- `CLAUDE.md` — lean, generalized guidance for agents working in THIS repo: engineering principles, harness discipline, workflow pointer, Definition of Done.
- `.gitignore` — ignores local junk + build artifacts; **shares** `.claude/agents/`, `.claude/plans/`, `.claude/settings.json` (ignores only `.claude/settings.local.json`).
- `.gitattributes` — normalizes line endings (`* text=auto eol=lf`; scripts forced LF) for a cross-platform plugin that bundles shell/Node scripts.

## docs/ — process, standards, and project memory

- `docs/WORKFLOW.md` — the staged agent development workflow (Triage → Discuss → Plan → Review → Spec → Approve → Implement → Verify → Land → Retrospect); source of truth for process.
- `docs/ENGINEERING_STANDARDS.md` — project-agnostic, ever-growing catch-all of engineering quality dimensions; the bar implementations are held to (the per-repo "Current scope" is added by `harness-init`, not shipped populated).
- `docs/ARCHITECTURE_TREE.md` — this file: one-line-per-file index of the repo.
- `docs/DECISIONS.md` — dated, one-line records of non-trivial decisions (newest at top); consult before re-litigating.
- `docs/ROADMAP.md` — backlog of substantial work; tangents land here, never silently into the current change.
- `docs/PLAYBOOK.md` — plain-English guide for a non-engineer driving the harness: the pipeline, your three leverage points, the orchestration patterns (fan-out, adversarial-verify, effort dial), a worked example, and a mini-glossary.

## docs/standards/ — the modular quality catalog (plan 0002 Pillar A)

- `docs/standards/_TEMPLATE.md` — the **module contract**: frontmatter schema (version, ISO-25010 mapping, load-scope) + per-dimension structure (good / auditor-checks / confidence / tradeoff / sources) every module conforms to. The gate for all module authoring.
- `docs/standards/README.md` — catalog index + meta-rules (select-don't-skip, additive, novel-patterns-allowed), the two-tier model (global copied-on-init + version-stamped vs local repo artifacts), versioning, and the module-status index. **Canonical home of the standards-governance text** (the modules carry content only).
- `docs/standards/security.md` — **(deep)** authN/authZ, secrets, injection/OWASP, supply-chain, privacy/PII, encryption, compliance; ASVS 5.0 / NIST-grounded.
- `docs/standards/maintainability-structure.md` — **(deep)** SOLID, Clean/Hexagonal/Onion layers, design-pattern catalog, code-health/smells/dead-code, type safety.
- `docs/standards/testing.md` — **(deep)** test pyramid, characterization/golden-master, mutation, test-diff review, visual/a11y testing, determinism, coverage.
- `docs/standards/product-ux.md` — **(deep)** IA, design tokens, loading/empty/error states, optimistic UI, perceived perf, ethical engagement, WCAG, objective UX signals.
- `docs/standards/data-and-persistence.md` — **(deep)** indexing, migrations (expand-contract), transactions/isolation, locking, N+1/ORM, soft-deletes, backups.
- `docs/standards/reliability-resilience.md` — *(migrated)* correctness/failure-paths, idempotency, timeouts/retry, circuit-breakers, concurrency, resource lifecycle.
- `docs/standards/performance-efficiency.md` — *(migrated)* algorithmic complexity, caching, DB access, API/network efficiency, memory/streaming, cost.
- `docs/standards/api-and-contracts.md` — *(migrated)* minimal/consistent contracts, idempotency, versioning, pagination, rate-limiting, stable error shapes.
- `docs/standards/observability-ops.md` — *(migrated)* structured logging, metrics/tracing/health, alerting, 12-factor config, env separation, feature flags.
- `docs/standards/accessibility-i18n.md` — *(migrated)* encoding, locale formatting, timezones, translatable strings, RTL (a11y itself lives in `product-ux.md`).
- `docs/standards/docs-traceability.md` — *(migrated)* ARCHITECTURE_TREE currency, DECISIONS, docstrings, onboarding/runbooks, commit/PR narrative.

## .claude/agents/ — specialist role library

- `.claude/agents/plan-reviewer.md` — adversarially critiques a draft plan (Stage 3): soundness, sizing/completeness, risk, YAGNI, harness impact; edits only the plan's Review section.
- `.claude/agents/implementer-architect.md` — implements one approved, spec'd slice to standard in an isolated worktree (Stage 6); lands code + tests + docs with no debt.
- `.claude/agents/architect-reviewer.md` — owns the Verify gate (Stage 7): audits the diff against in-scope `docs/standards/` modules in **solo** mode (small changes) or **synthesizes** lens-reviewer + yagni-sentinel findings in **fan-out** mode; read-only.
- `.claude/agents/product-designer.md` — product/UX discovery + design lens (Stage 1, user-facing work): user, job-to-be-done, flows, states, "what good feels like"; applies `product-ux`, persists to `docs/PRODUCT.md`.
- `.claude/agents/lens-reviewer.md` — audits a **diff (Verify) or an audit-scope (harness-audit)** against ONE named `docs/standards/` module; two modes (Verify-diff / Audit-scope), invoked per-lens in a fan-out; read-only, returns per-dimension findings for the synthesizer.
- `.claude/agents/yagni-sentinel.md` — the anti-over-engineering skeptic: argues a plan/diff is too much (speculative abstraction, premature infra, gold-plating); read-only, returns a cut-list.

## .claude/plans/ — active plans

- `.claude/plans/TEMPLATE.md` — the plan template (Problem / Goals / Approach / Affected files / Risks / Tests / Decomposition / Review / Spec) every plan starts from.
- `docs/archive/2026/0001-build-agentic-dev-harness.md` — *(archived)* the original build plan (slices B1–B6); **superseded by 0002**; moved out of the active tree per the archive convention (safe to delete).
- `.claude/plans/0002-harness-re-architecture.md` — **master plan**: re-architect the harness around three pillars (multi-lens quality catalog · legacy understand→audit→gated-refactor · multi-lens review + product/UX lens) + plugin packaging; **Phase 0 complete**, later phases get sub-plans.
- `.claude/plans/0003-functional-core.md` — **active sub-plan** of 0002: the functional core that makes the harness runnable on a real codebase — `harness-init` (scaffold) + `harness-audit` (→ tiered, tagged, plain-English backlog) as skills; execution rides the existing pipeline (no separate refactor command).

## .claude/ — harness config

- `.claude/settings.json` — Claude Code hooks: PostToolUse(Write) nudge + Stop backstop that run the architecture-tree check.

## .claude-plugin/ — plugin manifest (makes this repo installable)

- `.claude-plugin/plugin.json` — plugin manifest (name `agentic-dev-harness`, version, metadata); exposes the 6 specialist agents via the `agents` field pointing at `.claude/agents/*` (DRY — no duplicate `agents/` dir). Skills live under `skills/`; bundled hooks/gates not yet shipped.
- `.claude-plugin/marketplace.json` — single-plugin marketplace (`name: sh4npeiris`) so `/plugin marketplace add sh4npeiris/claugentic-dev-harness` → `/plugin install agentic-dev-harness@sh4npeiris` works.

## skills/ — harness entry points (the `/harness-` family)

- `skills/harness-init/SKILL.md` — **procedure live (plan 0003 S3):** the 9-step idempotent scaffold (copy the managed set version-stamped, generate ARCHITECTURE_TREE via the gate's file-list, set `INCLUDE_GLOBS`+`STALE_PATTERN`, merge the tree-check hook, write the CLAUDE.md `harness:managed` fence + Current-scope, git-init, seed ROADMAP/DECISIONS, detect+record tooling); every write detect→create-if-absent/merge-in-fence→report, never-clobber. Cold-install dogfood is S5.
- `skills/harness-audit/SKILL.md` — Understand + Audit + Backlog **live & dogfooded** (S2b-ii: real backlog in `docs/ROADMAP.md`). Phase 1 = inline overview + audit-plan; Phase 2 = `lens-reviewer` fan-out (audit-scope mode), dedup, deterministic `(module×dir)` cell resume; Phase 3 = tiered/tagged backlog into the `harness-audit:backlog` fence.

## scripts/ — tooling

- `scripts/check_architecture_tree.py` — deterministic (no-LLM) gate enforcing that this index lists every in-scope source file (presence) and references no deleted file (staleness); `--hook` / `--hook-write` modes wired in `.claude/settings.json`. `INCLUDE_GLOBS`/`STALE_PATTERN` are set per-repo by `harness-init`.
