# 0041 — Adopter hardening: make the harness's promises real in installed repos

- **Status:** In Review — revision 2 (2026-08-12) addresses all 13 plan-gate items; awaiting re-gate.
- **Resumable from:** awaiting plan-gate re-review verdict (§Review)
- **Blockers:** Slice 2 depends on PR #7 merging (user action; Slice 1 is green on that PR).
- **Flags:** none
- **Disposition at close:** per template — deferred remainders → `docs/claugentic-ROADMAP.md`.
- **Roadmap item:** `docs/claugentic-ROADMAP.md` → Later/Ideas → "Plan 0041 — adopter hardening (ACTIVE 2026-08-12)".
- **References:** `docs/claugentic-DECISIONS.md` (deterministic-gates · plugin-distribution · release-contract · doc-lifecycle shards) · 12-agent holistic review (wf_b334694f, 2026-08-12) · 3-adopter scout (wf_ee5f24f7, 2026-08-12)

## Problem

Evidence from the harness's first three real deployments (data-insights-hub docs@0.4.1 · DistrictSync docs@0.3.0/plugin 0.4.1 · AskBase docs@0.4.0) plus a 12-agent holistic review of this repo (both 2026-08-12):

1. **Ledger weight is unbounded in every adopter** — the #1 systemic failure, confirmed ×3. DECISIONS: 193KB+278KB archive (DIH, re-snowballed to 193KB within ~4 weeks of its own split) · 300KB monolith (DS) · 648KB monolith (AB, ~13× the size that triggered sharding here). "Optional, leave empty" CHARTER: 60KB / 8KB / 202KB. Uncapped split-extensions everywhere (DIH `AUDIT_BACKLOG.md` 391KB; AB `BACKLOG.md`+companions). CLAUDE.md always-loaded at 28KB / 63KB / 23KB. Root cause: `check_doc_budgets.py` is release-**stripped**, the caps-config is "adopter-created" (nobody creates it), and split-created extension files inherit **no cap** — so the exact condense machinery this repo built for itself protects only itself.
2. **Version skew is universal.** All three deployments run stale managed docs (0.3.0/0.4.0/0.4.1 vs 0.5.1); DistrictSync hand-documents "cite the plugin, not that file" instead of re-running init. Nothing surfaces "your stamped docs < installed plugin".
3. **Plan-lifecycle convention dropped in all three** (AB: 31 live + 50 archived plans, ~1MB; DS: landed 137KB plan retained; DIH: manual sweep needed). Delete-at-land is model-upheld and universally not upheld.
4. **Releases aren't gated on green CI.** v0.5.1 shipped inside an 11-day red-CI window (pytest collection dead — `import yaml` vs no pyyaml; fixed PR #7). `claude plugin validate --strict` is human-remembered (a MEMORY note), not mechanized.
5. **Five front-door over-claims** vs the honesty bar: README:3 "never changes your code without your sign-off" (lightweight path has no sign-off; stop discipline model-upheld, WORKFLOW:193) · "zero side effects" aborted-run claim (CLAUDE.md/CHANGELOG vs build_release.py:26-28) · README:57 "blocks *done* until *every file* documented" (commit-time, glob-scoped, conditionally wired) · "deterministic architecture enforcement" unqualified in both manifests · /build frontmatter "stops before anything irreversible" stated as fact.
6. **The Stage-9 learning loop doesn't close in adopters:** harvest destinations `.claude/agents/` + editable WORKFLOW exist only here (retrospect-harvester.md:18-19 vs WORKFLOW:151); honesty-reviewer:14 + product-designer:47 read a CLAUDE.md "honesty positioning" section only this repo has; no upstream contribution path exists in shipped docs.
7. **Team wiring is fragile:** husky repos (`core.hooksPath=.husky`) leave the tree gate written-but-inactive (init:499-506); a teammate without Python has every commit blocked by a cryptic error (wrapper can't distinguish missing interpreter from failing gate); wiring never propagates (git deliberately doesn't auto-activate hooks on clone).
8. **Engine defects:** audit.js:1137 checks `args.renderOnly` BEFORE parseArgs though scriptPath delivery passes args as a JSON string (documented at :756-768) → SELECT re-render seam throws · build-item.js:472-475 filters the explicit `null` "same-model" signals (:822,:854) before folding → a mixed run over-reports "cross-model confirmed" · qa.js:816-818 driverPrompt preamble malformed + :658/:730 trim only `/` (build-item trims both) · verify.js:484-523 fan-out unguarded where audit.js uses guardedAgent (:1203-1214) · build-item.js:790-792 silently defaults verify dimensions/trustSurface vs verify.js:141's "never defaulted" stance. Plus the 0040-banked standing fix: `nsAgent()` hard-namespaces spawns with no bare-name fallback (hit twice).
9. **Eval answer-key leak:** `docs/claugentic-ARCHITECTURE_TREE.md:141-145` describes each fixture file's planted seeds in the read-first doc; the canary grep can't detect absorption from there.
10. **Adopter incident to record:** harness doc content crashed DIH's Tailwind build (poison string scanned from docs/; commits a8248b3f/e315dcf6/3eb2e62d).

## Goals / Non-goals

- Goal: adopter doc budgets **mechanical where wired and an interpreter is present; seeding and wiring stay model-upheld (`init`, a prose skill) — the same honesty shape as the tree gate.** Adopter enforcement is **commit-time ONLY** (chained after the tree gate in the same pre-commit; `deterministic-gates.md:7` "No adopter CI" stands — the CI legs of this plan are harness-self). **PostToolUse/per-action hooks REJECTED** (user constraint 2026-08-12; consistent with 0024-S4a).
- Goal: release pipeline to industry standard — the human gate becomes the tag push; a tag-triggered workflow runs every gate (incl. `plugin validate --strict`) and only then publishes.
- Goal: every shipped sentence matches wiring; the learning loop closes in adopter repos; team wiring survives husky + python-less teammates; the six engine defects fixed with regression pins; eval leak sealed.
- **Delivery dependency (stated per gate #11):** nothing in the doc/skill slices reaches the three live adopters until a release ships **and they re-run `init`** — except the plugin-resident SessionStart advisor (Slice 3), which arrives on plugin update alone; that is why it is sequenced early.
- Non-goal: remediating the three existing deployments (their re-init + condense runs happen in those repos — ROADMAP line records this as follow-on).
- Non-goal: telemetry of any kind (privacy — declined 2026-08-12).
- Non-goal: the mechanical approval land-gate + secret-scan (stay honestly "not built yet" — existing DECISIONS line).
- Non-goal: standards-catalog gen-1 upgrade pass (own plan; ROADMAP line at close).
- Non-goal: WORKFLOW.md rewrite — Slice 12 is budget + relocation + numbering only.

## Approach

Ship the leanness machinery instead of keeping it harness-self (generalize `check_doc_budgets.py` to a per-repo caps-config; init seeds defaults incl. a heritable glob so split-extensions are born capped — **for flat siblings matching the seeded pattern**; managed full-copy docs excluded). Surface staleness at session start (advisor) and in doctor, never per-tool. Formalize release-on-green with GitHub-native mechanisms. Fix copy to match mechanics.

**Forks resolved (user, 2026-08-12):**
- **0038's "NO doc-budget hook" don't-re-break is SUPERSEDED** — the user directed commit-time enforcement "like the tree gate." A dated superseding DECISIONS line + the full enforcement-story copy sweep (`doc-lifecycle.md:5` · `honesty.md:5` · `PRODUCT_SPEC.md:42` · `CLAUDE.md:3` · `README.md:57` · `WORKFLOW.md:152/165` · `INVARIANTS.md:101/108/112`) land **in the same slice as the chaining contract change (Slice 6)** — no interim false-copy window.
- **Grace posture = per-file report-only flag** (option A): init seeds the recommended cap; an already-over file gets a visible `reportOnly` flag — the gate prints the breach and passes until the file first comes under cap, then enforcement self-arms. Avoids both rung-2's forbidden mechanical ceiling-raise and day-one repo-global blocking. Honoring the shrink is `/condense` + model-upheld — nothing mechanical shrinks anything; the flag makes the debt loudly visible every commit.
- **Release shape = CI publishes** (option A): `build_release.py` prepares + validates locally and STOPS before any push; the human act is pushing the tag; the tag-triggered workflow re-runs all gates + `plugin validate --strict` + built-tree validation, and only then pushes the `release` branch + creates the GitHub Release. Nothing adopters consume exists until CI is green. Offline publish is retired (recorded trade-off). The local preflight red-CI check becomes advisory (warn), not the load-bearing gate.
- **Loop closure = fix the agent pointers** (no managed-fence contract change).

Alternatives rejected: PostToolUse enforcement (user — overhead) · model-upheld budgets (observed failing ×3) · fail-closed hook on missing python (user chose warn-and-pass) · cap-at-current-size (rung-2 violation, gate #4) · verify-after-publish release shape (gates nothing adopters consume).

## Architecture & holistic fit

- **Codebase fit:** one-gate-one-invariant holds — doc-budgets stays a sibling script, **chained (run-both-and-report: a budget failure never masks the tree gate's message)** after the tree gate; `_repo_root()`/UTF-8 parity with siblings; init remains the sole writer of adopter wiring; the release workflow invokes the same gate scripts + `build_release.py` build path rather than forking logic.
- **Caps-config schema (spec'd once, gate #13 — no `version` field):** flat map `{"<relpath-or-glob>": <max_bytes> | {"max": <bytes>, "reportOnly": true}}`. The extended object form exists ONLY for the grace flag; `/doctor`'s reader-contract is updated to both forms in the same slice that ships the script (Slice 6). `REQUIRED_SHARDS` (routing integrity, not a cap) stays **harness-self**: driven by a harness-config-only key, inert in adopters.
- **Adopter config semantics:** absent config ⇒ **no-op exit 0** (a chained gate must never block a repo that hasn't opted in) · seeded glob matching nothing ⇒ **skip** · adopter globs are non-recursive and the flat-shape assertion stays harness-self (gate #8).
- **Product fit:** the adopter (possibly non-engineer) should never wake to a 648KB ledger or stale docs — the harness keeps itself lean and current without being asked.
- **Craft bar:** non-user-facing tooling — skipped per effort-dial.
- **Quality dimensions:** `maintainability-structure` · `docs-traceability` · `reliability-resilience` · `testing` · `security` (release workflow provenance).
- **Future-proofing:** release workflow steps single-purpose so signing/attestation slots in later; the object-form cap value is the extension point if a future flag is ever needed.

## Affected files

`scripts/check_doc_budgets.py` (generalize; caps migrate to config) · **`.claude/claugentic-doc-budgets.json` (NEW — this repo's own caps; one cap source per repo)** · `scripts/build_release.py` (stop-before-push shape, advisory preflight) · `.github/workflows/ci.yml` + **new `release.yml`** · `pyproject.toml` · `skills/init/SKILL.md` (caps seed, husky chain, wrapper, docs-scanner caution) · `skills/condense/SKILL.md` + `skills/doctor/SKILL.md` (reader-contract, gate table, skew advisory) · `scripts/claugentic-session-advisor.py` · `.githooks/pre-commit` · `engine/{audit,build-item,qa,verify}.js` · `README.md` · `CLAUDE.md` · `CHANGELOG.md` · `.claude-plugin/{plugin,marketplace}.json` · `.claude/agents/{retrospect-harvester,honesty-reviewer,product-designer}.md` · `docs/claugentic-WORKFLOW.md` · `docs/claugentic-INVARIANTS.md` · `docs/claugentic-PRODUCT_SPEC.md` · decisions shards (`doc-lifecycle` · `deterministic-gates` · `release-contract`) · `docs/claugentic-ARCHITECTURE_TREE.md` · `tests/*` per slice.

## Research / grounding

- **Files reviewed:** all cited `file:line` above, first-hand-verified for the CI incident (`gh run list`, ci.yml:26, test_frontmatter_parses.py:26); adopter facts from the bounded 3-repo scout (journal: wf_ee5f24f7); collision set from the Stage-3 gate's own verification pass.
- **Harness docs consulted:** deterministic-gates · plugin-distribution · release-contract · doc-lifecycle DECISIONS shards; CLAUDE.md; WORKFLOW DoD; RELEASE_CHECKLIST.
- **Findings:** the condense/budget machinery exists and works — the gap is distribution + seeding + heritability, not invention. The advisor is plugin-resident (`${CLAUDE_PLUGIN_ROOT}`-rooted) so it reaches adopters on plugin update without re-init. Husky-chaining gives teammate propagation for free via npm. The publish order (`release` branch pushed before the tag) is why a naive tag-triggered workflow gates nothing.
- **0040-banked items absorbed:** Slice 4 absorbs `check_doc_budgets.py`'s missing `_repo_root()` anchor + the CWD-coupled `TestClosurePassD`; Slice 10 absorbs the `nsAgent()` bare-name fallback. The index↔`REQUIRED_SHARDS` agreement test + non-`.md`-in-shard-dir stance **stay banked** (untouched by this plan).

## Risks & mitigations

- Chained gate blocking innocents → absent-config no-op · glob-no-match skip · report-only grace for day-one-over files · warn-and-pass wrapper lands **before** chaining (sequencing fixed, gate #5).
- Ship-class change breaking release contracts → Slice 6 updates the derived sets, Pass D, the byte-identical shipped-set test, and doctor's per-script-presence rule **together** (gate #3).
- Release workflow double-publish vs `build_release.py` → the script never pushes; the workflow is the only publisher (single writer).
- Dry-run tag poisoning the version-increase guard → dry-run uses a **non-`v*`** tag (`release-dryrun-*`); pushing even that is user-gated (class (c) outward action).
- Copy edits breaking frontmatter/manifest parse → `claude plugin validate --strict` + frontmatter test in each copy-touching slice's AC (model-upheld run until Slice 2 wires it into CI; per-slice AC says which).
- WORKFLOW relocation losing content → content-preserving diff, git history the archive, verify-panel review.
- Slices 5/7/9 all edit `skills/init/SKILL.md` → sequenced non-adjacent-conflict order (5 → 7 → 9); each rebases on the prior's landed text.

## Test strategy

Per-fix regression pins (renderOnly string-args · crossModelClaim mixed-run · qa trim/prompt shape · config-driven caps incl. object-form + no-op/skip semantics · wrapper missing-interpreter via PATH-stripped subprocess) in the existing suites; full `python -m pytest` + `node --test` + gate scripts green per slice. **Adopter end-to-end (gate #10):** Slice 7's AC runs `init` against a scratch repo (and one real adopter, read-only inspection) asserting caps seeded · hook chained · husky-repo case · PATH-stripped-python case · report-only grace behavior · skew nudge fires · `/condense` reachable. **Whole-feature closing pass** (WORKFLOW:130) runs on the final slice against the Stage-1 job-to-be-done: "an adopter's harness stays lean, current, and honest without being asked."

## Decomposition (slices) — execution order

- [x] **Slice 1 — CI restored** · **landed, pending merge** (PR #7, green ×5). Slice 2 depends on the merge.
- [ ] **Slice 2 — Release formalization (CI-publishes)** · test deps → pyproject (CI installs from it) · `release.yml` on `v*` tag: gates + `plugin validate --strict` + built-tree validation → push `release` branch + GitHub Release · `build_release.py` stops before any push; advisory red-CI preflight · RELEASE_CHECKLIST rewrite · required-checks branch protection documented (user applies) · non-`v*` dry-run tag, user-gated.
- [ ] **Slice 3 — Currency nudges** *(early: plugin-resident, reaches adopters on plugin update)* · advisor + doctor: stamped-docs < installed-plugin → "re-run init"; landed/cold-plan nudge · audience-split honored (nudges = user-facing `systemMessage` only; `additionalContext` stays the resume branch).
- [ ] **Slice 4 — Budget script generalization (3a — no ship, zero adopter surface)** · config-driven from `.claude/claugentic-doc-budgets.json` · **this repo's caps migrate to its own config** · no-op/skip/non-recursive semantics per §Architecture · report-only object form · `_repo_root()` + CWD fix (0040-banked) · tests.
- [ ] **Slice 5 — Team wiring (before any chaining)** · warn-and-pass wrapper (loud one-line skip on missing interpreter) · husky-chain detection in init · teammate bootstrap one-liner · docs-scanner-exclusion caution + DIH Tailwind incident → DECISIONS.
- [ ] **Slice 6 — Ship-class + contract sweep (3b)** · reclass to shipped: derived sets + Pass D + byte-identical shipped-set test + doctor gate-table/applicability + reader-contract (both cap forms) + condense rewiring · **0038-superseding DECISIONS line + the full 8-location copy sweep in THIS slice** · INVARIANTS candidate: "exactly one cap source per repo."
- [ ] **Slice 7 — init seeding + chaining (3c)** · seed caps (CLAUDE.md · DECISIONS+extensions · ROADMAP · CHARTER) + heritable glob **excluding managed full-copy docs** + report-only flags for over files · chain into pre-commit after the tree gate (run-both-and-report) · **adopter e2e battery** (Test strategy).
- [ ] **Slice 8 — Copy honesty pass** · the five pre-existing over-claims only · validate + frontmatter tests.
- [ ] **Slice 9 — Adopter loop closure (fix-pointers)** · Stage-9 destinations branch by repo type · honesty-reviewer/product-designer carry their premise inline · upstream contribution path named in shipped docs · WORKFLOW adopter-note moved to intro.
- [ ] **Slice 10 — Engine fixes** · the five defects + `nsAgent` bare-name fallback · ASCII-only + `|` / ` - ` delimiter constraints carried into spec · regression pins.
- [ ] **Slice 11 — Eval leak** · neutral tree entries + grep-for-seed-ids test.
- [ ] **Slice 12 — WORKFLOW weight (after the 3-series)** · relocate the condensation body to `/condense` + pointer sweep (`doc-lifecycle.md:6` canonical-home line · DoD · condense/doctor skills) · DoD dual-numbering fix · **cap in THIS repo's config at 70,000 B** (current 83,383 B; expected ~68 KB post-relocation — the cap bites) · **whole-feature closing pass**.

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_

RUNNING AS: Opus 5 (1M context) — a separate clean-context pass on the most capable model; a reduction of rubber-stamping risk, never model-family independence.

- **Verdict:** **CHANGES REQUIRED** — the problem set is real and first-hand-grounded, the path (full pipeline) is right, and the approach (ship the machinery, don't re-invent it) is sound. But **Slice 3 breaks a recorded don't-re-break** and three shipped contracts it doesn't name; **Slice 2's release gate fires after the thing it gates is already published**; the **grace posture hides a user-decision fork**; and **Slice 3 is oversized** for one session. Fix 1–8 before Spec; 9–13 are landable as plan edits.

_(Revision 2 addresses items 1–13: forks resolved by the user 2026-08-12 — 0038 superseded with same-slice sweep · report-only grace · CI-publishes · fix-pointers; Slice 3 split into Slices 4/6/7; sequencing reordered (nudges early, wiring before chaining, WORKFLOW last); honesty rewordings applied; adopter e2e + closing pass added; caps-config version field dropped; ROADMAP line added; 0040-banked absorption named. Full original findings: git history of this file at the Stage-3 commit.)_

- **Re-review verdict (Stage 3, round 2):** _pending_

---

## Spec  _(per slice, after Review passes — Stage 4)_
