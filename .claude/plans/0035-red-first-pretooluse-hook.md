# 0035 — Deferred red-first / characterization PreToolUse test-gate (behavior-changing — planned, NOT built by default)

- **Status:** Draft — **PLANNED, DO NOT BUILD without explicit user go-ahead.** The only behavior-changing item of the fine-tuning set; highest risk; sequence LAST, behind a feature flag, with an easy off-switch.
- **Blockers:** should land only AFTER 0030 (the model-upheld red-first-when-chosen wiring) has been dogfooded, and after 0031–0034. **Depends on:** the greens-without-editing INVARIANT (0030) + the WORKFLOW `feature`/`refactor`/`bug` red-first disciplines.
- **References:** FINETUNING-INPUTS → VERIFIED (PreToolUse now precisely spec-able) · Claude Code `hooks` doc (`PreToolUse`, matcher, `hookSpecificOutput.permissionDecision`) · `docs/claugentic-DECISIONS.md` → *The deterministic trust-gates for unwatched runs* (this is the named-but-unbuilt hook) · `docs/claugentic-INVARIANTS.md` → greens-without-editing · `.claude/agents/implementer.md` + `synthesizer-gate.md` (the model-upheld wiring this would MECHANIZE).

## Problem

The harness's red-first / characterization discipline (bug→failing-test-first · refactor→characterization-first · feature→test-first-when-chosen) is **model-upheld only** — the implementer + Verify gate uphold it; nothing mechanically enforces it. DECISIONS + WORKFLOW + 0030 all say "enforcement waits for the unbuilt `PreToolUse` hook." The hooks doc now makes that hook **precisely spec-able** (verified): `PreToolUse`, matcher `Edit|Write`, `hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason` until a failing test exists. Building it would turn "enforcement waits for the hook" into "enforced" — closing the honesty gap the harness has openly carried.

## Goals / Non-goals

- **Goal:** A `PreToolUse` hook (matcher `Edit|Write`) that returns `permissionDecision: "deny"` + a reason when the discipline requires a failing test that doesn't yet exist — MECHANIZING the model-upheld red-first rule. **Feature-flagged, off by default, easy off-switch.**
- **Goal:** When it lands, flip the honesty copy across DECISIONS/WORKFLOW/0030-descendants from "enforcement waits for the unbuilt hook" to "enforced by the PreToolUse hook when enabled" — and update the greens-without-editing INVARIANT to note the mechanical backstop.
- **Non-goal:** On-by-default. This is a **live workflow gate that can block legitimate edits** if the test-status check is wrong/slow — it must be opt-in per-repo, reversible, and fast.
- **Non-goal:** Replacing the model-upheld discipline — the hook is a backstop; the implementer/gate discipline stays primary.
- **Non-goal:** Building it THIS session (planned-not-built; the user reviews/tests first).

## Architecture & holistic fit

- **Codebase fit:** a new hook (bundled via `plugin.json` hooks) + a test-status probe (command/HTTP). Must stay FAST (fires pre-tool). SoC: the hook is the *mechanical* backstop; the agent prompts stay the *model-upheld* primary. DIP: the hook reads a declared test-status contract, not the plan.
- **Quality dimensions:** `reliability-resilience` (a deny-hook that mis-fires blocks work — fail-safe design, fast, off-switch) · `testing` (the discipline it enforces) · `docs-traceability` (the honesty-copy flip across every "unbuilt hook" mention) · `security` (a hook that gates edits is a trust boundary). Trust surface → `honesty-reviewer` (the copy flip must be accurate — only claim enforcement where the hook is actually enabled).
- **Honesty invariant:** enforcement is claimable ONLY where the hook is enabled; the default-off case stays model-upheld. Never claim blanket enforcement.
- **Risk posture:** the harness's own DECISIONS classify this hook as unbuilt precisely because a per-tool deny-hook is high-stakes; honor that caution.

## Affected files (indicative)

- A new hook script (`scripts/` or `engine/`) — the red-first PreToolUse check (fast, fail-safe, flag-gated).
- `.claude-plugin/plugin.json` — register the PreToolUse hook (matcher `Edit|Write`), behind the flag.
- `docs/claugentic-DECISIONS.md` / `docs/claugentic-WORKFLOW.md` / `docs/claugentic-INVARIANTS.md` — flip the "enforcement waits for the unbuilt hook" copy to "enforced when enabled"; the greens-without-editing INVARIANT gains the mechanical backstop note.
- `.claude/agents/implementer.md` + `synthesizer-gate.md` — note the hook as the enforcement backstop (when enabled); the model-upheld discipline stays primary.
- tests — the hook's deny/allow logic; the test-status probe; the off-switch.

## Risks & mitigations

- **Risk (HIGH): the deny-hook blocks legitimate edits** (wrong/slow test-status probe). → **Mitigation:** off by default; per-repo opt-in; fast + fail-SAFE (a probe error must NOT hard-deny — degrade to allow + warn, never block on the hook's own breakage); an easy documented off-switch (env var).
- **Risk: over-claiming enforcement.** → **Mitigation:** `honesty-reviewer` — claim enforcement ONLY where the flag is on; default stays model-upheld.
- **Risk: per-tool hook latency** (fires on every Edit/Write). → **Mitigation:** keep it fast (the hooks doc's high-frequency/keep-fast rule); a cheap test-status check, not a full suite run.

## Test strategy

- **Deterministic gates:** all standard gates + the hook's own deny/allow tests + a latency sanity check + an off-switch test (flag off ≡ current behavior, provably).
- **Reviewer sign-offs:** `reliability-resilience` + `testing` + `security` + `docs-traceability` via `synthesizer-gate`; `honesty-reviewer` on the enforcement-copy flip; `yagni-sentinel` on the hook's scope (a backstop, not a re-architecture).

## Decomposition (slices) — build ONLY on explicit go-ahead

- [ ] **Slice 1 — The flag-gated PreToolUse hook + fail-safe probe + off-switch (default OFF; default ≡ current behavior provably).**
- [ ] **Slice 2 — Wire it into `plugin.json` + the honesty-copy flip (enforced-when-enabled) across DECISIONS/WORKFLOW/INVARIANTS/agents + close-out.**

---

## Review  _(synthesizer-gate plan-gate, Stage 3 — run before any build)_
_(to be filled)_

## Spec  _(per slice, Stage 4)_
