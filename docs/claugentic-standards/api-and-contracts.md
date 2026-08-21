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

- **Auditor checks —** Scan new endpoints for fields that belong to internal domain models but have no external consumer `[J]`; check that path segments, query-param names, and JSON keys follow the project's established casing convention `[D via lint/schema tool if configured, otherwise J]`; verify HTTP verbs are used semantically (GET = safe+idempotent, POST = create, PUT/PATCH = update, DELETE = remove) `[J]`.

## Idempotency of mutating endpoints

- **Auditor checks —** Identify mutating endpoints in the diff `[D via HTTP verb]`; verify each either documents idempotency naturally or accepts an `Idempotency-Key` / equivalent header and deduplicates on it `[J]`; check the deduplication store has an appropriate TTL `[J]`.

## Versioning & backward compatibility

- **Auditor checks —** Identify any removed or renamed request/response fields in the diff `[J]`; verify the change is either backward-compatible (field is new and optional) or introduced under a new version path `[J]`; check that the version scheme is consistent with existing endpoints `[J]`; confirm deprecated fields carry a documented sunset date if applicable `[J]`.

## Pagination & bounded responses

- **Auditor checks —** Identify list endpoints in the diff `[D via route glob]`; verify each applies `.limit()` / slice / cursor before returning `[J]`; check that the API schema documents the pagination contract (fields, max page size) `[J]`; flag endpoints where `limit` is accepted from the caller but has no server-side cap `[J]`.

## Rate limiting & backpressure

- **Auditor checks —** Identify new public-facing endpoints in the diff `[J]`; verify rate-limiting middleware or decorator is applied `[J]`; check that `429` responses include a `Retry-After` header `[J]`; confirm the limit is configured externally (not hardcoded) `[J]`.

## Clear & stable error shapes

- **Auditor checks —** Scan new error-return paths in the diff for consistency with the project's error envelope schema `[J]`; check that 5xx responses do not leak stack traces or internal paths in the response body `[J]`; verify status codes are semantically appropriate for the error condition `[J]`; confirm error codes are documented `[J]`.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
