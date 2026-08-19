# Load-bearing invariants

Constraints that **must stay true or something breaks** — recorded so the next change in
their blast radius reads *why* before touching them. This is **live documentation, not a
gate**: nothing mechanically enforces these. One entry per genuine invariant; most code
has none, so keep this lean. (Sibling to `docs/claugentic-DECISIONS.md` — a *decision* is
"what we chose"; an *invariant* is "what must hold".)

Each entry: **the invariant** · **why** (what breaks if violated) · **enforcement, stated exactly** (which half is test-pinned vs model-upheld — a partly-enforced must-hold must say where the line falls, never imply the whole is mechanical) · **provenance** (dated — the failure or near-miss that taught it).

**Admission rule —** an invariant a live, **red-on-break test already enforces does NOT get a prose
entry** — the pin IS the memory; only what no test can hold is written here. Where an otherwise-pinned
constraint has a model-upheld remainder, that half alone rides *Unpinnable residue* at the foot.

---

## `eval/` source stays OUT of the tree gate's `INCLUDE_GLOBS`

- **Invariant —** `eval/**` (`fixture-defects/app/*.py`, `fixture-app/*.py`) must never enter
  `INCLUDE_GLOBS` (today `scripts/**/*.py` + `engine/**/*.js`). `glob_drift` short-circuits whenever
  the globs already match ≥1 file (they do), so eval source is invisible to the gate by design.
- **Why —** the eval is a measurement fixture, not shipped code: presence/staleness-checking the
  seeded-defect files would force them into the index (leaking the answer key into a read-first doc)
  and the zero-coverage drift census would fire on intentional fixtures. Both disarm the exam.
- **Provenance —** carried as tree-entry rationale until 2026-06-24 (plan 0024 S1), then evicted here
  as the durable "must hold" so the tree index stays a thin pointer.

---

## The scrubbed-file set must never regain the de-correlation claim

- **Invariant —** the SCRUBBED-FILE SET — `.claude/agents/honesty-reviewer.md` · `synthesizer-gate.md`
  · `product-designer.md` · `lens-reviewer.md` · `finding-verifier.md` · `README.md` ·
  `docs/claugentic-{WORKFLOW,PLAYBOOK,DECISIONS}.md` · `skills/{audit,build,product,init}/SKILL.md`
  · the rewritten comment block in `engine/audit.js` — must NOT assert model-family
  independence / de-correlation. The honest claim is "a different model family — a *reduction*
  of shared-blind-spot risk, **NOT** a guarantee." The three-state disclosure machinery
  (`sameModelTag` / `KNOWN_FAMILIES` / the cross-model run tag) stays everywhere it already
  lives — it is the **claim** that is forbidden in this set, not the machinery term.
- **Why —** judge and builder are the same vendor, so their errors are correlated; a
  de-correlation / model-family-independence claim launders that correlated judgment into
  apparent independence the harness has not earned, breaking the core honesty rule (it
  under-claims, never over-claims). See `docs/claugentic-DECISIONS.md` → Honesty positioning.
- **Provenance —** 2026-06-22: the v0.1.40 distillation drop + the v0.2.0 hybrid restore
  (plan 0023) — `main` was the start for the scrubbed set precisely so the claim could not
  return, and this is the durable form of that rule. Live gate: the honesty-reviewer over the
  diff (model-upheld; nothing mechanically enforces this).

---

## The independent test-author's failing tests must not be edited by the implementer

- **Invariant —** when the per-work choice selects **test-first**, the independent clean-context
  test-author writes the failing tests and the `implementer` **greens them WITHOUT editing the test
  files.** The implementer changes production code to pass the tests, never the tests themselves.
- **Why —** the test-first proof-of-meaningfulness collapses if the implementer can edit the failing
  tests — a green end-state can't prove the test captured anything if the same agent that greened it
  could rewrite what "green" means. Structural test integrity is worth more for an agent than a human
  (a human self-enforces; an agent needs the seam). The named observable audit artifact (the
  implementer's report names the test-author spawn + the untouched test files; the diff shows them
  added in a distinct authored-first step) is what makes the claim falsifiable.
- **Provenance —** 2026-07-03 (plan 0030 Slice 3): the red-first-when-test-first-is-chosen wiring.
  **Model-upheld + Verify-gate-audited** (`synthesizer-gate` keys on the named observable artifact),
  **NOT mechanically enforced — by design** — the red-first/characterization `PreToolUse` hook that
  would enforce it was considered and DECLINED (0035 rejected 2026-07-04; model-upheld is the chosen
  posture — the harness does not force test-first; never claim mechanical enforcement).

---

## The release strips ⇒ init recreates ⇒ nothing shipped dangles

- **Invariant —** whatever `scripts/build_release.py` strips that the workflow needs in ANY repo
  (Class-B: DECISIONS/ROADMAP/ARCHITECTURE_TREE/INVARIANTS, the plan & product-spec templates,
  PRODUCT*), `init` must (re)create or manage; and no SHIPPED file may reference a stripped-uncreated
  file, nor run a harness-self gate (Class-A: version-sync, shipped-content), without adopter-awareness
  (a caveat / an N-A path).
- **Why —** otherwise the release ships a harness that points an adopter at a file that isn't there, or
  runs a gate that errors in their repo — a failure in the adopter's context with every harness-self
  test green.
- **Enforcement, stated exactly —** **Test-pinned:** `tests/test_build_release.py::TestReleaseInitContract`
  (membership) + `scripts/check_shipped_content.py` (a **run-gate, NOT hook-enforced**) — the exact
  literals and the referential closure `NEEDS ⊆ HAS`; closure ≠ correctness (it pins that nothing
  dangles, never that the release is *right*). **Model-upheld:** the **dir-swept blind spot** — a
  `DEV_ONLY_DIRS` subtree carries no recreate-class, so those passes structurally cannot see it; for a
  dir-swept path (e.g. `docs/claugentic-decisions/`) the no-shipped-reference leg is model-upheld only
  (the rule is recorded in CLAUDE.md).
- **Provenance —** 2026-06-25 (plan 0027), hardened since; per-pass gate detail in git history.

---

## The `release` branch has exactly ONE publisher

- **Invariant —** only `.github/workflows/release.yml` writes `release`, and only by invoking
  `scripts/build_release.py --apply` at the tagged commit. No command in the flow, no other workflow,
  and no hand-rolled YAML build/push logic may write that branch. The human's one release act is the
  tag push (`git tag vX.Y.Z && git push origin main vX.Y.Z`).
- **Why —** the `release` branch IS the installed plugin, and it is force-updated: two writers means a
  publish can silently clobber the other's tree, and a YAML re-implementation of the strip drifts from
  the tested one on its first edit. **Consequence to accept, not fix:** the tag precedes publishing, so
  a red run SPENDS that version — first re-run the failed run (safe by construction); otherwise bump
  forward, and never reuse a tag (deleting a failed tag is an outward, user-gated exception).
- **Enforcement, stated exactly —** **Test-pinned (tooling half):** `tests/test_release_workflow.py` +
  `tests/test_build_release.py::TestGatedPublishCommand`. **Model-upheld (branch half) — until `release`
  is branch-protected**, verified 2026-08-12: no protection rule, no ruleset, so anyone with push rights
  can still write it by hand. Read "one publisher" as a contract the tooling keeps, not a permission the
  platform enforces; "a red run publishes nothing" likewise holds only for failures BEFORE the branch
  push, which is the second-to-last step of the publish job.
- **Provenance —** 2026-08-12: v0.5.1 published from an 11-day red-CI window; detail in git history.

---

## The audit cell-key delimiter must be name-safe + changed atomically

- **Invariant —** the audit cell-key (`engine/audit.js` `cellKey` builds `module|dir`) uses a
  delimiter (`|`) that CANNOT appear in a module name (`[a-z-]+`) or a forward-slash scope path.
  Changing it requires updating ALL sides together: producer (`cellKey`/`BLINDSPOT_CELL`), parser
  (`parseCellKey`), serializer (`renderStatusLine` → the audit fence's done/pending-cells), the SKILL
  resume re-parse (`skills/audit/SKILL.md`), and the pinned test fixtures.
- **Why —** the delimiter is the cell-key's only field separator AND it round-trips through the audit
  fence's persisted resume contract; a delimiter that can occur in a module name or path mis-splits
  `parseCellKey`, and a one-sided change silently corrupts resume (cells re-run or drop). (ASCII-only
  is a separate, mechanically-guarded requirement — `check_shipped_content.py` Pass C.)
- **Provenance —** 2026-06-25 (plan 0029): the engine ASCII-hardening swapped the original U+00D7
  delimiter to `|`; the plan-gate caught it was LOAD-BEARING (not display) and a blind swap to `x`
  would have corrupted resume (module/dir names contain `x`).

---

## A chained gate's advisory output rides stderr — the wrapper eats stdout

- **Invariant —** Any gate chained into `.githooks/pre-commit` must emit advisory output (a WARN band, a report-only breach) on **stderr**. The wrapper captures a gate's stdout and discards it on a passing run — advisory text printed there is silently lost, and the report-only grace becomes a no-op.
- **Why —** the wrapper's contract is quiet-when-clean: stdout is the verdict channel (shown only on failure), stderr the advisory channel (always flows through). A gate that warns on stdout looks compliant, passes green, and its early-warning signal never reaches a human — the exact hole (R6) plan 0041 S5 exists to close.
- **Enforcement, stated exactly —** **Test-pinned (wrapper half):** `tests/test_precommit_wrapper.py` pins that stderr survives a passing gate and stdout is discarded. **Model-upheld (per-gate half):** nothing scans a gate's source for stdout-WARNs; as of 0041 S5 both WARN-emitting gates (doc-budget, shipped-content) conform — zero known non-conformers.
- **Provenance —** 2026-08-14, plan 0041 S5 (the R6 residual). Established with the stream contract; the sibling sweep that moved `check_shipped_content.py`'s WARN to stderr landed in the same slice so this entry names no violator.

---

## A guard is UNPINNED until a mutation makes its test go red

**The invariant.** A test that only asserts a guard's *text* — that the step exists, that the string is
present — does not pin the guard. Deleting or disabling the guard must make a test FAIL. Until you have
watched that happen, the guard is unpinned no matter how many tests name it.

**Why.** A green suite over a removed guard is worse than no test: it is a *false* assurance, and it is
the shape this repo keeps re-discovering. Three instances now — the merge-commit gate (a conflict-free
`git merge` fired an unwired hook, so a capped ledger landed unchecked with the suite green) · the earlier
deleted-guard case · and the release job's `if: runner.os == 'Linux'` steps, where dropping `ubuntu-latest`
from `matrix.os` skips the on-main authorization check and `plugin validate --strict` while `gates` still
reports success and `publish` proceeds. In every case the existing tests asserted presence and stayed green.

**Enforcement, stated exactly.** **Model-upheld, and no pin can hold it** — a test asserting "guards are
mutation-verified" would itself be a presence assertion needing mutation-verification, so the regress is
the reason this is prose. What IS mechanical is each individual guard's own pin once written. The practice:
break it, watch it go red, restore it byte-for-byte (`git checkout --`), watch it go green.

**Provenance.** 2026-08-19, RM-3c — the third instance, and the one that made it a class rather than a
recurrence. Surfaced during the north-star backlog adjudication; the other eight proposed gate items were
declined as compensation, and this one was built precisely because a green suite hid a voided *release* gate.

## Unpinnable residue

The model-upheld remainder of constraints whose substance is otherwise test-pinned — kept only because
no pin can hold these halves. One line each; anything a test could carry does not belong here.

- **Doc-budget caps —** no *second* cap list is introduced anywhere (nothing greps for one), and every
  new file added under the deny-by-default `.claude/` directory gets its own un-ignore line —
  everything else about the caps config is pinned in `tests/test_check_doc_budgets.py`.
