# 0002 — Harness Re-Architecture: Three Pillars + Product Lens (Master Plan)

- **Status:** Draft (rev 2 — refinements integrated) — awaiting plan-review (Stage 3) + user approval (Stage 5)
- **Supersedes:** [`0001-build-agentic-dev-harness.md`](0001-build-agentic-dev-harness.md) — its build slices **B1–B6 fold into Phases 2–7** here (the plugin packages the *enriched* harness).
- **Roadmap item:** `docs/ROADMAP.md` (re-laid-out around these phases on approval).
- **References:** `docs/WORKFLOW.md` · `docs/ENGINEERING_STANDARDS.md` · `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · plan `0001`.

> **Master/umbrella plan.** Defines the vision, architecture, and full phase roadmap; **only Phase 0 is fully sliced.** Later phases are at altitude and get their own sub-plan (`0003+`) when reached — slice just-in-time (YAGNI applied to planning itself).

---

## Decisions locked this session (2026-06-04, see `docs/DECISIONS.md`)

1. **Re-scope into this master plan** — package the *enriched* harness, not the skeleton.
2. **Standards → full multi-lens catalog, scoped modules**, anchored to **ISO/IEC 25010:2023**; high-value subset → **executable fitness-function gates**.
3. **Learning loop = two tiers** *(refined):* **(a) global standards catalog** grows and **syncs across all repos** via the plugin (`/harness-update`); **(b) codebase-specific lessons** stay local and never propagate. The *local* loop is lightweight/manual now; the global catalog is versioned and syncable. Mechanized auto-distillation is designed-but-deferred.
4. **Product/UX lens now** — `product-designer` role, `ux-reviewer` + lens reviewers, a `product-ux` standards module, a product-discovery stage writing to **`docs/PRODUCT.md`**, and **run-and-observe verification** with objective UX signals.
5. **Catalog carries technology/capability modules** *(new):* Redis/caching, message queues/streams, object storage/CDN, third-party APIs, sidecars, ML/inference, search — *when-to-introduce + how-to-do-it-right + safety rails.*
6. **Not Python-centric** *(new):* harness tooling/gates reimplemented in **Node/JS** (first real target is a JS app); `check_architecture_tree` ports to Node in the gates phase. Gates are language-agnostic where possible.

---

## Problem (re-scoped)

The harness today is a **strong skeleton on genuine white-space**, but key organs aren't wired up, and the plugin we were about to build (0001) would package the thin version permanently:

1. **Learning loop is prose, not a mechanism** — no artifact, trigger, gate, or distribution model. And the two tiers are conflated: *global* standards (should sync everywhere) vs *local* lessons (should stay put).
2. **`ENGINEERING_STANDARDS` is ~40% of the catalog and structured not to scale** — ~17 flat rows in one always-loaded file; missing architectural **layers**, **styles**, **product/UX**, **code-health/housekeeping**, a **design-pattern** catalog, **data/DB** depth, and **technology/capability** guidance (how to *introduce* Redis, queues, storage, third-party APIs, sidecars, ML — the core of modernizing a vibe-coded app).
3. **No product / UX / look-and-feel lens** — no product-discovery, no design pass, no UX reviewer, no way to verify delight (you must run the app), and no durable product-context artifact.
4. **No cheap way to *understand* an existing codebase** before auditing (no derived dependency/symbol map).
5. **Review is one agent wearing all hats** — weaker than fanning out single-lens specialists with adversarial verification, and with no **effort dial** it would gold-plate every change (violating our own KISS/YAGNI).

> **Purpose clarified.** The harness's primary job is **not** rewriting legacy into new languages (though it could). It's to take a **recently vibe-coded app** and (a) bring it to a standard that passes any code review, **and** (b) **introduce appropriate modern technology** (caching, async messaging, proper storage, third-party integrations, sidecars, ML) — safely and incrementally.

## Vision

A self-improving Claude Code harness that lets a technically-literate non-engineer co-build software that **passes any code review and is a pleasure to use** — combining three things almost no harness does, and none do together (verified vs BMAD, spec-kit, Agent OS, SuperClaude, claude-flow, Cline, Cursor, Aider):

- **Pillar A — A multi-lens quality + capability catalog** ("what good looks like, and what tech to bring in"): ISO-25010-anchored, scoped-modular, ever-growing, **globally synced**; machine-checkable subset enforced as fitness functions.
- **Pillar B — Apply it to existing code, safely**: understand → bounded multi-lens audit → prioritized tiered backlog with **two tracks** (behavior-preserving *refactors* and new-capability *upgrades*) → gated, characterization-first or migration-safe execution. Never a bulk rewrite.
- **Pillar C — Multi-lens review incl. a product/UX lens** ("as if the world's best team built it"): fan-out specialist reviewers with adversarial verification and an **effort dial**, a product-discovery stage, and run-and-observe verification with objective UX signals.

Distributed as an installable plugin; a **two-tier knowledge model** keeps global standards syncing everywhere while codebase-specific lessons stay local.

## Goals / Non-goals

**Goals**
- Restructure + expand `ENGINEERING_STANDARDS` into a scoped, ISO-25010-anchored modular catalog (`docs/standards/`) incl. **technology/capability** modules; loaded by relevance; **versioned + globally syncable**.
- **Deterministic fitness-function gates** (Node/JS) for the machine-checkable subset.
- A **product/UX lens**: roles, a `product-ux` module, pipeline stages, `docs/PRODUCT.md`, run-and-observe verification with objective signals.
- **Multi-lens fan-out review** with adversarial verification + an **effort dial**; **judge-panel** design exploration at Plan.
- Legacy on-ramp: `/harness-understand` → `/harness-audit` (two-track backlog) → gated refactor / migration-safe upgrade.
- Package the enriched harness as a plugin; `init-harness` idempotently scaffolds it, **`git init`s if needed, and composes with the repo's existing tooling** (eslint/tsc/vitest, etc.).
- **Two-tier learning:** global standards versioned + syncable (`/harness-update`); local lessons stay in the repo. Local loop manual now; mechanized loop reserved.
- A lightweight **per-repo quality scorecard** (ISO-25010 maturity + backlog burndown) so progress is visible.

**Non-goals**
- Bulk / automatic refactor; editing target *code* on init; building the mechanized auto-distillation loop now; language lock-in (gates are Node but stack-agnostic in intent); over-speccing distant phases.

## Architecture — three pillars + cross-cutting tracks

### Pillar A — The Multi-Lens Quality + Capability Catalog
- `docs/ENGINEERING_STANDARDS.md` becomes a **thin index + meta-rules** (additive, select-don't-skip, per-change relevance, may-invent-a-justified-novel-pattern, the Current-scope mechanism) pointing to **`docs/standards/` modules**, each loaded only when a slice touches it (keyword/glob-scoped — Cursor's lesson) so the catalog can grow huge without bloating context.
- **Backbone = ISO/IEC 25010:2023** nine characteristics, so the taxonomy is recognized, not ad-hoc.
- **Quality modules (≈12):** `security` · `reliability-resilience` · `performance-efficiency` (incl. caching) · `maintainability-structure` (SOLID, layering, patterns, code-health/smells/dead-code) · `architecture-styles` (mono↔modular↔micro↔event↔serverless↔CQRS/ES, headless/BFF — when-to-use tradeoffs) · `data-and-persistence` · `api-and-contracts` · `observability-ops` (logs/traces/metrics, 12-factor, deploy) · `product-ux` (IA, design tokens, states, optimistic UI, perceived perf, micro-interactions, ethical engagement, look-and-feel) · `accessibility-i18n` · `testing` · `docs-traceability`.
- **Technology / capability modules** *(new family, `docs/standards/capabilities/`):* `caching-infra` (Redis: cache-aside/write-through, TTL, stampede, sessions) · `messaging` (queues/streams; async decoupling; outbox; idempotent consumers; ordering/DLQ) · `object-storage` (blob/S3/CDN; signed URLs; stop storing files in the DB) · `third-party-apis` (resilient clients, rate limits, webhooks, secrets, treat responses as untrusted) · `sidecars` (proxy/observability/auth offload) · `ml-inference` (model serving, eval, drift, cost) · `search` (full-text/vector). Each: **when-to-introduce + how-to-do-it-right + tradeoffs + safety rails.**
- **Versioning + global sync:** each module carries a version; the plugin is the **single source of truth**; `init-harness` brings them in and `/harness-update` re-syncs newer versions (merge, never clobber local Current-scope/lessons).

### Pillar B — Understand → Audit → Two-Track Backlog → Gated Execution
- **`/harness-understand`** — derive a cheap mental model (dependency/symbol map, hotspots; optional C4-style diagram via the excalidraw skill for the human) to seed the audit instead of exploring blindly.
- **`/harness-audit`** — bounded, multi-lens, multi-modal sweep (parallel subagents; budget + directory bounded; dedup; **loop-until-dry**) → a **prioritized, tiered backlog** in `docs/ROADMAP.md`, each finding mapped to a catalog dimension. Untested code → item #1 = **"establish a test baseline."**
- **Two backlog tracks:**
  - **Refactor items** (behavior-preserving) → `refactor-item` workflow: **characterization-tests-first** → refactor in isolated worktree → multi-lens review → verify behavior unchanged → land.
  - **Capability-upgrade items** (introduce new tech — *not* behavior-preserving) → the **feature pipeline** (product-discovery first), with **upgrade safety rails**: feature-flag the new path, dual-write/shadow where data moves, explicit migration + **rollback** plan, observability on the new dependency. Never a silent swap.

### Pillar C — Multi-Lens Review + the Product/UX Lens
- **Role library 3 → fuller set:** add `product-designer` (discovery), `ux-reviewer`, and parallel **lens reviewers** (`security`, `performance`, `data`, `resilience`, `accessibility`); existing `architect-reviewer` becomes the **synthesizer** over their findings. **Adversarial verify:** a skeptic tries to *refute* each finding to kill false positives.
- **Effort dial** *(new):* review depth scales with risk/scope (`light` → `standard` → `deep` → `ultra`) and lenses are **relevance-gated** — don't fan out 8 reviewers on a one-line change. Keeps the harness from gold-plating (honours KISS/YAGNI).
- **Pipeline additions:** a **product-discovery stage** *before* the technical plan (user, jobs-to-be-done, flows, what "delight" means, empty/error/loading states) writing to a durable **`docs/PRODUCT.md`**; a **design pass**; **fan-out review** at Verify; **run-and-observe verification** for user-facing slices — launch the app, screenshot, a11y tree, and **objective UX signals** (Lighthouse perf, a11y score, Nielsen-heuristic critique, CLS/LCP) via the Playwright/preview MCPs + `/verify`,`/run`.
- **Judge-panel** at Plan for non-trivial design forks: N independent approaches → score → synthesize best-of (mechanizes "evaluate possibilities, take the best of all").

### Cross-cutting 1 — Plugin Packaging (folds in 0001)
- `.claude-plugin/plugin.json` manifest (schema **verified vs official docs first**), exposing agents + commands + skills. `init-harness` (idempotent; **`git init` if absent**; **detects + composes with the repo's existing lint/type-check/test tooling** rather than imposing its own; language-detected check globs; never clobber), `harness-understand`, `harness-audit`. Marketplace package + cold-install dogfood. **Tooling/gates are Node/JS.**

### Cross-cutting 2 — Two-Tier Knowledge & the Learning Loop
- **Tier 1 — Global standards (sync everywhere):** the `docs/standards/` catalog lives in the plugin, is versioned, and reaches every repo via install/`harness-update`. A lesson promoted here improves *all* projects.
- **Tier 2 — Local lessons (stay put):** codebase-specific conventions, gotchas, decisions → the repo's `CLAUDE.md` / `DECISIONS.md` / `ENGINEERING_STANDARDS` **Current-scope**. Never propagate.
- **The loop (manual now):** after a slice lands, the orchestrator **proposes candidate lessons**, tags each *global* or *local*, and the **user approves**; approved global ones become catalog-module edits (promotable upstream), local ones append to repo memory.
- **Reserved (deferred):** mechanized distillation — a `retrospector` agent + a `Lesson` artifact format + a promotion/`harness-update` sync flow.

### Cross-cutting 3 — Visibility: the quality scorecard
- A lightweight per-repo **`docs/SCORECARD.md`** (or a ROADMAP section): which ISO-25010 dimensions are at what maturity, and backlog burndown — so a non-engineer can see "how close to world-class" and watch it improve (ties to the scientific-method/Dunning-Kruger framing).

## Phase roadmap

| Phase | Theme | Folds in | Detail |
|---|---|---|---|
| **0** | **Foundation enrichment** — catalog (incl. capability modules), roles, workflow, PRODUCT.md, scorecard | — | **Sliced below** |
| **1** | **Fitness-function gates (Node/JS)** — port the tree check; add complexity/dup/dead-code/layering/secret/coverage gates | — | Sub-plan `0003` |
| **2** | **Plugin shell + manifest** (packages the enriched harness) | 0001 B1 | Sub-plan |
| **3** | **`understand` + `audit` workflows** (two-track backlog) | 0001 B2 | Sub-plan |
| **4** | **`refactor-item` + capability-upgrade** workflows | 0001 B3 | Sub-plan |
| **5** | **`init-harness` command** (git-init, compose-with-tooling) | 0001 B4 | Sub-plan |
| **6** | **Command/skill wiring + `harness-update`** | 0001 B5 | Sub-plan |
| **7** | **Package & dogfood** (cold install → the user's JS app) | 0001 B6 | Sub-plan |

## Phase 0 — detailed slices

Each lands **complete in one ≤1M-context session, no debt** (docs + `ARCHITECTURE_TREE` + `DECISIONS` updated, gates green). **S2–S6 are independent modules → fan out in parallel** (the harness dogfooding itself).

- [ ] **P0-S1 — Catalog structure + ISO-25010 backbone + migrate existing dimensions + document the two-tier model.** Create `docs/standards/`; turn `ENGINEERING_STANDARDS.md` into the thin index + meta-rules; migrate the 17 dimensions into grouped modules; define module versioning + the global/local split. *Lands:* no content lost, index resolves, meta-rules intact.
- [ ] **P0-S2 — Quality modules: `security`, `maintainability-structure` (incl. code-health/housekeeping), `testing`.**
- [ ] **P0-S3 — Architectural modules: `layers` (Clean/Hex/Onion) + `architecture-styles` + design-pattern catalog.**
- [ ] **P0-S4 — `product-ux` + `accessibility-i18n`** (incl. defining the objective UX signals the UX reviewer will produce).
- [ ] **P0-S5 — Remaining quality modules: `performance-efficiency` (caching), `observability-ops`, `reliability-resilience`, `data-and-persistence`, `api-and-contracts`.**
- [ ] **P0-S6 — Capability modules: `caching-infra`, `messaging`, `object-storage`, `third-party-apis`, `sidecars`, `ml-inference`, `search`** (when-to-introduce + safety rails).
- [ ] **P0-S7 — Role library expansion.** `product-designer`, `ux-reviewer`, lens reviewers (`security`/`performance`/`data`/`resilience`/`accessibility`); model per CLAUDE.md (Sonnet for mechanical lenses, Opus where judgment-heavy). Record in DECISIONS.
- [ ] **P0-S8 — Workflow upgrade + scaffolding artifacts.** Add product-discovery (→ `docs/PRODUCT.md`) + design pass + fan-out review w/ effort dial + adversarial verify + run-and-observe + judge-panel + the manual two-tier learning-loop touchpoint; create `docs/PRODUCT.md` + `docs/SCORECARD.md` templates; update `CLAUDE.md` pointers (index, don't duplicate).

## Later phases (at altitude — own sub-plans)

- **Phase 1 (gates, Node):** port `check_architecture_tree` to Node; add gates for complexity, duplication, dead-code, **layering/import-boundary (dependency direction)**, secret-scan, coverage-floor — wired via hooks; language-agnostic where possible.
- **Phases 2–7:** as 0001's B1–B6 over the enriched harness; `understand` + two-track execution + `harness-update` added.

## Risks & mitigations

- **Catalog bloats review context** → scoped modules loaded by relevance (Pillar A core).
- **Harness gold-plates every change** → **effort dial + relevance-gated lenses** (Pillar C); respect KISS/YAGNI explicitly.
- **Scope explosion** → phase + sub-plan structure; only Phase 0 sliced; each slice session-sized, lands complete.
- **Capability-upgrades break a live app** → upgrade safety rails (flag, dual-write/shadow, migration + rollback, observability); upgrades go through the *feature* pipeline, not refactor-item.
- **Global sync clobbers local additions** → versioned modules; `harness-update` merges; local lessons live in separate repo-owned files (two-tier model).
- **Plugin manifest schema unknown** → verify vs official docs before Phase 2; validate it loads.
- **Audit blows budget on huge repos** → bounded + dedup + prioritize + loop-until-dry; fan out to subagents.
- **Refactoring untested code changes behavior** → characterization-tests-first mandatory; baseline is item #1.
- **Over-engineering the learning loop** → kept manual now; mechanization reserved.

## Test & dogfood strategy

- **Dogfood on this repo itself** (it builds with its own harness); the architecture-tree check stays green (Python here until the Node port ships).
- **Gates (Phase 1)** ship with tests + self-check.
- **Cold install (Phase 7):** packaged plugin into a **throwaway repo**, `/init-harness` → `/harness-understand` → `/harness-audit` end-to-end.
- **Real-repo dogfood (Phase 7, final):** the full on-ramp on **the user's JS app**; acceptance = audit reproduces its known tiered backlog and one refactor/upgrade lands with suites green.

## Affected files (new/changed across phases)

- `docs/standards/**` (new module tree) · `docs/ENGINEERING_STANDARDS.md` (→ thin index) · `docs/PRODUCT.md` (new) · `docs/SCORECARD.md` (new) · `.claude/agents/*` (new roles) · `docs/WORKFLOW.md` (stages) · `CLAUDE.md` (pointers) · `.claude-plugin/plugin.json` (new) · `commands/*` (new) · `scripts/check_architecture_tree.*` (Python → Node) · `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · `docs/ROADMAP.md`.

## Open decisions

1. **Dogfood target** — confirmed: a **JS app** the user will provide at Phase 7 (replaces 0001's DistrictSync bar). Git-backed?
2. **Module depth in Phase 0** — author **all** modules (incl. capability family, S2–S6) now, or just the high-frequency ones and defer the rest?
3. **Scorecard home** — standalone `docs/SCORECARD.md` vs a section in `ROADMAP.md`?

---

## Review  _(filled by plan-reviewer, Stage 3 — 2026-06-04)_

**Verdict: CHANGES REQUIRED.** The vision, two-pillar split, and "slice-only-Phase-0" discipline are sound and well-argued, and deferring later phases to sub-plans correctly applies YAGNI-to-planning. But Phase 0's slicing **fails the sizing gate** in three places, the "S2–S6 are independent → fan out in parallel" claim **overstates independence** (they depend on an S1 output the plan never names), and the knowledge-sync model is **internally contradictory** (local lessons edit global modules, yet sync must "never clobber local edits"). Fix the items below and re-review; most are plan-text changes, not redesign.

### Required changes

1. **Name the S1 module template/contract and gate S2–S6 on it.** Line 109 claims "S2–S6 are independent modules → fan out in parallel," but every module S2–S6 authors must conform to a shared module *contract* (front-matter: `version`, ISO-25010 mapping, relevance-load scope = keyword/globs per line 63, and for capabilities the when-to-introduce/safety-rail section shape per line 66). That contract is an **S1 deliverable** (line 111 already gives S1 "define module versioning + the global/local split" but omits the template). So S2–S6 are independent **of each other** but **hard-dependent on S1**. Restate as: *"S1 produces the module template/contract + versioning scheme + ISO-25010 mapping table; S2–S6 fan out in parallel **only after S1 lands**, each conforming to that template."* Add the template artifact to S1's "Lands" line.

2. **Split S1 — it bundles a design-lock task with a bulk-migration task.** S1 currently = (a) restructure to `docs/standards/` + convert `ENGINEERING_STANDARDS.md` to thin index + **migrate 17 dimensions** (verification-heavy, content-loss-sensitive mechanical work — the 17 count is correct, verified against `docs/ENGINEERING_STANDARDS.md:17-33`) **and** (b) **design** the versioning scheme + two-tier model + the module template/contract (a decision task S2–S6 block on). Mixing them risks the migration eating the session before the contract is locked. Split into **S1a — contract/template + versioning + two-tier model + ISO-25010 mapping** (the thing S2–S6 consume; lands as `docs/standards/_TEMPLATE.md` + meta-rules in the thin index), and **S1b — migrate the 17 dimensions into modules** (consumes S1a's template; lands "no content lost, index resolves"). S2–S6 gate on **S1a**, not S1b, so the migration and the new-module authoring can run concurrently.

3. **S5 and S6 are oversized — convert each to a per-module batch, not one checkbox.** S5 authors **5** substantial standards modules; S6 authors **7** capability modules, each needing when-to-introduce + how-to + tradeoffs + safety rails (the densest content in the catalog, line 66). Neither bundle "lands complete in one ≤1M-context session" per the WORKFLOW.md:30 hard gate. The fix is cheap because the modules are mutually independent: **make each module (or a 2-module group) its own session unit.** Re-render S5 as 5 units and S6 as 7 (or grouped) under one parallel batch heading. This is the single biggest sizing miss.

4. **Resolve copy-into-repo vs reference-installed-plugin — the plan assumes "copy + merge" but that fights the two-tier model.** Line 67/83 say `init-harness` *copies* modules in and `harness-update` *merges* "newer versions, never clobber local Current-scope/lessons." But the two-tier model (lines 86–87) says **globals sync everywhere, locals stay put** — which argues for **referencing** the installed plugin's pristine global modules (update plugin → every repo sees it, sync is free, no merge) and copying only the *local* artifacts (Current-scope, lessons). If globals are copied per-repo, `harness-update` becomes a real 3-way merge and the design is a drift hazard the plan waves away as "merge." Decide this explicitly and record it; the two-tier model itself points to "reference globals, copy locals."

5. **Reconcile the contradiction: local lessons must not edit global modules in-place.** Line 88 says approved global lessons "become catalog-module edits (promotable upstream)," but lines 67/131 say sync must "never clobber **local** edits to modules." These can't both hold: if a global module carries pending local edits, sync **is** a clobber. Clean design — keep in-repo global modules **pristine (sync = overwrite)**; stage candidate-global lessons in a **separate local file** (e.g. `docs/standards/CANDIDATES.md`) until promoted upstream into the plugin's source-of-truth. Fix the prose in cross-cutting §2 so the local loop never writes into a global module.

6. **De-risk the manifest/packaging unknown *before* authoring 12+ modules — add a cheap pre-Phase-0 spike.** The plan's own risk register (line 132) flags "manifest schema unknown" yet defers all packaging to Phase 2 — i.e. you author ~19 modules first and only then learn where they must live for `init-harness`/`harness-update` and whether the manifest constrains their layout. Add a small spike (verify `plugin.json` schema vs official docs + decide the plugin's `docs/standards/` file layout and copy-vs-reference from #4) **before P0-S1a**, since S1a's template/layout decision depends on it. This is the answer to "is Phase 0 first the right order?": Phase 0 mostly first is fine, but the **layout/packaging decision must precede S1a**, not wait for Phase 2.

7. **Resolve Open decision #2 now — it determines whether S5/S6 belong in Phase 0 at all (YAGNI).** Leaving "author all modules vs just high-frequency" open means Phase 0's scope is itself unresolved. Recommendation: author the high-frequency quality modules (S2–S4 + the 1–2 most-used of S5) now; **defer the capability family (S6) and the S5 long tail to a Phase 0.5 / later sub-plan.** Capability modules (Redis/queues/storage/ML/search, line 66) are the *least* exercised — this repo introduces none of them — so authoring all 7 now is speculative scope (violates the plan's own KISS/YAGNI claim at line 31). Defer S6 to ROADMAP/0.5 until a real capability-upgrade item needs it.

8. **Trim S8 — it conflates "author the stage as prose" with "build the mechanism" (Phase-0 vs later).** S8 lists product-discovery, design pass, fan-out review, effort dial, adversarial verify, **run-and-observe**, **judge-panel**, the learning touchpoint, PRODUCT.md + SCORECARD templates, and CLAUDE.md pointers — in one slice. Two problems: (a) it's oversized; (b) **run-and-observe (Lighthouse/a11y/Playwright-MCP, line 79) and judge-panel (line 80) are mechanisms, not foundation prose** — they belong in the gates/workflow-mechanization phases (or ROADMAP), not Phase 0. Keep in Phase 0 only the *documented* workflow stages + the effort-dial principle (cheap, it's the anti-gold-plating guard) + the artifact templates. Mark run-and-observe and judge-panel as "designed in Phase 0 prose, mechanized later." Split the remainder into ≥2 units (workflow-stage edits vs artifact-template creation).

### Sizing / completeness check (per slice)

- **P0-S1 — SPLIT (see #2).** → S1a (contract/template/versioning/two-tier/ISO map) + S1b (migrate 17 dimensions). S1a is the gate for S2–S6.
- **P0-S2 — OK** (3 modules: security, maintainability-structure, testing) once it consumes S1a's template. At the upper edge of one session; acceptable because the 3 are cohesive.
- **P0-S3 — OK** (layers + architecture-styles + pattern catalog) — cohesive architectural cluster; borderline but landable.
- **P0-S4 — OK** (product-ux + accessibility-i18n). Authoring the *standard* for objective UX signals here is right; do **not** also build the verification mechanism (that's #8).
- **P0-S5 — SPLIT (see #3).** 5 independent modules → 5 (or grouped) parallel session-units.
- **P0-S6 — SPLIT + DEFER (see #3, #7).** 7 capability modules → per-module units; recommend deferring the whole family to Phase 0.5/ROADMAP (YAGNI — none exercised here).
- **P0-S7 — OK.** Role-library expansion (product-designer, ux-reviewer, 5 lens reviewers, synthesizer change to `architect-reviewer`). Mechanical authoring against the 3 existing role files (`.claude/agents/*`); lands in one session. Confirm it explicitly updates ARCHITECTURE_TREE for each new agent file and records the model choices in DECISIONS (already noted).
- **P0-S8 — SPLIT + TRIM (see #8).** → workflow-stage edits (prose) + artifact-template creation; pull run-and-observe + judge-panel out of Phase 0.

### Other notes (non-blocking)

- **Node-port sequencing (Q6): no hazard, but state one subtlety.** The Python gate (`scripts/check_architecture_tree.py`, wired in `.claude/settings.json`) stays green on this repo through Phase 0 (line 139 correct); porting in Phase 1 is right. **But** `INCLUDE_GLOBS = [":(glob)scripts/**/*.py"]` (`check_architecture_tree.py:44`) does **not** track `docs/standards/**/*.md`, so the ~19 new module files are **not** enforced by the gate — their ARCHITECTURE_TREE entries rely on manual discipline. Add a line to each slice's "Lands" requiring the tree update, since the hook won't catch it.
- **Open decisions:** #2 should be **resolved**, not left open (see #7). **Add two:** (i) copy-vs-reference for global modules (#4); (ii) ownership/contents of the S1a module template/contract (#1). #1 (dogfood target) and #3 (scorecard home — safely deferrable) are fine as-is.

### Harness impact

- **New STANDARD / doc:** the `docs/standards/_TEMPLATE.md` module contract (from S1a) is itself a harness artifact and must be indexed in ARCHITECTURE_TREE; the meta-rules currently in `ENGINEERING_STANDARDS.md:5-12` move into the thin index — preserve them verbatim (regression risk: the "may-invent-a-justified-novel-pattern" and Current-scope rules must survive the migration; add a check to S1b's acceptance that no meta-rule is lost).
- **New agents (Stage 9):** S7 adds 7 role files; each needs an ARCHITECTURE_TREE entry + a DECISIONS line for its model assignment. The `architect-reviewer` role gains a "synthesizer over lens findings" responsibility — update `.claude/agents/architect-reviewer.md` accordingly (in-scope for S7, note it).
- **WORKFLOW.md change:** the effort-dial + fan-out-review + product-discovery stages alter the canonical pipeline in `docs/WORKFLOW.md` — that's a source-of-truth process edit, so it must go through this same plan-review discipline when S8 is spec'd.

---

## Spec  _(per slice, after Review passes — Stage 4)_
Spec'd per slice at its own approval gate, starting with **P0-S1**. Later phases get their own sub-plan (`0003+`) when reached.
