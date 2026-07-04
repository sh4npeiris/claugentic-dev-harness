# 0032 — Skills taxonomy mapping + edge-skill pointers (docs only)

- **Status:** Draft (fine-tuning; verified 2026-07-03). **Blockers:** none. Additive; docs-only; no behavior change. Does NOT touch 0029/0030.
- **Disposition:** done / deferred (ROADMAP) / rejected (DECISIONS) per slice.
- **References:** FINETUNING-INPUTS → VERIFIED · the "how we use skills" blog (9-category taxonomy) · Claude Code `cli-reference`/`common-workflows` (`/loop`, `/goal`) · the slash-command audit in FINETUNING-INPUTS.

## Problem

Two verified, grounded, docs-only opportunities:
1. The harness's own skills (`init`/`audit`/`build`/`product`/`doctor`) + the bundled defaults have **no map to the blog's 9-category skill taxonomy** — a discoverability + design-discipline lens.
2. Several **bundled default skills are genuine edge-adoptions** the harness doesn't reach: `/debug` (an *investigation* front-end for an unknown failure → feeds a `bug` item; the harness governs *fixing* a known bug, not *diagnosing* an unknown one), `/architecture` (a full ADR as a Stage-2 working artifact → distil ONE DECISIONS line at Land), `/skill-creator` (its description-triggering evals for the harness's OWN skills → addresses the stale-eval/BASELINE drift), `/incident-response` + `/deploy-checklist` (the known post-Land ops gap — "lifecycle stops at Land"). These are **pointers**, not custom wiring.

## Goals / Non-goals

- **Goal:** Add WORKFLOW **pointers** to the edge-skills at the right stages: `/debug` as the diagnosis front-end to the `bug` tag (a WORKFLOW tag-table / `reliability-resilience` pointer); `/architecture` as a Stage-2 ADR option (distil to one DECISIONS line); `/skill-creator` for the harness's own skill dev; `/incident-response` + `/deploy-checklist` as post-Land ops pointers for adopters who ship.
- **Goal:** Map the harness's own skills (+ the bundled ones) to the **9-category taxonomy** — a short `SKILLS_TAXONOMY` note or SKILL.md frontmatter — for discoverability.
- **Goal (corrected):** A correctly-scoped `/loop` + `/goal` pointer — as **post-automation** tools (e.g. after `/code-review`/`/debug` closes issues), **NOT** multi-agent orchestration. *(Verified: `/loop` = fixed-interval/self-paced/maintenance modes; `/goal` = condition-persistence. The dossier's "turn/goal/time/proactive" + "spins up its own harness" framing is WRONG — do not use it.)*
- **Non-goal:** Displacing harness-better skills. `system-design`/`tech-debt`/`code-review`/`testing-strategy` are strictly weaker inside the pipeline (single-shot, self-graded) — SKIP them (record the carve-out, don't wire).
- **Non-goal:** Any new skill/agent/engine/command. Pure pointers + a taxonomy map.

## Architecture & holistic fit

- **Codebase fit:** WORKFLOW (pointers) + a small taxonomy note. No machinery. SoC: the harness governs its pipeline; the edge-skills fill the edges it doesn't reach (diagnosis, ADR rigor, ops, its own skill-dev). DRY: pointer-not-restate.
- **Quality dimensions:** `docs-traceability` (primary — the pointers resolve, the taxonomy map is accurate) · `product-ux` (discoverability). Trust surface → `honesty-reviewer` (the harness-better carve-outs are honest; `/loop`-`/goal` uses the CORRECTED framing; no over-claim that a pointer is wired behavior).
- **Future-proofing:** the taxonomy map is the natural home for a new harness skill's category.

## Affected files

- `docs/claugentic-WORKFLOW.md` — edge-skill pointers at the right stages (tag-table `/debug`; Stage-2 `/architecture`; post-Land ops); the corrected `/loop`-`/goal` note; the harness-better SKIP carve-out (one line).
- `docs/claugentic-standards/reliability-resilience.md` — a `/debug` pointer for unknown-failure investigation (if it's the right home; confirm at Spec).
- A short `docs/claugentic-SKILLS_TAXONOMY.md` OR a note in an existing doc — map harness + bundled skills to the 9 categories. *(Confirm at Spec: a new managed doc vs. a note in PLAYBOOK/WORKFLOW — prefer NOT a new managed file unless it earns its `init`/tree surface; KISS.)*
- `docs/claugentic-DECISIONS.md` — one line (edge-skill pointers adopted; `/loop`-`/goal` corrected framing; harness-better SKIP carve-out).
- `docs/claugentic-ARCHITECTURE_TREE.md` — rows for any new doc + updated WORKFLOW row if scope changes.

## Risks & mitigations

- **Risk: repeating the debunked `/loop`-`/goal` "orchestration" framing.** → **Mitigation:** the spec uses the CORRECTED terminology (three loop modes; `/goal` = condition-persistence; post-automation only); `honesty-reviewer` checks it.
- **Risk: a pointer reads as wired behavior.** → **Mitigation:** frame as "consider `/debug` here" (model-upheld option), never "the harness runs `/debug`."
- **Risk: a new managed `SKILLS_TAXONOMY.md` over-adds surface.** → **Mitigation:** prefer a note in an existing doc; only make a new file if it genuinely earns it (YAGNI — confirm at Spec).

## Test strategy

- **Deterministic gates:** `pytest`, `check_shipped_content.py` (new/edited docs — no dangling refs/stranded literals), `check_doc_budgets.py`, `claugentic-check_architecture_tree.py` (any new doc row). Docs-only → no `node`/version-sync surface.
- **Reviewer sign-offs:** `docs-traceability` + `product-ux` via `synthesizer-gate`; `honesty-reviewer` on the `/loop`-`/goal` framing + the pointer-not-wired framing.

## Decomposition (slices)

- [ ] **Slice 1 — Edge-skill pointers + corrected `/loop`-`/goal` + harness-better carve-out (WORKFLOW).** **In-scope:** `docs-traceability`, `product-ux`; trust surface → `honesty-reviewer`.
- [ ] **Slice 2 — Skills-taxonomy map (note or lean doc) + close-out (DECISIONS/tree).** **In-scope:** `docs-traceability`.

---

## Review  _(synthesizer-gate plan-gate, Stage 3)_
_(to be filled)_

## Spec  _(per slice, Stage 4)_
