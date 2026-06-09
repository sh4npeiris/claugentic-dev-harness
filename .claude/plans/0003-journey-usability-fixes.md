# 0003 — Journey / usability fixes (the "go-button" + the live-colleague unblock)

- **Status:** Draft — Slice 1 in progress; Slices 2–3 for a fresh session
- **Roadmap item:** `docs/ROADMAP.md` → Next #1 (Journey / usability fixes)
- **References:** the journey review (this session); `docs/PLAYBOOK.md`, `README.md`, `skills/init/SKILL.md`, `skills/audit/SKILL.md`, `docs/WORKFLOW.md`, `.claude/plans/TEMPLATE.md`, `scripts/check_architecture_tree.py`

## Problem
The journey review found **both** user paths dead-end one step before the payoff: the docs explain the *philosophy* but never give the next *action* at the moment a non-engineer is stuck.
- **Existing path:** after `audit` writes a backlog, nothing tells the user how to *start* an item (no command, no copy-pasteable sentence — every doc phrases it passively).
- **New path:** after `init` on an empty repo, the funnel sends them to `audit` (a no-op) and never says "just describe your first feature."
- **Latent gate trap:** `INCLUDE_GLOBS` is guessed on an empty repo → as real code lands it mis-targets → the one mechanical gate silently rots (false safety) or throws a raw `.py` error a non-engineer can't fix.
These are **live** for the colleagues already using it.

## Goals / Non-goals
**Goals:** close the "no go-button" blocker on both paths; make the new-project entrance work; stop the gate silently rotting on a wrong glob; lower the on-ramp — all plain-English.
**Non-goals:** NOT building the autonomous build-loop (roadmap #3 — this adds only the doc "go" sentence + a basic "start now?" prompt); NOT a `:work` skill (the journey synthesis cut it as premature — revisit only if the doc fix proves insufficient); NOT the 0002 plumbing.

## Decomposition (slices)
- [ ] **Slice 1 — doc-only "go-button" + on-ramp (cheapest, unblocks colleagues now).**
  - The **"how to start anything"** sentence → `PLAYBOOK.md` + `README.md` + a plain "now do X" line at the end of `audit`'s backlog. *("To start anything — a backlog item or a brand-new project — just tell the agent in plain English what you want ('Let's do Tier-1 item 1' / 'I want to build X'); it asks you questions, then writes a plan + spec for you to approve before any code.")*
  - **Backlog "How to read this" legend** (2 lines inside the audit backlog fence): one phrase per tag; what "checked against the code" vs "could not confirm independently" means.
  - **Beginner on-ramp** (README): "type these in the Claude Code chat input"; a post-install success check ("type `/claugentic` and you should see `:init` and `:audit`"); exact Windows cache path `%USERPROFILE%\.claude\plugin-catalog-cache.json` + "this file is just a cache — deleting it is safe."
  - **Promote "fresh chat after init"** from a Tip to a numbered Quickstart step + a PLAYBOOK line: "if the agent starts writing code without asking you product questions first, say 'use the workflow' — it should pause and ask."
  - **"How to approve a spec" rubric** (PLAYBOOK): the 4–5 plain questions (Does this match what I asked? Anything I care about missing? Are the risks ones I'm OK with? What does it NOT do?) + "if any answer is no, say 'this is missing X, please revise'" + "the technical detail below the plain-English block is for the agent/reviewer — you're not expected to read it."
  - **`init` closing line** (SKILL step 9): a plain-English headline ("Done — I added a code map, a quality checklist, and a safety check; I did **not** change your code") + a generic next-step pointer.
- [ ] **Slice 2 — skill-flow (init/audit).** Branch `init`'s closing report on **repo-state** (has source → "run `:audit`" · empty → "just describe your first feature; skip audit until there's code") + gate Quickstart the same way; **empty-repo guard** in `audit` Phase 1 (no app source → "Nothing to audit yet — describe your first feature"); `audit` Phase 2 **progress beats** + "this can take several minutes" + "empty Tier-1+2 is a SUCCESS" + reassuring `PARTIAL`; **land-step close-out** loop sentence ("This one's done. Next: pick another item the same way, or re-run `:audit`; you're done when Tier 1+2 come back empty"); narrate the **refactor→test-baseline pause** + the **Discuss product-questions** when they fire.
- [ ] **Slice 3 — code + tests: `INCLUDE_GLOBS` self-correction.** The agent re-detects layout and resets `INCLUDE_GLOBS` automatically the first time real source of a recognizable stack appears; surfaces any gate failure as an agent-resolved "updating your codebase map" rather than a raw `.py` error. + characterization tests. (The one non-doc fix — its failure mode, silent false safety, directly violates the honesty pitch.)

## Risks / Test strategy
Doc/skill changes are additive + plain-English; must not over-claim (the verifier is a *reduction* of false confidence, etc.) and must not reintroduce build-history. Gates stay green (`python -m pytest` = 36; `python scripts/check_architecture_tree.py` = OK). Slice 3 is characterization-tested like the existing gate work. In-scope lens: `docs-traceability`, `product-ux` (Slice 1–2); `testing` + `reliability-resilience` (Slice 3).

---
## Review _(pending — Stage 3)_
## Spec _(Slice 1 spec lives in the implementer brief this session; Slices 2–3 spec on pickup)_
