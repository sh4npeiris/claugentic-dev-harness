# 0008 — Deterministic trust-gates (the mechanical land-gate + secret-scan + characterization hook)

- **Status:** **Parked** (2026-06-10, user decision) — the harness is declared usable at `v0.1.11` for watched (checkpoint) use, which is the mode the user actually wants today; these gates harden the *unwatched* mode specifically. **Resume trigger:** real-world dogfooding shows genuine demand for hands-off runs. The Stage-3 panel findings (cross-model, run at park time) are appended below when available — the plan resumes from them, not from scratch.
- **Roadmap item:** `docs/ROADMAP.md` → Next #5 ("Deterministic trust-gates") — **reshaped at Discuss** (this session): the general **land-gate** is the core; the characterization hook + secret-scan are the specialized additions. The ROADMAP row is updated to match (Slice 1), and a new follow-up item — **the autopilot flip** (batch spec-approval up front · unwatched in between · hard-stops remain) — is added right after #5.
- **References:** `docs/DECISIONS.md` (*Trust-first* — the deterministic track is the #1 known gap) · `docs/WORKFLOW.md` (DoD: deterministic gates vs reviewer sign-offs; the tag→discipline table's "until that hook lands" caveat) · `.claude/settings.json` (the existing hook wiring) · `scripts/check_architecture_tree.py` + `check_versions_synced.py` (the gate house-style) · `skills/build/SKILL.md` (the refusal this track ultimately retires)

> **Trust surface — Stage-3 diverse panel** (`plan-reviewer` + `yagni-sentinel` + `honesty-reviewer`, judges cross-model per the WORKFLOW wiring). `product-designer` not convened: the user-visible surface is block messages and copy (the honesty lens owns those); the autopilot flip — the real UX work — is deliberately a separate follow-up item with its own product pass.

---

## Problem

The Definition of Done's "deterministic gates" are **model-run discipline**: the orchestrator *chooses* to run `pytest`/tree-check/version-sync before landing. Only the tree-check is hook-enforced. Nothing **physically stops** a red slice from being committed — in a watched session that's acceptable (the human is the backstop); in an **unwatched (autopilot) run it's the missing trust mechanism**. The cross-model judge (#4) reduced *judgment* risk; #5 closes the *mechanical* gap: **tests gate every slice — feature, bug, or refactor — in a way no model can skip.**

Discuss (this session) corrected the item's framing: the originally-named pieces (characterization hook, secret-scan) are the *specialized* gates; the **general core** is a land-gate. The user's intent confirmed: the goal is autonomous roadmap execution for **all** item types (with human spec-approval as the retained steering gate), not refactor-only protection.

## Goals / Non-goals

**Goals**
1. **The land-gate (the core):** a `PreToolUse` hook on `Bash` that intercepts `git commit` / `git push` commands and **runs the deterministic suite itself** (pytest · tree-check · version-sync · the secret-scan once Slice 2 lands) — **exit-2 blocking** a red commit with a plain message. No model in the loop after the wiring: the agent *cannot* land red through its Bash tool.
2. **The secret-scan gate:** a deterministic scanner (`scripts/check_no_secrets.py`) over the **staged diff** — common credential patterns (AWS keys, private-key blocks, known token formats) — run inside the land-gate suite. **Honest scope:** catches *known patterns*, a risk reduction, not a guarantee of "no secrets ever."
3. **The characterization hook (the refactor-specific gate):** the **declared-intent contract** — when a `refactor`-tagged item starts, the workflow/build mode **declares it** in a small state file; from that moment a `PreToolUse` hook on `Edit`/`Write` **blocks source-file edits until the state records a test baseline** (and the suite is green). The declaration is model-upheld; the **enforcement after declaration is mechanical** — the split stated honestly everywhere. This finally retires the WORKFLOW tag-table's *"until that hook lands, upheld by the implementer"* caveat.
4. **Honest-copy reframe:** "the one mechanically-enforced gate" (tree-check) becomes "the mechanically-enforced gates" with the honest boundary stated: hooks fire **in Claude Code sessions** — they gate *the agent's* actions, not a human in a plain terminal; and the hook wiring itself is config (an adopter/user can remove it — it's tamper-evident in git, not tamper-proof).
5. **Dogfood here first** (user decision): wired into THIS repo's `.claude/settings.json` + DoD; adopter `init`-wiring is a follow-up (sequenced after #6's plugin-read rework, which changes how init ships files).
6. **ROADMAP restructure:** #5's row reshaped (land-gate core); a new item added directly after: **"Autopilot flip — build mode's autopilot goes live: batch spec-approval up front → unwatched Implement→Verify→Land to the stop-signal → irreversible hard-stops remain → end summary"** (its own plan, with a product-designer pass on the unwatched UX).

**Non-goals**
- **No autopilot flip in this plan** (user decision — separate follow-up).
- **No adopter init-wiring** (dogfood first; follow-up after #6).
- **No ride-along mini-gates** (README agent-count · no-ignored-tree-files stay LATER per their triggers).
- **No always-on edit-blocking heuristic** (rejected at Discuss: blocking any source edit when tests are missing would obstruct legitimate feature work; intent must be declared).
- **No write-time secret hook** (YAGNI for now: the land-gate placement catches everything before it can *land*, which is the trust boundary; a write-time layer can be added if a real need surfaces — ROADMAP note).
- **No entropy-based secret detection** (high false-positive rate; known-pattern regex only, scope stated honestly).

## Approach

### Slice 1 — the land-gate (the core)
- **`scripts/hook_land_gate.py`** (stdlib-only, mirrors the sibling gates' house style): reads the `PreToolUse` JSON from stdin; **fast no-op exit 0** unless the Bash command matches a `git commit`/`git push` invocation (word-boundary regex; handles `&&` chains); on match, runs the suite — `pytest -q`, `check_architecture_tree.py`, `check_versions_synced.py` (+ `check_no_secrets.py` once Slice 2 lands, discovered dynamically so Slice 1 doesn't dangle) — and on any failure **exits 2** with a plain, actionable stderr message (which gate failed + how to see it). Fail-LOUD on its own breakage (a crashed hook must not fail-open silently — exit 2 with the error).
- **`tests/test_hook_land_gate.py`** — hermetic: stdin-JSON parsing (commit/push/chained/non-git commands), block-on-red (suite runners mocked), pass-on-green, the fail-loud-on-crash path, non-Bash tool input ignored.
- **Wiring:** `.claude/settings.json` gains the `PreToolUse` → `Bash` matcher entry.
- **Copy:** WORKFLOW DoD — the deterministic gates are now **hook-enforced at the land boundary in this repo** (run-gates remain runnable any time); the honest boundary (agent-session scope; config-removable/tamper-evident) stated once in the DoD area. README's mechanical-claims paragraph updated the same way. ROADMAP #5 row reshaped + the autopilot-flip item inserted. DECISIONS. → `0.1.12`.

### Slice 2 — the secret-scan
- **`scripts/check_no_secrets.py`**: scans the **staged diff** (`git diff --cached`) — added lines only — for a lean, named pattern set: AWS access/secret keys · private-key PEM headers · GitHub/Slack/OpenAI/Anthropic-style token prefixes · `password|secret|token = "<literal>"` assignments with real-looking values. Plain block message naming file+line+pattern-class (never echoing the full secret). Runnable standalone (DoD run-gate) **and** invoked by the land-gate.
- **`tests/test_check_no_secrets.py`** — hermetic: each pattern class caught · clean diff passes · the message redacts · removed-lines ignored · garbled input fails loud.
- **Copy:** DoD entry (honest scope: known patterns, risk reduction); README one-liner. → `0.1.13`.

### Slice 3 — the characterization hook (declared intent)
- **The state contract:** a small `.claude/harness-state.json` (gitignored; never tree-listed): `{"refactor_in_flight": bool, "baseline_recorded": bool, "item": "<title>"}`. **Written by the workflow/build mode** at tag→discipline time (build SKILL step 2 + the WORKFLOW tag-table row instruct the declaration); `baseline_recorded` set when the baseline lands (tests green + characterization tests for the touched behavior committed); cleared at land.
- **`scripts/hook_characterization.py`** (`PreToolUse` → `Edit|Write`): no-op exit 0 unless `refactor_in_flight && !baseline_recorded` AND the target path is a **source file** (reuses the gate family's source-detection: `INCLUDE_GLOBS`/`SOURCE_EXTS`, doc files exempt so the plan/tree/DECISIONS stay editable); then **exit 2** with the WORKFLOW's own pause narration ("Before I tidy this code I need to capture what it currently does as a test…").
- **`tests/test_hook_characterization.py`** — hermetic: state-file absent → no-op · declared+no-baseline+source-edit → block · baseline recorded → pass · doc edits always pass · corrupt state fails loud (blocks, never fail-open).
- **Copy:** the WORKFLOW tag-table caveat **retired** ("now hook-enforced after declaration; the declaration itself is model-upheld"); build SKILL step 2 declares; the honest split stated. DECISIONS. → `0.1.14`.

### Honesty framing (the heart of the copy work)
- **What's genuinely mechanical:** *after wiring*, a red commit / an undeclared-baseline refactor edit / a pattern-matched secret **cannot pass through the agent's tools**. That's real, new, and the strongest claim the harness has ever made.
- **What stays model-upheld and is said plainly:** the refactor *declaration* (a model writes the state file) · the hook wiring is config (removable; git makes removal visible — tamper-evident, not tamper-proof) · hooks gate the agent's session, not a human terminal · the secret patterns are a known-set, not omniscience.
- The honesty-reviewer audits exactly these boundaries at Plan and Verify.

### Alternatives considered & rejected
Always-on heuristic blocking (obstructs legitimate work — intent must be declared) · write-time secret hook now (the land boundary is the trust boundary; YAGNI) · entropy detection (false-positive noise) · folding the autopilot flip in (separate product-heavy item, user decision) · extending `check_architecture_tree.py` instead of new scripts (SRP — one gate, one invariant, per the 0006 sibling-gate precedent).

## Affected files
**S1:** `scripts/hook_land_gate.py` + `tests/test_hook_land_gate.py` (new) · `.claude/settings.json` · `docs/WORKFLOW.md` (DoD) · `README.md` · `docs/ROADMAP.md` (#5 reshape + autopilot-flip item) · `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · manifests → `0.1.12`.
**S2:** `scripts/check_no_secrets.py` + `tests/test_check_no_secrets.py` (new) · `docs/WORKFLOW.md` (DoD entry) · `README.md` · tree/DECISIONS · manifests → `0.1.13`.
**S3:** `scripts/hook_characterization.py` + `tests/test_hook_characterization.py` (new) · `.claude/settings.json` · `.gitignore` (the state file) · `docs/WORKFLOW.md` (tag-table caveat retired) · `skills/build/SKILL.md` (step 2 declares) · tree/DECISIONS · manifests → `0.1.14`.

## Risks & mitigations
- **Hook latency** (fires on every Bash/Edit call) → fast no-op path first (string/regex check before any work); the suite only runs on actual commit/push.
- **Fail-open on hook crash** → explicit fail-loud (exit 2 + error); characterization tests for the crash path (the empty-globs lesson).
- **The land-gate blocks ITS OWN landing commits** (recursion: committing Slice 1 runs the new hook) → that's the dogfood working; the suite must be green anyway.
- **Over-claiming "mechanical"** → the honest-boundary copy (agent-session scope · tamper-evident config · declared intent); honesty-reviewer at both gates.
- **The state file drifts/stales** (a refactor declared but the session dies) → state is per-item and cleared at land; a stale `refactor_in_flight` blocks edits with a message that names the file and how to clear it honestly (never silently ignores it).
- **Windows/cross-platform** → stdlib-only Python, same as the proven gates; hooks already run on this Windows repo.

## Test strategy
Each slice ships **real hermetic unit tests** (pytest grows from 61). Plus: (1) the run-gates green at each slice; (2) a **live dogfood check** per slice — S1: attempt a deliberately-red commit in a temp state and observe the block; S3: declare a refactor and observe an edit block; (3) Stage-7 cross-model panel per slice; (4) the honest-boundary copy audited by the honesty-reviewer.

## Decomposition (slices)
- [ ] **Slice 1 — the land-gate.** The core mechanism + wiring + the DoD/README honest reframe + the ROADMAP restructure. **Lands complete:** a red commit is mechanically blocked in this repo; copy honest; gates green. → `0.1.12`
- [ ] **Slice 2 — the secret-scan.** The scanner + tests, folded into the land-gate suite + DoD. **Lands complete:** a pattern-matched secret cannot land; scope stated honestly. → `0.1.13`
- [ ] **Slice 3 — the characterization hook.** The declared-intent contract + hook + tests + the WORKFLOW caveat retirement + build-mode declaration. **Lands complete:** a declared refactor cannot touch source before a baseline; the model-upheld/mechanical split stated. → `0.1.14`

---

## Review *(Stage-3 — diverse panel, judges cross-model)*
- **Verdict:** _pending_

---

## Spec *(per slice, after Review passes)*
_To be written once the plan passes Stage-3 review._
