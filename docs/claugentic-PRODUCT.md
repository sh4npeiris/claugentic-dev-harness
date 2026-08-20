# PRODUCT — the durable product context for the harness

> The enduring user/product context that survives across sessions: who the harness is for,
> the job it does for them, and the design language its surfaces must honour. Kept **lean —
> an index, not a spec.** The pipeline and skills are the source of truth for *how*; this is
> the source of truth for *who it's for and what "good" feels like* on the user-facing
> surfaces. Authored at Discuss (Stage 1) by `product-designer`; deepened per feature.
>
> **Sibling:** the *engineering-methodology* record is `docs/claugentic-CHARTER.md` (the optional
> living per-work-type methodology record — different concern, different reader:
> `implementer`/`synthesizer-gate`, not `product-designer`). **Absent in THIS repo** — `init`
> creates it on demand from the `claugentic-_CHARTER.md` seed; until then the harness follows
> its default grain, and nothing here should be read as pointing at a file you can open.

## The user (across the whole harness)

A **capable non-engineer** (and sometimes an engineer) driving an AI dev team in plain
English. They make **product calls and approvals**, not code. They cannot read a diff to
check the work, so the surface must **earn trust honestly** — never make them feel they've
lost the thread, and never claim more than was actually checked. Full driver framing:
[`PLAYBOOK.md`](claugentic-PLAYBOOK.md).

## The design language (every surface inherits these)

- **Plain-English first.** Lead every surface with the reassurance/intent a non-engineer
  reads first; technical detail sits beneath, to verify against, never to decode.
- **Honest by construction.** Separate **measured** (deterministic/`[D]`) from **asserted**
  (judgment/`[J]`). Never launder a model's claim into apparent fact. Only the
  architecture-tree and doc-budget gates are mechanically enforced, and only where the commit
  hook is wired — say so where it matters.
- **In control, never surprised.** The user steers the decisions that matter; nothing
  irreversible happens without an explicit, plain-English ask.
- **Calm progress, no fake ETAs.** Long work narrates **completed beats**, never an estimate
  or a "nearly done" (a budget checkpoint can land partial at any time).
- **Right-sized.** A small change gets a light touch; a big one gets the full pipeline
  (KISS/YAGNI). Tangents → ROADMAP, never silently into the work.

## Per-project design language (the anti-sameness record)

Where THIS project pins its own visual/motion voice, so the universal craft floor lifts
quality **without making every project look the same** — the anti-sameness answer.

**DRY note:** the `## The design language (every surface inherits these)` list above is the
**harness's OWN instance** of exactly this per-project pattern — it pins the whole-harness
voice; this block is where *each project* pins ITS voice. One points at the other; **neither
restates conformance** (the universal floor lives in `docs/claugentic-standards/product-ux.md`).

The record (a nearly-empty template — fill a field, or leave it and it defaults to the floor):

- **Brand lane** — the family this product feels like · the closest kin it admires AND the one
  axis it deliberately diverges from even that kin · AND explicitly what it is NOT (a positive
  north-star, not only a list of dislikes — distinctiveness is a claim you make, not just a thing
  you avoid).
- **Voice / tone** — how copy and interactions should feel.
- **Anti-references** — specific products/looks to move AWAY from (the active push away from
  generic defaults — the anti-sameness lever).
- **Type / color / motion intent** — the per-project taste the universal standard can't hold
  (e.g. "restrained, editorial" vs "playful, high-motion").
- **Where the system comes from (mechanism-agnostic)** — the design system can come from any
  of: a code component-library reference, a synced design-system record (e.g. one kept in sync
  via a Claude Code `/design-sync` flow — **one option, never required**), or a hand-written
  brand-lane record. The craft floor (anti-slop + motion baseline in `product-ux.md`) applies
  ON TOP either way.

For the universal conformance floor (accessibility, states, tokens, motion safety) see
`docs/claugentic-standards/product-ux.md` — this block holds only per-project taste the
standard can't. It is **project-owned, model-upheld, never a gate**; its whole purpose is to
make each project establish its OWN voice so the craft floor is never a uniform template.

**An unfilled record is a choice, not a free default:** a product-bearing project that leaves
it blank accepts the shared floor as its whole voice and will read as competent-but-generic —
a deliberate call for an internal tool, a flag for a product meant to be distinctive.

*(The harness itself has no product UI — it's a plugin/docs repo — so its own per-project
record is minimal/N-A; this section is the pattern each adopter project fills.)*

---

# The product layer (`/claugentic-dev-harness:product`)

The harness's product memory + conscience: **spec mode** captures what the product is *supposed*
to be (who · job · promise · per-feature flow/states/what-good · machine-readable criteria) and
**gap mode** checks the code against it. The skill file (`skills/product/SKILL.md`) owns the
step-level mechanics; this is the product-level note.

- **Capture → conform → *elevate*.** The designer (`product-designer`) **surfaces** the user's
  truth and the standard (`docs/claugentic-standards/product-ux.md`) governs **conformance**; the
  **Excellence pass** — the `product-designer` agent's **elevate** mode (the **elevate** counterpart
  to discover) **critiques the draft by method** (forcing functions, not a dimension checklist) and
  returns a focused set of **proposals the user decides on** (adopt/adapt/reject/defer). It
  **proposes, never imposes** — proposals are *questions to the user*, never spec content until
  adopted, which extends (never violates) the designer's never-invent-scope rule. **Default-on
  every spec-mode run, skippable on ask.** Honesty register: it raises the bar, it never claims the
  spec is *guaranteed excellent*; benchmark claims without a deep-research round are model knowledge,
  tagged not-verified.
- **The rejected-proposals memory is user-owned and lives in the spec.** Rejected proposals (and a
  declined-pass marker) are recorded in a `<!-- product-critic:rejected-proposals -->`-fenced block
  in `docs/claugentic-PRODUCT_SPEC.md` — the user-owned, never-stamped spec — so the critic reads it next
  refresh and never re-pitches a decided idea. A **deferred** proposal lands in `docs/claugentic-ROADMAP.md`'s
  human-owned area (outside the regenerate-don't-accumulate audit fence); pickup is not automatic.

---

# Build mode (`/claugentic-dev-harness:build`)

The flagship Stage-1 product brief. Build mode is a **thin orchestration layer** over the
[`WORKFLOW.md`](claugentic-WORKFLOW.md) pipeline and the [`audit`](../skills/audit/SKILL.md)
skill — it does not invent process, it **drives** it. This section is product-level (the job ·
which states must exist · what-good-feels-like · honesty); the skill file owns the step-level
mechanics **and the copy**, and this file does not restate them.

## User & job-to-be-done

- **User:** someone who has run `/claugentic-dev-harness:audit` and is holding a tiered,
  tagged backlog. They want the work **built**, not just listed — but they are not equipped
  (or willing) to micromanage every plan, spec, and diff.
- **Job-to-be-done:** *"Drive my roadmap to production without micromanaging every step —
  keep me in control of the decisions that matter, and never hand me runaway scope or an
  irreversible surprise."*
- **Job-to-be-done, the harness's own upkeep:** *"Keep my harness **lean, current, and
  honest without being asked**."* The mechanisms serving it are deliberately partial and must
  say so on every surface: the byte-cap gate **bounds growth, it never shrinks anything**
  (`/claugentic-dev-harness:condense` is a human act), and the currency nudges are advisory.

The whole design tension is **autonomy vs. control**: build enough that the user isn't
clicking "next" forever, but pause at exactly the moments where a human judgment is
load-bearing — and nowhere else (decision-fatigue is a failure mode, not a safety feature).

## Where the mechanics live (not here)

**The mode axis, the flows, and every pause's copy live in [`skills/build/SKILL.md`](../skills/build/SKILL.md).**
That file owns the who-watches axis and its unlock conditions (*Mode handling*), the
triage → per-item engine → loop → stop procedure (steps 1-11), the batch-approval sitting,
and the verbatim wording each pause and each state uses. This file restates none of it: a
paraphrase one level up drifts (it already had, on how many pauses there are and what they
gate), and a second, drifted copy of a trust surface is the exact failure this product exists
to prevent. What stays here is the product truth the skill does not carry — the job above,
which states must exist, what "good" feels like, and the failure modes to design against.

## The states each flow needs (especially the non-happy ones)

A surface is only finished when none of these is a blank screen or a dead end. **The exact
wording of each is the skill's**; what this list fixes is that the state must exist at all.

- **Empty backlog / already-sound at start** — nothing to build. Say so plainly and offer the
  real next step; never enter the build loop, never manufacture work.
- **The checkpoint / decision state** — the pause itself, the product's core interaction: what
  was just done, what is being decided now, and the options, in plain English.
- **An item FAILS mid-build** — report what failed and why in plain English; nothing partial
  lands, the run does not barrel on, and a failed slice is never dressed as done.
- **Re-triage interruption** — new important work surfaced; pause and let the user re-pick,
  framed as the safety feature it is, not an error.
- **The long-running "working" state** — completed-beat narration only. No ETA, no "nearly
  finished," no silent multi-minute stall.
- **The terminal "done" state** — the honest success signal, scoped to the audited dimensions
  and the covered cells; never "your app is perfect."
- **The build-to-green decline state** — per-condition, evidenced, and offering the watched run
  as the live alternative; never an apology, never a vague "coming soon."

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
   at the load-bearing gates the skill enumerates, and auto-drive everything
   between; auto-continue the agreed list unless something material changed. *The in-sitting
   variant (batch spec-approval):* front-loading every spec into one sitting risks the same
   rubber-stamping **within** the sitting — a wall of N full specs the user skims and waves
   through. *Defend:* the sitting is **roster-first** — a scannable one-line-per-item overview
   (what it builds · what you're accepting) the user grasps at a glance, with the full triad
   **beneath each, to drill into** only where they want detail; the decision per item stays
   approve / adjust / drop, never an undifferentiated bulk "yes."

## Honesty surface — where the UX must NOT over-claim

Build mode rides on the audit's **model-upheld** verification — only the architecture-tree and
doc-budget gates are mechanically enforced, and only where the commit hook is wired — and is
**watched by default** (an unwatched build-to-green run is earned per-repo, never assumed).
Four user-facing surfaces are the over-claim hotspots; the exact honest wording for each is
owned by its source of truth, not restated here:

- **"verified / done / safe" copy** — reviewer judgment plus the deterministic gates that exist,
  not a mechanical proof (`skills/build/SKILL.md` → Verify · Guardrails).
- **The build-to-green decline** — name the unmet unlock conditions with evidence; a reduction of
  unwatched-run risk, never a substitute for the unbuilt trust-gates (`skills/build/SKILL.md` →
  Mode handling).
- **The "Tier-1+2 empty" success claim** — scoped to the **audited dimensions** and covered
  cells: "sound on what we checked," never "bug-free" or "perfect" (`skills/build/SKILL.md` → step 11, *Stop / done*).
- **The re-audit verification tags** — carried through from the audit unchanged
  (`skills/audit/SKILL.md` → verification tags).

The cross-model wiring and the same-model tag live in **`docs/claugentic-WORKFLOW.md` → Principles**; the
[`DECISIONS.md`](claugentic-DECISIONS.md) honesty section is the standing rule.