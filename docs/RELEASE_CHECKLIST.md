# Release Checklist

Releasing is now **one command up to a single human-gated push** — NOT a fully-automated release. `python scripts/build_release.py --apply --bump <version>` runs every mechanizable step (preconditions → write the version into BOTH manifests → build the stripped `release` tree → validate it) and then **STOPS and PRINTS the one command you run to publish.** The tool never tags and never pushes: the force-push (irreversible) and the eval-drift/`BASELINE.md` check stay **model-upheld** — a script can't judge them. An aborted run leaves **zero side effects** (no tag, no push; only the local `release` branch + the two bumped manifests, both re-runnable).

Releases are also gated by the **Definition of Done** in [`docs/claugentic-WORKFLOW.md`](claugentic-WORKFLOW.md#definition-of-done) — run the deterministic gates (tests · `claugentic-check_architecture_tree.py` · `check_versions_synced.py`) **and** the reviewer sign-offs there; this file does not restate them.

## One-time bootstrap (do ONCE, before the version-increase guard is trustworthy)

The version-increase guard anchors on the latest `vX.Y.Z` **git tag** — but the repo's tag history stops at `v0.2.0` while the shipped version is `0.3.1` (there is no `v0.3.x` tag). Until the anchor equals reality the guard is unsound (it would pass a downgrade to `0.3.0`, since `0.3.0 > v0.2.0`). Retroactively tag the current published release **once**:

```
git tag v0.3.1 <the 0.3.1 release commit> && git push origin v0.3.1
```

From then on every release is tagged at publish (step 3 below), so the anchor stays current automatically.

## The release — four steps

1. **Fetch + anchor on the live tip, then run the one command.** `git fetch origin && git checkout main && git pull --ff-only origin main` (the `--ff-only` refuses if your local `main` diverged — you're not on the live tip), then:

   ```
   python scripts/build_release.py --apply --bump <version>
   ```

   This writes `<version>` into `.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json` from the one value (a targeted `"version"`-field replace — a one-line diff per file, the two can't drift), refuses a stale base / a non-increasing version / a shipped-file dropped from the build base, builds the stripped `release` branch locally, and validates the built tree — all fail-loud, no commit if any stage refuses.

2. **Review its printed validation + drop-check summary, then run the model-upheld checks.** These are the genuinely-human `[J]` decisions the tool cannot make:
   - **Eval — the drift check (model-upheld).** Run the measurement procedure in [`eval/BASELINE.md`](../eval/BASELINE.md) — a standard audit over the seeded-defect fixture — and compare recall / precision-proxy / refute-rate to the latest baseline. A material regression **blocks the release** (defaults, overridable with a stated reason: recall down ≥2 seeds, or precision-proxy / refute-rate moved ≥15 pp). An intentional, understood shift is recorded as a **new dated baseline entry**, not a permanent block. **Nothing fires this mechanically — it is a discipline, not a gate.**
   - **`git range-diff` drop-check (model-upheld defense-in-depth).** The build's mechanized drop-check is a **subset guard, not a total drop guarantee** — it catches a missing shipped *file* on `origin/main`-not-`HEAD`, not a dropped *commit* whose file also legitimately changed. So still eyeball `git range-diff origin/release...release` and investigate any commit shown as dropped (a `<` line with no `>` counterpart) that you didn't intend to drop.

3. **Run the one gated command the tool printed** (this is the single irreversible, human-gated step — approve it deliberately):

   ```
   git tag v<version> && git push --force-with-lease origin release && git push origin v<version>
   ```

   Tag-create + lease-safe branch-push + tag-push are ONE atomic step. The `vX.Y.Z` tag is created **here, at publish** (never in-build) — it is the immutable rollback anchor AND the next release's version-increase compare source. `--force-with-lease` refuses if `origin/release` moved out from under you since fetch (a silent-clobber becomes a loud rejection).

4. **Update the marketplace only if needed.** The marketplace `source.ref` currently tracks the `release` **branch** (a mutable ref), so a normal release needs no marketplace edit. Repointing it at the `vX.Y.Z` tag is a deferred open question (a bigger call — see `docs/claugentic-DECISIONS.md` / plan 0034); do NOT repoint here.

## Honest scope

The mechanized stages **reduce, not eliminate,** release risk, and each has a bounded scope — do not read them as totality:
- the **drop-check** is a subset guard (a missing shipped *file*), not a total drop guarantee (it can't see a dropped *commit* whose file also changed) — the `git range-diff` eyeball stays;
- the **built-tree validation** checks the shipped *structure* (`check_shipped_content.py --root` — stranded tokens / dangling refs / non-ASCII engine `*.js` / referential closure), NOT "the release passes CI / the full suite";
- the **version-increase guard** fires only vs the latest **tag** — a same-version overwrite of an *untagged* in-progress build is intentionally allowed (so a re-run after a declined push works);
- the **force-push** and the **eval-drift/`BASELINE.md`** check stay model-upheld (`[J]`) — the flow STOPS and PRINTS the push command; it does not run it.

The flow as a whole is **"one command up to a single human-gated push,"** never "fully automated" or "fully enforced."
