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

   `main` rides along so the tagged commit is reachable from the branch — and the gates job now **checks that mechanically** (`git merge-base --is-ancestor`), so a tag on an unmerged branch refuses instead of publishing. The tag push triggers the release workflow; **watch that run.** Nothing reaches an adopter's `/plugin install` until the `publish` job reaches its branch-push step — which is the second-to-last step, so read *"a red run publishes nothing"* with the one exception below. Don't push to `main` while the run is in flight — the publish job's base-ancestry guard refuses a build whose base excludes a commit on `origin/main`.

4. **Update the marketplace only if needed.** The marketplace `source.ref` currently tracks the `release` **branch** (a mutable ref), so a normal release needs no marketplace edit. Repointing it at the `vX.Y.Z` tag is a deferred open question (a bigger call — see `docs/claugentic-DECISIONS.md` / plan 0034); do NOT repoint here.

## When the workflow goes red

A run that fails anywhere **before the branch push** publishes nothing. There is exactly one exception, and it decides your recovery: the branch push is the **second-to-last** step, so a run that fails *at* `gh release create` has **already served the content** — it is a red run that published.

**Start by reading the failed run's log and answering one question: did the "Publish the release branch" step succeed?**

- **First recovery, and usually the right one: re-run the failed run.** It is safe by construction — the re-run checks out the same commit, the version guard admits the rebuild (the tag points at it), the lease re-snapshots, and the Release step is idempotent (`gh release view || gh release create`). So a registry blip, a flaky network, or a runner hiccup costs you a re-run, **not a version number.** Try this before anything below.
- **If the run died AFTER the branch push:** the content is already live under this version. **Do not bump forward** — that would leave `release` serving content labelled with the older version and a tag with no Release page. Re-run, or create the Release by hand (`gh release create v<version> --notes-file …`).
- **If a gate failed (nothing published) and re-running won't help:** fix the cause on `main` and **bump forward** — release the next patch (`0.5.2` → `0.5.3`). The tag is already pushed, so that version number is spent. **A tag is never reused:** re-tagging a version whose content has changed leaves two builds claiming one version, and any clone that already fetched the old tag keeps it.
- **The last-resort exception: delete the failed tag.** Only when nothing consumed it, and only deliberately — deleting a pushed tag is an outward, irreversible act on a shared remote, so it is **yours to decide**, never an agent's.
- **The advertised-version window.** `marketplace.json` lives on `main` and is bumped at prepare time, so a failed run leaves the catalog **advertising a version the `release` branch doesn't serve** until a successful run lands. Adopters installing in that window get the previous content under the previous ref — the catalog entry is simply ahead of itself. Closing the window = landing the next successful release; there is nothing to clean up by hand.

## Honest scope

**What CI now guarantees.** The tag-triggered workflow mechanically re-runs, at the tagged commit, the full pytest suite on both OSes, the node helper tests, all four gate scripts, the tag ↔ `plugin.json` version match, the **tagged commit is an ancestor of `origin/main`**, and `claude plugin validate --strict` (marketplace manifest at the tagged commit; **plugin** manifest against the BUILT stripped tree, which is what adopters install). Only on green does it build via `build_release.py --apply` and push, and only the `publish` job holds a write-capable token.

**What stays model-upheld — do not read the above as totality.**
- **"the workflow is the only publisher"** is a **contract, not a mechanism.** Nothing in this repo's tooling pushes `release` (tests pin that the printed command contains no branch push), but the branch is **not protected** — verified: `branches/release/protection` → *404 Not protected*, `rulesets` → `[]` — so anyone with push rights can still write it by hand. Applying the branch-protection rule below is what would convert this into a real guarantee (`docs/claugentic-INVARIANTS.md` → *The `release` branch has exactly ONE publisher*);
- **"a red run publishes nothing"** holds for every failure **before** the branch push, which is the second-to-last step — see *When the workflow goes red* for the one window where it does not;
- the **eval-drift/`BASELINE.md`** check (step 2) — nothing fires it, nothing grades it;
- the **`git range-diff` drop-check** — the mechanized one is a subset guard (a missing shipped *file*), not a total drop guarantee (it can't see a dropped *commit* whose file also changed);
- the **`marketplace.json` catalog version**, bumped on `main` at prepare time and therefore *outside* the green gate — see the window above;
- the **built-tree validation** checks the shipped *structure* (`check_shipped_content.py --root` — stranded tokens / dangling refs / non-ASCII engine `*.js` / referential closure), NOT that the release is *correct*;
- the **version-increase guard** fires only vs the latest **tag**: strictly-greater at prepare time, and equal-allowed **iff** that tag points at HEAD (the workflow's own publish-time build);
- the **local red-CI preflight** is **advisory** — warn-only, silently skipped without `gh` or a network. The workflow is the gate; the preflight is a courtesy heads-up;
- **the validator itself is a floating dependency.** `claude plugin validate --strict` runs from `npm install -g @anthropic-ai/claude-code`, resolved fresh on every run (and, in the publish job, installed alongside the credential that writes the branch). That is a **deliberate choice, not an oversight**: a pinned validator goes stale and validates yesterday's manifest rules, which is worse validation than a moving one. The same applies to the `actions/*@vN` pins — mutable first-party majors, an accepted risk, not SHA-pinned. **Watch for on the FIRST real tag push (re-homed from the roadmap, 0041 S10b):** that run is the first evidence that `claude plugin validate --strict` works **unauthenticated** in CI — if it does not, the gates job fails before anything publishes, and the fix is a credential on that step, not a bypass.

The flow as a whole is **"prepare locally, push one tag, CI publishes on green"** — never "fully automated" (you decide when to tag, and what a green eval-drift looks like) and never "fully enforced" (the checks above *reduce* release risk; none makes a release correct).

## Branch protection (GitHub settings only a repo admin can apply)

Not mechanized here, and not something a script can do for you:

- **Require the CI checks on `main`.** In **Settings → Branches → `main`**, require `pytest (ubuntu-latest)`, `pytest (windows-latest)`, `node --test (…)` and `deterministic gates …` as **required status checks**. Until that is set, a red `main` can still be tagged — the release workflow will refuse to publish it, but you'll have spent a version number to find out.
- **Restrict who can push `release`.** The branch is currently unprotected, which is the *only* reason "the workflow is the only publisher" reads as a contract rather than a guarantee (see *Honest scope*). A ruleset restricting pushes to `release` to the GitHub Actions app is what makes that sentence mechanically true.
