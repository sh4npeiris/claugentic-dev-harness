# Harness fine-tuning — INPUT DOSSIER (read AFTER 0029 + 0030 land)

> **What this is:** the durable inputs for the **post-implementation harness fine-tuning pass**. It is NOT an active plan and NOT to be built as-is. **Sequence:** implement `0029-ui-ux-craft.md` → `0030-engineering-charter.md` first; THEN read everything here, and **produce the actual fine-tuning plan(s)** (numbered `00NN-*.md`) through the normal pipeline (Plan → Review → Spec → Approve → Implement). Do **not** modify 0029/0030's landed work. The plans are solid — this is additive sharpening from a clean, shipped base.
>
> Two tracks to plan from this: **(A) ground the harness in the official Claude Code platform** (the docs below), and **(B) the release-methodology consolidation** (the design below). Both were user-requested. `.claude/plans/` is dev-only (stripped from the release), so this file never ships.

---

## Track A — official Claude Code platform docs to review + apply

All at `https://code.claude.com/docs/en/<page>`:
`model-config` · `how-claude-code-works` · `features-overview` · `plugins-reference` · `tools-reference` · `hooks` · `advisor` · `cli-reference` · `claude-directory` · `context-window` · `prompt-caching` · `memory` · `common-workflows` · `prompt-library` · `best-practices`

Blogs / guides:
- **How we use skills at Anthropic** — https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills
- **How to use loops** and **How to use dynamic workflows** — Claude Code team blog/guide (find the current URLs; summarized: loop types = turn/goal/time/proactive; dynamic workflows = Claude spins up its own multi-agent harness; pair with `/loop` + `/goal`; token budgets).
- **The advisor strategy** — https://claude.com/blog/the-advisor-strategy

**Opportunities already spotted while skimming (verify against the docs, don't take on faith):**
- **advisor tool** (`/advisor`, `advisorModel`, `--advisor`) — pair a stronger advisor model with the reviewer agents at decision points (before committing to a plan, on a recurring error, before declaring done). A genuinely new lever the harness could adopt for its gate/verify roles. Anthropic-API-only, experimental; subagents inherit the advisor. Note the harness already ships a *different* thing — a SessionStart advisor script (`scripts/claugentic-advisor.py`); reconcile the naming so they aren't confused.
- **no-`PostToolUse` is VALIDATED** — the hooks doc classifies per-tool hooks as "high-frequency, keep fast." The harness's deliberate model-driven / one-commit-time-tree-check stance is well-founded; keep it. (The ONE hook-enforced gate = the architecture-tree check.)
- **the deferred red-first `PreToolUse` hook** (charter/refactor characterization) is now precisely spec-able: `PreToolUse`, matcher `Edit|Write`, `hookSpecificOutput.permissionDecision: "deny"` with a reason until a failing test exists. Still optional — build only if the model-upheld version proves insufficient.
- **model tier:** the most-capable tier is now **Fable 5** (`best`/`fable`), *above* Opus, for "tasks larger than a single sitting" (build-to-green over a backlog · deep audits · long research). Update the WORKFLOW model-tier note (currently "most capable = opus") to add Fable/`best` as the long-running-work tier; Opus stays the standard-judgment default. `opusplan` (opus-in-plan → sonnet-execute) exists but the harness's per-agent `model:` frontmatter is finer.
- **context / memory** — `context-window` + `memory` + `how-claude-code-works` confirm the harness's context economy (subagent isolation, CLAUDE.md < 200 lines, the doc-budget ledger caps, condense-on-WARN). Cross-check the doc-budget model against the official "put persistent rules in CLAUDE.md; skills load on demand; subagents isolate context" guidance.
- **plugins-reference** — skills/commands/agents are **auto-discovered** from directories when a plugin is installed; but `plugin.json` still carries explicit component lists in this harness (the `agents` array). Verify whether the `agents` array is required or can be auto-derived — this bears directly on the Track-B agents-list footgun.
- **skills taxonomy** (the "how we use skills" blog: nine skill types) — a lens for future skill-building and for the harness's own skills.
- **`/design-sync`** — already folded into `0029` (Slice 7). Platform pass can widen it (Verify craft-bar checks design-system drift via design-sync).
- **Honesty verb-lint pre-flag (harvest-derived, 0029 Stage-9; verify + YAGNI-gate on recurrence)** — the 0029 S5 land surfaced a bare mechanical verb (*"checks the floor **mechanically**"*) that read as an adopter-unconditional `[D]` guarantee; two reviewers caught it manually at Verify. Consider a **WARN-heuristic** grep over shipped/managed copy for the scrubbed verb set (`mechanically`/`enforced`/`guaranteed`/`verified`/`proven`/`de-correlated`) near a capability claim, pre-flagging the line for the honesty-reviewer's eye — **WARN only, never a hard gate** (correct uses like the tree-check stay legit; pre-flags, never *decides* honesty — the #1 rule stays model-upheld). Natural home = the Track-B release-gate / `check_shipped_content.py` Pass A.b evolution. **Build only if a bare-verb over-claim recurs past the panel** (one clean catch is weak evidence).

---

## Track B — release-methodology consolidation (the ONE mechanism)

**Verdict:** the core (`build_release.py` subtractive default-include) is genuinely clean and correct — keep it. The convolutedness is **one fact (the ship/strip partition) re-expressed 4 times**: `DEV_ONLY_FILES/DIRS` (L1/L2, source of truth) is re-hand-partitioned 3 more ways in `check_shipped_content.py` (`_INIT_CREATES` L3, `HARNESS_SELF_SCRIPTS` L4, `_DANGLE_EXCLUDED` L5) + echoed in the init managed-set table (L7) + the test pins. Adding one dev-only doc that init recreates = **4 edits, 3 files, for one fact.** L7 (init) and L1 (strip) encode the same contract from opposite ends and **nothing cross-checks them**.

**THE ONE mechanism — `scripts/release_gate.py`:**
1. **Annotate the single authored list.** Convert `DEV_ONLY_FILES/DIRS` into a `path → recreate-class` dict in `build_release.py` — the ONLY authored semantics. Classes: `init-seed` / `init-gen` (init recreates it) · `self-gate` (stripped harness-self script) · `config` (machinery, no doc points at it) · `dangle` (stripped AND never recreated). These four classes **replace L3/L4/L5 entirely** — read off the one manifest, not 3 parallel hand-lists.
2. **The load-bearing new check — referential closure (NEEDS ⊆ HAS).** `ship = tracked − DEV_ONLY`; `init_creates`/`self_gates`/`dangle_set` derived from the classes. Assert every `init-seed`/`init-gen` path is **actually producible by init** (its `_X.md` seed ships, OR it's in init's managed-set table, OR it's a known generator output). This **mechanizes the INVARIANT** (`INVARIANTS.md:77-98` "strips ⇒ init recreates ⇒ nothing dangles") that today is only prose — and is what stops L7↔L1 drifting silently.
3. **Fold in the content scan** (`check_shipped_content.py` M3): Pass B roster (FS-derived, keep), Pass A.a dangling (now reads `dangle_set` off the manifest), Pass A.b WARN (reads `self_gates`).
4. **Fold in version-sync** (`check_versions_synced.py`, ~40 lines, trivially absorbed).

**Remove/consolidate:** DELETE L3/L4/L5 + the 3-parallel-subtraction `dangling_paths()`; MERGE `check_versions_synced.py` + `check_shipped_content.py` → `release_gate.py` (5 release scripts → 3: `build_release`, `release_gate`, `check_doc_budgets`); collapse test pins to `classify` + the closure assertion. **Net: 7 hand-lists → 1 annotated manifest + `{update}`.**

**Keep (irreducible):** the `DEV_ONLY` membership + recreate-class (`[J]` semantic — one declared file); `{update}` prose-only token; `build_release.py` M1 subtractive core + M2 base-ancestry guard (orthogonal, guards lost-merges); the checklist's force-push + eval-drift steps (`[J]` model-upheld, a script can't judge these); `check_doc_budgets.py` (context-budget, not release-core). **Honesty note stands:** the gate pins exact-literals + closure mechanically; force-push/eval stay model-upheld.

**Migration (do AFTER 0029/0030 — a self-contained internal-tooling refactor with ZERO adopter-facing change; the safety property = ship set byte-identical before/after):** (1) annotate the manifest, assert ship set unchanged; (2) add the closure check to the *existing* `check_shipped_content.py` deriving the sets *alongside* the old hand-lists and assert they're equal (the safety net); (3) delete L3/L4/L5 once equality holds; (4) fold in version-sync + rename to `release_gate.py`, update the DoD gate list / RELEASE_CHECKLIST / tree; (5) add the L7 cross-check (may surface a real latent bug — good); (6) collapse the test pins. Each step green before the next — the whole point is a provable no-op.

**Key files:** `scripts/build_release.py:40-70,80-90,149-182` · `scripts/check_shipped_content.py:103-138,165-175` · `scripts/check_versions_synced.py` · `skills/init/SKILL.md:139-146,662-689` · `docs/claugentic-INVARIANTS.md:77-98` · `tests/test_build_release.py:19-146`.

**Bonus honesty flag to verify (not for this refactor):** `main`'s `plugin.json`/`marketplace.json` read `version: 0.3.0`, but MEMORY records **v0.3.1 shipped** to `origin/release`. Version-sync only checks the two manifests agree *with each other* — it can't catch that main's manifests lag the published release-tag. A **third** version-drift axis worth a check. Verify against actual repo/release state first.

---

## Track A (cont.) — default slash-commands / skills: what to USE vs where the harness wins

The harness is a **model-upheld, honesty-disciplined pipeline** (every finding independently re-checked by `finding-verifier`; `[D]`/`[J]` tagging; SELECT scope-gate). Most default skills are single-shot self-graded procedures — so the harness **wins where it already covers a concern**, and the defaults win **at the edges the harness doesn't reach.**

- **`/design-sync`** → **INTEGRATE** (highest-leverage adopt) — the one genuine craft-flow gap; already started in `0029` Slice 7. Wire it as the mechanism behind the design-language seam; the Verify craft-bar can check design-system drift via it.
- **`debug`** → **ADOPT** as the *diagnosis front-end* to the `bug` tag (real gap): the harness governs *fixing* a known bug (reproduce-first) but has no *investigation* procedure for an unknown failure. `debug` reproduces+isolates → its output enters the pipeline as a `bug` item. A WORKFLOW tag-table + `reliability-resilience.md` pointer.
- **`architecture`** (ADRs) → **COMPLEMENTARY** — for a genuinely weighty Stage-2 design fork, produce a full ADR as a working artifact, then distill ONE `DECISIONS.md` line at Land (respects both trade-off rigor and ledger-leanness; don't add ADRs as always-loaded docs).
- **`incident-response` + `deploy-checklist`** → **POINT-AT, don't build** — they fill the known post-Land ops gap ("lifecycle stops at Land"); reference them for adopters who ship; durable lessons feed back via Stage-9 / a `bug` item.
- **`skill-creator`** → **ADOPT for the harness's own dev** — its description-triggering evals + variance analysis directly address the outstanding **stale eval/BASELINE drift-check** (the harness as a self-improving plugin).
- **`deep-research`** → already INTEGRATED honestly (`product` elevate; `0029` motion/taste grounding) — keep; consider widening to `audit` (CVE/dependency grounding).
- **HARNESS-BETTER, do NOT displace (strictly weaker inside the pipeline — single-shot, self-graded):** `system-design` (≡ the architect-pass but ungated — carve-out: pre-repo greenfield ideation only) · `tech-debt` (≡ `audit` but unverified — SKIP) · `code-review` (native `/code-review` already runs at Verify — SKIP the plugin variant) · `testing-strategy` (≡ `testing.md` but unenforced — SKIP) · `/goal` + `/loop` (≡ decision-gated autonomy + build-to-green, finer — use `/loop` only for non-build ops polling) · `/model` (adopt the tool, keep the harness's accuracy-first tier *policy*).
- `standup`, `documentation`, `artifact-design` → mostly SKIP for harness-internal work (out of lane / dense-not-verbose ethos), use ad-hoc.

---

## Track A (cont.) — UI/craft skill references (already sources in `0029`, listed for completeness)

Distilled-with-attribution, **versionless links** (they back the craft floor): `github.com/emilkowalski/skill` · `easings.net` · `github.com/pbakaus/impeccable` · `github.com/Leonxlnx/taste-skill` · `github.com/lottiefiles/motion-design-skill` · GSAP easing docs · Material Design 3 motion · Apple HIG motion · Laws of UX. Plus Claude Design (`claude.ai/design`) + `/design-sync` for design-driven projects.

---

## VERIFIED against the real docs (2026-07-03 — honesty pass; supersedes "opportunities spotted" where they conflict)

A 6-cluster research fan-out WebFetched the real Claude Code docs/blog + checked the repo. Verdicts:

**Confirmed & worth building:** the model-tier menu (`best`/`fable`/`opus`/`sonnet`/`opusplan`/`[1m]` — Fable 5 = most-capable for *long multi-sitting* work, **NOT default**, access conditional → `best` auto-falls-back to Opus) · `opusplan` (opus-plan→sonnet-execute) · the **platform advisor** (`/advisor`, `advisorModel`, `--advisor`; escalates to a stronger model at decision points; **Anthropic-API-only, experimental v2.1.98+, beta header, subagents inherit**) · **no-PostToolUse VALIDATED** (docs: per-tool hooks are high-frequency, keep-fast) · **context-economy aligned** (official CLAUDE.md ~200-line cap, skills-on-demand, subagent isolation) + prompt-cache dynamics (fresh 5-min subagent caches) · the **9-category skills taxonomy** (blog) · the **edge-skill adoptions** (`/debug` `/architecture` `/skill-creator` `/incident-response` `/deploy-checklist` are real bundled skills) · the **PreToolUse red-first hook is now precisely spec-able** (matcher `Edit|Write`, `permissionDecision:"deny"` + `permissionDecisionReason`) · the **release "7-hand-lists-for-1-fact"** consolidation.

**Honesty corrections — do NOT build these as the dossier stated:**
- **`/loop`+`/goal` are NOT "multi-agent orchestration."** Real: three loop modes (fixed-interval · self-paced/dynamic · built-in maintenance); `/goal` = condition-based persistence. Drop the "turn/goal/time/proactive" + "spins up its own harness" framing. Position only as *post-automation* pointers, never orchestration.
- **Track-B: keep `check_versions_synced.py` a SEPARATE gate — do NOT fold it into `release_gate.py`** (folding adds dual-manifest JSON parsing = scope creep/risk). Honor the `INCLUDE_GLOBS` never-clobber carve-out in the closure check. Content-scan is already wired via dangle derivation.
- **Version "third drift axis" — REFUTED.** `main` + `origin/release` are BOTH `0.3.1`, in sync; `check_versions_synced.py` works as designed. No detector to build. *(Note: this worktree branch is based on `main@0.3.0` — older than current `main@0.3.1`; that is a rebase concern for landing, not a gate gap.)*
- **`plugin.json` agents array — KEEP the explicit list.** It IS optional/auto-discovered per docs, BUT the field *replaces* (not augments) the default `.claude/agents/` scan → dropping/mis-editing it can silently exclude a new agent. Keep it (safer footgun-avoidance).
- **doc-budget ledger caps are HARNESS-PROPRIETARY** (the *spirit* — load-sparingly/prune-aggressively — is official; the explicit-cap mechanism is not). Label it as such, never "official guidance."

**Per-concern plan map (produced this session as `0031`–`0035`, ordered leverage×low-risk):**
- **`0031`** — Model-tier + advisor awareness (docs + settings + the SessionStart-advisor rename to clear the naming collision). M · Low.
- **`0032`** — Skills taxonomy + edge-skill pointers (+ corrected `/loop`/`/goal`). S · Low (docs only).
- **`0033`** — Context-economy + cache-dynamics grounding. S · Low (docs only).
- **`0034`** — Track-B release consolidation (provable no-op: one class-annotated manifest; version-sync stays separate). M · Low-if-scoped.
- **`0035`** — Deferred red-first PreToolUse test-gate (behavior-changing, flag-gated). M-L · Medium — **LAST, planned-not-built by default.**

## The task for the fine-tuning session (after 0029 + 0030 land)
1. Read Track A docs + blogs; verify the "opportunities spotted" against the real docs (don't take them on faith — honesty rule).
2. Produce a **fine-tuning plan** (or a small set) covering: the platform-grounding improvements (advisor, model-tier/Fable, plugins agents-list auto-derivation, context/memory alignment, the edge-skill adoptions: `debug`/`architecture`/`skill-creator`/point-at-ops) and the **release consolidation (Track B)** as its own slice/plan (the provable-no-op migration).
3. Run each through the normal pipeline. Keep every honesty invariant. Don't touch 0029/0030's landed work.
