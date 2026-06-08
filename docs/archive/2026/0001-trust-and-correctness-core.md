# 0001 — Trust & Correctness Core (make the harness shareable)

- **Status:** Implemented + verified (all 3 slices PASS; final docs-traceability lens CLEAN) · awaiting user sign-off to land/commit (Stage 8, then archive)
- **Roadmap item:** `docs/ROADMAP.md` → Next (this plan also *refreshes* the roadmap: "Real-app dogfood" is now done; the verify-findings pass below is new and not yet listed).
- **References:** `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · `docs/WORKFLOW.md` · `skills/audit/SKILL.md` · `skills/init/SKILL.md` · `scripts/check_architecture_tree.py` · `.claude/agents/lens-reviewer.md` · `.claude/agents/architect-reviewer.md`

## Problem

The harness is structurally complete but three gaps stand between "works for its author" and **"a colleague can trust it"** (goal: share with non-engineer/mixed colleagues via the public marketplace):

1. **The audit asserts findings; it never independently proves them.** `skills/audit/SKILL.md` Phase 2 step 5 has a *citation-guard* (re-confirms a `file:line` exists, [SKILL.md:222](skills/audit/SKILL.md)) and *confidence labels* — but **nothing reads the cited code and tries to refute the claim.** The harness's whole thesis is "author → adversarially verify; trust the oracle, not the model" — applied at the Verify gate for *implementation* (`architect-reviewer`), but **not to its own audit output.** A backlog the user must hand-verify is a suggestion list, not a trustworthy one. (Confirmed live: the an adopter run presented a cross-tenant write + an SSRF as "deterministic" — checkable in principle, but never checked.)

2. **A real correctness bug in `init`'s generated gate.** `scripts/check_architecture_tree.py` uses a per-repo `STALE_PATTERN` regex that `init` hand-authors ([init/SKILL.md:138](skills/init/SKILL.md)). For a multi-extension repo, naïve alternation (`(?:ts|tsx)`) matches `ts` before `tsx`, truncating `foo.tsx`→`foo.ts`, producing **false "stale" positives** (this is the exact bug the an adopter audit hit — 98 false positives). It will bite **every multi-language repo a colleague inits.** The `INCLUDE_GLOBS`↔`STALE_PATTERN` "keep-in-sync" coupling is also a documented footgun ([check_architecture_tree.py:40-51](scripts/check_architecture_tree.py); `DECISIONS.md` 2026-06-05 "Tree-check is language-incidental").

3. **The one deterministic component has zero tests.** `check_architecture_tree.py` is the linchpin gate the whole harness trusts to be mechanical, and it just demonstrated it can carry a latent bug while still reporting green. No safety net = the gate's "green" can't itself be trusted. (This is Tier-1 #1 of the harness's *own* audit.)

## Goals / Non-goals

**Goals**
- The audit **independently verifies its high-stakes findings** (Tier-1 + security) before presenting them, attaches the proof, drops false positives, and flags what it could not confirm — in plain English a non-engineer can read.
- The architecture-tree gate is **correct on multi-extension repos** and **has a characterization-test safety net.**
- Docs tell the truth about the new behavior; a colleague can **install from the public marketplace without hitting the stale-cache trap.**

**Non-goals (guard against creep)**
- **No deterministic trust-gates** (the `PreToolUse` characterization hook, secret-scan) — that's the next, larger phase. *Out of scope.*
- **No `thorough` dial level, no "verify every finding", no per-dial verify-scaling.** This slice ships **one** rule — verify Tier-1 + security on every dial. Verify-more-on-`standard` and verify-all-on-`thorough` (+ the second adversarial sweep) remain deferred to ROADMAP.
- **No `/update` or `/explain` skills.** Colleagues `init` fresh on this version.
- **No CI wiring** for the new tests (running `python -m pytest` + documenting it is enough; CI → ROADMAP).
- **Not** re-auditing an adopter or any external repo.

## Approach

Three independent slices. **Slices 1 & 2 are file-disjoint and run in parallel** (separate worktrees); **Slice 3 (docs) runs last** because it describes 1 & 2.

### Slice 1 — Harden + test the architecture-tree gate

**Chosen design — eliminate the per-repo `STALE_PATTERN` knob (single source of truth).** Today staleness depends on a hand-authored regex kept in sync with `INCLUDE_GLOBS`. Instead, **derive the valid extensions from `INCLUDE_GLOBS`** (the *only* per-repo knob) and check tree-referenced paths by **full-extension equality after the last dot** — which structurally cannot have the `ts`-before-`tsx` bug (we compare whole extensions, never alternate-substrings):
- Extract candidate path tokens generically (backtick-quoted, path-shaped) — a *repo-agnostic* regex, no per-repo tuning. **Normalize `\`→`/` on the extracted tokens** before the existence check (the tree is markdown text; the FS may be Windows) — mirroring the normalization `in_scope_files()` already does on the file-list side ([check_architecture_tree.py:64](scripts/check_architecture_tree.py)), so *both sides* are normalized.
- Keep a token as a reference iff its **last-dot extension ∈ `EXTS`** (derived from `INCLUDE_GLOBS`, e.g. `:(glob)src/**/*.tsx` → `tsx`). **No path-prefix filter** — extension-equality alone kills the bug class (yagni-sentinel #5); a prefix check would re-introduce a softer version of the `INCLUDE_GLOBS`-coupling we're deleting *and* add glob-prefix-extraction edge cases (`**`/root-glob) for no real-world gain.
- `stale` = references (matching `EXTS`) whose file doesn't exist on disk.

This removes a whole bug class, kills the sync-footgun, and leaves **one** per-repo knob (KISS + DRY). *Alternative rejected:* "just fix `init`'s guidance to order alternations longest-first" — cheaper but model-upheld (the agent must get the regex right every time) and leaves the sync-footgun; contradicts the harness's deterministic-over-model ethos.

**`init` must emit extension globs (closing the gate's contract — plan-reviewer #6).** `EXTS` is derivable only if `INCLUDE_GLOBS` entries end in `*.ext`. Today init may set "a conservative broad source glob" for an unmappable ecosystem ([init/SKILL.md:140-144](skills/init/SKILL.md)) — possibly a bare directory glob. Slice 1 constrains init to **always emit extension globs** (for an unmappable layout: the dominant source *extensions* under the main dir, not a dir glob), and the script **skips any glob with no derivable extension** gracefully (those files stay presence-checked, just not staleness-checked — documented in the config comment).

**Tests (new `tests/`, pytest):** characterization-lock the gate's behavior — `evaluate()` presence + staleness (incl. an explicit `foo.ts`/`foo.tsx` regression case proving the old bug stays dead), mode dispatch + exit codes (`--hook`→2, default→1, OK→0), `--hook-write` stdin parsing (well-formed, malformed→None, overwrite/out-of-scope/already-indexed→0, new-undocumented→2), path normalization (Windows backslashes). `_git` is mocked so tests are hermetic (no real repo state).

**`init` update:** step 5 now sets **only** `INCLUDE_GLOBS` (always extension globs — see above); drop the `STALE_PATTERN` authoring instruction. *(Not adding `tests/**/*.py` to scope — that's an orthogonal "should tests be tree-indexed?" policy decision, deferred to ROADMAP per yagni-sentinel #2.)*

### Slice 2 — The verify-findings pass (the trust upgrade)

**New step in `skills/audit/SKILL.md` Phase 2, after step 7 (YAGNI prune), before Phase 3 (author backlog)** — verify the keepers, not findings we already cut.

**New agent `.claude/agents/finding-verifier.md`** (single responsibility, SOLID). **Input contract — this is how independence is *enforced*, not hoped (plan-reviewer agent-note):** the verifier receives **only** `{claim (plain + technical), file:line, source module, confidence label, exclude-set}` and a **refute-first posture** — **never the finder's transcript or rationale**, and the lens that produced a finding **never** verifies its own finding. With a clean-context subagent given only the claim+location, independence is structural. It reads the cited code + surrounding context and **tries to prove the finding wrong** (look for the org-filter / `LIMIT` / timeout / allowlist the finding says is missing; **default to `Unconfirmed` if it genuinely can't tell** — never guess). READ-ONLY. **`model: opus` — justified by *capability parity*:** the finders (`lens-reviewer`) run on opus; a verifier on a weaker model "refuting" an opus finding would let the weaker model overrule the stronger and **drop a real (possibly security) finding** — backwards for a trust feature. This is the "Opus when intelligence is required" exception to the global Sonnet-default; cost is bounded because verify scope is now **Tier-1 + security only** (few findings — see below), so the count is small without a dial-scaled throttle. *Alternative rejected:* a third `lens-reviewer` mode — it *finds gaps through a lens*; verifying *refutes a specific claim against code* (different responsibility, input shape, posture) → its own file, mirroring `yagni-sentinel` as a separate counterweight.

**One verification rule (no dial-scaling for v1):** **verify every Tier-1 (correctness/security/data-loss) and every security-module finding, on *every* dial.** The trust floor is dial-independent — never present an unverified critical/security claim. *(Deferred to ROADMAP, beside the existing deferred `thorough` sweep: `standard` additionally verifying `deterministic`-labeled findings, and `thorough` verifying **all** findings. Shipping those now is scope-scaling for an unmeasured cost — yagni-sentinel #1. Cutting the dial-table also removes the label collision plan-reviewer #1 flagged: we no longer overload the `deterministic` *confidence* label as a verify-*selector*.)*

**Verdicts — three outcomes, surfaced in plain English (no badge/legend system — yagni-sentinel #5):**
- **Refuted** → **dropped** from the backlog; one line in the run report (`dropped M false positives: …`). The actual trust win.
- **Verified** → kept; the **proof snippet** (real code) attached; tagged inline **"(verified against the code)"**.
- **Unconfirmed** → kept; tagged inline **"(could not confirm independently — model's assertion)"**.

**One status axis per item (resolves plan-reviewer #1).** Confidence (`deterministic`/`judgment` = *could a gate prove this*) and verification (*was it checked + outcome*) are different axes — but to avoid two parallel labels a non-engineer must reconcile: a **verified-scope item shows its verification tag** (verification supersedes the confidence label for display); an **out-of-scope item keeps its confidence label** exactly as today. No item shows both; no legend needed (the inline phrases are self-explanatory).

**Trust floor + the budget model (resolves plan-reviewer #3, #4, #5).** Verification is **part of the run budget**, not a separate uncapped burst: `max-cells-per-run` is set leaving headroom to verify the criticals found (criticals are few). The floor is **not** "always verified" (budget can't guarantee that) — it is **"never presented as verified unless it was."** Representable states for a Tier-1/security finding: `verified` · `unconfirmed` · **`deferred`** (couldn't verify within this run's budget → written with an explicit **"⚠ not yet verified — re-run to confirm"** flag, its verification listed in `pending`). A critical is **never** silently presented as fact.
- **Persistence / resume:** a verdict persists **in the backlog fence alongside its finding**; on a **resume** run a finding already carrying a verdict is **not re-verified** (and `done` cells aren't re-swept, so refuted findings don't reappear) — no O(rounds) re-verify cost.
- **Fresh re-run:** the backlog regenerates (snapshot, not accumulation), so a fresh audit legitimately re-finds and re-refutes — accepted cost. Refuted findings are intentionally **not** persisted durably (that would violate regenerate-don't-accumulate); their only trace is the run report.

**Register the agent** in `.claude-plugin/plugin.json` `agents[]`.

### Slice 3 — Docs & distribution honesty

- **`docs/ROADMAP.md`** — remove the done "Real-app dogfood"; reframe so the verify pass is *shipped* (not a roadmap item); keep trust-gates / `thorough` / `/update` / `/explain` in their tiers.
- **`README.md`** — upgrade the honesty section: the audit no longer presents purely "model-asserted" criticals — it **independently verifies Tier-1 + security findings and shows the proof.** Refresh status.
- **Install-troubleshooting** — a short, non-engineer, step-by-step note (in `README.md`) for the stale `plugin-catalog-cache.json` trap (symptom → clear cache → restart).
- **`docs/PLAYBOOK.md`** — one plain-English line that the audit now proves its critical findings.
- **`docs/DECISIONS.md`** — dated entries for: verify pass + `finding-verifier`; the `STALE_PATTERN`→single-knob redesign; the gate test baseline; dogfood-complete.

## Affected files

- `scripts/check_architecture_tree.py` — replace `STALE_PATTERN` with `EXTS`-derived staleness (no prefix filter; normalize both sides; skip extension-less globs); update the PER-REPO CONFIG comment. *(Slice 1)*
- `tests/test_check_architecture_tree.py` *(new)* — characterization tests (listed in the tree as a map entry; **not** added to `INCLUDE_GLOBS`). *(Slice 1)*
- `pyproject.toml` *(new, minimal)* — make `python -m pytest` runnable (out of `INCLUDE_GLOBS`; tree-listed). *(Slice 1)*
- `skills/init/SKILL.md` — step 5 sets one knob (extension globs only); drop `STALE_PATTERN` authoring. *(Slice 1)*
- `skills/audit/SKILL.md` — insert verify step (Phase 2); inline verdict tags + one-status-axis + run-report (Phase 3). *(Slice 2)*
- `.claude/agents/finding-verifier.md` *(new)* — the verifier role (independence input-contract). *(Slice 2)*
- `.claude-plugin/plugin.json` — register `finding-verifier`. *(Slice 2)*
- `docs/WORKFLOW.md` — add `finding-verifier` to the role library ([WORKFLOW.md:57-65](docs/WORKFLOW.md)). *(Slice 2)*
- `docs/ROADMAP.md` — **delete** the delivered "Test baseline for check_architecture_tree.py" item; mark "Real-app dogfood" done; add the deferred per-dial verify-scaling. *(Slice 3)*
- `README.md` — honesty upgrade + install-troubleshooting note; **bump "6 specialist agents" → 7**. *(Slice 3)*
- `docs/PLAYBOOK.md`, `docs/DECISIONS.md` — plain-English line + dated entries (verifier = false-confidence reduction, *not* a deterministic trust-gate). *(Slice 3)*
- `docs/ARCHITECTURE_TREE.md` — add `finding-verifier.md`, `tests/…`, `pyproject.toml`; update the script's line; **bump "the 6 specialist agents" → 7** ([ARCHITECTURE_TREE.md:59](docs/ARCHITECTURE_TREE.md)). *(each slice updates inline for its own files; agents vs scripts/tests sections kept distinct so parallel worktrees merge cleanly)*

## Risks & mitigations

- **Verify pass inflates audit cost/latency.** → Scope it to the critical subset by dial (table above); fan the verifiers out in parallel; `thorough`'s verify-everything stays deferred.
- **The verifier is the same model class → can it really refute itself?** → It's a *different instance with a clean context* told only the claim+location and an explicit *refute-first / default-to-Unconfirmed* posture (the proven `yagni-sentinel`/refuter pattern). It's an honest **reduction** of false confidence, not a deterministic oracle — the docs must not over-claim it (it complements, never replaces, the future deterministic trust-gates).
- **Changing the gate's staleness logic could regress detection** → that's exactly what the Slice-1 characterization tests lock down (incl. the `.ts/.tsx` case); the gate must stay green on *this* repo (`python scripts/check_architecture_tree.py`).
- **`EXTS`-derived matching could miss extension-less in-scope refs** → `INCLUDE_GLOBS` are extension globs by construction; document the assumption in the config comment; non-matching tokens are simply not treated as in-scope references (same as today).
- **Backlog readability (non-engineer)** → **no badge/legend system**; one inline plain-English tag per verified-scope item ("(verified against the code)" / "(could not confirm independently)"); Refuted items vanish from the list (one run-report line). **One status axis per item** (verification supersedes confidence where present).

## Test strategy

- **Slice 1 (tests-first ordering — plan-reviewer sizing note):** *first* write the suite locking **current** behavior green, *then* swap `STALE_PATTERN`→`EXTS` and prove the suite still green **and** the `.ts/.tsx` case flips false-positive→clean. Cases: presence; staleness (`.ts/.tsx` regression; a deep/monorepo path `packages/app/src/x.tsx`; a token whose extension ∉ `EXTS` is ignored; an extension-less `INCLUDE_GLOBS` entry skipped gracefully); `evaluate()` Windows-path normalization (tree cites `a/b.py`, FS has `\`); mode dispatch + exit codes (`--hook`→2, default→1, OK→0); `--hook-write` stdin (well-formed / malformed→None / overwrite / out-of-scope / already-indexed→0 / new-undocumented→2). All hermetic (mocked `_git`). Gate stays green on this repo; `python -m pytest tests/` documented as a gate in `CLAUDE.md`.
- **Slice 2:** behavioral (it's prompt/skill engineering, no runtime code). Acceptance = a dry-run trace through the audit on a seeded finding shows: an independent `finding-verifier` invoked (not the finder), a verdict produced, Refuted dropped + reported, Verified carries proof, Unconfirmed flagged. The `architect-reviewer` Verify gate checks the SKILL.md + agent contract for SOLID/clarity/no-overclaim.
- **Slice 3:** docs review — claims match shipped behavior (no overclaim of verification); install note is correct + non-engineer-readable; `check_architecture_tree.py` green after tree updates.
- **All slices:** Definition of Done per `docs/WORKFLOW.md` — in-scope `docs/standards/` lenses pass `architect-reviewer`; `check-tree` green; `/simplify` + `/code-review` on Slice 1's Python.

## Decomposition (slices)

- [x] **Slice 1 — Harden + test the gate.** ✅ landed + verified (architect-reviewer PASS after 2 doc gaps closed; 28 tests green, gate green). `check_architecture_tree.py` (single-knob staleness) + `tests/` + `init` step 5 + tree/DECISIONS. *Lands complete:* the gate is correct, tested, one knob; self-contained (no dependency on Slice 2). In-scope lenses: `testing`, `maintainability-structure`, `reliability-resilience`.
- [x] **Slice 2 — Verify-findings pass.** ✅ landed + verified (architect-reviewer PASS on all hard points; tree-currency gap closed at integration). `finding-verifier.md` + `audit/SKILL.md` (verify step + backlog format + report) + `plugin.json` + tree/DECISIONS/PLAYBOOK line. *Lands complete:* the audit verifies its criticals end-to-end. In-scope lenses: `maintainability-structure` (SOLID agent), `docs-traceability` (backlog honesty), `testing` (verification-as-trust discipline).
- [x] **Slice 3 — Docs & distribution honesty.** ✅ ROADMAP/DECISIONS/README/PLAYBOOK/tree updated; install-troubleshooting note added; version → 0.1.2. ROADMAP + README + install note + PLAYBOOK + DECISIONS. *Lands complete:* docs match reality; colleagues can install. Runs after 1 & 2. In-scope lens: `docs-traceability`.

---

## Review  _(plan-reviewer, Stage 3)_

- **Verdict:** **CHANGES REQUIRED** — the direction is sound and the slicing is mostly right, but Slice 2 leaves real holes (the confidence-vs-verification model collides with the *existing* `deterministic`/`judgment` label, the "trust floor on PARTIAL" double-spends a budget the plan never enlarges, and the verifier's `model: opus` cost is uncapped per-finding) and a few completeness items are missing. Fix the numbered items below, then it passes.

### Required changes

1. **Resolve the label collision between `Verification` and the existing `deterministic`/`judgment` confidence label (Slice 2).** The audit already carries a per-finding confidence label end-to-end ([audit/SKILL.md:218-220, 332-335](skills/audit/SKILL.md); [lens-reviewer.md:35-36](.claude/agents/lens-reviewer.md)) where `deterministic` means *"a gate could prove this — name the gate."* The plan now overloads the same word two ways: the dial table (line 61) keys `standard`-scope verification off the `deterministic` **label**, while the new `Verified`/`Refuted`/`Unconfirmed` badge is a *different* axis (was-it-checked, not could-a-gate-check-it). A `Verified` finding whose underlying claim is still a `judgment` call, and a `deterministic`-labeled finding that came back `Unconfirmed`, are both representable and will read as contradictory to a non-engineer. **The plan must state the two-axis model explicitly** (confidence = *checkability*; verification = *was-checked + outcome*) and define how the backlog renders both without confusion — ideally collapse to one badge per item with a documented precedence, not two labels the reader must reconcile. As written this is an OCP/ISP smell: the verify step bolts a second meaning onto a field other steps already own.

2. **Make the `model: opus` per-finding cost bound real, not aspirational (Slice 2).** Line 52 sets `finding-verifier` to `model: opus` and waves the cost concern away with "bounded by the scope lever." But the scope lever bounds *how many* findings get verified, not the per-finding cost, and the plan also fans them out in parallel (line 92). On a security-heavy `standard` audit this is N independent opus subagents, each doing a fresh read of cited code + context. The plan must (a) state a concrete per-run verifier cap (reuse / compose with the existing `max-cells-per-run` budget model — see #3 — rather than inventing a parallel uncapped budget), and (b) justify opus over sonnet against the dial's own KISS/effort-dial principle ([WORKFLOW.md:34](docs/WORKFLOW.md)). "Security reasoning needs intelligence" is plausible but currently asserted, not argued against the cheaper option.

3. **Reconcile "trust floor on PARTIAL" with the cell/budget/resume model — it is currently incoherent (Slice 2).** The existing budget model is deterministic: a finite `(module × dir)` cell set, `max-cells-per-run`, and a `PARTIAL` checkpoint that writes `done`/`pending` cell lists and stops ([audit/SKILL.md:160-162, 244-258, 288-301](skills/audit/SKILL.md)). The plan asserts Tier-1 + security findings from `done` cells are "**always** verified before they're written" (line 64) — but verification is *itself* work that consumes context/budget, and the plan adds it **after** the YAGNI prune (line 50), i.e. *after* the run has already spent its cell budget reaching dry/cap. So the trust floor can demand an unbounded burst of opus verifies at the exact moment the run is out of budget. The plan must say **where verification draws from the budget**: either (a) verification cells are *part of* the `max-cells-per-run` accounting (so a run may checkpoint with criticals still `⚠ Unconfirmed` — which contradicts the "always verified" floor), or (b) the floor is real and the plan must show the worst case (every covered cell is a Tier-1/security finding) still fits one ≤1M session. Pick one and make the status block represent it (a Tier-1 finding that is written but not-yet-verified needs a representable state, or the invariant is unenforceable). The current text claims an absolute guarantee the budget model can't keep.

4. **The verify step's placement vs. the resume/seen-set is under-specified (Slice 2).** Inserting verify "after step 7 (YAGNI prune), before Phase 3" (line 50) is the right *logical* spot (don't verify findings you cut). But step 5 maintains a **persisted seen-set across rounds** and step 7 runs only "after the loop has gone dry" ([audit/SKILL.md:233-242](skills/audit/SKILL.md)). On a **resume** run, are previously-`Verified` findings re-verified, or is the verdict persisted alongside the finding (and where)? If not persisted, every resume re-pays the full verify cost; if persisted, the plan must name the artifact (the backlog fence? the status block?) and confirm it survives the regenerate-don't-accumulate rule. Specify this — it's the difference between "lands complete" and "leaves a latent O(rounds) cost bug."

5. **State the `Refuted`-drop audit-trail rule precisely (Slice 2).** Line 54/66 says Refuted findings are "dropped from the backlog" but "counted + listed in the run report." The run report is *in-conversation* and ephemeral; the backlog fence is the durable artifact that **regenerates, not accumulates** ([audit/SKILL.md:35-36](skills/audit/SKILL.md)). So a false positive that was refuted leaves **no durable trace** — next run may re-find and re-present it, re-spending verify budget to re-refute it, with the user never seeing it was a known false positive. Decide and document: is the Refuted list durable (and if so, where, without violating the regenerate rule), or is re-refutation an accepted cost? Either is defensible; silence is not.

6. **Gate redesign: nail the edge cases the EXTS approach changes (Slice 1).** Dropping `STALE_PATTERN` for last-dot-extension-equality against `EXTS` does kill the `ts`-before-`tsx` bug class — good, and the right call over "order alternations longest-first." But the plan's token-extraction is hand-waved ("backtick-quoted, path-shaped … repo-agnostic regex") and several cases must be pinned down in the plan *before* spec, because they change detection semantics vs. today:
   - **Path-prefix scoping (line 39):** today staleness keys purely on path-shape; the new design adds an "in-scope path prefix" filter derived from `INCLUDE_GLOBS`. Deriving a *prefix* from a glob like `:(glob)src/**/*.tsx` is non-trivial (the `**` can be zero dirs; `:(glob)**/*.py` has no prefix). Specify the prefix-extraction rule and a test for the no-prefix / root-glob case.
   - **Windows paths:** `evaluate()` reads tree text and `Path(p).exists()`; the tree may cite `scripts/foo.py` while the file system is `\`. Existing code normalizes `\`→`/` for the *file list* ([check_architecture_tree.py:64](scripts/check_architecture_tree.py)) but the *tree-referenced* tokens come from markdown text — confirm the new extractor normalizes both sides. The plan lists a Windows test for normalization (line 44) but only for `--hook-write`; add one for `evaluate()` staleness too.
   - **Extension-less in-scope files:** the plan's mitigation (line 95) says "INCLUDE_GLOBS are extension globs by construction." That's an *assumption the init skill must enforce*. Today init can set "a conservative broad source glob" for an unmappable ecosystem ([init/SKILL.md:140-144](skills/init/SKILL.md)) — which could be a directory glob, not an extension glob. The plan must either (a) constrain init to always emit extension globs (and update [init/SKILL.md:140-144]) or (b) handle the no-extension token gracefully. Right now Slice 1 changes the gate's contract without closing the init-side of it.
   - **Nested dirs / monorepo prefixes:** add a characterization test for a deep path (`packages/app/src/x.tsx`) and a path that matches the extension but sits *outside* any in-scope prefix (must NOT be treated as a stale candidate).

7. **Don't overclaim verification in the docs — and pin the exact wording (Slice 3).** The risk is named (line 93) but the README's current honesty section is load-bearing and specific ([README.md:15, 21](README.md): *"labels what it actually checked vs. what's the model's judgment"* and *"the heavier deterministic gates are the top of the roadmap"*). The plan must require Slice 3 to keep the *same-model-class-is-not-a-deterministic-oracle* caveat **adjacent to** the new "independently verifies" claim, and the DECISIONS entry (line 76) must record that `finding-verifier` is a *false-confidence reduction*, not a trust-gate (so a future reader doesn't mistake it for the deferred deterministic track in [DECISIONS.md:37-40](docs/DECISIONS.md)). Add the exact replacement sentence to the spec so the reviewer can check it verbatim, not paraphrase it.

8. **`plugin.json` registration + tree currency are listed but verify the count/order claim (harness).** `.claude-plugin/plugin.json` currently lists **6** agents ([plugin.json:10-17](.claude-plugin/plugin.json)); the tree's manifest line says "the 6 specialist agents" ([ARCHITECTURE_TREE.md:59](docs/ARCHITECTURE_TREE.md)). The plan registers `finding-verifier` (line 68) and adds the tree entry (line 88) — good — but it must **also update that "6" → "7" in the ARCHITECTURE_TREE.md plugin.json description line** and add `finding-verifier` to the role library in [WORKFLOW.md:57-65](docs/WORKFLOW.md) (the workflow lists the starter library by name; a new first-class agent that isn't listed there is a doc-traceability gap the `docs-traceability` lens should catch). Add both to the Affected-files list.

### Sizing / completeness check

- **Slice 1 — Harden + test the gate: OK, lands complete.** Self-contained: script + `tests/` + init step 5 + tree/DECISIONS. One specialist, one session. The new pytest suite makes it vertically complete (no debt). Note: `tests/__init__.py` is auto-excluded by the existing `EXCLUDE_SUBSTR = (… "/__init__.py")` ([check_architecture_tree.py:47](scripts/check_architecture_tree.py)), so it won't need a tree entry — consistent, but the spec should confirm `pyproject.toml` (if chosen over `tests/__init__.py`) *does* get a tree entry or is out of `INCLUDE_GLOBS`. **One precondition:** per WORKFLOW's tag→discipline, hardening a behavior-bearing file is `refactor`-adjacent and characterization-first — Slice 1 satisfies this *because it writes the tests in the same slice*, but the spec must order it tests-first (lock current behavior green, *then* swap `STALE_PATTERN`→`EXTS`, prove the suite still green + the `.ts/.tsx` case flips from false-positive to clean).

- **Slice 2 — Verify-findings pass: SPLIT NOT REQUIRED, but it is the riskiest slice and only "lands complete" once #1–#5 are resolved.** It's prompt/skill engineering (no runtime code), so token cost is authoring, not execution — one session is fine. The danger is *completeness*, not *size*: as written it leaves an under-specified budget/resume interaction (#3, #4) and an unresolved label model (#1) that would surface as debt the first time someone runs a `standard` audit. **Do not split it** (the verify step + the verifier agent + the backlog format are one vertical feature — splitting them leaves a half-wired verify with no consumer). Instead, **tighten the spec** to answer #1–#5. The new-agent call is correct (see below).

- **Slice 3 — Docs & honesty: OK, lands last, correctly sequenced.** Depends on 1 & 2 being real. Add the two missing harness-doc updates (#8) to its scope.

- **Parallelism claim (Slices 1 & 2 in parallel worktrees):** **Mostly valid.** Source-file-disjoint: Slice 1 touches `scripts/` + `tests/` + `init/SKILL.md`; Slice 2 touches `audit/SKILL.md` + `finding-verifier.md` + `plugin.json`. The only overlap is `ARCHITECTURE_TREE.md` + `DECISIONS.md` (append-only files). That **is** a real merge conflict surface — both will append entries — but it's a trivial textual merge, not a logical one. Acceptable for parallel worktrees **provided** each slice appends to a *distinct section* of the tree (agents section vs scripts/tests section) so the merge is non-overlapping. Call that out in the spec. **Caveat:** `init/SKILL.md` (Slice 1) and `audit/SKILL.md` (Slice 2) share a documented DRY dependency — init step 5 reuses audit Phase 1's detection ([init/SKILL.md:134](skills/init/SKILL.md)). Slice 1's init edit (drop `STALE_PATTERN`) doesn't touch that shared detection, so no conflict — but the implementer of Slice 1 must not "tidy" the audit-reuse pointer.

### Agent decision — new `finding-verifier` vs. third `lens-reviewer` mode

**A separate `finding-verifier.md` is the right call (SOLID-correct).** `lens-reviewer` *finds gaps through one standards lens*; the verifier *refutes one specific claim against code*. Different single responsibility, different input shape (a claim + location, not a scope + module), different posture (refute-first vs survey-for-gaps). Folding it in as a third mode would violate SRP/ISP exactly as the plan argues (line 52), and the `yagni-sentinel`-as-separate-counterweight precedent ([WORKFLOW.md:63](docs/WORKFLOW.md)) is the right analogy. **However:** the plan claims independence "It is never the lens that produced the finding" (line 52) but never says *how the orchestrator enforces that*. With a clean-context subagent, independence is structural (it doesn't see the finder's reasoning, only the claim+location) — that's achievable and good. But state the enforced mechanism in the agent contract: *the verifier is given only {claim, file:line, source module, confidence, exclude-set} and the refute-first posture — never the finder's transcript or rationale.* Make that an explicit input contract in `finding-verifier.md`, or "independence" is a hope, not a guarantee.

### Harness impact

- **New agent → `plugin.json` `agents[]`** — listed (line 68). ✅ but also: bump **ARCHITECTURE_TREE.md "the 6 specialist agents" → 7** ([ARCHITECTURE_TREE.md:59](docs/ARCHITECTURE_TREE.md)) and **add `finding-verifier` to the WORKFLOW role library** ([WORKFLOW.md:57-65](docs/WORKFLOW.md)). Both missing from the plan (#8).
- **DECISIONS** — entries planned (line 76). Ensure the `finding-verifier` entry explicitly frames it as a *false-confidence reduction, not a deterministic trust-gate* (#7), so it doesn't get confused with the deferred Trust track ([DECISIONS.md:37-40](docs/DECISIONS.md)).
- **ROADMAP** — the plan ships "verify-findings" and marks "Real-app dogfood" done. Note: the current ROADMAP "Test baseline for check_architecture_tree.py" item ([ROADMAP.md:17](docs/ROADMAP.md)) is delivered by Slice 1 and must be **removed** from Next — the plan's Slice 3 says "reframe roadmap" but doesn't name this specific deletion. Add it.
- **No new STANDARD required.** This is well-covered by existing lenses (`maintainability-structure`, `testing`, `docs-traceability`). Do **not** invent a "verification" standards module — that would be scope creep (YAGNI); the discipline lives in the agent contract + audit SKILL, which is correct.
- **Candidate harness learning (Stage 9, post-land):** "two-axis confidence-vs-verification labeling" (#1) is a genuinely reusable pattern — if it works here, it's a candidate for `docs/standards/CANDIDATES.md`, not a per-repo note. Flag at retrospect, don't build now.

---

### Resolution — Stage 3 changes addressed (orchestrator)

**plan-reviewer (CHANGES REQUIRED → all addressed):** (1) label collision → **dial-table cut**; one status axis per item (verification supersedes confidence on in-scope items; out-of-scope keep the confidence label). (2) opus cost → **argued via capability-parity** + bounded by Tier-1+security-only scope (no dial throttle). (3) PARTIAL floor → reframed to **"never presented as verified unless it was"** + a representable `deferred` state; verification draws from `max-cells-per-run`. (4) resume → verdicts **persist in the fence**, not re-verified on resume. (5) Refuted trail → run-report only; not persisted (regenerate-don't-accumulate); `done` cells don't re-sweep. (6) gate edge cases → **prefix-filter cut** (extension-equality only), Windows-norm both sides, **init constrained to extension globs** + script skips extension-less globs; monorepo/out-of-scope cases tested. (7) no overclaim → exact caveat wording in the Spec; DECISIONS frames the verifier as *false-confidence reduction, not a deterministic trust-gate*. (8) harness currency → ARCHITECTURE_TREE "6→7", README "6→7", add to WORKFLOW role library, **delete the delivered "Test baseline" ROADMAP item**.

**yagni-sentinel (OVER-BUILT → cuts applied):** #1 dial-table **cut** (→ROADMAP). #2 `tests/**/*.py` in `INCLUDE_GLOBS` **dropped** (orthogonal policy → ROADMAP). #3 = #1. #4 opus **kept** (capability-parity overrides the Sonnet-default here; cost handled by #1's scope cut). #5 badge+legend **cut** → inline plain-English tags; prefix-clause **cut**. **Kept (both reviewers agree):** the `STALE_PATTERN`→`EXTS` elimination, the separate `finding-verifier` agent, the characterization tests, and Refuted-drop+report.

**No new standards module** (avoids YAGNI creep); "two-axis confidence-vs-verification labeling" flagged as a Stage-9 `CANDIDATES.md` candidate, not built now.

---

## Spec  _(per slice — Stage 4, approved Stage 5)_

> **Parallel execution rule.** Slices 1 & 2 run as two implementer agents at once. To stay conflict-free they are **fully file-disjoint**: **neither touches `docs/ARCHITECTURE_TREE.md`, `docs/DECISIONS.md`, `README.md`, `docs/PLAYBOOK.md`, `docs/ROADMAP.md`** — the **orchestrator** owns those (map + decisions at integration; Slice 3 owns the rest). This is safe for the tree-gate because each slice's *new* files are non-`.py`-in-scope (`tests/*.py` and `pyproject.toml` are out of `INCLUDE_GLOBS`; `finding-verifier.md` is markdown), so the Stop hook stays green with **no** tree edit in either worktree.

### Slice 1 — Harden + test the gate

**`scripts/check_architecture_tree.py`:**
- Add `_exts_from_globs(globs) -> set[str]`: from each `INCLUDE_GLOBS` entry, parse the trailing `*.<ext>` and collect lowercase `<ext>`; **skip** entries with no derivable `*.<ext>`. Compute `EXTS = _exts_from_globs(INCLUDE_GLOBS)` (module-level, after `INCLUDE_GLOBS`).
- Add a repo-agnostic candidate-token regex: backtick-quoted, path-shaped, with a dot-extension (e.g. `` re.compile(r"`([\w./\\-]+\.\w+)`") ``).
- In `evaluate()`: replace `referenced = set(STALE_PATTERN.findall(text))` with: extract candidate tokens, **normalize `\`→`/`**, keep those whose **last-dot extension ∈ `EXTS`**; `stale = sorted(p for p in referenced if not Path(p).exists())`. **No prefix filter.** If `EXTS` is empty, staleness is a no-op (documented).
- **Delete** `STALE_PATTERN`; rewrite the PER-REPO CONFIG comment: `INCLUDE_GLOBS` is the **only** per-repo knob; it **must** use extension globs (`*.ext`) so `EXTS` is derivable; extension-less globs are presence-checked but not staleness-checked. `INCLUDE_GLOBS` for this repo stays `[":(glob)scripts/**/*.py"]`.
- **Order: tests-first** — lock current behavior green *before* the swap, then prove still-green + `.ts/.tsx` flips to clean.

**`tests/test_check_architecture_tree.py` (new), `pyproject.toml` (new, minimal `[tool.pytest.ini_options] testpaths=["tests"]`):** mock `_git` (monkeypatch) + `tmp_path` for real `Path.exists`. Cover every case in *Test strategy → Slice 1*. `python -m pytest` must pass; `python scripts/check_architecture_tree.py` must print OK on this repo.

**`skills/init/SKILL.md` step 5:** set **only** `INCLUDE_GLOBS` (extension globs only — for an unmappable layout emit the dominant *extensions*, never a bare dir glob); **remove** all `STALE_PATTERN` authoring text + the "keep the two in sync" language.

**Acceptance:** pytest green; gate green on this repo; `.ts/.tsx` regression test proves the bug class is dead; no `STALE_PATTERN` reference remains anywhere; `init` step 5 mentions one knob. **In-scope lenses:** `testing`, `maintainability-structure`, `reliability-resilience`.

### Slice 2 — Verify-findings pass

**`.claude/agents/finding-verifier.md` (new):** frontmatter `name: finding-verifier`, `tools: Read, Grep, Glob, Bash`, `model: opus`, description (one finding → refute against code). Body: **input contract** (receives only `{claim, file:line, source module, confidence, exclude-set}` + refute-first posture; never the finder's rationale; never verifies its own lens's finding); **method** (read cited code + context; try to prove it WRONG; hunt for the specific guard claimed missing); **verdicts** — `Verified` (+ proof snippet `file:line`), `Refuted` (+ the disproving code), `Unconfirmed` (**default** when it can't tell — never guess); READ-ONLY; output = structured verdict + evidence + one plain-English line.

**`skills/audit/SKILL.md`:**
- **Phase 2:** insert a new step **after step 7 (YAGNI prune)** — "Verify high-stakes findings": for every **Tier-1 + security** survivor, spawn an independent `finding-verifier` (parallel), apply verdicts (drop Refuted; attach proof to Verified; flag Unconfirmed; `deferred` if budget-exhausted). Verification draws from `max-cells-per-run`. **Renumber** the following steps and fix cross-references. Note verdict **persistence in the fence** + **no re-verify on resume**.
- **Phase 3:** Item format gains the **inline verification tag** with the **one-status-axis** rule (verified-scope item shows its verification tag, superseding the confidence label; out-of-scope keeps the confidence label); update the **Confidence** bullet to reference the verification axis + precedence; run-report line `verified N · unconfirmed K · dropped M false positives`.
- Update the "How this skill works" note: findings are model-asserted, **then independently verified for Tier-1+security**, and human-triaged.

**`.claude-plugin/plugin.json`:** append `"./.claude/agents/finding-verifier.md"` to `agents[]`.
**`docs/WORKFLOW.md`:** add `finding-verifier` to the role library (Roles section).

**Acceptance:** the new agent enforces independence via its input contract; the audit verify step + Phase-3 tags + run-report are coherent and don't overclaim (it's a false-confidence *reduction*, not a deterministic oracle); plugin.json + WORKFLOW updated. **In-scope lenses:** `maintainability-structure`, `docs-traceability`, `testing`.

### Slice 3 — Docs (orchestrator/after 1&2)

`docs/ROADMAP.md` (drop delivered "Test baseline" item; mark dogfood done; add deferred per-dial verify-scaling) · `README.md` (honesty upgrade with the *same-model-not-a-deterministic-oracle* caveat kept adjacent; install-troubleshooting note; "6 specialist agents"→7) · `docs/PLAYBOOK.md` (one plain line) · `docs/ARCHITECTURE_TREE.md` (+`finding-verifier.md`, +`tests/…`, +`pyproject.toml`, script line, "6"→"7") · `docs/DECISIONS.md` (verify pass; gate redesign; test baseline; dogfood-done — verifier framed as false-confidence reduction). **In-scope lens:** `docs-traceability`.
