# PRODUCT_SPEC — what this product is supposed to be

> The filled product spec for **claugentic-dev-harness** itself — the dogfood worked example,
> refreshed by `product` spec mode (2026-06-17, full Product Excellence pass) to the
> four-command product (init · product · audit · build). User-owned; never stamped, never
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

## The job-to-be-done

"When I build software with an AI agent, I want the work to follow a disciplined, reviewable
pipeline that tells me honestly what was verified, so I can ship without personally auditing
every line."

## The promise

An installable harness that makes AI-assisted coding **disciplined and reviewable** across its
four commands (init · product · audit · build): it scaffolds without touching your content
unsaid, captures what your product is *supposed* to be, audits your code against a written
quality bar with every finding independently re-checked, drives approved work through a reviewed
pipeline that pauses only at the decisions that are yours, greets you each session with where you
left off — and **never claims more certainty than it has.**

## The invariant — Honest disclosure (the trust register)

Above every feature sits one invariant the whole harness is built to keep: **it never claims more
certainty than it has.** Every judged run (audit · verify · QA · build) reports its cross-model
outcome, computed in code from the judges' own self-reports. The honest split is stated plainly
and never blurred: the architecture-tree check is the **one hook-enforced gate**; version-sync,
the doc-budget check, and the test suite are **deterministic when run**; everything else —
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

- **Flow** — point `build` at an approved backlog item → checkpoint mode pauses at the spec,
  before land, and before anything irreversible → an unwatched build-to-green run is requestable
  and unlocks only where the repo has earned it.
- **States** — an unearned build-to-green ask declines naming exactly the unmet conditions with
  the evidence checked; the engine returns every pause to the orchestrator and never lands or
  pushes anything itself.
- **What good feels like** — "autonomy I can actually trust, because it tells me when it hasn't
  earned it."

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
      "the decline carries the verbatim risk-reduction scoping and offers checkpoint",
      "the engine never lands, pushes, or touches git — every terminal status is a return"
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
  }
]
```
