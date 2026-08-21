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

- **Auditor checks —** `[J]` Model normalized, or duplication accidental (same fact in two tables, no sync path). `[D]` Columns that should be mandatory carry `NOT NULL`. `[J]` Status/type columns constrained (enum/FK/check), not free strings. `[J]` Each denormalization has a stated read-path justification **and** a consistency mechanism, recorded in `docs/claugentic-DECISIONS.md`.

## Indexing strategy

- **Auditor checks —** `[J]` Each index maps to a known predicate/join/sort in the codebase, not cargo-culted. `[D]` Every FK column has a covering index (schema introspection). `[J]` Composite column order justified by query shape (leftmost prefix). `[J]` For a flagged hot read, a covering index would avoid the table lookup. `[D]` No duplicate indexes (same leading columns).

## Migrations — versioned, reversible, zero-downtime

- **Auditor checks —** `[D]` A checked-in migration with a version/sequence, not ad-hoc SQL. `[D]` A down-migration, or an explicit irreversibility note. `[J]` A destructive/blocking change on a live table (drop/rename column, add `NOT NULL`, type change) is split expand→migrate→contract across deploys, not one breaking step. `[J]` Backfills batched to avoid long table locks. `[D]` CI runs migrations forward **and** back on a scratch DB.

## Transactions & isolation levels

- **Good looks like —** The isolation level is **chosen, not defaulted-by-accident** — know the engine's default (PostgreSQL/Oracle = Read Committed) and raise it for invariants that read-then-write across rows. Transactions stay **short**: no network calls, no user think-time inside an open one.
- **Auditor checks —** `[J]` Related writes wrapped in one transaction, so a mid-failure can't leave half-applied state. `[J]` Isolation level appropriate for the invariant — would the default's anomalies (non-repeatable read, phantom, write skew) break this logic? `[J]` Transactions short: no I/O, external calls, or user think-time under lock. `[J]` `SERIALIZABLE` serialization-failure retries in place where used.

## Concurrency control — optimistic vs. pessimistic locking (lost-update protection)

- **Good looks like —** **Optimistic** (`UPDATE ... WHERE version = :v`; 0 rows affected = a conflict to handle/retry) fits low-contention, read-heavy paths with long think-time; **pessimistic** (`SELECT ... FOR UPDATE`) fits hot, high-contention rows (inventory, balances).
- **Auditor checks —** `[J]` Every read-modify-write on shared state prevents lost updates (version check or row lock) — no silently clobbered concurrent writer. `[J]` Strategy fits the contention profile (optimistic vs. pessimistic). `[D]` If optimistic, the conflict path is handled: 0-rows-affected detected and surfaced/retried, not ignored. `[J]` Pessimistic locks scoped tightly with consistent ordering, to avoid deadlocks.

## N+1 queries & ORM pitfalls

- **Auditor checks —** `[J]` No loop over rows accesses a lazy relation (N+1) — spot via query-count assertions or echo/SQL logs. `[D]` A regression test asserts a bounded query count for the hot endpoint. `[J]` Big reads streamed/chunked, not every row loaded as objects. `[J]` The generated SQL for a critical path was actually read.

## Connection pooling & resource lifecycle

- **Good looks like —** A **bounded** pool sized against the DB's ceiling, never ad-hoc per-request connections. **Serverless / high-fanout deployments front the DB with a pooler** (PgBouncer / RDS Proxy) instead of each instance holding its own pool.
- **Auditor checks —** `[D]` Connections acquired via a pool, not constructed inline per call. `[D]` Every connection/session closed on all paths (context manager / `finally`). `[J]` Pool sized against the DB's connection ceiling, unexhausted at peak concurrency. `[J]` Connection recycle/health-check set, so stale connections don't surface as errors.

## Soft deletes & audit columns

- **Auditor checks —** `[J]` Delete-vs-soft-delete chosen intentionally for this entity, with no conflict against an erasure requirement. `[D]` If soft-delete: default queries exclude soft-deleted rows everywhere — no path leaks "deleted" data. `[J]` Unique constraints/business rules treat soft-deleted rows correctly. `[D]` `created_at`/`updated_at` present and auto-populated on the touched tables.

## Read replicas & replication lag

- **Auditor checks —** `[J]` Read-after-write flows (save then immediately view) read the primary or a lag-bounded path, never stale data. `[J]` The write→primary / read→replica split explicit and correct — no writes to a read replica. `[D]` Replication lag monitored with an alert. `[J]` A stale or unavailable replica still behaves correctly (fallback to primary).

## Query optimization (EXPLAIN, no `SELECT *`)

- **Auditor checks —** `[J]` A flagged hot query's `EXPLAIN` plan avoids a large-table seq scan and uses the right index. `[D]` `SELECT *` absent from application queries (grep-able). `[J]` Deep pagination keyset-based, not high-`OFFSET`. `[J]` Filter/sort/aggregate done in SQL, not fetched-then-processed in memory.

## Referential integrity

- **Auditor checks —** `[D]` Relationship columns carry actual FK constraints in the schema (introspectable), not integrity hoped-for in code. `[J]` Each FK's on-delete/on-update action intentional — no accidental cascade wiping data, no orphans left. `[J]` Integrity that must be app-enforced is enforced on **all** write paths, and justified.

## Idempotent writes

- **Good looks like —** **“Exactly once” is at-least-once delivery + idempotent handling** — the only honest way to get there.
- **Auditor checks —** `[J]` Each retriable write is safely repeatable (unique key / upsert / dedup) — a retry never duplicates the effect. `[D]` A unique constraint or idempotency-key column backs the dedup (schema-checkable). `[J]` Externally-triggered writes (webhooks, queue consumers, payment callbacks) handle replay/duplicate delivery. `[J]` A retried multi-step write avoids partial application.

## Backup before destructive migration

- **Auditor checks —** `[D]` The destructive migration's runbook/PR requires a snapshot/backup before it runs. `[J]` The destructive step is reversible or staged (rename/keep, drop after soak), not an immediate irreversible drop. `[D]` Evidence backups are restore-tested, not just taken. `[J]` Mass data mutations batched and interruptible.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
