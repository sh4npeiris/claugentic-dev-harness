# 0001 — Build agentic-dev-harness (portable harness → installable plugin)

- **Status:** **Superseded by [`0002-harness-re-architecture.md`](0002-harness-re-architecture.md)** — its build slices B1–B6 fold into 0002's Phases 2–7 (the plugin now packages the *enriched* harness). Kept for reference. (Was: Draft awaiting plan-review.)
- **Roadmap item:** `docs/ROADMAP.md` → B1–B6
- **References:** `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` (Bootstrap) · `docs/WORKFLOW.md` · `docs/ENGINEERING_STANDARDS.md`

## Problem

The harness currently exists only as a set of files **inside the DistrictSync project** (`docs/WORKFLOW.md`, `docs/ENGINEERING_STANDARDS.md`, the `.claude/agents/*` role library, `.claude/plans/*`, `.claude/settings.json` hooks, `scripts/check_architecture_tree.py`). To reuse it in another codebase you'd copy-paste those files and hand-edit them — error-prone, drifts immediately, and there's no command to scaffold them or to bring an existing codebase up to standard. This repo holds the **generalized, portable** harness (already extracted + stripped of project specifics); the work is to **package it as a reusable Claude Code plugin** installable in *any* codebase, with commands that scaffold it and run its workflows.

## Goals / Non-goals

**Goals**
- An **installable Claude Code plugin** (`.claude-plugin/plugin.json` manifest) distributed via a **marketplace**, bundling the agents, workflow docs, standards, and the architecture-tree check.
- **`init-harness`** command — a fast, **idempotent** scaffold that drops the harness into a target repo without clobbering anything.
- A **separate `/harness-audit`** command — a bounded gap-analysis of the target codebase that writes a prioritized backlog into `docs/ROADMAP.md`.
- Two reusable workflows: **`audit`** (sweep → dedup → prioritize → backlog) and **`refactor-item`** (gated, characterization-tests-first, per-item bring-to-standard).
- Gated **per-item** refactor: characterization tests first, refactor in isolation, verify behavior unchanged, land.

**Non-goals**
- **Bulk / automatic refactor** of a codebase — the harness brings a repo to standard *incrementally and safely*, one approved item at a time. Never a mass rewrite.
- **Modifying the target repo's *code* on init** — `init-harness` only scaffolds harness/docs files; it never edits application source.
- **Language lock-in** — the harness is language-agnostic; `init-harness` detects languages to set the tree-check globs, and no workflow assumes Python (this repo happening to use Python for one script is incidental).

## Decisions (locked — see `docs/DECISIONS.md`, 2026-06-04)

1. Harness **extracted from DistrictSync (PR #16)** and generalized into this standalone repo.
2. **`init` = scaffold-only; audit = separate `/harness-audit`** (init stays fast + idempotent + re-runnable).
3. **Audit → ROADMAP backlog; refactor per-item & gated (characterization-tests-first); no bulk auto-refactor.**
4. **Packaged as a dedicated-repo plugin** (manifest + commands + agents + docs), installed via a marketplace.

## Two adoption modes

### Existing codebase — incremental, safe bring-to-standard
1. **`/init-harness`** scaffolds the harness into the repo:
   - copies the workflow docs, the engineering standards, the role library, and the hooks;
   - **generates `docs/ARCHITECTURE_TREE.md`** by walking the repo (one line per in-scope source file);
   - **creates the per-repo "Current scope"** snapshot at the bottom of `ENGINEERING_STANDARDS.md` (which dimensions are live in *this* codebase today);
   - **adds a harness section to the repo's `CLAUDE.md`** (or creates a lean one), pointing at the workflow/standards — without duplicating them;
   - **detects the repo's languages/layout → sets `INCLUDE_GLOBS`** (and the matching `STALE_PATTERN`) in `scripts/check_architecture_tree.py`;
   - **idempotent: never clobbers** an existing file — re-running is safe (skip/merge, report what it did).
2. **`/harness-audit`** runs the `audit` workflow → a **prioritized backlog** in `docs/ROADMAP.md`. For untested code, **"establish a test baseline" is item #1** (you cannot safely refactor what you can't characterize).
3. The user **picks items**; each runs the **full pipeline** (`docs/WORKFLOW.md`). The **`refactor-item`** workflow does: write **characterization tests first** → refactor in an **isolated worktree** → **verify behavior unchanged** (characterization + existing suite green) → land. The codebase is brought to standard **incrementally and safely — never a mass rewrite.**

### New project — right from day one
1. **`/init-harness`** scaffolds into the young/empty repo (same steps; `ARCHITECTURE_TREE.md` may start nearly empty and the language detection may infer from the chosen stack or default sensibly).
2. The **staged workflow governs from the first feature**; `ARCHITECTURE_TREE.md` **grows with the code** (the Write/Stop hooks keep it current); the **engineering standards apply from day one**. There's no backlog to audit yet — the harness simply enforces quality as the code is written.

## Approach

A **generalized, portable harness** (this repo) + a thin **plugin layer** on top:
- `.claude-plugin/plugin.json` **manifest** declaring the plugin, its agents (`.claude/agents/*`), and its commands.
- **Commands:** `init-harness` (scaffold) and `harness-audit` (run the audit workflow).
- **Two workflows** (`audit`, `refactor-item`) authored as command/skill instructions that drive the existing role library (`plan-reviewer`, `implementer-architect`, `architect-reviewer`) and the staged pipeline.
- **Dogfood** the workflows against a real codebase (**DistrictSync**) before finalizing — the audit must reproduce DistrictSync's known tiered backlog, and one `refactor-item` must run end-to-end with tests staying green.

Alternatives rejected (1 line each):
- *Copy-paste harness files per project* — drifts instantly, no scaffold/idempotency, no audit. The whole reason to package.
- *One mega `init` that also audits + refactors* — violates Decision 2/3 (init must stay fast + idempotent; audit + refactor are gated, per-item, and user-driven).
- *Runtime fetch of roles/skills from a marketplace* — supply-chain / prompt-injection / non-reproducibility risk; roles stay version-controlled in `.claude/agents/` (carried over from the source harness's standing decision).

## Affected files

- `.claude-plugin/plugin.json` — **new**: plugin manifest (name, version, agents, commands). *Schema verified against official Claude Code docs before authoring (Slice 1).*
- `commands/init-harness.*` — **new**: idempotent scaffold command (copy docs/agents/hooks, generate ARCHITECTURE_TREE, create Current-scope, add CLAUDE section, detect languages → set globs, never clobber).
- `commands/harness-audit.*` — **new**: runs the `audit` workflow against the host repo.
- `docs/WORKFLOW.md` — extend with the two new workflows (`audit`, `refactor-item`) as first-class procedures, or add companion docs they reference.
- `.claude/agents/*` — reuse as-is; add a new role only if a workflow needs a specialist not covered (note it in DECISIONS if so).
- `scripts/check_architecture_tree.py` — already parameterized (`INCLUDE_GLOBS`/`STALE_PATTERN` set per-repo by `init-harness`); `init-harness` writes those values.
- `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · `docs/ROADMAP.md` — kept current each slice.

## Risks & mitigations

- **Plugin manifest schema is unknown / may change** → **verify `plugin.json` against the official Claude Code plugin docs before Slice 1** and validate the packaged plugin loads. Don't guess the schema from memory.
- **Audit on huge / spaghetti repos blows the context budget or misses areas** → the `audit` workflow is **bounded by budget + directory**, **dedups** overlapping findings, **prioritizes** (tiers), and **loops until dry** (re-sweep remaining areas) rather than one unbounded pass. Delegate sweeps to parallel subagents so the orchestrator stays lean.
- **Refactoring untested code silently changes behavior** → **characterization-tests-first is mandatory** in `refactor-item`; "establish a test baseline" is backlog item #1 for untested code; refactor happens in an isolated worktree and must leave the characterization + existing suite green.
- **Generalization leaks project specifics** → the portable harness was stripped of DistrictSync specifics on extraction; `init-harness` must not bake in any one stack; review each shipped file for project-agnosticism.
- **`init-harness` clobbers a target repo's files** → **idempotency is a hard requirement**: detect existing files, skip or merge (never overwrite), and report exactly what was created/skipped; re-running must be safe.

## Test strategy

- **Dogfood every workflow on DistrictSync** (a real, non-trivial codebase).
- The **`audit` must reproduce DistrictSync's known backlog** (its existing Tier-1/2/3 architecture findings) — this is the acceptance bar for Slice 2.
- Run **one `refactor-item` end-to-end** on DistrictSync: characterization tests written first, refactor in a worktree, **existing + new tests stay green**.
- **Install the packaged plugin into a fresh, throwaway repo** and run `/init-harness` → `/harness-audit` end-to-end (Slice 6) to prove a cold install works.
- For this repo's own code: `python scripts/check_architecture_tree.py` stays green; any helper scripts added get tests.

## Decomposition (slices)

Workflows-first; each slice lands **complete in one ≤1M-context session, no debt** (code/commands + docs + ARCHITECTURE_TREE/DECISIONS updated, gates green).

- [ ] **Slice 1 — Plugin shell + manifest.** Author `.claude-plugin/plugin.json` exposing the agents + (stub) commands. *Verify the manifest schema against the official Claude Code plugin docs first.* *Lands complete:* the plugin loads in Claude Code; agents are discoverable; ARCHITECTURE_TREE + DECISIONS updated.
- [ ] **Slice 2 — `audit` workflow.** Bounded multi-modal sweep (parallel subagents, budget + directory bounds) → dedup → prioritize into tiers → write the backlog to `docs/ROADMAP.md`; loop-until-dry. *Lands complete:* running it on DistrictSync **reproduces its known Tier-1/2/3 backlog.**
- [ ] **Slice 3 — `refactor-item` workflow.** Characterize (tests first) → refactor in an isolated worktree → verify behavior unchanged → land. *Lands complete:* one DistrictSync item taken through it end-to-end with the existing + characterization suites green.
- [ ] **Slice 4 — `init-harness` command.** Idempotent scaffold: copy harness files, **generate `ARCHITECTURE_TREE`**, create the per-repo **Current-scope**, add the **CLAUDE harness section**, **detect languages → set `INCLUDE_GLOBS`/`STALE_PATTERN`**; **never clobber**. *Lands complete:* running it twice on a sample repo is a safe no-op the second time and reports what it did.
- [ ] **Slice 5 — `/harness-audit` command + skill wiring.** Surface the `audit` workflow (Slice 2) as a first-class command/skill from the manifest. *Lands complete:* `/harness-audit` invokes the workflow against the host repo.
- [ ] **Slice 6 — Package & dogfood.** Finalize the marketplace package; **install it into a throwaway repo** and run `/init-harness` → `/harness-audit` end-to-end; write the README install instructions. *Lands complete:* a cold marketplace install works end-to-end.

---

## Review  _(filled by plan-reviewer, Stage 3)_
- **Verdict:** PASS | CHANGES REQUIRED
- **Required changes:** …
- **Sizing/completeness:** per-slice OK / split …
- **Harness impact:** …

---

## Spec  _(per slice, after Review passes — Stage 4)_
Spec'd per slice at its own approval gate (Stage 4/5), starting with Slice 1.
