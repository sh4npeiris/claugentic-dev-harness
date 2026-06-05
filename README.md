# claugentic-dev-harness

A **reusable, self-improving Claude Code development harness**, packaged as a plugin you can install into any codebase.

It turns ad-hoc agent coding into a disciplined, repeatable practice: a staged workflow that takes substantial work from idea → landed change, a library of specialist agent roles, a project-agnostic engineering-standards catalog, an always-current architecture index with deterministic enforcement, and a loop that promotes what you learn back into the harness so each task starts smarter than the last.

> **Status — early v0.1 (functional core is live).** Phase 0 (the harness's "brain") is built, and so is the functional core: **both skills — `/claugentic-dev-harness:init` and `/claugentic-dev-harness:audit` — are live and installable today** (see *Install* below). The harness already **dogfoods itself** — it was used to build itself, and `/claugentic-dev-harness:audit` has run on this repo to produce a real backlog. **Honest about what's still ahead:** the immediate next step is a **cold-install verification** (a fresh adopter repo) + a **JS-app dogfood**; the deterministic **trust-gates** (an independent verification track), `/claugentic-dev-harness:update`, and `/claugentic-dev-harness:explain` are **future**, not built. The harness's whole pitch is honesty — so this README states only what's real.

## What's in the box

- **Staged workflow** (`docs/WORKFLOW.md`) — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → **Retrospect**. Small changes take the lightweight path (Implement + Verify); substantial work runs the full pipeline. Work is sliced so each unit lands **vertically complete in one session with no tech debt**.
- **Role library** (`.claude/agents/`) — **6 specialist subagents** the orchestrator delegates to and composes: `plan-reviewer` (adversarial plan critique), `implementer-architect` (builds one slice to standard in an isolated worktree), `architect-reviewer` (owns the Verify gate — solo for small changes, or synthesizer over a lens fan-out), `product-designer` (the product/UX lens at Discuss), `lens-reviewer` (audits a diff or an audit-scope against **one** standards module, fanned out one-per-lens), and `yagni-sentinel` (the anti-over-engineering skeptic). The library is meant to **grow** as needs emerge.
- **Engineering standards** (`docs/standards/`) — a **modular catalog of 11 quality modules** (security, maintainability-structure, testing, product-ux, data-and-persistence, reliability-resilience, performance-efficiency, api-and-contracts, observability-ops, accessibility-i18n, docs-traceability), anchored to ISO/IEC 25010 and loaded by relevance, not all at once. `docs/ENGINEERING_STANDARDS.md` is now a **thin pointer** into this catalog. The spec names the in-scope modules per slice; the reviewer audits against them.
- **Architecture index + enforcement** (`docs/ARCHITECTURE_TREE.md` + `scripts/check_architecture_tree.py`) — one line per source file so agents read the index, not the whole tree. A deterministic (no-LLM) hook checks presence + staleness on every Write and blocks finishing until the index is current (`.claude/settings.json`).
- **Audit → tiered backlog → per-item, discipline-gated execution** — `/claugentic-dev-harness:audit` does a bounded gap-analysis sweep of a codebase (a `lens-reviewer` fan-out) and writes a **tiered, tagged, plain-English backlog** into `docs/ROADMAP.md`. There is **no separate refactor command**: each item is brought to standard through the **existing staged pipeline**, and the **item's tag selects the discipline** (a `refactor` item → characterization-tests-first; see `docs/WORKFLOW.md` → *Executing an audit backlog item*) — never a mass auto-rewrite.

## Install

Distributed as a **Claude Code plugin** via a marketplace (`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`). The manifest exposes the **6 specialist agents**; the two skills (`/claugentic-dev-harness:init`, `/claugentic-dev-harness:audit`) live under `skills/`.

```
/plugin marketplace add sh4npeiris/claugentic-dev-harness
/plugin install claugentic-dev-harness@sh4npeiris
```

> Public + **Apache-2.0** licensed — free to install and use; no GitHub auth required.

## How it works

The flow once the plugin is installed:

1. **`/claugentic-dev-harness:init` scaffolds** the managed harness into your repo — the `docs/standards/` catalog, the workflow, the playbook, and the tree-check enforcement, each **version-stamped** as a managed copy. It detects your languages, **composes with your existing lint/type-check/test tooling** (detects and records it — never installs or reconfigures it), and is **idempotent and never clobbers** existing files (re-running is a safe no-op).
2. **`/claugentic-dev-harness:audit` audits** the repo — it reads the codebase, explains in plain English what the app is and does, then sweeps it through the quality lenses and writes a **prioritized, tiered, tagged backlog** into `docs/ROADMAP.md` (for untested behavior-bearing code, "establish a test baseline" is the Tier-1 starting point).
3. **You pick an item; the staged pipeline lands it.** Each backlog item runs through the full workflow (Discuss → Plan → Review → Spec → Approve → Implement → Verify → Land), and its **tag selects the discipline** — e.g. a `refactor` on untested code is gated behind a characterization-test baseline first. Safe, incremental, one item at a time — never a big-bang rewrite.

Same flow as above — the difference is where you start:

- **Existing codebase** — `/claugentic-dev-harness:init` then `/claugentic-dev-harness:audit` hands you a prioritized backlog to bring a mature project up to standard **incrementally**, one item at a time (never a big-bang rewrite).
- **New project** — `/claugentic-dev-harness:init` into the young/empty repo; the staged workflow then governs from the first feature, `ARCHITECTURE_TREE.md` grows with the code (hook-enforced), and the standards apply from day one.

## This repo dogfoods its own harness

`claugentic-dev-harness` is built **using** the harness it ships: the workflow, roles, standards, and architecture-tree enforcement here govern its own development — and `/claugentic-dev-harness:audit` has already run on this repo to produce the backlog in `docs/ROADMAP.md`. See `CLAUDE.md`, `docs/WORKFLOW.md`, and the active plan in `.claude/plans/`.

## Layout

See `docs/ARCHITECTURE_TREE.md` for the full index. Top level:

```
README.md             — this file
CLAUDE.md             — lean, generalized guidance for agents working in THIS repo
docs/                 — WORKFLOW, PLAYBOOK, ENGINEERING_STANDARDS (pointer), ARCHITECTURE_TREE, DECISIONS, ROADMAP
docs/standards/       — the 11-module engineering-standards catalog (+ _TEMPLATE, README)
.claude/agents/       — the 6-role specialist library (plan-reviewer, implementer-architect, architect-reviewer, product-designer, lens-reviewer, yagni-sentinel)
.claude/plans/        — active plans + TEMPLATE (completed/superseded plans → docs/archive/)
.claude/settings.json — hooks (architecture-tree enforcement)
.claude-plugin/       — plugin + marketplace manifests (makes this repo installable)
skills/               — the installable skills (init, audit), each a SKILL.md
scripts/              — check_architecture_tree.py (deterministic index gate)
```
