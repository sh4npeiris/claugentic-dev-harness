---
description: Drive your audit backlog through the full reviewed pipeline — plan → adversarial review → spec → your approval → implement → verify → land — pausing only at the decisions that are yours. Pick one item, several, or a whole tier; it works them one by one, re-checking the code it touched between items and pausing for you only when new important work surfaces, to the honest "sound on the audited dimensions" stop-signal. Checkpoint mode. Honest about its limits: every item's spec needs your approval before any code — per item as you go, or all at once up front in a single approval sitting if you say "spec everything first" — and it stops before anything irreversible; unwatched "autopilot" is not earned yet (it names exactly what's missing and offers checkpoint instead).
---

# /claugentic-dev-harness:build

The **go-button for your backlog.** Point it at one item from your `docs/ROADMAP.md`
backlog — or pick several, or a whole tier — and it drives the whole professional pipeline
for you — plan → adversarial review → spec → **your approval** → build → review-the-work →
land — pausing only where your judgment is load-bearing. A single named item stays the fast
path (no triage ceremony); ask for more than one and it confirms an ordered worklist, then
works it item-by-item to the honest stop-signal.

## How this skill works

Build mode is a **thin orchestration layer** — it does not invent process, it **drives**
the existing one. The pipeline it runs is **`docs/WORKFLOW.md`** (the source of truth for
the stages, the tag→discipline mapping, the Verify dial, the Definition of Done, and the
Stage-9 harvest); the item universe is the **`harness-audit:backlog` fence** that
`/claugentic-dev-harness:audit` writes into `docs/ROADMAP.md`. This skill points at both —
it does not restate them.

A **top-level agent (the orchestrator) runs this skill** — it spawns the pipeline
subagents (`plan-reviewer`, `implementer-architect`, `architect-reviewer`, the lenses, the
diverse panel), and subagents can't spawn subagents (the same constraint `audit` and `init`
carry). Invoke it in plain English — *"build Tier-1 item 2"*, *"build the input-validation
item"*, *"/claugentic-dev-harness:build the test-baseline item"*.

**What "checkpoint mode" means for you:** you can name one item and get back a landed,
reviewed change with **at most three interruptions per item** — each in plain English (*what
was just done · what's being decided · your options*). Everything between those three pauses
auto-drives. A failed item **pauses and tells you plainly that nothing partial landed**.
The three pauses are: (1) the spec, before any code — fired **per item** as you go, **or
pre-satisfied per item up front in a single approval sitting** if you ask to *spec everything
first* (see *Batch approval (on request)*) · (2) before land · (3) before any irreversible
action. *(Two further pauses fire only on exceptions — a mid-build re-slice and a failed
item — never on the happy path.)*

**The full-backlog loop is live.** Pick several items (or "all of Tier-1"), confirm the
ordered worklist, and it works them one by one — after each landed item it **re-checks the
code that item touched**, pausing to let you re-pick **only when new important work surfaces**
(otherwise it just continues the agreed list); when the worklist is done it runs **one full
audit** and tells you honestly whether you've reached *"sound on the audited dimensions."*
The single-named-item path above stays the fast path — the loop is opt-in by asking for more
than one.

---

## Mode handling *(read this first)*

Build mode has **one live mode** and **one named-but-not-built mode**:

- **`checkpoint` — the default and only live mode.** Everything below runs in checkpoint.
  If the user names no mode, this is what runs.
- **`autopilot` — named, but it has exactly one behavior: an honest decline.** If the user
  asks to run unwatched / on autopilot, return **EXACTLY** this and then continue in
  checkpoint if they wish:

  > Running unwatched needs mechanical trust-gates that can block a bad change without a human
  > watching — those don't exist, so I can't do this honestly. The cross-model judge is wired
  > (same-model runs are tagged as such), but it's a reduction of shared-blind-spot risk, not a
  > mechanical guarantee. Here's checkpoint instead.

  **This refusal is autopilot's only behavior.** Do **not** build a mode-dispatch layer, a
  config flag, or any autopilot execution path — there is nothing to dispatch to. It is a
  named mode whose whole implementation is this honest "not yet, here's why, here's
  checkpoint."

---

## The procedure *(checkpoint mode)*

### 1. Triage — locate the item(s) and confirm the worklist

Read the **`harness-audit:backlog` fence** in `docs/ROADMAP.md` (the item universe the
`audit` skill wrote). Two stop-conditions hold **before** any selection, single or multi:

- **No backlog, or it's stale** (no `harness-audit:backlog` fence, or it predates the
  current code) → **don't invent one.** Say so plainly and suggest running
  **`/claugentic-dev-harness:audit`** first so there's a current, verified backlog to build
  from.
- **Empty backlog / already-sound** (Tier 1 **and** Tier 2 both empty — only Tier-3 polish,
  or nothing) → **don't enter the build flow and don't manufacture work.** Reuse the
  audit's terminal phrasing **plus the real next step** (a fork, never a dead end):
  *"Sound on the audited dimensions — what remains is optional polish; you don't need to
  keep re-auditing. From here you can start something new — just tell me what you want to
  build — or stop."*

Otherwise, branch on **how many items the ask names:**

**(a) One named item — the fast path (no triage ceremony).** When the ask is specific —
*"build Tier-1 item 2"*, *"build the input-validation item"* — match the user's words to
exactly one item, by tier+number or by its title/topic. **If the match is ambiguous, ask**
— name the candidates and let the user pick; never guess which item they meant. Then go
straight to step 2 with a one-item worklist. **No tiered list, no "start now?" gate** — a
specific ask is already the go-ahead.

**(b) More than one item, a tier shortcut, or no item named — multi-item triage.** When the
user asks for several items, a **tier-level shortcut** (*"all of Tier-1"*, *"do Tiers 1 and
2"*, *"build my backlog"*), or doesn't name a specific one, run the triage:

1. **Present the tiered backlog** in plain English — the items as the `audit` skill wrote
   them (tier · title · tag · the one-line "why it matters"). Don't re-audit; you are
   reading the existing fence, not regenerating it.
2. **Let the user pick** — **individual items and/or tier shortcuts** (*"Tier-1 item 1 and
   item 3, plus all of Tier-2"*). A tier shortcut expands to that tier's items in their
   backlog order.
3. **Confirm the ordered worklist in plain English** — read the selection back as a numbered
   list in the order it'll be built (*"so I'll build, in order: 1) the test baseline · 2)
   input validation · 3) …"*), and let the user re-order or drop any before you start. The
   **recommended default order** is the backlog's own order (Tier-1 #1 first — the test
   baseline gates later refactors), but the user's order wins. Add **one passive tip line**
   here (a tip, not a question — it needs no answer; the as-we-go flow continues unchanged if
   it's ignored): *"(tip: you can say 'spec everything first' to approve the whole list in one
   sitting)"*.
4. **"Start now?" — the explicit gate into the loop.** Nothing is built until the user says
   go. This is triage selection (the first of build mode's load-bearing decisions); on "yes"
   you enter the loop (step 9), on "no" you stop.

**The batch ask (recognized here, not a standing question).** If the user says — in this
triage conversation — *"spec everything first," "approve them all in one sitting," "batch
approve,"* or the like, run **Batch approval (on request)** (below) instead of entering the
loop directly. **Absent the ask, as-we-go behaves exactly as before** — the only addition on
that path is the passive tip line; the spec/land/irreversible pauses are unchanged.
The ask is the only trigger; there is no standing approval-mode question and the tip line in
step 3 needs no answer.

---

## The per-item engine *(steps 2–8 — one worklist item, start to landed)*

Steps 2–8 build **one** item end-to-end. The fast path (a single named item) runs them once;
the loop (step 9) runs them per worklist item. They are the same engine either way.

### 2. Tag → discipline

The item carries a tag (`refactor` · `capability-upgrade` · `dependency-health` · `bug` ·
`feature`). Its tag **selects the discipline** the pipeline applies — the full mapping is
the **tag→discipline table in `docs/WORKFLOW.md`** (*Executing an audit backlog item*);
read it there and apply it. Do not restate the table here.

The **one** behavior to enforce up front (because it can stop the whole item before
planning): a **`refactor` on untested behavior-bearing code is characterization-tests-first
— a HARD precondition.** It **cannot start until its Tier-1 "establish a test baseline" item
is done.** If that baseline is absent, **stop and ask** rather than touching code, using the
WORKFLOW's pause narration:

> Before I tidy this code I need to capture what it currently does as a test, or I can't
> prove I didn't change its behavior — so I'll establish that baseline first.

Then offer to build the test-baseline item instead. (This precondition is upheld by the
implementer + the Verify gate — the durable `PreToolUse` hook does not exist yet; don't
imply it does.)

### 3. Auto-drive Plan → Review *(Stages 2–3 — no pause)*

Draft `.claude/plans/NNNN-<item>.md` from **`.claude/plans/TEMPLATE.md`**, sliced into
≤1-session units per the WORKFLOW *Principles*. Then spawn **`plan-reviewer`** to
adversarially critique it, **escalating to the diverse panel per the WORKFLOW Principles
trigger**: a contested design fork or a trust/honesty surface adds **`yagni-sentinel`** +
**`honesty-reviewer`**; a user-facing change also adds **`product-designer`**. **Spawn the
judge roles — `plan-reviewer` · `honesty-reviewer` — with the `fable` model override** (a
different model family than the builder; the mechanism, the `RUNNING AS:` self-report
comparison, the verbatim same-model tag, and the on-error respawn+tag live in **`docs/WORKFLOW.md`
→ Principles → "Convene the panel's judge roles with the `fable` model override"** — point there,
don't restate). Iterate the plan until the review verdict is **PASS**.

**Narrate progress as completed beats only — never an ETA, never a "nearly done."** *"Planned
it · reviewed the plan · folding in the changes…"* — the same calm completed-beat discipline
the `audit` skill uses. A long stretch between pauses is narrated, never silent and never
estimated.

### 4. Spec + THE PAUSE *(Stages 4–5 — pause 1, the spec, before any code)*

Write the spec into the plan (file-by-file changes, signatures, tests, acceptance, the
in-scope `docs/standards/` dimensions). Then **pause for the user's approval — no code
before "yes."**

At the pause, render the plan's **plain-English approval triad VERBATIM, BEFORE any
technical detail** — this is the non-engineer's steering wheel:

> - **What this builds:** …
> - **What "done" means for you:** …
> - **What you're accepting (risks / trade-offs):** …

Frame the checkpoint as *what was just done · what's being decided now · your options* —
the spec is written and reviewed; what's being decided is whether to build it; the options
are approve, adjust, or stop. The file-by-file detail sits **beneath** the triad, to verify
against, not to decode. **Wait for an explicit yes before Stage 6.**

### 5. Implement *(Stage 6 — no pause)*

On approval, spawn **`implementer-architect`** for the slice (one slice per session,
isolated, lands vertically complete per the WORKFLOW). Continue the completed-beat
narration.

**If the item won't fit one session** — it needs re-slicing mid-build — **pause and ask;
never silently re-plan.** Report plainly that it's bigger than one clean slice and offer to
re-slice it (and re-confirm the new shape) before continuing.

### 6. Verify *(Stage 7 — no pause unless it fails)*

Dial the Verify depth per the **WORKFLOW's named triggers** (read them there — the Stage-0
"substantial" triggers): a **solo `architect-reviewer`** is the small/local default; a named
trigger **fans out** the `lens-reviewer`s + `yagni-sentinel`, and a trust/honesty/user-facing
surface convenes the **diverse panel** per the WORKFLOW Principles — `architect-reviewer`
then synthesizes. **Spawn the judge roles — `architect-reviewer` · `honesty-reviewer` ·
`finding-verifier` — with the `fable` model override** (a different model family than the
builder; the mechanism, the `RUNNING AS:` self-report comparison, the verbatim same-model tag,
and the on-error respawn+tag live in **`docs/WORKFLOW.md` → Principles → "Convene the panel's
judge roles with the `fable` model override"** — point there, don't restate). Run the
**Definition-of-Done deterministic run-gates** (the canonical list lives in the WORKFLOW DoD —
run it, don't restate it).

**On a failed Verify, iterate implement→verify up to a small bounded number of attempts
(2–3).** If it still fails after that bound, **pause and ask — the item-failure pause:**

- Report **in plain English what failed and why** — don't dress a failed slice as done.
- State plainly: **nothing partial landed — the slice lands complete or not at all.**
- Offer the real options: **retry · skip this item · stop.**

### 7. Pre-land PAUSE + Land *(Stage 8 — pause 2, before land; pause 3, before anything irreversible)*

**Pause before landing** (pause 2), with the same plain-English frame as the spec pause —
*what was just done* = the slice is built and passed Verify; *what's being decided* =
whether to land it; *your options* = land · hold · stop.

**The irreversible hard-stop** (pause 3) — before **any** action in the **irreversible
hard-stop set** (see *Guardrails* below — the single authoritative list, including
push-to-`main`), **stop, name the exact action and its consequence in plain English, and
ask; never proceed on silence.**

On approval, land per the WORKFLOW Stage 8: a **conventional commit**, **remove the completed
plan from `.claude/plans/`** (git history keeps it), append a **`docs/DECISIONS.md`** line for
any non-trivial choice, and **run the Stage-9 harvest checklist** (the five sweeps — see
`docs/WORKFLOW.md` §9; point at it, don't restate it).

### 8. Close-out *(per item)*

Tell the user, in plain English, **what landed** and **which gate-class passed — separately,
never a blanket "verified/done":**

- the **deterministic gates** that passed (tests, the architecture-tree check, version-sync,
  the project's lint/type/security gates), and
- the **reviewer sign-offs** (the in-scope `docs/standards/` dimensions the
  `architect-reviewer` audited) — model-upheld judgment, **"passed the checks and the
  reviewer's audit,"** never "proven correct."

**Then branch on the worklist:**

- **Single named item (the fast path), or the worklist is now exhausted** → the next step:
  **another backlog item the same way, or re-run `/claugentic-dev-harness:audit`** for a
  fresh picture — you're finished when Tier 1 and Tier 2 come back empty. (When a loop's
  worklist is exhausted, the **stop/done** flow below runs the closing audit first — that's
  what confirms "finished.")
- **More worklist items remain** → don't run the full next-step prompt; this item's close-out
  is **one completed beat** (*"landed item 2 of 5"*), and you continue into the **scoped
  re-audit** (step 10) before the next item.

---

## The loop *(steps 9–11 — multi-item, entered from step 1b's "start now?")*

### 9. The build loop *(the worklist, item by item)*

On "start now?" yes (step 1b), work the **confirmed ordered worklist** one item at a time,
each through the per-item engine above (steps 2–8). After each item lands, run the **scoped
re-audit** (step 10), which decides whether to **pause and re-triage** or **auto-continue**
to the next item. When the worklist is exhausted with no re-triage pending, run **stop/done**
(step 11).

**Between items, narrate completed beats only — never an ETA.** As each item lands and its
re-check clears, emit one calm beat naming **what's done**: *"Landed item 2 of 5 —
re-checking the code it touched…"*, then *"clean — moving to item 3."* This is the same
completed-beat discipline steps 3–7 use within an item, now spanning the worklist. **Never**
estimate how long the remaining items will take, never say "nearly through the list."

The per-item checkpoint pauses hold across the loop: the **before-land** and **irreversible**
pauses **fire on every item**; the **spec** pause fires per item as you go, **or is
pre-satisfied per item by a batch sitting** (see *Batch approval (on request)*) — never
skipped, only satisfied earlier. **The loop never suppresses a pause that hasn't been
explicitly satisfied.** The autopilot refusal, the irreversible hard-stop set, and
no-invented-scope all hold unchanged across the whole loop.

### 10. The scoped re-audit + re-triage *(flow 3 — after each landed item)*

After an item lands, **re-run the audit scoped to the touched cells** — the
`(module × dir)` cells (the `audit` skill's existing granularity) that cover the files the
item changed. Spawn the audit's existing machinery over **only those cells** (the
`lens-reviewer`s for the relevant modules over the touched dirs, then the universal
`finding-verifier` re-check) — not a full repo sweep.

**Be honest about this re-audit's scope.** It covers the cells the item touched. **Cross-file
fallout beyond those cells — a change rippling into code the item didn't touch — is owned by
the closing full audit (step 11), not claimed here.** Say so if it matters; do **not** imply
the scoped re-check covers the whole repo, and do **not** describe it as chasing "dependents"
(the harness has no dependency graph — that claim would be a trust-surface over-claim; the
closing audit is what catches cross-file fallout).

Carry each re-audit finding's **verification tag unchanged** — `(checked against the code)` /
`(could not confirm independently — model's assertion)` / `(⚠ not yet verified — re-run to
confirm)` mean exactly what they mean in the `audit` skill: a reduction of false confidence by
a re-check from a different model family than the builder (the cross-model judge; on a
same-family run, tagged as such), **not** a deterministic guarantee. Don't upgrade the framing
because it's the loop re-checking its own work.

**Then decide — continue or re-triage:**

- **Any NEW Tier-1 or Tier-2 finding** (one the original backlog didn't already carry) →
  **pause to re-triage.** Show, in plain English, **what changed** — the new important
  finding(s) and where — framed as **the safety feature it is**: *"The re-check found new
  important work — that's the system catching things early, not a failure. Here's what
  surfaced; do you want to fold it into the list, re-order, or carry on as planned?"* The user
  **re-picks / re-orders** the remaining worklist (same triage interaction as step 1b,
  including the option to add the new finding) — then **confirm the updated worklist back as
  a numbered list and re-fire "start now?"** before continuing (the interruption ends on the
  same explicit go-ahead the first triage does; the new list's count also resets the "item
  N of M" beats, so position narration never silently drifts). Never silently absorb new
  scope, and never silently skip it.
- **Nothing new, or only Tier-3 polish** → **auto-continue** the agreed list. No pause — just
  the completed beat (*"clean — moving to item 3"*) and on to the next item. A clean re-check
  is **not** a checkpoint; interruptions taper as the criticals clear. (This is the deliberate
  safety-over-fatigue trade: any new Tier-1/2 interrupts, a clean or polish-only re-check does
  not.)

### 11. Stop / done *(flow 4 — the worklist is exhausted)*

When the worklist is worked through and **no re-triage is pending**, run **one `standard` full
audit** (the `audit` skill, repo-wide — this is what owns the cross-file fallout the scoped
re-audits didn't claim). Then:

- **Tier 1 and Tier 2 both empty** → surface the audit's terminal signal **verbatim**, plus
  the fork (never a dead end):

  > Sound on the audited dimensions — what remains is optional polish; you don't need to keep
  > re-auditing.

  …then: **start something new — just tell me what you want to build — or stop.**
- **Tier 1 or Tier 2 not empty** → **surface the remainder for a final triage decision.** Show
  what the closing audit found and ask plainly: **build more now (re-enter triage on the new
  list), or stop here.** **Never silently continue past the agreed worklist** — no-invented-scope
  applies to the worklist itself; the user decides whether the new findings become new work.

---

## Batch approval (on request) *(front-load the spec decisions into one sitting)*

Triggered **only** by the batch ask at step 1b (*"spec everything first," "approve them all
in one sitting"*). It does not invent new steps — it **re-orders when the existing pauses
fire**: every item's Stage-5 spec pause is satisfied up front, in **one sitting**, so the run
that follows has only the lighter per-item confirms left. The as-we-go default is untouched;
this path runs only when asked.

**At the ask, answer with both honesty lines once — no confirm-shaming, no penalty framing:**

> Spec-everything-first front-loads the approval decisions into one sitting, so you get
> **fewer interruptions: you'll still confirm each item before it lands, anything irreversible
> still stops, and if earlier work shifts the ground under a later item I'll pause to
> re-confirm.** And planning every item up front means a dropped item's planning is already
> spent.

(A multi-item batch is still several touchpoints — front-loaded *spec* decisions, not zero
presence. **Prep-cost, said plainly:** N items = N plan + review + spec cycles before anything
builds; the larger the worklist, the more likely a session boundary lands mid-prep — the
durable `Spec'd`/`Approved` states below absorb it, so a resumed run picks up derivably.)

### Prep — plan + review + spec every item, no code

Per worklist item, run the **existing steps 2–4** (tag → discipline → plan → panel review →
spec) — and **stop before any code**. Adjust-iterations reuse the **existing iterate-until-PASS
review loop** (step 3). No new mechanics: this is steps 2–4, run for every item before the
sitting instead of one item at a time. Narrate completed beats only (*"specced 3 of 7 —
no code yet…"*), never an ETA.

### The sitting — Stage 5, satisfied per item, up front (ROSTER-FIRST)

This **is** the Stage-5 spec pause, run once for the whole list. Lead with a **scannable
roster** so the user grasps the batch at a glance — **one line per item**: *number · title ·
one-line "what this builds" · one-line "what you're accepting"*. The **full approval triad per
item sits beneath, to drill into** (the same triad-above-detail pattern the single-item pause
uses at step 4) — the roster is the overview, the triads are the detail.

Per item, the choices are **approve / adjust / drop**:

- **Approve** → flip that item's plan file to **`Status: Approved`** (the `TEMPLATE.md`
  Status convention — **this is the durable mark** the run and any resume read; see the
  resume contract).
- **Adjust** → amend the spec and re-render that item's triad; a **material change re-enters
  the review loop** (step 3) before it can be approved.
- **Drop** → unjudged, **no penalty framing** — as easy and as blame-free as approve.

**Close the sitting by re-confirming the surviving ordered list** (a numbered read-back, the
same shape as step 1b) — **and restate what batch does not remove**: *"you'll still confirm
each item before it lands, anything irreversible still stops, and if earlier work shifts the
ground under a later item I'll pause to re-confirm."* (The echo matters: on a mid-prep resume
the sitting may run in a session where the user never heard the ask copy.)

### The run — the existing loop, spec pre-satisfied per item

Work the surviving list through the **existing loop (steps 5–8 per item)**. The **spec pause
is pre-satisfied per item by the sitting** (its plan reads `Status: Approved`) — every other
pause is unchanged: **pre-land per item · the irreversible hard-stop · the re-slice and
item-failure pauses · the re-triage on a new Tier-1/2 (step 10) · the currency pause (below).**

**Walk-away narration is load-bearing on this path.** Because batch invites the user to step
away after the sitting, the **completed beats** between items (*"built item 3 of 7 —
re-checking the code it touched…"*) are their **primary thread back into the run** — same
no-ETA discipline (step 9), now the explicit reassurance surface for the walk-away case.

### The spec-currency check — before item *k* implements

A later item's spec was written before earlier items landed, so the ground may have moved.
**Before item *k* implements:** intersect **the files landed since the sitting** (the landed
items' plan *Affected-files* lists / `git log`) with **the files item *k*'s spec names**.

- **No overlap** → proceed (the spec is still current).
- **Overlap** → the **currency pause**, in the standard pause frame: *what changed* (the
  landed work that touched this item's named files, in plain English) · *what's being decided*
  (re-confirm the spec as-is, **or** re-spec — a re-spec **re-fires the Stage-5 pause for that
  item**) · *the options*. Frame it as **the safety net promised at the sitting — never an
  error, and never a reversal of the user's approval.**

State it plainly: this is **file-level overlap, NOT semantic impact analysis** — the harness
has **no dependency graph and claims none**; semantic cross-file fallout stays owned by the
scoped re-audit (step 10) + the closing full audit (step 11). Model-upheld, said plainly.

---

## The resume contract *(derive the worklist — don't store it)*

A resumed `/claugentic-dev-harness:build` **reconstructs** the worklist from the two state
stores the harness already keeps — **there is no build-session state file, and this slice
adds none.** Derive, don't store:

- **The item universe + status** = the **`harness-audit:backlog` fence** in `docs/ROADMAP.md`
  (its status block + tiered items — exactly what triage reads in step 1).
- **An in-flight item** = its **plan file in `.claude/plans/`** with **unchecked
  implementation boxes**. **Offer to continue it/them first** before re-confirming the rest of
  the list — a **batch run can leave SEVERAL plans in-flight** (the run works the approved list
  in order), so offer to continue **all** of them, not just one, before re-confirming the rest.
- **A done item** = its **plan no longer in `.claude/plans/`** (removed at Land, step 7 —
  git history keeps it).

**The three batch-derived approval states** (from the plan files' `Status` line — the durable
mark the sitting writes; see *Batch approval (on request)*): **`Status: Spec'd`** (or in
review) = **awaiting a sitting** · **`Status: Approved`** = **build when reached** · a plan
with **unchecked implementation boxes** = **in-flight** (the case above). **Approval is never
inferred** — only an explicit `Status: Approved` counts as approved; a run that died mid-prep
or mid-sitting resumes derivably, each item exactly as `Spec'd` or `Approved` as its file says.

From those, **re-confirm the remaining selection + order with the user** (the step-1b
confirm + "start now?"). Be honest: the **picked order is the one thing not durably stored** —
the backlog and the plan files tell you *what's left and what's in flight*, but not the
sequence you'd agreed. A **5-second re-confirm** ("here's what's left — same order?") replaces
a third state store; that's the deliberate trade (derive-don't-store beats a worklist file
that could drift from the backlog).

---

## Guardrails *(non-negotiable, both now and in any future mode)*

- **Irreversible hard-stops.** Before any **push to a shared remote (incl. `main`),
  deploy, data deletion, spend, or external side-effect**: stop, name the action + its
  consequence in plain English, and **ask. Never proceed on silence.** This set holds in
  checkpoint today and in any future autopilot — it is the line autonomy never crosses
  unasked.
- **Never invent scope.** If a genuinely-new feature surfaces mid-build (something outside
  the item being built), it goes to **`docs/ROADMAP.md` for the user's approval** — it is
  **not built**. The work never silently expands.
- **Honesty register.** Say a slice **"passed the checks and the reviewer's audit,"** never
  "proven correct" / "guaranteed" / "bug-free." **"done" is scoped to the audited
  dimensions** (and the deterministic gates that ran), never a blanket claim. Progress is
  **completed-beat narration, never an ETA** or a "nearly finished." The autopilot refusal
  names exactly what's missing (the deterministic trust-gates — the cross-model judge is wired,
  but it's a reduction of shared-blind-spot risk, not a mechanical guarantee) — never a vague
  "coming soon," never a silent degrade to a weaker promise.
