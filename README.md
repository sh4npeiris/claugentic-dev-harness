# agentic-dev-harness

A **reusable, self-improving Claude Code development harness**, packaged as a plugin you can install into any codebase.

It turns ad-hoc agent coding into a disciplined, repeatable practice: a staged workflow that takes substantial work from idea → landed change, a growing library of specialist agent roles, a project-agnostic engineering-standards bar, an always-current architecture index with deterministic enforcement, and a loop that promotes what you learn back into the harness so each task starts smarter than the last.

> **Status:** scaffold. This repo was **extracted from a working harness** that lived as files inside a real project, then generalized to be project-agnostic. The plugin packaging and the workflows are the build ahead — see [`.claude/plans/0001-build-agentic-dev-harness.md`](.claude/plans/0001-build-agentic-dev-harness.md).

## What's in the box

- **Staged workflow** (`docs/WORKFLOW.md`) — Triage → Discuss → Plan → Review-the-plan → Spec → **Approve** → Implement → Verify → Land → **Retrospect**. Small changes take the lightweight path (Implement + Verify); substantial work runs the full pipeline. Work is sliced so each unit lands **vertically complete in one session with no tech debt**.
- **Role library** (`.claude/agents/`) — specialist subagents the orchestrator delegates to and composes: `plan-reviewer` (adversarial plan critique), `implementer-architect` (builds one slice to standard in an isolated worktree), `architect-reviewer` (audits the implemented diff against the standards). The library is meant to **grow** as needs emerge.
- **Engineering standards** (`docs/ENGINEERING_STANDARDS.md`) — a project-agnostic, ever-growing catch-all of quality dimensions (correctness, security, performance, extensibility, testing, …). The spec names the in-scope dimensions per slice; the reviewer audits against them.
- **Architecture index + enforcement** (`docs/ARCHITECTURE_TREE.md` + `scripts/check_architecture_tree.py`) — one line per source file so agents read the index, not the whole tree. A deterministic (no-LLM) hook checks presence + staleness on every Write and blocks finishing until the index is current (`.claude/settings.json`).
- **Audit → backlog → gated per-item refactor** — a `/harness-audit` workflow does a bounded gap-analysis sweep of an existing codebase and writes a prioritized backlog into `docs/ROADMAP.md`; each item is then brought to standard **incrementally and safely** through the full pipeline, with a characterization-tests-first `refactor-item` workflow — never a mass auto-rewrite.

## How it installs

Distributed as a **Claude Code plugin** via a marketplace, with a `.claude-plugin/plugin.json` manifest exposing the commands (`/init-harness`, `/harness-audit`) and bundling the agents, workflow docs, standards, and the architecture-tree check.

> Install instructions (marketplace + plugin name) are **TODO** — they land once the plugin is packaged (plan 0001, final slice).

## Two adoption modes

**Existing codebase** — bring a mature project up to standard incrementally:
1. `/init-harness` scaffolds the harness into the repo (docs, generated `ARCHITECTURE_TREE.md`, a per-repo Current-scope section, a CLAUDE.md harness section, and language-detected globs for the tree check) — **idempotent; never clobbers** existing files.
2. `/harness-audit` runs the audit workflow → a prioritized backlog in `docs/ROADMAP.md` (for untested code, "establish a test baseline" is item #1).
3. You pick items; each runs the full pipeline. The `refactor-item` workflow does **characterization-test-first → refactor in an isolated worktree → verify behavior unchanged → land.** Safe, incremental — never a big-bang rewrite.

**New project** — start right from day one:
1. `/init-harness` scaffolds into the young/empty repo.
2. The staged workflow governs from the first feature; `ARCHITECTURE_TREE.md` grows with the code (hook-enforced); the engineering standards apply from the start.

## This repo dogfoods its own harness

`agentic-dev-harness` is built **using** the harness it ships: the workflow, roles, standards, and architecture-tree enforcement here govern its own development. See `CLAUDE.md`, `docs/WORKFLOW.md`, and the active plan in `.claude/plans/`.

## Layout

See `docs/ARCHITECTURE_TREE.md` for the full index. Top level:

```
README.md            — this file
CLAUDE.md            — lean, generalized guidance for agents working in THIS repo
docs/                — WORKFLOW, ENGINEERING_STANDARDS, ARCHITECTURE_TREE, DECISIONS, ROADMAP
.claude/agents/      — specialist role library (plan-reviewer, implementer-architect, architect-reviewer)
.claude/plans/       — active plans + TEMPLATE; 0001 is the build plan for this repo
.claude/settings.json — hooks (architecture-tree enforcement)
scripts/             — check_architecture_tree.py (deterministic index gate)
```
