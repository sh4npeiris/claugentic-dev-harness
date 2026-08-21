---
description: Check the harness's OWN health — distinct from /audit, which checks YOUR code against the standards. Runs the existing deterministic gates read-only (architecture-tree · doc-budgets · version-sync · shipped-content, each only where its own script is present, else N-A in an adopter), probes the commit hook's interpreter, scans for landed/cold plans, re-asserts the init post-conditions (hook wiring incl. a healthy husky chain, managed stamps, fence-vs-plugin skew), and flags a likely-skipped Stage-9 harvest — then reports a green/WARN/breach/N-A snapshot with honest [D]-measured vs [J]-judgment tags. Diagnose is strictly read-only; it treats only the bounded-mechanical set (delete a landed/cold plan · re-wire the pre-commit hook, never clobbering a healthy husky chain · apply a user-approved doc-condensation diff · tree hygiene) and only on your explicit approval, never silently. Anything substantive routes to roadmap → plan → build.
---

# /claugentic-dev-harness:doctor

> **Agent ids:** prose-orchestrated; spawns no bundled agent. Work it routes into a plan/build uses the namespaced ids those skills already use (`claugentic-dev-harness:<role>`). Built-ins (`general-purpose`, `Explore`) stay bare.

The **harness's own-hygiene finder.** `/claugentic-dev-harness:audit` targets *your code* against the
`docs/claugentic-standards/` catalog; doctor targets the **harness's own** gates, managed-file stamps,
pre-commit hook, plan lifecycle, and whether the Stage-9 learning loop fired. Three movements —
**Diagnose** (strictly read-only) → **Report** (a transient snapshot) → **SELECT → treat-on-approval /
route-to-roadmap** — on the shared **FIND → SELECT → PLAN → OFFER-BUILD → BUILD** pipeline, whose single
source is `docs/claugentic-WORKFLOW.md` → **The finder pipeline** (read SELECT / OFFER-BUILD there).
Doctor **runs the EXISTING gate scripts** and classifies their output: **no new gate, hook,
always-loaded doc, or fence.** The report regenerates each run, so there is **no doctor backlog and no
doctor reject-memory**.

**The honesty register (the #1 rule).** Only a *measured fact* is mechanical: a gate's exit code and a
raw byte figure are `[D]`. Everything else — "cold" plan, "harvest likely skipped", "condense soon", and
**every treat decision** — is `[J]` model-upheld judgment. Claim only what the scripts returned, in
harness verb discipline: *"the gate returned exit 1 (breach)"*, never *"doctor verified the tree is
broken."* Doctor **treats on approval, never silently.**

## Diagnose — strictly READ-ONLY  *(acceptance gate: NO mutation before SELECT/approval)*

Reads and runs checks only. Deleting a plan, re-wiring a hook, editing a ledger and touching the tree
are all **Treat** actions, gated on SELECT + explicit approval below.

### 1. The deterministic gates  *(exit code → status; `[D]`)*

**Run each gate iff ITS OWN script is present in THIS repo — per-script, never per-class.** Payload
membership and repo-local presence are two facts and you run on the second; per-script presence is the
only adopter signal there is. An **absent script is N-A** — a presence fact, never a breach, never an
error, never a pass.

**NEVER substitute the plugin's own copy.** Every gate anchors to its OWN checkout (`_repo_root()` reads
`__file__`) and measures *that* tree — from an installed plugin a "nothing measured" no-op, from a dev
checkout a green about the harness. Both are verdicts about the wrong repo, worse than an honest N-A.

**Capture BOTH streams:** the verdict rides **stdout**, `WARN:` lines ride **stderr** (the wrapper's
stream contract). A stdout-only capture reports a WARN run as a silent green.

- **`python scripts/claugentic-check_architecture_tree.py`** — **0 = green** · **1 = breach**
  (missing/stale entry, or zero-coverage glob drift). Shipped **and** `init`-delivered; one of the two
  hook-enforced gates (doc-budgets is the other) where a pre-commit wrapper is wired — here doctor just
  runs it ad-hoc. Absent ⇒ N-A.
- **`python scripts/check_versions_synced.py`** — *harness-self; stripped from the release, so N-A in
  an adopter.* Present: **0 = green** · **1 = breach** (`plugin.json` ↔ `marketplace.json` version
  drift, or a malformed manifest).
- **`python scripts/claugentic-check_doc_budgets.py`** — shipped **and** `init`-delivered; where present
  it measures **that** repo's ledgers against **that** repo's caps (not harness-self). **0 + no `WARN:`
  = green** · **0 + a `WARN:` line = WARN** (a ledger ≥90% of budget — condense before it hard-breaks) ·
  **1 = breach** (over budget, or a broken caps config). **Every cap comes from
  `.claude/claugentic-doc-budgets.json`; the script holds none of its own** — no config ⇒ exit 0 and
  *"doc budgets are not configured for this repo; nothing measured"*, reported as
  **green-with-nothing-measured**, never "budgets pass". Absent ⇒ N-A: say re-running
  `/claugentic-dev-harness:init` delivers it.
- **`python scripts/check_shipped_content.py`** — *harness-self; stripped from the release, N-A in an
  adopter.* Scans the SHIPPED tree's text for release/init-contract breaches. Present: **0 + no `WARN:`
  = green** · **0 + a `WARN:` = WARN** (the heuristic uncaveated-gate-mention pass — never a hard fail) ·
  **1 = breach** (a stranded `claugentic-dev-harness:<token>` namespace literal, or a dangling reference
  to a stripped-uncreated path).

Report the **exact** exit status, never your gloss of it.

### 2. Adopter doc-budget advisory  *(config-driven · `[D]` byte / `[J]` "condense soon" · NOT a gate)*

The read-only, on-demand companion to the doc-budget gate — and the **canonical home of the caps-config
reader-contract** (the gate's module docstring defers here for the schema). Two readers, one cap source;
this one **runs no script, sets no exit code, and blocks nothing**, and in a repo with no gate script it
is the **only** budget signal available.

- **The caps config, stated exactly.** `.claude/claugentic-doc-budgets.json` is the ONE cap source per
  repo. Root is a JSON object; **every key is a repo-relative path or a flat glob — no reserved keys**
  (a `"version"` key is a path named `version`, not metadata). **Three entry forms, nothing else:**
  - **Plain integer** — `"docs/claugentic-DECISIONS.md": 60000` — that file's byte cap.
  - **Object with the grace flag** — `"docs/claugentic-ROADMAP.md": {"max": 14000, "reportOnly": true}`.
    `max` is required; an **unknown key inside the object is a fail-loud error**, never ignored.
  - **Glob by key** — `"docs/claugentic-decisions/*.md": 14000`. **The key's shape IS the declaration**
    (there is no kind field): each match is measured **independently against that same number**. `*` is
    allowed **only in the final path component**; `**` is **refused outright** — `docs/**/*.md` matches
    nothing and would pass green under an OK banner, the exact fail-open the refusal prevents. A glob
    matching **nothing** is skipped silently (a cap is declared for a *shape* of file, never for the
    existence of one); a **subdirectory** under a glob'd directory is a WARN, not an error (the entry is
    flat, it does not recurse). **Duplicate keys are fatal** — JSON last-wins would silently discard the
    tighter cap.
- **A glob is the SOLE cap for its matches** — never add a per-file key beside a glob that covers that
  file; that is the second cap source the one-cap-source invariant forbids. **A SPLIT ledger is exactly
  this case:** a repo on the last rung of `docs/claugentic-WORKFLOW.md` → *The escape-valve ladder* caps
  the routing index by its own path at its own deliberately-tight number and covers **every** part with
  one glob key, so adding a part later needs no config edit.
- **Absent, empty, and broken are THREE verdicts — never collapse them.**
  - **Absent config** → **skipped: N-A, no output, no error, no WARN, no breach** (an un-configured repo
    has not opted in). An absent *key* within a present config = un-capped → skipped too.
  - **Present with zero entries** → a distinct *positive* statement: the config exists and **declares no
    budget entries**; nothing measured. Say that, not "N-A" — it tells the user their config was read.
  - **Broken** (unreadable, non-UTF-8, unparseable JSON, non-object root, duplicate key, non-integer or
    non-positive cap, unknown object key, a key shape that could only ever match nothing) → **report it
    loudly as a finding.** A typo in your own cap list must never read as a free pass: the gate exits 1
    on these **and on any other structural defect** (illustrative, not closed — pathological nesting and
    a non-boolean `reportOnly` are two more), and this read must not be softer.
- **Measuring, and the two thresholds.** For each capped file that exists, measure bytes
  (`len(read_bytes())` — never char count) against its cap:
  - **A breach is STRICTLY over** — `measured > cap`. Exactly **at** cap is a WARN, not a breach.
  - **The WARN band is inclusive at 90%** — `measured >= int(cap * 0.9)` (floored, so a cap not divisible
    by 10 opens the band 1 byte early — fail-safe in direction). Surface a `[J]` "condense soon" carrying
    the `[D]` figure: *"DECISIONS.md at 92% of your configured cap (55200 / 60000 bytes) — condense
    soon."* **The byte count and the comparison are `[D]`; "condense soon" is `[J]`.**
  - Below the band, green. A capped file that **does not exist** is a **finding, never a silent skip** —
    the gate fails loud on it, because a deleted ledger is a contract breach.
- **`reportOnly` is a grace, not a cure — and it graces ONLY the size verdict.** A strict breach of that
  entry downgrades to a tagged warning carrying the **same remediation**; a **missing or unreadable**
  budgeted file still fails loud with the flag set. **A fired grace changes the headline** — state the
  count of report-only breaches instead of "all managed ledgers within budget", and render that entry as
  **OVER budget**, tagged; a run that passes on a grace must never read as a clean pass. **Nothing
  mechanical clears the flag** — condensing the ledger and deleting `reportOnly` is a `[J]` judgement
  owned by `/condense` and this skill, and the grace re-prints every run until a human removes it.
- **Honesty:** this read **NEVER claims to be a gate.** Say *"the caps config puts DECISIONS at 92% —
  condense soon"*, never *"the budget gate WARNs"*. It surfaces as a finder-pipeline finding (SELECT
  below), routed like any other.
- **OFFER `/claugentic-dev-harness:condense`** on a "condense soon" advisory **and** on the gate's
  `WARN:` line: it runs the ordered condensation procedure, proposes a diff, and applies it via the
  **same** user-approved-diff treat below. A WARN is a ramp, never a dead-end. (Model-surfaced; you
  still approve the diff.)

### 3. Plan-scan `.claude/plans/`  *(`[J]` — model-upheld classification)*

- **Landed** — present, all decomposition boxes `[x]`, Status `Done` (or every remaining item has a
  close-out disposition). Still existing ⇒ the **plan-removal / Stage-9 close-out was skipped** (a plan
  is deleted at Land — `docs/claugentic-WORKFLOW.md` → *Plan file lifecycle*). **Flag it.**
- **Cold / stale** — Status not `Done`, git mtime stale, Blockers externally-blocked. Such a plan should
  be **deferred-to-a-new-plan or rejected and closed**, not left pending (the 0024 disposition rule).
  **Flag it.**

"Cold" is **your judgment (`[J]`)**, not a script output — label it so.

### 4. Init post-conditions re-asserted  *(read-only checks)*

The canonical wiring contract is the `claugentic-dev-harness:init` skill + the *deterministic-gates*
shard indexed in `docs/claugentic-DECISIONS.md` — check against it, don't restate it. What is doctor's
own, and stated here, is the **health verdict**:

- **Pre-commit hook wired — THREE healthy shapes.** Green on any of:
  - **shared:** `.githooks/pre-commit` present **and** `core.hooksPath` = `.githooks`;
  - **solo:** `.git/hooks/pre-commit` present with `core.hooksPath` at its default;
  - **husky-chained:** `core.hooksPath` **resolves to husky** (`.husky` or `.husky/_`) **AND**
    `.husky/pre-commit` contains the managed marker `# >>> claugentic-dev-harness tree gate` **AND**
    `.githooks/pre-commit` is on disk. **Healthy wiring, not a hooksPath conflict.**

  **Do NOT inherit `init`'s wider detection rule as a health verdict.** Init also counts a bare
  `.husky/` with a `pre-commit` and `core.hooksPath` **unset** — right for deciding whether to *offer* a
  chain, wrong for calling a setup healthy. That state takes the **husky-not-installed** sub-flag below,
  never a green.

  A non-default `core.hooksPath` matching none of these is **reported, never assumed broken** (init
  never clobbers it). **Sub-flags on a husky chain — flags, not conflicts:**
  - **Marker present but UNREACHABLE** — an **unconditional `exit`** above it, so the appended block
    never runs. Report as **"appended"**, never "chained" or "running". *(`[J]` — "unconditional" is a
    control-flow reading, not a measurement.)*
  - **Missing exec bit on `.husky/pre-commit`** — read the **git index mode** (`git ls-files -s
    .husky/pre-commit` → `100755` / `100644`), **never a filesystem stat** (a Windows checkout reports a
    mode the repo does not carry). Check it **unconditionally on every husky chain**: init records only
    `- Husky chain: <appended | declined …>`, never "created", so a "did init create this?" predicate is
    unevaluable and would skip the common *appended* case. Flag it on **any** husky version — v8 runs the
    file directly and **skips a non-executable hook silently**.
  - **`.githooks/pre-commit` is git-ignored** — the chain depends on a file no teammate ever gets.
    `git check-ignore -v .githooks/pre-commit` names the offending rule; report both.
  - **CRLF bytes in the wired wrapper** *(`[D]` — read the bytes)* — any `\r\n` in the active hook
    file is a flag: a strict POSIX `sh` (dash) rejects a CRLF script outright while Git-Bash tolerates
    it — the writer's machine works, POSIX teammates' commits die on a raw syntax error. Fix: rewrite
    the file with LF endings.
  - **Husky present but not installed in this clone** — a `.husky/` directory (marker or not) while
    `core.hooksPath` is **unset or points elsewhere**: git runs `.git/hooks/`, so husky's hooks *and* any
    chained gate are inert until `npm install` runs husky's `prepare`. The ordinary fresh-clone state,
    and **green-looking while checking nothing.** Report it; the remedy is the repo's own npm machinery,
    which the harness neither wires nor checks.

  **Reading the record — asymmetric, deliberately.** A recorded `- Husky chain: declined` means
  **known-inactive**: informational, not a finding. An **ABSENT record proves NOTHING** — init records
  nothing by design when it refuses over an ignored wrapper, and in solo mode the records live in
  `CLAUDE.local.md`. Never read "no record" as "never offered", and never as "declined".
- **Commit-hook interpreter health** *(`[D]` at doctor-run time — scope note below)* — the wrapper picks
  the interpreter every chained gate runs on, so one it cannot find leaves the gate installed and inert.
  **Replicate the wrapper's probe EXACTLY**: `.githooks/pre-commit` is the authority — read it, don't
  paraphrase it. Candidates **in order, `python3` then `python` then `py`**, each **EXECUTED** with
  `-c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)'`, first exit 0 wins. **Never
  `command -v` / `where` / a bare PATH lookup** — resolution-without-execution is precisely the
  Windows-Store-stub false negative (a `python3` shim that resolves, exits non-zero, and sits *beside* a
  working `python`) this probe exists to defeat.
  - **Probe through `sh` where you have it** (`sh -c '…'`) — the hook's PATH view is not doctor's.
    **"Doctor runs Python, therefore the hook has Python" is a FALSE inference.** With no `sh`, state the
    fallback's limits: it proves *an* interpreter meeting the floor exists **for the shell doctor ran
    in** — not that the hook will find one, and nothing about any teammate's machine. **In that fallback
    treat "command not found" as a FAILED candidate — never read a stale exit code:** PowerShell retains
    the previous `$LASTEXITCODE` (0) after a `CommandNotFoundException`, so an exit-code read calls a
    missing `python3` working. Branch on the absence itself.
  - **No working candidate ⇒ report SKIPPED as a FLAG, never a WARN** (*WARN* is reserved for a gate's
    literal `WARN:` line). Keep the remedy in the hook's own register — **"install Python 3 — the gate
    resumes on the next commit; no re-init needed"** — reusing the wrapper's own skip wording. Never
    point at `/claugentic-dev-harness:init`: re-running init installs no runtime.
  - **Not a treat.** Report and stop — installing a runtime is outside the bounded-mechanical set.
- **Managed-file stamps** present and **parseable** — a parseable semver on line 1 (the never-clobber
  upsert marker).
- **Stamped fence vs the installed plugin** *(read-only — not a gate)* — compare the CLAUDE.md
  `harness:managed` fence's `claugentic-dev-harness@<semver>` stamp against the **installed plugin's
  own** `.claude-plugin/plugin.json` `version` (an adopter has no `.claude-plugin/` of its own). Stamp
  **<** plugin = **skew**. **Doctor REPORTS it; the remedy is YOU re-running
  `/claugentic-dev-harness:init`** (its never-clobber upsert re-stamps the fence) — **not one of
  doctor's treats**: init's repo-wide blast radius fails the treat boundary. `[D]` **only where both
  values are readable and parse as numeric semver**; a missing fence, unreadable manifest, or
  non-numeric version is **N-A — never a guess and never a breach.** (The SessionStart advisor nudges
  the same skew; this is the on-demand read.)
- **(Shared mode only) the plugin self-reference** in `.claude/settings.json` — the harness in
  `extraKnownMarketplaces` + `enabledPlugins`. **Solo mode has none by design** — its absence there is
  **not** a finding.

### 5. The Stage-9 harvest signal  *(REPORT-ONLY · `[J]` · soft advisory)*

Did a recent landed plan's land window touch a **learning surface**? **Weight them — they are not
equal**, and a flat any-surface test is what makes this signal useless:

- **Harvest-shaped → clear the flag:** `docs/claugentic-standards/` (**including a `CANDIDATES.md`
  staging entry**, where an adopter's universal lesson lands) · `.claude/agents/` (*harness-self* — the
  harness's roles are plugin-resident; an adopter's own project agents still count) · `CLAUDE.md` ·
  `docs/claugentic-WORKFLOW.md`.
- **DECISIONS / INVARIANTS alone → the WEAK signal, keep the soft flag.** Filing dated decision lines is
  *also* a **Stage-8 Land** obligation, so under a flat test a land that skipped Stage-9 entirely is
  byte-indistinguishable from one that harvested. Word it as such — *"the land filed decisions but
  touched no standards, role or workflow surface; the harvest may have been folded into Land
  bookkeeping."* *(0041 S10a, 2026-08-17: that land filed four decision lines and harvested separately;
  the flat test read clean either way.)*
- **No learning surface at all → "harvest likely skipped"** (`docs/claugentic-WORKFLOW.md` → *The
  learning loop*). Soft and model-upheld: a *might-have-missed*, not a fact.

> **Doctor only REPORTS this signal — it does not run the harvest.** The active retrospect is the
> `retrospect-harvester` agent's (plan 0026 §C5b). No double-build.

## Report — a transient green/WARN/breach snapshot  *(NOT a persisted fence)*

One row per check, its status from the vocabulary **green · WARN · breach · flag · condense-soon · skew · N-A** (each
check's own section above states which values it can take), and an honest source tag. **Transient —
never written to a fence, never accumulated;** re-running regenerates it from scratch. Assemble the rows
from the checks above — each states its own status range and its `[D]`/`[J]` source.

**`[D]` vs `[J]` is load-bearing, not decoration:** a `[D]` row states the gate's exact exit result; a
`[J]` row must read as judgment, never as a mechanical fact.

## SELECT — pick what to act on  *(the shared finder-pipeline gate)*

Present **every row that is not green or N-A** as the **SELECT** checklist, one editable `- [ ]` line
per finding — a `flag` or `condense-soon` row is what three of the four treats actually fire on, so
enumerating only WARN/breach leaves them unreachable. A row whose remedy is yours, not doctor's, is
still listed and simply has no treat. Mechanics: `docs/claugentic-WORKFLOW.md` → **The finder pipeline**
→ *SELECT*. The **checked subset is what gets acted on**; unchecked findings are a per-run skip.

> **No durable doctor reject-memory (deliberate).** Unlike `audit` / `product`, doctor keeps **no**
> `rejected-findings` fence. A recurring health issue **SHOULD recur** — the report is transient and
> there is no fence to bloat, so dismissal-memory is **YAGNI** here. A green tree next run is the only
> dismissal that matters.

## Treat — on approval, NEVER silent  *(the bounded-mechanical set)*

A checked finding in the bounded-mechanical set is **applied directly — no plan needed** — but **only on
your explicit approval, and doctor reports exactly what it did.** The set is precisely **bounded ∧
reversible (git history recovers it) ∧ no-architectural-decision** (the treat-boundary in
`docs/claugentic-DECISIONS.md`; point at it, don't re-litigate it):

- **Delete a landed / cold plan.**
- **Re-wire the pre-commit hook** — re-establish `.githooks/pre-commit` + `core.hooksPath` (shared) or
  `.git/hooks/pre-commit` (solo). **Chain-aware: it REFUSES to re-point ANY non-default `core.hooksPath`
  it did not itself establish** — not merely a *recognized-healthy* chain, whose narrower rule has a
  hole: a repo that **declined** the chain has `core.hooksPath=.husky` and no marker, so re-pointing it
  would **silently switch off every hook that repo owns**. On any husky repo, marked or not, the offer is
  to **CHAIN** (init's marker-guarded append), never to re-point; the treat's other actions are the
  sub-flag repairs (mark `.husky/pre-commit` executable · un-ignore the wrapper), and `core.hooksPath` is
  left to husky.
- **Apply a user-approved doc-condensation diff** for an over-budget / WARN ledger — the diff is the one
  `/claugentic-dev-harness:condense` proposes; this treat is its **apply path** (reused, not duplicated).
- **Tree hygiene** — add a missing `ARCHITECTURE_TREE.md` entry, drop a stale one, or condense an
  oversized one.

> **The doc-condensation treat is safe ONLY because the diff is user-approved before apply — the
> approval IS the decision gate, NOT because condensation is decision-free.** Condensing a ledger *is* a
> judgment about what to keep. Word it that way to yourself — never imply the edit was decision-free.

Each treat fires **only on explicit approval** (the SELECT tick is *intent*; the apply still confirms
what it will change). After applying, **report what was done** — never apply silently.

## Substantive findings — NOT treated here  *(→ roadmap → plan → OFFER-BUILD)*

A finding needing **an architectural decision or a non-trivial fix** is not treated by doctor. Route it:

- **Add it to the roadmap.** In the **harness's own** repo it is normal **Quality / Feature** work (the
  harness *is* the product). In an **adopter** repo it is tooling-maintenance → the existing **Later**
  parking lot with a `harness` / `maintenance` **tag** (no new section — YAGNI).
- **Commitment triggers the plan** (`docs/claugentic-WORKFLOW.md` → *Commitment, not capture, triggers
  the plan*). A not-yet-committed finding stays a planless one-liner.
- **OFFER-BUILD** — ask via AskUserQuestion *"build these now, or leave them in the roadmap?"*,
  **default = leave** (offered, never forced). Build now → enter the `build` procedure; leave → it
  persists for a later `/claugentic-dev-harness:build`.
