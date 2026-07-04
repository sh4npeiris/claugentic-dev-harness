# 0032 — Skills taxonomy mapping + edge-skill pointers (docs only)

- **Status:** Draft (fine-tuning; verified 2026-07-03). **Blockers:** none. Additive; docs-only; no behavior change. Does NOT touch 0029/0030.
- **Disposition:** done / deferred (ROADMAP) / rejected (DECISIONS) per slice.
- **References:** FINETUNING-INPUTS → VERIFIED · the "how we use skills" blog (9-category taxonomy) · Claude Code `cli-reference`/`common-workflows` (`/loop`, `/goal`) · the slash-command audit in FINETUNING-INPUTS.

## Problem

Two verified, grounded, docs-only opportunities:
1. The harness's own skills (`init`/`audit`/`build`/`product`/`doctor`) + the bundled defaults have **no map to the blog's 9-category skill taxonomy** — a discoverability + design-discipline lens.
2. Several **bundled default skills are genuine edge-adoptions** the harness doesn't reach: `/debug` (an *investigation* front-end for an unknown failure → feeds a `bug` item; the harness governs *fixing* a known bug, not *diagnosing* an unknown one), `/architecture` (a full ADR as a Stage-2 working artifact → distil ONE DECISIONS line at Land), `/skill-creator` (its description-triggering evals for the harness's OWN skills → addresses the stale-eval/BASELINE drift), `/incident-response` + `/deploy-checklist` (the known post-Land ops gap — "lifecycle stops at Land"). These are **pointers**, not custom wiring.

## Goals / Non-goals

- **Goal:** Add WORKFLOW **pointers** to the edge-skills at the right stages: `/debug` as the diagnosis front-end to the `bug` tag (a WORKFLOW tag-table / `reliability-resilience` pointer); `/architecture` as a Stage-2 ADR option (distil to one DECISIONS line); `/skill-creator` for the harness's own skill dev; `/incident-response` + `/deploy-checklist` as post-Land ops pointers for adopters who ship.
- **Goal:** Map the harness's own skills (+ the bundled ones) to the **9-category taxonomy** — a short `SKILLS_TAXONOMY` note or SKILL.md frontmatter — for discoverability.
- **Goal (corrected):** A correctly-scoped `/loop` + `/goal` pointer — as **post-automation** tools (e.g. after `/code-review`/`/debug` closes issues), **NOT** multi-agent orchestration. *(Verified: `/loop` = fixed-interval/self-paced/maintenance modes; `/goal` = condition-persistence. The dossier's "turn/goal/time/proactive" + "spins up its own harness" framing is WRONG — do not use it.)*
- **Non-goal:** Displacing harness-better skills. `system-design`/`tech-debt`/`code-review`/`testing-strategy` are strictly weaker inside the pipeline (single-shot, self-graded) — SKIP them (record the carve-out, don't wire).
- **Non-goal:** Any new skill/agent/engine/command. Pure pointers + a taxonomy map.

## Architecture & holistic fit

- **Codebase fit:** WORKFLOW (pointers) + a small taxonomy note. No machinery. SoC: the harness governs its pipeline; the edge-skills fill the edges it doesn't reach (diagnosis, ADR rigor, ops, its own skill-dev). DRY: pointer-not-restate.
- **Quality dimensions:** `docs-traceability` (primary — the pointers resolve, the taxonomy map is accurate) · `product-ux` (discoverability). Trust surface → `honesty-reviewer` (the harness-better carve-outs are honest; `/loop`-`/goal` uses the CORRECTED framing; no over-claim that a pointer is wired behavior).
- **Future-proofing:** the taxonomy map is the natural home for a new harness skill's category.

## Affected files

- `docs/claugentic-WORKFLOW.md` — edge-skill pointers at the right stages (tag-table `/debug`; Stage-2 `/architecture`; post-Land ops); the corrected `/loop`-`/goal` note; the harness-better SKIP carve-out (one line).
- `docs/claugentic-standards/reliability-resilience.md` — a `/debug` pointer for unknown-failure investigation (if it's the right home; confirm at Spec).
- A short `docs/claugentic-SKILLS_TAXONOMY.md` OR a note in an existing doc — map harness + bundled skills to the 9 categories. *(Confirm at Spec: a new managed doc vs. a note in PLAYBOOK/WORKFLOW — prefer NOT a new managed file unless it earns its `init`/tree surface; KISS.)*
- `docs/claugentic-DECISIONS.md` — one line (edge-skill pointers adopted; `/loop`-`/goal` corrected framing; harness-better SKIP carve-out).
- `docs/claugentic-ARCHITECTURE_TREE.md` — rows for any new doc + updated WORKFLOW row if scope changes.

## Risks & mitigations

- **Risk: repeating the debunked `/loop`-`/goal` "orchestration" framing.** → **Mitigation:** the spec uses the CORRECTED terminology (three loop modes; `/goal` = condition-persistence; post-automation only); `honesty-reviewer` checks it.
- **Risk: a pointer reads as wired behavior.** → **Mitigation:** frame as "consider `/debug` here" (model-upheld option), never "the harness runs `/debug`."
- **Risk: a new managed `SKILLS_TAXONOMY.md` over-adds surface.** → **Mitigation:** prefer a note in an existing doc; only make a new file if it genuinely earns it (YAGNI — confirm at Spec).

## Test strategy

- **Deterministic gates:** `pytest`, `check_shipped_content.py` (new/edited docs — no dangling refs/stranded literals), `check_doc_budgets.py`, `claugentic-check_architecture_tree.py` (any new doc row). Docs-only → no `node`/version-sync surface.
- **Reviewer sign-offs:** `docs-traceability` + `product-ux` via `synthesizer-gate`; `honesty-reviewer` on the `/loop`-`/goal` framing + the pointer-not-wired framing.

## Decomposition (slices)

- [ ] **Slice 1 — Edge-skill pointers + corrected `/loop`-`/goal` + harness-better carve-out (WORKFLOW).** **In-scope:** `docs-traceability`, `product-ux`; trust surface → `honesty-reviewer`.
- [ ] **Slice 2 — Skills-taxonomy map (note or lean doc) + close-out (DECISIONS/tree).** **In-scope:** `docs-traceability`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_

RUNNING AS: Opus 4.x — a clean-context, separate-role gate pass. The planner is also Opus-family, so this is a **same-model** review: a reduction of rubber-stamping risk (independent role + clean context), **not** model-independent verification — blind spots can still correlate.

**Verdict: CHANGES REQUIRED** — the plan is correct, honest, and well-scoped in substance (the `/loop`-`/goal` framing is the CORRECTED one, the harness-better carve-outs are honest SKIPs, the sibling overlaps are clean), but it leaves **two load-bearing decisions unresolved into Spec** where the effort-dial says a docs-pointer plan should make the call now, and it under-specifies one honesty guardrail. None are deep — three tightenings and it's a PASS.

### What I verified independently (not taken on the plan's word)

- **Correctness vs the VERIFIED findings — PASS.** Plan `:17` uses the corrected framing verbatim: three loop modes (fixed-interval / self-paced / maintenance) + `/goal` = condition-persistence, positioned as **post-automation** pointers, and it explicitly names the dossier's "turn/goal/time/proactive" + "spins up its own harness" framing as WRONG. I grepped `.claude/plans/` for `spins up its own harness` / `turn/goal/time/proactive` / `orchestration` — **zero residue** in this plan (the only hits are unrelated lines in 0028). Cross-checked against FINETUNING-INPUTS `:82` — they match exactly.
- **No pre-existing residue to correct.** WORKFLOW.md today has **no** `/loop`, `/goal`, or `/debug` reference at all (grep returned nothing), and there is **no** skills taxonomy anywhere in the repo. So this plan is purely *additive first-introduction*, not a correction of live copy — the debunked framing only ever lived in the (already-corrected) dossier. Good: the risk surface is "does the new copy stay honest," not "did we scrub the old."
- **Dedup vs 0031 / 0033 — clean.** 0031 owns model-tier + platform-advisor + the SessionStart-advisor rename; 0033 owns context-economy/cache grounding. 0032 touches none of those files' concerns. Confirmed it does **not** absorb the REFUTED audit items (init-description trim / skills-gotchas) — those appear nowhere in 0032's scope, and its Non-goals correctly fence "no new skill/agent/engine/command."
- **Harness-better carve-out — honest.** `:18` SKIPs `system-design`/`tech-debt`/`code-review`/`testing-strategy` (record the carve-out, don't wire), matching FINETUNING-INPUTS `:64`. Correct.

### Required changes (numbered, actionable)

1. **[Slice 2] Decide NOW, don't defer to Spec: kill the new managed doc.** The plan lists `docs/claugentic-SKILLS_TAXONOMY.md` **OR** a note in an existing doc, deferring the choice to Spec (`:31`). For a docs-only plan this is exactly the decision the plan-gate exists to force, and the evidence points one way: a new managed doc is **not** a cheap file. It would need a row in `init`'s managed-set upsert table (`skills/init/SKILL.md:137-145`), a managed-stamp, REFRESH/CURRENT handling, a release ship/strip classification, a tree row, **and** a CLAUDE.md `harness:managed` fence pointer to be discoverable (`skills/init/SKILL.md:624-636`) — the whole "7-hand-lists-for-1-fact" surface the Track-B consolidation is trying to *shrink*. A ~9-row taxonomy map does not earn that. **Resolve the plan to: a note in an existing doc (PLAYBOOK or WORKFLOW), NOT a new managed file.** Keep "confirm exact host doc at Spec," but the *new-managed-file* option should be struck here, not carried as a live fork into Spec. (This also removes the "new doc row" clauses in *Affected files* `:33` and the tree/DECISIONS lines — no new file means no new row.)

2. **[Slice 1] Confirm — and state in the plan — that `reliability-resilience.md` is the WRONG home for the `/debug` pointer; the WORKFLOW tag-table is the right one.** The plan hedges the `/debug` home twice (`:30` "if it's the right home; confirm at Spec"). I read `docs/claugentic-standards/reliability-resilience.md`: it is a pure **auditable-dimensions catalog** (Good-looks-like / Auditor-checks / Confidence / Tradeoff / Sources per dimension) with an explicit *additive-floor, never-delete* authoring contract (`:84-89`). A "consider `/debug` to investigate an unknown failure" pointer is **process guidance, not an auditable quality dimension** — it doesn't fit the module's shape and would be the first non-dimension prose in it. The genuine home is the **WORKFLOW `bug`-tag row** (`docs/claugentic-WORKFLOW.md:220`, the tag→discipline table), where `/debug` naturally reads as the *diagnosis front-end feeding a `bug` item* — precisely the FINETUNING-INPUTS `:59` framing. **Drop `reliability-resilience.md` from Affected files** (or, if you want a standards-side breadcrumb, it belongs in `testing.md`/process copy, not the resilience dimension list — but WORKFLOW alone is sufficient; adding a second home is DRY-violating). Making this call now also shrinks Slice 1 to a single-file edit.

3. **[Honesty — Slice 1] Make the "pointer-not-wired" rule a concrete copy constraint, not just a risk line.** The Risks section (`:38`) says "frame as 'consider /debug here,' never 'the harness runs /debug.'" That's the right instinct, but it lives in Risks, not in the deliverable spec. Because every one of these five pointers (`/debug`, `/architecture`, `/skill-creator`, `/incident-response`, `/deploy-checklist`) is an **edge-skill the harness does NOT reach**, each pointer must read as an *adopter-optional, model-upheld consideration* — never as harness behavior. Add one explicit Slice-1 acceptance line: *"every edge-skill pointer is phrased as a model-upheld option the agent/adopter may reach for ('consider …'), never as wired harness behavior; `honesty-reviewer` gates this."* This is the load-bearing trust check for the whole plan — pin it as an acceptance criterion, not a mitigation aside.

### Sizing / completeness check (per slice)

- **Slice 1 (edge-skill pointers + corrected `/loop`-`/goal` + SKIP carve-out, WORKFLOW) — OK, and tighter once #2 lands.** Single-doc (WORKFLOW) edit after dropping `reliability-resilience.md`. Lands vertically complete: pointers + the corrected note + the one-line carve-out, no half-state, no TODO. Session-sized comfortably. In-scope dimensions (`docs-traceability`, `product-ux`, `honesty-reviewer`) are the right set.
- **Slice 2 (taxonomy map + close-out) — OK once #1 lands.** As a **note in an existing doc** (not a new managed file) plus the DECISIONS line + any tree touch, it lands complete and small. As-drafted (with the live new-managed-file fork) it is *under-decided*, not over-sized — #1 resolves it. The DECISIONS one-liner + tree update are the correct close-out. No dangle.
- **Two-slice split is right.** Slice 1 (pointers/framing — the honesty-heavy surface) and Slice 2 (the taxonomy map + close-out) are cleanly separable and each independently landable. No merge/split needed.

### Honesty check — PASS (with #3 as a hardening, not a gap)

The `/loop`-`/goal` copy is the corrected three-modes/condition-persistence framing (not orchestration); the harness-better skills are honest SKIPs (recorded, not wired); no pointer is claimed as wired behavior in the plan's own copy. The one gap is *procedural*: the pointer-not-wired rule sits in Risks rather than as a Slice-1 acceptance criterion (#3). `honesty-reviewer` is correctly named on the trust surface for both the framing and the pointer-phrasing. No over-claim, no laundering of model-upheld judgment into mechanical fact.

### Harness impact

**No new hook, agent, STANDARD, engine, or command** — the Non-goals hold. The one latent harness-surface risk is the *new managed doc* in Slice 2, which #1 removes: keeping the taxonomy as a note in an existing managed doc means **zero** new init/managed-set/release/tree surface. No Stage-9 mechanism change implied. Confirmed: does **not** touch 0029/0030's landed work, and does not overlap 0031/0033. If the taxonomy map later grows into something that genuinely wants its own file, that is a separate ROADMAP call — YAGNI says not now.

_Re-gate after the three changes fold into the plan; expected → PASS._

## Spec  _(per slice, Stage 4)_

### Plan-gate resolutions (folded into scope — the plan is now single-doc + simpler)

- **R1 — no new managed doc.** The `SKILLS_TAXONOMY.md` option is **dropped**; the 9-category taxonomy map lives as a **note in an existing doc** (a new managed file costs an `init` managed-set row + stamp + REFRESH/CURRENT handling + release ship/strip class + a tree row + a fence pointer — a ~9-row map does not earn that). Home: a short subsection in `docs/claugentic-WORKFLOW.md` (beside the tag→discipline table); Spec default WORKFLOW.
- **R2 — `/debug` home is the WORKFLOW `bug`-tag row, not `reliability-resilience.md`.** That module is a pure auditable-dimensions catalog with a never-delete authoring contract — a process pointer doesn't fit its shape. **Drop `reliability-resilience.md` from Affected files.** The `/debug` diagnosis-front-end pointer goes on the WORKFLOW `bug`-tag row (`docs/claugentic-WORKFLOW.md:220`). This **shrinks the plan to a single-file WORKFLOW edit** (all edge-skill pointers + corrected `/loop`-`/goal` + harness-better SKIP + `/debug` bug-row + the taxonomy note → one file).
- **R3 — pointer-not-wired is a Slice-1 ACCEPTANCE CRITERION, not just a Risk.** Every edge-skill pointer must read as a model-upheld option ("consider `/debug` here"), never wired behavior ("the harness runs `/debug`"). `honesty-reviewer` verifies this pass/fail, plus the corrected `/loop`-`/goal` framing (no "orchestration"/"spins up its own harness" residue).
- **Revised affected set:** `docs/claugentic-WORKFLOW.md` (all of the above) · `docs/claugentic-DECISIONS.md` (one line) · `docs/claugentic-ARCHITECTURE_TREE.md` (WORKFLOW row only if its scope-line changes). No new managed doc; no standards-module edit. The 2 slices collapse toward one WORKFLOW-centered slice + close-out.
- **Status: ready to implement** (plan-gate CHANGES-REQUIRED resolved; expected PASS on re-gate).
