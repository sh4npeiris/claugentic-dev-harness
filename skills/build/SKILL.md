---
description: Drive one named backlog item through the full reviewed pipeline — plan → adversarial review → spec → your approval → implement → verify → land — pausing only at the decisions that are yours. Checkpoint mode, one item at a time. Honest about its limits: it pauses at the spec and before anything irreversible, and unwatched "autopilot" is not earned yet (it names exactly what's missing and offers checkpoint instead).
---

# /claugentic-dev-harness:build

The **go-button for a backlog item.** Point it at one item from your `docs/ROADMAP.md`
backlog and it drives the whole professional pipeline for you — plan → adversarial review
→ spec → **your approval** → build → review-the-work → land — pausing only where your
judgment is load-bearing.

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
reviewed change with **at most three interruptions** — each in plain English (*what was
just done · what's being decided · your options*). Everything between those three pauses
auto-drives. A failed item **pauses and tells you plainly that nothing partial landed**.
The three pauses are: (1) the spec, before any code · (2) before land · (3) before any
irreversible action. *(Two further pauses fire only on exceptions — a mid-build re-slice
and a failed item — never on the happy path.)*

**This release does one item at a time.** The full-backlog loop (pick several, work them
to the honest stop-signal) is the next slice — this one is the honest, shippable per-item
engine.

---

## Mode handling *(read this first)*

Build mode has **one live mode** and **one named-but-not-built mode**:

- **`checkpoint` — the default and only live mode.** Everything below runs in checkpoint.
  If the user names no mode, this is what runs.
- **`autopilot` — named, but it has exactly one behavior: an honest decline.** If the user
  asks to run unwatched / on autopilot, return **EXACTLY** this and then continue in
  checkpoint if they wish:

  > Running unwatched needs an independent cross-model judge (Roadmap #4) and deterministic
  > trust-gates (Roadmap #5) — neither exists yet, so I can't do this honestly. Here's
  > checkpoint instead.

  **This refusal is autopilot's only behavior.** Do **not** build a mode-dispatch layer, a
  config flag, or any autopilot execution path — there is nothing to dispatch to. When
  Roadmap #4 + #5 land, a future slice makes autopilot real; until then it is a named mode
  whose whole implementation is this honest "not yet, here's why, here's checkpoint."

---

## The procedure *(one item, checkpoint mode)*

### 1. Locate the item

Read the **`harness-audit:backlog` fence** in `docs/ROADMAP.md` (the item universe the
`audit` skill wrote). Match the user's words to exactly one item — by tier+number
(*"Tier-1 item 2"*) or by its title/topic (*"the input-validation item"*). **If the match
is ambiguous, ask** — name the candidates and let the user pick; never guess which item
they meant.

Two stop-conditions before you proceed:

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
**`honesty-reviewer`**; a user-facing change also adds **`product-designer`**. Iterate the
plan until the review verdict is **PASS**.

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
then synthesizes. Run the **Definition-of-Done deterministic run-gates** (the canonical list
lives in the WORKFLOW DoD — run it, don't restate it).

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

On approval, land per the WORKFLOW Stage 8: a **conventional commit**, move the plan to
**`docs/archive/<year>/`**, append a **`docs/DECISIONS.md`** line for any non-trivial
choice, and **run the Stage-9 harvest checklist** (the five sweeps — see `docs/WORKFLOW.md`
§9; point at it, don't restate it).

### 8. Close-out

Tell the user, in plain English, **what landed** and **which gate-class passed — separately,
never a blanket "verified/done":**

- the **deterministic gates** that passed (tests, the architecture-tree check, version-sync,
  the project's lint/type/security gates), and
- the **reviewer sign-offs** (the in-scope `docs/standards/` dimensions the
  `architect-reviewer` audited) — model-upheld judgment, **"passed the checks and the
  reviewer's audit,"** never "proven correct."

Then the next step: **another backlog item the same way, or re-run
`/claugentic-dev-harness:audit`** for a fresh picture — you're finished when Tier 1 and
Tier 2 come back empty.

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
  names exactly what's missing (Roadmap #4 + #5) — never a vague "coming soon," never a
  silent degrade to a weaker promise.
