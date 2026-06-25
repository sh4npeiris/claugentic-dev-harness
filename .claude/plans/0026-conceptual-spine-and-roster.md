# 0026 — The conceptual spine: native plan+implement + agent-roster redesign

- **Status:** Draft — extracted from `0025`'s scattered notes (the design conversation + workflow `wf_0ba75e61` first-principles validation). Needs its own plan-reviewer (Stage 3) pass before the §C rewrite. **§A's lens-coverage work (loud advisory + presence-check) was PULLED FORWARD and LANDED in build-step 2 (the lens-coverage-integrity phase) — see "Build phasing" below; do NOT rebuild it here.**
- **Resumable from:** **§A's mechanical pieces LANDED in step 2** (the user chose "loud advisory + presence-check" 2026-06-24, resolving the Stage-3 blocker — the full glob-driven mechanical gate was REJECTED so the recorded "`load_scope` is advisory, NOT a gate" decision stands; the presence-assertion + test-diff rule are in-sandbox and need no glob SoT). Next is §C (spine + roster). **The audit-side sibling (0025 ★) also LANDED in step 2.**
- **Blockers:** §C depends on `0025` (the finder pipeline + the Stage-2 plan sub-process it formalizes) and on `0024` (plan-lifecycle disposition). §A (lens-coverage: loud advisory + presence-check) is independent and was built early (step 2).
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
- **Strengthen lens-coverage integrity on both engines** — the audit-side cell fix (`0025`, mechanical/in-engine) + the verify-side **"loud advisory + presence-check"** (§A): a **mechanical presence-assertion** on the panel's OWN outputs (a named lens can't silently no-show) + a **mechanical test-diff rule** (the `testing` lens is mandatory on a test-touching change) + a **model-upheld** loud coverage-gap surfacing driven from each module's *advisory* `load_scope`. The full glob-driven mechanical FAIL-LOUD gate was **REJECTED** (it reversed the recorded "`load_scope` is advisory, not a gate" decision and is structurally mismatched with `verify.js`'s sandbox). `load_scope` STAYS advisory.
- **Right-size the roster top-down from the pipeline's distinct FUNCTIONS** (generative · lens · critic · gate · product), agents map to functions and steps compose them; agents never duplicate standards content (point at the catalog).
- **Close the structural review gaps:** add `runtime-qa` (agent), add `retrospect-harvester` (Stage 9), merge the two judging roles, demote `product-critic` to a `product-designer` mode, fold `blindspot` into a `lens-reviewer` whole-scope mode.

**Non-goals**
- Consolidating for a *smaller count* rather than for DRY — **keep distinct postures separate** (find ≠ refute ≠ gate ≠ synthesize ≠ critique); a focused single-posture prompt is more prescriptive than a multi-mode one. Only merge where the posture is genuinely the same.
- Turning any model-upheld discipline mechanical beyond what's already wired. The mechanical surfaces stay: the tree gate, plus §A's verify-side **presence-assertion** (a named lens can't silently no-show) + **test-diff rule** (`testing` mandatory on a test-diff), and `0025`'s audit cell-budget interleave — **none of which is a completeness gate over the diff**; lens-SELECTION coverage stays model-upheld (`load_scope` advisory).
- A new always-loaded doc or a new runtime hook.
- Re-opening the engineering→product "graduation" idea (rejected in `0024`).

## Build phasing (this plan builds in two non-adjacent steps)

- **§A — Lens-coverage: loud advisory + presence-check → BUILT IN STEP 2 (the lens-coverage-integrity phase).** Paired with `0025`'s audit cell-budget fix (its engine sibling) to avoid editing `engine/verify.js` twice. No agent-spawn-id changes → low bootstrapping risk. The mechanical pieces (presence-assertion + test-diff rule) **LANDED in step 2**; the model-upheld coverage-gap surfacing (piece #3) folds into §C's roster work, **not rebuilt in §C.**
- **§C — The spine + agent-roster redesign → BUILD STEP 4 (last).** Higher-touch: it rewrites the review machinery (which can't review its own rewrite) and edits agents + engine + tests in lockstep. Each new agent/engine design is surfaced to the user for a quick look before implementing (one line, proceed-unless-objected).
- **§0 governance (bootstrapping discipline)** applies throughout the whole multi-plan build (0024→0025→0026).

---

## §0 — Build execution: bootstrapping discipline (active tools ≠ source)

Implementing these plans = using the harness to improve the harness. Manageable because the **active tools and the source are already separate**: the harness RUNNING the build is the **INSTALLED plugin (v0.2.4)** — namespaced agents `claugentic-dev-harness:*` + install-path engine — distinct from this repo's working tree (the source we edit). **No separate clone needed** (source-vs-installed IS the isolation). Disciplines:
1. **Build machinery stays on installed v0.2.4 throughout** — plan-reviewer, implementer, the Verify panel spawn the stable installed agents; editing the source never breaks the active tools mid-build.
2. **Validate engine/agent edits via the TEST SUITE** (`node --test tests/workflows/*.test.mjs` + `python -m pytest`), NOT by live-spawning them. **Never run the half-edited repo-local `engine/*.js` as the build's own Verify** — the one way to break the machinery mid-run.
3. **Edit agent + engine + tests in LOCKSTEP per slice** — a rename moves the agent file, every `nsAgent("…")` spawn, and the `agent-namespace`/`cross-script` pins together.
4. **Republish at the END = the "replace."** RELEASE_CHECKLIST: bump both manifests → `build_release.py --apply` → push `release` → `/plugin update`. Only then do the new agents/engine become the active tools; validate the republished version on a real adopter repo.

**Per-plan risk:** `0024` + the lens-coverage **integrity work** (§A's presence-check + test-diff rule + `0025`'s audit cell-budget fix) touch no agent-spawn ids → low bootstrapping risk (engine-script edits still test-validated). `0025`/`0026` §C edit agents + engine → full discipline above.

---

## §A — Lens-coverage on the verify side: presence-check (mechanical) + loud-advisory selection · BUILD STEP 2

**The gap (verified in code intent).** `verify.js` only validates each `args.dimensions` slug is a real module, never that the set is COMPLETE for the diff → an un-selected lens is a dimension with **zero** review, all gates green (e.g. SSRF un-audited because only `{maintainability,testing}` were named).

**DECISION (user, 2026-06-24 — "Loud advisory + presence-check"; the full glob-driven mechanical FAIL-LOUD gate was REJECTED).** The Stage-3 review found the original "drive a FAIL-LOUD gate from `load_scope.globs`" design (a) **reverses a recorded decision** — `load_scope.globs` is documented in `README.md`/`DECISIONS.md`/`_TEMPLATE.md` as an **advisory relevance HINT, NOT a gate** (never a hard filter; never silently drops a lens — chosen to avoid false-positive storms on adopters off `src/**`), and (b) is **structurally mismatched** with `verify.js`'s sandbox (no filesystem; the diff arrives as opaque strings; a mechanical glob-match would need a hardcoded module→globs SoT that drifts from the 11 files — the exact drift `KNOWN_MODULES` exists to kill). So `load_scope` **STAYS advisory.** The decided design (three pieces):

1. **Mechanical presence-assertion (in-sandbox, honestly mechanical) — `verify.js`.** After the lens fan-out, assert **every dimension named in `args.dimensions` actually produced a lens-reviewer result**; if a named lens silently yielded nothing (spawn error / dropped output), **FAIL LOUD** — never report all-green with a named lens missing from the panel's own outputs. This closes "named but silently skipped" mechanically (a presence check on the panel's OWN results — no fs, no globs, no decision-reversal). Honest claim: a mechanical presence-check, NOT a "completeness gate."
2. **Force-include the `testing` lens on a test-diff (mechanical where the signal is available).** When the change touches test files, the `testing` lens MUST be in the panel (adversarial: *"prove these assertions didn't get weaker"*). The implementer designs the precise mechanism against `verify.js`'s actual inputs (does it receive the changed-file list, or only an opaque diff? — if the file list is available, mechanically require `testing` when a test path is present; otherwise enforce via the caller that prepares `args.dimensions`). Closes builder-written-test-weakening (a green suite hides a loosened assertion; `finding-verifier` only refutes *surfaced* findings).
3. **Loud-advisory selection from `load_scope` (model-upheld — NOT a hard fail).** Strengthen the lens-SELECTION guidance so the caller uses each module's `load_scope` as the relevance hint it already is, and **surfaces any module whose `load_scope` matches the diff but is unselected as a LOUD coverage-gap warning** (the existing `architect-reviewer` `coverageGaps`/`missed_dimensions` is the model-upheld owner; strengthen its prompt + the WORKFLOW/skill selection guidance). Loud, but advisory — honoring the recorded "advisory, not a gate" decision.

**Honesty (critical — the #1 rule):** this adds NO new over-claimed mechanical gate. Only piece #1 (and piece #2 where the file signal exists) is mechanical, and it is honestly a *presence-check on the panel's own outputs*, not a *completeness gate over the diff*. The selection/coverage-gap surfacing (#3) is **model-upheld and must say so**. Do NOT describe §A as "the second mechanical gate" anywhere (update any such copy — the original plan/DECISIONS framing).

**Acceptance:** a panel where a NAMED lens produced no result FAILS LOUD (piece #1); a test-touching diff requires/includes the `testing` lens (piece #2); a module matching the diff's `load_scope` but unselected is surfaced as a LOUD advisory coverage-gap (piece #3, model-upheld); `load_scope` is NOT promoted to a hard gate (the recorded decision stands); the `KNOWN_MODULES`⇄catalog pin stays green; helpers unit-tested in `tests/workflows/verify.test.mjs`.

**Sibling — same theme, two engines.** §A (verify: a named lens can't silently no-show; missed-but-relevant lenses are surfaced loudly) pairs with `0025`'s audit cell-budget fix (audit: selected lenses don't get STARVED — LANDED). Together = the **lens-coverage integrity** theme.

**Bootstrapping:** §A touches `engine/verify.js` + `tests/workflows/verify.test.mjs` (+ possibly the `architect-reviewer`/`lens-reviewer` prompt for #3 and the Verify caller in WORKFLOW/build SKILL) — **confirm no `nsAgent("<role>")` spawn-id rename** → validated by the test suite, low risk; lands before §C touches `verify.js` again. **0026 is higher-touch: surface the concrete `verify.js` seam design before implementing.**

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
- **★ Lens-coverage integrity (verify side)** → §A's loud-advisory + presence-check (the #1 build item; pulled forward to step 2). NOT a mechanical completeness gate — see §A.
- **Whole-feature re-verify** on the last slice of a multi-slice plan (`synthesizer-gate`, whole-feature scope vs the Stage-1 job-to-be-done) — closes cross-slice integration regressions.
- **Intent-vs-behavior** line in `runtime-qa`/`product-designer` Verify output; **Land-stage worktree-hygiene** check (an abandoned/escalated slice is left clean/disposed). Added responsibilities/modes + a few lines in `verify.js`/`WORKFLOW.md` — **NOT new agents.**

### Invariants to preserve when slimming
Worktree **isolation** for parallel implement · the **spec contract** · the Verify **synthesis** step · reviewers stay **clean-context** (native-implement, separate clean-context review).

### §C — Lockstep edit-map + behavior flags (from the spawn-site inventory, 2026-06-25)
**Four surfaces move in lockstep for EVERY roster change:** (1) engine `nsAgent("<role>")` spawn strings (only `audit.js`/`verify.js`/`build-item.js`/`qa.js`); (2) the `.claude/agents/<role>.md` file (+ `name:` frontmatter); (3) **`agent-namespace.test.mjs` `CUSTOM_AGENTS`** (lines 31–42 — the authoritative roster list the test enforces: it strips `nsAgent("<name>")` then asserts NO bare `"<name>"` literal remains in any engine file, incl. comments/`meta.description`); (4) **`plugin.json` `agents` array** (hand-maintained paths, not a glob). `cross-script.test.mjs` pins the `nsAgent` HELPER BODY byte-identical across all four (not role strings) — untouched by renames unless the helper changes.

**Spawn sites that change role string (the concrete edit list):**
- **`implementer-architect`→`implementer`:** `build-item.js:708` (the ONLY spawn — 1:1 rename). Update `meta.description`/comment prose at `:51`/`:703` for accuracy (not test-load-bearing — not bare-quoted). Rename `implementer-architect.md`→`implementer.md`, strip the inline SOLID/DRY/KISS/YAGNI block → point at CLAUDE.md + standards.
- **`architect-reviewer`+`plan-reviewer`→`synthesizer-gate`:** `architect-reviewer` spawns at `verify.js:267` (roster), `verify.js:566` (Verify synthesis verdict), `audit.js:1265`+`:1272` (audit synthesis + respawn). **`plan-reviewer` has NO engine spawn** (orchestrator/skill-invoked) — so the plan side is doc-only + the agent file. **Tools = UNION `Read,Grep,Glob,Bash,Edit`** (Edit comes from plan-reviewer's Review-section write; architect-reviewer lacks it).
- **`blindspot-reviewer`→`lens-reviewer` whole-scope mode:** `audit.js:1206` → `nsAgent("lens-reviewer")` + a whole-scope mode flag in the prompt; `buildBlindspotPrompt` already returns `LENS_SCHEMA`, so the engine schema is unchanged (1:1 slot). Remove `blindspot-reviewer` from `CUSTOM_AGENTS`.
- **`product-critic`→`product-designer` elevate mode:** NO engine spawn (both Stage-1, orchestrator-invoked) — agent file + manifest + `CUSTOM_AGENTS` bookkeeping only.
- **ADD `runtime-qa` / `retrospect-harvester`:** add agent files + manifest. **`runtime-qa` spawn-site DECISION:** qa.js's boot/drive/teardown currently use the **bare built-in `"general-purpose"`** (`qa.js:997/1038/1100`); decide whether any switch to `nsAgent("runtime-qa")` (→ then pinned by the namespace test) or `runtime-qa` is orchestrator-only. `retrospect-harvester` has no engine step (post-Land) → likely orchestrator-only, no spawn pin.

**★ BEHAVIOR FLAGS (not pure renames — verify the merge slots 1:1):**
- **`synthesizer-gate` must serve THREE distinct contracts/altitudes** the merge collapses: (a) **plan-gate** (plan-reviewer's Review-section edit, Stage 3) · (b) **verify-verdict** (`verify.js:566` synthesis, `SYNTHESIS_SCHEMA` = PASS/CHANGES_REQUIRED + `missed_dimensions`/`dod_check`/`reported_model_family`) · (c) **audit-synthesis** (`audit.js:1265` consolidate, a DIFFERENT schema = `items`/`cuts`). The engine schemas are UNCHANGED — the spawn is a 1:1 name swap **iff the merged agent honors whichever schema/prompt the caller passes** (mode-dispatched prompt). Confirm this before landing — it's the one place the merge could regress Verify.
- **`product-critic`→mode reversed a recorded SRP DECISION — RESOLVED (USER-APPROVED 2026-06-25).** `product-critic.md:8` + DECISIONS asserted "SRP-separate, never a mode." The user approved the supersession; a **superseding DECISIONS entry is recorded** ("Roster maps to distinct functions/postures, not 1:1 to a label — same-posture consolidates into modes"). When §C lands, condense the two old "never a mode" DECISIONS lines + update `product-critic.md`/`blindspot-reviewer.md` content into the merged agents. No longer an open fork.

## Affected files (§C)
- `docs/claugentic-WORKFLOW.md` — Stage 2/6/7 rewrite (native plan/implement framing) + the Roles section (the redesigned roster) + whole-feature re-verify + Land worktree-hygiene.
- `.claude/agents/*` — rename/slim/strip-standards: `implementer-architect`→`implementer`; `architect-reviewer`+`plan-reviewer`→`synthesizer-gate`; `blindspot-reviewer`→a `lens-reviewer` mode; `product-critic`→a `product-designer` mode; ADD `runtime-qa`, `retrospect-harvester`.
- `engine/verify.js` — the `lens-reviewer` plan-design-review mode (composes with `0025` Stage-2b); the `synthesizer-gate` spawn id; the whole-feature re-verify scope. **(§A's presence-assertion + test-diff rule already landed here in step 2.)**
- `engine/audit.js`, `engine/build-item.js`, `engine/qa.js` — every `nsAgent("<role>")` spawn updated for the renames, in lockstep.
- `.claude/plans/TEMPLATE.md` — the architect-pass section is **ALREADY LANDED (0025 Slice 2)**; §C reuses it, does NOT re-author. (plan-reviewer's audit-checklist item 8 also landed → carries through the `synthesizer-gate` rename.)
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
- [x] **§A — Lens-coverage: loud advisory + presence-check** — built in **step 2** (the lens-coverage-integrity phase), with `0025`'s audit cell-budget fix. Mechanical pieces (presence-assertion `finalVerdict` + test-diff `testing`-lens rule) LANDED in `engine/verify.js` + `tests/workflows/verify.test.mjs`; the model-upheld coverage-gap surfacing (piece #3) folds into §C. **DONE-IN-STEP-2; not rebuilt here.**
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

> **Scope of this review:** **§A — the lens-completeness gate** ONLY (the step-2 verify-side sibling). §C (the roster redesign) is a draft and gets its own Stage-3 pass before the §C rewrite. The companion audit-side fix (0025 ★) is reviewed in that file.

- **Verdict (§A only):** `CHANGES REQUIRED` — the design rests on a load-bearing premise that is **half-true**, and the "make it mechanical" core **re-litigates a settled, honesty-load-bearing decision without acknowledging it.** Both must be resolved before a spec.

### 1. The load-bearing assumption — VERIFIED, with a critical caveat
- **`load_scope:{keywords,globs}` DOES exist** in every `docs/claugentic-standards/*.md` module (read all 11 + `_TEMPLATE.md:11-13`). Exact shape:
  ```yaml
  load_scope:
    keywords: [auth, token, ssrf, ...]   # YAML flow-seq of bare tokens
    globs: ["**/auth/**", "**/*.env*"]    # YAML list of double-quoted glob STRINGS
  ```
  Globs are standard `**`/`*` path globs. So "drive selection from `load_scope`" is *feasible in principle*. **BUT:**
- **★ BLOCKER — `load_scope.globs` is documented as "an advisory relevance HINT, NOT a gate."** This is a **settled decision**, stated in three managed places: `README.md:15` (verbatim: *"a hint to be refined per repo, never a hard filter … does not break anything or silently drop the lens"*), `DECISIONS.md:82` (the adopter-aware list: *"`load_scope.globs` is **advisory**, not a gate"*), and `_TEMPLATE.md:11`. The §A goal — *"assert every matching module is present; FAIL LOUD"* — is **exactly the hard gate those three docs say it is not.** Per CLAUDE.md Harness Discipline ("consult DECISIONS before re-litigating"), §A must either (a) be re-scoped to NOT contradict the advisory rule, or (b) explicitly re-open the decision with the user and, if accepted, **update all three docs in the same slice** (a managed-doc change → re-init propagation surface). The plan does neither; it asserts the frontmatter "already exists" as if that settles it. It does not — *existence* was never the question; the docs deliberately chose *advisory*. **The reason it's advisory is load-bearing:** a module's default glob is often `src/**` (see `performance-efficiency`, `reliability-resilience`, `observability-ops`); an adopter whose code isn't under `src/` would have those lenses silently mis-scoped — as a *hint* that's harmless, as a *fail-loud gate* it would block every verify on every such repo (a false-positive storm). The plan's own risk note (0026:130, "tune `load_scope` not the gate") concedes this but treats per-repo glob-tuning as cheap — for an adopter it is editing a **managed copy that re-init overwrites** (DECISIONS.md:25). That is not a viable fix path.

### 2. The engine cannot do what §A asks — a structural mismatch with `verify.js`
- `verify.js` **never receives the changed-files list as structured data it can match globs against.** It gets `args.diffRef` (a string like `HEAD~1`) or `args.files` (an array) — but `args.files` is passed *opaquely* into the lens prompt string (verify.js:421, `JSON.stringify(input.files)`); it is never parsed against globs. And the script is **sandboxed: NO filesystem, NO imports** (verify.js:9-11) — so it **cannot read the `load_scope` frontmatter** off disk to know each module's globs. To make §A mechanical *in the engine*, you would have to (a) require `args.files` always be a concrete file list (not a `diffRef`), AND (b) hardcode every module's globs as a literal in verify.js (a new SoT that drifts from the 11 `.md` files — the very drift `KNOWN_MODULES` + its set-equality pin (verify.test.mjs:100-108) was built to kill), AND (c) implement a glob matcher with no imports. That is a real, non-trivial engine subsystem — **far larger than the "a few lines in verify.js" the plan implies (0026:104, 112).** The plan must either own that scope or move the matching to the orchestrator (model-upheld), which abandons the "MECHANICAL gate" claim.
- **The capability §A wants largely EXISTS already, model-upheld:** `architect-reviewer.md:14` mandates *"flag any clearly-relevant dimension the spec missed"*, the synthesis schema carries `missed_dimensions` (verify.js:363, 380), and `coverageGaps` (verify.js:260-280) already fails loud on a lens that was *selected but didn't run*. So the actual gap is narrower than "no completeness check exists" — it is "the lens-SELECTION step (which modules get named in `args.dimensions`) is model-upheld and the engine doesn't second-guess it." Framing §A as closing a total void over-states it.

### Required changes
1. **Resolve the advisory-vs-gate contradiction FIRST (this gates everything else).** Either re-scope §A to a *non-failing* completeness **prompt** (the synthesizer is already told to flag missed dimensions — sharpen that, keep it model-upheld, drop "FAIL LOUD"), OR formally re-open the `load_scope.globs`-is-advisory decision with the user. If re-opened and accepted: the slice MUST also rewrite `README.md:15`, `DECISIONS.md:82`, and `_TEMPLATE.md:11`, and handle the `src/**`-default false-positive (per-repo glob override that survives re-init) — which makes this **not a low-risk step-2 item.** Do not proceed to spec until this is decided.
2. **If a mechanical gate is still wanted: relocate the glob-matching out of the sandboxed engine.** verify.js cannot read frontmatter or files. Specify where the changed-files→module mapping actually runs (orchestrator pre-step that computes `dimensions` from globs, then passes the *required* set to the engine for a presence assertion). The engine can then mechanically assert "every required module is in `args.dimensions`" — that part IS in-sandbox and sound. Make the honest split explicit: matching = model-upheld/orchestrator; presence-assertion = mechanical/engine. Don't call the whole thing "mechanical."
3. **Re-scope the "few lines in verify.js" estimate.** As written §A implies a small helper; the real change is a new args-contract field (the required-module set), a presence-check helper, its unit test, AND the orchestrator-side selection logic + its documentation. Size it honestly.
4. **Testing-lens-mandatory-on-test-diff (the companion rule) is sound and separable — keep it, it is genuinely cheap and in-sandbox.** Forcing `testing` into the panel whenever the diff touches tests is a clean forced-inclusion rule (it does NOT need glob frontmatter — "diff touches tests" is the trigger, decided where dimensions are chosen). This part can land in step 2 regardless of how #1 resolves. But note: it has the same "where is 'the diff touches tests' computed?" question as #2 — answer it the same way.

### Sizing / completeness check
- **§A as scoped (mechanical fail-loud gate driven from `load_scope`): NOT step-2-ready — split + de-scope needed.** It is blocked on a settled-decision reversal (#1) and a hidden engine subsystem (#2). Forcing it into step 2 "to avoid editing verify.js twice" is a false economy — a half-designed gate is worse than a second edit. Recommended step-2 content: **(a) the testing-lens-on-test-diff forced-inclusion rule** (clean, in-sandbox, test-guarded) **+ (b) a sharpened model-upheld missed-dimension prompt** in the synthesizer. The **mechanical glob-driven gate becomes its own ROADMAP item** behind the #1 decision. That keeps step 2 vertically complete.
- **Pairing claim ("two engines, one theme") is rhetorically neat but the two halves are NOT symmetric:** the audit fix (0025 ★) is a genuine in-engine deterministic fix; §A's mechanical half cannot live in the engine at all. Don't let the "lens-coverage integrity" framing smuggle the harder, contested half in on the coattails of the clean one.
- **Bootstrapping CONFIRMED low-risk** for whatever §A *does* land: it touches `engine/verify.js` + `tests/workflows/verify.test.mjs` only, **no `nsAgent("<role>")` rename** (verified against verify.js spawn sites + the `agent-namespace` pin). Test-suite validation suffices; no mid-step republish. The user's claim holds — but it does not make the *design* ready.

### Harness impact
- **If the gate is built mechanical:** it changes the verify args contract (a new required-module set) — a shared-contract change touching `verify.js`, `skills/build/SKILL.md` (the dimensions arg, SKILL.md:94-95), and `build-item.js`'s verify invocation. That is a Stage-0 "shared contract" trigger → diverse panel, not a quiet step-2 edit.
- **The advisory→gate flip, if accepted, is a DECISIONS reversal + a managed-doc rewrite (README/_TEMPLATE/DECISIONS) → re-init propagation.** Name it as such. Also a candidate INVARIANT (what "complete coverage" means and where it's enforced).
- **`KNOWN_MODULES` drift risk:** any in-engine module-globs literal would need the same set-equality pin treatment as `KNOWN_MODULES` (verify.test.mjs:100-108) or it silently rots. Flag for the spec.

---

> **Combined note (both files):** the two fixes share a theme but not a difficulty. **0025 ★ (audit cell-budget)** is a real, confirmed, in-engine bug with a clean fix — PASS-able once prong #1 is split from the synthesis-ceiling work and the resume-stability test is mandated. **0026 §A (verify completeness)** is blocked on a settled-decision contradiction and a sandbox constraint that prevents the "mechanical" framing from being true as written. Recommend: build the audit fix (prong #1 + per-lens counts) + the testing-lens-on-test-diff rule in step 2; route the glob-driven mechanical gate and the audit synthesis-ceiling work to ROADMAP behind their respective decisions.

---

## Spec  _(per slice, after Review passes — Stage 4)_
_To be filled per slice once Review passes (§A specced with the step-2 lens-coverage work)._
