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
> Method, tags and the honesty register: `README.md` → *Reading a module*.
> <Optional last line: ONE governing rule specific to THIS module. Omit if there isn't one.>

---

## <Dimension name>

- **Good looks like —** <the target state — **only** where it carries a threshold, a named primitive, or a house preference the heading and the checks do not. **Omit the bullet otherwise**: a sentence that restates the heading is dead context.>
- **Auditor checks —** `[D]` <clause> · `[J]` <clause> · `[D]` <clause>.
- **Honesty register —** <only where the dimension must state what it deliberately does NOT prove or gate. Never compress this distinction away; compress the words around it.>
- **Incident —** <the concrete dated failure this rule prevents — the rule and a short dated pointer, never the retelling. **Expected on a NEW dimension; not required, not enforced.**>

<!-- repeat the block above, one per dimension -->

**The checks bullet is a CHECKLIST, not prose.** One ` · `-separated **clause** per check, each carrying **exactly one** tag — `[D]` (a gate can prove it — name the gate) or `[J]` (a reviewer's eye) — never both, never none. A check that is `[D]` with tooling and `[J]` without is **two clauses**, not one hedged tag: that split IS the mechanical-vs-model-upheld distinction, never compressed away. A clause carries what a model cannot infer — the threshold, the named tool, the house preference, the defect class this project hit — and nothing the heading already says. **These tags ARE the confidence record.**

---

## Authoring rules

- **Additive floor:** add dimensions as you discover them; **never delete** one — this catalog is meant to become "every standard we can think of."
- **Right-size:** apply only *relevant* dimensions per change (`KISS`/`YAGNI`); never skip a relevant one — `README.md` → *Reading a module*.
- **Novel patterns allowed** when they add clear value — justify (problem → why existing patterns fall short → benefit) and record in `docs/claugentic-DECISIONS.md`. Unconventional ≠ wrong.
- **Write for a capable model: NAME the convention, don't TEACH it.** No exposition, no bibliography, no plain-English gloss of a term the reviewer already knows. A module earns bytes only where it (a) names a check the model would otherwise **skip**, (b) sets a **threshold or house preference** it cannot infer, or (c) records a **defect class this project actually hit**. Everything else is encyclopedia — charged to every review that loads the module. *(2026-08-19: cut by more than half on exactly this rule — per-dimension Tradeoff prose, Sources lists and the duplicated preamble went. 2026-08-20: cut again to the clause form above, on the same rule. Do not re-inflate.)*
- **A NEW dimension should cite its dated motivating incident** — that is what makes a rule un-cargo-cultable and safe to delete once its cause is gone. **Aspirational, not a gate, and the catalog does not meet it:** only a minority carry one (`grep -c '\*\*Incident —\*\*' docs/claugentic-standards/*.md`). Whether to backfill the rest or drop the expectation is undecided — don't read the line above as a rule the catalog holds.

> Governance (two-tier model · managed-copy rules · versioning · the honesty register): `README.md`.
