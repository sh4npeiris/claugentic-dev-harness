---
description: Scaffold the claugentic-dev-harness into the current repo — copy the managed harness set (standards catalog, workflow, playbook, tree-check), generate docs/ARCHITECTURE_TREE.md, set the tree-check globs, wire the hook, git-init if needed, seed ROADMAP/DECISIONS, write a CLAUDE.md harness section, and compose with existing lint/type-check/test tooling. Idempotent; never clobbers — re-running is a safe no-op.
---

# /claugentic-dev-harness:init

Scaffold this harness into the current repo, **without clobbering anything**. Every
write is **detect → create-if-absent / merge-inside-a-fence / report** — the `init` skill
**never** overwrites user content, and **running it twice is a provable no-op** (the 2nd
run creates nothing, merges nothing new, and reports everything as already present).

## How this skill works

A top-level agent (the orchestrator) follows the **9-step procedure** below in order.
Each step is guarded — it detects the current state first, acts only if something is
absent (or merges into a fence if present), and reports what it did. The output is a
clear **created / skipped / merged / detected** summary.

**Never-clobber is the load-bearing safety invariant** (this writes into someone else's
repo — a careless overwrite is data loss). If any step is ambiguous about whether a
write would destroy user content, **stop and report rather than guess.**

### Two durable conventions this skill establishes

These are contracts the `init` skill's own re-run idempotency **and** the later
`/claugentic-dev-harness:update` depend on — they are deliberate, not incidental:

1. **The managed-stamp** — every file the `init` skill *copies* gets a stamp on its **first
   line** so a managed copy is unmistakable and machine-parseable:
   - **Markdown:** `<!-- claugentic-dev-harness@{VERSION} managed — do not edit; run /claugentic-dev-harness:update to refresh -->`
   - **Python:** `# claugentic-dev-harness@{VERSION} managed — do not edit; run /claugentic-dev-harness:update to refresh`
   - `{VERSION}` is read from the plugin's `plugin.json` `version` field (e.g. `0.1.0`).
   - The greppable token is **`claugentic-dev-harness@<semver>`**. Idempotency detects an
     already-copied managed file by the presence of `claugentic-dev-harness@`; `/claugentic-dev-harness:update`
     (later) regexes the semver to compare versions. Do **not** vary this format.

2. **The CLAUDE.md `harness:managed` fence** — the harness section the `init` skill writes
   into the adopter's `CLAUDE.md` lives between exact HTML-comment markers:
   ```
   <!-- harness:managed:start -->
   …managed pointer block — refreshed by /claugentic-dev-harness:update…
   <!-- harness:managed:end -->
   ```
   **Replace only inside the fence; everything outside it is human-owned and never
   touched.** Mirrors the established `harness-audit:overview` / `harness-audit:backlog`
   fences. **No volatile content (timestamps, counters, run-dates) goes inside the
   managed fence** — so a re-run with identical inputs is **byte-identical** and the
   "zero diffs on the 2nd run" guarantee holds. The seeded **Current scope** block lives
   **outside** this fence (local, editable, never overwritten — see step 6).

---

## The 9-step procedure

Run these in order. Each is **detect → create-if-absent / merge-in-fence → report.**

### 1. Preflight

- **Resolve the managed-set source.** When installed as a plugin, the source is the
  plugin root — **`${CLAUDE_PLUGIN_ROOT}`** (verified to expand in skill context). When
  running **from this harness's own repo in dev** (not installed), treat **the repo root**
  as the source. State which you're using in the report. *(The true installed-plugin
  `${CLAUDE_PLUGIN_ROOT}` resolution is exercised by the cold-install dogfood, plan 0003
  S5 — not by a dev run.)*
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

### 3. Copy the managed harness set (copy-if-absent, stamped)

Copy each of the following from the source (step 1) into the target, **copy-if-absent /
skip-if-present**, **stamping the first line** with the managed-stamp (convention 1):

| Source path | What it is |
|---|---|
| `docs/standards/` | the **11 authored modules** + `_TEMPLATE.md` + `README.md` (the whole catalog directory) |
| `docs/WORKFLOW.md` | the staged development workflow (process source of truth) |
| `docs/ENGINEERING_STANDARDS.md` | the thin standards entry point |
| `docs/PLAYBOOK.md` | the plain-English guide for the human driving the harness |
| `scripts/check_architecture_tree.py` | the deterministic architecture-tree gate |

Rules:
- **Per file: if the target path already exists, skip it and report "skipped (present)."**
  Detect an already-copied managed file by the **`claugentic-dev-harness@` marker** on its
  first line (convention 1) — a present-but-unstamped same-named file is a **user file**;
  do **not** overwrite it, skip and report it so the user can reconcile.
- **Stamp on copy**, not in the source. The source modules are pristine (editable
  upstream) and carry **no** stamp; the `init` skill adds the stamp as the copied file's
  first line — markdown files get the `<!-- … -->` form, the Python script gets the `# …`
  form (as its first line, after which the existing `#!/usr/bin/env python3` shebang and
  body follow — keep the file runnable).
- **Security / exclude-set:** copy **only** the managed set above. **Never** copy the
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

**(a) Set `INCLUDE_GLOBS` *and* `STALE_PATTERN` in the *copied* `check_architecture_tree.py`.**
These are the **only** per-repo knobs in the script, and the script itself requires the
two be **kept in sync** (the staleness check is dead if `STALE_PATTERN` doesn't recognize
the same path shapes `INCLUDE_GLOBS` matches). Set **both**:
- **Reuse the layout detection from `/claugentic-dev-harness:audit` Phase 1 (Understand)** — its
  ecosystem/manifest detection identifies the source layout (e.g. `src/**/*.ts`,
  `src/**/*.py`, `cmd/**/*.go`). **Do not author a second detector** (DRY). Map the
  detected layout to the git pathspec globs (`:(glob)src/**/*.ts`, …) for `INCLUDE_GLOBS`,
  and a matching regex for `STALE_PATTERN` (the same path shapes — e.g.
  `r"(src/[\w./-]+\.ts)"`).
- **Unmappable ecosystem?** Set a **conservative broad source glob** (e.g. the dominant
  source extensions under the main source dir) + a matching `STALE_PATTERN`, and **report**
  "globs set conservatively for an unrecognized layout; refine `INCLUDE_GLOBS` /
  `STALE_PATTERN` in `scripts/check_architecture_tree.py` if needed." Never guess a
  layout you can't see — broaden + flag instead.
- Edit **only** the copied script (step 3 placed it). You only set the two constants.

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
  re-run a provable no-op on this file.

### 6. Write the CLAUDE.md harness section (create / append-at-EOF / skip)

Three cases — **never touch anything above an existing fence:**
- **`CLAUDE.md` absent →** create it with the managed pointer block (in the fence) + the
  Current-scope block (outside the fence) below it.
- **Present, *no* `<!-- harness:managed:start -->` fence →** **append** the fenced block at
  **end-of-file**, touching **nothing above** (the user's existing CLAUDE.md is preserved
  verbatim). Seed the Current-scope block after the fence.
- **Present *with* the fence →** **skip** (the re-run path) — the managed block is already
  there; leave it. *(Refreshing the managed block's content to a newer version is
  `/claugentic-dev-harness:update`'s job, not init's — init is copy/seed-if-absent.)*

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
  refers to (it deliberately does **not** live in the managed `ENGINEERING_STANDARDS.md`,
  which `/claugentic-dev-harness:update` overwrites). Seed it from step 1's detected ecosystem (e.g. for
  a JS web app: `maintainability-structure`, `testing`, `security`, `api-and-contracts`,
  `product-ux`).
- The **detected existing tooling** block (from step 8) — the project's own gates.

### 7. Create `docs/ROADMAP.md` + `docs/DECISIONS.md` if absent

- **`docs/ROADMAP.md` absent →** create a seed (a one-line intro + an empty `## Later`
  human-owned section; `/claugentic-dev-harness:audit` later adds its `harness-audit:overview` /
  `harness-audit:backlog` fences). Present → skip.
- **`docs/DECISIONS.md` absent →** create a seed (the "append newest at top; consult
  before re-litigating" header). Present → skip.

### 8. Detect + record existing tooling (never reconfigure)

- **Scan** for the adopter's own gates: lint/format (`eslint`, `.eslintrc*`, `prettier`),
  type-check (`tsconfig.json`), test runner (`jest`/`vitest`/`pytest`/`go test` config),
  and CI (`.github/workflows`, `.gitlab-ci.yml`). **Reuse `/claugentic-dev-harness:audit` Phase 1's
  tooling detection** (DRY) — it already identifies these by config.
- **Record** what you find in the CLAUDE.md Current-scope-adjacent **detected-tooling
  block** (step 6, outside the managed fence) as **the project's gates** — the workflow
  uses *these*, not new ones imposed on top.
- **Detect + record only — never install, never reconfigure** the adopter's tooling. The
  harness *composes* with what's there.

### 9. Report

Emit a clear summary, grouped:
- **Created** — files written from scratch (e.g. `ARCHITECTURE_TREE.md`, `ROADMAP.md`).
- **Copied + stamped** — the managed set that was absent (or "all skipped — already
  copied").
- **Skipped (already present)** — everything that existed (user files left untouched).
- **Merged** — the settings.json hook entries appended (or "already present").
- **Detected** — the ecosystem, the interpreter, and the existing tooling recorded.

**On a fully-initialized repo, the whole run is a safe no-op** that reports "already
initialized — nothing to do." That re-run safety is the hard gate (below).

---

## Idempotency — the hard safety gate

Running the `init` skill twice on the same repo is **safe and a provable no-op**:
- Every **copy** is copy-if-absent (detected by the `claugentic-dev-harness@` stamp).
- Every **generate/create** (tree, ROADMAP, DECISIONS) is create-if-absent.
- The **settings.json** merge is keyed on a `command` containing `check_architecture_tree.py`
  (present → skip; never a duplicate append).
- The **CLAUDE.md** merge is skip-if-fence-present, and the managed fence carries **no
  volatile content**, so even a re-write would be byte-identical.

**Acceptance of a 2nd run:** `git status` in the target shows **zero changes** and the
report says everything was skipped / "already initialized." If a re-run dirties the repo,
an idempotency guard is missing — that is a bug, not expected behavior.

## What this skill does NOT do (honest scope)

- It does **not** install or reconfigure your linters/test runner — it **detects and
  records** them (step 8) so the workflow composes with them.
- It does **not** refresh an already-copied managed file to a newer version — that is
  **`/claugentic-dev-harness:update`**'s job (it parses the `claugentic-dev-harness@<semver>` stamp, compares
  versions, overwrites managed files, and re-merges hooks). The `init` skill is
  copy/seed-**if-absent** only.
- It does **not** audit your code or write a backlog — that is **`/claugentic-dev-harness:audit`**.
