# 0041 — Adopter hardening: make the harness's promises real in installed repos

- **Status:** Draft
- **Resumable from:** awaiting Stage-3 plan-gate review (§Review)
- **Blockers:** none (Slice 1 already landed via PR #7; user merges)
- **Flags:** none
- **Disposition at close:** per template — deferred remainders → `docs/claugentic-ROADMAP.md`.
- **Roadmap item:** to be added at first slice-land (this plan IS the holistic-hardening program).
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
8. **Engine defects:** audit.js:1137 checks `args.renderOnly` BEFORE parseArgs though scriptPath delivery passes args as a JSON string (documented at :756-768) → SELECT re-render seam throws · build-item.js:472-475 filters the explicit `null` "same-model" signals (:822,:854) before folding → a mixed run over-reports "cross-model confirmed" · qa.js:816-818 driverPrompt preamble malformed + :658/:730 trim only `/` (build-item trims both) · verify.js:484-523 fan-out unguarded where audit.js uses guardedAgent (:1203-1214) · build-item.js:790-792 silently defaults verify dimensions/trustSurface vs verify.js:141's "never defaulted" stance.
9. **Eval answer-key leak:** `docs/claugentic-ARCHITECTURE_TREE.md:141-145` describes each fixture file's planted seeds in the read-first doc; the canary grep can't detect absorption from there.
10. **Adopter incident to record:** harness doc content crashed DIH's Tailwind build (poison string scanned from docs/; commits a8248b3f/e315dcf6/3eb2e62d).

## Goals / Non-goals

- Goal: budgets **heritable and mechanical** in adopter repos — enforcement at **commit-time (chained after the tree gate in the same pre-commit) or CI/PR only; PostToolUse/per-action hooks are REJECTED** (user constraint 2026-08-12; consistent with 0024-S4a).
- Goal: release pipeline to industry standard — tag-triggered, green-CI-gated, `plugin validate --strict` mechanized, test deps declared in `pyproject.toml`.
- Goal: every shipped sentence matches wiring (the five copy fixes); the learning loop closes in adopter repos; team wiring survives husky + python-less teammates; the four engine defects fixed with regression pins; eval leak sealed.
- Non-goal: telemetry of any kind (privacy — declined 2026-08-12).
- Non-goal: the mechanical approval land-gate + secret-scan (stay honestly "not built yet" — existing DECISIONS line).
- Non-goal: standards-catalog gen-1 upgrade pass (own plan; ROADMAP line at close).
- Non-goal: WORKFLOW.md rewrite — Slice 10 is budget + relocation + numbering only.

## Approach

Ship the leanness machinery instead of keeping it harness-self (generalize `check_doc_budgets.py` to a per-repo caps-config; init seeds defaults incl. a heritable glob so split-extensions are born capped). Surface staleness at session start (advisor) and in doctor, never per-tool. Formalize release-on-green with GitHub-native mechanisms. Fix copy to match mechanics (chosen over building mechanics to match copy — user decision 2026-08-12). Alternatives rejected: PostToolUse enforcement (overhead — user); model-upheld budgets (observed failing ×3); fail-closed hook on missing python (user chose warn-and-pass).

## Architecture & holistic fit

- **Codebase fit:** one-gate-one-invariant holds — doc-budgets stays a sibling script, chained (not merged) after the tree gate in the pre-commit wrapper; `_repo_root()`/UTF-8 parity with siblings; init remains the sole writer of adopter wiring; release workflow consumes `build_release.py` logic rather than forking it.
- **Product fit:** the adopter (possibly non-engineer) should never wake to a 648KB ledger or stale docs — the harness keeps itself lean and current without being asked.
- **Craft bar:** non-user-facing tooling — skipped per effort-dial.
- **Quality dimensions:** `maintainability-structure` (knowledge-store shape) · `docs-traceability` (stamped-version currency) · `reliability-resilience` (hook failure modes) · `testing` (regression pins per fix) · `security` (release workflow provenance).
- **Future-proofing:** caps-config schema gets a `version` field; release workflow steps kept single-purpose so a future signing/attestation step slots in.

## Affected files

`scripts/check_doc_budgets.py` (generalize + ship) · `scripts/build_release.py` (ship-class change, red-CI refusal) · `.github/workflows/ci.yml` + new `release.yml` · `pyproject.toml` · `skills/init/SKILL.md` (caps seed, husky chain, wrapper, fence honesty block, docs-scanner-exclusion note) · `skills/condense/SKILL.md` + `skills/doctor/SKILL.md` (heritable caps, skew advisory) · `scripts/claugentic-session-advisor.py` (skew + stale-plan nudges) · `.githooks/pre-commit` (warn-and-pass on missing interpreter) · `engine/{audit,build-item,qa,verify}.js` · `README.md` · `CLAUDE.md` · `CHANGELOG.md` · `.claude-plugin/{plugin,marketplace}.json` · `.claude/agents/{retrospect-harvester,honesty-reviewer,product-designer}.md` · `docs/claugentic-WORKFLOW.md` · `docs/claugentic-ARCHITECTURE_TREE.md` · `tests/*` per slice.

## Research / grounding

- **Files reviewed:** all cited `file:line` above, first-hand-verified for the CI incident (`gh run list`, ci.yml:26, test_frontmatter_parses.py:26); adopter facts from the bounded 3-repo scout (journal: wf_ee5f24f7).
- **Harness docs consulted:** deterministic-gates · plugin-distribution · release-contract · doc-lifecycle DECISIONS shards; CLAUDE.md; WORKFLOW DoD.
- **Findings:** the condense/budget machinery already exists and works — the gap is distribution + seeding + heritability, not invention. The advisor script already has a SessionStart channel to ride. Husky-chaining gives teammate propagation for free via npm.

## Risks & mitigations

- Shipping the budget gate must not break adopters without Python → wrapper warn-and-pass (user decision) + doctor flag; gate absent ⇒ advisory only.
- Seeded caps firing on day-one giant ledgers (AB's 648KB) → seed caps **with a grace posture**: first run reports + points at /condense, breach blocks only NEW growth (cap = current size rounded up when over, with a recorded shrink target) — exact mechanism spec'd in Slice 3.
- Release workflow double-publishing vs `build_release.py` → workflow validates + creates the GitHub Release only; branch build stays the script's job.
- Copy edits breaking frontmatter/manifest parse → `claude plugin validate --strict` + existing frontmatter test in the loop (Slice 5 AC).
- WORKFLOW relocation losing content → git history + condense-style content-preserving diff, reviewed at verify.

## Test strategy

Per-fix regression pins (renderOnly string-args · crossModelClaim mixed-run · qa trim/prompt shape · budget-config seeding/heritability · wrapper missing-interpreter path via PATH-stripped subprocess) in the existing suites; full `python -m pytest` + `node --test` + all four gate scripts + `claude plugin validate --strict` green per slice; release workflow proven by a dry-run tag on a throwaway branch before documenting.

## Decomposition (slices)

- [x] **Slice 1 — CI restored** · pyyaml + incident ledger line (PR #7, green ×5 checks; user merges).
- [ ] **Slice 2 — Release formalization** · test deps → pyproject (CI installs from it) · `release.yml` on tag push: full gates + `claude plugin validate --strict` + built-tree validation + GitHub Release · `build_release.py` refuses on red main CI · RELEASE_CHECKLIST rewrite · branch-protection required-checks documented (user applies). Lands complete: one release surface, no adopter coupling.
- [ ] **Slice 3 — Adopter doc-budgets (the snowball fix)** · generalize `check_doc_budgets.py` (per-repo caps-config, CWD-independence parity) · ship it · init seeds defaults (CLAUDE.md · DECISIONS+shards · ROADMAP · CHARTER · **a heritable glob covering split-extensions**) · chain into pre-commit after tree gate · condense/doctor wire to it · WORKFLOW split-procedure states budgets-are-heritable.
- [ ] **Slice 4 — Currency nudges** · advisor + doctor: stamped-docs-version < installed-plugin-version → "re-run init"; landed/cold-plan nudge at SessionStart (reuses doctor detection).
- [ ] **Slice 5 — Copy honesty pass** · the five edits + validate + frontmatter tests.
- [ ] **Slice 6 — Adopter loop closure** · Stage-9 destinations branch by repo type · agent prompt pointers fixed (or init writes the honesty block into the fence) · upstream contribution path (issues/PRs) named in shipped docs · WORKFLOW adopter-note moved to intro.
- [ ] **Slice 7 — Team wiring** · init husky-chain detection · warn-and-pass wrapper · teammate bootstrap one-liner in the fence · docs-scanner-exclusion caution (DIH Tailwind incident recorded in DECISIONS).
- [ ] **Slice 8 — Engine fixes** · renderOnly parse-first · crossModelClaim null-honest · qa prompt/trim · verify guardedAgent parity · build-item explicit dimensions/trustSurface · regression pins.
- [ ] **Slice 9 — Eval leak** · neutral tree entries for fixture files + a test asserting the tree never describes seeds.
- [ ] **Slice 10 — WORKFLOW weight** · put WORKFLOW.md under a (harness-self) budget · relocate the condensation body to /condense with a pointer · fix the DoD dual-numbering · bounded to relocation, no rewrite.

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_
- **Verdict:**
- **Required changes:**
- **Sizing/completeness:**
- **Harness impact:**

---

## Spec  _(per slice, after Review passes — Stage 4)_
