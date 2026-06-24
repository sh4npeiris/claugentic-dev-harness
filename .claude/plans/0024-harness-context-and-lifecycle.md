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
Each lands complete in one session, no debt.
- [ ] **S1 — Tree condensation + CLAUDE.md read-economy wording.** Doc-only; biggest token win; independent.
- [~] **S2 — Tree enforcement → pre-commit hook.** OWN-REPO switch **DONE** (`eae7b28`: per-action hooks removed, `.githooks/pre-commit` + `core.hooksPath=.githooks` common config, `--staged` index-scope mode + tests; verified pytest 167 / node 344 / hook passes-clean+blocks-staged). **REMAINS: adopter-facing `init` wiring** — `init` writes `.githooks/pre-commit` + sets `core.hooksPath` for a shared adopter, `.git/hooks/` for solo (S4). Independent of S1.
- [ ] **S3 — INVARIANTS budget + advisor off-switch & audience-split.** Two scripts + two test updates; independent.
- [ ] **S4 — `init` solo/local-only mode.** Depends on S2 (uses its pre-commit wiring in `.git/hooks/`).
- [ ] **S5 — Plan lifecycle: disposition (blocked→defer→close) + scope-creep handling + Bugs capture + ROADMAP taxonomy.** WORKFLOW + build SKILL + TEMPLATE + ROADMAP sections; independent.
- **doctor + unified finder pipeline → plan `0025`** (not built in 0024).

---

## Review  _(filled by plan-reviewer, Stage 3 — pending user go)_
- **Verdict:** —
- **Required changes:** —
- **Sizing/completeness:** —
- **Harness impact:** —

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
