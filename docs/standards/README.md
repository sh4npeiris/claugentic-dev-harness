# Engineering Standards — Catalog

The multi-lens quality bar, as **scoped modules**. A module loads only when a change
touches its concern (see each module's `load_scope`), so the catalog can grow toward
"every standard we can think of" **without bloating any single review**. Anchored to
**ISO/IEC 25010:2023**.

- **Entry point:** `docs/ENGINEERING_STANDARDS.md` (thin — points here).
- **Module contract:** every module copies `_TEMPLATE.md`.
- **Who uses it:** the spec (Stage 4) names the in-scope modules/dimensions; `implementer-architect` builds to them; `architect-reviewer` audits against them (see `docs/WORKFLOW.md` → Definition of Done).

## How to use this catalog (meta-rules)

- **Select, don't skip.** For a given change, the architect picks the dimensions that are *relevant* and meets each one **fully** — no debt. Don't gold-plate irrelevant dimensions (that's its own waste — respect `KISS`/`YAGNI`), but **never skip a relevant one.** Relevance is a per-change judgment.
- **No hard "N/A" caps in the dimensions.** Don't mark a dimension *permanently* irrelevant — a stack grows into things, and a cap would mislead a future agent. A repo's *current* applicability is captured in a **Current scope** section that the `init` skill **seeds per-repo in the adopter's `CLAUDE.md` `harness:` section** (a local, non-managed spot — a non-capping, growing snapshot of which dimensions are live in that codebase today); this plugin ships the global catch-all only and does **not** ship that section populated. Ultimate relevance is always a per-change judgment.
- **Additive, not subtractive.** You may **add** dimensions/standards as you discover them; **don't remove** existing ones. This is meant to become "every standard we can think of."
- **Not confined — to this list or to known patterns.** Exceed the list when a change warrants it. Prefer established design patterns, but you **may invent a novel pattern** when it adds clear value — justify the problem, why existing patterns fall short, and the benefit, and record it in `DECISIONS.md`. Unconventional ≠ wrong.
- **The spec names the in-scope dimensions.** Stage 4 records which dimensions apply to a slice and the target bar; Stage 7 audits against them; "done" = they pass (see **Definition of Done** in `WORKFLOW.md`).

## Two-tier knowledge: global (synced) vs local (stays put)

Standards are **copied into each adopting repo on init**, not read from the plugin at runtime (copy-on-init — see `DECISIONS.md` 2026-06-05 "Copy standards on init").

- **Global modules — this directory.** Universal standards. They are **bundled in the plugin** (the source of truth) and **copied by the `init` skill** into the adopter's local `docs/standards/`, version-stamped and headed **"managed — do not edit."** Agents read the **local copy**. They are **pristine**: `/claugentic-dev-harness:update` re-copies newer versions, so a hand-edit inside an adopting repo is lost on the next sync — **never hand-edit a managed copy.** (The modules in *this* repo are the editable source, so they carry no such stamp.)
- **Local artifacts — the adopting repo (`${CLAUDE_PROJECT_DIR}`).** The **Current scope** snapshot (which dimensions are live in this repo), `CANDIDATES.md` (lessons awaiting promotion), and repo lessons in `CLAUDE.md` / `DECISIONS.md`. These **never propagate** to other repos.
- **Promotion path.** A lesson that's *universal* is staged in `CANDIDATES.md`, reviewed, then promoted upstream into a global module (with a version bump) — so every repo gets it on its next `/claugentic-dev-harness:update`. A lesson that's *repo-specific* stays local. This is the two-tier learning loop; the local half is manual for now (see `docs/WORKFLOW.md` → learning loop).

## Versioning

- Each module is **semver**-versioned in its frontmatter; bump on any content change (patch = fix/clarify · minor = add a dimension · major = restructure).
- `/claugentic-dev-harness:update` compares versions and re-copies newer **global** modules into the adopter's local `docs/standards/`; **local** artifacts are never touched.

## Module index

**11 authored modules** today (`security` … `docs-traceability`); the rows below them are **reserved** (named, not yet authored — authored just-in-time).

| Module | ISO/IEC 25010 | Status |
|---|---|---|
| `security` | Security | **draft** · web-verified |
| `maintainability-structure` | Maintainability | **draft** · web-verified |
| `testing` | Maintainability · Reliability · Functional-suitability | **draft** · web-verified |
| `product-ux` | Interaction Capability | **draft** · web-verified |
| `data-and-persistence` | Reliability · Maintainability | **draft** · web-verified |
| `reliability-resilience` | Reliability · Safety | draft |
| `performance-efficiency` | Performance Efficiency | draft |
| `observability-ops` | Reliability | draft |
| `api-and-contracts` | Compatibility | draft |
| `accessibility-i18n` | Interaction Capability | draft |
| `docs-traceability` | Maintainability | draft |
| `architecture-styles` *(reserved)* | Flexibility | reserved — no file yet (authored when a change pulls it in) |
| `capabilities/` *(reserved)* — Redis, queues, object-storage, third-party-apis, sidecars, ml, search | (various) | reserved — no files yet (authored just-in-time when an audit pulls one in) |

> **Status legend:** `reserved` = named, no file yet · `draft` = authored · `stable` = dogfooded. **web-verified** = the 5 deep modules' citations were checked against their sources and passed an adversarial conformance pass + a deterministic format check; the 6 migrated modules are draft (format-checked — their citations are independently verified when promoted to `stable` or pulled into real work).
