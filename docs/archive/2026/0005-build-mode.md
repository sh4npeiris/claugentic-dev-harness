# 0005 — Build mode (autonomous, trust-dialed)

- **Status:** Done — landed `d8937fe` (Slice 1) + `d5d6d6f` (Slice 2); archived 2026-06-10
- **Roadmap item:** `docs/ROADMAP.md` → Next #3 ("Build mode (autonomous, trust-dialed)")
- **References:** `docs/PRODUCT.md` (Build-mode brief — flows/states/honesty) · `docs/WORKFLOW.md` (the pipeline this auto-drives; post-0006: 4-beat, DoD canonical, diverse-panel trigger, Stage-9 harvest) · `skills/audit/SKILL.md` (triage source + re-audit + progress discipline) · `skills/init/SKILL.md` (sibling voice) · `docs/DECISIONS.md`
- **Stage-3 review:** PASSED with required changes folded in (see *Review* — full diverse panel: `plan-reviewer` CHANGES-REQUIRED→addressed · `yagni-sentinel` PROPORTIONATE (2 cuts + 1 trim applied) · `honesty-reviewer` OVERCLAIMS→wording fixed · `product-designer` ACHIEVES-INTENT (2 copy-structure fixes applied)).

> **Design fork + trust surface + user-facing — the FULL diverse panel** (per the `docs/WORKFLOW.md` Principles trigger): `plan-reviewer` + `yagni-sentinel` + `honesty-reviewer` + `product-designer` — at Plan **and** Verify.

---

## Problem

The harness today stops at a *list*. After `/claugentic-dev-harness:audit` writes a tiered backlog, the user must manually pick each item and walk it through the WORKFLOW pipeline, one at a time. Missing: (1) the **interactive post-audit triage** (deferred from Roadmap #1) — no in-product way to select what to build and hit go; (2) the **autonomy loop** — nothing works the backlog *item-by-item to the stop-signal* (Tier-1+2 empty). This is the flagship (Roadmap #3), and it must be **honest**: autopilot (unwatched) is gated on trust mechanisms that don't exist yet (#4 cross-model judge, #5 deterministic gates).

## Goals / Non-goals

**Goals**
- A new **`/claugentic-dev-harness:build`** skill: **triage → build loop → stop-signal**, a *thin orchestration layer* over the **existing** WORKFLOW + audit (no new pipeline, no new agents, **no new state stores**).
- **Two modes:** `checkpoint` (**LIVE**) · `autopilot` (**a named mode whose only behavior today is an honest decline** naming #4+#5 and offering checkpoint — no autopilot execution path, no mode-dispatch scaffolding; building real autopilot is gated on #4+#5 landing).
- **Checkpoint pauses at exactly:** (1) triage selection · (2) the **spec, before any code** (Stage 5) · (3) **before land / any irreversible action**. Auto-drives Plan/Review/Implement/Verify between (per the auto-drive contract below).
- **Per-item failure → pause-and-ask** (retry / skip-and-continue / stop); the failure report **states plainly that nothing partial landed** (the slice landed complete or not at all).
- **After each item:** a **scoped re-audit over the touched files' dirs/modules** (the audit's existing `(module × dir)` cell granularity — *honestly scoped: cross-file fallout beyond those cells is owned by the closing full audit, not claimed here*); **any new Tier-1 OR Tier-2 → pause to re-triage**; else auto-continue.
- **Stop-signal:** one **`standard`** full audit at the end; Tier-1+2 empty → the audit's **"Sound on the audited dimensions"** terminal signal.
- **Guardrails (both modes, non-negotiable):** hard-stop + ask before **irreversible** actions (push to a shared remote **incl. `main`**, deploy, delete data, spend money, external side-effects); **never invent scope** — a genuinely-new feature → ROADMAP for approval.
- **Honesty:** *"passed the checks and the reviewer's audit,"* never *"proven correct"*; **"done" scoped to audited dimensions**; the refusal names #4+#5; re-audit tags carry the audit's *reduction-of-false-confidence* framing unchanged.
- **Triage granularity:** individual items **+ tier-level shortcuts** ("do all of Tier-1").

**Non-goals**
- **Autopilot LIVE** — refusal-only until #4-5.
- **New pipeline stages, agents, or state stores** — reuses the WORKFLOW roles + the `audit` skill + the **existing two state stores** (the `harness-audit:backlog` fence + per-item plan files).
- **A dependency graph** — the scoped re-audit does NOT compute "dependents" (the harness has no reverse-import graph; claiming one would be a trust-surface over-claim). → ROADMAP if a real adopter proves the closing audit misses dependent-file regressions.
- **New deterministic gates** (that's #5) · **a typed-flag CLI** (natural-language invocation).

## Approach

### Architecture
`skills/build/SKILL.md` — a **prose skill the top-level orchestrator runs** (like `audit`: the orchestrator spawns pipeline subagents; subagents can't spawn subagents). Skills are auto-discovered from `skills/` (`init`/`audit` prove the pattern).

### The per-item auto-drive contract *(the skill's core mechanic — fully specified)*
For one worklist item, the orchestrator drives the WORKFLOW stages, spawning the **existing roles**:
- **Plan (Stage 2):** orchestrator drafts `.claude/plans/NNNN-<item>.md` from `TEMPLATE.md` (the item's tag → discipline per the WORKFLOW mapping: `refactor` → characterization-tests-first precondition (stop-and-ask if no baseline); `bug` → reproduce-first; etc.).
- **Review (Stage 3):** `plan-reviewer`, escalated to the **diverse panel** per the Principles trigger (contested fork / trust surface / user-facing → + `yagni-sentinel` + `honesty-reviewer` + `product-designer`). Orchestrator iterates the plan until PASS.
- **Spec + PAUSE (Stages 4–5):** spec written; **the checkpoint renders the plain-English triad verbatim — *what this builds · what "done" means for you · what you're accepting (risks/trade-offs)* — before any technical detail.** No code before "yes."
- **Implement (Stage 6):** `implementer-architect`, one slice per session.
- **Verify (Stage 7):** dial per the WORKFLOW's named triggers (solo `architect-reviewer` by default; **fan-out** when the diff touches a security/trust boundary, a shared contract/standard, ~8+ files, or a trust/honesty surface — the Stage-0 triggers). **On a failed Verify:** iterate implement→verify up to a small bounded number of attempts (2–3); still failing → the **item-failure pause-and-ask**. A mid-build re-slice (the item won't fit one session) is itself a **pause-and-ask**, never a silent re-plan.
- **Land + PAUSE (Stage 8):** the pre-land checkpoint (+ the irreversible hard-stop for any push/deploy); then conventional commit, plan → archive, DECISIONS line, **the Stage-9 harvest checklist runs**.

### Resume contract *(no new state store — the yagni cut, adopted)*
The worklist is **derived, not stored**: (a) the `harness-audit:backlog` fence = the item universe + its existing status block; (b) an **in-flight item** = its plan file in `.claude/plans/` with unchecked slices; (c) a **done item** = its plan archived in `docs/archive/` (the existing Land convention). A resumed `/…:build` reconstructs the worklist from those two stores and **re-confirms the remaining selection + order with the user** (a 5-second re-confirm beats a third state store; the user's picked order is the one thing not durably stored — accepted, stated honestly).

### The five flows (from `docs/PRODUCT.md`)
1. **Triage** — load the backlog (none/stale → run `audit` first). Tiered list; pick items and/or tiers; confirm order; "start now?". **Empty backlog / already-sound → don't enter the loop**: the "Sound on the audited dimensions" phrasing **plus the real next step — "start something new, or stop"** (a fork, never a dead end).
2. **Per-item build** — the auto-drive contract above.
3. **Re-audit → continue-or-re-triage** — scoped re-audit (touched cells); any new Tier-1/2 → pause, show what changed, re-pick (framed as the safety feature); else auto-continue.
4. **Stop/done** — worklist exhausted → one `standard` full audit → Tier-1+2 empty → the terminal signal; else surface the remainder for a final triage.
5. **Autopilot-refusal** — *"Running unwatched needs an independent cross-model judge (Roadmap #4) and deterministic trust-gates (Roadmap #5) — neither exists yet, so I can't do this honestly. Here's checkpoint instead."*

### Non-happy states (all designed — `docs/PRODUCT.md`)
Empty backlog (the fork above) · the **checkpoint/decision** state (*what was just done · what's being decided · the options*) · **item fails** (pause-and-ask; "nothing partial landed") · **re-triage interruption** (the safety feature) · **long-running** (completed-beat narration, **never an ETA**) · **irreversible hard-stop** (name the action + consequence; never proceed on silence).

### Why no new agent / pipeline / state
Build mode is *auto-driving transitions a human does manually* — orchestration, not capability. Every stage has its agent; triage + re-audit live in `audit`; the state lives in the two existing stores. **Release scoping:** `0.1.9` (Slice 1) is a real public release honestly scoped — *"build one backlog item at a time, with checkpoints"*; `0.1.10` (Slice 2) upgrades the copy to the full backlog loop. Neither implies more than it ships.

### Alternatives considered & rejected
Ship autopilot live (the #1 over-claim) · fold into `audit` (different job/output — SRP) · a build-orchestrator agent (subagents can't spawn subagents) · full re-audit per item (cost) · a new worklist state store (duplicates the two existing stores — DRY) · "+ dependents" blast radius (implies a dep-graph the harness lacks).

## Affected files

**Slice 1 — per-item engine + the modes:**
- `skills/build/SKILL.md` — **NEW** (mode detection + refusal · minimal triage ("build *this* item") · the auto-drive contract · the spec-pause triad verbatim · tag→discipline · item-failure pause-and-ask + "nothing partial landed" · irreversible hard-stops + no-invented-scope · honesty framing).
- `skills/audit/SKILL.md` — close-out gains the `/…:build` handoff line.
- `README.md` — **three commands**; the build line honestly scoped to *one item at a time* (Slice 2 upgrades it).
- `.claude-plugin/marketplace.json` — **`description` updated** ("two live skills" → three, naming `build`) + version; `.claude-plugin/plugin.json` — version. Both → **`0.1.9`** (the version-sync gate enforces the pair).
- `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md`.

**Slice 2 — the full-backlog loop + stop-signal:**
- `skills/build/SKILL.md` — multi-item triage (+ tier shortcuts) · the loop · the scoped re-audit (touched cells) + re-triage on new Tier-1/2 · the `standard` final audit + terminal signal · the **derive-don't-store resume contract** · the empty-backlog fork.
- `docs/WORKFLOW.md` — a short pointer (build mode = the orchestration layer over the pipeline) + the Stage-8 close-out line gains "or run `/…:build`".
- `README.md` + `marketplace.json` copy — upgrade to the full-loop scope; both manifests → **`0.1.10`**.
- `docs/ROADMAP.md` — **#3 DONE** (checkpoint shipped; autopilot = refusal until #4-5); `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md`.

## Risks & mitigations
- **Over-claim on the trust surface** → honesty framing baked into the spec wording; `honesty-reviewer` at Plan (done) + Verify; "done"/"verified"/"safe" audited.
- **Auto-drive runs away** → the three pauses + the bounded verify-retry (2–3) + re-slice-is-a-pause + the hard-stop set + no-invented-scope.
- **Decision-fatigue** (the user chose any-Tier-1/2 interrupts) → a clean re-audit = **no** pause; interruptions taper as criticals clear; framed honestly as the chosen safety trade.
- **Scoped re-audit coverage** → honestly scoped to touched cells; the closing `standard` audit owns cross-file fallout; never claimed otherwise.
- **Resumability** → the derive-don't-store contract (order re-confirmed at resume — stated, accepted).
- **Half-product at 0.1.9** → release copy scoped to one-item; Slice 2 upgrades it.

## Test strategy
The skill is **model-executed prose** — no unit test (like `audit`). **Validated by** *(deterministic gates verify what gates can; the rest is reviewer judgment, stated as such)*:
1. **Deterministic run-gates green** — `python -m pytest` (full suite, all green) · `python scripts/check_architecture_tree.py` (new skill indexed) · `python scripts/check_versions_synced.py` (both manifests, each bump).
2. **Internal consistency** — flows/states/guardrails match `docs/PRODUCT.md`; no contradiction with WORKFLOW; the refusal is the only autopilot behavior.
3. **Honesty acceptance** — no "verified/proven/safe/bug-free"; "done" dimension-scoped; the refusal names #4+#5; hard-stops present; the spec-pause triad verbatim.
4. **Stage-7 Verify = the FULL panel** (user-facing trust surface): `architect-reviewer` synthesis over `maintainability-structure` + `docs-traceability` lenses + `yagni-sentinel` + `honesty-reviewer` + **`product-designer`** (the shipped copy still achieves the JTBD, checked against `docs/PRODUCT.md`).
5. **Dry-run** — walk one real backlog item through the skill conceptually (no irreversible actions); confirm every pause fires where specified.

## Decomposition (slices)
- [ ] **Slice 1 — per-item build engine + the modes.** As *Affected files Slice 1*: "build me this one item" works end-to-end with the three checkpoints; autopilot refuses honestly; release copy scoped to one-item; gates green; → `0.1.9`. **Lands complete** as a genuinely shippable vertical.
- [ ] **Slice 2 — the full-backlog loop + stop-signal.** As *Affected files Slice 2*: "build my whole backlog to Tier-1+2-empty" works with the derive-don't-store resume, the scoped re-audit + re-triage, the `standard` terminal audit; copy upgraded; → `0.1.10`. **Lands complete** with the honest stop-signal.

---

## Review *(Stage-3 — the full diverse panel; synthesized by the orchestrator from the four critics' structured returns)*

**Verdict: PASS** (all required changes folded in above).

- **`plan-reviewer` — CHANGES REQUIRED → addressed.** *(blocking)* stale "47/47" test count → un-hardcoded ✓ · marketplace `description` edit added to Slice 1 ✓ · the 0.1.9/0.1.10 double-bump reconciled (both real releases, copy honestly scoped per slice) ✓ · blast-radius specified as **touched cells, no "+ dependents"** ✓ · the **auto-drive contract fully specified** (agents per stage, the Verify dial via the named triggers, bounded verify-retry → failure-pause, re-slice = pause) ✓. *(should-fix)* resume contract defined (derive-don't-store) ✓ · `product-designer` added to the Verify panel ✓ · *(nit)* version-sync gate listed ✓.
- **`yagni-sentinel` — PROPORTIONATE; 2 cuts + 1 trim applied.** The new build-session state store **cut** (derive from the backlog fence + plan files) ✓ · "+ dependents" **cut** (no dep-graph; closing audit owns fallout; → ROADMAP if proven needed) ✓ · the autopilot "wired seam" framing **trimmed** (a named mode whose only behavior is the refusal — no scaffolding) ✓. Keeps confirmed: the separate skill (SRP), the 2-slice split, the refusal-as-guardrail.
- **`honesty-reviewer` — OVERCLAIMS → fixed.** "Proven by"/"verified by" → **"Validated by"** with the gates-vs-judgment split stated ✓ · hardcoded test count dropped ✓. Substance confirmed CLEAN on all six hunts (the user-facing copy, "done" scoping, the refusal, the flagship phrase, checkpoint-trust attribution, re-audit bounds).
- **`product-designer` — ACHIEVES-INTENT; copy-structure fixes applied.** The **spec-pause triad carried verbatim** into the flow + acceptance ✓ · the **empty-backlog state is a fork** (terminal phrasing + "start something new, or stop") ✓ · the failure report **names "nothing partial landed"** ✓. All five flows + six non-happy states confirmed faithful; the decision-fatigue trade confirmed honestly framed.

**Harness impact:** new skill (+ tree entry) · audit close-out + WORKFLOW Stage-8 close-out lines · README/marketplace three-commands copy · bumps 0.1.9/0.1.10 (gate-enforced) · DECISIONS appends · no new agent/standard/state store.

---

## Spec

### Slice 1 — per-item build engine + the modes
**In plain English (the approval triad):**
- **What this builds:** a `/claugentic-dev-harness:build` command — point it at one backlog item and it drives the whole professional pipeline for you (plan → adversarial review → spec → **your approval** → build → review-the-work → land), pausing only where your judgment matters: approving the spec before any code, and before anything irreversible (like pushing). Asking for "autopilot" gets an honest refusal naming exactly what's missing before unwatched runs can be trusted.
- **What "done" means for you:** you can say *"build Tier-1 item 2"* and get a landed, reviewed change with at most three interruptions — each presented in plain English (*what was just done · what's being decided · your options*). A failed item pauses and tells you plainly that **nothing partial landed**.
- **What you're accepting:** this release does **one item at a time** (the full backlog loop is the next slice); the in-between stages run on the same model-upheld review discipline as today (the human gates are the trust mechanism, not a model guarantee).

**Files:** as *Affected files Slice 1*. **Acceptance:** gates green (pytest all-green · tree incl. the new skill · version-sync at `0.1.9` both manifests); the spec-pause renders the triad verbatim; the refusal names #4+#5; the hard-stop set incl. push-to-`main`; README + marketplace copy scoped to one-item; tag→discipline honored (refactor stops without a baseline); the Verify-retry bound + failure-pause specified in the skill.

### Slice 2 — the full-backlog loop + stop-signal
**In plain English (the approval triad):**
- **What this builds:** the full loop — pick several items (or "all of Tier-1"), confirm, and it works them one by one: after each landed item it re-checks the code it just touched; brand-new important findings pause it for you to re-pick, otherwise it keeps going; when the list is done it runs one full audit and tells you honestly whether you've reached *"sound on the audited dimensions."*
- **What "done" means for you:** *"build my backlog"* runs to the honest stop-signal with interruptions only for new important work; an interrupted session resumes by re-reading the backlog + in-flight plans and re-confirming your remaining picks.
- **What you're accepting:** the per-item re-check covers the files the item touched (the closing full audit covers everything else); your chosen *ordering* isn't stored between sessions — it's re-confirmed in seconds on resume; interruptions on any new Tier-1/2 was your chosen safety-over-fatigue trade.

**Files:** as *Affected files Slice 2*. **Acceptance:** gates green (`0.1.10` both manifests); the loop honors re-triage-on-new-Tier-1/2; the empty-backlog state is a fork; the terminal signal verbatim; the resume contract works from the two existing stores; ROADMAP #3 DONE with autopilot honestly deferred; README/marketplace copy upgraded.
