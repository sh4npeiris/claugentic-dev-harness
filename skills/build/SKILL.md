---
description: >-
  Drive your audit backlog through the full reviewed pipeline — plan → adversarial review → spec → your approval → implement → verify → land. Pick one item, several, or a whole tier; it works them one by one, re-checking the code it touched between items, to the honest "sound on the audited dimensions" stop-signal. Decision-gated: it stops only for a real decision (a design fork · a spec trade-off · anything irreversible), researches factual uncertainties instead of asking, and flags reversible judgment-calls to surface at the close. Every item's spec needs your approval before any code — per item, or all at once if you say "spec everything first" — and it stops before anything irreversible (a discipline this skill instructs — model-upheld, never a mechanical gate). Running unwatched (build-to-green) is requestable but earned per-repo (CI running the gates, a test baseline, a testable approved spec) with the engine available (a session precondition, not an earning); otherwise it declines naming exactly what's missing and offers a watched run.
---

# /claugentic-dev-harness:build

> **Agent ids:** spawn every role named below by its **namespaced id** `claugentic-dev-harness:<role>` (e.g. `claugentic-dev-harness:lens-reviewer`); built-ins (`general-purpose`, `Explore`) stay bare.
> **Every pointer below means READ IT THERE** — only load-bearing deltas are restated in this file.

The **go-button for your backlog.** Point it at one item from `docs/claugentic-ROADMAP.md` — or several, or a whole tier — and it drives plan → adversarial review → spec → **your approval** → build → review-the-work → land, pausing only where your judgment is load-bearing. One named item is the fast path (no triage ceremony); more than one confirms an ordered worklist and works it item-by-item to the honest *"sound on the audited dimensions"* stop-signal.

## How this skill works

A **thin orchestration layer**: it drives the existing process, it does not invent one.

- **Pipeline** = `docs/claugentic-WORKFLOW.md` (stages · tag→discipline · the Verify dial · Definition of Done · the Stage-9 harvest). **Item universe** = the three triage sources in step 1.
- **A top-level agent (the orchestrator) runs this skill** — it spawns the pipeline subagents (`synthesizer-gate`, `implementer`, the lenses, the diverse panel); subagents can't spawn subagents (the same constraint `audit` and `init` carry). Invoke it in plain English — *"build Tier-1 item 2"*.
- **When to stop = WORKFLOW → *Decision-gated autonomy*.** Its **three blocking-stop classes ARE the three concrete pauses here**, not a parallel set: **(a) design fork / (b) spec trade-off** → the **spec pause, before any code** (step 4 — per item, or pre-satisfied up front by a batch sitting); **(c) irreversible / outward action** → the **before-land pause** (step 7) and the **irreversible hard-stop** (*Guardrails*), which the flag path can **never** absorb. Everything else auto-drives — research a factual uncertainty (cited), flag-and-continue a reversible judgment, surface every flag at the close (step 8). *(A mid-build re-slice and a failed item are exception-only pauses.)*
- **Every stop is plain English:** *what was just done · what's being decided · your options.*
- **Narration rule, everywhere below: completed beats only — never an ETA, never "nearly done."** A long stretch between pauses is narrated, never silent.
- **Judge independence, everywhere below:** every judge role's independence is of **role and clean context, never of model** — they inherit the session's tier; the `RUNNING AS:` self-report + same-model tag disclose what resulted (WORKFLOW → *Principles*).

---

## Mode handling *(read this first)*

**Decision-gated is how build mode stops, always** — that governs **when to stop** on every run. The mode below is a **separate axis — who watches the run** — earned per-repo, by evidence, never assumed:

- **Watched (the default — no preconditions).** The orchestrator drives the per-item engine in this session under the decision-gated rules. No mode named → this runs.
- **`build-to-green` — running unwatched (requestable, earned per-repo).** Any ask to run unwatched — *"autopilot"*, *"run unwatched"*, *"build to green"* — is a build-to-green request. Before agreeing, check the **unlock conditions** below and **state the evidence per condition** (what you looked at, what you found). All met → run the item through the engine (contract below), which returns only at the **decision-gated hard stops, now surfaced as engine returns: before land · before anything irreversible (class (c)) · on a new Tier-1/2 finding.** Any condition unmet → the decline below, then offer the watched run. *(Unwatched changes who is present, not when to stop — reversible judgments are still flagged-and-continued, class (c) is still a return, never absorbed.)*

Build-to-green is **a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates** — the land-gate hook · the secret-scan (the *deterministic-gates* shard indexed in `docs/claugentic-DECISIONS.md`); the characterization-enforcement hook was **declined**, so that discipline stays model-upheld by design. **The unlock conditions — model judgment with stated evidence, never a mechanical gate:**

1. **CI runs the deterministic gates.** Evidence: a CI config (e.g. `.github/workflows/*.yml`) whose steps run this repo's Definition-of-Done deterministic gates (test suite + gate scripts). Name the file and the commands found.
2. **A test baseline covers the code this item touches.** Evidence: named test files that **assert observable behavior** of the files the item will change (not merely execute them) — so a regression there fails a test. (The `refactor` characterization-tests-first precondition is this condition's hard case.)
3. **The item traces to an approved spec with testable acceptance criteria.** Evidence: a plan in `.claude/plans/` with `Status: Approved` whose criteria are all checkable without a human mid-run — each maps to a deterministic gate or test, or to a `docs/claugentic-PRODUCT_SPEC.md` criterion whose `check` is `e2e` or `api`. A `check: "manual"` criterion needs a human, so it keeps that item watched.

**And one session precondition (not a repo condition):** build-to-green runs **only** via `engine/build-item.js` through the Workflow tool — **no prose-orchestrated build-to-green, ever** (an unwatched prose loop is exactly the unearned autonomy this axis exists to prevent). Tool or script unavailable → named in the decline like any other missing condition.

**The decline (verbatim frame — the list carries ONLY the unmet conditions, each with the evidence checked):**

> Build-to-green isn't earned here yet — here's exactly what's missing:
> [one line per unmet condition, from the fixed lines below]
> Build-to-green is a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates (the land-gate hook · the secret-scan — neither exists yet; the characterization-enforcement hook was declined by design), and these checks are my judgment against the evidence I named, not a mechanical gate. Here's a watched run instead — the same pipeline, decision-gated: I drive it with you present, stopping for a real decision and flagging the reversible judgment-calls for you to review at the close.

The fixed per-condition lines (angle-bracket slots filled per run from the evidence actually checked):
- *CI running the deterministic gates — I found <no CI config | `<file>`, but it doesn't run <the missing gate commands>>.*
- *a test baseline for the code this item touches — I found <no tests exercising <the touched files/behavior> | tests that exercise <the touched files> but assert nothing about <the behavior this item changes>>.*
- *an approved spec with testable acceptance criteria — <no plan with `Status: Approved` traces to this item | the spec's criteria include ones I can't check without you: <ids>>.*
- *the engine itself — <the Workflow tool isn't available in this session | `engine/build-item.js` isn't in the installed plugin>; build-to-green never runs as prose.*

### The build-to-green run *(the engine contract)*

All conditions met → invoke the engine. **The skill invokes it; the engine then runs the loop mechanically — invoking is still model-upheld** (the platform doesn't auto-fire workflows). The engine runs implement (in a worktree) → deterministic gates → the `verify.js` panel → `qa.js` (when criteria exist) → fix, until green or the cap.

**The args the skill assembles** (the engine validates them at the boundary and throws on any invalid field — fail loud):

- `item` — `{ id, title, tag, planPath, specText` (the approved spec section, verbatim) `, acceptanceCriteria }`. `acceptanceCriteria` is the item's frozen-schema criteria (`{id,feature,flow,expect,states,check}`) from its spec / `docs/claugentic-PRODUCT_SPEC.md`; `[]` when it has none. Optional `dimensions` (the in-scope `docs/claugentic-standards/` slugs for the Verify panel), `trustSurface`, `appUrl`.
- `repo` — `{ root, baseBranch, gateCommands` (this repo's **DoD deterministic gate commands** — the test suite + the gate scripts, from the WORKFLOW DoD / `init`-recorded tooling; **non-empty**, zero gates would make "green" a lie) `, runApp` (the recorded run-the-app command, or `null`) `, pluginRoot` (the expanded `${CLAUDE_PLUGIN_ROOT}`, for the child-workflow paths) `}`.
- `caps` — `{ maxIterations` (default 3 — the bounded 2–3) `, budget, stageTimeouts }`. `stageTimeouts` is the optional **per-stage duration bound** `{ implement?, gates?, qaBoot? }` (positive-integer seconds; the engine rejects any unknown key, non-integer/≤0 value, or a value **> 600** — the Bash-tool hard max — fail loud, never silently clamped). Defaults: `implement` and `gates` → **600s**; `qaBoot` has **no engine default** (`unset` ⇒ qa.js's own 60s default; qa.js silently clamps any value to its 300s cap).
- `builderFamily` — the orchestrator's session model family (for the honest same-model reporter).

**Honesty caveat — the three-way enforcement register (the bounds do NOT enforce equally):** **gates** = agent-applied per-command Bash-tool `timeout` **+ a mechanical red decision** (a timed-out command reports exitCode 124 → `gatesGreen` reads it red); **qaBoot** = a **mechanical clamp** in qa.js + an agent-executed bounded readiness probe; **implement/fix** = an **instruction-only** anti-hang nudge (IMPLEMENT_SCHEMA has no exit-code channel, so a runaway surfaces only downstream via the gates stage + the iteration cap — model-upheld, NOT a mechanical guarantee). The bound is **per-command within a stage, never a stage wall-clock total**; residual: a single legitimate command exceeding the 600s hard max can't be bounded-and-completed in one foreground call — split that repo's suite, or it isn't bounded-runnable.

**The engine's pauses are returns — map each returned status to its pause/interaction:**

- **`green`** → the **before-land pause** (pause 2). The engine NEVER lands or pushes — landing, the commit, and any push stay **the orchestrator's act**, behind the irreversible hard-stop set. The green close-out carries the register verbatim: *"passed the deterministic gates and the reviewers' audit on this run — a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates."*
- **`needs-irreversible`** → **pause 3's** verbatim guardrail flow (name the action + its consequence in plain English, ask; never proceed on silence).
- **`new-tier12`** → the **step-10 re-triage** interaction (a finding outside the item — show what surfaced, let the user fold it in / re-order / carry on; never silently absorbed).
- **`not-green`** (the cap) → the **item-failure pause**: *"not green; here is the residual"* + **nothing partial landed** — the branch is left for inspection, nothing merged. Offer retry / skip / stop.
- **`blocked`** → report the boundary error plainly (e.g. a `check:"manual"` criterion needs a human, or criteria exist with no run-the-app command) and run the item watched instead.

---

## The procedure *(watched, decision-gated)*

### 1. Triage — locate the item(s) and confirm the worklist

Read **three candidate sources** in `docs/claugentic-ROADMAP.md`: the **`harness-audit:backlog` fence** (engineering), the **`harness-product:backlog` fence** (gap-mode findings, if present), and the durable **`### Bugs` section** *outside* the fences (planless one-line defect jottings). This is **build-TRIAGE** — the 3-source SELECT assembling the *worklist*, distinct from a finder's own per-run SELECT (`docs/claugentic-WORKFLOW.md` → **The finder pipeline** → *"Two SELECTs at two altitudes."*).

Present **one worklist interleaved by tier** — all tier-1 across all three sources, then tier-2, then tier-3 — each **origin-tagged** (`engineering` / `product` / `bug`). **A Bug is a planless one-liner until selected: selecting it COMMITS it → triggers its plan**; a committed Bug then runs step 3 like any other item. **Dedup:** one issue flagged by both fences appears **once with both origins** (a priority signal), labelled *"merged from N findings"* — judgment, not a key-match, so merged rows are always shown as merged, never hidden.

**Honor the rejected-findings memory** — the **`<!-- harness-audit:rejected-findings -->`-fenced list** in `docs/claugentic-ROADMAP.md` (create-on-first-use, user-owned; `audit` defines it). Read it before presenting the worklist; **a dropped finding stays dropped.** Steps 10 and 11 read the same fence.

Two stop-conditions hold **before** any selection:

- **No backlog, or it's stale** (no `harness-audit:backlog` fence, or it predates the current code) → **don't invent one.** Say so plainly and suggest running **`/claugentic-dev-harness:audit`** first.
- **Empty backlog / already-sound** (Tier 1 **and** Tier 2 empty across both fences **and** no `### Bugs` jottings) → **don't enter the build flow and don't manufacture work.** Reuse the audit's terminal phrasing plus the real next step (a fork, never a dead end): *"Sound on the audited dimensions — what remains is optional polish; you don't need to keep re-auditing. From here you can start something new — just tell me what you want to build — or stop."*

**First-run path — engineering only, no product spec yet.** Audit fence present, **no `harness-product:backlog` fence** → present the engineering worklist alone plus a soft one-line invite (*"no product spec yet — run `/claugentic-dev-harness:product` spec mode for intent-vs-implementation checks too"*) and carry on. **Never imply the product check is broken, failing, or skipped** — there's no spec to check against yet.

Otherwise branch on **how many items the ask names:**

**(a) One named item — the fast path (no triage ceremony).** *"build Tier-1 item 2"*, *"build the input-validation item"*, or a plain-English description (*"fix the thing where the form doesn't save"*) — matched to exactly one item by tier+number or title/topic, and confirmed. **Ambiguous match → ask**, naming the candidates; never guess. Then step 2 with a one-item worklist. **No tiered list, no "start now?" gate** — a specific ask is already the go-ahead.

**(b) More than one item, a tier shortcut, or no item named — multi-item triage:**

1. **Present the tiered backlog** as `audit` wrote it (tier · title · tag · the one-line "why it matters") — read the fence, don't re-audit — and **let the user pick** individual items and/or tier shortcuts (*"all of Tier-2"*, expanding in backlog order).
2. **Confirm the ordered worklist** as a numbered read-back in build order; the user may re-order or drop any. **Default order = the backlog's own** (Tier-1 #1 first — the test baseline gates later refactors), but the user's order wins. Add **one passive tip line** (needs no answer): *"(tip: you can say 'spec everything first' to approve the whole list in one sitting)"*.
3. **"Start now?" — the explicit gate into the loop.** Nothing is built until the user says go; "yes" → the loop (step 9), "no" → stop.

**The batch ask (recognized here, not a standing question).** *"Spec everything first," "approve them all in one sitting," "batch approve"* → run **Batch approval (on request)** instead of entering the loop. **Absent the ask, as-we-go is unchanged** — the only addition is the passive tip line.

---

## The per-item engine *(steps 2–8 — one item, start to landed)*

Steps 2–8 build **one** item end-to-end — once on the fast path, per worklist item in the loop (step 9).

### 2. Tag → discipline

The item's tag (`refactor` · `capability-upgrade` · `dependency-health` · `bug` · `feature`) **selects the discipline** — the mapping is the **tag→discipline table in `docs/claugentic-WORKFLOW.md`** (*Executing an audit backlog item*). Do not restate the table here.

Enforce **one** thing up front, because it can stop the item before planning: a **`refactor` on untested behavior-bearing code is characterization-tests-first — a HARD precondition**, and **cannot start until its Tier-1 "establish a test baseline" item is done.** Baseline absent → **stop and ask** rather than touching code, using the WORKFLOW table's verbatim pause narration, then **offer to build the test-baseline item instead.** (Upheld by the implementer + the Verify gate; a mechanical `PreToolUse` hook was declined by design — never imply a mechanical gate exists or is coming.)

### 3. Auto-drive Plan → Review *(Stages 2–3 — no pause)*

**Start from the item's pre-made plan if it has one** — a committed item may already carry a **plan file in `.claude/plans/`** from the architect-pass (the finder-pipeline PLAN step). **START FROM IT** — don't re-draft; **currency-check it** (re-confirm if landed work has since touched its named files, refreshing the affected sections). It is **`synthesizer-gate`-gated (plan altitude) reviewed groundwork, not a guarantee of quality** — the Review below still runs.

**Else produce it architecture-first via Stage 2 — the architect-pass** (`docs/claugentic-WORKFLOW.md` → Stage 2), drafting `.claude/plans/NNNN-<item>.md` **structured by `docs/claugentic-PLAN_TEMPLATE.md`** (incl. **Architecture & holistic fit** — the forcing function) and sliced into ≤1-session units per the WORKFLOW *Principles*. Either way the plan precedes the item's slices (at most one fresh plan at a time); **the deep per-slice Spec stays just-in-time in step 4** — selection settled *scope*, the per-slice Spec is the *step*-pruning gate.

Then spawn **`claugentic-dev-harness:synthesizer-gate`** (plan-gate altitude) to critique the plan adversarially, **escalating to the diverse panel per the WORKFLOW Principles trigger**: a contested design fork or a trust/honesty surface adds **`claugentic-dev-harness:yagni-sentinel`** + **`claugentic-dev-harness:honesty-reviewer`**; a user-facing change also adds **`claugentic-dev-harness:product-designer`**. Iterate until the verdict is **PASS**.

### 4. Spec + THE PAUSE *(Stages 4–5 — pause 1, the spec, before any code)*

Write the spec into the plan (file-by-file changes, signatures, tests, acceptance, the in-scope `docs/claugentic-standards/` dimensions). Then **pause for the user's approval — no code before "yes."**

At the pause, render the plan's **plain-English approval triad VERBATIM, BEFORE any technical detail** — this is the non-engineer's steering wheel:

> - **What this builds:** …
> - **What "done" means for you:** …
> - **What you're accepting (risks / trade-offs):** …

*What was just done* = the spec is written and reviewed · *what's being decided* = whether to build it (a class-(a)/(b) call that's yours) · *your options* = approve, adjust, or stop. The file-by-file detail sits **beneath** the triad, to verify against, not to decode. **Wait for an explicit yes before Stage 6.**

### 5. Implement *(Stage 6 — no pause)*

On approval, spawn **`claugentic-dev-harness:implementer`** for the slice (one slice per session, isolated, lands vertically complete per the WORKFLOW).

**If the item won't fit one session** — it needs re-slicing mid-build — **pause and ask; never silently re-plan.** Say plainly that it's bigger than one clean slice, and offer to re-slice it (re-confirming the new shape) before continuing.

### 6. Verify *(Stage 7 — no pause unless it fails)*

Dial the Verify depth per the **WORKFLOW's named triggers** (the Stage-0 "substantial" triggers): a **solo `synthesizer-gate`** is the small/local default; a named trigger **fans out** the `lens-reviewer`s + `yagni-sentinel`; a trust/honesty/user-facing surface convenes the **diverse panel**, which `synthesizer-gate` then synthesizes. A finding re-check is one **`claugentic-dev-harness:finding-verifier`** per finding. Run the **Definition-of-Done deterministic run-gates** (canonical list: the WORKFLOW DoD). **On the LAST slice of a multi-slice item's plan, make it the whole-feature closing pass** (WORKFLOW → *Stage 7, the whole-feature closing pass*): hand the item's Stage-1 job-to-be-done into the `synthesizer-gate` verify prompt so it also confirms the *assembled* feature works end-to-end — model-upheld; the orchestrator passes the JTBD.

**On a failed Verify, iterate implement→verify up to a small bounded number of attempts (2–3).** Still failing → **pause and ask — the item-failure pause:**

- Report **in plain English what failed and why** — don't dress a failed slice as done.
- State plainly: **nothing partial landed — the slice lands complete or not at all.**
- Offer the real options: **retry · skip this item · stop.**

### 7. Pre-land PAUSE + Land *(Stage 8 — pauses 2 and 3)*

**Pause before landing** (pause 2), same frame: *what was just done* = the slice is built and passed Verify · *what's being decided* = whether to land it · *options* = land · hold · stop. **Gloss the git vocabulary:** *"landing means saving this change into the project's history (a commit) on this working branch — still local, nothing shared out yet."*

**The irreversible hard-stop** (pause 3) — before **any** action in the **irreversible hard-stop set** (*Guardrails* below is the single authoritative list, including push-to-`main`), **stop, name the exact action and its consequence in plain English, and ask; never proceed on silence.** **Bridge the git vocabulary the same way** — e.g. *"'push to main' means publishing this to the shared copy everyone else pulls from; once it's out, others can build on it, so it's hard to take back. Want me to go ahead?"* — never leave "push", "main", or "commit" unglossed here.

On approval, land per the WORKFLOW Stage 8: a **conventional commit**, **dispose of the plan** (below), append a **`docs/claugentic-DECISIONS.md`** line for any non-trivial choice, and **run the Stage-9 harvest checklist** (`docs/claugentic-WORKFLOW.md` §9).

**Disposition before removal (gated only on the committed slice).** A plan leaves `.claude/plans/` (git history keeps it) only once **every remaining unchecked item has a disposition** — *never* gated on the deferred/rejected/blocked parts (WORKFLOW *Plan file lifecycle* owns the three dispositions). **Don't let a plan linger on an external blocker** — defer-to-new-plan (or reject) and **close now**. A substantial remainder → a **new plan file** (+ one roadmap line); a small one → a **roadmap item**; a rejected one → a **declined-decision line**.

### 8. Close-out *(per item)*

Tell the user **what landed** and **which gate-class passed — separately, never a blanket "verified/done":**

- the **deterministic gates** that passed — name the ones this repo actually ran; the canonical list is `docs/claugentic-WORKFLOW.md` → Definition of Done (a second copy of that roster here is how a close-out goes stale);
- the **reviewer sign-offs** (the in-scope `docs/claugentic-standards/` dimensions the `synthesizer-gate` audited) — model-upheld judgment, **"passed the checks and the reviewer's audit,"** never "proven correct";
- the **run's model-relationship disclosure** — when the engine result's `crossModel` is not `confirmed`, state that tag **verbatim**, never a bare pass with the disclosure left in the JSON.

**Surface the flags — "things to review."** List **every flag** raised this run (each a one-line *what + the chosen default* from the plan file's `Flags:` sub-line) for **async review, now that the work has landed.** A **distinct concern from the plan disposition** (which closes out the *unbuilt* items): two separate lists, never merged. **No flags → say so explicitly** (*"no judgment-calls to review this slice"*), never a silent skip. (An *irreversible* call was never a flag — it was a class-(c) stop that already paused mid-run.)

**Surface the Stage-9 harvest result** — one line naming what it captured (*"Lessons captured this slice: <X>"* — a `docs/claugentic-DECISIONS.md` line, a ROADMAP follow-up, a CLAUDE.md note) — or explicitly *"nothing durable to capture this slice."* Either way the closing loop is **demonstrably visible**, never a silent no-op.

**Then branch on the worklist:**

- **Single named item (the fast path), or the worklist now exhausted** → next step: **another backlog item the same way, or re-run `/claugentic-dev-harness:audit`** — finished when Tier 1 and Tier 2 come back empty (a loop runs the **stop/done** closing audit first). **When product-origin items were in the worklist, or a `harness-product:backlog` fence exists,** ALSO offer **re-running `/claugentic-dev-harness:product` gap mode** — `build` never regenerates the product fence, so it goes stale as engineering items land.
- **More worklist items remain** → skip the next-step prompt; this close-out is **one completed beat** (*"landed item 2 of 5"*), then on to the **scoped re-audit** (step 10).

---

## The loop *(steps 9–11 — multi-item)*

### 9. The build loop *(the worklist, item by item)*

On "start now?" yes, work the **confirmed ordered worklist** one item at a time through the per-item engine (steps 2–8). After each item lands, run the **scoped re-audit** (step 10), which decides **pause-and-re-triage** vs **auto-continue**. Worklist exhausted, no re-triage pending → **stop/done** (step 11).

Every per-item stop holds across the loop: **before-land** and **irreversible** (class (c)) **fire on every item**; the **spec** stop (class (a)/(b)) fires per item **or is pre-satisfied by a batch sitting** — never skipped, only satisfied earlier. **The loop never suppresses a stop that hasn't been explicitly satisfied.** The build-to-green unlock contract, the irreversible hard-stop set, and no-invented-scope hold unchanged across the whole loop.

### 10. The scoped re-audit + re-triage *(after each landed item)*

After an item lands, **re-run the audit scoped to the touched cells** — the `(module | dir)` cells covering the files the item changed. Spawn the audit's existing machinery over **only those cells** (the `lens-reviewer`s for the relevant modules over the touched dirs, then the universal `finding-verifier` re-check) — not a full repo sweep.

**Be honest about its scope.** It covers only those cells; **cross-file fallout beyond them is owned by the closing full audit (step 11), not claimed here.** Never imply it covers the whole repo, and never describe it as chasing "dependents" — **the harness has no dependency graph and claims none.** Like the closing audit, it regenerates the **engineering** `harness-audit:backlog` fence **only** — never gap mode, never the `harness-product:backlog` fence.

Carry each finding's **verification tag unchanged** — `(checked against the code)` / `(could not confirm independently -- model's assertion)` / `(! not yet verified -- re-run to confirm)` mean exactly what they mean in the `audit` skill (the single source): a clean-context judge is a reduction of false confidence, same model family so blind spots aren't independent — **not** a deterministic guarantee. Don't upgrade the framing because it's the loop re-checking its own work.

**Then decide — continue or re-triage:**

- **Any NEW Tier-1 or Tier-2 finding** (one the original backlog didn't carry) → **pause to re-triage**, framed as **the safety feature it is**: *"The re-check found new important work — that's the system catching things early, not a failure. Here's what surfaced; do you want to fold it into the list, re-order, or carry on as planned?"* The user **re-picks / re-orders** the remainder (same interaction as step 1b) — then **confirm the updated worklist as a numbered list and re-fire "start now?"** (the new count resets the "item N of M" beats, so position narration never drifts). Never silently absorb new scope, never silently skip it.
- **Nothing new, or only Tier-3 polish** → **auto-continue** — just the completed beat (*"clean — moving to item 3"*). A clean re-check is **not** a stop; interruptions taper as the criticals clear (the safety-over-fatigue trade).

### 11. Stop / done *(the worklist is exhausted)*

Run **one `standard` full audit** (the `audit` skill, repo-wide — this owns the cross-file fallout the scoped re-audits didn't claim). Same fence rule as step 10: **engineering fence only**, never the product fence (auto-refreshing that at close is a separate future capability). Then:

- **Tier 1 and Tier 2 both empty** → surface the audit's terminal signal **verbatim**, plus the fork (never a dead end):

  > Sound on the audited dimensions — what remains is optional polish; you don't need to keep re-auditing.

  …then: **start something new — just tell me what you want to build — or stop.**
- **Tier 1 or Tier 2 not empty** → **surface the remainder for a final triage decision.** Show what the closing audit found and ask plainly: **build more now (re-enter triage on the new list), or stop here.** **Never silently continue past the agreed worklist** — no-invented-scope applies to the worklist itself.

---

## Batch approval (on request) *(front-load the spec decisions into one sitting)*

Triggered **only** by the batch ask at step 1b. It invents no steps — it **re-orders when the existing pauses fire**: every item's Stage-5 spec pause is satisfied up front, in **one sitting**, leaving the run only the lighter per-item confirms. The as-we-go default is untouched.

**At the ask, answer with both honesty lines once — no confirm-shaming, no penalty framing:**

> Spec-everything-first front-loads the approval decisions into one sitting, so you get **fewer interruptions: you'll still confirm each item before it lands, anything irreversible still stops, and if earlier work shifts the ground under a later item I'll pause to re-confirm.** And planning every item up front means a dropped item's planning is already spent.

(Still several touchpoints — front-loaded *spec* decisions, not zero presence. **Prep-cost, said plainly:** N items = N plan + review + spec cycles before anything builds, so a session boundary may land mid-prep — the durable `Spec'd`/`Approved` states absorb it, so a resumed run picks up derivably.)

**Prep — no code.** Per worklist item run the **existing steps 2–4** (tag → discipline → plan → panel review → spec) and **stop before any code**; adjust-iterations reuse the **existing iterate-until-PASS review loop** (step 3). No new mechanics — steps 2–4 for every item before the sitting, rather than one at a time.

**The sitting — Stage 5, satisfied per item, up front (ROSTER-FIRST).** Lead with a **scannable roster** — **one line per item**: *number · title · one-line "what this builds" · one-line "what you're accepting"* — with the **full approval triad per item beneath, to drill into** (step 4's triad-above-detail pattern). Per item the choices are:

- **Approve** → flip that item's plan file to **`Status: Approved`** — **the durable mark** the run and any resume read.
- **Adjust** → amend the spec and re-render that item's triad; a **material change re-enters the review loop** (step 3) before it can be approved.
- **Drop** → unjudged, **no penalty framing** — as easy and as blame-free as approve.

**Close the sitting by re-confirming the surviving ordered list** (a numbered read-back, the same shape as step 1b) — **and restate what batch does not remove** (the per-item land confirm, the irreversible stop, the currency re-confirm). The echo matters: on a mid-prep resume the sitting may run in a session where the user never heard the ask copy.

**The run.** Work the surviving list through the **existing loop (steps 5–8 per item)**. The **spec pause is pre-satisfied per item by the sitting** (its plan reads `Status: Approved`) — every other pause is unchanged: **pre-land per item · the irreversible hard-stop · the re-slice and item-failure pauses · the re-triage on a new Tier-1/2 (step 10) · the currency pause below.** Because batch invites the user to step away, the **completed beats between items are their primary thread back into the run.**

**The spec-currency check — before item *k* implements.** A later item's spec was written before earlier items landed, so the ground may have moved. Intersect **the files landed since the sitting** (the landed items' plan *Affected-files* lists / `git log`) with **the files item *k*'s spec names**: **no overlap** → proceed; **overlap** → the **currency pause** in the standard frame — *what changed* (the landed work touching this item's named files) · *what's being decided* (re-confirm the spec as-is, **or** re-spec, which **re-fires the Stage-5 pause for that item**) · *the options* — framed as **the safety net promised at the sitting, never an error and never a reversal of the user's approval.** State it plainly: **file-level overlap, NOT semantic impact analysis** — no dependency graph, none claimed; semantic cross-file fallout stays owned by steps 10 + 11. Model-upheld.

---

## The resume contract *(derive the worklist — don't store it)*

A resumed run **reconstructs** the worklist from the state stores the harness already keeps — **there is no build-session state file.** Derive, don't store:

- **The item universe + status** = the three triage sources (step 1). **Each fence's `done-cells`/`pending-cells` resumes against its OWN generating skill — the cells are NEVER crossed:** the engineering fence's `module|dir` cells against the audit script, the product fence's criterion-id cells against the gap script. Plan-files remain the state-of-record for in-flight work, so a **mid-build item never vanishes when a fence regenerates.**
- **An in-flight item** = its **plan file in `.claude/plans/`** with **unchecked implementation boxes**. **The decomposition checkboxes are the authoritative resume signal — the plan's prose `Resumable from:` line is a convenience derived from them, not a second source of truth.** On disagreement **the unchecked boxes win** and the `Resumable from:` line is what gets corrected. **Offer to continue it/them first** — a **batch run can leave SEVERAL plans in-flight**, so offer **all** of them.
- **A done item** = its **plan no longer in `.claude/plans/`** (removed at Land, step 7 — git history keeps it).

**The three batch-derived approval states** (from the plan files' `Status` line — the durable mark the sitting writes): **`Status: Spec'd`** (or in review) = **awaiting a sitting** · **`Status: Approved`** = **build when reached** · **unchecked implementation boxes** = **in-flight**. **Approval is never inferred** — only an explicit `Status: Approved` counts, so a run that died mid-prep or mid-sitting resumes derivably.

Then **re-confirm the remaining selection + order** (the step-1b confirm + "start now?"). Be honest: the **picked order is the one thing not durably stored.** A **5-second re-confirm** ("here's what's left — same order?") replaces a third state store — the deliberate trade (derive-don't-store beats a worklist file that could drift from the backlog).

---

## Guardrails *(non-negotiable, in every mode)*

- **Irreversible hard-stops (decision-gated class (c)).** Before any **push to a shared remote (incl. `main`), deploy, data deletion, spend, or external side-effect**: stop, name the action + its consequence in plain English, and **ask. Never proceed on silence.** A HARD stop the FLAG path can **never** absorb, even on a low-confidence call — watched or build-to-green alike, the line autonomy never crosses unasked. **Model-upheld:** this instruction is what holds it — no hook forces the stop (`docs/claugentic-WORKFLOW.md` → *Decision-gated autonomy* is the canonical statement).
- **Never invent scope — the in-flight split.** Work that surfaces mid-build is **never silently absorbed**; the user makes the call (WORKFLOW *Plan file lifecycle → in-flight split* is the source of truth): **(a) intrinsic to the item** → **fold it in** — account · spec · deliver, re-running the steps; if that breaks the one-session fit, **pause and re-slice** (step 5), never half-build. **(b) out-of-scope** (a genuinely-new feature, or a defect) → **not built** here; it goes to **`docs/claugentic-ROADMAP.md`** — a new feature to the relevant backlog for the user's approval, **a defect to the durable `Bugs` section** (a one-line, planless jotting; selecting it later triggers its own plan). **No debt is left behind either way** — deferring scope (tracked, built wholly later) is not creating debt (a half-done thing in code). **Model-upheld + reviewer-caught at Verify, not a mechanical guarantee.**
- **Honesty register.** Say a slice **"passed the checks and the reviewer's audit,"** never "proven correct" / "guaranteed" / "bug-free." **"done" is scoped to the audited dimensions** (and the deterministic gates that ran), never a blanket claim. A build-to-green decline names exactly which unlock conditions are unmet and what evidence was checked — never a vague "not yet," never a silent degrade to a weaker promise. Build-to-green, when it runs, is a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates (and the clean-context judge is a reduction of rubber-stamping risk, not a mechanical guarantee — same model family, so blind spots aren't independent).
