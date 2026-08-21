---
module: testing
title: Testing
status: draft
iso_25010: [maintainability, reliability, functional-suitability]
load_scope:
  keywords: [test, spec, coverage, mock, stub, fixture, characterization, regression, snapshot, e2e, mutation]
  globs: ["**/*.test.*", "**/*.spec.*", "**/test/**", "**/__tests__/**"]
---

# Testing — does the suite actually prove the behavior, and will it catch the next regression?

> **Loads when:** tests are added, edited or deleted; a behavior change that *should* be tested; a refactor of legacy/untested code (characterization first); UI work (visual + a11y); flaky-test triage; coverage/CI-gate changes.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **Governing rule: trust the oracle, not the author's word.** "Tests pass" is necessary, never sufficient — ask *what would have to break for this test to fail?*

---

## Test pyramid (shape of the suite: unit / integration / e2e)

- **Auditor checks —** `[J]` tested at the cheapest level that proves it · `[J]` no inverted pyramid (many e2e, few unit) signalling untestable design · `[D]` suite wall-clock and per-tier counts where the runner reports tiers · `[J]` integration tests hit the *real* seam (DB, serialization, HTTP contract), not a mock of the thing under test.

## Characterization tests & golden master (the equivalence oracle for legacy refactors)

- **Auditor checks —** `[J]` characterization tests land *before* a non-trivial refactor of untested code, visible in commit order · `[J]` they capture *actual* behavior, quirks and bugs included · `[D]` golden-master baselines committed, diffable, regenerable by a documented command · `[J]` throwaways later promoted or kept deliberately · `[J]` the oracle absorbed its adversarial pass **before** its first recorded run — afterwards the same fix is indistinguishable from tuning the exam, and the artifact owes a defect-versus-tuning rule (0044 S1a).

## Mutation testing (are the tests real?)

- **Auditor checks —** `[D]` mutation score meets the agreed threshold on the changed critical module (e.g. ≥80% on core logic) · `[J]` survivors triaged (gap → assertion, equivalent → justified suppression) · `[J]` aimed at logic that matters, not vanity-run over trivial code · `[D]` mutation config/CI step present where adopted · `[J]` for every **named central claim** — a test whose *name* asserts a structural property ("anchored to `__file__`, not the cwd", "capped", "byte-identical") — the wrong implementation it forbids was BUILT, RUN, and went red; four vacuity shapes recur (0041 S10a): **self-recompute**, **own-constant tautology** (remedy: an independent literal), **ambient coincidence** (the one cwd/locale/timezone/working-tree shape where right and wrong agree), **inactive regime**, **corpus-elsewhere** · `[J]` boundaries pinned from **both** sides (`n-1`, `n`, `n+1`) against a fixed reference.
- **Incident —** 0041 S3 (2026-08-13), three pins that asserted nothing: a `__file__`-vs-cwd pin recomputed its own expression, and pytest runs from the root where both coincide (killed by a subprocess with `cwd=tmp_path` over a **decoy** manifest); a 30-day boundary fed boundary **+5s** let `>`→`>=`, `30`→`7` and `abs()` survive (killed by a `(29,F) (30,F) (31,T) (-31,F)` table against a fixed `now`); a "byte-identical" promise was pinned where the reserve never bites. One **equivalent** mutant (`.isdecimal()`→`.isdigit()`) was proven so over all 1,114,112 code points and kept with its proof.

## Declarative artifacts (CI workflows, manifests, config — and instruction files a human or agent executes) — assert the refusal, not the vocabulary

- **Auditor checks —** `[D]` delete the guard clause the test names, re-run: red? (a whole-file substring survives on a neighbouring `echo` or error message) · `[D]` artifact parsed (YAML/JSON/TOML), not string-matched · `[J]` each assertion anchored to its owning job/step/key, not searching the document globally · `[J]` it asserts the artifact *refuses* the bad case, not that it *mentions* the check · `[J]` cross-artifact parity **derived** as a set relation plus a floor, never hand-typed · `[D]` occurrences of the asserted literal in the artifact itself: >1 makes a whole-file assertion vacuous by construction · `[D]` **this dimension owns the anchoring technique** for an instruction artifact with no parser (a runbook, a prompt/skill file, a template an agent executes): assert the anchor occurs **exactly once**, split on it, assert **inside that slice** — never an ordinal index, never the whole file · `[D]` every fixture derived from the artifact's own bytes; a hand-transcribed copy tests your reading of the prose, not the prose.
- **Incident —** Three, same repo. (1) `/build` and `/condense` shipped across v0.4.0–v0.5.1 with **unparseable YAML frontmatter** — three releases loading empty metadata, because nothing parsed them. (2) 0041 S2 (2026-08-12): **13 mutants, 9 alive** — deleting a lease comparison *and its `exit 1`* left the suite 26/26 green on a surviving `echo` in an adjacent step; closed by a `_step_run(job, name_fragment)` helper failing loud on 0-or-2 matches, and `gate_scripts(ci) ⊆ gate_scripts(release)` replacing a hand-typed list. (3) 0041 S7 (2026-08-16), twice in one slice, the second inside the fix for the first: a whole-file substring pinned a path occurring eight times, so deleting the headline row left all 638 tests green.

## Code the suite cannot EXECUTE, pinned as TEXT — assert the effect, and weigh the cost of moving the code

- **Auditor checks —** `[D]` run the mutant that **keeps the named construct and removes its payload** (keep the loop, delete the call inside it): red? · `[D]` a pin guarding a FORBIDDEN construct is mutated by CONSTRUCTION — build it in a syntax the spec did **not** name (an in-place `for` loop where the pin says `.map(`) and run it · `[J]` the pin forbids the **hazard** (what must not be swallowed, reshaped, spawned), never today's construct · `[J]` the assertion names an effect — a value produced, a call reached, an order held — not a keyword satisfiable without the behavior · `[D]` region-anchored, not whole-file (*Declarative artifacts* above owns the technique) · `[J]` where the diff **moved** production code to make it testable, the pin needs **values** (an output over many inputs, an ordering, a format), never **shape** — a move for a shape-only pin is production surface bought for nothing · `[J]` the region's untestability recorded where the next author meets it.
- **Incident —** 0041 S10a (2026-08-17): a pin asserted a `for…of` loop **exists**, and the mutant that kept the loop and deleted the `log()` inside it survived — under a test whose own failure message names the defect. The same slice relocated **three** helpers "so they can be pinned"; one earned it, two bought ~two dozen lines of production surface each. *Recurred at S10b: a pin on a "fatal if ignored" trap asserted the guard's **vocabulary**, and the gate built **two** forbidden implementations green at HEAD.*

## Exemptions and allowlists inside a scan are themselves under test

- **Auditor checks —** `[D]` every branch of the exemption vocabulary exercised, parametrized over a set **derived** from the scan's own source · `[J]` per branch, a fixture where that exact token rides a **live violation** and the scan still fires — positive-only coverage proves the vocabulary live, only the negative fixture proves it narrow · `[J]` each admitted phrase read against the class the guard is named for, not one that merely co-occurs · `[D]` delete the exemption, re-run: which tests go red? (a guard nothing pins is decoration) · `[J]` the exemption's measured **residual** written down, not implied to be zero.
- **Incident —** 0041 S6 (2026-08-14/15), twice in one slice, in the guard that had just become the **sole** mechanical custody of a class of stale shipped copy: a "history is not a denial" contract shipped with a **forward** clause naming the next slice; the second member was a bare present-state negation ("is no longer *shipped*"). Both narrowed and pinned in both directions.

## A scan's CORPUS is part of its contract — enumerate from the tracked tree, not the disk

- **Auditor checks —** `[D]` `git ls-files` with a fail-loud `check=True`, never `rglob(`/`os.walk(`/a repo-rooted recursive glob — **a working checkout is not the repo**: a walk swallows vendored virtualenvs, tool caches, build output and **linked worktrees parked inside the checkout** · `[D]` sweep run in **both** shapes (maintainer checkout, fresh clone or linked worktree), corpus **sizes** equal · `[D]` a corpus floor assertion (`len(candidates) >= N`) exists · `[J]` one enumeration convention per repo, recorded **at the call site** as a do-not-revert comment, since no gate re-derives it · `[D]` for every DERIVED set — above all a **vocabulary** parsed out of a document — mutate the source so **one** member stops parsing (bold, footnote or re-case the cell): red, or does the set quietly shrink while the scan reports clean? · `[D]` the derived set's size pinned against a cardinality another file **owns**, not a floor that 1-of-N satisfies · `[J]` a docstring's delegation claim is an assertion: make it mechanical or delete it · `[J]` the corpus includes **the slice that ADDS the scan** (plan record, ledger line, the pin's own docstring) and never git history — so a **commit message** is out of scope by construction (`docs-traceability.md` → *Change explainability* owns that half).
- **Incident —** 0041 S9 (2026-08-17): a pin enumerated markdown with `Path.rglob`. In the maintainer's checkout, **129 `.md` files, 61 leaked from linked worktrees** under a gitignored `.claude/worktrees/`, against **60 files and zero leaks** via `git ls-files` — GREEN in a worktree, GREEN in CI (which clones fresh, so the class passes CI *by construction*), RED only where the land ran; 8 more untracked `.md` came from a vendored virtualenv and a tool cache. *Recurred at S11 (2026-08-18) on the derived-vocabulary half: bolding **one** cell dropped its token from a regex-derived set asserting only non-emptiness, and republishing it elsewhere passed the entire suite — the sibling guard counted ROWS, the pin counted CELLS.*

## A checker's VERDICT is part of its contract — what it measured decides, and a narrowed run says so

- **Auditor checks —** `[D]` for each figure the tool prints, break what it measures and re-run: does the **exit code** move, or only the report? · `[J]` every collected quantity either enters the verdict or is labelled *advisory* — a figure on screen while the exit code comes from a narrower set is a green light with the evidence for red already printed · `[D]` run each narrowing flag (`--only`, `-k`, a subset filter): the verdict line names the subset, and the unqualified line is unreachable from it · `[J]` a narrowed run's transcript is distinguishable from a full run's.
- **Incident —** 0044 S1a (2026-08-20), **three in one slice**, in an instrument whose whole job is emitting verdicts: a hazard probe printed a dead endpoint's connection attempts yet scored on *"still running at the bound"* alone, so a 24-attempt no-backoff retry storm scored AVOIDED; the calibration runner printed `12/13` held-out and **exited 0**; `--only <id>` printed the unqualified pass line off **1 of 13** cases. All found by reading the report against the exit code, never by the suite.

## Forward promises need a tripwire (a strict expected-failure that fires when the promise is KEPT)

- **Auditor checks —** `[D]` grep the diff for forward-looking registrations and comments (*will*, *once X lands*, *planned*, a TODO naming a future change) — each has a test that **changes state** when the future arrives · `[D]` the marker is **strict** (`@pytest.mark.xfail(strict=True)`, `it.failing`): a lenient expected-failure passes in both worlds and guards nothing · `[J]` the tripwire asserts the *fulfilled* state, so it flips on success — today's state flips on nothing · `[J]` the abandonment branch is written down. *(Do-not-re-propose, 2026-08-14: pinning the strictness itself guards against vandalism, not drift.)*
- **Incident —** 0041 S4 (2026-08-13): a referential-closure gate accepted a new config path as an "init generates it" output while the init step writing it was a **later slice of the same plan**, and its own "if that slice is abandoned, re-annotate" instruction had **no mechanism behind it** — drop the slice and the gate vouches forever, green, for a file nothing produces. Closed by three lines **plus** the wording fix that stopped asserting a plan-order convention as a *property*.

## Coverage of behavior, not vanity %

- **Auditor checks —** `[J]` tests assert outcomes a caller cares about, not private internals and mock call-order · `[J]` no test executes code and asserts nothing (or only `not throws`) where a real outcome should be checked · `[J]` they would fail if the behavior silently changed, not only if the implementation is rewritten.

## Test-diff review (did the assertions/coverage get weaker?)

- **Auditor checks —** `[D]` grep the diff for `skip`, `only`, `xit`, `xdescribe`, `@Disabled`, `@Ignore`, `pytest.mark.skip`, `todo`, commented-out assertions, widened tolerances · `[J]` each removed or loosened assertion has a stated, legitimate reason · `[D]` diff-coverage shows changed lines didn't drop below threshold · `[J]` no expected value changed *to follow* the implementation (rubber-stamping a regression).

## Failure-path & edge-case coverage

- **Auditor checks —** `[J]` boundaries and invalid inputs tested, not only the typical case · `[J]` every error branch / `catch` / fallback exercised and its *effect* asserted, not just "didn't crash" · `[D]` branch coverage on the changed unit · `[J]` external-dependency failures injected (timeout/5xx/exception) and the degradation asserted.

## Determinism (no flaky tests)

- **Auditor checks —** `[D]` grep for nondeterminism smells: `sleep(`, `setTimeout`-then-assert, unseeded `random`, `Date.now()`/`new Date()`/`time.time()` in assertions, order-dependent fixtures, `@Retry`/`flaky`/`rerun` annotations · `[J]` async synchronized by await/poll on a condition, not a magic delay · `[D]` suite passes under randomized order (`--shuffle`/`-p randomly`) and on repeat runs · `[J]` known-flaky tests tracked and being fixed, not silently retried.

## Regression & snapshot tests

- **Auditor checks —** `[J]` each bug fix carries a test that would have caught the original · `[D]` snapshot files committed and present in the diff · `[J]` snapshots scoped, not sprawling captures rubber-stamped on update · `[J]` any snapshot update justified by an intended change.

## Visual-regression & accessibility testing (UI)

- **Auditor checks —** `[D]` visual-regression diffs against an approved baseline across key viewports/themes (Playwright / Chromatic / Percy / Storybook), committed and reviewed, not auto-accepted · `[D]` axe-core / `jest-axe` assertions on changed UI, build failing on new violations — automated a11y is a **floor, not a pass**: axe-core detects roughly half of issues (Deque 2021: ~57% across 13,000+ pages; older estimates ~30%) · `[J]` critical states (loading/empty/error, focus, RTL, dark mode) captured, not just the happy render · `[J]` manual keyboard/screen-reader coverage for what scanners miss (per `product-ux.md`).

## Contract testing (provider/consumer compatibility)

- **Auditor checks —** `[J]` changes to a published API/event carry a contract test (pact, schema-compat, stored-response verification) rather than slow brittle end-to-end · `[D]` provider verification / schema-back-compat runs in CI and passes; broker "can-I-deploy" green where adopted · `[J]` the contract is the genuine consumer expectation, not a stale hand-written stub · `[D]` breaking-change detector (Buf/OpenAPI-diff) gates the published surface.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
