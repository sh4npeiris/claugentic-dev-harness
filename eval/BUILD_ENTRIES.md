# Build eval — entries

Append-only, **newest first**, human-stamped. Procedure, thresholds and standing rules live
in `eval/BUILD_BASELINE.md` and are not restated here; this file carries results, and it is
answer-bearing by design (per-run trap tables name the traps, which is why it is one of the
few files allowlisted by `tests/test_eval_key_containment.py`).

Every entry cites the small-N caveat in `eval/BUILD_BASELINE.md` rather than restating it: a
K=3 comparison is a tripwire, not a proof.

---

## Entry 3 -- 2026-08-20 . DECISION SITTING: K=3 x 2 arms, the standards deep cut

**What this is.** Plan 0044 Slice 2b -- the decision comparison the whole instrument was
built for. Arm A = the current catalog (132,203 B); arm B = the deep cut (91,478 B, -30.8%,
branch `0044-2a-standards-cut`). Six builds, ONE sitting, ONE base commit (`7ea0eef`),
interleaved. Small-N caveat: `eval/BUILD_BASELINE.md`, cited.

- **Sitting calibration:** PASSED, 359.5s, H=13, 15 mutants, zero cross-trips.
- **Worktree prep:** six worktrees; class-derived deletion set = 46 files; index removal +
  routing-index fixpoint (one round each); post-deletion pytest 539/0 in all six.
- **Builders:** six fresh clean-context `implementer` spawns, all self-reported **Opus 5**.
  Blind grader for the six-pack: self-reported **Fable 5** (cross-family). One arm (A1) was
  DISCARDED and re-run -- see the contamination note; its replacement's single-pack re-grade
  drew an **Opus 4.8** grader (same-family for that one verdict, disclosed).

### Results

| arm | catalog | M (2-of-3 majority) | mean F | flap | spread |
|---|---|---|---|---|---|
| A | 132,203 B | **10/10** | 13.00/13 | 0 | 0 |
| B (cut) | 91,478 B | **10/10** | 13.00/13 | 0 | 0 |

**Delta = M(A) - M(B) = 0 . DeltaF = 0.00 . floors CLEAR.** Every trap AVOIDED in every run
(TG-5 graded blind AVOIDED on all six packs, each with supporting citations, none discounted).
The only S-axis movement was optional-kwarg signature drift, and it slightly FAVOURED arm B
(2 of 3 B runs compliant vs 0 of 3 A runs) -- separated from quality by design, so it moves no
verdict.

- **VERDICT (pre-registered rule): "no regression detected at this K."** Block iff Delta>=2 or
  DeltaF>=2 or a floor fails -- none fired. Never read as equivalence shown, never predicated of
  the cut itself.
- **SATURATION FIRED (both arms 10/10).** Recorded in entry 2 as a live risk before any arm-B
  number existed; it is now realised. The honest reading: the build-eval did NOT discriminate
  132K from 91K at Opus builder strength -- consistent with the north star (the model already
  holds the knowledge; the catalog's *authoring* value is low at this strength), NOT evidence the
  cut is costless in general. The calibration allowance (re-sharpen the brief/traps once, voiding
  prior runs) was **considered and DEFERRED by the user (2026-08-20)**: the cut lands on the rule
  plus the independent detection evidence below, and the exam re-sharpen is a recorded ROADMAP item
  for future cuts -- not taken now.

### Detection path (independent, NOT saturated) -- the load-bearing evidence for this land

A standard audit (36 agents, deep dial) over the seeded-defect fixture, run against the **91K
deep-cut catalog** as its lens: **recall 10/10** -- every seed, including the historically
coin-flip cohesion seed (its id lives only in the audit eval's own answer key; missed on the FULL
catalog in the post-thinning ablation) and both assert-nothing test seeds as *discrete* findings
(#8, #9 -- no subsumption, resolving that standing concern). 30 findings
surfaced, all 30 verified, **0 refuted**. This matches or exceeds every prior baseline, all of
which ran on the full 130K catalog. `crossModel: true / sameModelTag: null` -- reads on the
orchestrator family per the known engine-semantics bug (`docs/claugentic-ROADMAP.md`), so treat
the finder<->judge relationship as same-family; the recall count is unaffected by that caveat.

- **Attribution:** all six builders OPENED the catalog (11 modules listed each). No catalog-unread
  case; the treatment was received.
- **Contamination:** clean on all six SURVIVING runs (both canaries, both answer-key id sets, both
  key-filename sets -- absent across ~6M chars of transcript and every `out/`). **One discard,
  root-caused and fixed:** the first A1 build ingested `TG-7` plus its remedy sentence from a stale
  verify-round probe script left in the SHARED scratchpad by an earlier slice -- a cross-agent
  Edit-tool collision, not a deletion-set miss (the worktree was clean; the leak came from OUTSIDE
  it). Fixed by evacuating all 566 answer-bearing files out of the shared scratchpad into a private
  store; A1 re-run clean under one disclosed prompt deviation (scratch-inside-the-checkout). A
  second builder (arm A2, kept) independently INFERRED it was inside an eval fixture from the
  surviving `docs/claugentic-INVARIANTS.md` (which names the build-eval paths and is NOT in the
  deletion class) and deliberately avoided the deleted dirs' names -- no answer content is reachable
  that way (the invariant names paths, not traps), recorded as a disclosed residual of the filename
  class, and a candidate to widen the deletion class in a future slice.

### Honest reading

The deep cut lands because the rule cleared it AND an independent, non-saturated detection eval
scored 10/10 on the cut catalog. What this sitting did NOT establish: that the build path can
tell a good catalog from a bad one at this model strength -- it saturated, and says so. The exam
needs re-sharpening before it can gate a *deeper* cut on the output path; that is the deferred
ROADMAP item, not a silent gap.

---

## Entry 2 -- 2026-08-20 . SHAKEDOWN: K=3, arm A only (never a decision input)

**What this is.** Plan 0044 Slice 1b -- the exam's first real sitting. It validates the
instrument end-to-end with real builders and records the first run-to-run noise yardstick.
**Demoted by design (Stage-3 R1(i)):** the standards-cut decision comparison re-derives arm A
inside Slice 2b's own six-run sitting; nothing here is a decision input. Small-N caveat: see
`eval/BUILD_BASELINE.md` (cited, not restated).

- **Base commit:** `2ce66df` (the S1a landing commit). **Arm A identity:**
  `docs/claugentic-standards/` = 130,019 B, 13 files, unmodified.
- **Sitting calibration (step 2):** PASSED, 345.1s, H = 13, 15 mutants, zero cross-trips --
  run before any spawn.
- **Worktree prep (steps 3-6):** three worktrees at the base commit; class-derived deletion
  set = 46 tracked files (the grep authority surfaced nothing beyond the named set); `ls`-
  verified; index removal + routing-index fixpoint converged in one round (23 tree lines);
  post-deletion pytest **539 passed / 0 failed in all three worktrees** (736 minus the 197
  tests in the four deleted test files -- the arithmetic closes).
- **Builders:** three fresh clean-context `implementer` spawns, one sitting, identical
  prompts. All three self-reported **Claude Opus 5** (`claude-opus-5[1m]`). **Grader:
  self-reported Claude Fable 5** -- a cross-family builder/grader split on this run
  (configured and self-reported; still same-vendor: a reduction of shared-blind-spot risk,
  never independence).

### Results

| run | F (held-out) | S (surface) | traps |
|---|---|---|---|
| A1 | 13/13 | **drift**: `notify_over_budget` grew an optional `timeout` kwarg (1 pinned element) | 10/10 AVOIDED |
| A2 | 13/13 | compliant | 10/10 AVOIDED |
| A3 | 13/13 | compliant | 10/10 AVOIDED |

**M(A) = 10 . mean F = 1.0 (floor clear) . flap(A) = 0 . spread(A) = 0.** No delta -- single
arm by design. The S drift is exactly what separate-S exists for: an interface widening never
masquerades as a quality delta, and the nine mechanical trap probes bound regardless.

- **TG-5, graded blind:** seed 20260820; mapping sealed before grading, unsealed after the
  verdicts locked (pack-a=A3, pack-b=A1, pack-c=A2); 0 redacted lines, 0 code lines for
  human review. All three verdicts **AVOIDED**, each with supporting file:line citations;
  none discounted. The grader named pack-c (A2) the nearest call -- request-read plus one SQL
  statement in `monthly_report`'s body with rendering fully separated; two of three is not
  the trap, per the rule as written.
- **Attribution (step 10):** all three builders OPENED the catalog -- A2 exactly the five
  in-scope modules; A1 and A3 those plus a listing of the rest. No catalog-unread case.
- **Contamination (step 11):** both canaries ABSENT; zero answer-key ids and **zero
  answer-key filenames** across ~3M characters of transcripts and every `out/` file --
  cleaner than the sibling eval's recorded filename-residual precedent.
- **Deviations:** none from the procedure. One runner note: the builders' task `.output`
  mirrors materialized empty on this platform; transcripts were read from the session's
  subagents store (same content, different path).

### Honest reading

A 10/10-everywhere shakedown with zero spread says two things and no more: **the instrument
ran end-to-end** (every mechanical figure entered a verdict path, the blind channel worked,
the deletion discipline held), and **the measured noise at this K is zero**. It does NOT say
the exam can discriminate at these builders' strength: three Opus builders under the shipped
implementer contract, reading the full 130 KB catalog, avoided all ten traps -- so if the
Slice-2b comparison's arm B also scores 10/10, that is the pre-registered "no regression
detected at this K" outcome by rule, AND it is the both-arms-saturation shape the calibration
allowance names. The 2b sitting decides per the rule either way; this entry just says the
saturation risk is live, before anyone sees an arm-B number.

---

## Entry 1 — 2026-08-20 · calibration of the instrument (not an arm, not a measurement)

**What this is.** The instrument's own verification, run before any arm exists and required
by `eval/BUILD_BASELINE.md` step 2 before every future sitting. It answers one question: do
these probes discriminate? A probe that fires on clean code would blame a cut for a defect
nobody wrote; a probe that stays quiet on the defect it is named for is a green light that
pins nothing. **No catalog variant was involved and nothing about the catalog is measured
here.**

- **Command:** `python eval/fixture-build/calibration/run_calibration.py`
- **Base:** the working tree at `4fd38ef` plus plan 0044 slice 1a's own diff, un-landed at
  the time of the run (the instrument is what that slice adds, so there is no earlier commit
  this could have run against; the landing commit is the one carrying this entry).
- **Environment:** CPython 3.13.2, pytest 8.3.4, sqlite 3.45.3, Windows 11. Sixteen sweeps
  (one reference, fifteen mutants), **337.6s** wall clock, on the bytes as landed.
- **Pins in force:** `H = 13`, `delta-F >= 2` — pinned together in `eval/BUILD_BASELINE.md`
  before this run, and `H` is asserted equal to the real test count by
  `tests/test_eval_trap_manifest.py`.

### The reference half

| measurement | result |
|---|---|
| held-out suite | **13 / 13** (H/H) |
| pinned surface | **compliant** — every entry point present with the pinned parameter names |
| traps | **10 / 10 AVOIDED** — nine mechanical probes clear, the judged row with **zero** candidate functions |

No probe fires on the clean reference. That is the false-alarm half.

### The mutant half — each flips its own probe and nothing else

| mutant | overlay | its own probe | outcome | cross-trips | held-out | surface |
|---|---|---|---|---|---|---|
| TG-1 | `handlers.py, test_spendlog.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-2 | `handlers.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-3 | `test_spendlog.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-3.with-conftest | `conftest.py, test_spendlog.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-4 | `test_spendlog.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-5 | `report.py` | FLIPPED | JUDGE (candidate evidence appeared) | none | 13/13 | compliant |
| TG-6 | `report.py, test_spendlog.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-7 | `importer.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-7.executemany | `importer.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-8 | `handlers.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-9 | `handlers.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-9.cheerful-status | `handlers.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-10 | `notify.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-10.fire-and-forget | `notify.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |
| TG-10.retry-storm | `notify.py` | FLIPPED | FELL_IN | none | 13/13 | compliant |

**Result: CALIBRATION PASSED.** Reference H/H + 10/10 AVOIDED; **fifteen** mutants covering
ten traps, fifteen flipped probes, zero cross-trips, and no other trap's outcome moved on
any mutant.

### Probes that scored a real defect CLEAN, and the reviews that measured them (2026-08-20)

The first recorded calibration proved each mutant flips its own probe. It could not prove a
probe is unfoolable by a **different syntax of the same defect** — and two Stage-7 panels
then built five, measured them, and were right about all five. **The class is not closed:**
each round found the next instance in a predicate the previous round had just corrected. Each is a probe DEFECT under
`eval/BUILD_BASELINE.md` → *Defect versus tuning*: fixed, recorded, calibration re-run. The
reference was not touched, and no threshold was moved to reach a wanted verdict.

| defect the panel constructed | what it scored BEFORE the fix (measured) | after |
|---|---|---|
| a dashboard returning `{expense_count: 0, total_cents: 0, status: 'ok'}` off a corrupt store | **AVOIDED** — `failure_marker: status='ok'`, i.e. a key NAME was read as proof the failure surfaced | FELL_IN |
| a bounded retry storm: 24 connections at a dead endpoint, 0.51s apart, no backoff | **AVOIDED** — the outcome read only "still running at the bound"; the attempts and gaps were collected and printed but never entered the verdict | FELL_IN |
| a vacuous suite whose fixtures live in the arm's own `out/conftest.py` | **AVOIDED** — the prober OVERWROTE that file, the arm's fixtures vanished, the suite went red for the wrong reason and the arm got a free pass on the trap | FELL_IN |
| round 2: a dashboard returning `{…, budget_status: 'under'}` (also `http_status`, `latest_state`, `statement_count`) off a corrupt store | **AVOIDED** — the health-key pattern was unanchored, so an ordinary payload field read as proof the failure had surfaced. The **same class the round-1 fix was written for**, still live one site over | FELL_IN |
| round 2: a dashboard returning `{…, error: True}` — the most idiomatic surfacing there is | **FELL_IN wrongly** — `"true"` sat in the healthy-value set, so a boolean failure flag read as everything-is-fine, punishing the arms that got it right | AVOIDED |
| round 3: a **faithful, atomic** importer using one `executemany` | **UNCHECKABLE, i.e. counted FELL_IN** — the fault budget was charged per STATEMENT, so a batching arm never reached the injected failure and the probe could not bind. **The instrument blaming a correct arm** — the only AVOIDED-direction defect found so far, and the reason the admit-direction cases are routed (S1a-R2) | AVOIDED |
| round 3: a webhook that returns `{"queued": True}` and hammers from a daemon thread | **AVOIDED** — the watch ended the instant the call returned, so the endpoint was being pounded after the probe had stopped looking. The harm line is about the endpoint, not about who is blocked | FELL_IN |
| round 3: a well-layered function whose query carries `WHERE cents > ? AND cents < ?` | **marked as building markup** — the cohesion mark keyed on a string containing both angle brackets, so a SQL range filter read as a view. Evidence handed to a blind grader, so the cost was a wrong `[J]` candidate | not marked |

Two more, not probe predicates but the same shape — a measurement collected and never allowed
to decide anything:

| instrument defect | what it did (measured) | after |
|---|---|---|
| an overlay drifting beyond its trap | the calibration printed `12/13` held-out in its table and exited **0**: neither held-out drift nor spec-compliance drift reached `problems` | both enter the verdict; observed red: `TG-2: held-out moved to 12/13 (reference: 13/13) — an overlay has drifted beyond its trap` |
| `--only <id>` | printed `CALIBRATION PASSED` from **1 of 13** mutants with the completeness check silently suppressed — indistinguishable from a real calibration in a transcript | prints `PARTIAL (--only …): 1 of 13 mutants … this is NOT a calibration`, and never the unqualified line |

Each fix carries its own mutant, so the class is covered from now on rather than argued
about: the value is READ and not just its key matched; the attempt count and the gaps decide
the second half of that harm line; the removal is APPENDED to whatever conftest the arm
wrote, and a suite that stops COLLECTING is reported UNCHECKABLE rather than as a catch.
Verified by reverting each fix in turn — with the pre-fix code the variants score AVOIDED
(the atomic-batch arm: UNCHECKABLE) and the drift control exits 0 green; with the fixes, all
of them flip or go red. The
two round-2 vocabulary defects have no mutant of their own: they are pinned **hermetically**
instead, parametrized over the two key vocabularies parsed out of the sweep's own source,
one must-mark and one must-not-mark payload per member.

### The two facts worth carrying forward

- **F held constant at 13/13 across all sixteen sweeps.** The functional floor and the trap
  score move independently by construction: every mutant is a **quality** defect that still
  produces a working artifact. That separation is deliberate — the held-out suite was written
  to exercise a path each mutant leaves intact (for instance the report tests cover only
  categories with spend, so a report that has quietly narrowed its category set is caught by
  the trap probe and not by the functional floor). It is what keeps `delta` and `delta-F`
  from being two readings of the same thing.
- **The first calibration attempt FAILED, and the fix went into the mutants.** The standing
  rule it was decided under (`eval/BUILD_BASELINE.md` → *Defect versus tuning*): the
  reference is never touched outside the recorded allowance, and a probe is never adjusted to
  move a score — but a probe that demonstrably does not measure what its row claims is a
  defect and IS fixed, recorded, with the calibration re-run. Here neither applied; the
  mutants were what was wrong. Two mutants (TG-1, TG-6) left the reference's own test suite
  red, which correctly made the two mutation-based probes report UNCHECKABLE on those arms.
  The reading is that an arm whose own suite catches its own defect **has not fallen into the
  trap** — it is a different arm. Both mutants gained a second overlay file so their own
  suite is consistent with the defect they carry (TG-1 drops the test that would have caught
  it; TG-6's suite checks the report against the copy of the category set the report keeps).
  Recorded in `fixture-build/TRAP_MANIFEST.md` so a future reader does not "simplify" those
  overlays back to one file and quietly reintroduce the UNCHECKABLE.

### What this entry does NOT establish

- **Nothing about any catalog.** No arm ran; there is no `delta`, no `delta-F`, no verdict.
- **Nothing about a real builder.** The reference and the mutants are hand-authored, so this
  run says the probes discriminate — not that a spawned `implementer` produces artifacts the
  probes bind to. The first shakedown arm is what tests that end to end.
- **The size of what landed.** Measured over the staged diff at this entry's date: **34 new
  files, 209,871 B**, plus **+15,526 B** net on modified files — **225,397 B repo-side**. The
  plan's Stage-5 acceptance line said *"~30–40 KB of new repo-side files"*; that estimate is
  **superseded, not met**, by 5.5–7.3x. `eval/` is release-stripped, so no adopter downloads
  any of it — the defect is the unmeasured claim, not the bytes, and the correction belongs in
  front of the user before the next slice spends builder runs on top of it.
- **One component lands UNEXERCISED:** `run_sweep.py`'s `judge-pack` subcommand (the shuffle,
  the comment-line redaction log, the sealed mapping). Nothing in this slice runs it; the
  calibration does not reach it. It is written and reviewed, and **that is not verification** —
  the first sitting's blind grading is what will exercise it, and until then it is code nobody
  has run.
- **Nothing about coverage of the trap space.** Ten traps were chosen; a defect class nobody
  planted is not measured, and cannot be. **Nor does it establish that a probe is unfoolable
  by a syntax nobody has tried** — three were fooled the first time somebody tried, and the
  only reason the count is three is that three is how many were constructed.
- The judged row's flip was read from the **evidence** (candidate functions appearing where
  the reference had none), not from a grader's verdict. Blind grading is exercised for the
  first time by the first real sitting, not here.
