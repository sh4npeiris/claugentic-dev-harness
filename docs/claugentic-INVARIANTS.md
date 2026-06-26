# Load-bearing invariants

Constraints that **must stay true or something breaks** — recorded so the next change in
their blast radius reads *why* before touching them. This is **live documentation, not a
gate**: nothing mechanically enforces these. One entry per genuine invariant; most code
has none, so keep this lean. (Sibling to `docs/claugentic-DECISIONS.md` — a *decision* is
"what we chose"; an *invariant* is "what must hold".)

Each entry: **the invariant** · **why** (what breaks if violated) · **provenance** (dated —
the failure or near-miss that taught it).

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

## The release strips ⇒ init recreates ⇒ nothing shipped dangles

- **Invariant —** whatever `scripts/build_release.py` strips that the workflow needs in ANY repo
  (Class-B: DECISIONS/ROADMAP/ARCHITECTURE_TREE/INVARIANTS, the plan & product-spec templates,
  PRODUCT*), `init` must (re)create or manage; and no SHIPPED file may reference a stripped-uncreated
  file, nor run a harness-self gate (Class-A: version-sync, doc-budgets), without adopter-awareness
  (a caveat / an N-A path).
- **Why —** a release built by stripping the dev tree otherwise ships a harness that points an adopter
  at a file that isn't there, or runs a gate that errors in their repo — the harness fails in the
  adopter's context though every harness-self test was green.
- **Provenance —** 2026-06-25 (plan 0027): two instances — (1) shipped WORKFLOW / build-SKILL said a
  plan is "structured by `TEMPLATE.md`" while `.claude/plans/` (the template's home) is stripped
  wholesale (a degraded dangling ref); and the stronger (2) `check_doc_budgets.py` shipped and — new at
  0.3.0, after plan 0024 added the `INVARIANTS.md` budget row — **fail-louded on the lazily-created
  `INVARIANTS.md`**, a hard error a fresh 0.3.0 adopter would hit. Live gate:
  `tests/test_build_release.py::TestReleaseInitContract` (membership) + `scripts/check_shipped_content.py`
  (a **run-gate, NOT hook-enforced**; 0028 S3) — the latter now mechanically pins the **exact-literal**
  cases: a dangling stripped-uncreated path reference (Pass A.a, hard) and a stranded
  `claugentic-dev-harness:<token>` namespace literal (Pass B, hard). Its uncaveated-gate-mention pass
  (A.b) is **WARN-heuristic**, not a hard gate. The contract is therefore pinned mechanically for the
  exact literals only — NOT *fully* content-enforced; the membership test + model-upheld review still
  complement it.

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
