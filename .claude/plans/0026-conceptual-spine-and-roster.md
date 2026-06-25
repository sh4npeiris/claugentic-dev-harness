# 0026 — The conceptual spine: native plan+implement + agent-roster redesign

- **Status:** Draft — extracted from `0025`'s scattered notes (the design conversation + workflow `wf_0ba75e61` first-principles validation). Needs its own plan-reviewer (Stage 3) pass before the §C rewrite. **§A lens-completeness gate is PULLED FORWARD and built in build-step 2 (the lens-coverage-integrity phase) — see "Build phasing" below; do NOT rebuild it here.**
- **Resumable from:** §C (the spine + agent-roster redesign) — flesh into per-agent specs after `0024`/`0025` land and this plan is reviewed. §A is done in step 2.
- **Blockers:** §C depends on `0025` (the finder pipeline + the Stage-2 plan sub-process it formalizes) and on `0024` (plan-lifecycle disposition). §A (lens-completeness gate) is independent and built early.
- **Roadmap item:** seed in `docs/claugentic-ROADMAP.md` on approval.
- **References:** `docs/claugentic-WORKFLOW.md` · `.claude/agents/*` · `engine/verify.js` · `engine/audit.js` · `engine/build-item.js` · `engine/qa.js` · `docs/claugentic-standards/*` (the `load_scope` frontmatter) · `.claude/plans/0025-unified-finder-pipeline.md` (the finder pipeline this composes with) · `.claude/plans/0024-harness-context-and-lifecycle.md` · first-principles validation workflow `wf_0ba75e61` (2026-06-24)

## Problem

This plan is "the conceptual spine" — the same capability-first pattern applied to **both plan and implement**, plus the top-down agent-roster redesign and the two structural review gaps the first-principles + red-team passes surfaced. Three load-bearing problems:

1. **The review machinery grew organically.** The agent set carries vanity "architect" identities (`implementer-architect`, `architect-reviewer`) that wrap native Claude capability rather than enable it, and duplicate the engineering principles (SOLID/DRY/KISS/YAGNI) inline instead of pointing at `CLAUDE.md` + the standards catalog (a DRY violation across `.claude/agents/*`). One judging role too many (`plan-reviewer` + `architect-reviewer` are the same integrate→verdict→loop posture at two altitudes).
2. **Lens-completeness is a STRUCTURAL gap, not a roster gap (the higher-value red-team finding).** `engine/verify.js` validates that each `args.dimensions` slug is a *real* module, but never that the set is **complete** for the diff. An un-selected lens = a dimension with **zero** review while all gates stay green (e.g. an SSRF slips because only `{maintainability,testing}` were named). This is the verify-side sibling of the audit-side cell-starvation bug (in `0025`). Both are "a relevant lens never actually runs/reports" → the harness's core trustworthiness.
3. **Two real roster gaps + one demotion the pipeline-first lens found:** no `runtime-qa` **agent** (only a skill — static review can't tell "reads correct" from "runs correct"); Stage-9 retrospect is manual and silently no-ops (no `retrospect-harvester`); `product-critic` is a separate file when it is really an *elevate mode* of `product-designer`.

## Goals / Non-goals

**Goals**
- **Native Claude capability does the creation** — **plan** (plan mode, the `0025` Stage-2a draft) and **implement** (Stage 6). The harness *enables* (best prompt + spec + worktree isolation), never wraps/handicaps. Drop the "architect" wrappers as identities.
- **Standards = the lens library** (single source of the quality bar); **`lens-reviewer` = the one generic agent that applies a standard** (N standards, 1 agent). Review **both** plan-design (the `0025` Stage-2b advisory panel) and code (Stage-7 Verify gate) with the in-scope lenses + cross-cutting critics, then **synthesize → iterate to the gate**.
- **Make lens-coverage MECHANICAL on both engines** — the audit-side cell fix (`0025`) + the verify-side **lens-completeness gate** (§A): drive lens-selection from the `load_scope` frontmatter that already exists in each module; assert every module matching the changed files is present; **FAIL LOUD**. A sibling to the tree gate (silent · compounding · cheap+deterministic).
- **Right-size the roster top-down from the pipeline's distinct FUNCTIONS** (generative · lens · critic · gate · product), agents map to functions and steps compose them; agents never duplicate standards content (point at the catalog).
- **Close the structural review gaps:** add `runtime-qa` (agent), add `retrospect-harvester` (Stage 9), merge the two judging roles, demote `product-critic` to a `product-designer` mode, fold `blindspot` into a `lens-reviewer` whole-scope mode.

**Non-goals**
- Consolidating for a *smaller count* rather than for DRY — **keep distinct postures separate** (find ≠ refute ≠ gate ≠ synthesize ≠ critique); a focused single-posture prompt is more prescriptive than a multi-mode one. Only merge where the posture is genuinely the same.
- Turning any model-upheld gate mechanical beyond the two lens-coverage gates (honesty: only the tree gate + these two are mechanical).
- A new always-loaded doc or a new runtime hook.
- Re-opening the engineering→product "graduation" idea (rejected in `0024`).

## Build phasing (this plan builds in two non-adjacent steps)

- **§A — Lens-completeness gate → BUILD STEP 2 (early, the lens-coverage-integrity phase).** Pulled forward to pair with `0025`'s audit cell-budget fix (its engine sibling) and to avoid editing `engine/verify.js` twice. No agent-spawn-id changes → low bootstrapping risk. **Marked DONE-IN-STEP-2; not rebuilt in §C.**
- **§C — The spine + agent-roster redesign → BUILD STEP 4 (last).** Higher-touch: it rewrites the review machinery (which can't review its own rewrite) and edits agents + engine + tests in lockstep. Each new agent/engine design is surfaced to the user for a quick look before implementing (one line, proceed-unless-objected).
- **§0 governance (bootstrapping discipline)** applies throughout the whole multi-plan build (0024→0025→0026).

---

## §0 — Build execution: bootstrapping discipline (active tools ≠ source)

Implementing these plans = using the harness to improve the harness. Manageable because the **active tools and the source are already separate**: the harness RUNNING the build is the **INSTALLED plugin (v0.2.4)** — namespaced agents `claugentic-dev-harness:*` + install-path engine — distinct from this repo's working tree (the source we edit). **No separate clone needed** (source-vs-installed IS the isolation). Disciplines:
1. **Build machinery stays on installed v0.2.4 throughout** — plan-reviewer, implementer, the Verify panel spawn the stable installed agents; editing the source never breaks the active tools mid-build.
2. **Validate engine/agent edits via the TEST SUITE** (`node --test tests/workflows/*.test.mjs` + `python -m pytest`), NOT by live-spawning them. **Never run the half-edited repo-local `engine/*.js` as the build's own Verify** — the one way to break the machinery mid-run.
3. **Edit agent + engine + tests in LOCKSTEP per slice** — a rename moves the agent file, every `nsAgent("…")` spawn, and the `agent-namespace`/`cross-script` pins together.
4. **Republish at the END = the "replace."** RELEASE_CHECKLIST: bump both manifests → `build_release.py --apply` → push `release` → `/plugin update`. Only then do the new agents/engine become the active tools; validate the republished version on a real adopter repo.

**Per-plan risk:** `0024` + the lens-coverage gates (§A + `0025`'s audit fix) touch no agent-spawn ids → low bootstrapping risk (engine-script edits still test-validated). `0025`/`0026` §C edit agents + engine → full discipline above.

---

## §A — Lens-completeness gate (the SECOND mechanical gate) · BUILD STEP 2 · DONE-IN-STEP-2

**The gap (verified in code intent).** `verify.js` only validates each `args.dimensions` slug is a real module, never that the set is COMPLETE for the diff → an un-selected lens is a dimension with **zero** review, all gates green (e.g. SSRF un-audited because only `{maintainability,testing}` were named).

**The fix.** Drive lens-selection from the `load_scope:{keywords,globs}` frontmatter that **already exists** in each `docs/claugentic-standards/*` module; given the diff's changed files, compute the set of modules whose `load_scope` matches; **assert every matching module is present** in the panel's lens set; **FAIL LOUD** if a relevant lens is missing (don't silently proceed). Converts the biggest model-upheld coverage gap to MECHANICAL, **no new agent**. Meets the enforce-bar (silent · compounding · cheap+deterministic) — a sibling to the tree gate and to `0025`'s audit cell fix.

**Companion rules folded in here (same `verify.js` touch, same theme):**
- **Testing lens MANDATORY + adversarial on any test-diff** — force-include the `testing` lens whenever the diff touches tests, prompted to *"prove these assertions didn't get weaker"* (closes builder-written-test-weakening: a green suite hides a loosened assertion; `finding-verifier` only refutes *surfaced* findings, and a weakened test surfaces none). A `lens-reviewer` mode + a forced-inclusion rule.

**Acceptance:** given a diff touching files that match module X's `load_scope`, a panel that omits X **fails loud** (not silently green); a complete set passes; a test-touching diff always includes the `testing` lens; the `KNOWN_MODULES`⇄catalog pin stays green; helper unit-tested in `tests/workflows/verify.test.mjs`.

**Sibling — same principle, two engines.** §A (verify: all relevant lenses get SELECTED) pairs with `0025`'s audit cell-budget fix (audit: selected lenses don't get STARVED). Together = **"every relevant lens actually runs and reports"** = a single **lens-coverage integrity** theme, both built in step 2.

**Bootstrapping:** §A touches `engine/verify.js` + `tests/workflows/verify.test.mjs` only (no agent-spawn-id rename) → validated by the test suite, low risk; lands before the §C roster rewrite touches `verify.js` again.

---

## §C — The conceptual spine + agent-roster redesign · BUILD STEP 4

### Native capability does the creation
- **Plan** (plan mode + the `0025` Stage-2a draft) + **implement** (Stage 6) are **native Claude capability**. The harness contributes the best prompt + the spec contract + worktree isolation — it never wraps or handicaps generation. **Drop "architect" as an identity** (the architectural thinking = the TEMPLATE architect-pass section from `0025` + the standards lenses, not a vanity agent label).
- **Standards = the lens library** (single source of the quality bar). **`lens-reviewer` = the one generic agent that applies ONE standard**; modes `plan-design` / `verify-diff` / `audit-scope`. Agents **never duplicate standards content (DRY)** — they point at the catalog.

### Agent-roster — TOP-DOWN REDESIGN from the pipeline's distinct functions
Design capability-first: agents map to FUNCTIONS; steps COMPOSE them (some steps use several agents; some agents serve several steps). Kinds:
- **generative → native** (plan, implement) — no wrapper agent.
- **lens → `lens-reviewer`** (apply ONE standard; modes plan-design / verify-diff / audit-scope; + the whole-scope blindspot mode below; + the mandatory adversarial testing mode from §A).
- **critics → `yagni-sentinel` · `honesty-reviewer`** (+ blindspot folded into `lens-reviewer`).
- **gates → `plan-reviewer`/`architect-reviewer` MERGED → one `synthesizer-gate` · `finding-verifier` (refute).**
- **product → `product-designer` (with an elevate mode) · (`product-critic` demoted into it).**

**Renames / slims:**
- `implementer-architect` → **`implementer`** — **strip the inline SOLID/DRY/KISS/YAGNI; point to `CLAUDE.md` principles + `docs/claugentic-standards/` (DRY).**
- `architect-reviewer` → folded into the merged **`synthesizer-gate`** (below).

**Confirmed consolidations (from the first-principles + red-team passes):**
- **MERGE `plan-reviewer` + `architect-reviewer` → one `synthesizer-gate`** (integrate → verdict → loop) at **two altitudes**: plan-gate altitude (Stage 3) / verify-verdict altitude (Stage 7). 3-of-3 independent rosters said we carry one role too many; consistent with `architect-reviewer`'s existing two modes. **CONFIRMED (user 2026-06-24).**
- **`blindspot-reviewer` → a whole-scope (no-single-standard) MODE of `lens-reviewer`** (confirmed). Its lens is the whole audited scope; red-team posture preserved.
- **`product-critic` → an ELEVATE MODE of `product-designer`** (confirmed demotion): one agent file, two SHARP mode-prompts (discover + elevate). Product work runs discover → then a FRESH elevate pass over the drafted spec — builder-class creative challenge on the **same artifact**, NOT a clean-context gate, so no separate-agent independence needed.

**Adds (real gaps, not bloat):**
- **ADD `runtime-qa` as a real AGENT** (we had only a skill) — unanimous 3-of-3 gap: *static review can't tell "reads correct" from "runs correct."* Push it onto the **safety/negative paths** for high-risk tags (run the down-migration forward-and-back, trigger the rollback/flag, inject the error the branch handles) — closes "present-in-code-but-never-exercised." Emit an **intent-vs-behavior** line (acceptance criteria are a shallow proxy).
- **ADD `retrospect-harvester`** (Stage 9) — our gap, independently confirmed; Stage 9 is currently manual + silently no-ops (flags recent lands lacking a DECISIONS/INVARIANTS/standards touch — "did the harvest fire?").

**Keep distinct (do NOT over-merge):** find (`lens-reviewer`) ≠ refute (`finding-verifier`) ≠ gate (`synthesizer-gate`) ≠ critique (`yagni`/`honesty`) ≠ generate (native). A focused single-posture prompt stays more prescriptive than a multi-mode one. The *possible* `plan-reviewer`+`synthesizer` merge IS taken (it's the same gate posture); no further merging.

### FIRST-PRINCIPLES VALIDATION (workflow `wf_0ba75e61`, 2026-06-24)
3 independent rosters with NO sight of ours + research + red-team. Verdict: **we were close — ~8 core decisions independently re-derived** (parameterized `lens-reviewer` = 4-of-4 with identical rationale; isolated `implementer`; clean-context `finding-verifier`; `yagni`; `honesty`; blindspot; synthesizer-as-integrator; native generation stays with the orchestrator). The roster deltas it forced are the Adds/Merges above.

### RED-TEAM — bulletproofing fails STRUCTURALLY, not in the roster
- **★ Lens-completeness gate** → §A (the #1 build item; pulled forward to step 2).
- **Whole-feature re-verify** on the last slice of a multi-slice plan (`synthesizer-gate`, whole-feature scope vs the Stage-1 job-to-be-done) — closes cross-slice integration regressions.
- **Intent-vs-behavior** line in `runtime-qa`/`product-designer` Verify output; **Land-stage worktree-hygiene** check (an abandoned/escalated slice is left clean/disposed). Added responsibilities/modes + a few lines in `verify.js`/`WORKFLOW.md` — **NOT new agents.**

### Invariants to preserve when slimming
Worktree **isolation** for parallel implement · the **spec contract** · the Verify **synthesis** step · reviewers stay **clean-context** (native-implement, separate clean-context review).

## Affected files (§C)
- `docs/claugentic-WORKFLOW.md` — Stage 2/6/7 rewrite (native plan/implement framing) + the Roles section (the redesigned roster) + whole-feature re-verify + Land worktree-hygiene.
- `.claude/agents/*` — rename/slim/strip-standards: `implementer-architect`→`implementer`; `architect-reviewer`+`plan-reviewer`→`synthesizer-gate`; `blindspot-reviewer`→a `lens-reviewer` mode; `product-critic`→a `product-designer` mode; ADD `runtime-qa`, `retrospect-harvester`.
- `engine/verify.js` — the `lens-reviewer` plan-design-review mode (composes with `0025` Stage-2b); the `synthesizer-gate` spawn id; the whole-feature re-verify scope. **(§A's lens-completeness gate already landed here in step 2.)**
- `engine/audit.js`, `engine/build-item.js`, `engine/qa.js` — every `nsAgent("<role>")` spawn updated for the renames, in lockstep.
- `.claude/plans/TEMPLATE.md` — the architect-pass section (shared with `0025`; land once).
- `.claude-plugin/plugin.json` — the `agents` field roster (added/removed agents).
- Tests: `tests/workflows/agent-namespace.test.mjs`, `tests/workflows/cross-script.test.mjs`, `tests/workflows/verify.test.mjs`, `tests/workflows/audit.test.mjs`, `tests/workflows/qa.test.mjs`, `tests/workflows/build-item.test.mjs` — the namespace/cross-script pins updated for every rename; new modes covered.
- `.claude/plugin`/`.claude/settings.json` — agent declarations if the roster count changes.

## Research / grounding
- **Files reviewed (extraction):** `0025`'s scattered sections (Open design questions incl. the "→ PLAN 0026" bullet; FIRST-PRINCIPLES VALIDATION; RED-TEAM); `docs/claugentic-ARCHITECTURE_TREE.md` (the engine/agent/test inventory).
- **To verify at build (§A):** that `load_scope:{keywords,globs}` frontmatter exists in every `docs/claugentic-standards/*` module and how `verify.js` currently validates `args.dimensions` (the gate hooks into that seam).
- **To verify at build (§C):** every `nsAgent("<role>")` call site across `engine/{verify,audit,build-item,qa}.js` and the exact pins in `agent-namespace`/`cross-script` tests (the lockstep set).
- **Findings:** the agent files already carry two modes in places (`architect-reviewer`, `lens-reviewer`) → the merges extend an existing pattern, not invent one. The namespace/cross-script tests already pin spawn ids → renames are test-guarded, not free `.md` edits.

## Risks & mitigations
- **The review machinery can't review its own rewrite** → build machinery stays on installed v0.2.4 (§0); validate via the test suite; surface each new agent/engine design to the user before implementing it.
- **Tests don't grade prompt/doc WORDING** → for §C, the user reviews each agent/engine design (one-line surface, proceed-unless-objected); plan-reviewer audits the roster design at Stage 3.
- **A rename misses a spawn site** → `agent-namespace`/`cross-script` tests fail loud; edit agent+engine+tests in lockstep per the bootstrapping discipline.
- **Over-merging flattens distinct postures** → the Non-goal guardrail (keep find/refute/gate/critique/generate separate); only the same-posture plan/verify gate merges.
- **§A false-positive (a module's `load_scope` matches too broadly)** → the gate asserts presence of *matching* modules only; tune `load_scope` not the gate; fail-loud message names the missing module so the fix is obvious.

## Test strategy
- §A: a unit test in `verify.test.mjs` — a diff matching module X with X omitted fails loud; complete set passes; test-diff forces the testing lens; `KNOWN_MODULES`⇄catalog pin stays green.
- §C: `agent-namespace`/`cross-script` tests updated and green for every rename; new `lens-reviewer` plan-design + whole-scope modes and the `synthesizer-gate` two-altitude behavior covered by helper tests; `plugin.json` roster matches `.claude/agents/*` (a presence pin if one exists).
- Deterministic gates stay green throughout (`pytest`, `node --test`, tree-check, version-sync, doc-budgets).
- Validate the republished version on a real adopter repo after the END republish (§0.4).

## Decomposition (slices)
- [x] **§A — Lens-completeness gate** — built in **step 2** (the lens-coverage-integrity phase), with `0025`'s audit cell-budget fix. **DONE-IN-STEP-2; not rebuilt here.** *(Checkbox reflects schedule, not yet-built status; flip to actually-done when step 2 lands.)*
- [ ] **§C1 — Roster redesign spec + WORKFLOW Roles/Stage rewrite** (design surfaced to user first): the function→agent map, the merges/renames/adds, the Stage 2/6/7 framing. Doc + design; no engine spawn changes yet.
- [ ] **§C2 — `implementer-architect`→`implementer`** (strip inline principles → point at CLAUDE.md + standards) + every `nsAgent` spawn + namespace/cross-script pins, lockstep. Lands complete because the rename is mechanical + test-guarded.
- [ ] **§C3 — `plan-reviewer`+`architect-reviewer`→`synthesizer-gate`** (two altitudes) + spawn sites + pins + the whole-feature re-verify scope. Lands complete because the two roles share one posture.
- [ ] **§C4 — `blindspot-reviewer`→`lens-reviewer` whole-scope mode** + `product-critic`→`product-designer` elevate mode + spawn sites + pins.
- [ ] **§C5 — ADD `runtime-qa` (agent, safety/negative paths, intent-vs-behavior line) + ADD `retrospect-harvester` (Stage 9)** + `plugin.json` roster + Land worktree-hygiene check + WORKFLOW Stage-9 wiring.
- [ ] **§C6 — Republish (END only)** — RELEASE_CHECKLIST; **STOP and hand to the user before the force-push** (irreversible/outward). Validate on a real adopter repo after.

---

## Open design questions (for §C's design pass)
- **Placement of the architect-pass / Architecture-fit TEMPLATE section:** land it once (shared with `0025`); it applies to ALL plans immediately (incl. ad-hoc builds and this very plan) — sequence so it isn't authored twice.
- **`synthesizer-gate` two-altitude prompt:** one file with plan/verify modes vs two sharp prompts — keep the merge from flattening the plan-gate vs verify-verdict postures (the Non-goal guardrail).
- **`runtime-qa` agent vs the existing `engine/qa.js` skill seam:** the agent is the missing *role*; confirm how it composes with the QA Workflow script (the script drives; the agent is the spawned runtime reviewer) without duplicating the boot/flow logic.
- **`retrospect-harvester` trigger:** Stage-9 invocation vs a `doctor` check (`0025`) that flags "harvest didn't fire" — avoid two owners of the same signal.
- **Whole-feature re-verify scope source:** the Stage-1 job-to-be-done lives in `docs/claugentic-PRODUCT.md` / the plan — confirm the `synthesizer-gate` can read it on the last slice.

---

## Review  _(filled by plan-reviewer, Stage 3 — before the §C rewrite; §A reviewed with the step-2 spec)_
- **Verdict:** —
- **Required changes:** —
- **Sizing/completeness:** —
- **Harness impact:** —

---

## Spec  _(per slice, after Review passes — Stage 4)_
_To be filled per slice once Review passes (§A specced with the step-2 lens-coverage work)._
