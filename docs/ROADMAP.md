# Roadmap

The forward backlog for the harness itself. Work runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect), sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## The two standing tracks — growing the libraries (ongoing · just-in-time)

The harness grows as it meets more codebases. Neither track is ever "done" — that's the right shape: additions are made when real use proves a gap, never speculatively.

| Track | How it grows |
|------|--------------|
| **Grow the role library** (`.claude/agents/`) — add specialist agents as real use surfaces gaps the starter set lacks. | The workflow delegates to specialists; when real work keeps hitting a job no existing role owns, that's the signal to add one (and register it in `plugin.json`, the WORKFLOW roster, and the architecture tree). |
| **Grow the standards catalog** (`docs/standards/`) — author new quality modules and capability modules (Redis, queues, object-storage, …) as real projects pull them in. | A real audit or review that needs a bar the catalog doesn't carry is the signal to author it (conforming to `_TEMPLATE.md`, indexed in the catalog README). The catalog modernizes vibe-coded apps, not just cleans code. |

---

## Now

- **Harness v2 — re-platform the choreography (plan `0012`).** The audit pipeline, Verify panel, and build loop become executable Workflow scripts (invoked from the plugin install path); deterministic trust-gates (CI, land-gate, secret-scan, characterization-first) unlock an earned **build-to-green** autonomy ladder; a runtime-verification (QA) workflow drives the real app against acceptance criteria; a product layer (spec rebuild + product-gap audit) answers "is this product what it intended to be." Then: the **AskBase pilot** (spec rebuild with the user → gap audit → build-to-green to release-ready) before rolling across the neeshinc suite. (Decisions: `DECISIONS.md` → Harness v2.)
- **Standards-catalog integrity pass** (from the 2026-06-11 multi-lens review, all verified): bring the four `migrated` modules to the deep-module bar; make dimension-level Confidence labels match per-check tags (security.md has six "deterministic" dimensions containing `[J]` checks); replace the 14 dangling `ENGINEERING_STANDARDS.md §` sources; fix the verifiable citation errors (WCAG 2.4.13 is AAA not AA; AWS REL-9/idempotency; SRE-book ch. 5).
- **README first-screen rewrite + one real artifact** (verified DX findings): short plain sentences for the three commands, hedges stated once in Status, an embedded sample backlog excerpt + init report; document uninstall, update, and add a CHANGELOG.

## Later

- **Reconcile the `settings.json` tree-check hook *command string* on format change.** Today `init` keys hook-presence only on the `check_architecture_tree.py` substring (idempotency key, step 5b), so a managed copy whose hook *command format* drifts between plugin versions (flags, interpreter convention, quoting) is detected as "already present" and never updated. When a hook-command format change ships, `init` should reconcile the managed hook entry — without clobbering a user-customized command — rather than leaving the old form in place. (Deferred from plan 0010 — out of scope for the version-aware init slice.)
- **Make the managed `check_architecture_tree.py` layout comment adopter-neutral.** The script carries a hardcoded comment — `scripts/check_architecture_tree.py:56` "For THIS repo (claugentic-dev-harness) the only code is the check script itself." — which is **wrong once the file is copied into an adopter repo** (the adopter's code is *not* just the check script). Consider rewording that comment to be adopter-neutral (the `INCLUDE_GLOBS` carve-out already protects the per-repo *knob*, but the prose comment is a managed verbatim line that misleads in every adopter). (Surfaced by the real AskBase refresh.)
- **Warn before a REFRESH when the git-recovery net is empty.** A REFRESH overwrites a genuine managed copy and relies on **git history** as the recovery net (the user's prior version is recoverable from a commit). That net is **empty** when the overwritten file was **uncommitted/user-edited** (the working-tree version isn't in history) or the repo has **no commits at all**. Before such a REFRESH, `init` should **warn and suggest committing first** so the prior content is recoverable. (Deferred from plan 0010 Stage-7 verify — out of scope for the version-aware init slice.)
