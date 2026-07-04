# 0031 — Model-tier menu + platform advisor awareness (+ SessionStart-advisor rename)

- **Status:** Draft (fine-tuning pass; verified against real docs 2026-07-03)
- **Resumable from:** Slice 1 — not started. **Blockers:** none. Additive; does NOT touch 0029/0030's landed work.
- **Disposition at close:** done / deferred (ROADMAP) / rejected (DECISIONS) per slice.
- **References:** `.claude/plans/FINETUNING-INPUTS.md` → VERIFIED section · Claude Code docs `model-config`, `advisor`, `the-advisor-strategy` blog · `docs/claugentic-WORKFLOW.md` → *Model tiers* (`:38`) · `scripts/claugentic-advisor.py` + `tests/test_advisor.py` · `.claude/settings.json`.

## Problem

Two verified, grounded gaps:
1. **The WORKFLOW model-tier note is stale + thin.** It says "most capable = `opus`" — but the real menu now has **Fable 5** (`best`/`fable`) as the most-capable tier *for long, multi-sitting work* (deep audits, build-to-green, long research), plus **`opusplan`** (opus-plan→sonnet-execute) and `[1m]` variants. Fable is **not default**, access is **conditional** (temporary/limited), and `best` **auto-falls-back to Opus** — so the harness should present the menu with *graceful degradation*, never hardcoding Fable.
2. **The platform advisor is a genuinely new lever the harness hasn't adopted, AND its name collides with ours.** The Claude Code `/advisor` (`advisorModel` setting, `--advisor` flag) escalates to a **stronger model at decision points** (before committing to a plan · on a recurring error · before declaring done) — exactly the harness's gate/verify junctures. But it is **Anthropic-API-only, experimental (v2.1.98+, beta header), subagents inherit**. Separately, the harness already ships `scripts/claugentic-advisor.py` — a **SessionStart context/nudge hook** that is a *completely different thing* — so adopting the platform advisor would create a "which advisor?" confusion.

## Goals / Non-goals

- **Goal:** Update the WORKFLOW *Model tiers* note to the real menu with graceful positioning: **`best` (Fable→Opus fallback) for the hardest/longest work · `opusplan` for hybrid plan-mode · `opus` the standard-judgment default · `sonnet` routine · `haiku` mechanical** — and the explicit rule **never hardcode Fable / always provide an Opus fallback** (a user's Fable access can be temporary). Note `opusplan` as a coarse built-in complement to the finer per-agent `model:` frontmatter.
- **Goal:** Make the harness **advisor-AWARE** — document the platform advisor as an optional lever for the gate/verify roles (escalate at commit-to-plan / recurring-error / before-land), **behind an env/feature flag + a version-floor re-check**, with the API-only/experimental constraint stated. **Model-upheld invocation** (the model consults the advisor; nothing mechanical fires it).
- **Goal:** **Rename `scripts/claugentic-advisor.py`** (+ its test + all refs: `plugin.json` SessionStart hook, `CLAUDE.md`, tree, DECISIONS) to a name that conveys "SessionStart context/resumption advisor" (e.g. `claugentic-session-advisor.py`) — a pure clarity refactor, no behavior change — so the two "advisors" aren't confused.
- **Non-goal:** REQUIRING the platform advisor. It's optional, experimental, API-only — never a hard dependency; adopters on Bedrock/Vertex/Foundry must be unaffected.
- **Non-goal:** Building any mechanical advisor-selection. Invocation is model-upheld.
- **Non-goal:** Changing the harness's accuracy-first tier *policy* (keep it; just widen the menu).

## Approach

Three thin, low-risk edits. **The rename is the only one touching executable wiring** (the SessionStart hook command in `plugin.json` + the script filename + its test) — do it carefully with the tree-check + tests. The model-tier + advisor-awareness edits are docs (WORKFLOW/CLAUDE.md). The advisor adoption is **documented as available-behind-a-flag**, not wired on by default (experimental/API-only → must degrade gracefully).

**Honesty is load-bearing:** the model-tier note must say Fable access is conditional (never assert it's available); the advisor note must say experimental/API-only and that invocation is model-upheld (never claim the harness "uses a stronger judge" as a guarantee — DECISIONS already forbids cross-model-independence claims; the advisor is a *reduction* of single-model risk, honestly framed, not model-independent verification).

## Architecture & holistic fit

- **Codebase fit:** WORKFLOW/CLAUDE.md (docs) + the advisor-script rename (`scripts/` + `tests/` + `plugin.json` hook ref + `.claude/settings.json` if referenced). The rename touches the SessionStart hook command — verify the portable `python3 … || python …` launcher + rooted `${CLAUDE_PLUGIN_ROOT}` form stay intact (DECISIONS → the advisor launcher).
- **Quality dimensions:** `docs-traceability` (primary — the model-tier menu + advisor refs resolve; the rename updates every ref) · `maintainability-structure` (the rename is a clean clarity refactor) · `product-ux` (plain-English tier guidance). Trust surface → `honesty-reviewer` (Fable-conditional / advisor-experimental / model-upheld-not-independent-verification).
- **Honesty invariant:** the advisor is a *reduction of single-model-blind-spot risk*, **never** "independent verification" (same-vendor). The model-tier note stays "accuracy first, conservation second" (existing policy).
- **Future-proofing:** the tier note is the single place to change if a tier is renamed; the advisor note is written so wiring it on (when it graduates from experimental) is a one-line settings change.

## Affected files

- `docs/claugentic-WORKFLOW.md` — rewrite the *Model tiers* note (`:38`) to the real menu + graceful-fallback positioning + the never-hardcode-Fable rule; note `opusplan`.
- `docs/claugentic-WORKFLOW.md` (or CLAUDE.md) — a short **advisor-awareness** note: the platform advisor as an optional gate/verify lever, behind a flag, experimental/API-only, model-upheld, honestly framed (not independent verification).
- `scripts/claugentic-advisor.py` → **rename** (e.g. `claugentic-session-advisor.py`); `tests/test_advisor.py` → rename + update imports/refs; `.claude-plugin/plugin.json` → update the SessionStart hook command path (keep the portable launcher + rooted form); `CLAUDE.md` → the advisor off-switch mention (`CLAUDE_HARNESS_ADVISOR`); `docs/claugentic-DECISIONS.md` → the advisor entries reference the new name.
- `docs/claugentic-ARCHITECTURE_TREE.md` — update the advisor-script row (new name) + WORKFLOW row if scope changes.
- `docs/claugentic-DECISIONS.md` — dated lines: the model-tier menu update; the advisor-awareness adoption (optional/experimental/flagged); the rename.

## Risks & mitigations

- **Risk: the rename breaks the SessionStart hook** (a wrong path = advisor silently stops firing). → **Mitigation:** update `plugin.json`'s hook command + the script path together; keep the portable `python3 … || python …` launcher + `${CLAUDE_PLUGIN_ROOT}` rooting; run `pytest tests/test_advisor.py` + confirm the hook command resolves. The advisor is fail-safe (exit 0) so a lapse is non-blocking, but verify.
- **Risk: over-claiming the advisor** (as independent verification, or as available). → **Mitigation:** `honesty-reviewer` — frame as optional/experimental/API-only + model-upheld + a *reduction* of single-model risk (never independent-verification, never guaranteed-available).
- **Risk: hardcoding Fable.** → **Mitigation:** the note prescribes `best` (auto-fallback) or explicit fallback chains; never Fable-required.
- **Risk: rename churn.** → **Mitigation:** grep every ref (`claugentic-advisor`) before + after; the tree-check catches a stale file-index row.

## Test strategy

- **Deterministic gates:** `pytest` (incl. the renamed `test_advisor.py`), `check_shipped_content.py` (the renamed script + refs — no dangling stripped-path/namespace literal), `check_versions_synced.py`, `check_doc_budgets.py`, `claugentic-check_architecture_tree.py` (the renamed script's row).
- **Rename verification:** `grep -r claugentic-advisor` returns only the intended new name; the `plugin.json` SessionStart hook command points at the new path.
- **Reviewer sign-offs:** `docs-traceability` + `maintainability-structure` + `product-ux` via `synthesizer-gate`; `honesty-reviewer` on the model-tier + advisor copy.

## Decomposition (slices)

- [x] **Slice 1 — Model-tier menu update (WORKFLOW docs).** LANDED — WORKFLOW *Model tiers* widened to the verified menu (`best`/`fable`/`opus`/`sonnet`/`haiku`/`opusplan`), graceful Opus fallback, never-hardcode-Fable; DECISIONS entry + condensation. Verify: synthesizer-gate PASS + honesty-reviewer CLEAN.
- [x] **Slice 2 — Advisor-awareness note (docs).** LANDED — platform-advisor note (optional/experimental/API-only/opt-in/model-upheld; reduction-of-risk NOT independent verification; distinct from the SessionStart advisor). Verify: synthesizer-gate PASS + honesty-reviewer CLEAN.
- [ ] **Slice 3 — Rename the SessionStart advisor script (clarity refactor). DEFERRED (ready-to-build).** Rename `claugentic-advisor.py`→`claugentic-session-advisor.py` + test + `plugin.json` hook + `CLAUDE.md` + DECISIONS + tree refs. **Plan-gate REQUIRED FIX (see Review):** must ALSO update `tests/conftest.py:46` (`_load_hyphenated("advisor", "claugentic-advisor.py")` — a fail-loud loader that breaks the WHOLE test suite if the path is stale); specify the internal `"advisor"` module name; update the script's own usage-text path (`scripts/claugentic-advisor.py:58`); drop the empty `.claude/settings.json` from scope. Verify the hook still fires (portable launcher/rooting intact). **In-scope:** `maintainability-structure`, `docs-traceability`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_

RUNNING AS: Opus 4.x (same-model as builder/planner — a clean-context, separate-role pass; a reduction of rubber-stamping risk, not model-independent review).

**Verdict: CHANGES REQUIRED** — one load-bearing omission in the Slice-3 rename enumeration (would break the whole test suite, not just `test_advisor.py`), plus two small honesty/scoping tightenings. The plan is otherwise sound: correctness matches the VERIFIED findings (not the dossier over-claims), honesty framing is right, slices are session-sized and land-complete, and it does not touch 0029/0030.

### Required changes (numbered, actionable)

1. **[BLOCKER — Slice 3] The rename enumeration misses `tests/conftest.py:46` — the single most dangerous ref.** `conftest.py` hardcodes BOTH the logical module name and the filename: `_load_hyphenated("advisor", "claugentic-advisor.py")` (`:46`), and the loader **fails loud (`ImportError`) if the file path is stale** (`:36-37`) — so a missed rename here breaks *every* test in the suite via collection error, not just `test_advisor.py`. Its docstring/comment at `:44` ("the SessionStart advisor (`import advisor`)") also names it. Add `tests/conftest.py` to *Affected files* (S3) and to the S3 checklist. This is the one ref that turns "fail-safe advisor" into "hard test-suite breakage," so it must be explicit, not left to the grep.

2. **[Slice 3] Decide + state the logical module-name policy.** The rename covers the *filename* (`claugentic-advisor.py` → `claugentic-session-advisor.py`), but the internal Python module identifier registered in `conftest.py` is the bare string `"advisor"` and `test_advisor.py` does `import advisor`. Say explicitly whether the logical name stays `"advisor"` (minimal churn — only the *filename* arg changes) or also becomes `"session_advisor"` (rename the test's import too). Either is fine; leaving it unspecified invites a half-done rename. Recommend: keep the logical name churn minimal but rename `tests/test_advisor.py` → `tests/test_session_advisor.py` for clarity-parity with the goal.

3. **[Slice 3] Add the in-file self-reference.** `scripts/claugentic-advisor.py:58` contains its own path in the help/usage text (`python scripts/claugentic-advisor.py …`). List "update the script's own usage/docstring self-reference" in S3 so the renamed file doesn't print its old name.

4. **[Minor — References/Affected] `.claude/settings.json` is empty (`{}`) and carries no advisor reference.** The plan lists it in *References* and *Affected files*. Since the advisor-awareness note (Slice 2) is doc-only + model-upheld (nothing is wired into settings), drop `.claude/settings.json` from Affected (or explicitly note "no settings edit — documented-behind-a-flag only, not wired"). Keeping it listed implies a settings change the Non-goals correctly forbid.

### Sizing / completeness check (per slice)

- **Slice 1 (model-tier menu, WORKFLOW `:38`) — OK.** Single doc edit + DECISIONS line. Lands complete. Note: the current `:38` note only lists `opus`/`sonnet`/`haiku` and says "most capable = opus" — the rewrite is a genuine correction, correctly Fable-*conditional* (`best`→Opus fallback, never hardcode Fable), matching the VERIFIED cluster. Ensure the rewrite stays consistent with the adjacent honesty line at `:37` (no cross-model-independence claim) — the two notes sit back-to-back.
- **Slice 2 (advisor-awareness note) — OK.** Doc-only, model-upheld, flag-gated, experimental/API-only, framed as a *reduction* of single-model risk (not independent verification). Honesty framing matches `:37` and the DECISIONS ban on de-correlation claims. Correctly does NOT wire anything on. Lands complete.
- **Slice 3 (rename) — OK on size, but under-enumerated (see #1–#3).** Once `conftest.py` + the module-name policy + the in-file self-ref are added, it lands complete with no dangle. The tree-check + `pytest` + a post-rename `grep -r claugentic-advisor` returning only the new name is the right closure check; keep it. Confirm the `plugin.json` portable `python3 … || python …` launcher + `${CLAUDE_PLUGIN_ROOT}` rooting stay byte-intact (DECISIONS `:107`) — the note already says this. The advisor's fail-safe exit-0 means a *runtime* lapse is non-blocking, but the `conftest` `ImportError` is NOT fail-safe — so #1 is a true blocker, not a nicety.

### Honesty check — PASS

Fable is Fable-*conditional* (never assumed available); `best` auto-falls-back to Opus; the advisor is optional/experimental/API-only/model-upheld and a *reduction* of single-model risk, not independent verification; doc-tier *policy* is unchanged (menu widened, accuracy-first kept). The plan correctly avoids the refuted/nuanced dossier items (no `/loop`-`/goal`-orchestration framing, no version-third-axis detector, no settings-wiring). Good.

### Harness impact

**No new hook, no new agent, no new STANDARD.** Slice 3 renames an *existing* SessionStart hook script (a clarity refactor); the hook must keep firing after rename — guarded by the `plugin.json`-together-edit + `pytest` + hook-path-resolves checks (adequate once #1 lands). Slices 1–2 are doc-tier updates to existing WORKFLOW/DECISIONS surfaces. No Stage-9 harness-mechanism change implied. Confirmed: does **not** modify 0029/0030's landed work (additive docs + an internal rename).

_Re-gate after the four changes land in the plan; expected → PASS._

## Spec  _(per slice, Stage 4)_
