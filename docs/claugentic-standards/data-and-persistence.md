---
# ── Module contract: every docs/claugentic-standards/ module copies this frontmatter ──
module: data-and-persistence
title: Data & Persistence
status: draft
iso_25010: [reliability, maintainability]
load_scope:
  keywords: [db, database, query, sql, orm, migration, schema, index, transaction, model, repository, replica]
  globs: ["**/models/**", "**/migrations/**", "**/repositories/**", "**/*.sql", "**/schema*"]
---

# Data & Persistence — the stored state stays correct, consistent, and recoverable

> **Loads when:** a change touches the database — schema/models, migrations, queries, ORM mappings, repositories, transactions, indexes, or replication. Anything that reads or writes durable state.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **The unifying invariant: the stored truth never silently corrupts, never silently loses a write, and can always be rebuilt.**

---

## Schema design & normalization

- **Auditor checks —** `[D]` columns that should be mandatory carry `NOT NULL`; status/type columns constrained (enum/FK/check), not free strings · `[J]` each denormalization has a stated read-path justification **and** a consistency mechanism, recorded in `docs/claugentic-DECISIONS.md`.

## Indexing strategy

- **Auditor checks —** `[D]` every FK column has a covering index (schema introspection) · `[D]` no duplicate indexes (same leading columns) · `[J]` each index maps to a known predicate/join/sort, not cargo-culted · `[J]` composite column order justified by query shape (leftmost prefix) · `[J]` a covering index considered where a flagged hot read still does a table lookup.

## Migrations — versioned, reversible, zero-downtime

- **Auditor checks —** `[D]` a checked-in migration with a version/sequence, not ad-hoc SQL · `[D]` a down-migration, or an explicit irreversibility note · `[D]` CI runs migrations forward **and** back on a scratch DB · `[J]` a destructive or blocking change on a live table (drop/rename column, add `NOT NULL`, type change) split **expand→migrate→contract** across deploys · `[J]` backfills batched to avoid long table locks.

## Transactions & isolation levels

- **Good looks like —** The isolation level is **chosen, not defaulted-by-accident** — know the engine's default (PostgreSQL/Oracle = Read Committed) and raise it for invariants that read-then-write across rows. Transactions stay **short**: no network calls, no user think-time inside an open one.
- **Auditor checks —** `[J]` the level fits the invariant — would the default's anomalies (non-repeatable read, phantom, write skew) break this logic? · `[J]` `SERIALIZABLE` paths retry on serialization failure.

## Concurrency control — optimistic vs. pessimistic locking (lost-update protection)

- **Good looks like —** **Optimistic** (`UPDATE ... WHERE version = :v`; 0 rows affected = a conflict to handle) fits low-contention, read-heavy paths with long think-time; **pessimistic** (`SELECT ... FOR UPDATE`) fits hot, high-contention rows (inventory, balances).
- **Auditor checks —** `[D]` an optimistic path detects and surfaces/retries the 0-rows-affected conflict rather than ignoring it · `[J]` every read-modify-write on shared state prevents lost updates — version check or row lock · `[J]` the strategy fits the contention profile · `[J]` pessimistic locks scoped tightly, with consistent ordering, to avoid deadlocks.

## N+1 queries & ORM pitfalls

- **Auditor checks —** `[D]` a regression test asserts a **bounded query count** for the hot endpoint · `[J]` no loop over rows touches a lazy relation · `[J]` the generated SQL for a critical path actually read.

## Connection pooling & resource lifecycle

- **Good looks like —** A **bounded** pool sized against the DB's ceiling, never ad-hoc per-request connections. **Serverless / high-fanout deployments front the DB with a pooler** (PgBouncer / RDS Proxy) instead of each instance holding its own pool.
- **Auditor checks —** `[D]` connections acquired via a pool, not constructed inline per call · `[D]` every connection/session closed on all paths (context manager / `finally`) · `[J]` pool sized against the DB's connection ceiling at peak concurrency · `[J]` connection recycle/health-check set, so stale connections don't surface as errors.

## Soft deletes & audit columns

- **Auditor checks —** `[D]` with soft-delete, default queries exclude soft-deleted rows everywhere — no path leaks "deleted" data · `[D]` `created_at`/`updated_at` present and auto-populated on the touched tables · `[J]` delete-vs-soft-delete chosen intentionally, with no conflict against an erasure requirement · `[J]` unique constraints and business rules treat soft-deleted rows correctly.

## Read replicas & replication lag

- **Auditor checks —** `[D]` replication lag monitored with an alert · `[J]` read-after-write flows read the primary or a lag-bounded path · `[J]` a stale or unavailable replica falls back to primary.

## Query optimization (EXPLAIN, no `SELECT *`)

- **Auditor checks —** `[D]` `SELECT *` absent from application queries (grep) · `[J]` a flagged hot query's `EXPLAIN` plan avoids a large-table seq scan and uses the right index · `[J]` deep pagination keyset-based, not high-`OFFSET` · `[J]` filter/sort/aggregate done in SQL, not fetched-then-processed in memory.

## Referential integrity

- **Auditor checks —** `[D]` relationship columns carry actual FK constraints in the schema, not integrity hoped-for in code · `[J]` each FK's on-delete/on-update action intentional — no accidental cascade, no orphans · `[J]` app-enforced integrity enforced on **all** write paths.

## Idempotent writes

- **Good looks like —** **"Exactly once" is at-least-once delivery + idempotent handling** — the only honest way to get there.
- **Auditor checks —** `[D]` a unique constraint or idempotency-key column backs the dedup (schema-checkable) · `[J]` each retriable write is safely repeatable — a retry never duplicates the effect · `[J]` externally-triggered writes (webhooks, queue consumers, payment callbacks) handle replay · `[J]` a retried multi-step write avoids partial application.

## Backup before destructive migration

- **Auditor checks —** `[D]` the runbook/PR requires a snapshot before the destructive step runs, and backups are **restore-tested**, not just taken · `[J]` the step reversible or staged (rename/keep, drop after soak) · `[J]` mass mutations batched and interruptible.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
