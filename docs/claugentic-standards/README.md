# Engineering Standards — Catalog

The multi-lens quality bar as **scoped modules**, anchored to **ISO/IEC 25010:2023**. A module loads only when a change touches its concern (its `load_scope`), so the catalog can grow toward "every standard we can think of" without bloating any single review.

- **Entry point:** `docs/claugentic-ENGINEERING_STANDARDS.md` (thin). **Module contract + authoring rules:** `_TEMPLATE.md`.
- **Who uses it:** the spec (Stage 4) names the in-scope dimensions; `implementer` builds to them and self-applies their *Auditor checks* before handing off; `lens-reviewer` / `synthesizer-gate` audit against them (`docs/claugentic-WORKFLOW.md` → Definition of Done).
- **The roster is this directory.** Each module's ISO characteristic, `load_scope` and `status` live in its own frontmatter — read them there, so no index can drift. All are `draft` today.
- **Reserved — named, no file yet** (authored just-in-time when pulled in): `architecture-styles` (Flexibility) · `capabilities/` (Redis, queues, object-storage, third-party-apis, sidecars, ml, search).

## Reading a module

Every `##` heading is one **auditable dimension**. The core bullets, where each carries weight:

- **Good looks like —** the target state, present **only** where it carries something the heading and the checks do not: a threshold, a named primitive, a house preference. Absent on the many dimensions where the name already says it.
- **Auditor checks —** *the bar the reviewer applies*, as a **checklist**: ` · `-separated clauses, each carrying **exactly one** tag — `[D]` (a gate can prove it — name the gate) or `[J]` (needs a reviewer's eye), never both, never none. A check that is `[D]` with tooling and `[J]` without is **two clauses**; that split is the mechanical-vs-model-upheld distinction and is never compressed away. A clause states what a model cannot infer — the threshold, the named tool, the house preference — and nothing the heading already says. **These per-check tags are the catalog's confidence record** — there is no dimension-level Confidence line, and no honest reading of a dimension without them.
- **Honesty register —** where a dimension must state what it deliberately does **not** prove or gate.
- **Incident —** the concrete dated failure this dimension prevents, on the minority that have one (`grep -l '\*\*Incident —\*\*' docs/claugentic-standards/*.md`). An incident is what makes a rule un-cargo-cultable — and what makes it safe to delete once its cause is gone.

**Select, don't skip.** Apply the *relevant* dimensions, each **fully** — no debt; never gold-plate an irrelevant one (`KISS`/`YAGNI`), never skip a relevant one. Relevance is a per-change judgment.

**No permanent "N/A".** Don't cap a dimension as irrelevant forever — a stack grows into things. A repo's *current* applicability is the **Current scope** snapshot `init` seeds in the adopter's `CLAUDE.md` `harness:` block (local, non-managed, non-capping).

**Not confined — to this list or to known patterns.** Exceed the list when a change warrants it; a novel pattern is allowed on the terms `_TEMPLATE.md` → *Authoring rules* sets.

## Honesty register — what this catalog can actually prove

- **A `[D]` tag describes what is provable *in principle*.** A `[D]` check is *proven* only where the adopter has the tool wired (linter / scanner / test runner / CI). Without it the audit cannot run the check and reports it as the model's **judgment (`[J]`)**, not a verified fact. What is *actually* proven on a repo depends on that repo's tooling.
- **A `draft` module's specific claims are model-asserted** — thresholds, named tools, cited standards — checked independently only when it is promoted to `stable` or pulled into real work.
- **`load_scope.globs` is an advisory HINT, not a gate.** It only suggests which changed files pull a module in; `lens-reviewer` is told its module explicitly at invocation, so a non-matching default (a repo whose code isn't under `src/`) never breaks anything and never silently drops the lens.

## Two-tier knowledge: global (synced) vs local (stays put)

- **Global — this directory.** Bundled in the plugin and **copied into the adopter's `docs/claugentic-standards/` by `init`** — copy-on-init, never read from the plugin at runtime (`docs/claugentic-DECISIONS.md` → “Managed docs are adopter-aware”). Copies are version-stamped and headed **“managed — do not edit”**: a newer plugin version replaces them, so changing a standard means proposing it **upstream** and re-initing. In the **plugin repo** these files ARE the editable source.
- **Local — the adopting repo (`${CLAUDE_PROJECT_DIR}`).** The **Current scope** snapshot, `CANDIDATES.md` (lessons awaiting promotion — **created on first use**, not shipped empty), and repo lessons in `CLAUDE.md` / `docs/claugentic-DECISIONS.md`. These **never propagate**.
- **Promotion path — manual.** A *universal* lesson is staged in `CANDIDATES.md`, reviewed, then promoted upstream into a global module, reaching every repo on its next plugin update (`docs/claugentic-WORKFLOW.md` → *The learning loop*). A *repo-specific* lesson stays local.

## Versioning

A module carries **no version of its own.** The only version that means anything is the plugin release stamped on line 1 of an adopter's managed copy.

**Status legend:** `stub` = listed, unwritten · `draft` = written, model-asserted, not battle-tested · `stable` = dogfooded · `reserved` = named above, no file yet.
