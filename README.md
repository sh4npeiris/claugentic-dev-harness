# claugentic-dev-harness

A Claude Code plugin that makes AI-assisted coding **disciplined and reviewable**. It installs into any repo, **never touches your code without asking**, and gives your agent an always-current map of the codebase plus a skeptical second reviewer that knows what "good" looks like.

**Two commands:**

- **`/claugentic-dev-harness:init`** — scaffold the harness into your repo. Idempotent and **never clobbers** your files (re-running is a safe no-op): it adds an always-current architecture index + an enforcement hook, a quality-standards catalog, and the workflow docs — and **composes with your existing linters/tests** instead of replacing them.
- **`/claugentic-dev-harness:audit`** — point it at the repo and it explains, in plain English, what your app is and does, then writes a **prioritized to-do list** (a backlog) of the work worth doing. It **auto-sizes its effort to the codebase** and tells you plainly when the code is already sound.

## What you actually get

- **An enforced, always-current map of your codebase.** One line per file in `docs/ARCHITECTURE_TREE.md`, so your agent reads the index instead of re-walking the tree every session — and a deterministic (no-LLM) hook **blocks "done" until the index is current.** This is the part that's mechanical, not a prompt.
- **A quality bar that scopes itself.** A standards catalog (security, testing, maintainability, accessibility, …) that **only loads the parts your change actually touches** — a checklist, not a set of hoops to jump. An independent agent reviews the work against it and tries to *refute* it, because the model that wrote something is the worst judge of it.
- **Plain-English output for a non-engineer driver.** Every finding is stated technically *and* in plain language; you steer with product decisions, not code. (New to this? Start with [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md).)
- **Honesty by default.** `init` never overwrites your content; the audit **labels what it actually checked vs. what's the model's judgment**; execution happens one reviewed slice at a time.

## Status — v0.1.1 (honest about what's real)

The functional core is **live and proven**: both skills work, and the **cold install is verified** — a real adopter installed the plugin and ran `init` → `audit` against their own repo successfully. The harness also **dogfoods itself** (it was built using its own workflow).

**Not built yet** (and the docs say so wherever it's mentioned): the deterministic **trust-gates** — an independent verification track that would make the review *mechanical* rather than a disciplined prompt — plus `…:update` (re-sync managed copies) and `…:explain` (teach-as-you-go). Today the review discipline is upheld by an independent skeptical agent + the architecture-tree gate; the heavier deterministic gates are the top of the [roadmap](docs/ROADMAP.md). The harness's whole pitch is honesty, so it states only what's real.

## Install

```
/plugin marketplace add sh4npeiris/claugentic-dev-harness
/plugin install claugentic-dev-harness@sh4npeiris
```

Public + **Apache-2.0** — free to install and use. Install at **user scope** to use it across all your repos.

## How it works

1. **`init`** scaffolds the managed harness into your repo.
2. **`audit`** explains the codebase + writes a tiered, tagged backlog into `docs/ROADMAP.md` (for untested behavior-bearing code, "establish a test baseline" comes first).
3. **You pick an item; the staged workflow lands it** — one reviewed slice at a time. The item's **tag selects the discipline** (a `refactor` on untested code is gated behind a characterization-test baseline first).

Works the same for a **mature codebase** (audit → incremental backlog) and a **new project** (the workflow governs from the first feature; the index + standards apply from day one).

## Under the hood (here when you want it)

You don't need any of this to use the two commands — it's the machinery they run on:

- **Staged workflow** (`docs/WORKFLOW.md`) — Triage → Discuss → Plan → Review → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small changes skip straight to Implement + Verify; only substantial work runs the full pipeline.
- **6 specialist agents** (`.claude/agents/`) — a plan critic, a builder, a verifier, a product/UX lens, a per-standard lens reviewer, and an anti-over-engineering skeptic. The orchestrator delegates to them so your attention stays on decisions.
- **The standards catalog** (`docs/standards/`) — ISO/IEC 25010-anchored, loaded by relevance, with each finding labeled by how confidently it was checked.

## License & layout

Apache-2.0. See **`docs/ARCHITECTURE_TREE.md`** for the one-line-per-file index of the whole repo.
