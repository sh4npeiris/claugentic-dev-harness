# 0017 — Codebase-agnostic `init`: non-destructive, self-asserting adoption + cheap-skeleton tree

- **Status:** Implemented + Verified (DoD met) — awaiting land (commit). Both slices A+B shipped as 0.1.38.
- **Resumable from:** Land — commit 0.1.38 (user's call on commit-to-main vs branch+PR). Verify complete: gates green; architect PASS, honesty CLEAN, yagni proportionate; recorded-choice must-fix re-verified PASS.
- **Blockers:** none — edits the harness *source*; independent of which plugin version is installed
- **Roadmap item:** `docs/ROADMAP.md` → Standing tracks & later → "Agnostic init"
- **References:** `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · memory `harness-agnostic-update-design` · `harness-suite-rollout`

## Problem

`init` is not yet graceful on a **mature** codebase, and the gap actively blocks the suite rollout:

1. **Unconditional blocking gate (the rollout-blocker).** `init` wires **both** tree hooks unconditionally — including the blocking `Stop` gate — regardless of whether the repo keeps its own tree (`skills/init/SKILL.md:291-311`). Step 5c (`:323`) even references "the tree-gate decision in (b)" that **(b) never makes** — a documented-but-unimplemented decision.
2. **Measured consequence.** On a mature repo with its own tree, that blocking gate full-scans an *incompatible* tree. Exact-token coverage simulation (2026-06-16): 6/7 adopter repos (`the team, ConnectBase, DocBase, FlowBase, WatchBase, adopterOS`) score **0%** because their trees are **ASCII directory diagrams inside ` ``` `-fenced blocks**, which the gate's `_strip_fenced_blocks` strips → the gate flags **100%** of source files MISSING → every commit blocked. an adopter scores 95% (prior-init backtick tree). an adopter repo survived only because it was *hand-grafted* with the gate off (no hooks in its `settings.json`) — never a real `init` run. The suite rollout *is* the first real `init` on mature-with-tree repos, so this surfaces now.
3. **Adoption is silent about conflicts.** A competing way-of-work doc or rival instruction file just sits in the repo and can mislead agents; `init` neither flags it nor establishes the harness as authoritative.
4. **Full tree generation is expensive.** Today's generation does a "cheap read of each file" for descriptions (`skills/init/SKILL.md:247-249`) — on a 590–947-file repo that burns real agent budget.

## Goals / Non-goals

**Goals**
- `init` is **graceful and non-destructive on ANY codebase** — fresh, mature-without-tree, mature-with-tree — with one model.
- **Never wire a blocking gate that false-flags an incompatible tree** (the rollout-blocker fix).
- **Cheap-complete tree on adoption**: every real path listed from ground truth, no per-file content reads; descriptions enrich best-effort over time.
- **Assert harness authority** via the always-loaded `CLAUDE.md` managed fence; **never delete user files**.
- Surface conflicts (incompatible tree, competing way-of-work doc) as **plain-English prompts**; **harvest** a legacy way-of-work for fold-in.

**Non-goals (guard against creep)**
- **No deletion of user files, ever** (reversed from an earlier idea — users won't accept it; authority-via-CLAUDE.md replaces it).
- **No brace-glob tolerance in the gate** — deferred (YAGNI): "keep your own tree" repos run gate-*off*, so the gate never needs to read a curated tree. (Tracked as a future ROADMAP item if a repo ever wants gate-*on* over a brace-glob tree.)
- **No ASCII-diagram parsing** in the gate — the harness *dictates* backtick-prose format.
- **No new generator script** — the `init` agent already lists files via `git ls-files`; the skeleton is just formatting that list (sidesteps the antivirus-on-scripts concern entirely).
- **No mandatory description-enrichment hook/script/sub-agent** — descriptions are never gate-enforced, so they need no machinery (optional on-demand backfill noted as future).
- **No auto-merge of user prose** (the never-clobber invariant holds).

## Approach

`init` becomes **non-destructive + self-asserting**, branching on one detected scenario.

### Scenario detection → tree build → hook wiring

Reuse the existing signals (the `/audit` Phase-1 "Application source present" predicate at `skills/init/SKILL.md:273` + presence of `docs/ARCHITECTURE_TREE.md`). No new detector (DRY).

| Scenario | Detection | Tree action | Hooks wired |
|---|---|---|---|
| **Fresh** | no tree + little/no source | generate incrementally as files are added | `PostToolUse(Write)` nudge **+** blocking `Stop` |
| **Mature, no tree** | no tree + source present | **cheap-complete skeleton**: `git ls-files` ∩ globs → one `- \`path\`` line each, grouped by dir, thin path-derived description, **no content reads** | nudge **+** blocking `Stop` (complete → won't false-trip) |
| **Mature, with tree** | tree present | **prompt** (below) | per the user's choice |

**Why the skeleton is cheap *and* complete *and* accurate:** the expense was the per-file *descriptions*, not the path list. Listing paths is a millisecond `git ls-files` the agent already runs. Built from ground truth, it inherits **none** of any pre-existing tree's possible inaccuracy. Because it lists every path, **presence is satisfied from day 1** → the blocking `Stop` backstop can stay on without false-flagging. Descriptions stay thin and enrich best-effort via the *existing* convention ("update a file's line when you change its role") — **no new per-touch machinery**, because descriptions are never gate-checked.

### The mature-with-tree prompt (non-destructive)

When `init` finds an existing `docs/ARCHITECTURE_TREE.md`, it **pauses and prompts** (AskUserQuestion) with plain-English context — *"You have a `docs/ARCHITECTURE_TREE.md`. The harness gate reads a backtick-prose format and can't enforce a fenced ASCII diagram. How do you want to proceed?"*:
- **Replace with a harness skeleton** → write the cheap skeleton (old tree preserved in git history); wire nudge + blocking `Stop`.
- **Keep mine, gate off** → leave the tree untouched; wire **neither** hook; set `INCLUDE_GLOBS = []` so a manual run can't false-flag. (This is an adopter repo's circumstantial state, now an explicit choice.)
- **Skip** → leave as-is, record the choice, don't re-prompt next run.

Records the choice in the detected-tooling block (outside the fence) so re-`init` is idempotent (no re-prompt).

### Self-asserting CLAUDE.md authority clause

The managed fence (`skills/init/SKILL.md:353-401`) gains an **authority + conflict-resolution clause** (static managed content — idempotent):

> *The way we work here is defined by the harness — `docs/WORKFLOW.md`, `docs/ENGINEERING_STANDARDS.md`, `docs/PLAYBOOK.md`, `docs/ARCHITECTURE_TREE.md` — these are authoritative. Other `.md` files in this repo are project/domain content, **not** process authority; if anything conflicts with the harness way of work, the harness wins. When genuinely unsure, follow the harness and **ask**.*

Honest framing: this is **model-upheld** (no mechanical file-hiding exists), but `CLAUDE.md` is the only always-loaded anchor and "ask when in doubt" is the safety valve. It **replaces deletion** — no user file is touched.

### Competing-doc detection + harvest prompt (non-destructive)

When `init` detects an *obvious* competing way-of-work / agent-instruction doc (a small high-precision allow-list of names: a non-managed `docs/WORKFLOW.md`-class file, `.cursorrules`, `AGENTS.md`, `copilot-instructions.md`, a `SUITE_HARNESS`-style doc), it **prompts**: *"Found `X` that overlaps the harness way of work. Fold any lessons into the harness / leave it (the CLAUDE.md authority clause keeps agents on the harness) / skip?"* — **never deletes**. A quick scan offers the **harvest**: surface anything worth promoting into the harness, then leave the file in place.

**Alternatives rejected:** (a) auto-delete competing docs — users won't accept it, and the authority clause defuses the conflict without loss; (b) brace-glob / ASCII-diagram gate parsing — large machinery for a case "gate-off" already covers; (c) a skeleton-generator script — unnecessary (agent already lists via git) and adds an AV/EDR surface; (d) a description-enrichment read-hook — perpetual overhead for zero gate benefit.

## Affected files

- `skills/init/SKILL.md` — **step 4** (skeleton mode for mature-no-tree; the mature-with-tree prompt), **step 5b** (conditional hook wiring per scenario — the core fix), **step 6** (authority clause in the fence), **new** competing-doc/harvest prompt sub-step, **step 9** (report branches: skeleton / gate-off / reconciled).
- `docs/WORKFLOW.md` — reconcile the adopter note (`~:113`) so the "tree-gate off when you keep your own tree" claim matches the now-*real* conditional wiring.
- `scripts/check_architecture_tree.py` — **docstring only** (name the three scenarios; no logic change).
- `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — version bump **in lockstep** (`scripts/check_versions_synced.py` enforces the pair).
- `docs/DECISIONS.md` — record: non-destructive+authority-clause (not deletion); cheap-skeleton; gate-off-for-keep; format dictated; brace-glob deferred.
- `docs/ARCHITECTURE_TREE.md` — no new files expected → no entry change (confirm at Verify).

## Research / grounding

- **Files reviewed:** `skills/init/SKILL.md:1-509` (full flow map: steps 1-9; the unconditional dual-hook wiring at `:291-311`; the phantom "tree-gate decision" at `:323`; the expensive per-file-read generation at `:247-249`; the never-clobber/stop-if-ambiguous invariants at `:27-28,156-158`; idempotency contract `:513-536`); `scripts/check_architecture_tree.py:1-407` (presence = exact backtick token, `_strip_fenced_blocks` drops fenced diagrams, staleness, glob-drift, `--hook`/`--hook-write`); `.claude/plans/TEMPLATE.md`.
- **Evidence:** coverage sims — an adopter repo 287/1455 (20%); adopter 0% ×6 (ASCII-in-fences) + an adopter 95%. an adopter repo `settings.json` has **no** hooks (hand-grafted gate-off); its `.claude/rules/rules.md` confirms its tree was hand-maintained, no generator, no gate (model-upheld + review).
- **Harness docs consulted:** `docs/WORKFLOW.md` (DoD + adopter note), memory `harness-agnostic-update-design` (locked decisions) + `harness-suite-rollout`, `CLAUDE.md` (engineering principles; honesty positioning).
- **Findings:** reuse — `/audit` Phase-1 layout detection (scenario signal), existing self-silencing `--hook-write` nudge + `Stop` backstop, the managed fence + detected-tooling block (for the authority clause + choice-recording). Build — the scenario branch + skeleton mode + conditional wiring + prompts. Gotcha — every addition must regenerate **byte-identically** on re-run (idempotency `:513-536`), so prompts fire only on detected conflict and recorded choices suppress re-prompts.

## Risks & mitigations

- **Idempotency regression** → authority clause is static fenced content; prompts gate on detected conflict; keep/skip choices recorded in the detected-tooling block so re-`init` is a no-op. Verify with the existing re-run-zero-diff dogfood.
- **Backward-compat on re-`init`** (an adopter repo @0.1.34, adopter prep branches) → re-`init` detects the existing tree and **prompts**; it **never auto-removes** a previously-wired hook (flag-and-recommend) — no silent settings churn.
- **Model-upheld authority over-claim** → honest wording in the fence + docs; route the claim past the honesty-reviewer.
- **False-positive conflict prompts** → high-precision name allow-list only; `CLAUDE.md` itself is the designed merge target, never flagged as a conflict.

## Test strategy

This is primarily **SKILL.md prose + managed content** — verification is dogfooding + reviewers, not unit tests (no script logic changes beyond a docstring).
- **Dogfood (primary):** run `init` on a throwaway copy/branch of a mature-with-tree repo (e.g. a adopter repo) and confirm: (1) "replace" → skeleton lists all in-scope paths + gate green + both hooks wired; (2) "keep, gate off" → no hooks wired, `INCLUDE_GLOBS=[]`, tree untouched; (3) authority clause present in the fence; (4) **re-run = zero git diff** (idempotency); (5) a planted `.cursorrules` triggers the prompt and is **not** deleted.
- **Deterministic gates:** existing `tests/` stay green; `scripts/check_versions_synced.py` passes after the bump; the tree-check gate passes on the harness's own repo.
- **Reviewers:** architect-reviewer (SKILL changes), honesty-reviewer (authority + gate-off claims), yagni-sentinel (scope).

## Decomposition (slices)

Each slice lands **complete in one ≤1M-context session, no debt**.

- [ ] **Slice A — cheap-skeleton tree mode + conditional gate wiring** (+ reconcile the `:323` doc-vs-behavior gap and the WORKFLOW adopter note). The **rollout-unblocker**. Lands complete because it's verifiable end-to-end by dogfooding `init` on a mature-with-tree repo (the three tree outcomes + idempotency) and ships as a version bump. Independent of Slice B.
- [ ] **Slice B — self-asserting CLAUDE.md authority clause + non-destructive competing-doc/harvest prompts.** Lands complete because it's verifiable by dogfooding `init` on a repo with a planted competing doc (prompt fires, nothing deleted, fence carries the clause) + idempotency. Builds on A's prompt scaffolding but is independently shippable.

---

## Review  _(filled by plan-reviewer, Stage 3)_

> RUNNING AS: Opus 4.x — same-vendor as the likely builder family; treat this review as a shared-blind-spot-risk reduction, not an independent oracle.

- **Verdict:** CHANGES REQUIRED — the engineering is fundamentally sound and the conditional-wiring fix is correctly diagnosed, but four under-specified seams will leave the spec ambiguous or risk an idempotency/never-clobber regression. None is a design rethink; all are spec-level tightenings the implementer needs.

- **Required changes:**

  1. **Spell out the step-4 ↔ step-5(a) ordering for each scenario — it is currently load-bearing and unstated.** Step 4 (`skills/init/SKILL.md:242`) *calls into* step 5(a) glob-detection before building the tree, and step 5(a) (`:273-278`) sets `INCLUDE_GLOBS = []` whenever the "Application source present" predicate is false. The plan's scenario table (`:43-48`) treats "tree action" and "hooks wired" as one column each but never says, per scenario, **what `INCLUDE_GLOBS` is set to and in what order relative to the tree build.** The two failure modes this leaves open: (a) **Mature-no-tree** must run 5(a) → derive real globs → build skeleton from those globs → reconcile (the existing step-4 loop), or the skeleton and the gate disagree; (b) **Keep-mine-gate-off** must set `INCLUDE_GLOBS = []` *and* skip step 4 entirely (tree exists). The plan says gate-off sets `INCLUDE_GLOBS = []` (`:55`) but does not state that step 4's "first do 5's glob-detection" sub-call is itself conditional now. The spec must give a per-scenario sequence: detect → (tree action) → (glob value) → (hook decision), naming which existing sub-steps run and which are skipped.

  2. **Fix the `INCLUDE_GLOBS = []` idempotency interaction with the hybrid carve-out — name it explicitly.** Gate-off writes `INCLUDE_GLOBS = []` into the copied `check_architecture_tree.py`. On re-`init`, the step-3 body-compare **excludes** the `INCLUDE_GLOBS` assignment on both sides (`:189-192`) and a REFRESH **re-injects the adopter's existing globs** (`:193-197`). So `[]` *is* preserved across re-runs — good — but only if the implementer knows the gate-off `[]` is "the adopter's existing globs" that the carve-out protects, not a managed value to reset. The plan never connects gate-off-`[]` to the carve-out; an implementer could plausibly treat `[]` as a default to be re-derived on re-run, which would silently turn the gate back on for a "keep mine" repo (a real regression against the user's locked choice). The spec must state: gate-off `INCLUDE_GLOBS = []` is adopter-owned, protected by the existing `:189-201` carve-out, and re-`init` must NOT re-derive globs for a repo whose recorded choice was "keep mine, gate off."

  3. **Define the recorded-choice contract precisely — where it lives, its exact key, and how re-`init` reads it BEFORE prompting.** The plan says the choice is recorded "in the detected-tooling block (outside the fence)" (`:58`) so re-`init` doesn't re-prompt. But the detected-tooling block is **create-if-absent and never rewritten on re-run** (`:399-401`, `:421-423`, `:443-446` — except the single append-if-absent `Run the app:` line). A free-form choice line added there is safe to read, but the plan must specify: (a) the exact label/format of the recorded line (so the re-run detector matches it deterministically, like the `Run the app:` key); (b) that it is appended **append-if-line-absent** keyed on that label (consistent with `:443-446`), never rewritten; (c) the precedence when the recorded choice and the current on-disk state disagree (e.g. user later deleted their tree after choosing "keep mine"). Without this the "no re-prompt" idempotency claim (`:92`) is asserted, not derivable — and a malformed/absent record silently falls back to re-prompting, which dirties nothing but breaks the zero-interaction re-run contract the plan leans on.

  4. **The mature-with-tree "Replace" branch needs an explicit never-clobber guard mirroring step 3.** The prompt's "Replace with a harness skeleton" option (`:54`) overwrites a **user-owned** `docs/ARCHITECTURE_TREE.md` (it is create-if-absent / user-owned per `:238-239`, `:542-544`). Today step 4 *never* touches an existing tree. "Replace" is the first path in the skill that overwrites a user file, and the plan's "old tree preserved in git history" (`:54`) is the only stated safeguard. The spec must state: Replace proceeds **only** on the explicit AskUserQuestion confirmation (never on silence/default), and the report's Stage-9 honesty register must name it as a user-file overwrite recoverable only from git (an *uncommitted* user tree is unrecoverable — same caveat as the managed-refresh headline at `:459-467`). This is a genuine new clobber surface and the plan under-states it.

  5. **Reconcile the WORKFLOW adopter-note edit honestly — it currently DESCRIBES conditional wiring that does not yet exist.** `docs/WORKFLOW.md:113` already reads "wired as a hook by `init` only when the tree-gate is enabled." That sentence is *aspirational* today (Problem #1: wiring is unconditional). Slice A makes it true. The plan lists the WORKFLOW edit (`:77`) as "reconcile … so the claim matches the now-real conditional wiring" — good, but the implementer must edit WORKFLOW **in the same slice that makes the wiring conditional (A)**, never before, or the doc over-claims a behavior the code lacks. State this as a within-slice ordering constraint, and route it past `honesty-reviewer` (the plan already flags the authority-clause claim for honesty review at `:94`, but not this one).

- **Sizing/completeness:**
  - **Slice A (skeleton + conditional wiring + `:323`/WORKFLOW reconcile)** — **OK as one session.** It edits one SKILL step-cluster (4, 5a/5b), one docstring, two manifests, two docs; no script logic change. Lands vertically complete: dogfoodable end-to-end (three tree outcomes + idempotency), version-bumped. This is the rollout-unblocker and is correctly prioritized first. The required changes above (1, 2, 4, 5) are all absorbed into A's spec — they do not split it.
  - **Slice B (authority clause + competing-doc/harvest prompts)** — **OK as one session, but the A/B split has a real coupling the plan half-acknowledges and must resolve.** Both slices add **AskUserQuestion prompts** to `init` (A: the mature-with-tree prompt; B: the competing-doc prompt) and both record a choice outside the fence (Required change 3 governs both). The plan says B "builds on A's prompt scaffolding" (`:109`) — so the **recorded-choice mechanism (Required change 3) is shared infrastructure that MUST be built in A** (the mature-with-tree prompt needs it) and merely reused in B. Make that explicit in both specs: A owns the recorded-choice contract; B consumes it. With that pinned, the split is clean and B is independently shippable. **Do not merge** — A alone unblocks the rollout and is the time-sensitive deliverable; gating it on B's authority-clause/honesty-review cycle would delay the fix for no reason.
  - **Missing completeness item:** neither slice lists a deterministic test surface beyond "existing tests stay green." That is honest (the change is SKILL prose + managed content; the gate script changes only its docstring) — see Harness impact for the one thing worth adding.

- **Harness impact:**
  - **No new STANDARD or agent.** The plan correctly reuses the existing `/audit` Phase-1 predicate (no new detector) and adds no machinery — YAGNI-clean (the four rejected alternatives at `:72` are the right rejections).
  - **DECISIONS entries (`:80`) — confirm they capture the *engineering* invariants, not just the product calls:** add a line pinning "gate-off ⇒ `INCLUDE_GLOBS = []` is adopter-owned, protected by the existing INCLUDE_GLOBS carve-out, never re-derived on re-run" (Required change 2) and one for "Replace is a confirmed user-file overwrite, git-recoverable only" (Required change 4). These are the non-obvious choices a future maintainer will re-litigate.
  - **One Stage-9 gate-candidate worth a ROADMAP line (not this slice):** the "managed copy whose own claim depends on behavior in another file" pattern (WORKFLOW:113 ↔ conditional wiring) is exactly the kind of doc-vs-behavior drift no current gate catches — the same class as the retired phantom `:323` reference. A standing check is out of scope here, but log it as a candidate alongside the existing skills-prose-namespace gate item (`docs/ROADMAP.md:40`). The plan's claim of "no ARCHITECTURE_TREE change" (`:81`) is correct (no files added/moved) — confirm at Verify, nothing to pre-add.
  - **Cheap-skeleton claim verified sound (non-blocking confirmation):** a skeleton of `- \`path\`` lines passes `evaluate()` presence (`check_architecture_tree.py:289-290` via `_backtick_tokens` → `BACKTICK_TOKEN_PATTERN`), introduces no false staleness (every listed path exists, `:296-298`), and clears glob-drift (`in_scope_files()` non-empty short-circuits `glob_drift`, `:256-258`). **One constraint the spec MUST carry forward:** the skeleton and its directory grouping must use markdown headings + `- \`path\`` lines and **never** ```` ``` ````-fenced blocks — a fence would be stripped by `_strip_fenced_blocks` (`:129-150`) and desync the very pairing that caused the 6×0% adopter measurement. The plan's "backtick-prose, no ASCII diagrams" format (`:30`) already implies this; make it an explicit acceptance criterion so a future skeleton author can't reintroduce the regression the slice exists to fix.

---

## Spec  _(per slice, after Review passes — Stage 4)_

> All five plan-review Required Changes are folded in below. One refinement to the Approach: the mature-with-tree prompt collapses to **two** options (Replace / Keep-mine-gate-off) — the earlier "Skip" was mechanically identical to Keep-gate-off (records the choice, wires no hooks, no re-prompt), so it's dropped (KISS). To later switch a kept tree to the harness format, delete it and re-`init` (→ mature-no-tree → skeleton) — a clean escape hatch.

### Slice A — cheap-skeleton tree mode + conditional gate wiring  _(the rollout-unblocker — implement first)_

- **In plain English (the approval gate):**
  - **What this builds:** `init` stops blindly wiring a blocking tree-gate. It detects your repo's situation and acts: a **fresh** repo gets the full gate; a **mature repo with no tree** gets a cheap, complete file index (every path listed via `git ls-files`, *no* slow per-file reading) + the gate; a **mature repo that already has a tree** gets **asked** — replace it with a harness index, or keep yours and turn the gate off. It also fixes the doc (`WORKFLOW.md:113`) that currently claims this already works, and the phantom "tree-gate decision" reference at `SKILL.md:323`.
  - **What "done" means for you:** running `init` on any adopter repo no longer breaks commits — you pick "keep mine, gate off" (or "replace") and the harness wires accordingly. Re-running `init` changes nothing — no re-prompt, no git diff.
  - **What you're accepting:** "Replace" **overwrites** your existing `docs/ARCHITECTURE_TREE.md` (recoverable from git only — an *uncommitted* tree would be lost), and it happens **only** if you explicitly choose it. "Keep mine, gate off" means **no mechanical tree enforcement** on that repo (model-upheld via CLAUDE.md) — the deliberate trade for keeping your own tree.

- **Per-scenario sequence — detect → tree action → `INCLUDE_GLOBS` → hooks** _(Required changes 1 + 2):_
  - **Fresh** (no tree + "Application source present" = false): run 5a (→ `INCLUDE_GLOBS = []` per `:273-278`, or detected globs if any source) → create a minimal tree → wire `PostToolUse(Write)` nudge **+** blocking `Stop`. (≈ today's empty-repo behavior; the Write nudge fills it as files land.)
  - **Mature, no tree** (no tree + source present): run 5a → derive **real** globs → build the cheap skeleton **from those globs** → reconcile via the existing step-4 loop (gate is oracle) → wire nudge **+** blocking `Stop`. `INCLUDE_GLOBS` = the detected real globs.
  - **Mature, with tree** (tree present): **skip step 4's tree build entirely** (the tree exists) → run the two-option prompt below.
    - **Replace** → behave as mature-no-tree (5a → real globs → skeleton → reconcile), overwriting the tree → wire nudge + `Stop`. Record `replace`.
    - **Keep mine, gate off** → tree untouched; set `INCLUDE_GLOBS = []`; wire **neither** hook. Record `keep-gate-off`. **The `[]` is adopter-owned**, protected by the existing INCLUDE_GLOBS carve-out (`:189-201`): re-`init` must **NOT** re-derive globs for a repo whose recorded choice is `keep-gate-off` (else the gate silently turns back on — a regression against the locked choice).

- **Recorded-choice contract** _(Required change 3 — built here, consumed by Slice B):_
  - **Lives in** the detected-tooling block (outside the fence — create-if-absent, append-if-line-absent, never rewritten; same pattern as the `Run the app:` line at `:443-446`).
  - **Exact line:** `- Architecture tree: <harness-skeleton (gate on) | kept by adopter (gate off, your init choice)>` — keyed on the label `Architecture tree:`.
  - **Keying:** append-if-line-absent on that label; never rewritten.
  - **Read-before-prompt:** re-`init` reads this line **before** the mature-with-tree prompt; if present and consistent with on-disk state, honor it and **skip the prompt**.
  - **Precedence on disagreement:** **on-disk state wins for the tree action.** Tree present + record `keep-gate-off` → honor, no prompt. Tree present + no record → prompt. **Tree absent** (user deleted it later) → mature-no-tree path regardless of the record, and refresh the record. A malformed/absent record falls back to prompting (safe; dirties nothing).

- **Replace = confirmed user-file overwrite** _(Required change 4):_ Replace proceeds **only** on the explicit AskUserQuestion confirmation — never on silence/default/timeout/AskUserQuestion-unavailable (in which case fall back to `keep-gate-off` + report, mirroring the never-clobber stop-if-ambiguous posture at `:27-28,156-158`). The Stage-9 report **honesty register** must name it: *"Replaced your `docs/ARCHITECTURE_TREE.md` with a harness skeleton — your previous tree is in git history (an uncommitted tree is unrecoverable)"* (same caveat class as `:459-467`).

- **WORKFLOW reconcile — within-slice ordering** _(Required change 5):_ edit `docs/WORKFLOW.md:113` **in this slice** (never before the wiring is conditional, or the doc over-claims). Route the edit past `honesty-reviewer`.

- **Skeleton format — the regression guard** _(reviewer acceptance criterion):_ the skeleton uses markdown headings + `- \`path\`` lines and **never** ` ``` `-fenced blocks (a fence is stripped by `_strip_fenced_blocks:129-150` and would desync the very pairing that caused the 6×0% adopter measurement).

- **Files & changes:**
  - `skills/init/SKILL.md` — step 4 (skeleton mode + conditional 5a-call ordering + the mature-with-tree prompt), step 5b (conditional wiring per scenario — replace the unconditional dual-wire at `:295-302`), step 5c (make the `:323` "tree-gate decision in (b)" reference real), step 9 (report branches + Replace honesty register), + the recorded-choice sub-step.
  - `scripts/check_architecture_tree.py` — docstring names the three scenarios (no logic change).
  - `docs/WORKFLOW.md:113` — reconcile (this slice, honesty-reviewed).
  - `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — bump to **0.1.38** in lockstep (`scripts/check_versions_synced.py` enforces).
  - `docs/DECISIONS.md` — add: (a) gate-off ⇒ `INCLUDE_GLOBS=[]` is adopter-owned, carve-out-protected, never re-derived; (b) Replace is a confirmed user-file overwrite, git-recoverable only; (c) cheap-skeleton + format-dictated + brace-glob deferred.

- **Tests / verification** (SKILL prose + managed content → dogfooding + reviewers, no script logic change):
  - **Dogfood** on a throwaway copy/branch of a mature-with-tree adopter repo: (1) Replace → skeleton lists all in-scope paths, gate green, both hooks; (2) Keep-gate-off → no hooks, `INCLUDE_GLOBS=[]`, tree untouched; (3) **re-run = zero git diff + no re-prompt**; (4) skeleton has **no fenced blocks**.
  - Existing `tests/` stay green; `check_versions_synced` green after the bump; the harness's own tree-gate green.
  - Reviewers: `architect-reviewer` (SKILL changes), `honesty-reviewer` (`WORKFLOW:113` + gate-off claims), `yagni-sentinel` (scope).

- **Acceptance criteria:**
  - [ ] `init` wires **no** blocking `Stop` hook for a `keep-gate-off` repo; wires both for skeleton/fresh.
  - [ ] Mature-no-tree → cheap skeleton, **complete** (all in-scope paths present per the gate), no content reads, **no fenced blocks**, gate reconciles green.
  - [ ] Mature-with-tree → two-option prompt; **Replace only on explicit confirm**; Replace overwrite named in the Stage-9 honesty register.
  - [ ] Recorded-choice line (label `Architecture tree:`) suppresses re-prompt; **re-`init` = zero diff**; on-disk state wins on disagreement.
  - [ ] Gate-off `INCLUDE_GLOBS=[]` survives re-`init` (carve-out), never re-derived.
  - [ ] `WORKFLOW.md:113` matches the now-real conditional wiring; `honesty-reviewer` CLEAN.
  - [ ] `plugin.json` + `marketplace.json` at 0.1.38; `check_versions_synced` green.

### Slice B — self-asserting CLAUDE.md authority clause + non-destructive competing-doc/harvest prompts

- **In plain English (the approval gate):**
  - **What this builds:** the harness's `CLAUDE.md` section gains a short *"this is how we work; other instruction files aren't process authority; when in doubt follow the harness and ask"* clause — so agents stay on the harness even if old instruction docs linger. And `init` notices **obvious** competing way-of-work docs (a rival WORKFLOW, `.cursorrules`, `AGENTS.md`, a `SUITE_HARNESS`-style doc) and asks whether to **harvest** lessons from them — **never deleting anything**.
  - **What "done" means for you:** adopting onto a repo with old agent-instructions no longer creates confusion; **nothing of yours is deleted**; you get a one-time prompt to mine old way-of-work for ideas worth promoting into the harness.
  - **What you're accepting:** the authority clause is **model-upheld** (no mechanical file-hiding exists), backed by the "ask when in doubt" valve. Competing docs are **left in place** — the clause defuses them rather than removing them.

- **Depends on Slice A:** consumes A's **recorded-choice contract** (same `label:` / append-if-line-absent mechanism) so the competing-doc prompt doesn't re-fire on re-`init`.

- **Files & changes:**
  - `skills/init/SKILL.md` — step 6 (authority + conflict-resolution clause inside the managed fence — static, idempotent), new competing-doc detection + harvest-prompt sub-step (high-precision name allow-list; `CLAUDE.md` itself never flagged; **never delete**; record choice via A's contract), step 9 (report).
  - `docs/DECISIONS.md` — authority-via-CLAUDE.md replaces deletion; non-destructive adoption.
  - version bump (fold into 0.1.38 if shipped with A, else 0.1.39).

- **Tests / verification:**
  - **Dogfood:** planted `.cursorrules` → prompt fires, file **NOT** deleted; fence carries the authority clause; re-run = zero diff + no re-prompt.
  - Reviewers: `honesty-reviewer` (the model-upheld authority claim), `architect-reviewer`, `yagni-sentinel`.

- **Acceptance criteria:**
  - [ ] Managed fence contains the authority/conflict clause; **regenerates byte-identically** on re-run.
  - [ ] Competing-doc prompt fires only on the high-precision allow-list; `CLAUDE.md` itself never flagged.
  - [ ] **No user file deleted, ever.**
  - [ ] Harvest prompt offers fold-in; choice recorded via A's contract; no re-prompt.
  - [ ] `honesty-reviewer` CLEAN on the authority-clause wording.
