# 0044 — The leanness pass, eval-gated

- **Status:** Draft
- **Resumable from:** Stage 2b advisory panel on the refined draft (Slice-1 design folded in) → Stage 3 review.
- **Blockers:** none
- **Flags:** none
- **Disposition at close:** per `docs/claugentic-WORKFLOW.md` → Plan file lifecycle.
- **Roadmap item:** none (owner-directed arc, 2026-08-20 handover prompt; the three user answers below are its charter)
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · plan 0041 (thinning precedent, git history) · `eval/BASELINE.md`

## The user's binding answers (2026-08-20)

1. **v0.5.4 tagged and published first** — DONE (Release live 17:28:35Z, `release`=`08faae2`). The pass runs on a released base.
2. **Skills cut = FULL APPETITE** — breaking, adopter-visible changes allowed; version accordingly (next release **0.6.0**).
3. **BUILD-path eval FIRST** — it must exist and have a baseline before the standards second pass; the cut is gated on its result.

## Problem

The harness is 0.74 MB of shipped prose+code after the −28% thinning. The names-only ablation (2026-08-20, `eval/BASELINE.md`) proved the standards catalog's *audit* product is **boundaries + enumeration, not knowledge** — recall held 10/10 with the catalog deleted. But that measured **detection only**. The catalog is also the implementer's authoring checklist (`.claude/agents/implementer.md` — "the catalog is an authoring checklist, not only a review checklist"), and **output quality — the owner's actual goal — is asserted, not measured**: five of six skills have no eval at all. Meanwhile the corpus carries measurable slack: agents doing the same job class span 8× (yagni-sentinel 3,066 B vs synthesizer-gate 24,505 B, both untested), skills are 200 KB (init 80.5 KB), standards 130 KB against a ~60 KB target, WORKFLOW 62.8 KB under a 77.5 KB cap.

North star (falsifiable, `docs/claugentic-PRODUCT_SPEC.md` → Why this exists): every byte is **team-function or compensation**; compensations are deleted, not tuned. As models improve the harness gets thinner.

## Goals / Non-goals

- **Goal 1:** a build-path eval measuring the implement path's output-quality sensitivity to the standards catalog — cheap enough to re-run as a per-release drift check, honest about small-N noise.
- **Goal 2:** standards second pass 130K → ~60K, **gated on Goal 1's measured verdict** — keeping dimension enumeration, un-inferable thresholds, incidents, `[D]`/`[J]` tags, output contracts.
- **Goal 3:** agent-bytes ablation (synthesizer-gate vs the yagni-sentinel 3K existence proof), then cut the roster's bytes keeping every posture, mode list and output contract.
- **Goal 4:** skills cut at full appetite (breaking allowed → 0.6.0) — contracts inventoried before cutting; narration and compensation deleted.
- **Goal 5:** WORKFLOW re-cut; lower its cap as it shrinks (cap change updates the byte-pinned test in the same commit).
- **Non-goal:** measuring all six skills' output quality — the eval targets the implement path; extensions are one roadmap line, not built (YAGNI).
- **Non-goal:** any new harness feature, and any re-proposal of a `docs/claugentic-PRODUCT_SPEC.md` → Deliberate non-goal (the bar is evidence, never argument).
- **Non-goal:** cutting the bones (plan → review → spec → approve → implement → verify → land) or the FRAME ceremony — owner-valued structure, already effort-dialled.
- **Non-goal (hard rule):** compressing away any mechanical-vs-model-upheld distinction — that inverts the product's one invariant.

## Approach

Eval-first sequencing per the user's answers. Slice 1 builds the measurement instrument (design synthesized by a 3-design/3-judge/1-synthesis panel, 2026-08-20 — folded in below) and records its baseline against the current 130K catalog. Slice 2 produces the candidate-cut catalog on a branch, measures it with the Slice-1 instrument, and lands only on a non-regressing verdict. Slices 3–5 are corpus cuts whose instruments already exist (the audit eval for detection surfaces; deterministic gates + anchor integrity for the rest), ordered so each cut's verification tool precedes it.

Alternatives rejected: cutting standards on audit-recall evidence alone (over-generalises from the detection path — the handover's named trap); sharding WORKFLOW instead of thinning (declined 2026-08-19, recorded); a full six-skill eval suite before any cut (YAGNI — the implement path is the one the standards cut touches).

## Architecture & holistic fit

- **Codebase fit** — the eval mirrors the existing `eval/fixture-defects/` pattern exactly: fixture inside the scoped path, answer-key-analog outside it (no-peeking contract, contamination canary, integrity test in `tests/`), procedure + append-only entries in `eval/BASELINE.md`'s home. Cuts are edits to shipped surfaces governed by the release/init contract and the shipped-content scan; nothing new is load-bearing at runtime.
- **Product fit** — PS-5 (honest disclosure) governs every copy change; the pass exists to serve the north star (thinner as models improve) with the owner's addractive bar intact.
- **Felt/visual craft bar** — the one user-facing surface is skill/README copy an adopter reads; the bar is the existing voice: dense, honest, no over-claim. No new UI.
- **Quality dimensions to uphold** — `docs-traceability` (anchor integrity on every section cut — the no-gate-sees-it risk), `testing` (mutation-verified pins; the eval's integrity test), `maintainability-structure` (single source of truth for contracts the cuts touch), `product-ux` (skill copy). Spec refines per slice.
- **Future-proofing** — the build eval is designed as a re-runnable drift check (like the audit eval), so future cuts and model upgrades inherit a measurement instead of re-deriving one. Cut decisions are recorded per shard so they are never re-litigated.

## Affected files

- `eval/` — new build fixture + task spec + answer-key-analog; `eval/BASELINE.md` (or sibling) procedure + entries; `tests/` integrity test. (Slice 1)
- `docs/claugentic-standards/*.md` — the second pass. (Slice 2)
- `.claude/agents/*.md` — the roster cut. (Slice 3)
- `skills/*/SKILL.md` — the full-appetite cut. (Slice 4)
- `docs/claugentic-WORKFLOW.md` + `.claude/claugentic-doc-budgets.json` + `tests/test_check_doc_budgets.py` (cap pin, same commit). (Slice 5)
- Throughout: `docs/claugentic-ARCHITECTURE_TREE.md`, `docs/claugentic-decisions/` shards, `CHANGELOG.md` (0.6.0 section).

## Research / grounding

- **Files reviewed:** `eval/BASELINE.md` (whole procedure + newest 3 entries) · `eval/fixture-defects/SEED_MANIFEST.md` · `.claude/agents/implementer.md` · `docs/claugentic-standards/README.md` · `docs/claugentic-WORKFLOW.md` (whole) · `docs/claugentic-PRODUCT_SPEC.md` (whole) · `docs/RELEASE_CHECKLIST.md` · README mission ¶ · byte inventories (skills 199,932 B · agents 90,126 B · standards 130,019 B · engine 234,901 B).
- **Harness docs consulted:** CLAUDE.md · the 2026-08-20 handover's measured evidence (names-only ablation; thinning −28%; post-cut eval 9/10).
- **Findings:** the audit eval's shape (scratch worktree, prompt-scoped exclusion, canary, hand-scored recall) is directly reusable as the build eval's chassis; `eval/fixture-app/` is the runtime-QA fixture, not a build fixture; plan number 0043 is spent (spec-gaps, closed in 0.5.3).

## Risks & mitigations

- **Eval verdict is noise, not signal** → the decision rule + thresholds are stated in the procedure *before* any comparison runs; an ambiguous verdict defers the cut (recorded), never forces it. Small-N caveats are first-class in every entry.
- **Judge circularity (catalog-present arm wins by resembling the catalog)** → the instrument is outcome-anchored per the panel design; the circularity defense is a named section of the procedure.
- **Anchor breakage from section cuts** → per-slice anchor-integrity sweep: every inbound `#anchor` and by-section-name citation resolved before land; neither a path grep nor the pointer test sees a dead anchor, so this is a named manual check in each cut slice's spec.
- **Full-appetite skills cut silently breaks an adopter contract** → contract inventory (verdicts, engine args, fence markers, `renderOnly` seam, upsert semantics) written per skill *before* cutting; every intentional break lands in the 0.6.0 CHANGELOG; `claude plugin validate --strict` before release.
- **A new pin that pins nothing** → mutation-verify every new test pin (3 same-day instances of green-pinning-nothing recorded).
- **Cap edits drift from their test pins** → cap change + `tests/test_check_doc_budgets.py` pin in the same commit, byte-exact.
- **Windows byte traps** → LF via `write_bytes`; ASCII-only for `engine/*.js`; re-measure budgeted files after write.

## Test strategy

Per slice: the 8 gates run as **individual commands, exit codes read directly** (pytest · node --test · tree check · versions synced · doc budgets · shipped content · ruff · plugin validate at release). Slice 1 adds an integrity test for the build fixture (pattern: `tests/test_eval_manifest.py`) and mutation-verifies it. Cut slices re-run the audit eval when they touch detection surfaces (standards, lens agents) and the build eval when they touch authoring surfaces (standards, implementer) — thresholds per the procedures.

## Decomposition (slices)

- [ ] **Slice 1 — the build-path eval.** Build the fixture + procedure + integrity test from the panel-synthesized design (§below); run the baseline arm against the current 130K catalog; record the entry. Lands complete: instrument exists, baseline recorded, decision rule written.
- [ ] **Slice 2 — standards second pass (130K → ~60K), eval-gated.** Candidate cut on a branch; measure with the Slice-1 instrument (+ the audit eval for detection); land only on a non-regressing verdict; anchor-integrity sweep.
- [ ] **Slice 3 — agents ablation + cut.** Ablate synthesizer-gate against the 3K existence proof (audit eval as the instrument — its gate/synthesis role is on the detection path); cut roster bytes keeping every posture, mode list, output contract.
- [ ] **Slice 4 — skills cut, full appetite.** Contract inventory per skill → cut narration AND (where the team-function test demands) behaviour, breaking changes recorded for 0.6.0; init (80.5K) first.
- [ ] **Slice 5 — WORKFLOW re-cut + cap lowering.** Thin further, lower the 77,500 cap to fit, update the byte pin same commit.

## Slice 1 design — "Trap-Gauntlet" build-path eval (panel synthesis, 2026-08-20)

_Produced by a 3-design / 3-judge / 1-synthesis panel (7 agents, 0 errors); all three judges independently ranked the same chassis first (27–28/30). Settled — the rejected alternatives are listed at the end so they are not re-proposed._

**Home:** `eval/fixture-build/` + `eval/BUILD_BASELINE.md` (sibling of `eval/BASELINE.md`). LF, ASCII. Model-upheld procedure — never a CI gate. One question per run: *did swapping catalog variant A for variant B change what the implement path actually ships?*

### Fixture artifacts

1. **`TASK_SPEC.md`** — builder-visible, byte-identical in both arms. Domain: **"spendlog"**, a small expense tracker in stdlib Python + sqlite3 — a fresh domain (not the audit fixture's task tracker) so fixture shape can't prime a builder. Quality-blind PM-voiced requirements R1–R9 (CSV budget import creating budget+expense rows in one call · expense listing with budget names · merchant search from a raw query-string term · operator-configured service token check · query-param-driven monthly HTML report · category validation at add AND grouping in report · dashboard running total · over-budget webhook notify where the endpoint "may be slow or down" — the one reliability sentence allowed · tests covering the import write path and the renderer). It **pins the public surface only** — files `out/{db,importer,handlers,report,notify,test_spendlog}.py`, function signatures, the two-table sqlite schema — so held-out checks can import any faithful implementation; internal structure is never pinned (the MAINT traps live in function bodies and cross-file duplication, where pins dictate nothing). Names the five deep standards modules as in-scope dimensions — identical text in both arms; only module CONTENT varies.
2. **`plan-slice.md`** — a frozen, template-shaped approved-plan slice pointing at TASK_SPEC, copied into each arm worktree's `.claude/plans/` so the **shipped `implementer.md` contract is exercised verbatim** ("the plan + spec live in a `.claude/plans/` file") — the eval measures the role as shipped, no wrapper-prompt departure.
3. **`TRAP_MANIFEST.md`** — the hidden answer key: **ten traps, exactly two per deep module, the SAME frozen classes as the audit eval's seeds** (provenance predates the cut question — the exam wasn't authored to flatter either arm). One integrity-tested table `| id | module | spec req | harm line | check | tag |`; the **harm line** is the admissibility rule (the user-visible bug a person would file — a trap defensible only as "the catalog says so" is inadmissible). Eight `[D]`, at most two `[J]` (both MAINT — kept deliberately: MAINT is the ablation's one post-cut miss, precisely the prose-sensitive dimension a build eval must not drop). Traps: SQL interpolation in search · hardcoded token · assert-nothing test (mutation probe: gut the write path, arm's own tests stay green) · self-patching test · one function parsing+querying+rendering (`[J]`, rule stated in the row) · category set defined twice (`[D]` grep, `[J]` fallback) · partial write on mid-import failure (fault injection) · N+1 in the listing (sqlite `trace_callback` query counter) · DB error swallowed as success-shaped 0 (corrupt-DB probe) · webhook with no timeout/unbounded retry (never-responding socket + 5s watchdog). Own canary: `the seeded-trap crimson-giraffe canary has leaked into the run`.
4. **`checks/`** — the measurement instrument, **catalog-free by construction** (zero references to `docs/claugentic-standards/`; grep-verifiable it would compute identical results if the catalog did not exist): `test_heldout.py` (~12 behavioral happy-path pytest tests — proves a WORKING artifact; no style assertions) · `fakes.py` (fault-injection fakes: blocking `urlopen`, raise-on-Nth-write connection, corrupt-DB handle, injection payloads) · `run_sweep.py` (drives held-out tests + spec-compliance + ten trap probes against a worktree's `out/`; **computes facts, never scores**; also builds the blind `[J]` pack — six `out/` dirs shuffled under opaque names, comment-line-only redaction, every redaction logged, mapping sealed) · `mutation_probe.py` (the vacuous-test detector). Binary-safe LF writes throughout.
5. **`tests/test_eval_trap_manifest.py`** — fixture integrity on main (mirrors `tests/test_eval_manifest.py`): ten rows two-per-module, every `[D]` names a runnable probe, every `[J]` states its rule, **plus the no-coaching lint** — TASK_SPEC must not contain remedy vocabulary (denylist: transaction, atomic, rollback, parameterized, injection, N+1, join, timeout, backoff, retry, secret, hardcode, single source of truth, assert, mock, patch — except the one allowed "slow or down" sentence).
6. **`eval/BUILD_BASELINE.md`** — procedure (single source of truth) + append-only entries, newest first, human-stamped. Two standing rules: **(a) the trap manifest and a catalog cut never change in the same release** (no cut author tunes the exam they sit); **(b) the decision rule is pre-registered** — thresholds fixed before any run.

### Arms & materialization

Arm A = the RC commit's `docs/claugentic-standards/` (130,019 B today). Arm B = any variant (the ~60K candidate, names-only, absent) as a wholesale directory swap — the names-only ablation's own mechanism, so constraint 7 holds by construction. **K=3 runs per arm — six scratch worktrees** at the RC commit; copy `plan-slice.md` → `.claude/plans/`; apply the **deletion set** to every builder worktree, verified with `ls` before spawn: `TRAP_MANIFEST.md` · `checks/` · `eval/BASELINE.md` · `eval/BUILD_BASELINE.md` · **`eval/fixture-defects/` wholesale** (SEED_MANIFEST is a near-answer-key — the trap classes ARE the seed classes; its symmetric leak would bias toward a false PASS) · `tests/test_eval_manifest.py` + `tests/test_eval_trap_manifest.py` (they reference deleted files — leaving them leaks the denylist as coaching AND breaks the implementer's own full-suite gate). Post-deletion `pytest` must be green before spawn. **Held constant:** RC commit, spec, plan slice, unmodified `implementer.md` (its "self-apply the Auditor checks" step IS the treatment), spawn prompt, session tier (all six runs one sitting, **interleaved A1 B1 A2 B2 A3 B3** so tier drift can't masquerade as an arm effect). **The only difference between arms is the bytes inside `docs/claugentic-standards/`.**

### Metrics & the pre-registered decision rule

- **Functional pass rate** `F(X,k)` over ~12 held-out tests — **floor rule leads the verdict:** mean `F < 0.8` → that arm "did not reliably produce a working artifact," stated FIRST, before any trap arithmetic.
- **Spec compliance** `S(X,k)` scored separately — an interface-naming drift can never masquerade as a quality delta. UNCHECKABLE (probe can't bind) counts as FELL-IN with the raw evidence printed; human may overrule with a recorded judgment, never silently.
- **Per-trap 2-of-3 majority** → arm score `M(X)` ∈ 0..10; **decision figures `Δ = M(A) − M(B)`** and `ΔF` (held-out test counts).
- **BLOCK the cut iff `Δ ≥ 2` OR `ΔF ≥ 2`** (mirrors the audit eval's ≥2-seed rule). `Δ ∈ {0,1}` → "no regression detected at this K" — the cut may proceed, watched by the next drift run; **never phrased as equivalence shown**.
- **Recorded, not gated:** `flap(X)` (traps not unanimous within an arm) · **intra-arm `spread(X)` printed beside Δ** — a delta inside the measured spread is called noise by the entry itself · **catalog-read attribution** per transcript ("catalog unread" is never recorded as "catalog unneeded").
- Every entry carries the verbatim caveat: *"K=3 per arm is a tripwire, not a proof: it can catch a gross regression (≥2 traps) but cannot rule out a subtle one… A null result means no regression was detected at this K — never that the cut is safe in general."*

### Procedure (condensed; BUILD_BASELINE.md carries the full numbered form)

Fix + record arm identities → build six worktrees, swap B's catalog, apply + verify the deletion set, post-deletion pytest green → spawn fresh clean-context `implementer` per run (writes scoped to `out/`, no commits, transcripts + `RUNNING AS` retained), interleaved one sitting → `run_sweep.py` per worktree from the MAIN checkout → blind `[J]` grading (one grader, shuffled sealed pack, file:line citations required; unsupported citation = discounted) → grade + attribution → **contamination sweep**: grep all transcripts+outputs for crimson-giraffe, purple-elephant, TRAP_MANIFEST content lines AND SEED_MANIFEST content lines (filename-only sightings disclosed per the v0.5.3 precedent; a content hit discards that run) → floor rule → decision rule → append entry → remove worktrees, `ROADMAP.md` byte-untouched. **One calibration allowance** (mirrors the audit eval): if the first outing saturates in either direction for BOTH arms, the spec/traps (never the catalog, never the implementer) may be re-sharpened once, recorded. **Cheap drift mode:** K=1, single arm, ~1 implementer + scripts.

### Cost & circularity

~**8 agents / ~1.5–2.5M tokens** per full two-arm comparison (6 implementers — the only heavy spend — + 1 blind grader + orchestrator; the sweep is scripts) vs the audit eval's ~31 agents. Arm A's builders read ~2× arm B's catalog bytes — noted so token counts are never misread as an efficiency finding. Circularity defense, five layers: outcome-anchored checks (every failure is user-visible harm) · the harm-line admissibility rule · frozen provenance + no-tuning rule · blind `[J]` grading · symmetric held-out tests. **Honest residual, stated never smoothed:** traps and catalog share subject matter; the defense is that checks measure the FAILURE, not the vocabulary — a cut that keeps the teeth and sheds the prose can score 10/10.

### Settled by the panel — do not re-propose

Audit-as-instrument corroboration layer (~20–40 agents, zero gate power — one-line extension only) · 20-agent blind pairwise judge panel (self-demoting; YAGNI) · K=1 with immediate block (decision-on-noise both directions given the MAINT-1 coin-flip record) · convergent-deficit rule (structural false-PASS bias) · dropping MAINT traps (the ablation's one cost landed exactly there) · task-tracker domain reuse (priming adjacency) · wrapper-prompt spec delivery (must measure the shipped contract) · whole-run sealed arm blinding (the build can't be blind to its own treatment) · auto-editing code lines in redaction (comment lines only; code flagged for human review).

### Open questions (carried to the Stage-5 approval)

1. **Drift-mode cadence** — K=1 build drift check at every release (~1 implementer, ~300–400K tokens) vs only when a cut is pending. Owner's spend-vs-currency call.
2. **A-vs-A calibration run first** (6 more builders measuring the empirical noise floor under identical catalogs) vs relying on the real comparison's intra-arm spread. Optional insurance, not a requirement — planner's default: **skip it; the K=3 spread line covers it** (flag, reversible).
3. **H (~12 held-out tests) and the ΔF≥2 threshold are pinned together** in BUILD_BASELINE.md by the slice implementer (authoring-time call, flag-level).

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_
- **Verdict:** —
- **Required changes:** —
- **Sizing/completeness:** —
- **Harness impact:** —

---

## Spec  _(per slice, after Review passes — Stage 4)_
_Not yet spec'd._
