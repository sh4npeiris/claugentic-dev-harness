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
- **Copy the full managed harness set** the agents + user read — `docs/standards/` **+ `docs/WORKFLOW.md` + `docs/PLAYBOOK.md` + `scripts/check_architecture_tree.py`** — into the repo (version-stamped; headed "managed by agentic-dev-harness — do not edit; run `/harness-update` to refresh"). By RC-1, *anything an agent reads at a bare path must be local*, so it is **not just the standards**. Add a **CLAUDE.md harness section** pointing at these local files (the *same paths the agents read* — RC-5). **`/harness-update` (later) re-syncs the whole set** — the plugin's own agents/skills/hooks update separately via `/plugin`. Evolving this source repo is the **global tier of the learning loop**: improvements reach every adopter on their next update.
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

- [x] **S1 — Package as skills (honest stubs).** ✅ *(landed 2026-06-05)* Add `skills/harness-init/SKILL.md` + `skills/harness-audit/SKILL.md` as **deliberate honest no-ops** (each says "not yet implemented — see plan 0003 S2/S3") wired into the manifest; confirm the plugin **bundles** the catalog + workflow + playbook as resources `harness-init` will copy. *No agent changes needed* (copy-on-init → agents keep reading local `docs/standards/`). *Lands:* `claude plugin validate` passes; `/harness-init`/`/harness-audit` are discoverable and print their honest "coming soon" message.
- [x] **S2a — `understand`.** ✅ *(landed 2026-06-05)* Derive the repo map + the **exclude-set + prioritized directory order** (+ monorepo handling); produce the plain-English "what your app is & does" summary. *Lands:* run on this repo → a sensible summary + a derived map/exclude-set.
- [x] **S2b-i — `audit` engine (authoring).** ✅ *(landed 2026-06-05)* Author Phase 2 of the skill (the audit procedure: dial-parse, `(module × dir)` cells, fan-out, dedup, loop-until-dry, **deterministic resumable budget**), the backlog fence + status block, and the **`lens-reviewer` dual-use role-contract** (Verify-diff **or** audit-scope). Apply the S2a count-guard; **cut `thorough`** (→ ROADMAP LATER). *No fan-out run.* *Lands:* the engine text is coherent + self-consistent; gates green.
- [x] **S2b-ii — dogfood audit (execution).** ✅ *(landed 2026-06-05)* The **orchestrator** runs the engine on THIS repo (`lens-reviewer` fan-out), synthesizes, writes the real **tiered/tagged/dual-layer** backlog into the fence ("establish a test baseline" = Tier-1 #1 for the untested gate), **archives the stale B1–B6**, preserves `## Later`. *Lands:* a real, sensible, non-hallucinated backlog (an audit of the harness itself).
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

### S2b Spec — Review  _(plan-reviewer, Stage 3 for slice S2b — 2026-06-05)_

> Reviews the **`### S2b Spec — audit + backlog`** subsection only. Settled rev-2 calls (copy-on-init, characterization-precondition, S2-split) are not re-litigated.

**Verdict: CHANGES REQUIRED.** The shape is right and lean: reusing `lens-reviewer` instead of a new agent is correct DRY; co-locating resume-state in the ROADMAP fence (no new file) is consistent with S2a; "delegation primary, resume backstop" is the right budget model; and dogfooding on this repo is the correct proof. But there are **three load-bearing holes** — (1) the `lens-reviewer` dual-use note is under-specified for the very mode it enables (the role is 100% diff-centric today and audit mode silently breaks), (2) the resume mechanism is hand-wavy on *what gets recorded* and *what triggers a stop* (an LLM "sensing context filling" is not a reliable signal), and (3) **the slice is oversized** — it bundles authoring + a real multi-agent dogfood fan-out + stale-ROADMAP reconciliation into one session. Plus YAGNI on the 3-level dial and several completeness gaps below.

#### Required changes (prioritized)

1. **Split S2b — the dogfood fan-out cannot share a session with authoring (sizing, load-bearing).** S2b bundles five distinct deliverables: author the Phase-2 procedure, author the `lens-reviewer` dual-use note, **run the live multi-`lens-reviewer` fan-out over this repo**, dedup/synthesize the digests, author the backlog, and reconcile/archive the stale B1–B6 ROADMAP. The spec's own *implementation-execution note* (line 216) concedes the fan-out **can't run inside the implementer subagent** (subagents can't spawn subagents) — so it must be driven by the **top orchestrator**, which is a *different actor* from the `implementer-architect` that authors the SKILL/agent/doc text. That is the definition of a slice that does not land vertically complete in one specialist session: the authoring is `implementer-architect` work, but the dogfood proof is orchestrator-only work, and the backlog can't be authored until the orchestrator's fan-out digests exist. **Fix:** split into **S2b-i — author the engine** (SKILL.md Phase-2 procedure + `lens-reviewer` dual-use note + backlog-fence/status-line spec; *lands* when the procedure is followable and plugin-validate/tree-check are green — proof is the authored artifact, not a live audit) and **S2b-ii — dogfood + backlog + ROADMAP reconcile** (orchestrator runs the fan-out, synthesizes, writes the real backlog into the fence, archives B1–B6; *lands* the dogfood artifact). This also makes the actor switch explicit instead of hidden in a footnote. *(If the orchestrator insists on one slice, it must at minimum state that S2b is an **orchestrator-executed** slice end-to-end — not delegated to `implementer-architect` — because the proof requires spawning subagents; either way the current "give this to one implementer" framing is wrong.)*

2. **`lens-reviewer` dual-use needs a real contract change, not a one-paragraph note (correctness, load-bearing).** The current role is diff-centric in **every** instruction: "Audit an implemented **diff**" (`lens-reviewer.md:3`), "Read first: … the **diff**" (`:10`), "Audit the **diff** against your module's dimensions" (`:12`), "Audit the **diff**" again (`:12`), output keyed to a diff (`:19`). There is **no** notion of "a scope with no diff." Dropping in one sentence ("in audit mode there's no diff") leaves five diff-anchored instructions actively contradicting it — the agent will look for a diff, find none, and either stall or hallucinate one. **Fix:** the dual-use note must (a) name the **two explicit modes** up front (Verify-diff vs Audit-scope) and restate the read-first + audit-target + output lines for *each*; (b) define what the orchestrator **passes** in audit mode — the module, the **scoped directory/package list** (from Phase-1's prioritized order), and the exclude-set — since "the diff" no longer carries scope; (c) specify the audit-mode output unit is *findings on existing code* (`file:line` + confidence) with the **same** verified-vs-asserted honesty as Verify. Declare this as a **role-contract change** in the harness-impact list (it is not a cosmetic edit). This is the one place a "note" is genuinely insufficient — same lesson rev-2 learned for characterization-first.

3. **Make resume *mechanically* resumable — define the recorded state and a hard stop-trigger (correctness/termination).** Two gaps: **(a) the trigger.** Step 6 says stop "if context is filling" — an LLM cannot reliably sense its own context pressure, so this either never fires (then it blows the budget and the whole run is lost) or fires arbitrarily. Replace the soft signal with a **deterministic, countable trigger**: stop when **(modules-or-dirs completed ≥ the level's max-rounds/coverage cap)**, i.e. drive resume off the *same* discrete work-unit counter that guarantees termination (req. 4), not off a vibe. **(b) what's recorded.** "`covered / remaining / level`" is too coarse to prevent re-doing or skipping work: "covered: 3 dirs" doesn't say *which* `(module × directory/package)` cells are done. **Fix:** the status line (or a small checklist under it, still inside the fence) must record the **unit of resumption explicitly** — the `(module × dir/package)` pairs completed vs pending — so a re-run reads it, skips completed cells, and continues. State the resume **read-then-continue** contract in the procedure ("on resume, read the status checklist; treat listed-complete cells as done; sweep only pending cells"). Without a concrete unit, "resumable" is aspirational and a re-run will silently re-audit or skip.

4. **Pin termination + dedup precisely.** (a) **Termination:** the max-rounds cap (step 5) guarantees the *loop* ends, but only if "a round adds nothing new" is judged against a **persisted seen-set** — say where the seen-set lives across rounds and that the cap is a hard integer per level (e.g. quick = 1, standard = N). State both the cap *and* the seen-set, or "loop-until-dry" can oscillate. (b) **Dedup by `(file · rough location · issue-class)` (step 4) is under-defined at both ends:** "rough location" risks **merging two distinct issues** in the same function (e.g. a security gap and a perf gap at the same lines) — so dedup must key on **issue-class too** and only merge when *class* matches; and cross-file duplicates of the *same* systemic issue (e.g. "no input validation" in 12 handlers) should **roll up to one item listing the locations**, not 12 items or 1 that hides the spread. Spell out merge-when-class-matches and roll-up-systemic, or the backlog is either noisy or lossy.

5. **YAGNI: cut or defer the `thorough` dial level (over-engineering).** The approved plan asked for *budget-bounded with resumable exhaustion* and an *effort dial* — it did **not** ask for a second adversarial-verify pass **plus** a completeness-critic pass on a v1 audit (step 2, `thorough`). That is two extra fan-out rounds of speculative machinery for a backlog generator whose findings are explicitly *model-asserted and human-triaged* anyway. The user prefers lean, and `yagni-sentinel` is in this slice's own review loop. **Fix:** ship **two** levels — `quick` (top modules, single pass) and `standard` (all relevant modules, loop-until-dry) — default `standard`; record `thorough` (adversarial-verify + completeness-critic) as a **ROADMAP `LATER`** item to add *if* a real audit shows `standard` misses things. Fewer moving parts to author, test, and dogfood in this slice.

6. **Close the completeness gaps that will bite at build time.** Specify each, briefly, in the spec:
   - **How the dial is passed.** Skills receive natural-language invocation, not typed flags — say the skill **parses the dial from the invocation** (e.g. "audit thorough" / an explicit arg) and **defaults to `standard`** when absent; don't assume a CLI flag exists.
   - **No clearly-relevant module.** Phase-1 pre-selects candidate modules, but if a repo matches **none** strongly (e.g. a pile of shell scripts), say the fallback: default to the always-on lenses (`maintainability-structure`, `docs-traceability`, light `testing`) rather than auditing nothing.
   - **Monorepo audit ordering.** Phase 1 enumerates packages as separate units, but Phase 2 never says whether the budget/loop/resume operate **per-package** — make the resumption unit `(module × package × dir)` for monorepos so a partial run resumes mid-package and the status line shows package coverage.
   - **Honesty label.** The backlog format names "confidence (deterministic-checkable vs judgment)" — good — but also require the synthesizer to keep the `lens-reviewer`'s **verified-vs-asserted** tag through to the item (a finding a gate *could* prove vs a pure judgment call), matching the catalog's scorecard convention; don't let synthesis launder asserted findings into apparent fact.
   - **`PARTIAL` + the test-baseline guarantee.** "establish a test baseline = Tier-1 #1 for untested code" must hold even on a `PARTIAL` run — state that if behavior-bearing untested code was *seen* before the stop, its baseline item is still emitted (so a partial audit never green-lights an unguarded refactor).

#### Sizing / completeness check (per area)

- **`lens-reviewer` dual-use note — SPLIT-OF-CONCERN, not OK as written.** A one-paragraph note over a fully diff-anchored role is insufficient (req. 2). The *authoring* of the proper two-mode contract is fine to keep in the engine slice (S2b-i); it's the content that must grow, not the slice.
- **Phase-2 procedure authoring — OK** as a slice once the dial is 2-level (req. 5) and resume/dedup/termination are pinned (reqs. 3–4). This is followable skill text — `implementer-architect`-sized.
- **Dogfood fan-out + backlog + ROADMAP reconcile — SPLIT (req. 1).** Different actor (orchestrator, not implementer), depends on live subagent digests, and includes one-time manual ROADMAP housekeeping. Land it as its own slice (S2b-ii) with the dogfood backlog as its proof.
- **Backlog format/status-line spec — OK**, contingent on the resumption-unit being concrete (req. 3) and dedup roll-up defined (req. 4).
- **Effort dial — TRIM (req. 5).** 2 levels, not 3.

#### Harness impact (Stage 9 — declare these in the spec)

- **`lens-reviewer` becomes dual-use — this is a role-contract change** (Verify-diff **and** Audit-scope), not a tweak. Declare it explicitly; it also affects the WORKFLOW/ARCHITECTURE_TREE one-liners for that agent (currently "audits a **diff**"). Record in DECISIONS.
- **Two new conventions:** the `harness-audit:backlog` fence and the **resume status-line/checklist** format (resumption unit = `(module × dir/package)`). These are durable contracts a re-run depends on — name them in DECISIONS alongside the S2a fence convention.
- **WORKFLOW tag→discipline mapping (S4) is a dependency, not just a sibling.** The backlog's whole value is that "the tag selects the discipline" and that a `refactor` item is blocked until its test-baseline item is done — but that mapping/precondition is authored in **S4**, which isn't landed. State the dependency: either S4 lands before the dogfood backlog is *acted on*, or the backlog items reference the precondition as forthcoming. Don't let S2b emit `refactor`-tagged items that imply an enforcement that doesn't exist yet.
- **No new gate/agent file** otherwise — reusing `lens-reviewer` is the correct call; don't add an `audit-reviewer`.

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
Spec'd per slice at its own approval gate. **S1** done. **S2a** below — awaiting approval (Stage 5).

### S2a Spec — `understand` (the front-half of `harness-audit`)

**What this slice is.** `harness-audit` is one **skill** (a `SKILL.md` procedure an agent follows), built in two slices: S2a authors the **Understand** front-half; S2b adds the **Audit + backlog** back-half. S2a lands a genuinely-usable standalone capability — "point it at a repo, get a plain-English overview + an audit-plan" — and is proved by dogfooding on THIS repo.

**Discuss decisions (this slice):**
- **Summary persistence → `docs/ROADMAP.md` header** (user choice), inside a **fenced, regenerable region** so re-runs touch only the fence and never clobber human-added roadmap items.
- **Visual → text only** (user choice) — no Mermaid/Excalidraw.
- **Fence convention (new, load-bearing for S2b too):** audit-generated content in ROADMAP lives between HTML-comment markers — `<!-- harness-audit:overview:start -->…:end` (this slice) and `<!-- harness-audit:backlog:start -->…:end` (S2b). Regeneration replaces only inside the fences; everything outside is human-owned.
- **DRY with init:** Understand prefers an existing fresh `docs/ARCHITECTURE_TREE.md` as its file-level map; else it derives structure via a bounded `Glob` walk.
- **Understand is a single cheap inline pass** (manifests + structure + entry points + a few bounded reads) — **not** a fan-out. Parallelism is S2b's audit.

**Files changed:**

1. **`skills/harness-audit/SKILL.md`** — replace the stub with: a short *How this skill works* overview (Understand → Audit → Backlog); **Phase 1 — Understand** authored as the real, followable 8-step procedure below (with its output contract); **Phase 2 — Audit + backlog** kept as an **honest no-op** ("not yet implemented — lands in plan 0003 S2b; today the skill runs Understand, writes the overview, then stops here and says so"). Frontmatter `description` stays describing the full skill (clean for triggering); the body carries the honesty window (RC-6).
2. **`docs/ROADMAP.md`** — the dogfood artifact: insert the fenced `harness-audit:overview` region after the intro, holding the generated "What this app is & does" overview of THIS repo. Existing content (the stale PLAN-0001 B1–B6 table, `## Later`) is **preserved below the fence** — full reconciliation of that stale backlog is **S2b's** job (when it writes the backlog fence).
3. **`docs/ARCHITECTURE_TREE.md`** — update the `skills/harness-audit/SKILL.md` line: no longer a pure stub ("Understand phase live; Audit+backlog stub → S2b").
4. **`docs/DECISIONS.md`** — append a dated S2a entry (ROADMAP-header persistence + fence convention; text-only; tree-first; cheap-inline Understand).

**The Understand procedure — output contract (what the agent produces):**
- **(A) User-facing overview** — plain-English, text-only, written into the ROADMAP overview fence. Sections: *what it is · what it does · how it's built · how it's organized · safety-net signals (tests/CI/types) · confidence & caveats (honest: inferred from structure, not run).*
- **(B) Audit-plan** — audit-internal, handed to S2b; shown in-conversation as S2a's proof: *exclude-set · prioritized directory order · monorepo/package boundaries · detected ecosystem + existing tooling · candidate standards modules.*

**The Understand procedure — 8 steps (authored into SKILL.md):**
1. **Prefer existing signal** — if `docs/ARCHITECTURE_TREE.md` exists and is current, use it as the file-level map; else derive structure via a bounded `Glob` walk. Budget discipline: read **manifests, configs, entry points, READMEs** — not every source file.
2. **Detect ecosystem & tooling** — scan root+subdirs for manifests (`package.json`, `pyproject.toml`/`requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`/`build.gradle`, `Gemfile`, `composer.json`, `*.csproj`, …) → language(s), framework(s), package manager; and existing **lint/format/type-check/test** configs (eslint, prettier, tsconfig, jest/vitest/pytest, …) — this dovetails with init's compose-with-tooling and tells the audit what gates already exist. General rule over exhaustive list: "identify by manifest."
3. **Detect monorepo / package boundaries** — `workspaces`, `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, multiple manifests, `packages/`·`apps/` layout. If monorepo, enumerate packages as separate audit units.
4. **Build the exclude-set** — honor `.gitignore` as the primary signal, augmented by known dirs: VCS (`.git`), deps (`node_modules`, `vendor`, `.venv`/`venv`, `__pycache__`, `target`, `Pods`), build/output (`dist`, `build`, `.next`, `out`, `coverage`, `.turbo`), generated (`*.generated.*`, `*.min.js`, codegen output), lockfiles, binary/large assets. **Security:** never read or echo secrets (`.env*`, key/credential files) — exclude them and never surface contents in the overview.
5. **Identify entry points & surfaces** — from manifests (`main`/`bin`/`scripts`, `[project.scripts]`/`__main__`, `func main`, framework conventions `src/index.*`·`app/`·`pages/`·`cmd/`, Dockerfile `CMD`/`ENTRYPOINT`) → the app's **type** (CLI · web server · library · SPA · service) and external surfaces.
6. **Map dependencies (high-level)** — name the **architecturally-significant** deps (frameworks, DB drivers, HTTP/auth libs) — enough to say "an Express+Postgres API" — not every dep. This pre-selects the likely standards modules (DB driver → `data-and-persistence`; HTTP server → `api-and-contracts`+`security`).
7. **Prioritized directory order** — rank included dirs by likely risk/value for the audit's budget-spend: entry points & core domain first → data/persistence → API/routes → UI → config/scripts → tests last.
8. **Compose & emit** — write the plain-English overview (A) into the ROADMAP fence; emit the audit-plan (B) for S2b.

**Dogfood / acceptance (run on THIS repo):**
- Overview correctly frames the harness as **"a Claude Code plugin / self-improving dev-harness — mostly docs + agent roles + one Python gate script, not a conventional app,"** names the key parts (`docs/standards`, `.claude/agents`, `skills`, `scripts`, `.claude-plugin`), and is **honest it's inferred**.
- Ecosystem detection correct: **Python** (one script) + Markdown-heavy; **no Node/JS app**; **monorepo = no**; existing tooling = the tree-check hook in `.claude/settings.json` (no eslint/tsc/test runner).
- Exclude-set correct (honors `.gitignore`; excludes `.git`, `.claude/settings.local.json`, build junk); directory order sensible (standards/agents/skills/scripts before plans/archive).
- Overview written into `docs/ROADMAP.md` **inside the fence, non-destructively** (existing content intact below).
- `python scripts/check_architecture_tree.py` **green**; `claude plugin validate .` **green**.
- SKILL.md **honestly states** Phase 2 (audit+backlog) is not yet built.

**In-scope standards (the bar) + effort dial:**
- `docs-traceability` — overview + SKILL.md are docs: accurate, current, clear; fence/regenerate convention documented.
- `product-ux` — the overview is a teaching artifact for a non-engineer: plain language, right altitude, honest confidence ("what good feels like").
- `maintainability-structure` (light) — SKILL.md procedure is well-structured, single-responsibility (Understand ≠ Audit), no dead/speculative steps.
- **Effort dial: LOW** (doc/skill slice, read-only on real code) → **solo `architect-reviewer`** audit (no lens fan-out) + a quick **`yagni-sentinel`** check that the procedure isn't gold-plated; run **`/simplify`**, the tree-check, and plugin-validate.

**Out of scope (→ S2b / later):** the audit fan-out, dedup, loop-until-dry, budget/resume, backlog authoring (tiers/tags/dual-layer/impact/effort/recommended-start), reconciling the stale ROADMAP backlog, and persisting the audit-plan for cross-session resume.

### S2b Spec — split into S2b-i + S2b-ii _(per the S2b plan-review, above)_

> **Plan-review resolution (all findings addressed):** **(1) Split** — S2b bundled two actors (the implementer authors text; the dogfood fan-out is orchestrator-driven since subagents can't spawn subagents, and the backlog needs those digests). Split into **S2b-i (engine authoring)** + **S2b-ii (dogfood execution)**. **(2) `lens-reviewer` dual-use** is a real **role-contract rewrite** (two explicit modes), not a one-liner. **(3) Resume** is now **deterministic** — `(module × dir/package)` cells with done/pending tracking + a max-cells-per-run cap, not "sense context filling." **(4)** Dedup keys on **issue-class** + a persisted seen-set + systemic-dup roll-up; loop + finite cells **guarantee termination**. **(5) `thorough` cut** (YAGNI) → ROADMAP `LATER`; ship `quick`/`standard`. **(6)** Completeness gaps closed (dial NL-parse · no-relevant-module fallback · monorepo cell = package · confidence label preserved through synthesis · test-baseline emits even on `PARTIAL`). **(7)** Tags reference the **locked Decision 2** discipline (not the unbuilt S4); S4 only formalizes it in `WORKFLOW.md`.

#### S2b-i Spec — the audit engine (authoring)

**What this slice is.** Author Phase 2 of `/harness-audit` (the audit procedure) + the **`lens-reviewer` dual-use role-contract** + the backlog fence & deterministic resume model. **Pure authoring — no fan-out is run** (that's S2b-ii). Primary actor: **`implementer-architect`**.

**Files changed:**
1. **`skills/harness-audit/SKILL.md`** — replace the Phase 2 no-op with the authored audit procedure (below) + the `harness-audit:backlog` fence + the resume **status block**; apply the **S2a count-guard** to the Understand section (prefer a source-of-truth over inferred counts; hedge if inferring).
2. **`.claude/agents/lens-reviewer.md`** — **role-contract rewrite to two explicit modes** (below); update its `description` frontmatter (currently diff-only).
3. **`docs/ARCHITECTURE_TREE.md`** — update the `lens-reviewer` line ("audits a diff **or** an audit-scope") + the harness-audit SKILL line ("audit procedure authored; dogfood pending S2b-ii").
4. **`docs/WORKFLOW.md`** — the Roles-list one-liner for `lens-reviewer` (currently "audits a diff against ONE module") → "a diff **or** an audit-scope."
5. **`docs/DECISIONS.md`** — S2b-i entry (lens-reviewer dual-use role-contract; dial = quick/standard; deterministic cell-based resume; backlog fence; `thorough` deferred).

**`lens-reviewer` — the two modes (role-contract rewrite, not a note):**
- **Verify-diff mode** (Stage 7, today): input = the slice's **diff** + spec; audit the diff against the module.
- **Audit-scope mode** (harness-audit, new): input = the **module** + a **scoped list of dirs/packages** + the **exclude-set** (no diff carries the scope here); audit the **existing code** in that scope against the module.
- Restate **read-first / audit-target / output per mode**; both return the same structured per-dimension findings (met/gap + `file:line` + confidence + plain-English line). One role, two entry-shapes — DRY. Remove the diff-only framing so the agent never hunts for a diff that isn't there.

**The audit procedure (authored into SKILL.md Phase 2):**
1. **Parse the dial** from the invocation: if it names `quick`/`standard`, use it; else default **`standard`**. (Two levels only — see *Cut*.)
2. **Load the audit-plan** from Phase 1 (exclude-set · prioritized dirs · monorepo packages · candidate modules). **No clearly-relevant module?** Fall back to the always-relevant **baseline lenses** (`docs-traceability` + `maintainability-structure`) and say so.
3. **Enumerate work as `(module × dir-or-package)` cells** — the deterministic unit (for a monorepo, the dir = each package). On a **resume run**, read the status block, take the **pending** cells, and continue (never redo `done` cells).
4. **Fan out lenses (delegation = budget defense):** spawn a `lens-reviewer` **subagent in audit-scope mode** per cell-batch (a module over its scoped dirs); parallel; each returns a per-dimension digest. Cell granularity keeps each subagent in-budget on a big repo.
5. **Dedup + synthesize:** maintain a **persisted seen-set**; key dedup on **issue-class** (not just file·location) so distinct issues at one spot aren't merged; **roll up systemic cross-file dups** into one item ("recurs in N files"). Carry each finding's **confidence label** (verified-vs-asserted) through synthesis.
6. **Loop-until-dry** (standard): re-sweep not-yet-dry cells until a round adds nothing new; a **max-rounds cap** + the finite cell set **guarantee termination**.
7. **Budget checkpoint = deterministic:** each run has a **max-cells-per-run** cap; when hit (or cells remain after max-rounds), **checkpoint** — write the partial backlog, set the status block to `PARTIAL` with `done`/`pending` cells, and stop, telling the user to re-run. **Never silently truncate.** The test-baseline Tier-1 item **still emits** for any untested behavior-bearing code in the **covered** cells.
8. **Author the backlog** into the `harness-audit:backlog` fence (format below); **recommend a starting point**; report dial + coverage.

**Backlog format (the `harness-audit:backlog` fence):**
- **Status block** at top: `status: COMPLETE | PARTIAL · level · done-cells: [module×dir…] · pending-cells: […] · date`. The `done`/`pending` cell lists are what make resume **deterministic**.
- **Tier 1** (critical: correctness · security · data-loss · *untested behavior-bearing code → "establish a test baseline" = Tier-1 #1*) → **Tier 2** (maintainability · missing tests · perf) → **Tier 3** (docs · style · polish).
- Each item: title; **tag** (`refactor` · `capability-upgrade` · `dependency-health` · `bug` · `feature`); **dual-layer** (technical + `file:line`, then plain-English why / how-bad); **impact + rough effort**; **confidence** (deterministic vs judgment — honestly "model-asserted").
- **Tag → discipline** references the **locked Decision 2** (refactor → characterization-tests-first as a hard precondition; today enforced by "the implementer stops and asks," `WORKFLOW.md`-formalized in S4, durable hook in Phase 1) — honest that enforcement isn't yet automated.
- Ends with a **Recommended starting point**.
- Items are **pipeline-ready**: enough that the user picks one and the existing pipeline runs it.

**Cut (YAGNI — per review + user-lean):** **`thorough`** (the extra adversarial-verify + completeness-critic passes) is **deferred to ROADMAP `LATER`**; ship `quick` + `standard` for v1. A model-asserted backlog doesn't need a second verify pass yet — the deterministic trust-gates (Phase 1) are the real teeth.

**Acceptance (S2b-i):** the SKILL.md audit procedure + the **self-consistent** dual-use `lens-reviewer` (no diff-anchored contradictions left) + the fence/resume spec are authored and coherent; the count-guard is applied; `check_architecture_tree.py` + `claude plugin validate` green. **No fan-out is run.**

**In-scope standards + effort dial:** `docs-traceability` + `maintainability-structure` (procedure + role contract are docs/structure — coherent, **terminating**, single-responsibility) + light `product-ux` (the backlog *format* serves a non-engineer). **Effort dial: LOW–MEDIUM** (authoring, no code execution) → solo **`architect-reviewer`** + **`yagni-sentinel`** (confirm `thorough` stayed cut); tree-check + validate.

#### S2b-ii Spec — the dogfood audit (execution)

**What this slice is.** **Run** the S2b-i engine on THIS repo and write the real backlog. Primary actor: the **top orchestrator** (direct `lens-reviewer` fan-out or a `Workflow`) — subagents can't spawn subagents, so the implementer can't run this.

**Files changed:**
1. **`docs/ROADMAP.md`** — the real **tiered/tagged/dual-layer backlog** of THIS repo inside the `harness-audit:backlog` fence (status `COMPLETE`); **archive the stale B1–B6 build table** (per the archive policy — it lives in the archived `0001` plan); **preserve** genuine `## Later` items below the fences (human-owned).
2. **`docs/ARCHITECTURE_TREE.md`** — the harness-audit SKILL line → "Understand + Audit both live."
3. **`docs/DECISIONS.md`** — S2b-ii entry (dogfood backlog landed; B1–B6 archived).

**Acceptance (S2b-ii):**
- A **real, sensible, non-hallucinated** backlog of the harness, fanned out over the relevant lenses (`docs-traceability`, `maintainability-structure`, `product-ux`, light `testing`) — surfaces e.g. the 6 `draft` (un-web-verified) modules, README staleness, the untested Python gate, unpopulated Current-scope — **each item checkable against the repo** (the orchestrator spot-checks as synthesizer).
- Tiers/tags/dual-layer/impact-effort present; **"establish a test baseline" = Tier-1 #1** for the untested Python gate; status `COMPLETE`; a recommended start given.
- B1–B6 archived; `## Later` preserved; backlog only inside the fence.
- `check_architecture_tree.py` + `claude plugin validate` green.

**In-scope standards + effort dial:** `product-ux` (the backlog is the non-engineer deliverable — actionable, honest) + `docs-traceability`. **Slice-specific check:** backlog **non-hallucinated + sensibly tiered** (orchestrator validates). **Effort dial: MEDIUM** → `architect-reviewer` synthesizes; the dogfood-validity check is the gate.

**Out of scope (→ later):** `thorough` level; deterministic trust-gates (Phase 1); capability modules; `/harness-update` · `/harness-explain`; any automatic refactor (execution rides the pipeline per item, tag-selected).
