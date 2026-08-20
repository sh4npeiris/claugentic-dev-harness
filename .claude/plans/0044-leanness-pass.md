# 0044 — The leanness pass, eval-gated

- **Status:** Draft
- **Resumable from:** Slice 1 design pending the build-eval design panel synthesis; then Stage 2b advisory panel → Stage 3 review.
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

## Slice 1 design — build-path eval (panel synthesis)

_Pending: the 3-design/3-judge/1-synthesis panel (run `wf_6b606d54-78f`) — folded in verbatim on completion._

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_
- **Verdict:** —
- **Required changes:** —
- **Sizing/completeness:** —
- **Harness impact:** —

---

## Spec  _(per slice, after Review passes — Stage 4)_
_Not yet spec'd._
