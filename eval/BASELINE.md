# Eval baseline — the seeded-defect drift detector

## What this eval is

A fixed exam the harness can re-take. `fixture-defects/app/` is a small task-tracker
module carrying **ten seeded, realistic defects** (two per deep standards module:
security, testing, maintainability-structure, data-and-persistence, reliability-
resilience), documented in the answer key `fixture-defects/SEED_MANIFEST.md`. Running a
standard audit over it and scoring how many seeds it surfaces turns prompt/model drift
into a number.

> **This eval measures this fixture at this date — a drift detector, not a quality
> guarantee.** A good score means the audit still finds the flaws it found last time on
> this one small fixture; it does NOT prove the audit is good in general, that the
> standards catalog is complete, or that an audit of a real repo will find its defects.
> The scores are partly human judgment (hit-matching seeds to findings and the
> "judged-real" precision call) and are recorded as such.

## The no-peeking contract

The answer key (`SEED_MANIFEST.md`) and the mapping tables in THIS file reveal the
answers, so a run that reads them would grade itself. The measurement run is therefore
**scoped to `eval/fixture-defects/app/` only** — the manifest and this baseline sit
OUTSIDE that path. The exclusion is **model-upheld** (prompt-scoped, not a filesystem
sandbox): the runner states the scope in the run and states that the manifest is outside
it. The backstops are the **contamination canary** in the manifest (a distinctive
sentence — `the planted-purple-elephant canary` — that, if it ever appears in audit
output, proves the key leaked) and the **no-defect-markers** rule in the fixture source
(the code reads as ordinary sloppy code, enforced by `tests/test_eval_manifest.py`). Each
baseline entry records whether any contamination was declared.

## The measurement procedure (single source of truth)

1. **Scratch worktree/branch** at the release-candidate commit (the eval's writes never
   land on `main`).
2. **Invoke the audit skill at dial `standard`**, scoped to `eval/fixture-defects/app/`
   — the skill invokes `engine/audit.js`. If the Workflow tool is unavailable in the
   session, **abort and note it**: a prose-orchestrated run is not comparable to a scripted
   baseline and is never recorded as one. The runner states the scope and states that the
   manifest (`SEED_MANIFEST.md`) and this baseline are outside it and must not be read.
3. **Collect** the final backlog items + their verification tags, the run report's refuted
   count, and the agents' self-reported model families (builder + judge).
4. **Score by hand** (the human grades; the script produces no scores):
   - **Recall** = seeds matched by a surfaced finding / 10. A match = the same defect at
     the same file (line tolerance — a few lines off the manifest's line is still a hit).
     Record the seed↔finding mapping table so the grade is auditable.
   - **Precision proxy** = surfaced findings that are seeded OR judged-real by the recorder
     / total surfaced. A **proxy** — "judged-real" is human judgment, labeled as such.
   - **Refute-rate** = refuted / total findings sent to VERIFY (the run report's count).
5. **Append the entry** to the table below (newest first). **The human stamps the run date
   after the run — no date/time originates inside the script** (the audit script is
   clock-free; the orchestrator stamps the `{{DATE}}` placeholder). Then **revert the
   audit's fence write** in `docs/claugentic-ROADMAP.md` — the eval backlog never lands there.
6. **Record the contamination check**: did the canary appear in any output? (Expected: no.)

**One calibration allowance, recorded honestly.** If the first run's recall is `< 5/10`,
the **seeds** (never the audit) may be revised once for defensibility — make the seeded
defects clearer flaws, re-pin the manifest, and note the revision + rerun in the entry.
The audit prompts are never tuned to the fixture (that would make the exam self-grading).

## Baseline entries

Append-only, **newest first**. Each entry carries: date (human-stamped) · plugin version ·
dial · scope · builder + judge model families (self-reported, with the same-model tag
verbatim if it fired) · recall · precision proxy · refute-rate · the seed↔finding mapping
table · contamination note.

---

### 2026-08-20 · v0.5.4-dev · standard · eval/fixture-defects/app (post-thinning ablation — NOT a release gate)

- **Why this run exists:** the 2026-08-19 thinning cut the standards catalog **271,977 → 129,999 B
  (−52%)**. The catalog is the audit's lens, so the cut carried a falsifiable prediction — *recall
  holds on half the bytes because what was cut was encyclopedia, not checks.* This run is that test,
  at the same dial, scope and procedure as the release-gate entries.
- **Models — and the honest reading of `crossModel: true`:** the engine returned **`crossModel:
  true`, sameModelTag null** — the first `true` since v0.5.0 — but it must NOT be read as
  finder-vs-judge independence. All **31 sub-agents (5 lens finders, 1 synthesis, 25 verifiers)
  self-reported Opus 5**; the `true` keys on `builderFamily`, which was the **orchestrator's**
  family (Fable 5 — the session tier changed mid-day). So orchestrator↔judge is genuinely
  cross-family; **finder↔judge is same-family (Opus↔Opus)**, which is the relationship that guards
  rubber-stamping. Several verifiers' own `RUNNING AS` lines said exactly that. **The engine
  semantics gap — `crossModel` keys on the orchestrator, not the finding-producer — is filed as a
  Bug** (docs/claugentic-ROADMAP.md); read this run's precision figures as same-family. (Mechanism
  note, verified from run metadata: the sub-agents resolved through the *installed 0.5.2* plugin's
  agent registry, whose files still carry `model: opus` pins — d99b7dc's pin removal ships in
  0.5.3+, which this machine had not reinstalled.)
- **Run shape:** `COMPLETE` — 5/5 cells, **31 agents, 0 errors**, `verificationIncomplete: false`.
  `lensCoverage` all `ran-found`: security 8 · testing 9 · maintainability-structure 11 ·
  data-and-persistence 13 · reliability-resilience 10 (51 raw → 24 surfaced). Scratch worktree with
  the answer key deleted from it, per the v0.5.3 procedure; only the *filename* `SEED_MANIFEST.md`
  surfaced in agents' greps (main-checkout CWD residual, each disclosed), never a line of it.

- **Recall: 9/10 — DOWN one seed from v0.5.3's 10/10. MAINT-1 missed.** Block threshold (−≥2 seeds)
  not reached; the movement is in the blocking direction and is recorded, not smoothed. Map:

  | Seed | manifest loc | finding | match |
  |---|---|---|---|
  | SEC-1 | `handlers.py:23` | #1 search f-string reads any table | exact |
  | SEC-2 | `handlers.py:9` | #3 hardcoded admin token in source | exact |
  | TEST-1 | `test_tasks.py:21` | #7 suite green on broken features (survivor M1 = set_status writes nothing) | tolerance — **subsumed, 2nd consecutive run; see below** |
  | TEST-2 | `test_tasks.py:26` | #7 same item (survivor M5 = render_task_list gutted) | tolerance — **newly subsumed** (v0.5.3 gave it its own item) |
  | MAINT-1 | `service.py:9` | — | **MISS** (#11 is the SQL-placement/layering defect, not the parse+query+render cohesion defect; graded per the v0.5.0 precedent, where the layering near-miss counted as a miss) |
  | MAINT-2 | `handlers.py:6` | #10 STATUSES duplicated, diverged | exact |
  | DP-1 | `db.py:32` | #15 project half-created | exact |
  | DP-2 | `db.py:49` | #16 N+1 per task | exact |
  | REL-1 | `handlers.py:40` | #22 outage reads as zero tasks | exact |
  | REL-2 | `client.py:17` | #23 unbounded retry, no timeout | exact |

- **The MAINT-1 attribution, weighed rather than assumed.** The obvious story — *the cut killed the
  lens* — is measurably NOT supported: the condensed maintainability module still carries the exact
  check the seed needs, verbatim ("*Does any class/function mix unrelated responsibilities (e.g.
  HTTP parsing + business rules + SQL in one place)? (SRP)*"). And the seed is historically the
  weakest of the ten: **v5.0.0-era run missed it with the FULL 272 KB catalog**; found in v0.5.2 and
  v0.5.3; missed here. Two hits, two misses across four runs — a coin-flip seed, and this run's
  finder spent its cohesion attention on the neighbouring SQL-placement finding instead. **The
  trigger, recorded:** a second consecutive post-cut miss implicates the cut despite the surviving
  check (the deleted Good-looks-like prose may have been doing priming work the check alone does
  not), and the remedy then is restoring teeth to that one dimension — never re-inflating the catalog.
- **The TEST-1 escalation the v0.5.3 entry promised has FIRED.** v0.5.3: "if the next run also
  subsumes it, treat that as a recall regression forming." This run subsumed **both** TEST seeds
  into one suite-wide mutation finding (#7) — excellent evidence quality (a 20-mutant run, 19
  survivors, each named), but a reader working the backlog gets one item where the manifest expects
  two discrete fixable defects. **Routed to the roadmap** per the entry's own rule: two instances is
  evidence.
- **Precision proxy: 24/24 (100%)** on the judged-real instrument — 0 pp. Same-family caveat above
  applies. Cross-lens duplication recurred (the STATUSES divergence surfaced from both the security
  lens, #6, and the maintainability lens, #10, with different `findingKey`s) — the v0.5.3 entry said
  route it on a second occurrence; **routed**.
- **Refute-rate: 1/25 (4%) — the first nonzero in the baseline's history, and it is GOOD news:** the
  verifier killed a connection-leak claim by measurement (CPython refcounting closes the handle the
  finding said leaked), which is the adversarial check visibly working rather than rubber-stamping.
  Within the ±15 pp band.
- **Contamination: canary ABSENT** (checked case-insensitively over the full run record). Fence
  write: none — `docs/claugentic-ROADMAP.md` byte-untouched, verified.
- **Verdict: the thinning HOLDS — with one honest asterisk.** 9 of 10 seeds on 48% of the lens
  bytes, every exact-match seed identical to v0.5.3, precision flat, and the one miss is the
  historically flakiest seed whose check survived the cut verbatim. No block threshold approached.
  The asterisk: recall moved −1 for the first time since v0.5.0, on the first post-cut run — the
  next run decides whether that was the coin-flip seed landing tails or the cut's first real cost.

---

### 2026-08-19 · v0.5.3 · standard · eval/fixture-defects/app (release gate for v0.5.3)

- **Models:** builder **Opus 5 (1M context)**; judges **inherit the session tier** — v0.5.3 removed the
  pinned `model:` from the agents and left `MODELS = { judge: null }` in the engine, so there is no longer
  anything to pin them to. `verification.crossModel` came back **`false`** and the same-model tag FIRED
  verbatim: *"same-model review on this run -- the judge and the builder are the same model family here."*
  **This is now STRUCTURAL, not a run-to-run outcome, and it is the honest cost of the portability fix:**
  in a single-session run the judge can never be a different family from the builder, so `crossModel: true`
  is **unreachable** and the disclosure will fire every time. A genuine cross-family read now means running
  the review session on a different tier — which is exactly the one control that works for every adopter,
  and is why the fix was made. Read precision-proxy and refute-rate as same-family; recall is unaffected
  (it is graded by the human against the manifest, not by the judges). Stated in the v0.5.3 CHANGELOG
  under *Known* rather than left for a reader to discover.
- **Run shape:** scripted `engine/audit.js` via the Workflow tool (the only comparable path). `COMPLETE` —
  5/5 cells swept, 0 pending, **32 agents, 0 errors**, `verificationIncomplete: false`. `lensCoverage` all
  `ran-found`: security 9 · testing 7 · maintainability-structure 9 · data-and-persistence 14 ·
  reliability-resilience 11 (**50 raw → 26 surfaced** after coded dedup + synthesis prune; v0.5.2 was the
  same 50 raw → 29 surfaced, so the prune ran slightly harder — no recall consequence). First attempt
  succeeded; no respawn, no resume.
- **No-peeking, STRENGTHENED this run (the v0.5.2 fix, applied).** v0.5.2 recorded that prompt-scoping
  alone let three verifiers' greps surface **SEED_MANIFEST lines**, and prescribed a path-level exclusion.
  This run ran from a **scratch worktree with `SEED_MANIFEST.md` and `BASELINE.md` deleted from it**, so a
  scope-rooted grep cannot reach the key at all. **Honest limit:** agent CWD is still the main checkout, so
  a repo-rooted grep can still see the *filename* — and several did. **What changed is the payload:** this
  run surfaced only the **path**, never a manifest **line**, and every agent that saw it disclosed the fact
  and stated it did not open the file. Structural exclusion of the agents' CWD is the remaining gap.

- **Recall: 10/10 — flat vs v0.5.2's 10/10.** Seed↔finding map (graded by hand; each tolerance case
  re-verified against the source):

  | Seed | manifest loc | finding | finding loc | match |
  |---|---|---|---|---|
  | SEC-1 | `handlers.py:23` | #1 search f-string reads any table | `handlers.py:23-24` | exact |
  | SEC-2 | `handlers.py:9` | #3 hardcoded `API_TOKEN` in source | `handlers.py:9` | exact |
  | TEST-1 | `test_tasks.py:21` | #6 suite passes on deliberately broken code | `test_tasks.py:21-34` | **tolerance — the weakest hit of the ten; see below** |
  | TEST-2 | `test_tasks.py:26` | #7 the test patches the function under test | `test_tasks.py:26-30` | exact |
  | MAINT-1 | `service.py:9` | #13 one function parses + queries + renders | `service.py:9-36` | exact |
  | MAINT-2 | `handlers.py:6` | #10 **and** #11 (a duplicate pair) | `handlers.py:6` · `service.py:6` | exact |
  | DP-1 | `db.py:32` | #17 project half-created if the task write fails | `db.py:32-46` | tolerance — inside `create_project_with_task` (def at `:32`) |
  | DP-2 | `db.py:49` | #18 one extra query per task | `db.py:49-69` | tolerance — the N+1 inside `list_tasks_with_project` (def at `:49`) |
  | REL-1 | `handlers.py:40` | #24 DB outage reported as "zero tasks" | `handlers.py:40-41` | exact |
  | REL-2 | `client.py:17` | #22 unbounded retry, no timeout, no backoff | `client.py:17` | exact |

- **The TEST-1 qualification, stated rather than smoothed over.** v0.5.2 surfaced TEST-1 as its **own
  item** ("write-path test asserts nothing", `test_tasks.py:21-23`). This run did **not**: no finding's
  title names that test. It is instead **subsumed** into #6, a suite-wide mutation finding whose location
  range covers `:21-34` and whose survivor list names *"set_status becomes a no-op"* — precisely TEST-1's
  stated consequence, measured. Meanwhile #7's title claims *"two of the three existing tests check nothing
  real"* while its locations cover only TEST-2. So the defect **was** found and evidenced; it was not
  surfaced as a discrete, fixable item. Graded a hit under the manifest's own rule (same defect, same file,
  line tolerance) — **but a reader working this backlog would fix TEST-2 and might never notice TEST-1
  needs its own edit.** If the next run also subsumes it, treat that as a recall regression forming, not a
  presentational quirk.

- **Precision proxy: 26/26 (100%)** on the baseline-comparable *"judged real on review"* instrument —
  **0 pp** from v0.5.2's 29/29. As in v0.5.2, **no adversarial second instrument was run**, so there is no
  counterpart to v0.5.0's 19/25 refute-first number; that absence is stated rather than papered over, and
  it is why only the comparable figure carries the block decision. The 16 non-seeded findings are all
  literally true of the fixture (stored XSS in the renderer, an auth check that is never called, tests that
  delete the real DB, no indexes, unenforced FKs, a `create-if-absent` schema, no timestamps, leaked
  handles, a constant-true predicate, a timing-unsafe token compare) and all carry evidence.
- **Refute-rate: 0/26 (0%)** — **0 pp** from v0.5.2's 0/29. Same honest caveat as every prior baseline: a
  refute-rate of zero measures the judges' **agreement**, not the findings' truth, and this run's judges
  were same-family (structurally so — above).

- **MEASURED HARNESS DEFECT, new this run: coded dedup missed a same-defect pair.** MAINT-2 surfaced
  **twice** — #10 from the `testing` lens (key `contract-testing-/-declarative-parity-...`) and #11 from
  `maintainability-structure` (key `dry-/-single-source-of-truth-...`). Same defect, same two files, two
  different `findingKey`s, so the coded dedup — which keys on the normalized issue class — never collapsed
  them. **The 26 surfaced items therefore describe 25 distinct defects**, and the precision-proxy
  denominator is one high. Not a recall issue and not a regression vs v0.5.2 (which had no such pair to
  catch), but it is a real duplicate reaching a user's backlog. **Route it to the roadmap only if a second
  run reproduces it** — one instance is not yet evidence that a cross-lens semantic dedup pass is worth
  its cost, and the harness's own north star says an unevidenced addition is declined, not built.
- **Fence write:** none to revert. `engine/audit.js` was invoked directly and returns `renderedBacklog` for
  a skill to write; no skill write step ran, and `docs/claugentic-ROADMAP.md` is byte-untouched (verified
  with `git status --porcelain`).
- **Contamination: canary ABSENT.** The manifest's planted canary sentence appears nowhere in any output
  (checked case-insensitively across the full run record). The answer key was never opened — see the
  no-peeking note above for what *did* leak (the filename only) and what is still open.
- **Verdict: NO REGRESSION — does not block v0.5.3.** Recall **10/10, flat**; precision proxy **0 pp**;
  refute-rate **0 pp**. Block thresholds (recall down by >=2 seeds, or either rate moving >=15 pp) are not
  approached in the blocking direction. Three honest asterisks, none of them blocking: the same-model judge
  family is now **structural**, the adversarial instrument was again not run, and TEST-1 was found but not
  surfaced as its own item.

---

### 2026-08-18 · v0.5.2 · standard · eval/fixture-defects/app (release gate for v0.5.2)

- **Models:** builder **Opus 5 (1M context)**; verifiers/judges pinned `opus`. `verification.crossModel`
  came back **`false`** and the **same-model tag FIRED** verbatim: *"same-model review on this run -- the
  judge and the builder are the same model family here."* **This is a disclosure REGRESSION vs v0.5.0**
  (which ran builder Fable 5 against opus judges and got `crossModel: true`). It does not touch recall —
  recall is graded by the human against the manifest, not by the judges — but it **weakens the
  precision-proxy and refute-rate signals**, which are exactly the two the judges produce. Read those two
  numbers as same-family this run.
- **Run shape:** scripted `engine/audit.js` via the Workflow tool (the only comparable path). `COMPLETE` —
  5/5 cells swept, 0 pending, **35 agents, 0 errors**. `lensCoverage` all `ran-found`: security 9 ·
  testing 8 · maintainability-structure 11 · data-and-persistence 14 · reliability-resilience 8 (50 raw →
  **29 surfaced** after coded dedup + synthesis prune). All 29 verified, 0 unconfirmed, 0 deferred, 0 refuted.
- **First attempt failed and was NOT scored.** Run 1 died in PRUNE with `API Error: Connection lost
  mid-response` on the synthesis agent and `Connection refused` on its respawn — a transport failure after
  5/7 agents had completed, with nothing about the fixture or the lenses implicated. Recovered by
  `resumeFromRunId`, which replays the cached FIND prefix and re-runs only synthesis onward. **A network
  drop is not a measurement and was not recorded as one.**

- **Recall: 10/10 — UP one seed from v0.5.0's 9/10.** **MAINT-1, the seed v0.5.0 explicitly lost, is
  surfaced this run** — and with the *cohesion* framing the manifest describes ("One function parses the
  web request, queries the database and builds HTML", `service.py:9-36`), not the *layering* near-miss a
  3-lens panel scored 0/3 last time. Seed↔finding map (graded by hand; line tolerance applied and each
  tolerance case re-verified against the source):

  | Seed | manifest loc | finding | finding loc | match |
  |---|---|---|---|---|
  | SEC-1 | `handlers.py:23` | #1 SQL injection via f-string | `handlers.py:23-24` | exact |
  | SEC-2 | `handlers.py:9` | #2 hardcoded `API_TOKEN` | `handlers.py:9,14` | exact |
  | TEST-1 | `test_tasks.py:21` | #8 write-path test asserts nothing | `test_tasks.py:21-23` | exact |
  | TEST-2 | `test_tasks.py:26` | #9 patches the function under test | `test_tasks.py:26-30` | exact |
  | MAINT-1 | `service.py:9` | #12 one function parses + queries + renders | `service.py:9-36` | exact |
  | MAINT-2 | `handlers.py:6` | #11 `STATUSES` written twice, copies disagree | `service.py:5-6` | tolerance — same duplication cited from the other side; verified `handlers.py:6` has 3 values, `service.py:6` has 4 |
  | DP-1 | `db.py:32` | #25 two dependent writes, orphan on failure | `db.py:38,40` | tolerance — inside `create_project_with_task` (def at `:32`) |
  | DP-2 | `db.py:49` | #18 one extra query per task | `db.py:55-68` | tolerance — the N+1 loop inside `list_tasks_with_project` (def at `:49`) |
  | REL-1 | `handlers.py:40` | #24 bare except returns a made-up zero | `handlers.py:40-41` | exact |
  | REL-2 | `client.py:17` | #23 unbounded retry, no timeout, no backoff | `client.py:17,19` | exact |

- **Precision proxy: 29/29 (100%)** on the baseline-comparable (neutral "judged real on review") instrument
  — **0 pp** from v0.5.0's 25/25. **No adversarial second instrument was run this time**, so there is no
  counterpart to v0.5.0's 19/25 (76%) refute-first number; that absence is stated rather than papered over,
  and it is why only the comparable figure carries the block decision. The 19 non-seeded findings are all
  literally true of the fixture (missing logging, no indexes, no type hints, unclosed handles, unenforced
  FKs, `create-if-absent` schema, no timestamps), and all sit at T2/T3 — no non-seeded finding claimed T1.
- **Refute-rate: 0/29 (0%)** — **0 pp** from v0.5.0's 0/25. Same honest caveat as prior baselines: a
  refute-rate of zero measures the judges' agreement, not the findings' truth, and this run's judges were
  same-family (above).

- **Contamination: canary ABSENT — but a partial scope leak occurred and is recorded.** The manifest's
  planted canary sentence does **not** appear anywhere in the output (checked three spellings), so the
  answer key was never used. However **three separate verifier agents disclosed incidental leakage**: a
  recursive `grep` matched `SEED_MANIFEST.md` and surfaced one or two of its lines, each agent stating it
  disregarded them and reasoned only from source (e.g. *"A broad grep incidentally printed one matching
  line from SEED_MANIFEST.md; it was disregarded"*). **Structurally this cannot inflate recall:** every
  leak was in **VERIFY**, downstream of FIND, and recall is determined by what FIND surfaced. It is
  nonetheless a real weakening of the no-peeking contract. **Fix for the next run:** pass the exclude-set
  as a *path* exclusion the agents' own greps inherit, rather than relying on prompt-scoping alone — the
  exclusions were passed (`excludeSet`) and still leaked, which means prompt-scoping is not sufficient on
  its own for tools that walk the tree.
- **Fence write:** none to revert. Invoking `engine/audit.js` directly returns `renderedBacklog` for the
  skill to write; no skill write step ran, and `docs/claugentic-ROADMAP.md` is byte-untouched in both the
  main tree and the eval worktree (verified).
- **Verdict: NO REGRESSION — does not block v0.5.2.** Recall **+1 seed**; precision proxy **0 pp**;
  refute-rate **0 pp**. Block thresholds (recall −≥2 seeds, or either rate moving ≥15 pp) are not
  approached in the blocking direction. The two honest asterisks on this run are the same-model judge
  family and the absent adversarial instrument — both weaken *confidence in the precision figures*,
  neither weakens the recall result, and the recall result is the one that moved.

---

### 2026-07-30 · v0.5.0 · standard · eval/fixture-defects/app (release gate for v0.5.0)

- **Models:** builder Fable 5; verifiers/judges pinned `opus`. `verification.crossModel` came back
  **true** (every verifier returned a confirming different-family self-report) and no same-model tag
  fired — a stronger disclosure than the first baseline's unresolved floor.
- **Run shape:** scripted `engine/audit.js` via the Workflow tool. `COMPLETE` — 5/5 cells swept,
  0 pending, 31 agents, 0 errors. 25 findings surfaced, all 25 verified, 0 refuted.
- **Recall: 9/10** — down one seed from the first baseline. **MAINT-1 was NOT surfaced.** The run
  produced a *layering* finding ("Move all SQL into the data-access module", service.py:21-24) where
  v0.1.26 produced the *cohesion* finding ("render_task_list mixes request-parsing, data access, and
  HTML", service.py:9). A 3-lens adjudication panel (strict-rule · remediation-equivalence ·
  user-signal), run blind to each other, voted **0/3 surfaced**: acting on the layering finding as
  written would move the SELECT into `db.py` and leave `render_task_list` still parsing the raw query
  string and still hand-building HTML — the seeded defect survives its own fix. Scored a miss.
  Down 1 seed is **below** the ≥2-seed block threshold.
- **Precision proxy: 25/25 (100%) on the baseline-comparable instrument; 19/25 (76%) under a
  stricter adversarial instrument.** Both are recorded because they are *different instruments* and
  only the first is comparable to v0.1.26. All 25 findings are literally true of the code (the
  neutral "judged real on review" standard the first baseline used → 25/25, 0pp move). A separate
  refute-first panel (one grader per non-seeded finding, prompted to argue the finding is a false
  positive or gold-plating) rejected 6 of the 14 non-seeded findings → 19/25. **Comparing that 76%
  against a neutrally-graded 100% would be an instrument mismatch, not measured drift**, so the
  block decision rests on the comparable number.
- **The signal inside that split (the most useful thing this run produced):** the six rejected
  findings are **exactly the six non-seeded Tier-3 items** (#5 constant-time compare · #6 audit
  logging · #11 coverage floor · #18 `SELECT *`/Python-side filter · #19 indexes · #20 migrations),
  and the same panel flagged all six — and only those six — as severity-inflated. **Every Tier-1 and
  Tier-2 finding survived adversarial grading.** The tiering is doing its job: T1/T2 held real
  defects, T3 held true-but-speculative standards observations, which is what the skill already
  documents T3 to be.
- **Refute-rate: 0/25** (0pp move from 0/20). Worth noting honestly: the pipeline's own
  `finding-verifier` stage confirmed all 25 including the six an independent adversarial panel would
  not have kept. The verifier answers *"is this claim true of the code?"* — it is not a
  worth-acting-on filter, and this run is the first direct evidence of that gap. Banked to the
  ROADMAP; it is not a v0.5.0 blocker.
- **Seed ↔ finding mapping:** SEC-1→"Fix the SQL injection in task search" (handlers.py:23) ·
  SEC-2→"Move the admin token out of the source code" (handlers.py:9) · TEST-1→"Add assertions to
  the set_status test" (test_tasks.py:21-23) · TEST-2→"Delete the test that mocks the very function
  it claims to test" (test_tasks.py:26-30) · **MAINT-1→(no match — see above)** ·
  MAINT-2→"Collapse the two disagreeing status lists into one" (handlers.py:6, service.py:6) ·
  DP-1→"Make project-plus-first-task creation a single transaction" (db.py:38-46) · DP-2→"Replace
  the per-task project lookup with a single join" (db.py:49-69) · REL-1→"Stop the dashboard tile
  reporting zero tasks when the database is broken" (handlers.py:34-42) · REL-2→split across two
  findings, "Give the webhook call a timeout" (client.py:19) + "Bound the webhook retry loop"
  (client.py:17-22), both halves surfaced → scored one hit.
- **Contamination:** the canary line does **not** appear anywhere in the run output — 0 matches for
  `purple.{0,3}elephant` across all 31 agent transcripts. `SEED_MANIFEST` appears 133 times as a
  *path* only (incidental glob/grep hits, same as the first baseline); no agent read the file.
- **Procedure note — a recorded deviation.** The measurement ran in a scratch worktree at the
  release-candidate commit (`82fa80a`), as the procedure requires. **One line of the engine was
  shimmed in that worktree:** `nsAgent()` was changed from `claugentic-dev-harness:<agent>` to the
  bare name, because this session's plugin registry does not resolve the namespaced agent ids (the
  known nsAgent gap banked from plan 0040 — it is what forced the previous attempt to abort). The
  FIND → PRUNE → VERIFY pipeline is otherwise byte-identical to the shipped engine; only the
  agent-id string differs. **This run therefore measures the shipped pipeline through
  project-local agent definitions, not through the installed-plugin registry.** No ROADMAP fence
  write occurred (the script returns the render), so there was nothing to revert.
- **Scoring judgment note:** hit-matching and the "judged real" calls are the recorder's judgment
  per the calibration-honesty rule above. Unlike the first baseline, the two judgment-heaviest calls
  (the MAINT-1 match and the non-seeded precision grades) were delegated to independent panels first
  and the recorder adopted their verdicts — the MAINT-1 miss is an adopted panel verdict that
  overturned the recorder's own provisional "hit".
- **Verdict: no material regression → does not block v0.5.0.** Recall −1 seed (threshold ≥2),
  precision proxy 0pp on the comparable instrument (threshold ±15pp), refute-rate 0pp.

---

### 2026-06-12 · v0.1.26 · standard · eval/fixture-defects/app (first baseline)

- **Models:** builder Fable 5; verifiers/judges pinned `opus` (self-reported Opus 4.x). One
  verifier's self-report did not resolve against the known-family set, so the run's
  disclosure is the **unresolved floor** (verbatim): *"could not resolve the judge's model
  family on this run — no cross-model claim is made (treated as the same-model trust floor,
  not asserted as fact)."*
- **Recall: 10/10** seeded defects surfaced (and all 10 independently verified).
- **Precision proxy: 20/20** — 10 seeded + 10 bonus findings each judged real on review
  (incl. a genuine stored-XSS sink, a missing FK, an unclosed-connection leak the seeding
  didn't plan); 0 surfaced findings were refutable.
- **Refute-rate: 0/20** (the verifiers dropped nothing — and confirmed everything they kept).
- **Seed ↔ finding mapping:** SEC-1→"Search box is wide-open to SQL injection"
  (handlers.py:23) · SEC-2→"Admin auth token is hardcoded" (handlers.py:9) ·
  TEST-1→"set_status test asserts nothing" (test_tasks.py:21) · TEST-2→"render_task_list
  test mocks the function under test" (test_tasks.py:26) · MAINT-1→"render_task_list mixes
  request-parsing, data access, and HTML" (service.py:9) · MAINT-2→"Valid-status list
  duplicated in two files and already out of sync" (handlers.py:6) · DP-1→"Project+first-task
  creation isn't atomic" (db.py:38-46) · DP-2→"Task list runs one extra query per task"
  (db.py:49-69) · REL-1→"get_task_count silently swallows all errors" (handlers.py:40) ·
  REL-2→"Webhook call has no timeout and retries forever" (client.py:17).
- **Contamination:** the canary line does NOT appear anywhere in the run output. The
  manifest was in the exclude-set; one verifier's grep incidentally surfaced the manifest's
  *path* and the verifier explicitly declined to read it, stating its verdict rests on the
  application code only.
- **Procedure note:** run performed on the pre-land working tree rather than a scratch worktree, and no fence write occurred (the script returns the render — nothing was written to ROADMAP), so there was nothing to revert.
- **Scoring judgment note:** hit-matching and the bonus-findings "judged real" calls are
  the orchestrator's judgment against the key, per the calibration-honesty rule above.

| date | plugin version | dial · scope | model families (builder · judge) | recall | precision proxy | refute-rate | contamination |
|---|---|---|---|---|---|---|---|
| 2026-07-30 | 0.5.0 | standard · eval/fixture-defects/app | Fable 5 · Opus (cross-model confirmed; no same-model tag) | 9/10 | 25/25 comparable · 19/25 strict-adversarial | 0/25 | canary absent |
| 2026-06-12 | 0.1.26 | standard · eval/fixture-defects/app | Fable 5 · Opus 4.x (one self-report unresolved → the unresolved-floor disclosure) | 10/10 | 20/20 | 0/20 | canary absent |

<!-- Per-entry detail (the seed↔finding mapping table + notes) goes directly beneath the row
     it belongs to, as a sub-section, when the orchestrator records the run. -->
