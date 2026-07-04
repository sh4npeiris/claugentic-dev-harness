# Changelog

Notable, user-facing changes to the `claugentic-dev-harness` plugin. This is a
plain changelog, not marketing copy: it records what changed and why, and stays
honest about the mechanical-vs-model-upheld split the harness is built on.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the
plugin is versioned with [SemVer](https://semver.org/). The authoritative
version is `plugin.json`; each release is published on the `release` branch and
tagged `vX.Y.Z`.

## 0.4.0 (unreleased)

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
  you approve before anything is written.
- **One-command release (maintainer-facing).** `build_release.py --apply --bump
  <version>` -- a harness-self tool, not shipped to adopters -- now runs the full
  flow in one step: bump both manifests from one value, refuse a build whose
  version does not strictly increase, validate the built (already-stripped) tree,
  run the mechanized drop-check against the upstream tip, and run the
  referential-closure gate. It then STOPS and prints a single human-gated push
  command; nothing is tagged or pushed inside `--apply`, so an aborted run leaves
  zero side effects. The release checklist collapsed to a thin wrapper around
  this one command.

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
