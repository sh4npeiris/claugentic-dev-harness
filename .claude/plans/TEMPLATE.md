# NNNN — <Title>

- **Status:** Draft | In Review | Spec'd | Approved | Implementing | Done
- **Resumable from:** `<the exact next unchecked slice/box, or "awaiting user reply on §X">` — kept current as the plan evolves.
- **Blockers:** `<none | short list with expected resolution>`
- **Roadmap item:** <link to docs/claugentic-ROADMAP.md entry>
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · related plans

## Problem
What's wrong / needed, and why it matters (cite `file:line`).

## Goals / Non-goals
- Goal: …
- Non-goal: … (explicitly out of scope — guards against creep)

## Approach
The chosen design and why; alternatives considered and rejected (1 line each).

## Affected files
`path` — what changes.

## Research / grounding
- **Files reviewed:** `file:line` breadcrumbs the author actually read.
- **Harness docs consulted:** which `docs/claugentic-standards/*` modules · `docs/claugentic-DECISIONS.md` · CLAUDE.md gotchas were read (list as read, not a coverage checkbox).
- **Findings:** what already exists to reuse · what gaps need building · what gotchas apply.

_Substantial plans fill this; small/local changes may skip it._

## Risks & mitigations
Risk → mitigation. Call out anything that could change existing behavior or output (e.g. a regression/snapshot test).

## Test strategy
What tests prove correctness + that existing behavior is preserved.

## Decomposition (slices)
Each slice must land **complete in one ≤1M-context session, no debt**.
- [ ] **Slice 1** — <scope> · lands complete because <…>
- [ ] **Slice 2** — …

---

## Review  _(filled by plan-reviewer, Stage 3)_
- **Verdict:** PASS | CHANGES REQUIRED
- **Required changes:** …
- **Sizing/completeness:** per-slice OK / split …
- **Harness impact:** …

---

## Spec  _(per slice, after Review passes — Stage 4)_
### Slice 1
- **In plain English (shown first at the approval gate):** what this builds · what "done" means for you · what you're accepting (risks / trade-offs).
- **Files & changes:** signatures, exact edits.
- **In-scope standards dimensions:** <the docs/claugentic-standards/* modules this slice touches + target bar> (what Verify audits against).
- **Tests to add:** …
- **Acceptance criteria:** …
