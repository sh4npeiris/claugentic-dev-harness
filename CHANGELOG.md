# Changelog

Notable, user-facing changes to the `claugentic-dev-harness` plugin. This is a
plain changelog, not marketing copy: it records what changed and why, and stays
honest about the mechanical-vs-model-upheld split the harness is built on.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the
plugin is versioned with [SemVer](https://semver.org/). The authoritative
version is `plugin.json`; each release is published on the `release` branch and
tagged `vX.Y.Z`.

## Unreleased

### Added

- **The doc-budget gate now ships in the release payload.** `scripts/check_doc_budgets.py` used
  to be stripped from the release as harness-self tooling; its caps became per-repo data in the
  previous change, so the script is adopter-portable and is now part of what you install.
  **Shipping is not delivery, and the difference matters here:** nothing copies the script into
  *your* repo yet — that `init` step is a later change — so for now `python
  scripts/check_doc_budgets.py` will not resolve in your project, and `/doctor`'s budget
  advisory stays your budget signal. Do **not** substitute the plugin's own copy: every gate
  script anchors to its own checkout, so run from your project its verdict is about the plugin
  clone, not yours — from an install (whose caps config is stripped) a "not configured" no-op;
  from a harness dev checkout, a green about the *harness's* ledgers. Where the script IS present it measures that repo's
  ledgers against that repo's `.claude/claugentic-doc-budgets.json`, and with **no** config it
  exits 0 having measured nothing — the not-opted-in posture, so nothing changes for a repo
  that has not written one. It stays a run-gate you invoke; chaining it into the pre-commit
  hook is a later change. `/doctor` and `/condense` now describe the gate and the advisory as
  **two readers of one caps config** rather than a harness/adopter split, and `/doctor`'s
  reader-contract states all three cap forms (plain integer · `{"max": N, "reportOnly": true}`
  · glob-by-key) with their exact edge semantics.

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
