# 0006 — Institutionalize the workflow's own lessons

- **Status:** Done — landed `4d410b7` (S1) + `f3eaea0` (S2) + `2267052` (S3); archived 2026-06-09
- **Roadmap item:** `docs/ROADMAP.md` → Next #10 ("Streamlining review of the dev workflow itself")
- **References:** the dev-workflow self-review (this session — over-process/efficiency/effectiveness/honesty) · `docs/WORKFLOW.md` · `.claude/agents/*` · `docs/DECISIONS.md` · `scripts/check_architecture_tree.py` (the gate the new sibling mirrors)
- **Stage-3 review:** PASSED with required changes folded in (see *Review* below — `plan-reviewer` CHANGES-REQUIRED→addressed · `yagni-sentinel` PROPORTIONATE (3 trims applied) · honesty OVERCLAIMS→wording fixed).

> **Process + trust-surface change → Stage-3 DIVERSE panel** (`plan-reviewer` + `yagni-sentinel` + honesty pass). This plan also **institutionalizes that rule** — Slice 1.

---

## Problem

The diverse self-review found the dev WORKFLOW pipeline **fundamentally sound** (yagni: PROPORTIONATE; effectiveness: SOUND) but its **own best lessons under-institutionalized** — upheld by orchestrator *improvisation*, not by stated rules / first-class roles / mechanical gates. Five convergent findings (each flagged by ≥2 of the 4 lenses):

1. **The diverse-critics rule is an anecdote, not a trigger** (all 4). Two ~200-word war-stories re-derived per gate — the workflow keeps *re-discovering* where the panel applies (the Verify extension was reactive this session).
2. **The honesty lens has no spawnable role and no written bar** (honesty's #1). The most load-bearing reviewer in the repo (over-claiming = stated #1 risk) is pure improvisation — when `WORKFLOW.md` says "add the honesty pass," there's **no role to spawn**. (Confirmed: run via ad-hoc `general-purpose` prompts.)
3. **Version-sync is a manual catch, not a gate** (3 of 4). The `plugin.json`↔`marketplace.json` drift caught by hand this session is mechanically checkable — leaving it model-upheld violates the harness's own *mechanical-over-model* bias.
4. **Stage 9 (the learning loop) is over-described but under-operationalized** (all 4). The version-sync miss is the *proof*: a lesson landed in DECISIONS but never became a gate.
5. **DRY/prune debt:** the Definition of Done is duplicated across ~5 files; the Stage-7 Verify effort-dial stayed vague while its sibling audit dial got crisp triggers; a generic platform-advice section gold-plates the doc.

The panel was fair: the DoD's *deterministic-gates vs reviewer-sign-offs* split **is** honest and crisp, the reviewer agents carry strong "not a guarantee" framing, and ROADMAP #10 already *honestly logged* this work. This makes the honesty discipline **stated + spawnable**, *not* mechanical — the only thing this plan makes automatically-checkable is version-sync.

## Goals / Non-goals

**Goals**
- Make the diverse-critic + honesty discipline **STATED + SPAWNABLE** (one forward trigger in `WORKFLOW.md` Principles + a first-class `honesty-reviewer` role with its bar embedded) — explicitly **still model-upheld** (the orchestrator must invoke it; it does not fire automatically).
- **Mechanize** the one genuinely-deterministic gap: a **version-sync gate** (`plugin.json` ↔ `marketplace.json` version equality) run in the DoD gate suite.
- **Operationalize Stage 9:** a finite harvest checklist the orchestrator **runs at Land**, with the key step *"a manual/lens catch that a gate could make → open a gate item, not just a DECISIONS line."*
- **Restore DRY:** single-source the Definition of Done; port crisp triggers to the Verify dial; trim the generic advice; **re-present the pipeline as the `FRAME → APPROVE → BUILD → CLOSE` 4-beat model** (a graspability win, no stage change).

**Non-goals (leanness guards — the panel tightened these)**
- **No new pipeline STAGES.**
- **Exactly one new role** (`honesty-reviewer`) and **one new gate** (version-sync). **No separate standards module** — the honesty bar is **embedded in the agent's prompt** (self-contained, like `yagni-sentinel`/`finding-verifier`); promote to `docs/standards/honesty-claims.md` **only when a 2nd consumer appears** (→ ROADMAP). *(User decision; yagni trim b.)*
- **No Stage-1 fork-convergence procedure** — one fork doesn't earn a mechanism; the plan TEMPLATE's "alternatives considered" line covers it (→ ROADMAP). *(yagni trim d.)*
- **No freshly-authored `RELEASE_CHECKLIST`** — a 3-line **stub that links** to the DoD gates (the suite-CLAUDE references the file; the gate replaces the manual step). *(yagni trim c.)*
- **No agent-boilerplate "shared snippet" refactor** — agent prompts stay **self-contained** (→ ROADMAP). *Consequence:* the DoD gate list **stays inline in the agent files**; only `CLAUDE.md` + the pipeline table link to the canonical DoD. *(plan-reviewer blocking #5 — resolves my self-contradiction.)*
- **No managed-stamp version check** — this repo's files are **pristine/unstamped by design**; a stamp-scanner checks nothing here (the only stamp is a test fixture). Gate scope = the two manifest versions, full stop. *(plan-reviewer blocking #1.)*
- **No Stage-9 automation** — a checklist the orchestrator *runs*, never "fires."
- **Not building build mode** (plan 0005, parked — resumes after).

## Approach

### Dogfooding recursion
This plan runs through the pipeline it improves; Stage-3 used the diverse panel (per finding #1's rule). **Once Slice 1 lands the `honesty-reviewer` agent, Slices 2–3's Stage-7 Verify spawns the real role** instead of an ad-hoc prompt.

### Slice 1 — the honesty role + the diverse-critic rule (leaner: agent only)
- **`.claude/agents/honesty-reviewer.md`** (NEW · read-only · `opus` · refute-first on **claims**), with the **bar embedded in its prompt** (no separate module). It mirrors `finding-verifier`'s self-aware framing — *"not a deterministic oracle; a reduction of false confidence."* Its job:
  - Flag copy that **launders model judgment into apparent fact** — the verb discipline (mechanical-sounding "verified/proven/guaranteed/done/safe" used for a model-or-human-upheld action).
  - Flag any **`[D]`/deterministic label it cannot trace to a gate that appears wired** — reporting unverifiable wiring **as its own judgment, not asserting the gate is proven absent** (it does *not* mechanically cross-check — that would be the over-claim it polices). *(honesty should-fix #1.)*
  - **Signal-vs-noise rule (load-bearing):** distinguish a word that *launders judgment into fact* from an **accurate** use — "no new tech debt," "fails loud," "cannot start until" are honest statements, **not** over-claims. *Decide honestly; don't invent doubt to seem rigorous* (the `finding-verifier` posture). A claims-reviewer that cries wolf on honest copy is worse than none. *(plan-reviewer should-fix #3.)*
  - Embedded bar: the mechanical-vs-model line · `[D]`/`[J]` integrity · the verb discipline · dimension-scoped success claims · no-laundering. Output: per-claim {claim · `file:line` · why-it-launders · fix · severity} + `CLEAN`/`OVERCLAIMS`.
- **`docs/WORKFLOW.md`** — hoist the diverse-critics rule into **one forward trigger** in *Principles (apply at every stage)*: *"A contested design fork OR a trust/honesty surface (claims, `[D]`/`[J]` labels, proof-vs-attempt wording, a security boundary) triggers the **diverse panel** — `plan-reviewer`/`architect-reviewer` + `yagni-sentinel` + `honesty-reviewer`, **plus `product-designer` when the change is user-facing** (so the review confirms the plan still achieves what the user is trying to achieve, not just that it's technically sound) — at **every gate that change passes** (Plan **and** Verify); else a lone reviewer suffices. The panel is model-upheld — the orchestrator must convene it; it does not fire by itself."* *(Product lens added at approval — closes the intent-drift gap: today `product-designer` runs only at Discuss, and nothing at the review gate checks the plan against the user's goal.)* Demote the two war-stories to one-line evidence pointers (detail lives in DECISIONS 0003/0004). Add `honesty-reviewer` to the *Roles — a library* roster. Add a one-line **per-stage honesty obligation** to the Verify (7) + Land (8) rows (Verify reports *"attempted/tagged,"* never *"proved"*; Land names *which gate-class* passed).
- **Register:** `.claude-plugin/plugin.json` (`agents[]` 8→9 + version → `0.1.6`), `marketplace.json` (synced), `docs/ARCHITECTURE_TREE.md`, `docs/DECISIONS.md` (the standalone-role rationale + the *"bar embedded; promote to a module when a 2nd consumer appears"* trigger).

### Slice 2 — mechanize version-sync + operationalize Stage 9
- **`scripts/check_versions_synced.py`** (NEW · deterministic · no-LLM): reads `plugin.json.version` as the **single source of truth**, FAILS LOUDLY if `marketplace.json`'s plugin version disagrees. **Sibling** gate (SRP), mirroring `check_architecture_tree.py`'s exit-code convention. **Scope = the two manifest versions only.**
- **`tests/test_check_versions_synced.py`** (NEW · hermetic, mirroring `test_check_architecture_tree.py`): synced → pass; drift → fail with a plain message; **and the fail-LOUD cases** — garbled/non-JSON manifest, a manifest missing the `version` field, the two files parsed independently (no shared-read assumption) — so the gate can't regress into a fail-open like the empty-globs bug. *(plan-reviewer should-fix #4.)* (pytest rises from 47.)
- **`docs/RELEASE_CHECKLIST.md`** (NEW · 3–4 line **stub** that *links* to the DoD gates in `WORKFLOW.md`) — satisfies the suite-CLAUDE reference without re-stating the gate. *(yagni trim c.)*
- **`docs/WORKFLOW.md`** — add the version-sync gate to the DoD *Deterministic gates* group, **honestly scoped** (*"enforces `plugin.json` ↔ `marketplace.json` version equality"* — no stamp claim); state it is **run in the DoD gate suite at Verify/Land** (like `pytest` — no hook needed; honestly a run-gate, not a hooked one). Rewrite **Stage 9** to a finite harvest checklist the orchestrator **runs at Land** (sweep the 5 promote-targets; the load-bearing step: *"a manual/lens catch a gate could make → open a gate item"*); right-size the prose (cut the diagram + two-tier exposition to a sentence each). Use *"runs,"* not *"fires."* *(honesty nit.)*
- **Register/bump:** `ARCHITECTURE_TREE.md` (2 new files; the script is in-scope via `scripts/**/*.py`), `plugin.json`+`marketplace.json` → `0.1.7`, `DECISIONS.md`.

### Slice 3 — DRY + prune the process docs + the 4-beat reframe
- **Single-source the Definition of Done:** `WORKFLOW.md`'s DoD section is canonical; **`CLAUDE.md` keeps a one-line pointer** and the **pipeline row 7** points to the section below it. **The agent files (`implementer-architect.md`, `architect-reviewer.md`) KEEP the inline gate list** (self-contained prompts — they can't follow a link at spawn); a one-line note in DECISIONS records this *controlled, intentional* duplication and why. *(plan-reviewer blocking #5.)*
- **Re-present the pipeline as `FRAME → APPROVE → BUILD → CLOSE`** — a 4-beat overview above the stage table (FRAME = Triage/Discuss/Plan/Review/Spec · APPROVE = the gate · BUILD = Implement/Verify · CLOSE = Land+Retrospect, where Retrospect is now a Land checklist). A graspability win; **no stage is cut or renumbered.**
- **Port crisp triggers to the Verify effort-dial** (Stage 7): reuse the Stage-0 "substantial" triggers (security/trust boundary · shared contract/standard · ~8+ files) to flip solo→fan-out — *no new scoring formula.*
- **Trim** the generic *"Context, parallelism & handoff"* section to the 2 pipeline-specific lines.
- **Register/bump:** `plugin.json`+`marketplace.json` → `0.1.8` (now run through Slice 2's version-sync gate — real dogfooding, since the gate is in the DoD suite the implementer runs), `ARCHITECTURE_TREE.md` (if descriptions shift), `DECISIONS.md`, **mark ROADMAP #10 DONE** + log the deferred items (honesty-module promotion-trigger · fork-convergence · agent-boilerplate dedup · **"run the actual app and observe behavior" as a named Verify step for user-facing slices** — deferred at approval).

### Alternatives considered & rejected
- *Separate honesty standards module* — rejected (user/yagni): one consumer today; embed the bar in the agent, promote later.
- *Fold the honesty lens into `docs-traceability`/`lens-reviewer`* — rejected: it refutes *claims* (distinct posture); standalone like `finding-verifier`.
- *Extend `check_architecture_tree.py`* — rejected: SRP; a sibling keeps the tree-check about the file index.
- *Agents link to the DoD* — rejected (plan-reviewer): prompts must be self-contained; agents keep the inline list.
- *Stamp-version check · fork-convergence procedure · authored release checklist* — rejected (panel): no-op here / one-data-point / gate replaces it.

## Affected files
New: `honesty-reviewer.md` · `check_versions_synced.py` · `test_check_versions_synced.py` · `RELEASE_CHECKLIST.md` (stub). Modified: `WORKFLOW.md` (all 3 slices) · `CLAUDE.md` (DoD → pointer) · `plugin.json` · `marketplace.json` · `ARCHITECTURE_TREE.md` · `DECISIONS.md` · `ROADMAP.md`. **Unchanged (deliberately):** `implementer-architect.md` / `architect-reviewer.md` keep their inline gate list; **no** new standards module / `standards/README.md` edit.

## Risks & mitigations
- **The claims-reviewer cries wolf on honest copy** → the signal-vs-noise rule + the `finding-verifier` "don't invent doubt" posture are *in the agent spec*; Slice 1's own Verify (dogfooded by the new role on Slices 2–3) is the live test.
- **The honesty-reviewer over-claims its own rigor** → reworded to the judgment register (`[D]` wiring reported as judgment, not a mechanical cross-check); mirrors `finding-verifier`.
- **The version-sync gate masquerading as more than it is** → honestly scoped to the two manifest versions in the DoD; run in the gate suite (a run-gate like pytest, not a hooked one) — stated plainly.
- **DRY single-sourcing loses DoD content** → *link from CLAUDE.md/row 7, keep agents inline*; acceptance verifies the canonical DoD is complete + nothing lost.
- **Over-claiming "institutionalize"** → tempered to *stated + spawnable, still model-upheld* in Goals + the Problem disclaimer.
- **Process churn** → yagni PROPORTIONATE; one role + one gate + prose prune; the non-goals fence the cathedral.

## Test strategy
- **Slice 2 ships real unit tests** (the version-sync gate) → `pytest` rises from 47; cases: synced/drift/missing **+ fail-loud** (garbled JSON, missing `version`, independent parse).
- **Slices 1 + 3** are role/prose → deterministic gates green (incl. the new script indexed + the new version-sync gate passing) + internal consistency (DoD canonical once + CLAUDE/row-7 link, agents inline; the diverse-critics rule stated once; "the honesty pass" now resolves to a named role) + Stage-3 diverse review + **Stage-7 Verify spawning the real `honesty-reviewer`** for Slices 2–3.

## Decomposition (slices)
Each lands **complete in one ≤1M-context session, no debt.**

- [ ] **Slice 1 — the honesty role + the diverse-critic rule.** `honesty-reviewer` agent (bar embedded, judgment register, signal-vs-noise) + the one-line forward diverse-critics trigger in Principles + per-stage honesty obligations + roster + registration; bump → `0.1.6`. **Lands complete:** the honesty lens is a spawnable, self-contained role and the rule is stated once. *(No module, no fork-note.)*
- [ ] **Slice 2 — version-sync gate + Stage 9.** `check_versions_synced.py` (version-only) + hermetic tests incl. fail-loud + `RELEASE_CHECKLIST` stub + DoD gate entry + Stage-9 rewrite (runs-at-Land checklist); bump → `0.1.7`. **Lands complete:** version-sync is a real run-gate; the learning loop has a finite operation. *(Verify spawns the Slice-1 honesty-reviewer.)*
- [ ] **Slice 3 — DRY/prune + the 4-beat reframe.** Single-source the DoD (CLAUDE/row-7 link; agents keep inline) + the `FRAME→APPROVE→BUILD→CLOSE` overview + crisp Verify-dial triggers + trim the generic section; bump → `0.1.8` (run through the version-sync gate); mark ROADMAP #10 DONE + log deferred items. **Lands complete:** the process docs obey the repo's own DRY mandate; the pipeline reads as four beats.

---

## Review  _(Stage-3 diverse critics — synthesized; critics ran read-only, returned findings)_

**Verdict:** PASS (required changes folded into Approach / Non-goals / Slices above).

- **`yagni-sentinel` — PROPORTIONATE.** "~85% load-bearing fix; non-goals fence the cathedral." 3 trims **applied:** drop the separate honesty **module** (embed in agent — *user-confirmed*) · drop the Stage-1 **fork-convergence** note (→ROADMAP) · **stub** the RELEASE_CHECKLIST (link, don't author). KEEP (unchanged): the honesty-reviewer agent, the forward trigger, the version-sync gate + tests, Slice-3 DRY/prune, the non-goals. 3 slices (not 2) — confirmed (the dogfooding sequence needs the gate before Slice 3).
- **`plan-reviewer` — CHANGES REQUIRED → addressed.** *(blocking)* drop the **managed-stamp** clause (no-op in this pristine repo) → gate = two manifest versions. *(blocking)* the **DoD-agents-link self-contradiction** → agents keep the inline list, only CLAUDE/row-7 link. *(should-fix)* the honesty-reviewer **word-list false positives** → signal-vs-noise rule. *(should-fix)* version-sync **fail-loud tests**. *(should-fix)* version-sync **invocation** → a DoD run-gate (like pytest), honestly labeled. *(should-fix re module)* moot — module dropped.
- **honesty — OVERCLAIMS → wording fixed.** *(should-fix)* the honesty-reviewer's own *"cross-checks against an actually-wired gate"* → reworded to the judgment register (the claims-auditor must not over-claim its rigor). *(should-fix)* temper *"institutionalize/first-class/repeatable RULE"* → *stated + spawnable, still model-upheld.* *(nits)* Stage-9 *"runs"* not *"fires"*; the stamp *"if cheaply checkable"* aside removed.

**Harness impact:** +1 agent (`plugin.json` 8→9, roster, ARCHITECTURE_TREE) · +1 gate script + test (ARCHITECTURE_TREE; in-scope via `scripts/**/*.py`) · +1 RELEASE_CHECKLIST stub · DoD single-sourced (CLAUDE/row-7 link; agents inline) · DECISIONS appends · ROADMAP #10 DONE + 4 deferred items (incl. the run-the-app Verify step, added at approval). **No** new standards module.

---

## Spec

### Slice 1 — the honesty role + the diverse-critic rule

**In plain English (shown first at the approval gate):**
- **Builds:** the harness's #1 safeguard — the "is this over-claiming?" reviewer — becomes a **real, named teammate** (`honesty-reviewer`) you can call, instead of something improvised each time; and the rule for *when* to convene the skeptical panel is stated **once, up front** (any contested fork or any claim about what the harness guarantees → panel at Plan and Verify).
- **"Done" means:** the panel rule reads as one clear trigger (not two war-stories), and `honesty-reviewer` exists with a sharp, embedded bar that flags *laundering judgment into fact* without crying wolf on honest copy.
- **Accepting:** this makes the discipline **stated + spawnable**, *not* automatic — the orchestrator still has to convene it (it's model-upheld, like every workflow rule). We're deferring a separate honesty *standards module* until something other than this one agent needs the bar.

**Files & changes:** `honesty-reviewer.md` (NEW — as Approach Slice 1); `WORKFLOW.md` (Principles forward trigger + roster + Verify/Land honesty lines + demote war-stories); `plugin.json` (`agents[]` +1, `0.1.6`); `marketplace.json` (`0.1.6`); `ARCHITECTURE_TREE.md`; `DECISIONS.md`.
**Acceptance:** gates green (47 + tree, incl. new agent listed); the diverse-critics rule appears **once** as a forward trigger; "the honesty pass" resolves to a named role; the agent spec carries the signal-vs-noise rule + the judgment-register `[D]` wording (no mechanical self-claim); plugin↔marketplace both `0.1.6`.

### Slice 2 — version-sync gate + Stage 9

**In plain English:**
- **Builds:** the version mismatch we caught by hand becomes a **real automatic check** (the two plugin files must agree), and the "learn from each task" step becomes a **short checklist you actually run when landing** — including the key move *"if a human/lens caught something a check could catch, make the check."*
- **"Done" means:** a bumped version that's out of sync **fails the gate loudly**; Stage 9 is a finite list, not a vibe.
- **Accepting:** the gate covers exactly the two manifest versions (honestly scoped — not the copy-stamps, which don't exist in this repo); it runs as part of the gate suite (like the tests), not via a background hook.

**Files & changes:** `check_versions_synced.py` + `test_check_versions_synced.py` (NEW); `RELEASE_CHECKLIST.md` (NEW stub); `WORKFLOW.md` (DoD gate entry + Stage-9 rewrite); `ARCHITECTURE_TREE.md`; `plugin.json`/`marketplace.json` (`0.1.7`); `DECISIONS.md`.
**Acceptance:** `pytest` rises + green (synced/drift/missing/garbled/missing-field cases); `python scripts/check_versions_synced.py` exits 0 on the synced repo, non-zero + plain message on a drift; Stage-9 reads as a runs-at-Land checklist (uses "runs," not "fires"); RELEASE_CHECKLIST links to the DoD; both manifests `0.1.7`.

### Slice 3 — DRY/prune + the 4-beat reframe

**In plain English:**
- **Builds:** the process docs stop repeating themselves (the "Definition of Done" lives in one place; CLAUDE.md points to it), the pipeline gets a one-glance **FRAME → APPROVE → BUILD → CLOSE** overview, and the Verify step gets the same crisp "when to escalate" triggers the audit dial already has.
- **"Done" means:** the DoD appears canonically once (agents keep their own copy by necessity — documented why); the four-beat overview sits above the stage table; the Verify dial names its escalation triggers.
- **Accepting:** the agent files intentionally keep an inline gate list (they can't follow a link at spawn) — this is controlled, documented duplication, not drift.

**Files & changes:** `WORKFLOW.md` (DoD canonical + 4-beat overview + Verify triggers + trim the generic section); `CLAUDE.md` (DoD → one-line pointer); `plugin.json`/`marketplace.json` (`0.1.8`, run through the new gate); `ARCHITECTURE_TREE.md` (if descriptions shift); `DECISIONS.md` (the controlled-agent-duplication note + deferred items); `ROADMAP.md` (#10 DONE + 3 deferred).
**Acceptance:** the DoD gate list appears canonically once (CLAUDE/row-7 link; agents inline — DECISIONS notes why); the 4-beat overview present (no stage cut/renumbered); the Verify dial lists triggers; `0.1.8` passes the version-sync gate; ROADMAP #10 marked DONE.
