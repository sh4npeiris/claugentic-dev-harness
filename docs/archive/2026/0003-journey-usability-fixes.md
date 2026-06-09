# 0003 — Journey / usability fixes (the "go-button" + the live-colleague unblock)

- **Status:** **COMPLETE** — Slices 1–3 landed + verified (Stage-7 fan-outs). Archiving on this land.
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
- [x] **Slice 1 — doc-only "go-button" + on-ramp (cheapest, unblocks colleagues now).** _(landed `949c3b4`)_
  - The **"how to start anything"** sentence → `PLAYBOOK.md` + `README.md` + a plain "now do X" line at the end of `audit`'s backlog. *("To start anything — a backlog item or a brand-new project — just tell the agent in plain English what you want ('Let's do Tier-1 item 1' / 'I want to build X'); it asks you questions, then writes a plan + spec for you to approve before any code.")*
  - **Backlog "How to read this" legend** (2 lines inside the audit backlog fence): one phrase per tag; what "checked against the code" vs "could not confirm independently" means.
  - **Beginner on-ramp** (README): "type these in the Claude Code chat input"; a post-install success check ("type `/claugentic` and you should see `:init` and `:audit`"); exact Windows cache path `%USERPROFILE%\.claude\plugin-catalog-cache.json` + "this file is just a cache — deleting it is safe."
  - **Promote "fresh chat after init"** from a Tip to a numbered Quickstart step + a PLAYBOOK line: "if the agent starts writing code without asking you product questions first, say 'use the workflow' — it should pause and ask."
  - **"How to approve a spec" rubric** (PLAYBOOK): the 4–5 plain questions (Does this match what I asked? Anything I care about missing? Are the risks ones I'm OK with? What does it NOT do?) + "if any answer is no, say 'this is missing X, please revise'" + "the technical detail below the plain-English block is for the agent/reviewer — you're not expected to read it."
  - **`init` closing line** (SKILL step 9): a plain-English headline ("Done — I added a code map, a quality checklist, and a safety check; I did **not** change your code") + a generic next-step pointer.
- [x] **Slice 2 — skill-flow (init/audit).** _(verified PASS by 3 reviewers; landed `4c1e67b`)_ Branch `init`'s closing report on **repo-state** (has source → "run `:audit`" · empty → "just describe your first feature; skip audit until there's code") + gate Quickstart the same way; **empty-repo guard** in `audit` Phase 1 (no app source → "Nothing to audit yet — describe your first feature"); `audit` Phase 2 **progress beats** + "this can take several minutes" + "empty Tier-1+2 is a SUCCESS" + reassuring `PARTIAL`; **land-step close-out** loop sentence ("This one's done. Next: pick another item the same way, or re-run `:audit`; you're done when Tier 1+2 come back empty"); narrate the **refactor→test-baseline pause** + the **Discuss product-questions** when they fire.
- [x] **Slice 3 — code + tests: `INCLUDE_GLOBS` self-correction (LEAN).** _(verified by 4 critics — yagni PASS, bug-hunter could not break it; 4 hardening tests added at Verify; landed)_ The gate **mechanically flags** when it's watching *nothing* while real source exists (the zero-coverage case); the agent then re-detects layout and resets `INCLUDE_GLOBS` (model-upheld, on its next run), surfacing that **handled** drift case as "updating your codebase map" rather than a cryptic config message — a genuine crash still fails loud by design. + characterization tests. (The one non-doc fix — its failure mode, silent false safety, directly violates the honesty pitch. Registry cut → stack-agnostic check per Stage-3 review; partial-coverage → ROADMAP.)

## Risks / Test strategy
Doc/skill changes are additive + plain-English; must not over-claim (the verifier is a *reduction* of false confidence; detection is mechanical but the glob *reset* is model-upheld; "empty audit = success" is scoped to the audited dimensions) and must not reintroduce build-history. **Slice 2 regression risk:** new narration must stay *out* of the `harness-audit:*` managed fences (byte-identical-2nd-run idempotency). **Slice 3 risk:** the empty-globs `git ls-files --` fail-open (fixed by the guard) + a day-0 false-trip on the copied gate script (fixed by the managed-stamp exclusion); both characterization-tested. Gates stay green (`python -m pytest` = 36 + Slice-3 cases; `python scripts/check_architecture_tree.py` = OK). In-scope lens: `docs-traceability`, `product-ux` (Slice 1–2); `testing` + `reliability-resilience` (Slice 3).

---
## Review _(Stage 3)_

**Slice 1** — implemented & landed (`949c3b4`); the go-button + on-ramp shipped. No formal
plan-review preceded it (pragmatic, doc-only). **Slices 2–3 get a proper Stage-3 adversarial
pass** (plan-reviewer + yagni-sentinel) before the approval gate.

**Slices 2–3 verdict:** **CHANGES REQUIRED → RESOLVED** (3 critics: plan-reviewer +
yagni-sentinel + honesty-auditor; the cross-critic synthesis + resolved decisions are below, and
the revised specs fold them all in).

The approach is sound and the slice split (doc/skill prose vs. the one non-doc code fix) is
correct. Slice 3's empty-globs fail-open is real and well-motivated (verified: `git ls-files --`
with no pathspec lists *every* file), and the guard's two `in_scope_files()` consumers both
stay correct on a `set()` return. But the **central reused signal — "does the repo have app
source?" — is hand-waved across three call sites**, and two test branches that are the whole
reason the slices exist are missing. Fix the items below before approval.

### Required changes

1. **Define the "has app source" predicate as a named, single-source-of-truth signal — it does
   not exist today (Slice 2 + Slice 3, BLOCKER).** The spec leans on it in **three** places —
   init step 9 (Slice 2 file #1, "source-detection already done in steps 1/5"), audit Phase 1
   guard (Slice 2 file #3, "reuse the same detection signal"), and init step 5/self-correct
   (Slice 3 file #2, "reusing audit Phase-1"). But **nothing produces this boolean today.** Init
   **step 1** detects only the *interpreter* + repo root (no source check); init **step 5** /
   audit **Phase 1** detect *ecosystem/manifest/tooling/entry-points* and emit globs + an
   audit-plan — neither emits a defined "app-source present vs. docs/config-only" predicate. The
   citation "steps 1/5" is wrong (step 1 is irrelevant). **Specify the predicate explicitly:**
   what counts as "app source" (manifest present? entry point found? ≥1 file matching the
   detected source globs? — and is this repo's own `scripts/*.py` "app source" or not?), which
   step *owns* its definition, and how the other two consume it. Without this, three implementers
   will invent three different detectors — the exact DRY violation the spec claims to avoid.

2. **Test the empty-globs + real-source-present transition — the scenario the slice exists for
   (Slice 3, BLOCKER).** The test list covers "empty globs + *no* source → OK" but **not** the
   dangerous transition: `INCLUDE_GLOBS == []` (init's "unset" on an empty repo) **after** real
   source has landed. There `EXTS == set()`, so every implied ext is "not in EXTS" → `stack_drift`
   must fire and `evaluate()` must go **blocking** (not silent-green). This is precisely the
   "guessed-then-grew false all-clear" the slice promises to kill; it must be a characterization
   test, asserted as exit 1 / `--hook` exit 2.

3. **Resolve `stack_drift` vs. the empty-globs guard interaction explicitly (Slice 3, MAJOR).**
   `in_scope_files()` short-circuits to `set()` on `INCLUDE_GLOBS == []`, but `stack_drift` uses
   the separate `_all_repo_files()` (no glob filter) and `EXTS` (empty) — so drift *should* still
   fire on the unset state. The spec never states this is intended (it reads as if `[]` is a
   benign no-op everywhere). Make it explicit in file #1's `evaluate()` description: with empty
   globs, presence/staleness are no-ops **but drift is still live**, so an unset repo that grows
   is caught. (This is the mechanism that makes requirement #2 pass — state it, don't leave it
   emergent.)

4. **Tighten two under-specified Slice-2 edit anchors (MAJOR).** (a) **init step 9** — the spec
   says "replace the generic next-step + the deferral parenthetical," but step 9's closing line was
   already authored in Slice 1 (it ends with the `(Keep the next step generic for now …)`
   parenthetical at `skills/init/SKILL.md:226`). Name the exact anchor text to replace so the
   implementer doesn't double-edit Slice 1's headline. (b) **README Quickstart** — step 3 currently
   carries the "finish in passes" reassurance (`README.md:50`); the 3a/3b split must say where that
   reassurance lands (3a only) and must not orphan step 2 ("fresh chat") which both branches share.

5. **State the regression/no-diff guard for the Slice-2 fence edits (MAJOR).** Slice 2 edits
   `audit` Phase 1/2/3 prose, init step 9, and WORKFLOW — but `audit` writes into **managed
   fences** (`harness-audit:overview`/`backlog`) whose byte-identical-on-re-run idempotency is a
   DECISIONS-recorded invariant. The acceptance criteria don't verify that the new "progress
   beats"/"several minutes"/`PARTIAL` framing is **conversational narration, not fence content**
   (volatile beats inside a fence would break the zero-2nd-run-diff guarantee). Add an acceptance
   criterion: "no new volatile/narration content lands inside a managed fence." Slice 2 claims
   "no tests" — that's fine for prose, but this invariant is the one regression a prose edit can
   silently break.

6. **Make the Slice-3 init→gate self-correction loop concretely terminating (MAJOR).** File #2
   says on glob-drift the agent "re-runs step-5 detection and resets `INCLUDE_GLOBS`, then
   reconciles the tree (step-4 loop)." But step 4's reconcile loop already calls the gate, which
   now *also* runs `stack_drift` — so a mis-reset (globs that still miss a stack) re-trips drift on
   the very loop meant to clear it. State the termination condition (drift clears once the reset
   globs cover the detected stacks' exts; if a stack is genuinely unmappable, fall back to
   broaden-and-flag per step 5's existing "conservative globs" rule — do **not** loop forever or
   silence drift). Otherwise an implementer can land a self-correction that live-locks.

### Sizing / completeness check

- **Slice 2 — OK (size), but lands with latent debt until #1 + #4 + #5 are fixed.** Pure
  prose/skill edits across 4 files; comfortably one session. It does **not** land vertically
  complete as written: the audit Phase-1 guard (#3 of its file list) depends on a predicate that
  #1 says is undefined, and #5's fence-invariant check is unstated. Not a split — a spec-precision
  fix. After #1/#4/#5 it's a clean single slice.
- **Slice 3 — OK (size), but #2 + #3 + #6 are completeness gaps, not size gaps.** Code + tests in
  one file + one test file + two skill/doc touches; well within a session and genuinely
  characterization-tested in the established style. The missing transition test (#2) and the
  unstated drift/empty-globs + self-correction-termination semantics (#3, #6) are what stop it
  landing *complete*. No split needed once specified.
- **Split correctness — RIGHT.** Doc/skill prose (Slice 2) vs. the one behavior-bearing gate fix
  (Slice 3) is the correct seam: it isolates the only code/test change and keeps the honesty line
  (mechanical detection vs. model-upheld reset) inspectable in one slice. Keep it.

### YAGNI

`RECOGNIZED_STACKS` is the one place to watch, and the spec already self-adjudicates it (registry
vs. zero-match heuristic) and correctly justifies extension-granularity to catch *partial-coverage*
drift (which a pure zero-match check would miss). The starter set is reasonable and explicitly
just-in-time-extensible. **Accept the registry** — it earns its keep; do not gold-plate it
(no `*.csproj`-style glob-name manifests in v1, as the spec already says).

### Honesty positioning

Clean. Slice 3 consistently frames **detection as mechanical, reset as agent-driven/model-upheld**,
and the user-facing "updating your codebase map" framing avoids over-claiming. No edit blurs the
"only the tree gate is mechanical" line. Keep the ARCHITECTURE_TREE update (file #4) wording to
"presence + staleness + **glob-drift detection**" — drift *detection*, not drift *fix*.

### Harness impact (Stage 9)

- **DECISIONS (required at Land, both slices):** (a) the "has app source" predicate + its single
  owner (resolves #1 durably); (b) `RECOGNIZED_STACKS` drift-detection added to the one mechanical
  gate, with the mechanical-detection / model-upheld-reset split stated.
- **No new STANDARD or agent** is implied. The `refactor`→characterization-first discipline already
  covers Slice 3's test-first posture; the existing lenses (`testing`, `reliability-resilience`,
  `docs-traceability`, `product-ux`) are the right scope — no new module needed.
- **WORKFLOW** is itself edited by the slices (Stage-8 close-out, the two narrated pauses, the
  "updating your codebase map" framing) — that's in-scope content, not a harness-meta change.

---

### Synthesis across the three critics (orchestrator) — RESOLVED

Two more critics ran alongside the plan-reviewer:

**yagni-sentinel — over-built (Slice 3).** The *stated* failure (Problem ¶3) is the
**zero-coverage** event: init guessed globs on an empty repo, then code landed and the gate
watches nothing. `RECOGNIZED_STACKS` is built for the **partial-coverage** case (a covered repo
grows a *second* stack) — not the stated need — and the hardcoded list **re-introduces the rot it
claims to kill**: any stack not in it (it omits `.csproj`/.NET) grows un-watched → same false
all-clear, narrower. A list that must track *every adopter stack* is open-ended maintenance debt.
**Cut the registry; keep the empty-globs guard (load-bearing — explicitly NOT to cut); use a lean,
stack-agnostic check.** Partial-coverage → ROADMAP.

**honesty-auditor — 5 rewordings (none fatal).** (1) "never a raw .py error / never a traceback"
over-claims — true only for the *handled drift path*; `main()` already surfaces git failure as a
clean `ERROR:` string and a genuine crash still fails loud *by design*. (2) "**automatically**"
(Decomposition L27 + plain-English) blurs mechanical-detection vs. agent-driven-reset — the gate
*flags* (mechanical), the agent *resets* (model-upheld, next agent run). (3) "empty = success"
must carry the shipped **"on the audited dimensions / covered cells"** scoping (DRY). (4) progress
beats report **completed cells, never an ETA/completion promise** (a `PARTIAL` checkpoint can fire
any round). (5) "can't silently rot" must be **bounded** to what's actually detected.

**Resolved decisions (folded into the revised specs):**
- **R1 — Slice 3 goes LEAN (overrides the plan-reviewer's "accept the registry").** yagni + honesty
  are decisive: the registry self-undermines (incomplete list = same rot) and over-claims coverage
  the harness can't keep. The lean check is **stack-agnostic and always-correct for the stated
  zero-coverage failure**, with no list to maintain — and *more* honest. **Design:** a small, stable
  `SOURCE_EXTS` allow-list ("what a code file looks like" — extensions are stable, unlike tooling);
  **drift fires when `in_scope_files()` is empty (globs unset/`[]` or matching zero files) AND the
  repo has non-harness-managed source files.** Partial-coverage (covered repo grows a 2nd stack)
  → ROADMAP.
- **R2 — the "has app source" predicate is defined once** (BLOCKER #1): the *Application source
  present* definition now lives in the Slice-2 spec, **owned by audit Phase 1**, consumed by init
  step 9, init step 5/self-correct, and the audit Phase-1 guard.
- **R3 — managed-stamp exclusion is reused** (the documented `/update` convention) by BOTH the
  agent predicate (R2) and the script's source detection — so the copied gate script never
  false-trips drift on a day-0 empty adopter repo.
- **R4 — all 6 plan-reviewer required changes + the 5 honesty rewordings are folded in;** the
  missing empty-globs→real-source transition test (#2) is the headline Slice-3 test.

Split (prose Slice 2 / code Slice 3) is **kept** (unanimous). No re-review — spec-precision fixes,
verified at the Stage-7 gate.

---

## Spec — Slice 2 (skill-flow: init / audit / workflow narration)

### In plain English (shown first at the approval gate)
- **What this builds:** the *flow* fixes on top of Slice 1's words. After `init`, the closing
  report (and the README Quickstart) now tell you the right next move **for your repo**: code
  already here → run `:audit`; empty repo → just describe your first feature and skip audit.
  `audit` learns to say "nothing to audit yet" on an empty repo instead of a confusing no-op,
  warns a big audit "can take several minutes," and frames an **empty result as the success it is
  — sound *on the dimensions it audited*** (reusing the wording the audit already ships, not a
  looser new claim). The workflow narrates the two moments a non-engineer would otherwise find
  jarring — when it pauses to write a safety-net test before a refactor, and when it stops to ask
  product questions before any code.
- **What "done" means for you:** every dead-end in the journey now has a plain-English next
  step or reassurance; nobody lands on a no-op audit or a silent pause without an explanation.
- **What you're accepting:** doc/skill prose only — **no behavior-bearing code** in this slice.
  Risk is wording (must not over-claim, must not contradict the honesty pitch) and the managed-fence
  idempotency invariant (new narration must stay *out* of the `harness-audit:*` fences); mitigated
  by the `docs-traceability` + `product-ux` lens review + the fence acceptance check below.

### Shared signal — *Application source present* (the predicate R2 defines once)
**Definition (owned by `audit` Phase 1's ecosystem + entry-point detection; the single source of
truth):** the repo *has application source* **iff** it contains **≥1 non-harness-managed source
file of a detected ecosystem** — i.e. a recognized manifest is present **and/or** ≥1 file matches
the detected source layout — **excluding** harness-managed scaffolding (anything carrying the
`claugentic-dev-harness@` managed stamp — the copied `check_architecture_tree.py` — plus the seeded
`docs/standards/`, `WORKFLOW.md`, `PLAYBOOK.md`, etc.) and the standard exclude-set (deps / build /
generated). A repo of **only** docs + config + harness-scaffolding has **no** application source —
so a freshly-`init`'d empty adopter repo is correctly "no app source." **Consumers:** init step 9
(Slice 2 #1), the audit Phase-1 guard (Slice 2 #3), and init step 5 / self-correct (Slice 3 #2) all
read **this one** definition — none invents its own. (Reuses the existing `init step 5 → audit
Phase 1` DRY arrow; the managed-stamp exclusion is the documented `/update` convention — R3.)

### Files & changes
1. **`skills/init/SKILL.md` — step 9 (Report), repo-state branch.** **Exact anchor:** the closing
   next-step sentence authored in Slice 1 — *"Start a fresh chat, then either run
   `/claugentic-dev-harness:audit` on existing code, or just tell me what you want to build."* **and
   its trailing** *"(Keep the next step generic for now — tailoring it to whether the repo already
   has code is a separate, later change.)"* parenthetical (`skills/init/SKILL.md:224–226`). Replace
   **only those two sentences** (leave the Slice-1 plain-English headline above them untouched) with
   a branch on *Application source present*: **has app source →** "Start a fresh chat, then run
   `/claugentic-dev-harness:audit` — I'll explain your codebase in plain English and write a
   prioritized backlog." · **no app source yet →** "Start a fresh chat, then just tell me what you
   want to build — describe your first feature; no need to run `:audit` until there's code."
2. **`README.md` — Quickstart step 3, repo-state branch.** Split current step 3 into **3a (has
   code → run `:audit`)** — the existing "a large repo may finish in passes … re-run to continue"
   reassurance lands **here, in 3a only** — and **3b (empty repo → skip audit; just tell the agent
   what you want to build)**. **Step 2 ("Start a fresh chat after `init`") stays shared above both**
   (do not orphan or duplicate it). Keep step 1.
3. **`skills/audit/SKILL.md` — Phase 1 empty-repo guard.** Add a guard at the end of Phase 1: if
   *Application source present* is **false** → **stop, do not enter Phase 2**, report (in
   conversation) "Nothing to audit yet — I don't see application code, only docs/config. Describe
   your first feature when ready; re-run `:audit` once there's code." Consumes the shared predicate
   (no second detector).
4. **`skills/audit/SKILL.md` — Phase 2 narration (trimmed per yagni/honesty — point, don't
   duplicate).** Two genuinely-new beats only: **(a)** before the fan-out (step 4) a single line —
   "this can take several minutes on a larger repo; I'm reading the code through several quality
   lenses in parallel"; **(b)** at most **one light "still working" beat** per round reporting
   **cells already completed** ("swept the API routes…") — **never an ETA or completion promise**
   (a `PARTIAL` checkpoint can fire any round). For `PARTIAL` reassurance and "empty Tier-1+2 =
   success," **point to the prose the skill already ships** (step 9's `PARTIAL` framing; the Phase-3
   "Sound on the audited dimensions" terminal signal at SKILL lines ~373–380) — **do not author a
   parallel copy** (single source of truth). The only new framing: ensure the user-facing report
   *surfaces* that existing terminal signal so an empty result never reads as failure.
5. **`docs/WORKFLOW.md` — Stage 8 land close-out.** Add the loop sentence the agent says after a
   backlog item lands: "This one's done. Next: pick another item the same way, or re-run `:audit`
   for a fresh picture — you're finished when Tier 1 and Tier 2 come back empty."
6. **`docs/WORKFLOW.md` — narrate the two pauses as one-line "say this" notes anchored to the
   EXISTING homes (no duplicate rationale).** *Refactor→test-baseline:* a one-line plain-English
   "say this to the user" note **on the existing tag→discipline `refactor` row** (lines ~118–124) —
   "Before I tidy this I need to capture what it currently does as a test, or I can't prove I didn't
   change its behavior — so I'll establish that baseline first." *Discuss:* a one-line note **on the
   existing Stage 1 row** (the plain-English layer at lines ~75/87) — "Before any code I'll ask a few
   questions about who this is for and what 'good' looks like — your answers steer everything
   downstream." Anchor to the existing rows; do **not** add free-standing explanations that restate
   *why* the pause exists (it's already stated there).

### Tests / gates
Prose-only — no tests added. Gates stay green: `python -m pytest` (36) · `python
scripts/check_architecture_tree.py` (OK). No new files → no tree change. DECISIONS gets a dated
line at Land.

### Acceptance criteria
- init step 9 + README Quickstart branch on *Application source present*; init's Slice-1 deferral
  parenthetical is gone and its headline is untouched; README step 2 stays shared, the
  "finish in passes" reassurance sits in 3a.
- audit refuses to no-op on an empty repo (the Phase-1 guard fires); warns "several minutes"; emits
  at most one completed-cells beat per round (no ETA/completion promise); `PARTIAL` + "empty
  Tier-1+2 = success — *on the audited dimensions*" **point to** the existing prose, not a new copy.
- WORKFLOW Stage 8 close-out present; the refactor + Discuss narration are one-line notes on the
  **existing** rows (no duplicated rationale).
- **Managed-fence invariant (regression guard):** no new volatile/narration content lands inside a
  `harness-audit:overview`/`harness-audit:backlog` fence — beats/reassurance are spoken in
  conversation, so a 2nd `audit` run stays byte-identical (the DECISIONS-recorded idempotency).
- No over-claim (nothing implies a not-yet-built gate). **In-scope lenses:** `docs-traceability`,
  `product-ux`.

---

## Spec — Slice 3 (INCLUDE_GLOBS self-correction — the one non-doc fix)

### In plain English (shown first at the approval gate)
- **What this builds:** a safety fix for the one mechanical gate. When `init` runs on an empty
  repo it can only *guess* which files to track; if it guesses and then you build a real app, the
  gate would quietly track nothing and report "all good" while ignoring your whole codebase — a
  **false all-clear** that directly violates the harness's honesty promise. This makes the gate
  **mechanically flag** when it's watching *nothing* while real code exists, so the agent
  **re-detects your layout and resets the tracking** the next time it runs — and presents that one
  handled case as a plain "updating your codebase map" rather than a cryptic config message.
- **What "done" means for you:** the codebase-map gate can't sit *silently green while watching an
  empty set* once a new repo grows into a real one. Start empty, later add real code → the gate
  flags it's watching nothing and the agent fixes the config. *(Honest bound: this catches the
  **zero-coverage** case — the gate watching nothing. A repo whose globs already match some files
  but later grows a **second**, un-globbed stack is a narrower follow-up on the roadmap.)*
- **What you're accepting:** a small, well-tested addition to the deterministic gate script + the
  init/agent behavior that acts on it. **Detection is mechanical** (genuinely enforced — the gate
  *flags*); the **reset** is the agent's doing (model-upheld, on its next run) — stated honestly,
  not "auto-magic," and a genuine crash still fails loud by design (we don't cosmetically swallow
  errors).

### Design (LEAN — resolved R1: registry cut, stack-agnostic zero-coverage check)
The gate gains a **zero-coverage trip-wire**, *not* a per-stack registry. `INCLUDE_GLOBS` stays the
single per-repo knob for presence/staleness. A small, **stable `SOURCE_EXTS` allow-list** ("what a
code file looks like" — extensions are stable, unlike per-stack tooling) lets the gate answer one
stack-agnostic question: **is `in_scope_files()` empty (globs unset `[]` *or* matching zero files)
while the repo nonetheless contains non-harness-managed source files?** If so, the per-repo globs
were set before this code landed and the gate would otherwise sit green over an un-watched codebase
— a **loud, blocking, actionable** problem. No manifest registry to maintain, correct for **every**
stack, and *more* honest (it claims only what it detects). **Scope (honest bound):** fires for the
**zero-coverage** case (the stated failure — Problem ¶3); **partial-coverage** (a repo whose globs
already match files grows a *second* un-globbed stack) → **ROADMAP**, built when a real adopter hits
it. **Empty-globs ↔ drift interaction (R-#3, stated):** with `INCLUDE_GLOBS == []`,
presence/staleness are no-ops **but drift stays LIVE** (it keys off `in_scope_files()` being empty +
`_repo_source_files()`), so an *unset* repo that grows real code is still caught.

### Files & changes
1. **`scripts/check_architecture_tree.py`**
   - **`SOURCE_EXTS: frozenset[str]`** — a small, **stable** allow-list of common source-code
     extensions (`py js jsx mjs cjs ts tsx go rs java kt rb php cs swift c h cpp hpp cc scala vue
     svelte` …). Documented: **drift-detection only** — *not* used for presence/staleness
     (`INCLUDE_GLOBS`/`EXTS` remain the only per-repo knob there); intentionally broad + stable
     (extensions don't drift the way per-stack tooling does — no list to keep in lockstep).
   - **`MANAGED_STAMP = "claugentic-dev-harness@"`** + **`_is_harness_managed(path) -> bool`** —
     true if line 1 carries the managed stamp (the documented `/update` convention — R3). Reused so
     the **copied gate script never false-trips drift on a day-0 empty adopter repo** (in *this*
     repo the gate script is unstamped source, but it's covered by `INCLUDE_GLOBS` so drift
     short-circuits before any stamp read).
   - **`_repo_source_files() -> list[str]`** — tracked + untracked-not-ignored files whose
     extension ∈ `SOURCE_EXTS`, normalized, **minus** `EXCLUDE_SUBSTR` **and** harness-managed
     files (`_is_harness_managed`). The repo-wide view drift needs; fails loud via `_git`. (Stamp
     reads happen *only* in the zero-match state, where the candidate set is tiny — bounded cost.)
   - **`glob_drift(in_scope: set[str]) -> list[str]`** — `if in_scope: return []` (globs watch ≥1
     file → not the zero-coverage rot, and a fast short-circuit that avoids stamp reads in the
     steady state); else return `_repo_source_files()[:8]` (the un-watched source sample). `[]`
     whenever the globs match anything.
   - **`evaluate()`** — compute `files = in_scope_files()` once, pass to `glob_drift(files)`; add
     drift as a **third problem class** (after missing/stale): non-empty → an actionable block —
     *"INCLUDE_GLOBS watches no files but the repo contains source code (e.g. `src/app.ts`) — the
     globs are unset or stale; re-detect the layout and set INCLUDE_GLOBS in
     scripts/check_architecture_tree.py to match."* Clean problem text (the handled path), never a
     traceback.
   - **`in_scope_files()` empty-globs guard** — `if not INCLUDE_GLOBS: return set()` immediately
     (never `git ls-files --` with no pathspec, which lists **every** file — a real fail-open bug).
2. **`skills/init/SKILL.md` — step 5(a) empty-repo + self-correct (terminating).** No-app-source
   case (the shared predicate) → set **`INCLUDE_GLOBS = []`** (safe "unset"; gate no-op, guarded
   above) + report "no source yet — tracking is unset and I'll configure it when you add code."
   **Self-correction:** when the gate later reports the **zero-coverage** drift problem, the agent
   re-runs step-5 detection (reusing audit Phase-1 — DRY) and resets `INCLUDE_GLOBS`, then
   reconciles the tree (step-4 loop). **Termination (R-#6, stated):** drift clears the instant the
   reset globs match **≥1** file (`in_scope_files()` non-empty → `glob_drift` returns `[]`); if the
   stack is genuinely unmappable, fall back to step 5's existing **broaden-and-flag** rule (emit the
   dominant source-extension globs) — those still match ≥1 file, so drift clears. **Never loops
   forever, never silences drift.**
3. **`docs/WORKFLOW.md` (+ a one-line init step-9 note) — "updating your codebase map" framing
   (scoped, honest).** Instruct the agent to surface the **handled zero-coverage drift problem** to
   the user as a plain "I'm updating your codebase map to match your new code." **Scope the claim:**
   this covers the drift path — a *genuine* gate crash still fails loud (CLAUDE.md: never swallow
   errors); don't promise "no error ever," only that the **handled** drift case reads in plain
   English.
4. **`docs/ARCHITECTURE_TREE.md`** — update the `check_architecture_tree.py` line to note **drift
   *detection*** alongside presence + staleness (detection, not auto-fix). No new files.

### Tests to add (`tests/test_check_architecture_tree.py`)
Hermetic, in the established style: real on-disk files in `tmp_path` (so `_is_harness_managed`'s
line-1 read works), an **args-aware `_git` mock** (glob-scoped calls — args containing a `:(glob)`
pathspec — return the in-scope list; un-scoped `ls-files` calls return the repo-wide list),
monkeypatch `INCLUDE_GLOBS`/`EXTS`/`SOURCE_EXTS`.
- **Headline (the transition the slice exists for):** `INCLUDE_GLOBS == []` (so `in_scope` empty)
  **after** real source has landed (`src/app.ts` on disk) → `glob_drift` non-empty → `evaluate()`
  **blocking**; `main([])` exit 1 + actionable message, `main(["--hook"])` exit 2 / stderr.
- Steady state, **this repo's shape:** `INCLUDE_GLOBS` covers `scripts/**/*.py`, `in_scope`
  non-empty → `glob_drift == []` (no drift, fast short-circuit, no stamp reads).
- **Day-0 false-positive guard (R3):** `INCLUDE_GLOBS == []`, the only source file is a
  **stamped** `scripts/check_architecture_tree.py` → `_repo_source_files` excludes it → `glob_drift
  == []` (a freshly-`init`'d empty adopter repo does **not** false-trip).
- Empty-globs guard: `INCLUDE_GLOBS == []` → `in_scope_files() == set()` and **`_git` is not called
  with an empty pathspec** (does not list every file).
- Empty repo, truly no source: `INCLUDE_GLOBS == []`, no `SOURCE_EXTS` files → `evaluate()` OK (no
  false problem).
- `SOURCE_EXTS` discrimination: a `.md`/`.json`-only repo with `INCLUDE_GLOBS == []` → no drift
  (docs/config are not source).
- Self-correction termination (unit-level): once globs are reset to match the landed source,
  `glob_drift(non_empty_in_scope) == []` (drift clears).

### Acceptance criteria
- The gate **mechanically flags** the zero-coverage case (watching nothing while source exists) →
  clear, actionable, blocking problem (the handled path, no traceback); steady-state repos (incl.
  **this one**) stay green and a day-0 empty adopter repo does not false-trip.
- `INCLUDE_GLOBS == []` is a safe, well-defined unset state (no fail-open `git ls-files --`).
- init sets `[]` on a no-app-source repo; on first real source the agent re-detects/resets with a
  **terminating** loop and frames it as "updating your codebase map"; the framing is scoped to the
  handled drift path (a genuine crash still fails loud).
- New characterization tests pass — incl. the **empty-globs→real-source transition** (the headline)
  + the **day-0 stamped-gate-script** guard; **suite ≥ 36 + new cases**;
  `check_architecture_tree.py` green.
- Honesty: detection framed as mechanical (*flags*), reset as agent-driven (model-upheld); coverage
  claim **bounded** to zero-coverage; no over-claim. **In-scope lenses:** `testing`,
  `reliability-resilience` (+ a `docs-traceability` touch).
