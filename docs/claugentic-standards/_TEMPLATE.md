---
# ── Module contract: every docs/claugentic-standards/ module copies this frontmatter ──
module: <kebab-name>            # matches the filename, e.g. "security" -> security.md
title: <Human Title>           # e.g. "Security"
status: stub                   # stub (listed, unwritten) | draft (written, not battle-tested) | stable (dogfooded)
iso_25010: [<characteristic>]  # one+ of: functional-suitability, performance-efficiency, compatibility,
                               #   interaction-capability, reliability, security, maintainability,
                               #   flexibility, safety   (ISO/IEC 25010:2023)
load_scope:                    # how the harness decides to pull this module into a given change
  keywords: [<word>, <word>]   #   tokens in the task / diff that bring this module into scope
  globs: ["<path-glob>"]       #   file globs whose changes bring it into scope
---

# <Title> — <one-line purpose>

> **Loads when:** <plain-English — the kinds of changes that bring this module into scope.>
> **ISO/IEC 25010:** <characteristic(s)> · **Status:** <stub|draft|stable>

Each entry below is one **auditable dimension**. Per change, the reviewer applies the
*relevant* ones **fully** (select-don't-skip), right-sized to the change — never
gold-plating an irrelevant one, never skipping a relevant one.

---

## <Dimension name>

- **Good looks like —** <the target state, concrete and observable.>
- **Auditor checks —** <what to look for and where, phrased as checks. Tag **each check exactly one** of `[D]` (a gate can prove it) or `[J]` (needs a reviewer's eye) — never both. If a check is provable *with* tooling but judgment *without*, split it into a `[D]` check and a `[J]` check.>
- **Confidence —** `deterministic` (a gate proves it — name it) · `judgment` (reviewer call) · `mixed` (some checks each — the per-check `[D]`/`[J]` tags are authoritative). *Drives the scorecard's "verified vs asserted" split — the harness must be honest about what it proved vs what it's vouching for.* The dimension-level label summarizes; the per-check tags are the source of truth.
- **Tradeoff (plain English) —** <1–2 sentences a non-engineer understands: what this buys, what it costs, what breaks if you skip it.>
- **Sources —** <authoritative reference(s) the standard is grounded in.>
- **Motivating incident —** <the concrete failure, near-miss, or recurring pain this dimension/rule prevents — what makes a rule un-cargo-cultable, and what makes it safe to delete once its cause is gone. **Expected on a NEW dimension; not required and not enforced** — the existing catalog mostly omits it (see the authoring rule below).>

<!-- repeat the block above, one per dimension -->

---

## Authoring rules (the catalog meta-rules — do not delete)

- **Additive floor:** add dimensions as you discover them; **never delete** one. This catalog is meant to become "every standard we can think of."
- **Right-size:** apply only *relevant* dimensions per change (`KISS`/`YAGNI`); never skip a relevant one. Relevance is a per-change judgment — see `README.md`.
- **Novel patterns allowed** when they add clear value — justify (problem → why existing patterns fall short → benefit) and record in `docs/claugentic-DECISIONS.md`. Unconventional ≠ wrong.
- **Every dimension carries a Confidence tag** so the harness can separate what it *proved* (deterministic gates) from what it *asserts* (judgment). Trust the oracle, not the model's word.
- **A NEW dimension should cite its motivating incident** — the concrete failure/near-miss/recurring pain it prevents; that is what makes a rule un-cargo-cultable and safe to delete once its cause is gone. **Aspirational, not a gate, and the catalog does not currently meet it:** 3 of 117 dimensions carry one (measured 2026-08-19). Whether to backfill the rest or drop the expectation is undecided — don't read the line above as a rule the catalog holds.

> Governance (two-tier model · managed-copy rules · versioning): see `docs/claugentic-standards/README.md`.
