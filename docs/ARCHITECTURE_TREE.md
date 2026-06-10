# Architecture Tree

> **Read this first.** This is the one-line-per-file index of the repo — your map. Use it to find the right file instead of reading the whole tree. Keep it current: every file add/move/remove updates this index (a hook enforces presence + staleness — see CLAUDE.md → Harness Discipline). Descriptions are authored by you/the agent that touches the file.

This repo builds the **`claugentic-dev-harness`** Claude Code plugin. The only executable code is `scripts/check_architecture_tree.py`; everything else is harness docs, specialist roles, the plan template, and config.

## Root

- `README.md` — what `claugentic-dev-harness` is + the concrete value it delivers (the two commands), how it installs, how it works (init → audit → reviewed pipeline), and an honest status section.
- `CLAUDE.md` — lean, generalized guidance for agents working in THIS repo: engineering principles, harness discipline, workflow pointer, Definition of Done.
- `.gitignore` — ignores local junk + build artifacts; **shares** `.claude/agents/`, `.claude/plans/`, `.claude/settings.json` (ignores only `.claude/settings.local.json`).
- `.gitattributes` — normalizes line endings (`* text=auto eol=lf`; scripts forced LF) for a cross-platform plugin.
- `LICENSE` — Apache License 2.0 (the repo is public; © 2026 Shan Peiris).
- `pyproject.toml` — minimal pytest config (`testpaths=["tests"]`) so `python -m pytest` runs the gate's test suite.

## docs/ — process, standards, and project memory

- `docs/WORKFLOW.md` — the staged agent development workflow (Triage → Discuss → Plan → Review → Spec → Approve → Implement → Verify → Land → Retrospect); source of truth for process.
- `docs/ENGINEERING_STANDARDS.md` — thin entry point pointing to the `docs/standards/` catalog (the real quality bar); the per-repo Current scope is added by the `init` skill.
- `docs/ARCHITECTURE_TREE.md` — this file: one-line-per-file index of the repo.
- `docs/DECISIONS.md` — dated, one-line records of non-trivial decisions (newest at top); consult before re-litigating.
- `docs/ROADMAP.md` — backlog of substantial work; tangents land here, never silently into the current change.
- `docs/PLAYBOOK.md` — plain-English guide for a non-engineer driving the harness: the pipeline, your three leverage points, the orchestration patterns (fan-out, adversarial-verify, effort dial), a worked example, and a mini-glossary.

## docs/standards/ — the modular quality catalog

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
- `docs/standards/internationalization.md` — *(draft)* encoding, locale formatting, timezones, translatable strings, RTL (accessibility itself lives in `product-ux.md`).
- `docs/standards/docs-traceability.md` — *(migrated)* ARCHITECTURE_TREE currency, DECISIONS, docstrings, onboarding/runbooks, commit/PR narrative.

## .claude/agents/ — specialist role library

- `.claude/agents/plan-reviewer.md` — adversarially critiques a draft plan (Stage 3): soundness, sizing/completeness, risk, YAGNI, harness impact; edits only the plan's Review section.
- `.claude/agents/implementer-architect.md` — implements one approved, spec'd slice to standard in an isolated worktree (Stage 6); lands code + tests + docs with no debt.
- `.claude/agents/architect-reviewer.md` — owns the Verify gate (Stage 7): audits the diff against in-scope `docs/standards/` modules in **solo** mode (small changes) or **synthesizes** lens-reviewer + yagni-sentinel findings in **fan-out** mode; read-only.
- `.claude/agents/product-designer.md` — product/UX discovery + design lens (Stage 1, user-facing work): user, job-to-be-done, flows, states, "what good feels like"; applies `product-ux`, persists to `docs/PRODUCT.md`.
- `.claude/agents/lens-reviewer.md` — audits a **diff (Verify) or an audit-scope (the `audit` skill)** against ONE named `docs/standards/` module; two modes (Verify-diff / Audit-scope), invoked per-lens in a fan-out; in Audit-scope reads at the orchestrator-passed **`depth`** (`focused`/`deep` — the dial's only lever, never which lenses run); read-only, returns per-dimension findings for the synthesizer.
- `.claude/agents/yagni-sentinel.md` — the anti-over-engineering skeptic: argues a plan/diff is too much (speculative abstraction, premature infra, gold-plating); read-only, returns a cut-list.
- `.claude/agents/finding-verifier.md` — the audit's adversarial-verify counterpart to `lens-reviewer`: given ONE surfaced audit finding (claim + `file:line`, never the finder's rationale), independently reads the cited code and tries to **refute** it → `Verified` / `Refuted` / `Unconfirmed`; invoked on **every** finding the audit is about to surface (all tiers, every dial level), after the prune; read-only, opus. A false-confidence reduction, not a deterministic gate.

## .claude/plans/ — plan template

- `.claude/plans/TEMPLATE.md` — the plan template (Problem / Goals / Approach / Affected files / Risks / Tests / Decomposition / Review / Spec) every plan starts from. Completed plans are not kept here — they live in git history.

## .claude/ — harness config

- `.claude/settings.json` — Claude Code hooks: PostToolUse(Write) nudge + Stop backstop that run the architecture-tree check.

## .claude-plugin/ — plugin manifest (makes this repo installable)

- `.claude-plugin/plugin.json` — plugin manifest (name `claugentic-dev-harness`, version, metadata); exposes the 7 specialist agents via the `agents` field pointing at `.claude/agents/*` (DRY — no duplicate `agents/` dir). Skills live under `skills/`; bundled hooks/gates not yet shipped.
- `.claude-plugin/marketplace.json` — single-plugin marketplace (`name: sh4npeiris`) so `/plugin marketplace add sh4npeiris/claugentic-dev-harness` → `/plugin install claugentic-dev-harness@sh4npeiris` works.

## skills/ — harness entry points (the `/claugentic-dev-harness:*` family)

- `skills/init/SKILL.md` — the 9-step idempotent scaffold (copy the managed set version-stamped, generate ARCHITECTURE_TREE via the gate's file-list, set `INCLUDE_GLOBS`, merge the tree-check hook, write the CLAUDE.md `harness:managed` fence + Current-scope, git-init, seed ROADMAP/DECISIONS, detect+record tooling); every write detect→create-if-absent/merge-in-fence→report, never-clobber.
- `skills/audit/SKILL.md` — Understand + Audit + Backlog. Phase 1 = inline overview + audit-plan; Phase 2 = one uniform **FIND → PRUNE → VERIFY → surface** pipeline at every level — **auto-dial sized from Phase 1** (named level overrides) scales only **depth-per-lens** (`quick`=`focused` / `standard`=`deep`; `thorough` honestly deferred), `lens-reviewer` fan-out (audit-scope mode) auditing each `(module×dir)` cell **once**, dedup, **YAGNI prune**, then an **attempt to re-check every surfaced finding (all tiers) via `finding-verifier`**, deterministic resume + one shared budget cap; Phase 3 = tiered/tagged backlog into the `harness-audit:backlog` fence with **one verification tag per item** (+ the not-a-guarantee legend caveat) + the **"architecturally sound" terminal signal** when Tier 1/2 are empty.

## scripts/ — tooling

- `scripts/check_architecture_tree.py` — deterministic (no-LLM) gate enforcing that this index lists every in-scope source file (presence), references no deleted file (staleness), and **detects glob drift** (flags — does not auto-fix — when `INCLUDE_GLOBS` watches no files while the repo contains non-harness-managed source, the zero-coverage rot); `--hook` / `--hook-write` modes wired in `.claude/settings.json`. `INCLUDE_GLOBS` is the only per-repo knob for presence/staleness (set by `init`); the valid-extension set `EXTS` is derived from it. Drift detection uses a separate, stable `SOURCE_EXTS` allow-list + the `claugentic-dev-harness@` managed-stamp exclusion (no per-repo knob).

## tests/ — gate test suite

- `tests/test_check_architecture_tree.py` — characterization tests for the tree-check gate (presence, staleness incl. the `.ts/.tsx` regression, mode dispatch + exit codes, `--hook-write` stdin); hermetic via mocked `_git`. *(Out of `INCLUDE_GLOBS` — listed for the map, not gate-enforced.)*
- `tests/conftest.py` — puts `scripts/` on `sys.path` so the gate imports as a module under pytest.
