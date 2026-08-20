# PRODUCT — the durable product context for the harness

> Who the harness is for, the job it does, and the design language its surfaces must honour.
> **An index, not a spec** — the pipeline and skills own *how*; this owns *who it's for and what
> "good" feels like*. Authored at Discuss (Stage 1) by `product-designer`; deepened per feature.
>
> **Sibling:** `docs/claugentic-CHARTER.md` — the engineering-methodology record (different reader:
> `implementer`/`synthesizer-gate`). **Absent in THIS repo**; `init` creates it on demand from the
> `claugentic-_CHARTER.md` seed, so don't read that pointer as a file you can open today.

## The user (across the whole harness)

A **capable non-engineer** (sometimes an engineer) driving an AI dev team in plain English. They make
**product calls and approvals**, not code, and cannot read a diff to check the work — so the surface
must **earn trust honestly**: never let them lose the thread, never claim more than was checked.
Driver framing: [`PLAYBOOK.md`](claugentic-PLAYBOOK.md).

## The design language (every surface inherits these)

- **Plain-English first** — lead with the intent a non-engineer reads first; technical detail sits
  beneath it, to verify against, never to decode.
- **Honest by construction** — separate **measured** (`[D]`) from **asserted** (`[J]`); never launder
  a model's claim into apparent fact. Only the architecture-tree and doc-budget gates are
  mechanically enforced, and only where the commit hook is wired — say so where it matters.
- **In control, never surprised** — nothing irreversible without an explicit, plain-English ask.
- **Calm progress, no fake ETAs** — narrate **completed beats** only (a budget checkpoint can land
  partial at any time).
- **Right-sized** — small change, light touch; big one, full pipeline (KISS/YAGNI). Tangents →
  ROADMAP, never silently into the work.

## Per-project design language (the anti-sameness record)

Where THIS project pins its own visual/motion voice, so the universal craft floor lifts quality
**without making every project look the same**.

**DRY note:** the list above is the harness's OWN instance of this pattern; this block is where *each
project* pins ITS voice. One points at the other; **neither restates conformance** — the universal
floor is `docs/claugentic-standards/product-ux.md`.

The record — fill a field, or leave it and it defaults to the floor:

- **Brand lane** — the family it feels like · the kin it admires AND the one axis it diverges from
  even that kin · AND what it is NOT (a positive north-star, not just a list of dislikes).
- **Voice / tone** — how copy and interactions should feel.
- **Anti-references** — specific products/looks to move AWAY from (the anti-sameness lever).
- **Type / color / motion intent** — per-project taste the universal standard can't hold.
- **Where the system comes from (mechanism-agnostic)** — a code component-library reference, a synced
  design-system record (e.g. via a Claude Code `/design-sync` flow — **one option, never required**),
  or a hand-written brand-lane record. The `product-ux.md` craft floor applies ON TOP either way.

**Project-owned, model-upheld, never a gate.** **An unfilled record is a choice, not a free default:**
it accepts the shared floor as the whole voice and will read as competent-but-generic — fine for an
internal tool, a flag for a product meant to be distinctive.

*(The harness has no product UI — a plugin/docs repo — so its own record is N-A; this section is the
pattern each adopter project fills.)*

---

# The product layer (`/claugentic-dev-harness:product`)

Product memory + conscience: **spec mode** captures what the product is *supposed* to be (who · job ·
promise · per-feature flow/states/what-good · machine-readable criteria); **gap mode** checks the code
against it. `skills/product/SKILL.md` owns the step-level mechanics.

- **Capture → conform → *elevate*.** `product-designer` **surfaces** the user's truth, `product-ux.md`
  governs **conformance**, and the **Excellence pass** (that agent's **elevate** mode) critiques the
  draft **by method** — forcing functions, not a dimension checklist — returning proposals the user
  decides on (adopt/adapt/reject/defer). It **proposes, never imposes**: a proposal is a *question*,
  never spec content until adopted. **Default-on every spec-mode run, skippable on ask.** Honesty: it
  raises the bar, never claims the spec *guaranteed excellent*; a benchmark claim without a
  deep-research round is model knowledge, tagged not-verified.
- **The rejected-proposals memory is user-owned and lives in the spec.** Rejected proposals (and a
  declined-pass marker) go in a `<!-- product-critic:rejected-proposals -->`-fenced block in
  `docs/claugentic-PRODUCT_SPEC.md` — user-owned, never stamped — so the critic reads it next refresh
  and never re-pitches a decided idea. A **deferred** proposal lands in `docs/claugentic-ROADMAP.md`'s
  human-owned area (outside the regenerate-don't-accumulate audit fence); pickup is not automatic.

---

# Build mode (`/claugentic-dev-harness:build`)

A **thin orchestration layer** over the [`WORKFLOW.md`](claugentic-WORKFLOW.md) pipeline and the
[`audit`](../skills/audit/SKILL.md) skill — it drives process, it does not invent it. Product-level
only (job · which states must exist · what-good-feels-like · honesty).

## User & job-to-be-done

- **User:** someone holding the tiered, tagged backlog from `/claugentic-dev-harness:audit`. They want
  it **built**, not listed — and won't micromanage every plan, spec, and diff.
- **JTBD:** *"Drive my roadmap to production without micromanaging every step — keep me in control of
  the decisions that matter, and never hand me runaway scope or an irreversible surprise."*
- **JTBD, the harness's own upkeep:** *"Keep my harness **lean, current, and honest without being
  asked**."* Its mechanisms are deliberately partial and must say so: the byte-cap gate **bounds
  growth, it never shrinks anything** (`/claugentic-dev-harness:condense` is a human act), and the
  currency nudges are advisory.

The design tension is **autonomy vs. control**: build enough that the user isn't clicking "next"
forever, but pause exactly where a human judgment is load-bearing and nowhere else — decision-fatigue
is a failure mode, not a safety feature.

## Where the mechanics live (not here)

**The mode axis, the flows, and every pause's copy live in [`skills/build/SKILL.md`](../skills/build/SKILL.md)** —
*Mode handling* (the who-watches axis + unlock conditions), the triage → per-item engine → loop → stop
procedure (steps 1-11), the batch-approval sitting, and the verbatim wording of each pause and state.
This file restates none of it — a paraphrase one level up drifts (it already had, on how many pauses
there are and what they gate), and a drifted second copy of a trust surface is exactly the failure
this product exists to prevent.

## The states each flow needs (especially the non-happy ones)

**The exact wording is the skill's**; what this list fixes is that the state must exist at all — no
blank screen, no dead end.

- **Empty backlog / already-sound at start** — say so and offer the real next step; never enter the
  loop, never manufacture work.
- **The checkpoint / decision state** — the core interaction: what was just done, what is being
  decided, the options, in plain English.
- **An item FAILS mid-build** — what failed and why, plainly; nothing partial lands, the run does not
  barrel on, a failed slice is never dressed as done.
- **Re-triage interruption** — new important work surfaced; pause to let the user re-pick, framed as
  the safety feature it is, not an error.
- **The long-running "working" state** — completed-beat narration only; no ETA, no "nearly finished,"
  no silent multi-minute stall.
- **The terminal "done" state** — scoped to the audited dimensions and covered cells; never "your app
  is perfect."
- **The build-to-green decline state** — per-condition, evidenced, offering the watched run as the
  live alternative; never an apology, never a vague "coming soon."

## What "good" feels like

Build mode, in priority order: **In control** (can stop or redirect at any
pause) · **Trustworthy** · **Calm** · **Never surprised** (no scope creep, no over-claimed success).

### The top 3 UX failure modes to design against

1. **Losing control** — the orchestrator runs ahead and the user no longer knows what's being built.
   *Defend:* clear pauses at the load-bearing decisions, completed-beat narration between them.
2. **A silent irreversible action or an over-claimed "done"** — a push/deploy/delete without an ask,
   or a partial slice reported as finished. *Defend:* hard-stop + plain-English ask before anything
   irreversible; "done" is only ever the dimension-scoped Verify/terminal signal.
3. **Decision-fatigue** — so many pauses the user rubber-stamps, silently destroying every gate's
   value. *Defend:* pause **only** at the load-bearing gates the skill enumerates and auto-drive
   between them; auto-continue the agreed list unless something material changed. *In-sitting variant
   (batch spec-approval):* a wall of N full specs invites the same rubber-stamping, so the sitting is
   **roster-first** — a scannable one-line-per-item overview (what it builds · what you're accepting),
   the full triad **beneath each, to drill into**; the per-item decision stays approve / adjust /
   drop, never an undifferentiated bulk "yes."

## Honesty surface — where the UX must NOT over-claim

Build mode rides on the audit's **model-upheld** verification — only the architecture-tree and
doc-budget gates are mechanically enforced, and only where the commit hook is wired — and is
**watched by default** (an unwatched build-to-green run is earned per-repo, never assumed). Four
over-claim hotspots; each one's honest wording is owned by its source, not restated here:

- **"verified / done / safe" copy** — reviewer judgment plus the deterministic gates that exist, not a
  mechanical proof (`skills/build/SKILL.md` → Verify · Guardrails).
- **The build-to-green decline** — name the unmet unlock conditions with evidence; a reduction of
  unwatched-run risk, never a substitute for the unbuilt trust-gates (→ Mode handling).
- **The "Tier-1+2 empty" success claim** — scoped to the **audited dimensions** and covered cells:
  "sound on what we checked," never "bug-free" or "perfect" (→ step 11, *Stop / done*).
- **The re-audit verification tags** — carried through from the audit unchanged
  (`skills/audit/SKILL.md` → verification tags).

The cross-model wiring and the same-model tag live in **`docs/claugentic-WORKFLOW.md` → Principles**;
the [`DECISIONS.md`](claugentic-DECISIONS.md) honesty section is the standing rule.
