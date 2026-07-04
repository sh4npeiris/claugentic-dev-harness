# 0033 — Context-economy + cache-dynamics grounding (docs only)

- **Status:** Draft (fine-tuning; verified 2026-07-03). **Blockers:** none. Additive; docs-only. Does NOT touch 0029/0030.
- **Disposition:** done / deferred / rejected per slice.
- **References:** FINETUNING-INPUTS → VERIFIED · Claude Code `context-window`, `memory`, `prompt-caching`, `best-practices`, `hooks` docs · `docs/claugentic-DECISIONS.md` → *The deterministic gates* (doc-budget) · `scripts/check_doc_budgets.py`.

## Problem

The harness's context economy (subagent isolation, CLAUDE.md leanness, the doc-budget ledger caps + condense-on-WARN, the no-PostToolUse stance) is **verified to align with official Claude Code guidance** — but the harness doesn't *cite* that grounding, so a reader can't tell which mechanisms are official patterns vs. harness-proprietary. Three grounded, docs-only additions:
1. The official **CLAUDE.md ~200-line cap** + skills-load-on-demand + subagent-isolation guidance **confirms** the harness's approach — worth citing under the doc-budget rationale (grounds a proprietary mechanism in official precedent).
2. **no-PostToolUse is VALIDATED** — the hooks doc classifies per-tool hooks as high-frequency/keep-fast; a one-line WORKFLOW citation locks the rationale so it isn't re-litigated.
3. **Prompt-cache dynamics** for long multi-agent runs (fresh 5-min-TTL subagent caches; System→Project→Conversation ordering; `/compact` at task breaks) are worth a short dev-guide note so adopters structure long runs to keep caches warm.

## Goals / Non-goals

- **Goal:** Cite the official CLAUDE.md-lean / skills-on-demand / subagent-isolation guidance next to the harness's context-economy mechanisms — **labelling the explicit doc-budget CAP mechanism as HARNESS-PROPRIETARY** (the *spirit* is official; the byte-caps are not — never call the caps "official guidance").
- **Goal:** A one-line WORKFLOW/DECISIONS citation that **no-PostToolUse is officially well-founded** (per-tool hooks are high-frequency; the SessionStart+commit-time-tree-check architecture is the right call).
- **Goal:** A short **cache-dynamics** dev-guide note (fresh subagent caches, prefix ordering, `/compact` at breaks) for adopters running long multi-agent flows.
- **Non-goal:** Any architectural change — this is grounding/citation only; the harness's context economy is validated as-is.
- **Non-goal:** Over-claiming the doc-budget caps as official.

## Architecture & holistic fit

- **Codebase fit:** docs only (WORKFLOW/DECISIONS + a dev-guide note). No machinery.
- **Quality dimensions:** `docs-traceability` (primary — citations resolve, proprietary-vs-official labelled). Trust surface → `honesty-reviewer` (the proprietary/official split is THE honesty check — don't launder a harness mechanism into official guidance).
- **Future-proofing:** none needed; grounding is stable.

## Affected files

- `docs/claugentic-DECISIONS.md` (or WORKFLOW) — cite the official 200-line CLAUDE.md cap + skills-on-demand + subagent-isolation under the doc-budget rationale; label the cap mechanism harness-proprietary; the no-PostToolUse official-well-founded citation.
- A short dev-guide note (in PLAYBOOK or a `docs/` dev note) — cache dynamics for long multi-agent runs. *(Confirm at Spec: fold into an existing doc; no new managed file unless it earns it.)*
- `docs/claugentic-ARCHITECTURE_TREE.md` — row updates if a doc's scope changes.

## Risks & mitigations

- **Risk: laundering the doc-budget caps as "official."** → **Mitigation:** `honesty-reviewer` — the *spirit* is official, the explicit caps are harness-proprietary; the copy must say so.
- **Risk: over-adding a new managed doc.** → **Mitigation:** fold into an existing doc; YAGNI (confirm at Spec).

## Test strategy

- **Deterministic gates:** `pytest`, `check_shipped_content.py`, `check_doc_budgets.py` (the citations must not trip the DECISIONS/CLAUDE budget — condense-on-WARN if they do, owned by this plan's slice), `claugentic-check_architecture_tree.py`.
- **Reviewer sign-offs:** `docs-traceability` via `synthesizer-gate`; `honesty-reviewer` on the proprietary-vs-official split.

## Decomposition (slices)

- [ ] **Slice 1 — Context-economy grounding + no-PostToolUse citation + cache-dynamics note (docs).** DECISIONS/tree; condense-on-WARN if the citation trips a budget. **In-scope:** `docs-traceability`; trust surface → `honesty-reviewer` (proprietary-vs-official).

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_

RUNNING AS: Opus 4.x. **Same-model-review caveat:** this fine-tuning plan was authored in an Opus-family session and I am reviewing on the Opus family — a separate clean-context pass on the most capable model, a reduction of rubber-stamping risk, **not** a model-independent oracle. Opus blind spots are not de-correlated here.

**Verdict: CHANGES REQUIRED** — the plan is honest on THE load-bearing check and correctly scoped as grounding-only, but three things must be fixed at Spec before it lands: (C1) doc-derived numbers/wording must be re-confirmed at implement, not transcribed as fact; (C2) coordinate the DECISIONS add with 0036 (both edit a WARN-band ledger in the same window and both touch the no-PostToolUse concept); (C3) tighten the cache-dynamics note against YAGNI or fold it into item 1. None require re-slicing — the single docs slice is right-sized and lands complete. I verified the load-bearing claims against the real files/gate rather than taking the plan's word.

### Honesty check (the #1 gate — verified against DECISIONS:86)

- **The proprietary-vs-official split HOLDS everywhere — PASS (this was the blocker check, and it clears).** The plan labels the byte-cap mechanism HARNESS-PROPRIETARY in **four** places and forbids laundering it as official: Goal (`:16` "the byte-caps are not — never call the caps 'official guidance'"), Non-goal (`:20` "over-claiming the doc-budget caps as official"), Quality-dimensions (`:25` "don't launder a harness mechanism into official guidance"), and the Risk row (`:36` "the *spirit* is official, the explicit caps are harness-proprietary; the copy must say so"). This matches DECISIONS:86 verbatim in intent (spirit = official; explicit-cap mechanism = proprietary). The `honesty-reviewer` on the trust surface is correctly convened. No slip. **Reinforce for the Spec:** the copy must attribute *only the spirit* (load-sparingly / prune-aggressively) to official guidance and name the byte-caps + condense-on-WARN as the harness's OWN forcing-function — never "the official 200-line cap, which we implement as byte-budgets" (that phrasing would imply the caps are the official mechanism).

### Required changes

1. **[C1 — unverifiable-as-fact: the plan asserts doc-derived claims as settled, with no re-confirm step] Add a "WebFetch-to-confirm-at-implement" line for the three doc-grounded claims.** The plan states them as fact: "**verified to align** with official Claude Code guidance" (`:9`), "the official **CLAUDE.md ~200-line cap**" (`:10`), "**no-PostToolUse is VALIDATED** — the hooks doc classifies per-tool hooks as high-frequency/keep-fast" (`:11`), and the cache-dynamics specifics ("fresh 5-min-TTL subagent caches; System→Project→Conversation ordering", `:12`). These rest entirely on the Claude Code `context-window`/`memory`/`prompt-caching`/`hooks` docs. They *were* WebFetched once by the FINETUNING-INPUTS research fan-out (see FINETUNING-INPUTS:77-86, "6-cluster research fan-out WebFetched the real docs"), so they are grounded — but a plan whose **entire output is citations that transcribe exact numbers and doc classifications** must re-confirm the load-bearing literals at implement, because a stale "~200-line" or "5-min TTL" written into a managed ledger becomes a durable over-precise claim the harness can't defend. **Add to Test strategy / Slice 1:** at implement, `WebFetch` the `memory` + `prompt-caching` + `hooks` docs and confirm (a) the CLAUDE.md line-count guidance and its exact framing, (b) the per-tool-hooks "high-frequency/keep-fast" classification, (c) the subagent cache-TTL + prefix-ordering claims — cite what the doc *actually* says; **soften any number the doc doesn't state to the doc's own hedge** (prefer "keep CLAUDE.md lean / the docs' order-of-magnitude guidance" over a hard "~200-line cap" if the doc is itself approximate). A citation the plan cannot ground at implement is dropped, not asserted.

2. **[C2 — dedup / collision with 0036 + the same-window DECISIONS budget] Coordinate the DECISIONS edit with 0036, and cross-reference the two no-PostToolUse touches so they don't collide or duplicate.** Two real overlaps, both verified:
   - **No-PostToolUse concept is touched by both plans.** 0033 item 2 (`:11`,`:17`) adds a maintainer-facing "no-PostToolUse is officially well-founded (per-tool hooks are high-frequency)" citation to WORKFLOW/DECISIONS. 0036 already lands an **adopter-facing** PLAYBOOK note that the tree-check fires at commit-time-not-in-session and that adopters wire *their own* optional `PostToolUse` hook. They do NOT contradict (0033 = maintainer *why the architecture is right*; 0036 = adopter *when it fires + your own hook option*) — **but the underlying fact is one fact** (DECISIONS:18 already records "NOT the per-action `PostToolUse`/`Stop` hooks … zero per-tool overhead"; DECISIONS:62 already says "model-upheld / no-PostToolUse"). **The plan must state:** 0033's citation *grounds* the existing DECISIONS:18 rationale (add the "official: per-tool hooks are high-frequency" clause **to/beside DECISIONS:18**, don't open a new parallel entry — DRY), and it must **not** restate 0036's adopter-facing PLAYBOOK material. Name 0036 in References so the two land aware of each other.
   - **Both edit DECISIONS while it is at WARN, in the same landing window.** Verified live: `check_doc_budgets.py` prints `WARN: docs/claugentic-DECISIONS.md: 55114 bytes vs budget 60000 (>= 90%)` — 91.9%, exit 0, **only 4,886 bytes of headroom to breach**. 0033's premise here is **correct** (unlike an inflated figure would be — the gate confirms 91.9% WARN). But 0036 *also* adds ≥1 dense DECISIONS line in the same window; their combined add can eat 700–1,400 bytes of that 4,886-byte headroom. Neither plan alone breaches, but **whichever lands second must re-run `check_doc_budgets.py` against the other's already-landed text** and condense-on-WARN if the combined total approaches breach. The plan already owns condense-on-WARN (`:41`,`:46`) — extend it to say "**including any DECISIONS growth 0036 landed first**"; the condensation is a **separate user-approved pass** (the harness's own rule — DECISIONS doctor entry: a condensation diff is safe only because it is user-approved before apply), never silently folded into this slice.

3. **[C3 — YAGNI: the cache-dynamics note is the one item that is net-new adopter guidance, not grounding] Justify or fold it.** Items 1 and 2 *ground existing, working mechanisms* in official precedent — that earns its place because the reader genuinely can't tell official-pattern from harness-proprietary today (the honesty split needs the citation). Item 3 (the cache-dynamics dev-guide note — `:12`,`:18`,`:31`) is different: it is **new how-to guidance for adopters running long multi-agent flows** ("structure long runs to keep caches warm"), not a citation of something the harness already does. That risks scope-creep past a grounding-only plan. **Decide at Spec:** either (a) **fold it into item 1's grounding** as one line under the context-economy citation ("subagent caches are fresh per the platform's prompt-caching model; `/compact` at task breaks — per the docs") — grounding, not a how-to guide; OR (b) keep it as a standalone PLAYBOOK "Under the hood" note **only if** it earns its bytes by being genuinely actionable and adopter-relevant, and confirm at implement it isn't speculative advice the docs don't support (ties to C1). The plan's own instinct — "**no new managed file unless it earns it**" (`:31`,`:37`) — is the right call; make it a hard **no-new-file** decision at Spec (PLAYBOOK "Under the hood", line 66, is the confirmed home — there is no separate dev-guide doc and one must not be created). My lean is (a): a single grounded line is DRY-consistent with items 1–2 and dodges the "is this speculative adopter advice?" risk entirely.

### Sizing / completeness check

- **Slice 1 — OK, lands complete, no split needed.** One coherent docs-only slice (context-economy grounding + no-PostToolUse citation + cache-dynamics note). No half-done state, no `TODO`/debt, single specialist, single session, far under the ≤1M-context bar. The affected set (a DECISIONS/WORKFLOW citation block + one PLAYBOOK note + a possible tree-row touch) is tight and atomic. C1/C2/C3 fold into this one slice's Spec without growing it — they *tighten* scope, not expand it. **No new managed file** (C3) keeps it minimal.
- **No architectural change — CONFIRMED (task point 4).** The plan claims none (`:19` "Any architectural change" is a Non-goal; `:26` "grounding is stable") and the authoring-audit found orchestration/context-economy 13/13 aligned, so pure citation is the correct posture. I confirm 0033 adds **zero** machinery: docs only, no engine/skill/agent/plugin.json/gate wiring. The "Affected files" set (`:28-32`) is docs + a conditional tree-row — no code. Correct.
- **No manufactured work.** Three items, each grounded in a real FINETUNING-INPUTS VERIFIED verdict; nothing invented to fill the slice. If C3→(a), the slice legitimately shrinks — that is the right direction for a grounding-only plan.

### Harness impact

- **No new STANDARD, agent, WORKFLOW-mechanism, or DoD change.** Docs-only grounding that cites *existing settled* mechanisms (subagent isolation, CLAUDE.md leanness, the doc-budget caps, no-PostToolUse). No mechanical gate added; the proprietary-vs-official honesty split is *documented*, not enforced.
- **One Stage-9-adjacent record:** the no-PostToolUse "officially well-founded" citation is a consult-before-re-litigate record — keep it a clause on DECISIONS:18 (C2), not a new narrative entry.
- **Deterministic gates that will fire:** `check_doc_budgets.py` (**the load-bearing one** — DECISIONS at 91.9% WARN; condense-on-WARN owned by this slice, coordinated with 0036 per C2). `check_shipped_content.py` (edited PLAYBOOK ships → confirm no `claugentic-dev-harness:<token>` namespace literal and no dangling stripped-path ref; the cache-dynamics note in adopter-facing PLAYBOOK must stay adopter-aware — DECISIONS:105). `check_architecture_tree.py` fires only if a doc's one-line scope description changes (likely none — content added within existing files). **Note:** DECISIONS/WORKFLOW are dev-only/stripped, so their citations never reach adopters (item 3's PLAYBOOK note is the only adopter-facing surface — keep it self-contained and hedge-honest per C1).

## Spec  _(per slice, Stage 4)_

### Plan-gate resolutions (folded into scope)

- **C1 — re-confirm the literals at implement, hedge the unstated.** The "~200-line CLAUDE.md cap", "no-PostToolUse validated", and "5-min-TTL cache" claims are WebFetched-once, not durable fact. Slice 1 **re-fetches** (`memory` / `prompt-caching` / `hooks`) at implement and **hedges any number the doc doesn't state verbatim** — never bake a stale figure into the ledger as fact. Where a figure can't be re-confirmed, cite the *principle* (load-sparingly / keep-hooks-fast), not a number.
- **C2 — dedup with 0036: GROUND DECISIONS:18, do NOT fork.** 0033's no-PostToolUse citation and 0036's adopter-facing commit-time note touch **one fact** (already at DECISIONS:18/:62). 0033 adds a **clause on the existing DECISIONS:18 entry** ("officially well-founded — per-tool hooks are high-frequency/keep-fast"), never a parallel entry (DRY). **Sequencing:** 0036 lands the adopter-facing side first; 0033 then grounds the maintainer side referencing it. Whichever of {0033, 0036, 0034} lands second/third into the WARN-band DECISIONS **re-runs `check_doc_budgets.py`** against the other's landed text; condensation stays a **separate user-approved pass** (F9), not force-folded here.
- **C3 — the cache-dynamics note earns its place or folds.** Items 1–2 ground working mechanisms (keep). Item 3 (cache dynamics for long multi-agent runs) is net-new adopter how-to, not grounding — **fold it into item 1 as one grounded line** in PLAYBOOK "Under the hood" (confirmed home, no new managed file), unless Spec finds it genuinely actionable standalone. Default: fold.
- **Status: ready to implement** (plan-gate CHANGES-REQUIRED resolved; docs-only; expected PASS on re-gate). **Build AFTER 0036** (C2 dedup ordering).
