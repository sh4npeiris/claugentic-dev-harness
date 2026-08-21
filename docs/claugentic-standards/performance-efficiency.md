---
module: performance-efficiency
title: Performance & Efficiency
status: draft
iso_25010: [performance-efficiency]
load_scope:
  keywords: [performance, latency, throughput, cache, n+1, complexity, memory, streaming, cost, polling]
  globs: ["src/**"]
---

# Performance & Efficiency — do the right amount of work, at the right cost

> **Loads when:** the change touches queries, caching, loops, pagination, resource sizing, streaming, or pay-per-use infrastructure.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **"Large enough to matter" is always a judgment about realistic data volumes** — no gate decides it for you.

---

## Algorithmic complexity

- **Auditor checks —** `[J]` no nested loop over the same unbounded collection · `[J]` sorting/searching uses an appropriate structure (set, dict, heap), not a linear scan.

## Caching & invalidation

- **Auditor checks —** `[D]` cache reads/writes in the diff enumerated (grep the cache identifiers) · `[J]` every write sets a TTL or has a documented invalidation trigger · `[J]` cache keys include **all** discriminating parameters · `[J]` cache-aside on a hot key has stampede protection.

## Database access patterns

- **Auditor checks —** `[D]` no `SELECT *` in application queries (grep) · `[J]` no lazy-loaded relationship accessed inside a loop · `[J]` list endpoints paginate (`.limit()`/`.offset()` or cursor) · `[J]` migrations add indexes on FK/filter columns · `[J]` connection-pool settings not left at defaults for production load. *(Depth: `data-and-persistence.md`.)*

## API & network efficiency

- **Auditor checks —** `[J]` no API call inside a loop · `[J]` list endpoints that could return unbounded results paginate · `[J]` a polling loop replaced by a webhook/event subscription where possible · `[J]` responses not over-fetching (GraphQL over-select, REST extra fields).

## Memory & streaming

- **Auditor checks —** `[J]` no whole DB result set or file loaded into a list in one call · `[J]` file processing streams or chunks · `[J]` large in-memory collections bounded or short-lived.

## Cost & resource efficiency

- **Auditor checks —** `[J]` no pay-per-use API call inside a loop or bulk processor without a batching/dedupe guard · `[J]` polling intervals replaced by a webhook or queue consumer where possible · `[J]` resource allocations (instance sizes, memory limits) not hardcoded at "maximum safe" when a lower tier suffices.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
