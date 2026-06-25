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

- **Invariant —** the SCRUBBED-FILE SET — `.claude/agents/{honesty,architect,plan}-reviewer.md`
  · `product-critic.md` · `finding-verifier.md` · `README.md` ·
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
