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
> **ISO/IEC 25010:** performance-efficiency · **Status:** draft
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **"Large enough to matter" is always a judgment about realistic data volumes** — no gate decides it for you.

---

## Algorithmic complexity

- **Auditor checks —** Identify loops over collections in the diff `[J]`; flag any nested loop over the same unbounded collection as a candidate for algorithmic improvement `[J]`; check whether sorting/searching uses an appropriate data structure (set, dict, heap) rather than linear scan `[J]`.

## Caching & invalidation

- **Auditor checks —** Identify cache reads/writes in the diff `[D via grep for cache-related identifiers]`; verify every cache write sets a TTL or has a documented invalidation trigger `[J]`; check that cache keys include all discriminating parameters `[J]`; flag cache-aside patterns without stampede protection on hot keys `[J]`.

## Database access patterns

- **Auditor checks —** Scan ORM usage for lazy-loaded relationships accessed inside a loop `[J]`; verify list endpoints use `.limit()` / `.offset()` or cursor pagination `[J]`; grep for `SELECT *` and flag `[D]`; check migration files for index additions on FK/filter columns `[J]`; verify connection pool settings are not left at defaults for production load `[J]`. *(Depth on all of these: `data-and-persistence.md`.)*

## API & network efficiency

- **Auditor checks —** Identify API calls in loops in the diff `[J]`; flag missing pagination on list endpoints that could return unbounded results `[J]`; check whether a polling loop could be replaced by a webhook/event subscription `[J]`; verify response payloads are not over-fetching (GraphQL over-select, REST extra fields) `[J]`.

## Memory & streaming

- **Auditor checks —** Flag code that loads an entire DB result set or file into a list/array in one call `[J]`; verify file processing uses a streaming API or chunk loop `[J]`; check that large in-memory collections are bounded or short-lived `[J]`.

## Cost & resource efficiency

- **Auditor checks —** Identify calls to pay-per-use APIs in the diff `[J]`; flag any such call inside a loop or bulk processor without a batching/dedupe guard `[J]`; check for polling intervals that could be replaced by a webhook or queue consumer `[J]`; verify that resource allocations (instance sizes, memory limits) are not hardcoded at "maximum safe" when a lower tier suffices `[J]`.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
