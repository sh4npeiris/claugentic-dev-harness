# 0011 — genuine-managed predicate keys on the STABLE stamp prefix (trailing-clause drift fix)

- **Status:** Done — prose/doc-only follow-up to plan 0010; v0.1.16. SKILL.md predicate loosened to the stable prefix + migrate-on-refresh; DECISIONS + ROADMAP recorded; dogfood re-walked (verdicts below). Gates green (pytest 61 · version-sync 0.1.16 · tree-check). **Uncommitted — awaiting land decision.**
- **Roadmap item:** Closes a never-clobber-adjacent bug in plan 0010's tightened genuine-managed predicate — old-format-but-genuine managed files were classified `USER_FILE` and skipped forever, so `/init` silently failed to refresh exactly the old adopters the feature exists to serve.
- **References:** `.claude/plans/0010-init-version-aware-refresh.md` (the slice this follows up) · `skills/init/SKILL.md` · `docs/DECISIONS.md` → Plugin identity & distribution · `scripts/check_architecture_tree.py:56` (the adopter-neutral-comment nit → ROADMAP).

## Problem

Plan 0010's `init` refresh classifies a managed file via the **genuine-managed predicate**. We tightened leg 2 to require the **exact current full** stamp form `claugentic-dev-harness@<semver> managed — do not edit (copied from the claugentic-dev-harness plugin)`.

But the **trailing clause after `do not edit` has drifted across releases**:
- **0.1.1-era** copies read `claugentic-dev-harness@0.1.1 managed — do not edit; run /claugentic-dev-harness:update to refresh`.
- **Current** copies read `… managed — do not edit (copied from the claugentic-dev-harness plugin)`.

Under the strict predicate, an **old-format-but-genuine** managed file fails leg 2 → classified `USER_FILE` → **skipped → never refreshed**. So `/init` would silently fail to refresh exactly the old adopters the version-aware feature exists to serve. **AskBase hit this on a real 0.1.1→0.1.15 refresh** (we ruled it manually).

## Goals / Non-goals

- **Goal:** the predicate recognizes a genuine managed copy regardless of the version-variable trailing clause, so an old-adopter `/init` refreshes (and migrates the stamp) instead of skipping.
- **Goal:** keep plan 0010's clobber-edge protections intact (leg 1 path-in-set + leg 2 the full prefix on **line 1**).
- **Non-goal:** changing what `init` *writes* — the current full form is unchanged; only the **detection/identity test** loosens.
- **Non-goal:** any code change — `init` is an agent procedure; this is prose/doc-only.
- **Non-goal:** fixing the adopter-neutral-comment nit (`check_architecture_tree.py:56`) inline — deferred to ROADMAP.

## Approach

**Loosen leg 2 to the stable prefix; migrate the stamp on refresh.**
1. **Predicate leg 2** keys on the **stable managed-stamp prefix** — `claugentic-dev-harness@<semver> managed — do not edit` (in the file's comment syntax) **with a parseable semver**. The **trailing clause is version-variable and NOT part of the identity test** — match the stable prefix only.
2. **A REFRESH migrates the stamp to the current full form** — so an old trailing clause is normalized on refresh. Because an old-format genuine copy whose body is otherwise identical to source still has a stale stamp line, a **stamp-format migration is a legitimate REFRESH even when the body matches** — a one-time line-1 normalization, **distinct from the no-RESTAMP rule** (which is about not bumping the *version* of byte-identical current-format files).
3. **Clobber edge preserved:** the predicate still requires (leg 1) path-in-the-managed-set AND (leg 2) the prefix on **line 1**. A mere quote of the token in prose (or elsewhere on the line), an unstamped file, a foreign stamp, or a garbled/unparseable semver → `USER_FILE`. The trailing-clause tolerance does **not** weaken never-clobber.
4. **Convention 1** reconciled — detection keys on the stable prefix (trailing clause version-variable); what `init` WRITES stays the current full form.

*Alternatives rejected:* (a) maintain a per-release list of every historical trailing clause — an always-incomplete registry, the same rot the harness forbids elsewhere; (b) match only the bare `claugentic-dev-harness@<semver>` token — too loose, would match a prose quote and regress never-clobber.

## Affected files

- `skills/init/SKILL.md` — Convention 1 (managed-stamp definition: detection keys on the stable prefix, trailing clause version-variable, written form unchanged); step-3 four-verdict table (REFRESH row + CURRENT row gated on stamp format); the genuine-managed predicate leg 2 + the "Anything else is USER_FILE" paragraph; the stamp-on-copy/refresh rule + a new stamp-format-migration bullet; the body-compare stamp-format note; the step-9 Refreshed report line; the idempotency-section upsert bullet.
- `docs/DECISIONS.md` — append under *Plugin identity & distribution* (dated 2026-06-11).
- `docs/ROADMAP.md` — add the `check_architecture_tree.py:56` adopter-neutral-comment Later nit.
- `.claude-plugin/plugin.json` · `.claude-plugin/marketplace.json` — `version` 0.1.15 → 0.1.16 (the sync gate enforces the pair).
- `.claude/plans/0011-managed-stamp-prefix-predicate.md` — this plan.

## Risks & mitigations

- **The trailing-clause tolerance could be read as weakening never-clobber.** → It does not: leg 1 (path-in-set) + leg 2 (full `@<semver> managed — do not edit` prefix on **line 1**) are both still mandatory; a bare token quote in prose still fails leg 2. The SKILL.md prose states this explicitly. Flagged for the verify panel below.
- **Stamp-format migration confused with a RESTAMP / version bump.** → SKILL.md states the distinction crisply: no-RESTAMP is about not bumping the *version* of a byte-identical, already-current-format file; stamp-format migration normalizes the *line-1 format* of an old-format file (then re-reads CURRENT — idempotent at a fixed version).
- **Over-claim creep in the loosened wording.** → The predicate stays `init`'s judgment (no oracle); claim grep `-iE "provable no-op|safe no-op|guarante"` run, no new survivors.

## Test strategy

`init` is an agent procedure — no unit-test harness, no oracle script. Verification is a documented, model-walked **dogfood**:
- An old-format genuine managed copy (`@0.1.1 managed — do not edit; run /…:update to refresh`) on a managed-set path → recognized as GENUINE → REFRESH + stamp migrated to the current full form.
- Clobber edges still hold: a managed-path file whose line 1 merely quotes the token in prose → `USER_FILE` skip; a non-managed-set path with a perfect stamp → not a candidate (leg 1 fails).
- Gates: `python -m pytest` green; `python scripts/check_versions_synced.py` OK (both 0.1.16); `python scripts/check_architecture_tree.py` OK.

## Dogfood (model-walked rehearsal — 2026-06-11, installed 0.1.16)

A documented walk of the revised SKILL.md predicate (not a CI test — `init` is an agent procedure).

| # | Fixture (managed file / state) | Expected verdict | Result |
|---|---|---|---|
| 1 | managed-set path, line 1 = **OLD-format** stamp `<!-- claugentic-dev-harness@0.1.1 managed — do not edit; run /claugentic-dev-harness:update to refresh -->`, body otherwise identical to source | GENUINE → **REFRESH**, stamp **migrated** to current full form | **PASS** — leg 1 (path-in-set) + leg 2 (stable prefix `claugentic-dev-harness@0.1.1 managed — do not edit` present, `0.1.1` parses) both hold → GENUINE. Body strips line 1 → body-identical, BUT line 1 is in the old trailing-clause format → REFRESH (one-time stamp-format migration) → 0.1.1 → 0.1.16, line 1 rewritten to `… (copied from the claugentic-dev-harness plugin)`. A re-run reads CURRENT. |
| 2 | managed-set path, line 1 **merely quotes** the token in prose (e.g. `<!-- see claugentic-dev-harness@<semver> managed — do not edit in the docs -->` — token not leading the line as the full prefix) | USER_FILE skip | **PASS** — leg 2 fails: line 1 does not *lead* with the `claugentic-dev-harness@<semver> managed — do not edit` prefix (it is embedded in prose) → USER_FILE → skip, never overwritten. |
| 3 | **non-managed-set path** (e.g. `docs/notes.md`) with a **perfect current** stamp on line 1 | not a candidate (leg 1) | **PASS** — leg 1 fails (path not in the managed set) → never a REFRESH candidate whatever line 1 says → USER_FILE / left untouched. |

**Verdicts:** old-format genuine → REFRESH + migrate (the bug is fixed); both clobber edges hold (prose quote → skip; off-set perfect stamp → not a candidate). The trailing-clause tolerance does not weaken never-clobber.

Plus (this walk): claim grep `-iE "provable no-op|safe no-op|guarante"` over the refresh register — only sanctioned survivors (no new over-claim); `plugin.json`↔`marketplace.json` both `0.1.16` (sync OK); `python -m pytest` green (61); `check_versions_synced.py` + `check_architecture_tree.py` green.

## Decomposition (slices)

- [x] **Slice 1 (only) — stable-prefix predicate + migrate-on-refresh.** All of *Affected files* above + the dogfood walk. Lands complete in one session, no debt: entirely prose/doc edits (no code), the detection loosening and the migrate-on-refresh rule ship together, the dogfood walk is the documented model-walked check (not a CI test — no oracle), and the version bump satisfies the sync gate.

---

## Review  _(follow-up slice to plan 0010 — see that plan's diverse-panel Review + Stage-7 verify)_

This slice inherits plan 0010's design and panel review; it corrects one defect (the over-tight leg-2 form) surfaced by real AskBase use. The never-clobber framing is unchanged — leg 1 + leg 2-on-line-1 still guard the clobber edge; only the version-variable trailing clause is excluded from the identity test. Flag for the verify panel: scrutinize that the trailing-clause tolerance cannot be read as weakening never-clobber — we judge it does not (leg 1 path-in-set + leg 2 full prefix on line 1 are both still mandatory), but the panel confirms independently.
