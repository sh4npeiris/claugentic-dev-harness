---
description: Scaffold the claugentic-dev-harness into the current repo — upsert the managed harness set (standards catalog, workflow, playbook, tree-check, doc-budget gate) to the installed plugin version, generate docs/claugentic-ARCHITECTURE_TREE.md and set the tree-check globs — unless you choose to keep a tree you already have, which leaves your tree untouched and the gate off — wire the pre-commit hook with both gates chained into it wherever that gate is on, declare the plugin for teammates in Shared mode (seeds the harness's plugin self-reference into the committed .claude/settings.json so a cloned adopter repo prompts teammates to install it; Solo mode writes none of that), git-init if needed, seed ROADMAP/DECISIONS/CHARTER and the doc-budget caps config (create-if-absent, never clobbering tuned caps), refresh the CLAUDE.md harness fence, and compose with existing lint/type-check/test tooling. Asks Shared (default — committed for the team) vs Solo / local-only (this clone alone via .git/info/exclude + .git/hooks/pre-commit + CLAUDE.local.md, leaving git status clean and the committed .gitignore untouched). Re-running converges the repo to the installed version and never clobbers user content; a true no-op only when already at the installed version.
---

# /claugentic-dev-harness:init

Scaffold this harness into the current repo, **without clobbering user content**. Every write is
**detect → upsert-to-installed / refresh-inside-a-fence / report**; re-running **converges the repo to
the installed plugin version** and is a **true no-op only when it is already at that version**. The
drift decision and the writes are **`init`'s judgment** — rule-bound, never-clobber-guarded by the
stop-if-ambiguous invariant below — **not a mechanical oracle; idempotency at a fixed version is
checked by a dogfood run, not a wired gate.**

## How this skill works

The orchestrator runs the **9-step procedure** below in order; the output is a **created / refreshed /
skipped / merged / detected** summary. **Never-clobber is the load-bearing safety invariant** — this
writes into someone else's repo. If any step is ambiguous about whether a write would destroy user
content, **stop and report rather than guess.**

### Two durable conventions this skill establishes

1. **The managed-stamp** — every file `init` copies or refreshes carries a stamp on its **first
   line**. The current full form `init` **writes** (never vary it):
   - **Markdown:** `<!-- claugentic-dev-harness@{VERSION} managed — do not edit (copied from the claugentic-dev-harness plugin) -->`
   - **Python:** `# claugentic-dev-harness@{VERSION} managed — do not edit (copied from the claugentic-dev-harness plugin)`
   - `{VERSION}` is the plugin `plugin.json` `version` field (e.g. `0.1.0`).
   - **THE TRAILING-CLAUSE RULE — stated once here; every later step defers to it.** Detection keys
     on the **stable prefix** `claugentic-dev-harness@<semver> managed — do not edit` (in the file's
     comment syntax: markdown `<!-- … -->`, Python `# …`) **with a parseable semver**. The clause
     *after* `do not edit` is **version-variable** — it has changed across releases (early copies
     read `…; run /claugentic-dev-harness:update to refresh`) — and is **NOT** part of the identity
     test. So an old-format-but-genuine copy is still recognized and REFRESHed (the refresh
     normalizes line 1 to the current full form), never misclassified as a user file and skipped
     forever. **Only DETECTION tolerates the variable clause; what `init` WRITES is always the
     current full form.**

2. **The CLAUDE.md `harness:managed` fence** — the harness section lives between the exact markers
   `<!-- harness:managed:start -->` and `<!-- harness:managed:end -->`.
   **Replace only inside the fence; everything outside it is human-owned and never touched.**
   Mirrors the `harness-audit:overview` / `harness-audit:backlog` / `harness-product:backlog`
   fences. **No volatile content (timestamps, counters, run-dates) inside the fence** — so a re-run
   at the same version regenerates a byte-identical inner block. The seeded **Current scope** block
   lives **outside** it (step 6).

---

## The 9-step procedure

### 1. Preflight

- **Resolve the managed-set source.** Installed as a plugin → **`${CLAUDE_PLUGIN_ROOT}`** (verified to
  expand in skill context); running from this harness's own dev checkout → the repo root. State which
  you used in the report.
- **Confirm the target repo root** (the adopter's `${CLAUDE_PROJECT_DIR}` / current repo).
- **Verify Python** (both commit-time gates need it): try `--version` on `python`, `python3`, `py` and
  **record which one works**. **None found ⇒ report and continue** — the gates won't run until Python
  is installed, and the agent can fall back to **`Glob`** to maintain the tree. A missing interpreter
  is not fatal to scaffolding.
- **Resolve the harness mode — Shared (default) or Solo / local-only.** It governs four later
  divergences (steps 3, 5b, 5c, 6), so settle it **here**, before step 3 writes any managed docs.
  - **Read the recorded mode FIRST (re-run idempotency).** Before any prompt, read the
    **`- Harness mode:` line** from the detected-tooling block — `CLAUDE.local.md` in solo,
    `CLAUDE.md` in shared (check both; either presence settles it). **Exact line:**
    `- Harness mode: <shared | solo (local-only)>`, keyed on the `Harness mode:` label. Present ⇒
    **honor it and skip the prompt.**
  - **No recorded mode → prompt once (AskUserQuestion):** *"Adopt the harness **Shared with
    teammates** (the managed docs, tree gate, and plugin self-reference are committed so the whole
    team gets them), or **Solo / local-only** (you dogfood it on this clone alone — `git status`
    stays clean, your `.gitignore` is untouched, and a teammate's clone is unaffected)?"*
    **Default — and the value on silence / a timeout / AskUserQuestion being unavailable — is
    Shared**; never diverge to the less-common branch without an explicit choice.
  - **Record the chosen/honored mode** (step 6 writes the line, append-if-line-absent on the label).
    That is what makes **invalid states unrepresentable**: a recorded `solo` short-circuits the shared
    branches (5c never runs; the hook never goes to `.githooks/`).
  - **Shared = the steps exactly as written. Solo diverges in exactly four places, each flagged inline
    as a `> **Solo divergence**` block — and nowhere else.** The invariant they uphold: **ZERO new
    tracked paths, NO edit to the committed `.gitignore`, NO shared git config.**

### 2. `git init` if absent

- **No `.git` ⇒ run `git init`** (the tree-check enumerates via `git ls-files`; the workflow lands
  slices against a VCS). **`.git` present ⇒ skip**, report "git already initialized."

### 3. Upsert the managed harness set to the installed version (stamped)

**Upsert** each file in the managed set from the source (step 1) into the target — create it if
absent, **refresh a genuine managed copy that drifted from the installed source**, leave it
byte-untouched if already current — **stamping line 1** (convention 1). The managed set is exactly:

| Source path | What it is |
|---|---|
| `docs/claugentic-standards/` | the **11 authored modules** + `_TEMPLATE.md` + `README.md` (the whole catalog directory) |
| `docs/claugentic-WORKFLOW.md` | the staged development workflow (process source of truth) |
| `docs/claugentic-ENGINEERING_STANDARDS.md` | the thin standards entry point |
| `docs/claugentic-PLAYBOOK.md` | the plain-English guide for the human driving the harness |
| `docs/claugentic-PRODUCT_SPEC_TEMPLATE.md` | the product-spec contract template (pure verbatim copy; the filled `docs/claugentic-PRODUCT_SPEC.md` is user-owned, never managed) |
| `docs/claugentic-PLAN_TEMPLATE.md` | the plan-file contract template (verbatim copy; adopters copy one per plan into their own .claude/plans/) |
| `scripts/claugentic-check_architecture_tree.py` | the deterministic architecture-tree gate |
| `scripts/claugentic-check_doc_budgets.py` | the deterministic doc-budget gate — **delivery, not just payload membership**: the plugin carrying a script is not the same as your repo having one, and this row is what puts it in *your* `scripts/`. Same stamped-Python treatment as the tree gate (stamp line 1, `#!/usr/bin/env python3` line 2); **no exec bit** — the pre-commit wrapper invokes it as `"$PY" "$root/$gate"`, never directly. It reads the caps config step 7b writes; with no config it is a quiet exit-0 no-op |

**Per file, decide one of four verdicts (this is `init`'s judgment, rule-bound — there is no
oracle):**

| Detected state | Verdict | Action | Report line |
|---|---|---|---|
| target **absent** | `CREATE` | copy + stamp (installed version) | `created` |
| present, **not a genuine managed copy** (see predicate) | `USER_FILE` | **skip — never overwrite** | `skipped (user file / unrecognized stamp) — reconcile manually` |
| genuine managed copy, **body differs from source** OR **stamp not in the current full form** | `REFRESH` | overwrite the whole file with freshly-stamped source — **migrating the stamp to the current full form** (stamp = installed version) | `refreshed <path>: <old-semver> → <installed>` |
| genuine managed copy, **body identical to source AND stamp already in the current full form** | `CURRENT` | **leave byte-for-byte untouched** — even if its stamp semver is older than installed (**no RESTAMP**) | `skipped (already current)` |

**The genuine-managed predicate (never-clobber-critical).** A target is a genuine managed copy — and
therefore a REFRESH/CURRENT candidate — **only when both** hold: (1) its **path is in the managed set
above**, whatever its first line; and (2) **line 1 *begins* with the stable managed-stamp prefix** per
the trailing-clause rule (convention 1), the prefix immediately following the comment opener. So a line
that merely *contains* the token, carries it mid-line, bears a *foreign* plugin's stamp, or has a
garbled semver is **`USER_FILE` → skip and report, never overwrite**, exactly like an unstamped
same-named file. One honest narrowing vs 0010's exact-form rule: text a user appended *after* `do not
edit` on line 1 of a managed file is now part of the version-variable clause, so a REFRESH replaces and
reports it, like any other edit to a do-not-edit file. With no mechanical oracle, **REFRESH only when
the file is unambiguously a genuine managed copy; on any ambiguity, stop and report rather than
guess** — that stop-if-ambiguous rule **is** the never-clobber safety net here.

**The body compare (the off-by-one + CRLF traps — get this exactly right):**
- **Asymmetric:** `target body = target minus line 1` (the stamp); `source body = the pristine source
  as-is` (sources carry **no** stamp). For **either Python script**, strip **only line 1** — the
  `#!/usr/bin/env python3` shebang on line 2 **stays in the body**. Stripping it too misaligns every
  Python compare by one line and false-REFRESHes it.
- **Newline-insensitive:** compare **normalized for line endings** (LF/CRLF and trailing-newline
  insensitive). This repo's `.gitattributes` does not reach an adopter's repo, so a CRLF checkout with
  an identical body must read `CURRENT`, not `REFRESH`.
- **Stamp-format sits *alongside* the compare:** `CURRENT` needs an identical body **and** a
  current-form line 1. An old-format genuine copy compares body-identical (line 1 is stripped) but
  still reads `REFRESH` — a one-time format migration, after which it re-reads `CURRENT`. **Distinct
  from no-RESTAMP**, which is about not bumping the semver of an already-current-form file.

**The one hybrid managed file — `claugentic-check_architecture_tree.py`'s `INCLUDE_GLOBS`** (the named
exception to "managed files carry zero user content"; every other file in the set, the doc-budget gate
included, is a pure verbatim copy). It is the **only** per-repo knob, written per-adopter in step 5a,
so a configured adopter's globs differ from source and, without a carve-out, the file would **always**
REFRESH and **reset their globs** — a never-clobber violation plus a broken tree-check. Treat it as a
hybrid, exactly like the `CLAUDE.md` fence:
- **The body compare excludes the `INCLUDE_GLOBS = [ … ]` assignment** (from the line beginning
  `INCLUDE_GLOBS =` through its closing `]`) on **both** sides ⇒ custom globs read **CURRENT**.
- **A REFRESH re-injects the adopter's existing `INCLUDE_GLOBS`:** the new source body minus its own
  assignment + the adopter's current assignment + the installed stamp — never the source's globs.
  (Step 5's glob-drift self-correction then runs as today.)
- **Assumption, stated so the carve-out is well-defined:** `INCLUDE_GLOBS` is the single stable
  per-repo knob here; a future restructure is a version-migration concern, out of scope.

**Per-file upsert only — `init` never deletes.** A user-added file under `docs/claugentic-standards/`
is **left untouched** (not in the set); a managed module the installed version no longer ships is
**left in place and reported**. Upsert, not `rsync --delete`.

- **Stamp on copy/refresh, not in the source** — sources are pristine and unstamped; `init` writes the
  stamp as line 1 (Python: above the existing shebang, keeping the file runnable). The authoritative
  repo-version readout is the `CLAUDE.md` managed fence (step 6), not the per-file stamps — **mixed
  per-file stamps are expected and correct.**
- **Security / exclude-set:** upsert **only** the managed set. **Never** copy or surface the adopter's
  `node_modules`, build output, `vendor`, or secrets (`.env*`, keys, credentials). The same exclude
  discipline governs step 4's tree generation.

> **Solo divergence (a) — managed paths → `.git/info/exclude`, NEVER the committed `.gitignore`.**
> In **solo mode** every managed file `init` writes (the set above, both gate scripts, the step-4 tree,
> the step-7b caps config) is written **exactly as in shared mode** — then its path/pattern is
> **appended to `.git/info/exclude`** so `git status` shows it ignored. That file is per-clone and
> inherently untracked, so a teammate's clone never sees these paths. **NEVER edit the committed
> `.gitignore` in solo mode** — it is tracked; an edit disturbs teammates and breaks the solo
> invariant. Append the patterns covering what `init` actually wrote: `docs/claugentic-*` (managed docs
> + tree + the three seeds — this glob auto-routes the copied `CHARTER.md` too),
> `docs/claugentic-standards/`, `scripts/claugentic-check_architecture_tree.py`,
> `scripts/claugentic-check_doc_budgets.py`, `.claude/claugentic-doc-budgets.json` (the tracked-path
> invariant covers data files exactly as it covers scripts), and `CLAUDE.local.md` (step 6).
> **Append-if-absent** per pattern line, so a re-`init` is a no-op here. In **shared mode** none of this
> runs — managed paths commit normally and the committed `.gitignore` is the only ignore surface (step
> 5c manages its negation).

### 4. Provision `docs/claugentic-ARCHITECTURE_TREE.md` (scenario-based) + decide the tree-gate

**Scenario-based**, fixed by **two reused signals** (DRY — no new detector): the presence of
`docs/claugentic-ARCHITECTURE_TREE.md`, and the *Application source present* predicate defined in
`/claugentic-dev-harness:audit` Phase 1 (the same one step 5a reuses). The decision here — which
globs, whether to build a skeleton, gate on or off — is what steps 5b and 5c wire against.

**Read the recorded choice FIRST (re-run idempotency)** — the `Architecture tree:` line in the
detected-tooling block, per the contract below, read before any prompt. **On-disk state wins:** a
record of `keep-gate-off` with the tree now absent takes the mature-no-tree path regardless, and
rewrites the record. A malformed/absent record falls back to prompting — safe, dirties nothing.

The three scenarios — **detect → tree action → `INCLUDE_GLOBS` → gate decision**:

- **Fresh** (no tree, source present = **false** — an empty / docs-only repo): 5a (→ `INCLUDE_GLOBS =
  []`, or detected globs if any source exists) → create a **minimal** tree (short intro + the docs/
  scaffolding it can see) → **gate ON**. Report "created (minimal — fills in as you add code)."
- **Mature, no tree** (no tree, source present): 5a → the **real** globs → the **cheap-complete
  skeleton** below → reconcile via the gate loop → **gate ON** (the skeleton lists every path, so the
  first commit reconciles green and never false-trips). Report "created (skeleton from `git ls-files`
  — every path listed, descriptions enrich over time)."
- **Mature, with tree** (tree present, no honored `keep-gate-off` record): **skip the skeleton build
  entirely** — never overwrite a tree unasked — and run the two-option prompt below. A recorded
  `harness-skeleton (gate on)` means the tree is already a managed skeleton: gate ON per the record,
  no re-prompt (treat it as mature-no-tree only if the tree is absent).

**The cheap-complete skeleton** (mature-no-tree, and the Replace branch) — built with **no per-file
content reads**: the path list is a millisecond `git ls-files`; the descriptions were the expense.
  1. 5a has already set `INCLUDE_GLOBS` in the **copied** script to the real globs.
  2. Derive the file list from **`git ls-files`** filtered by those globs — what the copied script's
     `in_scope_files()` computes (tracked + staged + untracked-not-ignored, minus exclusions).
     Honoring `.gitignore` excludes deps/build/generated trees for free.
  3. Write it: a short intro that **states the per-entry length budget** — read `MAX_ENTRY_CHARS` from
     the copied `scripts/claugentic-check_architecture_tree.py` and name that number as the hard
     ceiling a commit is refused over (the Fresh minimal tree carries the same line) — then **one
     `- \`path\`` line per in-scope file**, **grouped under markdown headings by directory** (e.g.
     `## src/api`), each a thin path-derived one-liner. Descriptions enrich best-effort later, never
     gate-checked.
  4. **CRITICAL — format guard:** markdown headings + `- \`path\`` lines, and **NEVER ` ``` `-fenced
     code blocks**. A fence is stripped by the copied script's `_strip_fenced_blocks` and desyncs the
     presence-matching pairing — the measured bug that read fenced-diagram trees as 0% coverage. Never
     emit an ASCII directory diagram.
  5. **Run the copied gate and reconcile to green — the gate is the oracle.** Missing entry → add it;
     stale entry → remove it; loop until green.

**The mature-with-tree prompt (two options — non-destructive).** With an existing tree and no honored
record, **pause and prompt** (AskUserQuestion): *"You have a `docs/claugentic-ARCHITECTURE_TREE.md`.
The harness tree-gate reads a backtick-prose format and can't mechanically enforce a fenced ASCII
diagram. How do you want to proceed?"*
  - **Replace with a harness skeleton** → behave as mature-no-tree, **overwriting the existing tree** →
    **gate ON**. Record `harness-skeleton (gate on)`. **Replace = confirmed user-file overwrite
    (never-clobber guard):** the tree is **user-owned**, so Replace proceeds **only** on the explicit
    AskUserQuestion confirmation — **never** on silence, a default, a timeout, or AskUserQuestion being
    unavailable. On any of those, **fall back to Keep-mine-gate-off** and report it. The step-9
    **honesty register** must name the overwrite explicitly.
  - **Keep mine, gate off** → leave the tree **untouched**; set `INCLUDE_GLOBS = []`; **gate OFF** (no
    pre-commit hook). Record `kept by adopter (gate off, your init choice)`. The `[]` is
    **adopter-owned**, protected by the step-3 `INCLUDE_GLOBS` carve-out: a re-`init` on a
    `keep-gate-off` repo **MUST NOT re-derive globs**, or the gate silently turns back on against the
    locked choice. To switch to the harness format later, delete the tree and re-`init`.

There is **no third "Skip"** option — it was mechanically identical to Keep-mine-gate-off (KISS).

**The recorded-choice contract** _(built here, reused by the competing-doc sub-step):_
  - **Lives in** the detected-tooling block (outside the managed fence, create-if-absent). Unlike step
    8's append-once `Run the app:` line, this is a **single-value, label-keyed record rewritten in
    place on on-disk disagreement**.
  - **Exact line:**
    `- Architecture tree: <harness-skeleton (gate on) | kept by adopter (gate off, your init choice)>`
    — **keyed on the label `Architecture tree:`**, append-if-line-absent on first write. Exactly one
    such line exists at all times, so there is never an ambiguous pair to tie-break.
  - **Read-before-prompt:** present and consistent with on-disk state ⇒ **honor it, skip the prompt,
    rewrite nothing** (a settled re-run leaves the block byte-identical). Tree present + **no** record
    ⇒ prompt, then record. **Tree absent** (deleted later) ⇒ mature-no-tree **regardless** of the
    record, and **rewrite the line to `harness-skeleton (gate on)`**. Any disagreement: **on-disk wins
    and the line is rewritten to the honored outcome** — a correct response to new reality, not an
    idempotency violation.

### 5. Set the tree-check globs + wire the hook (conditional on step 4's gate decision)

**(a) Set `INCLUDE_GLOBS` in the *copied* `claugentic-check_architecture_tree.py`** — the **only**
per-repo knob (the staleness check derives `EXTS` from it, so there is no second regex to sync). Edit
only the copied script, and only this constant.

**When 5a runs:** **Fresh**, **Mature-no-tree**, **Replace**. For **Keep-mine-gate-off** it sets
**`INCLUDE_GLOBS = []` and re-derives NOTHING** — the `[]` is adopter-owned and carve-out protected
(step 3); reaching the detection below would silently turn the gate back on against the locked choice.
For the running scenarios:
- **Reuse the layout detection from `/claugentic-dev-harness:audit` Phase 1** — **do not author a
  second detector** (DRY). Map it to git pathspec **extension** globs (`:(glob)src/**/*.ts`,
  `:(glob)cmd/**/*.go`, …).
- **Always extension globs** (every entry ends in `*.<ext>`) so `EXTS` is derivable. **Never** a bare
  directory glob: the script presence-checks those files but cannot staleness-check them.
- **Unmappable ecosystem?** Emit the **dominant source extensions** under the main source dir and
  **report** "globs set conservatively for an unrecognized layout; refine `INCLUDE_GLOBS` in
  `scripts/claugentic-check_architecture_tree.py` if needed." Never guess a layout you can't see —
  broaden and flag.
- **No application source yet?** *Application source present* (audit Phase 1) false ⇒ set
  **`INCLUDE_GLOBS = []`** — the well-defined "unset" state (presence/staleness become no-ops, never a
  fail-open whole-repo scan) — and **report** "no source yet — file-tracking is unset; I'll configure it
  when you add code."
- **Terminating self-correction.** Once code lands, the gate's mechanical **drift detection** flags that
  `INCLUDE_GLOBS` watches *no* files. Re-run the detection, **reset `INCLUDE_GLOBS`**, reconcile the
  tree. **Termination:** drift clears the instant the reset globs match **≥1** file
  (`in_scope_files()` non-empty); an unmappable stack falls back to broaden-and-flag, which also
  matches ≥1. Never loops, never silences drift.

**(b) Wire the tree gate as a git `pre-commit` hook — CONDITIONAL on step 4's gate decision.**

**The gate runs once per `git commit`, not per agent action** — the tree only has to be correct at the
durable handoff, and the agent is in-context at commit time to describe a new file. A **git**
pre-commit hook is a *different* system from Claude Code's `.claude/settings.json` hooks: git triggers
it, so there is **zero per-tool-use overhead**. (`init` writes **no** tree hooks into
`.claude/settings.json`; the SessionStart advisor stays plugin-bundled in `plugin.json`.)

**Gate ON** (Fresh, Mature-no-tree, Replace) ⇒ wire it, init-managed (it travels with the repo, one
config line per clone). **Gate OFF** (Keep-mine-gate-off) ⇒ **write no `.githooks/pre-commit` and do
not set `core.hooksPath`**: a kept non-backtick tree must never be policed by a blocking gate that
would false-flag it (the measured fenced-diagram 0%-coverage regression); it stays model-upheld via the
CLAUDE.md authority anchor, and the gate-off choice is recorded on step 4's `Architecture tree:` line.

- **Gate ON, step 1 — write `.githooks/pre-commit`**, the same wrapper this harness ships in its own
  `.githooks/pre-commit`: repo root via `git rev-parse --show-toplevel` (worktree-safe), an interpreter
  **probe** over `python3` then `python`, then **both chained gates** —
  `scripts/claugentic-check_architecture_tree.py --staged` and
  `scripts/claugentic-check_doc_budgets.py` (no args — it reads none; step 3 delivered it and step 7b
  wrote the caps it reads) — where **exit 1 from either aborts the commit**.

  **Copy the block below verbatim** (only the comment header is adopter-appropriate — a fresh adopter
  has no per-action hooks to "replace"). **That header is the single authoritative statement of the
  four team-safety properties, and none may be dropped:** unreachable-infrastructure-never-blocks ·
  probe-don't-pick · quiet-when-clean · one-gate-per-line-with-its-own-args.
     ```sh
     #!/bin/sh
     # claugentic-dev-harness — the commit-time gate(s): once per `git commit`, locally, before
     # the commit is written; a non-zero exit aborts it. Each gate is invoked with the args its
     # call site gives it, so a gate that is not staged-scoped is never told that it is.
     #
     # INFRASTRUCTURE THAT CANNOT BE REACHED NEVER BLOCKS A COMMIT — a broken git, no working
     # Python 3.7+, a gate script not in this checkout. A gate that RUNS and exits non-zero still
     # aborts, one that crashes on import included: present-but-broken is a repo defect, not a
     # teammate's machine. The two skips differ in register, deliberately: a broken git passes
     # SILENTLY (no repo to report into), while no working Python and a missing gate script pass
     # LOUDLY — one plain line each, on stderr.
     # NO TIMEOUT, stated rather than hidden: a gate that hangs hangs the commit (Ctrl-C is the
     # exit). There is no portable POSIX timeout, and `timeout(1)` would trade a rare hang for a
     # common "not found" on exactly the machines this protects.
     root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
     # PROBE each candidate, never merely its presence, and never pick before probing: the
     # Windows-Store `python3` STUB is on PATH, exits non-zero, and commonly sits BESIDE a working
     # `python` — pick-then-probe disarms the gate on an ordinary Windows machine while saying
     # "no Python". Python 2 answers `-c ""` happily then dies on the gate with a SyntaxError, so
     # the probe asserts the VERSION the gate scripts record for themselves (`# Python 3.7+`).
     # Raise this floor only when a hook-wired gate raises its own.
     PY=
     for cand in python3 python; do
       if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' >/dev/null 2>&1; then
         PY=$cand
         break
       fi
     done
     if [ -z "$PY" ]; then
       printf '%s\n' "claugentic gates SKIPPED: no working Python 3.7+ on PATH (tried python3, python) - install Python 3 and the gates resume on your next commit (no re-init needed)" >&2
       exit 0
     fi
     # Run ONE gate with the args given. A gate script not in this checkout is a skip, not a
     # block (a stale hook, a sparse checkout, a half-finished clone). stdout is CAPTURED (a clean
     # pass prints nothing at all); stderr FLOWS THROUGH untouched. Exit 0 -> discard the captured
     # stdout; non-zero -> print it and return 1.
     # GATE-SIDE OBLIGATION: a gate chained here reports advisory lines on STDERR — its stdout is
     # discarded when it passes. Today's chain: the tree check (verdict only) and the doc-budget
     # check (a byte-budget WARN band, a report-only breach — while passing). Chaining another is
     # one more `run_gate <script> [args] || rc=1` line, and `rc` is what makes it
     # run-both-and-report: a later gate's failure never masks an earlier one's.
     run_gate() {
       gate=$1
       shift
       if [ ! -f "$root/$gate" ]; then
         printf '%s\n' "claugentic gate SKIPPED: $gate is not in this checkout" >&2
         return 0
       fi
       gate_out=$("$PY" "$root/$gate" "$@")
       gate_status=$?
       if [ $gate_status -eq 0 ]; then
         return 0
       fi
       [ -n "$gate_out" ] && printf '%s\n' "$gate_out"
       return 1
     }
     rc=0
     run_gate scripts/claugentic-check_architecture_tree.py --staged || rc=1
     run_gate scripts/claugentic-check_doc_budgets.py || rc=1
     exit $rc
     ```
  **Make it executable** (`chmod +x .githooks/pre-commit`; git tracks the bit so a clone inherits it).

  **Then write its merge sibling, `.githooks/pre-merge-commit`, and `chmod +x` it too.** git fires
  **`pre-merge-commit`** for a conflict-free `git merge` — **never `pre-commit`** — so without it
  neither gate runs on a merge result (measured, git 2.55: an over-cap ledger merges clean and lands
  unchecked). It **delegates, it does not duplicate** — one chain, two entry points, so a gate added to
  the wrapper covers merges automatically and the two can never drift:
     ```sh
     #!/bin/sh
     exec "$(dirname "$0")/pre-commit" "$@"
     ```
  **Unchanged limits, state them:** a **server-side PR merge runs no local hook at all**, and a merge
  that stops on conflicts commits through `pre-commit` anyway. The wrapper probes for itself, so a repo
  with no Python at `init` time still gets the hook: it skips (loudly) until Python is installed, then
  gates with no re-run needed.

  **Line endings — shared mode only.** The wrapper is a multi-line `sh` script; on a CRLF-normalizing
  checkout it becomes a **parse error** for every teammate whose `/bin/sh` is `dash` — a blocked commit
  with a raw shell error. So **append `.githooks/** text eol=lf` to `.gitattributes`**
  (append-if-line-absent; create the file if absent; never rewrite an existing line, and never impose a
  repo-global `* text=auto` — that is the adopter's call). **Solo mode: do NOT** — `.gitattributes` is
  tracked, and the solo hook lives at `.git/hooks/pre-commit`, which git never normalizes.
- **Gate ON, step 2 — run `git config core.hooksPath .githooks`**, pointing git at the tracked hook
  directory so the hook fires on every commit in this clone, and via its `pre-merge-commit` sibling on a
  conflict-free `git merge` too.
- **Idempotency — "already wired" = `.githooks/pre-commit` exists AND `core.hooksPath` is
  `.githooks`.** Both hold ⇒ **skip** (write nothing, set nothing) and report "pre-commit hook already
  wired". Read `core.hooksPath` with `git config --get core.hooksPath` before setting it.
  - **The ONE bounded reconciliation (an existing wrapper does not carry the budget chain).** "Already
    wired" is keyed on **presence**, so without this a repo that already has a wrapper keeps it forever
    and never gets the budget signal at commit time. **Compare RUN LOGIC, not bytes** — the on-disk
    wrapper's executable lines (drop blanks and whole-line comments; comment headers legitimately differ
    between the two homes) against the template above. **Three branches, in this order:**
    - **(1) Run logic equals the current template → ALREADY CHAINED.** Write nothing, set nothing,
      report **"pre-commit hook already wired (budget gate chained)"**. This is every settled re-run,
      and it must be enumerated first: without it a re-`init` falls through to branch (3) and tells the
      user to add a line that is already there — applying which would run the gate twice.
    - **(2) Run logic equals THIS VERSION'S SHAPE WITHOUT the budget-gate line → REFRESH IN PLACE.**
      Rewrite with the current template (comments and all) and report **"wrapper: refreshed (chained the
      budget gate)"**. **Scope it honestly — this is not "the previously shipped wrapper":** no released
      version ever shipped this shape; a match came from a development checkout of the harness.
    - **(3) Anything else → NEVER CLOBBER, and never assert authorship.** Report: *"the on-disk run
      logic is not this version's shape — it may be an older harness wrapper or your own edit; either
      way it is never rewritten."* Then give a **SHAPE-AWARE** remedy, because the wrong one is
      destructive:
      - **Defines a `run_gate` function** → the one-line addition: *"add
        `run_gate scripts/claugentic-check_doc_budgets.py || rc=1` immediately after the tree-gate
        line"* — no args, because that gate reads none.
      - **Does NOT** → *"your wrapper predates the `run_gate` shape (v0.5.1 and earlier) — that one-line
        addition does not apply and **must not be pasted in**: `run_gate` is undefined there, and the
        inserted line's exit status can mask the tree gate's own (measured — a red tree gate exits 0).
        The safe repair is to move the wrapper aside and re-run `init`, or to replace it with the
        template above after diffing your own changes in."* **Never print a remediation line you have
        not checked against the wrapper the reader actually has.**
    - **A repo with NO wrapper gets NO chain, and that is reported, not silently skipped** — gate-off
      repos have nothing to chain into, so they get **no commit-time budget signal at all**; the gate is
      still delivered, still runs when invoked, and `/doctor`'s advisory still reads the same caps config.
    - **Solo mode:** identical three-branch rule against `.git/hooks/pre-commit`.
- **Never-clobber `core.hooksPath`.** Set to something **other than `.githooks`** ⇒ the adopter has
  their own hook directory: **do NOT overwrite it.** Report the conflict ("core.hooksPath is set to
  `<value>`; the tree gate's `.githooks/pre-commit` was written but not activated — point
  `core.hooksPath` at it or chain it from your own hooks") and **continue**: wrapper on disk, their
  config untouched. **"Put it on disk" is create-or-reconcile, never a blind write** — an existing
  `.githooks/pre-commit` takes the same three-branch compare above. This is the branch a **husky** repo
  takes, so the file at risk is exactly the wrapper a pre-existing adopter relies on.
- **Husky repos — OFFER to chain (otherwise the gate is written-but-inactive).** Husky points
  `core.hooksPath` away from `.githooks`, so the branch above leaves the wrapper on disk and **dead**.
  This is an **ordered procedure — each step is a precondition of the next**; do not reorder it.
  1. **ONLY when the tree-gate is ON** — `.githooks/pre-commit` was written this run or already exists.
     A Keep-mine-gate-off repo has no wrapper to chain **to**, so chaining would wire a hard dependency
     on a file that will never exist. Gate OFF ⇒ skip all of it.
  2. **Read the record BEFORE asking.** Look for `- Husky chain:` in the detected-tooling block (step
     8). Present ⇒ **honor it and skip the offer**, reporting the recorded outcome ("husky chain:
     declined (recorded)"). This reader is what makes "a re-run never re-asks" true.
  3. **Detect husky specifically:** `core.hooksPath` is `.husky` **or `.husky/_`** (husky v9 points git
     at the generated `_` subdir while authored hooks stay in `.husky/`), **or** a `.husky/` directory
     exists containing a `pre-commit`. No match ⇒ nothing to offer, no record written.
  4. **Trackability precondition — REFUSE to chain a dependency on an untrackable file.** Run
     `git check-ignore -v .githooks/pre-commit`. **Ignored** (it would never reach a teammate) ⇒ **do
     not append, do not ask, record NOTHING** — report the rule `check-ignore` printed and the fix (a
     `!.githooks/` negation **after** the broad ignore line), then continue. Recording nothing is
     deliberate: a repo that fixes its ignore rules is offered the chain next run.
  5. **Ask** (`AskUserQuestion`, **default: chain**) — *Chain (default):* "run the harness's commit-time
     checks (the architecture tree and your doc budgets) from your existing husky `pre-commit`; your
     hook keeps working exactly as it does today" · *Don't chain:* "leave husky untouched — the wrapper
     stays on disk but inactive, and both checks stay model-upheld / on-demand."
  6. **On chain, READ `.husky/pre-commit` first** (create it only if **absent**; never write into
     `.husky/_`, which husky generates):
     - **A failed read STOPS the chain.** Exists but unreadable ⇒ **stop and report**, never append. An
       unreadable file is not an absent marker, and treating it as one appends a duplicate block.
     - **Idempotent on the OPEN marker** — if `# >>> claugentic-dev-harness tree gate` already appears,
       **write nothing** and report "husky chain already present". The marker **is** the
       idempotency key: a second append would run the gate twice and double every message printed.
       Check for the marker **BEFORE** appending, on every run.
     - **Reachability — check before you call it live.** The block is appended at end-of-file. Scan the
       existing content for an **unconditional `exit`** above the append point: if one exists the block
       is **unreachable** — say so, and do **not** describe the gate as running.
  7. **APPEND at end-of-file — never overwrite — this marker-guarded block:**
     ```sh
     # >>> claugentic-dev-harness tree gate (managed marker — do not duplicate)
     # A MISSING wrapper must not block anyone: `if`/`fi` (never `[ -f … ] && { … }`, which
     # returns 1 when the test fails and would abort the commit from the hook's last line).
     # A wrapper that RUNS and fails still blocks — that is the gate doing its job.
     hook="$(git rev-parse --show-toplevel 2>/dev/null)/.githooks/pre-commit"
     if [ -f "$hook" ]; then sh "$hook" || exit 1; fi
     # <<< claugentic-dev-harness tree gate
     ```
     **This file is TRACKED — it runs on every teammate's machine**, which is why the guard is not
     optional: an absent wrapper (a fresh clone mid-`init`, a sparse checkout, a gitignored path) must
     degrade to *no gate*, never to *no commits for anybody*.
  8. **Never overwrite anything** — existing content is preserved byte-for-byte; the block only grows
     the file. **If the append created the file, mark it executable** (`chmod +x` /
     `git update-index --chmod=+x`) — husky runs the file directly, and a bitless hook is **skipped
     silently**: chained, reported, never run.
  9. **Chaining replaces nothing else:** still write `.githooks/pre-commit`, and still leave
     `core.hooksPath` untouched (husky owns it).
  10. **Record the choice** as `- Husky chain: <appended | declined (tree gate written but inactive)>`,
      keyed on that label, append-if-line-absent — step 2 is its reader. Report **"appended"**, not
      "chained": `init` appends a block; whether it *runs* is step 6's reachability question.
  11. **Propagation is the adopter's npm machinery, not the harness's.** A chained gate travels with the
      repo **usually for free — *if* the repo's own `package.json` carries husky's `prepare` script**.
      Detection matches a bare `.husky/` directory too, which may have no `prepare` at all: **the
      harness neither wires nor checks it.**
  12. **Solo mode: skip this whole procedure.** `.husky/pre-commit` is **tracked**, and the solo
      invariant forbids a tracked change. Report the `core.hooksPath` conflict per divergence (b) instead.

> **Solo divergence (b) — pre-commit hook → `.git/hooks/pre-commit`, NOT `.githooks/` +
> `core.hooksPath`.** In **solo mode** with the gate **ON**, write the **same wrapper** (run-logic
> byte-identical to the shared one above) to **`.git/hooks/pre-commit`** and **`chmod +x`** it — plus
> the merge sibling **`.git/hooks/pre-merge-commit`**, the same delegating `exec`, also `chmod +x`,
> because git fires *that* on a conflict-free merge. `.git/` is never tracked, so this places **no
> tracked file** and needs **no shared git config**: **do NOT run `git config core.hooksPath
> .githooks`** and **do NOT create a tracked `.githooks/` directory**. `core.hooksPath` stays at its git
> default, so the hook fires on every commit in this clone. **Never-clobber:** if `core.hooksPath` is
> already **non-default**, `.git/hooks/` would not run — **REPORT the conflict** ("core.hooksPath is set
> to `<value>`; in solo mode the tree gate's `.git/hooks/pre-commit` was written but won't fire while
> hooksPath points elsewhere — unset it or chain the gate from your own hook") and **continue**.
> **Idempotency:** "already wired" in solo = `.git/hooks/pre-commit` exists with the wrapper body ⇒
> skip. **Gate OFF** wires no hook in solo either.

> **Solo divergence (c) — SKIP step 5c entirely.** In **solo mode** run none of it: no plugin
> self-reference into `.claude/settings.json`, **no `.gitignore` negation**, **no teammate prompt** on
> clone — both writes are exactly what the solo invariant forbids (a tracked path, a committed-
> `.gitignore` edit). Solo adoption is deliberately **invisible to teammates**; the user installed the
> plugin on this clone themselves. In **shared mode** 5c runs exactly as written.

**(c) Plugin self-reference — declare the harness for teammates (team distribution).** The harness's
agents, skills, and engine live in the plugin install, not the adopter's repo, so a teammate who clones
gets the committed standards but **none of the tooling** unless they install it too. `init` seeds the
harness's own publication identity into the adopter's **committed** `.claude/settings.json`, so Claude
Code prompts them on open (the documented mechanism: `extraKnownMarketplaces` + `enabledPlugins`). That
identity is fixed: marketplace **`sh4npeiris`** = github **`sh4npeiris/claugentic-dev-harness`**, plugin
**`claugentic-dev-harness`**. This **runs regardless of the tree-gate decision**, and since (b) writes
nothing to `.claude/settings.json` it is that file's **only** writer — **strictly never-clobber: merge,
never replace.**

1. **Make `.claude/settings.json` git-trackable.** Read `.gitignore`; if it ignores `.claude/` or
   `.claude/*`, **append a `!.claude/settings.json` negation AFTER the broad ignore line** (a negation
   before its ignore does nothing). **Never** add `!.claude/settings.local.json` — that file MUST stay
   ignored (local / secret config). Already trackable ⇒ **skip the edit**, report "settings.json already
   trackable." Append-if-line-absent, keyed on the negation line.
2. **Create-or-merge `.claude/settings.json`.** **Parse** it as JSON; **absent → treat as `{}`** (and
   create it); **present but *malformed* → fail loudly: report it and skip the merge — never overwrite
   or corrupt it.** **Merge** these two entries, preserving every existing key/hook/permission and every
   existing marketplace/plugin entry (add, never overwrite a sibling):
   - into `extraKnownMarketplaces` (create the map only if absent):
     `"sh4npeiris": { "source": { "source": "github", "repo": "sh4npeiris/claugentic-dev-harness" } }`
   - into `enabledPlugins` (create the map only if absent):
     `"claugentic-dev-harness@sh4npeiris": true`
   - **Idempotency:** both already present (keyed on the `sh4npeiris` marketplace key and the
     `claugentic-dev-harness@sh4npeiris` plugin key) ⇒ **skip**, report "plugin self-reference already
     declared."

### 6. Write the CLAUDE.md harness section (create / append-at-EOF / refresh-inside-fence)

> **Solo divergence (d) — the harness anchor → `CLAUDE.local.md`, NOT the committed `CLAUDE.md`.**
> In **solo mode**, write **everything this step writes** — the managed fence, the seeded **Current
> scope** block, and the **detected-tooling block** with all its recorded lines — into
> **`CLAUDE.local.md`**, Claude Code's conventional **local** anchor (loaded as repo context like
> `CLAUDE.md`). **git does NOT ignore it by default** — divergence (a) appends it to
> `.git/info/exclude`, which is what keeps it untracked, so the committed `CLAUDE.md` is left
> **byte-untouched**. **All three cases below apply unchanged, just to `CLAUDE.local.md`.** **ONE
> omission:** the fence's **teammate bootstrap block** is **shared-mode only** — solo wiring is
> `.git/hooks/pre-commit` on this clone alone, so there is no teammate to bootstrap and
> `core.hooksPath` must stay at its git default (setting it to `.githooks` would *disable* the solo hook).

Three cases — **never modify existing content outside the managed fence** (the Current-scope and
detected-tooling blocks are *seeded* outside it on first run and never rewritten):
- **`CLAUDE.md` absent →** create it with the managed pointer block (in the fence) + the Current-scope
  block (outside it) below.
- **Present, *no* fence →** **append** the fenced block at **end-of-file**, touching **nothing above**.
  Seed the Current-scope block after the fence.
- **Present *with* the fence → refresh inside the fence (the re-run path).** Regenerate the managed
  block from the **current** template and **replace only the text between
  `<!-- harness:managed:start -->` and `<!-- harness:managed:end -->`**, preserving everything outside
  the markers **byte-for-byte**; byte-identical regeneration is a no-op. The fence embeds
  `claugentic-dev-harness@{VERSION}`, so a version bump alone makes it differ. **This refreshed fence
  is the authoritative repo-version readout** (the reason per-file stamps need no RESTAMP — step 3).
  - **Malformed fence → stop and report (never guess the extent).** A `start` marker without its
    matching `end`, or either marker duplicated, makes the extent **ambiguous** and a replace could
    destroy human content. Per the never-clobber / stop-if-ambiguous invariant, **stop and report for
    manual reconciliation.**

**What goes in the managed fence** — **stable, no volatile content**, so a re-write is byte-identical:
- **Pointers to the local managed files** the agents read: `docs/claugentic-standards/README.md`,
  `docs/claugentic-WORKFLOW.md`, `docs/claugentic-ENGINEERING_STANDARDS.md`,
  `docs/claugentic-ARCHITECTURE_TREE.md`, `docs/claugentic-DECISIONS.md`, `docs/claugentic-ROADMAP.md`,
  the optional charter `docs/claugentic-CHARTER.md` (empty ≡ the harness's default behavior), and
  `docs/claugentic-PLAYBOOK.md` for how to drive the harness plus adoption notes — including that the
  architecture-tree and doc-budget checks run at commit time, not while you edit.
- **The teammate bootstrap block** (shared mode only). Git **never activates hooks on clone**, by
  design, so a teammate's fresh clone commits with no gate at all until one command is run — the single
  most common way team wiring silently stops existing. Write it **check-first**, so it needs no
  per-repo variation and can never assert something this repo did not do:
  > **New clone? Hooks never activate automatically** (git's design) — check before you commit: run
  > `git config --get core.hooksPath`.
  > - prints `.githooks` → wired; nothing to do.
  > - prints nothing → run `git config core.hooksPath .githooks` **once per clone** (or re-run
  >   `/claugentic-dev-harness:init`).
  > - prints `.husky` or `.husky/_` → **do not change it** (that would disable this repo's husky
  >   hooks). Run `npm install` so husky installs its hooks; the harness check runs too **only if**
  >   `.husky/pre-commit` contains the `claugentic-dev-harness tree gate` marker — grep it, and if it
  >   is absent re-run `/claugentic-dev-harness:init`, which can chain it.
- The **engineering principles** (SOLID > DRY > KISS > YAGNI; validate at boundaries; fail loudly;
  configurable over hardcoded; single source of truth), a **workflow pointer** ("substantial work
  follows `docs/claugentic-WORKFLOW.md`"), and the **plugin version**
  (`claugentic-dev-harness@{VERSION}` — a static token, not a date).
- An **authority + conflict-resolution clause**, written **honestly as model-upheld** — there is no
  mechanical file-hiding, so it must not claim a mechanical guarantee. Use this wording **verbatim**
  (it is part of the byte-identical fence):
  > **How we work here is defined by the harness.** `docs/claugentic-WORKFLOW.md`,
  > `docs/claugentic-ENGINEERING_STANDARDS.md`, `docs/claugentic-PLAYBOOK.md`, and `docs/claugentic-ARCHITECTURE_TREE.md` are
  > the **authoritative** process + standards. Other `.md` files in this repo are
  > **project/domain content, not process authority** — even if they describe a way of
  > working, they do not override the harness. **On any conflict, the harness wins.** When
  > you are genuinely unsure which applies, **follow the harness and ask.** (This is
  > model-upheld guidance, not a mechanical guarantee — `CLAUDE.md` is the always-loaded
  > anchor and asking is the safety valve.)

**What goes OUTSIDE the managed fence** (local, editable, never overwritten):
- A **Current scope** block, seeded once — a short, non-capping snapshot of which standards dimensions
  are LIVE in this repo today (it grows as the stack grows; relevance is always a per-change judgment).
  It deliberately does **not** live in the managed `claugentic-ENGINEERING_STANDARDS.md`, which is a
  managed copy and never the home of per-repo content. Seed it from step 1's detected ecosystem (e.g.
  for a JS web app: `maintainability-structure`, `testing`, `security`, `api-and-contracts`,
  `product-ux`).
- The **detected existing tooling** block (step 8), **seeded create-if-absent** like Current scope: a
  re-run leaves an existing block byte-untouched. **Its labeled recorded-choice lines are the
  exception** — step 8 lists them and each owning step states its own keying.

### 7. Seed the create-if-absent files: (a) `docs/claugentic-ROADMAP.md` + `docs/claugentic-DECISIONS.md` + `docs/claugentic-CHARTER.md` · (b) the doc-budget caps config

**(a) The ledger seeds** — the **one-time-seed** managed-file kind (the third in the WORKFLOW
Adopter-note's three-kinds taxonomy). The bytes are **shipped pristine `_X.md` files**; `init` copies
them, **stripping the leading underscore**: `${SOURCE}/docs/claugentic-_DECISIONS.md` →
`docs/claugentic-DECISIONS.md`, `_ROADMAP.md` → `docs/claugentic-ROADMAP.md`, and `_CHARTER.md` →
`docs/claugentic-CHARTER.md` — the OPTIONAL engineering charter, with **no forced "pick your
methodology" question** (an empty/absent charter ≡ the harness's default behavior). `${SOURCE}` is the
step-1 source, the same one step 3 copies from.

- **CREATE-IF-ABSENT ONLY — never refresh, never clobber.** Target present ⇒ **skip byte-untouched**
  (`skipped (present)`); write only when absent (`created`). A filled ledger is the adopter's own file.
- **The underscore-prefix convention (`_X.md` → `X.md`)** marks a **one-time seed** — copied once,
  renamed, **never refreshed**. **Distinct from `*_TEMPLATE.md`** (repeated-use plan / product-spec /
  standards-module skeletons, which the step-3 managed set DOES refresh). See WORKFLOW → Adopter note.
- **Seeds stay OUT of the managed-set table (step 3)** — a REFRESH would clobber a filled ledger. Two
  guards keep that safe: this step is create-if-absent, and a path outside the managed set can never
  satisfy the genuine-managed predicate (leg 1). Do not add a seed row to that table.
- Seeds ship **unstamped** and `init` does **NOT** stamp one — an unstamped target is exactly the
  create-if-absent signal. The harness's own filled `DECISIONS.md`/`ROADMAP.md` are stripped from the
  release; the adopter gets the pristine seed. (The harness keeps no live `CHARTER.md`; the
  `_CHARTER.md` seed still ships.)
- The seeded `ROADMAP.md` carries **no** `harness-audit:*` / `harness-product:backlog` fences —
  `/claugentic-dev-harness:audit` and `:product` gap mode **self-create** theirs on first run.

**(b) Seed the doc-budget caps config `.claude/claugentic-doc-budgets.json` — create-if-absent only**,
same never-refresh posture and for the same reason: once written the caps are **the adopter's own tuned
data**. This is what makes the step-3 gate *do* anything (with no config it is a quiet exit-0 no-op),
and it is the same file `/doctor`'s budget advisory and `/condense` read (**one cap source per repo,
two readers**).

- **Write it only when ABSENT.** Present ⇒ **skip byte-untouched**, report `skipped (present)`. Never
  merge, never add a key to an existing config, never "fix" a cap.
- **Read the `- Doc budgets:` record BEFORE seeding.** Record present *and* config absent = **the
  adopter deleted it on purpose** (removing the file is the documented opt-out) ⇒ **do not re-seed**;
  report `skipped (removed by you — the record says init already seeded one; delete the record line to
  be offered a fresh seed)`. Without this reader every re-run would resurrect a config the user threw
  away.
- **The seed — exactly this, and nothing else:**
  ```json
  {
    "CLAUDE.md": 6000,
    "docs/claugentic-DECISIONS.md": 3500,
    "docs/claugentic-decisions/*.md": 14000,
    "docs/claugentic-ROADMAP.md": 14000,
    "docs/claugentic-CHARTER.md": 8000
  }
  ```
  **Why exactly these five keys — "cap only what this same run guarantees exists":** `CLAUDE.md` comes
  from step 6 **in shared mode** (solo writes `CLAUDE.local.md` — see the anchoring bullet);
  `DECISIONS.md`, `ROADMAP.md`, `CHARTER.md` come from the seeds above; and
  `docs/claugentic-decisions/*.md` is a **shape, not a file** — a glob matching nothing is skipped
  silently, so it is safe from day one and needs no edit when the ledger is later sharded (it also
  structurally excludes the managed full-copy docs, which live elsewhere).
  **NEVER add an `INVARIANTS` or `WORKFLOW` key — one rule, two DIFFERENT reasons.**
  `docs/claugentic-INVARIANTS.md` is created **lazily by the workflow**, not by `init`, and a cap on an
  **absent** file is a hard exit-1 breach — *even under `reportOnly`*, which graces the size verdict
  only. **WORKFLOW is not that case: `init` DELIVERS it, so it is present.** It is excluded because it
  is a **managed full-copy doc the adopter does not author** — capping it would fire their own gate on
  harness-authored bytes they cannot condense, and a re-`init` could breach it unaided. **Do not copy
  the harness's own config**: it caps `INVARIANTS.md` because this repo has one, and its numbers are
  that repo's load profile.
- **Anchor every key to what THIS run leaves on disk — the mode matters.** In **solo mode** the anchor
  is **`CLAUDE.local.md`** (divergence (d)) and the committed `CLAUDE.md` is left byte-untouched, so
  **seed `CLAUDE.local.md` in place of the `CLAUDE.md` key**, at the same cap. (The three step-7a seeds
  are written to disk in both modes — divergence (a) only excludes them from git — so they need no
  substitution.) **General safety clause, applied last:** before writing, **drop any non-glob key whose
  target does not exist on disk at the end of this run.** A cap on an absent file is a hard exit 1 that
  `reportOnly` cannot grace, and with the gate chained into the hook that blocks **every commit** — a
  fresh adopter's first one included. A glob key is exempt: zero matches is a silent skip.
- **The numbers are the HARNESS's own load-profile recommendations — not measurements of your repo, and
  not telemetry (there is none, by design — the harness collects nothing).** Say it that way in the
  report: an agent writing from inside the adopter's repo must not imply the caps came from *their*
  ledgers. They encode load: `CLAUDE.md` is tight because it is always loaded; a sharded decisions
  ledger caps the routing index far tighter than a shard; `CHARTER.md` should stay skimmable. Say that
  tuning them is a one-line edit plus a dated `docs/claugentic-DECISIONS.md` line
  (`docs/claugentic-WORKFLOW.md` → the escape-valve ladder).
- **Day-one-over — the grace flag, NEVER a bigger number.** Before writing, **measure** each seeded path
  that already exists (`len(read_bytes())` — bytes, not characters) — **and for the glob entry, expand
  it and measure EVERY match**, because the cap applies per matched file: an adopter who sharded their
  ledger before adopting would otherwise take a strict breach on their first commit, the exact hard
  block this rule prevents. Any match over cap ⇒ seed **that entry** `reportOnly`, in the object form
  `{"max": <the recommended number>, "reportOnly": true}` — the cap stays honest and the breach is
  reported loudly at every run while passing. **Never seed a cap raised to fit** the current size: that
  is the mechanical ceiling-raise the escape-valve ladder's rung 2 forbids (a raise is a recorded human
  decision, never an init default). State plainly in the report that **nothing mechanical ever clears a
  `reportOnly` flag** — `/condense` does the work and you delete the flag when the file is genuinely
  under cap.
- **Trackability (shared mode) — the config must be committed or it measures nothing.** An ignored
  config is indistinguishable from an un-configured repo: green on the author's machine, silent
  everywhere else. Mirror step 5c: read `.gitignore`, and if it ignores `.claude/` or `.claude/*`,
  **append a `!.claude/claugentic-doc-budgets.json` negation AFTER the broad ignore line**
  (append-if-line-absent). Then **verify** with `git check-ignore -v
  .claude/claugentic-doc-budgets.json`: STILL ignored (a rule the harness must not fight — a global
  excludes file, a later broader pattern) ⇒ **REFUSE** — write nothing, record nothing, report the rule
  and the one-line fix. Recording nothing is deliberate: a repo that fixes its ignore rules is seeded on
  the next run. **Solo mode:** no `.gitignore` edit at all — the path goes into `.git/info/exclude` per
  divergence (a), where being untracked is the point.
- **Record it:** `- Doc budgets: <seeded | skipped (present)>` in the detected-tooling block (step 8),
  **keyed on the `Doc budgets:` label**, append-if-line-absent and never rewritten — the line this
  step's own reader consumes above. The **refused** case writes **no line**, like the husky refusal.
- **Stays OUT of the step-3 managed-set table**, for the same reason as the ledger seeds and with the
  same two guards. Do not add a row for it.

### 8. Detect + record existing tooling (never reconfigure)

- **Scan** for the adopter's own gates: lint/format (`eslint`, `.eslintrc*`, `prettier`), type-check
  (`tsconfig.json`), test runner (`jest`/`vitest`/`pytest`/`go test` config), CI
  (`.github/workflows`, `.gitlab-ci.yml`). **Reuse `/claugentic-dev-harness:audit` Phase 1's tooling
  detection** (DRY).
- **Record** what you find in the **detected-tooling block** (step 6, outside the managed fence) as
  **the project's gates** — the workflow uses *these*, not new ones imposed on top. **Create-if-absent:**
  write the block only when none exists; a re-run leaves an existing one byte-untouched.
- **Detect + record only — never install, never reconfigure**; the harness *composes* with what's here.
- **Also detect + record how to RUN the app** — the one line `engine/qa.js` consumes (the
  runtime-verification workflow can't read files, so the invoking skill relays it as `args`).
  **Detection order:**
  1. **A compose file at repo root** (`docker-compose.yml`/`.yaml`, `compose.yml`/`.yaml`) → record
     `docker compose up -d`; derive the **App URL** from the first published host port when it parses
     cheaply (`8000:8000` → `http://localhost:8000`), else use the placeholder and ask the user to
     complete it in the report.
  2. **Else a dev-server command** via the **same Phase-1 ecosystem detection** (DRY): `package.json`
     `dev` script (then `start`) run via the detected package manager; a Python ASGI/Django heuristic
     (`uvicorn <module>:app` / `python manage.py runserver`). Take the App URL from the framework's
     conventional dev port.
  3. **Undetectable** → record the honest placeholder and report it:
     `- Run the app: (not detected — fill in: \`<command>\` · App URL: \`<url>\`)`.
- **The ONE durable home** is a labeled line in the detected-tooling block — already the single
  user-editable home for "the project's own tooling", so no new artifact class (**DRY**):
  `- Run the app: \`<command>\` · App URL: \`<url>\`` (optionally ` · Stop: \`<command>\``).
  **Never-clobber-safe extension:** the block stays create-if-absent, but a block that exists
  **without** that line gets it **appended** (append-if-line-absent, keyed on the label); an existing
  line is **never modified**. Pure addition.
- **The four recorded-choice lines** live in this block too, each **keyed on its own label** and
  **owned by the step that writes it — do not restate their rules here**: `- Architecture tree:`
  (step 4) · `- Harness mode:` (step 1) · `- Husky chain:` (5b, whose step 2 is its reader) ·
  `- Doc budgets:` (7b, which reads it before seeding). All four are append-if-line-absent; only
  `- Architecture tree:` is ever rewritten, and only on on-disk disagreement. Steps 1 and 4 read
  theirs **before** prompting, so the values written here are the honored outcomes. **The block
  itself is routed by the mode** (divergence (d)): solo ⇒ `CLAUDE.local.md`, shared ⇒ `CLAUDE.md` —
  that is what makes a re-`init` read its own mode back.

**(detect a competing way-of-work doc — non-destructive; never delete).** A rival way-of-work /
agent-instruction doc can mislead agents. The step-6 authority clause already defuses it (the harness
wins on conflict), but `init` also **surfaces** it once so the user can decide whether to **harvest**
lessons from it.

- **Detection — a small, high-precision NAME allow-list only** (precision over recall; the authority
  clause covers the misses): a **non-managed** `WORKFLOW.md`-class file (not a genuine managed copy per
  the step-3 predicate), `.cursorrules`, `AGENTS.md`, `.github/copilot-instructions.md` (or a root
  `copilot-instructions.md`), and a `SUITE_HARNESS`-style doc. **`CLAUDE.md` is NEVER flagged** — it is
  the designed merge target for the managed fence, not a competitor. Match on these names only; do
  **not** content-scan arbitrary `.md` files for "process-like" prose (that re-introduces the
  false-positive rot).
- **Prompt (only when one is found and not already recorded):** *"Found `<X>` — it overlaps the harness
  way of work. The harness is now the authority (see the `CLAUDE.md` clause), so this file won't
  override it. Want me to **fold any lessons from it into the harness** (a quick scan, then I leave the
  file in place), or **leave it as-is**?"*
  - **Fold in (harvest)** → scan `<X>` and surface anything worth promoting (a ROADMAP item, a DECISIONS
    note, a suggested standards addition — **propose**, never silently rewrite managed files); **leave
    `<X>` in place**.
  - **Leave it** → do nothing; the authority clause defuses it.
  - **NEVER delete `<X>` (or any user file), ever** — non-destructive is absolute.
  - **Confirmation discipline:** act on the explicit choice only; on silence/default/unavailable,
    **default to "leave it"** and report it.
- **Record** one label-keyed line — `- Competing way-of-work docs: reviewed (your init choice)`, keyed
  on the `Competing way-of-work docs:` label, append-if-line-absent (no per-file keying; this is a
  low-stakes advisory prompt). Read it **before** prompting; present ⇒ **skip the prompt**.

### 9. Report

**Open with a one-line readiness summary** built only from detections `init` already ran (no new
mechanism): the step-1 harness mode, the step-4 tree-gate decision, the step-1 Python interpreter, and
the step-5c plugin self-reference. (**NOT** the scripted engine — its availability is a per-session
run-time condition `init` cannot know at setup time.) Each item reads `<on>` when healthy or
**`reduced — <what's missing>`** when degraded — e.g. *"Setup: mode SHARED · tree-gate ON · Python
**reduced — none found; install Python 3 to enable the tree check** · plugin declared for teammates"*.
**In solo mode** it **omits the plugin item** (5c is skipped) and reads mode SOLO (local-only).
Tree-gate `OFF` and mode SOLO are healthy chosen states, never "reduced."

**Then lead with a plain-English headline**, before the grouped summary, so a non-engineer reads it
first. **Branch on ONE predicate — did this run write anything the USER owns?** Compute it
directly: the tree on **Replace**, the pre-commit wrapper, a `.gitignore`/`.gitattributes` append, or
any **refreshed managed file**. **Never compute it from the Refreshed/Created groups** — the Replace
overwrite is filed under **Created**, so a group-based branch emits *"nothing overwritten"* on the one
path that overwrites a user-owned file.
- **Wrote nothing at all →** *"Done — everything is already at the installed version; I changed
  nothing. I did NOT touch any of your code or your own files."*
- **Wrote only NEW files →** *"Done — I added a code map, a quality checklist, and a safety check. I
  did NOT change any of your code or overwrite your own files — nothing existing was modified."*
- **Touched ANYTHING user-owned → say what, by name, IN THE HEADLINE — before any reassurance**, e.g.
  *"Done — and I replaced your `docs/claugentic-ARCHITECTURE_TREE.md` with a harness skeleton, as you
  confirmed."* Then **append the honest caveat:** *"Files marked `claugentic-dev-harness managed — do
  not edit` were refreshed to the installed version; if you had edited one of those, your edits were
  replaced — they're listed in the Refreshed group below, and git history keeps any version you
  committed (uncommitted edits to a managed file are not recoverable — commit before re-running
  `init`)."* **Never assert "I did NOT overwrite your own files" unconditionally when a managed file
  was refreshed** — that is false for anyone who edited one. (The `CLAUDE.md` fence is separate: only
  the content between the markers is replaced.)

**The architecture-tree branch of the honesty register** — name the tree action plainly, per step 4's
outcome: **Fresh** → "created a starter code map — it fills in as you add code"; **Mature-no-tree** →
"created a code map listing every source file from `git ls-files`; descriptions stay thin and improve
as the code is touched — nothing of yours was overwritten (you had no tree)"; **Keep-mine-gate-off** →
"left your `docs/claugentic-ARCHITECTURE_TREE.md` untouched and turned the tree-gate OFF for this repo
— no blocking check on your tree (it stays model-upheld via `CLAUDE.md`); to switch to the harness
format later, delete the tree and re-run `init`". **Replace (confirmed) — the one user-file overwrite,
name it loudly:** *"Replaced your `docs/claugentic-ARCHITECTURE_TREE.md` with a harness skeleton — your
previous tree is in git history (an uncommitted tree is unrecoverable)."* That is the **only** path in
`init` that overwrites a user-owned file, and only because you explicitly chose Replace.

Then tell the user the **setup is live** — honestly, implying no restart where none is needed (a skill
**cannot** restart a session; don't pretend otherwise):
- **Tree-gate ON:** **two gates run at commit time**, once per `git commit` — no restart, no per-action
  overhead. A missing tree entry, an entry longer than `MAX_ENTRY_CHARS` (in
  `scripts/claugentic-check_architecture_tree.py`), or a ledger over its cap **aborts that commit**; a
  ledger at **≥90%** of its cap prints a WARN and lets the commit through. Name the hook path per mode:
  **shared** → `.githooks/pre-commit` via `core.hooksPath=.githooks` (travels with the repo); **solo**
  → `.git/hooks/pre-commit` (local, untracked).
- **Tree-gate OFF:** say plainly that **no pre-commit hook was wired, so neither gate runs at commit
  time here**. Both scripts are still on disk: `python scripts/claugentic-check_architecture_tree.py`
  for a one-off check (it would flag a non-backtick tree, which is why the gate is off) and `python
  scripts/claugentic-check_doc_budgets.py` for the budget verdict — and `/claugentic-dev-harness:doctor`
  runs them for you.
- **You (the agent) have adopted the harness workflow for the rest of this session** — follow
  `docs/claugentic-WORKFLOW.md` from here; work continues immediately.
- **Suggest `/clear` or `/compact`** (quick — not a whole new chat): that is what loads the new
  `CLAUDE.md` (or `CLAUDE.local.md` in solo) as cached context. Recommend it before a big `audit` run;
  optional otherwise; in place next session regardless. **Never tell the user they *must* "start a
  fresh chat."**

**The solo-mode honesty + verification block — emit ONLY in solo mode** (omitted entirely in shared):
- **Solo honesty line:** *"I adopted the harness **solo / local-only** — everything I wrote lives on
  this clone alone: the managed docs, code map, and the `CLAUDE.local.md` anchor are kept untracked via
  `.git/info/exclude` (not your committed `.gitignore`, which I did **not** touch — git does not ignore
  `CLAUDE.local.md` on its own), and the tree gate is `.git/hooks/pre-commit` (local). **No new tracked
  file, no committed-`.gitignore` edit, no shared git config — a teammate's clone is byte-identical and
  unaffected.**"*
- **Verification claim (state only what you confirmed):** run `git status --porcelain` and confirm
  **zero new TRACKED paths**; run `git diff -- .gitignore` and confirm it is **empty**. Report both:
  *"Verified: `git status` shows no new tracked paths; `git diff -- .gitignore` is empty."*
- **The `git check-ignore` guard — FAIL LOUD if a should-be-local path is not ignored.** Run
  `git check-ignore <path>` for **each** solo-written path (everything appended to `.git/info/exclude`,
  plus `CLAUDE.local.md`). If **any** is **not** ignored — it would become a tracked change and leak to
  teammates — **do NOT paper over it**: report it **loudly** as a solo-invariant breach naming the exact
  path, and say the solo guarantee does not hold for it until it is excluded. That failure line
  **replaces** the clean verification claim above.

Then the **next step**, branched on the *Application source present* predicate (audit Phase 1): **has
app source** → *"Next: run `/claugentic-dev-harness:audit` — I'll explain your codebase in plain
English and write a prioritized backlog of the work worth doing. (A quick `/clear` first gives the
audit clean context.)"*; **no app source yet** → *"Next: just tell me what you want to build — describe
your first feature in plain English and I'll run the workflow. No need to run
`/claugentic-dev-harness:audit` until there's code to audit."*

Then emit the clear summary, grouped. **The group names are the contract:**
- **Created** — files written from scratch + managed files that were absent. Name the caps config
  (`seeded` / `skipped (present)` / refused / opted-out), and for any entry seeded `reportOnly`, **say
  which files and that nothing mechanical clears the flag** (`/claugentic-dev-harness:condense` does the
  work; you delete the flag). Name **which mode** produced the tree: minimal · cheap-complete skeleton ·
  **replaced-by-skeleton** (the user-file overwrite) · **kept-untouched, gate off**.
- **Refreshed** — managed files (and the CLAUDE.md fence) brought to the installed version because the
  body drifted **or the stamp was in an old trailing-clause format**; **each by path**, `<old> →
  <installed>`.
- **Skipped (already current)** — body matched; byte-untouched even if the stamp semver was older.
- **Skipped (user file / unrecognized stamp)** — not genuine managed copies; untouched, reported for
  manual reconciliation.
- **Wired** — the **pre-commit hook** and the **two gates chained into it** (tree check `--staged`, then
  the doc-budget check with no args), per mode: **shared** → `.githooks/pre-commit` +
  `core.hooksPath=.githooks`; **solo** → `.git/hooks/pre-commit`. Report whichever reconciliation
  outcome applies — "pre-commit hook already wired (budget gate chained)" · "wrapper: refreshed (chained
  the budget gate)" · the **never-clobber** report, which names neither the adopter nor an author and
  whose remedy is **shape-aware**. **Gate OFF ⇒ no wrapper ⇒ no commit-time budget signal** — say that
  plainly; the gate is still on disk and still runs when invoked. Flag a `core.hooksPath` **conflict**,
  or **"tree-gate OFF — no pre-commit hook wired"**. **When husky was detected**, name the outcome —
  **"appended", never "chained"**: *appended* (noting it reaches teammates **if** their `package.json`
  carries husky's `prepare` script, and flagging **unreachable** when an unconditional `exit` sits above
  the block) · *already present* · *declined* · *refused — `.githooks/pre-commit` is git-ignored*, with
  the rule and the fix · in **solo** the offer is skipped, so report the `core.hooksPath` conflict.
- **Merged** — the `.claude/settings.json` plugin self-reference, or "already declared". **Omitted in
  solo mode** (5c is skipped; the solo honesty block reports that instead).
- **Locally excluded (solo only)** — the paths appended to `.git/info/exclude`, each confirmed ignored
  via `git check-ignore`.
- **Detected** — the ecosystem, the interpreter, the existing tooling, the recorded **harness mode** and
  **architecture-tree choice**, and any **competing way-of-work doc**: name it, state the harvest
  outcome, confirm **it was NOT deleted**, and list whatever a harvest promoted.

**One caution to raise — build-time content scanners that read `docs/`.** A repo-wide content scanner
can ingest harness prose and **fail the build on a string it was never meant to read** (real adopter
incident: a CSS-utility scanner globbing the whole repo broke that project's build until `docs/` was
excluded). **Raise it whenever one is present, even if step 8 reported nothing** — it names its own
sources, because step 8's gate-oriented scan would never surface one: a Tailwind/UnoCSS
`content`/`include` glob over the repo · a docs/search-index build · a generator reading `**/*.md`.
Fix: **exclude `docs/` from the scanner's globs.** No mechanical check does this — `init` neither reads
nor edits your build config, so it is deliberately a prose flag.

**A repo already at the installed version reports** "already at the installed version — nothing to
refresh."; otherwise the Refreshed group lists what moved.

---

## Idempotency at a fixed version — the hard safety check

Re-running `init` **converges the repo to the installed version**, and is a **true no-op only when it
is already there**. The drift decision and the writes are **`init`'s judgment** (rule-bound,
never-clobber-guarded by stop-if-ambiguous), **not a mechanical oracle** — so **idempotency here is
checked by a dogfood run, not a wired gate.** It holds because every write above is one of three
already-convergent shapes: **managed upsert** (identical body + current-form stamp → `CURRENT`,
byte-untouched; drift or an old-format stamp → one `REFRESH`, after which it reads `CURRENT`) ·
**create-if-absent and user-owned, never refreshed** (the tree, the three ledger seeds, the caps config
— plus the `- Doc budgets:` opt-out reader, so a deleted config stays deleted) · **append/merge keyed
on its own marker** (`.git/info/exclude` patterns, the recorded-choice lines, the `.gitignore`
negations, and the `.claude/settings.json` merge keyed on the `sh4npeiris` marketplace +
`claugentic-dev-harness@sh4npeiris` plugin keys).

Three places need naming because they are not simply "write once":
- **The recorded choices are read BEFORE any prompt**, so a settled re-run never re-prompts: a
  `keep-gate-off` repo wires no hook and re-derives no globs (its `INCLUDE_GLOBS = []` is
  carve-out-protected); a `harness-skeleton` repo's tree already exists. **Only the `Architecture
  tree:` line is ever rewritten**, and only when on-disk state diverges — not the byte-identical re-run.
- **The pre-commit hook** is "already wired" when `.githooks/pre-commit` exists AND `core.hooksPath` is
  `.githooks` (solo: the `.git/hooks/pre-commit` presence) ⇒ a re-run writes nothing. **The one bounded
  exception is convergent, not repeating:** a wrapper whose run logic is this version's shape without
  the budget line is refreshed **once**, after which every later run takes the already-chained branch;
  any other shape is never touched at all — also a no-op, with a report. Gate-off wires no hook.
- **The CLAUDE.md fence** (or `CLAUDE.local.md` in solo) is refreshed inside the markers from a template
  with **no volatile content**, so once it embeds the installed `{VERSION}` a re-run regenerates a
  byte-identical inner block; everything outside is preserved byte-for-byte. Every solo divergence is
  likewise idempotent, and `git status` stays clean — nothing was tracked to begin with.

**Acceptance of a 2nd run at the same installed version:** `git status` in the target shows **zero
changes** and the report says everything was already current. If such a re-run dirties the repo, an
idempotency guard is missing — that is a bug, not expected behavior. (A re-run *after a version bump*
is expected to refresh — that is convergence, not a bug.)

## What this skill does NOT do (honest scope)

- It does **not** install or reconfigure your linters/test runner — it **detects and records** them
  (step 8) so the workflow composes with them.
- It does **not** refresh your **user-owned** files — `docs/claugentic-ARCHITECTURE_TREE.md`,
  `docs/claugentic-ROADMAP.md`, `docs/claugentic-DECISIONS.md`, `docs/claugentic-CHARTER.md` and
  `.claude/claugentic-doc-budgets.json` are seeded create-if-absent and then left to you (your tuned
  caps included).
- It does **not** 3-way-merge a user-edited **managed** file — managed files are marked *do not edit*
  and carry no user content by contract (sole exception: the `claugentic-check_architecture_tree.py`
  `INCLUDE_GLOBS` knob, preserved per step 3); on a genuine drift the installed version wins (reported
  by path) and **git is the review/recovery net** for content you committed (an uncommitted edit isn't
  recoverable — see the roadmap).
- It does **not** generally reconcile the pre-commit wrapper **contents** across versions —
  idempotency keys on the hook's presence. **Exactly one shape is repaired** (5b): a wrapper whose run
  logic is this version's shape without the budget line gets the chain line added. Anything else — a
  wrapper from **v0.5.1 or earlier** (which no `init` re-run will auto-chain), or one you edited — is
  **never rewritten**; you get a shape-aware report instead. General version-to-version reconciliation
  stays on the roadmap.
- **In solo / local-only mode it does NOT** declare the plugin for teammates, edit your committed
  `.gitignore`, or set any shared git config — solo adoption is invisible to teammates by design. The
  trade-off: a teammate who clones gets **none** of the harness — switch to **Shared** mode (re-`init`,
  choose Shared) when the team should adopt it too.
- It does **not** audit your code or write a backlog — that is **`/claugentic-dev-harness:audit`**.
