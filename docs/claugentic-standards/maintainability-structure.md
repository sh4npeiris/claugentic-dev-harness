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
> **ISO/IEC 25010:** Maintainability (modularity, reusability, analysability, modifiability, testability) · **Status:** draft
> Method, tags, honesty register: `README.md` → *Reading a module*.

---

## SOLID

- **Auditor checks —** `[J]` Does any class/function mix unrelated responsibilities (e.g. HTTP parsing + business rules + SQL in one place)? (SRP) `[J]` Does adding a case require editing a `switch`/`if-else` over a closed set instead of adding a type (OCP smell — full treatment in *Open/Closed & config-driven* dimension)? `[J]` Does a subtype throw `NotImplemented`, no-op an inherited method, or narrow accepted inputs (LSP break)? `[D]` Interface width — flag interfaces whose implementers stub out methods they don't use (ISP). *(DIP import-direction is audited in the *Dependency direction* dimension — see there.)*

## Separation of concerns

- **Auditor checks —** `[J]` Is there business logic inside a controller/handler, an ORM call inside a domain entity, or formatting inside a repository? `[J]` Can you name the single concern each module owns in one phrase? `[D]` Layer-boundary lint (import-linter / dependency-cruiser / `madge`) flags cross-concern imports where rules exist.

## Architectural layers (Clean / Hexagonal / Onion)

- **Auditor checks —** `[D]` Does any inner-ring file import an outer-ring concern (framework, ORM, HTTP, SDK)? — provable with an import-boundary linter (import-linter contracts / dependency-cruiser / ArchUnit-style). `[J]` Are ports defined by the **inner** ring and implemented by the **outer** ring (dependency inversion at the boundary), not the reverse? `[J]` Do DTOs exist at the boundary so the domain model isn't serialized straight to the wire? `[J]` Is validation logic confined to the boundary and absent from domain entities / use-case code? `[J]` Is there an ACL/translator where an external/legacy model enters?

## Design-pattern catalog (use the right one — or justify a novel one)

- **Auditor checks —** `[J]` Does the chosen pattern actually fit the problem, or is it pattern-for-pattern's-sake (e.g. a Factory that only ever makes one type, a Strategy with one strategy)? `[J]` Is data access behind a **Repository** (collection-like interface) rather than ORM/SQL scattered through services? `[J]` Where multiple writes must commit together, is **Unit-of-Work / transaction** boundary explicit? `[J]` For cross-service writes, is **Saga + Outbox** used instead of an unsafe dual-write? `[J]` For unreliable I/O, are **Circuit-Breaker / Bulkhead / Timeout / Retry** present where apt (cross-ref `reliability-resilience`)? `[J]` If a pattern is novel/unconventional, is the justification recorded?

## Composition over inheritance

- **Auditor checks —** `[J]` Is there an inheritance hierarchy deeper than ~2 levels, or one used only to share helper code? `[J]` Could a `extends` relationship be a constructor-injected collaborator instead? `[J]` Any "parallel inheritance hierarchies" smell (adding a subclass here forces a subclass there)?

## Dependency direction (DIP) & make invalid states unrepresentable

- **Auditor checks —** `[D]` Import direction — where an import-boundary linter is configured (import-linter / dependency-cruiser / ESLint `no-restricted-imports`), does it flag violations of "imports point toward abstractions"? `[J]` Without tooling, manually trace the import graph for DIP violations — do high-level modules reach for concrete low-level details instead of an abstraction? `[J]` Are impossible combinations representable (e.g. `status: string` + nullable fields that "shouldn't" coexist) where a discriminated union would forbid them? `[D]` Exhaustiveness — `switch` over a union has a `never`/exhaustive default that fails the type-checker on a missing case. `[J]` Do constructors/parsers validate at the boundary so downstream code can trust the type (parse, don't validate)?

## Code health & housekeeping (smells, complexity, duplication, naming, comments)

- **Auditor checks —** `[D]` Dead/unused code — linter (`ts-prune`/`knip`, ESLint `no-unused-vars`, `vulture`, compiler unused flags) reports zero new. `[D]` Cyclomatic/cognitive complexity over threshold — ESLint `complexity` / SonarQube / `radon` / `lizard`. `[D]` Duplication over threshold — `jscpd` / SonarQube copy-paste detector. `[D]` Commented-out code blocks present? (lint/grep). `[J]` Do names read as intent at the call site; any abbreviations or misleading names? `[J]` Are comments load-bearing *why*-comments, or do they restate the code / lie about it?

## DRY by collapse — the shared source must be a FIXED POINT on the live path

- **Good looks like —** Before N duplicated implementations become one shared helper, the helper's **algebraic properties on the live path** are stated and pinned — not just its behavior at one call. The property that bites first is **idempotence**: if any live path can apply the helper **more than once** (normalized at a boundary, then again inside a consumer; on write and again on read), `f(f(x)) === f(x)` is part of its contract and carries its own assertion over a corpus including the degenerate inputs (empty, all-separator, already-normalized, falsy-but-present). The equivalence check for the collapse runs over the **composed value the caller observes** — the joined path, the rendered string, the persisted key — never over the helper's return at each site in isolation. Where the observable is built from several normalized segments, **every** segment is normalized at the **same** boundary, not only the one the diff touched.
- **Auditor checks —** `[D]` Count the applications of the collapse target along each live path: more than one anywhere, and there must be an `f(f(x)) === f(x)` assertion over a corpus including the degenerate inputs. `[D]` Diff the **composed observable** before and after the collapse across a *generated* input corpus (not a hand-picked shape list) and report the divergence count — a collapse that changes any composed output is a behavior change needing its own approval. `[J]` Does the helper **default** before it **normalizes** (or otherwise emit a value its own second application would rewrite)? `[J]` For an observable assembled from several segments, is each one normalized, or only the one under the diff? `[D]` Does the collapse target have at least one call site at all — and does a comment claiming it is "the ONE source" name derivers that really call it? `[J]` **A total claim in a comment is earned by a pin, not by an argument:** for every "cannot diverge / always / never / the ONE source" a diff authors or re-asserts, name the assertion that turns red when it stops holding; if there is none, the honest comment states what was measured. Re-asserting a totality the same comment records as *previously false* is the loudest form of this.
- **Incident —** 0041 S10a (2026-08-17). The spec asked for *“one source of the artifact-directory shape”* and the diff delivered exactly that — five inconsistent copies routed through one helper. Nobody asked whether that helper was **idempotent**, and the live runtime-QA path applies it **twice**. It defaulted before it trimmed, so an all-separator directory trimmed to `""` and the second application substituted the default: the QA driver **saved** screenshots under one directory while the run report **cited** another. Measured, the pre-change code diverged on **0** of 23 directory shapes and the collapsed code on **8 — every one created by the collapse**; over 200,000 random pairs the divergence rate was **95.4%**. The diff conformed to the spec at every line, so reviewing it against the spec was no defense; only executing the *composed* path over a generated corpus found it. The same round found the twin defect one axis over (one segment normalized, the label on the other side left raw), and the helper's own comment asserted the two paths “cannot diverge” in the paragraph that recorded that claim as previously false. Closed by trimming before defaulting, normalizing both segments at one boundary, and pinning `f(f(x)) === f(x)`. *(The composed-observable corpus IS the equivalence oracle a collapse needs — `testing.md` → *Characterization tests & golden master*. The effectful cousin, a retried write, is `reliability-resilience.md` → *Idempotency & safe retry*.)*

## Type safety

- **Good looks like —** Strict and **on**: TS `strict`, `noImplicitAny`, `noUncheckedIndexedAccess`; mypy `--strict`. External input is **parsed** into a typed shape at the boundary, never cast.
- **Auditor checks —** `[D]` Type-checker passes with strict config (`tsc --noEmit`, `mypy --strict`) — no new errors and no new suppressions. `[D]` Count of `any`/`@ts-ignore`/`type: ignore` introduced (lint rule `no-explicit-any`, `no-ts-ignore`). `[J]` Is untrusted input *parsed* into a type at the edge (e.g. zod/pydantic) rather than asserted with `as`?

## Open/Closed & config-driven

- **Auditor checks —** `[J]` Does adding a variant require editing a central conditional, or registering a new entry? `[J]` Are environment/behavioral knobs configurable (not hardcoded per-env)? `[D]` Magic-literal lint where configured (`no-magic-numbers`). *(Don't pre-build the indirection before variation exists — YAGNI.)*

## Clear contracts & interfaces

- **Auditor checks —** `[J]` Is the public API minimal, or does it leak internals (helpers, mutable state, concrete types where an interface belongs)? `[J]` Are error/edge outcomes part of the contract (typed errors / documented), not surprises? `[D]` Public-surface lint (`no internal export` / package `exports` map / API-extractor) where configured. *(Breaking changes to a published contract are versioned — cross-ref `api-and-contracts`.)*

## Low coupling / high cohesion

- **Auditor checks —** `[D]` **Cyclic dependencies** — `madge --circular` / dependency-cruiser / import-linter reports none. `[D]` Fan-in/fan-out & instability metrics where tooled (dependency-cruiser, SonarQube). `[J]` Does a module reach across a boundary into another's internals (high coupling) or own unrelated responsibilities (low cohesion)? `[J]` Is wiring done via injected interfaces rather than `new`-ing concretes inside business code?

## Knowledge-store shape (bound what a reader READS, not what the system KNOWS)

- **Good looks like —** Long-lived knowledge stores (ledgers, decision records, catalogs, registries) are shaped for **bounded per-consultation reads**: a lean index (locate, don't ingest) routes to small per-topic units, each under its own size cap; accretion grows **horizontally** (new units), never one monolith. Distinguish a **log** (entries supersede — condense periodically; a recorded cap-bump is a fine escape) from a **rule-book** (entries persist by design — a fixed total cap eventually collides with the store's floor; shard it instead). External references point at the index/entry point, never at unit internals, so a future unit split stays cheap.
- **Auditor checks —** `[D]` Per-unit size caps exist and are gate-checked where a budget gate is wired. `[J]` Is the store a log or a rule-book, and does its growth mechanism match (condense-and-cap vs index+shards)? `[J]` Do external references bypass the index into unit internals? `[J]` Does one consultation require ingesting the whole store?
- **Incident —** This harness's own decisions ledger: a 54 KB single-file **rule-book** sitting at its condensed floor became an index + ten per-topic shards under per-shard caps (2026-07, plan 0040) — the cap-and-condense mechanism had run out of room because the store was never a log.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
