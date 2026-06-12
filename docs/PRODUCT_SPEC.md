# PRODUCT_SPEC — what this product is supposed to be

> The filled product spec for **claugentic-dev-harness** itself — the dogfood worked example,
> built by `product` spec mode from the README's own promises (2026-06-12). User-owned; never
> stamped, never auto-refreshed by `init`. Gap mode reads the *code* against the criteria
> (static — it does not run anything); this repo ships no bootable app, so every criterion is
> `check: "manual"` — gap mode still sweeps each one against the implementation.

---

## Who it's for

A capable product person — possibly a non-engineer — driving software development through a
Claude Code agent. They can describe what they want in plain English and make product decisions,
but they can't (or don't want to) read code to verify the agent's claims. They need the harness
to be honest about what was checked versus what is the model's judgment. (Durable context:
`docs/PRODUCT.md`.)

## The job-to-be-done

"When I build software with an AI agent, I want the work to follow a disciplined, reviewable
pipeline that tells me honestly what was verified, so I can ship without personally auditing
every line."

## The promise

An installable harness that makes AI-assisted coding **disciplined and reviewable**: it never
touches your content without saying so, audits your code against a written quality bar with
every finding independently re-checked, drives approved work through a reviewed pipeline that
pauses only at the decisions that are yours, and **never claims more certainty than it has**.

## Features

### Safe scaffolding (init)

- **Flow** — install the plugin → run `init` → the managed harness set is upserted into the
  repo → a created/refreshed/skipped summary reports exactly what was touched.
- **States** — the non-happy paths: an ambiguous managed-file state stops rather than guesses;
  a re-run converges to the installed version (see
  [`docs/standards/product-ux.md`](standards/product-ux.md) → *Loading / empty / error states*
  for the bar; init's surfaces are report-states, not async UI).
- **What good feels like** — "it set everything up and provably didn't overwrite anything of
  mine."

### Verified audit (audit)

- **Flow** — run `audit` → the pipeline sweeps the code through the relevant standards lenses →
  every surfaced finding is independently re-checked → a tiered, tagged, plain-English backlog
  lands in the ROADMAP fence.
- **States** — a budget-capped run checkpoints PARTIAL with exact resume lists; an unrun lens
  is an explicit could-not-run gap, never a silent clean.
- **What good feels like** — "the to-do list is real: the false alarms were dropped before I
  ever saw them, and each item says how it was checked."

### Honest disclosure (the trust register)

- **Flow** — any judged run (audit, verify, QA, build) reports its cross-model outcome → the
  claim is computed in code from the judges' self-reports → same-family and unresolved runs
  carry their verbatim tags.
- **States** — a missing self-report degrades to the same-model floor; an unrecognized family
  reads as unresolved, never asserted as same-model fact.
- **What good feels like** — "the harness under-claims rather than over-claims, every time."

### Earned autonomy (build)

- **Flow** — point `build` at an approved backlog item → checkpoint mode pauses at the spec,
  before land, and before anything irreversible → an unwatched build-to-green run is
  requestable and unlocks only where the repo has earned it.
- **States** — an unearned build-to-green ask declines naming exactly the unmet conditions
  with the evidence checked; the engine returns every pause to the orchestrator and never
  lands or pushes anything itself.
- **What good feels like** — "autonomy I can actually trust, because it tells me when it
  hasn't earned it."

## Acceptance criteria

The machine-readable projection of the promises above (the frozen schema — full runtime
semantics in `docs/DECISIONS.md` → the audit section). This repo ships no bootable app, so
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
      "a re-run at the same version is a true no-op"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-2",
    "feature": "Verified audit (audit)",
    "flow": ["Run a standard audit", "Read the backlog fence it writes"],
    "expect": [
      "every surfaced finding carries exactly one verification tag from its own verifier",
      "refuted findings are dropped and reported only as a count",
      "a budget-capped run checkpoints PARTIAL with concrete done/pending cell lists a re-run resumes from"
    ],
    "states": [],
    "check": "manual"
  },
  {
    "id": "PS-3",
    "feature": "Honest disclosure (the trust register)",
    "flow": ["Run any judged pipeline (audit, verify, QA, build)", "Read its cross-model run report"],
    "expect": [
      "cross-model is claimed only on confirming different-family self-reports",
      "a same-family run carries the verbatim same-model tag",
      "an unresolvable judge family is reported as unresolved, never asserted as same-model fact"
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
  }
]
```
