# 0034 — Release-methodology consolidation (Track B: one annotated manifest, provable no-op)

- **Status:** Draft (fine-tuning pass; verified against source 2026-07-03)
- **Resumable from:** Slice 1 — not started.
- **Blockers:** none. Additive from the shipped base; does NOT touch 0029/0030's landed work.
- **Disposition at close:** completes (deleted, git history keeps it) once every slice is done / deferred (a ROADMAP line) / rejected (a DECISIONS line).
- **Roadmap item:** `docs/claugentic-ROADMAP.md` → *Release/init-contract completeness gate* (this partially delivers it) + the FINETUNING-INPUTS Track-B design.
- **References:** `.claude/plans/FINETUNING-INPUTS.md` → Track B + VERIFIED section · `docs/claugentic-INVARIANTS.md` → *The release strips ⇒ init recreates ⇒ nothing dangles* · `scripts/build_release.py` · `scripts/check_shipped_content.py` · `scripts/check_versions_synced.py` · `tests/test_build_release.py`.

## Problem

**One fact — the ship/strip partition — is re-expressed by hand in ~7 places.** `build_release.py` `DEV_ONLY_FILES/DIRS` is the source of truth; it is then re-hand-partitioned three more ways in `check_shipped_content.py` (`_INIT_CREATES` · `HARNESS_SELF_SCRIPTS` · `_DANGLE_EXCLUDED`), echoed in the `init` managed-set table, and pinned again in `tests/test_build_release.py`. **Adding one dev-only doc that init recreates = 3–5 edits across 3–4 files** (0030 Slice 2 hit exactly this — `_CHARTER.md` needed the seed + the `_INIT_CREATES` entry + the test pin). Nothing cross-checks that `init` can actually (re)create everything the release strips — the release/init contract (`INVARIANTS.md`) is prose-only.

## Goals / Non-goals

- **Goal:** Make the ship/strip partition **one class-annotated manifest** in `build_release.py` — a `path → recreate-class` dict (`init-seed` · `init-gen` · `self-gate` · `config` · `dangle`) as the ONLY authored semantics; the three `check_shipped_content.py` hand-lists become **derived** from it.
- **Goal:** Add the **referential-closure run-gate** (`NEEDS ⊆ HAS`): `HAS = shipped ∪ init-created`; assert every `init-seed`/`init-gen` path is actually producible by `init` (its `_X.md` seed ships, OR it's in init's managed-set table, OR it's a known generator output). This **mechanizes the INVARIANT** that is prose-only today.
- **Goal:** **Provable no-op** — the shipped file set is **byte-identical before/after** (the load-bearing safety property; asserted by an equality check during migration).
- **Non-goal:** Folding `check_versions_synced.py` in — **it stays a SEPARATE gate** (verified: folding adds dual-manifest JSON parsing = scope creep + risk; the two-manifest agreement check is orthogonal). *(Corrects the dossier, which said "fold version-sync in.")*
- **Non-goal:** A version "third-drift-axis" detector — **REFUTED** (main + release both 0.3.1, in sync; the gate works as designed).
- **Non-goal:** Any adopter-facing change — this is internal harness tooling; adopters never see these scripts (all `DEV_ONLY`/stripped).
- **Non-goal:** Changing what ships. The partition's *membership* + recreate-class stays a human `[J]` judgment (one declared list); only the *re-derivation* is mechanized.

## Approach

Migrate in **safety-netted steps, each green before the next** (the whole point is a provable no-op):
1. **Annotate** — convert `DEV_ONLY_FILES` into a `DEV_ONLY_PATH_CLASSES` dict (`path → class`); keep `DEV_ONLY_DIRS`. Derive `is_dev_only()` / `classify()` from the dict's keys. **Assert the shipped set is unchanged** vs the pre-change `classify()` (a migration test).
2. **Derive-alongside** — in `check_shipped_content.py`, compute `_INIT_CREATES` / `HARNESS_SELF_SCRIPTS` / `_DANGLE_EXCLUDED` from the class annotations, **alongside the old hand-lists**, and assert they're equal (the safety net). Keep both until equality holds.
3. **Delete** the three hand-lists once the derived sets prove equal.
4. **Closure check** — add `NEEDS ⊆ HAS` to `check_shipped_content.py` (or a sibling): derive `init_creates`/`self_gates`/`dangle_set` from classes; assert every `init-seed`/`init-gen` path is producible by init; **honor the `INCLUDE_GLOBS` never-clobber carve-out** (the tree-script's glob assignment is adopter-owned — exclude it from closure exactly as init's body-compare does). May surface a real latent gap — good.
5. **Collapse the test pins** to `classify` + the closure assertion.

**`check_versions_synced.py` is untouched** (separate gate). The rename to `release_gate.py` (the dossier's naming) is **optional / deferred** — merging file names is cosmetic and risks churn; the value is the annotated manifest + closure check, which can live in the existing `check_shipped_content.py`. *(Confirm at Spec — prefer keeping the existing filename to minimize the DoD-gate-list / RELEASE_CHECKLIST / tree churn.)*

## Architecture & holistic fit

- **Codebase fit:** pure harness-self tooling (`scripts/` + `tests/`), all `DEV_ONLY`/stripped — zero adopter surface. SRP: one authored manifest (the `[J]` membership), derivations are DRY off it. DIP: the derived sets depend on the manifest, not vice-versa.
- **Quality dimensions:** `maintainability-structure` (primary — DRY the 7→1) · `testing` (the migration equality net + closure assertion) · `docs-traceability` (the INVARIANT now mechanized; RELEASE_CHECKLIST/DoD references stay accurate).
- **Honesty:** the closure gate pins `NEEDS ⊆ HAS` **mechanically**; the force-push + eval-drift steps stay `[J]`/model-upheld (a script can't judge them) — the RELEASE_CHECKLIST note must keep saying so. Never claim the gate makes the release "fully" content-enforced.
- **Future-proofing:** the class dict is the natural home for a future new class; the closure check is the natural home for the ROADMAP *completeness gate*'s "forgot-to-register fails loud" behavior — but build only what's asked (no build→init→diff round-trip test now unless trivial).

## Affected files

- `scripts/build_release.py` — `DEV_ONLY_FILES` → `DEV_ONLY_PATH_CLASSES` dict; `is_dev_only`/`classify` read the keys; `DEV_ONLY_DIRS` unchanged. Add a `recreate_class(path)` accessor.
- `scripts/check_shipped_content.py` — derive `_INIT_CREATES`/`HARNESS_SELF_SCRIPTS`/`_DANGLE_EXCLUDED` from `build_release.recreate_class`; delete the hand-lists; add the `NEEDS ⊆ HAS` closure check (honor `INCLUDE_GLOBS` carve-out).
- `tests/test_build_release.py` + `tests/test_check_shipped_content.py` — a migration equality test (shipped set byte-identical); a derived-vs-old equality test (dropped after step 3); collapse the seed pins to `classify` + closure assertions.
- `docs/claugentic-INVARIANTS.md` — update the release/init-contract invariant to note the closure check now mechanizes `NEEDS ⊆ HAS` (was prose-only).
- `docs/RELEASE_CHECKLIST.md` — note the closure gate; keep the `[J]` force-push/eval-drift steps as model-upheld.
- `docs/claugentic-ARCHITECTURE_TREE.md` — update the two script rows if their scope line changes.
- `docs/claugentic-DECISIONS.md` — one dated line (the 7→1 consolidation + closure gate; version-sync kept separate; provable-no-op).

## Risks & mitigations

- **Risk: silently changing what ships.** → **Mitigation:** step-1 migration test asserts the shipped set is byte-identical to pre-change; the whole plan gates on that equality. If it differs, STOP.
- **Risk: the closure check surfaces a real latent gap and fails.** → **Mitigation:** that's a *good* find — fix the wiring (add the missing seed/managed-set entry) or the class annotation; do NOT weaken the check to pass.
- **Risk: the `INCLUDE_GLOBS` carve-out breaks closure** (the tree-script's glob line is adopter-owned). → **Mitigation:** exclude it from the closure NEEDS exactly as `init`'s body-compare does (recorded constraint).
- **Risk: scope creep (folding version-sync / renaming the file).** → **Mitigation:** explicit non-goal; version-sync stays separate; the rename is deferred/optional.

## Test strategy

- **Deterministic gates:** `python -m pytest` (+ the new migration/closure tests), `node --test "tests/workflows/*.test.mjs"`, `python scripts/check_shipped_content.py` (must stay OK — now with the closure check), `python scripts/check_versions_synced.py` (untouched), `python scripts/check_doc_budgets.py`, `scripts/claugentic-check_architecture_tree.py`.
- **The load-bearing check:** a test/dogfood-run that computes the shipped set from `classify()` before and after the migration and asserts **byte-identical**.
- **Reviewer sign-offs:** `maintainability-structure` + `testing` + `docs-traceability` lenses via `synthesizer-gate`; `honesty-reviewer` on the RELEASE_CHECKLIST/INVARIANTS copy (mechanical-vs-`[J]` split); `yagni-sentinel` (no version-sync fold, no premature rename).

## Decomposition (slices)

- [ ] **Slice 1 — Annotate the manifest + prove the shipped set unchanged.** `DEV_ONLY_FILES`→`DEV_ONLY_PATH_CLASSES` dict in `build_release.py`; `is_dev_only`/`classify`/`recreate_class` off the dict; migration equality test (shipped set byte-identical). No behavior change. **In-scope:** `maintainability-structure`, `testing`.
- [ ] **Slice 2 — Derive-alongside + delete the hand-lists.** In `check_shipped_content.py` derive the three sets from `recreate_class`, assert-equal to the old hand-lists (safety net), then delete the hand-lists once green. **In-scope:** `maintainability-structure`, `testing`.
- [ ] **Slice 3 — The referential-closure gate (`NEEDS ⊆ HAS`).** Add the closure assertion (honor `INCLUDE_GLOBS` carve-out); mechanize the INVARIANT; update INVARIANTS + RELEASE_CHECKLIST copy (keep `[J]` steps model-upheld). Collapse the test pins. DECISIONS line; tree update. **In-scope:** `maintainability-structure`, `testing`, `docs-traceability`; trust surface → `honesty-reviewer`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_
_(to be filled)_

## Spec  _(per slice, Stage 4)_
