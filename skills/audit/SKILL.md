---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, loop-until-dry).
---

# /claugentic-dev-harness:audit

Point this at a repo and it teaches you what the codebase is, then finds the work
worth doing — written back as a plain-English, prioritized backlog a non-engineer
can act on.

## How this skill works

Three phases, cheap → expensive, run end-to-end in one pass:

1. **Understand** *(LIVE)* — one cheap inline pass over manifests + structure to produce
   a plain-English **"what your app is & does"** overview and an **audit-plan** (what to
   look at, in what order, with what excluded). No fan-out.
2. **Audit** *(LIVE)* — the expensive fan-out: `lens-reviewer`s (in **audit-scope mode**)
   sweep the included code through the relevant standards modules; dedup, loop-until-dry,
   **deterministically resumable** under a per-run budget cap.
3. **Backlog** *(LIVE)* — the audit findings, written as a **tiered, tagged,
   plain-English** backlog into the `harness-audit:backlog` fence in `docs/ROADMAP.md`,
   ending with a recommended starting point.

Run the full flow: Understand → Audit → Backlog. The fan-out in Phase 2 spawns
`lens-reviewer` subagents, so **a top-level agent (the orchestrator) runs this skill** —
subagents can't spawn subagents. Audit findings are **model-asserted, then independently
verified for the high-stakes ones (Tier-1 + security), and human-triaged**: a separate
`finding-verifier` reads the cited code and tries to *refute* each critical/security claim
before it reaches the backlog (Phase 2's verify step) — an honest **reduction of false
confidence**, not a deterministic gate. Carry each finding's confidence honestly (see
*Confidence* in the Phase 3 item format) — never launder a judgment call into apparent fact,
and never fabricate a finding to fill a tier.

### How to use it (a periodic snapshot, not a treadmill)

- **Run it periodically** — after meaningful changes, **not obsessively.** It's a snapshot
  of where the codebase stands, not a chore to keep chasing to zero.
- **The backlog regenerates, it doesn't accumulate.** A re-run replaces the fenced backlog
  with the *current* snapshot — it gives you today's picture, not an ever-growing pile.
- **Tier 3 is optional** polish; **an empty Tier 1 + Tier 2 means the code is sound** on the
  audited dimensions — that's the signal to stop, not a prompt to manufacture more work.
- **The dial auto-sizes** to the repo (small → `quick`, larger → `standard`) and is reported
  up front; **name `quick` / `standard` / `thorough` to override.**

---

## Phase 1 — Understand  *(LIVE)*

A single cheap, inline pass. **Budget discipline:** read **manifests, configs, entry
points, and READMEs — not every source file.** You are building a map, not reviewing code.

### Output contract — what this phase produces

- **(A) User-facing overview** — plain-English, **text-only** (no diagram), written
  into the ROADMAP overview fence (see *Where the overview goes* below). For a
  non-engineer. Sections, in order:
  *what it is · what it does · how it's built · how it's organized ·
  safety-net signals (tests / CI / types) · confidence & caveats.*
  Be **honest that it's inferred from structure, not from running the app.**
- **(B) Audit-plan** — audit-internal, handed to Phase 2; also shown to the user
  in-conversation as the proof this phase ran. Five fields:
  *exclude-set · prioritized directory order · monorepo / package boundaries ·
  detected ecosystem + existing tooling · candidate standards modules.*

### The 8-step procedure

Run these in order. Each step feeds the output contract above.

1. **Prefer existing signal.** If `docs/ARCHITECTURE_TREE.md` exists and is current
   (DRY with the `init` skill, which generates it), use it as the file-level map — do
   **not** re-walk the tree. Otherwise derive structure via a **bounded `Glob` walk**
   (top-level dirs + one or two levels in; do not enumerate excluded trees). Either
   way, read only manifests / configs / entry points / READMEs from here on.
   **Count-guard:** when you state a count (files, modules, packages, tests), **prefer a
   source-of-truth** — a manifest, an index like `ARCHITECTURE_TREE.md`, or a README —
   over counting raw files yourself; if you can only infer the number, **say so and
   hedge** ("~N, inferred") rather than asserting a precise figure.

2. **Detect ecosystem & tooling.** Scan the root and significant subdirs for
   **manifests** to identify language(s), framework(s), and package manager — the
   general rule is *"identify by manifest,"* not an exhaustive list:
   `package.json` (Node/JS/TS), `pyproject.toml` / `requirements.txt` / `setup.py`
   (Python), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml` / `build.gradle` (JVM),
   `Gemfile` (Ruby), `composer.json` (PHP), `*.csproj` / `*.sln` (.NET), … . In the
   same pass, detect **existing lint / format / type-check / test tooling** from its
   config (eslint, prettier, `tsconfig.json`, jest / vitest / pytest / go test, …)
   and any CI workflows (`.github/workflows`, `.gitlab-ci.yml`). This dovetails with
   the `init` skill's compose-with-existing-tooling and tells the audit **which gates
   already exist** so it doesn't propose redundant ones.

3. **Detect monorepo / package boundaries.** Look for `workspaces` (in `package.json`),
   `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, multiple manifests in
   different dirs, or a `packages/` · `apps/` layout. **If monorepo, enumerate the
   packages as separate audit units** (each gets its own slice of the directory order).

4. **Build the exclude-set.** Honor **`.gitignore` as the primary signal** (read it
   first), augmented by well-known dirs the audit must never spend budget on:
   - VCS: `.git`
   - dependencies: `node_modules`, `vendor`, `.venv` / `venv`, `__pycache__`,
     `target`, `Pods`
   - build / output: `dist`, `build`, `.next`, `out`, `coverage`, `.turbo`
   - generated: `*.generated.*`, `*.min.js`, codegen output
   - lockfiles and large binary / media assets
   - **Security (hard rule):** **never read or echo secrets** — `.env*` files, keys,
     credentials, certificates. Exclude them from the walk and **never surface their
     contents** in the overview or the audit-plan. If you must mention one exists, name
     the file, not its contents.

5. **Identify entry points & surfaces.** From the manifests and conventions, find how
   the app is entered: `main` / `bin` / `scripts` (Node), `[project.scripts]` /
   `__main__.py` (Python), `func main` (Go), framework conventions (`src/index.*`,
   `app/`, `pages/`, `cmd/`), `Dockerfile` `CMD` / `ENTRYPOINT`. Use these to classify
   the app's **type** — CLI · web server · library · SPA · service · (or, as here, a
   plugin / docs-and-tooling repo) — and its external surfaces.

6. **Map dependencies (high-level).** Name only the **architecturally-significant**
   dependencies (web frameworks, DB drivers, HTTP / auth libraries, queues) — enough to
   say *"an Express + Postgres API,"* not every transitive dep. These **pre-select the
   likely standards modules**: a DB driver pulls in `data-and-persistence`; an HTTP
   server pulls in `api-and-contracts` + `security`; a UI pulls in `product-ux`.

7. **Prioritized directory order.** Rank the *included* directories by likely
   risk / value for the audit's budget spend — highest first:
   **entry points & core domain → data / persistence → API / routes → UI →
   config / scripts → tests last.** This is what Phase 2 walks; spend lands where bugs
   and standards violations cluster.

8. **Compose & emit.** Write the plain-English overview **(A)** into the ROADMAP fence
   (replacing only the fenced content — see below), and present the audit-plan **(B)**
   to the user as this phase's proof and Phase 2's input.

### Where the overview goes — the ROADMAP fence  *(load-bearing convention)*

Phase 1 writes the overview into `docs/ROADMAP.md`, between exact HTML-comment markers:

```
<!-- harness-audit:overview:start -->
…generated overview here…
<!-- harness-audit:overview:end -->
```

Rules:
- On **re-run, replace only the content *inside* the fence.** Everything outside it
  is **human-owned and must never be touched** — human-added roadmap items survive
  every regeneration.
- If the fence is **absent**, insert it once near the top of the ROADMAP (after the
  intro block), headed
  `## What this app is & does  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh)_`.
- Phase 3 writes the **backlog** into a **parallel `harness-audit:backlog` fence**,
  governed by the same replace-only-inside rule (see *The backlog fence* in Phase 3).

---

## Phase 2 — Audit  *(LIVE)*

The expensive pass: fan out `lens-reviewer`s over the *included* code and synthesize
their findings. **You (the orchestrator) run this** — Phase 2 spawns subagents, and
subagents can't spawn subagents.

The whole pass is **deterministically bounded and resumable**: work is a finite set of
discrete `(module × dir)` cells, the status block tracks which are `done` vs `pending`
(so a re-run continues, never restarts), and the caps in steps 6 + 9 (max-rounds +
max-cells-per-run) **guarantee termination.**

### The 10-step procedure

1. **Set the dial — named level wins, else auto-size from Phase 1.** The skill is
   invoked in natural language, not with typed flags. First read the invocation for a
   **named** level — **`quick`** or **`standard`** (e.g. "audit quick", "do a standard
   audit"). **A named level always wins.** If none is named, **auto-pick from Phase 1's
   repo sizing** (the audit-plan's structure / candidate-module count / monorepo signal):
   a **small, simple repo → `quick`**; a **larger repo, many candidate modules, or a
   monorepo → `standard`.** Keep this a **rough size/complexity judgment** from the
   Understand phase — do not author a precise scoring formula. **Always report the chosen
   level up front** so the user can steer — e.g. *"Auto-selected `quick` — small repo; say
   `standard` (or `thorough`) to override"* (or *"Using `standard` as you asked"* when
   named). These are the **only two live levels** — if the user names `thorough`, run `standard`
   and tell them the deeper `thorough` pass (a second adversarial sweep) is a deferred
   roadmap item, not built yet. The level sets two caps used below:

   | level | max-rounds (loop-until-dry) | scope |
   |---|---|---|
   | `quick` | **1** (single pass, no re-sweep) | the **top** candidate modules over the highest-priority dirs only |
   | `standard` | **N** (re-sweep until a round is dry, capped — see step 6) | **all** relevant candidate modules over the full prioritized order |

2. **Load the audit-plan from Phase 1.** Take the four fields Phase 1 emitted:
   **exclude-set · prioritized directory order · monorepo / package boundaries ·
   candidate standards modules.** (If Phase 1 didn't run this session, run it first —
   the audit needs its plan.) **No clearly-relevant module?** If the repo matches no
   standards module strongly (e.g. a pile of shell scripts), **fall back to the baseline
   lenses — `docs-traceability` + `maintainability-structure`** — and **say so in the
   report** ("no strongly-matched module; audited against the baseline lenses"). Never
   audit nothing.

3. **Enumerate work as `(module × dir-or-package)` cells** — the deterministic unit of
   the whole pass. For each candidate module, pair it with each in-scope directory (or,
   for a **monorepo, each package**) it should cover, in the prioritized order. This
   finite cell set is what the budget cap counts, what the loop sweeps, and what the
   status block tracks.
   - **On a resume run:** read the **status block** at the top of the existing backlog
     fence (see Phase 3). Take the **`pending`** cells and continue from there; **never
     redo a `done` cell.** If the backlog has no status block (or it says `COMPLETE`),
     this is a fresh full run — enumerate all cells.

4. **Fan out lenses (delegation = the primary budget defense).** Group cells into
   **batches by module** (one module over its scoped dirs/packages) and spawn a
   **`lens-reviewer` subagent in audit-scope mode** per batch, **in parallel**. Pass each
   subagent: its **module**, the **scoped dir/package list** for that batch, and the
   **exclude-set**. Each returns a **per-dimension digest** (met/gap + `file:line` +
   confidence + a plain-English line). Cell granularity keeps each subagent's read-set
   small, so the fan-out stays in-budget even on a big repo.

5. **Dedup + synthesize.** Maintain a **persisted seen-set** of findings across rounds
   (so "did this round add anything new?" is judged against what's already been seen, not
   re-discovered). Key dedup on **issue-class** (the *kind* of problem — e.g.
   "missing-input-validation"), **not** on file·location alone — so two **distinct** issues
   at the *same* spot (say a security gap and a perf gap on the same lines) are **kept
   separate**, and only same-class findings merge. **Roll up systemic cross-file
   duplicates:** when one issue-class recurs across many files, collapse them into **one
   backlog item that lists the locations** ("recurs in N files: …") rather than N noisy
   items or one item that hides the spread. **Carry each finding's confidence label**
   (`deterministic` vs `judgment` / verified-vs-asserted) **through synthesis unchanged**
   — synthesis must not upgrade a judgment call into apparent fact.
   **Citation-guard:** before any finding's `file:line` enters the backlog, **re-confirm it
   against the actual file** — never carry a line number you haven't re-verified. The
   backlog's whole value is that its cited locations are trustworthy (the same discipline
   as the Phase-1 count-guard).

6. **Loop-until-dry (`standard` only).** Re-sweep the cells that aren't yet dry; a round
   is **dry** when it adds **nothing new** to the seen-set. Stop the loop when a round is
   dry **or** when the **max-rounds cap** for the level is hit (see step 1) — whichever
   comes first. The finite cell set **plus** the integer cap **guarantee the loop
   terminates** (it cannot oscillate, because "new" is judged against the persisted
   seen-set). For **`quick`**, max-rounds = 1: a single pass, no re-sweep.

7. **YAGNI right-size the consolidated set (post-dry).** After the loop has gone dry /
   hit max-rounds, do one final right-sizing pass over the consolidated findings — the
   harness's own YAGNI applied to its own output: **keep only findings with real impact;
   cut marginal "nice-to-haves" that don't earn their keep; never manufacture a finding to
   fill a tier.** A sound codebase legitimately yields few or no items — a valid, expected
   result. This is a synthesis discipline, *not* a fan-out (no extra subagents; a full
   adversarial `yagni-sentinel` sweep over the findings is a deferred `thorough`-level
   item — don't build it here). It runs only after dry-detection, so it trims the
   already-finished set and cannot affect loop termination. (Exception: never prune the
   Tier-1 "establish a test baseline" item for untested behavior-bearing code — see step 9.)

8. **Verify high-stakes findings (Tier-1 + security).** For every survivor of the prune that
   will be **Tier-1 (correctness / security / data-loss)** *or* comes from the **`security`
   lens** — determinable from the finding's nature/module before final tiering — spawn an
   independent **`finding-verifier`** to try to **refute** it against the code. **One rule,
   every dial:** Tier-1 + security on `quick` *and* `standard` alike — **no dial-scaling**
   (verifying `deterministic`-labeled findings on `standard`, or *all* findings on `thorough`,
   is a deferred roadmap item — don't build it here). The trust floor is dial-independent:
   never present an unverified critical/security claim as fact.
   - **Independence is enforced by the input contract.** Pass each verifier **only**
     `{claim (plain + technical), file:line, source module, confidence label, exclude-set}` and
     the refute-first posture — **never** the finder's transcript or rationale, and **never** let
     a lens verify its own finding (route it to a verifier seeded from a clean context). With a
     clean-context subagent given just the claim + location, independence is *structural*. (See
     `.claude/agents/finding-verifier.md`.) **You (the orchestrator) spawn these directly** —
     they are not nested under the `lens-reviewer`s. Fan them out **in parallel.**
   - **Apply the verdicts:**
     - **Refuted** → **drop** the finding from the backlog (it was a false positive); record it
       for the run report (step 10's report line). Refuted findings are **not** persisted durably
       (regenerate-don't-accumulate — see step 5 / Phase 3); their only trace is the run report.
     - **Verified** → **keep** + attach the verifier's **proof snippet** (`file:line`); tag it
       inline `(checked against the code)` in Phase 3.
     - **Unconfirmed** → **keep** + **flag** it inline `(could not confirm independently —
       model's assertion)` in Phase 3 — never silently presented as fact.
   - **Budget — verification draws from `max-cells-per-run`** (see step 9), **not** a separate
     uncapped burst. Size the cap to leave headroom to verify the criticals found (they are
     few). If the budget is **exhausted** before a Tier-1/security finding can be verified, mark
     it **`deferred`**: write the finding with an explicit **"⚠ not yet verified — re-run to
     confirm"** flag and list it in `pending-cells`. A critical is **never** silently presented
     as verified — its representable states are `verified` · `unconfirmed` · `deferred`.
   - **Persistence + resume.** A verdict **persists in the backlog fence alongside its finding**
     (its inline tag *is* the persisted verdict). On a **resume** run a finding already carrying
     a verdict is **not re-verified**, and `done` cells are not re-swept — so refuted findings
     don't reappear and there is no O(rounds) re-verify cost. (A fresh re-run regenerates the
     backlog from scratch, so it may legitimately re-find and re-refute — an accepted cost.)

9. **Budget checkpoint = deterministic (no "sensing context").** Each **run** has a
   **max-cells-per-run cap** — a hard integer ceiling on how many cells one run audits
   (size it to stay comfortably within context for the repo; the prioritized order means
   the highest-value cells are spent first). **When the cap is hit — or cells remain
   `pending` after max-rounds — checkpoint:**
   - write the **partial backlog** of what was found so far (Phase 3),
   - set the status block to **`PARTIAL`** with the explicit **`done`** and **`pending`**
     cell lists,
   - **stop, and tell the user to re-run** to continue (the re-run resumes from
     `pending`).
   **Never silently truncate** — a partial run must always say it's partial and record
   where it stopped. **Test-baseline guarantee:** even on a `PARTIAL` run, the Tier-1
   "establish a test baseline" item **still emits** for any **untested behavior-bearing
   code seen in the covered (`done`) cells** — a partial audit must never green-light an
   unguarded refactor.

10. **Author the backlog** (Phase 3) into the `harness-audit:backlog` fence, **recommend a
    starting point**, and **report the dial level + coverage** to the user (which cells
    ran, `COMPLETE` or `PARTIAL`, and — if any — which modules fell back to baseline). Include
    the **verification run-report line** for the high-stakes findings checked in step 8 —
    frame the refuted ones as a **trust signal that the check bit**, reported as a **count, not
    a list**: e.g. *"Independently re-checked the Tier-1/security findings; dropped N that
    couldn't be confirmed against the code."* Keep `verified N · unconfirmed K` in the same
    line. **Do not list the specific refuted claims** (that invites re-litigating dropped
    noise) and **do not persist them** — a count in the run report is the only trace a refuted
    finding leaves, since refuted findings aren't persisted.

---

## Phase 3 — Backlog  *(LIVE)*

Write the synthesized findings as a **tiered, tagged, plain-English** backlog a
non-engineer can act on. The backlog is the deliverable; each item is **pipeline-ready**
— enough that the user picks one and the existing workflow (Discuss → … → Land) runs it.

### The backlog fence  *(load-bearing convention — mirrors the overview fence)*

The backlog lives in `docs/ROADMAP.md` between exact HTML-comment markers:

```
<!-- harness-audit:backlog:start -->
…status block + tiered backlog here…
<!-- harness-audit:backlog:end -->
```

Same rules as the overview fence: **replace only the content *inside* the fence** on a
re-run; everything outside is **human-owned and never touched** (human-added roadmap
items and the `## Later` section survive every regeneration). If the fence is **absent**,
insert it once (below the overview fence), headed
`## Backlog — the work worth doing  _(generated by /claugentic-dev-harness:audit · do not edit — re-run to refresh)_`.

### Status block  *(first thing inside the fence — what makes resume deterministic)*

A single line at the very top of the fence:

```
status: COMPLETE | PARTIAL · level: quick|standard · done-cells: [module×dir, …] · pending-cells: [module×dir, …] · date: YYYY-MM-DD
```

- **`status`** — `COMPLETE` if every enumerated cell was audited; `PARTIAL` if the run
  checkpointed with cells still `pending`.
- **`done-cells` / `pending-cells`** — the explicit `(module × dir-or-package)` lists.
  **These are the resume contract:** a re-run reads them, treats `done-cells` as finished,
  and sweeps only `pending-cells` (Phase 2 step 3). On a `COMPLETE` run, `pending-cells`
  is empty. Keep the lists concrete — `done: 3 dirs` is not enough to resume from.

### "How to read this" legend  *(2 lines, just below the status block)*

Immediately under the status line — still **inside the fence**, before Tier 1 — write a
**short 2-line legend** so a non-engineer can read the tags without a glossary. Keep it to
**2 lines, not a wall** — one short phrase per tag, plus what the verification phrases mean:

- **Line 1 (tags):** `refactor` = tidy without changing behavior · `capability-upgrade` =
  add/upgrade a technology · `dependency-health` = update/patch dependencies · `bug` = fix
  wrong behavior · `feature` = new behavior.
- **Line 2 (verification):** `(checked against the code)` = a separate agent confirmed it
  against the actual code · `(could not confirm independently — model's assertion)` = still
  just the model's claim, not independently confirmed.

(Author it in plain prose on those two lines — the bullets above are the *content*, not the
required layout. Don't expand it into a section; the inline tags stay self-explanatory.)

### Tiers (most urgent first)

- **Tier 1 — critical:** correctness · security · data-loss. **Untested behavior-bearing
  code → "establish a test baseline" is Tier-1 item #1** (it gates any later refactor —
  see the tag→discipline note). This item emits even on a `PARTIAL` run.
- **Tier 2 — important:** maintainability · missing tests · performance.
- **Tier 3 — polish:** docs · style · cleanup.

**Architecturally-sound terminal signal.** When **Tier 1 and Tier 2 both come back empty**
(only Tier-3 polish, or nothing at all), the backlog must **say so plainly** rather than
leave the user guessing — it is the explicit "stop" signal. State it in the status area /
Recommended-starting-point, e.g.: *"Sound on the audited dimensions — what remains is
optional polish; you don't need to keep re-auditing."* (On a `COMPLETE` run this is a
genuine all-clear; on a `PARTIAL` run, scope it to the covered cells.) This pairs with the
step-7 YAGNI prune: a clean codebase legitimately produces few or no items, and that is a
*result*, not a gap to fill.

### Item format (every item)

- **Title** — a short, plain action ("Add input validation to the request handlers").
- **Tag** — exactly one of: **`refactor`** (behavior-preserving cleanup) · **`capability-upgrade`**
  (introduce/upgrade a technology) · **`dependency-health`** (update/patch deps) ·
  **`bug`** (fix incorrect behavior) · **`feature`** (new behavior). The tag selects the
  discipline when the item runs (see below).
- **Dual-layer** — (1) the **technical finding** with `file:line` (for a systemic item,
  list the locations / "recurs in N files"); then (2) **one plain-English line** —
  *why it matters / how bad it is / what could break.*
- **Impact + rough effort** — plain-English ("medium impact; ~half a day"), so the user
  can prioritize.
- **Verification + Confidence — one status axis per item, in plain English.** These are two
  *different* axes: **Confidence** = *could a gate prove this* (`deterministic` vs `judgment`);
  **Verification** = *was this checked against the code, and what came back* (Phase 2 step 8).
  To spare a non-engineer reconciling two labels, **show only one per item:**
  - A **verified-scope item** (Tier-1 or security — the findings step 8 checks) shows its
    **inline verification tag**, and that tag **supersedes** the `deterministic`/`judgment`
    confidence label for display:
    - `(checked against the code)` — a `finding-verifier` confirmed it (proof snippet attached
      to the technical finding).
    - `(could not confirm independently — model's assertion)` — the verifier returned
      `Unconfirmed`; kept, but honestly flagged as still just the model's claim.
    - `(⚠ not yet verified — re-run to confirm)` — `deferred`: budget ran out before it could be
      checked (it sits in `pending-cells`; a re-run verifies it).
  - An **out-of-scope item** (everything else — not Tier-1, not security) keeps its
    **confidence label** (`deterministic` / `judgment`) exactly as today.
  - **No item shows both**, and there is **no badge/legend system** — the inline phrase is
    self-explanatory. Findings the verifier **Refuted** are dropped entirely (they never appear
    here; their only trace is step 10's run-report line). Be honest either way: a verification
    tag is a *reduction of false confidence*, not a deterministic guarantee — never overstate it.

### Tag → discipline  *(the tag→discipline mapping in `docs/WORKFLOW.md` — enforcement is not yet automated)*

When the user later runs a backlog item through the pipeline, its **tag selects the
discipline** — the full mapping lives once in **`docs/WORKFLOW.md`** (→ *Executing an
audit backlog item — tag → discipline*). The one part you must reflect when **authoring**
the backlog: a **`refactor`** on untested behavior-bearing code is
**characterization-tests-first — it cannot start until its Tier-1 "establish a test
baseline" item is done.** Today that precondition is enforced by **the implementer
stopping and asking**; the durable `PreToolUse` hook **does not exist yet** (the first
Trust-track item, next phase) — so be honest in the backlog and **do not imply the hook
(or any automatic gate) already exists.**

### Recommended starting point

End the backlog with a short **Recommended starting point** — usually Tier-1 #1 (the test
baseline if there's untested behavior-bearing code), with one plain sentence on why to
start there. This is the hand-off: the user picks it, and the pipeline takes it from
Discuss. **If Tier 1 and Tier 2 are both empty**, the recommended-starting-point *is* the
sound signal — say *"Sound on the audited dimensions — what remains is optional polish; you
don't need to keep re-auditing"* instead of pointing at an item, so the stop signal is the
last thing the user reads.

After the Recommended-starting-point, **close the backlog with this plain "how to start" line**
(verbatim, so the user always has the go-button in front of them): *"To start anything — a
backlog item or a brand-new project — just tell the agent in plain English what you want
(e.g. 'Let's do Tier-1 item 1' or 'I want to build X'). It will ask you questions (Discuss),
then write a plan and spec for you to approve before any code."*
