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

RUNNING AS: Opus 5 (1M context) — a separate clean-context pass on the most capable model; a reduction of rubber-stamping risk, never model-family independence.

- **Verdict:** **CHANGES REQUIRED** — the problem set is real and first-hand-grounded, the path (full pipeline) is right, and the approach (ship the machinery, don't re-invent it) is sound. But **Slice 3 breaks a recorded don't-re-break** and three shipped contracts it doesn't name; **Slice 2's release gate fires after the thing it gates is already published**; the **grace posture hides a user-decision fork**; and **Slice 3 is oversized** for one session. Fix 1–8 before Spec; 9–13 are landable as plan edits.

### Required changes

1. **Reconcile "the only hook-enforced gate" — Slice 3 breaks a recorded don't-re-break.** `docs/claugentic-decisions/doc-lifecycle.md:5` states verbatim: *"Don't-re-break: **NO doc-budget hook** (only the tree-check is hook-enforced)"* (0038). Chaining `check_doc_budgets.py` into pre-commit contradicts it, and falsifies copy in `docs/claugentic-decisions/honesty.md:5` · `docs/claugentic-PRODUCT_SPEC.md:42` · `CLAUDE.md:3` · `README.md:57` · `docs/claugentic-WORKFLOW.md:165` (DoD gate 4: *"harness-self only … Not applicable to adopter repos — skip it"*) and `:152` (*"stripped from the release, so the script isn't even present in your repo"*) · `docs/claugentic-INVARIANTS.md:101,108,112` (*"a **run-gate, NOT hook-enforced**"*). Choose and record: **(a)** keep budgets a run-gate + `/doctor` advisory in adopters (no chaining — 0038 stands), or **(b)** supersede 0038 with a dated DECISIONS line **and sweep every one of those sentences in the SAME slice that lands the chaining**. Do **not** defer the sweep to Slice 5 — Slice 5 owns the five *pre-existing* over-claims, so deferring leaves an interim false-copy window = new debt, which the DoD forbids. Also check the `tests/` scan that 0038 says guards the shipped condensation trigger.

2. **Name the single cap source and the shipped script's config contract (Slice 3).** `scripts/check_doc_budgets.py:63-81` hardcodes *harness* caps (`docs/claugentic-DECISIONS.md` = 3,500 B — the **index** cap). Shipped as-is, an adopter's 648 KB monolithic `DECISIONS.md` is measured against 3,500 B on first run. Spec must state: the shipped script reads caps **only** from `.claude/claugentic-doc-budgets.json`; **this repo's own caps migrate into its own config** (doc-lifecycle.md:6 — *"exactly one cap source per repo"*); **absent config ⇒ no-op exit 0**, never fail-loud (a chained gate must not block every commit in a repo that never opted in); and where `REQUIRED_SHARDS` (`:91-105` — harness-self routing integrity, not a cap) lives after the split.

3. **The ship-class change is a contract change, not a file move (Slice 3).** `scripts/build_release.py:102` classes the script `self-gate`. `check_shipped_content.py`'s `HARNESS_SELF_SCRIPTS`/`_RECREATED` partitions and **Pass D** are *derived* from `recreate_class` (release-contract.md:8), a test pins the shipped set **byte-identical** (release-contract.md:7), and `/doctor` decides applicability by **per-script presence** (release-contract.md:5; `skills/doctor/SKILL.md:47,59,177`) — presence becomes universal, so that rule silently mis-reports. The slice must name the new class/applicability rule and update the derived sets, Pass D, doctor's gate table, and the shipped-set test **together**.

4. **STOP for the user on the grace posture — it is a design fork, not a spec detail** (the plan's Risks line defers it to Slice 3; it can't be). Three real options: **(A)** seed the recommended cap + run report-only for already-over files until they come under (needs a visible per-file flag in the config schema); **(B)** cap = current size rounded up — **this contradicts doc-lifecycle rung 2** (*"a RECORDED cap-bump … a `[J]` recorded decision, NEVER a mechanical ceiling-raise"*): `init` auto-writing a ceiling at today's bloat *is* the mechanical ceiling-raise that rung forbids; **(C)** don't seed a cap for an already-over file at all; `/doctor` advises until it's condensed. Two facts the user needs to decide: a chained budget gate is **repo-global**, so an over-cap ledger blocks **every** commit including unrelated ones (unlike the tree gate, which is `--staged`-scoped — `.githooks/pre-commit`), and *"blocks only NEW growth"* requires the cap itself to be the baseline, i.e. the next `DECISIONS` append is blocked on day one. Also say where the *"recorded shrink target"* lives and state plainly that honoring it is **model-upheld** — nothing mechanical shrinks anything.

5. **Sequencing defect: Slice 3 lands the breakage Slice 7 fixes.** Slice 3 chains the gate into pre-commit; the **warn-and-pass wrapper and husky-chain detection land in Slice 7**. Between them, a python-less teammate is blocked by a cryptic error and a husky adopter is silently un-gated — exactly the failure the Risks section promises to mitigate. Move the wrapper + husky work **before** (or into) the chaining. Note also that Slices 3, 6, and 7 all edit `skills/init/SKILL.md` (79,692 B) — sequence them so they don't interleave.

6. **The release gate fires after publish (Slice 2).** The publish command is `git tag v<version> && git push --force-with-lease origin release && git push origin v<version>` (`docs/RELEASE_CHECKLIST.md:34`, `scripts/build_release.py:488-489`) — the **`release` branch is pushed before the tag**, and the marketplace `source.ref` points at that **branch** (plugin-distribution.md:5). So a tag-triggered `release.yml` gates nothing an adopter consumes. Either re-order (tag → workflow gates → branch publish) or **re-scope `release.yml` honestly** as post-publish verification + GitHub Release creation, making the local red-CI refusal the load-bearing gate. Two more: name the refusal's failure posture (**no network / no `gh` auth / no CI run yet → refuse or warn?** — a fail-open check is not a gate, and fail-closed blocks an offline release, so pick and document), and ensure the *"dry-run tag on a throwaway branch"* uses a tag that does **not** match `v*` — the version-increase guard anchors on the highest `v*` tag (`build_release.py:251-253`), so a stray `v9.9.9` poisons every future release. The throwaway tag push is also a class-(c) irreversible outward action → user-gated.

7. **Slice 10: whose cap, and the pointer sweep.** `docs/claugentic-WORKFLOW.md` (83,383 B) is a **shipped full-copy managed doc**, so (i) its cap belongs in **this repo's** caps config (harness-self), and (ii) Slice 3's **heritable glob must EXCLUDE managed full-copy docs** (WORKFLOW / PLAYBOOK / `docs/claugentic-standards/*`) — otherwise an adopter's commits are blocked by a file they don't own and cannot shrink. State the **target cap and the expected post-relocation size**: a cap set at "whatever's left after the move" is the same mechanical ceiling-raise as #4(B) and buys nothing — either set one that bites, or keep the relocation and drop the cap. Relocating the condensation body also **moves the canonical home** named in `doc-lifecycle.md:6` (*"Canonical: WORKFLOW → The escape-valve ladder"*) and pointed at from the DoD, `skills/condense/SKILL.md`, and `skills/doctor/SKILL.md` — sweep those pointers in the slice. Slice 10 must land **after** Slice 3.

8. **Heritable-glob mechanics will hard-fail in adopter repos.** `_resolve_targets` (`check_doc_budgets.py:150-167`) raises `BudgetConfigError` when a glob **matches nothing** *and* when the globbed dir contains **any subdirectory** (the flat-shape assertion). Both are likely in an adopter (a seeded glob whose split-dir doesn't exist yet; any nested dir under `docs/`), and with the gate chained to pre-commit that becomes a blocked commit over a config artifact. Spec the adopter semantics: seeded-glob-matching-nothing ⇒ **skip**, not error; decide the subdirectory stance (recurse, ignore, or keep the assertion harness-self).

9. **Honesty fixes in the plan's own wording** (the plan is itself a trust surface): **(a)** Goal *"budgets **heritable and mechanical** in adopter repos"* — the **seeding and wiring are `init`, a prose skill = model-upheld**, and warn-and-pass degrades the gate to advisory without an interpreter; honest form: *"mechanical where wired and an interpreter is present; seeding/wiring stay model-upheld (init), as with the tree gate."* **(b)** *"green-CI-gated"* release → per #6. **(c)** *"split-extensions are **born capped**"* → holds only for flat siblings matching the seeded pattern. **(d)** Test strategy's *"`claude plugin validate --strict` green per slice"* is human/agent-run (model-upheld) until Slice 2 mechanizes it — say which per slice. **(e)** Slice 1 is `[x]` but unmerged — mark it *landed, pending merge* and state that Slice 2 depends on it.

10. **Test strategy has no adopter end-to-end.** For a plan whose entire thesis is adopter-side behavior, per-fix regression pins in this repo don't test the claim. Add a closing verification: `init` into a scratch repo (plus one real adopter) asserting caps seeded · hook chained (incl. a husky-repo case and a PATH-stripped-python case) · the over-cap grace path behaves as decided in #4 · the skew nudge fires · `/condense` reachable. Name the **whole-feature closing pass** (WORKFLOW:130) on the last slice against the Stage-1 job-to-be-done.

11. **Delivery ordering — Slice 4 is the vector, sequence it early.** Nothing in Slices 3/5/6/7/10 reaches the three live adopters until a release ships **and they re-run `init`**; the SessionStart advisor is **plugin-resident** (`${CLAUDE_PLUGIN_ROOT}`-rooted, plugin-distribution.md:22) so it reaches them on plugin update **without** a re-init. Move Slice 4 right after Slice 2, state the "release + re-init" dependency in Goals, and make remediating the three existing repos an explicit non-goal + ROADMAP line. Slice 4 must honor the advisor audience-split (0024 S3, plugin-distribution.md:23): nudges are **user-facing `systemMessage` only**; `additionalContext` stays the resume branch.

12. **Housekeeping.** Add the ROADMAP line **now** (the header defers it to "first slice-land"; Slice 1 already landed). Scope the Goals sentence *"commit-time … or CI/PR only"*: adopters are **commit-time only** — `deterministic-gates.md:7` records *"No adopter CI"*; CI is harness-self. Name which **0040-banked** ROADMAP items this plan absorbs (Slice 3 covers the `check_doc_budgets.py` `_repo_root()` anchor + the CWD-coupled `TestClosurePassD`; say whether Slice 8 absorbs the banked `nsAgent` bare-name fallback or leaves it). Specify the chained-wrapper semantics: run-both-and-report vs fail-fast, and that a budget failure must not mask the tree gate's message (one gate, one invariant — `deterministic-gates.md:8`).

13. **YAGNI — drop the caps-config `version` field** (§Architecture & holistic fit). `/doctor`'s documented reader-contract is a flat `{ "<relpath>": <max_bytes> }` map (`skills/doctor/SKILL.md:85`); a `version` key introduces a non-path key every reader must special-case, for no current need. If #4/#8 genuinely require a richer shape (a grace flag, a glob flag), spec that shape **once** and update doctor's contract in the same slice — don't add a version field for a hypothetical later migration.

### Sizing / completeness

- **Slice 1 — CI restored:** OK (landed; mark pending-merge per 9(e)).
- **Slice 2 — Release formalization:** **size OK** for one session (~7 files); **blocked on the #6 fork** — resolve publish ordering + refusal posture at Stage 5, and de-risk the throwaway tag. Not a split.
- **Slice 3 — Adopter doc-budgets:** **SPLIT REQUIRED — the largest miss in the plan.** As written it spans four contracts (release/init ship classes + Pass D + shipped-set test · the doctor reader-contract · the pre-commit wiring in a 79 KB prose skill · the enforcement-story copy sweep across ~8 shipped files) plus the script rewrite and its tests. Suggested split: **3a** generalize the script to config-driven + migrate this repo's own caps + tests (**no ship**, no wiring — fully complete, zero adopter surface); **3b** ship-class change + derived sets/Pass D/shipped-set test + `/doctor` + `/condense` rewiring + the DoD/adopter-note/PRODUCT_SPEC/INVARIANTS/CLAUDE.md/README copy sweep from #1; **3c** `init` seeding (caps + heritable glob + grace posture per #4) + the pre-commit chaining — **after** Slice 7's wrapper.
- **Slice 4 — Currency nudges:** OK; move earlier (#11).
- **Slice 5 — Copy honesty pass:** OK **only if** #1's sweep stays with Slice 3 — otherwise Slice 5 silently absorbs a second, larger job.
- **Slice 6 — Adopter loop closure:** OK size, but resolve the embedded fork (*"agent prompt pointers fixed **or** init writes the honesty block into the fence"*) before Spec — the second option changes the managed-fence contract (never-clobber, plugin-distribution.md:8) and is a materially bigger slice than the first.
- **Slice 7 — Team wiring:** OK; must precede 3c.
- **Slice 8 — Engine fixes:** OK (5 defects + pins). Constraints to carry into Spec: engine `*.js` **ASCII-only** and the cell-key `|` / status ` - ` delimiters are load-bearing (plugin-distribution.md:12).
- **Slice 9 — Eval leak:** OK, smallest slice. The leak is real (`docs/claugentic-ARCHITECTURE_TREE.md:141-145` names DP-1/SEC-1/REL-2/MAINT-1 by seed id); a grep-for-seed-ids test is a sound pin.
- **Slice 10 — WORKFLOW weight:** OK size **after** #7 is answered; today it is under-specified (no cap value, no pointer sweep, no ordering).

### Harness impact

- **DECISIONS (new/superseding lines):** the doc-budget hook posture (supersedes `doc-lifecycle.md:5`'s don't-re-break, if #1(b)) · the grace posture + its relation to rung 2 · the release-gating shape (which act is gated) · the DIH docs-scanner incident · the caps-config schema if #13 forces one.
- **INVARIANTS candidate:** *"exactly one cap source per repo — including harness-self"* (it hardens from a decision into a must-hold the moment the script ships).
- **Managed/shipped docs to change with the mechanics:** WORKFLOW DoD gate 4 + the adopter note + rungs 2/3 · `skills/doctor/SKILL.md` (reader-contract + gate table + per-script-presence rule) · `skills/condense/SKILL.md` · `skills/init/SKILL.md` · `docs/claugentic-PRODUCT_SPEC.md:42` · `README.md:57` · `CLAUDE.md:3` · both manifests' "deterministic architecture enforcement" copy.
- **New files → ARCHITECTURE_TREE:** `.github/workflows/release.yml`, this repo's caps config, any new test modules.
- **No new agent or standards module required.** Stage 9 at close should harvest: the *"a shipped gate's ship-class change is a four-contract change"* lesson (release/init contract) and the *"cap-at-current-size is a ceiling-raise"* rule.

---

## Spec  _(per slice, after Review passes — Stage 4)_
