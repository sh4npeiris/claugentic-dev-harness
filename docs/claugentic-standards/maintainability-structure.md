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

- **Auditor checks —** `[J]` No class/function mixes unrelated responsibilities (HTTP parsing + business rules + SQL in one place) — SRP. `[J]` Adding a case doesn't require editing a `switch`/`if-else` over a closed set instead of adding a type — OCP smell, full treatment in *Open/Closed & config-driven*. `[J]` No subtype throws `NotImplemented`, no-ops an inherited method, or narrows accepted inputs — LSP. `[D]` Interface width — flag interfaces whose implementers stub out methods they don't use (ISP). *(DIP import-direction is audited in *Dependency direction*.)*

## Separation of concerns

- **Auditor checks —** `[J]` No business logic inside a controller/handler, ORM call inside a domain entity, or formatting inside a repository. `[J]` The single concern each module owns is nameable in one phrase. `[D]` Layer-boundary lint (import-linter / dependency-cruiser / `madge`) flags cross-concern imports where rules exist.

## Architectural layers (Clean / Hexagonal / Onion)

- **Auditor checks —** `[D]` No inner-ring file imports an outer-ring concern (framework, ORM, HTTP, SDK) — provable with an import-boundary linter (import-linter contracts / dependency-cruiser / ArchUnit-style). `[J]` Ports defined by the **inner** ring, implemented by the **outer** ring — dependency inversion at the boundary, not the reverse. `[J]` DTOs exist at the boundary, so the domain model isn't serialized straight to the wire. `[J]` Validation confined to the boundary, absent from domain entities / use-case code. `[J]` An ACL/translator exists where an external/legacy model enters.

## Design-pattern catalog (use the right one — or justify a novel one)

- **Auditor checks —** `[J]` The chosen pattern fits the problem, not pattern-for-pattern's-sake (a Factory that makes one type, a Strategy with one strategy). `[J]` Data access sits behind a **Repository** (collection-like interface), not ORM/SQL scattered through services. `[J]` Where multiple writes must commit together, the **Unit-of-Work / transaction** boundary is explicit. `[J]` Cross-service writes use **Saga + Outbox**, never an unsafe dual-write. `[J]` Unreliable I/O carries **Circuit-Breaker / Bulkhead / Timeout / Retry** where apt (cross-ref `reliability-resilience`). `[J]` A novel/unconventional pattern has its justification recorded.

## Composition over inheritance

- **Auditor checks —** `[J]` No inheritance hierarchy deeper than ~2 levels, or used only to share helper code. `[J]` An `extends` relationship that could be a constructor-injected collaborator instead. `[J]` No parallel-inheritance-hierarchies smell (adding a subclass here forces a subclass there).

## Dependency direction (DIP) & make invalid states unrepresentable

- **Auditor checks —** `[D]` Import direction — where an import-boundary linter is configured (import-linter / dependency-cruiser / ESLint `no-restricted-imports`), it flags violations of "imports point toward abstractions". `[J]` Without tooling, trace the import graph by hand: high-level modules reaching for concrete low-level details instead of an abstraction. `[J]` Impossible combinations are unrepresentable (`status: string` + nullable fields that "shouldn't" coexist → a discriminated union forbids them). `[D]` Exhaustiveness — a `switch` over a union has a `never`/exhaustive default that fails the type-checker on a missing case. `[J]` Constructors/parsers validate at the boundary so downstream code can trust the type (parse, don't validate).

## Code health & housekeeping (smells, complexity, duplication, naming, comments)

- **Auditor checks —** `[D]` Dead/unused code — linter (`ts-prune`/`knip`, ESLint `no-unused-vars`, `vulture`, compiler unused flags) reports zero new. `[D]` Cyclomatic/cognitive complexity over threshold — ESLint `complexity` / SonarQube / `radon` / `lizard`. `[D]` Duplication over threshold — `jscpd` / SonarQube copy-paste detector. `[D]` Commented-out code blocks (lint/grep). `[J]` Names read as intent at the call site; no abbreviations or misleading names. `[J]` Comments are load-bearing *why*-comments, not restatements of the code or lies about it.

## DRY by collapse — the shared source must be a FIXED POINT on the live path

- **Good looks like —** Before N duplicated implementations become one shared helper, the helper's **algebraic properties on the live path** are stated and pinned — not just its behavior at one call. The property that bites first is **idempotence**: if any live path can apply the helper **more than once** (normalized at a boundary, then again inside a consumer; on write and again on read), `f(f(x)) === f(x)` is part of its contract and carries its own assertion over a corpus including the degenerate inputs (empty, all-separator, already-normalized, falsy-but-present). The equivalence check for the collapse runs over the **composed value the caller observes** — the joined path, the rendered string, the persisted key — never over the helper's return at each site in isolation. Where the observable is built from several normalized segments, **every** segment is normalized at the **same** boundary, not only the one the diff touched.
- **Auditor checks —** `[D]` Count the applications of the collapse target along each live path: more than one anywhere demands an `f(f(x)) === f(x)` assertion over a corpus including the degenerate inputs. `[D]` Diff the **composed observable** before and after the collapse across a *generated* input corpus (not a hand-picked shape list) and report the divergence count — a collapse that changes any composed output is a behavior change needing its own approval. `[J]` The helper doesn't **default** before it **normalizes** (or otherwise emit a value its own second application would rewrite). `[J]` For an observable assembled from several segments, each one is normalized — not only the one under the diff. `[D]` The collapse target has at least one call site, and a comment claiming it is "the ONE source" names derivers that really call it. `[J]` **A total claim in a comment is earned by a pin, not by an argument:** for every "cannot diverge / always / never / the ONE source" a diff authors or re-asserts, name the assertion that turns red when it stops holding; if there is none, the honest comment states what was measured. Re-asserting a totality the same comment records as *previously false* is the loudest form of this.
- **Incident —** 0041 S10a (2026-08-17): the spec asked for *"one source of the artifact-directory shape"* and the diff delivered exactly that — five inconsistent copies routed through one helper nobody asked to be **idempotent**, on a live runtime-QA path that applies it **twice**. It defaulted before it trimmed, so an all-separator directory trimmed to `""` and the second application substituted the default: the QA driver **saved** screenshots under one directory while the run report **cited** another. Measured, the pre-change code diverged on **0** of 23 directory shapes and the collapsed code on **8 — every one created by the collapse**; over 200,000 random pairs the divergence rate was **95.4%**. The diff conformed to the spec at every line, so reviewing it against the spec was no defense; only executing the *composed* path over a generated corpus found it. The same round found the twin defect one axis over (one segment normalized, the label on the other side left raw), and the helper's own comment asserted the two paths "cannot diverge" in the paragraph recording that claim as previously false. Closed by trimming before defaulting, normalizing both segments at one boundary, and pinning `f(f(x)) === f(x)`. *(The composed-observable corpus IS the equivalence oracle a collapse needs — `testing.md` → *Characterization tests & golden master*. The effectful cousin, a retried write, is `reliability-resilience.md` → *Idempotency & safe retry*.)*

## Type safety

- **Good looks like —** Strict and **on**: TS `strict`, `noImplicitAny`, `noUncheckedIndexedAccess`; mypy `--strict`. External input is **parsed** into a typed shape at the boundary, never cast.
- **Auditor checks —** `[D]` Type-checker passes with strict config (`tsc --noEmit`, `mypy --strict`) — no new errors, no new suppressions. `[D]` Count of `any`/`@ts-ignore`/`type: ignore` introduced (lint rule `no-explicit-any`, `no-ts-ignore`). `[J]` Untrusted input *parsed* into a type at the edge (zod/pydantic), not asserted with `as`.

## Open/Closed & config-driven

- **Auditor checks —** `[J]` Adding a variant means registering an entry, not editing a central conditional. `[J]` Environment/behavioral knobs configurable, not hardcoded per-env. `[D]` Magic-literal lint where configured (`no-magic-numbers`). *(Don't pre-build the indirection before variation exists — YAGNI.)*

## Clear contracts & interfaces

- **Auditor checks —** `[J]` The public API is minimal and leaks no internals (helpers, mutable state, concrete types where an interface belongs). `[J]` Error/edge outcomes are part of the contract (typed errors / documented), not surprises. `[D]` Public-surface lint (`no internal export` / package `exports` map / API-extractor) where configured. *(Breaking changes to a published contract are versioned — cross-ref `api-and-contracts`.)*

## Low coupling / high cohesion

- **Auditor checks —** `[D]` **Cyclic dependencies** — `madge --circular` / dependency-cruiser / import-linter reports none. `[D]` Fan-in/fan-out & instability metrics where tooled (dependency-cruiser, SonarQube). `[J]` No module reaches across a boundary into another's internals (high coupling) or owns unrelated responsibilities (low cohesion). `[J]` Wiring via injected interfaces, not `new`-ing concretes inside business code.

## Knowledge-store shape (bound what a reader READS, not what the system KNOWS)

- **Good looks like —** Long-lived knowledge stores (ledgers, decision records, catalogs, registries) are shaped for **bounded per-consultation reads**: a lean index (locate, don't ingest) routes to small per-topic units, each under its own size cap; accretion grows **horizontally** (new units), never one monolith. Distinguish a **log** (entries supersede — condense periodically; a recorded cap-bump is a fine escape) from a **rule-book** (entries persist by design — a fixed total cap eventually collides with the store's floor; shard it instead). External references point at the index/entry point, never at unit internals, so a future unit split stays cheap.
- **Auditor checks —** `[D]` Per-unit size caps exist and are gate-checked where a budget gate is wired. `[J]` The store is classified log or rule-book, and its growth mechanism matches (condense-and-cap vs index+shards). `[J]` No external reference bypasses the index into unit internals. `[J]` One consultation doesn't require ingesting the whole store.
- **Incident —** This harness's own decisions ledger: a 54 KB single-file **rule-book** sitting at its condensed floor became an index + ten per-topic shards under per-shard caps (2026-07, plan 0040) — the cap-and-condense mechanism had run out of room because the store was never a log.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
