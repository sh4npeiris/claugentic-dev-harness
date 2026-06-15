---
description: Scaffold the claugentic-dev-harness into the current repo — upsert the managed harness set (standards catalog, workflow, playbook, tree-check) to the installed plugin version, generate docs/ARCHITECTURE_TREE.md, set the tree-check globs, wire the hook, declares the plugin for teammates (seeds the harness's plugin self-reference into the committed .claude/settings.json so a cloned adopter repo prompts teammates to install it), git-init if needed, seed ROADMAP/DECISIONS, refresh the CLAUDE.md harness fence, and compose with existing lint/type-check/test tooling. Re-running converges the repo to the installed version and never clobbers user content; a true no-op only when already at the installed version.
---

# /claugentic-dev-harness:init

Scaffold this harness into the current repo, **without clobbering user content**. Every
write is **detect → upsert-to-installed / refresh-inside-a-fence / report** — the `init`
skill **never** overwrites *your* content, and **re-running converges the repo to the
installed plugin version**: it refreshes any managed file whose content changed since it
was copied, and is a **true no-op only when the repo is already at the installed version**
(then it creates nothing, refreshes nothing, and reports everything as already current).
The drift decision and the writes are **`init`'s judgment** — rule-bound and
never-clobber-guarded by the stop-if-ambiguous invariant below — not a mechanical oracle;
**idempotent-at-a-fixed-version is checked by a dogfood run, not a wired gate.**

## How this skill works

A top-level agent (the orchestrator) follows the **9-step procedure** below in order.
Each step is guarded — it detects the current state first, then acts: it creates what is
absent, **refreshes a genuine managed copy whose content drifted from the installed
source**, refreshes the managed fence in place, and **leaves user content untouched**. It
reports what it did. The output is a clear **created / refreshed / skipped / merged /
detected** summary.

**Never-clobber is the load-bearing safety invariant** (this writes into someone else's
repo — a careless overwrite is data loss). If any step is ambiguous about whether a
write would destroy user content, **stop and report rather than guess.**

### Two durable conventions this skill establishes

These are contracts the `init` skill's own re-run idempotency depends on — they are
deliberate, not incidental:

1. **The managed-stamp** — every file the `init` skill *copies or refreshes* gets a stamp on
   its **first line** so a managed copy is unmistakable and machine-parseable. The current
   full form `init` **writes** is:
   - **Markdown:** `<!-- claugentic-dev-harness@{VERSION} managed — do not edit (copied from the claugentic-dev-harness plugin) -->`
   - **Python:** `# claugentic-dev-harness@{VERSION} managed — do not edit (copied from the claugentic-dev-harness plugin)`
   - `{VERSION}` is read from the plugin's `plugin.json` `version` field (e.g. `0.1.0`).
   - **Detection keys on the stable prefix, not the full form.** The trailing clause after
     `do not edit` is **version-variable** — it has changed across releases (early copies
     read `…; run /claugentic-dev-harness:update to refresh`; current copies read
     `… (copied from the claugentic-dev-harness plugin)`). So the **identity test** is the
     **stable managed-stamp prefix** — `claugentic-dev-harness@<semver> managed — do not
     edit` (in the file's comment syntax: markdown `<!-- … -->`, Python `# …`) — **with a
     parseable semver**. A target counts as a **genuine managed copy** only when **line 1
     carries that stable prefix** (one leg of the step-3 predicate — the other is
     path-in-the-managed-set) — not merely a line that *contains* the token; a line that
     merely quotes the token in prose, a foreign stamp, or a garbled semver is a **user
     file**. The semver in the prefix records which plugin version the copy came from; the
     trailing clause is **not** part of the identity test (a REFRESH normalizes an old
     trailing clause to the current full form — step 3).
   - **Only the DETECTION/identity test tolerates the variable trailing clause; what `init`
     WRITES is always the current full form above.** Do **not** vary the written format.

2. **The CLAUDE.md `harness:managed` fence** — the harness section the `init` skill writes
   into the adopter's `CLAUDE.md` lives between exact HTML-comment markers:
   ```
   <!-- harness:managed:start -->
   …managed pointer block…
   <!-- harness:managed:end -->
   ```
   **Replace only inside the fence; everything outside it is human-owned and never
   touched.** Mirrors the established `harness-audit:overview` / `harness-audit:backlog`
   (and the product `harness-product:backlog`) fences. **No volatile content
   (timestamps, counters, run-dates) goes inside the
   managed fence** — so a re-run at the same installed version regenerates a
   byte-identical inner block — the zero-diffs-on-a-2nd-run acceptance
   (dogfood-checked) holds. The seeded **Current scope** block lives
   **outside** this fence (local, editable, never overwritten — see step 6).

---

## The 9-step procedure

Run these in order. Each is **detect → upsert-to-installed / refresh-in-fence → report.**

### 1. Preflight

- **Resolve the managed-set source.** When installed as a plugin, the source is the
  plugin root — **`${CLAUDE_PLUGIN_ROOT}`** (verified to expand in skill context). When
  running **from this harness's own repo in dev** (not installed), treat **the repo root**
  as the source. State which you're using in the report.
- **Confirm the target repo root** (the adopter's `${CLAUDE_PROJECT_DIR}` / current repo).
- **Verify Python is available** (the tree-check gate needs it). Detect the interpreter —
  `python`, `python3`, or `py` (try `--version` on each). **Record which one works**; it's
  written into the hook command in step 5. If **none** is found, **report it and continue**
  — note that the tree-check hook won't run until Python is installed, and that the agent
  can fall back to **`Glob`** to generate/maintain the tree. (Report + continue — a missing
  interpreter is not fatal to scaffolding.)

### 2. `git init` if absent

- If the target repo **has no `.git`**, run **`git init`** (the harness leans on version
  control — the tree-check enumerates files via `git ls-files`, and the workflow assumes a
  VCS to land slices against).
- If `.git` **already exists**, **skip** and report "git already initialized."

### 3. Upsert the managed harness set to the installed version (stamped)

**Upsert** each file in the managed set from the source (step 1) into the target — create
it if absent, **refresh it if a genuine managed copy has drifted from the installed
source**, and leave it byte-untouched if it is already current — **stamping the first
line** with the managed-stamp (convention 1). The managed set is exactly:

| Source path | What it is |
|---|---|
| `docs/standards/` | the **11 authored modules** + `_TEMPLATE.md` + `README.md` (the whole catalog directory) |
| `docs/WORKFLOW.md` | the staged development workflow (process source of truth) |
| `docs/ENGINEERING_STANDARDS.md` | the thin standards entry point |
| `docs/PLAYBOOK.md` | the plain-English guide for the human driving the harness |
| `docs/PRODUCT_SPEC_TEMPLATE.md` | the product-spec contract template (pure verbatim copy; the filled `docs/PRODUCT_SPEC.md` is user-owned, never managed) |
| `scripts/check_architecture_tree.py` | the deterministic architecture-tree gate |

**Per file, decide one of four verdicts (this is `init`'s judgment, rule-bound — there is
no oracle):**

| Detected state | Verdict | Action | Report line |
|---|---|---|---|
| target **absent** | `CREATE` | copy + stamp (installed version) | `created` |
| present, **not a genuine managed copy** (see predicate) | `USER_FILE` | **skip — never overwrite** | `skipped (user file / unrecognized stamp) — reconcile manually` |
| genuine managed copy, **body differs from source** OR **stamp not in the current full form** | `REFRESH` | overwrite the whole file with freshly-stamped source — **migrating the stamp to the current full form** (stamp = installed version) | `refreshed <path>: <old-semver> → <installed>` |
| genuine managed copy, **body identical to source AND stamp already in the current full form** | `CURRENT` | **leave byte-for-byte untouched** — even if its stamp semver is older than installed (**no RESTAMP**) | `skipped (already current)` |

**The genuine-managed predicate (never-clobber-critical — rule-bound, not eyeballed
loosely).** A target file is a **genuine managed copy** — and therefore a REFRESH/CURRENT
candidate — **only when all** hold:
1. its **path is in the managed set above** (a path outside the set is never a refresh
   candidate, whatever its first line);
2. **line 1 leads with the stable managed-stamp prefix** (the prefix immediately follows
   the comment opener — line 1 must *begin* with it, not merely *contain* it) —
   `claugentic-dev-harness@<semver> managed — do not edit` in the file's comment syntax
   (markdown `<!-- … -->`, Python `# …`) — **with a parseable semver**. The **trailing clause after `do not edit` is
   version-variable** and is **NOT** part of the identity test: it has changed across
   releases — early copies read `…; run /claugentic-dev-harness:update to refresh`, current
   copies read `… (copied from the claugentic-dev-harness plugin)` — so the predicate
   **matches the stable prefix only**. (This is why an old-format-but-genuine managed file —
   e.g. an `0.1.1` adopter — is still recognized and refreshed, rather than misclassified as
   a user file and skipped forever; a REFRESH then migrates its stamp to the current full
   form.)

**Anything else is `USER_FILE` → skip and report (never overwrite):** an unstamped
same-named file; a **line 1 that does NOT lead with the `claugentic-dev-harness@<semver>
managed — do not edit` prefix** — a mere quote of the token (`claugentic-dev-harness@<semver>`)
in prose, or the token sitting elsewhere on the line, does **not** match (the full
`@<semver> managed — do not edit` prefix must lead line 1); a *foreign* plugin's stamp; or a
**garbled/unparseable semver**. (A bare token quote stays excluded precisely because the
full prefix on line 1 of a managed-set path is required — the trailing-clause tolerance does
**not** weaken this: leg 1 path-in-set + leg 2 line-1 prefix are both still mandatory. One
honest narrowing vs 0010's exact-form rule: text a user appended *after* `do not edit` on
line 1 of a managed file — incidentally `USER_FILE` under the old exact match — is now part
of the version-variable trailing clause, so a REFRESH replaces it and reports it, like any
other edit to a do-not-edit file.) This wires directly to the
load-bearing **stop-if-ambiguous invariant** (above): with no mechanical oracle, REFRESH
only when the file is **unambiguously** a genuine managed copy; on **any** ambiguity about
whether a write would destroy user content, **stop and report rather than guess.** That
stop-if-ambiguous rule **is** the never-clobber safety net here.

**The body compare (the off-by-one + CRLF traps — get this exactly right):**
- **Asymmetric, unambiguous:** `target body = target minus line 1` (the stamp); `source
  body = the pristine source as-is` (sources carry **no** stamp). For
  `check_architecture_tree.py`, strip **only line 1** (the stamp) — the
  `#!/usr/bin/env python3` shebang on line 2 **stays in the body** (it is part of the
  pristine source). Stripping the shebang too would misalign every Python compare by one
  line and false-REFRESH it.
- **Newline-insensitive:** compare **normalized for line endings** (LF/CRLF equivalent +
  trailing-newline insensitive) so an adopter's checkout settings (Windows `autocrlf` →
  CRLF) never trigger a false REFRESH. This repo's `.gitattributes` does **not** reach an
  adopter's repo, so a CRLF checkout with an identical body must read `CURRENT`, not
  `REFRESH`.
- **Stamp-format check sits *alongside* the body compare for the CURRENT/REFRESH split:**
  `CURRENT` requires **both** an identical body **and** line 1 already in the **current full
  form**. The body compare strips line 1, so an old-format-but-genuine copy with a matching
  body would compare body-identical — but its line-1 stamp is still in an old trailing-clause
  format, so it reads `REFRESH` (a one-time stamp-format migration, above), not `CURRENT`.
  After that migration the file is in the current full form and re-reads `CURRENT`.

**The one hybrid managed file — `check_architecture_tree.py`'s `INCLUDE_GLOBS` (the named
exception to "managed files carry zero user content").** Four of the five managed files are
pure verbatim copies, but `scripts/check_architecture_tree.py` carries **one per-repo
region**: its `INCLUDE_GLOBS = [ … ]` assignment (the **only** per-repo knob — `init`
itself writes it per-adopter in step 5a, re-derives it on glob-drift, and **invites the
user to refine it**). A correctly-configured adopter's globs therefore differ from this
repo's source value, so without a carve-out the file would **always** read REFRESH and the
overwrite would **reset their globs to this repo's value** — a never-clobber violation plus
a broken tree-check for them. Treat it as a **hybrid, exactly like the `CLAUDE.md` fence**
(protect the per-repo region, refresh the managed rest):
- **The body compare for `check_architecture_tree.py` excludes the `INCLUDE_GLOBS = [ … ]`
  assignment** (from the line beginning `INCLUDE_GLOBS =` through its closing `]`) on
  **both** sides. So an adopter with custom globs reads **CURRENT** when the rest of the
  managed body matches — no false REFRESH.
- **A REFRESH preserves (re-injects) the adopter's existing `INCLUDE_GLOBS`:** write `the
  new source body, minus its INCLUDE_GLOBS assignment` + `the adopter's current
  INCLUDE_GLOBS assignment` + the installed stamp — never the source's globs. (Then init's
  existing step-5 glob-drift self-correction runs as today.) With this carve-out the
  never-clobber and idempotent-at-a-fixed-version claims stand **as written**.
- **Assumption (stated so the carve-out is well-defined):** `INCLUDE_GLOBS` is the single,
  stable per-repo knob in this file. If a future plugin version restructures it, that's a
  version-migration concern — **out of scope** here (it becomes a migration task only if
  such a restructure ever ships).

**Per-file upsert only — `init` never deletes.** Each managed-set path is created,
refreshed, or left alone independently; nothing is removed. A user-added file under
`docs/standards/` (e.g. `docs/standards/my-custom.md`) is **left untouched** (it is not in
the managed set). A managed module the **installed version no longer ships** is **left in
place and reported**, never deleted (this is upsert, not `rsync --delete`).

Rules:
- **Stamp on copy/refresh**, not in the source. The source modules are pristine (editable
  upstream) and carry **no** stamp; the `init` skill adds the stamp as the written file's
  first line — markdown files get the `<!-- … -->` form, the Python script gets the `# …`
  form (as its first line, after which the existing `#!/usr/bin/env python3` shebang and
  body follow — keep the file runnable). A REFRESH writes the **installed** version into the
  stamp **in the current full form** (`… (copied from the claugentic-dev-harness plugin)`),
  **migrating any old trailing-clause stamp** to that form; a CURRENT file keeps its older
  stamp untouched (the authoritative repo-version readout is the `CLAUDE.md` managed fence —
  step 6 — not the per-file stamps; mixed per-file stamps are expected and correct).
- **A stamp-format migration is itself a legitimate REFRESH — even when the body matches.**
  A genuine managed copy whose body is otherwise identical to source but whose **stamp line
  is in an old trailing-clause format** still reads `REFRESH`: the write is a **one-time
  format normalization** of line 1 to the current full form (the body is rewritten from
  pristine source, so the result is byte-identical to a fresh copy — **except the hybrid
  `check_architecture_tree.py`, whose REFRESH still re-injects the adopter's `INCLUDE_GLOBS`
  per the carve-out above**, so it is byte-identical apart from the preserved globs). This is **distinct
  from the no-RESTAMP rule**: no-RESTAMP is about *not bumping the version semver* of a
  byte-identical, **already-current-format** file; stamp-format migration is about
  *normalizing the line-1 format* of an old-format file. After it runs once, the file is in
  the current full form and a re-run reads `CURRENT` (idempotent at a fixed version).
- **Security / exclude-set:** upsert **only** the managed set above. **Never** copy the
  adopter's `node_modules`, build output, `vendor`, or secrets (`.env*`, keys,
  credentials) into the repo or surface their contents. This step copies *from the
  harness source*, so it touches none of those — but the same exclude discipline governs
  the tree generation in step 4.

### 4. Generate `docs/ARCHITECTURE_TREE.md` (only if absent)

- **If `docs/ARCHITECTURE_TREE.md` already exists, leave it (the user's tree wins) and
  report "skipped (present)."**
- **If absent, generate it — using the *same* in-scope file list the gate polices**
  (DRY, and so the gate can't reject the tree init just wrote):
  1. First do step 5's glob-detection (so `INCLUDE_GLOBS` in the **copied** script is set).
  2. Derive the file list from **`git ls-files`** filtered by those just-set globs — this
     is exactly what the copied `check_architecture_tree.py`'s `in_scope_files()` computes
     (tracked + staged + untracked-not-ignored, minus exclusions). Honoring `.gitignore`
     via git means deps/build/generated trees are excluded for free.
  3. Write the tree: a short intro + one `- \`path\` — <one-line description>` line **per
     in-scope file**, authored from a cheap read of each (manifest/header/obvious role —
     budget-disciplined, not a deep read). Group by directory.
  4. **Run the copied gate (`check_architecture_tree.py`) and reconcile to green** — the
     **gate is the oracle.** If it reports a missing entry, add it; if it reports a stale
     entry, remove it. Loop until the gate passes. This guarantees the generated tree and
     the gate that will police it **agree by construction**.

### 5. Set the tree-check globs + wire the hook

**(a) Set `INCLUDE_GLOBS` in the *copied* `check_architecture_tree.py`.**
`INCLUDE_GLOBS` is the **only** per-repo knob in the script — the staleness check derives
its valid extensions from it (`EXTS`), so there is no second regex to keep in sync. Set it:
- **Reuse the layout detection from `/claugentic-dev-harness:audit` Phase 1 (Understand)** — its
  ecosystem/manifest detection identifies the source layout (e.g. `src/**/*.ts`,
  `src/**/*.py`, `cmd/**/*.go`). **Do not author a second detector** (DRY). Map the
  detected layout to the git pathspec **extension** globs (`:(glob)src/**/*.ts`,
  `:(glob)src/**/*.tsx`, `:(glob)cmd/**/*.go`, …) for `INCLUDE_GLOBS`.
- **Always emit extension globs** (every entry ends in `*.<ext>`) so `EXTS` is derivable
  and the staleness check works. **Never** set a bare directory glob (e.g. `:(glob)src/**`):
  the script still presence-checks those files but cannot staleness-check them.
- **Unmappable ecosystem?** Emit the **dominant source *extensions*** under the main source
  dir as extension globs (e.g. `:(glob)src/**/*.rb`, `:(glob)src/**/*.erb`) — never a bare
  directory glob — and **report** "globs set conservatively for an unrecognized layout;
  refine `INCLUDE_GLOBS` in `scripts/check_architecture_tree.py` if needed." Never guess a
  layout you can't see — broaden (more extension globs) + flag instead.
- **No application source yet?** When the *Application source present* predicate (defined in
  `/claugentic-dev-harness:audit` Phase 1 — the same detection above, the single source of
  truth) is **false** — an empty / docs-only repo where there is nothing to track — set
  **`INCLUDE_GLOBS = []`** (the safe, well-defined "unset" state: presence/staleness become
  no-ops, never a fail-open whole-repo scan) and **report** "no source yet — file-tracking is
  unset; I'll configure it when you add code." Do **not** guess globs over an empty repo.
- **Terminating self-correction (when the gate later flags zero-coverage drift).** Once real
  code lands, the gate's **drift detection** (mechanical) flags that `INCLUDE_GLOBS` watches
  *no* files while the repo now contains source. The agent then **re-runs this step-5 detection**
  (reusing audit Phase 1 — DRY) and **resets `INCLUDE_GLOBS`** to match the now-visible layout,
  then **reconciles the tree (step-4 loop)**. **Termination:** drift clears the instant the
  reset globs match **≥1** file (`in_scope_files()` non-empty → the gate stops flagging drift);
  if the stack is genuinely unmappable, fall back to the **broaden-and-flag** rule above (emit
  the dominant source-extension globs) — those still match ≥1 file, so drift clears. This
  **never loops forever and never silences drift** — it resets the config so the gate can watch
  the real code.
- Edit **only** the copied script (step 3 placed it). You only set this one constant.

**(b) Wire the hook into `.claude/settings.json` (JSON-merge — the most dangerous write).**
- **Parse** `.claude/settings.json` as JSON. **Absent → treat as `{}`** (and create the
  file). **Present but *malformed* (not valid JSON) → fail loudly: report it and skip the
  merge — never overwrite or corrupt it.**
- Ensure the harness's **two hooks** exist, **appending into the existing arrays** (create
  `hooks` / `PostToolUse` / `Stop` only if absent), **preserving every existing user hook
  and key order**:

  | array | matcher | command |
  |---|---|---|
  | `hooks.PostToolUse` | `Write` | `python "${CLAUDE_PROJECT_DIR}/scripts/check_architecture_tree.py" --hook-write` |
  | `hooks.Stop` | *(none)* | `python "${CLAUDE_PROJECT_DIR}/scripts/check_architecture_tree.py" --hook` |

- Write the **`${CLAUDE_PROJECT_DIR}`-rooted** command (cwd-independent) — **not** the bare
  relative path this source repo uses. Use the **interpreter detected in step 1**
  (`python` / `python3` / `py`) as the leading token.
- **Idempotency key:** a hook whose `command` **contains `check_architecture_tree.py`** is
  "already present." If a `PostToolUse(Write)` entry and a `Stop` entry both already match,
  **skip** (don't append a duplicate) and report "hook already present." This makes a
  re-run a no-op on this file (skip-if-present, keyed on the substring — dogfood-checked
  like the rest of idempotency, not a wired gate).

**(c) Plugin self-reference — declare the harness for teammates (team distribution).**
The harness is a **plugin**: its agents, skills, and engine live in the plugin install,
**not** in the adopter's repo. A teammate who clones the adopter repo gets the committed
standards but **none of the tooling** unless they install the plugin too. So `init` seeds
the harness's **own publication identity** into the adopter's **committed**
`.claude/settings.json`, so Claude Code prompts a teammate to install it on open (the
documented team-distribution mechanism: `extraKnownMarketplaces` + `enabledPlugins`). The
harness's publication identity is fixed: marketplace **`sh4npeiris`** = github
**`sh4npeiris/claugentic-dev-harness`**, plugin **`claugentic-dev-harness`**.

This action **runs regardless of the tree-gate decision in (b)** — it is independent of
whether the architecture-tree hooks got wired (a Python-less or already-hooked repo still
gets the plugin self-reference). It is **strictly never-clobber: merge, never replace** —
every existing key, hook, permission, marketplace, and plugin entry is preserved.

1. **Make `.claude/settings.json` git-trackable.** Read the repo's `.gitignore`. If it
   ignores `.claude/` or `.claude/*` (so `settings.json` would not commit), **append a
   `!.claude/settings.json` negation** — placed **AFTER** the broad ignore line so the
   negation takes effect (a negation before its ignore does nothing). **Never** add
   `!.claude/settings.local.json` — `settings.local.json` MUST stay ignored (local / secret
   config). If `settings.json` is **already trackable** (no `.claude/`-or-`.claude/*` ignore,
   or an existing `!.claude/settings.json` negation already present), **skip the gitignore
   edit** and report "settings.json already trackable." Append-if-line-absent, keyed on the
   `!.claude/settings.json` line — never duplicated.
2. **Create-or-merge `.claude/settings.json`** (same parse-or-`{}` / fail-loud-on-malformed
   rule as (b) — never overwrite or corrupt a present-but-malformed file). **Merge** these
   two entries, **preserving every existing key/hook/permission and every existing
   marketplace/plugin entry** (add, never overwrite a sibling entry):
   - into `extraKnownMarketplaces` (create the map only if absent):
     `"sh4npeiris": { "source": { "source": "github", "repo": "sh4npeiris/claugentic-dev-harness" } }`
   - into `enabledPlugins` (create the map only if absent):
     `"claugentic-dev-harness@sh4npeiris": true`
   - **Idempotency:** if both entries are already present (keyed on the `sh4npeiris`
     marketplace key and the `claugentic-dev-harness@sh4npeiris` plugin key), **skip** and
     report "plugin self-reference already declared." A re-run is a no-op on this file.

This is one logical write to `.claude/settings.json` shared with (b) — apply (b)'s hooks (if
the tree gate wired them) and (c)'s plugin self-reference in the **same** create-or-merge so
the file is parsed and written once, both merges never-clobber.

### 6. Write the CLAUDE.md harness section (create / append-at-EOF / refresh-inside-fence)

Three cases — **never modify existing content outside the managed fence** (the
Current-scope and detected-tooling blocks are *seeded* outside it on first run, but an
existing one is never rewritten — see below):
- **`CLAUDE.md` absent →** create it with the managed pointer block (in the fence) + the
  Current-scope block (outside the fence) below it.
- **Present, *no* `<!-- harness:managed:start -->` fence →** **append** the fenced block at
  **end-of-file**, touching **nothing above** (the user's existing CLAUDE.md is preserved
  verbatim). Seed the Current-scope block after the fence.
- **Present *with* the fence → refresh inside the fence (the re-run path).** Regenerate the
  managed block from the **current** template and **replace only the text between
  `<!-- harness:managed:start -->` and `<!-- harness:managed:end -->`**, preserving
  everything outside the markers **byte-for-byte** (the Current-scope block, the
  detected-tooling block, and all human content above/below). Content-aware: if the
  regenerated inner block is **byte-identical** to what's there, it's a **no-op**; if it
  **differs**, replace it. The fence embeds `claugentic-dev-harness@{VERSION}`, so a
  version bump alone makes it differ → the fence refreshes. **This refreshed fence is the
  authoritative repo-version readout** (the reason per-file stamps need no RESTAMP — step 3).
  - **Malformed fence → stop and report (never guess the extent).** If a
    `<!-- harness:managed:start -->` marker exists **without** its matching
    `<!-- harness:managed:end -->`, or either marker is **duplicated**, the block's extent
    is **ambiguous** — a replace could destroy human content. Per the load-bearing
    never-clobber / stop-if-ambiguous invariant, **stop and report it for manual
    reconciliation**; do **not** guess where the block ends. (Mirrors step 3's explicit
    clobber-edge wiring.)

**What goes in the managed fence** (`<!-- harness:managed:start -->…:end`) — **stable, no
volatile content** so a re-write is byte-identical:
- **Pointers to the local managed files** the agents read (the *same paths*, now local):
  `docs/standards/README.md`, `docs/WORKFLOW.md`, `docs/ENGINEERING_STANDARDS.md`,
  `docs/ARCHITECTURE_TREE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `docs/PLAYBOOK.md`.
- The **engineering principles** (SOLID > DRY > KISS > YAGNI; validate at boundaries;
  fail loudly; configurable over hardcoded; single source of truth).
- A **workflow pointer** ("substantial work follows `docs/WORKFLOW.md`").
- The **plugin version** (`claugentic-dev-harness@{VERSION}`) — a static token, not a date.

**What goes OUTSIDE the managed fence** (local, editable, never overwritten):
- A **Current scope** block, seeded once — a short, non-capping snapshot of which
  standards dimensions are LIVE in this repo today (it grows as the stack grows; relevance
  is always a per-change judgment). This is the per-repo scope the standards catalog
  refers to (it deliberately does **not** live in the managed `ENGINEERING_STANDARDS.md` — that file
  is a managed copy, never the home of per-repo content). Seed it from step 1's detected ecosystem (e.g. for
  a JS web app: `maintainability-structure`, `testing`, `security`, `api-and-contracts`,
  `product-ux`).
- The **detected existing tooling** block (from step 8) — the project's own gates.
  **Seeded create-if-absent, like the Current-scope block:** a re-run **skips** an existing
  detected-tooling block (leaves it byte-untouched), and writes it only when none is present
  — it is never rewritten on a re-run.

### 7. Create `docs/ROADMAP.md` + `docs/DECISIONS.md` if absent

- **`docs/ROADMAP.md` absent →** create a seed (a one-line intro + an empty `## Later`
  human-owned section; `/claugentic-dev-harness:audit` later adds its `harness-audit:overview` /
  `harness-audit:backlog` fences, and `/claugentic-dev-harness:product` gap mode adds its own
  `harness-product:backlog` fence — each self-creates on first run, so `init` seeds **none** of
  them). Present → skip.
- **`docs/DECISIONS.md` absent →** create a seed (the "append newest at top; consult
  before re-litigating" header). Present → skip.

### 8. Detect + record existing tooling (never reconfigure)

- **Scan** for the adopter's own gates: lint/format (`eslint`, `.eslintrc*`, `prettier`),
  type-check (`tsconfig.json`), test runner (`jest`/`vitest`/`pytest`/`go test` config),
  and CI (`.github/workflows`, `.gitlab-ci.yml`). **Reuse `/claugentic-dev-harness:audit` Phase 1's
  tooling detection** (DRY) — it already identifies these by config.
- **Record** what you find in the CLAUDE.md Current-scope-adjacent **detected-tooling
  block** (step 6, outside the managed fence) as **the project's gates** — the workflow
  uses *these*, not new ones imposed on top. **Create-if-absent:** write this block only
  when none exists; a re-run **skips** (leaves) an existing detected-tooling block
  untouched, never rewrites it (it lives outside the fence — local, editable, user-owned).
- **Detect + record only — never install, never reconfigure** the adopter's tooling. The
  harness *composes* with what's there.
- **Also detect + record how to RUN the app** (the one line `engine/qa.js` consumes — the
  runtime-verification workflow can't read files, so the invoking skill reads-and-relays this
  line as `args`). **Detection order:**
  1. **A compose file at repo root** (`docker-compose.yml`/`.yaml`, `compose.yml`/`.yaml`) →
     record `docker compose up -d`. Derive the **App URL** from the first published host port
     when it parses cheaply (e.g. `8000:8000` → `http://localhost:8000`); when it doesn't, use
     the fill-in placeholder and add a report line asking the user to complete it.
  2. **Else a dev-server command** via the **same Phase-1 ecosystem detection steps 5/8 already
     reuse** (DRY): `package.json` `dev` script (then `start`) run via the detected package
     manager; a Python ASGI/Django heuristic (e.g. `uvicorn <module>:app` / `python manage.py
     runserver`). Pick the App URL from the framework's conventional dev port.
  3. **Undetectable** → record the honest placeholder and report it:
     `- Run the app: (not detected — fill in: \`<command>\` · App URL: \`<url>\`)`.
- **The ONE durable home** is a labeled line in the **detected-tooling block** (the same
  outside-the-fence block from step 6 — already the single user-editable home for "the project's
  own tooling," so no new artifact class is introduced; **DRY**):
  `- Run the app: \`<command>\` · App URL: \`<url>\`` (optionally ` · Stop: \`<command>\``).
- **Never-clobber-safe extension:** the detected-tooling block stays **create-if-absent**, but a
  block that exists **without** a `- Run the app:` line gets that one line **appended**
  (append-if-line-absent, keyed on the `Run the app:` label) — an existing `Run the app:` line is
  **never modified**. Pure addition: no existing content in the block is edited.

### 9. Report

**Lead with a plain-English headline** — before the grouped technical summary — so a
non-engineer reads the reassurance first. **Branch the headline on the Refreshed group (and, when it's empty, on the Created group —
never claim a refresh that didn't happen):**
- **Refreshed empty AND Created empty (a true no-op) →** *"Done — everything is already at
  the installed version; I changed nothing. I did NOT touch any of your code or your own
  files."*
- **Refreshed empty, Created non-empty (a first run / fill-in) →** *"Done — I added a code
  map, a quality checklist, and a safety check. I did NOT change any of your code or
  overwrite your own files — nothing existing was modified."*
- **Refreshed is non-empty →** keep the same lead, then **append the honest caveat:**
  *"Files marked `claugentic-dev-harness managed — do not edit` were refreshed to the
  installed version; if you had edited one of those, your edits were replaced — they're
  listed in the Refreshed group below, and git history keeps any version you committed
  (uncommitted edits to a managed file are not recoverable — commit before re-running
  `init`)."* Never assert "I did NOT overwrite your own files" unconditionally when a
  managed file was refreshed — that would be false for anyone who edited one. (The
  `CLAUDE.md` fence is separate: only the content between the markers is replaced —
  everything you wrote outside it is preserved.)

Then tell the user the **setup is live** — honestly, so no restart is implied where none is
needed (a skill **cannot** restart a session; don't pretend otherwise):
- The **architecture-tree hook is enforcing now** — `.claude/settings.json` is hot-reloaded by
  Claude Code's file-watcher the moment `init` writes it; the hook needs no restart.
- **You (the agent) have adopted the harness workflow for the rest of this session** — you just
  scaffolded it and follow `docs/WORKFLOW.md` from here, so work continues immediately.
- **Suggest `/clear` or `/compact`** (quick — not a whole new chat) for the cleanest standing
  setup: that's what loads the new `CLAUDE.md` as cached context (it's read once at session start
  and a skill can't force a re-read). Recommend it before a big `audit` run (clean context);
  optional otherwise; in place next session regardless. **Never tell the user they *must* "start
  a fresh chat."**

Then the **next step, branched on whether the repo already has application
source** — the *Application source present* predicate defined in
`/claugentic-dev-harness:audit` Phase 1 (step 5), the same detection this skill reuses in
step 5:
- **Has app source →** *"Next: run `/claugentic-dev-harness:audit` — I'll explain your codebase in
  plain English and write a prioritized backlog of the work worth doing. (A quick `/clear` first
  gives the audit clean context.)"*
- **No app source yet (empty / docs-only) →** *"Next: just tell me what you want to build —
  describe your first feature in plain English and I'll run the workflow. No need to run
  `/claugentic-dev-harness:audit` until there's code to audit."*

Then emit the clear summary, grouped:
- **Created** — files written from scratch (e.g. `ARCHITECTURE_TREE.md`, `ROADMAP.md`) +
  the managed files that were absent and copied + stamped.
- **Refreshed** — managed files (and the CLAUDE.md fence) brought up to the installed
  version because their content had drifted **or their stamp was in an old trailing-clause
  format** (a one-time format migration); **each reported by path** (`<old> → <installed>`).
- **Skipped (already current)** — managed files whose body already matched the installed
  source (left byte-untouched, even if the stamp semver was older).
- **Skipped (user file / unrecognized stamp)** — present files that are not genuine managed
  copies; left untouched, reported so the user can reconcile.
- **Merged** — the settings.json hook entries appended (or "already present").
- **Detected** — the ecosystem, the interpreter, and the existing tooling recorded.

**On a repo already at the installed version, the whole run is a true no-op** that reports
"already at the installed version — nothing to refresh." When managed content had drifted,
the run **converges the repo to the installed version** (the Refreshed group lists what
moved). Idempotency-at-a-fixed-version is the hard check (below) — dogfood-checked, not a
wired gate.

---

## Idempotency at a fixed version — the hard safety check

Re-running `init` **converges the repo to the installed version**, and is a **true no-op
only when the repo is already at the installed version**. The drift decision and the writes
are **`init`'s judgment** (rule-bound, never-clobber-guarded by stop-if-ambiguous), **not a
mechanical oracle** — so idempotency here is **checked by a dogfood run, not a wired gate.**
At a fixed installed version it holds because:
- Every **managed file** is upserted: absent → create; genuine managed copy with an
  identical body **and a current-form stamp** → `CURRENT` (byte-untouched); a drifted body
  **or an old-format stamp** → `REFRESH` once to the installed version (the stamp is
  migrated to the current full form), after which a re-run reads `CURRENT`.
- Every **generate/create** (tree, ROADMAP, DECISIONS) is create-if-absent (user-owned —
  never refreshed).
- The **settings.json** merge is keyed on a `command` containing `check_architecture_tree.py`
  (present → skip; never a duplicate append).
- The **CLAUDE.md** fence is refreshed inside the markers from a template with **no volatile
  content**, so once it embeds the installed `{VERSION}` a re-run regenerates a
  byte-identical inner block → no-op (everything outside the markers is preserved
  byte-for-byte).

**Acceptance of a 2nd run at the same installed version:** `git status` in the target shows
**zero changes** and the report says everything was already current. If such a re-run
dirties the repo, an idempotency guard is missing — that is a bug, not expected behavior.
(A re-run *after a version bump* is expected to refresh — that is convergence, not a bug.)

## What this skill does NOT do (honest scope)

- It does **not** install or reconfigure your linters/test runner — it **detects and
  records** them (step 8) so the workflow composes with them.
- It does **not** refresh your **user-owned** files — `docs/ARCHITECTURE_TREE.md`,
  `docs/ROADMAP.md`, and `docs/DECISIONS.md` are seeded create-if-absent and then left to
  you (they carry your content, not managed content).
- It does **not** 3-way-merge a user-edited **managed** file — managed files are marked
  *do not edit* and carry no user content by contract (sole exception: the
  `check_architecture_tree.py` `INCLUDE_GLOBS` knob, preserved per step 3); on a genuine
  drift the installed version wins (reported by path) and **git is the review/recovery
  net** for content you committed (an uncommitted edit isn't recoverable — see the roadmap).
- It does **not** reconcile the `settings.json` hook **command string** if its format
  changes between versions — the hook is keyed only on the `check_architecture_tree.py`
  substring (out of scope; tracked on the roadmap).
- It does **not** audit your code or write a backlog — that is **`/claugentic-dev-harness:audit`**.
