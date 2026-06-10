# 0004 — Thorough audit dial + streamlined verification

- **Status:** Done — landed `5de65c3` (Slice 1) + `07b608e` (Slice 2); archived 2026-06-09
- **Roadmap item:** `docs/ROADMAP.md` → Next #2 ("Thorough audit (`thorough` dial)")
- **References:** `skills/audit/SKILL.md` · `.claude/agents/{lens-reviewer,finding-verifier,yagni-sentinel}.md` · `docs/DECISIONS.md` (→ *Audit right-sizing*, *Trust & correctness core*, *Trust-first*) · `docs/WORKFLOW.md` (Stage-3 diverse-critics rule) · `docs/ARCHITECTURE_TREE.md` · `README.md`
- **Stage-3 review:** PASSED with required changes folded in (see *Review* below — diverse panel: `plan-reviewer` + `yagni-sentinel` + honesty pass).

---

## Problem

The audit dial (`skills/audit/SKILL.md`) is half-built and its discovery/verification model is more complex *and* less honest than it needs to be:

1. **`thorough` is a dead forward-pointer** — naming it runs `standard` and says "deferred, not built yet" (step 1, ~line 198).
2. **Verification is a confusing, cost-driven 3-rung ladder** — *only* Tier-1 + security findings are verified, "no dial-scaling," with deeper scaling deferred (step 8, ~line 273). The fallout (Phase-3 item format, ~line 426) is a two-class display a non-engineer must reconcile.
3. **Discovery carries loop-until-dry machinery whose re-sweeps mostly reproduce their own findings** — `standard` re-sweeps the *same* lenses until a round adds nothing new (step 6, ~line 255). The high-value "second look" is a *different angle*, not a repeat.

The Stage-1 Discuss (this session) reframed the goal: not "bolt `thorough` onto the ladder," but **streamline the whole pipeline into one honest, efficient shape and make `thorough` the genuine top of it.** A series of user design decisions (recorded under *Approach → Locked decisions*) settled the shape.

## Goals / Non-goals

**Goals**
- Make `thorough` a **live, named-only** level — no fallback-to-`standard`.
- Collapse to **one uniform order at every level: FIND → PRUNE → VERIFY → surface.**
- **Verification stops being a dial axis:** the audit **attempts to re-check every surfaced finding, all tiers, at every level** (the finding has already survived the YAGNI prune, so the set is right-sized). One rule, no per-dial scaling.
- **Retire loop-until-dry.** One look per `(module × dir)` cell; **no identical re-passes.** The only "second look" is `thorough`'s **diverse blind-spot sweep**.
- **The dial scales on exactly these axes:**
  - **FIND depth-per-lens** — `quick` = focused pass (clear gaps from a direct read); `standard`/`thorough` = deep pass (follow call-chains, subtle issues, edge cases). *All relevant lenses run at every level* — depth, never lens-count, is the `quick`↔`standard` lever.
  - **`thorough`-only additions** — the diverse blind-spot sweep (FIND) **and** an adversarial `yagni-sentinel` prune (PRUNE).
- **Budget:** one **shared** high backstop `max-cells-per-run` cap (rarely fires; enables `PARTIAL`/resume) — **no per-level cap, no dir-limiting.** Directory priority survives only as the **order budget is spent in.**
- **Honesty — strengthened, not just preserved.** Universal re-checking makes the verification tag the **primary** per-item trust signal, so the language must say the audit **attempts** to refute and **tags the outcome** — *never* "verifies / arrives with proof." The not-a-mechanical-guarantee caveat must reach the non-engineer at the legend (now the most-read trust line). Verb discipline: **"attempt to re-check," not "verify."**

**Non-goals**
- **No change to the deterministic Trust track (#5).** `finding-verifier` stays the same model class — a reduction of false confidence, not the mechanical CI.
- **No auto-selection of `thorough`** — named-only. The auto-dial still picks `quick`/`standard` by repo size.
- **No result-count cap** — ever. Coverage is bounded by lenses/depth/budget-cells; findings are never silently truncated (`PARTIAL` says so).
- **No change to `scripts/check_architecture_tree.py` or its tests.** Prose/skill + agent-library change; `pytest` stays 47/47, the tree-check gate untouched (beyond listing the new agent).
- **Standards-catalog curation for the 3-rung dial** → `ROADMAP.md` (a deliberate follow-on, not this slice).
- **Partial-coverage glob drift** stays in `ROADMAP.md` → *Later*.

## Approach

### Locked decisions (from the Stage-1 Discuss this session)

1. **All relevant lenses at every level** — never knowingly skip a relevant dimension; `quick`↔`standard` differ by **depth per lens**, not lens-count.
2. **Single look + diverse sweep** — retire loop-until-dry; no identical re-passes; the only second look is `thorough`'s different-angle sweep.
3. **Verify every surfaced finding, all tiers, every level** — uniform; supersedes the Tier-1+security ladder and the deferred deterministic/all-tiers sub-items.
4. **One shared backstop budget cap + resume** — per-agent context is *not* the constraint (each subagent has its own 1M); the cap bounds cost/time + the orchestrator's synthesis context and enables `PARTIAL`/resume.
5. **`thorough` = `standard` + diverse blind-spot sweep + adversarial `yagni-sentinel` prune + (shared) budget.**

### The four operations, untangled

| Operation | Answers | Posture |
|---|---|---|
| **FIND** (`lens-reviewer` fan-out, depth-dialed) | *Did we look everywhere relevant, at the right depth?* (recall) | additive — gaps through module X |
| **PRUNE** (YAGNI) | *Is this finding worth surfacing?* (precision) | cut marginal / over-built noise |
| **VERIFY** (`finding-verifier`) | *Can the claim be refuted against the code?* (correctness) | independent refute, clean context |
| **diverse sweep** (`thorough` only, **new** finder) | *What did the module checklists all miss?* (recall, blind-spots) | adversarial, non-checklist angle |

**Why this is simpler than today:** loop-until-dry was a *recall* hack and "verify only Tier-1+security" was a *cost* compromise. Once we (a) PRUNE before VERIFY (small set) and (b) accept the high-value second look is a *different angle* (not a repeat), verification is cheap enough to apply universally and repeats become pointless. The ladder and the loop both dissolve into **deletions**.

### The streamlined dial

Order, every level: **FIND → PRUNE → VERIFY → surface.**

| Stage | `quick` | `standard` | `thorough` |
|---|---|---|---|
| **FIND — lenses** | all relevant | all relevant | all relevant |
| **FIND — depth/lens** | **focused** (clear gaps from a direct read) | **deep** (call-chains, subtle, edge cases) | deep |
| **FIND — diverse sweep** | — | — | ✓ blind-spot critic |
| **PRUNE (YAGNI)** | synthesis right-size | synthesis right-size | **+ adversarial `yagni-sentinel` sweep** |
| **VERIFY (refute, all tiers)** | attempt on **all surfaced** | attempt on **all surfaced** | attempt on **all surfaced** |
| **budget** | one shared backstop cap + resume | same | same |

- **`quick`** — every relevant lens, **focused depth**: the clear gaps visible from a direct read. Honest contract: *"quick shows the clear issues fast; standard digs for the subtle ones."* Converges with `standard` only on small/clean repos (fine — the auto-dial picks `quick` there).
- **`standard`** — every relevant lens, **deep depth**: follows call-chains, edge cases, subtle issues.
- **`thorough`** — `standard` **+** the diverse blind-spot sweep (catches what the per-module fan-out structurally can't — cross-cutting, architectural, between-the-modules risk) **+** an adversarial `yagni-sentinel` prune (independent cut before the universal verify) **+** the shared budget.

### Depth-per-lens — the concrete mechanism

The dial level sets a **`depth`** the orchestrator passes to each `lens-reviewer` in audit-scope mode (alongside module · scope · exclude-set):
- **`focused`** (`quick`): *"Report the clear gaps visible from a direct read of the scoped code. Don't chase subtle/ambiguous issues or trace deep call-chains — surface what an experienced reviewer spots quickly."*
- **`deep`** (`standard`/`thorough`): *"Follow call-chains, weigh edge cases and subtle issues — report the full picture, not just the obvious gaps."*

This is the **only** `lens-reviewer` contract change; cells stay `(module × dir)`; the deterministic/judgment confidence label is still emitted per finding (it feeds the future Trust track), just demoted from per-item *display* (see below).

### Display consequence — verification is now universal

Every surfaced item is re-checked, so the Phase-3 **two-class display collapses**: **every item carries one verification tag** — `(checked against the code)` / `(could not confirm independently — model's assertion)` / `(⚠ not yet verified — re-run to confirm)`. The `deterministic`/`judgment` label is still emitted by lenses and recorded internally, but **no longer shown per item** (the verification tag is the stronger signal). **Critically (honesty):** the legend shrinks to one line *and gains* the not-a-gate caveat, because it becomes the most-read trust statement on the backlog.

### Termination — simpler post-retirement

Finite `(module × dir)` cells, each audited **once**; `thorough` adds **one** diverse-sweep batch; the **shared budget cap** bounds a run (overflow → `PARTIAL` + resume). No rounds, no max-rounds cap, no oscillation. The cell model, status block, `PARTIAL`/resume, and single-pass dedup all **stay**; only the cross-round seen-set logic goes.

### Alternatives considered & rejected (with the deciding fork)

- **Bolt `thorough` onto the existing ladder** — rejected: keeps the confusing display + the low-yield re-sweep.
- **Scale lenses by relevance gradient (quick = core lenses only)** — rejected (user fork): knowingly skipping a *relevant* lens undermines trust; scale **depth**, never lens-count.
- **Scale dirs** — rejected (user fork): the tree gives the full map; dir-limiting is arbitrary and budget-driven, and with 1M-context subagents there's little budget reason. Dir priority → budget-spend order only.
- **Fixed-N / loop-until-dry repeats** — rejected (user fork): same-lens re-runs mostly reproduce themselves; the *diverse* sweep is the high-yield second look.
- **Narrow verify to Tier-1+2 (skip Tier-3)** — rejected (user fork): the uniform "everything surfaced is re-checked" rule is simplest + most honest, and the Tier-3 set is small post-prune. (Logged as a ROADMAP tuning lever if cost ever bites.)
- **Drop `quick`, ship 2 levels** — rejected (user fork): a genuine fast triage is worth keeping; depth-per-lens delivers it.
- **Reuse `lens-reviewer` for the diverse sweep** — rejected: `lens-reviewer` is *exactly one module*; the sweep targets the *space between* modules — a distinct responsibility (SRP) → its own agent (mirrors `finding-verifier` being standalone, not a third lens mode — DECISIONS).

## Affected files

**Slice 1 — streamlined core dial (`thorough` honestly deferred):**
- `skills/audit/SKILL.md`:
  - **frontmatter `description` (line 2)** — drop "loop-until-dry"; reword to the new model (e.g. "…bounded, dedup, depth-dialed").
  - Phase 2 **step 1** (dial table) — `quick`/`standard` live by **depth-per-lens**; drop the `max-rounds`/scope table; keep `thorough` as an **honest deferred** that runs `standard` and says *the deeper pass lands next* (flips live in Slice 2).
  - Phase 2 **step 4** (fan-out) — pass each `lens-reviewer` the `depth`; single-look semantics.
  - Phase 2 **step 5** (dedup) — drop cross-round seen-set; keep single-pass dedup + citation-guard.
  - Phase 2 **step 6** (loop-until-dry) — **retire**: "single look per cell."
  - Phase 2 **step 8** (VERIFY) — **attempt to re-check all surfaced findings, all tiers, every level**; keep the independence input-contract, verdict application, and budget/`deferred` machinery; **verb discipline** ("attempt," not "verify").
  - Phase 2 **steps 9–10** (budget/report) — one shared cap; run-report line: *"re-checked every surfaced finding; dropped M that couldn't be confirmed — verified N · unconfirmed K · deferred J"* (breakdown mandatory).
  - Phase 3 (item format / status block / legend) — collapse to the universal verification tag; demote the confidence label from per-item display; **status block `level: quick|standard`**; **legend = one line + the not-a-mechanical-guarantee caveat.**
  - "How to use it" / "dial auto-sizes" blurbs — depth-per-lens framing; be **honest that `standard` is single-pass** and the high-value second look is `thorough`'s (Slice 2).
- `.claude/agents/lens-reviewer.md` — audit-scope contract gains the **`depth` input** (`focused`/`deep`) in *Read first* + *Audit*.
- `.claude/agents/finding-verifier.md` — description: drop "Tier-1 + security" framing → "attempts to refute **any** surfaced audit finding."
- `README.md` — **line 8** and **line 19** verification copy (verbatim replacements in the Spec) — scope → "every finding it surfaces," **kill "arrive with proof"/"carry their proof,"** fold a short caveat into line 19; **line 21** must stay immediately after line 19, unweakened.
- `.claude-plugin/plugin.json` — **version bump 0.1.3 → 0.1.4.**
- `docs/ARCHITECTURE_TREE.md` — refresh the `skills/audit/SKILL.md`, `lens-reviewer.md`, `finding-verifier.md` one-liners.
- `docs/DECISIONS.md` — append: the streamlined FIND→PRUNE→VERIFY dial + depth-per-lens; **universal re-check SUPERSEDES** the *Trust & correctness core* Tier-1+security scoping **and** the *Audit right-sizing* deferred sub-items; loop-until-dry retired (with the honest recall caveat); the **verb discipline** ("attempt to re-check"); one shared cap.
- `docs/ROADMAP.md` — add the new **standards-catalog-curation** NEXT item; note the "standard verifies deterministic-labeled" sub-item is **subsumed**.

**Slice 2 — `thorough`'s differentiators + flip live:**
- `.claude/agents/blindspot-reviewer.md` — **NEW** (name open to review): read-only adversarial cross-cutting finder for the diverse sweep; returns findings to the orchestrator's synthesis exactly like `lens-reviewer` (synthesis/dedup/verify path unchanged); always `deep`.
- `skills/audit/SKILL.md` — flip `thorough` **live**: wire the diverse-sweep batch (step 4/6) + the adversarial `yagni-sentinel` prune (step 7); status block `level:` adds `|thorough`.
- `.claude-plugin/plugin.json` — add the new agent to `agents[]`; **version bump 0.1.4 → 0.1.5.**
- `docs/ARCHITECTURE_TREE.md` — add the new agent line.
- `docs/WORKFLOW.md` — add the new agent to the "Roles — a library" roster (Stage 0).
- `README.md` — line ~71 "**7** specialist agents" → **8** + name the new role.
- `docs/DECISIONS.md` — append: the new agent + its SRP rationale; `thorough` live.
- `docs/ROADMAP.md` — mark Next #2 **DONE** (with commit refs).

## Risks & mitigations

- **Depth-per-lens reads fuzzy.** → Made concrete (the two `depth` instructions above, tied to investigation depth, not a new confidence axis). Honest contract names the trade ("clear issues fast" vs "digs for subtle").
- **Retiring loop-until-dry lowers `standard` recall** (a fresh round-2 lens *can* surface what round-1 missed — "dedups to nothing" ≠ "yields nothing new"). → **Surface it honestly, don't paper over it:** the skill states plainly that `standard` is single-pass and the high-value second look lives in `thorough`; the DECISIONS entry carries the recall caveat on the durable record. Soften any "breadth is where coverage lives" assertion to an honest trade-off.
- **Universal verification over-claims** (the honesty pass's three blocking finds). → One discipline closes all: anywhere scope is stated to a human (README 8/19, the run-report, the collapsed legend), say the audit **attempts** to refute every surfaced finding and **tags** the outcome — never "verifies / arrives with proof." Legend gains the not-a-mechanical-guarantee caveat. README line 21 stays adjacent + unweakened. Verbatim replacements in the Spec so the implementer can't reintroduce the over-claim.
- **Verify-all blows budget on a big repo.** → PRUNE-first shrinks the set; the shared cell-cap + `deferred` (`⚠ not yet verified`) backstop is unchanged; verifiers fan out in parallel; verify scales with *findings* (post-prune), not files.
- **Hollow `thorough` at the Slice-1 boundary** (plan-reviewer blocking). → Slice 1 keeps `thorough` **honestly deferred**; it flips live in Slice 2 the moment its differentiators exist.
- **Dangling references / missed scope phrases.** → Acceptance re-grep covers **both** retired *mechanism* terms (`loop-until-dry`, `max-rounds`) **and** retired *scope* phrases (`Tier-1 + security`, `most serious findings`) across README · SKILL · WORKFLOW · ARCHITECTURE_TREE · finding-verifier.
- **Version-stamp contract.** → Each slice that lands carries its own bump (Slice 1 → 0.1.4, Slice 2 → 0.1.5); if landed as one release, a single 0.1.4 — stated, not accidental.
- **Idempotency.** → All narration stays **conversational, never inside a `harness-audit:*` fence** (byte-identical-on-re-run). Re-asserted.

## Test strategy

The audit skill is **model-executed prose** — no unit test to add (YAGNI-clean; confirmed by the panel). Correctness is proven by:
1. **Deterministic gates green** — `python -m pytest` (47/47, unaffected) · `python scripts/check_architecture_tree.py` (green, incl. the new agent listed in `ARCHITECTURE_TREE.md` + `plugin.json` at Slice 2).
2. **Internal-consistency re-grep** — no retired *mechanism* term (`loop-until-dry`, `max-rounds`) **or** retired *scope* phrase (`Tier-1 + security`, `most serious findings`) survives where it described the old model.
3. **Honesty acceptance checks** — README 8/19 carry no "arrive/carry proof"; the legend carries the not-a-guarantee caveat; README 21 immediately follows 19, unweakened; the run-report keeps the `verified·unconfirmed·deferred` breakdown.
4. **Stage-7 Verify** — `architect-reviewer` audits the diff (`maintainability-structure` for the new agent's SRP + skill cohesion; `docs-traceability` for doc currency) + a `yagni-sentinel` diff re-check + an honesty pass on the shipped copy.

## Decomposition (slices)

Each slice lands **complete in one ≤1M-context session, no debt** — skill internally consistent, all gates green, `thorough` never hollow.

- [ ] **Slice 1 — streamlined core dial (`thorough` honestly deferred).** Rewrite `skills/audit/SKILL.md` to the uniform **FIND → PRUNE → VERIFY** pipeline with **depth-per-lens** (`quick` focused / `standard` deep), retire loop-until-dry, **attempt to re-check all surfaced findings every level**, one shared budget cap, collapse the Phase-3 display to the universal verification tag + **legend caveat**, status block (`level: quick|standard`), the **honest verb discipline** + recall honesty. Add the **`depth` input to `lens-reviewer.md`**; reword `finding-verifier.md`'s description. Fix **README lines 8/19** (+ protect 21), **bump plugin.json → 0.1.4**, append `docs/DECISIONS.md`, add the **standards-curation ROADMAP item**, refresh `ARCHITECTURE_TREE.md`. **Lands complete** because the skill works end-to-end on `quick`/`standard`, `thorough` is honestly deferred (never hollow), no dangling references, gates green.
- [ ] **Slice 2 — `thorough`'s differentiators + flip live.** Add the **blind-spot finder agent**, wire its diverse sweep into `thorough`'s FIND + the adversarial `yagni-sentinel` prune into `thorough`'s PRUNE, flip `thorough` **live** (status `level:` adds `|thorough`). Register the agent (`plugin.json` + **bump → 0.1.5**, `ARCHITECTURE_TREE.md`, `WORKFLOW.md` roster, `README.md` 7→8), final `DECISIONS.md` + mark `ROADMAP.md` #2 DONE. **Lands complete** because `thorough` now carries its real depth; SRP-clean, listed, gate-green. *(Fallback if a later review cuts the sweep: this slice narrows to the adversarial prune + roster/version housekeeping — both slices stay independently landable.)*

---

## Review  _(Stage-3 diverse critics — synthesized by the orchestrator; critics ran read-only and returned findings)_

**Verdict:** PASS *(after folding in the required changes below — all incorporated into the Approach / Affected files / Risks above).* Panel: `plan-reviewer` (CHANGES REQUIRED → addressed), `yagni-sentinel` (**PROPORTIONATE**), honesty pass (**OVERCLAIMS** → 3 blocking copy fixes addressed).

**`yagni-sentinel` — PROPORTIONATE.** "This plan deletes more than it adds." The new agent + adversarial prune are named verbatim in ROADMAP #2; retiring loop-until-dry / the uniform order / the display collapse are net deletions. Two flag-to-reconfirms, both resolved by user decision: **Tier-3 verification** kept (uniform rule; small post-prune; ROADMAP tuning-lever logged) · **standard-verifies-deterministic → universal** is an intended KISS widening (made explicit in DECISIONS as a supersession, not a silent drop). The `thorough`-higher-cap concern is **mooted** — replaced by one shared cap.

**`plan-reviewer` — required changes (all folded in):**
1. *(blocking)* **No hollow `thorough` at a slice boundary** → Slice 1 keeps it honestly deferred; Slice 2 flips it live.
2. *(should-fix)* **Name the SKILL frontmatter `description`** in Slice 1's edits (it carries "loop-until-dry") → added.
3. *(should-fix)* **Be honest about `standard`'s lost second look** → recall-honesty added to Approach/Risks + DECISIONS caveat.
4. *(should-fix)* **Version-bump placement** → each landing slice bumps (0.1.4 / 0.1.5); stated.
   *Harness-impact note accepted:* mark the universal-verify rule as **superseding** the prior Tier-1+security decision in DECISIONS — added as an acceptance item.

**Honesty pass — 3 blocking (all folded in):**
1. *(blocking)* README scope-flip kept "**arrive with proof**" → verbatim replacement that says **attempt + tag the outcome** (Spec).
2. *(blocking)* **Missed README line 8** ("most serious findings … carry their proof") → added to Affected files + the re-grep now catches scope phrases.
3. *(blocking)* **Legend collapse dropped the only non-engineer caveat** → the single legend line now **gains** "(an independent re-check by the same kind of model — a reduction of false confidence, not a mechanical guarantee)."
   *Plus should-fix:* verb discipline ("attempt to re-check," not "verify") + keep the `verified·unconfirmed·deferred` breakdown + protect README 21 adjacency → all added.

**Harness impact:** one new agent (`blindspot-reviewer`, name open) — SRP genuinely distinct from `lens-reviewer` (one-module vs space-between-modules), consistent with the `finding-verifier`-is-standalone precedent. No new STANDARD module. New ROADMAP item: standards-catalog curation for the 3-rung dial.

---

## Spec

### Slice 1 — streamlined core dial (`thorough` honestly deferred)

**In plain English (shown first at the approval gate):**
- **What this builds:** the audit gets one clean, honest shape — every level runs all the relevant quality lenses, then trims the noise, then *tries to independently disprove every finding it's about to show you* (all tiers), and only then writes your backlog. `quick` vs `standard` now differ by **how deep each lens digs** (quick = the clear issues fast; standard = digs for the subtle ones), not by skipping anything. The old "re-run the same checks until nothing new turns up" loop is removed (it mostly re-found what it already had). `thorough` stays *honestly labelled "coming next"* this slice — it goes fully live in Slice 2.
- **What "done" means for you:** running `quick` or `standard` gives the new behaviour; the backlog clearly tags each item with whether a second agent could confirm it against the code — and says, in plain words, that this re-check is a same-model sanity check, **not a mechanical guarantee**. Nothing over-claims.
- **What you're accepting (risks/trade-offs):** `standard` is now a **single deep pass** — no repeat sweep — so its recall rests on depth + breadth, and the deeper *second-angle* look is reserved for `thorough` (next slice). We judged the repeat sweep low-yield; this is stated honestly in the skill and the decision record. Re-checking *every* finding (incl. polish) is a deliberate simplicity/honesty choice over a cheaper graduated rule.

**Files & changes:**
- `skills/audit/SKILL.md` — as enumerated in *Affected files → Slice 1*. Key concrete edits:
  - **Dial (step 1):** replace the `max-rounds`/scope table with the depth-per-lens table; `thorough` = honest deferred ("runs a `standard`-depth pass; the deeper `thorough` pass — a diverse blind-spot sweep + an adversarial prune — lands in the next release"). Keep auto-dial (small→`quick`, larger→`standard`); `thorough` named-only.
  - **Retire step 6**; fold "single look per cell" into step 4; pass `depth` to each lens.
  - **Step 8 (VERIFY):** "After the prune, the orchestrator **attempts to refute every surfaced finding** (all tiers) via an independent `finding-verifier` … Tier/scope no longer gates which findings are checked." Keep the independence contract + `Refuted`/`Verified`/`Unconfirmed`/`deferred` handling. Verb: **attempt**.
  - **Step 10 run-report:** *"Independently re-checked every finding I surfaced against the code; dropped M that couldn't be confirmed — verified N · unconfirmed K · deferred J."* (count, not a list; never persist refuted).
  - **Phase 3 item format:** every item shows one verification tag; remove the verified-scope/out-of-scope split; remove the per-item confidence label from display (still emitted internally).
  - **Legend (one line):** `(checked against the code)` = a separate agent re-read the code and couldn't refute it · `(could not confirm independently — model's assertion)` = still just the model's claim · `(⚠ not yet verified — re-run to confirm)` = budget ran out before checking — **an independent re-check by the same kind of model, a reduction of false confidence, not a mechanical guarantee.**
  - **Status block:** `status: COMPLETE|PARTIAL · level: quick|standard · done-cells: […] · pending-cells: […] · date: YYYY-MM-DD`.
- `.claude/agents/lens-reviewer.md` — audit-scope *Read first* + *Audit*: "the orchestrator also passes a **`depth`** — `focused` (report the clear gaps from a direct read; don't trace deep call-chains or chase subtle/ambiguous issues) or `deep` (follow call-chains, weigh edge cases and subtle issues; report the full picture)."
- `.claude/agents/finding-verifier.md` — frontmatter `description`: "Take ONE **surfaced** audit finding … " (drop "Tier-1 + security … before it reaches the backlog" scoping → "any finding the audit is about to surface").
- `README.md`:
  - **Line 8** → *"…and **independently re-checks every finding it surfaces** — a separate agent reads the cited code and tries to *disprove* each one before it reaches your list (false alarms get dropped; each survivor is tagged with what came back — confirmed against the code, or still just the model's claim)."*
  - **Line 19** → *"The functional core is **live**: both `init` and `audit` work, and `init` installs cleanly into a fresh repo. The audit **tries to independently re-check every finding it surfaces** — a separate agent attempts to refute each one against the code, so false positives are dropped and each survivor is tagged with what came back (confirmed against the code, or still just the model's claim — never presented as proof when it isn't)."*
  - **Line 21** — unchanged; verify it remains the immediately-following sentence.
- `.claude-plugin/plugin.json` — `"version": "0.1.4"`.
- `docs/DECISIONS.md`, `docs/ARCHITECTURE_TREE.md`, `docs/ROADMAP.md` — as enumerated.

**Tests to add:** none (prose skill). **Acceptance criteria:**
1. `python -m pytest` 47/47 green; `python scripts/check_architecture_tree.py` green.
2. Re-grep finds no `loop-until-dry` / `max-rounds` / `Tier-1 + security` (as a verify scope) / `most serious findings` surviving as the old model across SKILL · README · WORKFLOW · ARCHITECTURE_TREE · finding-verifier.
3. README 8/19 contain no "arrive with proof"/"carry their proof"; the legend carries the not-a-mechanical-guarantee caveat; README 21 immediately follows 19, unweakened.
4. The skill states plainly that `standard` is single-pass and `thorough` (next) holds the second-angle look; `thorough` is honestly deferred (never presented as fully live).
5. DECISIONS records the supersession (Tier-1+security → universal) + the recall caveat + the verb discipline.

### Slice 2 — `thorough`'s differentiators + flip live

**In plain English (shown first at the approval gate):**
- **What this builds:** `thorough` becomes real. On top of `standard` it adds (1) a **fresh-angle "what did every checklist miss?" sweep** — a new reviewer that hunts cross-cutting / architectural / between-the-modules risks no single lens owns — and (2) an **independent skeptic that argues your findings down** before they're re-checked, so only the ones that matter survive. You ask for it by name; it never auto-runs.
- **What "done" means for you:** naming `thorough` runs the full deep audit **plus** those two extra adversarial passes; the backlog still tags every item honestly.
- **What you're accepting (risks/trade-offs):** `thorough` costs more (an extra reviewer pass + an extra prune); it's opt-in for exactly that reason. The new reviewer is a genuine addition to the agent library (justified: nothing else covers the space *between* lenses).

**Files & changes:** as enumerated in *Affected files → Slice 2*, **plus the refinements below** (adopted in Discuss this session — they supersede the original spec where they differ). The new `blindspot-reviewer.md` mirrors `lens-reviewer`'s read-only/return-to-synthesizer shape but its lens is "the whole scope, for what no single module owns"; same per-finding output (gap + `file:line` + confidence) so the synthesis/dedup/verify path is unchanged.

**Tests to add:** none. **Acceptance criteria:**
1. Gates green incl. the new agent listed in `ARCHITECTURE_TREE.md` + `plugin.json`.
2. `thorough` is live: **exhaustive** depth + diverse sweep + adversarial prune; status `level:` accepts `thorough`; auto-dial still never selects it.
3. `plugin.json` `0.1.5`; README says **8** agents; WORKFLOW roster + ARCHITECTURE_TREE list the new agent; ROADMAP #2 marked DONE; DECISIONS records the agent + SRP rationale.

#### Slice 2 refinements (Discuss this session — supersede the above where they differ)

1. **Depth is a 3-rung ladder, not binary.** Add a third `depth` value to `lens-reviewer.md`: **`exhaustive`** = `deep` + self-skeptical (questions its own conclusions, chases every ambiguous lead, adversarial per-dimension). `thorough`'s FIND runs **`exhaustive`** (not `deep`). So the monotonic ladder is `focused`(quick) → `deep`(standard) → `exhaustive`(thorough), and the blind-spot sweep + adversarial prune come *on top* at `thorough`.
2. **Frame the dial section as ONE thoroughness slider, three stage-responses** — not three separate pipelines. Rewrite the SKILL dial copy so it reads: one slider; FIND responds by depth (skim→deep→exhaustive, and at the top also steps back for the cross-cutting sweep); PRUNE responds by who cuts (self-review → independent skeptic at the top); **VERIFY is flat at every notch (the honesty floor — every surfaced finding re-checked, even on `quick`).** The sweep and adversarial prune are "what FIND and PRUNE look like at max," not bolt-ons.
3. **Honest about *where* depth saves.** Each lens already targets its reads via `ARCHITECTURE_TREE.md` (not whole-repo); depth trims the *variable* cost (call-chain chasing across files + reasoning), so `quick` is genuinely lighter but its biggest wins are on **small repos** (where it's auto-picked) and on **triage noise** (fewer, clearer findings) — not a dramatic big-repo token cut. The dial copy must not over-claim `quick` as "much cheaper everywhere."
4. **Design `blindspot-reviewer` to be REUSABLE, not audit-only.** Build the Audit-scope posture now (always `exhaustive`), but write it so it **generalizes to a Verify-diff mode later** (mirroring `lens-reviewer`'s two-mode shape) — its job ("what does the per-lens view miss?") is just as valid on a slice's diff. Don't build the diff mode now (YAGNI) — ROADMAP it.
5. **ROADMAP additions at land** (append, don't bloat this slice): (a) **read-once / group-lenses-by-shared-read**, *capped by per-reader context* (group only where the shared read fits one agent; split huge backends across readers) — a modest efficiency win, since tree-targeting already trims reads; (b) **wire `blindspot-reviewer` into the dev-workflow Stage-7 Verify** (give it a Verify-diff mode); (c) a **streamlining review of the dev workflow itself** (apply these lessons — FIND→PRUNE→VERIFY discipline, depth-dial, diverse critics, honesty verb discipline — to the Stage 1–9 pipeline + roles). The "two dials stay two" decision (audit→backlog vs Verify→pass/fail gate; shared agent library) is recorded in DECISIONS.
