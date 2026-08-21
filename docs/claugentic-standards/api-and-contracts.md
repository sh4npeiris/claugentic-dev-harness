---
module: api-and-contracts
title: API & Interface Design
status: draft
iso_25010: [compatibility]
load_scope:
  keywords: [api, endpoint, route, contract, version, pagination, rate-limit, webhook]
  globs: ["**/api/**", "**/routes/**", "**/controllers/**"]
---

# API & Interface Design — consistent, minimal, stable public surfaces

> **Loads when:** the change adds or modifies API endpoints, routes, controllers, public function signatures, webhooks, or any cross-boundary contract.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **Consistency is a whole-surface property** — judge a new endpoint against the surface it joins, not against the diff alone.

---

## Minimal & consistent contracts

- **Auditor checks —** `[D]` path segments, query-param names and JSON keys follow the project's casing convention, where a lint/schema tool is configured · `[J]` otherwise checked by eye against the surface the endpoint joins — consistency is a **whole-surface** property · `[J]` no new endpoint exposes internal domain fields with no external consumer.

## Idempotency of mutating endpoints

- **Auditor checks —** `[D]` mutating endpoints enumerated by HTTP verb · `[J]` each is naturally idempotent or accepts an `Idempotency-Key` and deduplicates on it, with a TTL on the dedup store.

## Versioning & backward compatibility

- **Auditor checks —** `[J]` removed or renamed request/response fields are backward-compatible (new and optional) or land under a new version path · `[J]` deprecated fields carry a documented sunset date.

## Pagination & bounded responses

- **Auditor checks —** `[D]` list endpoints enumerated by route glob, each applying `.limit()` / slice / cursor before returning · `[J]` a caller-supplied `limit` has a server-side cap, and the schema documents the contract (fields, max page size).

## Rate limiting & backpressure

- **Auditor checks —** `[J]` `429` responses include `Retry-After` · `[J]` the limit is configured externally, not hardcoded.

## Clear & stable error shapes

- **Auditor checks —** `[J]` new error paths match the project's error envelope, with documented codes · `[J]` 5xx bodies leak no stack traces or internal paths.
