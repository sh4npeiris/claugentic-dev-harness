# 0002 — Read harness files from the plugin (kill copy-on-init + `/update`)

- **Status:** Draft — **Slice 0 (validation) done**; design refined below; next = Slice 1 spec
- **Roadmap item:** `docs/ROADMAP.md` → Next "Plugin-read architecture (supersedes `/...:update`)"
- **References:** `docs/DECISIONS.md` → "Standards/workflow read from the plugin, not copied"; `skills/init/SKILL.md`; `skills/audit/SKILL.md`; `.claude/agents/lens-reviewer.md` · `architect-reviewer.md`; `scripts/check_architecture_tree.py`; `docs/WORKFLOW.md`

## Problem
`init` **copies** the managed set (`docs/standards/`, `WORKFLOW.md`, `PLAYBOOK.md`, `ENGINEERING_STANDARDS.md`, `check_architecture_tree.py`) into every adopter repo, and agents read those local copies. Costs: (1) N duplicated copies of the standards (DRY violation); (2) copies go **stale** when the harness improves — a marketplace update refreshes the *plugin* but cannot touch in-repo copies, and re-running `init` is copy-**if-absent** (skips them) → adopters freeze at their init-time version (e.g. the false-green gate fix never reaches them); (3) it forces a whole `/...:update` skill onto the roadmap.

## Proven this session (the unblock)
- A subagent **CAN `Read` a plugin-bundled file by absolute path** from inside an adopter project — tested at `…/.claude/plugins/cache/sh4npeiris/claugentic-dev-harness/<ver>/docs/standards/security.md` → **READ OK**. Refutes the "subagents can't read bundled files" assumption behind copy-on-init.
- The marketplace install bundles the **whole repo**; the install path is **version-stamped** (`…/<semver>/…`), so `${CLAUDE_PLUGIN_ROOT}` auto-follows marketplace updates.
- `${CLAUDE_PLUGIN_ROOT}` is empty in a plain shell (plugin-context var); expands in skill bodies (init relies on this).

## Goals / Non-goals
**Goals:** agents read standards/workflow/playbook from `${CLAUDE_PLUGIN_ROOT}/docs/…` (single source of truth, marketplace-refreshed); shrink `init` to per-repo essentials; make `init` **refresh-capable**; **delete the `/...:update` plan**.
**Non-goals:** no change to what the audit/workflow *do*; per-repo files (tree · ROADMAP · DECISIONS · the CLAUDE.md managed fence · per-repo gate config) **stay in the repo**; not touching the deterministic-trust-gates track.

## Slice 0 — validation results (done; via claude-code-guide reading the official docs)
- **Q1 — `${CLAUDE_PLUGIN_ROOT}` in a SKILL body: NO** (not in the documented substitution set; skills get vars in *frontmatter*, not body prose). **This contradicts the current `skills/init/SKILL.md` claim that it "expands in skill context" — that claim is wrong and must be corrected (Slice 3).** Consequence: the orchestrator can't get the plugin root by writing `${CLAUDE_PLUGIN_ROOT}` in skill/CLAUDE.md text; it must **discover** it (see Approach).
- **Q2 — `${CLAUDE_PLUGIN_ROOT}` in a PROJECT-level hook (adopter `.claude/settings.json`): YES** (hooks reference → "Available in hook commands"; expands at execution time, version-tracked; plugins-reference shows the exact `"${CLAUDE_PLUGIN_ROOT}"/scripts/…` pattern). **This is the unlock:** the init-written project hook runs the gate script straight from the plugin via `${CLAUDE_PLUGIN_ROOT}/scripts/check_architecture_tree.py` — **the script need not be copied**, and script fixes reach adopters on a marketplace update with no re-init.
- **Q3 — plugin-DEFINED hooks fire GLOBALLY** (every project the plugin is enabled in), no per-project scope → keep the gate hook **project-wired** (init writes it into the adopter's settings.json, as today): correctly scoped *and* gets the var (Q2).
- **Q4 — subagents reading absolute plugin paths: YES** (empirically confirmed this session); whether the *variable* reaches a subagent is undocumented — irrelevant, since the orchestrator passes a resolved absolute path.
- **Version tracking confirmed:** `${CLAUDE_PLUGIN_ROOT}` → `cache/<owner>/<plugin>/<semver>/`, always the installed version; never hardcode.
- **Residual before shipping Slice 1:** one end-to-end confirm in a REAL adopter repo (this dev repo isn't an installed-plugin context, so a hook test here isn't representative).

## Approach (refined by Slice 0)
The **hook** is the bridge: it's the one project-side context that gets `${CLAUDE_PLUGIN_ROOT}` (Q2), since skills/CLAUDE.md text don't (Q1).

- **Gate script → runs from the plugin (no copy).** `init` writes the project hook as `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_architecture_tree.py" --hook --config "${CLAUDE_PROJECT_DIR}/.claude/harness.json"`. The script reads its per-repo `INCLUDE_GLOBS` from that tiny per-repo config (externalized out of the script). Script fixes then propagate via marketplace.
- **Standards/workflow docs → read from the plugin by subagents.** Subagents can read absolute plugin paths (Q4), but the orchestrator must *discover* the (version-stamped) plugin root first (skills don't get the var — Q1). **Discovery:** `init` resolves the plugin root via a quick **Bash glob** of `~/.claude/plugins/cache/<owner>/<plugin>/` and writes it into `.claude/harness.json`, kept fresh by the hook (which has the live `${CLAUDE_PLUGIN_ROOT}`). The audit/verify flows read that marker → pass `…/docs/standards/<module>.md` absolute paths to lens-reviewers.
- **`init` shrinks + becomes refresh-capable.** Stops copying docs/script; writes `.claude/harness.json` (INCLUDE_GLOBS + plugin-root marker), wires the hook(s), generates the tree, seeds ROADMAP/DECISIONS, writes the CLAUDE.md managed fence. Re-running refreshes the version-stamped managed regions in place — **replacing `/update`.**
- **Per-repo files stay in the repo** (tree · ROADMAP · DECISIONS · CLAUDE.md fence · `.claude/harness.json` · hook wiring).

## Affected files (anticipated)
`skills/init/SKILL.md` (point-not-copy; refresh-capable; per-repo config) · `skills/audit/SKILL.md` + `.claude/agents/lens-reviewer.md`/`architect-reviewer.md` (read from `${CLAUDE_PLUGIN_ROOT}`) · `scripts/check_architecture_tree.py` (externalize `INCLUDE_GLOBS` if run from plugin) · `docs/DECISIONS.md` (supersede "Copy standards on init") · `docs/ROADMAP.md` (already drops `/update`) · `CLAUDE.md` · `docs/ARCHITECTURE_TREE.md`.

## Risks & mitigations
- Test 1 fails → fall back to discovering the plugin root or keep copying. · Test 2 fails → script stays a thin copy (acceptable; tiny). · Adopters lose easy local customization of standards → acceptable for the non-engineer audience; power users can still copy selectively. · **Backward-compat:** existing v0.1.2 adopters already have copied files — the new refresh-capable `init` must reconcile (refresh managed regions; optionally a one-time clean re-init), documented.

## Decomposition (slices) — refined after Slice 0
- [x] **Slice 0** — validation (done; results above).
- [ ] **Slice 1 (highest value, lowest risk) — gate script from the plugin.** Externalize `INCLUDE_GLOBS` → `.claude/harness.json`; `init` writes the hook as `${CLAUDE_PLUGIN_ROOT}/scripts/check_architecture_tree.py … --config …`; stop copying the script. **End-to-end confirm in a real adopter repo.** Fixes then propagate via marketplace.
- [ ] **Slice 2 — standards/workflow read from the plugin.** Plugin-root discovery (Bash glob at init + hook-refreshed marker in `.claude/harness.json`); audit/verify + lens-reviewer/architect-reviewer read `${plugin}/docs/standards/<module>.md` absolute paths; `init` stops copying the docs.
- [ ] **Slice 3 — `init` refresh-capable + retire `/update`; docs sweep** (correct the `skills/init/SKILL.md` "expands in skill context" claim; DECISIONS supersede "Copy standards on init"; ARCHITECTURE_TREE; confirm `/update` fully gone).

---
## Review  _(pending — Stage 3)_
## Spec  _(pending)_
