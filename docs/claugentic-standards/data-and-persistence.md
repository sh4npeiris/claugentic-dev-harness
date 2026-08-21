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

- **Auditor checks —** `[J]` Is the model normalized, or is duplication accidental (same fact stored in two tables with no sync path)? `[D]` Do nullable columns that should be mandatory carry `NOT NULL`? `[J]` Are status/type columns constrained (enum/FK/check) rather than free strings? `[J]` For each denormalization: is there a stated read-path justification **and** a consistency mechanism, recorded in `docs/claugentic-DECISIONS.md`?

## Indexing strategy

- **Auditor checks —** `[J]` Does each index map to a known predicate/join/sort in the codebase, or is it cargo-culted? `[D]` Does every FK column have a covering index (catch-able by schema introspection)? `[J]` For composite indexes, is column order justified by query shape (leftmost prefix)? `[J]` For a flagged hot read query, would a covering index avoid the table lookup? `[D]` Any duplicate indexes (same leading columns)?

## Migrations — versioned, reversible, zero-downtime

- **Auditor checks —** `[D]` Is the change a checked-in migration with a version/sequence (not ad-hoc SQL)? `[D]` Is there a down-migration, or an explicit irreversibility note? `[J]` For a destructive/blocking change on a live table (drop/rename column, add `NOT NULL`, type change), is it split into expand→migrate→contract across deploys rather than one breaking step? `[J]` Are backfills batched to avoid long table locks? `[D]` Does CI run migrations forward **and** back on a scratch DB?

## Transactions & isolation levels

- **Good looks like —** The isolation level is **chosen, not defaulted-by-accident** — know the engine's default (PostgreSQL/Oracle = Read Committed) and raise it for invariants that read-then-write across rows. Transactions stay **short**: no network calls, no user think-time inside an open one.
- **Auditor checks —** `[J]` Are related writes wrapped in a single transaction so a mid-failure can't leave half-applied state? `[J]` Is the isolation level appropriate for the invariant — would the default's anomalies (non-repeatable read, phantom, write skew) break this logic? `[J]` Are transactions kept short (no I/O / external calls / waiting on a user while holding locks)? `[J]` Are `SERIALIZABLE` serialization-failure retries in place where used?

## Concurrency control — optimistic vs. pessimistic locking (lost-update protection)

- **Good looks like —** **Optimistic** (`UPDATE ... WHERE version = :v`; 0 rows affected = a conflict to handle/retry) fits low-contention, read-heavy paths with long think-time; **pessimistic** (`SELECT ... FOR UPDATE`) fits hot, high-contention rows (inventory, balances).
- **Auditor checks —** `[J]` For each read-modify-write on shared state, is lost-update prevented (version check or row lock), or can a concurrent writer be silently clobbered? `[J]` Does the strategy fit the contention profile (optimistic vs. pessimistic)? `[D]` If optimistic, is the conflict path handled (0-rows-affected detected and surfaced/retried, not ignored)? `[J]` Are pessimistic locks scoped tightly to avoid deadlocks (consistent lock ordering)?

## N+1 queries & ORM pitfalls

- **Auditor checks —** `[J]` Does any loop over rows access a lazy relation, triggering N+1? (Spot via query-count assertions in tests or echo/SQL logs.) `[D]` Can a regression test assert a bounded query count for the hot endpoint? `[J]` Are big reads streamed/chunked instead of loading every row into memory as objects? `[J]` Was the generated SQL for a critical path actually looked at?

## Connection pooling & resource lifecycle

- **Good looks like —** A **bounded** pool sized against the DB's ceiling, never ad-hoc per-request connections. **Serverless / high-fanout deployments front the DB with a pooler** (PgBouncer / RDS Proxy) instead of each instance holding its own pool.
- **Auditor checks —** `[D]` Are connections acquired via a pool, not constructed inline per call? `[D]` Is every connection/session closed on all paths (context manager / `finally`)? `[J]` Is the pool sized against the DB's connection ceiling (won't exhaust it under peak concurrency)? `[J]` Is connection recycle/health-check set so stale connections don't surface as errors?

## Soft deletes & audit columns

- **Auditor checks —** `[J]` Is delete-vs-soft-delete chosen intentionally for this entity (and does soft-delete conflict with an erasure requirement)? `[D]` If soft-delete: do default queries exclude soft-deleted rows everywhere (no path leaks "deleted" data)? `[J]` Do unique constraints/business rules correctly treat soft-deleted rows? `[D]` Are `created_at`/`updated_at` present and auto-populated on the touched tables?

## Read replicas & replication lag

- **Auditor checks —** `[J]` Do read-after-write flows (user saves then immediately views) read from the primary or a lag-bounded path, avoiding stale data? `[J]` Is the write→primary / read→replica split explicit and correct (no writes sent to a read replica)? `[D]` Is replication lag monitored with an alert? `[J]` Does the system behave correctly if a replica is stale or unavailable (fallback to primary)?

## Query optimization (EXPLAIN, no `SELECT *`)

- **Auditor checks —** `[J]` For a flagged hot query, does its `EXPLAIN` plan avoid a large-table seq scan and use the right index? `[D]` Is `SELECT *` absent from application queries (grep-able)? `[J]` Is deep pagination keyset-based rather than high-`OFFSET`? `[J]` Is work (filter/sort/aggregate) done in SQL rather than fetched-then-processed in memory?

## Referential integrity

- **Auditor checks —** `[D]` Do relationship columns carry actual FK constraints in the schema (introspectable), or is integrity only hoped-for in code? `[J]` Is each FK's on-delete/on-update action intentional (no accidental cascade wiping data, no orphan-leaving)? `[J]` If integrity is app-enforced by necessity, is it enforced on **all** write paths and justified?

## Idempotent writes

- **Good looks like —** **“Exactly once” is at-least-once delivery + idempotent handling** — the only honest way to get there.
- **Auditor checks —** `[J]` Can each retriable write be safely repeated (unique key / upsert / dedup), or does a retry duplicate the effect? `[D]` Is there a unique constraint or idempotency-key column backing the dedup (schema-checkable)? `[J]` For externally-triggered writes (webhooks, queue consumers, payment callbacks), is replay/duplicate delivery handled? `[J]` Does a retried multi-step write avoid partial application?

## Backup before destructive migration

- **Auditor checks —** `[D]` Does the destructive migration's runbook/PR require a snapshot/backup before it runs? `[J]` Is the destructive step reversible or staged (rename/keep then drop after soak) rather than an immediate irreversible drop? `[D]` Is there evidence backups are restore-tested (not just taken)? `[J]` Are mass data mutations batched and interruptible?

> Authoring rules `_TEMPLATE.md` · governance `README.md`
