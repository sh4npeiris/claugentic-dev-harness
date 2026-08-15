# Load-bearing invariants

Constraints that **must stay true or something breaks** — recorded so the next change in
their blast radius reads *why* before touching them. This is **live documentation, not a
gate**: nothing mechanically enforces these. One entry per genuine invariant; most code
has none, so keep this lean. (Sibling to `docs/claugentic-DECISIONS.md` — a *decision* is
"what we chose"; an *invariant* is "what must hold".)

Each entry: **the invariant** · **why** (what breaks if violated) · **enforcement, stated exactly** (which half is test-pinned vs model-upheld — a partly-enforced must-hold must say where the line falls, never imply the whole is mechanical) · **provenance** (dated — the failure or near-miss that taught it).

---

## The two version manifests must move together

- **Invariant —** `plugin.json` and `marketplace.json` carry the same version; every bump
  moves both, with `plugin.json` as the source of truth.
- **Why —** they are one logical stamp; a drifted pair ships an install whose advertised
  version lies about its contents, and the marketplace serves the wrong tree.
- **Provenance —** 2026-06-22: codified after the version-sync gate (`check_versions_synced.py`)
  was added to mechanically catch a drift that had previously been caught only by eye.

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

## The SELECT re-render keeps coverage full-scope and never emits a false terminal signal

- **Invariant —** the SELECT seam (`renderOnly` in `engine/audit.js`) passes `lensCoverage` /
  `verification` through **full-scope** — never recomputed over the user's selected subset — and
  `renderOnly` is **never invoked with an empty selection** when the full run carried Tier-1/2
  findings (a keep-none result is handled conversationally + the fence write is skipped, never
  re-rendered through the engine).
- **Why —** recomputing coverage over the kept subset would falsely claim "every lens spoke" about
  only the findings the user kept; an empty `renderOnly` re-render over a run that *did* find things
  emits the engine's terminal "sound on the audited dimensions" signal — a lie when the run actually
  surfaced work the user simply chose not to act on now. Both break the harness honesty rule.
- **Provenance —** 2026-06-25 (plan 0025 S5): a focused plan-review found the prior "filter-before-
  render, zero engine change" SELECT design was unreachable from a prose skill (un-exported renderer)
  and its only literal implementation (string-dropping rendered blocks) was dishonest; the `renderOnly`
  seam replaced it, and this is the honesty contract that seam exists to uphold.

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
  file, nor run a harness-self gate (Class-A: version-sync), without adopter-awareness
  (a caveat / an N-A path).
- **Why —** a release built by stripping the dev tree otherwise ships a harness that points an adopter
  at a file that isn't there, or runs a gate that errors in their repo — the harness fails in the
  adopter's context though every harness-self test was green.
- **Provenance —** 2026-06-25 (plan 0027): two instances — (1) shipped WORKFLOW / build-SKILL said a
  plan is "structured by `TEMPLATE.md`" while `.claude/plans/` (the template's home) is stripped
  wholesale (a degraded dangling ref); and the stronger (2) `check_doc_budgets.py` shipped and — new at
  0.3.0, after plan 0024 added the `INVARIANTS.md` budget row — **fail-louded on the lazily-created
  `INVARIANTS.md`**, a hard error a fresh 0.3.0 adopter would hit. (It ships again from 0041 S6 —
  the failure mode is closed: caps are per-repo data, an absent config a quiet no-op.) Live gate:
  `tests/test_build_release.py::TestReleaseInitContract` (membership) + `scripts/check_shipped_content.py`
  (a **run-gate, NOT hook-enforced**; 0028 S3, closure pass 0034 S3 — run by CI on every push to `main`,
  and **since 0041 S2 also at the tagged commit** before anything publishes) — the latter
  now mechanically pins the **exact-literal** cases: a dangling stripped-uncreated path reference
  (Pass A.a, hard), a stranded
  `claugentic-dev-harness:<token>` namespace literal (Pass B, hard), and — 0034 Slice 3 — the
  **referential closure `NEEDS ⊆ HAS`** (Pass D, hard): every stripped adopter-relevant path is
  **producible by `init` OR the workflow's lazy/templated/agent authoring** — `init-seed` (its `_X.md`
  seed ships) · `init-gen` (a known init generator output) · `recreate-on-demand` (accepted VIA the
  class, **NOT** claimed init-produced) · `self-gate` (a stripped harness-self script,
  self-consistent). A missing seed / unregistered generator now fails the gate.
  Its uncaveated-gate-mention pass (A.b) is **WARN-heuristic**, not a hard gate. **Dir-swept blind
  spot (2026-07-30, plan 0040):** a `DEV_ONLY_DIRS` subtree carries **no recreate-class**, so Pass
  A.a/D structurally cannot see it — for a dir-swept path (e.g. `docs/claugentic-decisions/`) the
  no-shipped-reference leg is **model-upheld only** (the rule + its ungatedness are recorded in
  CLAUDE.md). The contract is
  therefore pinned mechanically for the exact literals + the referential closure — but **NOT** *fully*
  content-enforced: Pass D pins that nothing dangles (closure), **not** that the release is *correct*;
  the membership test + model-upheld review still complement it.

---

## The `release` branch has exactly ONE publisher

- **Invariant —** only `.github/workflows/release.yml` pushes the `release` branch, and it does so
  only by invoking `scripts/build_release.py --apply` at the tagged commit. No command in the flow,
  no other workflow, and no hand-rolled YAML build/push logic may write that branch. The human's one
  release act is the tag push (`git tag vX.Y.Z && git push origin main vX.Y.Z`).
- **Why —** the `release` branch IS the installed plugin, and it is force-updated. Two writers means
  a publish can silently clobber the other's tree, and a YAML re-implementation of the strip drifts
  from the tested one on its first edit — publishing content no test ever classified. **Consequence
  to accept, not fix:** because the tag precedes publishing, a red run spends that version — first
  try re-running the failed run (safe by construction); otherwise bump forward, and never reuse a
  tag (deleting a failed tag is an outward, user-gated exception).
- **Enforcement, stated exactly —** the *tooling* half is pinned: `tests/test_release_workflow.py`
  (`needs: gates`, the leased push scoped to its own step, no hand-rolled strip, no `--bump` at
  publish, write permission granted to `publish` alone) and
  `tests/test_build_release.py::TestGatedPublishCommand` (the printed human command contains no
  `release`-branch push at all). The *branch* half is **model-upheld until `release` is
  branch-protected** — verified 2026-08-12: no protection rule, no ruleset, so anyone with push
  rights can still write it by hand. Read "one publisher" as a contract the tooling keeps, not a
  permission the platform enforces; "a red run publishes nothing" likewise holds for every failure
  BEFORE the branch push, which is the second-to-last step of the publish job.
- **Provenance —** 2026-08-12 (plan 0041 S2): v0.5.1 published from an 11-day red-CI window because
  the human force-pushed `release` and CI gated nothing that adopters consume. The Stage-7 panel
  then caught the first draft of this very entry claiming the mechanical half — hence the split
  above.

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

## The doc-budget caps have exactly ONE source per repo — and it must be tracked

- **Invariant —** A repo's ledger byte caps live in exactly one place: its caps config (`.claude/claugentic-doc-budgets.json`). The gate only **reads** it — it holds no caps of its own. Where a glob entry covers a set of files, that glob is the **sole** cap for the set; per-file entries beside it are forbidden. And the config file must stay **tracked by version control**.
- **Why —** two cap homes means every file is measured twice (one breach prints two messages) and the number has two hand-maintained copies that drift — the exact defect a plan-gate round prescribed and the next round had to retract. And because an **absent** config is a deliberate quiet no-op ("this repo has not opted in"), an untracked config is indistinguishable from an uncapped repo: the gate passes green on the author's machine and measures **nothing** in CI or in any fresh clone, with no error anywhere.
- **Enforcement, stated exactly —** **Test-pinned:** the config is tracked (asserted through `git ls-files --error-unmatch`, never through the ignore rules' wording) · the five cap values are pinned byte-exactly (deliberate drift-detection — this pin is a harness-self extra, so a cap bump here touches the config *and* the pin) · every configured key resolves to something real · key shapes are validated (`**` refused; `*` only in the final path component; duplicate keys fatal) · shard **existence** is the two-direction index↔shards agreement test, not a second cap. **Model-upheld:** that no *second* cap list is introduced anywhere — nothing greps for one; and that any future file added under the deny-by-default `.claude/` directory gets its own un-ignore line.
- **Provenance —** 2026-08-13, plan 0041 Slice 4, when the caps moved from a hardcoded dict into the config; the tracked half came from a mid-slice near-miss (the new config was git-invisible by default — the gate would have measured nothing outside the author's machine). General class: `reliability-resilience` → *Opt-in by absence*; this entry is this repo's instance and the exact enforcement split. **Extended to every repo by 0041 S6:** the gate ships, so this binds an adopter's repo too.
---

## A chained gate's advisory output rides stderr — the wrapper eats stdout

- **Invariant —** Any gate chained into `.githooks/pre-commit` must emit advisory output (a WARN band, a report-only breach) on **stderr**. The wrapper captures a gate's stdout and discards it on a passing run — advisory text printed there is silently lost, and the report-only grace becomes a no-op.
- **Why —** the wrapper's contract is quiet-when-clean: stdout is the verdict channel (shown only on failure), stderr the advisory channel (always flows through). A gate that warns on stdout looks compliant, passes green, and its early-warning signal never reaches a human — the exact hole (R6) plan 0041 S5 exists to close.
- **Enforcement, stated exactly —** **Test-pinned (wrapper half):** `tests/test_precommit_wrapper.py` pins that stderr survives a passing gate and stdout is discarded. **Model-upheld (per-gate half):** nothing scans a gate's source for stdout-WARNs; as of 0041 S5 both WARN-emitting gates (`check_doc_budgets.py`, `check_shipped_content.py`) conform — zero known non-conformers.
- **Provenance —** 2026-08-14, plan 0041 S5 (the R6 residual). Established with the stream contract; the sibling sweep that moved `check_shipped_content.py`'s WARN to stderr landed in the same slice so this entry names no violator.
