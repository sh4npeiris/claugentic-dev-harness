# Release Checklist

**CI publishes.** You prepare locally, then push one tag; a tag-triggered workflow re-runs every gate at the tagged commit and — only if they are all green — publishes. `python scripts/build_release.py --apply --bump <version>` runs every mechanizable prepare step (preconditions → write the version into BOTH manifests → build the stripped `release` tree locally → validate it) and then **STOPS**. The script never tags and never pushes, at either of its two call sites.

**Your single act is the tag push.** `.github/workflows/release.yml` does the rest: full suite (both OSes) · `node --test` · the four gate scripts · tag ↔ `plugin.json` match · `claude plugin validate --strict` → then `build_release.py --apply` at the tagged commit, a leased push of the `release` branch, and the GitHub Release.

Releases are also gated by the **Definition of Done** in [`docs/claugentic-WORKFLOW.md`](claugentic-WORKFLOW.md#definition-of-done) — run the deterministic gates **and** the reviewer sign-offs there; this file does not restate them.

## The release — four steps

1. **Fetch + anchor on the live tip, then run the one prepare command.** `git fetch origin && git checkout main && git pull --ff-only origin main` (the `--ff-only` refuses if your local `main` diverged — you're not on the live tip), then:

   ```
   python scripts/build_release.py --apply --bump <version>
   ```

   This writes `<version>` into `.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json` from the one value (a targeted `"version"`-field replace — a one-line diff per file, the two can't drift), refuses a stale base / a non-increasing version / a shipped file dropped from the build base, builds the stripped `release` branch locally, and validates the built tree — all fail-loud, no commit if any stage refuses. If `gh` is installed it also prints an **advisory** warning when `main`'s latest CI run isn't green; it is warn-only and never blocks (step 3's workflow is the gate).

2. **Commit the bump, then run the model-upheld check.** The workflow builds from the **tagged commit**, so the version must be committed *before* you tag — the tool prints the exact `git commit` when the bump is still uncommitted.

   - **Eval — the drift check (model-upheld).** Run the measurement procedure in [`eval/BASELINE.md`](../eval/BASELINE.md) — a standard audit over the seeded-defect fixture — and compare recall / precision-proxy / refute-rate to the latest baseline. A material regression **blocks the release** (defaults, overridable with a stated reason: recall down ≥2 seeds, or precision-proxy / refute-rate moved ≥15 pp). An intentional, understood shift is recorded as a **new dated baseline entry**, not a permanent block. **Nothing fires this mechanically — it is a discipline, not a gate.**
   - **`git range-diff` drop-check (model-upheld defense-in-depth).** The build's mechanized drop-check is a **subset guard, not a total drop guarantee** — it catches a missing shipped *file* on `origin/main`-not-`HEAD`, not a dropped *commit* whose file also legitimately changed. So still eyeball `git range-diff origin/release...release` and investigate any commit shown as dropped (a `<` line with no `>` counterpart) that you didn't intend to drop.
   - **CHANGELOG.** The workflow builds the GitHub Release notes from the `## <version>` section and **fails loud if it is missing** — so rename the `## Unreleased` heading to `## <version>` (and commit it) before you tag.

3. **Run the one gated command the tool printed** (the single human-gated step — approve it deliberately):

   ```
   git tag v<version> && git push origin main v<version>
   ```

   `main` rides along so the tagged commit is always reachable from the branch. The tag push triggers the release workflow; **watch that run.** Nothing reaches an adopter's `/plugin install` until its `publish` job is green. Don't push to `main` while the run is in flight — the publish job's base-ancestry guard refuses a build whose base excludes a commit on `origin/main`.

4. **Update the marketplace only if needed.** The marketplace `source.ref` currently tracks the `release` **branch** (a mutable ref), so a normal release needs no marketplace edit. Repointing it at the `vX.Y.Z` tag is a deferred open question (a bigger call — see `docs/claugentic-DECISIONS.md` / plan 0034); do NOT repoint here.

## When the workflow goes red

A red run publishes nothing — but the tag is already pushed, so **that version number is spent.**

- **Default recovery: bump forward.** Fix the cause on `main`, then release the next patch (`0.5.2` → `0.5.3`). **A tag is never reused:** re-tagging a version whose content has changed leaves two builds claiming one version, and any clone that already fetched the old tag keeps it.
- **The exception: delete the failed tag.** Only when nothing consumed it, and only deliberately — deleting a pushed tag is an outward, irreversible act on a shared remote, so it is **yours to decide**, never an agent's.
- **The advertised-version window.** `marketplace.json` lives on `main` and is bumped at prepare time, so a failed run leaves the catalog **advertising a version the `release` branch doesn't serve** until a successful run lands. Adopters installing in that window get the previous content under the previous ref — the catalog entry is simply ahead of itself. Closing the window = landing the next successful release; there is nothing to clean up by hand.

## Honest scope

**What CI now guarantees.** The tag-triggered workflow mechanically re-runs, at the tagged commit, the full pytest suite on both OSes, the node helper tests, all four gate scripts, the tag ↔ `plugin.json` version match, and `claude plugin validate --strict` (marketplace manifest at the tagged commit; **plugin** manifest against the BUILT stripped tree, which is what adopters install). Only on green does it build via `build_release.py --apply` and push. It is the **only** publisher — no human command writes the `release` branch (`docs/claugentic-INVARIANTS.md` → *The `release` branch has exactly ONE publisher*).

**What stays model-upheld — do not read the above as totality.**
- the **eval-drift/`BASELINE.md`** check (step 2) — nothing fires it, nothing grades it;
- the **`git range-diff` drop-check** — the mechanized one is a subset guard (a missing shipped *file*), not a total drop guarantee (it can't see a dropped *commit* whose file also changed);
- the **`marketplace.json` catalog version**, bumped on `main` at prepare time and therefore *outside* the green gate — see the window above;
- the **built-tree validation** checks the shipped *structure* (`check_shipped_content.py --root` — stranded tokens / dangling refs / non-ASCII engine `*.js` / referential closure), NOT that the release is *correct*;
- the **version-increase guard** fires only vs the latest **tag**: strictly-greater at prepare time, and equal-allowed **iff** that tag points at HEAD (the workflow's own publish-time build);
- the **local red-CI preflight** is **advisory** — warn-only, silently skipped without `gh` or a network. The workflow is the gate; the preflight is a courtesy heads-up.

The flow as a whole is **"prepare locally, push one tag, CI publishes on green"** — never "fully automated" (you decide when to tag, and what a green eval-drift looks like) and never "fully enforced" (the checks above *reduce* release risk; none makes a release correct).

## Branch protection (a GitHub setting only a repo admin can apply)

Not mechanized here, and not something a script can do for you: in **Settings → Branches → `main`**, require the CI checks (`pytest (ubuntu-latest)`, `pytest (windows-latest)`, `node --test (…)`, `deterministic gates …`) as **required status checks**. Until that is set, a red `main` can still be tagged — the release workflow will refuse to publish it, but you'll have spent a version number to find out.
