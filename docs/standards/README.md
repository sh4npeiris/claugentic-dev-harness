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
- **No hard "N/A" caps in the dimensions.** Don't mark a dimension *permanently* irrelevant — a stack grows into things, and a cap would mislead a future agent. A repo's *current* applicability is captured in a **Current scope** section that `init-harness` **adds per-repo** (a non-capping, growing snapshot of which dimensions are live in that codebase today); this plugin ships the global catch-all only and does **not** ship that section populated. Ultimate relevance is always a per-change judgment.
- **Additive, not subtractive.** You may **add** dimensions/standards as you discover them; **don't remove** existing ones. This is meant to become "every standard we can think of."
- **Not confined — to this list or to known patterns.** Exceed the list when a change warrants it. Prefer established design patterns, but you **may invent a novel pattern** when it adds clear value — justify the problem, why existing patterns fall short, and the benefit, and record it in `DECISIONS.md`. Unconventional ≠ wrong.
- **The spec names the in-scope dimensions.** Stage 4 records which dimensions apply to a slice and the target bar; Stage 7 audits against them; "done" = they pass (see **Definition of Done** in `WORKFLOW.md`).

## Two-tier knowledge: global (synced) vs local (stays put)

- **Global modules — this directory.** Universal standards. They ship **in the plugin** and are read at runtime via `${CLAUDE_PLUGIN_ROOT}/docs/standards/`. They are **pristine**: a plugin update / `harness-update` overwrites them. **Never hand-edit a global module inside an adopting repo** — the edit is lost on the next update.
- **Local artifacts — the adopting repo (`${CLAUDE_PROJECT_DIR}`).** The **Current scope** snapshot (which dimensions are live in this repo), `CANDIDATES.md` (lessons awaiting promotion), and repo lessons in `CLAUDE.md` / `DECISIONS.md`. These **never propagate** to other repos.
- **Promotion path.** A lesson that's *universal* is staged in `CANDIDATES.md`, reviewed, then promoted upstream into a global module (with a version bump) — so every repo gets it on its next update. A lesson that's *repo-specific* stays local. This is the two-tier learning loop; the local half is manual for now (see `docs/WORKFLOW.md` → learning loop).

## Versioning

- Each module is **semver**-versioned in its frontmatter; bump on any content change (patch = fix/clarify · minor = add a dimension · major = restructure).
- `harness-update` compares versions and pulls newer **global** modules; **local** artifacts are never touched.

## Module index

| Module | ISO/IEC 25010 | Status |
|---|---|---|
| `security` | Security | stub → authored in Phase 0 |
| `maintainability-structure` | Maintainability | stub → authored in Phase 0 |
| `testing` | (cross-cutting) | stub → authored in Phase 0 |
| `product-ux` | Interaction Capability | stub → authored in Phase 0 |
| `data-and-persistence` | Reliability · Maintainability | stub → authored in Phase 0 |
| `reliability-resilience` | Reliability · Safety | stub |
| `performance-efficiency` | Performance Efficiency | stub |
| `observability-ops` | (cross-cutting) | stub |
| `api-and-contracts` | Compatibility | stub |
| `architecture-styles` | Flexibility | stub |
| `accessibility-i18n` | Interaction Capability | stub |
| `docs-traceability` | Maintainability | stub |
| `capabilities/` — Redis, queues, object-storage, third-party-apis, sidecars, ml, search | (various) | deferred (authored just-in-time when an audit pulls one in) |

> **Status legend:** `stub` = listed, not yet authored · `draft` = authored, not yet dogfooded · `stable` = dogfooded. The 5 high-frequency modules are authored first (plan `0002` Phase 0); the rest are stubs until pulled in by real work.
