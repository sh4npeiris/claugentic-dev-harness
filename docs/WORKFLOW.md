# Agent Development Workflow

> ### 👋 New here? Read this first
> This repo is built and maintained with an **agent-assisted workflow**:
> - **Small/local change?** Just make it — tests must pass, and the architecture-tree hook will prompt you to document any new source file in `docs/ARCHITECTURE_TREE.md`.
> - **Substantial change?** (new subsystem, cross-cutting refactor, shared-contract change, or **~8+ files**) — don't free-code. The agent will **pause, ask questions, enter plan mode**, and run the pipeline below: a plan in `.claude/plans/`, an adversarial review, a spec **you approve**, implementation in an isolated branch, verification, then a retrospect that improves this harness.
> - **Your map of the codebase** is `docs/ARCHITECTURE_TREE.md` (one line per file) — read it before diving into source. Specialist **roles** the agent delegates to live in `.claude/agents/` and grow over time.
> - **Decisions** → `docs/DECISIONS.md`. **Backlog** → `docs/ROADMAP.md`.

How agents **and** human devs take *substantial* work from idea → landed change while keeping quality high and the harness self-improving. CLAUDE.md links here; this is the source of truth for process.

> **One-line:** Triage → Discuss → Plan → Review the plan → Spec → **Approve** → Implement → Verify → Land → **Retrospect**. Small changes skip to Implement+Verify.

---

## 0. Triage — does this need the full pipeline?

**Full pipeline** for *substantial* work: a new subsystem, a cross-cutting refactor, a change to a shared contract/pattern/standard, a security boundary, or anything touching **roughly 8+ files** (or a pattern documented in CLAUDE.md / STANDARDS).

**Lightweight path** for small/local/mechanical changes: go straight to **Implement → Verify**, still updating `ARCHITECTURE_TREE.md` and `DECISIONS.md` as needed.

**Triage continuously, not just up front.** A conversation often *grows* into a substantial change. The moment a request is shaping up to cross the bar above (≈8 files, or any qualitative trigger), **stop free-coding**: ask the user clarifying questions — from technical *and* **product-discovery** angles (see Stage 1) — until scope is crystal-clear, then **enter plan mode (Stage 2)** and follow the pipeline — don't keep ad-hoc editing.

When unsure, default to full; the plan-reviewer (Stage 3) confirms the path was right.

---

## Principles (apply at every stage)

- **Slice small, land complete.** Every unit of work must be finishable by **one specialist agent in a single ≤1M-token-context session** and land **vertically complete** — no half-done state, no `TODO`/debt left behind. If it doesn't fit, decompose further *before* implementing. This is a hard gate, not a guideline.
- **No new tech debt.** A landed slice leaves the codebase at least as clean as it found it: tests added, docs/ARCHITECTURE_TREE updated, no dead code, no silenced errors.
- **The harness is living.** Any task may improve STANDARDS / CLAUDE.md / the `.claude/agents/` role library / this workflow. Stage 9 is how that happens; treat harness improvements as first-class output, not a chore.
- **Delegate liberally to preserve orchestrator context.** Use subagents freely and in parallel — **no resource constraints** — so the orchestrator's own context stays lean for synthesis and decisions (fan out reads, reviews, and implementation to specialists). The orchestrator picks whichever role(s) fit from the `.claude/agents/` library; as the library grows it has more specialists to choose from.
- **Effort-dial the machine.** Scale review/verification depth to the change's risk and size, and load only the standards modules the change *touches* (relevance-gating). A one-line fix gets a quick solo look; a security boundary gets the full lens fan-out. Don't run the whole machine on a trivial change — that's how a harness kills the velocity it's meant to protect.
- Plus the CLAUDE.md non-negotiables: SOLID > DRY > KISS > YAGNI · fail loudly · validate at boundaries · configurable-over-hardcoded · single source of truth.

---

## Context, parallelism & handoff

Keep the **orchestrator's context lean** so it rarely hits the compaction wall mid-work:
- **Delegate the token-heavy work to subagents** (exploration, implementation, review) — they burn *their* context and return digests. This is the main defense.
- **Run in parallel git worktrees** when useful (e.g. implementer + reviewer at once) — isolated checkouts, no clobbering. *(Boris Cherny calls parallel worktrees his "biggest productivity unlock.")*
- **`/clear` between unrelated tasks** — don't carry one feature's context into the next.

If context still runs low, **don't fear auto-compaction** — Claude Code summarizes and continues the same session. But it's *lossy*, so:
- **Keep the plan file current as you go** — the plan + `DECISIONS.md` + `ARCHITECTURE_TREE.md` are the real memory.
- For **long** work, a **fresh session resuming from the plan** beats a deeply-compacted context — `/clear` (or open a new session) and pick up from the plan checklist. No manual "handover" of the orchestrator is needed: a fresh agent upholds quality by reading the plan + DECISIONS + tree + standards.
- Prefer `/compact` **proactively** (with focus, e.g. *"preserve the plan checklist + test commands"*) over hitting the wall. (Auto-compaction has **no configurable threshold** — it just triggers near-full; the real lever is delegation + slicing.)

---

## Roles — a library, not a fixed pair

The orchestrator **selects the role(s) that fit the task** and may spawn several or compose them. It is not locked to a fixed sequence of agents.

Starter library (`.claude/agents/`):
- **`plan-reviewer`** — adversarially critiques a plan (correctness, SOLID/patterns, risk, **sizing & completeness**, over-engineering/YAGNI, harness impact); writes findings into the plan file.
- **`implementer-architect`** — implements an approved spec to standard, in an isolated worktree, landing one slice complete.
- **`product-designer`** — the product/UX lens at Discuss (Stage 1) for user-facing work: user, job-to-be-done, flows, states, "what good feels like"; applies `docs/standards/product-ux.md`, persists to `docs/PRODUCT.md`.
- **`architect-reviewer`** — owns the Verify gate (Stage 7): **solo** for small changes, or **synthesizer** over fan-out findings for risky ones.
- **`lens-reviewer`** — audits a **diff (Verify) or an audit-scope (harness-audit)** against **one** `docs/standards/` module; invoked once per relevant lens in a fan-out review.
- **`yagni-sentinel`** — the anti-over-engineering skeptic; argues a plan/diff is *too much*. The deliberate counterweight to the quality lenses.

Also available without new files: built-in **`Explore`** (fan-out search), **`Plan`** (drafting), and `/code-review` · `/simplify` for diff cleanup. **Add new role files as needs emerge** — the library grows (Stage 9).

---

## The pipeline

| # | Stage | Owner | Output |
|---|-------|-------|--------|
| 0 | **Triage** | orchestrator | full vs lightweight path |
| 1 | **Discuss & brainstorm** | orchestrator + **user** | learn the endeavour from multiple **angles** before planning — technical scope **+ product-discovery** (who's the user · the job-to-be-done · what success/"delight" looks like · the key flows & their states); these surface the user-story gaps a technical-only intake misses. User-facing work pulls in `product-designer` → `docs/PRODUCT.md`. Crystal-clear scope; tangents→ROADMAP, decisions→DECISIONS |
| 2 | **Draft plan** | orchestrator / `Plan` | `.claude/plans/NNNN-<slug>.md` from `TEMPLATE.md`, **sliced into ≤1-session units** |
| 3 | **Review the plan** | `plan-reviewer` (+ others as fit) | critique written into the plan's *Review* section; iterate until it passes the gate |
| 4 | **Spec** | orchestrator | plan upgraded to implementation-ready spec **per slice**: file-by-file changes, signatures, test list, acceptance criteria, **+ the in-scope `ENGINEERING_STANDARDS` dimensions & target bar** |
| 5 | **Approval gate** | **user** | sign-off on the spec — *no code before this* |
| 6 | **Implement** | `implementer-architect` | one slice/session, isolated worktree/branch; upholds CLAUDE.md; updates ARCHITECTURE_TREE inline |
| 7 | **Verify** | `architect-reviewer` (+ lenses) | **effort-dialed:** small change → `architect-reviewer` audits solo; risky/cross-cutting → fan out `lens-reviewer`s (one per relevant `docs/standards/` module) **+** `yagni-sentinel`, then `architect-reviewer` **synthesizes**. All gates green (full tests + regression/snapshot + `check-tree` + lint/type-check/security); run **`/simplify`** + **`/code-review`**; confirm spec match. Findings are **dual-layer** (technical + plain-English). |
| 8 | **Land & archive** | orchestrator | conventional commit/PR; move plan → `docs/archive/<year>/`; append DECISIONS |
| 9 | **Retrospect & evolve** | orchestrator | harvest learnings into the harness (see below) |

**Stage 3 gate — a plan may not pass review until:** it is correct & sound (SOLID/patterns), each slice is **session-sized and lands complete with no debt**, the right path was chosen, risks + test strategy are stated, and any harness impact (new STANDARD/agent/doc) is noted. The reviewer writes a verdict + required changes into the plan; the orchestrator iterates.

**Keep the docs current — it's part of each stage (no hooks needed beyond the tree check):**
- **Implement (6):** update `ARCHITECTURE_TREE.md` for any file add/move/remove (also hook-nudged); touch `CLAUDE.md` only for a genuinely new gotcha/command/pattern — *concisely; index, don't duplicate code*.
- **Land (8):** append a dated one-liner to `DECISIONS.md` for non-trivial choices; update `ROADMAP.md` if scope shifted.
- **Retrospect (9):** promote durable learnings into `ENGINEERING_STANDARDS.md` / `CLAUDE.md` / agent files.

---

## Definition of Done

A slice is **done** — and may land (Stage 8) — only when **all** hold:
1. **Acceptance criteria met** (the spec's checklist).
2. **In-scope `docs/standards/` modules pass** the `architect-reviewer` audit (solo, or synthesized from `lens-reviewer`s + `yagni-sentinel`), for what this slice touches.
3. **All gates green:** full test suite + any regression/snapshot tests + `check-tree` + the project's lint / type-check / security gates + `/simplify`/`/code-review`.
4. **No new tech debt.**

Iterate to meet this **fixed** bar, then **stop** — it terminates because the bar is *finite*, not "is it perfect?". Genuinely separate future work → `ROADMAP.md` (backlog, *not* debt).

---

## Executing an audit backlog item — tag → discipline

`/harness-audit` writes a tagged backlog into `docs/ROADMAP.md`; there is **no separate refactor command**. Each item runs through the pipeline above, and its **tag selects the discipline** the implementer applies. (Rationale is settled — see `DECISIONS.md` Decision 2; don't re-litigate it here.)

| Tag | Discipline |
|-----|-----------|
| **`refactor`** | **Characterization-tests-first — a HARD precondition.** A refactor item on untested behavior-bearing code **cannot start until its Tier-1 "establish a test baseline" item is done**; if that baseline is absent, the implementer **stops and asks** rather than touching code. Durable enforcement will be the Trust-track `PreToolUse` characterization hook (the first Phase-1 item); **until that hook lands, this is upheld by the implementer + the Verify gate** — not yet automatic. |
| **`capability-upgrade`** | Migration safety — feature-flag the new path · dual-write / shadow-read · keep a rollback. |
| **`dependency-health`** | Update + verify — bump, run the full suite green, check the changelog for breaking changes. |
| **`bug`** | Reproduce-first — a **failing test that captures the bug**, then the fix that makes it pass. |
| **`feature`** | The standard pipeline (no extra precondition). |

---

## 9. The learning loop (how the harness grows)

After a slice lands, **harvest** before moving on:

- A convention that recurred across review findings → promote to **STANDARDS / CLAUDE.md**.
- A prompt tweak that made a specialist sharper → fold into the **`.claude/agents/` role file**.
- Friction in the process itself → edit **this `WORKFLOW.md`**.
- A notably clean implementation → record it as the **reference pattern** to copy (promotion rule).
- Every non-trivial choice → one dated line in **`DECISIONS.md`**.

**Two tiers (manual for now).** A *universal* lesson → propose it as a candidate **global** standard: stage it in `docs/standards/CANDIDATES.md`, then promote upstream into the plugin so **every** repo gets it on the next update. A *codebase-specific* lesson → keep it **local** (`CLAUDE.md` / `DECISIONS.md` / the repo's Current-scope), never propagated. Either way, **the user approves** before promotion.

Periodically run a **consolidation pass** (merge duplicates, prune stale guidance, keep the index lean). The intent: each task starts smarter than the last. Feedback flows *upstream* from any stage — a plan-reviewer finding, an implementer surprise, a verification failure can all become a permanent harness improvement.

```
task → DECISIONS/ROADMAP → (periodic) consolidation → STANDARDS · CLAUDE.md · agents · WORKFLOW updated → next task starts smarter ↺
```

---

## Plan file lifecycle

`​.claude/plans/NNNN-<slug>.md` (active, contains Plan + Review + Spec + slice checklist) → on completion, move to `docs/archive/<year>/`. One plan per substantial change; the slices inside it are the per-session units. Numbering is sequential (`0001`, `0002`, …).
