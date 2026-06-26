# 0029 — Engine ASCII-hardening (0.3.1)

- **Status:** Draft — committed at draft (crash lesson). Awaiting Stage-3 plan-gate, then build S1→S2→Land→release.
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
| `×` mult | 00D7 | `x` | "3× / N×" |
| `·` middle dot | 00B7 | ` - ` or `;` | "a · b · c" lists (judgment) |
| `…` ellipsis | 2026 | `...` | trailing prose |
| `⚠` warning | 26A0 | `!` / `(!)` | warning log prefixes |
| `≥` / `≤` | 2265/2264 | `>=` / `<=` | thresholds in comments |
| `∪` union | 222A | `+` or `U` | "agents ∪ skills" set notes |
| `∧` logical-and | 2227 | `&&` or `and` | "bounded ∧ reversible" |
| `–` en dash | 2013 | `-` | stray |

**The load-bearing-char rule (the one real risk):** most of these live in **comments** (cosmetic — safe) or **`log()`/display strings** (terminal output — ASCII is fine/better). The ONLY danger is a glyph that is a **delimiter in emitted content that is later parsed/round-tripped** (e.g. a backlog-fence separator the engine writes AND reads, or a marker `audit.js` renders into the ROADMAP fence that `renderOnly` re-reads). For each substitution, the implementer must confirm it is comment/log/display-only; for any char in a written-and-parsed format, change **both sides** consistently (or leave it). **The full node suite (`node --test tests/workflows/*.test.mjs`, 372 tests) is the safety net** — a broken round-trip fails a test. Run it after S1; zero behavior change is the bar.

**S2 — regression guard + version bump.** Add a **HARD (exit-1) ASCII-only pass** to `scripts/check_shipped_content.py` over shipped **`*.js`** (= `engine/*.js`): flag any byte > 0x7F (exact, unambiguous — no heuristic). It must be GREEN after S1. Wire it into the scanner's existing report/exit + a hermetic test (`tests/test_check_shipped_content.py`): a shipped `*.js` with a non-ASCII char is flagged; an ASCII one is clean. Bump **0.3.0 → 0.3.1** in BOTH `.claude-plugin/plugin.json` + `marketplace.json` (the version-sync gate enforces the pair).

**Land + release.** ONE DECISIONS line (the engine-ASCII rule + its provenance: the DistrictSync validation); retire this plan; rebuild `release`; **PR + merge to main + force-push release** (the user authorized the full cycle).

## Architecture & holistic fit
- **Codebase fit:** S1 is a mechanical source-hygiene pass on existing files (no logic change); S2 extends the existing shipped-content scanner with one more exact, hard pass (sibling to its dangling-path + namespace passes) — same SRP gate, one new rule. No new layer/file beyond the test additions.
- **Quality dimensions** (→ standards): **reliability-resilience** (the engine path no longer silently degrades under strict approval layers) · **maintainability/portability** (ASCII source is universally renderable) · **api-and-contracts** (the new guard is an exact mechanical check — honest to call it hard/mechanical, unlike the scanner's A.b heuristic).
- **Honesty:** the new ASCII pass IS genuinely mechanical/exact (byte check) — state it as such. The fix does NOT claim to fix the adopter's permission handler; it makes the harness robust regardless. Record the cause honestly (adopter handler) + the harness's defensive choice.
- **Future-proofing:** the guard means no future engine edit can reintroduce the failure mode.

## Affected files
**S1:** `engine/audit.js` · `engine/build-item.js` · `engine/qa.js` · `engine/verify.js`.
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
_To be filled._
