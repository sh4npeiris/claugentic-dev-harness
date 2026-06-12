---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, depth-dialed) and tries to independently re-check every finding before it reaches the backlog.
---

# /claugentic-dev-harness:audit

Point this at a repo and it teaches you what the codebase is, then finds the work
worth doing — written back as a plain-English, prioritized backlog a non-engineer
can act on.

## How this skill works

Three phases, cheap → expensive, run end-to-end in one pass:

1. **Understand** *(LIVE, conversational)* — one cheap inline pass over manifests + structure to
   produce a plain-English **"what your app is & does"** overview and an **audit-plan** (what to
   look at, in what order, with what excluded). No fan-out. *(This phase genuinely needs you —
   it stays a conversation.)*
2. **Audit** *(LIVE)* — **the orchestrator invokes `workflows/audit.js`** (the Workflow tool) with
   the audit-plan as args; the script runs the FIND → PRUNE → VERIFY pipeline mechanically: a
   `lens-reviewer` fan-out per `(module × dir)` cell at the dial's **depth**, coded dedup, a
   synthesis self-review prune, and **exactly one `finding-verifier` per surviving finding**
   (cross-model judge), with a deterministic budget cap + resume.
3. **Backlog** *(LIVE)* — the script's **structured return** is rendered into the
   `harness-audit:backlog` fence in `docs/ROADMAP.md` as a **tiered, tagged, plain-English**
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

> **Which path runs (be honest about it):** `quick` and `standard` run through `workflows/audit.js`
> (the script). **`thorough` runs on the legacy prose path** (the *Prose-orchestrated fallback*
> below) **until Slice 3b adds its script stages** — and the run report says so, tagged
> "prose-orchestrated". If the **Workflow tool is unavailable** in this session, *any* level falls
> back to the prose path, stated to you and tagged the same way. Never claim script guarantees on a
> prose run.

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

1. **Prefer existing signal.** If `docs/ARCHITECTURE_TREE.md` exists and is current (DRY with the
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
   `scripts/check_architecture_tree.py` — plus the seeded `docs/standards/`, `WORKFLOW.md`,
   `PLAYBOOK.md`) and the exclude-set (deps / build / generated). A repo of **only** docs + config
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

Phase 1 writes the overview into `docs/ROADMAP.md`, between exact HTML-comment markers:

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
`thorough` *additionally* runs a cross-cutting blind-spot sweep and an independent adversarial
prune — but those stages live on the prose path until Slice 3b (see the path note above).

---

## Phase 2 — Audit  *(LIVE — invoke the script)*

**You (the orchestrator) run this** — the script's fan-out spawns subagents, and subagents can't
spawn subagents. For `quick`/`standard` with the Workflow tool available, **invoke the script**;
otherwise take the *Prose-orchestrated fallback*.

### Invoke `workflows/audit.js`

Call the Workflow tool with:

- **`scriptPath`** = `${CLAUDE_PLUGIN_ROOT}/workflows/audit.js` (the version-stamped plugin install
  path — read-from-install-path, never copied to an adopter). **When dogfooding *this* repo**, use
  the repo-local `./workflows/audit.js` (the working tree *is* the plugin source).
- **`args`** mapped from the audit-plan (Phase 1):
  - `dial` — the chosen level (`quick` | `standard`; **`thorough` is rejected by the script** — it
    routes to the prose path).
  - `modules` — the candidate standards-module **names** (e.g. `["security","testing"]`; the script
    maps each to `docs/standards/<name>.md`). **No clearly-relevant module?** fall back to the
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
    straight to VERIFY for re-checking. Findings already carrying a *resolved* verdict tag
    (`verified` / `unconfirmed`) are **not** re-passed — their verdicts persist in the fence.
  - `builderFamily` — your (the orchestrator's) model family, for the same-model tag.

**Tell the user first, in plain English** (so a multi-minute pass isn't a silent stall): *"This can
take several minutes on a larger repo — I'm reading the code through several quality lenses in
parallel."* What the script then runs mechanically: **FIND** (one `lens-reviewer` per module batch
at `depthForDial(dial)`), **PRUNE** (coded dedup → a synthesis self-review agent → cut-list, with
the `missing-test-baseline` item **never** pruned), **VERIFY** (exactly one `finding-verifier` per
surviving finding, cross-model judge-pinned, clean-context input — never the finder's rationale).
A lens batch that errors after one retry sends its cells to `pending` (the run goes `PARTIAL` —
never a silent skip); the cap forces `PARTIAL` with exact `done`/`pending` cell lists for a
deterministic resume.

### The structured return (what Phase 3 renders)

```
{ status, level, depth, doneCells, pendingCells,
  items: [{ findingKey, modules, tier, tag, titlePlain, claimTechnical, locations,
            whyPlain, impactEffort, confidence, verification: {state, evidence, plainLine} }],
  refutedCount,
  verification: { verified, unconfirmed, deferred, refuted, crossModel, sameModelTag } }
```

- `verification.state` per item is one of `verified` · `unconfirmed` · `deferred` — never a silent
  "checked". Refuted findings are **dropped** (their only trace is `refutedCount`); no timestamps
  anywhere (the orchestrator stamps the date when it renders).
- `verification.crossModel` is true **only** when every verifier returned a confirming
  different-family self-report; otherwise `verification.sameModelTag` carries the verbatim tag.

### Prose-orchestrated fallback  *(Workflow tool unavailable, OR `dial = thorough` until Slice 3b)*

State to the user which trigger applies, run the legacy 9-step pipeline below by hand, and **tag
the conversational run report "prose-orchestrated"** — never claim the script's mechanical
guarantees on a prose run. The pipeline (each agent's full contract is in its `.claude/agents/`
file — read it there):

1. **Set the dial** (above) — depth per lens; at `thorough`, also the blind-spot sweep + the
   adversarial prune.
2. **Load the audit-plan** from Phase 1.
3. **Enumerate `(module × dir-or-package)` cells** — the deterministic unit; on resume, read the
   status block and continue from `pending`, never redoing a `done` cell.
4. **Fan out lenses — one look per cell.** One `lens-reviewer` (audit-scope mode) per module batch,
   in parallel, passed its module + scoped dirs + exclude-set + the dial's `depth`
   (`.claude/agents/lens-reviewer.md`). *(thorough only:* also one `blindspot-reviewer` over the
   whole scope at `exhaustive` — it FINDS only; its findings join the same dedup → prune → verify
   path. `.claude/agents/blindspot-reviewer.md`.)
5. **Dedup + synthesize.** Key dedup on **issue-class**, not file·location alone; roll up systemic
   cross-file duplicates into one "recurs in N files" item; carry each finding's confidence label
   unchanged. **Citation-guard:** re-confirm every `file:line` against the actual file first.
6. **PRUNE — YAGNI right-size** the consolidated set (keep real impact; cut nice-to-haves; never
   manufacture a finding to fill a tier). *(thorough only:* additionally spawn one `yagni-sentinel`
   over the set — the independent skeptic — and apply its cut-list. `.claude/agents/yagni-sentinel.md`.)
   **Exception: never prune the Tier-1 "establish a test baseline" item.**
7. **VERIFY — re-check every surfaced finding** (all tiers, every level). Spawn one
   `finding-verifier` per finding **with the `fable` model override** (the cross-model judge — the
   mechanism, the self-report comparison, the verbatim same-model tag, and the on-error respawn+tag
   live in `docs/WORKFLOW.md` → Principles → *"Convene the panel's judge roles with the `fable`
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

## Phase 3 — Backlog  *(LIVE — render the structured return)*

Render the script's structured return (or, on the prose path, the synthesized findings) as a
**tiered, tagged, plain-English** backlog a non-engineer can act on. Each item is **pipeline-ready**
— enough that the user picks one and the existing workflow (Discuss → … → Land) runs it. **For this
slice the format rules below are the source of truth** (Slice 3b moves the rendering into a
unit-tested script helper).

### The backlog fence  *(load-bearing convention — mirrors the overview fence)*

The backlog lives in `docs/ROADMAP.md` between exact HTML-comment markers:

```
<!-- harness-audit:backlog:start -->
…status block + tiered backlog here…
<!-- harness-audit:backlog:end -->
```

Same rules as the overview fence: **replace only the content *inside* the fence** on a re-run;
everything outside is **human-owned and never touched** (human-added roadmap items and the
`## Later` section survive every regeneration). If the fence is **absent**, insert it once (below
the overview fence), headed
`## Backlog — the work worth doing  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh)_`.

### Status block  *(first thing inside the fence — what makes resume deterministic)*

A single line at the very top of the fence, built from the return's `status` / `level` /
`doneCells` / `pendingCells` (the date is **stamped by you**, the orchestrator, after the run — the
script carries no clock):

```
status: COMPLETE | PARTIAL · level: quick|standard|thorough · done-cells: [module×dir, …] · pending-cells: [module×dir, …] · date: YYYY-MM-DD
```

- **`status`** — `COMPLETE` if every enumerated cell was audited; `PARTIAL` if the run checkpointed
  with cells still `pending`.
- **`done-cells` / `pending-cells`** — the explicit `(module × dir-or-package)` lists from the
  return, **verbatim `cellKey` tokens**. **These are the resume contract:** a re-run reads them,
  treats `done-cells` as finished, and sweeps only `pending-cells`. Keep the lists concrete —
  `done: 3 dirs` is not enough to resume from.

### "How to read this" legend  *(2 lines, just below the status block)*

Immediately under the status line — still **inside the fence**, before Tier 1 — write a **short
2-line legend** so a non-engineer can read the tags without a glossary. Keep it to **2 lines** —
one short phrase per tag, then the verification phrases on a single line. Because every item now
carries a verification tag, the verification line is the **most-read trust statement** — so it MUST
carry the not-a-guarantee caveat:

- **Line 1 (tags):** `refactor` = tidy without changing behavior · `capability-upgrade` =
  add/upgrade a technology · `dependency-health` = update/patch dependencies · `bug` = fix wrong
  behavior · `feature` = new behavior.
- **Line 2 (verification — one line, caveat included):** `(checked against the code)` = a separate
  agent re-read the code and couldn't refute it · `(could not confirm independently — model's
  assertion)` = still just the model's claim · `(⚠ not yet verified — re-run to confirm)` = budget
  ran out before checking — **a re-check by a different model family than the builder (the
  cross-model judge; on a same-family run, tagged as such) — a reduction of shared-blind-spot risk,
  not a mechanical guarantee.**

### Tiers (most urgent first)

- **Tier 1 — critical:** correctness · security · data-loss. **Untested behavior-bearing code →
  "establish a test baseline" is Tier-1 item #1** (it gates any later refactor — see tag→discipline).
  This item emits even on a `PARTIAL` run (the script protects its `missing-test-baseline` key from
  the prune).
- **Tier 2 — important:** maintainability · missing tests · performance.
- **Tier 3 — polish:** docs · style · cleanup.

Map each return `item` to its tier by `item.tier`; order tiers most-urgent-first.

**Architecturally-sound terminal signal.** When **Tier 1 and Tier 2 both come back empty** (only
Tier-3 polish, or nothing at all), the backlog must **say so plainly** — the explicit "stop"
signal. State it in the Recommended-starting-point, e.g.: *"Sound on the audited dimensions — what
remains is optional polish; you don't need to keep re-auditing."* (On a `COMPLETE` run this is a
genuine all-clear; on a `PARTIAL` run, scope it to the covered cells.)

### Item format (every item)

For each return `item`:
- **Title** — `item.titlePlain` (a short, plain action).
- **Tag** — exactly one of `refactor` · `capability-upgrade` · `dependency-health` · `bug` ·
  `feature` (`item.tag`). The tag selects the discipline when the item runs (below).
- **Dual-layer** — (1) the **technical finding** `item.claimTechnical` with `item.locations` (for a
  systemic item, "recurs in N files: …"); then (2) **one plain-English line** `item.whyPlain` —
  *why it matters / how bad / what could break.*
- **Impact + rough effort** — `item.impactEffort` (plain-English, so the user can prioritize).
- **Verification — exactly one inline tag per item**, from `item.verification.state`:
  - `verified` → `(checked against the code)` — proof snippet (`item.verification.evidence`)
    attached to the technical finding.
  - `unconfirmed` → `(could not confirm independently — model's assertion)`.
  - `deferred` → `(⚠ not yet verified — re-run to confirm)` (it sits in `pending-cells`; a re-run
    re-checks it).

  There is **no badge/legend system** beyond this single inline phrase, and the per-finding
  `deterministic`/`judgment` confidence label is **not shown per item** (`item.confidence` is
  carried internally only). Findings the verifier **Refuted** are dropped entirely — their only
  trace is the run-report count below. A verification tag is a *reduction of false confidence*, not
  a deterministic guarantee — never overstate it.

### Tag → discipline  *(the mapping lives in `docs/WORKFLOW.md` — enforcement is not yet automated)*

When the user later runs a backlog item through the pipeline, its **tag selects the discipline** —
the full mapping lives once in **`docs/WORKFLOW.md`** (→ *Executing an audit backlog item — tag →
discipline*). The one part to reflect when **authoring**: a **`refactor`** on untested
behavior-bearing code is **characterization-tests-first — it cannot start until its Tier-1
"establish a test baseline" item is done.** Today that precondition is upheld by **the implementer
stopping and asking**; the durable `PreToolUse` hook **does not exist yet** — so be honest in the
backlog and **do not imply the hook (or any automatic gate) already exists.**

### Recommended starting point + the verification run report

End the backlog with a short **Recommended starting point** — usually Tier-1 #1 (the test baseline
if there's untested behavior-bearing code), with one plain sentence on why. **If Tier 1 and Tier 2
are both empty**, the recommended-starting-point *is* the sound signal — say *"Sound on the audited
dimensions — what remains is optional polish; you don't need to keep re-auditing"* instead of
pointing at an item.

Then **report the dial level + coverage** to the user (which cells ran, `COMPLETE` or `PARTIAL`,
and any baseline fallback), and include the **verification run-report line** driven by the return's
`verification` block — frame the dropped ones as a trust signal, reported as a **count, not a
list**: *"Re-checked every finding I surfaced against the code (the cross-model judge — by default
a different model family than the builder); dropped `refutedCount` that couldn't be confirmed —
verified N · unconfirmed K · deferred J."* **When `verification.crossModel` is false** (the run
carries `verification.sameModelTag`), **replace** the parenthetical with the verbatim tag — never
emit both clauses: *"same-model review on this run — the judge and the builder are the same model
family here."* **On a prose-orchestrated run, also state that** in the report. **Do not list the
specific refuted claims** and **do not persist them.**

Finally, **close the backlog with this plain "how to start" line** (verbatim, so the user always
has the go-button): *"To start anything — a backlog item or a brand-new project — just tell the
agent in plain English what you want (e.g. 'Let's do Tier-1 item 1' or 'I want to build X'). It
will ask you questions (Discuss), then write a plan and spec for you to approve before any code.
For a backlog item, the go-button is **`/claugentic-dev-harness:build`** — point it at one item
('build Tier-1 item 1') and it drives the whole reviewed pipeline for you, pausing only at the spec
(before any code) and before anything irreversible."*
