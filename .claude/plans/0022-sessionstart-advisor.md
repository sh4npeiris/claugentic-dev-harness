# 0022 — SessionStart advisor + status surface

- **Status:** Implemented (2026-06-17 — D1 + D2 landed in the working tree; all gates + 144 pytest + 344 node green) — awaiting the live SessionStart smoke check (needs a reinstall + restart to confirm `${CLAUDE_PLUGIN_ROOT}` resolves in a hook command)
- **Resumable from:** D1 + D2 done; remaining = the live smoke check on an installed plugin (init-wiring fallback named if `${CLAUDE_PLUGIN_ROOT}` doesn't resolve)
- **Blockers:** none (independent of 0020/0021; sequence anywhere after the ruler)
- **Roadmap item:** Harness distillation effort — mechanism upgrade P6 (SessionStart advisor; the other P6 items deferred to ROADMAP)
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · diagnostic findings FWD-1/FWD-3/FWD-4 · hooks API confirmed via claude-code-guide (SessionStart + plugin-bundled hooks + `additionalContext`/`systemMessage`)

## Problem

The harness already **derives** resumable state (backlog fences + in-flight `.claude/plans/*` + the CLAUDE.md managed-fence version) but never **volunteers** it. A returning or new user has no "where am I / what to run next / what's in flight" surface; the single most common non-engineer stall is "which of init/product/audit/build do I run now?" (diagnostic FWD-1/FWD-3/FWD-4). The state exists, scattered; nothing renders it.

## Goals / Non-goals

- **Goal:** Once per session, surface ONE plain-English line — recommended next step + any in-flight work — derived from existing artifacts, plus inject the same as `additionalContext` so the agent can act on it.
- **Goal:** Zero steady-state overhead; **silent when there's nothing actionable** (fresh repo / no fences / no plans) — never nag.
- **Goal:** Auto-wired on install, no per-adopter settings change, read-from-install-path (no copy, no drift).
- **Non-goal:** Any new state store — strictly derive-don't-store (reads existing fences/plans).
- **Non-goal:** Per-prompt or per-tool-call surfacing — **REJECTED-BY-PRINCIPLE.** SessionStart only.
- **Non-goal:** Asserting anything new — it reports what the fences SAY; it is an advisor, not an authority (honesty register).
- **Non-goal (this plan):** The other P6 upgrades (PreToolUse guard, cross-model-tag surfacing, context-budget dial) — deferred to ROADMAP.

## Approach

A deterministic (no-LLM) Python script `scripts/claugentic-advisor.py` (fits the existing `scripts/` gate-script pattern), wired as a **plugin-bundled `SessionStart` hook** (the harness's first bundled hook) via `hooks/hooks.json` (or inline `plugin.json`), matcher `startup` + `resume`, command **`python "${CLAUDE_PLUGIN_ROOT}/scripts/claugentic-advisor.py"`** (the `python` prefix is REQUIRED — every existing hook uses it; a bare `.py` won't run on Windows). Confirmed API: the hook exits 0 and emits JSON `{ systemMessage, additionalContext }` on stdout. **Caveat:** `${CLAUDE_PLUGIN_ROOT}` inside a hook *command* is unproven in this repo (the one wired hook uses `${CLAUDE_PROJECT_DIR}`); D2's smoke check proves resolution on an installed plugin, with init-wiring into settings.json as the named fallback.

- **Reads (derive-don't-store):** the backlog fences `harness-audit:backlog` / `harness-product:backlog` in **`docs/claugentic-ROADMAP.md`** (pinned — written there by `skills/audit/SKILL.md:321` + product gap mode), in-flight `.claude/plans/*.md` (Status + Resumable-from), and **optionally** the CLAUDE.md `harness:managed` fence version (**adopter-only — absent in this source repo, so the advisor gracefully skips that input here**, never a dead-branch crash).
- **Computes:** the single highest-value next step (e.g. "no product spec yet → /product", "3 Tier-1 audit items → /build", "2 plans in flight → resume X") + an in-flight summary.
- **Emits:** `systemMessage` = the one user-facing line; `additionalContext` = the same compact state for the agent. **Budgeted to one tight line each** (it would be ironic to fix tree bloat then bloat every session — the advisor's own output is size-capped).
- **Silent path:** nothing actionable → no `systemMessage` (empty/suppressed), minimal/no `additionalContext`.
- **Fail-safe:** any error (missing files, parse failure, non-repo) → exit 0 with no output. A SessionStart hook must NEVER block or slow a session (mirrors the tree gate's `--hook-write` returning 0 on git failure).
- Alternatives rejected: init-wiring into the adopter's settings.json (the bundled hook is cleaner + auto-wired); a JS/engine implementation (deterministic file-read fits a `scripts/` Python gate, not a Workflow script); a per-prompt refresh (rejected-by-principle overhead).

## Affected files

- `scripts/claugentic-advisor.py` — **new.** Pure derive-the-next-step logic + the SessionStart JSON contract + fail-safe + manual-run CLI.
- `tests/test_advisor.py` — **new.** Hermetic: fence/plan fixtures → expected line; silent-when-empty; fail-safe-on-bad-input; output size cap.
- `.claude-plugin/plugin.json` (or new `hooks/hooks.json`) — declare the bundled SessionStart hook.
- `docs/claugentic-ARCHITECTURE_TREE.md` — entries for the new script + test (within the A1 budget).
- `docs/claugentic-DECISIONS.md` — the first-bundled-hook decision + the derive-don't-store advisor + the rejected per-prompt overhead.
- `docs/claugentic-PLAYBOOK.md` — one line: the harness greets you with where-you-are / what's-next.

## Research / grounding

- **Hooks API (confirmed, claude-code-guide):** SessionStart fires once per session (startup/resume/clear/compact matchers); JSON output supports `systemMessage` (to user) + `additionalContext` (to agent) + `suppressOutput`; plugins bundle hooks in `hooks/hooks.json` or inline `plugin.json`, auto-wired on install; zero steady-state cost. PreToolUse blocking confirmed (for the deferred roadmap guard).
- **Existing patterns to reuse:** the `scripts/` gate-script shape (fail-loud-or-safe, hermetic tmp_path tests, forward-slash normalization, `${CLAUDE_PLUGIN_ROOT}` read-from-install); the build skill's resume contract (`skills/build/SKILL.md:513` — derive the worklist from fences + plans) is the exact state-derivation this script renders.
- **Findings:** the architecture tree notes "bundled hooks/gates not yet shipped" — this is that step; opens a (deferred) option to migrate the tree-gate hook to bundled too.

## Risks & mitigations

- **Nag / noise** → silent-when-nothing-actionable is a HARD acceptance criterion; the line is genuinely useful or absent.
- **A SessionStart error degrades every session** → fail-safe exit 0, bounded local reads only, no network, no writes.
- **`additionalContext` bloats sessions** → output size-capped (one tight line each); the advisor is budgeted like any managed surface.
- **Cross-platform + hook-var resolution** → the command uses the **`python` prefix** (like every existing hook) + forward-slash handling like the tree gate; `${CLAUDE_PLUGIN_ROOT}`-in-a-hook-command is **unproven here** (the wired hook uses `${CLAUDE_PROJECT_DIR}`) → D2's live smoke check is the proof, and **init-wiring into settings.json is the named fallback** if bundled resolution fails.
- **Managed-fence input is adopter-only** → this source repo's CLAUDE.md has no `harness:managed` fence, so the version input is *optional* and silently skipped here (not a dead branch); the smoke that exercises it runs against an adopter repo that has the fence.
- **First bundled hook regresses install** → additive; the tree-gate init-wiring is untouched; an adopter without the plugin simply never gets the hook.

## Test strategy

Deterministic + hermetic (`tests/test_advisor.py`, tmp_path): fence+plan fixtures → the expected recommended line; empty/fresh repo → silent (**hard assertion: NO `systemMessage`/`additionalContext` keys at all** on the silent path); malformed fence / missing plan / non-repo / absent managed-fence → fail-safe exit 0, no crash; **hard assertion on the output size cap (explicit byte/line ceiling)** — this slice exists to fix bloat, so the cap is tested, not just intended. No live session needed for D1 — the pure renderer is unit-tested; the hook wiring is verified by inspection + a real-session smoke check (D2).

## Decomposition (slices)

- [x] **D1 — Advisor script.** `scripts/claugentic-advisor.py` — pure `recommend_next(state)` logic + state-derivation from the `docs/claugentic-ROADMAP.md` fences + plans (+ optional adopter-only managed-fence, gracefully skipped when absent) + the SessionStart JSON contract + fail-safe + a minimal manual-run CLI (its consumer is the D2 smoke check + the tests, not a user feature); `tests/test_advisor.py` (hard size-cap + silent-path assertions). Lands complete: a deterministic, tested advisor.
- [x] **D2 — Bundle as a SessionStart hook.** Declare the plugin-bundled hook (`hooks/hooks.json` / `plugin.json`, matcher startup+resume, command **`python "${CLAUDE_PLUGIN_ROOT}/scripts/claugentic-advisor.py"`**); tree entries (within the A1 budget); DECISIONS entries (first bundled-hook distribution class · derive-don't-store advisor · rejected per-prompt overhead); PLAYBOOK line. **The advisor is NOT a gate — it must not appear in the DoD gate list** (it advises, doesn't enforce; adding it would be the over-claim the harness forbids). Lands complete: auto-wired on install, **smoke-checked in a real installed-plugin session** proving `${CLAUDE_PLUGIN_ROOT}` resolves (init-wiring fallback named if not). *(Depends on D1.)*

## In-scope Verify dimensions

maintainability-structure (script SRP/DRY) · testing (deterministic coverage) · product-ux (the surfaced line — clarity, silent-when-empty, no-nag) · **honesty-reviewer** (derive-don't-store, advisor-not-authority, no over-claim) · docs-traceability.

---

## Review  _(filled by plan-reviewer, Stage 3)_

> `RUNNING AS: Opus 4.x` — cross-model vs a builder default of `opus` is **not** achieved on this run; if the builder is also Opus, treat this as a **same-model review — the judge and the builder are the same model family here** (shared-blind-spot risk not reduced).

- **Verdict:** **CHANGES REQUIRED** (5 required changes; none are fatal to the design — the bundled-hook approach is sound and the path choice is right. These are concrete gaps that would otherwise surface mid-implementation or at the smoke check.)

- **Required changes:**

  1. **Pin the fence file path — it is `docs/claugentic-ROADMAP.md`, not a file named after the fence.** Approach line 27 says "the backlog fence file … implementer pins the path from the audit skill" and Affected-files never names it. I verified it: `skills/audit/SKILL.md:321` writes `harness-audit:backlog` and `skills/product/SKILL.md` writes `harness-product:backlog`, **both into `docs/claugentic-ROADMAP.md`** (confirmed at `docs/claugentic-ROADMAP.md:11-13` and `:19-21`; the resume contract `skills/build/SKILL.md:519` says the same). The plan must state `docs/claugentic-ROADMAP.md` + the two exact markers as the read source so the implementer doesn't re-derive it (and so the test fixtures match reality). This is a derive-don't-store contract; the source-of-truth path belongs in the plan, not in the implementer's head.

  2. **The CLAUDE.md `harness:managed` fence does NOT exist in THIS repo — only in adopters.** The advisor's third input (Goals line 11, Approach line 27: "the CLAUDE.md managed-fence version") is written by `init` into an *adopter's* CLAUDE.md (`skills/init/SKILL.md:57-62`); a `grep` for `harness:managed:start` in this repo's `CLAUDE.md` returns **nothing**. So D1's claim "*a deterministic, tested, manually-runnable advisor (usable even before wiring)*" is **false when dogfooded against this repo** — the managed-fence read has no source here, and a naïve implementation either errors (caught by fail-safe, but then that input silently never fires) or the tests pass against a fixture that the real dogfood repo doesn't match. Decide and state explicitly: (a) the managed-fence read is **adopter-only** and absent-in-source is a normal silent path (not an error), AND (b) the smoke check (D2) must run against a repo that actually HAS the fence (an adopter or a fixture), because this repo can't exercise that branch. Without this the "fail-safe" masks a permanently-dead input.

  3. **The hook command is missing the `python` interpreter and will not run cross-platform.** Approach line 25 proposes the command `"${CLAUDE_PLUGIN_ROOT}"/scripts/claugentic-advisor.py` — executing the `.py` directly. Every existing hook in this repo invokes the interpreter explicitly: `.claude/settings.json:9,19` (`python scripts/…`) and `skills/init/SKILL.md:417-418` (`python "${CLAUDE_PROJECT_DIR}/scripts/…"`). On Windows a bare `.py` path depends on the Python launcher file-association / `PATHEXT` and is exactly the cross-platform fragility the plan's Risks section (line 54) claims is handled. Pin the command to **`python "${CLAUDE_PLUGIN_ROOT}/scripts/claugentic-advisor.py"`** (mirror the tree hook's proven shape), and fix the Risks line so it doesn't over-claim "OS-agnostic" for a form that isn't.

  4. **`${CLAUDE_PLUGIN_ROOT}` inside a hook `command` is unproven in this repo — make the smoke check prove it, don't assume it.** All 12 current uses of `${CLAUDE_PLUGIN_ROOT}` are Workflow-tool `scriptPath` args (`engine/*.js`) or SKILL prose — **none is a hook command**; the one wired hook uses `${CLAUDE_PROJECT_DIR}` instead. The plan rests the whole bundled-hook design on `${CLAUDE_PLUGIN_ROOT}` resolving in a `SessionStart` hook command on an installed adopter. The Test strategy (line 59) downgrades wiring to "verified by inspection + a manual session smoke check" — that is too weak for the load-bearing, first-of-its-kind claim. Make D2's acceptance criterion explicit: **smoke-check on an actually-installed plugin (not the dogfood working tree)** that the hook fires and resolves the path; if `${CLAUDE_PLUGIN_ROOT}` does not resolve in a hook context, the fallback (init-wiring with `${CLAUDE_PROJECT_DIR}`, the very alternative the plan rejects at line 32) must be named as the contingency rather than discovered at smoke time.

  5. **Add a regression/snapshot test pinning the output size cap as a *byte/line assertion*, and pin the silent-path contract as an exact empty-output assertion.** The plan lists "output size cap" and "silent-when-empty" as test cases (lines 37, 59) but the honesty stakes here are high: this slice exists to *fix* context bloat, so the test must assert a concrete ceiling (e.g. `systemMessage` and `additionalContext` each ≤ N chars/one line) and that the silent path emits **no** `systemMessage` and **no** `additionalContext` (not an empty-but-present key that still costs tokens). Make these hard `assert`s, not prose intentions — consistent with the repo's "verbatim drift pin" test discipline (`tests/workflows/cross-script.test.mjs`).

  _Soundness notes that PASS (do not change):_ silent-when-empty is correctly a hard criterion and is the right no-nag posture; fail-safe-exit-0 is correctly modelled on the tree gate's git-failure path; **derive-don't-store / advisor-not-authority is genuinely preserved** — it reports what the fences say and asserts nothing new (honesty register intact); the per-prompt variant is correctly rejected-by-principle (line 19); Stage-0 path choice (full pipeline as a sub-plan of 0020's P6) is right — this is a new bundled-hook subsystem touching the manifest, not a lightweight change. The "additive, tree-gate untouched, adopter-without-plugin gets nothing" claim is **true**: the tree hook lives in the adopter's `.claude/settings.json` (init-wired), the advisor lives in the plugin manifest — disjoint surfaces, no interaction.

- **Sizing/completeness:**
  - **D1 (script + tests) — OK on size, but completeness is conditional on Required-change #2.** As written, "lands complete, usable even before wiring" is not true while the managed-fence input has no source in this repo. Once #2 reframes that read as adopter-only-silent and the tests use explicit fixtures, D1 lands vertically complete in one session. No split needed.
  - **D2 (bundle + docs) — OK on size, but the smoke check is the real acceptance gate (Required-change #4), and the docs list is right.** Keep D2 as one slice; it is small (manifest declaration + tree/DECISIONS/PLAYBOOK lines). **Do NOT merge D1+D2 into one slice** — the split is correct: D1 is pure-logic + hermetic tests (no platform dependency), D2 is the platform-wiring + live smoke check (the only part that can't be unit-tested). That seam is exactly where a one-session boundary belongs.
  - **YAGNI — cut or justify the "manual-run CLI."** Affected-files line 36 and D1 both add a "manual-run CLI" path. The only stated consumer is the hook (which pipes JSON on stdin/stdout). A separate human-facing CLI mode is speculative second-interface scope unless the smoke-check procedure (#4) actually needs to invoke the script by hand — in which case say *that* is its one consumer and keep it dead-simple (run → print the line), not a parallel UX. Otherwise cut it: the hermetic unit tests already exercise the pure renderer without a CLI. (Everything else in the plan is appropriately minimal — the deferred P6 items are correctly parked to ROADMAP.)

- **Harness impact:**
  - **This is the FIRST plugin-bundled hook — it needs a `docs/claugentic-DECISIONS.md` entry under "Plugin identity & distribution" recording the new distribution class** (read-from-install hook, auto-wired via the manifest, distinct from the init-wired tree hook in the adopter's `settings.json`). The plan lists a DECISIONS entry (line 40) but frame it as establishing the *pattern* for any future bundled hook, and record the `${CLAUDE_PLUGIN_ROOT}`-in-hook-command resolution result from the smoke check (Required-change #4) as a verified fact — this is the kind of "verified fact worth keeping" the DECISIONS file already curates (e.g. `:73`).
  - **Architecture-tree entry must stay within the new per-entry form budget** that plan 0020 Phase 0 introduces (`MAX_ENTRY_CHARS`, `scripts/claugentic-check_architecture_tree.py`). Since 0022 is a sibling P6 item under the same 0020 distillation effort, the new `scripts/claugentic-advisor.py` + `tests/test_advisor.py` tree lines must be authored to that budget or the tree gate will fail — note this dependency-on-0020-ordering in the plan (or state 0022 is independent of it, per Status line 5, and the entries are budget-clean regardless).
  - **No new STANDARD or agent required** — the advisor is deterministic, no-LLM, no judge spawn; it does not touch the cross-model panel, the standards catalog, or the role library. Correctly scoped.
  - **WORKFLOW DoD impact: none** — the advisor is not a gate (it advises, it doesn't pass/fail). Confirm the plan does NOT add it to the Definition-of-Done gate list (it must not — that would launder an advisor into apparent gate authority, the exact honesty violation the harness forbids).

---

## Spec  _(per slice, after Review passes — Stage 4)_
_Expanded after plan-review, in the batch-approval roster._

## Audit deltas (confirmed 2026-06-17)

The advisor's `Computes` gains three derive-only branches (no new store):
- **plan age** via `git log -1 --format=%cr -- <planfile>` (omit silently if git unavailable) — so a user away "days" can tell stale from fresh (RETURN-2).
- **paused audit (PARTIAL):** if a backlog fence's status line reads PARTIAL, surface "your last audit/gap run was partial — re-run to finish" (RETURN-3, one status-token check, not a new input).
- **advisory-not-authority:** prefix `additionalContext` with "Derived suggestion (confirm before acting):" so a SessionStart injection never silently auto-drives a resume past build's deliberate re-confirm gate (RETURN-6).
