# 0020 — Harness distillation & the doc-discipline ratchet

- **Status:** Implemented + Verify-panel SOUND (architect PASS; honesty over-claim fixed → CLEAN) — all gates + 116 pytest + 344 node green; at the before-land checkpoint on branch `harness-distillation`
- **Resumable from:** awaiting user "go" to commit the ruler to the branch → then plan 0021 (cleanup)
- **Blockers:** none
- **Roadmap item:** Harness distillation & doc-discipline ratchet (this plan is the roadmap for the effort)
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · `docs/claugentic-WORKFLOW.md` · the 2026-06-17 take-stock diagnostic (6-dimension, adversarially verified)

## Problem

A maturation push (strict self-reference, the `claugentic-` rename, mature-repo install) left sediment, and a verified diagnostic surfaced one **confirmed** structural failure plus a cluster of small gaps:

- **The flagship context-economy artifact bloated.** `docs/claugentic-ARCHITECTURE_TREE.md` is ~50.7K chars (~13K tokens), read first every session. 16 of 79 entries exceed 800 chars, 4 exceed 3000 (worst: `engine/build-item.js` at 4,452 — ~1,100 tokens for **one** index entry). Its own header says "one-line-per-file index." **Confirmed** by independent re-measurement (`docs/claugentic-ARCHITECTURE_TREE.md:88,86,89,79`).
- **Root cause, confirmed against the gate code:** `scripts/claugentic-check_architecture_tree.py:4-9` enforces PRESENCE + STALENESS + GLOB-DRIFT only — "*Descriptions are authored by humans/agents — this script does not write them.*" Entry **form/length was the one managed property left at the model-upheld (prose) altitude**, and model-upheld properties drift. This is the harness's own thesis (only deterministic gates hold; per `harness-honesty-positioning` memory + `docs/claugentic-DECISIONS.md:7`) playing out on the harness itself.
- **No shrink mechanism** for any monotonic ledger (tree, `DECISIONS.md` ~31K, `ROADMAP.md`) — they only grow.
- A long tail of verified small gaps (de-sediment, skill distillation, flow handoffs, the hints-file slot, mechanism upgrades, consumer-doc honesty) — catalogued in §Phase 1+.

The diagnostic's adversarial verifier downgraded every overstated "high" and **refuted** one (the "CLAUDE.md honesty headline is stale" finding — `scripts/check_versions_synced.py` is a *deterministic run-gate*, distinct from the *hook-enforced* tree gate; CLAUDE.md L3 is correct as written). Net evidence: the system is fundamentally sound → **distill, do not rebuild** (user-confirmed 2026-06-17).

## Goals / Non-goals

- **Goal:** Convert ledger **form/size discipline from model-upheld → deterministic**, so the tree (and the other ledgers) **physically cannot rebloat**. "Fix the ruler before measuring with it."
- **Goal:** Regenerate the tree to standard — roughly halve the most-loaded artifact (~50.7K → ~25K chars; **~6–10K tokens** reclaimed per session, budget-dependent).
- **Goal:** A reusable **monotonic-doc compaction** trip-wire for tree / DECISIONS / ROADMAP.
- **Goal (later phases):** Land the verified de-sediment / distillation / flow-gap / mechanism-upgrade backlog, organized by a dogfooded product spec.
- **Non-goal:** Mechanically enforcing description *quality* or semantic SRP-bleed — those stay model-upheld and reviewer-caught (honesty-reviewer / yagni-sentinel at Verify). The gate enforces *form*, not *prose quality*.
- **Non-goal:** Any per-tool-call enforcement overhead. Form/size/compaction live at the **CI/Land checkpoint altitude**, never per-finger-move. The only per-Write hook stays the existing quiet coverage nudge.
- **Non-goal (this plan):** Rebuilding any engine code; touching the cross-script-pinned helper blocks; changing CLAUDE.md L3's substance.

## Approach

**Enforcement-altitude principle (governs every choice here):** match each property to the *cheapest primitive that holds it*. Coverage/staleness → the existing quiet per-Write hook. **Form/size/compaction → a deterministic gate at CI/Land** (occasional, milliseconds, zero steady-state cost). Description *quality* → model-upheld, surfaced + reviewer-caught.

**Phase 0 — Fix the ruler (this plan's detailed scope):**
1. Extend the tree gate with a deterministic **per-entry form budget**, `MAX_ENTRY_CHARS = 450` (configurable). **Derivation (from measured data):** the bloat is *concentrated* — across the 79 entries the median is 291 and mean 617, but the top 4 alone are ~15K chars (~30% of the file); a ~450 budget forces the ~14 genuinely-bloated entries (the 800–4452 outliers) down hard while sparing the ~27 sound 250–350-char one-sentence descriptions of genuinely complex files. A 220 budget would churn 70% of the index (55/79 entries) and rewrite good one-liners — **rejected**. **Standing-decision reconciliation (`docs/claugentic-DECISIONS.md:14` — "new mechanically-checkable invariants get a sibling script, not an extension"):** entry *form* is **the same index-wellformedness invariant the tree-check already owns** (it already parses every entry for presence/staleness) — a scoped refinement, not a new invariant — so extending the tree gate is correct here; `check_doc_budgets.py` is a *genuinely different* invariant set across 3 docs, so it is correctly the sibling. A4 records this as a scoped refinement of `:14`, not a silent override. Alternatives rejected: a separate tree-form script (re-parses the same structure — DRY violation); the per-Write hook (wrong altitude — would nag mid-edit).
2. New table-driven **`scripts/check_doc_budgets.py`** for CLAUDE / DECISIONS / ROADMAP size+entry budgets, CI-run. Justified shared module (3+ consumers — the harness's own "extract on 2nd consumer" rule). Alternative rejected: bespoke per-file checks (not DRY).
3. **Regenerate the tree to standard** — every entry to one budgeted line; genuinely useful mechanism detail relocates to each file's own header docstring (read-on-open, not read-every-session). Index-don't-duplicate, applied to the index itself.
4. **Documented model-upheld halves**: scoped single-line regen on a flag; bounded compaction pass on a trip. Start flag-and-suggest; earn automation later (YAGNI).

**Phase 1+ (outline; each gets its own plan/spec when reached):** dogfood `product` spec mode for a north-star spec, fold the diagnostic into one backlog, work it tier by tier.

## Affected files (Phase 0)

- `scripts/claugentic-check_architecture_tree.py` — add per-entry form-budget check. **Entry-line predicate (pinned):** run AFTER `_strip_fenced_blocks` (the AskBase regression, `:136-157`); an entry is a line matching `^\s*- ` whose **first backtick token is path-shaped** (contains `/` or `.`) — anchored on the backtick-bullet shape, NOT "any list item" and NOT "any long line". The two prose lines (`:5` blurb, `:112` eval-intro) and any fenced-block line are exempt by construction. New `MAX_ENTRY_CHARS` constant; fail-loud listing offenders + lengths. Presence/staleness/drift untouched.
- `scripts/check_doc_budgets.py` — **new.** Table-driven `DOC_BUDGETS` (max bytes / max entries / per-item char budget per ledger); independent fail-loud reads; names the remediation action.
- `tests/test_check_architecture_tree.py` — characterization for the form check (over/at/under budget; prose lines exempt; existing checks unaffected).
- `tests/test_check_doc_budgets.py` — **new.** Hermetic tmp_path budgets (under/over/missing/garbled, independent reads).
- `docs/claugentic-ARCHITECTURE_TREE.md` — regenerated to standard (≤ budget per entry; new script entry added within budget).
- `.github/workflows/ci.yml` — add `check_doc_budgets.py` to the `gates` job.
- `CLAUDE.md` + `docs/claugentic-WORKFLOW.md` (DoD) — name the new deterministic gates, **preserving the honesty taxonomy** (tree-form = part of the hook-wired tree gate; doc-budgets = a CI run-gate like version-sync — mirror the precedent the verifier defended).
- `docs/claugentic-DECISIONS.md` — dated entry: form/size discipline moved to the deterministic altitude; the altitude principle.
- Engine/script file headers — receive the mechanism detail relocated out of the tree (paired with Slice A3).

## Research / grounding

- **Files reviewed:** `scripts/claugentic-check_architecture_tree.py:1-413` (full — confirmed presence/staleness/drift only, no form check); `docs/claugentic-ARCHITECTURE_TREE.md:1-128` (the bloat, measured); `.claude/plans/TEMPLATE.md:1-56` (template structure + its own stale-path defect, lines 6/7/24); the verified diagnostic (34 findings, 6 dimensions).
- **Harness docs consulted:** `docs/claugentic-DECISIONS.md:7` (honesty positioning — only the tree gate is hook-enforced; version-sync + tests are deterministic run-gates) · `docs/claugentic-WORKFLOW.md` DoD/gate taxonomy · `harness-honesty-positioning` + `harness-holistic-review-2026-06` memories.
- **Findings:** the tree gate already tokenizes entries (`_backtick_tokens`) → form-budget is a cheap extension, not a new parser. `check_versions_synced.py` is the exact template for a table-driven, independent-read, fail-loud CI run-gate. The cross-script-pinned helper blocks (`tests/workflows/cross-script.test.mjs`) must **not** be touched. The honesty taxonomy (hook-enforced vs deterministic-run-gate) is load-bearing and must be preserved in the DoD wording.

## Risks & mitigations

- **Budget too tight / too loose** → `MAX_ENTRY_CHARS = 450`, derived from the measured distribution (§Approach): targets the ~14 concentrated outliers, spares sound one-sentence entries. Single configurable constant; genuinely complex detail moves to the file's own header, not the index. Form ≠ quality.
- **Regen loses navigation-useful info** → relocate detail to file headers (don't delete); acceptance test = "can an agent still locate the right file from the one-liner?" Spot-checked across the 4 worst entries.
- **CI gates-job change breaks the pipeline** → characterization tests + local run before land; the new gate is additive (new step), version-sync/tree untouched.
- **Wording the new gates could over-claim mechanical enforcement** → honesty-reviewer in-scope at Verify; preserve the hook-enforced-vs-run-gate distinction verbatim in spirit (the verifier just defended it).
- **Scope creep into Phase 1+** → Phase 0 is the ruler only; everything else is explicitly deferred to its own plan.

## Test strategy

Deterministic, hermetic, CI-run. Tree-form: extend the existing characterization suite (over/at/under the 450 budget; the two prose lines `:5`/`:112` must NOT trip; a fenced ASCII-diagram long line must NOT trip — gate runs after `_strip_fenced_blocks`; a `- `-bullet whose first backtick token is not path-shaped must NOT trip; presence+staleness regression-guarded). Doc-budgets: new suite mirroring `test_check_versions_synced.py` (under/over/missing/garbled per file; independent reads; `main()` exit codes). Acceptance for A3: the form gate passes on the regenerated tree, total ~25K chars (from 50.7K), zero files unindexed.

## Decomposition (slices)

Phase 0 — each lands complete in one session, no debt:

- [x] **Slice A1 — Tree form-gate.** `MAX_ENTRY_CHARS = 450` + the pinned backtick-bullet entry predicate (post-`_strip_fenced_blocks`; prose-line `:5`/`:112` + fenced-block + non-path-bullet exemptions as named regression tests) + fail-loud; characterization tests. Lands complete: deterministic, self-contained, presence/staleness untouched. *(Independent of A2.)*
- [x] **Slice A2 — Doc-budget gate.** `scripts/check_doc_budgets.py` (table-driven, independent reads) + tests + CI wiring. Lands complete: a standalone run-gate on the `version-sync` template. *(Independent of A1.)*
- [x] **Slice A3 — Regenerate the tree to standard.** Rewrite the **~14 over-budget entries** (the 800–4452 outliers) to one ≤450-char line; relocate the genuinely-useful mechanism detail to each file's own header docstring. **Also fix the factual count at `:9`** (the README entry's "three commands: init · audit · build" → "four", incl. `product`) — under-budget so the regen won't auto-trigger it, but A3 owns all tree edits. Lands complete: A1 gate passes, ~half the file reclaimed (~6–10K tokens). *(Depends on A1 — needs the defined budget.)*
- [x] **Slice A4 — Procedures + DoD + DECISIONS.** Document scoped-regen-on-flag + compaction-on-trip (**flag-and-suggest only — no automation this pass**). Name the new gates in CLAUDE.md/WORKFLOW DoD with the honesty taxonomy as a **hard acceptance criterion** (tree-form inherits **hook-enforcement** inside the tree gate; `check_doc_budgets.py` is a **CI run-gate like `check_versions_synced.py`** — NOT hook-wired; copy must not blur "two deterministic gates" into "two hook-enforced gates"). DECISIONS entries: the enforcement-altitude principle + the scoped refinement of `:14`. Tree gains the new script's (budgeted) entry. **honesty-reviewer in-scope at A4 Verify.** *(Depends on A1+A2+A3.)*

A1 and A2 are parallelizable. Sequencing within the session: (A1 ∥ A2) → A3 → A4.

## Phase 1+ — outline (own plan/spec when reached; ordered after Phase 0)

- **P1 — Product-spec spine.** Dogfood `/claugentic-dev-harness:product` spec mode → north-star spec; then gap mode; fold the diagnostic into one backlog.
- **P2 — De-sediment (WS-B).** `TEMPLATE.md` 4 stale paths; delete empty `workflows/`; bare `ARCHITECTURE_TREE` shorthand ×2; add "locate via tree" to `engine/verify.js` + `engine/audit.js` lens prompts; reconcile 3-vs-4 commands; pin the cross-model paragraph with a grep test (don't dedupe).
- **P3 — Distill heavy skills (WS-C).** `init` idempotency recap → pointer (~3K tokens/init); `build` cross-model restatement → pointer; test/eval tree entries → category one-liners.
- **P4 — Close flow gaps (WS-D).** product handoffs (init Next, spec-mode close-out, build close-out); **Retrospect fires + is visible at Land**; "I disagree with a finding" rejected-memory fence (mirror product's); resume-after-interruption user note for audit/product; uninstall/disable note; `CANDIDATES.md` create-on-first-use affordance.
- **P5 — Hints-file: ADAPT (WS-E).** Bless the CLAUDE.md per-repo harness block as the durable structural/domain-context home (model-upheld, un-enforced, never authoritative). No fixed data-hints schema.
- **P6 — Mechanism upgrades (WS-F).** `PreToolUse` irreversible-guard (model-upheld → mechanical, e.g. push-to-main); `SessionStart` advisor/status surface (derive-don't-store; the "what's next" + cross-model-tag + in-flight-resume surfacing); context-budget-aware dial. *(Each confirmed against the live hooks API at spec time.)*
- **P7 — Consumer-doc honesty (WS-G).** README surfaces the Workflow-tool dependency honestly (NOT "Requires Node"); install self-check line; install-scope/team-distribution explanation.

---

## Review  _(filled by plan-reviewer, Stage 3)_

**RUNNING AS:** Opus 4.x (cross-model protocol: self-identified family — if the builder is also an Opus-family model, treat this as a same-model review on this run, the judge and the builder are the same model family here).

- **Verdict:** `CHANGES REQUIRED` — the approach is sound and the enforcement-altitude principle is correct, but three issues must be fixed in the plan before Spec: (1) an unaddressed conflict with a standing DECISIONS rule, (2) a budget value that is mathematically untenable against the real data, and (3) a missing entry-line-detection edge case. The verdict is close to PASS; these are tightenings, not a redesign.

### Required changes (numbered, actionable)

1. **Resolve the `sibling-script-not-extension` conflict head-on (Slice A1).** `docs/claugentic-DECISIONS.md:14` is a *standing* decision: *"the tree-check owns the file index (presence · staleness · zero-coverage glob-drift) … New mechanically-checkable invariants get a sibling script, not an extension."* Slice A1 **extends** the tree gate. The plan's DRY justification (L35: "the tree gate already tokenizes entries") is reasonable but **does not cite or reconcile the decision it contradicts** — and CLAUDE.md mandates consulting DECISIONS before re-litigating. Fix: in §Approach add one explicit sentence arguing entry-**form** is *part of the same index invariant the tree-check already owns* (well-formedness of the index it presence/staleness-checks), **not** a new invariant — therefore the sibling-script rule does not apply, and `check_doc_budgets.py` (a genuinely *different* invariant set across 3 docs) is correctly the sibling. Then A4's DECISIONS entry must record this as a scoped refinement of L14, not a silent override. Without this the plan trips the harness's own re-litigation guard.

2. **`MAX_ENTRY_CHARS ~220` is untenable against the real tree — re-derive it from measured data (Slices A1+A3).** Measured: 79 entry lines, median **291**, mean **617**; **only 24 of 79 (30%) are already ≤220**; **55 of 79 exceed 220**. A 220 budget does not "regenerate the 4 worst entries" — it forces a **rewrite of 70% of the index in one slice**, and many of the 221–400 entries (27 of them) are legitimate one-sentence descriptions of genuinely complex files (`engine/build-item.js`, `skills/build/SKILL.md`). 220 chars is "one short sentence"; these files need one *dense* sentence. Pick a budget that (a) forces the 14 over-800 and 4 over-3000 outliers down hard while (b) not gratuitously churning sound 250–350-char entries. A budget around **~400–500** still reclaims the ~9–12K tokens the goal targets (the bloat is concentrated: the top 4 entries alone are ~15K chars / ~30% of the file) while keeping A3 a focused rewrite of the ~14 real offenders, not a 55-entry mass-edit. State the chosen number **and its derivation** in §Approach; if 220 is kept deliberately, the plan must own that A3 is a full-index rewrite and re-justify A3's single-session sizing against that. As written, A3's "rewrite every over-budget entry" + "~9–12K reclaimed" silently assumes a small offender set that a 220 budget contradicts.

3. **Specify entry-line detection precisely + add the two prose-line exemptions as named test cases (Slice A1).** Verified against the real file: every index entry is a **single physical line** matching `^\s*- ` followed by a backtick (`` - `path` — … ``); the only two non-entry, non-heading, non-blank lines are the top blurb (`:5`) and the eval-section intro (`:112`), **neither of which starts with `` - ` ``**. So the detection rule is robust *iff* it is **anchored on the `` - ` ``-bullet-with-leading-backtick shape, not "any list item" and not "any long line."** The plan says "entry-line detection" and "prose/section lines exempt" but never pins the rule. Fix: §Affected-files + the A1 test list must name (a) the exact predicate (line, post-`_strip_fenced_blocks`, matching the backtick-bullet shape), (b) explicit exemption + regression tests for both `:5` and `:112` prose lines (a future long prose paragraph must NOT trip the gate), and (c) a fenced-block exemption test — the gate must run **after** `_strip_fenced_blocks` (the AskBase regression, `claugentic-check_architecture_tree.py:136-157`), or an adopter's ASCII-diagram line could false-trip. Note a `- `-bullet that *isn't* an entry (a prose bullet starting with a backtick'd word) is a theoretical false-positive — accept it explicitly or require the backtick to be immediately followed by a path-shaped token.

4. **Lock the honesty-taxonomy wording for the new gates as a hard acceptance criterion, not a risk note (Slice A4).** The plan correctly flags this (L50, L65) but leaves it as a mitigation. Make it an A4 **acceptance criterion**: tree-form is enforced inside the **hook-wired** tree gate (so it inherits hook-enforcement — the *one* hook-enforced gate per `DECISIONS.md:7`), whereas `check_doc_budgets.py` is a **CI run-gate like `check_versions_synced.py`** (mechanical-when-run, running-it-is-discipline, **not** hook-wired). The CLAUDE.md/WORKFLOW-DoD copy must say exactly that and must not let "two new deterministic gates" blur into "two new hook-enforced gates." This is the taxonomy the diagnostic's verifier *defended* (refuted the stale-honesty-headline finding precisely on this distinction) — A4 regressing it would be the over-claim the harness forbids. Require honesty-reviewer in the A4 Verify panel (trust-surface).

### Sizing/completeness check (per slice)

- **A1 — Tree form-gate.** OK as a unit *once #1 and #3 land*. Self-contained, deterministic, characterization-testable, presence/staleness untouched. Independent of A2 — correct.
- **A2 — Doc-budget gate.** OK. `check_versions_synced.py` is an exact, proven template (independent reads, fail-loud, `main()` exit codes, hermetic tmp_path tests). The table-driven `DOC_BUDGETS` clears YAGNI: **3 real consumers** (CLAUDE.md, DECISIONS, ROADMAP) = the harness's own "extract on 2nd consumer" rule, not speculation. Independent of A1 — correct.
- **A3 — Regenerate the tree.** **Split-risk, budget-dependent.** At `~220` this is a 55-entry rewrite — too big to land clean *and* risks navigation-info loss across the whole index in one session (the "can an agent still locate the file?" acceptance test is spot-checked on only 4 entries per L63, but 55 would change). At a measured `~400–500` budget (#2) it collapses to ~14 real offenders + the paired file-header relocations — **then A3 is correctly single-session.** Sizing verdict is *contingent on #2*; resolve the budget and A3 is OK, otherwise split A3 into "top-4 outliers" + "remaining over-budget."
- **A4 — Procedures + DoD + DECISIONS.** OK, with #1 and #4 folded in. One caveat: A4 touches CLAUDE.md, WORKFLOW DoD, DECISIONS, the tree (new script entry), **and** documents the model-upheld halves — verify this stays one session; it is mostly prose and should, but it is the densest slice. The `flag-and-suggest first, automate later` restraint is the **right** YAGNI call — do **not** build scoped-regen/compaction automation this pass (no proven 2nd trigger yet).
- **Dependency order `(A1 ∥ A2) → A3 → A4`** is correct: A3 needs A1's budget constant; A4 needs all three. No missing Phase-0 slice — the de-sediment/distillation tail is correctly deferred to Phase 1+ (P2–P7), not smuggled into A4.

### Harness impact

- **STANDARD/gate:** Two new deterministic checks named in CLAUDE.md + WORKFLOW DoD (#4) — this is a genuine Stage-9 harness change; the DoD gate list grows by one CI run-gate (`check_doc_budgets.py`) and the tree gate gains a sub-check. Record the **enforcement-altitude principle** as a new `DECISIONS.md` entry (it is a reusable rule, not a one-off).
- **Must NOT touch:** the cross-script-pinned helper blocks (`MODELS`/`SAME_MODEL_TAG`/`UNRESOLVED_FAMILY_TAG`/`KNOWN_FAMILIES`/`modelFamily`/`sameModelTag`/`nsAgent`/`parseArgs`) pinned by `tests/workflows/cross-script.test.mjs:107` — Phase 0 has no reason to, and the plan correctly says so (L58). Confirmed: none of A1–A4's files overlap those blocks.
- **No new agent** needed. honesty-reviewer (existing) must be in-scope at A4 Verify (#4); that is a trigger-application, not a new role.
- **Over-claim watch:** the only harness-honesty risk is #4's wording; everything else (quality stays model-upheld, no per-tool-call overhead) is consistent with `DECISIONS.md:7-17`.

---

## Spec — Phase 0  _(Stage 4; plan-reviewer changes #1–#4 incorporated)_

### Slice A1 — Tree form-gate
- **In plain English:** the tree-check gains one rule — each file's index entry must be ≤ 450 characters. If an entry balloons into a paragraph, the gate fails loud and names it with its length. This is the ratchet that makes the bloat physically unable to return. You're accepting a deterministic length budget (450, tunable) — not any judgment on description *quality*.
- **Files & changes:** `scripts/claugentic-check_architecture_tree.py` — add `MAX_ENTRY_CHARS = 450`; a pure `_form_violations(text)` helper that, on the already-`_strip_fenced_blocks`'d text, flags each entry line (`^\s*- ` whose first backtick token is path-shaped) longer than the budget; fold its output into `evaluate()`'s problem list as a new "entries EXCEED the one-line budget (≤450)" block (`name — N chars`). Presence/staleness/drift logic unchanged.
- **Tests (`tests/test_check_architecture_tree.py`):** over-budget entry → flagged with length · at/under → clean · the `:5` blurb + `:112` eval-intro prose lines (long) → NOT flagged · a fenced ASCII-diagram long line → NOT flagged (post-strip) · a `- `-bullet whose token isn't path-shaped → NOT flagged · presence/staleness regression-green.
- **Acceptance:** fails on a synthetic over-budget tree, passes on a compliant one; all existing tree-gate tests green; `MAX_ENTRY_CHARS` is the single source of the budget.

### Slice A2 — Doc-budget gate
- **In plain English:** a new no-LLM check (run in CI, like the version-sync check) that flags when CLAUDE.md / DECISIONS / ROADMAP grow past a sane size and tells you to run a curation pass. It never edits — it flags. You're accepting a CI run-gate (not hook-wired) with tunable table-driven budgets.
- **Files & changes:**
  - `scripts/check_doc_budgets.py` (new): `DOC_BUDGETS = {"CLAUDE.md": {"max_bytes": 6000}, "docs/claugentic-DECISIONS.md": {"max_bytes": 40000}, "docs/claugentic-ROADMAP.md": {"max_bytes": 12000}}` — **total-bytes for all three** (a per-item char gate would wrongly flag legitimate deferred-but-unplanned ROADMAP detail; the "1-liner + plan-file once an item is planned" rule stays a model-upheld convention, not a gate). Independent fail-loud reads (one oversize/broken file can't mask another); each breach prints file + measured-vs-budget + the named remediation ("run a compaction pass; merge superseded → git history"); `main()` exits 1 on any breach. Built on the `check_versions_synced.py` shape.
  - `.github/workflows/ci.yml`: add `python scripts/check_doc_budgets.py` to the `gates` job.
- **Tests (`tests/test_check_doc_budgets.py`, new):** under/at/over per rule type (bytes + per-item chars) · missing file → fail-loud · garbled/unreadable → fail-loud · independent reads (two breaches both reported) · `main()` exit codes. Hermetic tmp_path + monkeypatched path constants.
- **Acceptance:** green on the current repo (CLAUDE.md 3.2K<6K · DECISIONS 31K<40K · ROADMAP ~5K<12K) · red on a synthetic oversize fixture · CI runs it.

### Slice A3 — Regenerate the tree to standard
- **In plain English:** rewrite the ~14 bloated entries down to one tight line each, moving genuinely-useful detail into each file's own header where it's read only when the file is opened. Reclaims ~6–10K tokens on the file every agent reads first. You're accepting denser index entries and detail relocated (not deleted).
- **Files & changes:** `docs/claugentic-ARCHITECTURE_TREE.md` — every entry ≤450 chars (role + primary collaborators + pointer); the relocated mechanism detail lands in the corresponding `engine/*.js` / `scripts/*.py` file-header docstrings (paired edits); **plus the `:9` factual fix (three→four commands, incl. `product`).** No file dropped from the index.
- **Tests:** A1 form-gate passes on the regenerated tree · presence still passes (no file unindexed) · manual spot-check on the 4 worst former entries — "can an agent locate the right file from the one-liner?"
- **Acceptance:** A1 gate green · total tree ~25K chars (from 50.7K) · no navigation-needed info lost (spot-checked) · relocated detail present in the file headers.

### Slice A4 — Procedures, DoD wiring, DECISIONS
- **In plain English:** document the two model-upheld halves (regenerate one line when flagged; run a bounded curation pass when a ledger trips — flag-and-suggest only, no automation yet), and update the project's own rules to name the new gates **honestly** — crystal clear on which is hook-enforced vs CI-run. You're accepting doc/process changes only; no new automation.
- **Files & changes:**
  - `CLAUDE.md` + `docs/claugentic-WORKFLOW.md` (DoD gate list): name (a) the tree gate's new form sub-check (inherits **hook-enforcement**) and (b) `check_doc_budgets.py` (a **CI run-gate like version-sync**, NOT hook-wired). Wording must not blur the two.
  - `docs/claugentic-DECISIONS.md`: dated entries — the **enforcement-altitude principle** (reusable rule) and the **scoped refinement of `:14`** (entry-form extends the tree gate; doc-budgets is the sibling).
  - `docs/claugentic-ARCHITECTURE_TREE.md`: add (budgeted) entries for `scripts/check_doc_budgets.py` + `tests/test_check_doc_budgets.py`.
  - Document the scoped-regen + compaction procedures (CLAUDE.md → Harness Discipline / WORKFLOW).
- **Verify panel (in-scope dimensions):** maintainability-structure (SRP/DRY of the gates) · docs-traceability (the tree IS the traceability artifact) · testing · **honesty-reviewer** (DoD copy is a trust surface — must not over-claim hook-enforcement).
- **Acceptance:** DoD names both gates with the correct taxonomy (honesty-reviewer CLEAN) · DECISIONS records both entries · tree lists the new files within budget · all gates + tests green.

### Audit deltas folded into A4 (confirmed 2026-06-17)
- DECISIONS also records the **~14 journey/SRP-audit over-engineering rejections** (the boundary, so they're not re-litigated): don't split init / audit.js · don't collapse the cross-script helper (the copy is correct under the no-imports sandbox) · don't merge/split agents · no commit-on-red land-gate · no Verify-stage split · no onboarding-wizard / `/update`-command / per-teammate-config / resume-store.
- DoD wording gains **adopter self-labelling**: version-sync + the tree gate are the harness's own self-tests — adopters substitute their equivalents (ADOPT-3/6).
- Tree-Stop-hook altitude (WFFIT-2): **keep as-is** (cheap subprocess, zero model-context cost); roadmap option = migrate to a bundled hook later.
