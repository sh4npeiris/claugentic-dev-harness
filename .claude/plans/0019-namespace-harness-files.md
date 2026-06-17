# 0019 — Namespace all harness files with a `claugentic-` prefix (v0.1.39)

- **Status:** APPROVED (Slice 1 only) — Slice 2/migration DROPPED. No backward-compat: the harness has been used on one project (data-insights-hub), aligned by hand. Implementing.
- **Resumable from:** implementing Slice 1 (the atomic rename + sweep + gate + init).
- **Blockers:** none — edits the harness *source*; independent of installed plugin version
- **Roadmap item:** `docs/ROADMAP.md` → Standing tracks & later → supersedes the "Agnostic init" tree behavior
- **References:** `docs/ARCHITECTURE_TREE.md` · `docs/DECISIONS.md` · memory `harness-agnostic-update-design` · **supersedes plan 0018** (tree-as-tool) and the 0.1.38 conditional gate

## Problem

Harness-owned files (`docs/WORKFLOW.md`, `docs/ARCHITECTURE_TREE.md`, `docs/standards/*`, `scripts/check_architecture_tree.py`, …) sit at conventional paths an adopter may already use. Today a collision yields the weak `USER_FILE`-skip ("reconcile manually") — the harness file silently isn't installed. Plan 0018 solved *only the tree* via rename-on-collision + a marker, but that (and any approach where the adopter's harness-file path differs from the canonical name) creates a **source-vs-adopter duality**: the `audit`/`build`/`product` skills and the engine JS (`engine/audit.js`, `qa.js`, `build-item.js`, `verify.js`) name harness doc-paths inside the prompts they hand sub-agents, so a path that varies breaks those references in one context.

**The decision:** give every harness-owned file a **uniform `claugentic-` filename prefix, in the source repo *and* in adopters.** Collisions become structurally impossible (no adopter has `claugentic-*` files), the duality vanishes (one set of names everywhere), and `init` copies path-for-path. Measured reference surface: **~337 references across ~53 files** — large but mechanical; the dominant risk is a *missed* reference.

## Goals / Non-goals

**Goals**
- Every harness-owned **adopter-facing** file is `claugentic-`-prefixed, identically in the source repo and in adopters → no collision, no duality, `init` copies path-for-path.
- The harness remains fully self-referential and dogfooded (its own repo uses the prefixed names).
- Existing adopters (data-insights-hub, neesh) migrate cleanly on re-init — old un-prefixed harness-stamped copies are renamed, **user files never touched**.
- Drop 0018's now-moot machinery (marker, rename-on-collision, path-selection, configurable `TREE_PATH` knob).

**Non-goals (guard against creep)**
- **Don't prefix plugin-internal files** — `engine/*.js`, `.claude/agents/*`, `.claude/plans/*`, `scripts/check_versions_synced.py` are read-from-install, **never copied to adopters** → no collision, no duality → keep clean names.
- **No marker / rename-on-collision / path-selection / `TREE_PATH` knob** — a uniform prefix makes all of it unnecessary (`TREE_PATH` becomes a fixed constant = the prefixed path).
- **No overwrite or deletion of user files** — migration only renames files proven harness-owned by their line-1 stamp.

## Approach

A **uniform rename + exhaustive reference sweep**, plus a one-time adopter migration.

### 1. The rename set (source + adopter, identical)
| Category | Files | New name |
|---|---|---|
| **Copied managed docs** (verbatim harness content) | `docs/WORKFLOW.md`, `docs/PLAYBOOK.md`, `docs/ENGINEERING_STANDARDS.md`, `docs/PRODUCT_SPEC_TEMPLATE.md` | `docs/claugentic-<NAME>.md` |
| **Standards collection** | `docs/standards/*` (13 modules + README + _TEMPLATE) | `docs/claugentic-standards/*` (dir-level prefix) |
| **The gate script** | `scripts/check_architecture_tree.py` | `scripts/claugentic-check_architecture_tree.py` |
| **Generated artifact** | `docs/ARCHITECTURE_TREE.md` | `docs/claugentic-ARCHITECTURE_TREE.md` |
| **Seeded / project-content** (harness structure, project content) | `docs/ROADMAP.md`, `docs/DECISIONS.md`, `docs/PRODUCT.md`, `docs/PRODUCT_SPEC.md` | `docs/claugentic-<NAME>.md` — **see Risk R-ORPHAN for the migration caveat** |

**Stays clean (plugin-internal, never in adopters):** `engine/*.js`, `.claude/agents/*`, `.claude/plans/*`, `scripts/check_versions_synced.py`, `docs/RELEASE_CHECKLIST.md` (harness-internal release doc — confirm it's not in the managed set). The harness's own `CLAUDE.md`/`.claude/settings.json`/`.gitignore` are not renamed (they're merge targets), but their **contents** reference prefixed paths.

### 2. The reference sweep (~337 refs / ~53 files)
Every reference to a renamed path updates to the prefixed path, across: `CLAUDE.md`, `README.md`, every `.claude/agents/*`, every `skills/*/SKILL.md` (esp. `init` 47, `build` 17, `product` 14, `audit` 12), every `engine/*.js`, the standards modules' cross-refs, the tests, and the renamed docs' self/cross references (the tree alone has 35). **Grep-driven + verified** (see Test strategy).

### 3. The gate (`scripts/claugentic-check_architecture_tree.py`)
- `TREE_PATH` default → `docs/claugentic-ARCHITECTURE_TREE.md` (a **fixed constant** — uniform everywhere, **not** a per-repo knob; this drops 0018's knob + carve-out + "two-knobs" reconcile entirely; `INCLUDE_GLOBS` stays the only per-repo knob).
- The ~7 hardcoded literal `docs/ARCHITECTURE_TREE.md` strings in messages/docstring (0018 review change 1: `:2,:50,:310,:314,:323,:369,:398`) → use `str(TREE_PATH)` (DRY, single source).
- `INCLUDE_GLOBS = scripts/**/*.py` still matches the renamed `scripts/claugentic-check_architecture_tree.py` (it's `*.py`) → the gate still indexes itself; the tree lists it at the new name.

### 4. init (`skills/init/SKILL.md`)
- Managed-set table → prefixed paths; **copy path-for-path** (source is prefixed → no transform).
- Seeding (ROADMAP/DECISIONS/PRODUCT*) → prefixed paths.
- Hook command → `…/scripts/claugentic-check_architecture_tree.py`; idempotency key substring → `claugentic-check_architecture_tree.py`.
- CLAUDE.md fence/manifest → names the prefixed paths.
- **Delete** 0018-superseded machinery if any survived in the working tree (none landed — 0018 was a plan); the gate is unconditional (always on); the genuinely-empty-repo `INCLUDE_GLOBS=[]` case stays.

### 5. No migration — fresh adoption only (no backward-compat)
The harness has been used on **one** project (data-insights-hub); the neesh repos were never init'd (they keep their own docs). So **init carries NO migration logic** — it only ever writes the prefixed names. The single existing adopter is aligned **by hand** (delete its old un-prefixed harness copies; a re-init creates the prefixed set). This drops the stamp-rename, the hook-rewrite, and the R-ORPHAN handling entirely (YAGNI — no real adopters to be backward-compatible with).

**Alternatives rejected:** source-clean + init-prefix-transform (the duality — *why this plan prefixes the source*); 0018 tree-as-tool (only the tree; same latent duality for engine refs); format-tolerant gate; keep-gate-off tier.

## Affected files
Effectively the whole harness doc/skill/engine surface (~53 files, ~337 refs). Concentrations: `skills/init/SKILL.md` (managed-set + hook + manifest + migration), `scripts/check_architecture_tree.py` (rename + TREE_PATH + literals), the renamed docs + their self/cross-refs, `engine/{audit,build-item,verify,qa}.js`, `skills/{build,product,audit}/SKILL.md`, the `.claude/agents/*`, `CLAUDE.md`, `README.md`, the tests, `.github/workflows/ci.yml`, `.claude-plugin/{plugin,marketplace}.json` (→ 0.1.39 lockstep).

## Research / grounding
- **Reference surface (grep, 2026-06-16):** 370 hits / 55 files for the renamed-path tokens (≈337 excluding the 0018 draft + generic TEMPLATE mentions). Per-file: `init` 47, `ARCHITECTURE_TREE.md` self 35, `WORKFLOW.md` self 23, `build` 17, `product` 14, `test_check_architecture_tree.py` 13, `audit` 12, standards modules + agents + engines the remainder.
- **Source-vs-adopter duality (architect map):** the `audit`/`build`/`product` skills + `engine/*.js` name adopter doc-paths in sub-agent prompts (`engine/audit.js:305,:483`, `qa.js:856`, `build-item.js:557`, `verify.js:106`) — the reason the prefix must apply to the source too.
- **Stamp is path-independent:** the genuine-managed predicate keys on line-1 stamp + path-in-set; renaming the file doesn't affect the stamp → migration-by-rename is safe + body-compare is path-agnostic.

## Risks & mitigations
- **R-MISS — a missed reference** (the dominant risk at 337 refs). Mitigation: per-path grep-and-replace; a **pre-land grep that must return zero** un-prefixed references to any renamed path (outside generic TEMPLATE/historical prose); the tree-gate (catches a stale tree); the full test suite (catches broken paths in skills/engines); the architect-reviewer.
- **R-ORPHAN — N/A** (no migration). The seeded/project-content files (ROADMAP/DECISIONS/PRODUCT*) are simply `git mv`'d in the harness's own repo; there is no existing-adopter orphan to handle.
- **R-DOGFOOD — the harness's own tree-gate** must stay green through the rename (the tree file moves + re-indexes every renamed path). Land the tree update in the same atomic change.
- **R-VERSIONS — version-sync:** bump `plugin.json` + `marketplace.json` together; `check_versions_synced.py` enforces.
- **Re-init convergence (not a regression):** the *first* 0.1.39 re-init on an old adopter is a migration (renames + refreshes + hook rewrite + orphan report) — a deliberate one-time change; the *second* is byte-identical.

## Test strategy
- **Pre-land grep (the safety net):** zero un-prefixed references to any renamed path remain (allow-list only generic TEMPLATE/historical prose). This is the gate against R-MISS.
- **The harness's own gates green after the rename:** `python scripts/claugentic-check_architecture_tree.py` (the renamed gate, enforcing the renamed tree) passes; `check_versions_synced` passes; the full `tests/` suite (pytest + node `tests/workflows/*`) green — these exercise the skills/engines and will fail on a broken path.
- **Dogfood:** run `init` on a throwaway repo → all harness files land prefixed, gate green, manifest names prefixed paths; a planted old-style adopter (un-prefixed stamped `docs/WORKFLOW.md`) → migrated (renamed) on re-init, a planted user `docs/WORKFLOW.md` (no stamp) → untouched.
- **Reviewers:** `architect-reviewer` (completeness of the sweep, no dangling refs), `honesty-reviewer` (the migration/orphan report wording), `yagni-sentinel` (confirm plugin-internal files stayed clean + no 0018 machinery crept in).

## Decomposition (slices)
- [ ] **Slice 1 — The rename + sweep + gate + init (atomic core).** Rename the source rename-set; exhaustively update all ~337 references; update the gate (filename, `TREE_PATH` constant, `str(TREE_PATH)` messages); update the harness's own `.claude/settings.json` hook + the regenerated tree; update `init`'s managed-set to the prefixed paths (copy path-for-path) + hook command + manifest + idempotency key; version bump. **Atomic** — a half-done rename breaks the gate and every cross-reference; it must land green in one pass. Verified by the pre-land grep + the full gate/test suite.
- ~~Slice 2 — Existing-adopter migration~~ **DROPPED** — no backward-compat (single existing adopter aligned by hand). init writes only the prefixed names.

---

## Review  _(filled by plan-reviewer, Stage 3)_

**RUNNING AS: Opus 4.x** — same-model review on this run if the builder is also an Opus-family model; the orchestrator should tag accordingly. A cross-model panel (`yagni-sentinel` + `honesty-reviewer`) is warranted here given the size and the migration's never-clobber/honesty surface.

- **Verdict:** **CHANGES REQUIRED** — the engineering approach is sound and the slicing is right, but the **reference-sweep token set is demonstrably incomplete**: I found four distinct missed-reference classes by grep against the live tree, any one of which would silently break a renamed path. The product decision is not contested; these are completeness gaps the spec must absorb before Slice 1 is implementable.

- **Required changes:**

  1. **`PRODUCT.md` is in the rename set (table line 39) but absent from the sweep token list.** It is referenced in **8 files / 15 occurrences** (`skills/product/SKILL.md:40`, `.claude/agents/product-designer.md:3,10,22,24` — the agent *persists* to `docs/PRODUCT.md`, `.claude/agents/product-critic.md`, `docs/WORKFLOW.md`, plus the docs themselves). The stated token set only carries `PRODUCT_SPEC`. **Add `PRODUCT.md` as an explicit sweep token** (and a `PRODUCT_SPEC_TEMPLATE` token distinct from `PRODUCT_SPEC` — the underscore-less basename appears in `tests/test_product_spec_template.py:1`). Also resolve the **categorization question the task flagged:** `PRODUCT.md` is *generated by the `product-designer` agent in adopters* (adopter-facing, like `PRODUCT_SPEC.md`), so prefixing it is consistent — but then **the agent's persist-target string and read-target at `product-designer.md:10,22` must be updated too**, or the agent will write `docs/PRODUCT.md` while the rest of the harness reads `docs/claugentic-PRODUCT.md` (a new duality — exactly what this plan exists to kill). State this explicitly in the spec.

  2. **The `docs/standards` token MISSES the bare-`standards/` relative-link form.** `docs/ENGINEERING_STANDARDS.md:3,5` links the catalog as **`[…](standards/README.md)`**, `(standards/_TEMPLATE.md)` — **no `docs/` prefix** (markdown relative links resolve from the file's own dir). A literal `docs/standards` grep-and-replace does **not** touch these, and after the dir becomes `docs/claugentic-standards/` those links 404. **Add a bare `standards/` sweep token** and audit every relative markdown link in the renamed docs (the standards `README.md` similarly uses bare `_TEMPLATE.md`, `WORKFLOW.md`, `DECISIONS.md`, `CANDIDATES.md` relative links — confirm each resolves post-rename, since the dir prefix changes the relative base for links *inside* `claugentic-standards/` too).

  3. **A filesystem directory-read is not text-grep-reachable and will break the gate-test.** `tests/workflows/verify.test.mjs:23` reads the real dir via `join(REPO_ROOT, "docs", "standards")` (separate string args — a `docs/standards` grep never matches it) to mechanically pin `KNOWN_MODULES` against the on-disk `docs/standards/*.md` basenames (test at `:100`). Renaming the dir without updating this `join(...)` makes the set-equality pin fail or read an empty dir. **The spec must list `tests/workflows/verify.test.mjs` line 23's path-join explicitly** and search for the `"docs", "standards"` / `'docs','standards'` join form, not only the slash form. (The runtime path-builders `engine/verify.js:106` and `engine/audit.js:305` use the `docs/standards/${slug}.md` slash form and *are* caught — but call them out as load-bearing: they construct the prompt paths the lens sub-agents read.)

  4. **The pre-land "zero un-prefixed references" grep needs a real allow-list spec, because `ARCHITECTURE_TREE` appears as a CONCEPT, not only a path.** `docs/standards/docs-traceability.md:24` is a heading `## ARCHITECTURE_TREE.md currency` and `:29`/`:30` use `ARCHITECTURE_TREE` as a discipline name in prose. These are *conceptual* references that should arguably stay readable (an adopter reading "claugentic-ARCHITECTURE_TREE.md currency" as a heading is odd), yet the dominant-risk grep ("zero un-prefixed references to any renamed path") will flag them. **The spec must decide, per-token, which occurrences are filepath references (rename) vs prose/heading concept-names (leave), and encode that as the grep's allow-list** — otherwise the safety net either produces false positives that get waved through (defeating the net) or over-renames headings. This is the single most important spec deliverable for R-MISS.

  5. **Minor mis-statement to correct (the plan claims to enumerate the set precisely).** Table line 36 says standards = "13 modules + README + _TEMPLATE" — there are **11 authored modules + `_TEMPLATE.md` + `README.md` = 13 files total** (verified: `docs/standards/*.md` is exactly 13 files). The init managed-set table (`skills/init/SKILL.md:109`) already says "11 authored modules" — align line 36 to it (DRY with the source of truth, and the wrong count erodes trust that the set was actually counted).

  6. **Confirm-or-resolve the two categorization spot-checks (both currently land correctly — record the verdict so it isn't re-litigated):** `docs/RELEASE_CHECKLIST.md` is **NOT** in the init managed set (`skills/init/SKILL.md:109-115`) — correctly excluded as plugin-internal; keep it clean. `eval/**` carries **zero** references to any renamed path (verified) and is never copied to adopters — correctly untouched. State both as settled in the spec so a later sweep doesn't second-guess them.

- **Sizing/completeness:**
  - **Slice 1 (rename + sweep + gate + init) — OK as atomic, NOT splittable.** I agree with the plan's atomicity claim and it is load-bearing, not hand-waving: a half-rename leaves the tree-gate red (the renamed gate enforces the renamed tree, which must list the renamed gate script — a chicken-and-egg that only closes in one pass) and breaks the `engine/*.js` prompt-path builders + the `verify.test.mjs` dir-read simultaneously. A "docs-first, gate-second" sub-split would leave the repo gate-red between slices (debt + a non-landable intermediate state) — it FAILS the vertical-complete rule, so do **not** split it. The one-session feasibility holds *because* it's mechanical grep-and-replace; the risk is breadth, not depth — which is why findings 1–4 (making the sweep genuinely exhaustive) are the gate, not the slice count. The pre-land-grep-zero net is the right safety mechanism **only once finding 4 gives it a real allow-list**; as written it is under-specified.
  - **Slice 2 (existing-adopter migration) — OK, cleanly dependent on Slice 1.** The stamp-line-1 discriminator is airtight for the *stamped* managed copies (path-in-set + line-1 stable prefix → rename old→prefixed is safe; a no-stamp file is never touched — consistent with the genuine-managed predicate at `skills/init/SKILL.md:126-158`). The hook-command rewrite (line 60) correctly *rewrites* rather than skips — necessary, since the old hook points at the un-prefixed `check_architecture_tree.py` and would otherwise run a now-missing script. **One completeness gap to add:** Slice 2 must also handle the **`INCLUDE_GLOBS` carve-out under the new gate filename** — when migrating an adopter's `scripts/check_architecture_tree.py` → `scripts/claugentic-check_architecture_tree.py`, the REFRESH must still re-inject the adopter's existing `INCLUDE_GLOBS` (the hybrid-file rule at `skills/init/SKILL.md:179-201`), and the body-compare carve-out must key on the new path. Confirm the migration is a `git mv` + re-stamp, not a delete+create that would drop the adopter's globs.
  - **R-ORPHAN default (loud-report, don't auto-move) is the right non-destructive call** and consistent with the project's established "never overwrite/move a user file without explicit confirmation" posture (DECISIONS → Plugin identity, the Replace-is-confirmed-overwrite precedent). The fence-migrate option is sound *as an opt-in*. Keep it flagged as the spec's main open decision, as the plan does.

- **Harness impact:**
  - **A new DECISIONS.md entry is required at Land** (Plugin identity & distribution section): "every harness-owned adopter-facing file carries a uniform `claugentic-` prefix in source AND adopters; plugin-internal files (`engine/*.js`, `.claude/agents/*`, `scripts/check_versions_synced.py`, `docs/RELEASE_CHECKLIST.md`) stay clean" — this supersedes the 0.1.38 conditional-gate / 0018 tree-as-tool decisions, which the plan correctly flags. Without it the rationale is lost and a future agent re-opens the source-vs-adopter duality.
  - **A Stage-9 STANDARD candidate (docs-traceability or a new "managed-file naming" note):** the lesson "a managed file's name is part of its contract — prefix it so adopter-path collisions are structurally impossible" is universal (any future managed file must be born prefixed). Capture it so `init`'s managed-set table and any new managed file inherit the rule mechanically, not by memory. Pair this with the **paired-or-explicitly-not fence-convention lesson** already in DECISIONS (audit section) — the same class of "every reference must be swept" discipline.
  - **No new agent needed.** The existing `architect-reviewer` (sweep completeness) + `yagni-sentinel` (confirm plugin-internal stayed clean) + `honesty-reviewer` (migration/orphan-report wording) panel the plan names is the right set.
  - **`.github/workflows/ci.yml:64` is correctly in scope** (it invokes `python scripts/check_architecture_tree.py`) — confirm the spec lists the CI rename, since a missed CI reference would not be caught by the harness's own gate-run (CI would just fail on the next push). `TREE_PATH` → fixed constant `docs/claugentic-ARCHITECTURE_TREE.md` is sound (no per-repo variation survives once source+adopter names match), and `INCLUDE_GLOBS = :(glob)scripts/**/*.py` still matches the renamed `scripts/claugentic-check_architecture_tree.py` (it's `*.py`), so the gate self-indexes — both confirmed correct.

---

## Spec  _(per slice, after Review passes — Stage 4)_

> All six plan-review Required Changes are folded in. The load-bearing deliverable is the **exhaustive sweep methodology** (the dominant risk is a missed reference); the pre-land grep is only a real safety net once its per-token allow-list is decided (RC4).

### Slice 1 — The rename + sweep + gate + init (atomic; un-splittable)

- **In plain English (the approval gate):**
  - **What this builds:** every harness-owned adopter-facing file gets a `claugentic-` prefix — in the harness's own repo *and* in adopters — so harness files can never collide with yours and the skills/engines reference one set of names. `init` then just copies path-for-path.
  - **What "done" means:** the harness's own repo is green under the renamed gate; a clean adopter gets all-prefixed harness files; the pre-land grep finds zero un-prefixed *filepath* references.
  - **What you're accepting:** a large one-time mechanical change (~337 references across ~53 files); the harness's own docs now carry the prefix (e.g. `docs/claugentic-WORKFLOW.md`); this supersedes the 0.1.38 conditional gate and the 0018 tree-as-tool approach.

- **The rename set** (`git mv` each — preserve history; source + adopter identical): `docs/{WORKFLOW,PLAYBOOK,ENGINEERING_STANDARDS,PRODUCT_SPEC_TEMPLATE,ARCHITECTURE_TREE,ROADMAP,DECISIONS,PRODUCT,PRODUCT_SPEC}.md` → `docs/claugentic-*.md`; `docs/standards/` → `docs/claugentic-standards/` (dir-level; **11 authored modules + `_TEMPLATE.md` + `README.md` = 13 files** — RC5); `scripts/check_architecture_tree.py` → `scripts/claugentic-check_architecture_tree.py`. **Settled-excluded (RC6):** `docs/RELEASE_CHECKLIST.md` (not in the managed set — plugin-internal), `engine/*.js`, `.claude/agents/*`, `.claude/plans/*`, `scripts/check_versions_synced.py`, `eval/**` (zero renamed-path refs) — all stay clean.

- **The exhaustive sweep — the expanded token set (RC1–3):** grep-and-replace each *filepath* occurrence. Tokens MUST include, beyond the original set: **`PRODUCT.md`** (15 occ / 8 files — RC1), **`PRODUCT_SPEC_TEMPLATE`** + the underscore-less basename `product_spec_template` (`tests/test_product_spec_template.py:1`), **bare `standards/`** (relative markdown links — RC2), and the **path-`join` form** `"docs", "standards"` / `'docs','standards'` (RC3). Special-form targets the slash-grep misses:
  - **RC1 — the product-designer agent's write/read target:** `.claude/agents/product-designer.md:10,22` *persists to* `docs/PRODUCT.md` — update to `docs/claugentic-PRODUCT.md`, or the agent writes one name while the harness reads another (a new duality). Same for any read of `PRODUCT_SPEC.md`.
  - **RC2 — bare relative links:** `docs/ENGINEERING_STANDARDS.md:3,5` link `(standards/README.md)`, `(standards/_TEMPLATE.md)` (no `docs/`). Audit every relative markdown link in the renamed docs, **including links *inside* `claugentic-standards/`** whose relative base shifts with the dir rename (the standards `README.md`'s bare `_TEMPLATE.md`/`WORKFLOW.md`/`DECISIONS.md` links).
  - **RC3 — the test dir-read:** `tests/workflows/verify.test.mjs:23` `join(REPO_ROOT, "docs", "standards")` pins `KNOWN_MODULES` against on-disk basenames (assert at `:100`) — update the join. The runtime builders `engine/verify.js:106` + `engine/audit.js:305` (`docs/standards/${slug}.md`) are caught by the slash-grep but are load-bearing (they build the lens sub-agents' prompt paths) — verify explicitly.
  - **CI:** `.github/workflows/ci.yml:64` invokes `python scripts/check_architecture_tree.py` → prefixed (a missed CI ref isn't caught by the harness's own gate-run — only by a red CI on the next push).

- **The filepath-vs-prose allow-list (RC4 — the most important R-MISS deliverable):** for each occurrence of a renamed token, decide **filepath reference → prefix** vs **prose/heading concept-name → leave**. Known concept-name occurrences to leave (or rephrase to a generic "the architecture-tree index"): `docs/claugentic-standards/docs-traceability.md` heading `## ARCHITECTURE_TREE.md currency` + the discipline-name uses at `:29,:30`; generic examples in `.claude/plans/TEMPLATE.md`. **Record the leave-set as the explicit allow-list** so the pre-land grep ("zero un-prefixed *filepath* references") is meaningful and not waved through.

- **The gate** (`scripts/claugentic-check_architecture_tree.py`): `TREE_PATH` → fixed constant `Path("docs/claugentic-ARCHITECTURE_TREE.md")` (no per-repo knob, no carve-out — `INCLUDE_GLOBS` stays the only per-repo knob); the ~7 message/docstring literals (`:2,:50,:310,:314,:323,:369,:398`) → `str(TREE_PATH)` (DRY). `INCLUDE_GLOBS = :(glob)scripts/**/*.py` still matches the renamed script (`*.py`) → self-indexes.

- **init** (`skills/init/SKILL.md`): managed-set table → prefixed targets (copy path-for-path); seeding → prefixed; the hook command + the idempotency-key substring → `claugentic-check_architecture_tree.py`; the CLAUDE.md fence/manifest → prefixed paths.

- **The harness's own setup:** regenerate `docs/claugentic-ARCHITECTURE_TREE.md` (re-indexing every renamed path); update `.claude/settings.json`'s hook command to the renamed gate; bump `.claude-plugin/{plugin,marketplace}.json` → 0.1.39 (lockstep).

- **Verification (the safety net for a change this size):**
  - **Pre-land grep returns zero** un-prefixed *filepath* references to any renamed token (per the RC4 allow-list).
  - `python scripts/claugentic-check_architecture_tree.py` green (renamed gate enforces the renamed tree, which lists the renamed gate).
  - `python scripts/check_versions_synced.py` green; full `tests/` (pytest + node `tests/workflows/*`) green — these exercise the skills/engines and fail on a broken path.
  - Dogfood: `init` on a throwaway repo → all harness files land prefixed, gate green, manifest prefixed.
  - Reviewers: `architect-reviewer` (sweep completeness, zero dangling refs), `yagni-sentinel` (plugin-internal stayed clean), `honesty-reviewer` (manifest wording).

- **Acceptance criteria:**
  - [ ] Every rename-set file is `git mv`-renamed (source); every plugin-internal file stays clean.
  - [ ] Pre-land grep: zero un-prefixed *filepath* references (per the recorded allow-list); the product-designer write-target, the bare `standards/` links, and the `verify.test.mjs` join are all updated.
  - [ ] Gate: `TREE_PATH` is the fixed prefixed constant; messages use `str(TREE_PATH)`; the gate self-indexes.
  - [ ] The harness's own gate + full test suite + CI-equivalent all green; `plugin.json`+`marketplace.json` at 0.1.39.

### Slice 2 — DROPPED

No migration / backward-compat (single existing adopter aligned by hand). `init` writes only the prefixed names; it carries no stamp-rename, hook-rewrite, or orphan-handling logic.

> **At Land:** add a `docs/DECISIONS.md` entry (Plugin identity & distribution) — "every harness-owned adopter-facing file carries a uniform `claugentic-` prefix in source AND adopters; plugin-internal files stay clean — supersedes the 0.1.38 conditional-gate / 0018 tree-as-tool decisions." Consider a docs-traceability/standards note that **a managed file's name is part of its contract — born prefixed** (so future managed files inherit the rule). (Plan-review Harness-impact.)
