# 0003 — Functional core: make the harness runnable on a real codebase

- **Status:** Draft (**rev 2** — plan-review addressed) — awaiting user approval (Stage 5).
- **Parent:** [`0002`](0002-harness-re-architecture.md) — this is the **"functional for others"** phase (folds 0002's Phases 2/3/5 into one focused sub-plan).
- **References:** `docs/WORKFLOW.md` · `docs/standards/README.md` · `docs/PLAYBOOK.md` · `docs/DECISIONS.md`.

## Problem

Phase 0 gave the harness its **brain** (module contract + 11-module catalog + 6 roles + upgraded workflow + playbook), and the plugin installs (6 agents). But an adopter **can't yet run it on their code** — there's no way to scaffold the harness into a repo, or to audit that repo into a backlog. The gap to "usable by others" is **two skills + packaging.**

## Decisions (locked this session, 2026-06-05)

1. **`/harness-` prefix for all entry points** (discoverability — type `/harness` to see the family). Rename `init-harness` → **`harness-init`**. Family: `harness-init`, `harness-audit` now; `harness-explain`, `harness-update` later.
2. **No separate refactor/execute command.** `harness-audit` writes a backlog to `docs/ROADMAP.md`; the user picks items and the **existing pipeline** implements each. Each item is **tagged by type** (*refactor · capability-upgrade · dependency-health · bug · feature*) and the tag selects the discipline. **Safety on the highest-risk path is a hard precondition, not prose** (RC-2): a `refactor`-tagged item on untested behavior-bearing code **cannot start until its Tier-1 "establish a test baseline" item is done** — the implementer **stops and asks** otherwise. The durable enforcement is the Trust-track `PreToolUse` characterization hook, pulled forward as the **first Trust-track item** right after this phase.
3. **The audit teaches, not just lists.** Output for a non-engineer: a plain-English **"what your app is & does"** summary + a **tiered, tagged, plain-English** backlog (impact · rough effort · type) + a **recommended starting point**.
4. **Copy the standards into the adopter repo on init; re-sync on update** *(reverses 0002 Decision 10 — verified RC-1 resolution).* Official docs confirm a plugin's **subagents can't read bundled files via bare paths** in an adopter repo (they resolve to the project root), and `${CLAUDE_PLUGIN_ROOT}` doesn't cover the **parameterized** `lens-reviewer`. So the catalog is **bundled in the plugin (source of truth)** and `harness-init` **copies** it into the adopter's `docs/standards/` (version-stamped, headed "managed — do not edit"); agents read it locally **unchanged**; `/harness-update` re-copies newer versions (the proven Agent-OS pattern). The **two-tier model holds**: global = copied+managed+stamped; local = Current-scope / CANDIDATES / lessons (never overwritten). *(Carried: init composes with existing tooling; tree-check stays Python; init sets `INCLUDE_GLOBS`.)*

## Goals / Non-goals

**Goals:** package the enriched harness as installable **skills**; **`harness-init`** (idempotent scaffold); **`harness-audit`** (bounded multi-lens sweep → understand summary + tiered tagged backlog); dogfood end-to-end (this repo → throwaway → the user's JS app).

**Non-goals:** a refactor/execute command (the pipeline handles execution); the full deterministic trust-gate suite (later); capability modules (JIT); any mass/automatic change to a codebase.

## The two skills + the execution model

### `harness-init` — one-time scaffold (idempotent)
Into the adopter's repo, **without clobbering anything** (detect → skip/merge → report what it did; re-running is a safe no-op):
- **Copy the standards catalog** into the repo's `docs/standards/` (version-stamped; each module headed "managed by agentic-dev-harness — do not edit; run `/harness-update` to refresh"). Add a **CLAUDE.md harness section** (or create a lean one) pointing at the workflow + the **local** `docs/standards/` — the *same path the agents read* (RC-5).
- **Generate `docs/ARCHITECTURE_TREE.md`** by walking the repo (one line per in-scope source file).
- **Detect the source layout → set the tree-check `INCLUDE_GLOBS`**; wire the tree-check hook (Python — harness tooling).
- **`git init`** if absent; create `docs/ROADMAP.md` / `docs/DECISIONS.md` / the per-repo **Current-scope** if absent.
- **Detect + compose with existing tooling** (eslint / tsc / test runner) — reuse them as the project's gates rather than imposing new ones.

### `harness-audit` — find the work (repeatable)
A bounded, multi-lens, multi-modal sweep:
- **Understand first (→ S2a)** — derive a cheap map (structure, entry points, dependencies) → a plain-English **"what your app is & does"** summary (optionally a C4-style diagram), **plus an exclude-set** (`node_modules`, `dist`/`build`/`.next`/`out`, `vendor`, generated code, lockfiles, `.git`) **and a prioritized directory order**; handle monorepo package boundaries.
- **Audit (→ S2b)** — fan out `lens-reviewer`s (one per relevant `docs/standards/` module) over the *included* code, **dedup**, **loop-until-dry** — but **budget-bounded with explicit exhaustion behavior**: on budget exhaustion, write a **partial, honestly-labeled** backlog and **record where it stopped so a re-run resumes** (re-runnable means *resumable*, not restart-from-zero).
- **Backlog** — write a prioritized, **tiered** (Tier 1 critical → Tier 3 polish), **tagged** (refactor / capability-upgrade / dependency-health / bug / feature) backlog to `docs/ROADMAP.md`; each item **dual-layer** (technical + plain-English what/why/how-bad) with **impact + rough effort**. Untested behavior-bearing code → **"establish a test baseline" is Tier-1 item #1.** End with a **recommended starting point**.
- Re-runnable to refresh as the code evolves.

### Execution = the existing pipeline (no new command)
The user picks a backlog item; the agent runs **Discuss → Plan → Review → Spec → Approve → Implement → Verify → Land**. The item's **tag** selects the discipline: *refactor* → **characterization-tests-first, enforced as a hard precondition** (can't start until its test-baseline item is done; the implementer stops and asks otherwise — Decision 2); *capability-upgrade* → migration safety (flag / dual-write / rollback); *dependency-health* → update + verify. A `WORKFLOW.md` note documents the mapping; the **durable** characterization enforcement is the Trust-track `PreToolUse` hook (first Trust-track item, next phase).

## Packaging (folds 0002 Phase 2)
Expose `harness-init` + `harness-audit` as **skills** (`skills/<name>/SKILL.md`) in `.claude-plugin/plugin.json`; the plugin bundles the catalog + workflow + playbook (read via `${CLAUDE_PLUGIN_ROOT}`); validate with `claude plugin validate`; the marketplace entry already exists.

## Decomposition (slices) — each lands complete in one session

- [ ] **S1 — Package as skills (honest stubs).** Add `skills/harness-init/SKILL.md` + `skills/harness-audit/SKILL.md` as **deliberate honest no-ops** (each says "not yet implemented — see plan 0003 S2/S3") wired into the manifest; confirm the plugin **bundles** the catalog + workflow + playbook as resources `harness-init` will copy. *No agent changes needed* (copy-on-init → agents keep reading local `docs/standards/`). *Lands:* `claude plugin validate` passes; `/harness-init`/`/harness-audit` are discoverable and print their honest "coming soon" message.
- [ ] **S2a — `understand`.** Derive the repo map + the **exclude-set + prioritized directory order** (+ monorepo handling); produce the plain-English "what your app is & does" summary. *Lands:* run on this repo → a sensible summary + a derived map/exclude-set.
- [ ] **S2b — `audit` + backlog.** The bounded multi-lens sweep consuming S2a's map (dedup, loop-until-dry, **resumable budget-exhaustion**) → a **tiered, tagged, dual-layer** backlog (impact · effort · recommended start; "establish a test baseline" = Tier-1 #1 for untested code) in `docs/ROADMAP.md`. *Lands:* run on this repo → a real, sensible backlog (an audit of the harness itself).
- [ ] **S3 — `harness-init` skill.** Idempotent scaffold: **copy the version-stamped catalog**, generate `ARCHITECTURE_TREE`, set `INCLUDE_GLOBS`, write the CLAUDE pointer (→ local `docs/standards/`), `git init` if absent, **compose with existing tooling**; never clobber (detect→skip/merge→report). *Lands:* running it twice on a sample repo is a safe no-op the 2nd time and reports what it did/skipped.
- [ ] **S4 — `WORKFLOW.md` tag→discipline + characterization precondition.** Document the tag→discipline mapping **and** the hard precondition (a refactor item is blocked until its test-baseline item is done); record the Trust-track hook as the durable enforcement (first Trust-track item). Source-of-truth process edit → re-review when spec'd.
- [ ] **S5 — Package & dogfood.** Install into a **throwaway repo**; `/harness-init` → `/harness-audit` end-to-end. **Named RC-1 acceptance: in the throwaway, a reviewer agent actually reads a *copied* standards module** (proves copy-on-init works — *this* repo can't surface the bug because it has the modules natively). Then (final) the **user's JS app**: audit reproduces its known issues; one item runs the pipeline to land. Refresh `README.md` + `ROADMAP.md`.

## Risks & mitigations
- **Adopter agents can't read bundled standards (RC-1)** → **copy on init** (version-stamped, managed) so agents read locally unchanged; `/harness-update` re-syncs. The throwaway-repo dogfood (S5) is the named test that this works.
- **Audit blows budget on a big repo (RC-4)** → S2a emits an exclude-set (`node_modules`/`dist`/vendored/generated) + directory order; S2b is budget-bounded with **resumable** exhaustion (partial, labeled, records where it stopped). Fan out to subagents.
- **Refactoring untested code (RC-2)** → characterization-tests-first is a **hard precondition** (can't start a refactor item until its test-baseline item is done; implementer stops and asks); durable enforcement = the Trust-track `PreToolUse` hook (first Trust-track item).
- **Standards drift across repos** → copied modules are version-stamped + "managed, do not edit"; `/harness-update` overwrites with newer; local artifacts untouched.
- **`harness-init` clobbers files** → idempotency is a hard gate: detect → skip/merge → report; re-run safe.
- **Tree-check runtime missing** → Python broadly available; init verifies it; agent can fall back to `Glob`.
- **Audit findings are model-asserted** → tier/tag honestly, surface "verified-vs-asserted"; deep modules are the bar; deterministic trust-gates (later) add teeth.

## Test & dogfood strategy
- **Dogfood `harness-audit` on THIS repo first** (already scaffolded) → a sensible backlog (and a real audit of the harness).
- **`harness-init` on a throwaway sample** → idempotent, composes with existing tooling.
- **Cold install** into a throwaway repo → `/harness-init` → `/harness-audit` end-to-end.
- **Final:** the **user's JS app** → audit reproduces its known issues; pick one item → pipeline lands it, gates green.

---

## Review  _(filled by plan-reviewer, Stage 3 — 2026-06-05)_

**Verdict: CHANGES REQUIRED.** The shape is right — "2 skills + execution-via-pipeline" is the correct YAGNI call, dropping a bespoke `refactor-item` command is sound (the pipeline already carries the discipline), and dogfooding `harness-audit` on this scaffolded repo before building `harness-init` is good sequencing. But the plan has **one load-bearing correctness hole** (referenced globals are unreadable by the agents that must read them — RC-1), **one regression against a locked decision** (characterization-first downgraded from a hook to prose on the highest-risk path — RC-2), and **S2 is oversized** (RC-3). Fix these and the bounding/harness gaps below, then re-review. Most are plan-text + one agent-prompt slice, not a redesign.

### Required changes

1. **RC-1 — "reference globals via `${CLAUDE_PLUGIN_ROOT}`" is incomplete; the agents can't read them. (Correctness, load-bearing.)** Every reviewer agent reads the catalog at the **bare relative path** `docs/standards/...` — `architect-reviewer.md:12`, `lens-reviewer.md:8,10`, `product-designer.md:10` — and `implementer-architect.md:10` reads `docs/ENGINEERING_STANDARDS.md` the same way. In an adopter repo those resolve to `${CLAUDE_PROJECT_DIR}/docs/standards/`, which the reference-don't-copy decision **guarantees does not exist**. `${CLAUDE_PLUGIN_ROOT}` appears only in the standards docs and the manifest narrative — never in the agents that do the reading. So as written, in any repo other than this one, the reviewers read **nothing** and silently pass. The plan asserts "the plugin delivers the catalog (referenced)" (S1, line 49; Packaging, line 45) but **never lists updating the agents to read via the plugin root.** Add an explicit slice (or fold into S1): update `architect-reviewer`, `lens-reviewer`, `product-designer`, `implementer-architect` to read standards via `${CLAUDE_PLUGIN_ROOT}/docs/standards/` (with a "fall back to repo-local if running inside the harness's own repo" note, since this repo *is* the plugin). Verify the variable actually expands inside an agent/subagent prompt context (the 0002 spike verified it for skills/hooks — confirm for agents too; if it does not expand in agent bodies, `harness-init` must write the resolved path into the adopter's CLAUDE.md and the agents must read *that*). **Until this is proven, "referenced globals" is not functional and the whole audit/review path is a no-op for adopters.**

2. **RC-2 — characterization-tests-first needs more than a prose note on untested code. (Tech-debt / regression against a locked decision.)** Decision 2 (line 14) + S4 (line 52) make characterization-first "a *standard*, not a command," enforced only by a `WORKFLOW.md` sentence. But 0002's Trust track **already decided this exact path needs teeth**: a `PreToolUse` hook that **blocks edits to untested/baseline files without a token** (`0002:62`). Prose was explicitly judged insufficient *here*, for *this* behavior. The plan defers all Trust gates (Non-goals, line 22) yet leans on prose to guarantee the single most dangerous operation — an LLM mutating behavior-bearing code that has **no test to catch a regression**. That is a step backward from a locked decision on the highest-risk path. Resolve one of two ways and record it: **(a)** pull the minimal `PreToolUse` "no edit to untested behavior-bearing file without a characterization test first" gate forward into this phase (it is the one Trust gate the execution model structurally depends on), **or (b)** explicitly scope `harness-audit`/the pipeline to **refuse to start a `refactor`-tagged item until the audit's "establish a test baseline" Tier-1 item is done first**, making the ordering a hard precondition rather than a hope. A `WORKFLOW.md` note alone does not satisfy the Stage-3 "no new tech debt / fail loudly" bar for a safety-critical path.

3. **RC-3 — split S2.** As written S2 bundles three distinct design surfaces that 0002 itself treated as **separate organs** (`0002:74-75`, and Phase 3 vs the roadmap): **(i) understand** (derive structure/entry-points/deps map → plain-English "what your app is & does" summary + optional C4); **(ii) the bounded multi-lens sweep** (fan out `lens-reviewer`s, dedup, loop-until-dry, budget/dir bounding); **(iii) backlog authoring** (tiered + tagged + dual-layer + impact/effort + recommended start, written to ROADMAP). Each is a session's worth of design and prompt-engineering, and (i) is the natural producer of the exclude-set/budget that (ii) consumes. Split into **S2a — understand** (lands: a plain-English summary + a derived map/exclude-set on this repo) and **S2b — audit + backlog** (lands: the sweep consumes S2a's map and writes the tiered tagged backlog). This also lets (i) ship value alone and de-risks (ii)'s bounding (see RC-4).

4. **RC-4 — close the audit bounding gaps; the bounds as stated are under-specified and internally tense.** "Bounded by budget + directory" + "loop-until-dry" pull against each other: on a large repo loop-until-dry will hit the budget *before* dry, and the plan never says what happens then (partial backlog? resume token? which directories were skipped?). It also has **no exclude-set** for the things that will dominate a real JS repo: `node_modules`, `dist`/`build`/`.next`/`out`, `vendor`, generated code, lockfiles, and **monorepo** package boundaries. Specify: (a) the understand step (S2a) emits the exclude-set + a prioritized directory order; (b) define budget-exhaustion behavior explicitly (write a partial, honestly-labeled backlog + record where it stopped so a re-run resumes — "re-runnable" must mean *resumable*, not *restart-from-zero*); (c) name the monorepo/generated/vendored handling. Without these the audit either blows context or silently under-covers and the user can't tell which.

5. **RC-5 — `harness-init`'s CLAUDE.md pointer must agree with the agents' read path (depends on RC-1).** Line 28 has init write a CLAUDE.md "pointing at standards via `${CLAUDE_PLUGIN_ROOT}`." A static pointer in CLAUDE.md does **not** redirect an agent that has its own hardcoded `docs/standards/` read instruction. State that the pointer init writes and the path the agents read **are the same resolved location**, and that init's job is only to (optionally) materialize the resolved plugin-root path if the variable doesn't expand in agent context. Otherwise init looks like it wires standards in while the agents still read a non-existent local dir.

6. **RC-6 — make S1's stub window explicit and honest.** S1 ships skill **stubs** wired into the manifest (acceptance: "discoverable as `/harness-init`, `/harness-audit`") while S2/S3 author the bodies. That is fine, but as written it creates a window where `/harness-audit` is discoverable yet does nothing. State that S1's stubs are **deliberate honest no-ops** (e.g. each SKILL.md says "not yet implemented — see plan 0003 S2/S3") so a user who types the command during the window gets a clear message, not silence. (Marketplace claim checks out — `marketplace.json:6-13` already lists the plugin; "the marketplace entry already exists" is accurate.)

### Sizing / completeness check (per slice)
- **S1 — Package as skills — OK** once RC-1 (agent read-path fix) is added here or as its own slice, and RC-6 (honest stubs) is noted. Lands complete.
- **S2 — `harness-audit` — SPLIT (RC-3)** → **S2a understand** + **S2b audit+backlog**. As one slice it is three deliverables and will not land vertically complete in one session.
- **S3 — `harness-init` — OK** (well-bounded: detect→skip/merge→report, idempotent, compose-with-tooling, git-init). The idempotency-as-hard-gate framing is sound. Tighten only via RC-5 (pointer ↔ read-path coherence).
- **S4 — `WORKFLOW.md` tag→discipline note — OK as a doc slice, but insufficient as the *enforcement* of characterization-first (RC-2).** Keep the note; do not let it be the *only* mechanism.
- **S5 — Package & dogfood — OK**, but add an explicit acceptance that the **referenced-globals path works in the throwaway repo** (a reviewer agent, run in the throwaway, actually reads a module via the plugin root) — this is the concrete test that RC-1 is fixed. Right now S5 would "pass" even with RC-1 unfixed because dogfooding *this* repo has the modules locally; the throwaway/JS-app run is the only place the bug surfaces, so make it a named check.

### Harness impact (Stage 9 — under-declared in the plan; add these)
- **Agent prompts change (RC-1):** updating four agents to read globals via `${CLAUDE_PLUGIN_ROOT}` is a **convention worth promoting to a STANDARD / CLAUDE.md line** — "agents/skills read global standards via the plugin root, never a bare repo-local path." Name it; it will recur for every future agent.
- **New artifact type:** `skills/*/SKILL.md` is a new tree category — add a `## skills/` section to `ARCHITECTURE_TREE.md` (the Python tree-gate won't catch markdown; do it by hand, per 0002's standing note).
- **`WORKFLOW.md` tag→discipline mapping (S4)** is a process source-of-truth edit — flag for re-review when spec'd, and decide RC-2's enforcement there.
- **Possible new gate (RC-2 option a):** if you pull the `PreToolUse` characterization-first block forward, that is the first Trust-track hook landing early — record the scope-pull in DECISIONS so Phase 1 doesn't double-build it.

---

## Resolution  _(orchestrator, rev 2 — all findings addressed)_

- **RC-1 (load-bearing) → resolved by reversing Decision 10 to COPY-on-init** (user-confirmed; official-docs-verified that bundled files aren't readable by subagents via bare paths, and `${CLAUDE_PLUGIN_ROOT}` doesn't cover the parameterized `lens-reviewer`). Agents stay **unchanged**; `harness-init` copies the version-stamped catalog; `/harness-update` re-syncs. S5 adds the named throwaway-repo test that a reviewer agent reads a *copied* module. *(Cleaner than the reviewer's suggested agent-prompt rewrite — no agent changes, no runtime path magic.)*
- **RC-2 → characterization-first is a hard precondition + a fast-follow hook**, not prose (Decision 2 + Execution + S4): a refactor item can't start until its test-baseline item is done (implementer stops and asks); the durable `PreToolUse` hook is pulled forward as the **first Trust-track item** (recorded in DECISIONS so Phase 1 doesn't double-build it).
- **RC-3 → S2 split** into **S2a** (understand) + **S2b** (audit + backlog).
- **RC-4 → audit bounding closed:** S2a emits the exclude-set + directory order + monorepo handling; S2b has explicit **resumable** budget-exhaustion.
- **RC-5 → pointer = read-path:** init writes the CLAUDE pointer at the **local** `docs/standards/` the agents already read (copy-on-init makes them the same place).
- **RC-6 → honest stubs:** S1's skills are explicit no-ops ("not yet implemented").
- **Harness impacts declared:** the copy-on-init decision (supersedes 0002 Decision 10 — in DECISIONS); a new `## skills/` ARCHITECTURE_TREE section (S1); the WORKFLOW process edit (S4, re-reviewed); the characterization-hook scope-pull (first Trust-track item).

---

## Spec  _(per slice, after Review passes — Stage 4)_
Spec'd per slice at its own approval gate, starting with **S1**.
