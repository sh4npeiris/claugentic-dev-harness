---
description: Build or refresh your product spec by conversation, then audit intent-vs-implementation into the backlog. Two modes — spec mode walks you through what the product is supposed to be (who it's for, the promise, each feature's flow and states) and writes docs/PRODUCT_SPEC.md with machine-readable acceptance criteria; gap mode reads your code against that spec, criterion by criterion (static — it does not run the app), and writes the gaps into the same backlog the audit uses, every finding independently re-checked.
---

# /claugentic-dev-harness:product

Give the harness a **product memory** and a **product conscience**. Spec mode writes down what
your product is *supposed* to be; gap mode checks the code against it. **A top-level agent runs
this** — gap mode fans out subagents (and subagents can't spawn subagents), so the orchestrator
invokes it.

## Mode selection — never guess

- A named mode wins: **"spec"** / *"rebuild the product spec"* / *"write the product spec"* →
  **spec mode**. **"gap"** / *"intent vs implementation"* / *"what's promised but missing"* →
  **gap mode**.
- **None named?** Ask one plain question — *"Do you want to (a) build/refresh the product spec, or
  (b) check the code against it for gaps?"* — and wait. Never assume.

The honesty register runs through **both** modes: writing the spec **checks nothing**; gap mode
**attempts / tags / reduces risk** — it never **proves**.

---

## Spec mode — build/refresh the product spec by conversation  *(LIVE, conversational)*

A plain-English conversation that ends in `docs/PRODUCT_SPEC.md`: who it's for, the job, the
promise, each feature's flow and states, and a machine-readable acceptance-criteria block. **This
phase genuinely needs the user — it stays a conversation.**

1. **Locate the template.** Use the local managed copy `docs/PRODUCT_SPEC_TEMPLATE.md` if present;
   otherwise read `${CLAUDE_PLUGIN_ROOT}/docs/PRODUCT_SPEC_TEMPLATE.md` (the version-stamped plugin
   install path) and tell the user *"re-run `/claugentic-dev-harness:init` to get your local
   copy."* The template is the section order and the FROZEN criteria schema.

2. **Gather intent — don't invent it.** Read, in this order: an existing `docs/PRODUCT_SPEC.md`
   (this is the **refresh path** — walk the user through what changed, section by section, rather
   than rewriting from scratch); `docs/PRODUCT.md` (durable product/UX context, if kept); the
   `README`; and the user. The spec is the user's product truth — you surface and structure it,
   you do not decide it.

3. **Convene `product-designer`** (Stage-1 Discuss register — per `.claude/agents/product-designer.md`,
   no new agents): plain-English opener; surface the user, job-to-be-done, the key flows and their
   loading/empty/error states, and what "good" feels like; **the user owns every product decision;
   never invent scope** (a genuinely-new feature idea goes to the user as a question, not into the
   spec). The states bar is the standard — **point at** `docs/standards/product-ux.md` →
   *Loading / empty / error states*, don't restate it.

4. **Draft per the template.** Fill **Who it's for · The job-to-be-done · The promise · Features**
   (per feature: flow · states · what-good-feels-like) **· Acceptance criteria**. For each
   criterion choose its `check` **with the user in plain English** where it's ambiguous — `e2e`
   (driven in a real browser), `api` (an HTTP call), or `manual` (a human check the QA run lists
   but never claims). Each `feature` value is the feature heading **verbatim**.

5. **Validate at the boundary BEFORE writing — fail loud.** Every criterion must have **exactly**
   the six frozen keys `id, feature, flow, expect, states, check`; non-empty `flow` and `expect`;
   `states` ⊆ `{empty, loading, error}`; `check` ∈ `{e2e, api, manual}`; **ids unique**. On any
   violation, **stop and name the offending criterion id and the exact problem**, fix it, and
   re-validate — never write a malformed criteria block (the gap check and `qa.js` both consume it,
   and a pytest pins the frozen field names).

6. **Write `docs/PRODUCT_SPEC.md`** — **user-owned: NO managed stamp** (`init` never refreshes it).
   Preserve any user content outside the template's own structure; never clobber sections the user
   added. Add its `docs/ARCHITECTURE_TREE.md` entry.

**Register:** spec mode produced a *contract*. It **checked nothing** — checking is gap mode
(static, below) and the QA workflow (`qa.js`, runtime). Say so.

---

## Gap mode — intent vs implementation → the backlog  *(LIVE — invoke the script)*

Read the **code** against the spec, criterion by criterion, and write the gaps into the **same
backlog fence the audit uses**. **Static code reading — gap mode does NOT run the app. Runtime
checking is the QA workflow's job (`qa.js`); say so.**

1. **Precondition — a schema-valid spec must exist.** Require `docs/PRODUCT_SPEC.md` with a
   parseable, schema-valid acceptance-criteria block. **If it's absent or invalid, stop honestly:**
   *"No product spec to audit against — run `/claugentic-dev-harness:product` spec mode first."*
   **Never audit against guessed intent.**

2. **Invoke `workflows/audit.js` in criteria mode — an args mode, NOT a fork.** Gap is the same
   FIND → PRUNE → VERIFY pipeline with a **different lens source**; a second script would duplicate
   the dedup / budget / resume / verify machinery (DRY). Call the Workflow tool with:
   - **`scriptPath`** = `${CLAUDE_PLUGIN_ROOT}/workflows/audit.js` (the version-stamped install
     path — read-from-install-path, never copied). **Dogfooding *this* repo:** the repo-local
     `./workflows/audit.js`.
   - **`args`**:
     - `criteria` — the parsed acceptance-criteria array (the script enumerates **one cell per
       criterion**, keyed by its id; each lens call gets the criterion object + the instruction to
       locate the implementation via `docs/ARCHITECTURE_TREE.md`, **read it statically**, and report
       missing / partial / diverging behavior per flow step, expectation, and required state, in the
       standard lens finding shape).
     - `excludeSet` — deps / build output / secrets (secrets never read).
     - `maxCellsPerRun` — the single deterministic cap (enables `PARTIAL`/resume with criterion ids
       as the cells).
     - `doneCells` — on a resume run, the backlog status block's `done-cells` (criterion ids); `[]`
       fresh.
     - `deferredFindings` — prior-run findings carrying the `deferred` tag, re-checked this run.
     - `builderFamily` — your (the orchestrator's) model family, for the same-model tag.

   The criteria list (not a depth dial) bounds FIND — **lens depth is fixed at `deep`**. Findings
   join the **unchanged** path: coded dedup → synthesis prune → **exactly one `finding-verifier`
   per surviving finding** (cross-model judge + same-model tagging owned by the script, per the
   shared `MODELS` contract); the shared budget cap + status-block resume apply with criterion ids
   as the cells.

3. **Write the backlog into the EXISTING `harness-audit:backlog` fence** — **no new fences.** Same
   `docs/ROADMAP.md` markers, same **replace-only-inside** rule (regenerate-don't-accumulate: a gap
   run **replaces** the current backlog snapshot, and a later `/claugentic-dev-harness:audit`
   regenerates the engineering view — state this before writing). The script returns
   `renderedBacklog` (the complete fence body); write it between the markers and replace `{{DATE}}`
   with today's date. The status block carries `level: gap` and `done-cells`/`pending-cells` =
   criterion ids; the same 2-line legend, the same five tags (gap items are typically **`feature`**
   = promised-but-missing or **`bug`** = diverges-from-spec), the same per-item verification tags
   and the run-report line (with cross-/same-model tagging).

4. **The honest-scope line — ALWAYS, in the report:** *"This read the code against the spec — it
   did not run the app; runtime checking is the QA workflow."*

5. **Prose-orchestrated fallback** *(Workflow tool unavailable — the ONLY fallback trigger).* State
   to the user that the Workflow tool is unavailable, run the **audit SKILL's prose pipeline**
   (`skills/audit/SKILL.md` → *Prose-orchestrated fallback*) with the **criteria as the lens
   source** — one cell per criterion, the same dedup → prune → one-verifier-per-finding path — and
   **tag the run "prose-orchestrated."** Never claim the script's mechanical guarantees on a prose
   run.

**Register throughout:** gap mode **attempts / tags / reduces the risk** the product diverged from
intent. It is **never proof** the product is good — and it **reads code, it does not run the app.**
