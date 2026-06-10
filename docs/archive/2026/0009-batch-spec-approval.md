# 0009 — Batch spec-approval for build mode

- **Status:** Done — landed `a9bfdaa`; archived 2026-06-10
- **Roadmap item:** follow-on to #3 (build mode) — born at the 0008-park decision: the **near-term** user want is *"approve the specs in one sitting, then let it build the list"* — a build-mode UX upgrade, **not** unwatched autopilot (0008's gates remain the parked longer-term hardening).
- **References:** `skills/build/SKILL.md` · `docs/PRODUCT.md` · `docs/WORKFLOW.md` (Stages 4–5) · `.claude/plans/TEMPLATE.md` (the `Approved` Status convention this leans on) · `docs/DECISIONS.md`
- **Stage-3 review:** PASSED with required changes folded in (full diverse panel, judges cross-model — see *Review*; the sitting was redesigned roster-first, approval got a durable home, and the standing mode-question was cut for a requestable ask).

> **User-facing + the approval gate = trust surface → full diverse panel** (`plan-reviewer` + `yagni-sentinel` + `honesty-reviewer` + `product-designer`).

---

## Problem

Checkpoint mode pauses at **every item's spec**, scattering the heavyweight approval decisions across a multi-item run. The user's wanted rhythm: **front-load the heavyweight spec decisions into one sitting** — then execution proceeds with only the lighter confirmations (per-item land · irreversible · safety pauses) arriving as items finish. Today approvals can't be front-loaded.

## Goals / Non-goals

**Goals**
- **Batch approval is a requestable ask, not a standing question** *(yagni cut, adopted)*: when the user says so in the triage conversation — *"spec everything first," "approve them all in one sitting"* — the engine runs the batch flow. **Absent the ask, as-we-go runs unchanged, byte-for-byte.** Discoverability is passive: one **tip line** (not a gate) at the worklist confirmation — *"tip: you can say 'spec everything first' to approve the whole list in one sitting"* — plus a README/PLAYBOOK sentence.
- **The flow, expressed through the EXISTING steps** *(yagni cut: no Phase-A/B/C vocabulary)*:
  1. **Prep:** for each worklist item, run the existing steps 2–4 (tag→discipline → plan → panel review → spec) — **no code**. Adjust-iterations use the existing iterate-until-PASS review loop.
  2. **The sitting** (= Stage 5, satisfied per item, up front), **roster-first** *(product blocking fix)*: lead with a **scannable roster** — one line per item: *number · title · one-line "what this builds" · one-line "what you're accepting"* — so the user grasps the whole batch at a glance; the **full triad per item sits beneath, to drill into** (the same triad-above-detail pattern the single-item pause already uses). Per item: **approve / adjust / drop**. **Adjust** = the orchestrator amends the spec and re-renders the triad; a material change re-enters the review loop. **Drop carries no penalty framing** — as easy and unjudged as approve. Close by re-confirming the surviving ordered list.
  3. **The run:** the existing loop (steps 5–8 per item), the spec pause **pre-satisfied per item by the sitting**. Remaining pauses unchanged: **pre-land (per item) · irreversible hard-stops · re-slice/failure · re-triage on new Tier-1/2 · the currency pause (below).**
- **Approval gets a durable home — the existing plan-file convention** *(plan-reviewer blocking fix; still no new state store)*: the sitting flips each approved item's plan file to **`Status: Approved`** (`TEMPLATE.md` already defines it). A **resumed run derives three states** and **never infers approval**: `Spec'd` = awaiting a sitting · `Approved` = build when reached · a plan with unchecked implementation boxes = the in-flight item (offer to continue **it/them** first — a batch run can leave **several** in-flight plans, not one). A run that dies mid-prep or mid-sitting resumes derivably (items are `Spec'd` or `Approved` per their files).
- **The spec-currency check, operationally defined** *(plan-reviewer blocking fix)*: before item *k* implements, **intersect the files landed since the sitting** (the landed items' Affected-files lists / `git log`) **with the files item *k*'s spec names**. Overlap → **the currency pause**; none → proceed. **This is file-level overlap, NOT semantic impact analysis** (the harness has no dependency graph and claims none); semantic cross-file fallout stays owned by the scoped re-audit + the closing full audit. Model-upheld, said plainly.
- **The currency pause reads as the promised safety net** *(product fix)* — the standard pause frame: *what changed* (the landed work that touched this item's named files, plain English) · *what's being decided* (re-confirm the spec as-is, or re-spec — a re-spec re-fires the Stage-5 pause for that item) · *the options* — explicitly tied back to the trade accepted at the sitting, **never framed as an error or a reversal of the user's approval**.
- **Interruption-honesty at the ask and the sitting** *(honesty fix)*: the scripted copy names what batch does **not** remove — *"…fewer interruptions: you'll **still confirm each item before it lands**, anything **irreversible still stops**, and if earlier work shifts the ground under a later item I'll pause to re-confirm."* (A 5-item batch is still ~6+ touchpoints — front-loaded *spec* decisions, not zero presence.) The **sunk-cost fact stated once, neutrally, at the ask** (*"planning every item up front means a dropped item's planning is already spent"*) — no confirm-shaming anywhere.
- **Walk-away narration named load-bearing** *(product fix)*: on the batch path the completed beats (*"built item 3 of 7 — re-checking the code it touched…"*) are the user's **primary thread back into a run they may have stepped away from** — same no-ETA discipline, explicitly the reassurance surface for the walk-away case batch invites.
- **Prep-cost honesty:** N items = N plan+review+spec cycles in one orchestrator session before anything builds — large worklists make a session boundary *more* likely mid-prep; the durable `Spec'd`/`Approved` states absorb it (resume is derivable).
- **Fix-in-passing** *(Stage-9 second-occurrence trigger)*: harden `plan-reviewer.md`'s `RUNNING AS:` line like architect-reviewer's — *name the model family, never just the vendor or your role* (its self-report came back vendor-only in two consecutive panels; per the tag rule those reviews carry the same-model tag).

**Non-goals**
- **NOT autopilot** — pre-land + hard-stops + re-triage + currency pauses all remain; the refusal stays verbatim; no copy may imply unwatched running arrived.
- **No new state stores** — the durable approval mark rides the *existing* plan-file Status convention.
- **No standing mode-question** at triage *(cut)* · **no semantic dependency analysis** in the currency check · **no change to the single-item fast path or the as-we-go default** · **no batch flow for re-triage additions** (an addition mid-run is spec'd + approved when reached — a sitting of one).

## Approach
One coherent extension to `skills/build/SKILL.md`: the batch-ask recognition + tip line at the worklist confirmation (step 1b) · a short **"Batch approval (on request)"** section (prep → the roster-first sitting → the run, expressed via the existing steps; the durable Status flips; the currency check + pause; the interruption/sunk-cost copy verbatim) · the **contradiction sweep** (frontmatter :2 "pauses at the spec" · the ":30–34 three-pauses-per-item" framing · the ":266–268 'the loop does not suppress them'" line — each reworded to *"the spec pause fires per item, or is pre-satisfied per item by a batch sitting"*) · the resume-contract section gains the three derived states + the several-in-flight fix. `docs/PRODUCT.md`: the batch flow + the sitting + the currency-pause states; the **approval-mode ask added to the decision-state list**; **failure-mode #3 extended** with the in-sitting fatigue variant + its defense (roster-first). `README.md` one sentence + `docs/PLAYBOOK.md` one line *(marketplace.json description: explicitly **no change** — it describes the command set, which is unchanged)*. `.claude/agents/plan-reviewer.md`: the RUNNING-AS hardening line. `docs/DECISIONS.md`: the design + the **"near-term user want"** framing (0008's park was sequencing, not refuted intent) + the Status-line-becomes-load-bearing-for-batch-resume note. Manifests → `0.1.12`.

## Risks & mitigations
Staleness → the operational currency check + re-triage net + the trade named at the ask. Copy drift toward autopilot → the interruption-honesty copy + the refusal acceptance grep. In-sitting fatigue → the roster-first design. Approval ambiguity on resume → the durable Status states (never inferred). Prep-cost surprise → the sunk-cost + sizing honesty at the ask. Scope creep → no new files beyond the agent line; prose only.

## Test strategy
Run-gates green at `0.1.12` · internal consistency (the batch section composes with 1b/2–8/9–11 + resume; the as-we-go path byte-identical; the contradiction sweep verified by grep on the named lines) · honesty acceptance (the interruption-honesty clause present at the ask + sitting; the refusal verbatim; no "autopilot/unwatched/hands-off" in user-facing copy; the sunk-cost line neutral) · Stage-7 full panel (product-designer measures the sitting against the roster-first requirement).

## Decomposition (slices)
- [ ] **Slice 1 (only):** everything above. **Lands complete:** batch is requestable and works end-to-end (prep → roster sitting → run with derived resume), as-we-go untouched, all copy register-correct, gates green. → `0.1.12`

---

## Review *(Stage-3 — full diverse panel, judges cross-model; synthesized)*

**Verdict: PASS** (all required changes folded in above).

- **`plan-reviewer` — CHANGES REQUIRED → addressed.** *(blocking)* durable approval home via the existing plan-Status convention + the three derived resume states + the several-in-flight fix ✓ · the currency check operationally defined (file-overlap, not semantic) ✓. *(should-fix)* the contradiction sweep enumerated (frontmatter, the three-pauses lines, PRODUCT/README mirrors) + interruption-honesty at the ask ✓ · adjust mechanics + prep-cost/session-boundary honesty ✓. *(nit)* PLAYBOOK in scope; marketplace explicitly no-change ✓. **Tag note:** its `RUNNING AS:` self-report was vendor-only — per the rule, **this review carries the same-model tag** (*"same-model review on this run — the judge and the builder are the same model family here"*); the recurrence triggered the fix-in-passing hardening of its instruction.
- **`yagni-sentinel` — PROPORTIONATE; both cuts adopted.** The standing approve-mode question **cut** → batch is a requestable ask + a passive tip line (as-we-go stays byte-identical) ✓ · the Phase-A/B/C vocabulary **cut** → expressed through the existing steps ✓. Keeps confirmed: the currency check, the staleness narration, the single slice, no new stores.
- **`honesty-reviewer` (fable — confirmed cross-model) — OVERCLAIMS → fixed.** The remaining-pauses clause now required in the scripted copy at the ask + sitting ✓ · the Problem reworded (*front-loads the heavyweight decisions; lighter land confirmations still arrive*) ✓ · the DECISIONS framing qualified to **"near-term user want"** (0008 = sequencing, not refuted intent) ✓.
- **`product-designer` — INTENT-GAPS → addressed.** *(blocking)* the sitting is **roster-first** (scannable overview, triads beneath) ✓. *(should-fix)* the currency-pause copy in the standard pause frame, as the promised safety net ✓ · walk-away narration named load-bearing ✓ · the non-shaming drop register ✓ · PRODUCT.md gains the approval-mode decision-state + the in-sitting fatigue variant of failure-mode #3 ✓. *(nit)* the choice-point copy locked in non-engineer terms (no "spec freshness"/process jargon) ✓.

**Harness impact:** prose-only + one agent-line hardening; no new agent/module/store; PRODUCT brief amended (not just extended); manifests `0.1.12`.

---

## Spec

### Slice 1 — batch spec-approval (requestable)

**In plain English (the approval triad):**
- **What this builds:** you can now say *"spec everything first"* when picking backlog items, and build mode will plan and write **all** the specs before building anything, then walk you through **one approval sitting** — a scannable list of every item (what it builds · what you're accepting, one line each), with the full detail under each to drill into. Approve, adjust, or drop each; then it builds the approved list, and the only interruptions left are the quick per-item "ready to land?" confirms, anything irreversible, and the safety pauses. If earlier work shifts the ground under a later item's spec, it pauses and asks you to re-confirm — the safety net, not a do-over.
- **What "done" means for you:** the rhythm you described — one sitting of real decisions, then execution with only light touches. Asking for nothing different keeps today's approve-as-you-go exactly as it is.
- **What you're accepting:** every item is planned before anything builds (a dropped item's planning is already spent — stated once, neutrally); specs for later items are written before earlier ones land, so a later item may pause for a re-confirm if the ground shifted (file-level check, model-upheld — said plainly); this is **not** autopilot — you still confirm each landing.

**Files & changes / acceptance:** as *Approach* above. Key acceptance: the batch ask recognized + the tip line present (no standing question); the roster-first sitting; `Status: Approved` flips + the three derived resume states; the operational currency check + its pause copy in the standard frame; the interruption-honesty + neutral sunk-cost lines verbatim at the ask/sitting; the contradiction sweep clean (grep the named lines); the as-we-go path unchanged; the refusal verbatim; plan-reviewer's RUNNING-AS hardened; `0.1.12` both manifests.
