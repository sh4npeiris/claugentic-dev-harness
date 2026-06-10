# 0007 — Cross-model adjudication at the verify gates

- **Status:** Done — landed `a911eb6`; archived 2026-06-10
- **Roadmap item:** `docs/ROADMAP.md` → Next #4 ("Cross-model adjudication at the verify gates")
- **References:** `docs/DECISIONS.md` (*Trust-first*; the 0005/0006 honesty entries) · `docs/WORKFLOW.md` · `skills/audit/SKILL.md` (step 7) · `skills/build/SKILL.md` (the refusal) · the four judge agents
- **Stage-3 review:** PASSED with required changes folded in (see *Review* — and the panel itself ran **cross-model**: `plan-reviewer` + `honesty-reviewer` on fable, dogfooding the design under review; both returned findings the prior same-model panels structurally missed).

> **Trust surface — Stage-3 diverse panel** (`plan-reviewer` + `yagni-sentinel` + `honesty-reviewer`; `product-designer` not convened — no flow/state change; the user-visible surface is copy + a tag, owned by the honesty lens).

---

## Problem

Every reviewer — including the judges that *gate* work — runs on the **same model class as the builder** (all 9 agents `model: opus`). The harness's #1 stated risk (*Trust-first*) is the same model class grading its own work; clean context + adversarial posture reduce contamination, but **errors stay correlated** — a shared blind spot passes both builder and judge.

**The precondition was checked this session (Stage-1)** — evidence, not proof: `claude-fable-5` is **real and spawn-wireable** (demonstrated via the model override), and **one refute-first smoke test showed judge-grade behavior** (it refuted a claim against `check_versions_synced.py` with exact line citations and unprompted probed a residual failure angle). It also articulated the honest register unprompted: *"reduced shared-blind-spot risk," not "independent verification."* **The Stage-3 panel for this very plan then ran cross-model and out-performed prior same-model panels** — a second, live data point.

## The wiring (spike-resolved — ONE mechanism)

A pre-slice spike settled the open wiring question: **frontmatter `model: fable` does NOT resolve** (an agent with fable frontmatter and no override ran as Opus). The **spawn-site override is the proven mechanism** (the Stage-1 test and the Stage-3 fable panel both used it). So:

- **The pin lives at the spawn sites, not in frontmatter:** the instructions that convene the four judges — the WORKFLOW panel bullet · `skills/audit/SKILL.md` step 7 (`finding-verifier` spawns) · `skills/build/SKILL.md` steps 3/6 (`plan-reviewer`/`architect-reviewer` spawns) — each say: **spawn this judge with the `fable` model override.** Still a static pin (the user's chosen design), just at the instruction that actually controls the model.
- **Frontmatter stays `model: opus`** — the *honest* fallback default (it is what actually runs if the override is omitted or unavailable). A non-resolving `fable` in frontmatter would itself be a false-wiring claim.
- Each judge's prose gains one line: *"intended to run cross-model (a different model family than the builder), passed by the orchestrator at spawn."*
- **On a spawn ERROR** (the override model unavailable on an account): respawn with the default + apply the tag (below) — the gate role never becomes unspawnable.

## The self-identification rule (one mechanism, every same-model case)

Each of the four judges **opens its output with `RUNNING AS: <model family>`** (the platform tells an agent its model; the Stage-1 + spike agents both self-identified accurately). The orchestrator compares that self-report to its own session/builder family:

- **Different family** → cross-model, no tag.
- **Same family — for any reason** (the override fell back · the model is unavailable on this account · the session/builder itself runs fable) → apply the **verbatim tag**: *"same-model review on this run — the judge and the builder are the same model family here."*

One rule, detection included, covering every same-model path — no per-trigger machinery. The comparison is **model-upheld** (the orchestrator must do it), stated as such. The tag text is fixed verbatim in its two homes (WORKFLOW + the audit run-report) **to resist drift** into euphemism.

## Goals / Non-goals

**Goals**
- The **four gate/refute roles** — `finding-verifier` · `architect-reviewer` · `honesty-reviewer` · `plan-reviewer` — run cross-model via the spawn-site pin. Finders + the builder stay `opus`. *(yagni dissented on `plan-reviewer` — "it grades the orchestrator's plan, not the builder's code"; **kept by user decision + live counter-evidence**: in build mode the orchestrator both drafts and convenes review of plans — same-class-grading-own-artifact is real there — and this session's fable `plan-reviewer` caught register contradictions the same-model panels missed. Dissent recorded here and in DECISIONS.)*
- **The two senses of "independent" — the register ruling (recorded in DECISIONS):**
  - **Forbidden:** model-family independence claims — "independent judge/model/verification," "real independence," "heterogeneous = independent." The honest claim is ***"a different model family (same vendor) — a reduction of shared-blind-spot risk; errors remain correlated through shared vendor data and objectives."***
  - **Preserved:** the established **structural** independence of the clean-context input contract ("independence is structural," "independently re-checks") — that's about *context isolation*, is accurate, and stays.
- **The conditional register sweep** — the re-pin falsifies existing "same model class" copy; reword to the conditional register (*"by default a different model family than the builder; same-family runs are tagged"*) at the named sites: `finding-verifier.md:12` · `honesty-reviewer.md:10` · `README.md:22` · `skills/build/SKILL.md:277` · `skills/audit/SKILL.md:455` · `docs/PRODUCT.md:169`.
- **The refusal reword** (both touch-points in `skills/build/SKILL.md` — the verbatim block ~:57 **and** the Guardrails mirror ~:357 — plus README/PRODUCT mirrors): *"Running unwatched still needs deterministic trust-gates (Roadmap #5). The cross-model judge is now **wired** (same-model runs are tagged as such), but it's a reduction of shared-blind-spot risk, not a mechanical guarantee — so unwatched runs stay gated on #5."*
- **Directed ROADMAP rewords:** #4 → DONE (drop "real independence"/"independent model" from the row); **#5's row reworded in-plan** (not "check it reads right"): *"#5 is the remaining mechanical piece; with the cross-model judge (#4 — a shared-blind-spot risk reduction, not independence) it is what earns autopilot — tests mechanically gating every slice."*
- **`docs/PRODUCT.md` mirrors** (lines ~59/121/161 "the not-yet-built cross-model judge" + :169 register) updated; **`docs/PLAYBOOK.md:46` fixed in passing** (it still carries the superseded Tier-1-only verification scope + a banned "proof attached" verb — one line, in-scope under the register sweep).
- `honesty-reviewer`'s embedded bar gains one line: **"cross-model ≠ independent."**

**Non-goals**
- No autopilot flip (#5 still missing). · No relative judge≠builder machinery (user fork; the self-report rule covers the honesty ground). · No different-vendor judge (not wireable; limitation stated). · No finder re-pins. · No frontmatter-fable (spike-refuted). · No pin-drift gate yet (ROADMAP only if drift recurs — lesson→gate discipline, not speculative).

## Affected files
- `.claude/agents/finding-verifier.md` · `architect-reviewer.md` · `honesty-reviewer.md` · `plan-reviewer.md` — the `RUNNING AS:` output-header rule + the intended-cross-model line + the conditional-register reword (+ the honesty-bar line in honesty-reviewer). **Frontmatter unchanged (`model: opus`).**
- `docs/WORKFLOW.md` — the judge-model bullet at the panel/Verify honesty lines: spawn the four with the fable override · the self-report comparison · the verbatim tag · the on-error respawn+tag.
- `skills/audit/SKILL.md` — step 7 spawn instruction + the run-report tag line + the :455 register reword.
- `skills/build/SKILL.md` — steps 3/6 spawn instructions + both refusal touch-points + the :277 register reword.
- `README.md` — the trust-paragraph sentence (the honest register) + the :22 reword + the refusal mirror.
- `docs/PRODUCT.md` (~:59/:121/:161/:169) · `docs/PLAYBOOK.md` (:46, in passing).
- `docs/ROADMAP.md` — #4 DONE (reworded) + the directed #5 reword.
- `docs/ARCHITECTURE_TREE.md` — the four agent one-liners.
- `docs/DECISIONS.md` — the spawn-site pin (spike evidence: frontmatter doesn't resolve) · the self-report tag rule · the two-senses register ruling · the four-role scope incl. the yagni dissent on plan-reviewer · the honest register.
- `.claude-plugin/plugin.json` + `marketplace.json` → **`0.1.11`** (gate-enforced).

## Risks & mitigations
- **Self-report reliability** → both test agents self-identified accurately; the comparison is model-upheld and stated as such; a wrong self-report degrades to the pre-#4 status quo (same-model review), never to a false cross-model claim *stronger* than today's.
- **Cost/latency** (fable judges per surfaced finding) → accepted consciously; verdicts are the highest-leverage tokens.
- **Register sweep misses a mirror** → the **broad acceptance grep**: `independent`/`independence` (about the judge) · `same model class` · `same kind of model` · `cross-model` across all live docs — incl. ROADMAP #4's "real independence" (archives + DECISIONS history excluded).
- **Stale refusal mirror** → both build-SKILL touch-points named; grep backstop.

## Test strategy
**Validated by** (gates verify what gates can; the rest is reviewer judgment): (1) run-gates green (pytest · tree · version-sync at `0.1.11`); (2) a **post-implementation wiring check** — spawn each of the four judges per the new spawn-site instruction; each must open `RUNNING AS:` with a fable identification (in this environment); (3) the **broad register grep** (above) — zero violations in live docs; (4) Stage-7 panel — judges running on the very wiring the slice lands.

## Decomposition (slices)
- [ ] **Slice 1 (only):** everything above. **Lands complete** because the four judges are cross-model at every spawn site (or honestly tagged), every claim is register-correct (the two-senses ruling applied), and gates are green. *(Line-scale edits across ~14 files; one session.)*

---

## Review *(Stage-3 — the panel ran CROSS-MODEL: plan-reviewer + honesty-reviewer on fable, yagni on opus)*

**Verdict: PASS** (all required changes folded in).

- **`plan-reviewer` (fable) — CHANGES REQUIRED → addressed.** *(blocking)* tag-trigger detection unspecified → the **`RUNNING AS:` self-report rule** + on-error respawn+tag ✓ · the **"same model class" body-copy contradiction** → the conditional-register sweep at the six named sites + the broadened grep ✓ · the **two senses of "independent"** → the register ruling drawn in-plan + DECISIONS ✓. *(should-fix)* PRODUCT.md mirrors added ✓ · fallback surface widened to all three spawn-site docs — then **mooted by the spike** (one mechanism; no fallback prose) ✓ · PLAYBOOK:46 fixed in passing ✓. *(nits)* the Guardrails refusal mirror named ✓ · the two-senses ruling → DECISIONS; the pin-drift gate deferred (YAGNI) ✓.
- **`yagni-sentinel` — OVER-BUILT → 2 cuts adopted, 1 declined with cause.** The **dual-path wiring carried in-slice** → cut: resolved by the pre-slice spike (frontmatter refuted; one mechanism wired) ✓. The **second tag trigger as separate machinery** → mooted: the self-report rule is ONE mechanism covering every same-model path (no per-trigger code) ✓. The **plan-reviewer pin cut** → **declined** (user decision + live counter-evidence: build mode's orchestrator drafts *and* convenes plan review — same-class-grading-own-artifact is real; and the fable plan-reviewer's catches this session are the empirical case). Dissent recorded.
- **`honesty-reviewer` (fable) — OVERCLAIMS → all reworded.** "verified" → *checked; evidence of capability, not proof* ✓ · "covers both gaps" → grounded in the detectable self-report rule ✓ · the **#5 row reword directed in-plan** ✓ · "can't drift" → *to resist drift* ✓ · refusal "now exists" → *"is now wired (same-model runs are tagged as such)"* ✓ · the acceptance grep broadened to catch ROADMAP #4's "real independence" ✓.

**Harness impact:** no new agent/module/gate; 4 agent-prose edits + 3 spawn-site docs + the copy surface; DECISIONS records the spike, the ruling, and the dissent; `0.1.11`.

---

## Spec

### Slice 1 — cross-model judges at every verify gate

**In plain English (the approval triad):**
- **What this builds:** the four reviewers whose verdicts *gate* work — the finding re-checker, the final work-reviewer, the over-claim checker, and the plan critic — now run on a **different model family than the one that builds** (Fable instead of Opus), so a blind spot shared by the builder is less likely to also blind the judge. Every judge announces which model it actually ran as, and any run where judge and builder turn out to be the same family is **plainly tagged as such** — never silently passed off as cross-model.
- **What "done" means for you:** reviews keep working exactly as today, but the verdicts that matter come from a different model family — and the docs tell the truth about what that buys: *fewer shared blind spots* (same vendor, so not full independence). The build command's "autopilot" refusal updates honestly: one of its two missing trust mechanisms now exists; the other (#5, the mechanical gates) is still required.
- **What you're accepting:** the judge is a different model *family*, not a different *vendor* — errors can still correlate through shared training; the copy says so. The same-family tag is upheld by the orchestrator reading the judge's self-report (a discipline, not a mechanical gate). Fable judges may cost more per review — verdicts are where those tokens buy the most.

**Files & changes / acceptance:** as *Affected files* + *Test strategy* above. Key acceptance: the four spawn sites instruct the fable override; each judge's output opens `RUNNING AS:`; the verbatim tag text in WORKFLOW + the audit run-report; the conditional register at the six named sites; both refusal touch-points reworded; ROADMAP #4 DONE + the directed #5 reword; the broad grep clean; `0.1.11` both manifests.
