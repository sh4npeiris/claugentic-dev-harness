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

- **Auditor checks —** `[J]` no new endpoint exposes internal domain fields with no external consumer · `[D]` path segments, query-param names and JSON keys follow the project's casing convention, where a lint/schema tool is configured · `[J]` otherwise that convention is checked by eye against the surface the endpoint joins · `[J]` HTTP verbs semantic: GET safe+idempotent, POST create, PUT/PATCH update, DELETE remove.

## Idempotency of mutating endpoints

- **Auditor checks —** `[D]` mutating endpoints in the diff enumerated by HTTP verb · `[J]` each is naturally idempotent or accepts an `Idempotency-Key` and deduplicates on it · `[J]` the dedup store has a TTL.

## Versioning & backward compatibility

- **Auditor checks —** `[J]` removed or renamed request/response fields identified in the diff · `[J]` each change is backward-compatible (new and optional) or lands under a new version path · `[J]` the version scheme matches existing endpoints · `[J]` deprecated fields carry a documented sunset date.

## Pagination & bounded responses

- **Auditor checks —** `[D]` list endpoints in the diff enumerated by route glob · `[J]` each applies `.limit()` / slice / cursor before returning · `[J]` the schema documents the pagination contract (fields, max page size) · `[J]` a caller-supplied `limit` has a server-side cap.

## Rate limiting & backpressure

- **Auditor checks —** `[J]` new public-facing endpoints carry rate-limiting middleware · `[J]` `429` responses include `Retry-After` · `[J]` the limit is configured externally, not hardcoded.

## Clear & stable error shapes

- **Auditor checks —** `[J]` new error paths match the project's error envelope · `[J]` 5xx bodies leak no stack traces or internal paths · `[J]` status codes semantically appropriate · `[J]` error codes documented.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
