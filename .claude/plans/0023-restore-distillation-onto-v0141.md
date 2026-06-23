# 0023 — Restore the dropped distillation work onto v0.1.41 (→ v0.2.0)

- **Status:** **Spec'd — all 5 slices (Stage 4), coherence = COHERENT** — **awaiting your combined spec approval** before any code
- **Resumable from:** user spec-approval gate (Stage 5) → implement Slice 1 → 2a → 2b → 3 → 4 on `restore/distillation-onto-v0141`
- **Blockers:** none (spec approval gates implementation)
- **Roadmap item:** — (reconciliation of the v0.1.40 distillation work dropped from `main` by the v0.1.41 history-rewrite; tracked by this plan)
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · `docs/claugentic-WORKFLOW.md` · `docs/claugentic-INVARIANTS.md` · prior plans 0020 (ruler) / 0021 (cleanup) / 0022 (advisor) [in git history] · evaluation workflow `distillation-reconciliation` (10 agents) + Stage-3 plan-review (both corrections folded below)

## Problem

On 2026-06-17 the distillation effort (plans 0020–0022) was **merged into `main`** via PR #1 + PR #2 (v0.1.40). On 2026-06-22 the v0.1.41 "first clean public release" was rebuilt starting from the **pre-distillation commit `03c404a`** and force-pushed during the privacy/client-name history-rewrite — silently **dropping both merge commits** (`a7d2151`, `df20ed1`). `merge-base(main, harness-distillation) = 03c404a`; the merge commits are no longer reachable from `main` (GitHub still serves `a7d2151`; the branch `harness-distillation@d541825` holds 100% of the work).

Net effect: **v0.1.41 ships without** the doc-budget "ruler" gate, the SessionStart advisor hook, the rejected-findings memory, and the refreshed PRODUCT_SPEC — and there is **no process guard** preventing this from recurring on the next release.

Concrete current-state evidence on `main`:
- `docs/claugentic-ARCHITECTURE_TREE.md` = **52,659 bytes, ~27–30 entries over 450 chars** (worst: `engine/build-item.js`=4394, `skills/build/SKILL.md`=3861, `engine/audit.js`=3451) — unbudgeted (dist's tree = 28,034 bytes, 8 over).
- `main:.claude-plugin/plugin.json` has **no `hooks` key**; `scripts/claugentic-advisor.py` absent.
- `main:skills/audit/SKILL.md` and `skills/build/SKILL.md` have **no rejected-findings memory**, while `main:skills/product/SKILL.md:67/97/104` carries the mirrored `rejected-proposals` — a user-dismissed audit finding **re-surfaces on every re-audit**.
- `main:docs/claugentic-PRODUCT_SPEC.md` is **byte-identical to `03c404a`** (never refreshed): the `product` command feature is missing from the feature headers (real drift), and honest-disclosure is a peer feature, not the spine.

## Goals / Non-goals

- **Goal:** restore the four distillation features onto v0.1.41 `main` as **v0.2.0**, preserving every v0.1.41 decision — especially the **de-correlation-claim scrub** (see Approach for what that precisely is).
- **Goal:** add a release-process guardrail so a stale-base build can never again silently drop merged work.
- **Non-goal:** a blind `git merge harness-distillation` (would mangle 18 both-edited files and re-introduce the scrubbed **de-correlation claim**).
- **Non-goal:** restoring dist's plan-0021 prose that re-asserts **model-family independence / de-correlation** (the specific claim main forbade) in the scrubbed-file set.
- **Non-goal:** removing or rewriting the **cross-model disclosure machinery** that v0.1.41 KEPT (the `sameModelTag`/`KNOWN_FAMILIES`/three-state tag in the engine + eval + tree descriptions) — out of scope.
- **Non-goal:** reverting any v0.1.41 work (model refactors, INVARIANTS registry, `build_release.py`, version-sync gate, CWD/UTF-8 hardening) — all preserved.
- **Non-goal:** re-litigating the distillation design itself (already plan-reviewed + shipped once); this is a reconciliation, not a redesign.

## Approach

**Hybrid selective restore**, never a merge — governed by a precise three-way classification (verified per file with `git diff 03c404a {main,dist} -- <path>`).

**The cross-model correction (Stage-3 finding #2).** v0.1.41 did **not** scrub "cross-model" wholesale — `git grep cross-model main` is live in `engine/{verify,audit,build-item}.js`, `eval/BASELINE.md:72` ("builder Fable 5"), the tree descriptions, etc. What v0.1.41 KEPT is the **disclosure machinery** ("a different model family — a reduction of shared-blind-spot risk, **not** a guarantee"; the three-state `sameModelTag`). What it **forbade** (`DECISIONS.md:9` "claims of model-family independence are forbidden"; `:21` removed the `fable` override) is the **de-correlation/independence CLAIM**, rewritten only in a bounded **SCRUBBED-FILE SET**:
> `.claude/agents/{honesty,architect,plan}-reviewer.md` · `product-critic.md` · `finding-verifier.md` (main-only) · `README.md` · `docs/claugentic-{WORKFLOW,PLAYBOOK,DECISIONS}.md` · `skills/{audit,build,product,init}/SKILL.md` · the one rewritten comment block in `engine/audit.js`.

**The governing rule:** in the scrubbed-file set, **start from main and never re-introduce the de-correlation claim**; the "cross-model" *machinery* term stays everywhere it already lives. The honesty check is therefore the **semantic** de-correlation claim (honesty-reviewer's job), scoped to that set — **not** a grep for "cross-model" (dozens of legitimate machinery hits remain on main).

**Rejected alternatives:** `git merge harness-distillation` → mangles 18 both-edited files, re-introduces the scrubbed claim. Per-commit cherry-pick → same conflicts, less control.

## Affected files

### A. DIST-ONLY — restore from `harness-distillation` (21 files; main == merge-base, so no conflict)

**New files (4):** `scripts/claugentic-advisor.py`, `tests/test_advisor.py`, `scripts/check_doc_budgets.py`, `tests/test_check_doc_budgets.py`.

**Modify-take-whole (1):** `tests/conftest.py` — dist's `_load_hyphenated` *replaces* main's inline tree-loader; safe to take whole (main == baseline) and **required by the advisor** (registers `advisor` for `import`).

**Net-new polish — small, verified machinery-consistent (15):** `engine/qa.js` (+14/−7, locate-via-tree pointer), `engine/verify.js` (+2), `.claude/agents/{blindspot-reviewer,implementer-architect,lens-reviewer,product-designer}.md` (1–3 lines each), `.claude/plans/TEMPLATE.md`, `docs/claugentic-PRODUCT.md`, `docs/claugentic-ROADMAP.md` (+12/−3), `docs/claugentic-standards/README.md`, `eval/BASELINE.md`, `eval/fixture-app/{README.md,main.py}`, **`.github/workflows/ci.yml`** (the doc-budget gate step — *belongs to Slice 2b*), **`CLAUDE.md`** (durable-context bullet + ledger-budget line — the ledger-budget half is *coupled to the ruler*; watch the 6000-B budget).

**Dist-only, substantive — restored *gated* in Slice 4 (1):** `docs/claugentic-PRODUCT_SPEC.md` — the product-spec refresh (the 16th dist-only modify; not "polish" — handled with its sibling-gating in Slice 4).

*Verified: only `ROADMAP`(+1), `qa.js`(+1), and `PRODUCT_SPEC`(+3) touch "cross-model" — all the KEPT machinery/disclosure term, not the forbidden de-correlation claim. (4 new + 1 conftest + 15 polish + 1 PRODUCT_SPEC = 21.)*

### B. BOTH-EDITED — hand-reconcile, start from main (18 files)

**Scrubbed-claim set (start from main; add dist's net-new ONLY; never regain the de-correlation claim):** `.claude/agents/{architect-reviewer,honesty-reviewer,plan-reviewer,product-critic}.md`, `README.md`, `docs/claugentic-{PLAYBOOK,WORKFLOW,DECISIONS}.md`, `skills/{audit,build,product,init}/SKILL.md`, `engine/audit.js` (6+/5−).
- Net-new to re-apply: rejected-findings memory (audit+build, mirroring product's rejected-proposals), durable-context/per-repo-block pointers, Stage-9 harvest line, git glosses, resume footers, init readiness summary — all onto main's wording.

**Structural converge (mergeable with care):**
- `scripts/claugentic-check_architecture_tree.py` — hand-port ONLY the form-budget block (`MAX_ENTRY_CHARS=450` L142, `_form_violations()` L178, over-budget check in `evaluate()` L362) onto main's hardened script (`import os` L39, `_repo_root` L380, `_force_utf8_output` L404, `os.chdir` L425). Reuse main's existing `import os`.
- `tests/test_check_architecture_tree.py` — keep main's `_repo_root` monkeypatch pins **and** add dist's `_form_violations`/`_entry` block.
- `docs/claugentic-ARCHITECTURE_TREE.md` — **regenerate fresh** against the merged file set (neither side's tree is correct; dist's describes dist's files), every entry ≤450 chars.

**Manifests:** `.claude-plugin/plugin.json` (append `hooks.SessionStart`; keep main's version until Slice 4), `.claude-plugin/marketplace.json` (keep `source: …@release`; bump at Slice 4). **Do not copy dist's `0.1.40` version line.**

### C. MAIN-ONLY — preserve untouched (10 files)
`.claude/agents/finding-verifier.md`, `.claude/settings.json`, `docs/claugentic-INVARIANTS.md`, `docs/claugentic-standards/_TEMPLATE.md`, `docs/claugentic-standards/docs-traceability.md`, `scripts/build_release.py`, `scripts/check_versions_synced.py`, `tests/test_build_release.py`, `tests/test_check_versions_synced.py`, `tests/workflows/agent-namespace.test.mjs`. *(dist's diff shows INVARIANTS.md/build_release.py as DELETED — a rebase-drop artifact; they're main-only net-new, never touched by a selective restore.)*

### New
- `docs/RELEASE_CHECKLIST.md` — the anchor-on-current-main + `git range-diff` drop-check guardrail. *(Already in `build_release.py` `DEV_ONLY_FILES` L50 → correctly excluded from the shipped release.)*

## Research / grounding

- **Files reviewed:** all 49 divergent files classified three-way (`git diff 03c404a {main,dist}` per file); `git grep -i cross-model main` (confirms the machinery is live on main → finding #2); dist-only triage (`--shortstat` + claim-line grep) shows the 16 omitted modifies are 1–14 lines and only 2 touch the machinery term.
- **Harness docs consulted:** `docs/claugentic-WORKFLOW.md` (DoD, Stage-9 (b) "a manual catch a gate could make") · `docs/claugentic-INVARIANTS.md` · `docs/claugentic-DECISIONS.md:9/:21` (the exact de-correlation-claim decision) · CLAUDE.md honesty positioning · memory [[harness-honesty-positioning]], [[harness-lost-merge-reconciliation]].
- **Findings:** all four features still-needed, none redundant; the dominant hazard is the **de-correlation claim** in the scrubbed set (not "cross-model" broadly); `_load_hyphenated` belongs to the advisor; `build_release.py` already excludes `RELEASE_CHECKLIST.md`.

## Risks & mitigations

- **Re-introducing the scrubbed de-correlation claim** (the highest-stakes failure; honesty-thesis violation) → **Mitigation:** honesty-reviewer over the diff (the real gate) **+ a per-file rule** — any file in the SCRUBBED-FILE SET must not regain a model-family-independence/de-correlation *assertion*; files main left cross-model are out of scope. *(Do NOT grep the diff for "cross-model" — dozens of legitimate machinery hits remain on main; if grepping, target the claim phrases — "different model family", "de-correlat", "independent … model" — and only within the scrubbed set.)*
- **PRODUCT_SPEC over-claim** — a restored criterion whose feature didn't land documents an absent capability. **Mitigation:** each PS-N must map to a feature that lands in this PR; verify in the spec.
- **Doc-budget green-at-close** — DECISIONS has only **5,017 B** headroom (34,983→40,000) and Slices 3+4 both append; CLAUDE.md has **2,788 B** (3,212→6,000) and Slices 1+3 append. **Mitigation:** each slice budgets the bytes it adds and shows the running total stays under cap; if a real compaction is needed it is a **named step**, never a runtime budget-bump (that is the laundering the gate exists to stop).
- **Tree-gate red until full regen** — the restored 450 budget red-flags ~27 entries. **Mitigation:** the form-budget gate and the full regen ship in the **same slice (2b)**.
- **Version drift** — borrowed manifests carry `0.1.40`. **Mitigation:** keep main's version throughout; single bump to `0.2.0` (both manifests) in Slice 4.
- **`@release` re-derivation on a stale base** reproduces the exact drop. **Mitigation:** rebuild from the NEW post-merge `main` HEAD; `git range-diff` drop-check before force-push.

## Test strategy

- All gates green at every slice close: `pytest` (advisor 28 + doc-budget + tree + version-sync + build_release + workflow tests), `python scripts/claugentic-check_architecture_tree.py` (now also the 450 form budget — green post-regen), `python scripts/check_versions_synced.py`, `python scripts/check_doc_budgets.py`, plus adopter lint/type/security.
- New tests arrive **with** their feature; the tree form-budget test block merges into `test_check_architecture_tree.py`.
- **Honesty regression check** (model-upheld): honesty-reviewer over the diff **+ the scoped per-file claim check** (scrubbed set only) — proves no v0.1.41 disclosure decision was reverted.
- **Drop-check** (the guardrail): `git range-diff` proves the restore branch contains every v0.1.41 commit AND the restored features.

## Decomposition (slices)

Sequential commits on **`restore/distillation-onto-v0141`** (branched off current `main`; never touch `main`); land together as one v0.2.0 PR. Each slice leaves the branch green.

- [ ] **Slice 1 — Release guardrail (root-cause fix).** Create `docs/RELEASE_CHECKLIST.md` (anchor on current `origin/main`; `git range-diff` drop-check before any `@release` force-push) + the CLAUDE.md one-liner (~+300 B, within budget) + **a base-ancestry refusal in `build_release.py`** (not optional — it's the only *mechanical* defense against recurrence; refuse to build if the base excludes any merge commit reachable from `origin/main`. Note: `--apply` builds the local `release` branch and does **not** push — the force-push to `@release` stays a manual, checklist-gated step, so the guard *reduces*, not eliminates, the manual risk) + a ROADMAP gate item noting the mechanical guard now exists. *Lands complete:* independent, small; could ship as its own first PR.
- [ ] **Slice 2a — The advisor (clean adds).** `git checkout harness-distillation --` the advisor script+test + `conftest.py`; append the `hooks.SessionStart` block to `plugin.json` (keep main's version); re-confirm the advisor's HONESTY REGISTER docstring matches main's post-v0.1.41 gate-set + INVARIANTS framing. *Lands complete:* 28 advisor tests pass, hook wired, **and the advisor's tree lines are added in 2a** — its scripts are tree-gate in-scope, so deferring them to 2b would leave the gate red at 2a close (violating "each slice leaves the branch green").
- [ ] **Slice 2b — The ruler + full tree regen.** `git checkout` the doc-budget script+test; hand-port the form-budget block onto main's hardened tree script; merge the two test blocks; add the `check_doc_budgets.py` CI step (+ job relabel); re-measure the 3 ledgers against the budget table; **regenerate the full `ARCHITECTURE_TREE.md` to ≤450/entry against the merged file set** (includes both lines' new files). *Lands complete:* the form-budget gate is green (regen + gate ship together), doc-budget gate green.
- [ ] **Slice 3 — The 0021 net-new nucleus (scrubbed-set careful).** For the scrubbed-claim set + the 16 dist-only polish files: start from main, re-apply ONLY net-new (rejected-findings memory, durable-context blessing + per-repo-block pointers, Stage-9 harvest line, git glosses, resume footers, init readiness summary, the locate-via-tree pointers). **Preserve main's de-correlation-claim position; restore the 16 dist-only polish files** (verified machinery-consistent). Run honesty-reviewer + the scoped claim-check over the diff. Budget the CLAUDE.md/DECISIONS bytes added. *Lands complete:* honesty-clean, gates green, no dist-only file silently dropped.
- [ ] **Slice 4 — PRODUCT_SPEC + version + final reconcile.** Restore PRODUCT_SPEC **trimmed so every criterion maps to a feature that landed** (PS-1 form-budget, PS-3 rejected-findings, PS-5 advisor, the `product` feature, honest-disclosure-as-invariant); cross-reference `INVARIANTS.md`; **record in `INVARIANTS.md` the "scrubbed-set must not regain the de-correlation claim" constraint** (provenance-stamped — the durable form of finding #2). Bump BOTH manifests to **0.2.0**; final tree/DECISIONS reconcile + dated decision entry (budget-checked). *Lands complete:* spec maps 1:1 to shipped reality, version-sync green. **Post-merge:** rebuild `@release` from the new `main` HEAD; `git range-diff` + verify it contains all four features + `INVARIANTS.md` before force-push.

---

## Review  _(filled by plan-reviewer, Stage 3)_

**Reviewer:** plan-reviewer (Opus 4.x), clean-context · separate-role. All claims below checked against the two branches with `git show`/`git diff`/`git grep` (evidence cited inline).

- **Verdict:** **CHANGES REQUIRED**

**What holds up (verified, do not re-do):**
- Git topology is exactly as stated: `merge-base(main,dist)=03c404a`; `a7d2151` not an ancestor of main; the 18 both-edited / 10 main-only counts are correct (`comm` over the two `git diff --name-only` sets).
- The model-disclosure conflict **is real and load-bearing in the agent role files**: `main:.claude/agents/honesty-reviewer.md` says *"separate specialist agent … same model … not an independent oracle"*; `harness-distillation:` of the same file says *"intended to run cross-model — a different model family than the builder."* Starting from main and re-applying only net-new for these files is the correct call.
- Tree form-budget hand-port is a genuine surgical merge, not a swap: main's script has the hardening (`import os` L39, `_repo_root` L380, `_force_utf8_output` L404, `os.chdir` L425) and **no** form budget; dist's adds `MAX_ENTRY_CHARS=450` L142 / `_form_violations` L178 / over-budget check in `evaluate()` L362. Line refs accurate. Running dist's `_form_violations` regex over main's live tree reproduces the offenders (≈27 in my run; top three `engine/build-item.js`=4394, `skills/build/SKILL.md`=3861, `engine/audit.js`=3451 — exactly the plan's numbers).
- Ledger sizes: `DECISIONS.md`=34,983 B / 40000 (exact match), `CLAUDE.md`=3,212 B / 6000, `ROADMAP.md`=4,766 B / 12000. `check_doc_budgets.py` budgets these three.
- `build_release.py` on main **already** lists `docs/RELEASE_CHECKLIST.md` in `DEV_ONLY_FILES` (L50) — the new guardrail file is correctly excluded from the shipped release.
- INVARIANTS.md / build_release.py "falsely DELETED" is benign and correctly diagnosed: they simply never existed on the dist branch (main-only net-new), so a *selective restore* never touches them.
- `conftest.py`'s `_load_hyphenated` is correctly attributed to the advisor (it registers both `check_architecture_tree` and `advisor`).
- CI reconciliation is a true pure-add: `check_versions_synced` predates the split (`03c404a` already has it), so dist's ci.yml diff is only `+ Managed-ledger byte-budget check` + the job relabel; main's gates job is byte-identical to baseline.

- **Required changes:**

  1. **Fix the file accounting — it is materially incomplete (highest-impact).** The plan's three buckets total 18+10+5-named, but the divergence has a **fourth bucket the plan never names: 21 dist-only files, of which only 4 are true additions** (`claugentic-advisor.py`, `check_doc_budgets.py`, `test_advisor.py`, `test_check_doc_budgets.py`). `conftest.py` is a **Modify (M), not a clean add** — main's copy equals baseline, so a verbatim drop happens to be safe, but it *replaces* main's inline tree-loader; relabel it "dist-only modify, safe to take whole" not "clean add (byte-identical)." The other **16 dist-only MODIFIED files are absent from the plan entirely**: `engine/qa.js`, `engine/verify.js`, `.claude/agents/{blindspot-reviewer,implementer-architect,lens-reviewer,product-designer}.md`, `.claude/plans/TEMPLATE.md`, `docs/{claugentic-ROADMAP,claugentic-PRODUCT,claugentic-standards/README}.md`, `eval/BASELINE.md`, `eval/fixture-app/{README.md,main.py}`. For **each**, the plan must state restore-net-new vs drop-as-obsolete vs preserve-main — silence is not a decision. Several carry real net-new capability (e.g. `engine/qa.js` adds the **full-mode QA driver**, `engine/verify.js`/`engine/audit.js`/`lens-reviewer` add the "locate via ARCHITECTURE_TREE" pointer); dropping them silently *loses distillation capability the plan claims to restore*. **Also: two BOTH-EDITED files are silently omitted from the hand-reconcile list — `engine/audit.js` (6+/5−) and `README.md` (11+/4−).** Add them.

  2. **Correct the central thesis and the honesty mitigation — main is NOT cleanly scrubbed of cross-model.** `git grep -i cross-model main` returns it live in `engine/verify.js`, `engine/audit.js` (e.g. `audit.js:955` *"the cross-model judge — by default a different model family than the builder"*), `engine/build-item.js`, `docs/claugentic-WORKFLOW.md` (in disavowal context), `eval/BASELINE.md:72` (*"builder Fable 5"* — the exact fable framing), plus several docs/tests. v0.1.41 scrubbed the **agent role files + finding-verifier.md + some prose** but left the **engine layer and eval docs** claiming cross-model. Consequences: (a) the plan's premise *"main's framing supersedes the C3 cross-model trims"* is only half-true — restoring dist's engine/eval edits on top of a still-cross-model main may be *consistent with main*, so the blanket "drop all cross-model" rule in Slice 3 is wrong as stated and must be scoped to the files main actually scrubbed; (b) the **grep-for-`cross-model` mitigation is unusable as written** — it will fire on dozens of legitimate main-retained occurrences and train the reviewer to ignore it. Replace it with: *honesty-reviewer over the diff* (the real gate) **+** a **per-file** rule — "any file main scrubbed (the agent role files + the docs listed) must not regain cross-model/fable wording; files main left cross-model are out of this restore's scope." Name the scrubbed-file set explicitly so the check is decidable.

  3. **Split Slice 2 — it is over one session and bundles unrelated verticals.** As written it does: 4 clean adds (~1093 LoC) + conftest replace + the form-budget hand-port (+60 onto a hardened script) + the tree-test block merge (+116 into main's `_repo_root`-pinned test) + the CI step + the `plugin.json` hooks block + a 3-ledger doc-budget reconcile + **a full ARCHITECTURE_TREE regeneration rewriting ~27 over-budget entries (four of them 3000–4400 chars) to ≤450 each, against main's *current* file content** (note: dist's regenerated tree describes dist's files — e.g. its two-mode qa.js — and **cannot be copied**, because main's files differ; this is a fresh, judgment-heavy regen). That tree regen alone is a session. **Split:** Slice 2a = advisor (clean adds + conftest + `plugin.json` hook + advisor tests); Slice 2b = the ruler (form-budget hand-port + test-block merge + CI doc-budget step + doc-budget reconcile) **and in the same slice the full tree regen to ≤450/entry** (the gate cannot be green until the regen lands, so they must ship together). Confirm each half is independently green.

  4. **Make the doc-budget green-at-close explicit per slice, with measured headroom.** DECISIONS has only **5,017 B** of headroom (34,983 → 40,000) and **Slices 3 and 4 both append** to it; CLAUDE.md additions (Slice 1 + Slice 3) eat into 2,788 B of headroom. The plan must (a) budget the bytes each slice adds to DECISIONS/CLAUDE.md and show the running total stays under cap, or (b) pre-commit to a compaction pass. Do not leave "trim or adjust the budget with a recorded reason" as a runtime escape hatch — adjusting the budget to pass is the exact laundering the gate exists to prevent; if a real compaction is needed, plan it as a named step.

  5. **State the version-line discipline for the borrowed files.** Both `plugin.json` and `marketplace.json` on dist carry `0.1.40`; the implementer who ports the hooks block / marketplace edits must **not** copy dist's version line — version stays at main's until the single Slice-4 bump to `0.2.0` (both manifests together, or `check_versions_synced` fails). Call this out so a verbatim port doesn't drift the version mid-stream.

- **Sizing/completeness:**
  - **Slice 1 (guardrail):** OK — small, independent, vertically complete; could ship as its own PR as the plan says.
  - **Slice 2 (ruler + advisor):** **SPLIT REQUIRED** → 2a (advisor) + 2b (ruler + full tree regen). See change 3. The tree regen against main's real content is the dominant cost and must not be under-scoped as "regenerate the tree."
  - **Slice 3 (0021 nucleus):** OK on size, but **blocked on change 1 + 2** — its scope is undefined until the 16 dist-only modifies and the scrubbed-file set are pinned down; "drop all cross-model" is too blunt as written.
  - **Slice 4 (PRODUCT_SPEC + version):** OK on size; the PS-N-maps-to-a-landed-feature gate is sound. Verify the `product` feature header and honest-disclosure-as-invariant land before claiming them in the spec.

- **Harness impact:**
  - **New STANDARD / gate item (ROADMAP):** the root cause — a force-push from a stale base silently dropping merged commits — is exactly the Stage-9 (b) case (a manual catch a gate could make). The `RELEASE_CHECKLIST.md` + `git range-diff` guardrail is the right *altitude* (model-upheld checklist, honestly not a mechanical gate), but log a ROADMAP gate item for a future mechanical `build_release.py` base-ancestry refusal so it doesn't stay forever model-upheld. The plan's "(optional) base-ancestry refusal" should be **not optional** if it's cheap — it's the only mechanical defense against recurrence.
  - **DECISIONS entry (e):** one dated line recording the drop + the hybrid-restore choice (the plan has this).
  - **INVARIANTS (f):** if honest-disclosure-as-invariant is restored into PRODUCT_SPEC and cross-referenced, record the "scrubbed files must not regain cross-model wording" constraint in `docs/claugentic-INVARIANTS.md` with provenance — that is precisely a "must stay true or the honesty thesis breaks" invariant, and it is the durable form of change 2.
  - **No new agent needed** — honesty-reviewer + architect-reviewer cover the Verify trust-surface.

---

## Revision log  _(author response to Stage-3 — folded 2026-06-22)_

All five required changes folded; awaiting re-review.
1. **File accounting** → §Affected files now enumerates all 21 dist-only (4 new + `conftest` modify-take-whole + 16 polish, each with a disposition), all 18 both-edited (incl. the previously-omitted `engine/audit.js` + `README.md`), and 10 main-only. Dist-only triage verified the 16 polish files are 1–14 lines, machinery-consistent.
2. **Cross-model thesis** → §Approach replaces "drop all cross-model" with the bounded SCRUBBED-FILE SET + the de-correlation-CLAIM-vs-machinery distinction; §Risks/§Test-strategy replace the grep mitigation with honesty-reviewer + a scoped per-file claim-check.
3. **Slice split** → Slice 2 → **2a (advisor)** + **2b (ruler + full tree regen, shipped together so the gate is green)**.
4. **Doc-budget discipline** → §Risks + each slice now budget the DECISIONS/CLAUDE.md bytes (5,017 B / 2,788 B headroom); compaction is a named step, never a runtime budget-bump.
5. **Version-line discipline** → §Affected files + Slice 4 pin: keep main's version; single 0.2.0 bump (both manifests) at Slice 4.
- Harness impact: base-ancestry refusal in `build_release.py` made **non-optional** (Slice 1) + ROADMAP gate item; INVARIANTS entry for the scrubbed-set constraint added to Slice 4.

---

### Re-review  _(plan-reviewer, Stage-3 second pass — 2026-06-22)_

**Reviewer:** plan-reviewer (Opus 4.x), clean-context · separate-role. Every claim below re-checked against both branches (`git diff 03c404a {main,dist}`, `comm` over the name-only sets, `git grep -i cross-model main`, per-file `--shortstat`).

- **Verdict:** **CHANGES REQUIRED** — one residual accounting inconsistency introduced by the fold; everything else from the first pass is correctly resolved.

**Confirmed RESOLVED (re-verified, do not re-do):**
- **Buckets exact.** `comm` over the two `git diff --name-only 03c404a {main,dist}` sets returns **21 dist-only / 18 both-edited / 10 main-only** — byte-for-byte the plan's lists. The two previously-omitted both-edited files are now present and correctly sized **against `main..dist`** (the reconcile-relevant base): `engine/audit.js` = 6+/5− (matches; `base..main` is 5+/4−, `base..dist` is +2 — the plan correctly uses `main..dist`), `README.md` = 11+/4− (matches). 10 main-only verified.
- **Cross-model thesis (finding #2) — sound.** `git grep -i cross-model main` is live across `engine/{verify,audit,build-item,qa}.js`, `eval/BASELINE.md:72` ("builder Fable 5"), the tree descriptions, PRODUCT_SPEC, WORKFLOW — confirming the KEPT *machinery*. Scrubbed-file set spot-checked: `main:honesty-reviewer.md` + `main:plan-reviewer.md` genuinely carry the scrubbed wording ("the same model … not of model"), while `dist:` of each asserts "**a different model family than the builder — cross-model**" (the forbidden de-correlation claim). `eval/BASELINE.md` is correctly OUTSIDE the scrubbed set (it's a dist-only polish file; main itself retains "Fable 5"/"cross-model" there as eval machinery, dist adds no de-correlation *claim*). The honesty mitigation is now the scoped **semantic** claim-check (honesty-reviewer over the diff + claim-phrase targeting within the scrubbed set), not a blunt `cross-model` grep. Resolved.
- **Slice split — done.** 2a (advisor + conftest + hook) and 2b (ruler hand-port + test-block merge + CI step + doc-budget reconcile + **full tree regen, shipped in the same slice as the form-budget gate**). Resolved — see one sub-note below.
- **Doc-budget — measured & carried.** DECISIONS = 34,983 B (headroom **5,017**), CLAUDE.md = 3,212 B (headroom **2,788**) — both exact; `DOC_BUDGETS` = 40000/6000/12000 confirmed. Per-slice budgeting + compaction-as-a-named-step (never a runtime bump) is in §Risks and the slices. Resolved.
- **Version-line — pinned in both load-bearing places.** main = 0.1.41 (both manifests), dist = 0.1.40; the "keep main's version, single 0.2.0 bump both manifests at Slice 4, preserve `@release` source" rule appears at §Affected-files B (where the manifests are touched) **and** Slice 4. Resolved.
- **Harness impact follow-through — present.** `build_release.py` base-ancestry refusal is **non-optional** (Slice 1) + ROADMAP item; INVARIANTS scrubbed-set entry is in Slice 4 (provenance-stamped). Both land where claimed.

- **Required changes (1):**

  1. **Fix the section-A count: it says "16" but lists 15, and the 16th — `docs/claugentic-PRODUCT_SPEC.md` — is a dist-only MODIFY that the triage claim silently excludes.** The actual dist-only-modified set (21 − 4 new − conftest) is **16 files including `docs/claugentic-PRODUCT_SPEC.md`**; the §Affected-files A "Net-new polish (16)" bullet (L50) enumerates only the other **15**. Two concrete consequences: **(a)** PRODUCT_SPEC has a **split status** — it is a dist-only modify but is handled in Slice 4, not in the §A "restore the polish" path or Slice 3 — so state that explicitly (e.g. "16th dist-only modify, dispositioned in Slice 4, not in the polish-restore batch") rather than dropping it from the count; **(b)** the inline triage claim *"only `ROADMAP`(+1) and `qa.js`(+1) touch 'cross-model'"* is **true only for the 15 it lists** — `dist:PRODUCT_SPEC` adds **+3 'cross-model' lines** (`git diff 03c404a dist -- docs/claugentic-PRODUCT_SPEC.md`). Those +3 are verified **KEPT-machinery** framing ("cross-model is claimed only on confirming different-family self-reports") and carry **no** de-correlation *claim*, so the restore is safe — but the triage sentence must say "of the 16, PRODUCT_SPEC also touches the machinery term (machinery, not the claim); its trim is Slice 4's job." Leaving the count at "16" while listing 15 and asserting a machinery-triage that omits the 16th is the exact silent-disposition gap the first pass's change #1 targeted; close it by name. *(No capability is lost — PRODUCT_SPEC is genuinely restored in Slice 4 — this is an accounting/claim-accuracy fix, not a missing-feature fix.)*

- **Sizing/completeness (per slice):**
  - **Slice 1 (guardrail):** OK — small, vertically complete; base-ancestry refusal correctly non-optional. *(Honesty note, not a blocker: `build_release.py --apply` builds the LOCAL `release` branch and does NOT push (L23–24); the mechanical refusal guards the build, but the actual `@release` force-push stays manual — so Slice 1's spec must not let "mechanical guard exists" read as "recurrence is now mechanically impossible." The plan's "only *mechanical* defense" wording is accurately scoped; keep it that way in the spec.)*
  - **Slice 2a (advisor):** OK — but tighten one branch. `scripts/claugentic-advisor.py` is in-scope for the tree gate (`INCLUDE_GLOBS` watches `scripts/**/*.py`), so it **must get a tree entry in 2a** for the gate to be green at 2a close. The "Lands complete" line offers "…*or* add them here" alongside deferring to 2b's regen — but deferring leaves the gate **red** at 2a, contradicting "each slice leaves the branch green" (L94). Drop the defer option: pin "add the advisor's tree line in 2a." (`tests/test_advisor.py` is out-of-scope — tests/ isn't globbed — so only the script needs the entry.) Minor; in-scope of the existing slice, no re-split.
  - **Slice 2b (ruler + full tree regen):** OK — regen + form-budget gate ship together (the gate can't be green before the regen), which is the correct coupling.
  - **Slice 3 (0021 nucleus, scrubbed-set):** OK on size; scope is now decidable (scrubbed-file set named, 15 polish files dispositioned). Will be fully unblocked once required change 1 lands PRODUCT_SPEC's status unambiguously.
  - **Slice 4 (PRODUCT_SPEC + version + INVARIANTS):** OK — PS-N-maps-to-a-landed-feature gate sound; verify the `product` feature header + honest-disclosure-as-invariant land before the spec claims them.

- **Harness impact:** unchanged from first pass and all present in the revision — ROADMAP gate item for the future mechanical base-ancestry guard, DECISIONS line for the drop + hybrid-restore choice, INVARIANTS entry for the scrubbed-set constraint (Slice 4). No new agent needed.

---

## Spec  _(Stage 4 — written by the `spec-distillation-restore` workflow; coherence pass = COHERENT)_

> Cross-slice coherence (verified): budgets stay under cap (CLAUDE.md →3,796/6,000 · DECISIONS →~36,877/40,000 · ROADMAP well under 12,000); every PS-N maps to a feature an earlier slice ships; 2b's regen covers the files 2a/3 add; no slice re-introduces the de-correlation claim. Verbatim restores use `git checkout harness-distillation -- <path>` (main == merge-base for those files → byte-identical to the reviewed-and-shipped distillation code).

### Slice 1 — Release guardrail (root-cause fix)
- **Plain English:** Fixes the root cause — a release rebuilt from a stale base + force-pushed, silently dropping merged PRs. Three layers: (1) **extends** the *existing* `docs/RELEASE_CHECKLIST.md` (anchor-on-`origin/main` + `git range-diff` drop-check); (2) a **non-optional mechanical** base-ancestry refusal in `build_release.py --apply`; (3) discoverability (a CLAUDE.md bullet + a ROADMAP item). **You're accepting:** the guard *reduces, not eliminates* recurrence — `--apply` builds the LOCAL `release` branch and does not push, so the force-push stays a manual checklist step, and the guard reads the local `origin/main` tracking ref (operator must `git fetch` first).
- **Files & changes:**
  - `docs/RELEASE_CHECKLIST.md` — **EXTEND** (it exists, 1,393 B; preserve its 3 sections verbatim). Append two sections: *"Anchor the release on the live tip"* (fetch → ff-only pull → `--apply`) and *"Drop-check before the force-push"* (`git range-diff origin/release...release` + a `git log --not release` shipped-path check), closing with an honest-scope note.
  - `scripts/build_release.py` — add `UPSTREAM_REF = "origin/main"` + `_dropped_merges(root) -> list[str] | None` (`git rev-list --merges origin/main --not HEAD`; `None` on a missing ref = fail-loud). Call it as the **first** guard in `_apply()`: return 1 (stderr) on `None` (ref absent → "run `git fetch`") or a non-empty list (naming the dropped merges). Hoist the existing `root = _repo_root()` into the guard. Add a one-line comment pinning "base == HEAD because `_apply` builds from HEAD."
  - `tests/test_build_release.py` — add `TestBaseAncestryGuard` (pure, monkeypatched `_git`): empty→`[]`, two SHAs→list, missing ref→`None`.
  - `CLAUDE.md` — one bullet under "## Harness Discipline" pointing at the checklist (**+312 B → 3,524/6,000**).
  - `docs/claugentic-ROADMAP.md` — one bullet under "### Later — surfaced by real use": the mechanical half is DONE, the force-push stays model-upheld (does **not** claim recurrence is impossible).
  - `docs/claugentic-ARCHITECTURE_TREE.md` — refresh the `build_release.py` + `RELEASE_CHECKLIST.md` entries for accuracy (hygiene — the gate checks presence/existence/drift, **not** description quality, so this is not gate-required; keep each ≤450 chars).
- **Acceptance:** `RELEASE_CHECKLIST.md` has 3→3+2 `##` sections incl. `git range-diff` + `origin/main`; `build_release.py` defines `_dropped_merges` using `--merges … --not HEAD`; `pytest tests/test_build_release.py` green incl. the new class; full `pytest` + tree gate + version-sync green; **no version change** (both manifests 0.1.41); `RELEASE_CHECKLIST.md` still STRIP in the dry-run.
- **Budget:** CLAUDE.md +312 (→3,524); ROADMAP +~620; DECISIONS +0. **Deps:** lands first; independent (could be its own PR).
- **Open question (needs your nod):** the guard reads the *local* `origin/main` ref (no auto-fetch) — deliberately, to keep the build tool offline/deterministic (KISS); the `git fetch` stays the operator's checklist step 1. Confirm that trade-off.

### Slice 2a — The SessionStart advisor (clean adds)
- **Plain English:** Wires the no-nag, fail-safe advisor: once per session it derives ONE "where you left off / what's next" line from state the harness already records (ROADMAP backlog fences, in-flight plans, adopter fence version) and injects it as a "Derived suggestion (confirm before acting):" hint — silent on a clean repo, never a gate, swallows all errors to exit 0. **You're accepting:** model-upheld guidance, not a guarantee; taking `conftest.py` whole is safe only because main's copy == merge-base (verified empty diff).
- **Files & changes:** `git checkout harness-distillation -- scripts/claugentic-advisor.py tests/test_advisor.py tests/conftest.py` (verbatim). Append the `hooks.SessionStart` block (matcher `startup|resume`, command `python "${CLAUDE_PLUGIN_ROOT}/scripts/claugentic-advisor.py"`) to `.claude-plugin/plugin.json` — **keep main's `"version": "0.1.41"`**. Add two ≤450-char `ARCHITECTURE_TREE.md` entries (advisor.py + test_advisor.py) and refresh the now-stale `conftest.py` entry.
- **Acceptance:** 28 advisor tests pass; full `pytest` green (proves conftest swap kept `check_architecture_tree` importable); `plugin.json` parses with `version==0.1.41` AND the hook wired; version-sync green; tree gate green; no de-correlation claim added (advisor touches no scrubbed-set file).
- **Budget:** none (touches no gated ledger). **Deps:** after Slice 1; 2b's regen carries its tree entries forward.

### Slice 2b — The ruler + full tree regen
- **Plain English:** Lands the doc-budget "ruler" gate (flags, never edits, when a managed ledger outgrows its byte budget) + the per-entry 450-char tree **form** budget, hand-ported onto main's hardened tree script, **and** regenerates the whole `ARCHITECTURE_TREE.md` to ≤450/entry in the same slice (the gate can't be green until the regen lands). **You're accepting:** the regen is judgment-heavy — ~27 over-budget entries (4 of them 3,000–4,400 chars) distilled to one tight line each *without losing meaning*; dist's tree can't be copied (it describes dist's files); the form budget measures *length only*, so vague-but-short still passes and must be reviewer-caught.
- **Files & changes:** `git checkout harness-distillation -- scripts/check_doc_budgets.py tests/test_check_doc_budgets.py` (verbatim; `DOC_BUDGETS = {CLAUDE.md:6000, DECISIONS:40000, ROADMAP:12000}`). **Hand-port** onto main's `claugentic-check_architecture_tree.py` (reusing main's `import os`): `MAX_ENTRY_CHARS=450`, `ENTRY_LINE_PATTERN`, `_form_violations()`, and the `over_budget` call+report in `evaluate()` (order: missing→stale→over_budget→drift) — **leave `_repo_root`/`_force_utf8_output`/`os.chdir` untouched**. Merge dist's `TestFormBudget` + `_entry` block at the **end** of main's `test_check_architecture_tree.py` (after `TestCwdIndependence`, keeping main's `_repo_root` pins). Add the `check_doc_budgets.py` CI step + relabel the gates job. **Regenerate** the full tree against the merged set (incl. advisor + doc-budget files + main-only `INVARIANTS.md` + `test_build_release.py`).
- **Acceptance:** doc-budget script+test byte-identical to dist + pass; the 3 ledgers each under budget; main's tree-script hardening intact (`import os` once; `_repo_root`/`_force_utf8_output`/`os.chdir` each present); `MAX_ENTRY_CHARS=450`+`_form_violations` present; `pytest test_check_architecture_tree.py` green incl. `TestFormBudget` (8); CI relabel matches dist; **tree gate green with zero over-budget**; every merged-set file indexed; version-sync green; full `pytest` + node workflow tests green.
- **Budget:** none (writes no ledger bytes; tree net-shrinks). **Deps:** after 2a; form-gate + regen ship together.

### Slice 3 — The 0021 net-new nucleus (scrubbed-set careful)
- **Plain English:** Re-applies the dropped plan-0021 polish onto **main's** wording, restoring genuinely-missing capability while never reviving the de-correlation claim. **You're accepting:** the highest-stakes manual work — each scrubbed-set file starts from main and gains *only* net-new; the honesty-reviewer + a scoped semantic claim-check (not a `cross-model` grep) is the gate.
- **Files & changes:**
  - **Net-new capability (re-author onto main):** the **rejected-findings memory** — restore dist's `<!-- harness-audit:rejected-findings -->` fence + "### The rejected-findings memory" section in `skills/audit/SKILL.md` (dist ~L336) and the "Honor the rejected-findings memory" step in `skills/build/SKILL.md` (pull verbatim via `git diff 03c404a harness-distillation -- skills/audit/SKILL.md skills/build/SKILL.md` — these blocks are framing-independent); the **durable-context blessing** bullet in `CLAUDE.md` (+272 B) + the "also consult the CLAUDE.md per-repo harness block" pointer on `honesty-reviewer.md`/`architect-reviewer.md` Read-first lines; the Stage-9 harvest-visibility line; plain-English git glosses (land/push) + product/audit resume footers + the init one-line readiness summary.
  - **Preserve main untouched** (no net-new needed): `plan-reviewer.md`, `product-critic.md`, `docs/claugentic-WORKFLOW.md`, `README.md`/`engine/audit.js` model-claim regions — **do NOT** apply dist's README "Model-upheld" rewrite or the `engine/audit.js` MODELS-comment rewrite (those revive the scrubbed claim).
  - **13 dist-only polish files** (`git checkout harness-distillation --` each; main == merge-base, verified machinery-consistent): `engine/qa.js`, `engine/verify.js`, `.claude/agents/{blindspot-reviewer,implementer-architect,lens-reviewer,product-designer}.md`, `.claude/plans/TEMPLATE.md`, `docs/claugentic-PRODUCT.md`, `docs/claugentic-standards/README.md`, `eval/BASELINE.md`, `eval/fixture-app/{README.md,main.py}` — plus a **hand-merge** of dist's ROADMAP `+12/−3` that **preserves Slice 1's added bullet**.
  - `docs/claugentic-DECISIONS.md` — append 2 lines (rejected-findings ~828 B + durable-context ~466 B = **+1,294 B**). Refresh the `qa.js` tree entry if its description changed (≤450).
- **Acceptance:** scoped claim grep (`different.*family than|de-correlat|independent.*model`, scrubbed set) zero hits; honesty-reviewer = CLEAN over the diff; `main:audit/SKILL.md` had 0 rejected-findings hits, branch now has the fence (mirrors product's `rejected-proposals`); budgets pass; all gates green; ROADMAP retains Slice 1's bullet.
- **Budget:** CLAUDE.md +272 (→3,796); DECISIONS +1,294 (→~36,277). **Deps:** after 1/2a/2b; before 4.

### Slice 4 — PRODUCT_SPEC + version + final reconcile
- **Plain English:** Makes the harness's own spec tell the truth about v0.2.0 and stamps the release. Restore the PRODUCT_SPEC refresh (already trimmed-to-landed — every PS-N maps to a shipping feature), add the missing `product` feature header, promote honest-disclosure to the spine, record the scrubbed-set rule as a durable **invariant**, bump **both** manifests to **0.2.0**, append one dated DECISIONS line, reconcile the tree. **Post-merge:** rebuild `@release` from the NEW main + `git range-diff` before force-push.
- **Files & changes:** restore `docs/claugentic-PRODUCT_SPEC.md` verbatim from dist (6,172→9,167 B; its 3 "cross-model" lines are KEPT machinery — `grep` confirms no de-correlation claim before restoring). Append the "## The scrubbed-file set must never regain the de-correlation claim" section to `docs/claugentic-INVARIANTS.md` (Invariant/Why/Provenance, dated, naming the set). Bump `plugin.json` + `marketplace.json` version `0.1.41→0.2.0` (keep `source: …@release`). Append one dated `DECISIONS.md` line (~600 B) recording the drop + hybrid-restore + guardrail. Final tree touch-up of the PRODUCT_SPEC + INVARIANTS entries (≤450; skip if 2b's regen already added INVARIANTS).
- **Acceptance:** PRODUCT_SPEC byte-identical to dist; `test_product_spec_template.py` green (PS-1..PS-5, schema, `check==manual`); each PS-N ⇔ a present capability; scoped claim grep empty; INVARIANTS section present + dated; version-sync = both 0.2.0; marketplace source unchanged; doc-budget green (DECISIONS under cap after 3+4 — **named compaction** if breached, never a budget-bump); tree + full `pytest` green; honesty-reviewer CLEAN. **Post-merge:** `git range-diff`/containment proves `@release`'s base contains the four features + INVARIANTS + the bump before force-push.
- **Budget:** DECISIONS +~600 (→~36,877, ~3,123 B headroom); CLAUDE.md +0. PRODUCT_SPEC/INVARIANTS unbudgeted (dev-only, stripped from the install). **Deps:** last slice; after all others.
- **Open question (implementation-time):** measure live DECISIONS size after Slice 3 before appending; if 3+4 would breach 40,000 B, the named compaction is a Slice-4 sub-step.
