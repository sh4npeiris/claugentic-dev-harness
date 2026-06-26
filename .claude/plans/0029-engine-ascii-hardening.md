# 0029 — Engine ASCII-hardening (0.3.1)

- **Status:** Plan-gate APPROVE-WITH-CHANGES — all 5 must-fixes FOLDED (2026-06-25): `×` is the load-bearing cell-key delimiter (+`·` status-line) → change atomically w/ a name-safe delim; suite is a tripwire (update test literals in lockstep); scanner = decoded-codepoint check + `.js` filter; cross-version resume noted. Ready to build S1→S2→Land→release.
- **Resumable from:** plan-gate → S1 ASCII-clean engine/*.js → S2 scanner ASCII-guard + version bump → Land (DECISIONS + retire plan) → PR + merge + release 0.3.1.
- **Blockers:** none.
- **References:** the DistrictSync adopter validation (2026-06-25) that surfaced this · `engine/*.js` (the 4 Workflow-orchestrated scripts) · `scripts/check_shipped_content.py` (the scanner to extend) · `scripts/build_release.py` (DEV_ONLY / ship set) · `.claude-plugin/{plugin,marketplace}.json` (version pair).

## Problem
Real-world adopter validation (DistrictSync, a 0.2.4→0.3.0 adopter) surfaced this: when the audit skill invoked the engine via the **Workflow tool**, the session's **permission handler rejected the script for "control characters,"** silently demoting the engine-orchestrated audit to **prose-fallback** (no script-mechanical guarantees). Investigation: `engine/*.js` contains **zero genuine control/zero-width chars** — but heavy **printable-unicode typography** (149 em-dashes in `audit.js`; plus `→ ⇒ ─ × · … ⚠ ≥ ≤ ∪ ∧ –`). Claude Code attributed the failure to *the adopter's* permission handler ("the tool input from the model was valid; configuration issue in your canUseTool/PermissionRequest hook/permission-prompt tool") — so it is **not** a harness defect.

**But** the engine path (mechanical orchestration) is the harness's core value-add, and it ships scripts that must pass through *arbitrary* permission/approval layers in every adopter session. Any layer strict about non-ASCII silently kills that value. **ASCII-only engine scripts are immune regardless of the handler** — a real, durable robustness win.

## Goals / Non-goals
- **Goal:** `engine/*.js` is ASCII-only (byte ≤ 0x7F), behavior unchanged; a regression guard prevents non-ASCII creeping back; release as **0.3.1**.
- **Non-goal (YAGNI — no demonstrated problem):** ASCII-cleaning the Python scripts (`scripts/*.py`). They run via the **Bash** tool (not the Workflow approval dialog) and already carry `_force_utf8_output()` for their em-dash output. Including them is undemonstrated scope creep — explicitly out.
- **Non-goal:** changing the adopter's permission handler (their config; the ASCII fix is the harness-side durable answer).

## Approach
**S1 — ASCII-clean `engine/*.js` (audit.js · build-item.js · qa.js · verify.js).** Replace every non-ASCII glyph with a readable ASCII equivalent. Substitution map (the full inventory from the 2026-06-25 scan):

| char | U+ | ASCII | typical context |
|---|---|---|---|
| `—` em dash | 2014 | ` - ` (spaced) / `--` (tight) | comment + log separators (149+122+137+41) |
| `→` arrow | 2192 | `->` | "X → Y" flow notes |
| `⇒` dbl arrow | 21D2 | `=>` | "if ⇒ then" notes |
| `─` box draw | 2500 | `-` | `// ─────` separators |
| `×` mult | 00D7 | ★ see Load-bearing | **cell-key DELIMITER — parsed, not display** |
| `·` middle dot | 00B7 | ★ see Load-bearing | **status-line separator (parsed) + prose lists** |
| `…` ellipsis | 2026 | `...` | trailing prose |
| `⚠` warning | 26A0 | `!` / `(!)` | warning log prefixes |
| `≥` / `≤` | 2265/2264 | `>=` / `<=` | thresholds in comments |
| `∪` union | 222A | `+` or `U` | "agents ∪ skills" set notes |
| `∧` logical-and | 2227 | `&&` or `and` | "bounded ∧ reversible" |
| `–` en dash | 2013 | `-` | stray |

**★ Load-bearing chars — change ALL sides atomically (plan-gate finding).** Two glyphs are NOT display — they are parsed delimiters in the audit cell-key / resume contract:
- **`×` (cell-key delimiter):** `cellKey` (`engine/audit.js:103`) + `BLINDSPOT_CELL` (`:107`) build `` `module×dir` ``; `parseCellKey` (`:355`) `indexOf("×")`-splits it; `renderStatusLine` (`:919`) serializes the keys into the audit fence's `done-cells`/`pending-cells`, which the audit SKILL re-parses on resume (`skills/audit/SKILL.md:217-218,385-387`). Replace `×` with a **name-safe ASCII delimiter — absent from module names (`[a-z-]+`) AND forward-slash scope paths** (so NOT `x`; use `::` or `|`, after confirming it's unambiguous in the fence format), changing **producer + parser + serializer + SKILL re-parse together**.
- **`·` (status-line separator):** in the status-line format + its shape regex (`~engine/audit.js:929`). Change the emit + the regex + any test literal together. (Its use as a plain prose list-separator elsewhere is display — `;` or ` - `.)

**The node suite is a TRIPWIRE, not a passive net (plan-gate).** It HARD-PINS these: `×` in ~15 `audit.test.mjs` assertions, the `·` status-line regex (`:929`), and `⚠`/`—` display tags in `qa.test.mjs:661,663`. So S1 edits the test literals **in lockstep** and expects red until updated — coverage of the emitted-format round-trip is strong, so a missed delimiter WILL fail a test (`node --test tests/workflows/*.test.mjs`, 372). Everything ELSE in the map (`—`/`→`/`⇒`/`─`/`…`/`⚠`/`≥`/`≤`/`∪`/`∧`/`–`) is comment/log/display — replace freely, updating any test that pins the exact display string. Zero behavior change is the bar.

**Cross-version resume (acceptable — state it).** A 0.3.0 audit fence carrying old `×`/`·` tokens, re-read by a 0.3.1 engine using the new delimiters, mis-splits on resume — but that's **transient in-flight single-session state** (the audit just re-runs those cells); no durable data is affected. Acceptable for a patch release.

**S2 — regression guard + version bump.** Add a **HARD (exit-1) ASCII-only pass** to `scripts/check_shipped_content.py` over shipped **`*.js`** (= `engine/*.js`): flag any non-ASCII codepoint (> 0x7F) — exact, unambiguous, no heuristic. ★ plan-gate: the existing scanner cores take UTF-8-decoded `{path:text}` maps, so the check is on **decoded codepoints > 0x7F** (equivalent to "any byte > 0x7F" for detecting non-ASCII, and consistent with the existing core); add a **`.js` filter** sibling to the existing markdown filter (NOT the markdown corpus). It's a new internal `evaluate()` pass — **no new wiring** (the scanner is already a CI + DoD run-gate, and is itself stripped — confirmed by the plan-gate). It must be GREEN after S1. Hermetic test (`tests/test_check_shipped_content.py`): a shipped `*.js` with a non-ASCII codepoint is FLAGGED (hard); an ASCII one is CLEAN. Bump **0.3.0 → 0.3.1** in BOTH `.claude-plugin/plugin.json` + `marketplace.json` (the version-sync gate enforces the pair).

**Land + release.** ONE DECISIONS line (the engine-ASCII rule + its provenance: the DistrictSync validation); retire this plan; rebuild `release`; **PR + merge to main + force-push release** (the user authorized the full cycle).

## Architecture & holistic fit
- **Codebase fit:** S1 is a mechanical source-hygiene pass on existing files (no logic change); S2 extends the existing shipped-content scanner with one more exact, hard pass (sibling to its dangling-path + namespace passes) — same SRP gate, one new rule. No new layer/file beyond the test additions.
- **Quality dimensions** (→ standards): **reliability-resilience** (the engine path no longer silently degrades under strict approval layers) · **maintainability/portability** (ASCII source is universally renderable) · **api-and-contracts** (the new guard is an exact mechanical check — honest to call it hard/mechanical, unlike the scanner's A.b heuristic).
- **Honesty:** the new ASCII pass IS genuinely mechanical/exact (byte check) — state it as such. The fix does NOT claim to fix the adopter's permission handler; it makes the harness robust regardless. Record the cause honestly (adopter handler) + the harness's defensive choice.
- **Future-proofing:** the guard means no future engine edit can reintroduce the failure mode.

## Affected files
**S1:** `engine/audit.js` · `engine/build-item.js` · `engine/qa.js` · `engine/verify.js` · `skills/audit/SKILL.md` (the resume re-parse of the cell delimiter, `:217-218,385-387`) · `tests/workflows/audit.test.mjs` + `tests/workflows/qa.test.mjs` (test literals pinned to `×`/`·`/`⚠`/`—` — update in lockstep).
**S2:** `scripts/check_shipped_content.py` (new ASCII pass) · `tests/test_check_shipped_content.py` (test) · `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (0.3.1).
**Land:** `docs/claugentic-DECISIONS.md` (the rule + provenance; condense-on-WARN if needed) · delete this plan.

## Risks & mitigations
- **Load-bearing delimiter** (the real risk): an ASCII substitution changes a parsed/round-tripped marker → mitigated by the 372-test node suite (run after S1) + per-char comment/log-vs-parsed review. If a test fails, fix the round-trip (both sides) or revert that one char.
- **Display-output churn:** engine log/backlog output changes from `—`/`→` to `--`/`->`. This is adopter-visible cosmetic output; acceptable (ASCII is more portable). No parser depends on the glyphs (verified by S1 review + tests).
- **Scanner scope:** the ASCII pass covers shipped `*.js` only (engine), NOT `*.py` (out of scope per Non-goals) — keeps it targeted; documented in the gate.
- **DECISIONS budget:** at ~86% post-0028; one short line fits, condense-on-WARN if it trips.

## Test strategy
- **S1:** the existing `node --test tests/workflows/*.test.mjs` (372) MUST stay green (the behavior-unchanged proof). `node --check engine/*.js` for syntax. The new scanner ASCII pass (added in S2) then proves the source is ASCII.
- **S2:** hermetic test for the ASCII pass (non-ASCII `*.js` flagged; ASCII clean; the pass is exit-1 hard). Full suite + all gates (tree, version-sync at 0.3.1, doc-budgets, the scanner itself) green.

## Decomposition (slices)
- [ ] **S1 — ASCII-clean `engine/*.js`.** Apply the substitution map across the 4 engine scripts; confirm comment/log/display-only (no broken parsed delimiter); `node --check` + the full 372-test node suite green (zero behavior change). Lands complete.
- [ ] **S2 — Scanner ASCII guard + 0.3.1 bump.** HARD ASCII-only pass over shipped `*.js` in `check_shipped_content.py` + hermetic test; bump both manifests to 0.3.1. Gate green on the cleaned tree. Lands complete.

## Land (after S2)
ONE `DECISIONS.md` line (engine-ASCII rule + DistrictSync provenance; condense-on-WARN) · delete this plan · rebuild `release` from the new main tip · **PR + merge + force-push release** (0.3.1) · `/plugin update`.

---

## Review  _(synthesizer-gate, plan-gate altitude, Stage 3)_

RUNNING AS: Opus 4.x

**Verdict: APPROVE WITH CHANGES.** The approach is sound, the scope decision (engine `*.js` only, not `scripts/*.py`) is correct and confirmed, the slicing/sequencing is right, and the scanner wiring needs no new surfaces. **But the plan's central safety claim mis-classifies the one genuinely load-bearing glyph** — `×` (U+00D7) is the structural cell-key delimiter, NOT display-only — and the substitution map at line 27 actively instructs the implementer to blind-swap it. That single correction is mandatory before build; the rest are tightening.

### Required changes (numbered, actionable)

1. **★ `×` (U+00D7) is LOAD-BEARING — pull it out of the blind-swap map and handle it consciously.** It is the structural delimiter in `cellKey` (`engine/audit.js:103` — `` `${moduleName}×${dir}` ``), the `BLINDSPOT_CELL` token (`:107` → `blindspot×(scope)`), and is parsed back via `key.indexOf("×")` in `parseCellKey` (`:355`). Worse, these tokens are **serialized verbatim into the persisted audit fence** — `renderStatusLine` (`:919`) writes `done-cells: [...]`/`pending-cells: [...]`, and the SKILL's resume contract reads them back on the next run (`skills/audit/SKILL.md:217-218, 385-387`). So `×` round-trips through *on-disk state the next session re-parses*. The substitution-map row at **line 27** files `×` under "3× / N×" display context and maps it to `x` — that misclassification is the single thing most likely to break this change.
   **Fix the plan:** (a) remove `×` from the "blind-swap, comment/log/display-only" treatment; (b) make S1 change it on **both** sides atomically — the `cellKey` template, `parseCellKey`'s split char, the `BLINDSPOT_CELL` literal, AND **the matching test literals** (see #2); (c) decide a safe ASCII delimiter — recommend `|` or `::` (NOT `x`: a module or dir name could legitimately contain the letter `x`, e.g. `…x-…`, silently corrupting `parseCellKey`'s "split on first separator"; `×` was chosen precisely because it can't occur in a name). Also update the now-doubly-stale comment at `:309-311` (it already says "`<module>x<dir>` (a literal multiplication sign)" — fix it to match the new delimiter).

2. **Re-frame the "372-test suite is the safety net" claim — it is a TRIPWIRE that goes RED, not a passive net, and S1 must update the pinned literals in lockstep.** The plan (lines 36, 54, 60) leans on "run the suite; zero behavior change is the bar." But the suite does not silently bless an ASCII swap — it **hard-codes the affected glyphs in assertions** and will FAIL loudly on a naive swap: `×` is pinned in ~15 places (`tests/workflows/audit.test.mjs:278, 282, 289, 303-305, 323-326, 709, 715-719, 731-739, 774-777, 926, 934-937`); the status-line `·` separator is pinned by the shape regex (`audit.test.mjs:929`); and the display tags `⚠`/`—` are pinned in `qa.test.mjs:661, 663` (and the audit verification-phrase tests). This is GOOD — the coverage is genuinely strong on the emitted-format round-trip, rebutting any "thin coverage" worry. But it means: **S1 must edit the test literals alongside the source**, and "zero behavior change" is true at the *runtime-behavior* level, NOT the *test-source* level (dozens of assertions change). State this in the plan so the implementer expects red tests and updates them deliberately rather than treating a failure as "I broke the round-trip." After S1, the swapped-delimiter round-trip must still pass (`cellKey`↔`parseCellKey`, the `renderStatusLine` shape, the interleave/budget tests).

3. **Spell out the cross-version resume-contract migration as an explicit, conscious decision.** Because the cell tokens persist in the adopter's audit fence on disk, a 0.3.0-written fence carries `×` tokens; a 0.3.1 engine that splits on the new delimiter will mis-parse a *resumed* in-flight audit (the module/dir recovery silently breaks). Add one line to Risks: this is acceptable (an in-flight audit fence is transient single-session state, a stale resume re-sweeps at worst), but it must be a *named* call, not a silent consequence. (No migration code needed — just the honest note.)

4. **Scanner ASCII pass must check RAW BYTES, not the decoded string.** The plan says "byte > 0x7F" (correct) but the existing scanner cores operate on `{path: text}` UTF-8-*decoded* maps (`check_shipped_content.py:272-279, 191-257`). A `char > '\x7f'` test over the decoded `str` checks **codepoints**, not bytes — which is actually fine and arguably *more* correct (it catches a >0x7F codepoint regardless of encoding), but it is NOT the "byte > 0x7F" the plan and `Goals` (line 14) describe. Pick one and be consistent: either (a) read the `.js` files as **bytes** and flag any `b > 0x7F` (matches the stated "byte ≤ 0x7F" contract literally), or (b) keep the decoded-string codepoint check and **re-word** Goals/S2 to say "codepoint > U+007F." Recommend (a) for a clean ASCII-byte guarantee and to avoid a decode step the other passes don't need on `.js`. Either way: confirm it scans `.js` files specifically (the other passes are markdown-only) — add a `.js` filter sibling to the `md_texts` filter at `:301`, and report the offending **byte offset / line:col** so a regression is locatable.

5. **Tighten two over-stated lines (otherwise honesty is good).** (a) Line 36 / line 60: replace "the full node suite is the safety net … a broken round-trip fails a test" with the tripwire framing from #2 (it's a red-test signal the implementer must resolve, including editing the assertions — not a passive guarantee). (b) The `architecture & holistic fit` "Honesty" bullet correctly calls the new pass mechanical/exact — keep it; it IS a deterministic check and the framing is honest.

### Sizing / completeness check (per slice)

- **S1 — ASCII-clean engine/*.js — OK (no split needed), but re-scope its content.** One specialist, one session: a mechanical hygiene pass over 4 files + the lockstep test-literal edits + the ONE conscious delimiter change (#1). Lands complete (suite green on the cleaned tree). The only risk is the `×` mis-handling (#1/#2) — with that corrected, sizing is fine. Do NOT split; the delimiter change and its test edits must land atomically in the same slice or the suite is red between slices.
- **S2 — scanner ASCII guard + 0.3.1 bump — OK.** One session: one new pass inside the already-wired `evaluate()` + a hermetic test (`tests/test_check_shipped_content.py`) + the manifest version pair (confirmed both at `0.3.0` today; version-sync gate enforces the pair). Lands complete. Sequencing S1→S2 is **correct** — clean first so the new hard pass is green when added (a guard that ships red would block its own land).
- **2 slices is right, not 1.** S1 (behavior-preserving source change, proven by the node suite) and S2 (a new Python gate + version bump, proven by pytest) are different change-kinds with different test suites and a real ordering dependency; keeping them separate keeps each diff reviewable and each landing clean.

### Confirmations (pressure-tested, no change needed)

- **Scope is correct.** `build_release.classify` confirms the **only** shipped `.js` are exactly the 4 engine files (`engine/{audit,build-item,qa,verify}.js`); zero `.js` are stripped. "Shipped `*.js` = engine/*.js" holds. The `scripts/*.py` non-goal is right — they run via Bash, carry `_force_utf8_output()`, and are out of the Workflow-approval path.
- **No new wiring needed.** `check_shipped_content.py` is already a run-gate (CI + Definition-of-Done suite, `WORKFLOW.md:138`) and is itself DEV_ONLY/stripped (`build_release.py:54`). A new internal pass in `evaluate()` inherits all of that — no ci/doctor/WORKFLOW surface to add.
- **Provenance + honesty are accurate.** The cause (the adopter's permission handler, not a harness defect) and the framing of the new pass as hard/mechanical are both correct and honest.
- **Budget headroom confirmed.** DECISIONS is at 51,852 / 60,000 = **86%** — one short Land line fits; condense-on-WARN if it trips 90%.

### Harness impact

- **DECISIONS (Land):** the one-line engine-ASCII rule + DistrictSync provenance — already planned.
- **INVARIANTS candidate (Stage-9 harvest):** the `×` finding exposes a real load-bearing invariant worth recording — *"engine `*.js` is ASCII-only (byte/codepoint ≤ 0x7F) so it survives arbitrary adopter permission/approval layers; the cell-key delimiter must be ASCII-and-name-safe (cannot occur in a module/dir name)."* The why isn't obvious from the code (it reads as cosmetic). Flag for the retrospect-harvester at Land, not for this plan to pre-write.
- No new agent or STANDARD module needed.
