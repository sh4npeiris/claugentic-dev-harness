# Changelog

Notable, user-facing changes to the `claugentic-dev-harness` plugin. This is a
plain changelog, not marketing copy: it records what changed and why, and stays
honest about the mechanical-vs-model-upheld split the harness is built on.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the
plugin is versioned with [SemVer](https://semver.org/). The authoritative
version is `plugin.json`; each release is published on the `release` branch and
tagged `vX.Y.Z`.

## Unreleased

### Fixed

- **The chained gates now run on a MERGE, not only on an ordinary commit.** git fires
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
