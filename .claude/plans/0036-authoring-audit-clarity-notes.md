# 0036 — Authoring-audit clarity notes: adopter tree-gate timing + maintainer agents-array rationale (docs only)

- **Status:** Draft (fine-tuning; authoring-audit + adversarial verification 2026-07-03). **Blockers:** none. Additive; docs-only; no behavior change. Does NOT touch 0029/0030's landed work.
- **Resumable from:** Slice 1 — not started.
- **Disposition at close:** done / deferred (ROADMAP) / rejected (DECISIONS) per slice.
- **References:** the harness self-authoring audit (`wf_2d9c6e3f-807`) + its adversarial gap-verification (`wf_3585df76-c5f`, 5-of-6 gaps refuted) · Claude Code `plugins-reference` (auto-discovery + the agents-array replaces-not-augments footgun) + `hooks` docs · `docs/claugentic-DECISIONS.md:18` (the tree-gate commit-time altitude) + `:94` (Plugin identity & distribution) · `docs/claugentic-PLAYBOOK.md` (adopter-facing) · `skills/init/SKILL.md:622-648` (the CLAUDE.md managed-fence content) · `.claude-plugin/plugin.json` (the `agents` array).

## Problem

A self-authoring audit compared the harness's OWN skills/agents/plugin/orchestration against the real Claude Code authoring docs. **The harness is strongly aligned** — 28 of 42 findings aligned; the whole orchestration layer 13/13 aligned. Adversarial verification then **refuted 5 of the 6 surfaced gaps** as aligned-by-design or false-premise (see *Refuted, do-not-re-litigate* below). **One genuine gap survived**, plus one adjacent maintainer-clarity note:

1. **Adopter-facing (the survivor):** the architecture-tree gate validates at **`git commit` time, not in-session** (a deliberate altitude — determinism + adopter portability, DECISIONS:18). But an adopter's read-on-demand `PLAYBOOK.md` and always-loaded `CLAUDE.md` managed fence are **both silent** on this. An adopter who adds/moves a source file gets **no explanation** that the tree must be updated and that the check fires at commit — they can be surprised at commit time, or not know the model at all. The rationale is documented **only** in `DECISIONS.md`, which is **dev-only / stripped from the release** — adopters never receive it.
2. **Maintainer-facing (adjacent, tiny):** the `plugin.json` `agents` array is explicit (all 9 agents listed) rather than relying on auto-discovery. This is **deliberate and correct** (the array *replaces* — does not augment — the default `.claude/agents/` scan, so dropping/mis-editing it can silently exclude a new agent), but the *why* is **nowhere recorded** — a future maintainer could "simplify" it away and reintroduce the footgun.

## Goals / Non-goals

- **Goal:** Add a concise adopter-facing note — in `PLAYBOOK.md` (read-on-demand "Under the hood" is the natural home; keep the always-loaded fence lean) — that the tree-check runs at **commit time, not while editing**: add/move a file → update the tree → the pre-commit gate checks it; wanting live in-session validation is an adopter's own optional `PostToolUse` hook. **Framed honestly as a deliberate design (determinism + portability), NOT a limitation or an apology.**
- **Goal:** Record the **agents-array-explicit rationale** as one dense `DECISIONS.md` line under *Plugin identity & distribution* (the array replaces-not-augments the auto-scan → keep it explicit; a footgun to preserve, not "simplify").
- **Goal:** Record the **authoring-audit outcome** as one dated `DECISIONS.md` line (harness strongly aligned; the 5 refuted gaps named) so they are **not re-litigated** — consult-before-revisiting is the ledger's job.
- **Non-goal:** Any change to the commit-time altitude itself (that decision stands — DECISIONS:18) or to the session-time-validation question (**0035 owns** the deferred `PreToolUse` hook — do NOT re-open it here; this only *documents* the current model).
- **Non-goal:** Bloating the byte-identical always-loaded CLAUDE.md managed fence (Spec confirms the home; default = PLAYBOOK, not the fence). No new managed doc; no `init` behavior change beyond the fence's *content* if Spec chooses a one-line fence pointer.
- **Non-goal:** Acting on any refuted gap (skill progressive-disclosure, init-description trim, agent-description routing tighten, per-agent model comments) — verification killed them; they are aligned-by-design.

## Architecture & holistic fit

- **Codebase fit:** docs only — `PLAYBOOK.md` (adopter-facing) + two `DECISIONS.md` lines (maintainer-facing). Clean **separation of concerns by audience**: the *how-it-works* note lives where adopters read (PLAYBOOK); the *why-explicit* rationale lives where maintainers read (DECISIONS). No engine/skill/agent/plugin.json wiring changes.
- **Quality dimensions:** `docs-traceability` (primary — the note is accurate, resolves, and names the deliberate decision) · `product-ux` (adopter clarity — the model is graspable without reading `DECISIONS`). Trust surface → `honesty-reviewer`: the note must (a) frame commit-time as a **deliberate design**, not a defect; (b) **not claim** any in-session enforcement the harness doesn't have (the only hook-enforced gate remains the commit-time tree-check — DECISIONS honesty split); (c) not imply the optional `PostToolUse` hook is provided.
- **Doc-budget interaction:** `DECISIONS.md` is at a WARN (~91.9%). This plan **adds ~2 dense lines** — small, but it must land net-safe. Either condense-on-WARN within this slice (owned here) OR land alongside the pending F9 condensation. The Spec picks; the DoD `check_doc_budgets.py` gate is the backstop (a breach blocks the commit — fail-loud).
- **Future-proofing:** none needed — these document *existing* settled decisions.

## Affected files

- `docs/claugentic-PLAYBOOK.md` — a concise adopter note (in "Under the hood", or a new short subsection): the tree-check validates at commit time, not in-session; update the tree when you add/move a file; wire your own `PostToolUse` hook if you want live validation (optional). Adopter-aware (no harness-self references — DECISIONS:105).
- `docs/claugentic-DECISIONS.md` — (a) one dense line: the agents-array-explicit rationale (replaces-not-augments the auto-scan; keep explicit); (b) one dated line: the authoring-audit outcome + the 5 refuted gaps (do-not-re-litigate). Condense-on-WARN if the additions trip the budget (owned by this slice).
- `docs/claugentic-ROADMAP.md` — two enhancement-candidate lines, gated on **real adoption evidence** (not now): a "Common Adoption Gotchas" digest in INVARIANTS if inline+indexed coverage proves to miss real blind-spots; an optional adopter-guidance note on wiring a design-system / QA MCP (the harness declares none by design — adopters wire their own).
- `docs/claugentic-ARCHITECTURE_TREE.md` — row updates only if a doc's one-line scope description changes (likely none — content added within existing files).

## Refuted, do-not-re-litigate (from the verification — recorded so this plan's scope stays honest)

- **Skill progressive-disclosure refactor** — REFUTED. Skills already externalize procedures to `engine/*.js` + reference managed docs (50+ refs); the self-contained constraint (DECISIONS:79) scopes to *spawned agents*, not skills. Word counts also overstated (init is 10,935 words). The harness already implements the pattern.
- **`init` description trim** — REFUTED (false premise). The `description:` field is ~130 words (not 381 — the finder counted the body), mid-range vs peers, and its "dense" terms are load-bearing trigger keywords; trimming would hurt discovery.
- **Agent-description routing tighten** — REFUTED (false premise). The orchestrator routes by explicit `nsAgent("<role>")` ids (`engine/*.js`), never by parsing description text; the multi-mode descriptions are deliberate (DECISIONS:79, "posture=mode-not-file").
- **Per-agent model-tier comments** — REFUTED. Uniform `model: opus` is deliberate documented policy (DECISIONS:28-32, plan 0031); 9 inline comments would duplicate the central WORKFLOW policy (DRY violation).
- **Skills "Gotchas" sections** — ADJUSTED→dropped-as-work. Failure-modes are already covered inline (init 44+, build 16+, audit 6+ guards) + indexed in DECISIONS/INVARIANTS by deliberate DRY design → a ROADMAP enhancement candidate only.

## Risks & mitigations

- **Risk: the note reads as an apology / "the harness can't validate in-session."** → **Mitigation:** frame as a deliberate altitude (determinism + portability); `honesty-reviewer` checks the tone + that no in-session enforcement is claimed.
- **Risk: re-opening the session-time-validation decision (0035's turf).** → **Mitigation:** explicit non-goal; the note *documents* the current model and points at the adopter's own optional `PostToolUse` hook — it does not propose the harness build one.
- **Risk: the DECISIONS additions trip the doc-budget WARN→breach.** → **Mitigation:** keep the additions to ~2 dense lines; condense-on-WARN within this slice if needed (canonical procedure — WORKFLOW DoD); `check_doc_budgets.py` is the fail-loud backstop.
- **Risk: adopter-facing copy carries a harness-self reference.** → **Mitigation:** the PLAYBOOK note names only adopter-relevant surfaces (their tree, their commit, their optional hook); `docs-traceability` + the DECISIONS:105 adopter-aware rule.

## Test strategy

- **Deterministic gates:** `pytest` · `check_shipped_content.py` (edited PLAYBOOK/DECISIONS — no dangling refs / stranded namespace literals) · `check_doc_budgets.py` (**the load-bearing one** — DECISIONS must stay under budget) · `claugentic-check_architecture_tree.py` (any row change). Docs-only → no `node` / version-sync surface.
- **Reviewer sign-offs:** `docs-traceability` + `product-ux` via `synthesizer-gate`; `honesty-reviewer` on the deliberate-design framing + the no-in-session-enforcement claim.

## Decomposition (slices)

- [ ] **Slice 1 — Adopter tree-gate timing note (PLAYBOOK) + maintainer agents-array + audit-outcome lines (DECISIONS) + ROADMAP enhancement lines; close-out.** One coherent docs slice (all authoring-audit clarity, different audiences by surface). Condense-on-WARN if DECISIONS trips the budget. **In-scope:** `docs-traceability`, `product-ux`; trust surface → `honesty-reviewer`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_

RUNNING AS: Opus 4.x. **Same-model-review caveat:** this plan is fine-tuning authored in an Opus-family session, and I am reviewing on the Opus family — a separate clean-context pass on the most capable model, a reduction of rubber-stamping risk, **not** a model-independent oracle. Opus blind spots are not de-correlated here.

**Verdict: PASS** — with one required correction (a factual premise error, C1) and one required decision (C2). The plan is correctly small, honest, and refuses the refuted work. Neither finding blocks the slice from landing complete; both are things the Stage-4 Spec must fold in.

I verified the load-bearing claims against the real files rather than taking the plan's word — results below.

### Required changes

1. **[C1 — correctness of the plan's own premise] The doc-budget figure is wrong; fix it before it drives a wasted condensation.** The plan states DECISIONS is "at a WARN (~91.9%)" (`Architecture & holistic fit` → Doc-budget interaction; and the `Risks` row). Verified: `docs/claugentic-DECISIONS.md` is **52,866 bytes = 88.1%** of the 60K budget; `WARN_RATIO=0.9` (`scripts/check_doc_budgets.py:60`); running the gate prints **`OK: all managed ledgers within budget`** — it is **NOT in the WARN band** and has ~7,100 bytes (~12%) of headroom. The plan's ~2 dense lines fit trivially. **Correct the figure to ~88.1% (below WARN)** and re-frame: condensation is **NOT required-first** and must **not** be forced into this slice — adding ~2 lines stays well under WARN. `check_doc_budgets.py` (WARN@90%, breach@100%) is a fully sufficient fail-loud backstop here. Keep the "condense-on-WARN within this slice" option only as a *conditional* ("only if the additions somehow trip WARN — they won't at 88%"); the Spec must not treat pre-condensation as a live obligation. This matters because the honesty bar cuts both ways: overstating the plan's own budget pressure could trigger an unnecessary condensation pass (churn + git-history noise) on a false premise.

2. **[C2 — resolve the always-loaded-fence pointer in the Spec, don't defer it as "if Spec chooses"] Decide explicitly whether the fence gets a one-line pointer, and add `skills/init/SKILL.md` to Affected files if it does.** The plan's Non-goal says "no `init` behavior change beyond the fence's *content* if Spec chooses a one-line fence pointer," and Affected-files omits `skills/init/SKILL.md`. Verified: the CLAUDE.md managed-fence content (`skills/init/SKILL.md:621-660`) contains **no** tree-gate/commit-time reference (the only "gate" hit is "the project's own gates," i.e. detected tooling) — so the always-loaded surface an adopter reads *first* is silent, while PLAYBOOK is read-on-demand. The SoC-by-audience reasoning (adopter how-it-works → PLAYBOOK, keep the fence byte-lean; maintainer why-explicit → DECISIONS) is **sound**, and PLAYBOOK "Under the hood" is the right home for the substantive note. But the discoverability half of the gap the plan itself names ("an adopter who adds/moves a file gets no explanation") only closes if the adopter can *find* the PLAYBOOK note. **Decide in the Spec:** either (a) add a single static one-line pointer in the fence (e.g. beside the existing PLAYBOOK pointer: "tree-check timing + adoption gotchas → PLAYBOOK") — this touches only the fence's static, byte-identical-per-run content, **no `init` behavior change** — and **add `skills/init/SKILL.md` (fence-content edit only) to Affected files**; OR (b) justify in the Spec why read-on-demand PLAYBOOK alone suffices (e.g. the SessionStart advisor already surfaces adoption gotchas). My lean is (a): it is the cheapest close of the discoverability half and keeps the fence byte-stable. Leaving it as "if Spec chooses" pushes a real completeness call downstream unframed — the plan-gate's job is to force that decision now.

### Sizing / completeness check

- **Slice 1 — OK, lands complete, no dangle.** One coherent docs-only slice, all authoring-audit clarity, no half-done state, no TODO/debt. Single specialist, single session, far under the ≤1M-context bar. The affected set (PLAYBOOK note + 2 DECISIONS lines + gated ROADMAP lines + conditional TREE row) is tight and atomic. With C2→(a), add the fence-content edit — still one slice, still complete. **No split needed.**
- **Missed affected file:** only the fence (`skills/init/SKILL.md`), handled by C2. No mirror is needed elsewhere — adopter-facing note (PLAYBOOK) + maintainer rationale (DECISIONS) is the complete audience set; the WORKFLOW Adopter-note already covers the tree-hook mechanics at the maintainer altitude, so **no WORKFLOW edit is required** (PLAYBOOK is the genuinely-missing adopter-plain surface — correct call).
- **ROADMAP lines are correctly gated, not manufactured work.** Both enhancement candidates (adoption-gotchas digest; adopter-guidance on wiring a design-system/QA MCP) are conditioned on "real adoption evidence — not now." Right disposition (YAGNI deferral, not scope creep). The plan does not manufacture work to fill the slice.

### Honesty check

- **Scope honesty — PASS.** The plan correctly refuses the 5 refuted gaps and records them in *Refuted, do-not-re-litigate*. I re-verified two refutations against source and both hold: (1) **per-agent model comments** — all 9 agents carry uniform `model: opus` (`grep "^model:" .claude/agents/*.md`), so 9 inline tier comments would duplicate the central policy (DECISIONS:30) — the DRY refutation is correct; (2) **agent-description routing** — the orchestrator routes by explicit `nsAgent("<role>")` ids (`engine/audit.js:44`, `verify.js:34`, `build-item.js:70`, `qa.js:56`), never by parsing description text — the false-premise refutation is correct. The **agents-array claim is accurate**: `.claude-plugin/plugin.json:10-20` lists all 9 agents explicitly, and an explicit array replaces (not augments) the default `.claude/agents/` scan — recording that replaces-not-augments footgun rationale under DECISIONS *Plugin identity & distribution* is warranted and correctly placed.
- **Confirmed gap is REAL — verified independently.** (a) `PLAYBOOK.md` has **zero** matches for commit / pre-commit / tree-check / in-session / PostToolUse / architecture-tree (case-insensitive grep). (b) The fence content (`skills/init/SKILL.md:621-660`) omits any tree-gate timing. (c) `DECISIONS.md:18` documents the commit-time altitude (determinism + adopter portability). (d) `docs/claugentic-DECISIONS.md` is in `build_release.py` `DEV_ONLY_FILES` (`:44`) — **stripped from the release**, so adopters genuinely never receive the rationale. The plan's framing of the gap is fully accurate.
- **Deliberate-design framing — PASS.** Goals + Risks correctly require the note read as a deliberate altitude (determinism + portability), *not* a defect/apology, and forbid claiming any in-session enforcement the harness lacks — consistent with DECISIONS:7 (only the tree-check is hook-enforced) and DECISIONS:24 (unbuilt trust-gates are not claimed). `honesty-reviewer` on the trust surface is correctly convened. Reinforcement for the Spec: keep the verb discipline verbatim — the note documents the adopter's *own optional* `PostToolUse` hook and must never imply the harness *provides* live in-session validation.
- **0035 ownership preserved — PASS.** Session-time-validation is an explicit Non-goal; the note *documents* the current model and does not re-open the deferred hook decision 0035 owns.

### Harness impact

- **No new STANDARD, agent, or WORKFLOW/DoD change.** Docs-only clarity that documents *existing settled* decisions (tree-gate altitude, agents-array-explicit). No mechanical gate, no managed-doc addition, no `init` behavior change (fence *content* only, if C2→(a)).
- **One Stage-9-adjacent note:** the authoring-audit-outcome DECISIONS line (Goal 3) is itself the harvest of this audit — a consult-before-re-litigate record. Keep it a single dated line; do not expand into a narrative.
- **Deterministic gates that will fire:** `check_shipped_content.py` (edited PLAYBOOK ships) — confirm the PLAYBOOK note carries **no** `claugentic-dev-harness:<token>` namespace literal and no dangling stripped-path ref (adopter-aware rule, DECISIONS:33/47/92). `check_doc_budgets.py` passes comfortably (see C1). `check_architecture_tree.py` fires only if a row description changes (likely none — content added within existing files).

## Spec  _(per slice, Stage 4)_

### Slice 1 — resolutions of the plan-gate's C1 + C2 (folded into scope)

**C1 — the doc-budget figure: the plan's ~91.9% WARN STANDS; the reviewer's "88.1% OK" was a char-vs-byte mis-measurement (re-verified).**
The authoritative gate `scripts/check_doc_budgets.py` measures **bytes** (`measured = len(path.read_bytes())`, `:79`) and, run now, **prints `WARN: docs/claugentic-DECISIONS.md: 55114 bytes vs budget 60000 (>= 90%)`** → 55,114 / 60,000 = **91.9% = WARN**. The plan-gate's `52,866` is the UTF-8 **character** count (DECISIONS is em-dash/middot/arrow-dense; bytes − chars ≈ 2,248 of multibyte overhead), not the byte count the gate enforces. **The plan's original figure is correct; C1's premise is wrong — do NOT rewrite the figure to 88.1%/OK** (that would launder a wrong number into the ledger, an honesty breach). Recorded transparently here rather than silently applied or silently ignored.
- **Implication (this is the part C1 got right in spirit):** condensation is **NOT required-first** for this slice — WARN (≥90%, exit 0) is not breach (>100%, exit 1). Adding **one** dense combined DECISIONS line keeps the doc at WARN, not breach; the slice lands. The F9 condensation is a **separate, user-approved pass** (the harness's own rule: a condensation diff is safe only because it is user-approved before apply — DECISIONS doctor entry), NOT folded into this slice.
- **To minimize the add:** collapse Goals 2 + 3 into **one** dense DECISIONS line under *Plugin identity & distribution* — the agents-array-explicit rationale **and** the authoring-audit-outcome/do-not-re-litigate record in a single line (they share the "record a settled plugin-structure decision" nature). One line, not two.

**C2 — resolved to (a): add a one-line static fence pointer.**
Adopt option (a): add a single **static** pointer line in the CLAUDE.md managed fence (beside the existing managed-doc pointers), e.g. *"tree-check timing + adoption gotchas → `docs/claugentic-PLAYBOOK.md`."* It touches only the fence's **byte-identical-per-run static content** — **no `init` behavior change**, the zero-diffs-on-2nd-run property holds. This closes the discoverability half (the always-loaded surface now points to the substantive PLAYBOOK note). **Add `skills/init/SKILL.md` (fence-content edit only, ~lines 622–648) to Affected files.**

**Final Slice-1 affected set:** `docs/claugentic-PLAYBOOK.md` (the substantive adopter note, "Under the hood") · `skills/init/SKILL.md` (one static fence-pointer line) · `docs/claugentic-DECISIONS.md` (ONE dense combined line: agents-array-explicit rationale + audit-outcome do-not-re-litigate) · `docs/claugentic-ROADMAP.md` (two gated enhancement lines) · `docs/claugentic-ARCHITECTURE_TREE.md` (row touch only if a scope-line changes — expected none). **In-scope dimensions:** `docs-traceability`, `product-ux`; trust surface → `honesty-reviewer` (deliberate-design framing · no in-session-enforcement claim · adopter's-own-optional-hook wording · no namespace literal in shipped PLAYBOOK).

**Status: ready to implement** (plan-gate PASS; C1 re-verified, C2 resolved).
