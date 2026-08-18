# 0042 — Shard `docs/claugentic-WORKFLOW.md` (escape-valve rung 3)

- **Status:** Draft — **not yet through Stage 2b/3.** Everything below the *Research / grounding*
  section is a **proposal for 0042's own draft pass**, not an approved design.
- **Resumable from:** Stage 2a — draft the plan proper from the grounding below (it is measured,
  so do **not** re-derive it; re-measure only what this file marks as "measure again at draft").
- **Blockers:** none.
- **Flags:** none.
- **Disposition at close:** per `docs/claugentic-WORKFLOW.md` → *Plan file lifecycle*.
- **Roadmap item:** `docs/claugentic-ROADMAP.md` → Later / Ideas → "Plan 0042 — shard
  `docs/claugentic-WORKFLOW.md`".
- **References:** `docs/claugentic-DECISIONS.md` (→ doc-lifecycle: the escape-valve ladder, the
  cap-band rule, and the rung-3 decision this plan discharges) · plan 0040 (the decisions-ledger
  shard — the precedent, and the ways this differs from it).

## Problem

`docs/claugentic-WORKFLOW.md` is **87,215 B** (`wc -c`, head of `feat/0041-s12b-close`) and is the
**one large managed doc absent from `.claude/claugentic-doc-budgets.json`** — nothing has ever
bounded its growth. Plan 0041 Slice 12 tried to fix that by pairing a 70,000 B cap with a hard
≤ 56,000 B condensation AC; that AC was **measured impossible** and withdrawn (the full density
lever list sheds 21,000–25,400 B, landing 64,900–69,200 B — above the 63,000 B WARN line of the
cap it was meant to satisfy, i.e. permanent WARN on day one). The user chose **escape-valve
rung 3 — shard it** (2026-08-18). 0041 S12b landed the two sanctioned density cuts and recorded
the decision; **this plan owns the split and the cap.**

Why rung 3 rather than rung 2 (a recorded cap-bump): WORKFLOW is a **rule-book**, not a log — its
entries persist by design, so every condensation pass lands higher than the last and a bump only
defers. That content-class distinction is the ladder's own rationale
(`docs/claugentic-DECISIONS.md` → doc-lifecycle).

## Goals / Non-goals

- Goal: a **thin routing index at the original path** `docs/claugentic-WORKFLOW.md` + one file per
  topic under `docs/claugentic-workflow/`, each under a cap declared in the caps config.
- Goal: **every external reference keeps pointing at the index path** — nothing outside has to
  learn the parts (this is what bounds the blast radius; see *Approach*).
- Goal: the release/init contract carries the new directory, with no adopter-visible regression.
- **Non-goal: a semantic rewrite.** Content moves; meaning does not. (Density work is 0041's
  ledger, already closed — do not re-open it here.)
- **Non-goal: changing what any rule says.** A shard boundary that would require rewording a rule
  is the wrong boundary.

## Approach (PROPOSED — 0042's Stage 2/3 decides)

**The routing contract is the load-bearing choice, and it is contested.** Two shapes exist in this
repo already:

- **Index-only routing** (the decisions ledger, plan 0040): external pointers name **the index
  path only**, never a shard. `CLAUDE.md` states this as a standing rule — *"Reference the
  decisions ledger only via `docs/claugentic-DECISIONS.md` … never link one of its shards
  directly."* Cost: one extra hop for a reader. Benefit: a future re-split is cheap, and the
  **blast radius of this plan stays ~10 files instead of ~50** (see *Research* for the measured
  counts behind that).
- **Direct-module linking** (the standards catalog): `docs/claugentic-ENGINEERING_STANDARDS.md` is
  a 1,455 B entry point and callers link `docs/claugentic-standards/<module>.md` directly.

They are not interchangeable, and **the DECISIONS rule — not the standards-catalog shape — is the
one to apply here**: WORKFLOW's citations are overwhelmingly *anchored* (`… → Definition of Done`,
`… → Plan file lifecycle`), so direct linking would rewrite ~100 pointers now and again at every
future boundary change. Recommend **index-only routing**; take it to the plan-gate as a decision,
not an assumption. Whichever wins, the index stays **routing-only under a tight cap of its own** —
an index that starts holding entries has quietly become the ledger again.

## Architecture & holistic fit

- **Codebase fit** — this is the *same* structural move the decisions ledger already made (index +
  topic files under a shared per-shard glob cap), applied to a second content class. Reuse that
  shape; do not invent a second one. The index↔shards agreement test from 0041 S4
  (`docs/claugentic-decisions/` — both directions fail independently) is the pattern to copy for
  the new directory.
- **Product fit** — an adopter reads WORKFLOW to answer one question at a time ("do I need the
  full pipeline?", "what does done mean?"). Bounding **what an agent reads per consult, not what
  the harness knows** is the principle the ladder encodes; the index must make the routing obvious
  in one screen.
- **Quality dimensions to uphold** — `docs-traceability` (every moved anchor still resolves; the
  index is a locator, never a second source of truth) · `maintainability-structure` (the shard
  boundaries are the real design work) · `testing` (the pins below must be *moved*, not deleted) ·
  `honesty` (the release/init copy must say what actually ships).
- **Future-proofing** — new stages/sections land in a shard, not in the index. Keep the index's
  cap tight enough that "just put it in the index" is uncomfortable.

## Research / grounding (MEASURED — do not re-derive)

All figures measured on `feat/0041-s12b-close` at head, after 0041 S12b's two density cuts.

**Section sizes** (`## `-delimited, bytes incl. the section's own trailing blank line):

| Section | Bytes |
|---|---|
| front matter (title · "New here?" banner · adopter note · one-line map) | 5,543 |
| `## 0. Triage` | 2,900 |
| `## Principles` | 8,284 |
| `## Context & handoff` | 464 |
| `## Roles` (incl. `### Why the multi-agent shape`) | 5,157 |
| `## The pipeline` | **21,822** |
| `## Definition of Done` | 10,836 |
| `## Decision-gated autonomy` | 4,974 |
| `## The finder pipeline` | 9,661 |
| `## Executing an audit backlog item` (incl. the methodology toolbox) | 5,667 |
| `## Bundled edge-skills` | 3,440 |
| `## 9. The learning loop` | 4,939 |
| `## Plan file lifecycle` | 3,529 |
| **total** | **87,215** |

**The binding constraint this table exposes:** `## The pipeline` alone is **21,822 B**. No 7-way
grouping of these sections keeps every shard under a decisions-ledger-style 14,000 B cap unless
**the pipeline itself splits** — its own `FRAME → APPROVE → BUILD → CLOSE` beats are the natural
seam, and they are already named in the document. Decide *cap first, then grouping*: an index of
~11,400 B (front matter + Triage + Context & handoff + the routing table) leaves **~78,300 B**
across the shards, i.e. ~11,200 B mean over 7 — workable only if no shard is much above the mean.

**Blast radius** (`git grep -o` / `-l` over `git ls-files`, so no worktree leakage):

- **122** occurrences of the literal path `claugentic-WORKFLOW.md` across **37** tracked files.
- **98** across **36** files excluding `.claude/plans/` (plan files are deleted at close, so that
  is the number the change actually owes).
- Under **index-only routing**, most of those are *already correct* — they name the index path.
  The files that must change are the ones that would need a shard path: re-derive that set at
  draft with `git grep -n "claugentic-WORKFLOW.md" -- $(git ls-files)` and classify each hit as
  *index-only* (no change) vs *anchored-into-a-shard* (change). **Measure again at draft** — this
  ratio is what turns ~10 files into ~50 if the routing contract flips.

**Mechanically-pinned assertions that break on the split** — all in
`tests/test_adopter_pointer_integrity.py`. Note there are **four**, in two classes (an earlier
grounding pass said "three"; the corpus scan and the within-file count are separate assertions):

1. `TestWorkflowAdopterNoteComesFirst::test_both_headings_exist` — both the adopter-note heading
   and a `## 0.` stage heading exist **in WORKFLOW.md**.
2. `…::test_the_adopter_note_precedes_the_first_stage_heading` — the note precedes the first
   `## 0.` heading. **If `## 0. Triage` moves to a shard, the anchor this pin is defined on leaves
   the file** — decide deliberately whether Triage stays in the index (recommended: it is the
   reader's first question) or the pin is re-anchored.
3. `TestWorkflowNamesTheUpstreamChannel::test_the_channel_is_named_exactly_once` — the plugin repo
   URL appears **exactly once inside WORKFLOW.md**. It currently lives in *The learning loop*, so
   a `learning-loop` shard takes the URL with it and this pin must follow.
4. `…::test_no_other_shipped_prose_repeats_the_url` — the corpus scan asserting
   `offenders == [WORKFLOW_PATH]` over every tracked `*.md`. After the split the sole home is a
   **shard**, so this assertion's expected value changes; keep it a one-home assertion, do not
   loosen it to "one or more".

**Caps + config.** `.claude/claugentic-doc-budgets.json` gains **one** key — a
`docs/claugentic-workflow/*.md` glob (a shape, zero-match-safe, needing no edit per new shard) —
plus a tight cap for the index. **Two files move together:** this repo also pins its caps
**byte-exactly** at `tests/test_check_doc_budgets.py` →
`TestProductionConfig::test_the_migrated_caps_are_exactly_the_five_entries` (~`:1167`), a
deliberate drift-detection pin; a harness-self cap change updates it in the same commit.
**The cap must be picked by the band, never by the measurement** — `docs/claugentic-DECISIONS.md`
→ doc-lifecycle, *Setting a NEW cap*, and read its corrected worked case first: it is this very
document's failed attempt.

**Release/init contract — the finding that shrinks this plan.** *"It ships"* is **not** an
obstacle, and no build script needs changing:

- The harness has **already** sharded a shipped, `init`-delivered rule-book: the standards
  catalog. `docs/claugentic-ENGINEERING_STANDARDS.md` is a thin entry point; 11 modules live in
  `docs/claugentic-standards/` and are delivered by a **single directory row** in the managed-set
  table at `skills/init/SKILL.md` (the `docs/claugentic-standards/` row).
- `scripts/build_release.py` needs **no** change — a tracked directory ships by default-include;
  `docs/claugentic-decisions/` is dev-only precisely because it is listed in `DEV_ONLY_DIRS`, and
  `docs/claugentic-workflow/` simply is not.
- `scripts/check_shipped_content.py` Pass D (dangling references to stripped-uncreated paths) is
  unaffected for the same reason.

So the init-side work is **one directory row** in the managed-set table plus the full-copy-doc
kind it inherits — not a per-shard delivery list. **Confirm both by reading those two scripts at
draft** (this is a read-and-confirm, not an assumption).

## Risks & mitigations

- **A pointer sweep that closes on the author's site list, not on the retired string** → assert
  the retired path/anchor forms return **zero** over `git ls-files`, frontmatter included (a
  shipped `description:` is a capability surface). This is ROADMAP gate item (h).
- **The index quietly becoming the ledger again** → a tight index cap, plus the index↔shards
  two-direction agreement test.
- **A merge measuring differently from either branch** → measure the ledgers on the **merge tree**
  (`git merge-tree --write-tree` + materialize + run the real gate), per WORKFLOW → Land.
- **Adopter churn** — a re-`init` replaces one managed file with a directory. Confirm the
  never-clobber upsert and the stale-single-file case (an adopter whose `docs/` still holds the
  pre-split monolith) are both handled, and say plainly which one `init` does.

## Test strategy

Move-don't-delete for all four pointer-integrity pins above · a two-direction index↔shards
agreement test (every routed shard exists; every shard file is routed) · the byte-exact caps pin
updated in the same commit as the config · the existing full battery green
(`python -m pytest -q` · `node --test tests/workflows/*.test.mjs` · `ruff` ·
`check_versions_synced` · `claugentic-check_doc_budgets` **zero WARN** · `check_shipped_content` ·
`claugentic-check_architecture_tree`).

## Decomposition (slices) — PROPOSED

- [ ] **Slice 1** — decide + record the routing contract and the cap/grouping (a Stage-2/3
      decision, not an implementation), including whether `## The pipeline` splits by its beats.
- [ ] **Slice 2** — create `docs/claugentic-workflow/` + move the content verbatim; index in
      place; caps config + byte-exact pin; the agreement test.
- [ ] **Slice 3** — the pointer sweep + the four pinned assertions re-homed, closed on the
      retired string.
- [ ] **Slice 4** — release/init: the managed-set directory row + the adopter re-`init` path.

---

## Review  _(filled by synthesizer-gate in its plan-gate altitude, Stage 3)_
- **Verdict:** _not yet reviewed_
