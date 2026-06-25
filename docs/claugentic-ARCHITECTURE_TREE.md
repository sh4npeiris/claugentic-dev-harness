# Architecture Tree

> **Locate, don't ingest.** One line per file — your map. Scan/grep it to find the right file, then read THAT file; don't read the whole tree. Keep it current: every file add/move/remove updates this index (commit-time hook enforces presence + staleness — CLAUDE.md → Harness Discipline). **Working target ~150 chars/entry** (what-it-is + when-to-open); **450 is the hard ceiling** (`MAX_ENTRY_CHARS`) — aim small, evict rationale to DECISIONS/INVARIANTS.

Executable code = the gate scripts (`scripts/`) + the Workflow choreography (`engine/` — audit pipeline, Verify panel, QA runtime, build loop; named `engine/` not `workflows/` so the platform never auto-registers them as `[dynamic workflow]` commands). Everything else: harness docs, specialist roles, the plan template, config, and the `eval/` measurement fixtures (runnable, out of gate scope). `INCLUDE_GLOBS` watches only `scripts/**/*.py` + `engine/**/*.js`.

## Root

- `README.md` — open for the adopter-facing pitch: what the plugin is + its value, the four commands (init · product · audit · build), install/update, how the reviewed pipeline works, honest status.
- `CLAUDE.md` — open for this repo's agent guidance: engineering principles, harness discipline, workflow pointer, DoD pointer to `docs/claugentic-WORKFLOW.md`.
- `.gitignore` — open when changing what's tracked: ignores local junk + build artifacts; shares `.claude/{agents,plans,settings.json}`, ignores only `.claude/settings.local.json`.
- `.gitattributes` — line-ending normalization (`* text=auto eol=lf`, scripts forced LF) for a cross-platform plugin.
- `LICENSE` — Apache-2.0 (public repo; © 2026 Shan Peiris).
- `pyproject.toml` — pytest config (`testpaths=["tests"]` + `integration` marker); open when changing test discovery.

## .github/ — CI

- `.github/workflows/ci.yml` — open for CI config: on push/PR to `main` runs pytest (ubuntu+windows, 3.12), `node --test` (Node 22), and the tree + version-sync gate scripts — the DoD deterministic gates, machine-run.

## docs/ — process, standards, and project memory

- `docs/claugentic-WORKFLOW.md` — open for the process + the canonical Definition of Done: the 10-stage workflow (`FRAME → APPROVE → BUILD → CLOSE`), source of truth for the gate list.
- `docs/claugentic-ENGINEERING_STANDARDS.md` — thin entry point to the `docs/claugentic-standards/` catalog (the quality bar); per-repo Current-scope added by `init`.
- `docs/claugentic-ARCHITECTURE_TREE.md` — this file: the one-line-per-file index.
- `docs/claugentic-DECISIONS.md` — open before re-litigating a past choice: the forward-looking maintainer guide of standing decisions by area (honesty, gates, judges, audit, build, workflow, plugin) + Readiness footer. Condensed (not append-only).
- `docs/claugentic-ROADMAP.md` — open for the harness's own backlog (currently cleared) + the two generated fences (`harness-audit:backlog` / `harness-product:backlog`); adopters generate their own by running the skills.
- `docs/RELEASE_CHECKLIST.md` — open before a release: model-upheld runbook (bump both manifests, eval drift-check, anchor on `origin/main`, `build_release.py --apply` refuses a stale base, `git range-diff` drop-check before the `@release` force-push).
- `docs/claugentic-PLAYBOOK.md` — open for the non-engineer's driving guide: the pipeline, three leverage points, orchestration patterns (fan-out, adversarial-verify, effort dial), worked example, glossary.
- `docs/claugentic-PRODUCT.md` — open for durable product/UX context (`product-designer` Stage-1 output): user + design language, the product-layer/Excellence-pass note, and the Build-mode brief (JTBD, flows, states, UX failure modes, honesty surface).
- `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` — open when editing the product-spec contract: managed template (who-for · JTBD · promise · Features · Acceptance-criteria) carrying the FROZEN JSON schema (`id`/`feature`/`flow`/`expect`/`states`/`check`) the audit/qa engines + test pin.
- `docs/claugentic-PRODUCT_SPEC.md` — the harness's own filled spec (dogfood example): who-for/job/promise, the honest-disclosure invariant, the four command-features + frozen-schema criteria PS-1..PS-5 (all `manual`). User-owned, never stamped/auto-refreshed.
- `docs/claugentic-INVARIANTS.md` — open before touching an invariant's blast radius: live (non-gate) record of load-bearing invariants — invariant · why · dated provenance (sibling to DECISIONS: chose-vs-must-hold). Kept lean.

## docs/claugentic-standards/ — the modular quality catalog

- `docs/claugentic-standards/_TEMPLATE.md` — open to author/audit a module: the module contract (frontmatter schema + per-dimension structure: good / auditor-checks / confidence / tradeoff / sources).
- `docs/claugentic-standards/README.md` — open for standards governance (its canonical home): catalog index + meta-rules (select-don't-skip, additive, novel-patterns), the two-tier model, versioning, module-status index.
- `docs/claugentic-standards/security.md` — **(deep)** authN/authZ, secrets, injection/OWASP, supply-chain, privacy/PII, encryption, compliance; ASVS 5.0 / NIST-grounded.
- `docs/claugentic-standards/maintainability-structure.md` — **(deep)** SOLID, Clean/Hexagonal/Onion layers, design-pattern catalog, code-health/smells/dead-code, type safety.
- `docs/claugentic-standards/testing.md` — **(deep)** test pyramid, characterization/golden-master, mutation, test-diff review, visual/a11y testing, determinism, coverage.
- `docs/claugentic-standards/product-ux.md` — **(deep)** IA, design tokens, loading/empty/error states, optimistic UI, perceived perf, ethical engagement, WCAG, objective UX signals.
- `docs/claugentic-standards/data-and-persistence.md` — **(deep)** indexing, migrations (expand-contract), transactions/isolation, locking, N+1/ORM, soft-deletes, backups.
- `docs/claugentic-standards/reliability-resilience.md` — *(migrated)* correctness/failure-paths, idempotency, timeouts/retry, circuit-breakers, concurrency, resource lifecycle.
- `docs/claugentic-standards/performance-efficiency.md` — *(migrated)* algorithmic complexity, caching, DB access, API/network efficiency, memory/streaming, cost.
- `docs/claugentic-standards/api-and-contracts.md` — *(migrated)* minimal/consistent contracts, idempotency, versioning, pagination, rate-limiting, stable error shapes.
- `docs/claugentic-standards/observability-ops.md` — *(migrated)* structured logging, metrics/tracing/health, alerting, 12-factor config, env separation, feature flags.
- `docs/claugentic-standards/internationalization.md` — *(draft)* encoding, locale formatting, timezones, translatable strings, RTL (accessibility itself lives in `product-ux.md`).
- `docs/claugentic-standards/docs-traceability.md` — *(migrated)* ARCHITECTURE_TREE currency, DECISIONS, docstrings, onboarding/runbooks, commit/PR narrative.

## .claude/agents/ — specialist role library

- `.claude/agents/plan-reviewer.md` — Stage-3 gate: adversarially critiques a draft plan (soundness, sizing, risk, YAGNI, harness impact); edits only the plan's Review section. Structural safeguard (clean-context contract), `model: opus`, opens `RUNNING AS:`.
- `.claude/agents/implementer-architect.md` — Stage-6 builder: implements one approved, spec'd slice to standard in an isolated worktree; lands code + tests + docs, no debt.
- `.claude/agents/architect-reviewer.md` — owns the Stage-7 Verify gate: audits the diff against in-scope standards modules (solo) or synthesizes lens-reviewer + yagni-sentinel (fan-out); read-only, `model: opus`, script runs pinned via `engine/verify.js`.
- `.claude/agents/product-designer.md` — Stage-1 product/UX discovery (user-facing work): user, JTBD, flows, states, "what good feels like"; applies `product-ux`, persists to `docs/claugentic-PRODUCT.md`.
- `.claude/agents/product-critic.md` — the elevate counterpart to product-designer: critiques a draft product spec by method (forcing functions + mandatory premise-challenge), returns adopt/adapt/reject/defer proposals; read-only.
- `.claude/agents/lens-reviewer.md` — audits a diff (Verify) or audit-scope against ONE named standards module; per-lens in a fan-out; Audit-scope reads at the passed `depth` (`focused`/`deep`/`exhaustive`); read-only, returns per-dimension findings.
- `.claude/agents/yagni-sentinel.md` — the anti-over-engineering skeptic: argues a plan/diff over-builds (speculative abstraction, premature infra, gold-plating); read-only, returns a cut-list. Also the audit's `thorough`-only prune.
- `.claude/agents/finding-verifier.md` — the audit's refute counterpart: given ONE finding (claim + `file:line`, never the finder's rationale) tries to refute it → Verified/Refuted/Unconfirmed; per-finding after the prune; structural safeguard, read-only, `model: opus`.
- `.claude/agents/blindspot-reviewer.md` — the `thorough`-only cross-cutting sweep: red-teams the risk no single module-lens owns (emergent smells, seam gaps, systemic issues); always `exhaustive`, FINDS-only (re-checked by finding-verifier), read-only, opus.
- `.claude/agents/honesty-reviewer.md` — the over-claim lens: refutes COPY not code (verb discipline · `[D]`/`[J]` integrity · `cross-model ≠ independent`); bar embedded in the prompt; on the diverse panel at Plan/Verify on trust surfaces; read-only, `model: opus`.

## .claude/plans/ — plan template (active plans land here while in flight)

- `.claude/plans/TEMPLATE.md` — open when starting a plan: the template (Problem/Goals/Approach/Affected-files/Research/Risks/Tests/Decomposition/Review/Spec + Status block). In-flight plans live here as `NNNN-*.md` until Land, then deleted (git history keeps them).

## .claude/ — harness config

- `.claude/settings.json` — Claude Code settings (currently `{}` — the tree gate moved to the git pre-commit hook; the advisor hook lives plugin-side). See DECISIONS → Tree-gate altitude.
- `.githooks/pre-commit` — open when changing the commit gate: wired via `core.hooksPath=.githooks`, runs `claugentic-check_architecture_tree.py --staged` once per `git commit` (exit 1 aborts). See DECISIONS → Tree-gate altitude.

## .claude-plugin/ — plugin manifest (makes this repo installable)

- `.claude-plugin/plugin.json` — open to change the manifest: name/version/metadata; exposes the 10 agents via the `agents` field → `.claude/agents/*` (DRY); skills under `skills/`; ships ONE bundled hook (the SessionStart advisor, `python3 || python` launcher).
- `.claude-plugin/marketplace.json` — single-plugin marketplace (`name: sh4npeiris`) so `/plugin marketplace add sh4npeiris/claugentic-dev-harness` → `/plugin install claugentic-dev-harness@sh4npeiris` works.

## skills/ — harness entry points (the `/claugentic-dev-harness:*` family)

- `skills/init/SKILL.md` — open to change adoption/scaffolding: the 9-step never-clobber upsert (managed docs, tree+globs, pre-commit hook, plugin self-ref, ROADMAP/DECISIONS). Two modes — Shared (committed, default) vs Solo/local-only (kept fully local; git stays clean).
- `skills/audit/SKILL.md` — open to change the audit entry: thin trigger (Understand → invoke `engine/audit.js` → write the backlog between `harness-audit:backlog` markers, replace-only). `thorough` adds blind-spot + yagni-sentinel. Format SoT = `renderBacklogFence`; carries the prose fallback.
- `skills/build/SKILL.md` — open to change the build go-button: thin layer driving backlog items through the WORKFLOW pipeline in checkpoint mode (per-item code/land/irreversible pauses); reads BOTH fences into one tier-interleaved worklist; build-to-green requestable; irreversible hard-stop guardrail.

- `skills/product/SKILL.md` — open to change the product layer: two modes — Spec (product-designer draft → product-critic Excellence pass → frozen-schema validate → user-owned PRODUCT_SPEC.md) and Gap (`engine/audit.js` criteria mode → `harness-product:backlog` fence).

## engine/ — executable choreography (Workflow-tool scripts)

- `engine/verify.js` — open to change the Stage-7 Verify panel: fans one lens-reviewer per in-scope module + yagni-sentinel + honesty-reviewer, dedups gaps, then an architect-reviewer synthesis (`model: MODELS.judge`). Three-state disclosure computed in code; helpers tested by `verify.test.mjs`; gate-watched.
- `engine/audit.js` — open to change the audit pipeline (FIND→PRUNE→VERIFY): fans lens-reviewer over `(module×dir)` cells, then one finding-verifier per finding; returns `renderedBacklog`. `thorough` adds blindspot + yagni-sentinel; criteria mode is an args mode, not a fork. Three-state disclosure block.

- `engine/build-item.js` — open to change the build-to-green engine: iterates one approved item implement (implementer-architect) → gates (`gatesGreen`, never fail-open) → Verify → QA → fix until green/cap. NEVER touches git (every terminal status returns to the orchestrator); spawns no judge.
- `engine/qa.js` — open to change runtime verification: boot + flow-driving (`boot-only` / `full`). A boot agent probes `appUrl` on a bounded `readinessPlan` (failed boot ⇒ a could-not-run finding); full mode drives one agent per criterion → findings re-checked by one finding-verifier. Three-state disclosure block.

## scripts/ — tooling

- `scripts/claugentic-check_architecture_tree.py` — open to change the tree gate: deterministic, checks presence + staleness + the `MAX_ENTRY_CHARS`=450 FORM budget (`_form_violations`) + glob drift; `--staged` (pre-commit scope) + default (manual/CI) modes; `INCLUDE_GLOBS` the one per-repo knob.
- `scripts/check_versions_synced.py` — open to change the version-sync gate: `plugin.json` version is SoT; fails loud (exit 1) if `marketplace.json` disagrees or on broken input. DoD run-gate, not hook-wired; the two files parsed independently.
- `scripts/build_release.py` — open to change the release builder: `classify()` splits tracked files ship-vs-strip (default-include); `--apply` rebuilds a local `release` branch (refuses a stale base via `_dropped_merges`), `--dry-run` prints the split.
- `scripts/check_doc_budgets.py` — open to change the ledger byte-budget gate: flags a managed ledger over its `DOC_BUDGETS` cap (CLAUDE 6K · DECISIONS 60K · ROADMAP 12K · INVARIANTS 20K) + a WARN at ≥90% (`WARN_RATIO`); independent fail-loud reads; exit 1 on breach. Not hook-wired.
- `scripts/claugentic-advisor.py` — open to change the SessionStart advisor (not a gate): derives ONE "where am I / what's next" line; size-capped JSON, agent-facing `additionalContext` ONLY on the resume branch (nudges = `systemMessage` only); `CLAUDE_HARNESS_ADVISOR=off` mutes; fail-safe exit 0.

## tests/ — gate test suite

- `tests/test_check_architecture_tree.py` — tests for the tree-check gate (presence, staleness incl. the `.ts/.tsx` regression, `--staged` scope, mode dispatch + exit codes, CWD-independence); hermetic via mocked `_git`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_check_versions_synced.py` — tests for the version-sync gate (synced/drift/missing/garbled/missing-version/independent-read + main() exit codes); hermetic via tmp_path manifests. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_check_doc_budgets.py` — tests for the ledger byte-budget gate (under/at/over budget, missing/unreadable, independent reads, main() exit codes); hermetic via tmp_path + monkeypatched `DOC_BUDGETS`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_build_release.py` — tests for the release builder: `TestClassify` pins the ship-vs-strip split, `TestBaseAncestryGuard` pins `_dropped_merges` (empty/two-SHAs/missing-ref); hermetic via monkeypatched `_git`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_product_spec_template.py` — pins the FROZEN acceptance-criteria schema: extracts the JSON block from PRODUCT_SPEC_TEMPLATE.md (always) + PRODUCT_SPEC.md (when present), asserting six keys, valid states/check, unique ids. *(Out of `INCLUDE_GLOBS`.)*
- `tests/conftest.py` — open when an import fails under pytest: puts `scripts/` on `sys.path` + `_load_hyphenated` (importlib loader registering the two `claugentic-`-prefixed scripts under bare names, since hyphens aren't valid module ids).
- `tests/test_advisor.py` — tests for the SessionStart advisor: HARD invariants (silent path emits neither key, `MAX_LINE_CHARS` cap, fail-safe exit 0), the recommendation priority order, the RETURN-2/3/6 branches; tmp_path + stubbed `git log`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/_load-helpers.mjs` — the shared extract-and-eval harness (`loadHelpersFrom`) the four `*.test.mjs` files import: extracts a script's `// --- helpers ---` block + evals via `new Function`. Not a `*.test.mjs` (never collected). *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/verify.test.mjs` — `node --test` tests for `engine/verify.js`'s pure helpers (via `_load-helpers.mjs`), incl. the `KNOWN_MODULES` ⇄ `docs/claugentic-standards/*.md` set-equality pin. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/audit.test.mjs` — `node --test` tests for `engine/audit.js`'s pure helpers: `enumerateCells` (blindspot pseudo-cell), `applyPrune` (`missing-test-baseline` never-pruned), `buildVerifierInput` independence, the fence renderer, the criteria seam. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/qa.test.mjs` — `node --test` tests for `engine/qa.js`'s pure helpers: boot (`parseRunArgs` 300s-clamp/could-not-run, `readinessPlan`, `bootOutcome`) + flow-driving (`criterionPlan` manual-never-driven, `verdictFor` precedence, `applyVerifierVerdicts`). *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/build-item.test.mjs` — `node --test` tests for `engine/build-item.js`'s pure helpers: `gatesGreen`, `qaGreen` (couldNotRun), `outOfScopeTier12`, the `nextAction` priority order, `residualReport`/`foldResidual`, `maxIterationsFor` + copied-helper drift fixtures. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/cross-script.test.mjs` — the cross-script drift pin: the copied trust-surface helpers (`MODELS`, `sameModelTag`, `nsAgent`, `parseArgs`, …) stay byte-identical across `engine/{verify,audit,qa,build-item}.js`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/agent-namespace.test.mjs` — the namespace regression guard (plan 0016): source-level grep asserting every custom-agent spawn in `engine/*.js` is `nsAgent("<role>")` (built-ins stay bare). *(Out of `INCLUDE_GLOBS`.)*

## eval/ — measurement fixtures (not gate-enforced, not vendored)

The harness's runnable targets: `fixture-app/` for runtime verification (`engine/qa.js`), and `fixture-defects/` — the seeded-defect baseline the audit re-takes as a drift detector. *(All `eval/` is OUT of `INCLUDE_GLOBS` — listed for the map, invisible to the gate by design; see INVARIANTS → eval source stays out of gate scope. Deps documented-not-installed; `pyproject testpaths=["tests"]` keeps bare pytest out of `eval/`.)*

- `eval/fixture-app/main.py` — the minimal FastAPI list app `engine/qa.js` boots against: `GET /`, `GET`/`POST /api/items`; seeds 3 items unless `FIXTURE_SEED=0`. The typo'd `/api/item` route the broken flow POSTs to 404s on purpose.
- `eval/fixture-app/static/index.html` — the page with two permanent seeded UX defects (DO NOT fix — the run's catch targets): broken add flow (`ux-broken-flow`, 404s the typo route) + missing empty state (`ux-missing-empty-state`, blank `<ul>` at `FIXTURE_SEED=0`).
- `eval/fixture-app/acceptance-criteria.json` — the FROZEN-schema criteria instance passed as `args.criteria` to a `engine/qa.js` dogfood run: AC-1 broken flow + AC-2 empty state (fail), AC-3/AC-4 pass, AC-5 `manual` (never driven).
- `eval/fixture-app/requirements.txt` — the fixture's documented (not vendored) deps: `fastapi`, `uvicorn`.
- `eval/fixture-app/README.md` — open to run the QA fixture: purpose, run command (`uvicorn main:app --app-dir eval/fixture-app --port 8123`), the `FIXTURE_SEED` knob, the seeded-defects section (must-not-fix), criteria description.
- `eval/fixture-defects/app/__init__.py` — the seeded-defect fixture's package init (re-exports `connect`/`init_schema`); a stdlib-only task tracker the standard audit re-takes as its drift exam.
- `eval/fixture-defects/app/db.py` — sqlite3 data access; carries the two data-and-persistence seeds (DP-1 no-transaction, DP-2 N+1). *(Seeded on purpose — see SEED_MANIFEST.)*
- `eval/fixture-defects/app/handlers.py` — request handlers; carries SEC-1 (f-string SQL), SEC-2 (hardcoded token), REL-1 (`except: pass`), MAINT-2 (divergent `STATUSES`). *(Seeded on purpose.)*
- `eval/fixture-defects/app/service.py` — the HTML-rendering service; carries MAINT-1 (one function parses+queries+formats) + the other half of MAINT-2. *(Seeded on purpose.)*
- `eval/fixture-defects/app/client.py` — outbound webhook notifier; carries REL-2 (`urlopen` no-timeout in an unbounded retry loop). *(Seeded on purpose.)*
- `eval/fixture-defects/app/test_tasks.py` — the fixture's own tests; carries TEST-1 (asserts nothing) + TEST-2 (patches the function under test). Never collected by the repo's pytest. *(Seeded on purpose.)*
- `eval/fixture-defects/SEED_MANIFEST.md` — the answer key: the ten seeds (`id · module · file · line · expected`) + the canary. MUST NOT be read during a measurement run (out of the audit's `app/`-scoped path on purpose).
- `eval/BASELINE.md` — open before a measurement run: what the eval is (drift detector), the measurement procedure (SoT), the append-only baseline-entries table the orchestrator fills.
- `tests/test_eval_manifest.py` — the manifest-integrity guard: the seed table parses (10 rows / 2-per-module), every file:line exists in range, the canary is present, `app/*.py` compiles, bare `pytest --collect-only` finds nothing in `eval/`. *(Out of `INCLUDE_GLOBS`.)*
