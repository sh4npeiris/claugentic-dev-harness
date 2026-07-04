# 0037 — "Dynamic-workflow harness" grounding + skill-usage observability (from the Claude Code blogs)

- **Status:** Draft (from the 3 Claude Code team blogs the user surfaced 2026-07-04: *getting-started-with-loops* · *a-harness-for-every-task-dynamic-workflows* · *lessons-from-building-skills*). **Blockers:** none for the docs slices; Slice 3 (hook) is behavior-adding → explicit go-ahead only. Additive; does NOT touch 0029/0030's landed work.
- **Disposition at close:** done / deferred (ROADMAP) / rejected (DECISIONS) per slice.
- **References:** the three blogs (first-hand-read, quotes below) · `.claude/plans/FINETUNING-INPUTS.md` → the CORRECTED `/loop`-`/goal` record (2026-07-04) · the harness's own `engine/audit.js` · `engine/build-item.js` · `engine/qa.js` + the Workflow tool · `docs/claugentic-WORKFLOW.md` (roles/patterns) · the skills blog's PreToolUse skill-usage-logging idea + the outstanding stale-eval/BASELINE drift-check.

## Problem

The dynamic-workflows blog defines a **dynamic workflow** as *"Claude writing its own multi-agent harness on the fly … a javascript file with a few special functions that help spawn and coordinate subagents"* — which is **exactly what the harness's `engine/*.js` + the Workflow tool ARE**. Yet the harness (a) had **dismissed** that framing as "debunked" (the 0032 over-refutation — being corrected in the current pass), (b) doesn't **name itself** a dynamic-workflow harness or cite the blog's articulation of **why** multi-agent structure beats single-context Claude, and (c) doesn't leverage two concrete, low-risk ideas the blogs surface. The harness's core patterns are *externally validated* by these blogs — we should ground in them, not ignore them.

**What the blogs give us (first-hand quotes):**
- Dynamic-workflows blog — our patterns, named: **fan-out-and-synthesize** (*"synthesize … a barrier — waits for all fan-out agents, then merges"*), **adversarial verification**, **tournament** (*"N agents … different approaches … judge pairwise"*), **loop-until-done** (*"until a stop condition is met"*), **classify-and-act**, **generate-and-filter**. The failure modes structure prevents: **agentic laziness (stopping early) · self-preferential bias (preferring own results) · goal drift**. Plus **token budgets** (*"use 10k tokens"*) and **pairing with `/loop`+`/goal`** for repeatable flows.
- Loops blog — the four loop **types** (turn/goal/time/proactive) as a valid taxonomy; code-quality-across-iterations (clean codebase · a way to self-verify · reachable docs · a **fresh-context reviewer**) — all things the harness already embodies.
- Skills blog — *"a **PreToolUse hook** that lets us **log skill usage**"* to spot *"skills that are … undertriggering"*; *"the highest-signal content in any skill is the **Gotchas section**"*; the *"don't state the obvious"* anti-pattern.

## Goals / Non-goals

- **Goal (docs — the honest core):** Name the harness a **dynamic-workflow multi-agent harness** and **ground its design** in the blog's three failure-modes (laziness / self-preference / goal-drift) — as the honest *rationale* for the clean-context-independent-reviewer + adversarial-verify architecture. **Grounding, NOT proof** (the blog explains why the shape helps; it doesn't certify the harness is correct). Home: a short WORKFLOW note + one DECISIONS line.
- **Goal (docs — pattern names):** Map the harness's existing orchestration to the blog's named patterns (fan-out-synthesize = audit fan-out / verify panels; adversarial-verify = finding-verifier; tournament = judge-panel/best-of-N; loop-until-done = audit loop-until-dry) so a maintainer sees the correspondence. A note, not new machinery.
- **Goal (Slice 3, behavior-adding — GO-AHEAD ONLY):** A **skill-usage-logging `PreToolUse` hook** — **fail-safe, non-blocking, observability-only** (logs which harness skill fired, never denies) — to measure triggering and catch the **stale-eval / undertriggering** drift. **Distinct from 0035** (which is a *blocking* deny-hook); this one only *observes*. Off-switchable; writes to `${CLAUDE_PLUGIN_DATA}` or a log path.
- **Goal (reconsider):** Reopen the **Gotchas-section** question the audit-verification refuted — the skills blog calls it *"the highest-signal content."* Evaluate whether a dedicated Gotchas section earns its place in the longest skills (vs the current inline+indexed coverage) — a `product`/`docs-traceability` judgment, likely a small doc slice or a ROADMAP note.
- **Non-goal:** Re-architecting the engines. The patterns are ALREADY there; this NAMES + grounds them (YAGNI — don't build a "pattern framework").
- **Non-goal:** Token-budget wiring into `engine/*.js` unless it's a trivial pointer — the Workflow tool already exposes `budget.*`; the engines are invoked by skills, not the raw Workflow tool. Confirm at Spec whether an explicit budget knob is warranted or a YAGNI (likely a ROADMAP note).
- **Non-goal:** Building Slice 3 without explicit go-ahead (any `PreToolUse` hook is behavior-adding; even observability-only fires on every tool call → must be fast + fail-safe + opt-in).

## Architecture & holistic fit

- **Codebase fit:** Slices 1-2 are docs (WORKFLOW note + DECISIONS line + pattern-map). Slice 3 is a new fail-safe hook (bundled via `plugin.json` hooks) + a log sink. Slice 4 (gotchas) is docs. SoC: the grounding names existing structure; the hook adds observability, not control.
- **Quality dimensions:** `docs-traceability` (the grounding/pattern-map is accurate; quotes attributed) · `product-ux` (the gotchas reconsideration). Slice 3 adds `reliability-resilience` (a per-tool hook must be fast + fail-safe) + `security` (a hook is a trust boundary, even observability). Trust surface → `honesty-reviewer`: the grounding must say **the blog validates the design's rationale, NOT that the harness is proven correct**; never claim the failure-modes are "solved," only "structurally mitigated."
- **Honesty invariant:** grounding cites the blog as **external design rationale** (model-upheld), never as a correctness proof. The skill-usage hook **observes**, never enforces — do not let its copy imply enforcement (that's 0035's unbuilt territory).
- **Doc-budget:** the grounding adds to WORKFLOW (not budget-gated) + ONE DECISIONS line — and it lands AFTER the condensation frees headroom (sequence it so DECISIONS stays comfortable; contribute a forward-looking keep-line, NOT a LANDED narrative — per the formalized condensation-prevention rule).

## Affected files (indicative)

- `docs/claugentic-WORKFLOW.md` — the "we are a dynamic-workflow harness + the three failure-modes rationale + the pattern-name map" note (Principles/roles area).
- `docs/claugentic-DECISIONS.md` — ONE forward-looking line (the dynamic-workflow identity + failure-modes grounding; blog-attributed; grounding-not-proof).
- *(Slice 3)* a new hook script + `plugin.json` hooks registration (fail-safe, opt-in, off-switchable) + tests + the log sink.
- *(Slice 4)* the longest skills' SKILL.md (a Gotchas section) OR a ROADMAP note if it doesn't earn it.
- `docs/claugentic-ARCHITECTURE_TREE.md` — rows for any new file (Slice 3).

## Risks & mitigations

- **Risk: grounding over-claims (the blog "proves" the harness works).** → `honesty-reviewer`: grounding = external rationale for the design shape, never a correctness proof; the failure-modes are *mitigated by structure*, not *solved*.
- **Risk: re-importing the "orchestration" confusion.** → keep the crisp split: `/loop`-`/goal` = scheduling/goal primitives; **dynamic workflow = the multi-agent harness (us)**; they pair. (The corrected WORKFLOW:259 + FINETUNING record are the reference.)
- **Risk (Slice 3): a per-tool hook is slow / fails / leaks.** → fast + fail-safe (an error degrades to allow+silent, never blocks a tool); opt-in + off-switch; observability-only (no deny path); a hook that gates is out of scope (that's 0035).
- **Risk: gotchas-section churn re-adds DRY duplication the audit flagged.** → only add where a real failure-mode isn't already captured inline+indexed; `yagni-sentinel` guards.

## Test strategy

- **Slices 1-2 (docs):** `pytest` · `check_shipped_content.py` (WORKFLOW/DECISIONS ship — adopter-aware, no stranded token) · `check_doc_budgets.py` (DECISIONS stays comfortable post-condensation) · tree.
- **Slice 3 (hook):** the hook's fail-safe behavior (probe error ⇒ allow, never block) · latency sanity · off-switch (flag off ≡ current behavior) · the log-sink format · `node`/`pytest` as the hook's language dictates.
- **Reviewer sign-offs:** `docs-traceability` + `product-ux` via `synthesizer-gate`; `honesty-reviewer` on the grounding-not-proof + observe-not-enforce framing; `yagni-sentinel` on Slice 3/4 scope.

## Decomposition (slices)

- [ ] **Slice 1 — Dynamic-workflow harness identity + failure-modes grounding + pattern-name map (docs).** WORKFLOW note + ONE DECISIONS line. **In-scope:** `docs-traceability`; trust surface → `honesty-reviewer` (grounding-not-proof).
- [ ] **Slice 2 — Pair-with-`/loop`-`/goal` + token-budget pointers (docs; likely folds into Slice 1 or a ROADMAP note — confirm at Spec, YAGNI).**
- [ ] **Slice 3 — Skill-usage-logging `PreToolUse` observability hook (fail-safe, opt-in, off-switch). BUILD ONLY ON EXPLICIT GO-AHEAD** (behavior-adding; addresses the stale-eval/triggering-drift gap). **In-scope:** `reliability-resilience`, `security`, `testing`, `docs-traceability`.
- [ ] **Slice 4 — Reopen the Gotchas-section question (evaluate + add where it earns its place, else ROADMAP note).** **In-scope:** `product-ux`, `docs-traceability`; `yagni-sentinel`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_
_(to be filled)_

## Spec  _(per slice, Stage 4)_
