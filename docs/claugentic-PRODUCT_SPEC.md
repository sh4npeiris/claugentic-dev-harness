# PRODUCT_SPEC — what this product is supposed to be

> The filled product spec for **claugentic-dev-harness** itself — the dogfood worked example,
> refreshed by `product` spec mode (2026-06-17, full Product Excellence pass; extended to six
> 2026-07-04) to the six-command product — four core (init · product · audit · build) plus two
> utilities (doctor · condense). User-owned; never stamped, never
> auto-refreshed by `init`. Gap mode reads the *code* against the criteria (static — it does not
> run anything); this repo ships no bootable app, so every criterion is `check: "manual"` — gap
> mode still sweeps each one against the implementation.

---

## Who it's for

A capable product person — possibly a non-engineer — driving software development through a
Claude Code agent. They can describe what they want in plain English and make product decisions,
but they can't (or don't want to) read code to verify the agent's claims. They need the harness
to be honest about what was checked versus what is the model's judgment. (Durable context:
`docs/claugentic-PRODUCT.md`.)

## Why this exists (the north star, and the test every addition must pass)

**The agent already has the knowledge and the capability. What it lacks is a team.** So this
harness supplies what a team supplies and nothing else: adversarial review, institutional memory,
and the discipline to finish — never knowledge the model already has.

That is a **falsifiable test for every future addition**: *does this supply something a team
supplies, or is it compensating for a capability the model already has?* Compensations get
deleted, not tuned.

**Corollary, and it cuts against the instinct to add:** as models get more capable, this harness
should get **THINNER, not thicker.** A rule written for a weaker model is debt once the model
outgrows it.

## The job-to-be-done

"When I build software with an AI agent, I want the work to follow a disciplined, reviewable
pipeline that tells me honestly what was verified, so I can ship without personally auditing
every line."

## The promise

An installable harness that makes AI-assisted coding **disciplined and reviewable** across its
six commands — four core (init · product · audit · build) plus two utilities (doctor · condense):
it scaffolds without touching your content unsaid, captures what your product is *supposed* to be,
audits your code against a written quality bar with every finding independently re-checked, drives
approved work through a reviewed pipeline that pauses only at the decisions that are yours, greets
you each session with where you left off, **checks its own health** on demand, and **keeps its own
managed docs lean** — and **never claims more certainty than it has.**

## The invariant — Honest disclosure (the trust register)

Above every feature sits one invariant the whole harness is built to keep: **it never claims more
certainty than it has.** Every judged run (audit · verify · QA · build) reports its cross-model
outcome, computed in code from the judges' own self-reports. The honest split is stated plainly
and never blurred: the architecture-tree and doc-budget checks are the **hook-enforced pair,
where the commit hook is wired**; version-sync, the shipped-content scan and the test suite are
**deterministic when run**; everything else —
reviewer sign-offs, the audit's re-checks, build's pauses, and the session advisor — is
**model-upheld and said so.** The advisor *advises*; it is never a gate. This is the spine every
feature below honors, and it is checkable as **PS-5**. **What good feels like** — "the harness
under-claims rather than over-claims, every time."

## Features

### Safe scaffolding (init)

- **Flow** — install the plugin → run `init` → the managed harness set is upserted into the repo
  (including wiring the codebase-map gate) → a created/refreshed/skipped summary reports exactly
  what was touched, opening with a one-line readiness summary.
- **States** — the non-happy paths: an ambiguous managed-file state stops rather than guesses; a
  re-run converges to the installed version; a degraded setup (no Python, or the gate left off)
  is reported honestly, never a false-healthy claim (see
  [`docs/claugentic-standards/product-ux.md`](claugentic-standards/product-ux.md) → *Loading / empty / error states*
  for the bar; init's surfaces are report-states, not async UI).
- **What good feels like** — "it set everything up and provably didn't overwrite anything of
  mine — it keeps my managed docs lean enough to stay readable, and when I come back it tells me
  exactly where I left off."

### Product memory & conscience (product)

- **Flow** — run `product` spec mode → a plain-English conversation captures who it's for, the
  job, the promise, and each feature's flow/states/criteria, and an Excellence pass proposes
  sharper framing you decide on → it writes the user-owned `docs/claugentic-PRODUCT_SPEC.md`.
  Later, run `product` gap mode → it reads the *code* against those criteria (statically) → the
  gaps land in the product backlog.
- **States** — no spec yet → gap mode stops honestly ("run spec mode first"), never auditing
  guessed intent; the refresh path walks what changed section by section; a budget-capped gap run
  checkpoints PARTIAL with criterion-id resume cells.
- **What good feels like** —
  - "I wrote down what I'm building in plain English, and the harness pushed me to make it
    sharper."
  - "It tells me honestly where the code has drifted from that intent — without running it."

### Verified audit (audit)

- **Flow** — run `audit` → the pipeline sweeps the code through the relevant standards lenses →
  every surfaced finding is independently re-checked → a tiered, tagged, plain-English backlog
  lands in the ROADMAP fence.
- **States** — a budget-capped run checkpoints PARTIAL with exact resume lists; an unrun lens is
  an explicit could-not-run gap, never a silent clean; **a finding I dismiss stays dismissed** — a
  re-audit honors the rejected-findings memory rather than re-surfacing it.
- **What good feels like** — "the to-do list is real: the false alarms were dropped before I ever
  saw them, each item says how it was checked, and the ones I judged wrong don't keep coming
  back."

### Earned autonomy (build)

- **Flow** — point `build` at an approved backlog item → the watched run pauses at the spec,
  before land, and before anything irreversible → an unwatched build-to-green run is requestable
  and unlocks only where the repo has earned it.
- **States** — an unearned build-to-green ask declines naming exactly the unmet conditions with
  the evidence checked; the engine returns every pause to the orchestrator and never lands or
  pushes anything itself.
- **What good feels like** — "autonomy I can actually trust, because it tells me when it hasn't
  earned it."

### Self health-check (doctor)

- **Flow** — run `doctor` → it runs the existing deterministic gates **read-only** (the codebase-map
  check always; version-sync / doc-budgets / shipped-content where their scripts are present, else
  N-A), scans for landed/cold plans and a likely-skipped retrospect, re-asserts `init`'s
  post-conditions → reports a **green / WARN / breach** snapshot. It treats only a bounded-mechanical
  set (delete a landed/cold plan · re-wire the pre-commit hook · apply a user-approved condensation
  diff · tree hygiene), and **only on your explicit approval**; anything substantive routes to the
  roadmap.
- **States** — the diagnose is strictly read-only (nothing is mutated before you select and approve a
  fix); a harness-self gate absent in your repo is reported **N-A**, never a false green; nothing is
  auto-fixed silently.
- **What good feels like** — "I can check the harness's own health any time, and it changes nothing
  until I say so."

### Doc-lifecycle upkeep (condense)

- **Flow** — a doc-budget WARN (or `doctor`'s "condense soon" advisory) flags an over-budget managed
  ledger → run `condense` → it **classifies every entry first** (landed-record / superseded /
  live-constraint / must-hold), absorbs landed narratives to git history, promotes hardened
  constraints to their home, then merges + trims → proposes a **diff you approve** (via the same
  approve-the-diff path `doctor` uses) → re-checks it landed under budget.
- **States** — nothing is written before you approve the diff; a shallow diff that would re-fire the
  WARN on the next append is rejected (cut deeper); when content is genuinely all-live it stops
  rather than over-cut, and names the escape-valve ladder.
- **What good feels like** — "my managed docs stay lean over months of use, and nothing is dropped
  without my say-so — git history keeps the full record."

## Deliberate non-goals (declined 2026-08-19 — do NOT re-propose)

Declined against the north star above: each compensates for a capability the model already has,
or waits on evidence that has not arrived. **Deleting them is the YAGNI rule applied to this
harness itself.** Git history holds the full prior text.

- **Bootstrap-and-approve self-extension** — the harness proposing a tailored per-project agent/skill
  set. A capable model already tailors its approach; this is scaffolding for one that could not.
- **Multi-charter / domain-pack** — re-pointing the kernel at a non-software domain. Diagnosed, never
  built, and no second domain has asked for it.
- **`doctor` ledger-coherence check** — flag semantically conflicting ledger entries. A model reading
  two contradictory rules already notices; this mechanizes noticing.
- **Release/init-contract completeness residual** — its own text said *YAGNI-until-a-real-miss*. No miss.
- **Experience-craft's two deferred parts** — runtime felt-observation (capability unproven) and a
  frozen-schema enum slice.
- **Small standards fills** (`architecture-styles`, error-handling, DDD) — its own text said *only when
  a change pulls it in*. Nothing pulled.
- **Adoption-evidence-gated items** — its own text said *only if a real adopter proves the need*.
  Three deployments, no such need.
- **Stage-2b advisory panel as an engine fan-out** — prose-convened 2b works; engine orchestration was
  conditional on it proving unwieldy, which it has not.

- **The nine proposed gate items** (a local exit-code-observing gate runner · content-anchored spec file-lists · an
  exemption-inside-a-scan pin · the matrix-leg guard's siblings · a `git ls-files` corpus-scan pin · printed
  headroom · a routing-citation resolver · a retired-string sweep pin · IDs-spelled-in-full). Declined
  2026-08-19 **except the matrix-leg guard, which was BUILT** — it is the only one where a green suite hides a
  voided *release* gate. The other eight police how **this repo** writes its own commits, plans and tests; each
  lesson is already a written rule in the shipped surface that owns it (`docs/claugentic-standards/testing.md`,
  the Definition of Done, `synthesizer-gate`), and one pin would have been green on arrival. Mechanizing a rule a
  model reads and follows is compensation.
- **0041's verify-deferred CI/robustness batch** (S2 CI hygiene · S3 advisor timeouts and call-count pins · S4's
  `_repo_root()` five-file sweep · the S10b namespace-retry residuals). Declined 2026-08-19: S2's only consumer is
  this repo's own `release.yml`; the `timeout=` requests name **no hang class** (`git rev-parse --show-toplevel`
  and `git log -1` are local, lock-free, prompt-free); **S4's premise is false** — the five copies are *not*
  byte-identical (the tree gate alone carries a `GIT_DIR` strip); and the retry residuals are compensation, since
  the run log already carries the first cause. **The one real defect in the batch — an unrun honesty judge reading
  as PASS — was BUILT, not deferred.**
- **A repo-wide mechanical-vs-run-gate register sweep.** Declined 2026-08-19: its premise is false. `CLAUDE.md:3`
  already carries the *where wired* scoping, and `:31` already names the deterministic run-gate class; the
  `honesty-reviewer` role owns this sweep as a standing lens.
- **`init --rewrite-wrapper` / a released-shape wrapper catalogue.** Declined 2026-08-19: the repair is not
  unbuilt — `init` already prints a shape-aware refusal *and* the working manual remedy, pinned by
  `tests/test_precommit_wrapper.py`. Automating it is migration tooling for a population of three author-owned repos.
- **Budgeting a non-`.md` file in a ledger shard directory.** Declined 2026-08-19: the glob caps a *shape* of file
  by design, the script's own docstring says so, and zero non-`.md` file has ever landed there.
- **Splitting `eval/BASELINE.md`, and back-filling a row per release.** Declined 2026-08-19: both premises are
  false. The newest entry is **v0.5.2**, not v0.5.0 (v0.5.1 was a hotfix with no eval run — recording a row would
  fabricate a figure), and the procedure names the answer key only to forbid reading it, so splitting blinds nobody
  who is not already required to look away.
- **Sharding or cap-bumping `docs/claugentic-INVARIANTS.md`.** Declined 2026-08-19: the answer to a rule-book at its
  band is **deleting what a red test already holds** — the pin *is* the memory. Condensed instead.
- **Sharding `docs/claugentic-WORKFLOW.md` (plan 0042, deleted).** Declined 2026-08-19, reversing the 2026-08-18
  rung-3 pick: sharding preserves 100% of the bytes and pays 99 anchored pointers across 36 files, the release/init
  contract, and two test pins — to re-house content a thinning pass is about to delete. **Thin it, then cap it.**

**If one is ever re-proposed, the bar is evidence — a real project that needed it — not a better argument.**

## Acceptance criteria

The machine-readable projection of the promise + invariant + features above (the frozen schema —
full runtime semantics in `docs/claugentic-DECISIONS.md`). This repo ships no bootable app, so
every criterion is `check: "manual"`; gap mode sweeps each against the code statically.

```json
[
  {
    "id": "PS-1",
    "feature": "Safe scaffolding (init)",
    "flow": ["Run init in a repo with existing user content", "Re-run init at the same version"],
    "expect": [
      "no user-authored content is overwritten (managed files only are refreshed)",
      "the report headline branches on whether anything was refreshed — never a false 'nothing overwritten' claim",
      "a re-run at the same version is a true no-op",
      "init wires the codebase-map gate whose per-entry form budget keeps the map lean"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-2",
    "feature": "Product memory & conscience (product)",
    "flow": ["Run product spec mode on a repo", "Run product gap mode against the resulting spec"],
    "expect": [
      "spec mode writes a schema-valid acceptance-criteria block and is user-owned (no managed stamp; init never refreshes it)",
      "the Excellence pass returns proposals as user-decided questions and records rejected ones — it never folds an un-adopted proposal into the spec",
      "gap mode reports each criterion as met / partial / missing against the static code and always states it did not run the app"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-3",
    "feature": "Verified audit (audit)",
    "flow": ["Run a standard audit", "Dismiss a finding, then re-run the audit", "Read the backlog fence it writes"],
    "expect": [
      "every surfaced finding carries exactly one verification tag from its own verifier",
      "refuted findings are dropped and reported only as a count",
      "a budget-capped run checkpoints PARTIAL with concrete done/pending cell lists a re-run resumes from",
      "a finding recorded in the rejected-findings memory is not re-surfaced on a re-audit"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-4",
    "feature": "Earned autonomy (build)",
    "flow": ["Ask for an unwatched build-to-green run in a repo that has not earned it"],
    "expect": [
      "the ask declines naming exactly the unmet unlock conditions with the evidence checked",
      "the decline carries the verbatim risk-reduction scoping and offers the watched run",
      "the engine never lands, pushes, or merges (it does commit on its own branch) — every terminal status is a return"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-5",
    "feature": "Honest disclosure (the trust register)",
    "flow": ["Run any judged pipeline (audit, verify, QA, build)", "Read its cross-model run report"],
    "expect": [
      "cross-model is claimed only on confirming different-family self-reports",
      "a same-family run carries the verbatim same-model tag",
      "an unresolvable judge family is reported as unresolved, never asserted as same-model fact",
      "the advisor and other model-upheld surfaces are never reported as gates"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-6",
    "feature": "Self health-check (doctor)",
    "flow": ["Run doctor in a repo", "Select a flagged bounded-mechanical fix"],
    "expect": [
      "the diagnose is strictly read-only — nothing is mutated before the user selects and approves a fix",
      "a harness-self gate whose script is absent is reported N-A, never a false green",
      "only the bounded-mechanical set is treated, and only on explicit approval; substantive findings route to the roadmap"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-7",
    "feature": "Doc-lifecycle upkeep (condense)",
    "flow": ["Run condense on an over-budget managed ledger"],
    "expect": [
      "it classifies every entry before proposing any edit, and proposes a diff the user approves — nothing is written unapproved",
      "a diff that re-lands at or above the WARN is rejected (it cuts deeper) rather than accepted",
      "no live constraint is dropped — absorbed content is recoverable from git history (the archive)"
    ],
    "states": [],
    "check": "manual"
  }
]
```
