# 0016 — Namespace bundled-agent spawn references for installed adopters

- **Status:** Done (implemented 2026-06-15; all deterministic gates green — orchestrator runs the Verify panel + lands)
- **Roadmap item:** n/a — release-blocker surfaced by the an adopter pilot (2026-06-15)
- **References:** `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · claude-code-guide confirmation (plugin agents resolve only as `<plugin-name>:<agent>`)

## Problem
The engine scripts and skill prose spawn the plugin's 10 bundled agents by **bare** name —
e.g. `engine/audit.js:1119` `agentType: "lens-reviewer"`, `engine/verify.js:217`
`agentType: "architect-reviewer"`, `engine/build-item.js:703` `agentType: "implementer-architect"`,
and skill prose like `skills/build/SKILL.md:271` "spawn `implementer-architect`". When the plugin
is **installed** in an adopter repo, bundled agents resolve **only** as
`claugentic-dev-harness:<name>` (confirmed against the Claude Code plugin docs and reproduced by
the an adopter pilot: *agent type 'lens-reviewer' not found … Available: claugentic-dev-harness:lens-reviewer*).
So `/audit` and `/build` **crash for every installed adopter** at the first agent spawn. Bare names
only worked when dogfooding from this repo, where the same agents are *also* present as project-local
`.claude/agents/` — masking the bug (a textbook self-referential-evidence blind spot). This blocks circulation.

## Goals / Non-goals
- **Goal:** every SPAWN site of a bundled agent resolves for an installed adopter.
- **Goal:** built-in agents (`general-purpose`, `Explore`, `Plan`, …) stay **bare**.
- **Goal:** dogfooding from this repo still works (the namespaced id resolves here too).
- **Goal:** a regression-guard test pins the namespaced spawn strings so this can't silently return.
- **Non-goal:** touching pure descriptive mentions / file-path cross-refs / role tables (WORKFLOW.md,
  ARCHITECTURE_TREE.md, agent-def cross-refs). They are **not** spawn sites; namespacing a file path is wrong.
- **Non-goal:** changing any agent prompt, behavior, or pipeline logic.
- **Non-goal:** fixing the adopter-side skill-cache staleness (a separate install/update concern; the
  adopter must update the plugin to get this fix — the cache patch was always ephemeral).

## Approach
Hardcode the namespace `claugentic-dev-harness:<name>` at **spawn sites**.
- **Engine:** add one **pure** helper to each engine file's `// --- helpers ---` block —
  `const nsAgent = (t) => \`claugentic-dev-harness:${t}\`;` — and wrap every **custom**-agent
  `agentType` (`agentType: nsAgent("lens-reviewer")`). Built-ins stay bare literals. Pure → unit-testable
  via the existing extract-and-eval harness.
- **Prose:** at the SPAWN-PROSE instructions in `skills/build`, `skills/audit`, `skills/product`, write the
  spawn instruction with the namespaced id. Descriptive mentions stay bare.
- *Alternatives rejected:* (a) runtime-derive the namespace — no FS/plugin-context global is available to a
  Workflow script (KISS); (b) a relative/bare convention — none exists per the docs.

## Affected files
- `engine/audit.js`, `engine/verify.js`, `engine/build-item.js`, `engine/qa.js` — namespace custom-agent `agentType`s via `nsAgent`.
- `skills/build/SKILL.md`, `skills/audit/SKILL.md`, `skills/product/SKILL.md` — namespace the spawn instructions.
- `tests/workflows/verify.test.mjs` (+ `audit/build-item/qa.test.mjs` as needed) — update the 6 bare-name assertions to namespaced; add a guard test.
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — bump to `0.1.34`.
- `docs/DECISIONS.md` — append the decision. `docs/ARCHITECTURE_TREE.md` — only if a description changes (no new files; expected no-op).

## Plan-reviewer required changes (folded in)
1. **Add the missed positional spawn `engine/verify.js:447` (honesty judge).** Real judge spawns go through `spawnJudge(role, agentType, …)` → `agent({ agentType })` (verify.js:392/395); the agentType is a **positional arg** at `verify.js:447` (`"honesty-reviewer"`) and `:489` (`"architect-reviewer"`). Roster entries 211–217 are cosmetic (feed `log()`/return only) — namespace them too for consistency, but the **load-bearing** spawns are 426/436/447/489.
2. **Strengthen the residual guard** — an `agentType:` grep can't see positional args. The guard greps the **quoted custom-agent name set** for zero *unprefixed* occurrences in `engine/*.js`, AND asserts the four `"general-purpose"` literals stay bare. Implement as a source-level regression test (the Stage-9 lesson→gate).
3. **Test impact is just `verify.test.mjs:328`** (the roster `agentType` assertion). Lines 347/353/357/361/367 pass agentType as an opaque arg to `judgeOutcome` and assert on outcome shape — they neither break nor change.
4. **Prose disambiguation rule** — namespace only the imperative *spawn* instruction; leave file-path cross-refs and descriptive mentions bare, and do **not** disturb the co-located `fable` override.

## Risks & mitigations
- **Missing a spawn site → still crashes.** → Drive from the exhaustive sweep (incl. the positional verify.js:447/489); after editing, the regression test asserts **zero** unprefixed quoted custom-agent names in `engine/*.js`; verify panel cross-checks.
- **Test assertions pin bare names → break.** → Update `verify.test.mjs:328` to the namespaced value (only that one breaks); add the regression guard.
- **Built-in accidentally namespaced** (`general-purpose` in qa/build-item). → Explicitly excluded; guard test asserts built-ins stay bare.
- **Over-namespacing a non-spawn mention** (file path / role description). → Strictly scope to spawn sites.
- **In this repo, a namespaced ref runs the *cached* plugin agent, not working-tree edits.** → Already true for the cached engine/skills; documented; agent-edit dogfooding goes via plugin reinstall (existing gotcha).
- **No live adopter-spawn proof here.** → Honest limit: the proof surface is the namespaced-string pins + the docs/claude-code-guide confirmation + the reproduced pilot error; a true end-to-end re-run requires the adopter to update to 0.1.34.

## Test strategy
- `node --test tests/workflows/*.test.mjs` green incl. updated + new pinning tests.
- `pytest`, `check_versions_synced.py`, `check_architecture_tree.py --hook` green.
- Grep: zero residual bare custom-agent `agentType:` in `engine/*.js`; built-in `agentType`s remain bare.

## Decomposition (slices)
- [x] **Slice 1** — namespace all engine + prose spawn sites, update + add tests, bump manifests, append DECISIONS. Lands complete because it is a single cohesive packaging fix with its own regression test, ≤1 session.

---

## Review  _(plan-reviewer, Stage 3 — 2026-06-15)_

RUNNING AS: Opus 4.x

> Same-model review on this run — the judge and the builder are the same model family here. This is a reduction of shared-blind-spot risk, not an independent oracle: take the findings on their cited merits, not on reviewer authority.

- **Verdict:** **CHANGES REQUIRED** (the approach is sound; the spawn-site inventory and the residual-grep mitigation are both incomplete in a way that re-creates the exact bug for two judge spawns).

### Required changes

1. **Add the missing spawn site `engine/verify.js:447` (honesty judge) to the inventory.** The actual judges in `verify.js` are spawned via `spawnJudge(role, agentType, …)` — `spawnJudge` passes its positional `agentType` arg into `agent({ agentType, model, … })` (verify.js:392/395). The two judge spawns are therefore the **positional string literals**: `verify.js:447` `"honesty-reviewer"` and `verify.js:489` `"architect-reviewer"`. The plan lists 489 but **omits 447**. Roster entries 215/217 are cosmetic (see #3) — leaving 447 bare means the honesty judge still crashes on every installed trust-surface verify. Add 447; namespace both positional args.

2. **The residual-grep mitigation `bare custom-agent agentType:` cannot catch the real judge spawns — strengthen it.** verify.js:447 and 489 are passed as **positional arguments** to `spawnJudge`, not as `agentType:` object keys, so a grep for `agentType:` proves nothing about them. Replace the mitigation with a grep over the **bare quoted custom-agent name set** (`"lens-reviewer"|"yagni-sentinel"|"honesty-reviewer"|"architect-reviewer"|"finding-verifier"|"blindspot-reviewer"|"implementer-architect"|"plan-reviewer"|"product-designer"|"product-critic"`) asserting zero residual **unprefixed** occurrences in `engine/*.js`, AND a positive grep asserting the four `"general-purpose"` literals (qa.js:985/1025/1089, build-item.js:762) stay bare. This is the load-bearing regression guard; the helper unit test is not (see #4).

3. **Correct the test-impact inventory: only `verify.test.mjs:328` is a behavioral pin; 347/353/357/361/367 are not.** Line 328 (`assert.equal(honesty.agentType, "honesty-reviewer")`) asserts the **roster** value and MUST flip to `claugentic-dev-harness:honesty-reviewer` once verify.js:215 is namespaced. Lines 347/353/357/361/367 pass the agent-type only as an **opaque positional arg** to `judgeOutcome` and assert solely on outcome shape (`forcedSameModel`/`needRetry`/the throw-regex, which does not match the agentType) — they do **not** break and do **not** need changing for green. Updating them for input-realism is optional; listing them as "assertions that pin bare names" is inaccurate and risks the implementer thinking the test work is done when the real regression guard (#2) is still missing. State plainly: the only existing test that breaks is 328; everything else is the new guard.

4. **Drop the "pure → unit-testable via the extract-and-eval harness" framing for the wrapping.** The `nsAgent` helper is trivially testable, but **every spawn site that matters lives below `// --- end helpers ---` in the control-flow section** (verify.js after :380, audit.js after :999, qa.js after :732, build-item.js after :619; the only in-helpers occurrences are the cosmetic verify.js roster 211–217). A `const nsAgent` in the helpers block IS in module-top-level scope and reaches those sites — so the mechanism works — but the extract-and-eval harness does **not** exercise the wrapping. The guard for the wrapping is the source grep (#2), not a helper unit test. Say so, so the proof surface isn't over-claimed (honesty register).

5. **Add an explicit prose disambiguation rule for the skills.** In `skills/*/SKILL.md` the identical bare token (e.g. `plan-reviewer`) appears in three roles on adjacent lines: a **spawn directive** (build:237 "spawn `plan-reviewer`"; audit:276/288–289), a **role label in prose**, and a **file-path cross-ref** (`.claude/agents/plan-reviewer.md`). The non-goal correctly excludes the file path, but the plan gives the implementer no rule to tell a spawn directive from a prose label. State the rule: namespace **only the imperative spawn instruction** ("spawn `X`" / "one `X` per …" in the prose-orchestrated execution path), leave the `.claude/agents/X.md` cross-refs and descriptive role mentions bare. Without this the "~10 prose" count is unverifiable and the slice is ambiguous. (Note the audit/build prose ALSO carries the `fable` override instruction for judge roles — namespacing must not disturb that; an installed prose-orchestrated run needs both the namespace AND the override.)

### Sizing / completeness check

- **Slice 1 — OK, no split.** A single cohesive packaging fix: ~19 engine literals + the prose spawn directives + 1 broken test + 1 new guard + 2 manifest bumps + 1 DECISIONS line. Mechanical, no cross-file design coupling, lands vertically complete with its own regression guard. Well within one session. **It only lands complete if #1, #2, #5 are folded in** — as written it leaves verify.js:447 broken (half-done for the trust-surface path), which would fail the no-debt gate.
- **Behavior-change check (item 4 of the brief): clean.** `judgeOutcome` uses `agentType` only in a throw-message string (verify.js:247) — cosmetic. The roster `agentType` feeds only `log()` (414) and the returned `panel:` object (537) — cosmetic. Dedup keys on `file:line`+dimension (verify.js:162), roster keys on `role`, cross-model/same-model tags key on `role`/`reportedFamily` — **none key on `agentType`**, so namespacing changes nothing but resolution. The "no behavior change" claim holds; the only string a consumer sees differently is the roster echo and the error message, both correct to namespace.
- **Path (Stage 0): correct.** Spawn-site-only, descriptions-bare is the right scope; the rejected alternatives (runtime-derive, relative convention) are sound per the no-plugin-context-global constraint. No YAGNI concern — this is the minimum fix, not over-built.
- **Honest-limit (no live adopter proof): acceptable as stated**, given the reproduced pilot error + docs confirmation + the string pins; keep the register honest in DECISIONS (the fix is *expected* to resolve, proven only when an adopter updates to 0.1.34).

### Harness impact

- **DECISIONS:** append under *Plugin identity & distribution* — "bundled-agent spawns must use `claugentic-dev-harness:<name>`; bare names resolve only when dogfooded (project-local `.claude/agents/` masked the bug — a self-referential-evidence blind spot); built-ins stay bare." Correctly listed.
- **Stage-9 gate candidate (the lesson→gate step, WORKFLOW §9(b)):** this class of bug is mechanically detectable. Add a ROADMAP gate item: a deterministic check (sibling script or a `*.test.mjs` pin) asserting **every quoted custom-agent name in `engine/*.js` and every spawn directive in `skills/*/SKILL.md` is namespaced**, built-ins exempt — so this can't silently return. The plan's per-slice guard (#2) covers the engine; a standing gate is the durable harness improvement and should be logged now even if built later.
- **Version bump 0.1.33 → 0.1.34:** correct (plugin.json is currently 0.1.33; bump both manifests — `check_versions_synced.py` enforces the pair).
- **ARCHITECTURE_TREE:** no-op expected (no file add/move; engine descriptions unchanged) — correct, unless a description references "spawn by name" worth a one-word note (optional).
