# claugentic-dev-harness

A Claude Code plugin that turns AI coding into a **disciplined, reviewable process**: it plans before it builds, reviews its own work against a written standards catalog, keeps an always-current map of your codebase, and **never changes your code without your sign-off.**

You steer with plain-English decisions; it does the engineering one reviewed slice at a time — and it's **honest about the difference between what it checked mechanically and what's its own judgment.**

## The four commands

- **`/claugentic-dev-harness:init`** — set it up in your repo. Adds a codebase map, a quality-standards catalog, and the workflow docs. Never overwrites your content; re-run any time to re-converge. *(To move to a newer harness release it's two steps: `/plugin update claugentic-dev-harness@sh4npeiris` to fetch it, then re-run `:init` to converge your managed docs — `:init` alone never fetches a new version.)*
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

> **For teammates who haven't installed the plugin:** the committed codebase-map hook (in `.claude/settings.json`) runs even if you never installed the harness, and it needs **Python 3**. If your agent reports the hook failed, either install Python 3 or skip it locally by overriding that hook in `.claude/settings.local.json` (gitignored — yours only). The hook is intentionally loud rather than silent so a missing map is never overlooked.

> **Removing or pausing the harness:** to silence the codebase-map gate, remove its two entries from `.claude/settings.json` (the `PostToolUse` Write hook and the `Stop` hook). The managed docs (`docs/claugentic-*`) are plain files — delete the ones you don't want. The plugin itself uninstalls the standard way: `/plugin uninstall claugentic-dev-harness@sh4npeiris`.

**Requires** `git` and **Python 3** (for the codebase-map check; without it the agent maintains the map by hand). Public + **Apache-2.0** — install at **user scope** to use it across all your repos.

**Two-layer install:** you install the *plugin* at user scope for yourself (it never lives in your repo). `init` then commits a lightweight **pointer** (a `.claude/settings.json` entry) so a teammate who clones the repo is prompted to install the plugin too — the tracked file is the pointer, never the plugin code, so the new `.claude/settings.json` change in your first commit isn't a surprise.

New to this? Start with **[`docs/claugentic-PLAYBOOK.md`](docs/claugentic-PLAYBOOK.md)** — a plain-English guide for non-engineers.

## Honest about what's real

The harness's whole pitch is honesty, so here's the straight version:

- **Mechanical (a real gate):** the codebase-map check `init` installs — a deterministic, no-LLM hook that blocks "done" until every file is documented. It checks that files are *documented*, **not** that the code is *good*, and it composes with your own linters and tests rather than replacing them.
- **Model-upheld (judgment, not a guarantee):** every review and the audit's double-checks. A skeptical reviewer runs by default on a **different Claude model family** than the builder — a reduction of shared-blind-spot risk, **not** independence (same vendor, so errors can still correlate). The audit *tries to refute* each finding and tags what came back; it never presents judgment as proof.
- **Not built yet:** the mechanical trust-gates that would make a fully-unwatched run safe (a land-gate that blocks a bad commit, a secret-scan). So an unwatched "build-to-green" run is offered only where a repo has earned it (CI, a test baseline, an approved spec) — and otherwise declines honestly, naming what's missing.
- **How the scripted parts run:** the audit, review-panel, and build engines run as scripts via Claude Code's **Workflow tool**. Where that tool isn't available in a session, the harness falls back to an **honestly-tagged prose run** (`"prose-orchestrated"`) — the same steps driven by the agent rather than the script: weaker, model-upheld, not a mechanical guarantee — and it always says which path it took.

## Under the hood *(optional)*

- A **staged workflow** (`docs/claugentic-WORKFLOW.md`): Triage → Discuss → Plan → Review → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small changes skip straight to Implement; only substantial work runs the full pipeline.
- **10 specialist sub-agents** (`.claude/agents/`) — a plan critic, a builder, a verifier, a product designer, a **product critic** that pushes your spec to be more ambitious, per-standard reviewers, an anti-over-engineering skeptic, and an honesty reviewer — so the main agent stays focused on your decisions.
- A relevance-loaded **standards catalog** (`docs/claugentic-standards/`, ISO/IEC 25010-anchored), with each finding labeled by how confidently it was checked.

Full file-by-file map: **[`docs/claugentic-ARCHITECTURE_TREE.md`](docs/claugentic-ARCHITECTURE_TREE.md)**. License: **Apache-2.0**.
