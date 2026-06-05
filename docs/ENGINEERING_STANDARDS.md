# Engineering Standards

The engineering quality bar is a **modular catalog** under [`docs/standards/`](standards/README.md) — scoped modules loaded only when relevant, anchored to **ISO/IEC 25010:2023**. This file is the thin entry point.

**Start here → [`docs/standards/README.md`](standards/README.md)** — the catalog index, the meta-rules (select-don't-skip, additive, novel-patterns-allowed), the two-tier global/local model, and versioning. The module contract is [`docs/standards/_TEMPLATE.md`](standards/_TEMPLATE.md).

**How it plugs into the workflow:** the spec (Stage 4) names the in-scope modules/dimensions; `implementer-architect` builds to them; `architect-reviewer` audits against them; "done" = the in-scope dimensions pass (see `docs/WORKFLOW.md` → Definition of Done).

> The original 17 dimensions now live as modules under `docs/standards/` — **no content lost.** Authored deep: `security` · `maintainability-structure` · `testing` · `product-ux` · `data-and-persistence`. Migrated: `reliability-resilience` · `performance-efficiency` · `api-and-contracts` · `observability-ops` · `accessibility-i18n` · `docs-traceability`. Capability modules (Redis, queues, storage, …) are authored just-in-time.

---

> **Current scope (per repo).** This file is a **managed copy** (`/claugentic-dev-harness:update` overwrites it), so the per-repo scope does **not** live here. The `init` skill seeds it in the adopter repo's **`CLAUDE.md` `harness:` section** (a local, non-managed spot that survives `/claugentic-dev-harness:update`): a living, non-capping snapshot of which dimensions/modules are LIVE in *that* repo today (relevance is always a per-change judgment; it grows as the stack grows). The plugin ships only the universal catalog and does **not** ship a populated Current scope.
