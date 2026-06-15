# PRODUCT — the durable product context for the harness

> The enduring user/product context that survives across sessions: who the harness is for,
> the job it does for them, and the design language its surfaces must honour. Kept **lean —
> an index, not a spec.** The pipeline and skills are the source of truth for *how*; this is
> the source of truth for *who it's for and what "good" feels like* on the user-facing
> surfaces. Authored at Discuss (Stage 1) by `product-designer`; deepened per feature.

## The user (across the whole harness)

A **capable non-engineer** (and sometimes an engineer) driving an AI dev team in plain
English. They make **product calls and approvals**, not code. They cannot read a diff to
check the work, so the surface must **earn trust honestly** — never make them feel they've
lost the thread, and never claim more than was actually checked. Full driver framing:
[`PLAYBOOK.md`](PLAYBOOK.md).

## The design language (every surface inherits these)

- **Plain-English first.** Lead every surface with the reassurance/intent a non-engineer
  reads first; technical detail sits beneath, to verify against, never to decode.
- **Honest by construction.** Separate **measured** (deterministic/`[D]`) from **asserted**
  (judgment/`[J]`). Never launder a model's claim into apparent fact. Only the
  architecture-tree gate is mechanically enforced — say so where it matters.
- **In control, never surprised.** The user steers the decisions that matter; nothing
  irreversible happens without an explicit, plain-English ask.
- **Calm progress, no fake ETAs.** Long work narrates **completed beats**, never an estimate
  or a "nearly done" (a budget checkpoint can land partial at any time).
- **Right-sized.** A small change gets a light touch; a big one gets the full pipeline
  (KISS/YAGNI). Tangents → ROADMAP, never silently into the work.

---

# The product layer (`/claugentic-dev-harness:product`)

The harness's product memory + conscience: **spec mode** captures what the product is *supposed*
to be (who · job · promise · per-feature flow/states/what-good · machine-readable criteria) and
**gap mode** checks the code against it. The skill file (`skills/product/SKILL.md`) owns the
step-level mechanics; this is the product-level note.

- **Capture → conform → *elevate*.** The designer (`product-designer`) **surfaces** the user's
  truth and the standard (`docs/standards/product-ux.md`) governs **conformance**; spec mode now
  adds an **Excellence pass** — the `product-critic` agent (the SRP **elevate** counterpart to the
  designer) **critiques the draft by method** (forcing functions, not a dimension checklist) and
  returns a focused set of **proposals the user decides on** (adopt/adapt/reject/defer). It
  **proposes, never imposes** — proposals are *questions to the user*, never spec content until
  adopted, which extends (never violates) the designer's never-invent-scope rule. **Default-on
  every spec-mode run, skippable on ask.** Honesty register: it raises the bar, it never claims the
  spec is *guaranteed excellent*; benchmark claims without a deep-research round are model knowledge,
  tagged not-verified.
- **The rejected-proposals memory is user-owned and lives in the spec.** Rejected proposals (and a
  declined-pass marker) are recorded in a `<!-- product-critic:rejected-proposals -->`-fenced block
  in `docs/PRODUCT_SPEC.md` — the user-owned, never-stamped spec — so the critic reads it next
  refresh and never re-pitches a decided idea. A **deferred** proposal lands in `docs/ROADMAP.md`'s
  human-owned area (outside the regenerate-don't-accumulate audit fence); pickup is not automatic.

---

# Build mode (`/claugentic-dev-harness:build`)

The flagship Stage-1 product brief. Build mode is a **thin orchestration layer** over the
existing [`WORKFLOW.md`](WORKFLOW.md) pipeline and the [`audit`](../skills/audit/SKILL.md)
skill — it does not invent process, it **drives** it. This section is product-level (flows ·
states · what-good-feels-like · honesty); the skill file owns the step-level mechanics.

## User & job-to-be-done

- **User:** someone who has run `/claugentic-dev-harness:audit` and is holding a tiered,
  tagged backlog. They want the work **built**, not just listed — but they are not equipped
  (or willing) to micromanage every plan, spec, and diff.
- **Job-to-be-done:** *"Drive my roadmap to production without micromanaging every step —
  keep me in control of the decisions that matter, and never hand me runaway scope or an
  irreversible surprise."*

The whole design tension is **autonomy vs. control**: build enough that the user isn't
clicking "next" forever, but pause at exactly the moments where a human judgment is
load-bearing — and nowhere else (decision-fatigue is a failure mode, not a safety feature).

## The two modes (one seam)

- **`checkpoint` — LIVE.** Auto-drives Plan → Review → Implement → Verify between the real
  human gates, and **pauses** at: (1) triage selection, (2) the spec, before any code
  (Stage 5) — **per item as you go, or pre-satisfied per item up front in one approval
  sitting** when the user asks to *spec everything first* (the batch ask), (3) before land /
  any irreversible action.
- **`build-to-green` — REQUESTABLE, evidence-checked.** The flat autopilot refusal is
  superseded by the **autonomy ladder** (the contract lives in `skills/build/SKILL.md` →
  Mode handling): checkpoint stays the default; an unwatched build-to-green run unlocks
  per-repo only on three evidence-stated conditions (CI running the deterministic gates ·
  a test baseline on the touched code · an approved spec with testable acceptance criteria)
  plus the engine being installed (`engine/build-item.js` — Slice 5b; until it ships,
  every ask declines). Anything unmet → an honest decline naming exactly what's missing,
  offering checkpoint — never silently degrading to a weaker promise. Build-to-green is a
  reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates.

## The key flows (end-to-end)

1. **Triage** — present the audit's tiered backlog; the user **picks** the items to build.
   Then "start now?" Nothing is built before this yes.
2. **Per-item build** — for each chosen item, auto-drive the pipeline to the next gate,
   pausing only at spec-approval and any irreversible action. The item's **tag selects the
   discipline** (`refactor` → characterization-tests-first, `bug` → reproduce-first, etc. —
   see WORKFLOW's tag→discipline table). **Spec-approval has two rhythms:** as-we-go (the
   default — each item's spec is approved when its turn comes) or, on the **batch ask**
   (*"spec everything first"*), one **roster-first approval sitting** up front that approves
   the whole list before anything builds; then the run has only the lighter per-item land
   confirms + the safety pauses left.
3. **Re-audit → continue-or-re-triage** — after each item, a **scoped re-audit** over the
   touched `(module × dir)` cells (honest scope — cross-file fallout beyond those cells is
   owned by the closing full audit; the harness has no dependency graph and claims none). If
   nothing material surfaced, **auto-continue**
   the agreed list. If material new/obsoleted work surfaced, **pause to re-triage** — the
   user re-picks before more is built.
4. **Stop / done** — when the agreed list is worked through, one **full audit** confirms
   Tier-1+2 empty → the terminal "Sound on the audited dimensions" signal. Stop.
5. **Build-to-green ask** — if the user asks for an unwatched run, check the ladder's
   unlock conditions with stated evidence; unmet → decline honestly (naming exactly what's
   missing) and offer checkpoint.

**Guardrails (both modes, non-negotiable):** hard-stop + ask before any **irreversible
action** (push to a shared remote, deploy, delete data, spend money, external side-effect);
**never invent scope** — a genuinely-new feature it discovers goes to ROADMAP for the user's
approval, it is **not built**.

## The states each flow needs (especially the non-happy ones)

A surface is only finished when none of these is a blank screen or a dead end.

- **Empty backlog / Tier-1+2 already empty at start** — there is nothing to build. Don't
  enter the build loop or manufacture work. Say it plainly, reusing the audit's terminal
  phrasing: *"Sound on the audited dimensions — what remains is optional polish; you don't
  need to keep re-auditing."* Offer the real next step (start something new, or stop).
- **The checkpoint / decision state** — the pause itself, the product's core interaction.
  At each pause the user sees **what was just done, what's being decided now, and the
  options** in plain English:
  - *Triage* — the tiered list to pick from.
  - *Spec approval (Stage 5)* — the spec's plain-English block first (*what this builds ·
    what "done" means for you · what you're accepting*); no code before the yes.
  - *The approval-mode ask (batch spec-approval)* — when the user says *"spec everything
    first,"* the spec pauses are front-loaded into **one roster-first sitting**: a scannable
    list of every item (what it builds · what you're accepting, one line each) with the full
    triad beneath each to drill into; approve / adjust / drop per item, then it builds the
    approved list. Honest at the ask — and echoed at the sitting close — about what batch does *not* remove (still confirm each
    landing, anything irreversible still stops, a later item re-confirms if the ground
    shifted) and the neutral sunk-cost fact (a dropped item's planning is already spent). The
    durable approval mark rides the plan file's `Status` line. As-we-go stays the default.
  - *Irreversible hard-stop* — name the exact action and its consequence, and wait. Never
    proceed on silence.
- **An item FAILS mid-build** — the Verify gate fails, implementation can't complete, or a
  slice won't land clean. Build mode **pauses honestly** and reports *what failed and why in
  plain English* — it does **not** barrel on to the next item, and does **not** dress a
  failed slice as done. Offer the real options (retry, skip this item and continue the rest,
  or stop). A half-done slice never lands (WORKFLOW: slice lands vertically complete or not
  at all).
- **Re-triage interruption** — a scoped re-audit surfaced new critical work. Pause, show
  what changed (new/obsoleted items), and let the user re-pick before building more — framed
  as the safety feature it is, not an error.
- **The long-running "working" state** — between gates, the user sees **honest progress
  narration**: completed beats only (*"planned it · built it · running the checks…"*), reusing
  the audit's "completed-beat per item, **never an ETA**" discipline. No fake ETA, no "nearly
  finished," no silent multi-minute stall.
- **The terminal "Tier-1+2 empty — done" state** — the honest success signal. One **full**
  audit confirms it; surface the audit's *"Sound on the audited dimensions"* phrasing,
  scoped honestly to the audited dimensions (not "your app is perfect / bug-free").
- **The build-to-green decline state** — honest about *exactly which* unlock conditions this
  repo hasn't met (per-condition evidence lines, per `skills/build/SKILL.md` → Mode handling),
  and offers checkpoint as the live, trustworthy alternative. Not an apology, not a vague
  "coming soon" — a clear, true, per-condition reason.

## What "good" feels like

The four experience qualities, in priority order:

- **In control** — the user always knows what's happening, what's being decided, and that
  nothing big moves without their yes. They can stop or redirect at any pause.
- **Trustworthy** — every claim is scoped to what was actually checked; "verified," "done,"
  and "safe" mean exactly what they say and no more.
- **Calm** — steady completed-beat narration; no anxiety-inducing ETAs, no silent stalls, no
  wall of jargon.
- **Never surprised** — no irreversible action, no scope creep, no over-claimed success ever
  arrives unannounced.

### The top 3 UX failure modes to design against

1. **The user feeling they've lost control** — the orchestrator runs ahead and the user no
   longer knows what's being built or why. *Defend:* clear pauses at the load-bearing
   decisions + completed-beat narration between them, so the thread is never dropped.
2. **A silent irreversible action or an over-claimed "done"** — a push/deploy/delete happens
   without an ask, or a failed/partial slice is reported as finished. *Defend:* hard-stop +
   plain-English ask before anything irreversible; "done" is only ever the honest,
   dimension-scoped Verify/terminal signal — never asserted over a failure.
3. **Decision-fatigue from too many checkpoints** — so many pauses the user rubber-stamps
   without reading, which silently destroys the value of every gate. *Defend:* pause **only**
   at the three load-bearing gates (triage · spec · irreversible) and auto-drive everything
   between; auto-continue the agreed list unless something material changed. *The in-sitting
   variant (batch spec-approval):* front-loading every spec into one sitting risks the same
   rubber-stamping **within** the sitting — a wall of N full specs the user skims and waves
   through. *Defend:* the sitting is **roster-first** — a scannable one-line-per-item overview
   (what it builds · what you're accepting) the user grasps at a glance, with the full triad
   **beneath each, to drill into** only where they want detail; the decision per item stays
   approve / adjust / drop, never an undifferentiated bulk "yes."

## Honesty surface — where the UX must NOT over-claim

Build mode rides on the audit's **model-upheld** verification — only the architecture-tree gate
is mechanically enforced — and is **checkpoint-only-live**. Four user-facing surfaces are the
over-claim hotspots; the exact honest wording for each is owned by its source of truth, not
restated here:

- **"verified / done / safe" copy** — reviewer judgment plus the deterministic gates that exist,
  not a mechanical proof (`skills/build/SKILL.md` → Verify · Guardrails).
- **The build-to-green decline** — name the unmet unlock conditions with evidence; a reduction of
  unwatched-run risk, never a substitute for the unbuilt trust-gates (`skills/build/SKILL.md` →
  Mode handling).
- **The "Tier-1+2 empty" success claim** — scoped to the **audited dimensions** and covered
  cells: "sound on what we checked," never "bug-free" or "perfect" (`skills/build/SKILL.md` → step 10).
- **The re-audit verification tags** — carried through from the audit unchanged
  (`skills/audit/SKILL.md` → verification tags).

The cross-model wiring and the same-model tag live in **`docs/WORKFLOW.md` → Principles**; the
[`DECISIONS.md`](DECISIONS.md) honesty section is the standing rule.
