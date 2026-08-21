---
# ── Module contract (copied from _TEMPLATE.md) ──
module: maintainability-structure
title: Maintainability & Structure
status: draft
iso_25010: [maintainability]
load_scope:
  keywords: [refactor, architecture, module, layer, service, pattern, coupling, cohesion, naming, dead-code, complexity, types]
  globs: ["src/**", "lib/**", "**/*.ts", "**/*.js"]
---

# Maintainability & Structure — is this code shaped so the next change is cheap?

> **Loads when:** new/changed code introduces or reshapes structure — modules, layers, services, interfaces, abstractions; refactors; anything where SOLID, layering, design-pattern choice, coupling/cohesion, type-safety, naming, or code-health is in play.
> Method, tags, honesty register: `README.md` → *Reading a module*.

---

## SOLID

- **Auditor checks —** `[D]` interface width — flag interfaces whose implementers stub methods they don't use (ISP) · `[J]` no class/function mixes unrelated responsibilities — HTTP parsing + business rules + SQL in one place (SRP) · `[J]` adding a case does not mean editing a `switch` over a closed set (OCP; full treatment in *Open/Closed & config-driven*) · `[J]` no subtype throws `NotImplemented`, no-ops an inherited method, or narrows accepted inputs (LSP). *(DIP import-direction: *Dependency direction* below.)*

## Separation of concerns

- **Auditor checks —** `[D]` layer-boundary lint (import-linter / dependency-cruiser / `madge`) flags cross-concern imports where rules exist · `[J]` no business logic in a controller/handler, ORM call in a domain entity, or formatting in a repository · `[J]` each module's single concern is nameable in one phrase.

## Architectural layers (Clean / Hexagonal / Onion)

- **Auditor checks —** `[D]` no inner-ring file imports an outer-ring concern (framework, ORM, HTTP, SDK) — import-linter contracts / dependency-cruiser / ArchUnit-style · `[J]` ports defined by the **inner** ring and implemented by the **outer** ring, not the reverse · `[J]` DTOs at the boundary, so the domain model isn't serialized straight to the wire · `[J]` validation confined to the boundary, absent from domain entities and use-case code · `[J]` an ACL/translator where an external or legacy model enters.

## Design-pattern catalog (use the right one — or justify a novel one)

- **Auditor checks —** `[J]` the pattern fits the problem, not pattern-for-pattern's-sake (a Factory making one type, a Strategy with one strategy) · `[J]` data access behind a **Repository**, not ORM/SQL scattered through services · `[J]` an explicit **Unit-of-Work / transaction** boundary where multiple writes must commit together · `[J]` **Saga + Outbox** for cross-service writes, never an unsafe dual-write · `[J]` **Circuit-Breaker / Bulkhead / Timeout / Retry** on unreliable I/O where apt (cross-ref `reliability-resilience`) · `[J]` a novel pattern carries its recorded justification.

## Composition over inheritance

- **Auditor checks —** `[J]` no hierarchy deeper than ~2 levels, or used only to share helper code · `[J]` an `extends` that could be a constructor-injected collaborator · `[J]` no parallel-inheritance-hierarchies smell.

## Dependency direction (DIP) & make invalid states unrepresentable

- **Auditor checks —** `[D]` import-boundary lint (import-linter / dependency-cruiser / ESLint `no-restricted-imports`) flags violations of "imports point toward abstractions" · `[D]` exhaustiveness: a `switch` over a union has a `never` default that fails the type-checker on a missing case · `[J]` without tooling, the import graph traced by hand for high-level modules reaching concrete low-level details · `[J]` impossible combinations unrepresentable — `status: string` plus nullable fields that "shouldn't" coexist becomes a discriminated union · `[J]` constructors/parsers validate at the boundary so downstream code can trust the type (parse, don't validate).

## Code health & housekeeping (smells, complexity, duplication, naming, comments)

- **Auditor checks —** `[D]` dead/unused code — `ts-prune`/`knip`, ESLint `no-unused-vars`, `vulture`, compiler unused flags report zero new · `[D]` cyclomatic/cognitive complexity under threshold (ESLint `complexity` / SonarQube / `radon` / `lizard`) · `[D]` duplication under threshold (`jscpd` / SonarQube CPD), no commented-out code blocks · `[J]` names read as intent at the call site — no abbreviations, no misleading names · `[J]` comments are load-bearing *why*-comments, not restatements or lies.

## DRY by collapse — the shared source must be a FIXED POINT on the live path

- **Auditor checks —** `[D]` count the applications of the collapse target along each live path: more than one anywhere demands an **`f(f(x)) === f(x)`** assertion over a corpus including the degenerate inputs (empty, all-separator, already-normalized, falsy-but-present) · `[D]` diff the **composed observable the caller sees** — the joined path, the rendered string, the persisted key — before and after the collapse across a *generated* corpus, not a hand-picked shape list, and report the divergence count: any changed composed output is a behavior change needing its own approval · `[J]` the helper does not **default** before it **normalizes**, or otherwise emit a value its own second application would rewrite · `[J]` where the observable is assembled from several segments, **every** segment is normalized at the same boundary, not only the one the diff touched · `[D]` the collapse target has at least one call site, and a comment claiming "the ONE source" names derivers that really call it · `[J]` **a total claim in a comment is earned by a pin, not an argument** — for every "cannot diverge / always / never", name the assertion that turns red when it stops holding, or state what was actually measured.
- **Incident —** 0041 S10a (2026-08-17): the spec asked for *"one source of the artifact-directory shape"* and got it — five copies routed through one helper nobody asked to be **idempotent**, on a live path that applies it **twice**. It defaulted before it trimmed, so an all-separator directory trimmed to `""` and the second application substituted the default: the QA driver **saved** screenshots under one directory while the report **cited** another. Measured, the pre-change code diverged on **0** of 23 directory shapes and the collapsed code on **8 — every one created by the collapse**; over 200,000 random pairs the divergence rate was **95.4%**. The diff conformed to the spec at every line; only executing the *composed* path over a generated corpus found it. *(The oracle a collapse needs: `testing.md` → *Characterization tests & golden master*; the effectful cousin: `reliability-resilience.md` → *Idempotency & safe retry*.)*

## Type safety

- **Auditor checks —** `[D]` type-checker passes with strict config on — TS `strict`, `noImplicitAny`, `noUncheckedIndexedAccess`; mypy `--strict` — no new errors and no new suppressions · `[D]` count of `any`/`@ts-ignore`/`type: ignore` introduced (`no-explicit-any`, `no-ts-ignore`) · `[J]` untrusted input *parsed* into a type at the edge (zod/pydantic), never cast with `as`.

## Open/Closed & config-driven

- **Auditor checks —** `[D]` magic-literal lint where configured (`no-magic-numbers`) · `[J]` adding a variant means registering an entry, not editing a central conditional · `[J]` environment/behavioral knobs configurable, not hardcoded per-env. *(Don't pre-build the indirection before variation exists — YAGNI.)*

## Clear contracts & interfaces

- **Auditor checks —** `[D]` public-surface lint (`no internal export` / package `exports` map / API-extractor) where configured · `[J]` the public API is minimal and leaks no internals (helpers, mutable state, concrete types where an interface belongs) · `[J]` error/edge outcomes are part of the contract — typed or documented, not surprises. *(Breaking changes are versioned — cross-ref `api-and-contracts`.)*

## Low coupling / high cohesion

- **Auditor checks —** `[D]` no cyclic dependencies (`madge --circular` / dependency-cruiser / import-linter) · `[D]` fan-in/fan-out and instability metrics where tooled · `[J]` no module reaches across a boundary into another's internals, nor owns unrelated responsibilities · `[J]` wiring via injected interfaces, not `new`-ing concretes inside business code.

## Knowledge-store shape (bound what a reader READS, not what the system KNOWS)

- **Auditor checks —** `[D]` per-unit size caps exist and are gate-checked where a budget gate is wired · `[J]` the store is classified **log** (entries supersede — condense periodically; a recorded cap-bump is a fine escape) or **rule-book** (entries persist by design — a fixed total cap collides with the store's floor, so shard it), and its growth mechanism matches · `[J]` accretion grows **horizontally** — a lean index routing to small per-topic units, never one monolith · `[J]` external references point at the index, never at unit internals, so a future split stays cheap · `[J]` one consultation does not require ingesting the whole store.
- **Incident —** This harness's own decisions ledger: a 54 KB single-file **rule-book** sitting at its condensed floor became an index + ten per-topic shards under per-shard caps (2026-07, plan 0040) — cap-and-condense had run out of room because the store was never a log.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
