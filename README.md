# claugentic-dev-harness

A Claude Code plugin that makes AI-assisted coding **disciplined and reviewable**. It installs into any repo, **never touches your code without asking**, and gives your agent an always-current map of the codebase plus a skeptical second reviewer that reviews against a written, ISO/IEC 25010-anchored catalog of what good looks like.

**Two commands:**

- **`/claugentic-dev-harness:init`** — scaffold the harness into your repo. Idempotent and **never clobbers** your files (re-running is a safe no-op): it adds an always-current architecture index + an enforcement hook, a quality-standards catalog, and the workflow docs — and **composes with your existing linters/tests** instead of replacing them.
- **`/claugentic-dev-harness:audit`** — point it at the repo and it explains, in plain English, what your app is and does, then writes a **prioritized to-do list** (a backlog) of the work worth doing. It **auto-sizes its effort to the codebase**, tells you plainly when the code is already sound, and **independently verifies its most serious findings** — a separate agent reads the cited code and tries to *disprove* each security/correctness item before it reaches your list (false alarms get dropped; the rest carry their proof).

## What you actually get

- **An enforced, always-current map of your codebase.** One line per file in `docs/ARCHITECTURE_TREE.md`, so your agent reads the index instead of re-walking the tree every session — and a deterministic (no-LLM) hook **blocks "done" until the index is current.** It checks that every file is **documented** (present, not deleted) — **not that the code is good**, and the one-line descriptions themselves are authored, not gate-verified. This is the part that's mechanical, not a prompt.
- **A quality bar that scopes itself.** A standards catalog (security, testing, maintainability, accessibility, …) that **only loads the parts your change actually touches** — a checklist, not a set of hoops to jump. An independent agent reviews the work against it and tries to *refute* it, because the model that wrote something is the worst judge of it.
- **Plain-English output for a non-engineer driver.** Every finding is stated technically *and* in plain language; you steer with product decisions, not code. (New to this? Start with [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md).)
- **Honesty by default.** `init` never overwrites your content; the audit **labels what it actually checked vs. what's the model's judgment**; execution happens one reviewed slice at a time.

## Status (honest about what's real)

The functional core is **live**: both `init` and `audit` work, and `init` installs cleanly into a fresh repo. The audit **independently verifies its Tier-1 + security findings** — a separate agent tries to refute each one against the code, so false positives are dropped and the rest arrive with proof.

That finding-verification is an honest *reduction* of false confidence, **not** a deterministic guarantee (it's the same model class, run independently and adversarially). The genuinely **mechanical, model-independent trust-gates** — a characterization-tests-first hook + a secret-scan — are **not built yet** — they're the top of the [roadmap](docs/ROADMAP.md). Today the review discipline is upheld by independent skeptical agents + the deterministic architecture-tree gate. The harness's whole pitch is honesty, so it states only what's real.

## Install

Type these in the Claude Code chat input — the same place you talk to Claude (not a separate terminal):

```
/plugin marketplace add sh4npeiris/claugentic-dev-harness
/plugin install claugentic-dev-harness@sh4npeiris
```

**Success check:** type `/claugentic` and you should see `:init` and `:audit` offered — that's it installed.

Public + **Apache-2.0** — free to install and use. Install at **user scope** to use it across all your repos.

**Requires:** `git`, and `Python 3` (for the architecture-tree gate; without it the gate is skipped and the agent maintains the index manually).

**If the install doesn't show up** (the plugin list looks empty, or `init` / `audit` aren't found right after you add the marketplace) — Claude Code is usually holding a stale plugin cache. The marketplace and plugin themselves are fine; you just need to rebuild the local index:

1. **Quit Claude Code completely** (not just the window).
2. **Delete the `plugin-catalog-cache.json` file** from your Claude Code config folder (`~/.claude/` on macOS/Linux; on Windows it's at `%USERPROFILE%\.claude\plugin-catalog-cache.json` — search your home folder for that filename if you're unsure where it lives). **This file is just a cache; deleting it is safe — Claude Code rebuilds it on restart.**
3. **Reopen Claude Code** and run the two install commands above again.

## Quickstart

In order:

1. **`/claugentic-dev-harness:init`** — scaffolds the harness into your repo (safe — never overwrites; you'll see a created/skipped/merged summary).
2. **Start a fresh chat after `init`** so the agent picks up the new setup.
3. **Then, depending on your repo:**
   - **Already have code? → `/claugentic-dev-harness:audit`** — explains the codebase in plain English + writes a prioritized backlog into `docs/ROADMAP.md` (a large repo may finish in passes and say "re-run to continue" — that's expected).
   - **Brand-new / empty repo? → skip the audit.** Just tell the agent what you want to build — describe your first feature in plain English and it runs the workflow from there.

New to this? Read [`docs/PLAYBOOK.md`](docs/PLAYBOOK.md).

## How it works

1. **`init`** scaffolds the managed harness into your repo.
2. **`audit`** explains the codebase + writes a tiered, tagged backlog into `docs/ROADMAP.md` (for untested behavior-bearing code, "establish a test baseline" comes first).
3. **You pick an item; the staged workflow lands it** — one reviewed slice at a time. The item's **tag selects the discipline** (a `refactor` on untested code is gated behind a characterization-test baseline first).

**To start anything — a backlog item or a brand-new project — just tell the agent in plain English what you want** (e.g. "Let's do Tier-1 item 1" or "I want to build X"). It will ask you questions (Discuss), then write a plan and spec for you to approve before any code.

Works the same for a **mature codebase** (audit → incremental backlog) and a **new project** (the workflow governs from the first feature; the index + standards apply from day one).

## Under the hood (here when you want it)

You don't need any of this to use the two commands — it's the machinery they run on:

- **Staged workflow** (`docs/WORKFLOW.md`) — Triage → Discuss → Plan → Review → Spec → **Approve** → Implement → Verify → Land → Retrospect. Small changes skip straight to Implement + Verify; only substantial work runs the full pipeline.
- **7 specialist agents** (`.claude/agents/`) — a plan critic, a builder, a verifier, a product/UX lens, a per-standard lens reviewer, an anti-over-engineering skeptic, and a finding-verifier that refutes audit findings against the code. The orchestrator delegates to them so your attention stays on decisions.
- **The standards catalog** (`docs/standards/`) — ISO/IEC 25010-anchored, loaded by relevance, with each finding labeled by how confidently it was checked.

## License & layout

Apache-2.0. See **`docs/ARCHITECTURE_TREE.md`** for the one-line-per-file index of the whole repo.
