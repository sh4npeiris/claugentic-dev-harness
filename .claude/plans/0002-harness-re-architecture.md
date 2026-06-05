# 0002 — Harness Re-Architecture: Trust-First, Three Pillars + Product Lens (Master Plan)

- **Status:** Draft (**rev 3** — trust-first; plan-review addressed; manifest spike done) — awaiting user approval to start Phase 0 (Stage 5).
- **Supersedes:** [`0001-build-agentic-dev-harness.md`](../../docs/archive/2026/0001-build-agentic-dev-harness.md) *(archived)* — its B1–B6 fold into Phases 2–7 here.
- **References:** `docs/WORKFLOW.md` · `docs/ENGINEERING_STANDARDS.md` · `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · plan `0001`.

> **Master/umbrella plan.** Defines vision + full phase roadmap; **only Phase 0 is fully sliced.** Later phases get their own sub-plan (`0003+`) when reached — slice just-in-time.

---

## Decisions locked this session (2026-06-04, see `docs/DECISIONS.md`)

1. **Re-scope into this master plan** — package the *enriched* harness, not the skeleton.
2. **Standards → scoped modular catalog** anchored to **ISO/IEC 25010:2023**; high-value subset → executable gates.
3. **Two-tier knowledge:** global standards sync everywhere; local lessons stay put.
4. **Product/UX lens now** — roles, `product-ux` module, product-discovery → `docs/PRODUCT.md`, run-and-observe verification.
5. **Technology/capability modules** in the catalog (Redis, queues, storage, 3rd-party APIs, sidecars, ML, search) — *authored just-in-time* (deferred, see Decision 9).
6. **Tree-check is language-incidental** *(refined 2026-06-05):* it's harness tooling the agent runs to list files (never parses project source), so its language needn't match the project — `check_architecture_tree.py` **stays as-is, no port**. Only `INCLUDE_GLOBS` is project-specific (`init-harness` sets it). Code-analyzing gates *compose with the project's own linters/analyzers* rather than being reimplemented per language.
7. **Trust-first** *(rev 3):* an independent, deterministic **Trust & Verification** track is foundational and built **early (Phase 1)** — the harness's credibility cannot rest on the same model grading its own work.
8. **High-frequency catalog first** *(rev 3):* author the ~5 modules this repo + a JS app actually exercise; stub the rest.
9. **Capability family deferred** *(rev 3):* authored JIT when a real audit pulls one in — none are exercised yet (YAGNI).
10. ~~**Reference, don't copy, globals**~~ → **SUPERSEDED 2026-06-05 (plan-0003 RC-1):** verified that a plugin's subagents can't read bundled files via bare paths in an adopter repo, and `${CLAUDE_PLUGIN_ROOT}` doesn't cover the parameterized `lens-reviewer` → **`harness-init` COPIES the standards into the adopter repo (version-stamped, "managed"); `/harness-update` re-syncs.** Two-tier model unchanged (global copied+managed vs local); candidate-global lessons still stage in `docs/standards/CANDIDATES.md`.
11. **Skills over commands** *(rev 3, spike-confirmed):* harness entry points are skills (`skills/<name>/SKILL.md`), not legacy commands.

---

## Problem (re-scoped)

The harness is a strong skeleton on real white-space, but key organs aren't wired up, and 0001 would package the thin version permanently:

1. **Trust rests on the model grading itself** — code, tests, review, and scorecard all come from the same model class, which reliably games finite success criteria. A pretty-but-wrong green scorecard is *worse* than none for a non-engineer who can't independently verify. **This is the #1 risk** and the current harness under-defends it.
2. **Learning loop is prose, not a mechanism**; the two tiers (global sync vs local) are conflated.
3. **`ENGINEERING_STANDARDS` is ~40% of the catalog and structured not to scale** — 17 flat rows, always-loaded; missing layers, styles, product/UX, code-health, design-pattern, data/DB, and technology/capability guidance.
4. **No product / UX / look-and-feel lens** and no durable product-context artifact.
5. **No cheap way to *understand* an existing codebase** before auditing.
6. **Review is one agent wearing all hats**, with no **effort dial** → gold-plates everything (violating our own KISS/YAGNI).

> **Purpose.** Take a **recently vibe-coded app** and (a) bring it to a standard that passes any code review, **and** (b) **introduce appropriate modern technology** (caching, async messaging, proper storage, third-party integrations, ML) — safely, incrementally, verifiably.

## Vision

A self-improving Claude Code harness that lets a technically-literate non-engineer co-build software that **passes any code review and is a pleasure to use** — resting on **independent, deterministic, human-anchored trust**, applied through three pillars, distributed as a plugin, and getting smarter via a two-tier learning loop.

- **Trust & Verification (foundation):** deterministic gates + a frozen behavioral baseline + hook-enforced Definition-of-Done — "green" is a machine fact, not a model claim.
- **Pillar A — Quality + capability catalog:** ISO-25010-anchored, scoped-modular, globally synced (referenced from the plugin).
- **Pillar B — Apply it to existing code, safely:** safety-scan → understand → bounded multi-lens audit → 3-lane tiered backlog → gated execution. Never a bulk rewrite.
- **Pillar C — Multi-lens review incl. product/UX:** fan-out specialist reviewers with adversarial verification + an effort dial; product-discovery; run-and-observe with objective signals.
- **Teaching layer:** the harness coaches the non-engineer (playbook, plain-English outputs, decision-explainers) so they learn to run an AI dev team.

## Goals / Non-goals

**Goals:** the foundational Trust track; a scoped ISO-25010 catalog (high-frequency now); a product/UX lens; multi-lens fan-out review with an effort dial; the legacy on-ramp (safety-scan → understand → audit → gated execution); plugin packaging (skills, referenced globals, bundled gates); a two-tier learning loop (manual now); a teaching layer; a per-repo quality scorecard that honestly separates *verified* from *asserted*.

**Non-goals:** bulk/auto refactor; editing target *code* on init; mechanized auto-distillation now; authoring the capability family now; language lock-in; over-speccing distant phases.

## Architecture

### Trust & Verification (the foundation — built early, Phase 1)
The load-bearing answer to risk #1: move trust onto signals independent of the model being graded.
- **Deterministic fitness-function gates** (no LLM; compose with the project's own linters/analyzers where they exist): complexity, duplication, dead-code, **layering/import-boundary (dependency direction)**, secret-scan, coverage-floor — alongside the architecture-tree check.
- **Frozen behavioral baseline (golden-master):** capture real user-journey traces + screenshots + an HTTP/DB-call inventory *before* changes; this — not agent-authored tests — is the equivalence oracle for refactors.
- **Hook-enforced Definition-of-Done:** `PreToolUse` (block edits to the frozen baseline / migration files without a token), `PostToolUse` (run the scoped gate on changed files), `Stop` (refuse "done" until gates are green). Mechanizes DoD instead of trusting self-report.
- **Test-diff review + mutation testing:** every change is checked for "did the tests get *weaker*?"; mutation score verifies the tests are real.
- *(No dedicated pre-flight safety scan — the first dogfood target has no credentials. Secret-hygiene stays in the `security` module + the Phase-1 secret-scan gate; run-and-observe still stubs external side-effects for repos that need it.)*
- **Scorecard honesty:** every score is tagged **verified-deterministically** vs **asserted-on-the-model's-word**, so the user learns where to apply their own judgment.

### Pillar A — Quality + Capability Catalog
- `ENGINEERING_STANDARDS.md` → **thin index + meta-rules** (preserved verbatim) pointing to **`docs/standards/` modules**, each keyword/glob-scoped so it loads only when relevant.
- **Backbone = ISO/IEC 25010:2023.** **Module contract** (`docs/standards/_TEMPLATE.md`): frontmatter (`version`, ISO-25010 mapping, load-scope, auditor-checks) + a required **"explain the tradeoff to a non-engineer"** field + a **confidence-basis** field (deterministic vs judgment).
- **High-frequency quality modules now (5):** `security` · `maintainability-structure` (SOLID, layering, patterns, code-health/smells/dead-code) · `testing` · `product-ux` (+ `accessibility-i18n`) · `data-and-persistence`. Remaining quality modules + the **capability family** are **stubbed**, authored JIT.
- **Global sync = reference, not copy** (Decision 10): plugin is the source of truth; `harness-update` = bump the plugin, every repo sees new globals for free.

### Pillar B — Safety-scan → Understand → Audit → 3-Lane Backlog → Gated Execution
- **`understand`** — derive a dependency/symbol map + hotspots (optional C4 diagram for the human).
- **`audit`** — bounded, multi-lens, multi-modal sweep (parallel subagents; budget + directory bounded; lenses read the *derived map + scoped modules*, never the raw tree; dedup; **loop-until-dry**) → a **prioritized tiered backlog** with **dual-layer** entries (technical finding + plain-English "what this means / traffic-light"). Untested code → item #1 = "establish a test baseline."
- **Three lanes:** **refactor** (behavior-preserving → characterization-first + golden-master) · **capability-upgrade** (new tech → *feature* pipeline + safety rails: flag, dual-write/shadow, **backup-before-migration**, migration + **rollback runbook**, observability) · **dependency-health** (CVEs, outdated deps, lockfile, runtime version — its own risk class).

### Pillar C — Multi-Lens Review + Product/UX Lens
- **Roles:** add `product-designer`, `ux-reviewer`, lens reviewers (`security`/`performance`/`data`/`resilience`/`accessibility`), and a **`yagni-sentinel`** (argues the change is *too much*); `architect-reviewer` becomes the **synthesizer**.
- **Adversarial verify:** a skeptic gets the diff **and** the test-diff and tries to refute the change ("weakened a test? mocked a real path? moved goalposts?").
- **Effort dial + relevance-gating:** review depth scales with risk/scope; don't fan out 8 lenses on a one-liner; review is budget-bounded like the audit.
- **Product-discovery stage** before the technical plan → durable **`docs/PRODUCT.md`**; a **design pass**; **run-and-observe verification** for user-facing slices (Lighthouse/a11y/Playwright via MCP, declared as **required-signal contracts** so a missing signal fails loudly, plus a "safe to run / stub externals" check).
- **Judge-panel** at Plan with **persona-diverse** members (ship-it minimalist / future-proofer / security-paranoid) so best-of-N actually decorrelates.

### Cross-cutting — Packaging · Learning · Teaching · Visibility
- **Packaging:** `.claude-plugin/plugin.json` (verified schema); entry points are **skills**; **hooks/hooks.json** references bundled Node gates via `${CLAUDE_PLUGIN_ROOT}`; `marketplace.json` for distribution; `init-harness` `git init`s if needed, **composes with the repo's existing tooling** (eslint/tsc/vitest), references globals, scaffolds only local artifacts.
- **Learning (two-tier, manual now):** after a slice, the orchestrator **proposes candidate lessons** tagged global/local; the **user approves**; globals → `docs/standards/CANDIDATES.md` (promoted upstream later), locals → repo memory. An **episodic log** (`docs/.harness/episodic-log.md`) captures failed attempts + verbalized lessons for the next slice. Mechanized distillation reserved (Decision: deferred).
- **Teaching:** `docs/PLAYBOOK.md` (orchestration patterns in plain English) + a `/harness-explain` skill (narrates *why* the harness did what it did) + **dual-layer outputs** everywhere + `docs/GLOSSARY.md`.
- **Visibility:** `docs/SCORECARD.md` — ISO-25010 maturity + backlog burndown + the verified-vs-asserted split; readable as a narrative report card.

## Phase roadmap

| Phase | Theme | Folds in |
|---|---|---|
| **0-prelude** | **Packaging spike** — verify manifest schema + layout + reference-vs-copy | **DONE (this session)** |
| **0** | **Foundation** — module contract, 5 high-frequency modules, roles, workflow prose, artifact templates | — |
| **1** | **Trust & Verification (Node)** — gates, frozen baseline, hook-enforced DoD, test-diff/mutation, safety scan | — |
| **2** | **Plugin shell + manifest + marketplace** (skills; bundled gates) | 0001 B1 |
| **3** | **`understand` + `audit`** (safety-scan → 3-lane backlog) | 0001 B2 |
| **4** | **Execution** — refactor-item · capability-upgrade · dependency-health | 0001 B3 |
| **5** | **`init-harness`** (git-init, compose-with-tooling, reference globals) | 0001 B4 |
| **6** | **Wiring + `harness-update` + `/harness-explain`** | 0001 B5 |
| **7** | **Package & dogfood** (throwaway → the user's JS app) | 0001 B6 |

## Phase 0 — detailed slices

Each lands **complete in one ≤1M-context session, no debt**; **each slice's acceptance explicitly requires the `ARCHITECTURE_TREE` update** (the gate won't catch new markdown). **S2–S6 fan out in parallel only after S1a lands** (they consume its template).

- [ ] **P0-S1a — Module contract + meta-rules + two-tier model.** Author `docs/standards/_TEMPLATE.md` (frontmatter: version, ISO-25010 mapping, load-scope, auditor-checks, tradeoff-explainer, confidence-basis) + the thin-index meta-rules (preserve `ENGINEERING_STANDARDS.md:5-12` **verbatim** — incl. "may-invent-a-justified-novel-pattern" + Current-scope) + the global/local split + versioning. **The gate for S2–S6.**
- [ ] **P0-S1b — Migrate the 17 dimensions** into modules per the template; `ENGINEERING_STANDARDS.md` → thin index. *Acceptance:* no content lost, no meta-rule lost, index resolves. (Gates on S1a; concurrent with S2–S6.)
- [ ] **P0-S2 — `security` module.**
- [ ] **P0-S3 — `maintainability-structure` module** (incl. code-health/housekeeping, layering, design-pattern catalog).
- [ ] **P0-S4 — `testing` module** (incl. characterization, golden-master, mutation, visual-regression/a11y testing).
- [ ] **P0-S5 — `product-ux` (+ `accessibility-i18n`) module** (incl. defining the objective UX signals).
- [ ] **P0-S6 — `data-and-persistence` module.**
- [ ] **P0-S7 — Role library expansion.** `product-designer`, `ux-reviewer`, 5 lens reviewers, `yagni-sentinel`; `architect-reviewer` → synthesizer. Each: ARCHITECTURE_TREE entry + DECISIONS line for model choice (Sonnet mechanical / Opus judgment-heavy).
- [ ] **P0-S8a — Workflow upgrade (prose).** Add product-discovery (→ PRODUCT.md), design pass, fan-out review + **effort dial** + adversarial-verify (test-diff lens) + persona-diverse panels, the 3 backlog lanes + upgrade safety rails, the two-tier learning touchpoint + episodic log, dual-layer output convention. *(Run-and-observe, judge-panel, gates = designed-in-prose here, **mechanized in Phases 1/3**.)*
- [ ] **P0-S8b — Artifact templates + pointers.** Create templates: `docs/PRODUCT.md`, `docs/SCORECARD.md`, `docs/PLAYBOOK.md`, `docs/GLOSSARY.md`, `docs/standards/CANDIDATES.md`, `docs/.harness/episodic-log.md`; update `CLAUDE.md` pointers (index, don't duplicate).

## Later phases (at altitude — own sub-plans)

- **Phase 1 (Trust):** the full Trust & Verification track above; **fix the tree-check's `INCLUDE_GLOBS` to track `docs/standards/**/*.md`** (the script stays Python — it's harness tooling, not project code); code-analyzing gates compose with the project's existing linters/analyzers.
- **Phases 2–7:** 0001's B1–B6 over the enriched harness; skills-not-commands; referenced globals; 3-lane execution; `harness-update`; `/harness-explain`.
- **JIT / ROADMAP:** capability modules (authored when an audit pulls one in); mechanized learning loop (retrospector + Lesson artifact); episodic-memory automation.

## Risks & mitigations

- **False confidence (the model grades itself)** → the Trust & Verification track (deterministic gates + frozen baseline + hook-enforced DoD + test-diff/mutation + verified-vs-asserted scorecard), built early.
- **Velocity death by process** → default-to-lightweight bias + a time-box ("if a small change is >N turns of process, you mis-triaged") + a process-cost line in the retrospective.
- **Gold-plating (catalog's own gravity / over-fanning review)** → effort dial + `yagni-sentinel` lens + budget-bounded review + lenses read the derived map, not the raw tree.
- **Capability-upgrades break a live app** → safety rails (flag, dual-write/shadow, backup, migration + rollback runbook, observability); upgrades use the *feature* pipeline.
- **Running a vibe-coded app leaks/nukes prod** → pre-flight safety scan + "safe to run / stub externals" check before run-and-observe.
- **Scope explosion** → phase + sub-plan structure; capability family deferred; only Phase 0 sliced.
- **Tree gate misses markdown** → each slice's acceptance requires the ARCHITECTURE_TREE update; Phase 1 fixes the glob.

## Test & dogfood strategy

- **Dogfood on this repo** (it builds with its own harness); the Python tree gate stays green until the Node port (Phase 1).
- **Trust gates (Phase 1)** ship with tests + self-check.
- **Cold install (Phase 7):** packaged plugin into a throwaway repo; `/init-harness` → safety-scan → `/harness-understand` → `/harness-audit` end-to-end.
- **Real-repo dogfood (Phase 7, final):** the full on-ramp on **the user's JS app**; acceptance = the audit reproduces its known tiered backlog and one item per lane lands with gates green.

## Affected files (across phases)

`docs/standards/**` (`_TEMPLATE.md` + modules + `CANDIDATES.md`) · `docs/ENGINEERING_STANDARDS.md` (→ thin index) · `docs/PRODUCT.md` · `docs/SCORECARD.md` · `docs/PLAYBOOK.md` · `docs/GLOSSARY.md` · `docs/.harness/episodic-log.md` · `.claude/agents/*` (new roles + synthesizer change) · `docs/WORKFLOW.md` · `CLAUDE.md` · `.claude-plugin/{plugin.json,marketplace.json}` · `skills/*` · `hooks/hooks.json` · `scripts/check_architecture_tree.*` (Python → Node) + new gate scripts · `.gitattributes` · `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · `docs/ROADMAP.md`.

## Open decisions

1. **Dogfood target** — a JS app the user provides at Phase 7. Git-backed? (deferrable)
2. ~~Module depth in Phase 0~~ — **RESOLVED:** high-frequency now, capability family JIT (Decisions 8–9).
3. ~~Copy-vs-reference for globals~~ — **RESOLVED:** reference via `${CLAUDE_PLUGIN_ROOT}` (Decision 10, spike-confirmed).
4. **Scorecard home** — standalone `docs/SCORECARD.md` (current choice) vs a ROADMAP section. (deferrable)

---

## Review  _(filled by plan-reviewer, Stage 3 — 2026-06-04)_

**Verdict: CHANGES REQUIRED.** The vision, two-pillar split, and "slice-only-Phase-0" discipline are sound and well-argued, and deferring later phases to sub-plans correctly applies YAGNI-to-planning. But Phase 0's slicing **fails the sizing gate** in three places, the "S2–S6 are independent → fan out in parallel" claim **overstates independence** (they depend on an S1 output the plan never names), and the knowledge-sync model is **internally contradictory** (local lessons edit global modules, yet sync must "never clobber local edits"). Fix the items below and re-review; most are plan-text changes, not redesign.

### Required changes
1. **Name the S1 module template/contract and gate S2–S6 on it.** Modules must conform to a shared contract (frontmatter: version, ISO-25010 mapping, load-scope, capability section shape) that is an **S1 deliverable**. Restate: S1 produces the template; S2–S6 fan out **only after S1 lands**.
2. **Split S1** — it bundles a design-lock task (contract/versioning/two-tier) with bulk migration of the 17 dimensions. → **S1a** (contract/template + versioning + two-tier + ISO map; the thing S2–S6 consume) + **S1b** (migrate the 17). S2–S6 gate on **S1a**.
3. **S5 and S6 are oversized** — 5 and 7 modules → make each module its own session unit under a parallel batch.
4. **Resolve copy-into-repo vs reference-installed-plugin** — the two-tier model argues for **referencing** pristine globals and copying only locals. Decide and record.
5. **Reconcile the contradiction** — keep in-repo globals **pristine (sync = overwrite)**; stage candidate-global lessons in a **separate local file** (`CANDIDATES.md`) until promoted upstream. Local loop must never write into a global module.
6. **Add a cheap pre-Phase-0 spike** — verify `plugin.json` schema + decide the `docs/standards/` layout + copy-vs-reference **before P0-S1a**.
7. **Resolve Open decision #2 now** — author high-frequency modules now; **defer the capability family** (least exercised; speculative scope).
8. **Trim S8** — pull run-and-observe + judge-panel (mechanisms) out of Phase 0; keep documented stages + effort dial + templates; split into ≥2 units.

### Sizing / completeness check
- **P0-S1 — SPLIT** → S1a + S1b. · **S2/S3/S4 — OK** once consuming S1a. · **S5/S6 — SPLIT/DEFER.** · **S7 — OK.** · **S8 — SPLIT + TRIM.**

### Other notes
- `INCLUDE_GLOBS = scripts/**/*.py` does **not** track `docs/standards/**/*.md` — new modules aren't gate-enforced; each slice must update ARCHITECTURE_TREE manually.
- Resolve Open #2; add (i) copy-vs-reference, (ii) ownership/contents of the S1a contract.

### Harness impact
- `docs/standards/_TEMPLATE.md` is a harness artifact (index it); preserve the `ENGINEERING_STANDARDS.md:5-12` meta-rules verbatim (regression risk). S7 adds 7 role files (+ tree/DECISIONS entries) and changes `architect-reviewer` to synthesizer. The WORKFLOW.md stage edits are a source-of-truth process change → re-review when S8 is spec'd.

---

## Resolution  _(orchestrator, rev 3 — all 8 required changes addressed)_

1. **S1a is named and is the gate.** `docs/standards/_TEMPLATE.md` is the contract; S2–S6 explicitly "fan out only after S1a lands."
2. **S1 split** into S1a (contract) + S1b (migrate 17). S2–S6 gate on S1a; S1b runs concurrently.
3. **Per-module slices** — S2–S6 are now one module each (security / maintainability-structure / testing / product-ux / data-and-persistence).
4. **Copy-vs-reference RESOLVED → reference** (Decision 10), confirmed by the manifest spike (`${CLAUDE_PLUGIN_ROOT}`). Sync is free; no merge.
5. **Contradiction removed** — globals pristine (overwrite on plugin update); candidate-global lessons stage in `docs/standards/CANDIDATES.md`; the local loop never edits a global module.
6. **Spike DONE this session** (manifest schema + layout + reference decision verified against official docs); recorded in DECISIONS.
7. **Open #2 RESOLVED** — high-frequency now (Decision 8); **capability family deferred** to JIT/ROADMAP (Decision 9).
8. **S8 split + trimmed** → S8a (workflow prose, effort dial) + S8b (artifact templates); run-and-observe + judge-panel marked "designed in prose, mechanized in Phases 1/3."
- **Tree-gate gap** noted in every slice's acceptance + scheduled for the Phase-1 Node port (fix `INCLUDE_GLOBS`). Meta-rule preservation is an explicit S1b acceptance check.

---

## Spec  _(per slice, after approval — Stage 4)_
Spec'd per slice at its own approval gate, starting with **P0-S1a**. Later phases get their own sub-plan (`0003+`).
