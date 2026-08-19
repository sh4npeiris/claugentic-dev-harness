# Architecture Tree

> **Locate, don't ingest.** One line per file — your map. Scan/grep it to find the right file, then read THAT file; don't read the whole tree. Keep it current: every file add/move/remove updates this index (commit-time hook enforces presence + staleness — CLAUDE.md → Harness Discipline). **Working target ~150 chars/entry** (what-it-is + when-to-open); **450 is the hard ceiling** (`MAX_ENTRY_CHARS`) — aim small, evict rationale to DECISIONS/INVARIANTS.

Executable code = the gate scripts (`scripts/`) + the Workflow choreography (`engine/` — audit pipeline, Verify panel, QA runtime, build loop; named `engine/` not `workflows/` so the platform never auto-registers them as `[dynamic workflow]` commands). Everything else: harness docs, specialist roles, the plan template, config, and the `eval/` measurement fixtures (runnable, out of gate scope). `INCLUDE_GLOBS` watches only `scripts/**/*.py` + `engine/**/*.js`.

## Root

- `README.md` — the adopter-facing pitch: plugin value, the "addractive" craft headline, the six commands (init · product · audit · build · doctor · condense), install/update, how the pipeline works, honest status.
- `CLAUDE.md` — this repo's agent guidance: engineering principles, harness discipline, workflow + DoD pointers.
- `.gitignore` — open when changing what's tracked: `.claude/*` is ignored with a per-file un-ignore (`agents/`, `plans/`, `settings.json`, `claugentic-doc-budgets.json` — an untracked caps config silently disarms the budget gate).
- `.gitattributes` — line-ending normalization (`* text=auto eol=lf`, scripts forced LF) for a cross-platform plugin.
- `CHANGELOG.md` — adopter-facing release history: current release's changes + a one-line-per-release prior list. Ships; git history is the full archive.
- `LICENSE` — Apache-2.0 (public repo; © 2026 Shan Peiris).
- `pyproject.toml` — open when changing test deps, discovery, or lint scope: the PEP-735 `test` dependency group CI installs from + pytest config (`testpaths`, `integration` marker) + ruff (`extend-exclude=["eval"]`).

## .github/ — CI

- `.github/workflows/ci.yml` — open for CI config: on push/PR to `main` runs pytest (ubuntu+windows, 3.12; deps from the pyproject `test` group), `node --test` (Node 22), and the four gate scripts.
- `.github/workflows/release.yml` — THE publisher: on a `v*` tag re-runs every gate + `claude plugin validate --strict` at the tagged commit, then `build_release.py --apply` → leased `release` push + GitHub Release.

## docs/ — process, standards, and project memory

- `docs/claugentic-WORKFLOW.md` — open for the process + canonical Definition of Done: the 10-stage workflow (`FRAME → APPROVE → BUILD → CLOSE`), gate-list SoT, the tag→discipline table + methodology toolbox, and the plan-disposition / in-flight-scope-split lifecycle.
- `docs/claugentic-ENGINEERING_STANDARDS.md` — thin entry point to the `docs/claugentic-standards/` catalog (the quality bar); per-repo Current-scope added by `init`.
- `docs/claugentic-ARCHITECTURE_TREE.md` — this file: the one-line-per-file index.
- `docs/claugentic-DECISIONS.md` — open FIRST before re-litigating a past choice: the decisions ledger's routing INDEX (one keyword line per shard + the filing rule). Content-free by rule; never append entries here.
- `docs/claugentic-decisions/*.md` — the ledger's per-topic shards the index routes to (honesty · gates · verify-roles · audit · build-mode · workflow-process · roles-review · doc-lifecycle · plugin-distribution · release-contract). Reach them VIA the index, never linked directly.
- `docs/claugentic-ROADMAP.md` — open for the harness's own backlog: two generated fences (`harness-audit:backlog` / `harness-product:backlog`) + durable standing sections outside them (Bugs · Later/Ideas; dismissed findings live in `rejected-findings`).
- `docs/claugentic-CHARTER.md` — the OPTIONAL engineering charter (`init` step-7 create-if-absent from the `_CHARTER.md` seed): a living per-work-type methodology record (record/apply/adapt/grow). **Absent in THIS repo** — the harness follows its default grain.
- `docs/RELEASE_CHECKLIST.md` — the CI-publishes ritual: prepare with `build_release.py --apply --bump <version>`, push one tag, the workflow gates + publishes; red-run recovery, and the honest-scope split (what CI guarantees vs the `[J]` eval-drift/`range-diff`/branch-protection halves).
- `docs/claugentic-PLAYBOOK.md` — open for the non-engineer's driving guide: the pipeline, three leverage points, orchestration patterns, worked example, glossary.
- `docs/diagrams/*.{excalidraw,png}` — README diagrams (Excalidraw source + PNG) that **ship** with the plugin: `harness-usage-flow` (the *Commands* command-map) and `harness-journey` (the *Under the hood* pipeline).
- `docs/claugentic-PRODUCT.md` — open for durable product/UX context (`product-designer` Stage-1 output): user + design language, the per-project design-language (anti-sameness) record, and the Build-mode brief (JTBD, flows, states, UX failure modes).
- `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` — open when editing the product-spec contract: managed template (who-for · JTBD · promise · Features · Acceptance-criteria) carrying the FROZEN JSON schema the audit/qa engines + test pin.
- `docs/claugentic-PLAN_TEMPLATE.md` — open when starting a plan: the managed plan-file contract template (Problem/Goals/Approach/**Architecture-&-holistic-fit** incl. the **felt/visual craft-bar**/Research/Risks/Tests/Review/Spec + Status). Adopters copy one per plan.
- `docs/claugentic-_DECISIONS.md` — the SHIPPED pristine adopter DECISIONS seed (one-time-seed): `init` step 7 copies it → `DECISIONS.md`, underscore stripped, create-if-absent. Blank ledger, no harness content.
- `docs/claugentic-_ROADMAP.md` — the SHIPPED pristine adopter ROADMAP seed (one-time-seed): `init` step 7 copies it → `ROADMAP.md`, underscore stripped, create-if-absent. Intro + empty Later/Ideas, no fences (skills self-create those).
- `docs/claugentic-_CHARTER.md` — the SHIPPED pristine adopter CHARTER seed (one-time-seed): `init` step 7 copies it → `CHARTER.md`, underscore stripped, create-if-absent. Ships nearly-empty (prose header + commented examples).
- `docs/claugentic-PRODUCT_SPEC.md` — the harness's own filled spec (dogfood example): who-for/job/promise, the honest-disclosure invariant, the six command-features + frozen-schema criteria PS-1..PS-7 (all `manual`). User-owned, never stamped.
- `docs/claugentic-INVARIANTS.md` — open before touching an invariant's blast radius: live (non-gate) record of load-bearing invariants — invariant · why · dated provenance. Kept lean.

## docs/claugentic-standards/ — the modular quality catalog

- `docs/claugentic-standards/_TEMPLATE.md` — open to author/audit a module: the module contract (frontmatter schema + per-dimension structure: good / auditor-checks / confidence / tradeoff / sources).
- `docs/claugentic-standards/README.md` — open for standards governance: catalog index + meta-rules (select-don't-skip, additive, novel-patterns), the two-tier model, versioning, module-status index.
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
- `docs/claugentic-standards/docs-traceability.md` — *(migrated)* the docs & traceability lens: explainable change, navigable architecture. The file IS the dimension list — none restated here.

## .claude/agents/ — specialist role library

- `.claude/agents/synthesizer-gate.md` — the GATE (integrate→verdict→loop) at three altitudes: plan-gate (Stage-3, EDITS the plan's Review), verify-verdict (Stage-7, audits test-first independence), audit-synthesis (tiers findings). Clean-context opus; pinned in `engine/{verify,audit}.js`.
- `.claude/agents/implementer.md` — Stage-6 builder (native implement): implements one approved, spec'd slice in an isolated worktree; lands code + tests + docs, no debt; consults the methodology toolbox + charter record and runs red-first when test-first is chosen.
- `.claude/agents/product-designer.md` — product/UX lens, two modes: Discover (Stage-1) surfaces user/JTBD/flows/states; Elevate (spec mode) critiques a draft (forcing functions + craft/feel signature-moment test). Applies `product-ux`, returns durable product truth for the orchestrator to persist to PRODUCT.md.
- `.claude/agents/lens-reviewer.md` — applies ONE lens, five modes: Verify-diff (Stage-7), Audit-scope (passed `depth`), Plan-design (Stage-2b), Whole-scope (the `thorough` cross-cutting red-team sweep), Product-gap (one acceptance criterion, `/product` gap mode). Per-lens fan-out; read-only, per-finding results.
- `.claude/agents/yagni-sentinel.md` — the anti-over-engineering skeptic: argues a plan/diff over-builds (speculative abstraction, premature infra, gold-plating); read-only, returns a cut-list. Also the audit's `thorough`-only prune.
- `.claude/agents/finding-verifier.md` — the audit's refute counterpart: given ONE finding (claim + `file:line`, never the finder's rationale) tries to refute it → Verified/Refuted/Unconfirmed; per-finding after the prune. Read-only, `model: opus`.
- `.claude/agents/honesty-reviewer.md` — the over-claim lens: refutes COPY not code (verb discipline · `[D]`/`[J]` integrity · `cross-model ≠ independent`); on the diverse panel at Plan/Verify on trust surfaces. Read-only, `model: opus`.
- `.claude/agents/runtime-qa.md` — the runs-correct (≠ reads-correct) reviewer: drives the RUNNING app to verify ONE acceptance criterion (Playwright / curl), pushes negative paths. READ-ONLY/non-destructive; spawned at the DRIVE step of `engine/qa.js`.
- `.claude/agents/retrospect-harvester.md` — the Stage-9 ACTIVE harvest: after a slice lands, sweeps the six learning-loop categories over the change and proposes concrete harness-improvement edits. Orchestrator-invoked post-Land; READ-ONLY/proposes.

## .claude/plans/ — in-flight plans

- In-flight plans live here as `NNNN-*.md` until Land, then deleted (git history keeps them). The plan-file contract template is the managed doc `docs/claugentic-PLAN_TEMPLATE.md`.

## .claude/ — harness config

- `.claude/settings.json` — Claude Code settings (currently `{}`; the tree gate moved to the git pre-commit hook, the advisor hook lives plugin-side). See DECISIONS → Tree-gate altitude.
- `.claude/claugentic-doc-budgets.json` — open to change THIS repo's ledger byte caps: the one cap source (the file IS the list — no values restated here); read by the doc-budget gate, pinned byte-exactly by its migration test. Dev-only (`init-gen`) — never ships.
- `.githooks/pre-commit` — open when changing the commit gate: wired via `core.hooksPath=.githooks`, `run_gate <script> [args]` runs each gate once per `git commit` (stdout captured = silent clean pass, stderr flows through, exit 1 aborts); broken git skips silently, no working Python / absent gate script skip loudly. Template twin in `skills/init/SKILL.md` (parity-pinned).

## .claude-plugin/ — plugin manifest (makes this repo installable)

- `.claude-plugin/plugin.json` — open to change the manifest: name/version/metadata; exposes the bundled agents via `agents` → `.claude/agents/*` (DRY — the manifest IS the roster, no count restated here); skills under `skills/`; ships ONE bundled hook (the SessionStart advisor).
- `.claude-plugin/marketplace.json` — single-plugin marketplace (`name: sh4npeiris`) so `/plugin marketplace add sh4npeiris/claugentic-dev-harness` → `/plugin install claugentic-dev-harness@sh4npeiris` works.

## skills/ — harness entry points (the `/claugentic-dev-harness:*` family)

- `skills/init/SKILL.md` — open to change adoption/scaffolding: the 9-step never-clobber upsert (managed docs, tree+globs, pre-commit hook, plugin self-ref, ROADMAP/DECISIONS/CHARTER seeds). Two modes — Shared (committed, default) vs Solo/local-only.
- `skills/audit/SKILL.md` — open to change the audit entry: thin trigger (Understand → invoke `engine/audit.js` → write the backlog between `harness-audit:backlog` markers, replace-only). `thorough` adds blind-spot + yagni-sentinel.
- `skills/build/SKILL.md` — open to change the build go-button: thin layer driving backlog items through the WORKFLOW pipeline, decision-gated (stop only for a fork/trade-off/irreversible); reads BOTH fences into one tier-interleaved worklist.

- `skills/product/SKILL.md` — open to change the product layer: two modes — Spec (product-designer discover → elevate → frozen-schema validate → user-owned PRODUCT_SPEC.md) and Gap (`engine/audit.js` criteria mode → `harness-product:backlog` fence).

- `skills/doctor/SKILL.md` — open for harness-OWN-health (NOT your code — that's audit): runs the gates read-only + plan-scan + init post-conditions (stamped-fence skew · husky-chained wiring · commit-hook interpreter probe) + Stage-9 signal → snapshot → SELECT → treat / roadmap. Owns the caps-config reader-contract.

- `skills/condense/SKILL.md` — open to change the condensation operator: the CANONICAL condensation procedure (classify-first → absorb → promote → merge → trim) WORKFLOW's DoD points at. Proposes a diff, human approves, applies via `/doctor`'s treat. OFFERed on a WARN.

## engine/ — executable choreography (Workflow-tool scripts)

- `engine/verify.js` — open to change the Stage-7 Verify panel: fans one lens-reviewer per in-scope module + yagni-sentinel + honesty-reviewer, then synthesizer-gate synthesis. `finalVerdict` forces CHANGES_REQUIRED on a named-lens no-show. Helpers tested by `verify.test.mjs`.
- `engine/audit.js` — open to change the audit pipeline (FIND→PRUNE→VERIFY): fans lens-reviewer over interleaved `(module×dir)` cells (deterministic resume), one finding-verifier per finding. `thorough` adds blindspot + yagni-sentinel; criteria + `renderOnly` are args modes.

- `engine/build-item.js` — open to change the build-to-green engine: iterates one approved item implement (implementer) → gates (`gatesGreen`, never fail-open) → Verify → QA → fix until green/cap. branches+commits but NEVER lands/pushes/merges; spawns no judge.
- `engine/qa.js` — open to change runtime verification: boot + flow-driving (`boot-only` / `full`). A boot agent probes `appUrl` on a bounded `readinessPlan`; full mode drives one `runtime-qa` per criterion → re-checked by finding-verifier.

## scripts/ — tooling

- `scripts/claugentic-check_architecture_tree.py` — open to change the tree gate: deterministic, checks presence + staleness + the `MAX_ENTRY_CHARS`=450 FORM budget + glob drift; `--staged`/default modes; `INCLUDE_GLOBS` the one per-repo knob.
- `scripts/check_versions_synced.py` — open to change the version-sync gate: `plugin.json` version is SoT; fails loud (exit 1) if `marketplace.json` disagrees or on broken input. DoD run-gate, not hook-wired; files parsed independently.
- `scripts/build_release.py` — SINGLE release BUILD path (local prepare + the workflow's publish): `DEV_ONLY_PATH_CLASSES` drives `classify` (default-include — a file ships by having NO entry); preconditions → build → validate → STOP + print the gated tag-push. Never tags/pushes.
- `scripts/claugentic-check_doc_budgets.py` — open to change the ledger byte-budget MECHANICS (caps are data: `.claude/claugentic-doc-budgets.json`): absent config = no-op, malformed = fail loud, `*`-key = glob, `reportOnly` = graced breach, ≥90% WARN (stderr — the advisory stream the pre-commit wrapper lets through; verdict stays stdout), independent reads. SHIPS + `init`-delivered + hook-chained (0041 S6/S7).
- `scripts/check_shipped_content.py` — shipped-content scanner gate (harness-self): scans the dev checkout, or `--root <tree>` a built/stripped worktree; HARD passes (exit 1) non-ASCII `*.js` · stranded tokens · dangling refs · closure `NEEDS ⊆ HAS`; gate-mention WARN.
- `scripts/claugentic-session-advisor.py` — open to change the SessionStart advisor (not a gate): ONE "where am I / what's next" line + two user-facing currency clauses (docs-behind-plugin skew · landed/cold count, `COLD_DAYS`) whose budget is RESERVED, so overflow truncates the recommendation, never a nudge; `additionalContext` = resume branch only, never the clauses; `CLAUDE_HARNESS_ADVISOR=off` mutes; fail-safe exit 0.

## tests/ — gate test suite

- `tests/test_check_architecture_tree.py` — tests for the tree-check gate (presence, staleness incl. the `.ts/.tsx` regression, `--staged` scope, mode dispatch + exit codes, CWD-independence); hermetic via mocked `_git`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_check_versions_synced.py` — tests for the version-sync gate (synced/drift/missing/garbled/missing-version/independent-read + main() exit codes); hermetic via tmp_path manifests. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_check_doc_budgets.py` — tests for the ledger byte-budget gate (under/at/over, missing/unreadable, independent reads, exit codes) + the config boundary: absent-vs-malformed, glob-by-key, dead-glob skip, subdir WARN, reportOnly, WARN-to-stderr stream contract + the init seed-block parity pin (parses `skills/init/SKILL.md`). *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_precommit_wrapper.py` — runs `.githooks/pre-commit` through real `sh` in a scratch repo (fake gate — plus a REAL-gate real-`git commit` e2e): stub-beside-working Python still gates, absent Python/gate script skip loudly, broken git skips silently, stdout captured vs stderr through, red aborts; plus the init-template parity pin, the husky rules, and the floor/ast pin derived from the hook's call sites. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_decisions_index_agreement.py` — pins `claugentic-DECISIONS.md`'s routing index against `docs/claugentic-decisions/` in BOTH directions (no dead route · no unrouted shard); replaced `check_doc_budgets`'s `REQUIRED_SHARDS`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_build_release.py` — release-builder tests: ship-vs-strip split, stale-base/version-increase/drop-check guards, the `--bump` writer (`TestBumpManifests`) + `TestApplyBumpOrchestration` (the one-command flow: abort · retry · gated-command-not-run). *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_release_workflow.py` — static shape pins for `.github/workflows/release.yml`: `v*` trigger, read-only default + write on `publish` only, `needs: gates`, on-main + tag↔version refusals, the push lease, derived gate parity, CHANGELOG heading contract. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_product_spec_template.py` — pins the FROZEN acceptance-criteria schema: extracts the JSON block from PRODUCT_SPEC_TEMPLATE.md (always) + PRODUCT_SPEC.md (when present), asserting six keys, valid states/check, unique ids. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_check_shipped_content.py` — hermetic tests for the shipped-content scanner: pure cores take an injected `{path: text}` map (no real git/filesystem), pinning the exact literals the gate must catch AND the false-positive classes it must not (slash-command + memory-fence tokens stay CLEAN); git is monkeypatched for the `main()` exit codes incl. fail-loud. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_frontmatter_parses.py` — pins that every shipped skill/agent's YAML frontmatter actually PARSES. Exists because `/build` + `/condense` shipped in 0.4.0/0.4.1/0.5.0 with unparseable `description:` scalars (a bare `: ` reads as a nested mapping key) — the runtime does NOT fail loud: the skill loads with EMPTY metadata and silently drops every field. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_seed_templates.py` — pins the PRISTINE shape of the one-time `_X.md` seeds `init` copies into an adopter (underscore stripped, create-if-absent): blank ledgers carrying no harness-specific content and no generated fences — incl. that the DECISIONS seed carries "Honesty positioning" in NEITHER shape. *(Out of `INCLUDE_GLOBS`.)*
- `tests/conftest.py` — open when an import fails under pytest: puts `scripts/` on `sys.path` + `_load_hyphenated` (importlib loader registering the two `claugentic-`-prefixed scripts under bare names).
- `tests/test_session_advisor.py` — tests for the SessionStart advisor: HARD invariants (silent path, `MAX_LINE_CHARS` cap, fail-safe exit 0), priority order, RETURN branches, currency nudges (skew · `_version_lt` totality · `_is_cold` table · clause-preserving overflow) + the audience-split pin and the foreign-CWD anchor pin (subprocess). *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_shipped_condensation_trigger.py` — inverted regression scan (0038 S1 → 0041 S6): asserts NO shipped file claims the budget-gate WARN is unreachable, nor caveats the gate away with a `check_shipped_content` marker; past-tense history exempted. Sole mechanical custody — docstring states the measured residual. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_adopter_pointer_integrity.py` — three pin CLASSES over adopter-facing pointers (0041 S9, S12b): honesty-pointer reach (no role file cites a heading in neither repo) · WORKFLOW-content pins (adopter note, upstream-URL sole home) · the roles roster's three-way agreement, doc ↔ `git ls-files` ↔ `plugin.json:agents`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/_load-helpers.mjs` — the shared extract-and-eval harness (`loadHelpersFrom`) the four `*.test.mjs` files import: extracts a script's `// --- helpers ---` block + evals via `new Function`. Not collected. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/verify.test.mjs` — `node --test` tests for `engine/verify.js`'s pure helpers: the `KNOWN_MODULES` ⇄ `docs/claugentic-standards/*.md` set-equality pin, the `finalVerdict` presence-assertion, the test-diff-mandates-`testing` rule. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/audit.test.mjs` — `node --test` tests for `engine/audit.js`'s pure helpers: `enumerateCells` (interleaved + resume + blindspot last), `lensCoverage`, `applyPrune`, the fence renderer, `renderOnlyResult`, the criteria seam. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/qa.test.mjs` — `node --test` tests for `engine/qa.js`'s pure helpers: boot (`parseRunArgs`, `readinessPlan`, `bootOutcome`) + flow-driving (`criterionPlan`, `verdictFor`, `applyVerifierVerdicts`). *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/build-item.test.mjs` — `node --test` tests for `engine/build-item.js`'s pure helpers: `gatesGreen`, `qaGreen`, `outOfScopeTier12`, `nextAction`, `residualReport`/`foldResidual`, `maxIterationsFor` + drift fixtures. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/cross-script.test.mjs` — the cross-script drift pin: the copied trust-surface helpers (`MODELS`, `sameModelTag`, `nsAgent`, `parseArgs`, …) stay byte-identical across `engine/{verify,audit,qa,build-item}.js`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/workflows/agent-namespace.test.mjs` — the namespace regression guard (plan 0016): source-level grep asserting every custom-agent spawn in `engine/*.js` is `nsAgent("<role>")` (built-ins stay bare). *(Out of `INCLUDE_GLOBS`.)*

## eval/ — measurement fixtures (not gate-enforced, not vendored)

The harness's runnable targets: `fixture-app/` for runtime verification (`engine/qa.js`), and `fixture-defects/` — the seeded-defect baseline the audit re-takes as a drift detector; **its defects are planted on purpose — never 'fix' them (that disarms the exam)**. *(All `eval/` is OUT of `INCLUDE_GLOBS` — listed for the map, invisible to the gate by design; see INVARIANTS → eval source stays out of gate scope. Deps documented-not-installed; `pyproject testpaths=["tests"]` keeps bare pytest out of `eval/`.)*

**Do not revert the `fixture-defects/` entries below to defect-level detail.** An entry says what the file **is**, never what is planted in it — naming a seed here publishes the exam's answers in the doc every agent reads first, where the manifest's contamination canary (a tracer inside the manifest) cannot see it. `tests/test_eval_key_containment.py` pins the **id** half mechanically; the paraphrase half — describing a planted defect without naming its id — is **model-upheld, and this note is its only guard**. The answers live in `SEED_MANIFEST.md` and, for recorded runs, in `eval/BASELINE.md`'s baseline entries (that file's own no-peeking contract says so).

- `eval/fixture-app/main.py` — the minimal FastAPI list app `engine/qa.js` boots against: `GET /`, `GET`/`POST /api/items`; seeds 3 items unless `FIXTURE_SEED=0`. The typo'd `/api/item` route the broken flow POSTs to 404s on purpose.
- `eval/fixture-app/static/index.html` — the page with two permanent seeded UX defects (DO NOT fix — the run's catch targets): broken add flow (`ux-broken-flow`) + missing empty state (`ux-missing-empty-state`, blank `<ul>` at `FIXTURE_SEED=0`).
- `eval/fixture-app/acceptance-criteria.json` — the FROZEN-schema criteria instance passed as `args.criteria` to a `engine/qa.js` dogfood run: AC-1 broken flow + AC-2 empty state (fail), AC-3/AC-4 pass, AC-5 `manual`.
- `eval/fixture-app/requirements.txt` — the fixture's documented (not vendored) deps: `fastapi`, `uvicorn`.
- `eval/fixture-app/README.md` — open to run the QA fixture: purpose, run command (`uvicorn main:app --app-dir eval/fixture-app --port 8123`), the `FIXTURE_SEED` knob, the seeded-defects section, criteria description.
- `eval/fixture-defects/app/__init__.py` — the seeded-defect fixture's package init (re-exports `connect`/`init_schema`); a stdlib-only task tracker the standard audit re-takes as its drift exam.
- `eval/fixture-defects/app/db.py` — the tracker's sqlite3 data access: `connect`/`init_schema` plus the project-and-task write path and the task/project read queries.
- `eval/fixture-defects/app/handlers.py` — the tracker's request handlers: header auth, task search, per-project task count, status update.
- `eval/fixture-defects/app/service.py` — the tracker's HTML rendering: the task-list fragment and the status-label formatter.
- `eval/fixture-defects/app/client.py` — the tracker's outbound webhook notifier: posts a task-changed event to the configured URL, plus the is-it-configured check.
- `eval/fixture-defects/app/test_tasks.py` — the fixture's own tests over the tracker (status update, list rendering, status label). Never collected by the repo's pytest.
- `eval/fixture-defects/SEED_MANIFEST.md` — the answer key: the ten seeds (`id · module · file · line · expected`) + the canary. MUST NOT be read during a measurement run (out of the audit's `app/`-scoped path on purpose).
- `eval/BASELINE.md` — open before a measurement run for *What this eval is* + *The measurement procedure* (SoT), then **stop: the baseline entries below carry per-seed answer mappings** (its own no-peeking contract). Append-only; the orchestrator fills an entry after each run.
- `tests/test_eval_manifest.py` — the manifest-integrity guard: the seed table parses (10 rows / 2-per-module), every file:line exists, the canary is present, `app/*.py` compiles, bare `pytest --collect-only` finds nothing in `eval/`. *(Out of `INCLUDE_GLOBS`.)*
- `tests/test_eval_key_containment.py` — the answer-key containment pin: no tracked file outside a justified allowlist names a seed id (vocabulary derived from the manifest, corpus from `git ls-files` with a floor). *(Out of `INCLUDE_GLOBS`.)*
