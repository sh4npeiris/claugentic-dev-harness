# 0004 — Audit right-sizing (v0.1.1): auto-dial + YAGNI synthesis + "sound" signal

- **Status:** Spec'd — user-approved ("build it"). A contained enhancement to `/claugentic-dev-harness:audit`.
- **Parent:** post-`0003` (v0.1 functional core shipped). References: `skills/audit/SKILL.md` · `docs/PLAYBOOK.md`.

## Problem

The audit fans out the quality lenses + synthesizes, but two right-sizing gaps remain:
1. **The dial is manual** — you must name `quick`/`standard` (default `standard`); it isn't sized to the repo, so a tiny repo over-audits and a huge one under-warns.
2. **No anti-over-engineering pass on the findings** — an LLM against a rich catalog can almost always find *some* "improvement," so re-runs churn out marginal nice-to-haves and nudge toward the very over-engineering the harness exists to prevent, with **no clear "it's sound, stop" signal.** The `yagni-sentinel` + `/simplify` exist only at the **Verify** stage (checking a change you're *making*) — not in the audit that *generates* findings.

## The slice (all in `skills/audit/SKILL.md` + a `docs/PLAYBOOK.md` note)

1. **Auto-dial.** Phase 1 (Understand) already sizes the repo (in-scope file count · structure · ecosystem · monorepo). Use that to **pick a default dial** when the user didn't name one — **small/simple → `quick`**, **larger/complex/monorepo → `standard`** — and **report the chosen level** with "name `quick`/`standard`/`thorough` to override." A named level always wins. (Applies the harness's existing *effort-dial* principle to the audit itself.)
2. **YAGNI right-sizing in synthesis** (Phase 2, dedup/synthesize step). When consolidating the lenses' findings, **apply the harness's own YAGNI**: keep findings with **real impact**; **cut marginal "nice-to-haves"** that don't earn their keep; **a sound codebase yields few or none**; **never manufacture** an item to fill a tier. A *synthesis discipline*, **not** a separate fan-out (see Out-of-scope). Findings still get tiered/tagged; this trims the Tier-3 noise, it doesn't invent it.
3. **"Architecturally sound" terminal signal** (Phase 3 backlog). When **Tier 1 + Tier 2 come back empty**, the backlog says so plainly: *"Sound on the audited dimensions — what remains is optional polish; you don't need to keep re-auditing."* So the user **knows when to stop**, instead of inferring it.
4. **Usage guidance** (a short SKILL note + a `PLAYBOOK.md` line). The audit is a **periodic snapshot** (run after meaningful changes, not obsessively); the backlog **regenerates** (doesn't accumulate); **Tier 3 is optional**; **empty Tier 1/2 = sound**; the **auto-dial + override**.

## Out of scope (→ later / `thorough`-level)
A full **adversarial `yagni-sentinel` fan-out** over the audit findings (the heavier, deferred `thorough` option — YAGNI to add now). Changing the lens fan-out itself. The cold-install (separate).

## Files
`skills/audit/SKILL.md` (the 4 changes; **keep the loop-until-dry termination intact** — the YAGNI prune happens at synthesis, after dry-detection, so it can't break termination) · `docs/PLAYBOOK.md` (an audit-usage / don't-over-engineer line) · `docs/DECISIONS.md` (entry) · `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` (**version → 0.1.1**) · `docs/ARCHITECTURE_TREE.md` (refresh the audit SKILL caption if it changes).

## In-scope standards + effort dial
- `maintainability-structure` — the synthesis logic stays coherent; the auto-dial heuristic is simple + sound; **the loop still provably terminates**.
- `product-ux` — the "sound" signal + the guidance are legible to a **non-engineer** (the whole point).
- `docs-traceability` — SKILL/PLAYBOOK/DECISIONS accurate.
- **Effort dial: MEDIUM** → `implementer-architect` builds; **Verify = `architect-reviewer` + `yagni-sentinel`** — fittingly, the anti-over-engineering skeptic vetting an anti-over-engineering feature: **it must not over-build** (the prune is an instruction, not a new subsystem). **Version 0.1.1**; re-tag at land.

## Acceptance
- The audit **auto-picks + reports** the dial when none is named; a named level overrides.
- Synthesis **right-sizes** findings (cuts marginal); a clean lens yields **no manufactured items**.
- **Empty Tier 1/2 → the explicit "sound, stop" signal.**
- Usage guidance present in SKILL + PLAYBOOK.
- The audit **still terminates** (loop/dry/caps unchanged; the prune is post-dry).
- `python scripts/check_architecture_tree.py` + `claude plugin validate .` green; version is **0.1.1**.
