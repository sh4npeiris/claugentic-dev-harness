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
_(to be filled)_

## Spec  _(per slice, Stage 4)_
