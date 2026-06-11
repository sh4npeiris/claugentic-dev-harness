# 0010 — `init` becomes version-aware (refresh managed content, never clobber user content)

- **Status:** Done — Slice 1 landed (prose-only; version-aware init + lockstep claim change; v0.1.15). Stage-7 CHANGES_REQUIRED resolved 2026-06-10: `INCLUDE_GLOBS` hybrid carve-out wired into step 3; dogfood acceptance matrix re-walked + recorded (all rows PASS incl. 4/5/12 + second-walk); forbidden-verb survivor (`guarante`) demoted; step-9 headline branched on the Refreshed group; minor stop-rule / never-deletes / heading / wording fixes applied. Stage-7 **re-check** (same-family, honestly tagged) confirmed both blockers fixed; final word-level honesty polish applied (recovery wording conditioned on *committed* history per the slice's own ROADMAP:23; the settings.json "provable no-op" demoted; `INCLUDE_GLOBS` exception noted in the does-NOT scope). Gates green (pytest 61 · version-sync · tree-check); refresh/no-op claim register clean. **Uncommitted — awaiting your land decision.**
- **Roadmap item:** Closes the init version-drift gap — adopters stamped at an old plugin version had no update path (the design intent "init is the updater" was never realized; see `docs/DECISIONS.md` → Plugin identity).
- **References:** `skills/init/SKILL.md` · `docs/DECISIONS.md` · `README.md` · `docs/ARCHITECTURE_TREE.md` · `docs/PLAYBOOK.md:62` ("trust the oracle, not the model")

## Problem

`init` is **copy-if-absent only**. After a plugin version bump, an adopter's managed files keep their old content and old stamp forever — there is no update path:

- `skills/init/SKILL.md:92` — "Per file: if the target path already exists, skip it."
- `skills/init/SKILL.md:279-281` — "It does **not** refresh an already-copied managed file to a newer version — the `init` skill is copy/seed-**if-absent** only."

The discovery sweep confirmed **no documented update path exists anywhere** (README, WORKFLOW, ROADMAP, DECISIONS). The original intent — *one idempotent door that also updates* — was never built. A user init'd at `0.1.1` is frozen at `0.1.1` content while the installed plugin is `0.1.14`, silently missing every release's improvements to the standards catalog, workflow, and gate.

## Goals / Non-goals

**Goals**
- Re-running `init` **refreshes stale managed content to the installed plugin version** while **preserving all user-owned content** (never-clobber stays the load-bearing invariant).
- **One door** — no separate `update`/`sync` command (KISS; the owner's explicit intent).
- Behavior per the locked + panel-resolved decisions: **Refresh + report** · **content-aware** · **both the managed files and the `CLAUDE.md` fence** · **no RESTAMP** (content-identical files are left byte-untouched) · **prose-only decision** (no oracle script).

**Non-goals**
- **No RESTAMP.** A content-identical managed file is left **byte-for-byte untouched** even if its stamp semver is older than installed. Per-file stamps therefore mean "the version this content last changed at," and the **authoritative repo-version readout is the `CLAUDE.md` managed fence** (which *does* refresh). Mixed per-file stamps are expected and correct.
- **No 3-way merge** of user edits *inside* a managed (`do not edit`) file. Managed files carry zero user content by contract; on a genuine content change the installed version wins, and **git is the review/recovery net**.
- **No refresh of seeded user-owned docs:** `docs/ARCHITECTURE_TREE.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md` stay create-if-absent.
- **No destructive directory mirror** — a user-added file (e.g. `docs/standards/my-custom.md`) is **never deleted** (per-file upsert, not `rsync --delete`).
- **No reconciliation of the `settings.json` hook *command string*** if its format changes between versions (keyed on the `check_architecture_tree.py` substring; out of scope → ROADMAP).
- **No new script, no oracle, no new state store, no new agent.** The refresh decision is made by `init` inline (model-upheld, rule-bound).

## Approach

### Step 3 goes from *copy-if-absent* → *upsert-to-installed* (four verdicts)

For each file in the managed set, `init` reads line 1 of the target and decides:

| Detected state | Verdict | Action | Report line |
|---|---|---|---|
| target **absent** | `CREATE` | copy + stamp (today's behavior) | `created` |
| present, **not a genuine managed copy** (see predicate) | `USER_FILE` | **skip — never overwrite** | `skipped (user file / unrecognized stamp) — reconcile manually` |
| genuine managed copy, **body differs from source** | `REFRESH` | overwrite whole file with freshly-stamped source (stamp = installed) | `refreshed <path>: <old> → <installed>` |
| genuine managed copy, **body identical to source** | `CURRENT` | **leave byte-untouched** (true no-op — even if stamp semver is older) | `skipped (already current)` |

### The genuine-managed predicate (never-clobber-critical — rule-bound, not eyeballed loosely)

A target file is a **genuine managed copy** (eligible for REFRESH) only when **all** hold:
1. its **path is in the managed set** (a path not in the set is never a REFRESH candidate, whatever its first line);
2. line 1 is the **exact stamp form** — `claugentic-dev-harness@<semver> managed — do not edit (copied from the claugentic-dev-harness plugin)` in the file's comment syntax — **with a parseable semver**.

**Anything else is `USER_FILE` → skip:** an unstamped same-named file, a line-1 that merely *quotes* the token, a *foreign* plugin's stamp, or a **garbled/unparseable semver**. And the existing load-bearing invariant governs the residue: **if it is ambiguous whether a write would destroy user content, `init` stops and reports rather than guesses** (`SKILL.md:19-21`). With no mechanical oracle, this stop-if-ambiguous rule *is* the never-clobber safety net — the spec wires step 3 to it explicitly.

### The content compare (the off-by-one + CRLF traps)

- **Asymmetric, unambiguous:** `target body = target minus line 1` (the stamp); `source body = the pristine source as-is` (sources carry **no** stamp — `SKILL.md:96`). For the Python gate this strips **only line 1** (the stamp); the `#!/usr/bin/env python3` shebang on line 2 **stays in the body**. Stripping the shebang too would misalign every Python compare by one line and false-REFRESH it.
- **Newline-insensitive:** compare normalized (LF/CRLF + trailing-newline insensitive) so an adopter's line-ending settings (Windows `autocrlf` → CRLF on checkout) never trigger a false REFRESH. This repo's `.gitattributes` does **not** reach adopter repos, so this is a real adopter-side risk; the **CRLF dogfood fixture** (Test strategy) is its safety net since there is no unit test.

### The one hybrid managed file — `check_architecture_tree.py`'s `INCLUDE_GLOBS` (Stage-7 blocker fix)

The founding premise "all 5 managed files are pure verbatim, zero user content" is **wrong for one file**. `scripts/check_architecture_tree.py:40-57` carries `INCLUDE_GLOBS` — "the **ONLY** per-repo knob" — which **init itself writes per-adopter** in step 5a, re-derives on glob-drift, and **invites the user to refine** (`SKILL.md:192-193`). So an adopter's correctly-configured copy **always** differs from the pristine source → would always REFRESH (breaking no-op) and the overwrite would **reset their globs to this repo's value** (a never-clobber violation + a broken tree-check for them).

**Fix — treat it as a hybrid, exactly like the `CLAUDE.md` fence (protect the per-repo region, refresh the managed rest):**
- **Compare excludes the `INCLUDE_GLOBS = [ … ]` assignment** (from `INCLUDE_GLOBS =` through its closing `]`) on *both* sides → an adopter with custom globs reads **CURRENT** when the rest of the managed body matches.
- **A REFRESH preserves (re-injects) the adopter's existing `INCLUDE_GLOBS`** — write `new source body, minus its INCLUDE_GLOBS` + `the adopter's current INCLUDE_GLOBS assignment` + the installed stamp. (Then init's existing step-5 glob-drift self-correction runs as today.) With the carve-out, the never-clobber and idempotent-at-a-fixed-version claims stand **as written**.
- **Assumption (stated so the carve-out is well-defined):** `INCLUDE_GLOBS` is the single, stable per-repo knob. If a future version restructures it, that's a version-migration concern → ROADMAP.

### `CLAUDE.md` managed fence (the "both" decision)

Step 6 changes from **skip-if-fence-present** → **refresh-inside-fence**: regenerate the managed block from the current template and **replace only between `<!-- harness:managed:start -->` / `:end`**, preserving everything outside (Current-scope block, detected-tooling block, all human content) **byte-for-byte**. Content-aware: byte-identical inner block → no-op; differs → replace. The fence embeds `claugentic-dev-harness@{VERSION}` (`SKILL.md:202`), so a version bump alone makes it differ → it refreshes. This fence is the authoritative repo-version readout (the reason RESTAMP is unneeded).

### The honesty-critical claim change (ships in the same slice — non-negotiable)

Every live "safe no-op / provable no-op" claim becomes the conditional, **honestly model-upheld** wording. The whole refresh decision is `init`'s judgment (there is no oracle), so **nothing here is "mechanical" or "unit-tested"** — say so:

> Re-running `init` **converges the repo to the installed version** — it refreshes any managed file whose content changed since it was copied, and is a **true no-op only when the repo is already at the installed version**. The drift decision and the writes are **`init`'s judgment** (rule-bound, never-clobber-guarded by stop-if-ambiguous); **idempotent-at-a-fixed-version** is checked by a **dogfood run, not a wired gate.**

This is the over-claim trap the harness forbids (`DECISIONS.md:5-10`; user memory `harness-honesty-positioning`). Behavior and claim **land in the same slice** — shipping refreshed behavior under a "provable no-op" claim would itself be the dishonesty the harness exists to prevent.

**True claim-site inventory (grep-verified — supersedes the draft's wrong list):**
- **Change:** `README.md:7` ("re-running is a safe no-op"), `README.md:49` ("safe — never overwrites"), `SKILL.md:2` (frontmatter description), `SKILL.md:8-9` ("provable no-op" + "detect → create-if-absent…"), `SKILL.md:55` ("detect → create-if-absent / merge-in-fence → report" — step 3 is now upsert), `SKILL.md:256` ("the whole run is a safe no-op"), `SKILL.md:263` ("safe and a provable no-op"), `ARCHITECTURE_TREE.md:70` ("idempotent scaffold … create-if-absent").
- **Assess for scope, likely keep with a tightened clause:** `README.md:16` ("`init` never overwrites *your content*") — stays **true** (user content is never overwritten), but verify it can't be read as "never overwrites a managed file" now that a genuine managed copy *is* refreshed.
- **Preserve unchanged (still accurate):** `SKILL.md:181` ("a provable no-op on *this file*" — the settings.json hook merge, genuinely unchanged) and `PLAYBOOK.md:70` (glossary definition of "idempotent").

### Self-demonstrating on release

Releasing as **`0.1.15`** means every adopter's next `init` re-run **exercises the refresh path** (the fence + any changed managed file move to `0.1.15`). *(Demonstrates the path runs — it does not "prove" never-clobber for a hand-edited managed file, which by contract is overwritten.)*

## Affected files

- `skills/init/SKILL.md` — **step 3** copy → upsert (the four-verdict table + the genuine-managed predicate + the compare rules + the stop-if-ambiguous wiring); **step 6** fence skip → refresh-inside-fence; **step 9** report groups (`Refreshed` added; drop "copy-if-absent only" framing); **idempotency section `262-273`** → "idempotent at a fixed version, model-upheld, dogfood-checked"; **"does NOT" bullet `279-281`** → remove the "does not refresh" line, replace with the user-owned-files-never-refreshed scope; **opening `7-10`** + **`55`** verb fix; **frontmatter `2`** description.
- `README.md` — `:7`, `:49` claim rewrite; `:16` scope-check (likely keep).
- `docs/ARCHITECTURE_TREE.md` — `:70` init one-liner → "version-aware upsert-to-installed / refresh-inside-fence / never-clobber user content" (tree-check enforces presence, **not** description accuracy — model-upheld).
- `docs/DECISIONS.md` — append under *Plugin identity & distribution*: init is version-aware (upsert-to-installed, RESTAMP-free, prose-decided) + the "idempotent at a fixed version (model-upheld, dogfood-checked)" honesty line; record the settings.json-command-format non-goal.
- `.claude-plugin/plugin.json` — **`version` → `0.1.15`** only (description carries no no-op claim — no copy change).
- `.claude-plugin/marketplace.json` — **`version` → `0.1.15`** only (gated to match by `check_versions_synced.py`; description carries no claim — verify it stays in sync by inspection).
- `docs/ROADMAP.md` — add the deferred "reconcile settings.json hook command on format change" item.

## Risks & mitigations

- **Prose decision mis-classifies a genuine-managed vs user file → clobber.** (The accepted cost of prose-only.) → Mitigation: the **explicit predicate** (path-in-set + exact stamp + parseable semver) + the **stop-if-ambiguous** invariant (overwrite only when unambiguously a genuine managed copy) + **git** as the recovery net (every overwrite is reported by path).
- **False REFRESH from CRLF / trailing-newline (Windows adopters).** → Newline-normalized compare, **covered by the CRLF dogfood fixture** (the only safety net absent a unit test).
- **Off-by-one (stripping the Python shebang in the compare).** → The asymmetric rule above + the "freshly-copied Python gate must read CURRENT" dogfood assertion.
- **Fence replacement corrupts content outside the markers.** → Replace-only-inside is the proven audit-fence pattern; the dogfood asserts outside-fence bytes preserved.
- **A stale "safe no-op" survives in a missed copy.** → The grep-verified inventory + a **post-change acceptance grep** (`no-op|provable|safe no-op`); every survivor must be new wording or an unrelated standards-module use.
- **Claim/behavior drift apart.** → Same slice; honesty-reviewer gates it.

## Test strategy

`init` is an **agent procedure — no unit-test harness**, and (per the owner's prose-only choice) there is **no oracle script to unit-test**. Verification is therefore a **documented, reproducible dogfood acceptance**, run by the implementer at Verify and re-runnable by a reviewer — stated honestly as model-upheld, not a wired gate:

1. **Fixture setup (checked-in or scripted):** a throwaway target repo with — managed files hand-stamped at `0.1.1`, a **mix** of (a) content-identical-to-current-source and (b) content-changed; one with **CRLF** line endings + identical body; a managed file a user **edited**; an **unstamped** same-named file; a file whose line 1 merely **quotes** the token; a user-added `docs/standards/extra.md`; a `CLAUDE.md` with a `0.1.1` fence + edited human content outside it.
2. **Run init.** Assert: (b) → `REFRESH` to installed; (a) + the CRLF one → `CURRENT`, **byte-untouched**; the user-edited managed file → `REFRESH` (reported by path); unstamped + token-quote + foreign → `USER_FILE` skip; user-added file untouched & not deleted; fence refreshed inside markers, outside bytes preserved; report groups correct.
3. **Run init again → `git status` shows zero diffs** (idempotent at a fixed version — the headline behavioral assertion).
4. **Claim grep:** no surviving `safe no-op`/`provable no-op` except the new wording / `SKILL.md:181` / `PLAYBOOK.md:70` / standards-module uses. **Description-sync:** `plugin.json` and `marketplace.json` versions match (`check_versions_synced.py`) and neither description regressed.
5. **`python -m pytest`** still green (unchanged — confirms no collateral breakage of the existing gates).
6. **Honesty-reviewer** over the rewritten copy: no "mechanical/proven/no-op" survives where model-upheld convergence is the real behavior.

## Decomposition (slices)

- [x] **Slice 1 (only) — version-aware init + lockstep claim change.** All of *Affected files* above + the dogfood acceptance fixtures/steps. **Lands complete in one session, no debt:** it is entirely prose/doc edits (no code), behavior and the honesty claim ship together (mandatory), and the dogfood acceptance is the runnable proof. *(The earlier two-slice split existed only to isolate the oracle's unit tests; with prose-only there is no separable code unit, so one vertical slice is correct.)*

---

## Review  _(diverse panel, Stage 3 — plan-reviewer · yagni-sentinel · honesty-reviewer)_

- **Verdict (on the original draft):** **CHANGES REQUIRED** (unanimous). Core design endorsed (upsert table, lockstep claim change, slicing); defects in claim-site completeness, two never-clobber edges, honest framing, and two scope forks.

- **Owner resolution of the two forks (now reflected in the body above):**
  1. **RESTAMP → CUT** (yagni-sentinel). Content-identical files left byte-untouched; version readout lives in the refreshed `CLAUDE.md` fence. Table is now four verdicts.
  2. **Oracle → PROSE-ONLY** (yagni-sentinel). No `check_managed_drift.py`. `init` makes the drift decision inline, rule-bound; the never-clobber predicate is enforced by explicit rules + the existing stop-if-ambiguous invariant; CRLF correctness is covered by the dogfood fixture, not a unit test. Collapses to **one slice**. Honesty consequence applied: **nothing in the refresh is described as "mechanical / unit-tested"** — the decision and writes are model-upheld, idempotency is dogfood-checked.

- **Required fixes folded in:** corrected grep-verified claim inventory (plugin/marketplace = version-bump-only; added `README:16,49`, `SKILL.md:55,256`, `ARCHITECTURE_TREE:70`; preserved `SKILL.md:181` + `PLAYBOOK:70`); genuine-managed predicate for the garbled/quoted/foreign-stamp clobber edges; asymmetric off-by-one compare + Python-shebang rule; honest framing of mechanical-vs-model-upheld; `ARCHITECTURE_TREE:70` staleness; scripted dogfood acceptance incl. CRLF + claim-grep + description-sync; harness-impact note (no pytest covers init; only the tree-check gate is touched; nothing new added to the copied managed set).

- **Harness impact:** No existing test asserts init's old "copy-if-absent" behavior → no phantom regression. Only the tree-check + version-sync gates are touched (version bump satisfies the latter). Nothing added to the copied managed set.

---

## Stage-7 verify — findings & resolution (cross-model panel: honesty + architect on `fable`, yagni on opus)

> Honest note: both gate roles ran **Claude-family** models (`claude-fable-5`, `Fable 5`) — same vendor as the Opus builder, so this is **shared-blind-spot reduction, not independence**; the honesty-reviewer self-tagged it. yagni: **CLEAN** (proportionate). Both gates: **CHANGES_REQUIRED / OVERCLAIMS** — defects below.

- **[BLOCKER · resolved in Approach above]** `check_architecture_tree.py` is hybrid (`INCLUDE_GLOBS`) → the carve-out section. Never-clobber + no-op claims now stand.
- **[BLOCKER · dogfood proof never recorded]** The implementer walked the dogfood in a temp dir then deleted it — no checked-in fixture, no recorded matrix, while Status said "Done." The dogfood is the **only** compensating control for cutting the oracle (CRLF / shebang off-by-one / fence-preservation have no other net). **Resolution:** record the reproducible fixture-setup + the per-fixture verdict matrix in the Spec section below (a documented model-walked rehearsal — honestly *not* a CI-runnable test, since init is an agent procedure). Re-walk including the new `INCLUDE_GLOBS` fixture.
- **[major · honesty]** `SKILL.md:58` "the 'zero diffs on the 2nd run' **guarantee** holds" — forbidden mechanical verb on the demoted claim; evaded the grep (no "no-op", "guarantee" not "guaranteed"). Reword to the dogfood-checked register; widen the acceptance grep to case-insensitive `guarante`.
- **[major · honesty]** Step-9 plain-English headline asserts "I did NOT overwrite your own files" unconditionally — substantively false right after a user-edited managed file is REFRESH'd. Branch it on the Refreshed group (when non-empty, add the "if you'd edited a managed file your edits were replaced — see Refreshed; git keeps them" caveat).
- **[minor · architect]** Step 6: malformed fence (start without end / duplicate markers) → ambiguous extent → **stop-and-report** (wire to never-clobber, like step 3 did); add a half-fence dogfood fixture.
- **[minor · architect]** Step 3: state the **never-deletes** rule (per-file upsert; a user-added `docs/standards/*` is left; a managed module the installed version no longer ships is left in place + reported, never removed).
- **[minor · architect]** Step 6 heading "never touch anything **outside** the managed fence" self-contradicts (Current-scope + tooling blocks are seeded outside) → "never **modify existing content** outside the fence"; state whether a re-run updates or skips an existing detected-tooling block; `SKILL.md:35` "copies" → "copies or refreshes."
- **[minor · honesty]** `README.md:16` tighten once: "…edits made inside one are replaced on refresh; git history keeps them." Convention-1 parenthetical → "(one leg of the predicate — the other is path-in-the-managed-set)."
- **[ROADMAP · not this slice]** Before a REFRESH over a user-edited/uncommitted managed file (or a repo with no commits), the git-recovery net is empty → warn / suggest committing first. Added to ROADMAP Later.

## Spec  _(Stage 4 — dogfood acceptance matrix; implementer fills the Result column on re-walk)_

A documented, reproducible **model-walked rehearsal** (not a CI test — init is an agent procedure). Fixture: a throwaway target repo with the rows below; walk the revised step-3/step-6 procedure, then walk it a **second** time.

> **Honesty note on this matrix (read first).** This is a **documented, model-walked
> rehearsal**, *not* a CI-runnable test — `init` is an agent procedure with no oracle
> script, so there is nothing for `pytest` to drive. The implementer built a throwaway
> fixture repo (under the system temp dir), wrote each row's file, then walked the revised
> step-3 predicate + asymmetric compare + the `INCLUDE_GLOBS` carve-out + the step-6
> fence/half-fence rules **exactly as written in `SKILL.md`**, applying them as `init`
> would judge. The verdicts below are that walk's outcome; the fixture was deleted after
> (it is **not** checked in — checking fixture files in would complicate the tree-check; the
> recorded matrix here is the durable artifact). Re-walk: 2026-06-10, installed `0.1.15`.

| # | Fixture (managed file / state) | Expected verdict | Result |
|---|---|---|---|
| 1 | managed `.md`, body changed vs source, stamp `0.1.1` | REFRESH → 0.1.15 | **PASS** — REFRESH 0.1.1 → 0.1.15 |
| 2 | managed `.md`, body identical, stamp `0.1.1` | CURRENT (byte-untouched) | **PASS** — CURRENT, stamp `0.1.1` left untouched (no RESTAMP) |
| 3 | managed `.md`, identical body, **CRLF** line endings | CURRENT (no false REFRESH) | **PASS** — CURRENT (newline-normalized compare; no false REFRESH) |
| 4 | `check_architecture_tree.py`, **custom `INCLUDE_GLOBS`**, rest-of-body identical | **CURRENT** (carve-out) | **PASS** — CURRENT; carve-out excluded the globs region on both sides, rest-of-body matched |
| 5 | `check_architecture_tree.py`, custom globs, **rest-of-body changed** | **REFRESH preserving the custom globs** | **PASS** — REFRESH 0.1.1 → 0.1.15; written file kept adopter globs `:(glob)src/**/*.ts`,`:(glob)src/**/*.tsx` (NOT this repo's `:(glob)scripts/**/*.py`) |
| 6 | managed file a user **edited** (stamp intact, body drifted) | REFRESH (reported by path) | **PASS** — REFRESH 0.1.1 → 0.1.15 (reported by path; user edit dropped, git is the recovery net) |
| 7 | unstamped same-named file | USER_FILE skip | **PASS** — USER_FILE (no stamp on line 1) → skip |
| 8 | line-1 merely **quotes** the token | USER_FILE skip | **PASS** — USER_FILE (line 1 only quotes the token, not the exact stamp form) → skip |
| 9 | **foreign** plugin stamp / **garbled** semver | USER_FILE skip | **PASS** — both USER_FILE → skip (foreign stamp fails the form; `not.a.version` fails the parseable-semver leg) |
| 10 | user-added `docs/standards/extra.md` | untouched, not deleted | **PASS** — USER_FILE (path not a specific managed-set path) → left untouched, never deleted |
| 11 | `CLAUDE.md` `0.1.1` fence + edited human content outside | fence refreshed inside; outside bytes preserved | **PASS** — refreshed inside markers; pre-fence intro + post-fence Current-scope preserved byte-for-byte |
| 12 | `CLAUDE.md` **half-fence** (start, no end) | stop-and-report (ambiguous) | **PASS** — start without end → STOP-AND-REPORT (ambiguous extent; never-clobber invariant) |
| — | **second walk over the post-refresh repo** | 0 changes (idempotent at fixed version) | **PASS** — rows 1/5/6 all re-read CURRENT (stamp `0.1.15`); fence inner block byte-identical on re-gen → zero diffs |

Plus (this re-walk, 2026-06-10): claim grep `-iE "safe no-op|provable no-op|guarante"` — only sanctioned survivors (the new conditional wording, `settings.json` hook-merge "provable no-op on this file", PLAYBOOK glossary, standards-module uses); `plugin.json`↔`marketplace.json` both `0.1.15` (sync OK); `python -m pytest` green; `check_versions_synced.py` + `check_architecture_tree.py` green.