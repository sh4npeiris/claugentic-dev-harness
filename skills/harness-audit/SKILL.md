---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, loop-until-dry).
---

# /harness-audit — not yet implemented (stub)

This skill is a **deliberate honest no-op** — it lands in plan `0003`, slices **S2a** (understand) + **S2b** (audit + backlog).

When complete it will:
- **Understand first** — build a plain-English **"what your app is & does"** map (structure, entry points, dependencies) + an exclude-set (`node_modules`, `dist`/`build`, vendored, generated) and a prioritized directory order.
- **Audit** — fan out `lens-reviewer`s (one per relevant `docs/standards/` module) over the included code, **dedup**, **loop-until-dry**, **budget-bounded with resumable exhaustion**.
- **Backlog** — write a **tiered** (Tier 1 critical → Tier 3 polish), **tagged** (refactor / capability-upgrade / dependency-health / bug / feature), **dual-layer** (technical + plain-English) backlog to `docs/ROADMAP.md`, with impact + rough effort and a **recommended starting point**. Untested behavior-bearing code → "establish a test baseline" is Tier-1 #1.

**For now:** tell the user `/harness-audit` is not yet built (plan 0003, S2) and take no other action.
