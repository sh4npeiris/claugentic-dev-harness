# Build eval — the procedure and the pre-registered decision rule

**One question per run:** *did swapping standards-catalog variant A for variant B change
what the implement path actually ships?*

`fixture-build/` is a fixed programming task (`TASK_SPEC.md`) an `implementer` agent builds
from a frozen approved plan slice, in a scratch worktree, with the catalog variant under
test in place. What it ships is then measured mechanically: a **held-out suite** that says
whether it works, a **spec-compliance** pass that says whether it built the pinned surface,
and **ten trap probes** that say which realistic mistakes it made. The answers live in
`fixture-build/TRAP_MANIFEST.md`, which no run may read; the per-run results live in
`eval/BUILD_ENTRIES.md`, which is the only file that carries them.

**This file carries no answers.** That split is day one and deliberate — a runner opens
this file for the procedure and never scrolls past a results table into an answer key. It is
mechanical **for the id half**: `tests/test_eval_key_containment.py` scans every tracked file
for the trap **ids** and this file is **not** on its allowlist, so an answer that **names a
trap** goes red. **An answer written in paraphrase, without an id, stays green — that half is
model-upheld**, held by this rule and by review, exactly as the architecture tree's
do-not-revert note records for the sibling exam.

> **The honest size of this instrument.** K=3 per arm is a **tripwire, not a proof**: it can
> catch a gross regression (two traps or more) and it cannot rule out a subtle one. A null
> result means **no regression was detected at this K** — never that the cut is safe in
> general, and never that the two catalogs are equivalent. Every entry cites this
> paragraph rather than restating it.

## Pinned before any run

- **H = 13 and delta-F >= 2** — pinned together on 2026-08-20, before any arm ran, and
  **re-pinnable only together**. `H` is the number of held-out tests in
  `fixture-build/checks/test_heldout.py` (the functional floor an arm is scored against);
  `delta-F` is the held-out-test-count gap between arms that blocks a cut. Changing one
  without the other changes what the threshold means, silently — which is why
  `tests/test_eval_trap_manifest.py` asserts this line's `H` equals the real count of tests
  in that file. (Written `delta-F` in ASCII throughout so the pin parses.)
- **Standing rule (a) — the exam is not tuned by the people sitting it.** After its initial
  landing, `TRAP_MANIFEST.md` never changes in a release that cuts the catalog, **with one
  carve-out: the recorded both-arms-saturation calibration allowance below.** Its trigger is
  symmetric, so it cannot favour the cut; and **a re-sharpened manifest voids all prior
  runs — both arms are re-run against it.**
- **Standing rule (b) — the decision rule is pre-registered.** Every threshold on this page
  was fixed before any arm ran. A threshold argued into place after seeing a result is not a
  threshold.

## Shared mechanics — read them in `eval/BASELINE.md`, they are not copied here

The two evals share one chassis, and it has exactly one home. `eval/BASELINE.md` owns:
**scratch-worktree hygiene** (the run's writes never land on `main`), **canary handling**
(a distinctive line planted in the answer key; if it ever appears in a run's output the key
leaked and the run is discarded), the **filename-only-disclosure precedent** (an agent whose
grep surfaces the answer key's *path* discloses it and states it did not open the file — a
recorded residual, not a clean bill), and **the human stamps the run date** (nothing
clock-bearing originates inside a script). This eval adds its own canary line, its own
fixture and its own answer key; everything above behaves as that file describes.

## The procedure

1. **Fix and record the arm identities.** Arm A is the base commit's
   `docs/claugentic-standards/`; arm B is the variant under test. The **only** difference
   between arms is the bytes inside that directory.
2. **Run the calibration pair and require both halves to pass** —
   `python eval/fixture-build/calibration/run_calibration.py`. The reference must come back
   H/H on the held-out suite, compliant with the pinned surface, and clear of all ten traps;
   each mutant must flip its own probe and no other. **A failed calibration stops the run**:
   an instrument that has not been shown to discriminate cannot be used to wave a cut
   through or to block one.
3. **Build the sitting's worktrees** at one base commit — three for a shakedown (one arm),
   six for a decision comparison. Swap arm B's catalog wholesale.
4. **Copy `fixture-build/plan-slice.md` into each worktree's `.claude/plans/`.** The builder
   is spawned against the shipped `implementer` contract verbatim; the run's scoping (writes
   confined to `out/`, the architecture tree out of scope) rides that plan slice, which is
   the contract's own delivery channel — scoping, not coaching. `TASK_SPEC.md` goes in
   alongside it.
5. **Apply the deletion set, and verify it with `ls`.** **The class has ONE home — read it
   in `eval/BASELINE.md` step 1.** It is a shared chassis mechanic, and a second copy in
   narrower words is exactly how an answer key survived into a run worktree once already.
   This eval adds nothing to that class and narrows nothing in it; `eval/fixture-defects/`
   falls inside it for the same reason the build fixture falls inside the sibling's — **the
   trap classes ARE its seed classes**. **What the grep cannot see:** a file that assembles a
   deleted path from segments at runtime rather than writing it out. That half is closed by
   step 6, not by a wider pattern — which is the reason step 6 runs before any spawn rather
   than after the sitting.
6. **Take the deletions out of the INDEX too, then bring the tree index to a fixpoint, then
   require `python -m pytest` green — in that order, before any spawn.** Three steps, because
   the deletions alone do not get there. **Measured end-to-end 2026-08-20** on the commit this
   procedure landed with: 537 passed / **2 failed** after step 5's deletions alone.
   - **(a)** `git rm -r --cached <the same set>`. Repo-wide scans enumerate the **tracked**
     tree, so a file deleted from disk but still in the index is still in their corpus.
   - **(b)** Bring every ROUTING INDEX to a fixpoint. Run the architecture-tree gate,
     **remove every row AND every prose mention it names**, and repeat until it exits 0; do
     the same for `docs/claugentic-DECISIONS.md`, dropping any route whose shard the deletion
     removed. A fixpoint, not a list, matching this file's own
     class-not-hand-list doctrine — and the prose half is load-bearing: the gate's staleness
     check reads path mentions in prose, and both do-not-revert notes cite a test file this
     very deletion set removes. Measured: (a) alone left 538/1; (a) plus dropping only the
     ROWS still left 538/1; the fixpoint converged in **two rounds** and gave **539 passed,
     tree gate exit 0**. The arithmetic closes: 537+2 = 538+1 = 539+0. **Re-measured against
     the widened answer-bearing class (2026-08-20): 18 paths deleted, index fixpoint in two
     rounds, 380 passed / 0 failed** — the drop in the total is the deleted tests, and it is
     why clause (ii) of the class is non-transitive.
   - **(c)** Then `python -m pytest` must be green. **Pytest-only by design:**
     `tests/workflows/*.mjs` sits outside this gate, and the only one that touches `eval/`
     reads the runtime-QA fixture, which the deletion set does not remove.
7. **Spawn one fresh clean-context `implementer` per run**, interleaved across arms in one
   sitting — A1 B1 A2 B2 A3 B3 — so a mid-session tier shift is spread across both arms
   rather than confounded with one. **A cross-sitting or cross-commit comparison is invalid
   by this design.** Held constant: the base commit, the brief, the plan slice, the
   unmodified `implementer` contract (its "self-apply the Auditor checks" step **is** the
   treatment), the spawn prompt and the session tier. Retain every transcript and its
   `RUNNING AS` line. The builder makes no commit.
8. **Sweep each worktree from the MAIN checkout** —
   `python eval/fixture-build/checks/run_sweep.py sweep --out <worktree>/out`. The sweep
   computes facts and never a score.
9. **Grade the judged trap blind.** Build the pack with `run_sweep.py judge-pack` (the
   sitting's `out/` directories shuffled under opaque names, comment-line-only redaction,
   every redaction logged, code lines flagged for a human rather than edited, the mapping
   sealed to a path outside the pack). One grader, given the manifest's rule for that row
   and nothing else, citing `file:line`; an unsupported citation is discounted, and the
   discount is recorded.
10. **Record catalog-read attribution** per transcript — did the builder actually open the
    catalog? **"Catalog unread" is never recorded as "catalog unneeded".**
11. **Run the contamination sweep** over every transcript and output: this fixture's canary,
    the audit fixture's canary, and content lines from either answer key. A filename-only
    sighting is disclosed per the precedent in `eval/BASELINE.md`; a **content** hit discards
    that run. **Honest limit, stated rather than implied: this catches verbatim leakage
    only.** The agents' working directory is the main checkout, so that read path stays open,
    and paraphrase contamination is undetectable at this layer.
12. **Apply the floor rule, then the decision rule** (below), in that order.
13. **Append the entry** to `eval/BUILD_ENTRIES.md`, newest first, with the date stamped by
    the human.
14. **Remove the worktrees** and confirm `docs/claugentic-ROADMAP.md` is byte-untouched.

## What is measured

- **`F(X,k)` — functional pass rate** over the held-out suite, out of H.
- **`S(X,k)` — spec compliance**, scored **separately** so an interface-naming drift can
  never masquerade as a quality delta.
- **Per-trap outcome** per run: AVOIDED, FELL_IN, or UNCHECKABLE. **UNCHECKABLE counts as
  FELL_IN**, with the raw evidence printed; a human may overrule it with a recorded
  judgment, never silently.
- **`M(X)` in 0..10** — the arm's trap score, by **2-of-3 majority per trap** across the
  arm's three runs.
- **The decision figures:** `delta = M(A) - M(B)` and `delta-F` (the held-out test counts).

## The pre-registered decision rule

**The floor leads the verdict, before any trap arithmetic is quoted.**

1. **Floor.** Mean `F < 0.8` for an arm means that arm **did not reliably produce a working
   artifact**, and that is stated first. **Candidate arm below the floor while the baseline
   arm clears it → BLOCK the cut. Both arms below the floor → the instrument is invalid for
   this sitting: the cut is deferred and the calibration allowance is considered.**
2. **BLOCK the cut if and only if** `delta >= 2` **or** `delta-F >= 2` **or** the floor
   clause above fires.
3. Otherwise — `delta` in {0, 1} and the floors clear — the verdict is **"no regression
   detected at this K"** and the cut may proceed. **Never phrased as equivalence shown, and
   never predicated of the cut itself:** "a non-regressing cut" is the forbidden reading,
   because what was measured is this instrument's failure to detect a difference, not the
   absence of one.
4. An **ambiguous** result defers the cut and says so. It never forces one.

**Recorded beside the verdict, never gated on:** `flap(X)` — traps not unanimous inside an
arm — and the intra-arm **spread**, printed next to `delta`, so **a delta that lands inside
the measured spread is called noise by the entry itself**.

**One calibration allowance.** If the first outing saturates in the same direction for
**both** arms, the brief and the traps — never the catalog, never the `implementer`
contract — may be re-sharpened **once**, recorded, under standing rule (a)'s carve-out.

**Defect versus tuning — the line the allowance does not blur.** A probe that **demonstrably
does not measure what its row claims** is a defect: fix it, record it, and re-run the
calibration, whenever it is found. A probe is **never adjusted to move an arm's score**, and
**the reference is never touched** outside the allowance above. The test is what the change
is answerable to — a named, reproducible mis-measurement, or a number somebody wanted.

## Circularity, and the residual that stays

Five layers stand between this instrument and grading itself: every check is anchored to a
**user-visible failure**; the **harm-line rule** makes a catalog-only justification
inadmissible; the trap **classes** predate the question and the manifest is not tuned by a
cutting release; the judged row is **graded blind**; and the held-out suite is
**symmetric** across arms. **The residual, stated and not smoothed:** the traps and the
catalog share subject matter. The defense is that the checks measure the **failure**, not
the vocabulary — a cut that keeps the teeth and sheds the prose can score ten out of ten.

## Extension, derivable from this procedure but not built

*A K=1 single-arm advisory run is derivable from this procedure — **advisory only**: it can
trigger a full K=3 comparison, and can never issue a pass or block verdict.*

---

**Entries live in `eval/BUILD_ENTRIES.md`** — append-only, newest first, human-stamped. This
file is procedure; that file is results.
