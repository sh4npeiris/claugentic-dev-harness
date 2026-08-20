# Build eval — entries

Append-only, **newest first**, human-stamped. Procedure, thresholds and standing rules live
in `eval/BUILD_BASELINE.md` and are not restated here; this file carries results, and it is
answer-bearing by design (per-run trap tables name the traps, which is why it is one of the
few files allowlisted by `tests/test_eval_key_containment.py`).

Every entry cites the small-N caveat in `eval/BUILD_BASELINE.md` rather than restating it: a
K=3 comparison is a tripwire, not a proof.

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
