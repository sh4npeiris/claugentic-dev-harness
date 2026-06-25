# 0025 — Unified finder→select→plan→build pipeline (+ doctor)

- **Status:** Draft outline — captured from design conversation; needs its own design + plan-reviewer pass. **Depends on `0024`** (plan-lifecycle S5; the pre-commit + init patterns).
- **Resumable from:** flesh out the Approach into per-slice specs after 0024 lands and this outline is reviewed.
- **Blockers:** 0024 not yet landed.
- **References:** `skills/audit/SKILL.md` · `skills/product/SKILL.md` · `skills/build/SKILL.md` · `engine/audit.js` · `docs/claugentic-WORKFLOW.md` · `.claude/plans/0024-harness-context-and-lifecycle.md`

## Problem

The harness has three "finders" of work, but the lifecycle from *finding* to *doing* leaks effort and bloats the backlog:

1. **No selection gate before elaboration.** `audit` writes **all** surfaced findings into the backlog; the user later has to weed it. Worse, when building, specialists **Spec/research items the user then rejects** (the workflow Specs at Stage 4 *before* Approve at Stage 5) — the user's real pain: *"plans had steps I didn't want; I had to force-complete after specialists had already spec'd."*
2. **No shared scaffold step.** A selected item becomes a backlog line with no groundwork; build re-derives context from scratch.
3. **Finders dead-end.** After an audit/product run the user must manually re-invoke `/build`; the find→do flow isn't continuous.
4. **No harness-health finder.** `doctor` (the harness's own-hygiene checker — distinct from `audit`, which targets *your code* against *standards*) does not exist; the gates (tree, version-sync, doc-budgets, stale plans, init post-conditions, Stage-9 capture) run ad-hoc inside Verify/Land.

## Goals / Non-goals

**Goals**
- One **shared finder pipeline** — `FIND → user multiselect → produce a full plan per selected item → offer build` — reused by `audit`, `doctor`, and `product` gap-mode (DRY).
- The multiselect **is** the scope-selection gate (**item-level**): unselected findings are dropped (no backlog bloat). **Because selection already gates what's wanted, each selected item gets the specialist-produced PLAN preemptively** (problem · approach · decomposition), not a token stub.
- The **deep per-slice SPEC stays just-in-time inside build** (existing Stage-4) — not because items are unwanted (selection settled that) but because per-slice spec is the existing step-pruning gate and is cheaper JIT than deep-speccing every slice upfront. Step-level control = plan-review/approve + 0024 disposition.
- The **initial-plan agent does an architect-level holistic pass** — a required *Architecture & holistic fit* plan section (codebase fit/layering/modules/design-patterns/SOLID · product fit · the quality dimensions to uphold, mapped to `docs/claugentic-standards/` · extensibility/future-proofing) — so architecture is framed **from the start** and guides downstream agents, countering the observed "model-upheld ⇒ agents sometimes skip architecture." Structurally prompted (template forces the section) + `plan-reviewer`-audited; **YAGNI-balanced** (holistic ≠ gold-plated).
- Build `doctor` fully on this pipeline: **diagnose → report → multiselect → treat-on-approval → offer build**; mechanical fixes applied directly on approval (never silently, no new hook), substantive ones planned + offered to build.

**Non-goals**
- **Full upfront per-slice SPEC** of all selected items (the deep Spec is JIT per slice inside build; the PLAN *is* done upfront on selection, the Spec is not).
- **Forced** auto-build (build is *offered* after selection; default is "leave in backlog").
- Engineering→product graduation (rejected in 0024).
- A new always-loaded doc or a new hook (doctor stays user-invoked; honesty posture: only the tree gate is mechanical, now at commit altitude).

## Approach (to be specced)

**The shared finder contract.** A finder produces a candidate list, then:
1. **SELECT** — present the candidates as a **multiselect** (anti-bloat; the user picks what to act on, the rest are dropped — honoring the existing `rejected-findings` / `rejected-proposals` memory so a dropped item stays dropped).
2. **PLAN (preemptive, per selected item)** — a specialist (`Plan`/architect + `plan-reviewer`) produces the item's **full plan file** in `.claude/plans/` (problem · **Architecture & holistic fit** · approach · decomposition · the finding's evidence/`file:line`) **and** a one-line ROADMAP item. The agent does the **architect-level holistic pass** (below); only the **deep per-slice Spec** is deferred to build (which has deeper code context — user-confirmed).
3. **OFFER BUILD** — ask *"build these now, or leave them in the backlog?"* If build: enter the build loop. If not: the plans + backlog lines persist for a later `/build`.
4. **BUILD (JIT spec per slice)** — build works items **one at a time**, each starting from its pre-made plan; per slice the **Spec → Approve → Implement → Verify** runs as build reaches it (existing workflow). Step-level pruning happens at plan-review/approve and 0024 disposition — so no slice is *deep-spec'd* before its turn, and unwanted steps are cut without waste. Build keeps its per-item checkpoints (before code / land / irreversible).

**Commitment — not capture — triggers the plan.** A *committed* item (one you select to do) auto-gets its plan via step 2 (with the architect-pass). A raw *capture* (a bug or idea jotted to the **Bugs/Later** zone) stays a **planless one-liner until you commit it** — so quick capture stays cheap and planning is never front-loaded onto un-prioritized items (the wasted-effort guard). "Adding to the roadmap" = **committing** = the plan trigger; the capture zones are a cheap inbox that doesn't. (Trivial/mechanical items skip even this — `doctor` or a small inline fix just does them, no roadmap, no plan.)

**ONE planning process, every scenario (auto-triggered OR ad-hoc "build feature X").** No weak ad-hoc path where architecture gets skipped. **It expands WORKFLOW Stage 2 (Plan) into a 3-step sub-process, keeping Stage 3 (Review) as the gate "as before":**
- **2a Draft** — Claude's **plan mode** + `Plan` agent → output **structured by the TEMPLATE** (architect-pass = the forcing function).
- **2b Specialist deep-dive + feedback** — a scoped panel (in-scope standards lenses + `architect-reviewer` + `yagni-sentinel`, + `honesty-reviewer` on claims, + `product-designer` if user-facing) review the plan's **design** and give **advisory** feedback (builder-class — they *contribute*, not gate). Reuses the **Verify-panel machinery** (`engine/verify.js` pattern; add a `plan-design-review` mode to `lens-reviewer` beside its diff/audit modes). This **formalizes + standardizes** the diverse-panel-at-Plan the workflow already gestures at (WORKFLOW.md:36, currently contested-only + prose-convened) into a standard Stage-2 sub-step for substantial work.
- **2c Planner incorporates** the feedback → refined plan (loop 2b↔2c as needed).
- → **Stage 3 Review** (`plan-reviewer`, the adversarial **gate** — judge-class) verdicts the refined plan as before → **Stage 5 approve**.

**Same panel, two altitudes (the right-size on "all agents"):** 2b reviews **design** (advisory); Stage 7 Verify reviews **code** (gate) — most lenses contribute at both; security/perf do design-level threat-model/complexity at plan, concrete violations at verify. **Scoped + dial-able** (only the architect-pass's named dimensions; trivial changes keep the lightweight path — not all lenses every plan). **Enforcement = model-upheld + structurally-prompted** (skill flow requires the plan; template forces the sections; 2b panel + Stage-3 gate) — optionally a cheap "plan file exists + required sections non-empty" presence check, but quality stays reviewed.
- **Iteration is the enforcer (loop to a fixed bar).** Quality is upheld by *looping until the gate passes*: **2b↔2c** is **bounded** (1 round default — advisory has no natural stop; the planner decides if another round genuinely adds value, diminishing returns) · **2↔3** loops until `plan-reviewer` **PASS** · **6↔7** loops until the **DoD is green**. Three guardrails make iteration *enforce* rather than spin/cheat: **(1) a fixed, finite bar** (DoD / Stage-3 criteria) so loops terminate — "meet the bar, then stop," never "until perfect" (WORKFLOW.md:135); **(2) a cap → escalate to the user** if a gate won't converge (never loop forever, never fail-open by lowering the bar — `engine/build-item.js` carries the build cap → PARTIAL/escalate); **(3) clean-context adversarial gates** so a PASS is genuine, not the builder rubber-stamping its own rationale. The loop enforces deterministic gates *strictly* and reviewer gates as far as the reviewer's *judgment* — it never turns a model-upheld gate mechanical, just refuses to stop short of it.

**Architect-level holistic pass (the plan's load-bearing addition).** Because architecture is model-upheld, agents sometimes skip it — so the plan TEMPLATE gains a required **Architecture & holistic fit** section the initial-plan (architect) agent must fill: how the item fits the **codebase** (layering · module placement · design patterns · SOLID / separation-of-concerns) · how it fits the **product** · the **quality dimensions to uphold** (maintainability · performance/efficiency · security · reliability · extensibility — each mapped to its `docs/claugentic-standards/` module so the standards frame the plan rather than being discovered late) · **future-proofing**. These are **initial architect thoughts / placeholders**, NOT the deep per-slice Spec (that stays JIT in build) — but they EXIST from the start and **guide every downstream agent** to uphold them. Enforcement = **structural prompt + review**: the template forces the section to exist and `plan-reviewer` audits it is genuinely reasoned (not hand-waved) — you can't mechanically grade architecture, but you can require the section and review it. **YAGNI-balanced** (the existing `yagni-sentinel`): holistic ≠ gold-plated — the section frames what to uphold, not a mandate to build every abstraction now. Plans are ephemeral (deleted at Land), so a richer plan is working scaffolding, never context-bloat. **Surfaces:** `.claude/plans/TEMPLATE.md` (the new section) · the `Plan` agent's mandate · `plan-reviewer`'s audit checklist.

**doctor (the harness-health finder).** Diagnose = run the existing `claugentic-check_architecture_tree.py` + `check_versions_synced.py` + `check_doc_budgets.py` (incl. the new INVARIANTS cap) + scan `.claude/plans/` for landed/cold plans + re-assert init post-conditions (pre-commit wired; managed stamps current; plugin self-ref present in shared mode) + flag recent lands lacking a DECISIONS/INVARIANTS/standards touch (Stage-9 "did the harvest fire?"). **Report** a green/WARN/breach table (default = report-only). **Treat** (on approval): **bounded, reversible, no-architectural-decision fixes are applied directly — no plan needed** (delete a landed/cold plan · re-wire the pre-commit hook · apply an approved **doc-condensation** diff for an over-budget ledger · **tree hygiene** — add a missing entry / drop a stale one / condense an oversized entry). The "just-do-it, no plan" threshold = *bounded + reversible (git history) + no architectural decision*. Anything **substantive** is **not** done here — it's added to the roadmap, which **auto-triggers a plan** (see *Commitment triggers the plan*, below) and is offered to build. Name = `doctor`; treats on approval, never silent, no hook. **Where findings go:** most are **fixed on approval** (no backlog home needed); the report is a **transient snapshot** (regenerates, doesn't accumulate — like audit's overview). A *deferred substantive* finding goes to the **ROADMAP** (kept together, not a separate file) but needs **no new section**: in the harness's **own** repo it's normal **Quality/Feature** work (the harness *is* the product); in an **adopter** repo it's tooling-maintenance → the existing **Later** parking lot with a `harness`/`maintenance` **tag** (distinguishable without a new section). A dedicated *Maintenance* section only if volume ever warrants (YAGNI — doctor fixes most on the spot).

**Retrofits.** `audit` (Phase 3) and `product` gap-mode gain the SELECT step *before* writing the backlog fence (today audit writes the whole fence). `build` gains "start each item from its pre-made plan + JIT per-slice spec" and the post-selection build-now offer. `docs/claugentic-WORKFLOW.md` Stage ordering reflects scope-approval-before-deep-spec.

## Open design questions (for this plan's own design pass)
- Plan-file lifecycle when many are created at once on a bulk selection (ephemeral — deleted at Land per 0024 — but a large multiselect creates several upfront; bound the upfront planning work, e.g. plan-on-select vs plan-when-build-reaches-it for very large selections).
- How multiselect is surfaced (AskUserQuestion vs a checklist fence the user edits) — and how it scales past ~4 items (AskUserQuestion caps options).
- Bounds on doctor's "mechanical treat" set (what is safe to apply on approval vs must route to build).
- How the SELECT step composes with `engine/audit.js`'s current "render the whole backlog" return (gate which findings render, vs render-then-prune).
- Whether `audit`'s lens *selection* (Phase 1 candidate modules) is also surfaced for user multiselect (the user asked "are all 10 standards considered?" — they're a relevant subset; selection could expose it).
- Where the "Discovered while working" bug entries (0024 S5) feed into this pipeline's SELECT step.
- **Placement of the architect-pass / Architecture-fit template section:** land it here in 0025 (with the pipeline), or **pull the TEMPLATE + `Plan`-agent mandate + `plan-reviewer` audit forward into 0024** — it's small and applies to ALL plans immediately (incl. ad-hoc builds, and this very plan), so there's a case for sooner.
- **→ PLAN 0026 — "the conceptual spine" (unified plan+implement on native capability + standards/agents/skills formalization).** Bigger than just planning; the same pattern applied to plan AND implement. Scope:
  - **Native Claude capability does the *creation*** — **plan** (plan mode, 2a) + **implement** (6). The harness *enables* (best prompt + spec + isolation), never wraps/handicaps. Drop the "architect" wrappers.
  - **Standards = the lens library** (single source of the quality bar); **`lens-reviewer` = the one generic agent that applies a standard** (N standards, 1 agent). **Review BOTH plan (2b, design) and code (7, verify)** with the in-scope lenses + cross-cutting critics, then **synthesize → iterate to the gate**.
  - **Agents are three kinds:** generative (→ native capability), lens (`lens-reviewer`×standards), critic/gate (`plan-reviewer`·`finding-verifier`·`yagni`·`honesty`·`blindspot`·`product-designer`·`product-critic`). **Agents never duplicate standards content (DRY)** — they point at the catalog. **"Architect" dropped as an identity** (the architectural thinking = the template architect-pass + the standards lenses).
  - **Agent-roster — TOP-DOWN REDESIGN from the pipeline's distinct functions** (the current set grew organically — vanity "architect" labels, duplicated principles). Design capability-first: agents map to FUNCTIONS, steps COMPOSE them (some steps use several agents; some agents serve several steps). Kinds: generative→native (plan, implement); **lens**→`lens-reviewer` (apply ONE standard; modes plan-design/verify-diff/audit-scope); **critics**→`yagni`·`honesty`·`blindspot`; **gates**→`plan-reviewer`·`synthesizer`·`finding-verifier`(refute); **product**→`product-designer`·`product-critic`.
    - **Renames/slims:** `implementer-architect`→`implementer` (**strip SOLID/DRY/KISS/YAGNI — point to CLAUDE.md principles + standards, DRY**); `architect-reviewer`→`synthesizer`.
    - **Consolidation candidates (conservative — consolidate for DRY, not for a smaller count):** fold `blindspot-reviewer` into a `lens-reviewer` **whole-scope (no-single-standard) mode**; *possibly* merge `plan-reviewer`+`synthesizer` into one gate with plan/code modes. **Keep distinct postures separate** (find vs refute vs gate vs synthesize vs critique) — a focused single-posture prompt is more prescriptive than a multi-mode one.
    - **Gap discovered (pipeline-first lens found it):** a **`retrospect`/learning-harvester** role — Stage 9 is currently manual + silently no-ops.
    - **Rewrite with prescriptive, intentional wording**, each agent facilitating its pipeline function; reference the standards catalog, never duplicate it.
    - **Caveat — coordinated change:** `engine/verify.js`/`audit.js` spawn agents by **namespaced id**, and `agent-namespace`/`cross-script` tests pin them — any rename/consolidation updates engine + tests in lockstep (not a free `.md` edit).
  - **FIRST-PRINCIPLES VALIDATION (workflow wf_0ba75e61, 2026-06-24 — 3 independent rosters with NO sight of ours + research + red-team).** Verdict: **we were close — ~8 core decisions independently re-derived** (parameterized `lens-reviewer` = 4-of-4 with identical rationale; isolated `implementer`; clean-context `finding-verifier`; `yagni`; `honesty`; blindspot; synthesizer-as-integrator; native generation stays with the orchestrator). **Roster deltas this forces:**
    - **ADD `runtime-qa` as a real AGENT** (we had only a skill) — unanimous 3-of-3 gap; *static review can't tell "reads correct" from "runs correct."*
    - **MERGE `plan-reviewer` + `architect-reviewer` → one `synthesizer-gate`** (integrate→verdict→loop at two altitudes) — 3-of-3 said we carry one role too many; consistent with architect-reviewer's existing two modes. **CONFIRMED (user 2026-06-24): merge** (two modes of one judging role — plan-gate altitude / verify-verdict altitude).
    - **ADD `retrospect-harvester`** (Stage 9) — our gap, independent-#2-confirmed.
    - blindspot → whole-scope **mode** of `lens-reviewer` (confirmed); **`product-critic` CONFIRMED demoted → a `product-designer` ELEVATE mode** (one agent file, two SHARP mode-prompts: discover + elevate; product work runs discover→then a FRESH elevate pass over the drafted spec — builder-class creative challenge on the same artifact, NOT a clean-context gate, so no separate-agent independence needed).
  - **RED-TEAM — bulletproofing fails STRUCTURALLY, not in the roster (the higher-value finding):**
    - **★ Lens-completeness = the SECOND mechanical gate.** `verify.js` only validates each `args.dimensions` slug is a real module, never that the set is COMPLETE for the diff → an un-selected lens = a dimension with ZERO review, all gates green (e.g. SSRF un-audited because only `{maintainability,testing}` were named). **Fix: drive lens-selection from the `load_scope:{keywords,globs}` frontmatter that ALREADY EXISTS in each standards module; assert every module matching the changed files is present; FAIL LOUD.** Converts the biggest model-upheld gap to MECHANICAL, no new agent. Meets the enforce-bar (silent · compounding · cheap+deterministic) — a sibling to the tree gate. **PLACEMENT (my call, user delegated): stays in 0026 in lockstep with the `verify.js` rewrite (avoids editing verify.js twice) — the #1 build item in 0026. Split standalone-early into 0024 only if wanted sooner.**
    - **Force the testing lens MANDATORY + adversarial** on any test-diff ("prove these assertions didn't get weaker") — closes builder-written-test-weakening (green suite hides a loosened assertion; `finding-verifier` only refutes surfaced findings, a weakened test surfaces none). A `lens-reviewer` mode + a forced-inclusion rule.
    - **Push `runtime-qa` onto the safety/negative paths** for high-risk tags (run the down-migration forward-and-back, trigger the rollback/flag, inject the error the branch handles) — closes "present-in-code-but-never-exercised."
    - **Whole-feature re-verify** on the last slice of a multi-slice plan (synthesizer, whole-feature scope vs the Stage-1 job-to-be-done) — closes cross-slice integration regressions.
    - **Intent-vs-behavior** line in `runtime-qa`/`product-designer` Verify output (criteria are a shallow proxy); **Land-stage worktree-hygiene** check (abandoned/escalated slice left clean/disposed). All are added responsibilities/modes + a few lines in `verify.js`/`WORKFLOW.md` — **NOT new agents.**
  - **Invariants to preserve when slimming:** worktree **isolation** for parallel implement · the **spec contract** · the Verify **synthesis** step · reviewers stay **clean-context** (native-implement, separate clean-context review).
  - Surfaces: `docs/claugentic-WORKFLOW.md` (Stage 2/6/7 rewrite + Roles section), `.claude/agents/*` (rename/slim/strip-standards), `engine/verify.js` (+ a `lens-reviewer` plan-design-review mode), `.claude/plans/TEMPLATE.md`. **Decision: confirm 0026 scope (this) + sequencing vs 0024/0025.**

## Decomposition (sketch — to be sized in the design pass)
- [ ] Shared pipeline contract + the scaffold-plan helper.
- [ ] `doctor` (diagnose + report + treat + pipeline).
- [ ] `audit` SELECT-gate retrofit (Phase 3 + `engine/audit.js` seam).
- [ ] `product` gap-mode SELECT-gate retrofit.
- [ ] `build` "start from pre-made plan + JIT per-slice spec" + the build-now offer + WORKFLOW Stage ordering.

---

## ★ Audit lens-coverage integrity — a CURRENT BUG in `engine/audit.js` (do EARLY)

**Symptom (observed on 0.2.4, real adopter audit):** a `standard` run over a large repo (8 lenses × 8 dirs = 64 cells) at `maxCellsPerRun: 28` returned `PARTIAL` with **4 of 8 lenses never run** (zero findings) + a 5th half-covered. No lens was truncated mid-run (each that ran ran to full `depthForDial`); the budget dropped **whole lenses**.

**Root cause (verified in code):** `enumerateCells` (audit.js:316-331) orders cells **module-major** (`m0×d0…m0×dN, m1×d0…`); `applyCellBudget` (audit.js:336-341) is a flat prefix `slice(0, N)`. Any `N < total` consumes the first lenses fully and **starves the tail to zero**. No interleaving, no per-lens floor.

**It violates the documented promise.** `skills/audit/SKILL.md:184`: *"all relevant lenses run at every level — depth, never lens-count, is the lever."* Dial = DEPTH (focused/deep/exhaustive + blindspot/yagni at thorough); cell-budget = a SEPARATE cost/context bound. So a `standard` pass SHOULD hear from every lens (at deep depth) — the fix **aligns the engine with the promise**, NOT "make standard like thorough."

**Why the cap exists (the real ceiling):** `maxCellsPerRun` bounds the **synthesis context** — N finder outputs in one dedup/prune pass. "Just run at N=64" only works when the synthesizer can hold 64 outputs; on a big repo it can't (that's why the cap was low). So the fix has TWO prongs: make a LIMITED pass cover all lenses, AND make a FULL pass feasible at scale.

**The fix (ranked):**
1. **Interleave + per-lens floor** — enumerate round-robin across lenses (priority dirs inner) + ≥1 cell per configured lens. A budget-limited pass covers EVERY lens's top dirs (broad-then-deep); starvation structurally impossible.
2. **Auto-size the cap** from `lenses × dirs` (clamped to the synthesis ceiling); default to a **full single pass** (`N ≥ total`, one global dedup) when it fits. Stop hand-picking N (28 was a footgun).
3. **Hierarchical synthesis** (per-lens roll-up → global dedup) — raises the synthesis ceiling so a full pass is feasible on LARGE repos. This is what makes "always all lenses" work at scale (not optional for big repos).
4. **Per-lens finding counts (incl. explicit `CLEAN`) in the run report** — confirm "all lenses spoke" before prioritizing (the user's workflow goal).
5. **(Separate, optional) per-dir fan-out** — one agent per `(lens × dir)` for deeper/uniform reading; a DEPTH/parallelism boost, NOT the coverage fix; bounded by the concurrency cap `min(16, cores−2)` + needs #3.

**Acceptance:** a sub-total budget covers every configured lens ≥1 cell (verify via `done-cells`); a full budget completes all lenses in ONE pass with ONE global dedup; the done/pending cell-key ordering stays a deterministic resume contract after the ordering change; per-lens counts (incl. CLEAN) visible.

**Sibling — same principle, two engines.** This (audit: selected lenses don't get STARVED) pairs with 0026's **lens-completeness gate** (verify: all relevant lenses get SELECTED). Together = **"every relevant lens actually runs and reports"** = the harness's core trustworthiness. Treat as one **lens-coverage integrity** theme.

**Ordering impact (RECOMMENDED — confirm):** current bug in the flagship deliverable + self-contained + clear acceptance + tests → **autonomous-tier eligible (like 0024), high-priority, do EARLY** — before the 0025-pipeline / 0026-spine rewrites (both touch `audit.js`/`verify.js` and should build on the fixed cell logic). **New order:** `0024` → **lens-coverage integrity (audit budget + verify completeness) [autonomous, early]** → `0025` → `0026`. Pull 0026's lens-completeness gate forward to pair here.

**Immediate adopter unblock (NOT a harness change; done in the ADOPTER session, not this repo):** re-run that audit at `maxCellsPerRun: 64` (full pass) or resume from the fence — all 8 lenses report now, IF the adopter's synthesis fits 64 outputs (else resume in chunks). The engine fix makes this the reliable default.

---

## Build execution — bootstrapping discipline (active tools ≠ source)

Implementing these plans = using the harness to improve the harness. Manageable because the **active tools and the source are already separate**: the harness RUNNING the build is the **INSTALLED plugin (v0.2.4)** — namespaced agents `claugentic-dev-harness:*` + install-path engine — distinct from this repo's working tree (the source we edit). **No separate clone needed** (source-vs-installed IS the isolation). Disciplines:
1. **Build machinery stays on installed v0.2.4 throughout** — plan-reviewer, implementer, the Verify panel spawn the stable installed agents; editing the source never breaks the active tools mid-build.
2. **Validate engine/agent edits via the TEST SUITE** (`node --test tests/workflows/*.test.mjs` + `python -m pytest`), NOT by live-spawning them. **Never run the half-edited repo-local `engine/*.js` as the build's own Verify** — the one way to break the machinery mid-run.
3. **Edit agent + engine + tests in LOCKSTEP per slice** — a rename moves the agent file, every `nsAgent("…")` spawn, and the `agent-namespace`/`cross-script` pins together.
4. **Republish at the END = the "replace."** RELEASE_CHECKLIST: bump both manifests → `build_release.py --apply` → push `release` → `/plugin update`. Only then do the new agents/engine become the active tools; validate the republished version on a real adopter repo.

**Per-plan risk:** 0024 + the lens-coverage audit fix touch no agent-spawn ids → low bootstrapping risk (engine-script edits still test-validated). 0025/0026 edit agents + engine → full discipline above.

---

## Decision-gated autonomy + async flags (refine the autonomy ladder)

**Today:** `WORKFLOW.md:133` has a BINARY ladder — *checkpoint* (3 routine pauses) vs *build-to-green*. Crude: checkpoint over-stops on ceremony; build-to-green under-surfaces (no async signal). The build skill *aspires* to "pause only for the decisions that are yours" but lacks the mechanism.

**The refined model — decision-gated:**
- **STOP (blocking) ONLY for must-decide:** (a) a genuine design fork (multiple valid options); (b) a spec with a real trade-off to accept; (c) an irreversible/outward action (commit-to-shared · republish · delete user content).
- **RESEARCH, don't ask** — a FACTUAL/technical uncertainty the agent can resolve from official/trusted sources is resolved by research (cited), **never a user stop**. Stops are for the user's PREFERENCE/JUDGMENT, not facts the agent can look up.
- **FLAG (non-blocking)** — a should-know (a judgment call · accepted risk · deviation · low-confidence choice): record a one-line flag + the **chosen default** + CONTINUE. Async-reviewable.
- **SURFACE flags at the close** — the close-out lists all flags ("things to review") so the user reviews async, not mid-run.

**Surfaces:** `docs/claugentic-WORKFLOW.md` (replace the binary ladder with the decision-gated model + flag mechanism) · `skills/build/SKILL.md` (mode handling + the close-out flag summary) · the plan file's Status/Flags block (the running flag list).

**Acceptance:** an autonomous run completes without stopping for anything that isn't a genuine user-action; every non-blocking judgment is flagged with a chosen default + surfaced at close; a factual uncertainty triggers research (cited), not a stop; the three blocking-stop classes always stop.

**Honesty:** model-upheld (the agent JUDGES "is this a real choice?"), not a mechanical gate — the bar is the criteria + examples. A wrong "proceed" is bounded by flag-and-surface (the user sees it at close), so a mis-judgment costs a flagged item to review, not a silent action. **Bootstrapping note:** this run encodes the behavior manually in its kickoff; landing this feature makes it the built-in default for all future runs.

---

## Review  _(filled by plan-reviewer, Stage 3 — after the outline is fleshed out)_
- **Verdict:** —
