# 0021 — Harness cleanup batch (de-sediment · distill · flow gaps · hints-file · consumer docs)

- **Status:** Verify SOUND (architect PASS; honesty OVERCLAIMS → 2 should-fixes applied: dead `statusMessage` removed, init readiness line stopped claiming engine-detection → CLEAN) — all gates + 116 pytest + 344 node green. C1 docs + C2 engine-clause + C3/C4/C5 skills+agents + C6 non-adopter note (README, the real surface); **C7 REJECTED** (renderer extraction infeasible — no-imports sandbox, no 2nd consumer). Committing to branch `harness-distillation`.
- **Resumable from:** batch approval → implement `(C1 ∥ C2) → C3 → C4 → C5`
- **Blockers:** runs after 0020 Phase 0 lands (the tree is regenerated to standard first; some entries here are subsumed by A3 — noted per slice)
- **Roadmap item:** Harness distillation effort (sibling of plan 0020)
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · the 2026-06-17 verified diagnostic (every item below traces to a finding ID)

## Problem

The verified diagnostic surfaced a long tail of small, confirmed gaps left by the maturation push: stale leftover, DRY/redundancy, missing flow handoffs, no durable per-repo context slot, and consumer-doc honesty gaps. None is structural; together they are the "distill to essence + close the circle" work. Every item below cites its diagnostic finding ID and a `file:line`.

## Goals / Non-goals

- **Goal:** Land every verified small gap, grouped into coherent slices that each complete in one session with no debt.
- **Goal:** Make the durable-context decision concrete (hints-file → ADAPT: bless the CLAUDE.md per-repo block).
- **Non-goal:** Deeper SRP restructuring of the heavy skills — distillation is **verified redundancies only** (user-locked). The `init`/`build` files stay structurally intact; only the confirmed-redundant prose collapses to pointers.
- **Non-goal:** Re-deriving findings — the diagnostic is the authority; this plan transcribes verified items into slices.
- **Non-goal:** Anything subsumed by 0020 A3 (the whole-tree regen already trims the `test.mjs`/`eval` tree entries — BLOAT-3/BLOAT-4 — so they are NOT re-listed here).

## Approach

Group the ~18 verified items by **nature of change** (which also sets the Verify dimensions and the worktree-conflict order):

- **C1 — Documentation truth pass** (doc-only, no code): leftover paths, honesty gaps, missing navigational notes.
- **C2 — Code/test de-sediment** (engine prompt + a new pin test).
- **C3 — Skill distillation** (verified redundancies → pointers).
- **C4 — Flow handoffs + retrospect + resume** (skill behavioral edits).
- **C5 — Durable user-owned memory** (rejected-findings fence · CLAUDE.md context slot · CANDIDATES affordance · install self-check).

**Worktree-conflict ordering (load-bearing for parallel execution):** C1 (docs) and C2 (engine/test) touch disjoint files → parallelizable. C3, C4, C5 all edit the shared skill files (`init`/`build`/`audit`/`product` SKILL.md) → they MUST serialize (`C3 → C4 → C5`), or worktree merges collide. Execution: `(C1 ∥ C2) → C3 → C4 → C5`.

## Affected files (by slice)

- **C1:** `.claude/plans/TEMPLATE.md` · `README.md` · `docs/claugentic-PLAYBOOK.md` · `.claude/agents/plan-reviewer.md` · `docs/claugentic-WORKFLOW.md` · delete empty `workflows/` dir.
- **C2:** `engine/verify.js` · `engine/audit.js` · `tests/workflows/<new>-agent-crossmodel-pin.test.mjs`.
- **C3:** `skills/init/SKILL.md` · `skills/build/SKILL.md` · (poss. `scripts/claugentic-check_architecture_tree.py` comments).
- **C4:** `skills/init/SKILL.md` · `skills/product/SKILL.md` · `skills/build/SKILL.md` · `skills/audit/SKILL.md` · `docs/claugentic-WORKFLOW.md` · `README.md`.
- **C5:** `skills/audit/SKILL.md` · `skills/build/SKILL.md` · `skills/init/SKILL.md` · `CLAUDE.md` · `docs/claugentic-WORKFLOW.md` · `docs/claugentic-standards/README.md`. *(No tree edit — CANDIDATES is create-on-first-use, prose-only.)*

## Risks & mitigations

- **C3 pointer-collapse drops honesty substance** → honesty-reviewer in-scope at C3 Verify; the pointer must preserve every `[D]`/`[J]` claim, only removing the *restatement*.
- **The stale "three commands" lives ONLY at `ARCHITECTURE_TREE.md:9`** (verified: README:7 already says "The four commands"; PLAYBOOK has no count) → owned by **0020 A3**, whose scope is widened to fix this short factual entry even though it's under the 450 budget (a char-budget regen has no trigger for a count error on a 239-char line). C1 touches the tree for nothing.
- **C5 new fence format drift** → mirror the existing `<!-- product-critic:rejected-proposals -->` fence convention exactly; reuse, don't invent.
- **Worktree collisions on shared skill files** → the serialized `C3 → C4 → C5` order (above) is mandatory.

## Test strategy

C1/C3/C4/C5 are prose — verified by the in-scope reviewers (docs-traceability, product-ux, honesty-reviewer), not unit tests. C2 adds a real deterministic pin test (the cross-model paragraph grep), mirroring `tests/workflows/cross-script.test.mjs` / `agent-namespace.test.mjs`. The tree-form gate (0020 A1) and doc-budget gate (0020 A2) guard every doc edit's form/size on land.

## Decomposition (slices)

- [ ] **C1 — Documentation truth pass.** TEMPLATE.md 4 stale paths → `claugentic-*` (LEFT-1/INCON-2) · delete empty `workflows/` (LEFT-2) · `docs/ARCHITECTURE_TREE` bare shorthand at `plan-reviewer.md:15` + `WORKFLOW.md:32` → concept wording (LEFT-3) · **ADD** a README line: the scripted engine runs via the Claude Code Workflow tool, with an honestly-tagged prose fallback where unavailable — an *addition*, NOT a "Requires Node" fix (README:31 already says only git+Python; there is no "Node" string) (READY-1) · README install-scope/team-distribution note (READY-4) · PLAYBOOK "quick check one file/diff → /code-review·/simplify" (NAV-6) · README/PLAYBOOK "removing or pausing the harness" note (NAV-5). **Phantom removed:** README:7 already says "The four commands" and PLAYBOOK has no count, so the only stale "three commands" is `ARCHITECTURE_TREE.md:9` (owned by 0020 A3). Verify incl. **honesty-reviewer** (README is a trust surface). *Doc-only; parallel with C2.*
- [ ] **C2 — Code/test de-sediment.** Add "locate code via `docs/claugentic-ARCHITECTURE_TREE.md` instead of reading whole files" to `engine/verify.js` Verify-diff lens prompt + `engine/audit.js` `buildLensPrompt` (Self-improve INCON-1) · new grep test pinning the cross-model `RUNNING AS` paragraph across the 4 judge agents (RED-1/REDUN-3 — pin, don't dedupe). *Engine/test; parallel with C1.*
- [ ] **C3 — Skill distillation (verified only).** `init/SKILL.md` idempotency recap (~732-764) → pointer to steps 3-6, ~3K tokens/init (REDUN-1) · `build/SKILL.md` cross-model restatements (242-245, 287-290) → pointer alone (REDUN-2). *Serialized: shared skill files.*
- [ ] **C4 — Flow handoffs + retrospect + resume.** init Next branches → add product pointer (NAV-1) · product spec-mode close-out → "next: gap mode or /build" (NAV-1) · build close-out → also offer "re-run /product gap mode" when product items were in play (NAV-7) · build close-out emits a one-line Stage-9 harvest result + add Retrospect to README lifecycle (NAV-2/FWD-1) · audit + product skills → one-line "interrupted? re-run, it resumes (PARTIAL)" note (NAV-4). *Serialized.*
- [ ] **C5 — Durable user-owned memory.** Rejected-findings memory fence mirroring `<!-- product-critic:rejected-proposals -->` so a re-audit won't re-surface a user-dismissed finding (NAV-3) · bless the **CLAUDE.md per-repo harness block** as the durable structural/domain-context home + agent read-first instruction (GAP-2/hints-ADAPT) · `CANDIDATES.md` → document **create-on-first-use** at `WORKFLOW.md:162` + `standards/README.md` (**prose-only, NO tree entry** — so the tree-gate can't flag a phantom file) (GAP-1) · install self-check readiness line in init Stage-9 report (READY-3). *Serialized.*

---

## Review  _(filled by plan-reviewer, Stage 3)_

**RUNNING AS:** Opus 4.x (cross-model protocol: self-identified family — if the builder is also an Opus-family model, treat this as a same-model review on this run, the judge and the builder are the same model family here).

- **Verdict:** `CHANGES REQUIRED` — the slice grouping and serialize-order are **sound**; the subsumption logic is **mostly correct but has one real double-punt gap**; and **two C1 sub-items are phantoms** (the wrong text doesn't exist on disk). The approach is right; these are corrections to the item list, not a redesign. Verdict is close to PASS.

### Required changes (numbered, actionable)

1. **The `tree:9` "three commands" fix is double-punted — nobody owns it (C1 risk-table L44 + 0020 A3).** Verified: `docs/claugentic-ARCHITECTURE_TREE.md:9` still says *"the three commands: init · audit · build"* and **omits `product`**. C1 (L54) explicitly hands this line to A3 ("tree line owned by A3"); but **0020 A3 will not touch it**: line 9 measures **239 chars — under A3's 450-char budget**, and 0020 A3 (`0020:144-148`) only rewrites *over-budget* entries (the ~14 outliers). A char-budget regen has no trigger to fix a *factual* count error on an under-budget line. So the stale "three" survives **both** plans. Fix one of: (a) add the `tree:9` three→four correction explicitly to C1 (and drop the "owned by A3" claim), **or** (b) amend 0020 A3's acceptance to include "line 9 lists all four commands incl. `product`." Pick (a) — it keeps the de-dup honest and doesn't reach into a different plan's slice. Either way the current risk-table mitigation (L44) is **factually wrong as written** and must change.

2. **Two C1 sub-items are phantoms — the text they "fix" doesn't exist (C1 L54).** Verified on disk: **`README.md:7` already reads "## The four commands"** and lists init · product · audit · build correctly; **`docs/claugentic-PLAYBOOK.md` has no command-count statement at all** (grep: zero "three/four commands" hits). So "README/PLAYBOOK 3-vs-4 commands → canonical four" (READY-2) is **already done in README and vacuous for PLAYBOOK** — the *only* live instance is `tree:9` (see #1). Separately, **`README.md:31` says "Requires `git` and Python 3" — there is no "Requires Node" string to correct**; READY-1's real gap is an **omission** (the README never states the `engine/*.js` audit/build/verify scripts need the **Workflow tool**), not a wrong line to rewrite. Re-word both C1 items: READY-2 → "confirm README four-commands wording is canonical (likely no-op); the only stale count is `tree:9`, owned per #1"; READY-1 → "**add** an honest Workflow-tool-dependency line to README (the audit/build/verify engines run via the Workflow tool; `git`+Python cover only the codebase-map check) — phrase it so it never reads as 'Requires Node'." As written, an implementer hunting for "Requires Node" or a PLAYBOOK "three commands" will find nothing and either no-op or invent an edit.

3. **Name honesty-reviewer in-scope for C1, not only C3 (Risks L43).** C1 rewrites README **capability copy** and (per #2) **adds a dependency-honesty line** — that is a trust/honesty surface by the WORKFLOW diverse-panel trigger (`docs/claugentic-WORKFLOW.md:36`), exactly like C3. The plan scopes honesty-reviewer only to C3's pointer-collapse. Add honesty-reviewer to C1's Verify dimensions (the Workflow-tool line must not over- or under-claim; the four-commands copy must stay honest about `product` being optional).

4. **State C5's `CANDIDATES.md` "create-on-first-use" as the chosen mechanism, and add its tree entry to C5's affected-files (C5 L58).** Verified: `CANDIDATES.md` is referenced live by `WORKFLOW.md:162` and `standards/README.md:26-27` but **does not exist** — GAP-1 is real. The plan lists "`CANDIDATES.md` … in WORKFLOW:162 + standards/README + tree" but never says whether the file is **created now** or stays **create-on-first-use**. Decide explicitly (create-on-first-use is the lighter, YAGNI-correct choice — no empty managed file to maintain). If a `CANDIDATES.md` file *is* created, it needs a tree entry (C5 already lists the tree in affected-files — good); if create-on-first-use, the affordance is prose-only and **no tree entry is needed** — say which, so the tree-gate doesn't flag a phantom.

### Sizing/completeness check (per slice)

- **C1 — Documentation truth pass.** OK as one session *after #1–#3*. Doc-only, disjoint from C2 — parallelism confirmed (C1 touches TEMPLATE/README/PLAYBOOK/plan-reviewer.md/WORKFLOW.md + deletes empty `workflows/`; **zero skill files**). Confirmed live: `workflows/` is empty (LEFT-2 ✓), TEMPLATE stale paths at `:6,:7,:24` (LEFT-1 ✓ — note it's 5 path instances across 3 lines, not "4 paths"; reconcile the count), `WORKFLOW.md:32` + `plan-reviewer.md:15` bare-shorthand (LEFT-3 ✓ — "concept wording" is right; do NOT linkify to a `claugentic-` path).
- **C2 — Code/test de-sediment.** OK. Verified non-redundant: `engine/audit.js` `buildLensPrompt` (`:458-469`) **lacks** the tree-locate line while `buildCriterionLensPrompt` (`:483`) already has it — Self-improve INCON-1 is a real asymmetry, correctly targeted. The new `RUNNING AS` grep test across the **4** judge agents (architect-reviewer/finding-verifier/honesty-reviewer/plan-reviewer — confirmed exactly those carry it) is distinct from `cross-script.test.mjs` (which pins *engine* helpers, not agent prose) — no duplication. Touches no skill file — parallel-with-C1 holds.
- **C3 — Skill distillation.** OK, serialized. init recap at `:732-764` ("Idempotency at a fixed version") and build cross-model blocks at `:242-245`/`:287-290` confirmed. Caveat: the build blocks are **already mostly pointers** ("point there, don't restate") — verify REDUN-2 is collapsing *residual restatement*, not deleting a load-bearing pointer; honesty-reviewer scope (L43) covers this.
- **C4 — Flow handoffs + retrospect + resume.** **OK, do NOT split — but tighten the boundary.** 7 sub-items across 4 skill files + WORKFLOW + README sounds large, but each is a 1–2-line additive insertion (a pointer / a close-out branch / a one-line note), all the *same nature of change* (flow-handoff prose), and they share no logic — this is the kind of homogeneous prose batch that lands clean in one session. The real risk is **not size but file-overlap with C3/C5**, already handled by the serialize order. Keep C4 whole; the cost of splitting (more worktree round-trips on the same shared files) exceeds the benefit. One completeness note: NAV-2 ("build close-out emits a one-line Stage-9 harvest result") must add the line to `build/SKILL.md` step 7/8 **and** the README lifecycle list (`README.md:45` ends the pipeline at "Land" — Retrospect is missing) — the plan says this (FWD-1); ensure both edits land or the slice is half-done.
- **C5 — Durable user-owned memory.** OK, serialized, *after #4*. Rejected-findings fence mirroring `<!-- product-critic:rejected-proposals -->` is the right reuse (convention confirmed live in product-critic.md:22 / product/SKILL.md:67,97). The CLAUDE.md per-repo-block blessing (GAP-2/hints-ADAPT) matches the 0020 P5 ADAPT decision — consistent.
- **Serialize order `(C1 ∥ C2) → C3 → C4 → C5`** — **correct.** Verified C3/C4/C5 all edit `skills/build/SKILL.md` (and init/audit/product); even in disjoint line-regions a file-level worktree merge of parallel branches risks collision, so serializing is the conservatively-right call. C1/C2 are genuinely disjoint from all skills — the parallel claim is sound.

### Harness impact

- **No new STANDARD or agent.** Every item is a transcription of a verified diagnostic finding; honesty-reviewer (existing) is the only role with a scope change (extend it to C1 per #3).
- **New live file (conditional):** if C5 creates `CANDIDATES.md` it must get a tree entry (the tree-gate will flag it otherwise) — resolve per #4.
- **Doc-budget gate interaction (0020 A2):** C5 and C4 *add* prose to `CLAUDE.md` and `WORKFLOW.md`; if 0020's `check_doc_budgets.py` lands first (CLAUDE.md budget 6000 bytes), confirm the C5 CLAUDE.md per-repo-block blessing doesn't push CLAUDE.md over budget. State the dependency: this batch runs after 0020 Phase 0 (already noted L5), so the budget gate is live — keep the added prose dense.
- **Cross-plan coupling (#1)** is the one genuine harness risk: two sibling plans each assuming the other owns `tree:9`. Resolve in-plan (option (a)) rather than reaching into 0020.

---

## Spec  _(per slice, after Review passes — Stage 4; expanded once Review passes)_
_Each slice's items carry a finding ID + file:line above; full per-edit spec written after plan-review, in the batch-approval roster._

## Audit deltas (confirmed 2026-06-17 — fold into the slices at build time; evidence = the journey-srp-audit output)

- **NEW slice C6 — non-adopter graceful-degradation:** a committed note (what the Stop hook is · it needs Python 3 · the `.claude/settings.local.json` skip path) so a teammate who never installed isn't policed without explanation (TEAM-1/2/3, confirmed). Keep the hook loud — the fix is the missing pointer, not fail-open code.
- **NEW slice C7 — engine renderer extraction:** move the backlog-fence renderer out of `engine/audit.js` into its own engine module (real 2nd consumer: qa.js product-gap + the skill) (ENGSRP-1). Engine-only; parallel with the doc slices.
- **C1 +=** README/init update two-step (`/plugin update` THEN `/init`; fix README:9) (ADOPT-2, confirmed) · TEMPLATE per-slice Spec gains an **in-scope-dimensions** line (CONTRIB-4) · reframe the mature-tree prompt in outcome language (NONENG-1) · resolve BOTH CANDIDATES refs together (WORKFLOW:162 + standards/README, the latter ships to adopters) (ADOPT-4).
- **C2 +=** pin the cross-model **fold rule** in the cross-script test (reimplemented 4 ways, unpinned — trust-surface drift) (ENGSRP-2) · move qa.js's cross-model fold into the pure-helpers block (testable) (ENGSRP-3).
- **C3 +=** evidence-backed relocations: build/init/audit skill prose restating engine contracts → field-roster + pointer (SKILLSRP-2/4/5/6) · trim product-critic/honesty-reviewer teaching prose (AGENTSRP-2). KEEP build's status→pause mapping resident (SKILLSRP-7 — the relocate boundary, do not cut).
- **C4 +=** reconcile the two resume oracles into ONE render (RETURN-1, confirmed) · plain-English bridge at the git-vocabulary pauses (NONENG-4) · name the 4th leverage point (pre-land) in the PLAYBOOK (WFFIT-4) · implementer-architect writes the slice's own test FIRST for bug/refactor (CONTRIB-3) · add version-sync to implementer-architect's gate list (WFFIT-3) · plain-language `/build` item-naming example (NONENG-3) · orientation note above the two backlog fences (NONENG-5).
- **Execution order update:** `(C1 ∥ C2 ∥ C6 ∥ C7) → C3 → C4 → C5` (C6 = settings/docs, C7 = engine — both disjoint from the skill files, so they parallelize with C1/C2).
