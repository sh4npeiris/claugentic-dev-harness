---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/claugentic-ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, depth-dialed) and tries to independently re-check every finding before it reaches the backlog.
---

# /claugentic-dev-harness:audit

> **Agent ids:** every role named below is one of this plugin's bundled agents — when you spawn one, use its **namespaced id** `claugentic-dev-harness:<role>` (e.g. `claugentic-dev-harness:lens-reviewer`); built-ins (`general-purpose`, `Explore`) stay bare.

Point this at a repo and it teaches you what the codebase is, then finds the work
worth doing — written back as a plain-English, prioritized backlog a non-engineer
can act on.

## How this skill works

Three phases, cheap → expensive, run end-to-end in one pass:

1. **Understand** *(LIVE, conversational)* — one cheap inline pass over manifests + structure to
   produce a plain-English **"what your app is & does"** overview and an **audit-plan** (what to
   look at, in what order, with what excluded). No fan-out. *(This phase genuinely needs you —
   it stays a conversation.)*
2. **Audit** *(LIVE)* — **the orchestrator invokes `engine/audit.js`** (the Workflow tool) with
   the audit-plan as args; the script runs the FIND → PRUNE → VERIFY pipeline mechanically: a
   `lens-reviewer` fan-out per `(module × dir)` cell at the dial's **depth**, coded dedup, a
   synthesis self-review prune, and **exactly one `finding-verifier` per surviving finding**
   (cross-model judge), with a deterministic budget cap + resume.
3. **Backlog** *(LIVE)* — the script's **structured return** is rendered into the
   `harness-audit:backlog` fence in `docs/claugentic-ROADMAP.md` as a **tiered, tagged, plain-English**
   backlog, ending with a recommended starting point.

**The honest formula (verbatim):** *the skill invokes the script, and the script then runs the
fan-out, the prune, and one independent re-check per surfaced finding mechanically.* Invoking the
script is still the model's act — what's mechanical is everything **after** the invocation.

Findings are **model-asserted, then independently re-checked, and human-triaged**: after the
prune, a separate `finding-verifier` reads the cited code and **attempts to refute every surviving
finding** before it reaches the backlog — an honest **reduction of false confidence**, not a
deterministic gate. The script enforces *one verifier per finding*; the model can no longer forget
a verification, skip the prune, or silently truncate a run.

### How to use it (a periodic snapshot, not a treadmill)

- **Run it periodically** — after meaningful changes, **not obsessively.** It's a snapshot
  of where the codebase stands, not a chore to keep chasing to zero.
- **The backlog regenerates, it doesn't accumulate.** A re-run replaces the fenced backlog
  with the *current* snapshot — today's picture, not an ever-growing pile.
- **Tier 3 is optional** polish; **an empty Tier 1 + Tier 2 means the code is sound** on the
  audited dimensions — that's the signal to stop, not a prompt to manufacture more work.
- **One thoroughness slider, three notches** — `quick` · `standard` · `thorough`. The **dial
  auto-sizes** to the repo (small → `quick`, larger → `standard`) and is reported up front;
  **name a level to override.** `thorough` is **named-only** — never auto-picked. The slider sets
  **how deep each lens digs** (`focused` → `deep` → `exhaustive`) and, at the top notch, adds two
  fresh-angle adversarial passes. Whatever the level, **every surfaced finding is independently
  re-checked** — that floor never moves.

> **Which path runs (be honest about it):** **all three notches run through `engine/audit.js`**
> (the script) — `thorough` adds a whole-scope blind-spot sweep (FIND) and an adversarial
> yagni-sentinel prune (PRUNE) as script stages. The **only** fallback is the *Prose-orchestrated
> fallback* below: if the **Workflow tool is unavailable** in this session, *any* level falls back
> to the prose path, stated to you and tagged "prose-orchestrated". Never claim script guarantees on
> a prose run.

---

## Phase 1 — Understand  *(LIVE, conversational)*

A single cheap, inline pass. **Budget discipline:** read **manifests, configs, entry points, and
READMEs — not every source file.** You are building a map, not reviewing code.

### Output contract — what this phase produces

- **(A) User-facing overview** — plain-English, **text-only** (no diagram), written into the
  ROADMAP overview fence (see *Where the overview goes* below). For a non-engineer. Sections, in
  order: *what it is · what it does · how it's built · how it's organized · safety-net signals
  (tests / CI / types) · confidence & caveats.* Be **honest that it's inferred from structure, not
  from running the app.**
- **(B) Audit-plan** — audit-internal, handed to Phase 2 as the script's args; also shown to the
  user in-conversation as the proof this phase ran. Five fields: *exclude-set · prioritized
  directory order · monorepo / package boundaries · detected ecosystem + existing tooling ·
  candidate standards modules.*

### The 8-step procedure

Run these in order. Each step feeds the output contract above.

1. **Prefer existing signal.** If `docs/claugentic-ARCHITECTURE_TREE.md` exists and is current (DRY with the
   `init` skill, which generates it), use it as the file-level map — do **not** re-walk the tree.
   Otherwise derive structure via a **bounded `Glob` walk** (top-level dirs + one or two levels in;
   do not enumerate excluded trees). Either way, read only manifests / configs / entry points /
   READMEs from here on. **Count-guard:** when you state a count, **prefer a source-of-truth** — a
   manifest, an index like `ARCHITECTURE_TREE.md`, or a README — over counting raw files yourself;
   if you can only infer, **say so and hedge** ("~N, inferred") rather than asserting a precise
   figure.

2. **Detect ecosystem & tooling.** Scan the root and significant subdirs for **manifests** to
   identify language(s), framework(s), and package manager — the general rule is *"identify by
   manifest"*: `package.json` (Node/JS/TS), `pyproject.toml` / `requirements.txt` / `setup.py`
   (Python), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml` / `build.gradle` (JVM), `Gemfile`
   (Ruby), `composer.json` (PHP), `*.csproj` / `*.sln` (.NET), … . In the same pass, detect
   **existing lint / format / type-check / test tooling** from its config and any CI workflows
   (`.github/workflows`, `.gitlab-ci.yml`) — this tells the audit **which gates already exist** so
   it doesn't propose redundant ones.

3. **Detect monorepo / package boundaries.** Look for `workspaces` (in `package.json`),
   `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, multiple manifests in different
   dirs, or a `packages/` · `apps/` layout. **If monorepo, enumerate the packages as separate
   audit units** (each gets its own slice of the directory order).

4. **Build the exclude-set.** Honor **`.gitignore` as the primary signal** (read it first),
   augmented by well-known dirs the audit must never spend budget on:
   - VCS: `.git` · dependencies: `node_modules`, `vendor`, `.venv` / `venv`, `__pycache__`,
     `target`, `Pods` · build / output: `dist`, `build`, `.next`, `out`, `coverage`, `.turbo` ·
     generated: `*.generated.*`, `*.min.js`, codegen output · lockfiles and large binary / media
     assets.
   - **Security (hard rule):** **never read or echo secrets** — `.env*` files, keys, credentials,
     certificates. Exclude them from the walk and **never surface their contents** in the overview
     or the audit-plan. If you must mention one exists, name the file, not its contents.

5. **Identify entry points & surfaces.** From the manifests and conventions, find how the app is
   entered (`main` / `bin` / `scripts`, `[project.scripts]` / `__main__.py`, `func main`, framework
   conventions, `Dockerfile` `CMD` / `ENTRYPOINT`). Use these to classify the app's **type** —
   CLI · web server · library · SPA · service · (or, as here, a plugin / docs-and-tooling repo) —
   and its external surfaces.

   **Application source present — the shared predicate (single source of truth).** As a named
   output of this detection, decide whether the repo *has application source*: **true iff there is
   ≥1 non-harness-managed source file of a detected ecosystem** (a recognized manifest present
   **and/or** ≥1 file matching the detected source layout), **excluding** harness-managed
   scaffolding (anything carrying the `claugentic-dev-harness@` managed stamp — e.g. the copied
   `scripts/claugentic-check_architecture_tree.py` — plus the seeded `docs/claugentic-standards/`, `claugentic-WORKFLOW.md`,
   `claugentic-PLAYBOOK.md`) and the exclude-set (deps / build / generated). A repo of **only** docs + config
   + harness scaffolding is **"no application source"** (e.g. a freshly-`init`'d empty repo).
   **`/claugentic-dev-harness:init` reuses this exact predicate** — do **not** author a second
   detector.

6. **Map dependencies (high-level).** Name only the **architecturally-significant** dependencies
   (web frameworks, DB drivers, HTTP / auth libraries, queues) — enough to say *"an Express +
   Postgres API,"* not every transitive dep. These **pre-select the likely standards modules**: a
   DB driver pulls in `data-and-persistence`; an HTTP server pulls in `api-and-contracts` +
   `security`; a UI pulls in `product-ux`.

7. **Prioritized directory order.** Rank the *included* directories by likely risk / value for the
   audit's budget spend — highest first: **entry points & core domain → data / persistence → API /
   routes → UI → config / scripts → tests last.** This is the `scopeDirs` order Phase 2 passes the
   script; spend lands where bugs and standards violations cluster.

8. **Compose & emit — or stop if there's nothing to audit.** **Empty-repo guard (the Phase 1 →
   Phase 2 gate):** if *Application source present* (step 5) is **false** — only docs / config /
   harness scaffolding, or a brand-new empty repo — **stop here: do NOT write an overview and do
   NOT enter Phase 2.** Report, in conversation (never into a fence): *"Nothing to audit yet — I
   don't see any application code here, just documentation and config files. When you're ready,
   just tell me what you want to build and I'll run the workflow from your first feature; re-run
   `/claugentic-dev-harness:audit` once there's code."* **Otherwise**, write the plain-English
   overview **(A)** into the ROADMAP fence (replacing only the fenced content — see below), and
   present the audit-plan **(B)** to the user as this phase's proof and Phase 2's input.

### Where the overview goes — the ROADMAP fence  *(load-bearing convention)*

Phase 1 writes the overview into `docs/claugentic-ROADMAP.md`, between exact HTML-comment markers:

```
<!-- harness-audit:overview:start -->
…generated overview here…
<!-- harness-audit:overview:end -->
```

Rules:
- On **re-run, replace only the content *inside* the fence.** Everything outside it is
  **human-owned and must never be touched** — human-added roadmap items survive every regeneration.
- If the fence is **absent**, insert it once near the top of the ROADMAP (after the intro block),
  headed
  `## What this app is & does  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh)_`.
- Phase 3 writes the **backlog** into a **parallel `harness-audit:backlog` fence**, governed by the
  same replace-only-inside rule.

### Set the dial (a pre-invoke step)

One thoroughness slider; **named level wins, else auto-size** from Phase 1's repo sizing (structure
/ candidate-module count / monorepo signal): a small, simple repo → `quick`; a larger repo, many
candidate modules, or a monorepo → `standard`. Keep this a **rough size/complexity judgment** — do
not author a scoring formula. **`thorough` is never auto-picked — named-only.** **Always report the
chosen level up front** so the user can steer — e.g. *"Auto-selected `quick` — small repo; say
`standard` or `thorough` to override"* (or *"Using `thorough` as you asked"*).

The dial is the **one lever**: it sets the `depth` each lens reads at (`focused` → `deep` →
`exhaustive`). All relevant lenses run at every level — depth, never lens-count, is the lever.
`thorough` *additionally* runs a cross-cutting blind-spot sweep (FIND) and an independent
adversarial yagni-sentinel prune (PRUNE) — both are **script stages** the run executes mechanically,
joining the same dedup → prune → verify path as any finding.

---

## Phase 2 — Audit  *(LIVE — invoke the script)*

**You (the orchestrator) run this** — the script's fan-out spawns subagents, and subagents can't
spawn subagents. For any level (`quick`/`standard`/`thorough`) with the Workflow tool available, **invoke the
script**; only when the Workflow tool is unavailable take the *Prose-orchestrated fallback*.

### Invoke `engine/audit.js`

Call the Workflow tool with:

- **`scriptPath`** = `${CLAUDE_PLUGIN_ROOT}/engine/audit.js` (the version-stamped plugin install
  path — read-from-install-path, never copied to an adopter). **When dogfooding *this* repo**, use
  the repo-local `./engine/audit.js` (the working tree *is* the plugin source).
- **`args`** mapped from the audit-plan (Phase 1):
  - `dial` — the chosen level (`quick` | `standard` | `thorough`; at `thorough` the script adds the
    whole-scope blind-spot sweep and the adversarial yagni-sentinel prune).
  - `modules` — the candidate standards-module **names** (e.g. `["security","testing"]`; the script
    maps each to `docs/claugentic-standards/<name>.md`). **No clearly-relevant module?** fall back to the
    baseline lenses — `docs-traceability` + `maintainability-structure` — and **say so in the
    report**. Never audit nothing.
  - `scopeDirs` — the prioritized directory order (step 7).
  - `excludeSet` — the exclude-set (step 4); secrets are never passed or read.
  - `maxCellsPerRun` — the single deterministic cap (one integer ceiling on cells per run; sized to
    stay within your synthesis context for the repo — it bounds cost/time and enables `PARTIAL`/
    resume, not any single subagent's context).
  - `doneCells` — **on a resume run**, parse the existing backlog fence's status block (Phase 3)
    and pass its `done-cells` list; `[]` on a fresh run. The script never re-sweeps a done cell.
  - `deferredFindings` — prior-run findings carrying the `deferred` (`⚠ not yet verified`) tag, fed
    straight to VERIFY for re-checking.
  - `priorItems` — **on a resume run**, the prior pass's *resolved* items (`verified` /
    `unconfirmed` tags) parsed from the fence; the script merges them into the regenerated
    fence **unchanged** (their verdicts persist — they are never re-verified; a finding the
    new sweep re-surfaces supersedes its prior copy). Without this channel a resumed render
    would silently drop confirmed findings (the regenerate-don't-accumulate fence rebuilds
    whole).
  - `builderFamily` — your (the orchestrator's) model family, for the same-model tag.

**Tell the user first, in plain English** (so a multi-minute pass isn't a silent stall): *"This can
take several minutes on a larger repo — I'm reading the code through several quality lenses in
parallel."* What the script then runs mechanically: **FIND** (one `lens-reviewer` per module batch
at `depthForDial(dial)`; **at `thorough`, also one `blindspot-reviewer` over the whole scope** as a
pseudo-cell — it FINDS only, its findings join the same path), **PRUNE** (coded dedup → a synthesis
self-review agent → cut-list, with the `missing-test-baseline` item **never** pruned; **at
`thorough`, also an adversarial `yagni-sentinel` sweep** over the consolidated set, its cuts applied
with the same never-prune-the-baseline protection), **VERIFY** (exactly one `finding-verifier` per
surviving finding — **including blindspot-originated ones** — cross-model judge-pinned, clean-context
input — never the finder's rationale). A lens batch (or the blind-spot pseudo-cell) that errors
after one retry sends its cells to `pending` (the run goes `PARTIAL` — never a silent skip); the cap
forces `PARTIAL` with exact `done`/`pending` cell lists for a deterministic resume (the blind-spot
pseudo-cell `blindspot×(scope)` is capped/resumed like any cell).

### The structured return (what Phase 3 renders)

```
{ status, level, depth, doneCells, pendingCells,
  items: [{ findingKey, modules, tier, tag, titlePlain, claimTechnical, locations,
            whyPlain, impactEffort, confidence, verification: {state, evidence, plainLine} }],
  refutedCount,
  verification: { verified, unconfirmed, deferred, refuted, crossModel, sameModelTag },
  renderedBacklog }   // the COMPLETE fence body to write between the markers (Phase 3)
```

- `renderedBacklog` is the **complete inner fence body** — status line, legend, tiers, recommended
  starting point, run report, go-button — built by the script's `renderBacklogFence` helper (the
  fence format's single source of truth). It carries a `{{DATE}}` placeholder and **no markers/no
  heading** (those stay SKILL-owned). Phase 3 is now: write this string between the markers and
  replace `{{DATE}}` with today's date.
- `verification.state` per item is one of `verified` · `unconfirmed` · `deferred` — never a silent
  "checked". Refuted findings are **dropped** (their only trace is `refutedCount`); no timestamps
  anywhere (the orchestrator stamps the date when it renders).
- `verification.crossModel` is true **only** when every verifier returned a confirming
  different-family self-report; otherwise `verification.sameModelTag` carries the verbatim tag.

### Prose-orchestrated fallback  *(Workflow tool unavailable — the ONLY fallback trigger)*

State to the user that the Workflow tool is unavailable, run the legacy 9-step pipeline below by
hand (it covers all three levels — the `thorough`-only sub-steps fire at `thorough`), and **tag
the conversational run report "prose-orchestrated"** — never claim the script's mechanical
guarantees on a prose run. The pipeline (each agent's full contract is in its `.claude/agents/`
file — read it there):

1. **Set the dial** (above) — depth per lens; at `thorough`, also the blind-spot sweep + the
   adversarial prune.
2. **Load the audit-plan** from Phase 1.
3. **Enumerate `(module × dir-or-package)` cells** — the deterministic unit; on resume, read the
   status block and continue from `pending`, never redoing a `done` cell.
4. **Fan out lenses — one look per cell.** One `claugentic-dev-harness:lens-reviewer` (audit-scope mode) per module batch,
   in parallel, passed its module + scoped dirs + exclude-set + the dial's `depth`
   (`.claude/agents/lens-reviewer.md`). *(thorough only:* also one `claugentic-dev-harness:blindspot-reviewer` over the
   whole scope at `exhaustive` — it FINDS only; its findings join the same dedup → prune → verify
   path. `.claude/agents/blindspot-reviewer.md`.)
5. **Dedup + synthesize.** Key dedup on **issue-class**, not file·location alone; roll up systemic
   cross-file duplicates into one "recurs in N files" item; carry each finding's confidence label
   unchanged. **Citation-guard:** re-confirm every `file:line` against the actual file first.
6. **PRUNE — YAGNI right-size** the consolidated set (keep real impact; cut nice-to-haves; never
   manufacture a finding to fill a tier). *(thorough only:* additionally spawn one `claugentic-dev-harness:yagni-sentinel`
   over the set — the independent skeptic — and apply its cut-list. `.claude/agents/yagni-sentinel.md`.)
   **Exception: never prune the Tier-1 "establish a test baseline" item.**
7. **VERIFY — re-check every surfaced finding** (all tiers, every level). Spawn one
   `claugentic-dev-harness:finding-verifier` per finding **with the `fable` model override** (the cross-model judge — the
   mechanism, the self-report comparison, the verbatim same-model tag, and the on-error respawn+tag
   live in `docs/claugentic-WORKFLOW.md` → Principles → *"Convene the panel's judge roles with the `fable`
   model override"* — read it there). Pass each verifier **only** `{claim (plain + technical),
   file:line, source module, confidence label, exclude-set}` and the refute-first posture — never
   the finder's rationale, never a lens verifying its own finding (`.claude/agents/finding-verifier.md`).
   Apply verdicts exactly as the script does (the *Item format* in Phase 3 is the verdict→tag map):
   **Refuted** → drop (count it, don't persist) · **Verified** / **Unconfirmed** → keep with the
   matching tag · **budget-exhausted** → `deferred` and list in `pending-cells`.
8. **Budget checkpoint** — one shared `max-cells-per-run` cap; on a hit (or cells `pending`),
   checkpoint `PARTIAL` with explicit `done`/`pending` lists and **tell the user to re-run**.
   **Never silently truncate.** Even on `PARTIAL`, the Tier-1 test-baseline item still emits for
   untested behavior-bearing code seen in the covered cells.
9. **Author the backlog** (Phase 3) and **report the dial level + coverage** + the run-report line.

---

## Phase 3 — Backlog  *(LIVE — write the rendered fence body)*

On the **script path**, Phase 3 is **file mechanics**, not free-hand authoring: the script's return
carries `renderedBacklog` — the **complete fence body** built by the script's `renderBacklogFence`
helper (status line, legend, tiers, recommended starting point, run report, go-button). **Write that
string between the markers and replace `{{DATE}}` with today's date.** The format is the **renderer's**
to own — **format source of truth: `renderBacklogFence` and its tests in
`tests/workflows/audit.test.mjs`** — so it can no longer drift from the documented shape. (On the
*prose-orchestrated fallback* only, you author the body by hand, following that same documented shape
— see the renderer + its tests for the exact format.)

### The backlog fence  *(load-bearing convention — mirrors the overview fence)*

The backlog lives in `docs/claugentic-ROADMAP.md` between exact HTML-comment markers:

```
<!-- harness-audit:backlog:start -->
…the rendered fence body (renderedBacklog) here…
<!-- harness-audit:backlog:end -->
```

Same rules as the overview fence — **these rules govern the write and are NOT owned by the renderer:**
**replace only the content *inside* the fence** on a re-run; everything outside is **human-owned and
never touched** (human-added roadmap items and the `## Later` section survive every regeneration). If
the fence is **absent**, insert it once (below the overview fence), headed
`## Backlog — the work worth doing  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh · run /claugentic-dev-harness:build to see it merged with the product backlog)_`.
The heading and the markers are **SKILL-owned** — the renderer emits neither.

### The three things to know about what you're writing  *(summary — the renderer is the source of truth)*

1. **The status line is the resume contract.** Its `done-cells` / `pending-cells` are verbatim
   `cellKey` tokens; a re-run reads them, treats `done-cells` as finished, and sweeps only
   `pending-cells` (pass them back as the script's `doneCells` arg). The Tier-1
   `missing-test-baseline` item emits even on a `PARTIAL` run (the script protects its key from the
   prune). The `{{DATE}}` placeholder is the **only** thing you fill in.
2. **Every item carries exactly one verification phrase** (`(checked against the code)` /
   `(could not confirm independently — model's assertion)` / `(⚠ not yet verified — re-run to
   confirm)`) — a *reduction of false confidence*, never a guarantee; refuted findings are dropped
   (their only trace is the run-report count). When Tiers 1+2 are both empty, the recommended
   starting point is the **terminal "sound" signal** — the explicit stop. The renderer handles all of
   this; do not re-author it.
3. **The closing run-report you say to the user** (conversationally, outside the fence) frames the
   refuted count as a trust signal. The rendered fence already carries the run-report line; **when
   `verification.crossModel` is false**, that line carries the verbatim same-model tag instead of the
   cross-model parenthetical (never both) — and **on a prose-orchestrated run, also state that** in
   your conversational report.

### Tag → discipline  *(the mapping lives in `docs/claugentic-WORKFLOW.md` — enforcement is not yet automated)*

When the user later runs a backlog item through the pipeline, its **tag selects the discipline** —
the full mapping lives once in **`docs/claugentic-WORKFLOW.md`** (→ *Executing an audit backlog item — tag →
discipline*). The one part to reflect when **authoring**: a **`refactor`** on untested
behavior-bearing code is **characterization-tests-first — it cannot start until its Tier-1
"establish a test baseline" item is done.** Today that precondition is upheld by **the implementer
stopping and asking**; the durable `PreToolUse` hook **does not exist yet** — so be honest in the
backlog and **do not imply the hook (or any automatic gate) already exists.**

### After the write — report to the user

After writing the fence and stamping the date, **report the dial level + coverage** conversationally
(which cells ran, `COMPLETE` or `PARTIAL`, and any baseline fallback). The verification run-report
line is already in the rendered fence; echo its trust framing to the user (count of dropped findings,
the cross-model-or-same-model-tag clause exactly as the fence carries it). **Do not list the specific
refuted claims** and **do not persist them.**
