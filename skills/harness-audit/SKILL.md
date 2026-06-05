---
description: Audit this codebase against the engineering-standards catalog and write a prioritized, plain-English backlog to docs/ROADMAP.md. Builds a "what your app is & does" map first, then sweeps the code through the relevant standards lenses (bounded, dedup, loop-until-dry).
---

# /harness-audit

Point this at a repo and it teaches you what the codebase is, then finds the work
worth doing — written back as a plain-English, prioritized backlog a non-engineer
can act on.

## How this skill works

Three phases, cheap → expensive:

1. **Understand** *(LIVE — this slice)* — one cheap inline pass over manifests +
   structure to produce a plain-English **"what your app is & does"** overview and
   an **audit-plan** (what to look at, in what order, with what excluded). No fan-out.
2. **Audit** *(NOT YET BUILT — plan 0003 S2b)* — the expensive fan-out: `lens-reviewer`s
   sweep the included code through the relevant standards modules, dedup, loop-until-dry.
3. **Backlog** *(NOT YET BUILT — plan 0003 S2b)* — the audit findings, written as a
   tiered, tagged, plain-English backlog in `docs/ROADMAP.md`.

Today the skill runs **Phase 1**, writes the overview, hands the audit-plan forward,
and **stops** — telling the user the audit phase is coming. Do not fabricate findings.

---

## Phase 1 — Understand  *(LIVE)*

A single cheap, inline pass. **Budget discipline:** read **manifests, configs, entry
points, and READMEs — not every source file.** You are building a map, not reviewing code.

### Output contract — what this phase produces

- **(A) User-facing overview** — plain-English, **text-only** (no diagram), written
  into the ROADMAP overview fence (see *Where the overview goes* below). For a
  non-engineer. Sections, in order:
  *what it is · what it does · how it's built · how it's organized ·
  safety-net signals (tests / CI / types) · confidence & caveats.*
  Be **honest that it's inferred from structure, not from running the app.**
- **(B) Audit-plan** — audit-internal, handed to Phase 2; also shown to the user
  in-conversation as the proof this phase ran. Five fields:
  *exclude-set · prioritized directory order · monorepo / package boundaries ·
  detected ecosystem + existing tooling · candidate standards modules.*

### The 8-step procedure

Run these in order. Each step feeds the output contract above.

1. **Prefer existing signal.** If `docs/ARCHITECTURE_TREE.md` exists and is current
   (DRY with `harness-init`, which generates it), use it as the file-level map — do
   **not** re-walk the tree. Otherwise derive structure via a **bounded `Glob` walk**
   (top-level dirs + one or two levels in; do not enumerate excluded trees). Either
   way, read only manifests / configs / entry points / READMEs from here on.

2. **Detect ecosystem & tooling.** Scan the root and significant subdirs for
   **manifests** to identify language(s), framework(s), and package manager — the
   general rule is *"identify by manifest,"* not an exhaustive list:
   `package.json` (Node/JS/TS), `pyproject.toml` / `requirements.txt` / `setup.py`
   (Python), `go.mod` (Go), `Cargo.toml` (Rust), `pom.xml` / `build.gradle` (JVM),
   `Gemfile` (Ruby), `composer.json` (PHP), `*.csproj` / `*.sln` (.NET), … . In the
   same pass, detect **existing lint / format / type-check / test tooling** from its
   config (eslint, prettier, `tsconfig.json`, jest / vitest / pytest / go test, …)
   and any CI workflows (`.github/workflows`, `.gitlab-ci.yml`). This dovetails with
   `harness-init`'s compose-with-existing-tooling and tells the audit **which gates
   already exist** so it doesn't propose redundant ones.

3. **Detect monorepo / package boundaries.** Look for `workspaces` (in `package.json`),
   `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, multiple manifests in
   different dirs, or a `packages/` · `apps/` layout. **If monorepo, enumerate the
   packages as separate audit units** (each gets its own slice of the directory order).

4. **Build the exclude-set.** Honor **`.gitignore` as the primary signal** (read it
   first), augmented by well-known dirs the audit must never spend budget on:
   - VCS: `.git`
   - dependencies: `node_modules`, `vendor`, `.venv` / `venv`, `__pycache__`,
     `target`, `Pods`
   - build / output: `dist`, `build`, `.next`, `out`, `coverage`, `.turbo`
   - generated: `*.generated.*`, `*.min.js`, codegen output
   - lockfiles and large binary / media assets
   - **Security (hard rule):** **never read or echo secrets** — `.env*` files, keys,
     credentials, certificates. Exclude them from the walk and **never surface their
     contents** in the overview or the audit-plan. If you must mention one exists, name
     the file, not its contents.

5. **Identify entry points & surfaces.** From the manifests and conventions, find how
   the app is entered: `main` / `bin` / `scripts` (Node), `[project.scripts]` /
   `__main__.py` (Python), `func main` (Go), framework conventions (`src/index.*`,
   `app/`, `pages/`, `cmd/`), `Dockerfile` `CMD` / `ENTRYPOINT`. Use these to classify
   the app's **type** — CLI · web server · library · SPA · service · (or, as here, a
   plugin / docs-and-tooling repo) — and its external surfaces.

6. **Map dependencies (high-level).** Name only the **architecturally-significant**
   dependencies (web frameworks, DB drivers, HTTP / auth libraries, queues) — enough to
   say *"an Express + Postgres API,"* not every transitive dep. These **pre-select the
   likely standards modules**: a DB driver pulls in `data-and-persistence`; an HTTP
   server pulls in `api-and-contracts` + `security`; a UI pulls in `product-ux`.

7. **Prioritized directory order.** Rank the *included* directories by likely
   risk / value for the audit's budget spend — highest first:
   **entry points & core domain → data / persistence → API / routes → UI →
   config / scripts → tests last.** This is what Phase 2 walks; spend lands where bugs
   and standards violations cluster.

8. **Compose & emit.** Write the plain-English overview **(A)** into the ROADMAP fence
   (replacing only the fenced content — see below), and present the audit-plan **(B)**
   to the user as this phase's proof and Phase 2's input.

### Where the overview goes — the ROADMAP fence  *(load-bearing convention)*

Phase 1 writes the overview into `docs/ROADMAP.md`, between exact HTML-comment markers:

```
<!-- harness-audit:overview:start -->
…generated overview here…
<!-- harness-audit:overview:end -->
```

Rules:
- On **re-run, replace only the content *inside* the fence.** Everything outside it
  is **human-owned and must never be touched** — human-added roadmap items survive
  every regeneration.
- If the fence is **absent**, insert it once near the top of the ROADMAP (after the
  intro block), headed
  `## What this app is & does  _(generated by /harness-audit · do not edit — re-run to refresh)_`.
- Phase 2 (S2b) will add a **parallel `<!-- harness-audit:backlog:start -->…:end`
  fence** for the backlog, governed by the same replace-only-inside rule. *(Forthcoming.)*

---

## Phase 2 — Audit + backlog  *(NOT YET BUILT)*

This phase **is not implemented yet — it lands in plan `0003`, slice S2b.**

Today: after Phase 1 writes the overview and emits the audit-plan, **stop here and
tell the user the audit phase is coming** (do not fan out, do not invent findings,
do not write a backlog). The Understand overview is the deliverable for now.

When built (S2b), Phase 2 consumes the audit-plan to fan out `lens-reviewer`s over the
included code and write a **tiered, tagged, plain-English backlog** into a parallel
`harness-audit:backlog` fence — full design in plan `0003` (slice S2b).
