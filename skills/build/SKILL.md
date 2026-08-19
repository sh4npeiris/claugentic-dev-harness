---
description: >-
  Drive your audit backlog through the full reviewed pipeline — plan → adversarial review → spec → your approval → implement → verify → land — pausing only at the decisions that are genuinely yours. Pick one item, several, or a whole tier; it works them one by one, re-checking the code it touched between items and pausing for you only when new important work surfaces, to the honest "sound on the audited dimensions" stop-signal. Decision-gated: it proceeds autonomously and stops only for a real decision (a design fork · a spec trade-off · anything irreversible), researches factual uncertainties instead of asking, flags reversible judgment-calls and surfaces them at the close. Honest about its limits: every item's spec needs your approval before any code — per item as you go, or all at once up front in a single approval sitting if you say "spec everything first" — and it stops before anything irreversible (a discipline this skill instructs — model-upheld, never a mechanical gate); running unwatched (build-to-green) is requestable but runs only where the repo has earned it (CI running the gates, a test baseline, a testable approved spec) and the engine is installed; otherwise it declines naming exactly what's missing and offers a watched run.
---

# /claugentic-dev-harness:build

> **Agent ids:** every role named below is one of this plugin's bundled agents — when you spawn one, use its **namespaced id** `claugentic-dev-harness:<role>` (e.g. `claugentic-dev-harness:lens-reviewer`); built-ins (`general-purpose`, `Explore`) stay bare.

The **go-button for your backlog.** Point it at one item from your `docs/claugentic-ROADMAP.md`
backlog — or pick several, or a whole tier — and it drives the whole professional pipeline
for you — plan → adversarial review → spec → **your approval** → build → review-the-work →
land — pausing only where your judgment is load-bearing. A single named item stays the fast
path (no triage ceremony); ask for more than one and it confirms an ordered worklist, then
works it item-by-item to the honest stop-signal.

## How this skill works

Build mode is a **thin orchestration layer** — it does not invent process, it **drives**
the existing one. The pipeline it runs is **`docs/claugentic-WORKFLOW.md`** (the source of truth for
the stages, the tag→discipline mapping, the Verify dial, the Definition of Done, and the
Stage-9 harvest); the item universe is the **`harness-audit:backlog` fence** that
`/claugentic-dev-harness:audit` writes into `docs/claugentic-ROADMAP.md`. This skill points at both —
it does not restate them.

A **top-level agent (the orchestrator) runs this skill** — it spawns the pipeline
subagents (`synthesizer-gate`, `implementer`, the lenses, the
diverse panel), and subagents can't spawn subagents (the same constraint `audit` and `init`
carry). Invoke it in plain English — *"build Tier-1 item 2"*, *"build the input-validation
item"*, *"/claugentic-dev-harness:build the test-baseline item"*.

**What "decision-gated" means for you:** you can name one item and get back a landed,
reviewed change that **auto-drives, stopping only for a decision that is genuinely yours**
(the model is `docs/claugentic-WORKFLOW.md` → *Decision-gated autonomy* — read it there;
this skill applies it). Each stop is in plain English (*what was just done · what's being
decided · your options*). The **three blocking-stop classes** map onto the three concrete
pauses below — they are the *same* three, not a parallel set:

- **(a) a design fork / (b) a spec trade-off** → the **spec pause, before any code** — fired
  **per item** as you go, **or pre-satisfied per item up front in a single approval sitting**
  if you ask to *spec everything first* (see *Batch approval (on request)*). This is where a
  genuine fork or a trade-off-to-accept becomes your call.
- **(c) an irreversible / outward action** → the **before-land pause** and the **irreversible
  hard-stop**. A wrong "proceed" here can't be undone by later review, so it is a HARD stop the
  flag path can **never** absorb — even on a low-confidence call.

Everything else **auto-drives**: a **factual / technical uncertainty is researched (cited),
not asked**; a **reversible judgment-call** (a deviation from the spec · an accepted risk · a
low-confidence choice) is **flagged — one line + the chosen default — and the run CONTINUES**,
surfaced for you at the close (step 8), never as a mid-run interruption. A failed item
**pauses and tells you plainly that nothing partial landed**. *(Two further pauses fire only on
exceptions — a mid-build re-slice and a failed item — never on the happy path.)*

**The full-backlog loop is live.** Pick several items (or "all of Tier-1"), confirm the
ordered worklist, and it works them one by one — after each landed item it **re-checks the
code that item touched**, pausing to let you re-pick **only when new important work surfaces**
(otherwise it just continues the agreed list); when the worklist is done it runs **one full
audit** and tells you honestly whether you've reached *"sound on the audited dimensions."*
The single-named-item path above stays the fast path — the loop is opt-in by asking for more
than one.

---

## Mode handling *(read this first)*

**Decision-gated is how build mode stops, always** — it proceeds autonomously and stops only
for a genuine user-decision (the model is `docs/claugentic-WORKFLOW.md` → *Decision-gated
autonomy*: STOP only for a design fork · a spec trade-off · an irreversible action · RESEARCH a
factual uncertainty · FLAG a reversible judgment + CONTINUE · SURFACE flags at the close). That
governs **when to stop** on *every* run. The mode below is a **separate axis — who watches the
run** — earned per-repo, by evidence, never assumed:

- **Watched (the default — no preconditions).** The orchestrator drives the per-item engine in
  this session, applying the decision-gated rules above. If the user names no mode, this runs.
- **`build-to-green` — running unwatched (requestable, earned per-repo).** Any ask to run
  unwatched — *"autopilot"*, *"run unwatched"*, *"build to green"* — is a build-to-green
  request. Before agreeing, check the **unlock conditions** below and **state the evidence per
  condition** (what you looked at, what you found). All met → run the item through the engine
  script (`${CLAUDE_PLUGIN_ROOT}/engine/build-item.js` via the Workflow tool — the skill invokes
  the script, and the script then runs the implement → gates → verify → QA → fix loop
  mechanically), returning to you only at the **decision-gated hard stops, now surfaced as engine
  returns: before land · before anything irreversible (class (c)) · on a new Tier-1/2 finding.**
  Any condition unmet → the decline below, naming exactly what's missing, then offer the watched
  run. *(Unwatched changes who is present, not when to stop — the same decision-gated rules hold;
  reversible judgments are flagged-and-continued, the irreversible class (c) is a return, never
  absorbed.)*

Build-to-green is **a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates** (the land-gate hook · the secret-scan — the *deterministic-gates* shard indexed in `docs/claugentic-DECISIONS.md`; the characterization-enforcement hook was considered and **declined** — that discipline stays model-upheld by design).

**The unlock conditions — judgment with stated evidence.** These checks are the skill reading your repo and saying what it found — honestly labeled model judgment, never a mechanical gate:

1. **CI runs the deterministic gates.** Evidence: a CI config (e.g. `.github/workflows/*.yml`) whose steps run this repo's Definition-of-Done deterministic gates (the test suite + the gate scripts). Name the file and the commands found.
2. **A test baseline covers the code this item touches.** Evidence: named test files that assert observable behavior of the files the item will change (not merely execute them) — so a regression in that behavior would fail a test. (The `refactor` characterization-tests-first precondition is this condition's hard case — unchanged.)
3. **The item traces to an approved spec with testable acceptance criteria.** Evidence: a plan in `.claude/plans/` with `Status: Approved` whose acceptance criteria are all checkable without a human mid-run — each maps to a deterministic gate or test, or to a `docs/claugentic-PRODUCT_SPEC.md` criterion whose `check` is `e2e` or `api`. A `check: "manual"` criterion needs a human, so it keeps that item on the watched run.

**And one session precondition (not a repo condition):** build-to-green runs **only** via `engine/build-item.js` through the Workflow tool — there is **no prose-orchestrated build-to-green, ever** (an unwatched prose loop is exactly the unearned autonomy the who-watches axis exists to prevent). The Workflow tool or the script unavailable → named in the decline like any other missing condition.

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

All unlock conditions met → invoke the engine (`${CLAUDE_PLUGIN_ROOT}/engine/build-item.js`
via the Workflow tool). **The skill invokes the engine; the engine then runs the loop
mechanically — invoking it is still model-upheld** (the platform doesn't auto-fire workflows).
Once invoked, the engine runs implement (in a worktree) → deterministic gates → the `verify.js`
panel → `qa.js` (when criteria exist) → fix, until green or the iteration/budget cap.

**The args the skill assembles** (the engine validates them at the boundary and throws on any
invalid field — fail loud):

- `item` — `{ id, title, tag, planPath, specText` (the approved spec section, verbatim) `,
  acceptanceCriteria }`. `acceptanceCriteria` is the item's frozen-schema criteria
  (`{id,feature,flow,expect,states,check}`) from the item's spec / `docs/claugentic-PRODUCT_SPEC.md`; `[]`
  when the item has none. Optional `dimensions` (the in-scope `docs/claugentic-standards/` slugs for the
  Verify panel), `trustSurface`, `appUrl`.
- `repo` — `{ root, baseBranch, gateCommands` (this repo's **DoD deterministic gate commands** —
  the test suite + the gate scripts, from the WORKFLOW DoD / `init`-recorded tooling; **non-empty**,
  zero gates would make "green" a lie) `, runApp` (the recorded run-the-app command, or `null`) `,
  pluginRoot` (the expanded `${CLAUDE_PLUGIN_ROOT}`, for the child-workflow paths) `}`.
- `caps` — `{ maxIterations` (default 3 — the bounded 2–3) `, budget, stageTimeouts }`.
  `stageTimeouts` is the optional **per-stage duration bound** `{ implement?, gates?, qaBoot? }`
  (positive-integer seconds; the engine rejects any unknown key, non-integer/≤0 value, or a value
  **> 600** — the Bash-tool hard max — fail loud, never silently clamped). Defaults: `implement` and
  `gates` default to **600s**; `qaBoot` has **no engine default** (`unset` ⇒ qa.js's own 60s default;
  qa.js silently clamps any value to its 300s cap). **Honesty caveats — the three-way enforcement
  register (the bounds do NOT enforce equally):** **gates** = agent-applied per-command Bash-tool
  `timeout` **+ a mechanical red decision** (a timed-out command reports exitCode 124 → `gatesGreen`
  reads it red); **qaBoot** = a **mechanical clamp** in qa.js + an agent-executed bounded readiness
  probe; **implement/fix** = an **instruction-only** anti-hang nudge (IMPLEMENT_SCHEMA has no
  exit-code channel, so a runaway surfaces only downstream via the gates stage + the iteration cap —
  model-upheld, NOT a mechanical guarantee). The bound is **per-command within a stage, never a stage
  wall-clock total**; residual: a single legitimate command exceeding the 600s hard max can't be
  bounded-and-completed in one foreground call — split that repo's suite, or it isn't bounded-runnable.
- `builderFamily` — the orchestrator's session model family (used by the honest same-model reporter).

**The engine's pauses are returns — map each returned status to its pause/interaction:**

- **`green`** → the **before-land pause** (pause 2). The engine NEVER lands or pushes — landing,
  the commit, and any push stay **the orchestrator's act**, behind the irreversible hard-stop
  set. The green close-out carries the register verbatim: *"passed the deterministic gates and
  the reviewers' audit on this run — a reduction of unwatched-run risk, never a substitute for
  the unbuilt deterministic trust-gates."*
- **`needs-irreversible`** → **pause 3's** verbatim guardrail flow (name the action + its
  consequence in plain English, ask; never proceed on silence).
- **`new-tier12`** → the **step-10 re-triage** interaction (a finding outside the item — show
  what surfaced, let the user fold it in / re-order / carry on; never silently absorbed).
- **`not-green`** (the cap) → the **item-failure pause**: *"not green; here is the residual"* +
  **nothing partial landed** — the branch is left for inspection, nothing merged. Offer
  retry / skip / stop.
- **`blocked`** → report the boundary error plainly (e.g. a `check:"manual"` criterion needs a
  human, or criteria exist with no run-the-app command) and run the item watched instead.

---

## The procedure *(the watched, decision-gated run)*

### 1. Triage — locate the item(s) and confirm the worklist

Read **three candidate sources** in `docs/claugentic-ROADMAP.md` — the **`harness-audit:backlog`
fence** (the engineering item universe the `audit` skill wrote), the **`harness-product:backlog`
fence** (the intent-vs-implementation gaps the `product` gap mode wrote, if present), **and the
durable `### Bugs` section** (`docs/claugentic-ROADMAP.md`, *outside* the fences — the one-line,
planless defect jottings; see *Never invent scope → in-flight split → (b)* below). This is
**build-TRIAGE** — the 3-source SELECT that assembles the *worklist*, distinct from a finder's own
per-run SELECT; see `docs/claugentic-WORKFLOW.md` → **The finder pipeline** → *"Two SELECTs at two
altitudes."* Present **one worklist interleaved by tier** — all tier-1 items across **all three**
sources first, then tier-2, then tier-3 — each item **origin-tagged** (`engineering` / `product` /
`bug`) so the user always sees which source raised it. **A Bug is a planless one-liner until
selected: selecting it COMMITS it → triggers its plan** (per *Commitment, not capture, triggers
the plan* in the finder-pipeline contract; a committed Bug then runs Step 3 like any other item).
**Dedup:** if the same underlying
issue is flagged by both fences, present it once tagged with **both** origins — that's a
priority signal (two lenses flagged it), shown as *"merged from N findings"* so you can verify;
this is a judgment, not a key-match, so I may occasionally miss an overlap (you'd see it twice)
or over-merge two distinct issues (so merged rows are always shown as merged, never hidden).

**Honor the rejected-findings memory.** A user can drop a finding they judge wrong — recorded
in the **`<!-- harness-audit:rejected-findings -->`-fenced list** in `docs/claugentic-ROADMAP.md`
(the create-on-first-use, user-owned memory `audit` defines, mirroring product spec mode's
`<!-- product-critic:rejected-proposals -->` convention). **Read it before presenting the
worklist and don't re-surface a dropped finding** — a dropped finding stays dropped. The same
memory governs the scoped re-audit (step 10) and the closing full audit (step 11): both invoke
the `audit` machinery, which reads this fence and skips listed findings, so a re-audit won't
re-raise something the user already dismissed.

Two stop-conditions hold **before** any selection, single or multi:

- **No backlog, or it's stale** (no `harness-audit:backlog` fence, or it predates the
  current code) → **don't invent one.** Say so plainly and suggest running
  **`/claugentic-dev-harness:audit`** first so there's a current, verified backlog to build
  from.
- **Empty backlog / already-sound** (Tier 1 **and** Tier 2 both empty across both fences **and
  the `### Bugs` section carries no jottings** — only Tier-3 polish, or nothing) → **don't enter
  the build flow and don't manufacture work.**
  Reuse the audit's terminal phrasing **plus the real next step** (a fork, never a dead end):
  *"Sound on the audited dimensions — what remains is optional polish; you don't need to
  keep re-auditing. From here you can start something new — just tell me what you want to
  build — or stop."*

**The common first-run path — engineering only, no product spec yet.** When there's a
`harness-audit:backlog` fence but **no `harness-product:backlog` fence** (the user ran `audit`
but hasn't built a product spec yet), present the **engineering worklist alone** plus a soft
one-line invite — *"no product spec yet — run `/claugentic-dev-harness:product` spec mode for
intent-vs-implementation checks too"* — and carry on normally. **Never imply the product check
is broken, failing, or skipped** — there's simply no spec to check against yet.

Otherwise, branch on **how many items the ask names:**

**(a) One named item — the fast path (no triage ceremony).** When the ask is specific —
*"build Tier-1 item 2"*, *"build the input-validation item"*, **or just describe it in your
own words — *"fix the thing where the form doesn't save"* — and I'll match it to the right
backlog item and confirm** — match the user's words to exactly one item, by tier+number or by
its title/topic. **If the match is ambiguous, ask** — name the candidates and let the user
pick; never guess which item they meant. Then go straight to step 2 with a one-item worklist.
**No tiered list, no "start now?" gate** — a specific ask is already the go-ahead.

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
the **tag→discipline table in `docs/claugentic-WORKFLOW.md`** (*Executing an audit backlog item*);
read it there and apply it. Do not restate the table here.

The **one** behavior to enforce up front (because it can stop the whole item before
planning): a **`refactor` on untested behavior-bearing code is characterization-tests-first
— a HARD precondition.** It **cannot start until its Tier-1 "establish a test baseline" item
is done.** If that baseline is absent, **stop and ask** rather than touching code, using the
WORKFLOW's pause narration:

> Before I tidy this code I need to capture what it currently does as a test, or I can't
> prove I didn't change its behavior — so I'll establish that baseline first.

Then offer to build the test-baseline item instead. (This precondition is upheld by the
implementer + the Verify gate — a mechanical `PreToolUse` enforcement hook was declined by design;
never imply a mechanical gate exists or is coming.)

### 3. Auto-drive Plan → Review *(Stages 2–3 — no pause)*

**Start from the item's pre-made plan if it has one.** A committed item (selected via a finder's
SELECT, or a prior session) may already carry a **plan file in `.claude/plans/`** — produced
preemptively via the architect-pass (the finder-pipeline PLAN step). **If a pre-made plan exists,
START FROM IT** — don't re-draft from scratch; **currency-check it** (re-confirm if landed work has
since touched its named files, refreshing the affected sections). It is **`synthesizer-gate`-gated
(plan altitude) reviewed groundwork, not a guarantee of quality** — the Review below still runs.

**Else produce it architecture-first via Stage 2 — the architect-pass.** When the item has no
pre-made plan, draft `.claude/plans/NNNN-<item>.md` via **Stage 2** (`docs/claugentic-WORKFLOW.md`
→ Stage 2): **2a** plan-mode draft **structured by `docs/claugentic-PLAN_TEMPLATE.md`** (incl. the
**Architecture & holistic fit** section — the forcing function) → **2b** advisory panel **for
substantial work only** (the Stage-0 substantial triggers; trivial plans skip the panel) → **2c**
incorporate → the **Stage-3 `synthesizer-gate` gate** (plan altitude) below. Slice into ≤1-session units per the
WORKFLOW *Principles*. Reference the architect-pass; don't restate it. Either way the plan precedes
the item's slices (architecture-first per the plan-volume bound — at most one fresh plan at a time);
**the deep per-slice Spec stays just-in-time in Step 4** (unchanged — selection settled *scope*; the
per-slice Spec is the *step*-pruning gate, cheaper JIT). Then spawn **`claugentic-dev-harness:synthesizer-gate`** (plan-gate altitude) to
adversarially critique it, **escalating to the diverse panel per the WORKFLOW Principles
trigger**: a contested design fork or a trust/honesty surface adds **`claugentic-dev-harness:yagni-sentinel`** +
**`claugentic-dev-harness:honesty-reviewer`**; a user-facing change also adds **`claugentic-dev-harness:product-designer`**. **Spawn the
judge roles — `claugentic-dev-harness:synthesizer-gate` · `claugentic-dev-harness:honesty-reviewer`** — their independence is of **role and clean context**, never of model; they inherit the session's tier, and the `RUNNING AS:` self-report + same-model tag disclose what resulted
(**`docs/claugentic-WORKFLOW.md` → *Principles*** — point there, don't restate).
Iterate the plan until the review verdict is **PASS**.

**Narrate progress as completed beats only — never an ETA, never a "nearly done."** *"Planned
it · reviewed the plan · folding in the changes…"* — the same calm completed-beat discipline
the `audit` skill uses. A long stretch between pauses is narrated, never silent and never
estimated.

### 4. Spec + THE PAUSE *(Stages 4–5 — pause 1, the spec, before any code)*

Write the spec into the plan (file-by-file changes, signatures, tests, acceptance, the
in-scope `docs/claugentic-standards/` dimensions). Then **pause for the user's approval — no code
before "yes."**

At the pause, render the plan's **plain-English approval triad VERBATIM, BEFORE any
technical detail** — this is the non-engineer's steering wheel:

> - **What this builds:** …
> - **What "done" means for you:** …
> - **What you're accepting (risks / trade-offs):** …

Frame the stop as *what was just done · what's being decided now · your options* —
the spec is written and reviewed; what's being decided is whether to build it (a class-(a)/(b)
decision that's yours); the options are approve, adjust, or stop. The file-by-file detail sits **beneath** the triad, to verify
against, not to decode. **Wait for an explicit yes before Stage 6.**

### 5. Implement *(Stage 6 — no pause)*

On approval, spawn **`claugentic-dev-harness:implementer`** for the slice (one slice per session,
isolated, lands vertically complete per the WORKFLOW). Continue the completed-beat
narration.

**If the item won't fit one session** — it needs re-slicing mid-build — **pause and ask;
never silently re-plan.** Report plainly that it's bigger than one clean slice and offer to
re-slice it (and re-confirm the new shape) before continuing.

### 6. Verify *(Stage 7 — no pause unless it fails)*

Dial the Verify depth per the **WORKFLOW's named triggers** (read them there — the Stage-0
"substantial" triggers): a **solo `synthesizer-gate`** is the small/local default; a named
trigger **fans out** the `lens-reviewer`s + `yagni-sentinel`, and a trust/honesty/user-facing
surface convenes the **diverse panel** per the WORKFLOW Principles — `synthesizer-gate`
then synthesizes. **Spawn the judge roles — `claugentic-dev-harness:synthesizer-gate` · `claugentic-dev-harness:honesty-reviewer` ·
`claugentic-dev-harness:finding-verifier`** — their independence is of **role and clean context**,
never of model; they inherit the session's tier, and the `RUNNING AS:` self-report + same-model tag
disclose what resulted (**`docs/claugentic-WORKFLOW.md` → *Principles*** — point there, don't restate). Run the
**Definition-of-Done deterministic run-gates** (the canonical list lives in the WORKFLOW DoD —
run it, don't restate it). **On the LAST slice of a multi-slice item's plan, make it the
whole-feature closing pass** (WORKFLOW → *Stage 7, the whole-feature closing pass*): hand the
item's Stage-1 job-to-be-done into the `synthesizer-gate` verify prompt so it also confirms the
*assembled* feature works end-to-end — model-upheld, the orchestrator passes the JTBD.

**On a failed Verify, iterate implement→verify up to a small bounded number of attempts
(2–3).** If it still fails after that bound, **pause and ask — the item-failure pause:**

- Report **in plain English what failed and why** — don't dress a failed slice as done.
- State plainly: **nothing partial landed — the slice lands complete or not at all.**
- Offer the real options: **retry · skip this item · stop.**

### 7. Pre-land PAUSE + Land *(Stage 8 — pause 2, before land; pause 3, before anything irreversible)*

**Pause before landing** (pause 2), with the same plain-English frame as the spec pause —
*what was just done* = the slice is built and passed Verify; *what's being decided* =
whether to land it; *your options* = land · hold · stop. **Gloss the git vocabulary in plain
English** (matching the spec pause's plain-English style): *"landing means saving this change
into the project's history (a commit) on this working branch — still local, nothing shared
out yet."*

**The irreversible hard-stop** (pause 3) — before **any** action in the **irreversible
hard-stop set** (see *Guardrails* below — the single authoritative list, including
push-to-`main`), **stop, name the exact action and its consequence in plain English, and
ask; never proceed on silence.** **Bridge the git vocabulary the same way** — e.g.
*"'push to main' means publishing this to the shared copy everyone else pulls from; once it's
out, others can build on it, so it's hard to take back. Want me to go ahead?"* — never leave
"push", "main", or "commit" unglossed at this pause.

On approval, land per the WORKFLOW Stage 8: a **conventional commit**, **dispose of the plan**
(below), append a **`docs/claugentic-DECISIONS.md`** line for any non-trivial choice, and **run
the Stage-9 harvest checklist** (the six sweeps — see `docs/claugentic-WORKFLOW.md` §9; point
at it, don't restate it).

**Disposition before removal (gated only on the committed slice).** A plan is **removed from
`.claude/plans/`** (git history keeps it) only once **every remaining unchecked item has a
disposition** — and *never* gated on the deferred/rejected/blocked parts (the WORKFLOW *Plan
file lifecycle* is the source of truth — point there, don't restate the three dispositions).
**Don't let a plan linger waiting on an external blocker** — defer-to-new-plan (or reject) and
**close now**. A substantial remainder moves into a **new plan file** (+ one roadmap line); a
small one becomes a **roadmap item**; a rejected one becomes a **declined-decision line**.

### 8. Close-out *(per item)*

Tell the user, in plain English, **what landed** and **which gate-class passed — separately,
never a blanket "verified/done":**

- the **deterministic gates** that passed — name the ones this repo actually ran; the canonical
  list is `docs/claugentic-WORKFLOW.md` → Definition of Done (read it there, never a roster
  restated here — a second copy of that list is how a close-out goes stale), and
- the **reviewer sign-offs** (the in-scope `docs/claugentic-standards/` dimensions the
  `synthesizer-gate` audited) — model-upheld judgment, **"passed the checks and the
  reviewer's audit,"** never "proven correct."
- the **run's model-relationship disclosure** — when the engine result's `crossModel` is not
  `confirmed`, state that tag **verbatim** (WORKFLOW → *Principles*), never a bare pass with
  the disclosure left in the JSON.

**Surface the flags — "things to review"** (the decision-gated close-out). List **every flag**
raised during the run (the reversible judgment-calls the run flagged-and-continued — each a
one-line *what + the chosen default* from the plan file's `Flags:` sub-line) so the user can
review them **async, now that the work has landed.** This is a **distinct concern from the plan
disposition** (which closes out the *unbuilt* items): surface flags and dispositions as two
separate lists, never merged. **No flags this run → say so explicitly** (*"no judgment-calls to
review this slice"*) so the close-out is demonstrably visible, never a silent skip. (A flag is a
reversible call the user can now act on or wave through; an *irreversible* call was never a flag
— it was a class-(c) stop that already paused mid-run.)

**Surface the Stage-9 harvest result** (don't let the closing loop no-op silently). Emit one
plain-English line naming what the harvest captured this slice — *"Lessons captured this
slice: <X>"* (e.g. a new `docs/claugentic-DECISIONS.md` line, a ROADMAP follow-up, a CLAUDE.md
note) — or, when nothing durable surfaced, say so explicitly: *"nothing durable to capture
this slice."* Either way the closing loop is **demonstrably visible**, never a silent skip.

**Then branch on the worklist:**

- **Single named item (the fast path), or the worklist is now exhausted** → the next step:
  **another backlog item the same way, or re-run `/claugentic-dev-harness:audit`** for a
  fresh picture — you're finished when Tier 1 and Tier 2 come back empty. (When a loop's
  worklist is exhausted, the **stop/done** flow below runs the closing audit first — that's
  what confirms "finished.") **When the worklist included product-origin items, or a
  `harness-product:backlog` fence exists,** ALSO offer: **re-run `/claugentic-dev-harness:product`
  gap mode for a fresh product picture** — `build` never regenerates the product fence, so it
  can go stale as engineering items land.
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

The per-item decision-gated stops hold across the loop: the **before-land** and **irreversible**
stops (class (c)) **fire on every item**; the **spec** stop (class (a)/(b)) fires per item as
you go, **or is pre-satisfied per item by a batch sitting** (see *Batch approval (on request)*)
— never skipped, only satisfied earlier. **The loop never suppresses a stop that hasn't been
explicitly satisfied.** Reversible judgment-calls are flagged-and-continued across the loop and
surfaced together at the close. The build-to-green unlock contract, the irreversible hard-stop
set, and no-invented-scope all hold unchanged across the whole loop.

### 10. The scoped re-audit + re-triage *(flow 3 — after each landed item)*

After an item lands, **re-run the audit scoped to the touched cells** — the
`(module | dir)` cells (the `audit` skill's existing granularity) that cover the files the
item changed. Spawn the audit's existing machinery over **only those cells** (the
`lens-reviewer`s for the relevant modules over the touched dirs, then the universal
`finding-verifier` re-check) — not a full repo sweep.

**Be honest about this re-audit's scope.** It covers the cells the item touched. **Cross-file
fallout beyond those cells — a change rippling into code the item didn't touch — is owned by
the closing full audit (step 11), not claimed here.** Say so if it matters; do **not** imply
the scoped re-check covers the whole repo, and do **not** describe it as chasing "dependents"
(the harness has no dependency graph — that claim would be a trust-surface over-claim; the
closing audit is what catches cross-file fallout). Like the closing audit, the scoped re-audit
regenerates the **engineering** `harness-audit:backlog` fence **only** — it never runs gap mode
or touches the `harness-product:backlog` fence.

Carry each re-audit finding's **verification tag unchanged** — `(checked against the code)` /
`(could not confirm independently — model's assertion)` / `(⚠ not yet verified — re-run to
confirm)` mean exactly what they mean in the `audit` skill: a reduction of false confidence by
a re-check from a separate specialist agent with a clean context (the clean-context judge; it
never sees the finder's rationale, so it can't rubber-stamp it — it runs the same model family,
so model blind spots aren't independent), **not** a deterministic guarantee. Don't upgrade the framing
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
  is **not** a stop; interruptions taper as the criticals clear. (This is the deliberate
  safety-over-fatigue trade: any new Tier-1/2 interrupts, a clean or polish-only re-check does
  not.)

### 11. Stop / done *(flow 4 — the worklist is exhausted)*

When the worklist is worked through and **no re-triage is pending**, run **one `standard` full
audit** (the `audit` skill, repo-wide — this is what owns the cross-file fallout the scoped
re-audits didn't claim). This regenerates the **engineering** `harness-audit:backlog` fence
**only** — it does **not** run product gap mode and **never touches the
`harness-product:backlog` fence** (the product backlog survives a `build` run untouched;
auto-refreshing it at close is a separate future capability, not this flow). Then:

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

- **Approve** → flip that item's plan file to **`Status: Approved`** (the plan's
  Status field — **this is the durable mark** the run and any resume read; see the
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

- **The item universe + status** = **both backlog fences + the durable `### Bugs` section** in
  `docs/claugentic-ROADMAP.md` (`harness-audit:backlog` + `harness-product:backlog` + Bugs) — the
  three triage sources (step 1); each fence's status block + tiered items, plus the planless Bug
  one-liners. **Each fence's `done-cells`/`pending-cells`
  resumes against its OWN generating skill — the cells are NEVER crossed:** the engineering
  fence's `module|dir` cells resume against the audit script, the product fence's criterion-id
  cells against the gap script. Plan-files remain the state-of-record for in-flight work, so a
  **mid-build item never vanishes when a fence regenerates** — it lives in its plan file, not
  as a fence entry.
- **An in-flight item** = its **plan file in `.claude/plans/`** with **unchecked
  implementation boxes**. **The decomposition checkboxes are the authoritative resume signal —
  the plan's prose `Resumable from:` line is a human-readable convenience derived from them, not
  a second source of truth.** When the two disagree, **the unchecked boxes win** and the
  `Resumable from:` line is the thing to correct (it's kept current *to* the boxes, never
  consulted instead of them). **Offer to continue it/them first** before re-confirming the rest
  of the list — a **batch run can leave SEVERAL plans in-flight** (the run works the approved
  list in order), so offer to continue **all** of them, not just one, before re-confirming the rest.
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

- **Irreversible hard-stops (decision-gated class (c)).** Before any **push to a shared remote
  (incl. `main`), deploy, data deletion, spend, or external side-effect**: stop, name the action
  + its consequence in plain English, and **ask. Never proceed on silence.** This is the
  decision-gated irreversible class (c) — a HARD stop the FLAG path can **never** absorb, even on
  a low-confidence call. It holds on the watched run today and on the build-to-green (unwatched)
  rung — it is the line autonomy never crosses unasked. **Model-upheld:** this instruction is what
  holds it — no hook forces the stop (`docs/claugentic-WORKFLOW.md` → *Decision-gated autonomy* is
  the canonical statement).
- **Never invent scope — the in-flight split.** Work that surfaces mid-build is **never
  silently absorbed**; the user makes the call (the WORKFLOW *Plan file lifecycle → in-flight
  split* is the source of truth — point there, don't restate it):
  - **(a) intrinsic to the item being built** (genuinely part of *this* item's requirement) →
    **fold it in** — account · spec · deliver, re-running the steps; the slice grows because it
    *is* the feature. If folding it makes the slice no longer fit one session, **pause and
    re-slice** (step 5's re-slice pause), never half-build.
  - **(b) out-of-scope** (a genuinely-new feature, or a defect) → it is **not built** here; it
    goes to **`docs/claugentic-ROADMAP.md`** — a new feature to the relevant backlog for the
    user's approval, **a defect to the durable `Bugs` section** (a one-line, planless jotting;
    selecting it later triggers its own plan). The work never silently expands.
  - **No debt is left behind either way** — deferring scope (tracked, built wholly later) is not
    creating debt (a half-done thing in code). This is **model-upheld + reviewer-caught at
    Verify, not a mechanical guarantee.**
- **Honesty register.** Say a slice **"passed the checks and the reviewer's audit,"** never
  "proven correct" / "guaranteed" / "bug-free." **"done" is scoped to the audited
  dimensions** (and the deterministic gates that ran), never a blanket claim. Progress is
  **completed-beat narration, never an ETA** or a "nearly finished." A build-to-green decline
  names exactly which unlock conditions are unmet and what evidence was checked — never a vague
  "not yet," never a silent degrade to a weaker promise. Build-to-green, when it runs, is a
  reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates
  (the clean-context judge stays a reduction of rubber-stamping risk, not a mechanical guarantee —
  it runs the same model family, so model blind spots aren't independent).
