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
