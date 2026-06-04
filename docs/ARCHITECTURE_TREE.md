# Architecture Tree

> **Read this first.** This is the one-line-per-file index of the repo — your map. Use it to find the right file instead of reading the whole tree. Keep it current: every file add/move/remove updates this index (a hook enforces presence + staleness — see CLAUDE.md → Harness Discipline). Descriptions are authored by you/the agent that touches the file.

This repo builds the **`agentic-dev-harness`** Claude Code plugin and dogfoods its own harness. The only executable code today is `scripts/check_architecture_tree.py`; everything else is harness docs, roles, plans, and config.

## Root

- `README.md` — what `agentic-dev-harness` is (reusable self-improving Claude Code dev harness + plugin), how it installs, the two adoption modes, and current scaffold status.
- `CLAUDE.md` — lean, generalized guidance for agents working in THIS repo: engineering principles, harness discipline, workflow pointer, Definition of Done.
- `.gitignore` — ignores local junk + build artifacts; **shares** `.claude/agents/`, `.claude/plans/`, `.claude/settings.json` (ignores only `.claude/settings.local.json`).
- `.gitattributes` — normalizes line endings (`* text=auto eol=lf`; scripts forced LF) for a cross-platform plugin that bundles shell/Node scripts.

## docs/ — process, standards, and project memory

- `docs/WORKFLOW.md` — the staged agent development workflow (Triage → Discuss → Plan → Review → Spec → Approve → Implement → Verify → Land → Retrospect); source of truth for process.
- `docs/ENGINEERING_STANDARDS.md` — project-agnostic, ever-growing catch-all of engineering quality dimensions; the bar implementations are held to (the per-repo "Current scope" is added by `init-harness`, not shipped populated).
- `docs/ARCHITECTURE_TREE.md` — this file: one-line-per-file index of the repo.
- `docs/DECISIONS.md` — dated, one-line records of non-trivial decisions (newest at top); consult before re-litigating.
- `docs/ROADMAP.md` — backlog of substantial work (the plan-0001 build slices B1–B6); tangents land here, never silently into the current change.

## .claude/agents/ — specialist role library

- `.claude/agents/plan-reviewer.md` — adversarially critiques a draft plan (Stage 3): soundness, sizing/completeness, risk, YAGNI, harness impact; edits only the plan's Review section.
- `.claude/agents/implementer-architect.md` — implements one approved, spec'd slice to standard in an isolated worktree (Stage 6); lands code + tests + docs with no debt.
- `.claude/agents/architect-reviewer.md` — audits an implemented diff against the in-scope ENGINEERING_STANDARDS dimensions before it lands (Stage 7); read-only on source.

## .claude/plans/ — active plans

- `.claude/plans/TEMPLATE.md` — the plan template (Problem / Goals / Approach / Affected files / Risks / Tests / Decomposition / Review / Spec) every plan starts from.
- `.claude/plans/0001-build-agentic-dev-harness.md` — the original build plan (package the portable harness as a plugin, slices B1–B6); **superseded by 0002** (its B1–B6 fold into Phases 2–7 there).
- `.claude/plans/0002-harness-re-architecture.md` — **active master plan**: re-architect the harness around three pillars (multi-lens quality catalog · legacy understand→audit→gated-refactor · multi-lens review + product/UX lens) + plugin packaging; Phase 0 (foundation enrichment) is sliced, later phases get sub-plans.

## .claude/ — harness config

- `.claude/settings.json` — Claude Code hooks: PostToolUse(Write) nudge + Stop backstop that run the architecture-tree check.

## scripts/ — tooling

- `scripts/check_architecture_tree.py` — deterministic (no-LLM) gate enforcing that this index lists every in-scope source file (presence) and references no deleted file (staleness); `--hook` / `--hook-write` modes wired in `.claude/settings.json`. `INCLUDE_GLOBS`/`STALE_PATTERN` are set per-repo by `init-harness`.
