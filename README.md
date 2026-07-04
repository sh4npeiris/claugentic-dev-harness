# claugentic-dev-harness

A Claude Code plugin that turns AI coding into a **disciplined, reviewable process**: it plans before it builds, reviews its own work against a written standards catalog, keeps an always-current map of your codebase, and **never changes your code without your sign-off.**

You steer with plain-English decisions; it does the engineering one reviewed slice at a time — and it's **honest about the difference between what it checked mechanically and what's its own judgment.**

The mission is **addractive** software — *attractive + addictive by merit*: earned pull through craft and delight, the honest opposite of dark-pattern "addiction" (no traps, no manipulation). The harness doesn't promise beautiful software — it **forces the craft question**, **checks the safety and accessibility floor** (mechanically where your tooling is wired, by reviewer judgment otherwise), and **routes the taste verdict to you.** It never certifies "beautiful"; it raises the bar and hands you the call.

## The four commands

- **`/claugentic-dev-harness:init`** — set it up in your repo. Adds a codebase map, a quality-standards catalog, and the workflow docs. Never overwrites your content; re-run any time to update.
- **`/claugentic-dev-harness:product`** — define what you're building (who it's for, the promise, each feature) — then it **proposes ways to make it better and more ambitious**, as questions *you* decide on. *(Optional, but recommended.)*
- **`/claugentic-dev-harness:audit`** — explain your codebase in plain English and write a **prioritized to-do list**, independently double-checking every item before it reaches your list.
- **`/claugentic-dev-harness:build`** — work that list through a reviewed pipeline — *plan → review → **your approval** → build → verify* — one slice at a time, pausing only for the decisions that are yours.

## Quickstart

Type these in the Claude Code chat (the same place you talk to Claude — not a separate terminal):

```
/plugin marketplace add sh4npeiris/claugentic-dev-harness
/plugin install claugentic-dev-harness@sh4npeiris
/claugentic-dev-harness:init
```

You're set up right away — the enforcement hook activates the moment `init` writes it, and the agent follows the harness workflow from here. *(Tip: a quick `/clear` gives the cleanest slate — worth it before a big `:audit` run.)* From there:

- **New / empty project?** Just tell the agent what you want to build — it asks questions, plans, and gets your approval before writing any code. *(Run `:product` first to pin down the vision.)*
- **Existing codebase?** Run **`:audit`**, then **`:build`** to work the backlog.

> **Commands not showing up** after install? Quit Claude Code fully, delete `plugin-catalog-cache.json` from your config folder (`~/.claude/` — `%USERPROFILE%\.claude\` on Windows; it's just a cache, safe to delete), reopen, and re-run the two install commands.

**Requires** `git` and **Python 3** (for the codebase-map check; without it the agent maintains the map by hand). Public + **Apache-2.0** — install at **user scope** to use it across all your repos.

New to this? Start with **[`docs/claugentic-PLAYBOOK.md`](docs/claugentic-PLAYBOOK.md)** — a plain-English guide for non-engineers.

## Updating

The plugin installs once (globally); each repo gets the docs via `init`. To move to a newer release:

```
/plugin marketplace update sh4npeiris
/plugin update claugentic-dev-harness@sh4npeiris
```

Then re-run **`/claugentic-dev-harness:init`** in each repo — it's version-aware: it refreshes the managed docs to the new version and **never touches your own content** (your spec, roadmap, and edits are left alone). *(Commands not refreshing? See the troubleshooting note above.)*

## Honest about what's real

The harness's whole pitch is honesty, so here's the straight version:

- **Mechanical (a real gate):** the codebase-map check `init` installs — a deterministic, no-LLM hook that blocks "done" until every file is documented. It checks that files are *documented*, **not** that the code is *good*, and it composes with your own linters and tests rather than replacing them.
- **Model-upheld (judgment, not a guarantee):** every review and the audit's double-checks. A skeptical reviewer is a **separate specialist agent with a clean context** — it never sees the builder's reasoning, so it can't rubber-stamp it. A reduction of rubber-stamping risk, **not** independence (it runs the same capable model, so model blind spots aren't independent). The audit *tries to refute* each finding and tags what came back; it never presents judgment as proof.
- **Not built yet:** the mechanical trust-gates that would make a fully-unwatched run safe (a land-gate that blocks a bad commit, a secret-scan). So an unwatched "build-to-green" run is offered only where a repo has earned it (CI, a test baseline, an approved spec) — and otherwise declines honestly, naming what's missing.

## Under the hood *(optional)*

- A **staged workflow** (`docs/claugentic-WORKFLOW.md`): Triage → Discuss → Plan → Review → Spec → **Approve** → Implement → Verify → Land. Small changes skip straight to Implement; only substantial work runs the full pipeline.
- **9 specialist sub-agents** (`.claude/agents/`) — a plan critic, a builder, a **product designer** that also pushes your spec to be more ambitious, per-standard reviewers, an anti-over-engineering skeptic, a finding double-checker, a runtime QA agent, an honesty reviewer, and a retrospective harvester — so the main agent stays focused on your decisions.
- A relevance-loaded **standards catalog** (`docs/claugentic-standards/`, ISO/IEC 25010-anchored), with each finding labeled by how confidently it was checked.

`init` generates a file-by-file map of your repo at `docs/claugentic-ARCHITECTURE_TREE.md`, kept current by the codebase-map check. License: **Apache-2.0**.
