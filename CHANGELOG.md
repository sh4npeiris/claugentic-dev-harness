# Changelog

Notable, user-facing changes to the `claugentic-dev-harness` plugin. This is a
plain changelog, not marketing copy: it records what changed and why, and stays
honest about the mechanical-vs-model-upheld split the harness is built on.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the
plugin is versioned with [SemVer](https://semver.org/). The authoritative
version is `plugin.json`; each release is published on the `release` branch and
tagged `vX.Y.Z`.

## 0.5.4

**What this release is for.** Two things, and the second is why you should take it
promptly. The harness **got 28% smaller** without losing a check — and the first
real-world install found three defects, all fixed here. One of them means your
commit gates may not have been running at all.

### Fixed

- **If only the `py` launcher is on your PATH, both commit gates were silently skipped.**
  The hook probed `python3` and `python` — not `py`, which is the *only* interpreter on a
  common Windows Python install. Reproduced end to end: a planted always-fail gate never
  ran and the commit landed. The hook now probes `py` last (Unix behaviour unchanged; the
  existing 3.7+ check already rejects a Python-2 launcher), and a test pins that the gates
  **run** — mutation-verified, so the pin goes red if the candidate list ever regresses.

  **You are affected if** your machine has `py` but not `python`/`python3`. Re-run `init`
  after updating; the notice now names all three candidates.

- **`init` never told you to stage what it delivered.** It writes a rewired commit hook
  *plus* new files (the gate script, the caps config). `git add -u` or `git commit -a`
  stages the hook and **misses the untracked new files** — so teammates get a wrapper
  chaining a script their checkout doesn't have. Reproduced. `init`'s report now prints the
  exact `git add …` for everything it touched, and warns that `-u`/`-a` won't cover it.
  (Shared mode only — solo mode deliberately tracks nothing.)

- **The hook could be written with Windows line endings, breaking it on Linux/macOS.** The
  shipped file was always LF, but `init` has the agent *write* the hook, and a text-mode
  write on Windows emits CRLF. Real `dash` rejects that with a syntax error while Git Bash
  accepts it — so it works for whoever ran `init` and breaks for everyone else. There is
  now an explicit LF rule on all three hook-write paths with a post-write byte check, and
  `/doctor` gained a CRLF probe on the wired hook.

- **Deleting `docs/claugentic-CHARTER.md` blocked your commits**, even though the docs call
  the charter optional. The budget gate fail-louds on a *missing* budgeted file — correct
  behaviour, and its error already names the one-line fix — but "an absent charter changes
  nothing" was false on a repo that had run `init`. Both places that made the claim now say
  to remove its caps line too.

### Changed

- **The harness is 28% smaller: 1.04 MB → 0.75 MB of shipped prose and code**, and the
  standards catalog — the lens every audit reviews through — went **272 KB → 130 KB**.
  Nothing was cut that does work: **all 117 dimension headings, all 117 auditor-check
  bullets, all 476 `[D]`/`[J]` tags, every threshold and every recorded incident survive
  verbatim.** What went was the bibliography nothing cited, tradeoff essays, prose restating
  a heading, and the same preamble repeated eleven times.

  **Verified, not asserted:** the seeded-defect eval re-ran against the halved catalog and
  held **9 of 10** — every exact-match seed identical to the previous release. The one miss
  is the historically flakiest seed (missed twice before, including with the *full*
  catalog), and the check it needs survived the cut word for word. Recorded honestly in
  `eval/BASELINE.md`, including what would make us conclude the cut was wrong.

- **`docs/claugentic-WORKFLOW.md` finally has a byte cap** (77,500 — it lands at 81%). It
  was the one large managed doc whose growth nothing bounded.

- **Smaller download: the two README diagrams are now inline Mermaid, not images.** 956 KB
  of PNG and Excalidraw — roughly half the payload — is gone; GitHub renders the diagrams
  natively. The real win is maintainability: a rendered image can't be diffed, grepped or
  corrected, which is how four of its labels went wrong and stayed wrong. Those four labels
  are fixed in the new diagrams, and the next one is a one-line change.

### Known

- **`crossModel` reports the relationship between the *orchestrator* and the judges**, not
  between the finder and the judges. On a mixed-tier session that can read as independence
  the run didn't have. The disclosure is still computed from real self-reports, never
  assumed — but read it with that scope. Tracked with its measured case.

## 0.5.3

**What this release is for.** Two threads. The first is **the harness saying only what it
actually did** — six places where a run reported more certainty than it had, including one
where a review that never happened read as a clean pass. The second is **the harness getting
smaller**: the backlog was judged against the product's own north star rather than worked
down, and most of it was deleted. As always, nothing here reaches an existing adopter until
this version publishes **and** they re-run `init`.

### Added

- **Gap mode now tells you which parts of your spec the code DOES deliver.** The promise was a
  criterion-by-criterion **met / partial / missing** report; what shipped was a list of surviving
  problems, so "met" was indistinguishable from "the check quietly produced nothing" and "partial"
  had no representation at all. The per-criterion verdict the reviewer already returned was
  collected and thrown away. Every criterion now carries one of four states — **met · partial ·
  missing · not-checked** — and the fourth matters most: a criterion whose batch was budget-deferred
  or failed is reported as **not checked this run**, never as a verdict.

  **Three things make it trustworthy rather than a relayed claim.** The verdict is **schema-required**
  at the boundary, not prompt guidance a reviewer may forget. Attribution is the **unioned** module
  list — an earlier attempt keyed it on a first-wins field, so a second criterion's finding vanished
  into the first criterion's and that criterion then read **MET**; that path is closed and pinned by
  the regression that found it. And the verdict is **folded against surviving evidence in both
  directions**: a "met" with a surviving finding is downgraded to partial, and a "missing" whose
  findings were all refuted is upgraded to met. The evidence wins, never the claim.

### Fixed

- **The merge hook shipped NON-EXECUTABLE, so on macOS and Linux the merge gate did nothing.**
  `.githooks/pre-merge-commit` was tracked mode `100644` while its `pre-commit` sibling was
  `100755`. Git does not run a hook it cannot execute — it says so and carries on — so the
  merge-commit gate above, **this release's headline fix, silently did not fire on POSIX**, in this
  repo or in any adopter's. Windows and Git-Bash ignore the mode bit entirely, which is exactly why
  it went unseen: it is invisible on the platform this harness is developed on, and no gate looked
  at it.

  Now `100755`, and **pinned across the whole `.githooks/` directory** — derived from the directory,
  so a hook added later is covered on arrival, and asserted on the **index** mode, which is what
  `git archive` writes into the release and what your clone checks out. Verified by making the
  mutation and watching the pin go red.

  **What it means for you:** if you installed a prior version and merge branches locally, your
  budget and codebase-map gates were **not** running on conflict-free merges on macOS or Linux.
  Re-run `init` after this version publishes to get the executable hook. A server-side PR merge
  still runs no local hook at all — unchanged, and stated so nothing is read into this that is not
  there.

- **Twenty-two places still claimed a model pin that no longer exists.** The portability fix below
  removed every `model:` — from all nine agents and from the engine — and then hedged **one** site.
  Left standing across the engine, the agent files, the codebase map, the workflow doc and two
  skills: *"judge-pinned"*, *"cross-model finding-verifier"*, *"model: opus"*, and *"every agent
  runs the most capable available model"*. This harness's one stated invariant is that it never
  claims more certainty than it has, and it was shipping claims of a **cross-model independence the
  run does not have.**

  Swept — 65 sites. What replaced them is what was always the real claim: **independence is of role
  and clean context**, not of model — a separate agent, a clean contract, one lens, never the
  builder's rationale or transcript — and the **same-model tag remains the computed disclosure** of
  the relationship that actually resulted. Two passages were **deleted** rather than corrected,
  because both were platform knowledge you already have: a model-tier/alias table, and a paragraph
  about an experimental editor feature nothing here fires. The one real rule inside them — disclose
  a model substitution in that run's own report — was kept and re-homed.

- **An unrun trust-surface review no longer reads as a clean pass.** On a trust/honesty surface the
  panel convenes an honesty reviewer. If that judge failed twice, `engine/verify.js` reported
  `honesty: null` with **`panelDegraded: false`** and a **PASS** verdict — the adversarial review
  the whole panel exists for could fail silently and the run still read green. It now logs, marks
  the panel **degraded**, and serializes `{ couldNotRun: true }`, exactly as the yagni sentinel
  already did. **It degrades; it does not block** — `finalVerdict` is unchanged, because turning a
  failed spawn into a blocked land was never the ask. The ledger sentence that recorded this as
  *"routed, not fixed"* was amended in the same change rather than left standing.

- **Your spec gaps are no longer pruned by a filter written for engineering audits.** Before you saw
  them, gap findings passed through a step told to cut "marginal nice-to-haves" and told to add an
  "establish a test baseline" item. So a **genuinely promised-but-missing feature could be cut with
  no trace** — and with no per-criterion report, that criterion then simply looked met — while an
  engineering to-do mapping to no acceptance criterion could appear in your product backlog. Gap mode
  now runs a **conformance** prune: cut only exact duplicates and findings citing no criterion, every
  cut reason naming its criterion id, and never the test-baseline item. **Fixed at all three sites** —
  the engine, the reviewer's own contract, and both prose fallbacks; a one-site patch was refused
  because it would have left the engine and the contract disagreeing.

- **Shipped skills no longer point you at files you don't have.** Seven places told the reader to
  consult `.claude/agents/<role>.md`. Those agents are **plugin-resident** — your repo has no such
  directory — so the pointer dangled for exactly the person the skill is written for. The role is now
  named by its id, which resolves. The sweep closes on the **retired string**, not on a list of sites:
  the first pass found five and a re-check found two more.

- **A release gate that could be voided while the suite stayed green.** Three steps in the release
  workflow run on the Linux leg only — the check that the tagged commit is actually on `main`, the
  CLI install, and `claude plugin validate --strict`. Dropping `ubuntu-latest` from the job's matrix
  would **skip all three, leave the job reporting success, and publish anyway**, with the existing
  tests still green because they assert the steps' *text*, never that they *run*. Now pinned, and the
  pin was verified by making the mutation and watching it go red. Recorded as an invariant: **a guard
  is unpinned until a mutation makes its test go red** — the third instance of that class here.

- **Dead code deleted rather than wired.** `engine/qa.js` carried a screenshot-path helper with zero
  call sites that five tests still pinned. Wiring it as the report's oracle would have fabricated a
  path the script cannot verify — it has no filesystem, and the report cites what the driver agent
  returns. Deleted; its tests were **re-aimed** at the sanitizer that guards the live boundary and had
  no direct pin of its own, so removing dead code did not open a real hole.

### Changed

- **The backlog was judged, not worked down — and most of it was deleted.** Every open item was put to
  the product spec's own test: *does this supply what a team supplies, or compensate for a capability
  the model already has?* Each verdict was then handed to an independent re-checker. **Sixteen items:
  eight declined, four built, three split, one routed to a setting only a repo admin can apply.**
  Three items' premises turned out to be **measurably false** and died on inspection. The declines are
  recorded as **deliberate non-goals**, where the bar for re-proposing is evidence — a real project
  that needed it — not a better argument.

  The visible result is a **thinner harness**: the roadmap went 9,500 → 4,396 bytes, the invariants
  ledger 17,976 → 12,751 (four entries a live test already holds were deleted — the pin *is* the
  memory), and three decision shards sitting at their warning band were **condensed rather than given
  a bigger cap**. A plan to split the workflow document into pieces was deleted too: it would have
  preserved every byte and paid for the privilege in ~99 cross-references, to re-house content that
  should be cut instead.

  **The honest limit:** "thinner" here is measured in the ledgers, not in the workflow document itself,
  which is unchanged at ~88,000 bytes and still the one large managed doc with no cap on it.

### Known

- **`crossModel` can no longer come back `true` in a single-session run.** Removing the pinned judge
  model (below) means judges inherit the session's tier, so the judge and the builder are always the
  same family and the same-model disclosure always fires. This is the disclosure working, not
  breaking — but read every judged run's precision figures as same-family unless you deliberately run
  the review on a different tier.


### Fixed

- **The harness no longer names a model it cannot promise you.** Nine shipped agents pinned
  `model: opus` and the engine pinned `MODELS = { judge: "opus" }` — so an adopter without that
  tier got a failed or silently degraded spawn. **No model is named anywhere now:** a judge
  **inherits the session's tier**, which is portable everywhere and means whatever you are driving
  is what judges. Independence here was never of *model* — it is of **role and clean context** —
  and the same-model tag already discloses the relationship that actually resulted, so nothing is
  assumed away. Want judges on a stronger tier? Run the session on it; that is the one control
  that works for every adopter.

- **Seven trust-register defects — the harness claiming more than it did.** Found by `/product gap`
  against the product spec. `init`'s report said *"I did NOT change any of your code or overwrite your
  own files"* on the one path that overwrites yours (it branched on report groups, and the overwrite is
  filed under *Created*); it now branches on **did this run write anything you own**, and names the file
  in the headline. Gap mode called a clean run **"sound"** and never said it hadn't run your app — both
  fixed, and the scope line is now on the fence, which persists, not just in chat. **"Keep all" resurrected
  findings you had dismissed** — "all" now means all of what was *presented*. The backlog never printed
  the **stable id** that resume and dismissal both key on. `build` **asserted same-model** on runs where it
  could not resolve the judge (a three-state disclosure folded to two). The QA summary **always** claimed a
  cross-model re-check. And a **`reportOnly` grace was never cleared** — three surfaces said only
  `/condense` clears it and `/condense` never did, so a capped ledger silently stopped being gated.

- **Running the audit no longer jams your commits.** `/audit` and `/product gap` write their
  backlog **into `docs/claugentic-ROADMAP.md`**, and `init` seeds every adopter a **14,000-byte cap
  on that exact file**. A real backlog costs **~4,815 bytes per finding** — so an adopter's **third
  finding** breached the cap `init` had just given them, and the pre-commit hook then blocked their
  commits. Measured here: a real 25-finding gap run rendered **120,687 bytes**, taking ROADMAP to
  **132,200 — a 9.4× breach of its own cap**. Finding more problems was punished.

  The gate now measures the **hand-written** body and excludes **generated backlog fences**. The
  distinction is the fix: a hand-written ledger **accretes**, and bounding that is what a cap is
  for; a fence is **regenerate-don't-accumulate** — replaced whole on every run, and it **shrinks
  as findings get fixed**. Its size is a symptom, never an accretion. **Deliberately not capped
  separately either:** a cap on the fence would block you from *recording* findings, which is worse
  than the disease — so the size is **reported on every run** instead, visible without being
  punitive.

  Proven both directions on the real 132,200-byte file: old measure → breach, exit 1; new measure
  → 11,513 bytes hand-written, ok, with `+120,687 B in generated backlog fences, not counted`.
  Pinned with a non-vacuity twin (the same bytes *outside* a fence still breach) and a loophole
  guard (an **unclosed** fence is counted in full, the safe direction).

- **The chained gates now run on a MERGE, not only on an ordinary commit** — and, corrected
  before release, they now run on **macOS and Linux too** (see *the merge hook shipped
  non-executable*, below; on POSIX the first version of this fix did nothing). git fires
  `pre-merge-commit` — never `pre-commit` — when a conflict-free `git merge` creates its commit,
  and nothing wired that hook. So a ledger pushed past its cap on a branch **merged clean and
  landed completely unchecked**. Measured on git 2.55 before the fix: a 14,192-byte ledger against
  a 14,000-byte cap merged at exit 0; with the hook wired the same merge is refused, with the
  gate's own reason on screen. `init` now writes `pre-merge-commit` in both hook homes (shared
  `.githooks/`, solo `.git/hooks/`), and it **delegates to the wrapper rather than restating the
  gate list** — one chain, two entry points, so a gate added later covers merges automatically and
  the two can never drift.

  Pinned behaviourally, not by inspection: a breach arriving by merge is refused, **and** a
  non-vacuity twin removes only the merge hook and proves the same merge then lands — so the
  refusal is this hook working, not the merge failing for an unrelated reason.

  **Unchanged, and stated so nothing is read into this that is not there:** a **server-side PR
  merge still runs no local hook at all**, and a merge that stops on conflicts commits through
  `pre-commit` as it always did.

## 0.5.2

**What this release is for, and what it does not do.** The through-line is that
an adopter's harness stays **lean, current, and honest without being asked** — the
byte-cap gate below is the *lean* half, and it is shipped, delivered, seeded and
chained for the **five adopter-authored ledgers** only. Its limit, stated plainly:
it **bounds growth; it never shrinks anything** — a ledger over its cap reports the
breach on every commit the hook sees and keeps passing until a human runs
`/claugentic-dev-harness:condense`. And two preconditions are **manual, neither
automatic**: nothing here reaches an existing adopter until **v0.5.2 publishes**
and they **re-run `init`** in their own repo.

### Added

- **The doc-budget gate now ships in the release payload — and `init` puts it in your repo.**
  `scripts/claugentic-check_doc_budgets.py` used
  to be stripped from the release as harness-self tooling; its caps became per-repo data in the
  previous change, so the script is adopter-portable and is now part of what you install.
  **Shipping is not delivery, and both halves are here:** `init` copies the script into your
  `scripts/` (born under the managed `claugentic-` prefix — one path in every repo), seeds a
  caps config, and chains the gate into your pre-commit hook. Do **not** substitute the
  plugin's own copy: every gate
  script anchors to its own checkout, so run from your project its verdict is about the plugin
  clone, not yours — from an install (whose caps config is stripped) a "not configured" no-op;
  from a harness dev checkout, a green about the *harness's* ledgers. Where the script IS present it measures that repo's
  ledgers against that repo's `.claude/claugentic-doc-budgets.json`, and with **no** config it
  exits 0 having measured nothing — the not-opted-in posture, so nothing changes for a repo
  that has not written one. `/doctor` and `/condense` describe the gate and the advisory as
  **two readers of one caps config** rather than a harness/adopter split, and `/doctor`'s
  reader-contract states all three cap forms (plain integer · `{"max": N, "reportOnly": true}`
  · glob-by-key) with their exact edge semantics.

- **Your ledgers get a commit-time budget signal (`init` delivers, seeds, and chains).** Running
  `/claugentic-dev-harness:init` now (1) copies the doc-budget gate into `scripts/`, (2) seeds
  `.claude/claugentic-doc-budgets.json` with recommended caps for the files that same run
  creates — `CLAUDE.md`, the DECISIONS index and its shard glob, ROADMAP, CHARTER — and (3)
  chains the gate into the shared pre-commit hook right after the architecture-tree check. So a
  ledger drifting past 90% of its cap now says so **on every commit the hook sees** instead of
  never, and one over its cap blocks the commit with the remediation named. **Both gates run every
  time the hook fires**, and a failure in one never hides the other's message. **The gap, stated
  plainly:** the wrapper is a `pre-commit` hook, and a conflict-free `git merge` fires
  `pre-merge-commit` instead — which nothing wires — so **neither gate runs on a merge result**;
  a server-side PR merge runs no local hook at all. **The caps are yours from the moment they
  are written:** the seed is create-if-absent only — a re-run never touches tuned caps, and
  deleting the file is how you opt out. A file that is **already over** its recommended cap on
  day one is seeded `{"max": N, "reportOnly": true}` — the honest cap with the breach reported
  loudly on every commit the hook sees while it still passes — never a cap raised to fit; nothing mechanical
  ever clears that flag (`/claugentic-dev-harness:condense` does the work, you delete the flag).
  **Where it does NOT apply, stated plainly:** a repo that chose "keep my own tree, gate off"
  has no pre-commit wrapper, so it gets no commit-time budget signal — the gate is still on disk
  and `/doctor` still runs it. **An existing wrapper is only rewritten when its RUN LOGIC —
  comments and blank lines ignored, so a comment-only edit of yours can be rewritten — matches
  this version's wrapper without the chain line.** Anything else is left alone and reported,
  and that includes a wrapper installed by **v0.5.1 or earlier: those are never auto-chained**,
  because they predate this wrapper shape entirely. For those `init` prints how to adopt the
  new wrapper (move yours aside and re-run, or diff and replace) — deliberately **not** a
  one-line paste, which would not work there. A machine with no working Python still commits, with one
  skip notice covering both gates. **The two mechanically-enforced gates are now the
  architecture-tree check and the doc-budget check** — everything else the harness claims stays
  model-upheld, and the docs say which is which.

- **`/doctor` gains two health rows.** A **commit-hook interpreter** probe that replicates the
  hook's own candidate loop — each interpreter *executed* against the 3.7+ assertion, never
  merely resolved on PATH (a resolvable-but-broken shim is exactly the case it exists to
  catch) — reporting a dead interpreter as a flag with the hook's own remedy. And **husky-aware
  hook wiring**: a `.husky/pre-commit` carrying the managed marker is now recognized as a
  *healthy* third wiring shape instead of a hooksPath conflict, with sub-flags for a marker
  made unreachable by an early `exit`, a missing exec bit on the chained hook (git index mode,
  checked unconditionally — never conditioned on who created the file), and a
  git-ignored wrapper. The re-wire treat now refuses to re-point `core.hooksPath` away from a
  healthy chain; the treat **count** is still exactly four, though that treat's **boundary** grew
  — it may now offer to un-ignore the wrapper, an action `init` itself refuses to take.

- **Team-friendly commit gate (warn-and-pass) + husky chaining.** The pre-commit wrapper now
  probes for a working Python (`python3` then `python`, 3.7+): a machine without one gets ONE
  plain skip-notice and the commit proceeds — infrastructure failure never blocks a commit
  (a broken git passes silently; a gate that runs and fails still aborts). Gate warnings now
  ride stderr, which the wrapper always lets through, so advisory output survives a passing
  commit. On repos already using husky, `init` OFFERS to chain the gate into `.husky/pre-commit`
  (marker-guarded, idempotent, never an overwrite — travels to teammates via husky's own npm
  `prepare`). The CLAUDE.md fence gains a teammate bootstrap line, and init's report cautions
  about broad build-time content scanners ingesting `docs/` (a real adopter incident).

- **The SessionStart advisor now volunteers two currency nudges** (user-facing only; mute with
  `CLAUDE_HARNESS_ADVISOR=off`): when your repo's stamped harness docs are behind the installed
  plugin it says so and points at `:init`, and when Done/stale plans pile up in `.claude/plans/`
  it points at `:doctor`. Both reads are best-effort and fail silent; the agent-facing context is
  untouched (resume-branch only, byte-identical to before). `/doctor` gains the same skew row.

### Changed

- **Releasing is now gated on green CI — the shape changed.** This is maintainer-facing only;
  the release tooling below is harness-self and not shipped to adopters. Previously a maintainer
  ran the build tool and then force-pushed the `release` branch by hand; nothing mechanical
  stood between a red repository and an adopter's `/plugin install`. (That is how v0.5.1 shipped
  inside an 11-day window where pytest was dying at collection.) Now the harness-self
  `build_release.py --apply --bump <version>` **prepares** locally and stops, your single act is
  pushing the tag (`git tag vX.Y.Z && git push origin main vX.Y.Z`), and a tag-triggered
  workflow re-runs every gate at the tagged commit — the full suite on both OSes, the node
  helper tests, all four gate scripts, a tag-versus-manifest match, a check that the tagged
  commit is actually an ancestor of `main`, and `claude plugin validate --strict` — before it
  builds and publishes. **A run that fails before the branch push publishes nothing** (that push
  is the second-to-last step; see the release ritual for the one window where a red run has
  already served content). Publishing by hand is **retired as a practice, in the documented
  flow** — nothing in the tooling pushes the branch, and only the publish job holds a
  write-capable token — but `release` is not branch-protected, so a maintainer with push rights
  can still write it directly. The workflow publishes by invoking that same harness-self build
  path, never a second build implementation in YAML.
- **What "an aborted run leaves zero side effects" now says instead.** That claim (0.5.0) was
  unqualified. Stated exactly: an aborted prepare creates no tag and runs no push. What it
  leaves depends on how far it got — an early refusal leaves nothing; a later one leaves the
  rewritten manifests in your working tree (revert with `git checkout`) and, if it reached the
  build, a rebuilt local `release` branch (that ref is force-reset, so it is not a `git checkout`
  away — the next run simply rebuilds it). The script still never tags and never pushes.
- **The trade-off this buys, stated plainly.** The tag now comes *before* publishing, so a red
  run **spends that version number** — unless re-running the failed run fixes it, which is safe
  by construction and is the first recovery to try. Otherwise bump forward to the next patch: a
  tag is never reused (deleting a failed tag is a documented exception, and it is yours to
  decide). And because `marketplace.json` is bumped on `main` at prepare time, a failed run
  leaves the catalog advertising a version the `release` branch does not yet serve, until a
  successful run lands. Offline publishing is retired.
- **Test dependencies moved into `pyproject.toml`** as a PEP-735 `test` dependency group, and
  every job that runs pytest installs from it. The pyyaml break above happened because a
  workflow hand-listed its packages and one the suite imports at collection time was missing;
  there is now one place to add a test dependency.
- CI action pins moved off the deprecated Node-20 action runtime (checkout / setup-python /
  setup-node at v7, which run on node24).
- **Four front-door sentences now say what the harness actually does.** The README headline
  claimed it "never changes your code without your sign-off" — true of the full pipeline's
  approval gate, not of the lightweight path small local fixes take, so the claim is now scoped
  to substantial changes and the lightweight path is named. The README's mechanical-gate bullet
  said a hook "blocks *done* until *every file* is documented"; it blocks a **commit**, it covers
  the paths its globs watch, and it is a **pair** now (codebase-map + doc budgets) that is a gate
  only wherever `init` wired the hook — with the no-config and no-Python cases stated. Both
  plugin manifests advertised "deterministic architecture enforcement", which read as always-on
  and architecture-only; they now say "deterministic commit-time gates (the codebase-map and
  doc-budget checks, wired by init)". And `/build`'s description asserted "it stops before
  anything irreversible" as bare fact — the discipline is real and instructed, so it now carries
  its register (model-upheld, never a mechanical gate), matching the guardrail in the skill body.
  No mechanics changed in this entry: only the claims about them.

- **The Stage-9 learning loop now has destinations that exist in YOUR repo — and says where a
  lesson goes upstream.** The harvest destinations used to read as harness-self: "fold it into
  the `.claude/agents/` role file", "edit this `WORKFLOW.md`", "promote to STANDARDS" — none of
  which an adopter can do (the specialist agents live in the plugin install, and your standards
  catalog and WORKFLOW are managed copies a re-`init` replaces). Those destinations now **branch
  by repo type** where they are stated as a checklist (`docs/claugentic-WORKFLOW.md` → *The learning
  loop*, and the `retrospect-harvester` role that points at it): a *universal* lesson is staged
  in `docs/claugentic-standards/CANDIDATES.md` and sent **upstream**, a *repo-specific* one goes
  to a home you already own. And "promote it upstream" finally says **where** — an issue or a
  pull request at the plugin's own repo, written in prose exactly once so it cannot drift.
  Two reviewer roles (`honesty-reviewer`, `product-designer`) also stop pointing at a
  `CLAUDE.md` → "Honesty positioning" section that neither your `CLAUDE.md` nor the harness's own carries;
  each states its premise **inline** instead. The **adopter note** — how WORKFLOW's references
  resolve inside your project — moves from the middle of `WORKFLOW.md` to its **intro**, so you
  read it before the references it corrects rather than a hundred-odd lines later. Nothing new is
  enforced here: this is copy, plus three regression pins that keep it from rotting back.

- **The condensation procedure now lives in exactly one place — the `/condense` skill.**
  `WORKFLOW.md`'s Definition of Done carried a second copy of it, several passages word for word
  with the skill: the keep/drop buckets, the merge-siblings rule, the "landed build-records are
  the primary target" anti-footgun, the lever order and the ~80% band. That copy is **deleted**
  (5,785 bytes net), leaving one line that says what the Definition of Done is actually for — a
  budget WARN is a **do-it-now signal, not a deferral**, discharged inside the current slice —
  and points at `/claugentic-dev-harness:condense` as the operator that owns the steps. **No rule
  changed and nothing moved out of reach:** the **escape-valve ladder stays in `WORKFLOW.md`**,
  where `/condense`, `/doctor` and `init` already point at it. A stale bullet telling you to
  create the caps config by hand also went: `init` has seeded one for you since the doc-budget
  gate shipped (see *Added*, above), and `/doctor` states the config's schema. Every pointer that
  named the deleted text — in `CLAUDE.md`, both decisions-ledger headers, `/doctor` and
  `/condense` itself — now names the skill.

### Fixed

- **"Gate 5" in the Definition of Done was ambiguous — two different items carried that number.**
  The *reviewer sign-offs* list was numbered `5.`/`6.`, continuing the deterministic-gate list
  that already ends at 6, so a cross-reference to "DoD gate 5" could mean the shipped-content
  scan or the standards-dimension audit. The sign-offs are now numbered from 1 within their own
  group; the deterministic gates keep their numbers, so existing references still resolve.

- **A caller could make the Verify panel spawn the same reviewer 200 times.** `dimensions` was
  checked for membership in the standards catalog but was neither de-duplicated nor capped, so a
  list of 200 copies of one module validated cleanly and fanned out 200 reviewer agents over that
  one module. The list is now de-duplicated once, at the boundary, and both consumers (the roster
  and the audited-module list) read that same result — so the fan-out is bounded by the catalog
  (at most one reviewer per module) rather than by the length of the caller's array, and a
  narrowed list is reported in the run log instead of applied silently. The panel's lens and
  cut-list thunks also carry a local guard now: a spawn that fails degrades to "this reviewer did
  not run" **in place**, and the failure is written to the run log rather than swallowed by the
  platform. For a **lens**, the existing coverage check turns that into an explicit gap and a
  forced `CHANGES_REQUIRED`; an unrun cut-list only marks the panel degraded. The trust-surface
  honesty judge is deliberately **not** guarded, because the guard's wording describes neither of
  those consequences for a judge. The file's own header
  claimed the call count was "structurally bounded by the roster — no loops"; both halves were
  false, and it now says what is actually true.

- **The engine could not spawn its own agents when this repo dogfooded itself.** Bundled agents
  are spawned by their namespaced id, which is what an installed plugin resolves — but in a
  project-local session, where the agent definitions live in `.claude/agents/`, only the bare
  name resolves, and every spawn failed at the first call. That is what aborted an eval run and
  forced the published v0.5.0 baseline to be measured through a hand-edited engine, so the
  repo's own baseline does not measure the shipped agent-resolution path. Every engine spawn now
  retries **once** with the bare name when the namespaced spawn *throws*; the bare name is
  derived from the id at runtime, never written down. It is a namespace retry and nothing more:
  it does not consume a judge's one respawn, does not touch the flag that drives the same-model
  disclosure, does not swallow a two-failure error, and carries its own `:ns-fallback` label so
  the run log distinguishes a namespace retry from a model respawn.

- **Four engine defects that shipped in every `/audit`, `/build` and QA run.** Each one is now
  covered by a regression test that was **observed failing against the old code first** — the
  fixes and their tests landed in separate commits so that is checkable in the history.
  - **`/audit`'s "re-render the backlog" fast path never fired.** It read `renderOnly` off the
    *raw* arguments, but a script invocation delivers them as a JSON **string** — the only shape
    `/audit` actually uses. So the documented call fell through and failed argument validation,
    and a caller that re-sent its original arguments got a **second full audit**, with the whole
    reviewer fan-out, instead of a cheap re-render. The check now runs on the parsed arguments.
  - **A build run could report cross-model review it did not get.** When one child confirmed a
    different model family and another explicitly reported *not* confirming, the fold dropped the
    non-confirming signal and reported `confirmed`. It now reports the same-model disclosure, as
    it always should have. (Values only get *more* conservative — never less.)
  - **The runtime-QA driver prompt was malformed.** Its narrowing "check only these states"
    constraint was emitted *before* the agent was told what its job was, and the two sentences
    were run together with no separator at all. The task framing now comes first, and the
    constraint follows it as its own paragraph. In the same pass, the artifact-directory shape
    got a single source: it was documented as having one while four places re-implemented it
    inconsistently, and its trailing-separator trim now handles Windows-style paths (a directory
    ending in `\` used to produce `out\qa\/<run>`).
  - **Build mode's Verify panel substituted defaults silently.** An item that named no review
    dimensions quietly got a two-dimension panel, and a non-boolean `trustSurface` value quietly
    read as `false` — which is the flag that decides whether the trust-surface reviewer runs at
    all. Both values are unchanged (still fail-closed); the run log now **says** when a
    substitution happened, so a narrowed panel is visible instead of invisible.

### Not changed (by design)

- **The eval-drift check stays model-upheld.** CI does not run `eval/BASELINE.md`; nothing
  fires it and nothing grades it. Nor does CI own the `marketplace.json` catalog version — it is
  written at prepare time, outside the green gate. Both are named as such in the maintainer's
  release ritual, which now separates what CI guarantees from what a human still judges.

## 0.5.1

A single-defect patch release. **Adopters on 0.4.0, 0.4.1 or 0.5.0 should take
this one** -- it repairs two skills that were silently loading without their
descriptions.

### Fixed

- **`/build` and `/condense` had unparseable YAML frontmatter.** Both
  `description:` values were plain (unquoted) scalars containing `: `
  (colon-space) -- e.g. `Decision-gated: it proceeds...` -- which YAML reads as a
  nested mapping key, so the whole block failed to parse. The runtime does not
  fail loud on this: the skill loads with **empty metadata and every frontmatter
  field silently dropped**, so the description telling Claude when to reach for
  the skill was simply absent. Both are now folded block scalars (`>-`), with the
  description text preserved byte-for-byte. **This had shipped in 0.4.0, 0.4.1
  and 0.5.0** -- three consecutive releases -- and was found by
  `claude plugin validate --strict`.

### Added

- **A frontmatter gate.** Every `skills/*/SKILL.md` and `.claude/agents/*.md` is
  now parsed by the test suite and required to carry a usable description (plus
  `name` for agents). Nothing had ever parsed frontmatter, which is why the
  defect above shipped three times. The gate was verified to FAIL on the pre-fix
  bytes, not merely to pass afterwards.

### Not re-measured (and why)

- The seeded-defect eval was **not** re-run for this release. Its baseline was
  recorded at the 0.5.0 commit, and the entire delta since is this changelog, two
  YAML scalar reformats whose text is unchanged, and one new test file -- nothing
  on the audit path (no engine, standards module, agent, audit skill, or
  fixture). Re-running it would measure the same inputs; the 2026-07-30 baseline
  stands.

## 0.5.0

A ledger-scaling and intake release, published alongside the first eval baseline
since 0.1.26.

### Added

- **The decisions ledger is sharded.** `docs/claugentic-DECISIONS.md` is now a
  routing INDEX over per-topic shards in `docs/claugentic-decisions/` (honesty,
  gates, verify-roles, audit, build-mode, workflow-process, roles-review,
  doc-lifecycle, plugin-distribution, release-contract), each with its own byte
  budget. Growth is horizontal -- a topic that outgrows a shard gets a new shard
  rather than bloating one file. External references still point only at the
  index, never at a shard path, so a future re-split stays cheap.
- **A mirror-back intake rule.** Stage 0 of the workflow now has a
  shape-triggered rule to mirror the request back before building, on either the
  staged or the lightweight path -- the cheapest possible guard against
  confidently building the wrong thing.

### Changed

- The marketplace description now names all **six** live skills; it had been
  claiming five and omitting `/condense` since that skill shipped.

### Measured

- **The seeded-defect eval was re-run as the release gate** (`eval/BASELINE.md`,
  2026-07-30) -- the first recorded baseline since 0.1.26. Recall **9/10**
  (down one seed, below the block threshold), precision proxy **25/25** on the
  instrument the prior baseline used, refute-rate **0/25**, canary absent. Two
  findings were banked rather than fixed: `finding-verifier` checks whether a
  claim is *true*, not whether it is *worth acting on* (an independent
  refute-first panel would have cut six findings the pipeline kept -- exactly the
  six non-seeded Tier-3 items, with every Tier-1/Tier-2 finding surviving both),
  and the run needed a bare-name agent shim because the engine's namespaced
  agent ids did not resolve in the measuring session. Both are honest, recorded
  limitations, not claims of a clean bill of health.

## 0.4.1

- Carry-forward gate, a DECISIONS condensation pass, an architecture-tree entry
  trim, a six-lens leanness audit (20 of 21 proposals refuted and recorded as
  do-not-re-propose), and a cross-platform CI fix for the pre-commit hook.

## 0.4.0

A doc-lifecycle-and-release hardening release. The headline is a portable
doc-budget story for adopters and a single-command release flow for maintainers.

### Added

- **Robust adopter doc-lifecycle.** A portable, config-driven `/doctor`
  doc-budget advisory (reads `.claude/claugentic-doc-budgets.json`,
  skip-when-absent) plus a first-class `/condense` skill and a documented
  escape-valve ladder. This lets an adopter's managed ledgers (DECISIONS,
  ROADMAP, CLAUDE.md) stay lean without depending on the harness's internal
  byte-budget gate, which is stripped from the release and never runs in an
  adopter repo. The advisory is exactly that -- an advisory, not a hook or a
  gate; `/condense` classifies every ledger entry first, then proposes a diff
  you approve before anything is written. *(Correction 2026-08-14, kept here
  rather than rewritten: the "stripped from the release and never runs in an
  adopter repo" half is now dated -- the byte-budget gate joined the release
  payload in the ship-class change under Unreleased. The rest still holds: a
  repo-local copy needs an `init` delivery step that does not exist yet, so the
  advisory remains the adopter-side signal.)*
- **One-command release (maintainer-facing).** `build_release.py --apply --bump
  <version>` -- a harness-self tool, not shipped to adopters -- now runs the full
  flow in one step: bump both manifests from one value, refuse a build whose
  version does not strictly increase, validate the built (already-stripped) tree,
  run the mechanized drop-check against the upstream tip, and run the
  referential-closure gate. It then STOPS and prints a single human-gated push
  command; nothing is tagged or pushed inside `--apply`, so an aborted run leaves
  zero side effects. The release checklist collapsed to a thin wrapper around
  this one command. *(Correction, kept here rather than rewritten: "zero side
  effects" was unqualified -- depending on how far it got, an aborted run can
  leave the rebuilt local `release` branch (force-reset, not checkout-revertable)
  and the bumped manifests. And the publish half of this entry is superseded by
  the CI-publishes change under Unreleased.)*

### Changed

- **Named and grounded as a dynamic-workflow multi-agent harness.** The harness
  is framed explicitly against the three failure-modes described in the Claude
  Code dynamic-workflows guidance, used as honest rationale for the staged
  pipeline and the clean-context reviewer roles -- not as a novelty claim.
- Advisor script renamed to `claugentic-session-advisor.py` (was
  `claugentic-advisor.py`) to avoid confusion with the platform's own advisor
  concept.
- Bundled edge-skill pointers and context-economy notes added to the workflow
  docs, grounded in the official Claude Code memory/context guidance.

### Not changed (by design)

- **Test-first enforcement stays model-upheld.** A mechanical, hook-based
  red-first enforcement gate (a `PreToolUse` characterization-test hook) was
  considered and deliberately declined. The harness does not force test-first;
  the red-first discipline stays model-upheld, and the one hook-enforced gate
  remains the architecture-tree check. Over-claiming a mechanical guarantee the
  harness does not have would violate its own honesty rule.

## Prior versions

Condensed one-line-per-release history; git history is the full archive.

### 0.3.x -- craft and methodology

- **0.3.0** -- the "addractive" craft pass: a first-class product/UX craft bar
  (aesthetic and motion), a per-project design-language seam, and a designer
  role that pushes the spec to be more ambitious.
- **0.3.0** -- optional engineering-charter seed: a living, per-work-type
  methodology record an adopter can grow (create-if-absent, never refreshed).
- **0.3.1** -- engine scripts hardened to ASCII-only (a strict adopter
  permission layer was silently demoting the engine to a prose fallback), with a
  mechanical codepoint guard.

### 0.2.x -- hardening and honesty

- **0.2.0** -- restored the distillation work a prior release had silently
  dropped, and added a base-ancestry guard so a stale release base can no longer
  drop merged work.
- **0.2.1** -- doc-budget WARN band (a ledger signals before it hard-breaks) and
  a cross-model honesty fix.
- **0.2.2** -- portable SessionStart advisor hook; the doc-budget gate listed in
  the Definition of Done.
- **0.2.4** -- fixed an uninstallable-plugin bug: the marketplace `source` must
  be the documented github object form, not the `owner/repo@ref` string.

### 0.1.x -- foundations

- Initial public releases: the staged workflow, specialist agent roles, the
  ISO/IEC 25010-anchored engineering-standards catalog, and the deterministic
  architecture-tree check. Later 0.1.x work moved the workflow choreography into
  the `engine/` scripts, added the decision-gated build mode, and established the
  release/init consistency contract.
