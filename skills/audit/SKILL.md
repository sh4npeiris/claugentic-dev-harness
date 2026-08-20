---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/claugentic-ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, depth-dialed) and tries to independently re-check every finding before it reaches the backlog.
---

# /claugentic-dev-harness:audit

> **Agent ids:** spawn every role named below by its **namespaced id** `claugentic-dev-harness:<role>` (e.g. `claugentic-dev-harness:lens-reviewer`); built-ins (`general-purpose`, `Explore`) stay bare.

Point this at a repo and it teaches you what the codebase is, then finds the work worth doing — a plain-English, prioritized backlog a non-engineer can act on.

## How this skill works

Three phases, cheap → expensive, run end-to-end in one pass — **Understand** (inline conversational pass → the overview + audit-plan; no fan-out) → **Audit** (the orchestrator invokes `engine/audit.js` with the audit-plan as args; the script runs FIND → PRUNE → VERIFY mechanically) → **Backlog** (the structured return rendered into the `harness-audit:backlog` fence of `docs/claugentic-ROADMAP.md`).

**The honest formula (verbatim):** *the skill invokes the script, and the script then runs the fan-out, the prune, and one independent re-check per surfaced finding mechanically.* Invoking the script is still the model's act — what's mechanical is everything **after** the invocation.

Findings are **model-asserted, then independently re-checked, and human-triaged**: a separate `finding-verifier` reads the cited code and **attempts to refute every surviving finding** before it reaches the backlog — an honest **reduction of false confidence, not a deterministic gate**. The script enforces *one verifier per finding*, so the model can't forget a verification, skip the prune, or silently truncate a run.

### How to use it (a periodic snapshot, not a treadmill)

- **Run it periodically** — after meaningful changes, **not obsessively**; **the backlog regenerates rather than accumulating** (a re-run replaces the fenced backlog with the *current* snapshot).
- **Tier 3 is optional** polish; **an empty Tier 1 + Tier 2 means the code is sound on the audited dimensions** — the signal to stop, not a prompt to manufacture work.
- **One thoroughness slider, three notches** (`quick` · `standard` · `thorough` — see *Set the dial*). **Every surfaced finding is independently re-checked at every level** — that floor never moves.
- **Be honest about which path ran:** all three notches run through `engine/audit.js`; the **only** fallback is *Prose-orchestrated fallback* below (**Workflow tool unavailable**), stated to the user and tagged "prose-orchestrated". Never claim script guarantees on a prose run.

---

## Phase 1 — Understand  *(LIVE, conversational)*

**Budget discipline:** read **manifests, configs, entry points, and READMEs — not every source file.** Build a map; don't review code.

### Output contract — what this phase produces

- **(A) User-facing overview** — plain-English, **text-only** (no diagram), for a non-engineer, into the ROADMAP overview fence. Sections, in order: *what it is · what it does · how it's built · how it's organized · safety-net signals (tests / CI / types) · confidence & caveats.* Be **honest that it's inferred from structure, not from running the app.**
- **(B) Audit-plan** — audit-internal, handed to Phase 2 as the script's args; also shown in-conversation as this phase's proof. Five fields: *exclude-set · prioritized directory order · monorepo / package boundaries · detected ecosystem + existing tooling · candidate standards modules.*

### The 8-step procedure

1. **Prefer existing signal.** If `docs/claugentic-ARCHITECTURE_TREE.md` exists and is current (DRY with `init`, which generates it), use it as the file-level map — do **not** re-walk the tree. Otherwise derive structure via a **bounded `Glob` walk** (top-level dirs + one or two levels in; never enumerate excluded trees). **Count-guard:** prefer a **source-of-truth** for any count (a manifest, `ARCHITECTURE_TREE.md`, a README) over counting raw files; if you can only infer, **say so and hedge** ("~N, inferred").

2. **Detect ecosystem & tooling — identify by manifest.** In the same pass detect **existing lint / format / type-check / test tooling** from its config and any CI workflows — this tells the audit **which gates already exist** so it doesn't propose redundant ones.

3. **Detect monorepo / package boundaries.** **If monorepo, enumerate the packages as separate audit units** — each gets its own slice of the directory order.

4. **Build the exclude-set.** Honor **`.gitignore` as the primary signal** (read it first), plus the usual dependency / build / generated / lockfile / large-binary trees. **Security (hard rule): never read or echo secrets** — `.env*` files, keys, credentials, certificates. Exclude them from the walk and **never surface their contents**; if you must mention one exists, name the file, not its contents.

5. **Identify entry points & surfaces**, and classify the app's **type** (CLI · web server · library · SPA · service · plugin/docs-and-tooling repo) and its external surfaces.

   **Application source present — the shared predicate (single source of truth).** As a named output of this detection, decide whether the repo *has application source*: **true iff there is ≥1 non-harness-managed source file of a detected ecosystem** (a recognized manifest present **and/or** ≥1 file matching the detected source layout), **excluding** harness-managed scaffolding (anything carrying the `claugentic-dev-harness@` managed stamp — e.g. the copied `scripts/claugentic-check_architecture_tree.py` — plus the seeded `docs/claugentic-standards/`, `claugentic-WORKFLOW.md`, `claugentic-PLAYBOOK.md`) and the exclude-set. A repo of **only** docs + config + harness scaffolding is **"no application source"** (e.g. a freshly-`init`'d empty repo). **`/claugentic-dev-harness:init` reuses this exact predicate** — do **not** author a second detector.

6. **Map dependencies (high-level).** Name only the **architecturally-significant** ones — enough to say *"an Express + Postgres API,"* not every transitive dep. These **pre-select the likely standards modules**: a DB driver pulls in `data-and-persistence`; an HTTP server pulls in `api-and-contracts` + `security`; a UI pulls in `product-ux`.

7. **Prioritized directory order.** Rank the *included* directories by likely risk / value, highest first: **entry points & core domain → data / persistence → API / routes → UI → config / scripts → tests last.** This is the `scopeDirs` order Phase 2 passes the script.

8. **Compose & emit — or stop if there's nothing to audit.** **Empty-repo guard (the Phase 1 → Phase 2 gate):** *Application source present* (step 5) **false** → **stop: do NOT write an overview and do NOT enter Phase 2.** Report, in conversation (never into a fence): *"Nothing to audit yet — I don't see any application code here, just documentation and config files. When you're ready, just tell me what you want to build and I'll run the workflow from your first feature; re-run `/claugentic-dev-harness:audit` once there's code."* **Otherwise**, write overview **(A)** into the ROADMAP fence (replacing only the fenced content) and present audit-plan **(B)** as this phase's proof and Phase 2's input.

### Where the overview goes — the ROADMAP fence  *(load-bearing convention)*

The overview goes into `docs/claugentic-ROADMAP.md`, between exact HTML-comment markers:

```
<!-- harness-audit:overview:start -->
…generated overview here…
<!-- harness-audit:overview:end -->
```

- On **re-run, replace only the content *inside* the fence.** Everything outside is **human-owned and must never be touched** — human-added roadmap items survive every regeneration.
- Fence **absent** → insert it once near the top of the ROADMAP (after the intro block), headed `## What this app is & does  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh)_`.
- Phase 3 writes the **backlog** into a **parallel `harness-audit:backlog` fence** under the same replace-only-inside rule.

### Set the dial (a pre-invoke step)

**Named level wins, else auto-size** from Phase 1's repo sizing: small and simple → `quick`; larger, many candidate modules, or a monorepo → `standard`. A **rough size/complexity judgment** — do not author a scoring formula. **`thorough` is named-only, never auto-picked.** **Always report the chosen level up front** so the user can steer — *"Auto-selected `quick` — small repo; say `standard` or `thorough` to override"*.

The dial is the **one lever**: it sets the `depth` each lens reads at (`focused` → `deep` → `exhaustive`). All relevant lenses run at every level — **depth, never lens-count, is the lever.** `thorough` *additionally* runs a cross-cutting blind-spot sweep (FIND) and an independent adversarial yagni-sentinel prune (PRUNE) — both **script stages**, joining the same dedup → prune → verify path.

---

## Phase 2 — Audit  *(LIVE — invoke the script)*

**You (the orchestrator) run this** — the script's fan-out spawns subagents, and subagents can't spawn subagents. With the Workflow tool available, **invoke the script** at any level; only when it's unavailable take the fallback.

### Invoke `engine/audit.js`

Call the Workflow tool with:

- **`scriptPath`** = `${CLAUDE_PLUGIN_ROOT}/engine/audit.js` (the version-stamped install path — read-from-install-path, never copied to an adopter). **When dogfooding *this* repo**, use the repo-local `./engine/audit.js` (the working tree *is* the plugin source).
- **`args`** mapped from the audit-plan (Phase 1):
  - `dial` — the chosen level (`quick` | `standard` | `thorough`).
  - `modules` — the candidate standards-module **names** (e.g. `["security","testing"]`; the script maps each to `docs/claugentic-standards/<name>.md`). **No clearly-relevant module?** fall back to the baseline lenses — `docs-traceability` + `maintainability-structure` — and **say so in the report**. Never audit nothing.
  - `scopeDirs` — the prioritized directory order (step 7).
  - `excludeSet` — the exclude-set (step 4); secrets are never passed or read.
  - `maxCellsPerRun` — the single deterministic cap (one integer ceiling on cells per run; sized to stay within your synthesis context — it bounds cost/time and enables `PARTIAL`/resume, not any single subagent's context).
  - `doneCells` — **on a resume run**, the existing backlog fence's status-block `done-cells` list; `[]` on a fresh run. The script never re-sweeps a done cell.
  - `deferredFindings` — prior-run findings carrying the `deferred` (`! not yet verified`) tag, fed straight to VERIFY for re-checking.
  - `priorItems` — **on a resume run**, the prior pass's *resolved* items (`verified` / `unconfirmed` tags) parsed from the fence; the script merges them in **unchanged** (verdicts persist, never re-verified; a finding the new sweep re-surfaces supersedes its prior copy). Without this channel a resumed render would silently drop confirmed findings — the fence rebuilds whole.
  - `builderFamily` — your (the orchestrator's) model family, for the same-model tag.

**Tell the user first, in plain English** (so a multi-minute pass isn't a silent stall): *"This can take several minutes on a larger repo — I'm reading the code through several quality lenses in parallel."*

What the script then runs mechanically:

- **FIND** — one `lens-reviewer` per module batch at `depthForDial(dial)`; **at `thorough`, also one in whole-scope mode** as the pseudo-cell `blindspot|(scope)` (FINDS only; its findings join the same path).
- **PRUNE** — coded dedup → a synthesis self-review agent → cut-list, with the `missing-test-baseline` item **never** pruned; **at `thorough`, also an adversarial `yagni-sentinel` sweep**, its cuts under the same never-prune-the-baseline protection.
- **VERIFY** — exactly one `finding-verifier` per surviving finding, **including blindspot-originated ones**: clean-context judge, clean-context input, never the finder's rationale.
- A batch (or the pseudo-cell) that errors after one retry sends its cells to `pending` → the run goes `PARTIAL`, never a silent skip; the cap likewise forces `PARTIAL` with exact `done`/`pending` lists for a deterministic resume (the pseudo-cell is capped/resumed like any cell).

### The structured return (what Phase 3 renders)

```
{ status, verificationIncomplete, level, depth, doneCells, pendingCells,
  items: [{ findingKey, modules, tier, tag, titlePlain, claimTechnical, locations,
            whyPlain, impactEffort, confidence, verification: {state, evidence, plainLine} }],
  refutedCount,
  verification: { verified, unconfirmed, deferred, refuted, carried, crossModel, sameModelTag },
  renderedBacklog }   // the COMPLETE fence body to write between the markers (Phase 3)
```

- `renderedBacklog` is the **complete inner fence body** (status line, legend, tiers, recommended starting point, run report, go-button), built by `renderBacklogFence` — the format's single source of truth. It carries a `{{DATE}}` placeholder and **no markers/no heading** (those stay SKILL-owned).
- `verification.state` per item is one of `verified` · `unconfirmed` · `deferred` — never a silent "checked". Refuted findings are **dropped** (their only trace is `refutedCount`); no timestamps anywhere (the orchestrator stamps the date at render).
- `verification.crossModel` is true **only** when every verifier that ran — **including those whose finding was refuted and dropped** — returned a confirming different-family self-report; otherwise `verification.sameModelTag` carries the verbatim tag.

### Prose-orchestrated fallback  *(Workflow tool unavailable — the ONLY trigger)*

State to the user that the Workflow tool is unavailable, run the **same FIND → PRUNE → VERIFY stages** (bulleted above, `thorough` additions included) **by hand**, and **tag the conversational run report "prose-orchestrated"** — never claim the script's mechanical guarantees on a prose run. This list carries only what changes when *you* run the stages; each agent's full contract is in its agent definition.

1. **Set the dial**, **load the audit-plan** (Phase 1), and **enumerate `(module | dir-or-package)` cells** — the deterministic unit; on resume, read the status block and continue from `pending`, never redoing a `done` cell.
2. **FIND — one `claugentic-dev-harness:lens-reviewer`** (audit-scope mode) per module batch, in parallel, passed its module + scoped dirs + exclude-set + the dial's `depth`. *(thorough: also one in whole-scope mode at `exhaustive`.)*
3. **Dedup + synthesize.** Key dedup on **issue-class**, not file·location alone; roll systemic cross-file duplicates into one "recurs in N files" item; carry each confidence label unchanged. **Citation-guard:** re-confirm every `file:line` against the actual file first.
4. **PRUNE — YAGNI right-size** (keep real impact; cut nice-to-haves; never manufacture a finding to fill a tier). *(thorough: also spawn one `claugentic-dev-harness:yagni-sentinel` — the independent skeptic — and apply its cut-list.)* **Never prune the Tier-1 "establish a test baseline" item.** **Criteria-as-lens-source (gap) mode runs the CONFORMANCE variant instead** — per the `synthesizer-gate` **Mode 3 gap variant**: no YAGNI right-sizing, cut only exact duplicates and criterion-less findings (every reason naming its criterion id), **never a promised-but-missing behaviour**, and **never add the test-baseline item** (it maps to no criterion).
5. **VERIFY — one `claugentic-dev-harness:finding-verifier` per surfaced finding**, all tiers, every level. Its independence is of **role and clean context, never of model**: it inherits the session's tier; the `RUNNING AS:` self-report + same-model tag disclose what resulted (`docs/claugentic-WORKFLOW.md` → *Principles*). Pass it **only** `{claim (plain + technical), file:line, source module, confidence label, exclude-set}` and the refute-first posture — never the finder's rationale, never a lens verifying its own finding. Verdicts, exactly as the script applies them: **Refuted** → drop (count it, don't persist) · **Verified** / **Unconfirmed** → keep with the matching tag · **budget-exhausted** → `deferred`, listed in `pending-cells`.
6. **Budget checkpoint** — one shared `max-cells-per-run` cap; on a hit (or cells `pending`), checkpoint `PARTIAL` with explicit `done`/`pending` lists and **tell the user to re-run. Never silently truncate.** Even on `PARTIAL`, the Tier-1 test-baseline item still emits for untested behavior-bearing code seen in the covered cells.
7. **Author the backlog** (Phase 3) and **report the dial level + coverage** + the run-report line.

---

## Phase 3 — Backlog  *(LIVE — write the rendered fence body)*

On the **script path**, Phase 3 is **file mechanics, not free-hand authoring**: the return carries `renderedBacklog`, the complete fence body. **Write that string between the markers and replace `{{DATE}}` with today's date.** **Format source of truth: `renderBacklogFence` in `engine/audit.js`.** (On the *Prose-orchestrated fallback* only, you author the body by hand following that same shape — see the renderer + its tests.)

### SELECT — the scope gate  *(before the fence write)*

**Run the finder-pipeline SELECT step before writing the fence** — the user picks which findings to keep, so the backlog never bloats with work they never wanted. Contract: `docs/claugentic-WORKFLOW.md` → **The finder pipeline** (SELECT mechanics + skip-vs-reject). The audit-specific wiring:

1. **Read `<!-- harness-audit:rejected-findings -->` first** (below) and **omit** any already-rejected candidate from what's presented.
2. **Present the remaining `result.items` as an editable `- [ ]` checklist** — one line per candidate in the rendered item form (titlePlain · tier · tag), a **transient conversational artifact** (never written into the fence). Offer a **"keep all"** shortcut.
3. **Write paths** *(the kept subset is what reaches the fence):*
   - **Keep all** → **"all" means all of what you PRESENTED, never the engine's original.** If step 1 omitted anything, the original `renderedBacklog` still contains it, so writing it directly **resurrects a finding the user dismissed** — silently undoing their decision and breaking the re-audit guarantee. **Nothing omitted** (or the run found nothing) → write the original directly, no `renderOnly` needed. **Anything omitted** → route through `renderOnly` with the presented set, exactly like a partial keep.
   - **Keep a non-empty subset (≥1 dropped)** → **re-invoke the Workflow tool** with `args.renderOnly = { ...result, items: <selected> }`; it re-renders over the selected subset while passing `lensCoverage`/`verification` through **full-scope** (the renderer stays the single source). Write the returned `renderedBacklog`.
   - **★ Keep NONE but the full run had Tier-1/2 findings** → **do NOT call `renderOnly`.** An empty `items` re-render emits the engine's terminal "sound" signal — a **false** claim (you found things; the user just chose not to act now). Handle it **conversationally** (*"found N this run — you kept none; re-run `/claugentic-dev-harness:audit` to see them again"*) and **skip/clear** the backlog write.
   - **Named precondition:** **`renderOnly` is never invoked with an empty `items` when the full run carried Tier-1/2 findings** (the false-terminal-signal guard — the honesty payload of the SELECT seam).

A **skip** (left unchecked) is **per-run** and may resurface; **explicit rejection** ("this finding is *wrong*") appends to the rejected-findings memory so it stays dropped — never infer rejection from a non-tick.

### The backlog fence  *(load-bearing convention)*

The backlog lives in `docs/claugentic-ROADMAP.md` between exact HTML-comment markers:

```
<!-- harness-audit:backlog:start -->
…the rendered fence body (renderedBacklog) here…
<!-- harness-audit:backlog:end -->
```

Same rules as the overview fence — **these govern the write and are NOT owned by the renderer** (human-added items and the `## Later` section survive every regeneration). Fence **absent** → insert it once (below the overview fence), headed
`## Backlog — the work worth doing  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh · run /claugentic-dev-harness:build to see it merged with the product backlog)_`.
The heading and the markers are **SKILL-owned** — the renderer emits neither.

### The rejected-findings memory  *(a dropped finding stays dropped)*

Record a dismissal in a **rejected-findings memory** that **mirrors product spec mode's `<!-- product-critic:rejected-proposals -->` convention exactly** (reused, not a new format): a **`<!-- harness-audit:rejected-findings -->`-fenced list**, **create-on-first-use**, **one terse line per dropped finding** (its plain title / finding-key), **never stamped**, **user-owned**. It lives in `docs/claugentic-ROADMAP.md` **OUTSIDE** the backlog fence, so a re-audit (which wipes that fence) **never wipes it**. **Before rendering, read this fence and skip re-surfacing any listed finding.** A **user override of the model's judgment, not a deletion of evidence** — the user can clear a line themselves; the harness never silently second-guesses a recorded dismissal.

### The three things to know  *(the renderer is the source of truth)*

1. **The status line is the resume contract.** Its `done-cells` / `pending-cells` are verbatim `cellKey` tokens (a re-run passes them back as `doneCells`). The Tier-1 `missing-test-baseline` item emits even on a `PARTIAL` run (the script protects its key from the prune). **`{{DATE}}` is the only thing you fill in.**
2. **Every item carries exactly one verification phrase** (`(checked against the code)` / `(could not confirm independently -- model's assertion)` / `(! not yet verified -- re-run to confirm)`) — a *reduction of false confidence*, never a guarantee; refuted findings are dropped (their only trace is the run-report count). Tiers 1+2 both empty → the recommended starting point is the **terminal "sound" signal**, the explicit stop. The renderer handles all of this; do not re-author it.
3. **The closing run-report you say to the user** (conversationally, outside the fence) frames the refuted count as a trust signal. **When `verification.crossModel` is false**, the fence's run-report line carries the verbatim same-model tag instead of the clean-context-judge parenthetical (never both) — and **on a prose-orchestrated run, also state that** in your report.

### Tag → discipline  *(mapping lives in WORKFLOW; enforcement is model-upheld, not automated)*

A backlog item's **tag selects the discipline** when it later runs through the pipeline — the mapping lives once in **`docs/claugentic-WORKFLOW.md`** (→ *Executing an audit backlog item — tag → discipline*). The one part to reflect when **authoring**: a **`refactor`** on untested behavior-bearing code is **characterization-tests-first — it cannot start until its Tier-1 "establish a test baseline" item is done.** That precondition is upheld by **the implementer stopping and asking**; a mechanical `PreToolUse` hook was **declined by design** — so **never imply the hook (or any automatic gate) exists or is coming.**

### After the write — report to the user

Report the **dial level + coverage** conversationally (which cells ran, `COMPLETE` or `PARTIAL`, any baseline fallback) — and **never call a run finished while `verificationIncomplete` is true**; say how many findings the budget left unchecked. Echo the rendered fence's run-report trust framing (dropped-finding count, the clean-context-judge / same-model-tag clause exactly as the fence carries it). **Do not list the specific refuted claims** and **do not persist them.**

**Resume note (one line, user-facing):** *"Interrupted? If the run reported `PARTIAL` — or any item still reads `! not yet verified` — just re-run `/claugentic-dev-harness:audit`, it picks up where it left off"* (`verificationIncomplete` is the second trigger — pass those items back as `deferredFindings`).

### OFFER-BUILD — the finder→build bridge  *(offered, never forced)*

Don't dead-end into a manual `/build`. After the backlog is written (post-SELECT), run the finder-pipeline **OFFER-BUILD** step (contract: `docs/claugentic-WORKFLOW.md` → **The finder pipeline**): ask via **AskUserQuestion** *"build these now, or leave them in the backlog?"* — **default = leave** (build is **offered, never forced**; forced auto-build is an explicit non-goal). **Build now** → enter the `build` procedure on the kept items. **Leave** → the backlog persists for a later `/claugentic-dev-harness:build`. (Skip the offer when SELECT kept nothing.)
