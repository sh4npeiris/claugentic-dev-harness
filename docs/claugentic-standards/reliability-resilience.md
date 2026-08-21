---
module: reliability-resilience
title: Reliability & Resilience
status: draft
iso_25010: [reliability]
load_scope:
  keywords: [error, exception, retry, timeout, circuit-breaker, idempotent, concurrency, async, thread, race, deadlock, backpressure, upgrade, migration, reconcile, installer]
  globs: ["src/**"]
---

# Reliability & Resilience — guard against failure, partial state, and contention

> **Loads when:** the change touches error handling, I/O with external systems, concurrent or async code, retries, timeouts, or shared mutable state.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **The forbidden failure class across this module: a mechanism that silently passes on its own breakage.**

---

## Correctness & failure paths

- **Auditor checks —** `[J]` no bare `except`/`catch` discards or swallows the exception · `[J]` partial-state scenarios (write A succeeds, write B fails) leave the system consistent and recoverable · `[J]` error messages identify the cause and suggest a remedy.

## Total guards & the exception set they must cover (a fail-safe boundary turns a narrow guard into total silence)

- **Good looks like —** A guard predicate **rejects everything the operation it guards rejects** (`isdigit()` before `int()`, `is_file()` before `open()`) — or it is only a fast path and the operation is wrapped anyway. An `except` clause is **as wide as what the guarded call can actually raise**, checked against the language's real *taxonomy* rather than the intuitive one (`UnicodeDecodeError` **is** a `ValueError` and is **not** an `OSError`; `subprocess.TimeoutExpired` is neither; deep `json.loads` raises `RecursionError`) — named classes, never a blanket `except Exception`.
- **Auditor checks —** `[D]` for each `try`, enumerate what the body can raise and diff it against the `except` tuple — the mismatch *is* the finding · `[D]` grep predicate-then-convert pairs (`isdigit`/`int`, `isnumeric`, `hasattr`, match-then-parse): the predicate's accepted domain must be a **subset** of the operation's · `[J]` behind an **outer fail-safe** (a hook, a plugin entry point, middleware that must never break its caller) every inner reader degrades to "this one input is absent" — the boundary turns any escape into **silent total loss of output**, so drive one hostile input end-to-end through the entry point and check what the *user* sees; a unit test passes green while the process emits nothing · `[J]` the docstring's promise matches the `except` tuple, with no "ANY failure → None" over-claim · `[J]` when one reader is fixed, its **siblings in the same file** are fixed in the same edit.
- **Incident —** 0041 S3 (2026-08-13), five sites in one file: `_version_lt` guarded `int()` with `.isdigit()`, `True` for `'²'`, so a typo'd version stamp (`@1.²`) raised through the outer fail-safe and the SessionStart hook printed **nothing at all** — not the nudge, not the pre-existing resume line, no error. `.isdecimal()` alone would not have fixed it (a >4300-digit segment is legal decimal and still raises under CPython's int-conversion limit): the **`try` is the load-bearing half**. Four `read_text` readers in the same file caught `OSError` alone, so one non-UTF-8 byte in `CLAUDE.md` blanked the banner the same way. Three reviewers found it independently — only the one that ran it end-to-end saw that the *entire* output vanished.

## Opt-in by absence — a "no config, no-op" mechanism is armed only by its config's PRESENCE

- **Good looks like —** A mechanism opt-in by the **presence of a file** treats *absent* as "not opted in" **only where that file's presence is guaranteed** — tracked in version control, asserted by a test that queries the **VCS**, never the ignore rules' wording. The two defaults are reviewed as a **composition**: a deny-by-default ignored directory with per-file un-ignore, plus an absent-is-a-no-op reader, compose into a mechanism **green on the author's machine and disarmed everywhere else** — neither site wrong alone, which is why no single-file review finds it.
- **Auditor checks —** `[D]` for every path a tool reads as its *own* configuration, run the VCS's queries (`git check-ignore -v <path>`, `git ls-files --error-unmatch <path>`) — genuinely tracked, or only present locally? · `[D]` where the repo ignores a directory and re-includes files one by one, every file **added to it in this diff** has its own un-ignore line · `[J]` what the mechanism does when its config is missing — fail loud, or pass quietly; if quietly, name what guarantees presence · `[J]` the absence would be *visible*: a no-op that prints one line is recoverable, one that prints nothing is not · `[D]` every path a generated config names exists at the end of the run **in each mode the installer supports**, and the consumer run against that result degrades rather than hard-failing — an installer names only what **that run created**, per mode (a mode writing `X.local` and leaving `X` untouched must not seed a key for `X`), and drops any non-glob key whose target is absent · `[J]` a grace flag (`reportOnly`, warn-only) covers the *value* verdict, not the *existence* one.
- **Incident —** 0041 S4 (2026-08-13): the doc-budget caps moved into a per-repo config whose designed posture for an absent config is a quiet exit 0, while the ignore file excluded all of `.claude/` and re-included shared files individually — so the new config was invisible to git. Correct in isolation; composed, they would have shipped a gate green locally and **measuring nothing in CI or any fresh clone**. Caught by the implementer, not a reviewer; fixed with one un-ignore line **plus** a test asserting tracking *through the VCS*. *(S7, 2026-08-16: the seeder capped `CLAUDE.md` unconditionally, but its **solo** mode writes `CLAUDE.local.md` — measured end-to-end, the fresh solo adopter's **first** `git commit` was blocked by the gate the seeder had just armed, and `reportOnly` graces the size verdict only. The spec's premise was the defect.)*

## Silent disarm — an installed mechanism that never runs

- **Good looks like —** For any mechanism whose value depends on being **invoked** (a git hook, a scheduled job, a CI step, a plugin registration, middleware), the installing change names and guards every way it can be present-but-inert. The recurring shapes, each of which reads exactly like success: the **launcher** resolves a name that exists but does not work (a shim/stub on PATH, a wrong-version runtime) · the **exec bit** is missing (git skips a non-executable hook silently) · the **registration** is owned and repointed by another tool sharing the setting (a JS hook manager taking `core.hooksPath`) · the block sits **after an unconditional early exit** · the output is **captured and discarded on the success path** · the installed file is **untracked** · the **commit path bypasses the hook** — a conflict-free `git merge` fires `pre-merge-commit`, not `pre-commit`, and a server-side merge fires nothing, so the merge result is the one artifact no local gate sees (measured, git 2.55).
- **Auditor checks —** `[D]` run the launcher the way the machine will — **probe** the interpreter/binary rather than testing for presence, and confirm a broken first candidate cannot shadow a working sibling · `[D]` check the mode bits of every file this change creates that something else executes · `[D]` read the **live** value of any registration another tool may own; never assume the default · `[J]` trace the output path end-to-end: on the **success** path, does anything the mechanism prints reach a human? · `[J]` ask the disarm question per shape — *if this quietly stopped running tomorrow, what would tell anyone?* "Nothing" is the finding.
- **Incident —** 0041 S5 (2026-08-14): one slice, five shapes, four reproduced by running rather than reading. The commit-hook wrapper picked the first interpreter **name** on PATH — a Windows-Store `python3` stub exits non-zero and commonly sits beside a working `python` — announced "no working python", passed, and left the gate permanently disarmed with a false message; a hook without its exec bit is run directly by husky v8 and **skipped silently**; the repo's hook path was already owned by husky; the wrapper discarded the gate's stdout on exit 0, so a report-only warning printed **nothing** (fixed by moving advisories to stderr); and a **tracked** hook hard-depending on an **untracked** wrapper would have blocked **every teammate's** commit.

## Upgrade & reconciliation paths are keyed on RELEASED shapes — and the printed remedy is executed against the artifact the reader holds

- **Good looks like —** Code or instructions that **reconcile an artifact the reader already has** (a hook, a wrapper, a config, a schema, a migration) enumerate branches over the shapes actually **published** — every supported release, never the author's `main` — and every branch is *reachable* by a real population. The **current** post-upgrade shape is enumerated too, so a settled re-run reports "already done" instead of "you edited this". A divergence the tool will not rewrite is reported **without asserting authorship**.
- **Auditor checks —** `[D]` enumerate the released shapes from the VCS (`git show <tag>:<path>` per supported tag) and diff each against the branch's stated comparable — which branch does each real version land in, and is any branch **unreachable**? · `[D]` execute any **copy-pasteable remedy** against each released artifact in a scratch copy and compare **exit status / effect** before and after: it may never weaken what the reader already had, and is refused by name where it is not measured safe · `[J]` the current shape is its own branch, so a re-run is a reported no-op rather than a second application · `[J]` no message claims the user *edited* a divergence the tool merely fails to recognize · `[D]` run the tool twice and diff the artifact (cross-ref *Idempotency & safe retry* below).
- **Incident —** 0041 S7 (2026-08-16): an installer learned to **refresh** any pre-commit wrapper "whose run logic is exactly the prior shipped shape", but **no release had ever shipped that shape** (three published versions carry a 7-line wrapper with no `run_gate`; `grep -c run_gate` = 0 at all three tags — the compared shape existed only on `main`). **100 % of the named population** fell through to the never-clobber branch, whose printed one-line fix — run through a real `sh` against the actual released wrapper — had its exit status read by the following `[ $? -eq 0 ] && exit 0`, turning a blocked commit (exit 1) into a **pass** with the breach output discarded: **the remedy disarmed the gate the adopter already had.** A third state (a wrapper equal to the *current* template) was unenumerated, so a settled re-run accused the user of editing the file. One root cause behind all four: the reader's baseline was assumed to be the author's checkout. *(The location axis of the same bar: `docs-traceability.md` → *Reach, not residence*.)*

## Idempotency & safe retry

- **Auditor checks —** `[D]` every non-GET external call in the diff enumerated (grep) · `[J]` each carries an idempotency key, dedup guard, or insert-or-ignore/upsert semantics · `[J]` client retry logic never retries a non-idempotent path unconditionally.

## Timeouts & retry with backoff

- **Auditor checks —** `[D]` a timeout parameter set on every HTTP client, DB connection and socket call in the diff (grep `timeout`) · `[J]` retry loops carry a delay with a cap and a max-attempts guard.

## Circuit breakers & graceful degradation

- **Auditor checks —** `[J]` external dependencies in the diff identified · `[J]` each non-critical path has a circuit-breaker library or manual tripped-state guard · `[J]` the degraded-mode response is intentional and documented.

## Thread safety & concurrency hazards

- **Auditor checks —** `[J]` shared mutable state in the diff identified (class-level variables, singletons, module globals) · `[J]` access serialized, or the object documented thread-local · `[J]` async code free of unguarded concurrent writes to shared collections · `[J]` channels/queues bounded or carrying explicit backpressure.

## Resource lifecycle & cleanup

- **Auditor checks —** `[D]` grep the diff for `open(`, connection acquire, thread/process spawn · `[J]` each wrapped in a context manager or explicit `finally` · `[J]` no in-memory collection grows without a cap or eviction policy.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
