---
description: Scaffold the claugentic-dev-harness into the current repo — upsert the managed harness set (standards catalog, workflow, playbook, tree-check) to the installed plugin version, generate docs/claugentic-ARCHITECTURE_TREE.md, set the tree-check globs, wire the pre-commit hook, declares the plugin for teammates (seeds the harness's plugin self-reference into the committed .claude/settings.json so a cloned adopter repo prompts teammates to install it), git-init if needed, seed ROADMAP/DECISIONS, refresh the CLAUDE.md harness fence, and compose with existing lint/type-check/test tooling. Asks Shared (default — committed for the team) vs Solo / local-only (this clone alone via .git/info/exclude + .git/hooks/pre-commit + CLAUDE.local.md, leaving git status clean and the committed .gitignore untouched). Re-running converges the repo to the installed version and never clobbers user content; a true no-op only when already at the installed version.
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
- **Resolve the harness mode — Shared (default) or Solo / local-only.** This one choice
  governs four later divergences (steps 3, 5b, 5c, 6); resolve it **here**, before step 3
  writes any managed docs, so every diverging step reads a single settled value.
  - **Read the recorded mode FIRST (re-run idempotency, mirrors step 4's tree-choice
    contract).** Before any prompt, read the **`- Harness mode:` line** from the
    detected-tooling block — the local CLAUDE source for it is `CLAUDE.local.md` in solo
    mode, the `CLAUDE.md` detected-tooling block in shared mode (check both; either presence
    settles it). **Exact line:** `- Harness mode: <shared | solo (local-only)>`, keyed on the
    `Harness mode:` label. If present, **honor it and skip the prompt** (a re-`init` stays
    consistent — a recorded `solo` keeps every solo divergence; a recorded `shared` is exactly
    today's behavior).
  - **No recorded mode → prompt once (AskUserQuestion):** *"Adopt the harness **Shared with
    teammates** (the managed docs, tree gate, and plugin self-reference are committed so the
    whole team gets them), or **Solo / local-only** (you dogfood it on this clone alone — `git
    status` stays clean, your `.gitignore` is untouched, and a teammate's clone is unaffected)?"*
    **Default — and the value on silence / a timeout / AskUserQuestion being unavailable — is
    Shared** (no change for an existing adopter or the no-question path; the same
    confirmation discipline as the step-4 Replace prompt — never diverge to the less-common
    branch without an explicit choice).
  - **Record the chosen/honored mode** so a re-run reads it: step 6 writes the `- Harness
    mode:` line into the detected-tooling block (in `CLAUDE.local.md` for solo, in `CLAUDE.md`
    for shared), append-if-line-absent on the `Harness mode:` label. Recording it is what makes
    **make-invalid-states-unrepresentable** hold: a recorded `solo` short-circuits the shared
    branches (step 5c never runs; the pre-commit hook never goes to `.githooks/`).
  - **Shared mode = the steps exactly as written below (today's S4a behavior — unchanged).**
    **Solo mode diverges in exactly four places, each flagged inline as a `> **Solo
    divergence**` block — and nowhere else.** The solo invariant the divergences exist to
    uphold: **solo writes ZERO new tracked paths, makes NO edit to the committed `.gitignore`,
    and sets NO shared git config** — so `git status` stays clean and a teammate's clone is
    byte-identical. Everything not flagged as a solo divergence is identical in both modes.

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
| `docs/claugentic-standards/` | the **11 authored modules** + `_TEMPLATE.md` + `README.md` (the whole catalog directory) |
| `docs/claugentic-WORKFLOW.md` | the staged development workflow (process source of truth) |
| `docs/claugentic-ENGINEERING_STANDARDS.md` | the thin standards entry point |
| `docs/claugentic-PLAYBOOK.md` | the plain-English guide for the human driving the harness |
| `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` | the product-spec contract template (pure verbatim copy; the filled `docs/claugentic-PRODUCT_SPEC.md` is user-owned, never managed) |
| `docs/claugentic-PLAN_TEMPLATE.md` | the plan-file contract template (verbatim copy; adopters copy one per plan into their own .claude/plans/) |
| `scripts/claugentic-check_architecture_tree.py` | the deterministic architecture-tree gate |

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
  `claugentic-check_architecture_tree.py`, strip **only line 1** (the stamp) — the
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

**The one hybrid managed file — `claugentic-check_architecture_tree.py`'s `INCLUDE_GLOBS` (the named
exception to "managed files carry zero user content").** Four of the five managed files are
pure verbatim copies, but `scripts/claugentic-check_architecture_tree.py` carries **one per-repo
region**: its `INCLUDE_GLOBS = [ … ]` assignment (the **only** per-repo knob — `init`
itself writes it per-adopter in step 5a, re-derives it on glob-drift, and **invites the
user to refine it**). A correctly-configured adopter's globs therefore differ from this
repo's source value, so without a carve-out the file would **always** read REFRESH and the
overwrite would **reset their globs to this repo's value** — a never-clobber violation plus
a broken tree-check for them. Treat it as a **hybrid, exactly like the `CLAUDE.md` fence**
(protect the per-repo region, refresh the managed rest):
- **The body compare for `claugentic-check_architecture_tree.py` excludes the `INCLUDE_GLOBS = [ … ]`
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
`docs/claugentic-standards/` (e.g. `docs/claugentic-standards/my-custom.md`) is **left untouched** (it is not in
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
  `claugentic-check_architecture_tree.py`, whose REFRESH still re-injects the adopter's `INCLUDE_GLOBS`
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

> **Solo divergence (a) — managed paths → `.git/info/exclude`, NEVER the committed
> `.gitignore`.** In **solo mode**, every managed file `init` writes to disk (the managed
> set above, plus the generated tree from step 4 and the copied tree script from step 5a) is
> written **exactly as in shared mode** — but its path/path-pattern is then **appended to
> `.git/info/exclude`** so `git status` shows it as ignored (nothing to commit). `.git/info/exclude`
> is **per-clone and inherently untracked** (`.git/` is never tracked) — it does the same job as
> `.gitignore` for *this* clone only, so a teammate's clone never sees these paths. **NEVER edit the
> committed `.gitignore` in solo mode** (it is a tracked file — an edit disturbs teammates and
> breaks the solo invariant). Append the patterns that cover what `init` actually wrote:
> `docs/claugentic-*` (the managed docs + tree + DECISIONS/ROADMAP/CHARTER seeds — the `docs/claugentic-*`
> glob auto-routes the copied `CHARTER.md` local in solo, no new divergence needed), `docs/claugentic-standards/`,
> `scripts/claugentic-check_architecture_tree.py`, and `CLAUDE.local.md` (step 6). **Append-if-absent**
> (keyed on each pattern line — never duplicate a line on a re-run) so a re-`init` is a no-op on
> `.git/info/exclude`. In **shared mode** none of this runs — managed paths commit normally and the
> committed `.gitignore` is the only ignore surface (step 5c manages its negation).

### 4. Provision `docs/claugentic-ARCHITECTURE_TREE.md` (scenario-based) + decide the tree-gate

The tree action is **scenario-based** — `init` detects the repo's situation and acts. The
scenario is fixed by **two reused signals** (DRY — no new detector): (1) the presence of
`docs/claugentic-ARCHITECTURE_TREE.md`, and (2) the *Application source present* predicate defined in
`/claugentic-dev-harness:audit` Phase 1 (the same detection step 5a reuses). The decision
made here — **which globs, whether to build a skeleton, and whether the tree-gate is on or
off** — is the input step 5b wires the hooks against (step 5c also depends on it).

**Read the recorded choice FIRST (re-run idempotency).** Before any prompt, read the
**recorded-choice line** from the detected-tooling block (the contract below). It governs
the mature-with-tree path so a re-`init` never re-prompts. **On-disk state wins:** if the
record says `keep-gate-off` but the tree is now **absent** (the user deleted it), take the
mature-no-tree path regardless and refresh the record (see the contract). A malformed or
absent record falls back to prompting — safe, dirties nothing.

The three scenarios — **detect → tree action → `INCLUDE_GLOBS` → gate decision**:

- **Fresh** (no tree **and** *Application source present* = **false** — an empty / docs-only
  repo): run step 5a (→ `INCLUDE_GLOBS = []` per step 5a's "No application source yet" rule,
  or detected globs if any source exists) → create a **minimal** tree (a short intro + the
  docs/ scaffolding lines it can see) → **gate ON** (step 5b wires the **pre-commit hook**;
  the commit gate enforces the tree as files land and get committed). Report "created
  (minimal — fills in as you add code)."

- **Mature, no tree** (no tree **and** source present): run step 5a → derive the **real**
  globs → build the **cheap-complete skeleton** from those globs (below) → reconcile via the
  step-4 gate loop (the gate is the oracle) → **gate ON** (step 5b wires the **pre-commit
  hook** — the skeleton lists every path, so the first commit's gate reconciles green and
  never false-trips). `INCLUDE_GLOBS` = the detected real globs. Report "created
  (skeleton from `git ls-files` — every path listed, descriptions enrich over time)."

- **Mature, with tree** (tree present, and no honored `keep-gate-off` record): **skip the
  skeleton build entirely** (the tree exists — never overwrite it unasked) → run the
  **two-option prompt** below. If the recorded choice is already `harness-skeleton (gate
  on)` from a prior Replace, re-derive nothing destructive: treat it as mature-no-tree only
  if the tree is absent; otherwise the tree is already a managed skeleton and step 5b wires
  the gate ON per the record (no re-prompt).

**The cheap-complete skeleton** (mature-no-tree, and the Replace branch) — **how to build it
without per-file content reads** (the whole point: the *path list* is a millisecond
`git ls-files`; the expense was the descriptions, which the skeleton skips):
  1. Step 5a has already set `INCLUDE_GLOBS` in the **copied** script to the real globs.
  2. Derive the file list from **`git ls-files`** filtered by those globs — exactly what the
     copied `claugentic-check_architecture_tree.py`'s `in_scope_files()` computes (tracked + staged +
     untracked-not-ignored, minus exclusions). Honoring `.gitignore` via git excludes
     deps/build/generated trees for free.
  3. Write the skeleton: a short intro, then **one `- \`path\`` line per in-scope file**,
     **grouped under markdown headings by directory** (e.g. `## src/api`), each line a
     **thin, path-derived one-liner** (the filename/dir role — **NO per-file content reads**;
     descriptions enrich best-effort later via the existing "update a file's line when you
     change its role" convention — never gate-checked).
  4. **CRITICAL — format guard (the regression this slice exists to fix):** the skeleton uses
     **markdown headings + `- \`path\`` lines and NEVER ` ``` `-fenced code blocks.** A fence
     is stripped by `_strip_fenced_blocks` (`scripts/claugentic-check_architecture_tree.py:129-150`)
     and would desync the presence-matching pairing — the exact bug that read fenced-diagram trees
     as 0% coverage. Never emit an ASCII directory diagram; emit backtick-prose lines.
  5. **Run the copied gate and reconcile to green** — the **gate is the oracle.** Missing
     entry → add it; stale entry → remove it; loop until green. The skeleton lists every
     path, so it satisfies presence from day 1 → the first commit's pre-commit gate never
     false-trips.

**The mature-with-tree prompt (two options — non-destructive).** When `init` finds an
existing `docs/claugentic-ARCHITECTURE_TREE.md` and there is no honored recorded choice, it **pauses and
prompts** (AskUserQuestion) with plain-English context — *"You have a
`docs/claugentic-ARCHITECTURE_TREE.md`. The harness tree-gate reads a backtick-prose format and can't
mechanically enforce a fenced ASCII diagram. How do you want to proceed?"*:
  - **Replace with a harness skeleton** → behave as mature-no-tree (step 5a → real globs →
    build the skeleton → reconcile), **overwriting the existing tree** → **gate ON** (step 5b
    wires the **pre-commit hook**). Record `harness-skeleton (gate on)`.
    - **Replace = confirmed user-file overwrite (never-clobber guard).** The tree is a
      **user-owned** file (create-if-absent; step 4 has never overwritten one before).
      Replace proceeds **only** on the explicit AskUserQuestion confirmation — **never** on
      silence, a default, a timeout, or AskUserQuestion being unavailable. On any of those,
      **fall back to Keep-mine-gate-off** and report it (mirroring the never-clobber
      stop-if-ambiguous posture at `:27-28,156-158`). The Stage-9 report **honesty register**
      must name the overwrite explicitly (step 9).
  - **Keep mine, gate off** → leave the tree **untouched**; set `INCLUDE_GLOBS = []`; **gate
    OFF** (step 5b wires **NO** pre-commit hook). Record `kept by adopter (gate off, your init
    choice)`. The `[]` is **adopter-owned**, protected by the existing INCLUDE_GLOBS
    carve-out (`:189-201`): a re-`init` on a `keep-gate-off` repo **MUST NOT re-derive
    globs** (or the gate silently turns back on — a regression against the locked choice).
    (This was previously a circumstantial state, now an explicit choice. To later
    switch a kept tree to the harness format, delete it and re-`init` → mature-no-tree →
    skeleton.)

There is **no third "Skip"** option — it was mechanically identical to Keep-mine-gate-off
(records the choice, wires no hook, no re-prompt), so it is dropped (KISS).

**The recorded-choice contract** _(built here, consumed by the competing-doc sub-step too):_
  - **Lives in** the detected-tooling block (outside the managed fence — create-if-absent).
    Unlike step 8's `Run the app:` line (which is append-once and **never** rewritten), this
    line is a **single-value, label-keyed record that is rewritten in place on
    on-disk-disagreement**: appended on first write (line absent), and thereafter rewritten in
    place **only** when on-disk tree state forces an outcome different from the recorded value.
  - **Exact line:**
    `- Architecture tree: <harness-skeleton (gate on) | kept by adopter (gate off, your init choice)>`
    — **keyed on the label `Architecture tree:`**.
  - **Keying:** append-if-line-absent on that label; **rewrite-in-place on on-disk
    disagreement** (not append-a-second-line — exactly one `Architecture tree:` line exists at
    all times, so there is never an ambiguous pair to tie-break). When the recorded value and
    current on-disk state diverge (e.g. recorded `keep-gate-off` but the tree is now absent),
    rewrite this one line to the honored outcome so the next re-run reads a value consistent
    with on-disk state.
  - **Read-before-prompt:** re-`init` reads this line **before** the mature-with-tree prompt;
    if present and consistent with on-disk state, **honor it and skip the prompt.**
  - **Precedence on disagreement — on-disk state wins for the tree action, and the record is
    rewritten to match.** Tree present + record `kept by adopter (gate off…)` → honor, no
    prompt, gate stays off, **no rewrite**. Tree present + record `harness-skeleton (gate on)`
    → honor, no prompt, **no rewrite**. Tree present + **no** record → prompt, then record.
    **Tree absent** (user deleted it later) → take the mature-no-tree path (build skeleton,
    gate on) **regardless** of the record, and **rewrite the line to `harness-skeleton (gate
    on)`**. Any case where on-disk state and the record disagree → **on-disk state wins and the
    line is rewritten to match the honored outcome.** A malformed/absent record falls back to
    prompting (safe; dirties nothing).
  - **Idempotency:** a **settled** re-run — on-disk state matches the record — performs **no
    rewrite** and the block is **byte-identical**. The rewrite fires only on a genuine state
    change (the repo changed between runs, e.g. the user deleted the tree), which is a correct
    response to new on-disk reality, **not** an idempotency violation.

### 5. Set the tree-check globs + wire the hook (conditional on step 4's gate decision)

**(a) Set `INCLUDE_GLOBS` in the *copied* `claugentic-check_architecture_tree.py`.**
`INCLUDE_GLOBS` is the **only** per-repo knob in the script — the staleness check derives
its valid extensions from it (`EXTS`), so there is no second regex to keep in sync.

**When 5a runs (per step 4's scenario):** the glob-detection below runs for **Fresh**,
**Mature-no-tree**, and the **Replace** branch. For **Keep-mine-gate-off** (the recorded or
chosen `gate off` outcome), 5a sets **`INCLUDE_GLOBS = []` and re-derives NOTHING** — the
`[]` is adopter-owned and protected by the existing INCLUDE_GLOBS carve-out (`:189-201`), so
a re-`init` on a `keep-gate-off` repo must **not** reach the layout-detection below (else the
gate silently turns back on against the locked choice). Set it (for the running scenarios):
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
  refine `INCLUDE_GLOBS` in `scripts/claugentic-check_architecture_tree.py` if needed." Never guess a
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

**(b) Wire the tree gate as a git `pre-commit` hook — CONDITIONAL on step 4's gate
decision.**

**The gate runs once per `git commit`, not per agent action.** The tree only has to be
correct at the durable handoff (the commit → the next session/clone reads it), and the
working agent is in-context at commit time to write a new file's description while it's
fresh. So the gate is a **git pre-commit hook** — a *different* hook system from Claude
Code's `.claude/settings.json` hooks: it is triggered **only by `git commit`** (by git,
never by a tool use), so it adds **zero per-tool-use overhead**. (`init` writes **no**
tree hooks into `.claude/settings.json` — the SessionStart advisor hook stays
plugin-bundled in `plugin.json`, untouched by `init`.)

**The gate decision from step 4 governs the wiring:** the pre-commit hook is wired
**only when the tree-gate is ON** (Fresh, Mature-no-tree, Replace). When the gate is
**OFF** (Keep-mine-gate-off), **wire NO pre-commit hook** and **do not set
`core.hooksPath`** — the kept (non-backtick) tree must never be policed by a blocking gate
that would false-flag it (the measured fenced-diagram 0%-coverage regression). The tree
then stays model-upheld via the CLAUDE.md authority anchor.

- **Gate ON →** wire the pre-commit hook, init-managed (it then travels with the repo,
  one config line per clone):
  1. **Write `.githooks/pre-commit`** — the same wrapper logic this harness ships in its
     own `.githooks/pre-commit`: it resolves the repo root via `git rev-parse
     --show-toplevel` (worktree-safe), picks `python3 || python`, runs
     `scripts/claugentic-check_architecture_tree.py --staged`, and **exit 1 aborts the
     commit** (a git failure resolving the root lets the commit pass — a broken git must
     never block a commit). Wrapper (run-logic identical to the shipped hook; the comment
     header is adopter-appropriate — a fresh adopter has no per-action hooks to "replace"):
     ```sh
     #!/bin/sh
     # claugentic-dev-harness — architecture-tree gate at COMMIT time. Checked once per
     # `git commit`, locally, before the commit is written; a non-zero exit aborts it.
     # `--staged` scopes it to what's being committed. A git failure must never block a
     # commit, so resolve the root defensively and let a clean state pass.
     root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
     if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
     out=$("$PY" "$root/scripts/claugentic-check_architecture_tree.py" --staged 2>&1)
     [ $? -eq 0 ] && exit 0
     printf '%s\n' "$out"
     exit 1
     ```
     **Make it executable** — set the file's exec bit (`chmod +x .githooks/pre-commit`;
     git tracks the bit so a clone inherits it). The wrapper itself prefers `python3` then
     falls back to `python`, so the step-1 interpreter detection is not baked into the file.
  2. **Run `git config core.hooksPath .githooks`** — points git at the tracked hook
     directory so the hook fires on every commit in this clone.
- **Gate OFF (Keep-mine-gate-off) →** wire **no** pre-commit hook: do **not** write
  `.githooks/pre-commit` and do **not** set `core.hooksPath`. (Record the gate-off choice
  via step 4's `Architecture tree:` line as before.)
- **Idempotency — "already wired" = `.githooks/pre-commit` exists AND `core.hooksPath` is
  `.githooks`.** When both hold, **skip** (write nothing, set nothing) and report
  "pre-commit hook already wired" — a re-run is a no-op on this. Read `core.hooksPath` with
  `git config --get core.hooksPath` before setting it.
- **Never-clobber `core.hooksPath`.** If `core.hooksPath` is already set to **something
  other than `.githooks`**, the adopter has their own hook directory — **do NOT overwrite
  it.** Report the conflict (e.g. "core.hooksPath is set to `<value>`; the tree gate's
  `.githooks/pre-commit` was written but not activated — point `core.hooksPath` at it or
  chain it from your own hooks") and **continue** (write `.githooks/pre-commit` so the
  wrapper is on disk, but leave their config untouched). This is the same fail-loud,
  stop-if-ambiguous posture as the rest of `init` — never silently clobber the adopter's
  hook config.

> **Solo divergence (b) — pre-commit hook → `.git/hooks/pre-commit`, NOT `.githooks/` +
> `core.hooksPath`.** In **solo mode** with the gate **ON** (Fresh / Mature-no-tree /
> Replace), write the **same wrapper** (run-logic byte-identical to the shared `.githooks/pre-commit`
> above) to **`.git/hooks/pre-commit`** instead, and **make it executable** (`chmod +x`). That
> path is **inherently local + untracked** (`.git/` is never tracked), so it places **no tracked
> file** and needs **no shared git config** — therefore **do NOT run `git config core.hooksPath
> .githooks`** and **do NOT create a tracked `.githooks/` directory** in solo mode (`.githooks/`
> would be a tracked path — a solo-invariant violation). `core.hooksPath` stays at its git default,
> so `.git/hooks/pre-commit` fires on every commit in this clone. **Never-clobber:** if
> `core.hooksPath` is already set to a **non-default** value, `.git/hooks/` would **not** run — so
> the hook wouldn't fire. Mirroring the shared branch, **REPORT the conflict** ("core.hooksPath is
> set to `<value>`; in solo mode the tree gate's `.git/hooks/pre-commit` was written but won't fire
> while hooksPath points elsewhere — unset it or chain the gate from your own hook") and
> **continue** (write the wrapper to `.git/hooks/pre-commit` so it's on disk; leave their config
> untouched — never silently clobber). **Idempotency:** "already wired" in solo = `.git/hooks/pre-commit`
> exists with the wrapper body → skip (write nothing). **Gate OFF (Keep-mine-gate-off)** wires no
> hook in solo mode either (same as shared). In **shared mode** the `.githooks/` + `core.hooksPath`
> wiring above runs unchanged.

> **Solo divergence (c) — SKIP step 5c entirely.** In **solo mode**, do **not** run any of
> step 5c: no plugin self-reference into `.claude/settings.json`, **no `.gitignore`
> negation** (`!.claude/settings.json`), and **no teammate prompt** on clone. Solo adoption is
> deliberately **invisible to teammates** — declaring the plugin in the committed
> `.claude/settings.json` (and editing the committed `.gitignore` to make it trackable) would
> place a tracked path and a committed-`.gitignore` edit, the exact two things the solo
> invariant forbids. So `init` writes **nothing** to `.claude/settings.json` and **nothing** to
> `.gitignore` in solo mode. (The user installed the plugin on this clone themselves; nothing
> needs to prompt them.) In **shared mode** step 5c runs exactly as written below.

**(c) Plugin self-reference — declare the harness for teammates (team distribution).**
The harness is a **plugin**: its agents, skills, and engine live in the plugin install,
**not** in the adopter's repo. A teammate who clones the adopter repo gets the committed
standards but **none of the tooling** unless they install the plugin too. So `init` seeds
the harness's **own publication identity** into the adopter's **committed**
`.claude/settings.json`, so Claude Code prompts a teammate to install it on open (the
documented team-distribution mechanism: `extraKnownMarketplaces` + `enabledPlugins`). The
harness's publication identity is fixed: marketplace **`sh4npeiris`** = github
**`sh4npeiris/claugentic-dev-harness`**, plugin **`claugentic-dev-harness`**.

This action **runs regardless of the tree-gate decision** that step 4 set and step (b)
acted on (gate ON → pre-commit hook wired; gate OFF → none) — it is independent of whether
the tree gate's pre-commit hook got wired (a Python-less, gate-off, or already-wired repo
still gets the plugin self-reference). **Step (b) writes no tree hooks into
`.claude/settings.json` at all** (the tree gate is now a git pre-commit hook), so this step
is the **only** writer of `.claude/settings.json` — its single job here is the plugin
self-reference. It is **strictly never-clobber: merge, never replace** — every existing
key, hook, permission, marketplace, and plugin entry is preserved.

1. **Make `.claude/settings.json` git-trackable.** Read the repo's `.gitignore`. If it
   ignores `.claude/` or `.claude/*` (so `settings.json` would not commit), **append a
   `!.claude/settings.json` negation** — placed **AFTER** the broad ignore line so the
   negation takes effect (a negation before its ignore does nothing). **Never** add
   `!.claude/settings.local.json` — `settings.local.json` MUST stay ignored (local / secret
   config). If `settings.json` is **already trackable** (no `.claude/`-or-`.claude/*` ignore,
   or an existing `!.claude/settings.json` negation already present), **skip the gitignore
   edit** and report "settings.json already trackable." Append-if-line-absent, keyed on the
   `!.claude/settings.json` line — never duplicated.
2. **Create-or-merge `.claude/settings.json`.** **Parse** it as JSON; **absent → treat as
   `{}`** (and create the file); **present but *malformed* (not valid JSON) → fail loudly:
   report it and skip the merge — never overwrite or corrupt it.** **Merge** these
   two entries, **preserving every existing key/hook/permission and every existing
   marketplace/plugin entry** (add, never overwrite a sibling entry):
   - into `extraKnownMarketplaces` (create the map only if absent):
     `"sh4npeiris": { "source": { "source": "github", "repo": "sh4npeiris/claugentic-dev-harness" } }`
   - into `enabledPlugins` (create the map only if absent):
     `"claugentic-dev-harness@sh4npeiris": true`
   - **Idempotency:** if both entries are already present (keyed on the `sh4npeiris`
     marketplace key and the `claugentic-dev-harness@sh4npeiris` plugin key), **skip** and
     report "plugin self-reference already declared." A re-run is a no-op on this file.

This is the **only** write to `.claude/settings.json` — (b) no longer touches it (the tree
gate is a git pre-commit hook). So `.claude/settings.json` is parsed and written once here,
the plugin-self-reference merge never-clobber.

### 6. Write the CLAUDE.md harness section (create / append-at-EOF / refresh-inside-fence)

> **Solo divergence (d) — the harness anchor → `CLAUDE.local.md`, NOT the committed
> `CLAUDE.md`.** In **solo mode**, write **everything this step writes** — the managed fence,
> the seeded **Current scope** block, and the **detected-tooling block** (including the
> recorded `- Harness mode: solo (local-only)`, `- Architecture tree:`, and `- Run the app:`
> lines from steps 1/4/8) — into **`CLAUDE.local.md`** instead of `CLAUDE.md`. `CLAUDE.local.md`
> is Claude Code's conventional **local** anchor (loaded as repo context like `CLAUDE.md`); **git
> does NOT ignore it by default** — divergence (a) above appends it to `.git/info/exclude`, and
> that is what keeps it untracked on this clone, so the committed `CLAUDE.md` is left
> **byte-untouched** (a teammate's clone never sees the harness fence). **All three cases below
> (absent / no-fence / refresh-in-fence) apply unchanged — just to `CLAUDE.local.md` as the
> target file.** The `Harness mode:` line written here is what a re-`init` reads in step 1 to
> stay in solo mode. In **shared mode** this step writes to `CLAUDE.md` exactly as below.

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
  `docs/claugentic-standards/README.md`, `docs/claugentic-WORKFLOW.md`, `docs/claugentic-ENGINEERING_STANDARDS.md`,
  `docs/claugentic-ARCHITECTURE_TREE.md`, `docs/claugentic-DECISIONS.md`, `docs/claugentic-ROADMAP.md`, `docs/claugentic-PLAYBOOK.md`,
  and the optional engineering charter → `docs/claugentic-CHARTER.md` (the living per-work-type
  methodology record — empty ≡ the harness's default behavior). A stable pointer line, byte-identical every run.
  - A **static adoption-notes pointer**: `docs/claugentic-PLAYBOOK.md` covers how to drive the
    harness plus adoption notes — including that the architecture-tree check runs at commit time,
    not while you edit. One fixed line, byte-identical every run (no volatile content).
- The **engineering principles** (SOLID > DRY > KISS > YAGNI; validate at boundaries;
  fail loudly; configurable over hardcoded; single source of truth).
- A **workflow pointer** ("substantial work follows `docs/claugentic-WORKFLOW.md`").
- An **authority + conflict-resolution clause** (static managed content — same byte block
  every run, so the fence stays byte-identical). It establishes the harness docs as the
  process authority and tells an agent what to do on a conflict. Write it **honestly as
  model-upheld** — `CLAUDE.md` is the always-loaded anchor and "ask when in doubt" is the
  safety valve; there is **no** mechanical file-hiding, so it must not claim a mechanical
  guarantee. Use this wording (verbatim — it is part of the byte-identical fence):
  > **How we work here is defined by the harness.** `docs/claugentic-WORKFLOW.md`,
  > `docs/claugentic-ENGINEERING_STANDARDS.md`, `docs/claugentic-PLAYBOOK.md`, and `docs/claugentic-ARCHITECTURE_TREE.md` are
  > the **authoritative** process + standards. Other `.md` files in this repo are
  > **project/domain content, not process authority** — even if they describe a way of
  > working, they do not override the harness. **On any conflict, the harness wins.** When
  > you are genuinely unsure which applies, **follow the harness and ask.** (This is
  > model-upheld guidance, not a mechanical guarantee — `CLAUDE.md` is the always-loaded
  > anchor and asking is the safety valve.)
- The **plugin version** (`claugentic-dev-harness@{VERSION}`) — a static token, not a date.

**What goes OUTSIDE the managed fence** (local, editable, never overwritten):
- A **Current scope** block, seeded once — a short, non-capping snapshot of which
  standards dimensions are LIVE in this repo today (it grows as the stack grows; relevance
  is always a per-change judgment). This is the per-repo scope the standards catalog
  refers to (it deliberately does **not** live in the managed `claugentic-ENGINEERING_STANDARDS.md` — that file
  is a managed copy, never the home of per-repo content). Seed it from step 1's detected ecosystem (e.g. for
  a JS web app: `maintainability-structure`, `testing`, `security`, `api-and-contracts`,
  `product-ux`).
- The **detected existing tooling** block (from step 8) — the project's own gates.
  **Seeded create-if-absent, like the Current-scope block:** a re-run **skips** an existing
  detected-tooling block (leaves it byte-untouched), and writes it only when none is present
  — it is never rewritten on a re-run. **Two labeled lines inside it are the exception**,
  append-if-line-absent, keyed on their label: the `- Run the app:` line (step 8), which is
  **never rewritten**; and the `- Architecture tree:` recorded-choice line (step 4's contract,
  step 8), which is **rewritten in place only on on-disk disagreement** (e.g. the tree was
  deleted between runs) and is otherwise left untouched (a settled re-run is byte-identical).

### 7. Seed `docs/claugentic-ROADMAP.md` + `docs/claugentic-DECISIONS.md` + `docs/claugentic-CHARTER.md` if absent (the one-time-seed kind)

These three are the **one-time-seed** managed-file kind (the third kind in the WORKFLOW
Adopter-note's three-kinds taxonomy). The seed bytes are **shipped pristine `_X.md` files** in
the plugin — `init` **copies them, stripping the leading underscore**:

- copy **`${SOURCE}/docs/claugentic-_DECISIONS.md` → `docs/claugentic-DECISIONS.md`**,
- copy **`${SOURCE}/docs/claugentic-_ROADMAP.md` → `docs/claugentic-ROADMAP.md`**, and
- copy **`${SOURCE}/docs/claugentic-_CHARTER.md` → `docs/claugentic-CHARTER.md`** (the
  OPTIONAL engineering charter — the living per-work-type methodology record; **no forced
  "pick your methodology" question**, `init` just copies the seed and points at it in the
  fence below — an empty/absent charter ≡ the harness's default behavior).

(`${SOURCE}` is the managed-set source resolved in step 1 — `${CLAUDE_PLUGIN_ROOT}` installed, the
repo root in dev — the same source the step-3 managed-copy uses.)

- **CREATE-IF-ABSENT ONLY — never refresh, never clobber.** If the target already exists, **skip
  it byte-untouched** (report `skipped (present)`); only write when absent (report `created`). A
  filled `DECISIONS.md`/`ROADMAP.md`/`CHARTER.md` is an adopter's own file — re-`init` must never
  overwrite it.
- **The underscore-prefix convention (`_X.md` → `X.md`):** a leading-underscore source file is a
  **one-time seed** — copied once, renamed by stripping the underscore, and **never refreshed**.
  This is **distinct from `*_TEMPLATE.md`** (the repeated-use templates — plan / product-spec /
  standards-module skeletons — which an adopter keeps and copies one per use, and which the step-3
  managed set DOES refresh). See WORKFLOW → Adopter note → the three managed-file kinds.
- **Seeds stay OUT of the managed-set table (step 3) — deliberately.** They are NOT refreshed, so
  they must never enter the four-verdict REFRESH upsert (a REFRESH would clobber a filled ledger).
  Two guards keep that safe: this step is create-if-absent (a present file is skipped), AND a path
  outside the managed set can never satisfy the genuine-managed predicate (step 3, leg 1). Do not
  add a seed row to the managed-set table.
- The seeds ship **unstamped** (like every managed/seed source) — `init` does **NOT** stamp a seed
  (an unstamped target is exactly the create-if-absent signal). The harness's own filled
  `DECISIONS.md`/`ROADMAP.md` are stripped from the release; the adopter receives the pristine seed.
  (The harness keeps **no** live `CHARTER.md` — it legitimately follows its own default grain, so
  the file is absent here; the pristine `_CHARTER.md` seed still ships for adopters.)
- The seeded `ROADMAP.md` carries **no** `harness-audit:*` / `harness-product:backlog` fences —
  `/claugentic-dev-harness:audit` and `/claugentic-dev-harness:product` gap mode **self-create**
  their own fences on first run, so the seed correctly omits them.

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
- **Record the architecture-tree choice (step 4's contract).** Write the recorded-choice
  line into this same block: `- Architecture tree: <harness-skeleton (gate on) | kept by
  adopter (gate off, your init choice)>`, **keyed on the `Architecture tree:` label**. Unlike
  the `Run the app:` line above (append-once, never rewritten), this line is
  **rewrite-on-disk-disagreement**: append-if-line-absent on first write, and rewritten in
  place when on-disk tree state forces a different outcome than the record (per step 4's
  contract). Step 4 already read this line **before** prompting, so the value written here
  reflects the honored/chosen outcome. **The one rewrite case:** when step 4 overrode a
  recorded `keep-gate-off` because the tree was deleted (on-disk wins → mature-no-tree
  skeleton), rewrite the single `Architecture tree:` line in place to the new
  `harness-skeleton (gate on)` outcome so the next re-run reads a value consistent with
  on-disk state. A settled re-run (on-disk matches the record) rewrites nothing — the block
  stays byte-identical.
- **Record the harness mode (step 1's contract).** Write the recorded-mode line into this
  same detected-tooling block: `- Harness mode: <shared | solo (local-only)>`, **keyed on the
  `Harness mode:` label**, append-if-line-absent (it is not rewritten on a re-run — the mode is
  a once-chosen adoption setting, like `Run the app:`, not a state that tracks on-disk drift).
  Step 1 read this line **before** prompting, so the value written here reflects the
  honored/chosen mode. **The block this line lives in is itself routed by the mode** (step 6's
  solo divergence (d)): in **solo** mode the whole detected-tooling block — and this line — is
  in **`CLAUDE.local.md`**; in **shared** mode it is in `CLAUDE.md`. This is what makes a
  re-`init` read its own mode back and stay consistent.

**(detect a competing way-of-work doc — non-destructive; never delete).** Adopting onto a
repo that carries an *obvious* rival way-of-work / agent-instruction doc can mislead agents.
The step-6 authority clause already defuses this (the harness wins on conflict), but `init`
also **surfaces** the doc once so the user can decide whether to **harvest** lessons from it.

- **Detection — a small, high-precision NAME allow-list only** (precision over recall — a
  false positive is worse than a missed obscure doc; the authority clause covers the misses):
  a **non-managed** `docs/claugentic-WORKFLOW.md`-class file (a `WORKFLOW.md` that is NOT a genuine
  harness managed copy per the step-3 predicate — e.g. one at repo root or carrying no
  managed stamp), `.cursorrules`, `AGENTS.md`, `.github/copilot-instructions.md` (or a
  root `copilot-instructions.md`), and a `SUITE_HARNESS`-style way-of-work doc (e.g.
  `SUITE_HARNESS.md`). **`CLAUDE.md` is NEVER flagged** — it is the designed merge target
  for the managed fence (step 6), not a competitor. Match on these names only; do **not**
  content-scan arbitrary `.md` files for "process-like" prose (that re-introduces the
  false-positive rot).
- **Prompt (only when at least one is found, and not already recorded — see below):**
  *"Found `<X>` — it overlaps the harness way of work. The harness is now the authority (see
  the `CLAUDE.md` clause), so this file won't override it. Want me to **fold any lessons from
  it into the harness** (a quick scan, then I leave the file in place), or **leave it as-is**
  (the authority clause keeps agents on the harness)?"*
  - **Fold in (harvest)** → scan `<X>` and surface anything worth promoting into the harness
    (a `docs/claugentic-ROADMAP.md` item, a `docs/claugentic-DECISIONS.md` note, or a suggested standards addition —
    **propose**, do not silently rewrite managed files); **leave `<X>` in place**.
  - **Leave it** → do nothing to the file; the authority clause defuses it.
  - **NEVER delete `<X>` (or any user file), ever** — non-destructive is absolute.
  - **Confirmation discipline:** like the Replace prompt, act on the explicit choice only; on
    silence/default/unavailable, **default to "leave it"** (the safe, non-destructive choice)
    and report it.
- **Record via A's recorded-choice contract** (same append-if-line-absent mechanism, so a
  re-`init` does **not** re-prompt): write a **single label-keyed line** into the
  detected-tooling block — `- Competing way-of-work docs: reviewed (your init choice)`,
  **keyed on the `Competing way-of-work docs:` label** (one line, append-if-line-absent — no
  per-file/plural-doc keying; this is a low-stakes advisory prompt and the `CLAUDE.md`
  authority clause defuses the conflict regardless). Read this line **before** prompting; if
  present, the competing-doc prompt is **skipped** (no re-prompt).

### 9. Report

**Open with a one-line readiness summary** — a plain-English "is the setup healthy?" line
that **reuses the detections `init` already ran** (no new mechanism): the step-1 harness
mode, the step-4 tree-gate decision, the step-1 Python interpreter, and the step-5c plugin
self-reference. (NOT the scripted engine — its availability is a per-session, run-time
condition the Workflow tool decides when a command runs; `init` cannot know it at setup time,
so it is not reported here.) Each item reads `<on>` when healthy, or **`reduced — <what's
missing>`** when degraded — e.g. *"Setup: mode SHARED · tree-gate ON · Python found
(`python3`) · plugin declared for teammates"*, or with a degraded item flagged, *"Setup: mode
SHARED · tree-gate ON · Python **reduced — none found; install Python 3 to enable the tree
check** · plugin declared for teammates"*. (Tree-gate is `OFF` not "reduced" on the Keep-mine
choice — that's a healthy chosen state, not a degradation.) **In solo mode** the line reads
*"Setup: mode SOLO (local-only) · tree-gate ON · Python found (`python3`)"* — and **omits the
plugin-self-reference item** (step 5c is skipped in solo, so there is nothing to report);
mode SOLO is a healthy chosen state, never "reduced."

**Then lead with a plain-English headline** — before the grouped technical summary — so a
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

**The architecture-tree branch of the honesty register** — name the tree action plainly,
branched on step 4's outcome (each is honest about what was created/overwritten/left):
- **Fresh / minimal tree →** *"I created a starter code map (`docs/claugentic-ARCHITECTURE_TREE.md`) —
  it fills in as you add code — the harness nudges to keep it current."*
- **Mature-no-tree skeleton →** *"I created a code map (`docs/claugentic-ARCHITECTURE_TREE.md`) listing
  every source file from `git ls-files` — descriptions stay thin and improve as the code is
  touched. Nothing of yours was overwritten (you had no tree)."*
- **Replace (mature-with-tree, confirmed) — the one user-file overwrite, name it loudly:**
  *"Replaced your `docs/claugentic-ARCHITECTURE_TREE.md` with a harness skeleton — your previous tree is
  in git history (an uncommitted tree is unrecoverable)."* This is the **only** path in
  `init` that overwrites a user-owned file, and it happened **only** because you explicitly
  chose Replace (same recoverable-from-git-only caveat class as the Refreshed group above).
- **Keep-mine-gate-off →** *"I left your `docs/claugentic-ARCHITECTURE_TREE.md` untouched and turned the
  tree-gate OFF for this repo — no blocking check on your tree (it stays model-upheld via the
  harness instructions in `CLAUDE.md`). To switch to the harness format later, delete the
  tree and re-run `init`."*

Then tell the user the **setup is live** — honestly, so no restart is implied where none is
needed (a skill **cannot** restart a session; don't pretend otherwise):
- **When the tree-gate is ON:** the **tree gate runs at commit time** — a git **pre-commit
  hook** checks the tree once per `git commit` (no restart, no per-action overhead); a missing
  entry aborts that commit until you add it. Name the **hook path per mode**: **shared** →
  `.githooks/pre-commit` via `core.hooksPath=.githooks` (travels with the repo); **solo** →
  `.git/hooks/pre-commit` (local to this clone, untracked — `core.hooksPath` left at its
  default). **When the tree-gate is OFF (Keep-mine-gate-off):** say so plainly — *no* tree
  hook was wired; run `python scripts/claugentic-check_architecture_tree.py` manually only if
  you ever want a one-off check (it would flag a non-backtick tree, which is why the gate is
  off).
- **You (the agent) have adopted the harness workflow for the rest of this session** — you just
  scaffolded it and follow `docs/claugentic-WORKFLOW.md` from here, so work continues immediately.
- **Suggest `/clear` or `/compact`** (quick — not a whole new chat) for the cleanest standing
  setup: that's what loads the new `CLAUDE.md` (or **`CLAUDE.local.md`** in solo mode) as cached
  context (it's read once at session start and a skill can't force a re-read). Recommend it
  before a big `audit` run (clean context); optional otherwise; in place next session
  regardless. **Never tell the user they *must* "start a fresh chat."**

**The solo-mode honesty + verification block — emit ONLY in solo mode** (in shared mode this
block is omitted entirely; nothing changes there):
- **Solo honesty line:** *"I adopted the harness **solo / local-only** — everything I wrote
  lives on this clone alone: the managed docs, code map, and the `CLAUDE.local.md` anchor are
  kept untracked via `.git/info/exclude` (not your committed `.gitignore`, which I did **not**
  touch — git does not ignore `CLAUDE.local.md` on its own), and the tree gate is
  `.git/hooks/pre-commit` (local). **No
  new tracked file, no committed-`.gitignore` edit, no shared git config — a teammate's clone
  is byte-identical and unaffected.**"*
- **Verification claim (state it as what you confirmed, honestly):** run `git status
  --porcelain` and confirm it shows **zero new TRACKED paths** (solo-written paths show only as
  ignored / not at all), and run `git diff -- .gitignore` and confirm it is **empty** (the
  committed `.gitignore` is byte-unchanged). Report both: *"Verified: `git status` shows no new
  tracked paths; `git diff -- .gitignore` is empty."*
- **The `git check-ignore` guard — FAIL LOUD if a should-be-local path is not ignored.** For
  **each** solo-written path (the managed docs/tree/tree-script patterns appended to
  `.git/info/exclude`, and `CLAUDE.local.md`), run `git check-ignore <path>` and confirm it
  reports the path as ignored. If **any** should-be-local path is **not** ignored (it would
  therefore become a tracked change and leak to teammates), **do NOT paper over it** — report
  it **loudly** as a solo-invariant breach naming the exact path, and tell the user the solo
  guarantee does not hold for that path until it is excluded. (This is the same fail-loud,
  never-swallow posture as the rest of `init`: a silent leak is the worst outcome, so surface
  it.) When every path checks out, the verification claim above is honest; if not, the failure
  line replaces the clean claim.

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
- **Created** — files written from scratch (e.g. `claugentic-ARCHITECTURE_TREE.md`, `claugentic-ROADMAP.md`) +
  the managed files that were absent and copied + stamped. For the tree, name **which mode**
  produced it: minimal (fresh), cheap-complete skeleton (mature-no-tree), or
  **replaced-by-skeleton** (mature-with-tree → Replace — the user-file overwrite above); or
  **kept-untouched, gate off** (Keep-mine-gate-off — not created, left as the user's).
- **Refreshed** — managed files (and the CLAUDE.md fence) brought up to the installed
  version because their content had drifted **or their stamp was in an old trailing-clause
  format** (a one-time format migration); **each reported by path** (`<old> → <installed>`).
- **Skipped (already current)** — managed files whose body already matched the installed
  source (left byte-untouched, even if the stamp semver was older).
- **Skipped (user file / unrecognized stamp)** — present files that are not genuine managed
  copies; left untouched, reported so the user can reconcile.
- **Wired** — the tree-gate **pre-commit hook**, named **per mode**: **shared** →
  `.githooks/pre-commit` written + `core.hooksPath=.githooks` set (gate ON); **solo** →
  `.git/hooks/pre-commit` written (gate ON, local + untracked, no `core.hooksPath` change);
  "pre-commit hook already wired" (idempotent re-run), a `core.hooksPath` **conflict** flagged
  (the adopter has their own hooks path — see step 5b, both modes), or **"tree-gate OFF — no
  pre-commit hook wired"** (Keep-mine-gate-off).
- **Merged** — the `.claude/settings.json` plugin self-reference (`extraKnownMarketplaces` +
  `enabledPlugins`), or "already declared" on a re-run. **In solo mode this group is
  omitted** — step 5c is skipped, so `.claude/settings.json` and the committed `.gitignore`
  are untouched (report that explicitly under the solo honesty block above).
- **Locally excluded (solo mode only)** — the solo-written paths appended to
  `.git/info/exclude` (managed docs/tree/tree-script + `CLAUDE.local.md`), each confirmed
  ignored via `git check-ignore` (per the guard above). Omitted in shared mode.
- **Detected** — the ecosystem, the interpreter, the existing tooling, the recorded
  **harness mode** (`Harness mode:` line — shared/solo) and **architecture-tree choice**
  (`Architecture tree:` line — gate on/off), and any **competing way-of-work doc** found: name
  it, state the harvest outcome (**harvested → lessons promoted into the harness, or left in
  place**), and confirm **it was NOT deleted** (nothing of the user's is ever removed). When a
  harvest promoted something, list the ROADMAP/DECISIONS/standards item it proposed.

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
- Every **create-if-absent** target — the tree (generated), and the ROADMAP/DECISIONS seeds
  (copied from `_X.md`, underscore stripped, step 7) — is **user-owned, never refreshed.**
- The **architecture-tree scenario decision is recorded** (`Architecture tree:` line in the
  detected-tooling block — append-if-line-absent, then rewritten in place only on on-disk
  disagreement) and **read before any prompt**, so a re-`init` on a settled repo **honors the
  record and never re-prompts**: a `keep-gate-off` repo wires no hook and re-derives no globs
  (the `INCLUDE_GLOBS = []` is carve-out-protected), and a `harness-skeleton` repo's tree
  already exists (create-if-absent → skipped). On-disk state wins (and the line is rewritten to
  match) only when it diverges (the user deleted the tree), which is not the byte-identical
  re-run case.
- The **pre-commit hook** is "already wired" when `.githooks/pre-commit` exists AND
  `core.hooksPath` is `.githooks` → a re-run writes nothing and sets nothing. **Gate-off
  wires no hook, so there is nothing to write on a re-run** (the recorded `keep-gate-off`
  suppresses re-wiring). The **`.claude/settings.json` plugin self-reference** merge is keyed
  on the `sh4npeiris` marketplace + `claugentic-dev-harness@sh4npeiris` plugin keys (both
  present → skip; never a duplicate).
- The **harness mode** is recorded (`Harness mode:` line) and **read before any prompt** (step
  1), so a re-`init` honors it and never re-prompts. **In solo mode** every solo divergence is
  itself idempotent: `.git/info/exclude` is append-if-absent (re-run adds nothing); the solo
  pre-commit hook is "already wired" when `.git/hooks/pre-commit` exists (re-run writes
  nothing); step 5c is skipped (so `.claude/settings.json` and the committed `.gitignore`
  stay untouched on every run); and the `CLAUDE.local.md` fence is the byte-identical-inner-block
  refresh below, just targeting `CLAUDE.local.md`. So a settled solo re-run is also a no-op —
  `git status` stays clean (nothing was tracked to begin with).
- The **CLAUDE.md** fence (or **`CLAUDE.local.md`** in solo mode) is refreshed inside the
  markers from a template with **no volatile content**, so once it embeds the installed
  `{VERSION}` a re-run regenerates a byte-identical inner block → no-op (everything outside the
  markers is preserved byte-for-byte).

**Acceptance of a 2nd run at the same installed version:** `git status` in the target shows
**zero changes** and the report says everything was already current. If such a re-run
dirties the repo, an idempotency guard is missing — that is a bug, not expected behavior.
(A re-run *after a version bump* is expected to refresh — that is convergence, not a bug.)

## What this skill does NOT do (honest scope)

- It does **not** install or reconfigure your linters/test runner — it **detects and
  records** them (step 8) so the workflow composes with them.
- It does **not** refresh your **user-owned** files — `docs/claugentic-ARCHITECTURE_TREE.md`,
  `docs/claugentic-ROADMAP.md`, and `docs/claugentic-DECISIONS.md` are seeded create-if-absent and then left to
  you (they carry your content, not managed content).
- It does **not** 3-way-merge a user-edited **managed** file — managed files are marked
  *do not edit* and carry no user content by contract (sole exception: the
  `claugentic-check_architecture_tree.py` `INCLUDE_GLOBS` knob, preserved per step 3); on a genuine
  drift the installed version wins (reported by path) and **git is the review/recovery
  net** for content you committed (an uncommitted edit isn't recoverable — see the roadmap).
- It does **not** reconcile the pre-commit wrapper **contents** if the shipped wrapper
  changes between versions — idempotency keys only on the hook's presence (+
  `core.hooksPath=.githooks` in shared mode; the `.git/hooks/pre-commit` presence in solo
  mode) (out of scope; tracked on the roadmap).
- **In solo / local-only mode it does NOT** declare the plugin for teammates, edit your
  committed `.gitignore`, or set any shared git config — solo adoption is invisible to
  teammates by design (everything lives on this clone via `.git/info/exclude`,
  `.git/hooks/pre-commit`, and `CLAUDE.local.md`). The trade-off: a teammate who clones gets
  **none** of the harness (no managed docs, no tree gate, no plugin prompt) — switch to
  **Shared** mode (re-`init`, choose Shared) when the team should adopt it too.
- It does **not** audit your code or write a backlog — that is **`/claugentic-dev-harness:audit`**.
