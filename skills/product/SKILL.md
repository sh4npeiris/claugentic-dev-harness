---
description: Build or refresh your product spec by conversation, then audit intent-vs-implementation into the backlog. Two modes — spec mode walks you through what the product is supposed to be (who it's for, the promise, each feature's flow and states) and writes docs/claugentic-PRODUCT_SPEC.md with machine-readable acceptance criteria; gap mode reads your code against that spec, criterion by criterion (static — it does not run the app), and writes the gaps into the same backlog the audit uses, every finding independently re-checked.
---

# /claugentic-dev-harness:product

> **Agent ids:** every role named below is one of this plugin's bundled agents — spawn it by its **namespaced id** `claugentic-dev-harness:<role>` (e.g. `claugentic-dev-harness:product-designer`); built-ins (`general-purpose`, `Explore`) stay bare.

Give the harness a **product memory** and a **product conscience**. Spec mode writes down what your
product is *supposed* to be; gap mode checks the code against it. **A top-level agent runs this** — gap
mode fans out subagents, and subagents can't spawn subagents.

## Mode selection — never guess

- A named mode wins: **"spec"** / *"rebuild the product spec"* / *"write the product spec"* → **spec
  mode**. **"gap"** / *"intent vs implementation"* / *"what's promised but missing"* → **gap mode**.
- **None named?** Ask one plain question — *"Do you want to (a) build/refresh the product spec, or (b)
  check the code against it for gaps?"* — and wait. Never assume.

The honesty register runs through **both** modes: writing the spec **checks nothing**; gap mode
**attempts / tags / reduces risk** — it never **proves**.

---

## Spec mode — build/refresh the product spec by conversation  *(LIVE, conversational)*

A plain-English conversation ending in `docs/claugentic-PRODUCT_SPEC.md`. **This phase genuinely needs
the user — it stays a conversation.**

1. **Locate the template.** Use the local managed copy `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` if
   present; otherwise read `${CLAUDE_PLUGIN_ROOT}/docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` (the
   version-stamped plugin install path) and tell the user *"re-run `/claugentic-dev-harness:init` to get
   your local copy."* The template is the section order and the FROZEN criteria schema.

2. **Gather intent — don't invent it.** Read, in this order: an existing
   `docs/claugentic-PRODUCT_SPEC.md` (the **refresh path** — walk the user through what changed, section
   by section, rather than rewriting from scratch); `docs/claugentic-PRODUCT.md`; the `README`; the user.
   The spec is the user's product truth — you surface and structure it, you do not decide it.

3. **Convene `claugentic-dev-harness:product-designer`** (Stage-1 Discuss register): surface the user,
   job-to-be-done, the key flows and their loading/empty/error states, and what "good" feels like. **The
   user owns every product decision; never invent scope** — a genuinely-new feature idea goes to the user
   as a question, not into the spec. The states bar is `docs/claugentic-standards/product-ux.md` →
   *Loading / empty / error states*; **point at it, don't restate it.** The agent is **read-only**: it
   returns the `docs/claugentic-PRODUCT.md` update; **you write it**.

4. **Draft per the template.** Fill **Who it's for · The job-to-be-done · The promise · Features** (per
   feature: flow · states · what-good-feels-like) **· Acceptance criteria**. Choose each criterion's
   `check` **with the user in plain English** where it's ambiguous — `e2e` (driven in a real browser),
   `api` (an HTTP call), or `manual` (a human check the QA run lists but never claims). Each `feature`
   value is the feature heading **verbatim**.

5. **The Product Excellence pass — elevate the draft (default-on every spec-mode run; skip only if the
   user asks).** Register: the pass **proposes — you decide**; it **never** guarantees the spec is
   excellent, and any benchmark/competitor claim made without a deep-research round is **model knowledge,
   tagged not-verified** (only a research round carries citations).

   1. **Convene `claugentic-dev-harness:product-designer` in its elevate mode** (a second subagent,
      allowed under the top-level-agent constraint). Pass it four things: the **elevate mode** · the
      **draft spec** · the **spec-conversation context** (what the user said that didn't survive
      structuring) · the **rejected-proposals memory** (the `<!-- product-critic:rejected-proposals -->`
      fenced list in `docs/claugentic-PRODUCT_SPEC.md`, when present — so it never re-pitches a decided
      idea). It **critiques by method** — second-session walkthrough · pre-mortem · kill-test ·
      tell-a-friend · the **mandatory premise-challenge** — and **points at**
      `docs/claugentic-standards/product-ux.md` for conformance rather than re-auditing states /
      flow-completeness (discover + the standard own those). It opens with **what's already strong** and
      is **licensed to return few or no proposals** — never filler.

   2. **Present TIERED, not as a flat per-item ballot** (that is the decision-fatigue failure mode):
      **Headline** (the 1–2 highest-leverage) — open as a conversation, not a yes/no vote · **Quick wins**
      (small, high-confidence) — **bulk-adoptable**, offer *"adopt all"* or cherry-pick · **Parked**
      (everything else) — **defer-by-default**, surfaced briefly, adopting nothing unless the user pulls
      it up.

   3. **Per proposal: adopt / adapt / reject / defer.** *Adapt* is a **counter-proposal conversation** —
      the user reshapes the idea and you fold the reshaped version. *Reject* and *defer* are recorded.

   4. **Fold adopted into the draft.** A proposal with a **suggested acceptance-criterion** folds into the
      **Features** prose AND the criteria block. A **non-criterial adoption** (qualitative — e.g. *"the
      empty state should invite the first action"*) lands in that feature's **what-good-feels-like** prose
      only. **State the honest scope: gap mode and the QA run check only the criteria — a
      what-good-feels-like line is durable product intent the checks won't verify.**

   5. **Record the decided proposals** in the **user-owned** spec (never stamped; step 7 preserves it).
      - **Rejected** → append to the `<!-- product-critic:rejected-proposals -->` fenced list in
        `docs/claugentic-PRODUCT_SPEC.md`, one terse line each, so the next elevate pass skips it. Create
        the fence if absent.
      - **Declined pass** → a one-line `<!-- product-critic:declined YYYY-MM-DD -->` note beside the
        fence, so nothing downstream implies the spec was elevated when it wasn't. **If no fence exists
        yet**, create the fence region at first use and write the marker beside it — they co-locate, so
        the next refresh finds both.

   6. **Refresh-path scoping.** On the refresh path (step 2), critique the **changed sections + a light
      whole-spec scan**, not a full re-critique. Tell the elevate pass the scope.

   7. **Deep-research on demand.** To ground a proposal in how the best products actually solve a job,
      invoke the **`deep-research` skill** (a session-available skill, **not** a repo file) scoped to
      *"how do the best products solve `<job>`, and where do they underserve"* → feed the **cited**
      findings to the elevate pass. **If `deep-research` is unavailable this session: say so plainly and
      fall back to critique-only**, benchmark claims tagged *model knowledge, not verified this run*.
      **Never claim research that didn't run.**

   8. **A deferred proposal → `docs/claugentic-ROADMAP.md`, the human-owned area.** Land it as a `feature`
      note **OUTSIDE** the `harness-audit:backlog` fence — that fence is regenerate-don't-accumulate (the
      next audit/gap run **wipes** anything inside it). **Honest pickup:** `build`'s item universe **is**
      the fence, so a deferred note is **not** picked up automatically — it enters when the **user names
      it** or a later **gap run regenerates it from the now-adopted spec**. Say so; don't imply it'll be
      built on its own.

6. **Re-validate the frozen criteria schema after folding — fail loud.** Every criterion must have
   **exactly** the six frozen keys `id, feature, flow, expect, states, check`; non-empty `flow` and
   `expect`; `states` ⊆ `{empty, loading, error}`; `check` ∈ `{e2e, api, manual}`; **ids unique**. On any
   violation, **stop and name the offending criterion id and the exact problem**, fix it, and re-validate
   — never write a malformed criteria block: the gap check and `qa.js` both consume it, and `qa.js`
   re-validates at its boundary and **refuses the whole run** rather than silently dropping a bad
   criterion. Any **adopted** proposal's suggested criterion goes through this same validation.

7. **Write `docs/claugentic-PRODUCT_SPEC.md`** — **user-owned: NO managed stamp** (`init` never refreshes
   it). Preserve any user content outside the template's own structure; never clobber sections the user
   added. Add its `docs/claugentic-ARCHITECTURE_TREE.md` entry.

**Register:** spec mode produced a *contract*. It **checked nothing** — checking is gap mode (static,
below) and the QA workflow (`qa.js`, runtime). Say so.

**Next:** run **gap mode**, or **`/claugentic-dev-harness:build`** to start working items.

---

## Gap mode — intent vs implementation → the backlog  *(LIVE — invoke the script)*

Read the **code** against the spec, criterion by criterion, into the **same backlog machinery the audit
uses**. **Static code reading — gap mode does NOT run the app; runtime checking is the QA workflow's job
(`qa.js`).**

1. **Precondition — a schema-valid spec must exist.** Require `docs/claugentic-PRODUCT_SPEC.md` with a
   parseable, schema-valid acceptance-criteria block. **If it's absent or invalid, stop honestly:** *"No
   product spec to audit against — run `/claugentic-dev-harness:product` spec mode first."* **Never audit
   against guessed intent.**

2. **Invoke `engine/audit.js` in criteria mode — an args mode, NOT a fork** (same FIND → PRUNE → VERIFY
   pipeline, **different lens source**; a second script would duplicate the dedup / budget / resume /
   verify machinery). Call the Workflow tool with:
   - **`scriptPath`** = `${CLAUDE_PLUGIN_ROOT}/engine/audit.js` (the version-stamped install path —
     read-from-install-path, never copied). **Dogfooding *this* repo:** the repo-local `./engine/audit.js`.
   - **`args`**:
     - `criteria` — the parsed acceptance-criteria array. The script enumerates **one cell per criterion**,
       keyed by its id; each lens call gets the criterion object + the instruction to locate the
       implementation via `docs/claugentic-ARCHITECTURE_TREE.md`, **read it statically**, and report
       missing / partial / diverging behavior per flow step, expectation, and required state, in the
       standard lens finding shape.
     - `excludeSet` — deps / build output / secrets (secrets never read).
     - `maxCellsPerRun` — the single deterministic cap (enables `PARTIAL`/resume, criterion ids as cells).
     - `doneCells` — on a resume run, the backlog status block's `done-cells` (criterion ids); `[]` fresh.
     - `deferredFindings` — prior-run findings carrying the `deferred` tag, re-checked this run.
     - `builderFamily` — your (the orchestrator's) model family, for the same-model tag.

   The criteria list (not a depth dial) bounds FIND — **lens depth is fixed at `deep`**. Findings join the
   same path — **dedup and verify unchanged, the PRUNE mode-branched**: coded dedup → synthesis prune in
   its **spec-conformance variant** (no YAGNI right-sizing, no test-baseline item; `synthesizer-gate`
   Mode 3 gap variant) → **exactly one `finding-verifier` per surviving finding** (clean-context judge +
   same-model tagging owned by the script, per the shared `MODELS` contract); the shared budget cap +
   status-block resume apply with criterion ids as the cells.

3. **Write the backlog into the product's OWN `harness-product:backlog` fence** —
   `<!-- harness-product:backlog:start -->` / `<!-- harness-product:backlog:end -->`, **separate from the
   engineering `harness-audit:backlog` fence** the `audit` skill owns. It carries a **per-criterion `met` /
   `partial` / `missing` / `not-checked` line**, so a criterion that was checked and IS delivered is
   distinguishable from one the run never reached. **Each fence regenerates independently — a gap run
   never touches the engineering one, and an engineering audit never touches this one.** The renderer is
   **reused, not forked** — `renderedBacklog` is the same `renderBacklogFence` body the engineering path
   uses; the split is only **which marker this skill writes to**. Write rules, same as the engineering
   fence: **replace only inside the markers** on a re-run (regenerate-don't-accumulate — state this before
   writing); everything outside is **human-owned and never touched**. If the product fence is **absent,
   insert it once** (below the engineering region), headed with —
   `## Product backlog — gaps vs your spec  _(generated by /claugentic-dev-harness:product gap · do not edit — re-run to refresh · run /claugentic-dev-harness:build to see it merged with the engineering backlog)_`.

   **SELECT before the write — the scope gate.** Run the finder-pipeline **SELECT** step (contract:
   `docs/claugentic-WORKFLOW.md` → **The finder pipeline** — mechanics + skip-vs-reject live there):
   **read `<!-- product-critic:rejected-proposals -->` first** and omit already-rejected candidates;
   present the remaining `result.items` as an editable `- [ ]` checklist (transient; "keep all" shortcut).
   Then:
   - **Keep all / nothing found** → write the engine's original `renderedBacklog` — **but only when the
     rejected-proposals read omitted NOTHING.** "All" means all of what you presented; the original still
     carries any omitted candidate, so writing it directly resurrects a rejected proposal. If anything was
     omitted, route through `renderOnly` with the presented set.
   - **Keep a non-empty subset** → **re-invoke the Workflow tool** with `args.renderOnly = { ...result,
     items: <selected> }` — passing the **full `result` (incl. its `verification`) through unchanged** so
     the fence's run-report **and its `criterionCoverage`** stay **full-scope**: a SELECT-narrowed item
     list must never narrow the per-criterion report (the same full-scope-coverage invariant the
     engineering audit holds). Write the returned `renderedBacklog`.
   - **★ Keep none but the run found gaps** → do **NOT** call `renderOnly` (it would emit the false
     "sound" terminal signal); handle conversationally + skip/clear the write. **Precondition:
     `renderOnly` is never invoked with an empty `items` when the full run carried findings.**

   The script returns `renderedBacklog` (the complete fence body); write it between the product markers and
   replace `{{DATE}}` with today's date. The status block carries `level: gap` and
   `done-cells`/`pending-cells` = criterion ids; same legend, same five tags (gap items are typically
   **`feature`** = promised-but-missing or **`bug`** = diverges-from-spec), same per-item verification tags
   and run-report line (with cross-/same-model tagging).

4. **The honest-scope line — ALWAYS, in the report:** *"This read the code against the spec — it did not
   run the app; runtime checking is the QA workflow."*

5. **Prose-orchestrated fallback** *(Workflow tool unavailable — the ONLY fallback trigger).* Say so to the
   user, then run the **audit SKILL's prose pipeline** (the `claugentic-dev-harness:audit` skill →
   *Prose-orchestrated fallback*) with the **criteria as the lens source** — one cell per criterion, the
   same dedup → prune → one-verifier-per-finding path, PRUNE in its **conformance variant**
   (`synthesizer-gate` Mode 3 gap variant: no YAGNI, cut only duplicates and criterion-less findings,
   **never** a promised-but-missing behaviour, and **never** add the test-baseline item) — and **tag the
   run "prose-orchestrated."** Never claim the script's mechanical guarantees on a prose run.

6. **OFFER-BUILD — the finder→build bridge** *(after the write, post-SELECT — offered, never forced)*. Run
   the finder-pipeline **OFFER-BUILD** step (contract: `docs/claugentic-WORKFLOW.md` → **The finder
   pipeline** → *OFFER-BUILD*): ask via **AskUserQuestion** *"build these now, or leave them in the
   backlog?"* — **default = leave** (forced auto-build is an explicit non-goal). **Build now** → enter the
   `build` procedure on the kept items. **Leave** → the backlog persists for a later
   `/claugentic-dev-harness:build`. (Skip the offer when SELECT kept nothing.)

**Interrupted?** If the run reported `PARTIAL`, just re-run — it picks up where it left off.
