# 0040 — Shard the DECISIONS ledger (index + per-topic shards)

- **Status:** Approved (2026-07-16) → Implementing
- **Resumable from:** `Slice 1 implementation in progress (worktree)` — implementation order: gate capability + tests green → scripted move + entry-level substring check → rewiring (write-path · WORKFLOW · tree · ROADMAP · doctor) → full gate suite → commit. If a session dies mid-move: `git checkout` the ledger + shard dir and re-run the extractor — never resume a partial move by hand.
- **Blockers:** `none`
- **Flags:** `<none>`
- **Disposition at close:** per `docs/claugentic-WORKFLOW.md` → Plan file lifecycle.
- **Roadmap item:** amends the existing `docs/claugentic-ROADMAP.md:44` ledger-sharding item (was "Not built")
- **References:** `docs/claugentic-ARCHITECTURE_TREE.md` · `docs/claugentic-DECISIONS.md` · `docs/claugentic-WORKFLOW.md` → Doc lifecycle (ladder at :172-178)
- **2b panel:** convened 2026-07-16 (maintainability-structure · docs-traceability · yagni-sentinel · honesty-reviewer); this revision incorporates the round (1 round, bounded).

## Problem

`docs/claugentic-DECISIONS.md` (54,416 B measured) has crossed the 90% WARN line of its 60,000 B budget with no condensable material the 2026-07-06 condensation pass could find (`[J]`, corroborated by the leanness audit's 20/21 REFUTED). Git history shows the post-condense floor **trending upward** across the three pass days (lowest post-pass size: ≈47.5K Jul 3 → ≈50.3K Jul 4 → ≈53.2K Jul 6). Root cause: the ledger has evolved from a chronological log (condensable — entries supersede) into a **themed rule-book of do-not-re-break / do-not-re-litigate contracts** (non-condensable — entries persist by design). Condense-plus-fixed-total-budget is the right mechanism for a log and structurally wrong for a rule-book. The budget currently guards total bytes known; the quantity worth guarding is bytes read per consultation.

**Ladder honesty (this plan reverses a recorded stance):** WORKFLOW `:172-178` already records sharding as the ladder's rung 3 — "LAST resort (PARKED, not built)… reached only if rung 2 has itself become untenable." This plan **skips rung 2 (cap-bump) deliberately**: a recorded bump is the right answer for a log and a treadmill for a rule-book whose floor trends upward — bumping defers, it does not resolve. That reversal is recorded as a dated decision (see Affected files), not slipped in as a tidy-up.

## Goals / Non-goals

- Goal: smaller, index-routed consultation reads (model-upheld — the budget bounds shard *size*, not how many shards an agent opens; the tree's "LOCATE, don't ingest" applied to the ledger).
- Goal: content-preserving moves — sections move verbatim **except two enumerated amendments** (see Approach 6). This is reorganization, NOT condensation and NOT pointer-collapse (the leanness audit REFUTED pointer-collapse; content moves intact).
- Goal: per-shard budgets so a harness-side WARN names one shard and remediation scopes to it; a glob entry means new shards need no budget-dict edit, so remediation cost does not grow with shard count on the axes visible today. (**Adopter honesty:** the gate is stripped from the release — no adopter WARN exists unless they add caps keys themselves.)
- Goal: path stability — `docs/claugentic-DECISIONS.md` remains at its path as the index. The 90 references / 41 files (measured; ~109 lines counting seed-template forms) stay **path-valid**; section-targeted pointers resolve **one hop via the index**, which depends on keyword-rich index lines (model-upheld, checked against the enumerated pointer list in Acceptance below — not mechanically verified).
- Goal: adopters unaffected — seeded ledger stays single-file; the already-documented rung 3 becomes "built and climbed by the harness on its own ledger; optional last resort for an adopter," with the adopter procedure stated (one caps-config key per shard — doctor's flat caps map has no glob support).
- Non-goal: no rewriting/condensing of any entry EXCEPT the two enumerated amendments (Approach 6).
- Non-goal: no archive tier (git history stays the only archive).
- Non-goal: no INVARIANTS restructure (10,143/20,000 today; the amended ROADMAP sharding item notes it climbs the same ladder when its own WARN fires — no new roadmap line).
- Non-goal: no new hooks/enforcement (deferred-enforcement decision holds; this amends the existing `check_doc_budgets.py` gate's data + adds a glob capability). The considered-and-skipped option of registering the shard dir in the shipped-content scanner's forbidden set is recorded here once: skipped (YAGNI + the posture) — the no-literal-shipped-path rule below is **model-upheld, not gate-caught**.

## Approach

1. **`docs/claugentic-DECISIONS.md` becomes the index — content-free by rule.** First content line is an imperative stop-sign: *"Index only — never append entries here; file into the fitting shard (no fit → create one — growth is horizontal). Not finding something? `rg docs/claugentic-decisions/`."* Then: one keyword-rich line per shard (~150-char target, tree-style), a "read `honesty.md` first" marker, and the internals rule: **all external references point at this index; never link a shard path from outside it** (that rule is what keeps a future shard split cheap).
2. **Shards** at `docs/claugentic-decisions/<topic>.md`, sections moved verbatim: `honesty` (2,809) · `deterministic-gates` (6,102) · `verify-roles` (2,022) · `audit` (6,234) · `build-mode` (3,248) · `doc-lifecycle` (1,763 + the whole relocated `## Readiness` section, 329 B) · `plugin-distribution` (10,992, **not split**) · `release-contract` (5,848) · and the one oversize section `Workflow & roles` (14,056 measured — over budget; 24 flat top-level bullets, no `###` seams) split topically at creation into `workflow-process.md` + `roles-review.md` (verbatim partition, no rewording). No percentage seed rule — the only creation constraint is the gate itself: a seed shard may not start in its WARN band. (Byte figures are body-only measurements except `Workflow & roles` 14,056 and `Readiness` 329, which include their headings — presentational only; the extractor works from heading offsets.)
3. **Shard header (each file, one line):** *"Part of the decisions ledger — index & filing rule: `docs/claugentic-DECISIONS.md`. Do not link this file from outside the index."* (back-pointer + internals rule at point of use; deliberately NOT an in-dir README — no second index.)
4. **Budgets — exactly one cap source per file.** Index cap **set from the drafted index at Spec time** (the index is drafted during Spec; the cap is chosen so the seed lands ≤70–75% of it — a tight cap is the mechanical backstop for the model-upheld routing rule, and slack is where mis-routed entries would hide) · shards **14,000 B** each (largest seed = plugin-distribution at ~80% — accepted, see Architecture; ≈3.5K tokens per consult). `check_doc_budgets.py`: entries gain an explicit kind (a `"glob": True` flag — no key-sniffing; **a rule with no `glob` key resolves to a single-file target so the existing hermetic test fixtures pass with ZERO edits**) via a new pure `_resolve_targets(rel_path: str, rule: dict) -> list[str]` seam (**sorted** output — glob order is FS-dependent; the collapsed summary and its test need determinism) feeding the **unchanged** `_check_one`; glob entry `docs/claugentic-decisions/*.md`; zero matches = fail-loud error; a subdirectory under the shard dir = fail-loud error (recursion is speculative — assert instead); OK-summary collapses a glob to one clause (`…/*.md (10 files) <= 14000 bytes each` — count computed at runtime, not hardcoded). **Existence guard = a SEPARATE construct, never a second cap:** `REQUIRED_SHARDS: tuple[str, ...]` (the seed shard filenames) with its own pure existence check surfaced through `evaluate()` — deleting `honesty.md` fails loud while the shard cap keeps exactly ONE home (the glob entry: no duplicate WARN lines, no second cap source). Docstring states the honest limit: a post-seed shard's *existence* is unguarded until listed (its *budget* is glob-covered).
   **String register constraint:** new/edited docstring + remediation strings preserve the existing honesty register — a WARN is printed, exit 0, a heads-up cueing a judgment pass, never "enforced"/"will be split"; shard-shape WARN remediation ≈ *"approaching budget — condense this shard, or split it topically"*. Avoid the literal phrase "WARN fires" in any SHIPPED prose (`test_shipped_condensation_trigger.py` trip-hazard).
5. **Shipped-doc wording (model-upheld rule):** no literal `docs/claugentic-decisions/` path in any SHIPPED file — the dir joins `DEV_ONLY_DIRS`, is not init-recreated, and (verified) is **structurally invisible to `check_shipped_content` Pass A.a/D** (dir-swept paths carry no recreate-class), so this rule is upheld at authoring time and by reviewer read of the shipped diff, **not by any gate**. The literal path lives only in dev-only files (the index, repo CLAUDE.md, this plan). Note: the standards-catalog precedent gives this design its *structure* only — that dir ships and is init-refreshed; this one is stripped and never recreated, and it's the ship/strip half that creates the wording constraint.
6. **The two verbatim exceptions (enumerated):** **(a)** the Doc-lifecycle rung-3 line (`DECISIONS.md:87`, *"shard = LAST resort, PARKED (ROADMAP; not built)"*) — amended in place + re-dated: rung 3 is built and climbed by the harness on its own ledger; rung 2 deliberately skipped (log-vs-rule-book rationale); **(b)** the cap-list line (`DECISIONS.md:21`, *"…`DECISIONS.md` 60K…"*) — amended in place + re-dated to the sharded cap shape (index cap + per-shard 14K). Every other entry moves byte-identically. (`DECISIONS.md:23` — the tree's "condense now, shard later" — is about the *tree*, stays true, don't sweep it.)
7. **Write-path routing (the index header can't reach a writer that never opens the file):**
   - Repo `CLAUDE.md`: the "Record decisions" line gains a ~40-char path-free clause (*"…filed per its header's filing rule"*), plus one Harness-Discipline one-liner carrying the internals rule to writers who never open the shard dir (*"reference the decisions ledger only via `docs/claugentic-DECISIONS.md`; never link a shard path directly"*). Headroom verified: 4,672/6,000 B.
   - `.claude/agents/implementer.md` + `.claude/agents/retrospect-harvester.md` (SHIPPED) append-instructions gain the same **path-free** clause — adopter-honest: the shipped seed `claugentic-_DECISIONS.md` already instructs filing "at the top of the relevant section," so "filing rule" is true in both shapes.
   - Consult-widening (SHIPPED, path-free, adopter-harmless): `.claude/agents/synthesizer-gate.md:17` + `retrospect-harvester.md:12` read-instructions gain *"…then the shard(s) the index points at for the areas you're judging"* (an unsharded ledger has no shards — no-op for adopters).
   - `engine/*.js`: **no edits, by design** (adopter-accurate + ASCII-only). Stated consequence, not hidden: `engine/build-item.js:557` emits an append-instruction, so in this repo correct routing relies on the index stop-sign when that agent opens the file (model-upheld). The other four engine refs are consult-pointers.
8. **Strip-classification guard:** `build_release.is_dev_only` prefix-matches case-**sensitively** while the dev filesystem is case-insensitive — a mis-cased tracked prefix (e.g. `docs/claugentic-Decisions/…`) would escape the sweep and SHIP. Add a test asserting every tracked file under the shard dir classifies dev-only.

Alternatives rejected: raise budget to 80K (rung 2 — treadmill for a rule-book, recorded); pointer-collapse (REFUTED, do-not-re-propose); archive file (retired convention); per-entry budgets (rejected in the script's own docstring); per-shard condense-skill operating branch (speculative — no adopter can be in the sharded state; the skill's "references the ladder; does not build it" stays true).

## Architecture & holistic fit

- **Codebase fit** — applies the repo's proven index+modules pattern to its last monolithic knowledge store; the budget script keeps its single-dict + independent-per-file design, extended at a named seam (`_resolve_targets`) so existing tests keep pinning `_check_one` unchanged (open/closed, test-pinnable).
- **Product fit** — adopter promise unchanged (one simple ledger file); the ladder's last rung becomes real, documented honestly, with the adopter procedure stated.
- **Net context accounting** — per-consult read drops ~54K → ≤14K (+ the Spec-sized index, ~3K); the tree gains ONE dir-level line + a rewritten `DECISIONS.md` line (index shape), NOT per-shard entries — the read-every-task tree does not re-spend what the on-demand ledger saves. Tree entries for docs are model-upheld (the tree gate's globs cover only `scripts/**/*.py` + `engine/**/*.js`) — Verify must not claim the tree gate proves shard indexing.
- **Quality dimensions to uphold** — `maintainability-structure` · `docs-traceability` · `testing` (entry point: `docs/claugentic-ENGINEERING_STANDARDS.md`).
- **Principle recorded** (doc-lifecycle shard): **bound what an agent READS per consult, not what the harness KNOWS.** Stage-9 harvest item: promote it — with the index+shards+per-shard-budget shape as the worked example — into `docs/claugentic-standards/maintainability-structure.md` (project-agnostic, adopter-reusable; staged per the two-tier promotion rule).
- **Future-proofing** — INVARIANTS climbs the same ladder when its own WARN fires (recorded in the amended ROADMAP item; nothing built now). A future shard split stays cheap only while the internals rule holds (index-only external references). **Accepted + named:** `plugin-distribution.md` seeds at ~80% of its cap — the most-appended area — and is expected to be the FIRST post-land WARN within a release or two; that is the designed remediation path (split topically), not a design miss.

## Affected files

- `scripts/check_doc_budgets.py` — glob-kind entries + `_resolve_targets(rel_path, rule)` seam + index/shard caps + `REQUIRED_SHARDS` existence check + no-subdir assertion + register-safe strings (drop the 60K entry in the same edit).
- `tests/test_check_doc_budgets.py` (**EXTEND — it exists, 264 lines, 7 classes**; its hermetic `{path: {"max_bytes": N}}` fixtures must pass UNCHANGED) — see Test strategy.
- `docs/claugentic-DECISIONS.md` — rewritten as the index (path unchanged). Both Approach-6 amendments land in the SHARDS their entries move into (`doc-lifecycle.md` · `deterministic-gates.md`), not in the index.
- `docs/claugentic-decisions/*.md` — 10 seed shards (verbatim + the one split + the folded `## Readiness` section).
- `scripts/build_release.py` — `DEV_ONLY_DIRS` += `docs/claugentic-decisions/` (shipped-set byte-identity test stays green).
- `CLAUDE.md` · `.claude/agents/implementer.md` · `.claude/agents/retrospect-harvester.md` · `.claude/agents/synthesizer-gate.md` — path-free routing/consult clauses per Approach 7.
- `docs/claugentic-WORKFLOW.md` — **four factual corrections** (`:172` lever list · `:176` rung 3 · `:178` deferred-lever note · `:165` budgeted-set enumeration, generically reworded): rung 3 = built and climbed by the harness, optional last resort for adopters; the adopter caps procedure is **doctor's to state** (the rung POINTS at it — WORKFLOW `:177` already defers the caps reader-contract to doctor, "this doc does not redefine it"); rung-2-skip rationale; generic wording, no literal shard path, no "WARN fires" phrasing, no claim that an adopter WARN "localizes" (none exists).
- `skills/doctor/SKILL.md` — the ONE owner of the adopter caps sentence: a sharded ledger needs one caps-config key per shard (absent key = un-capped/skipped). WORKFLOW's rung points here; no duplicate.
- `skills/condense/SKILL.md` — **NO edit** (decided at Stage 3: its ladder line `:136` stays true post-land — sharding remains the last resort and the line never claimed "unbuilt"; "references the ladder; does not build it" survives). NO per-shard operating branch.
- `docs/claugentic-ROADMAP.md` — amend `:44` (sharding no longer "Not built"; parked item narrows to "INVARIANTS climbs the same ladder at its own WARN").
- `docs/claugentic-ARCHITECTURE_TREE.md` — rewrite the `DECISIONS.md` line (`:26`, index shape) + ONE dir-level line for the shards + amend the stale `DOC_BUDGETS` cap list at `:108`.
- `tests/test_seed_templates.py` — comment correction only (`:63-70` sentinel rationale references the pre-shard heading location; assertion unchanged).

## Research / grounding

- **Files reviewed:** ledger (all sections, byte-measured) · `check_doc_budgets.py:47-115` · `build_release.py` (DEV_ONLY_DIRS, `is_dev_only` case-sensitivity) · `check_shipped_content.py:185-316` (dir-swept invisibility — verified by the 2b panel) · WORKFLOW `:160-180` (the existing ladder) · `skills/condense/SKILL.md` · `skills/doctor/SKILL.md` (flat caps map) · reference inventory (90 lines/41 files literal; ~109 with seed-template forms; **zero content-parsing consumers found — nothing breaks at the path level**).
- **Harness docs consulted:** WORKFLOW → Doc lifecycle + DoD; DECISIONS → leanness-audit do-not-re-propose · retired-archive · deferred-enforcement · release/referential-closure contracts.
- **2b panel round (1, bounded):** yagni OVER-BUILT verdict → cut second content split, 75% rule, two verification rituals, per-shard tree lines, INVARIANTS roadmap line, condense-skill branch; merged slices. maintainability F1-F13 → required-set, internals rule, adopter caps procedure, case test, `_resolve_targets` seam, tight index cap. docs-traceability F1-F12 → write-path inventory, six stale "not built" statements, scanner-invisibility proof, condensation-trigger test trap, enumerated pointer list. honesty OVERCLAIMS (2 blocking) → scanner claim corrected, verbatim exception enumerated, register fixes throughout.

## Risks & mitigations

- **Content loss during the move** → the move is a **scripted extraction** (heading offsets from `git show <pre>:docs/claugentic-DECISIONS.md` → shards written as bytes/`newline=""`; `.gitattributes` pins `eol=lf`, so byte-identity is well-defined on Windows) — **never model-retyped prose**. Then an exact, split-agnostic check — a **line-multiset equality**: `sorted(lines(pre-move)) == sorted(lines(concat(shards)) − scaffolding)`, whose only expected diffs are the two enumerated amendments + structural scaffolding (section headings, shard headers) (`[D]` one-shot at Verify; not a permanent gate — deferred-enforcement holds).
- **A shipped file gains a literal shard path** → model-upheld authoring rule + reviewer read of the shipped diff at Verify (**no gate covers this** — stated plainly).
- **Writer routes a new entry to the wrong shard / appends to the index** → index stop-sign + the tight Spec-sized index cap (Approach 4) as the mechanical backstop + the write-path clauses (Approach 7); doctor's roadmap-candidate ledger-coherence check is the eventual net — accepted risk, same class as today's wrong-section risk.
- **Section-targeted pointers degrade** → enumerated acceptance list (below), not a sample. One known degraded link: `docs/claugentic-PRODUCT.md:261` names the honesty *section* — index line must carry "honesty" so the hop is one step.
- **Stale-ladder / stale-cap incoherence** → **nine** stale statements, individually enumerated in Affected files (WORKFLOW ×4 · ROADMAP `:44` · DECISIONS `:87` + `:21` · TREE `:26` + `:108`); the rung-2-skip decision is dated into `doc-lifecycle.md`. **The index's own recourse is stated there too: rung 2 (a recorded cap-bump) IS the right rung for the index** — a routing table is all-live and cannot itself be sharded, and growth-by-new-shards legitimately raises its cap over time. Coherent with skipping rung 2 for the rule-book: different content class, different rung.

## Test strategy

**Extend** `tests/test_check_doc_budgets.py` (exists — 264 lines, 7 classes; its hermetic `{path: {"max_bytes": N}}` fixtures MUST pass unchanged, which is what pins the no-`glob`-key ⇒ single-file contract): glob resolves per-file independent checks (**sorted**) · zero-match fail-loud · subdir-under-shard-dir fail-loud · `REQUIRED_SHARDS` deletion (`honesty.md` removed → exit 1; existence check distinct from the cap) · WARN/breach thresholds per shard · collapsed glob summary line · `_check_one` pinned unchanged. New assertion in `tests/test_build_release.py` (or sibling): every file under `docs/claugentic-decisions/` classifies dev-only (case guard). Existing suites stay green: `test_build_release` (shipped-set byte-identity) · `test_check_shipped_content` · `test_seed_templates` · **`test_shipped_condensation_trigger`** (the "WARN fires" shipped-prose regex — in blast radius, listed deliberately). Verify additionally runs the one-shot line-multiset check (Risks 1) and the full gate suite.

## Acceptance criteria (Slice 1)

1. All gates green; extended tests pass; the entry-level substring check passes with exactly the enumerated diffs (two amendments + structural scaffolding).
2. Post-shard: `python scripts/check_doc_budgets.py` exits 0 with **no WARN** — the index seeds ≤75% of its Spec-drafted cap (strictly below the WARN band); every shard strictly below its WARN band.
3. Index lines cover the enumerated section-pointer targets verbatim: *Plugin identity & distribution* (the four engine consult-pointers) · *Honesty positioning* · *The deterministic gates*; entry-level pointers ("the two senses of 'independent'" · "Managed docs are adopter-aware" · craft/product entries · the plan-0034 release/`source.ref` content — keyworded on the plugin-distribution/release index lines) reachable in one hop. (`RELEASE_CHECKLIST.md:39` is a bare whole-file pointer — path-valid, needs nothing.)
4. No SHIPPED file contains the literal `docs/claugentic-decisions/` (checked by reviewer read of the shipped diff — model-upheld, no gate).
5. All **nine** formerly-stale statements read true post-land (WORKFLOW ×4 · ROADMAP `:44` · DECISIONS `:87` + `:21` · TREE `:26` + `:108`). `skills/condense/SKILL.md:136` verified-true unchanged (decided: no edit).

## Decomposition (slices)

- [ ] **Slice 1 (single slice — atomic).** Script capability + caller + tests + the restructure + all rewiring above, one session. (The panel cut the two-slice split: a capability slice with zero callers is dead code until its caller lands; capability + caller + tests together IS the no-half-state guarantee.)

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_

_Reviewer: `synthesizer-gate`, clean context, **running as Opus 5** (same model family as the planner — independence of **role + clean context**, NOT of model; a reduction of rubber-stamping risk, never a guarantee). Every claim below was spot-verified against the live files, not read off the plan's Research section._

- **Verdict (round 2): PASS** — conditional on the four **binding pre-Spec corrections** in *Outstanding* below (they are mandatory, not optional polish; Verify checks them). Round 1 returned CHANGES REQUIRED (5 blocking · 6 accuracy · 2 rationale); **all 14 dispositions re-checked against the code and confirmed** — no disposition was accepted on assertion. The design is unchanged and sound; what remains is two stale numbers and two definitional clauses, none of which touch the approach.

### Round-1 dispositions — re-verified (14/14)

| # | Round-1 finding | Round-2 state |
|---|---|---|
| 1 | tests file called "new" (it exists) | **Fixed** `:60`, `:88` — EXTEND + "fixtures pass UNCHANGED"; the no-`glob`-key ⇒ single-file contract is stated at `:35` and *pinned by* the untouched fixtures. Correct mechanism. |
| 2 | required-set = second cap + double-check | **Fixed** `:35` — `REQUIRED_SHARDS` is a separate existence-only construct; shard cap has one home (the glob). No duplicate WARN path remains. |
| 3 | `_resolve_targets(entry)` unimplementable | **Fixed** `:35` — `(rel_path: str, rule: dict) -> list[str]`, sorted. |
| 4 | predicate can't yield "exactly one mismatch" | **Fixed** `:80`/`:92` — entry-level + preamble + reverse direction; Readiness restated as the whole 329 B section, Workflow & roles as 14,056 B / 24 flat bullets. (One definitional gap remains — O2.) |
| 5 | `DECISIONS.md:21` cap-list stale inside a "verbatim" shard | **Fixed** `:38` — second enumerated exception, amended in place + re-dated; Goals `:21`, Non-goals `:25`, Acceptance `:96` all say *two*. |
| 6 | index cap asserted, not sized; growth dead-end | **Fixed** `:35` (cap set from the drafted index at Spec, seed ≤70–75%), `:84` (rung 2 IS the index's rung — argued, not asserted), `:93` (off-by-one gone). |
| 7 | `ARCHITECTURE_TREE.md:108` cap list | **Fixed** `:69`. |
| 8 | `WORKFLOW.md:165` budgeted-set enumeration | **Fixed** `:65` — fourth correction, generic wording (no shard path). |
| 9 | `(9 files)` vs 10 shards | **Fixed** `:35` — `(10 files)`, computed at runtime. |
| 10 | move mechanism unspecified | **Fixed** `:80` — scripted extraction, bytes/`newline=""`, LF note, "never model-retyped". |
| 11 | pointer list mis-described `RELEASE_CHECKLIST:39` | **Fixed** `:94` — reclassified as a bare whole-file pointer; plan-0034/`source.ref` keyworded. |
| 12 | case rationale factually wrong | **Fixed** `:44` — now the real hazard (case-sensitive `is_dev_only` prefix vs case-insensitive FS ⇒ a mis-cased prefix ships); test kept, scoped to *tracked* files. |
| 13 | adopter caps sentence duplicated | **Fixed** `:65`/`:66` — doctor is the one owner; the rung points at it, per WORKFLOW `:177`'s own deferral. |
| 14 | conditional condense-skill edit left open | **Fixed** `:67`/`:96` — decided NO edit, hedge removed. |

Sizing/harness carry-ins also landed: intra-session order + interruption recovery (`:4`), plugin-distribution ~80% named as the accepted first WARN (`:55`), the Stage-9 promotion of the reads-vs-knows principle (`:54`), the CLAUDE.md internals-rule one-liner with verified headroom (`:40`).

### Outstanding — binding before Spec opens (4)

- **O1 — two stale `4K` index-cap references contradict the new Spec-time sizing.** `:52` (*"≤14K (+4K index)"*) and `:82` (*"tight **4K** index cap** as the mechanical backstop"*) still carry the number that change 6 removed from `:35`/`:93`. This is the exact failure mode the round-1 finding described — an implementer reading Risks first sets 4,000 and the index can seed in its own WARN band. Replace both with *"the Spec-drafted index cap"*. **(Introduced by the revision — fix before Spec.)**
- **O2 — define "entry" in the verification predicate, or the net has a hole.** `:80`'s two halves are *"every top-level `- ` entry appears byte-identical in exactly one shard"* + *"no shard contains text absent from the pre-move file"*. If *entry* = the top-level **line**, a dropped **nested** sub-bullet passes both halves (it isn't a top-level entry, and its absence isn't extra text). **Measured blast radius: exactly one nested sub-bullet exists in the whole ledger** (`docs/claugentic-DECISIONS.md:22`, the *"Grounding — the leanness spirit is official"* child) — and it sits under the very entry being amended, so the real risk is small but the safety net should not depend on that. Cheapest airtight formulation, split-agnostic and trivially scriptable: **the multiset of non-scaffolding lines is identical** — `sorted(lines(pre)) == sorted(concat(lines(shards)) − scaffolding)`, with exactly the enumerated diffs. Prefer it over an entry-block definition.
- **O3 — Affected files no longer says where the two amendments land.** `:61` still reads *"rung-3 entry amended per Approach 6"* (singular) on the **index** line, but both amendments land in **shards** (`doc-lifecycle.md`, `deterministic-gates.md`) and `:62` doesn't mention them. Move/duplicate the note onto `:62`.
- **O4 — three small factual/wording corrections.** (a) `tests/test_check_doc_budgets.py` has **7** test classes, not 8 (`:60`, `:88`) — **my round-1 error, propagated; verified `grep -c "^class Test"` = 7.** (b) Approach 2 `:33` now mixes two byte conventions: nine sizes are section-body-only, while `14,056` and `329` include the `##` heading line (body-only they are 14,032 / 316). Add one clause naming the convention — the sizes are what the "may not seed in its WARN band" rule is judged against. (c) Test strategy `:88` still calls it the *"section-substring script"* while `:92` calls it the *entry-level* check — one name.

### Verified independently this round (saves Verify the re-work)

- **The enumerated pointer list is genuinely complete, not a sample.** A repo-wide sweep for section-targeted `DECISIONS.md →/->/#` references returns exactly: `INVARIANTS.md:51` (*Honesty positioning*) · `standards/README.md:23` (*"Managed docs are adopter-aware"*) · `skills/doctor/SKILL.md:135` + `skills/build/SKILL.md:87` (*The deterministic gates*) · the four `engine/*.js` (*Plugin identity & distribution*) · `tests/conftest.py:6` (dev-only). **All are covered by Acceptance 3** — and the three SHIPPED skill/standards consumers (`standards/README.md:23`, `doctor:135`, `build:87`) are the ones whose one-hop resolution depends on index keywords; hand the implementer that list.
- **The cap numbers now live in three docs** (`DOC_BUDGETS` · `TREE:108` · `DECISIONS:21`). That is pre-existing practice (both doc copies exist today), and `DOC_BUDGETS` remains the single *enforced* source — but the `DECISIONS:21` amendment can only be written **after** the Spec fixes the index cap. Sequence it that way so the three can't land divergent.

### Verified-sound (unchanged from round 1 — no change needed)

- **Scanner invisibility is real, not asserted.** `_paths_in_classes` derives from `DEV_ONLY_FILES` and `recreate_class` returns `None` for dir-swept paths (`scripts/check_shipped_content.py:185-193`, `scripts/build_release.py:152-160`) → a `DEV_ONLY_DIRS` entry is structurally absent from Pass A.a/D. The plan's "model-upheld, no gate covers this" framing (Approach 5 / Risks:81 / Acceptance:95) is **honest and correct** — the register fix landed.
- **The shipped-set byte-identity test survives.** `tests/test_build_release.py:209-221` computes both sides through the **live** `br.DEV_ONLY_DIRS`, so a fifth dir entry moves both sides identically.
- **Path stability preserves the release/init contract.** `docs/claugentic-DECISIONS.md` stays class `init-seed` with its shipped `claugentic-_DECISIONS.md` HAS attestation (Pass D, `check_shipped_content.py:291-324`) — untouched.
- **The path-free "filing rule" clause is adopter-true.** The seed's header does say *"For a genuinely new decision, append a dated one-liner at the top of the relevant section"* (`docs/claugentic-_DECISIONS.md:3`) — Approach 7's both-shapes claim verified.
- **`tests/test_seed_templates.py:63-70` call is right** — the sentinel asserts the *seed* lacks "Honesty positioning"; the index gaining that phrase cannot collide. Comment-only fix, assertion unchanged.
- **Ladder line refs all check out**: WORKFLOW `:172` lever list · `:176` rung 3 (PARKED/not built) · `:178` deferred-lever note; `DECISIONS.md:87` rung-3 line; `DECISIONS.md:23` is the *tree's* "condense now, shard later" (correctly excluded); `ROADMAP.md:44`; `ARCHITECTURE_TREE.md:26`. **CLAUDE.md has headroom** for the routing clause (4,672/6,000 = 78%).

### Sizing / completeness — round 2

- **Slice 1 — session-sized: OK · atomic: OK · lands complete, no debt: OK** (given O1–O4). ~15 files, ~53.7 KB relocated. Now that the move is a **scripted extraction** (`:80`) rather than model-retyped prose, the session cost is dominated by the rewiring, not the payload — comfortably inside one ≤1M session, and the one failure mode that could have run long *and* silently corrupted content is designed out.
- **Do not re-split.** A capability slice with no caller is dead code; any split at the restructure boundary leaves the ledger half-moved with live pointers straddling both shapes. **Nothing here is severable without a half-state** — atomic IS the vertical-completeness guarantee. The intra-session order + interruption-recovery line at `:4` closes the one gap the atomic framing left (mid-move death → `git checkout` + re-run the extractor, never a hand-resume).
- **Two accepted risks, both now named in-plan rather than discovered at Verify:** `plugin-distribution.md` seeds at ~80% of its cap and is the expected first post-land WARN (`:55` — designed remediation, not a miss); and the index's own growth is bounded by rung 2, a recorded cap-bump (`:84`), which is coherent with skipping rung 2 for the rule-book because the content class differs.
- **No new tech debt introduced by the plan as written** — `skills/condense/SKILL.md` decided (no edit), the conditional acceptance hedge is gone, and all nine stale statements are enumerated with a per-statement destination.

### Harness impact (Stage 9)

1. **A recorded stance flips**: WORKFLOW rung 3 moves PARKED/not-built → built-and-climbed — **nine** enumerated statements (`:84`, `:96`), not six. This is the plan's largest harness-doc surface; it is honestly reversed (dated decision + rung-2-skip rationale), not silently contradicted.
2. **Stage-9 harvest — promote the principle, don't leave it dev-only.** *"Bound what an agent READS per consult, not what the harness KNOWS"* is project-agnostic; `:54` now names the promotion into `docs/claugentic-standards/maintainability-structure.md` with the index+shards+per-shard-budget shape as the worked example. That is what makes this reusable by an adopter rather than harness-private. Carry it into the retrospect, don't let it die with the slice.
3. **A new repo-wide authoring rule with no gate** — *"reference the ledger only via the index; never link a shard path directly"*. `:40` now carries it into `CLAUDE.md` → *Harness Discipline* (headroom verified, 4,672/6,000), which is the only place it reaches a writer who never opens the shard dir. Model-upheld; **do not let Verify describe it as enforced.**
4. **Shipped-surface changes** (adopter-facing): `skills/doctor/SKILL.md` (sole owner of the caps-per-shard sentence), the WORKFLOW rung-3 rewrite, and the three path-free agent clauses. Honesty bar for Verify: no literal shard path in a SHIPPED file, no "WARN fires" phrasing, and **no claim that an adopter WARN localizes** — no adopter WARN exists (the gate is stripped).
5. **No new agent/skill/hook** — correct. The `/condense` per-shard branch stays cut (no adopter can be in the sharded state); the doctor **ledger-coherence** roadmap candidate (`docs/claugentic-ROADMAP.md:42`) remains the eventual net for mis-routing, deferred to the post-v0.4.0 holistic eval. The deferred-enforcement posture holds — this slice adds gate *data* and one glob *capability*, nothing hook-wired.

---

## Spec  _(Slice 1 — Stage 4)_

### In plain English (shown first at the approval gate)

- **What this builds:** the decisions rule-book (54K, one file) becomes a small table-of-contents file at the same path plus ten topic files, each with its own size budget the gate checks independently. Every existing pointer keeps working; a consultation reads ~3–14K instead of 54K.
- **What "done" means for you:** all gates green with zero WARNs; a byte-exact line-accounting proves nothing was dropped or reworded (except two lines that would otherwise state falsehoods about this very change, amended and re-dated); the nine places that currently say "sharding isn't built" read true; adopters are untouched (their ledger stays one simple file).
- **What you're accepting:** where a new entry gets filed is model-upheld judgment (the tight index cap + stop-sign are the backstop, doctor's future ledger-coherence check the eventual net); the no-shard-paths-in-shipped-docs rule is model-upheld (no gate can see that dir); `plugin-distribution.md` starts at ~80% and is expected to be the first WARN within a release or two — by design (split it then); rung 2 (cap-bump) is skipped for the rule-book and recorded as a dated decision.

### The drafted index (sets the cap)

```markdown
# Decisions ledger — INDEX

Index only — NEVER append entries here; file into the fitting shard in `docs/claugentic-decisions/`
(no fit → create one — growth is horizontal). Not finding something? `rg docs/claugentic-decisions/`.
All external references point at THIS file — never link a shard path from outside the index.

Read `honesty.md` first — Honesty positioning is the #1 rule.

- [honesty](claugentic-decisions/honesty.md) — Honesty positioning (the #1 rule): [D]/[J] verb discipline; never launder model-upheld into mechanical; the two senses of "independent".
- [deterministic-gates](claugentic-decisions/deterministic-gates.md) — The deterministic gates: tree check · version-sync · doc budgets & caps · shipped-content scanner · one gate, one invariant.
- [verify-roles](claugentic-decisions/verify-roles.md) — The verify/judge roles: skeptical clean-context review, refute-first, same-model tag honesty.
- [audit](claugentic-decisions/audit.md) — The audit: lens fan-out · dedup · finding-verifier · tiered backlog · depth dial · rejected-findings fence.
- [build-mode](claugentic-decisions/build-mode.md) — Build mode: backlog auto-drive, build-to-green, decision-gated autonomy (three stop classes).
- [workflow-process](claugentic-decisions/workflow-process.md) — Workflow/process: stages & gates, carry-forward + mirror-back, methodology toolbox & charter, plan lifecycle, scope-agnostic rule.
- [roles-review](claugentic-decisions/roles-review.md) — Roles & review: roster postures, diverse panel, craft-is-first-class ([J] ceiling), lens coverage, runtime-qa, DoD ownership.
- [doc-lifecycle](claugentic-decisions/doc-lifecycle.md) — Doc lifecycle & condensation: the budgets ladder (bump for logs/index · shard for rule-books), reads-vs-knows principle, Readiness posture.
- [plugin-distribution](claugentic-decisions/plugin-distribution.md) — Plugin identity & distribution: marketplace github-object form, release branch, managed docs are adopter-aware, init/update contracts.
- [release-contract](claugentic-decisions/release-contract.md) — Release contract: build_release single command, ship/strip classes, referential closure, range-diff drop-check, plan-0034 `source.ref` repoint.
```

Measured draft ≈ 2,310 B → **index cap 3,200 B** (seed ≈72%, WARN at 2,880). The implementer may adjust line wording, but every Acceptance-3 keyword above (verbatim section names + entry-level keywords) must survive, and the final seed must land ≤75% of the cap (bump the cap, not the content, if wording grows).

### File-by-file

1. **`scripts/check_doc_budgets.py`** — add `_resolve_targets(rel_path: str, rule: dict) -> list[str]` (no `"glob"` key → `[rel_path]`; `"glob": True` → sorted glob matches; zero matches → error entry; any subdirectory under `docs/claugentic-decisions/` → error). `evaluate()` iterates resolved targets through the **unchanged** `_check_one`; add `REQUIRED_SHARDS: tuple[str, ...]` (the ten seed filenames) with a pure existence check surfaced through `evaluate()`. `DOC_BUDGETS`: drop the 60K entry; add `"docs/claugentic-DECISIONS.md": {"max_bytes": 3200}` and `"docs/claugentic-decisions/*.md": {"max_bytes": 14000, "glob": True}`. OK-summary collapses a glob entry to one clause with a runtime-computed count. Docstring + remediation strings per the register constraint (Approach 4; no "WARN fires" literal anywhere shipped — this file is dev-only but keep the register anyway).
2. **Extractor (scratch, not committed)** — read `git show HEAD:docs/claugentic-DECISIONS.md` bytes; split on `^## ` heading offsets; write shards with `newline=""` + the one-line shard header (Approach 3); `Workflow & roles` partitioned topically: process-rule bullets (edge-skills · dynamic-workflow grounding · methodology · decision-gated autonomy · plan disposition · DoD · Stage 9 · carry-forward · mirror-back · scope-agnostic · enforcement-deferred) → `workflow-process.md`; roster/review bullets (craft · v0.3 re-review · architect-pass · 2a/2b/2c · diverse panel · roster postures · runtime-qa · lens-coverage · product-excellence · CLAUDE.md-home · worktree hygiene · audit-tags · leanness-audit) → `roles-review.md` (final assignment is implementer judgment; both files stay under 14K and no bullet is split internally).
3. **The two amendments** (in the shards, re-dated 2026-07-16): DECISIONS `:87` rung-3 line → built-and-climbed + rung-2-skip rationale + index-rung-2 recourse; `:21` cap-list → index 3,200 + shards 14,000 each.
4. **Rewiring** — exactly as enumerated in Affected files (WORKFLOW ×4 generic corrections pointing at doctor for the caps procedure · doctor's one caps sentence · CLAUDE.md two clauses · implementer/retrospect-harvester path-free filing clauses · synthesizer-gate + retrospect-harvester consult-widening · ROADMAP `:44` amendment · TREE `:26` rewrite + ONE dir line + `:108` cap-list fix · `build_release.DEV_ONLY_DIRS` + shard dir · `test_seed_templates` comment fix).
5. **Tests** — extend `test_check_doc_budgets.py` per Test strategy; new dev-only-classification assertion for the shard dir (case guard) in `test_build_release.py` or sibling.

### In-scope standards dimensions

`maintainability-structure` (structure/seams/one-cap-source) · `docs-traceability` (the nine statements + pointer acceptance list) · `testing` (fixtures-unchanged contract + new cases). Target bar: DoD green + the Acceptance criteria in this plan.

### Acceptance criteria

The five in the plan body (§Acceptance criteria), unchanged.
