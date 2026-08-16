---
module: reliability-resilience
title: Reliability & Resilience
version: 0.1.0
status: draft
iso_25010: [reliability]
load_scope:
  keywords: [error, exception, retry, timeout, circuit-breaker, idempotent, concurrency, async, thread, race, deadlock, backpressure]
  globs: ["src/**"]
last_reviewed: 2026-06-04
---

# Reliability & Resilience — guard against failure, partial state, and contention

> **Loads when:** the change touches error handling, I/O with external systems, concurrent or async code, retries, timeouts, or shared mutable state.
> **ISO/IEC 25010:** reliability · **Status:** draft · **v0.1.0**

Each entry below is one **auditable dimension**. Per change, the reviewer applies the
*relevant* ones **fully** (select-don't-skip), right-sized to the change — never
gold-plating an irrelevant one, never skipping a relevant one.

---

## Correctness & failure paths

- **Good looks like —** Every edge and error path is explicitly handled; exceptions surface with actionable messages; no silent swallowing of errors; all operations that must succeed atomically are guarded so no partial state can persist.
- **Auditor checks —** Scan call sites for bare `except`/`catch` blocks that discard the exception or swallow it silently `[J]`; check that partial-state scenarios (e.g. write A succeeds, write B fails) leave the system in a consistent, recoverable state `[J]`; verify error messages identify the cause and suggest a remedy `[J]`.
- **Confidence —** `judgment` — requires a reviewer to trace failure paths through the logic; no gate can prove completeness.
- **Tradeoff (plain English) —** Explicit error handling makes failures visible and debuggable. The cost is more code and more test cases. Skipping it means silent data corruption or misleading success responses that are far harder to diagnose in production.
- **Sources —** "Fail loudly, fail fast" — Release It! (Michael Nygard, 2nd ed., §4); ENGINEERING_STANDARDS.md § Correctness & resilience.

---

## Total guards & the exception set they must cover (a fail-safe boundary turns a narrow guard into total silence)

- **Good looks like —** A guard predicate **rejects everything the operation it guards rejects** (`isdigit()` before `int()`, `startswith` before a parse, `is_file()` before `open()`) — or it is only a fast path and the operation is wrapped anyway. An `except` clause is **as wide as what the guarded call can actually raise**, checked against the language's real exception *taxonomy* rather than the intuitive one (`UnicodeDecodeError` **is** a `ValueError` and is **not** an `OSError`; `subprocess.TimeoutExpired` is neither; deep `json.loads` raises `RecursionError`) — named classes, never a blanket `except Exception`. Where the component sits behind an **outer fail-safe** (a hook, a plugin entry point, middleware that must never break its caller), every inner reader degrades to *"this one input is absent"*, because the outer boundary turns any escape into **silent total loss of output** rather than a local one. A degradation docstring states what is **actually caught**, never "any failure".
- **Auditor checks —** `[D]` For each `try`, enumerate what the body can raise and diff it against the `except` tuple — the mismatch *is* the finding. `[D]` Grep for predicate-then-convert pairs (`isdigit`/`int`, `isnumeric`, `hasattr`, match-then-parse) and ask whether the predicate's accepted domain is a **subset** of the operation's. `[J]` Does this code sit behind a fail-safe boundary? If so, drive one hostile input **end-to-end through the entry point** and check what the *user* sees — a unit test can pass green while the process emits nothing at all. `[J]` Does the docstring's promise match the `except` tuple, or over-claim ("ANY failure → None")? `[J]` When one reader is fixed, are its **siblings in the same file** fixed in the same edit?
- **Confidence —** `mixed`
- **Tradeoff (plain English) —** A guard that is narrower than what it guards is worse than no guard: it reads as handled, tests green, and the failure surfaces as *nothing happening* — the hardest symptom to diagnose because there is no error anywhere. Widening the catch costs one token per site; getting it wrong behind a fail-safe boundary costs the entire output, silently, until a human happens to notice.
- **Incident that motivated this (delete this rule once its cause is gone) —** Plan 0041 Slice 3 (2026-08-13): five sites in one file, three of them shipped and two pre-existing. `_version_lt` guarded `int()` with `.isdigit()`, which is `True` for `'²'` — a character `int()` rejects — so a hand-typo'd version stamp (`@1.²`) raised through the module's outer fail-safe and the SessionStart hook printed **nothing at all**: not the new nudge, not the pre-existing resume line, no error. `.isdecimal()` alone would not have fixed it either: a >4300-digit segment is legal decimal and still raises under CPython's int-conversion limit, so the **`try` is the load-bearing half** and the predicate is only the fast path that states intent. In the same file four `read_text` readers caught `OSError` alone, so a single non-UTF-8 byte in the repo's `CLAUDE.md` blanked the whole banner by the same route. Two of those readers pre-dated the slice and were folded into the fix, because a fixed reader beside two unfixed siblings re-breeds the bug. Three reviewers reached the finding independently — only the one that ran the input **end-to-end through the entry point** saw that the *entire* output vanished rather than one clause.
- **Sources —** Python docs, *Built-in Exceptions* hierarchy (`UnicodeDecodeError` ⊂ `ValueError`, disjoint from `OSError`) and *Integer string conversion length limitation* (CPython ≥ 3.11, `sys.set_int_max_str_digits`); cross-ref *Correctness & failure paths* above and `testing.md` → *Failure-path & edge-case coverage*.

---

## Opt-in by absence — a "no config, no-op" mechanism is armed only by its config's PRESENCE

- **Good looks like —** A mechanism that is **opt-in by the presence of a file** (a caps/policy/lint config, a `.env`) treats *absent* as "not opted in" **only where that file's presence is itself guaranteed** — tracked in version control, and asserted by a test that queries the VCS rather than reading the ignore rules' wording. The two defaults are reviewed as a **composition**: a deny-by-default ignored directory with a per-file un-ignore allow-list, plus an absent-is-a-no-op reader, compose into a mechanism that is **green on the author's machine and disarmed everywhere else** — in CI, in every fresh clone, for every other contributor. Neither site is wrong on its own, which is exactly why no single-file review finds it; the defect lives at the join.
- **Auditor checks —** `[D]` For every path a tool reads as its *own* configuration, run the VCS's ignore-and-track queries against it (`git check-ignore -v <path>`, `git ls-files --error-unmatch <path>`) — is it genuinely tracked, or only present locally? `[D]` If the repo ignores a directory and re-includes files one by one, every file **added to that directory in this diff** needs its own un-ignore line — grep the diff for such adds. `[J]` What does the mechanism do when its config is missing — fail loud, or pass quietly? If quietly, name what guarantees presence. `[J]` Would the absence be *visible*? A no-op that prints one line is recoverable; one that prints nothing is not.
- **Confidence —** `mixed`
- **Tradeoff (plain English) —** "Absent config = not opted in" is the right posture for a tool that must not fail a repo that never asked for it — and it is indistinguishable, from the outside, from the tool being switched off. Pinning presence costs one ignore-file line and one test. Skipping it means that the day the file stops being tracked, every check it drives stops running and every run still reads green.
- **Incident that motivated this (delete this rule once its cause is gone) —** Plan 0041 Slice 4 (2026-08-13): the harness's doc-budget caps moved out of a hardcoded dict into a per-repo config file, and the reader's *designed* posture for an absent config is a quiet exit 0 ("this repo has not opted in"). The repo's ignore file excludes the whole `.claude/` directory and re-includes shared files individually — so the brand-new config was invisible to git by default. Both decisions were correct in isolation; composed, they would have shipped a gate that passed green locally and **measured nothing in CI or in any fresh clone**, with no error anywhere. Caught by the implementer mid-slice, not by any reviewer. The fix is one un-ignore line **plus** a test asserting the file is tracked *through the VCS itself*, never through the ignore rules' wording.
- **Sources —** cross-ref *Correctness & failure paths* above ("a gate that silently passes on its own breakage is the forbidden failure class"); Git docs — `gitignore(5)` negation patterns and `git-check-ignore`; Nygard, *Release It!* on fail-open defaults.

---

## Silent disarm — an installed mechanism that never runs

- **Good looks like —** For any mechanism whose value depends on being **invoked** (a git hook, a scheduled job, a CI step, a plugin/extension registration, middleware), the change that installs it names — and guards — every way it can be present-but-inert. The recurring shapes, each of which reads exactly like success: the **launcher** resolves a name that exists but does not work (a shim/stub on PATH that exits non-zero, a wrong-version runtime) · the **exec bit** is missing (git skips a non-executable hook **silently**) · the **registration** is owned and repointed by another tool that shares the setting (a JS hook manager taking `core.hooksPath`) · the block is appended **after an unconditional early exit** · the mechanism runs but its output is **captured and discarded on the success path**, so an advisory never reaches a human · the installed file is **untracked**, so it exists only on the author's machine. Every one ends in the same state: green everywhere, checking nothing.
- **Auditor checks —** `[D]` Run the launcher the way the machine will — **probe** the interpreter/binary rather than testing for its presence, and confirm a broken first candidate cannot shadow a working sibling. `[D]` Check the mode bits of every file this change creates that something else executes. `[D]` Read the **live** value of any registration another tool may own; never assume the default. `[J]` Trace the output path end-to-end: on the **success** path, does anything the mechanism prints reach a human? `[J]` Then ask the disarm question for each shape: *if this quietly stopped running tomorrow, what would tell anyone?* "Nothing" is the finding.
- **Confidence —** `mixed`
- **Tradeoff (plain English) —** A check that is installed but never runs is worse than no check: the team believes it is covered and stops looking. Each guard above costs one line at install time. Skipping them buys a mechanism whose failure mode is indistinguishable from success — discovered only when the thing it guarded against actually happens.
- **Incident that motivated this (delete this rule once its cause is gone) —** Plan 0041 Slice 5 (2026-08-14): one slice, five shapes, four of them reproduced by running rather than reading. (1) The commit-hook wrapper picked the first interpreter **name** on PATH — a Windows-Store `python3` stub exists, exits non-zero, and commonly sits **beside a working `python`**; in a scratch repo the wrapper announced "no working python", passed, and left the gate permanently disarmed with a factually false message. (2) A hook file created without its exec bit is run directly by husky v8 and **skipped silently** — appended, reported as chained, never run. (3) The repo's hook path was already owned by husky, leaving the gate written-but-inactive. (4) The wrapper captured the gate's stdout and discarded it on exit 0, so a report-only warning printed **nothing** — the grace posture it existed to serve degraded to a no-op; fixed by moving advisories to stderr, which the wrapper always lets through. (5) A hook appended into a **tracked** file that hard-depended on an **untracked** wrapper would have blocked **every teammate's** commit; the wiring step now refuses until the dependency is trackable.
- **Sources —** cross-ref *Opt-in by absence* above (the config-presence sibling of this axis) and *Correctness & failure paths* ("a gate that silently passes on its own breakage is the forbidden failure class"); Git docs — `core.hooksPath`, hook executability; Nygard, *Release It!* on fail-open defaults.

---

## Idempotency & safe retry

- **Good looks like —** Mutating operations that cross a network boundary (API calls, queue publishes, DB writes) are idempotent or protected by an idempotency key, so retrying on transient failure cannot create duplicate side effects.
- **Auditor checks —** Identify every non-GET external call in the diff `[D via grep]`; check each for an idempotency key, deduplication guard, or "insert-or-ignore" / upsert semantics `[J]`; verify the client retry logic does not retry non-idempotent paths unconditionally `[J]`.
- **Confidence —** `judgment` — presence of a key is detectable `[D]`, but correctness of scope and implementation requires review.
- **Tradeoff (plain English) —** Idempotency lets you retry safely after a network hiccup without double-charging or double-creating records. It requires agreeing on a stable key (e.g. request ID) and storing deduplication state, which adds design overhead.
- **Sources —** "Designing for idempotency" — Stripe Engineering Blog (stripe.com/blog/idempotency); AWS Well-Architected Framework — Reliability Pillar, REL 9.

---

## Timeouts & retry with backoff

- **Good looks like —** Every blocking I/O call (HTTP, DB, queue) has an explicit timeout; retries use exponential backoff with jitter; maximum retry count is bounded.
- **Auditor checks —** Search the diff for HTTP client / DB connection instantiation and socket calls; verify a timeout parameter is set on each `[D via grep for `timeout`]`; verify retry loops include `sleep` / delay with a cap and a max-attempts guard `[J]`.
- **Confidence —** `judgment` — timeout presence is grep-able `[D]`, but whether the value is correct and whether backoff is implemented correctly is `[J]`.
- **Tradeoff (plain English) —** Without timeouts a hung downstream service stalls your threads indefinitely; without backoff a thundering-herd of retries amplifies an outage. The cost is slightly more complex call-site code and configuration to tune.
- **Sources —** Google SRE Book, Ch. 22 "Addressing Cascading Failures"; Release It! §5 "Timeouts".

---

## Circuit breakers & graceful degradation

- **Good looks like —** Where a dependency is non-critical or prone to outages, a circuit-breaker (or equivalent) prevents repeated failed calls from cascading; the system degrades gracefully (serves cached data, returns a safe default, or surfaces a clear partial-availability error) rather than propagating failure.
- **Auditor checks —** Identify external dependencies in the diff `[J]`; for each, check whether a circuit-breaker library or manual tripped-state guard exists for non-critical paths `[J]`; verify the degraded-mode response is intentional and documented `[J]`.
- **Confidence —** `judgment` — whether a dependency warrants a circuit-breaker is context-dependent; no gate can decide this.
- **Tradeoff (plain English) —** Circuit breakers add operational complexity (state to monitor, thresholds to tune). Skipping them means a single slow external service can exhaust your connection pool and take down the whole application.
- **Sources —** Release It! §5 "Circuit Breaker"; Martin Fowler, CircuitBreaker pattern (martinfowler.com/bliki/CircuitBreaker.html).

---

## Thread safety & concurrency hazards

- **Good looks like —** Shared mutable state is protected by locks, atomic primitives, or eliminated via immutability/message-passing; no race conditions, deadlocks, or starvation in async/threaded code; backpressure is applied at queue/channel boundaries to prevent unbounded growth.
- **Auditor checks —** Identify shared mutable state in the diff (class-level variables, singletons, module globals) `[J]`; verify access is serialized or the object is documented thread-local `[J]`; check async code for unguarded concurrent writes to shared collections `[J]`; verify channels/queues have bounded capacity or explicit backpressure `[J]`.
- **Confidence —** `judgment` — concurrency bugs require mental model tracing; no static gate reliably catches all races.
- **Tradeoff (plain English) —** Concurrency gives throughput but introduces non-deterministic failure modes that are hard to reproduce and debug. Explicit locking and immutability add overhead but make behavior predictable.
- **Sources —** Java Concurrency in Practice (Goetz et al.), §1; Python `asyncio` docs — "Synchronization Primitives"; ENGINEERING_STANDARDS.md § Resources & concurrency.

---

## Resource lifecycle & cleanup

- **Good looks like —** All acquired resources (file handles, DB connections, network sockets, threads) are released on both the happy path and every failure path; context managers / `try-finally` / RAII patterns are used so cleanup is guaranteed; memory is bounded (no unbounded accumulation in caches or queues).
- **Auditor checks —** Grep diff for `open(`, connection acquire, thread/process spawn calls `[D]`; verify each is wrapped in a context manager or explicit `finally` block `[J]`; check for in-memory collections that grow without a cap or eviction policy `[J]`.
- **Confidence —** `judgment` — structural presence of `with`/`finally` is grep-able `[D]`, but correctness of scope requires review.
- **Tradeoff (plain English) —** Resource leaks are invisible at small scale and catastrophic under load — connections pool exhausts, memory spikes, file descriptor limit hits. The fix (context managers) is cheap; the leak is expensive.
- **Sources —** PEP 343 — The "with" Statement; ENGINEERING_STANDARDS.md § Resources & concurrency.

---

## Authoring rules (the catalog meta-rules — do not delete)

- **Additive floor:** add dimensions as you discover them; **never delete** one. This catalog is meant to become "every standard we can think of."
- **Right-size:** apply only *relevant* dimensions per change (`KISS`/`YAGNI`); never skip a relevant one. Relevance is a per-change judgment — see `README.md`.
- **Novel patterns allowed** when they add clear value — justify (problem → why existing patterns fall short → benefit) and record in `claugentic-DECISIONS.md`. Unconventional ≠ wrong.
- **Every dimension carries a Confidence tag** so the harness can separate what it *proved* (deterministic gates) from what it *asserts* (judgment). Trust the oracle, not the model's word.
