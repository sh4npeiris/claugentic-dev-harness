# 0024 — Harness context-economy & lifecycle hygiene

- **Status:** Draft — scope & key designs locked. **S2 own-repo switch LANDED 2026-06-24 (commit `eae7b28`); the adopter-facing `init`-wiring of S2 still remains.** Ready for plan-reviewer (Stage 3) on the rest. **doctor + the unified finder→select→plan→build pipeline → plan `0025`** (not built here).
- **Resumable from:** awaiting user instruction to run plan-reviewer on 0024 (or continue refining). Slices S1–S5 below.
- **Blockers:** none. S4 (init solo) composes with S2's pre-commit wiring — sequence S2 before S4.
- **Roadmap item:** seed in `docs/claugentic-ROADMAP.md` on approval (+ a pointer to `0025`).
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · `scripts/claugentic-check_architecture_tree.py` · `scripts/check_doc_budgets.py` · `scripts/claugentic-advisor.py` · `skills/init/SKILL.md` · `.claude/settings.json` · grounded by the harness-lifecycle-review workflow (wf_4c6557cb-f17)

## Problem

A grounded multi-agent review (10 agents) + this design conversation established the real context-economy and lifecycle picture, correcting two load-bearing premises and locking the leverage:

1. **The architecture tree is the real recurring context tax** — ~7,570 tokens, the only **read-first-every-task** large doc; ~3–4k of those are *rationale* crammed into oversized entries (34 of 86 ≥400 chars; 9 pinned at the 450-char ceiling). (DECISIONS/ROADMAP are **not** auto-loaded, so restructuring *them* saves ~0 — the tree is the cost.)
2. **The tree gate fires per-action** — `PostToolUse(Write)` + `Stop` hooks in `.claude/settings.json` add overhead on every agent action / turn. The durable checkpoint is the **commit**, not each action.
3. **`INVARIANTS.md` is uncapped** — a sibling accreting ledger to DECISIONS with no `DOC_BUDGETS` entry.
4. **The advisor has no off-switch and one audience** — it injects its derived line into *agent* context (can nudge toward backlog work the user didn't ask for) with no env mute.
5. **No solo / local-only adoption mode** — `init` writes everything into git-tracked territory + step 5c makes `.claude/settings.json` trackable and prompts teammates on clone. No way to dogfood on a team repo undisturbed.
6. **(real-usage pain) Plans can't complete with deferred/rejected parts** — the user had to force-complete a plan; there's no clean disposition.

## Goals / Non-goals

**Goals**
- Cut per-task tree read-cost ~3–4k tokens at zero loss of navigation value; leave verbatim instruction docs untouched.
- Move tree enforcement off the per-action hooks onto a **once-per-commit pre-commit hook**; **no adopter CI**.
- Budget every *accreting, loaded* ledger; leave stable instruction docs ungated.
- Give the user advisor control (mute + audience-split).
- Add a solo/local-only `init` mode (`git status` stays clean, teammate clones byte-identical).
- Let plans complete with deferred/rejected/externally-blocked parts cleanly dispositioned; capture bugs found mid-work onto the ROADMAP without bloating the current plan.

**Non-goals (rejected or moved — recorded so they aren't re-litigated)**
- DECISIONS/ROADMAP → table-of-contents pointer files (saves ~0, adds pointer-miss + sprawl). **Rejected.**
- Per-item persistent detail files (git history is the archive). **Rejected.**
- Engineering→product "graduation" pipeline (two independent regenerated snapshots, not a pipeline). **Rejected.**
- **Adopter CI** for the tree gate — declines Actions-minute cost on private repos; the next commit catches any miss. **Dropped** (the harness's own *public* repo keeps its free CI, unrelated to adopters).
- Tree sharding by directory (the large-repo scaling lever) — **deferred** to ROADMAP.
- Version-migration/upgrade nudge — **deferred** (no live adopters yet).
- **`doctor` + the unified finder→select→plan→build pipeline → moved to plan `0025`.**

## Approach

**S1 — Tree condensation + read-economy wording (doc-only; highest token win; independent).**
- Rewrite every oversized `ARCHITECTURE_TREE.md` entry to a tight ~120–160-char one-liner that still conveys *what the file is and when to open it* (the navigation signal — the pointer-miss mitigation). **Evict** load-bearing rationale to DECISIONS/INVARIANTS; **drop** the rest (git history recovers it). Tighten prose as you evict (condense DECISIONS in the same pass so its bytes don't simply rise). Update the tree header to state the **~150-char working target** (450 stays the hard ceiling).
- **CLAUDE.md** Harness-Discipline wording → prescriptive read-economy: *consult the tree to locate files; scan/grep it rather than ingest it whole; skip it for a scoped single-file edit.*
- _Alternatives rejected:_ lower hard `MAX_ENTRY_CHARS` (fails legitimately-detailed entries on big repos); mechanical auto-condense (can't preserve the navigation signal).

**S2 — Tree enforcement → pre-commit hook (replace per-action hooks; no adopter CI).**
- **Two separate hook systems (the crux):** Claude Code hooks (`.claude/settings.json` — `PostToolUse`/`Stop`) fire per-tool-use / per-turn = the overhead being removed; a **git** pre-commit hook (`.git/hooks/` or `core.hooksPath`) is a *different system*, triggered **only by `git commit`** (by git, never by a tool use) → **zero per-tool-use overhead.** S2 deletes the former and adds the latter — the tree check is **not** a `PostToolUse` hook, and **no CI** (GitHub Actions is remote — the agent-might-be-gone problem; pre-commit is local + only-at-commit).
- **Remove** the `PostToolUse(Write)` + `Stop` hooks from `.claude/settings.json`. **Add** a git **pre-commit** hook — a one-line wrapper (`python3 || python`, repo-root-anchored via `git rev-parse --show-toplevel`) calling the **existing** `claugentic-check_architecture_tree.py` in plain mode (exit 1 aborts the commit; the message is already authored). Checked **once per commit**, zero per-action overhead. Rationale: the tree only needs to be correct at the durable handoff (commit → next session/clone reads it); the working agent is in-context at commit to write the new file's description while fresh; a missed file is caught by the very next commit (the check is idempotent + runs every commit).
- **Wiring (`init` step 5b rewrite):** shared mode → commit `.githooks/pre-commit` + `init` runs `git config core.hooksPath .githooks` (hook travels with the repo; one config line per clone, init-managed). Solo mode (S4) → write `.git/hooks/pre-commit` directly (inherently local/untracked).
- **Cost:** `git ls-files` (index read) + ~30 KB markdown regex + Python startup, once per commit — negligible; the repo-wide source census short-circuits whenever the globs match ≥1 file.
- **Spec detail:** scope the pre-commit check to the **staged** set (what's being committed) rather than also flagging unrelated untracked source files (today `in_scope_files()` unions untracked — right for the old per-write nudge, wrong for a commit gate). Retire the now-unused `--hook` / `--hook-write` modes (or keep dormant) — decide in spec.
- _Alternatives rejected:_ adopter CI floor (Actions-minute cost on private repos — user declined; next-commit-catches suffices); keeping per-action hooks (the overhead being removed).

**S3 — Budget INVARIANTS + advisor control.**
- Add `docs/claugentic-INVARIANTS.md` to `DOC_BUDGETS` in `check_doc_budgets.py` (≈20,000 B, read-on-demand profile). WARN@90%/FAIL@100% + condense-on-WARN apply for free. One dict line + a test row.
- **Advisor off-switch:** `build_output()` returns `{}` when `CLAUDE_HARNESS_ADVISOR=off` (fail-safe to silent). Document one line in CLAUDE.md/README.
- **Advisor audience-split:** emit the orientation line as `systemMessage` (user-facing) but **not** `additionalContext` (agent-facing) — user stays oriented without the agent being nudged toward backlog work. Keep `additionalContext` only where the derived line is a genuine next-action the agent should see.
- _Alternatives rejected:_ task-aware suppression (no task context at SessionStart — YAGNI); removing the advisor (orientation is wanted, just controllably).

**S4 — `init` solo / local-only mode.**
- Trigger: **ask at init time** (AskUserQuestion: "Shared with teammates, or solo/local-only?"); default **shared** (no change for existing adopters). Mode recorded (e.g. `- Harness mode: solo (local-only)` in the anchor) so re-runs stay consistent (make-invalid-states-unrepresentable: solo ⇒ step 5c never runs).
- Four steps differ: **(1)** managed docs + tree script written to disk but path-patterns appended to `.git/info/exclude` (per-clone, untracked); **(2)** hooks → `.claude/settings.local.json` (already gitignored) — and the **pre-commit hook → `.git/hooks/pre-commit`** (local) per S2's solo branch; **(3)** **skip step 5c** (no plugin self-reference, no `.gitignore` negation, no teammate prompt); **(4)** CLAUDE anchor → `CLAUDE.local.md`.
- Step-9 report: solo honesty line + verification claim (`git status` shows no new tracked paths; `.gitignore` byte-unchanged). Guard: verify `settings.local.json` is still ignored (`git check-ignore`), fail loud otherwise.
- _Alternatives rejected:_ edit committed `.gitignore` (tracked → disturbs teammates); separate `init-solo` command (DRY); out-of-repo doc location (breaks `${CLAUDE_PROJECT_DIR}` rooting).

**S5 — Plan lifecycle: disposition · scope-creep handling · Bugs capture · ROADMAP taxonomy.**
- **Disposition (at close / on demand).** Each remaining unchecked plan item gets a disposition: `done` (checked) · `defer` → a one-line `docs/claugentic-ROADMAP.md` item **or**, for substantial / externally-blocked remainder, **move the remaining items into a NEW plan file** (+ roadmap item) · `reject` → recorded as a declined decision (not re-proposed) and dropped. The plan then **completes and is deleted** — gated only on the committed slice, never on deferred/rejected/blocked parts.
- **Explicit blocked-on-external path:** when the last pieces are blocked externally, the user defers-to-new-plan (or rejects) and **closes NOW** — no plan lingers `pending` waiting on outside events.
- **Scope-creep vs out-of-scope (the in-flight split).** Work that emerges mid-build goes two ways: **(a) intrinsic to the feature** (genuinely part of *this* plan's requirement) → **fold into the plan** — account · spec · deliver (agile; the decomposition/spec grows, since it *is* the feature). **(b) out-of-scope** (a defect or unrelated issue) → does **not** bloat the plan; record on the ROADMAP. The (a)/(b) call is the user's at plan-review/approve + disposition; the architect-pass frames what's genuinely in-scope.
- **Bugs capture.** An out-of-scope defect → a one-line entry in a durable, human/agent-owned **`Bugs`** ROADMAP section (**outside** the regenerated audit/product fences, so a re-audit never wipes it). The capture stays a **planless one-liner until you commit it** (selecting it to do triggers the plan, per 0025) — so jotting a bug mid-work stays cheap; it's triaged/selected/built later via the normal pipeline. Under the ROADMAP byte-budget + condense-on-WARN; a dedicated budgeted `BUGS` ledger is a deferred escape hatch only if volume warrants.
- **No standing "tech-debt" section — debt isn't *created*, so there's nothing to park.** Implementation can't legitimately leave debt: every slice **lands complete (DoD), no shortcuts**, and **Verify audits the diff against the standards before it lands** (model-upheld + reviewer-caught, not a mechanical guarantee). Work that would *otherwise* become debt is **built wholly, never left half-done**: in-scope discovery → **fold into the plan** and re-run the steps (plan→review→spec→build→verify) · a too-big slice → **re-decompose** into complete slices · an emergent design flaw → **re-plan + re-review** · genuinely out-of-scope work → its **own roadmap item + own complete plan** (built wholly later) · an external blocker → **deferred + tracked** (not half-built). *Deferring scope* (tracked, completed wholly later) ≠ *creating debt* (a half-done thing left in code — not allowed). *Existing* debt in an adopter codebase is the **audit's** domain (Quality findings, tracked-to-fix). Debt is structurally prevented, never accumulated — which is why there's no debt bucket.
- **ROADMAP section taxonomy (minimal — KISS/anti-bloat; only `Bugs` is new).** *Generated/regenerated:* Overview · **Quality** backlog (`harness-audit:backlog` — standards/engineering, where existing debt surfaces) · **Features/Functionality** backlog (`harness-product:backlog`). *Durable human/agent-owned (never wiped):* **Bugs** *(new)* · **Later/Ideas** · **Rejected-findings**. The "generic/main" backlog = **Features/Functionality**. Add a section only on real need (YAGNI); items can carry a lightweight type tag if finer grain is ever wanted, rather than spawning more sections. **`doctor`/harness-maintenance findings** are mostly fixed-on-approval and rarely reach the roadmap; a deferred one rides **Later** with a `harness` tag (own repo → normal Quality/Feature) — **no new section**.
- Surfaces: `docs/claugentic-WORKFLOW.md` (Stage 8 Land + Stage 9 + the scope-creep split), `skills/build/SKILL.md` (close-out + mid-build discovery), `.claude/plans/TEMPLATE.md` (a Disposition note), `docs/claugentic-ROADMAP.md` (the `Bugs`/`Later` sections + the taxonomy).

**Bookkeeping (all slices).** Dense one-line DECISIONS entries: corrected load model · budget-only-accreting-loaded-ledgers · the mechanical-enforcement rule (silent ∧ compounding ∧ cheap → mechanical; tree qualifies; now at commit-altitude) · no-adopter-CI · the three rejections · tree-sharding deferred. **One line each.**

## Affected files
- `docs/claugentic-ARCHITECTURE_TREE.md` — condense entries (S1).
- `CLAUDE.md` — surgical tree-read wording (S1); advisor off-switch note (S3).
- `.claude/settings.json` — **remove** the two tree hooks (S2).
- `.githooks/pre-commit` — NEW shared-mode hook wrapper (S2); `skills/init/SKILL.md` step 5b — wire pre-commit + `core.hooksPath` (S2) and the solo branch (S4).
- `scripts/claugentic-check_architecture_tree.py` — staged-scope tweak for commit context; retire `--hook*` modes (S2).
- `scripts/check_doc_budgets.py` — INVARIANTS budget row (S3).
- `scripts/claugentic-advisor.py` — off-switch + audience-split (S3).
- `skills/init/SKILL.md` — solo-mode branch (S4).
- `docs/claugentic-WORKFLOW.md`, `skills/build/SKILL.md`, `.claude/plans/TEMPLATE.md` — plan-disposition (S5).
- `docs/claugentic-DECISIONS.md` (+ `docs/claugentic-INVARIANTS.md`) — bookkeeping + evicted rationale.
- `docs/claugentic-ROADMAP.md` — seed item + sharding/upgrade deferrals + `0025` pointer.
- Tests: `tests/test_check_doc_budgets.py` (INVARIANTS), `tests/test_advisor.py` (off-switch + audience-split), `tests/test_check_architecture_tree.py` (staged-scope; hook-mode removal).

## Research / grounding
- **Files reviewed:** `scripts/claugentic-check_architecture_tree.py:1-519` (full), `.claude/settings.json:1-25`, `docs/claugentic-ARCHITECTURE_TREE.md:1-134`, `skills/audit/SKILL.md:1-391`, doc line/byte counts; + the harness-lifecycle-review workflow's five readers.
- **Findings:** doc-budget gate, condensed DECISIONS, ephemeral plans, regenerate-don't-accumulate fences **already exist** — reuse. The tree (read-first) is the real tax. The check script already has a plain exit-1 mode → a pre-commit hook needs no new check logic. Solo mode is cleanly buildable via `.git/info/exclude` + `settings.local.json` + skip-5c + `CLAUDE.local.md`.

## Risks & mitigations
- **Tree condensation drops a navigation cue** → keep each one-liner descriptive enough to convey *when to open the file* (~150-char target, not bare titles); plan-reviewer gates it.
- **Condensation relocates rather than removes bytes** → tighten prose as you evict; condense DECISIONS same pass; verify budgeted bytes don't rise.
- **Pre-commit over-flags untracked scratch files** → scope to the staged set (S2 spec detail).
- **Pre-commit not installed on a fresh clone** → init wires it (shared via `core.hooksPath`); accepted that a never-init'd clone has no local gate (next commit after init catches drift; `--no-verify` is a deliberate opt-out).
- **Advisor audience-split changes injected context** → `test_advisor.py` asserts orientation = systemMessage-only; off-switch defaults to current behavior.
- **Solo mode leaks a tracked file** → `git check-ignore` guard + the "git status clean" verification claim.

## Test strategy
- Deterministic gates stay green: `pytest`, `node --test`, tree-check, version-sync, doc-budgets.
- New/updated unit tests: INVARIANTS budget row; advisor off-switch + audience-split; tree-check staged-scope + hook-mode removal.
- Pre-commit hook: dogfood — stage a new in-scope file without a tree entry → commit blocked; add entry → commit passes.
- `init --solo`: dogfood on a scratch repo → `git status` shows zero new tracked paths; `git diff -- .gitignore` empty.
- Each slice updates `claugentic-ARCHITECTURE_TREE.md` (now enforced at commit).

## Decomposition (slices)
Each lands complete in one session, no debt. **(Updated per Stage-3 review — folded decisions inline; full review below.)**
- [ ] **S1 — Tree condensation + CLAUDE.md read-economy wording.** Doc-only; biggest token win; independent. **Build FIRST** (reclaims DECISIONS headroom before per-slice bookkeeping lines land — review #7). **Measurable target (review #3):** tree ~30,780 B → **≤ 27,000 B**; DECISIONS stays **≤ 60,000 B** after eviction (doc-budget gate confirms; 33,770 B now).
- [~] **S2 — Tree enforcement → pre-commit hook.** OWN-REPO switch **DONE** (`eae7b28` + worktree-resolution fix `38926be`: per-action hooks removed, `.githooks/pre-commit` + `core.hooksPath=.githooks`, `--staged` index-scope + tests). **REMAINS: adopter-facing `init` wiring → folded into S4a.**
- [ ] **S3 — INVARIANTS budget + advisor off-switch & audience-split.** Two scripts + two test updates; independent. **Folded decisions:** (a) **off-switch** `CLAUDE_HARNESS_ADVISOR=off` → `build_output` returns `{}` (fail-safe to silent). (b) **audience-split = NUANCED (review #1):** keep `additionalContext` (with the existing RETURN-6 `ADVISORY_PREFIX` disclaimer) ONLY for the in-flight-plan **resume** branch (`recommend_next` priority 1 — a genuine next-action the agent should see); emit **`systemMessage`-only** for the three promotional nudges (open-backlog / PARTIAL-rerun / no-product-spec — "work the user didn't ask for"). Honors problem #5 WITHOUT regressing RETURN-6; update `tests/test_advisor.py` to assert the per-branch split. (c) **INVARIANTS budget = 20,000 B (review #2)** justified: an *accreting* ledger (sibling to DECISIONS) whose only growth-bound is this gate — budgeted because it accretes, even though read-on-demand not auto-loaded; test BOTH WARN (≥90%) + breach (≥100%) bands. **Trust surface → convene `honesty-reviewer` at Verify.**
- [ ] **S4a — Shared-adopter pre-commit wiring (the S2 remainder).** `init` step-5b shared branch: write `.githooks/pre-commit` + `git config core.hooksPath .githooks`; **retire the now-unused `--hook`/`--hook-write` modes** + their helpers (`_check_written_file`/`_stop_hook_active_from_stdin`/`_written_path_from_stdin`) + tests (review #4 — DECIDED: REMOVE in this same slice, since init no longer wires them; removing earlier would strand init). Lands complete — init shared-branch text + dead-mode removal, test-guarded.
- [ ] **S4b — `init` solo/local-only mode.** Depends on S2 + S4a (review #5 split). The four diverging steps (managed docs → `.git/info/exclude`; hooks → `settings.local.json` + `.git/hooks/pre-commit`; skip 5c; CLAUDE anchor → `CLAUDE.local.md`) + the AskUserQuestion mode trigger + the recorded-mode line + the `git check-ignore` guard + the step-9 solo honesty/verification line.
- [ ] **S5 — Plan lifecycle: disposition (blocked→defer→close) + scope-creep handling + Bugs capture + ROADMAP taxonomy.** WORKFLOW + build SKILL + TEMPLATE + ROADMAP sections; independent. **Folded (review #6):** ALSO edit `docs/claugentic-WORKFLOW.md`'s **Plan-file-lifecycle** section (`:168-170`, currently "on completion, remove it" — reconcile with the disposition model) — add to Affected-files. **Acceptance criterion (checkable):** the `Bugs` section sits OUTSIDE the regenerated `harness-audit`/`harness-product` fences so a re-audit never wipes it (dogfood: seed a `Bugs` entry, run `/audit`, confirm survival). **Harness-process change → diverse panel at Verify, not solo.**
- **doctor + unified finder pipeline → plan `0025`** (not built in 0024).

---

## Review  _(plan-reviewer, Stage 3 — 2026-06-24)_

- **Verdict:** **CHANGES REQUIRED** (focused — the plan is sound and well-sliced; the fixes are scoping/grounding corrections, not a redesign. S2 core verified landed: `.githooks/pre-commit` present + `--staged`, `core.hooksPath` set, `.claude/settings.json == {}`.)

**Required changes**

1. **S3 advisor audience-split contradicts a recorded, tested design decision — reconcile it explicitly.** The plan proposes emitting the orientation line as `systemMessage` only and **dropping `additionalContext`** for it. But `additionalContext` carrying the `ADVISORY_PREFIX` disclaimer ("Derived suggestion (confirm before acting):") is a **deliberate, documented contract** (advisor RETURN-6, `scripts/claugentic-advisor.py:14-16,78-79,404-406`) and is **asserted by the existing tests** (`tests/test_advisor.py:132-133` asserts it absent only on the SILENT path → present on actionable paths). The split criterion as written ("keep `additionalContext` only where the derived line is a genuine next-action") is **ambiguous and self-contradicting**: the resume/orientation line *is* the highest-priority next-action (`recommend_next` priority 1). The spec must state the concrete rule per `recommend_next` branch (which of the 4 actionable branches keep `additionalContext`, which go systemMessage-only) and **why that doesn't regress RETURN-6** — the disclaimer prefix was the original mitigation for "agent nudged by injected context," so the plan must say why systemMessage-only is *additionally* needed rather than re-litigating a settled choice. Note: removing `additionalContext` does **not** break `build`'s resume (the resume contract derives from ROADMAP fences + plan files, `skills/build/SKILL.md:538-561`, never from the advisor) — so the only real cost is the test/contract churn, which the spec must own.

2. **S3 INVARIANTS budget — the proposed 20,000 B cap and "read-on-demand profile" need a one-line justification against actual size.** `docs/claugentic-INVARIANTS.md` already exists at **2,631 B** (it has no `DOC_BUDGETS` row — the plan's Problem §3 is correct). 20 KB is ~7.6× current size; fine as a generous on-demand cap, but the spec should (a) confirm INVARIANTS is **not** auto-loaded (so the budget is a pure accretion trip-wire — the plan's goal is "budget only accreting, *loaded* ledgers"; INVARIANTS is accreting but *not* loaded, so name why it still earns a budget), and (b) add the WARN-band test row, not just the breach row (`check_doc_budgets.py` has a WARN@90% path; `test_check_doc_budgets.py` should cover INVARIANTS at both bands for parity with the other three ledgers).

3. **S1 must state a measurable acceptance target, not "verify bytes don't rise."** The tree is **30,780 B** today with ~36 entries in the 400–450-char band (in chars; the 450 ceiling IS enforced — `MAX_ENTRY_CHARS=450`, `_form_violations` confirmed live and green). The "~150-char working target" is good but the slice's done-condition is soft ("verify budgeted bytes don't rise"). Make it a **concrete, checkable acceptance criterion**: e.g. "tree ≤ ~26–27k B after condensation (the claimed 3–4k saving)" AND "DECISIONS stays ≤ its 60 KB budget after eviction" (DECISIONS is **33,770 B** now — large headroom — but the slice evicts rationale *into* it + adds bookkeeping lines, so name the post-pass budget check). Without a number, "condensed enough" is a judgment the implementer can't self-gate on.

4. **S2 leftover — DECIDE retire-vs-keep `--hook`/`--hook-write` in this plan; don't defer it to spec as "decide in spec."** Lines 51 + Affected-files say "retire the now-unused `--hook`/`--hook-write` modes (or keep dormant) — decide in spec." That fork has a tech-debt consequence: dead modes left dormant = dead code the DoD forbids; but `init` step 5b still documents wiring them (`skills/init/SKILL.md:417-418`). Resolve + sequence now: the per-action Claude-Code hooks are gone repo-wide (`settings.json == {}`), so `--hook`/`--hook-write` + `_check_written_file`/`_stop_hook_active_from_stdin`/`_written_path_from_stdin` are dead **for this repo** — but they remain the **adopter** wiring path until `init` is rewritten. So state it: the `--hook*` modes (and the step-5b "Gate ON → two hooks" table) stay until **S4** migrates `init` to write the pre-commit hook for adopters, and are removed **in that same slice** — removing them earlier strands `init`. Fold the removal into S4; don't leave "(or keep dormant)" as an open option that creates debt.

5. **S4 is the largest slice and carries the most clobber-risk — assert single-session fit with the edit list, or SPLIT.** S4 changes **four** distinct `init` behaviors (managed-docs→`.git/info/exclude`, hooks→`settings.local.json` + `.git/hooks/pre-commit`, skip-5c, CLAUDE→`CLAUDE.local.md`), **plus** absorbs the S2 adopter init-wiring (shared `.githooks` + `core.hooksPath`), **plus** a new AskUserQuestion mode trigger + a recorded-mode line + step-9 honesty reporting + a `git check-ignore` guard. `skills/init/SKILL.md` is an ~800-line never-clobber-critical procedure; touching its hook-wiring (5b), gitignore negation (5c), and CLAUDE fence (6) at once is a lot of surface. It is doc/procedure text only (no engine), so it *may* fit — but the plan must **either** assert the fit explicitly with the file-by-file edit list, **or** split into **S4a (shared adopter pre-commit wiring — the S2 remainder: 5b `.githooks` + `core.hooksPath` + the `--hook*` removal from change #4)** and **S4b (solo/local-only mode — the four-branch divergence + the mode trigger/guard/report)**. **Recommend the split** unless the spec proves single-session fit; S4a is the smaller, lower-risk piece and is exactly the S2 remainder.

6. **S5 — add `WORKFLOW.md`'s Plan-file-lifecycle section to Affected-files, and make "Bugs survives re-audit" a checkable criterion.** S5 augments existing beats (build already has the re-slice-pause at `skills/build/SKILL.md:286-288` and the close-out at `:332`, and WORKFLOW Stage 8/9 exist) — say it *augments*, doesn't author from scratch. Crucially, WORKFLOW's **Plan file lifecycle** section (`docs/claugentic-WORKFLOW.md:168-170`) currently says only "on completion, remove it" with **no disposition concept** — S5's whole disposition model must reconcile *that* section, but it is **not** in the plan's Affected-files list for WORKFLOW. Add it. Also make the load-bearing property — the new **`Bugs`** section sits **outside** the regenerated `harness-audit`/`harness-product` fences so a re-audit never wipes it — an explicit acceptance criterion with a dogfood check (run `/audit` against a seeded `Bugs` entry, confirm it survives). ROADMAP is budgeted at 12,000 B (currently ~1.7 KB) so the new standing sections are fine on budget.

7. **Sequence the S1 condense-pass first so DECISIONS doesn't drift mid-plan.** The plan adds a DECISIONS line in *every* slice plus evicts S1 rationale into DECISIONS; S1 also "condenses DECISIONS in the same pass." Make the ordering a stated dependency (S1 before the slices that only *add* lines) so the condense headroom is reclaimed before the additions land. Low risk at 33.7 KB / 60 KB, but it's the plan's own "condense on WARN as part of the work" discipline — name where it happens.

**Sizing / completeness check (per slice)**
- **S1** (tree condensation + CLAUDE.md wording) — **OK**, doc-only, independent. Add the measurable byte target (change #3); the current done-condition is too soft to self-gate.
- **S2 remainder** (adopter init-wiring) — **fold into S4/S4a** (already is). Resolve + sequence the `--hook*` retirement (change #4) — not "decide in spec."
- **S3** (INVARIANTS budget + advisor off-switch & audience-split) — **OK on size**; the audience-split (change #1) must reconcile with the recorded RETURN-6 decision + existing tests before spec-ready; INVARIANTS row needs the WARN-band test (change #2). Off-switch (`CLAUDE_HARNESS_ADVISOR=off` → `{}`, fail-safe to silent) is clean and low-risk — good.
- **S4** (init solo + S2 adopter wiring) — **SPLIT RECOMMENDED** → S4a (shared adopter pre-commit wiring) + S4b (solo mode). Highest-risk slice (never-clobber `init` surface). See change #5.
- **S5** (plan lifecycle) — **OK on size** (doc/procedure text, independent), but add WORKFLOW's Plan-file-lifecycle section to Affected-files and make "Bugs survives re-audit" checkable (change #6).

**Harness impact**
- **No engine / agent-spawning code touched** — confirmed. All slices are doc + standalone scripts (`check_doc_budgets.py`, `claugentic-advisor.py`, `claugentic-check_architecture_tree.py`) + `init`/`build`/`WORKFLOW` SKILL/doc text. Low bootstrapping risk, as framed.
- **S5 IS a harness-process change** (Stage 8/9 + a new plan-disposition discipline + a `Bugs` ROADMAP taxonomy) — it changes how *every* future plan closes, so run the **diverse panel at Verify** per `docs/claugentic-WORKFLOW.md:36`, not a solo review. Name it in the S5 spec's in-scope dimensions.
- **S3 advisor audience-split is a trust/honesty surface** (it changes what context is injected into agents) — convene **`honesty-reviewer`** at Verify (RETURN-6 is exactly the honesty register this slice edits). Name it.
- **No new STANDARD or agent** required; `docs/claugentic-INVARIANTS.md` already exists, so S3 only adds a budget row (not a new doc). DECISIONS bookkeeping is correctly planned (one line each); sequence the S1 condense first (change #7).

---

## Spec  _(per slice, after Review passes — Stage 4)_
_To be filled per slice once Review passes._

## Design decisions resolved (this conversation)
- **Tree enforcement → commit-time.** Pre-commit hook running the existing check; **drop** both `PostToolUse(Write)` + `Stop` hooks; **no adopter CI** (next commit catches misses; harness's own public repo keeps free CI). Cheap (`git ls-files` + small parse, once per commit).
- **Mechanical-enforcement rule:** enforce only when violation is *silent* ∧ damage *compounds* ∧ check is *cheap+deterministic* — the tree qualifies, now at commit altitude; all else model-upheld.
- **Budget only accreting, loaded ledgers**; stable instruction docs stay review-governed.
- **Tree read-economy** = condense + prescriptive CLAUDE.md wording now; **shard** later (deferred).
- **doctor → plan `0025`**, built on the shared finder pipeline (not 0024).
- Solo trigger = **ask at init** (default shared).
