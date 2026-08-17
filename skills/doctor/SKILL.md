---
description: Check the harness's OWN health (distinct from /audit, which checks YOUR code vs the standards) — run the existing deterministic gates read-only (architecture-tree and doc-budgets both ship and run wherever present · version-sync + shipped-content are harness-self, run only where their script is present, else N-A in an adopter), probe the commit hook's own interpreter, scan for landed/cold plans, re-assert the init post-conditions (including a husky-chained hook as a healthy wiring), and flag a likely-skipped Stage-9 harvest, then report a green/WARN/breach snapshot. It treats only the bounded-mechanical set (delete a landed/cold plan · re-wire the pre-commit hook, never clobbering a healthy husky chain · apply a user-approved doc-condensation diff · tree hygiene) — and ONLY on your explicit approval, never silently. Anything substantive is routed to the roadmap → plan → offered to build. The diagnose is strictly read-only; nothing is mutated before you select and approve.
---

# /claugentic-dev-harness:doctor

> **Agent ids:** this skill is prose-orchestrated and spawns no bundled agent itself; if it routes a substantive finding into a plan/build it uses the namespaced ids those skills already use (`claugentic-dev-harness:<role>`). Built-ins (`general-purpose`, `Explore`) stay bare.

The **harness's own-hygiene finder.** Where `/claugentic-dev-harness:audit` targets *your
code* against the `docs/claugentic-standards/` catalog, **doctor checks the harness's own
wiring, ledgers, and plans** — the gates, the managed-file stamps, the pre-commit hook, the
plan lifecycle, and whether the Stage-9 learning loop fired. It rides the **same finder
pipeline** every other finder does — **`FIND → SELECT → PLAN → OFFER-BUILD → BUILD`** —
so nothing is treated or planned until you've picked it. The contract is the single source:
`docs/claugentic-WORKFLOW.md` → **The finder pipeline** (read SELECT / OFFER-BUILD there;
this skill points at it, it does not restate it).

## How this skill works

Three movements, in order: **Diagnose** (strictly read-only) → **Report** (a transient
green/WARN/breach snapshot) → **SELECT → Treat-on-approval / route-to-roadmap**. The skill
**runs the EXISTING gate scripts** and classifies their output — it adds **no new gate, no
new hook, no new always-loaded doc, and no new fence.** Its report is a **transient
conversational snapshot** (it regenerates each run, it does not accumulate — like the audit
overview), so there is **no doctor backlog and no doctor reject-memory**.

**The honesty register (the #1 rule — say it plainly).** Diagnose is **mechanical only for a
measured fact**: a gate script's exit code is a deterministic fact (`[D]`), and so is a raw
byte measurement (the adopter doc-budget read's *"55200 / 60000 bytes"* is `[D]`). Everything
else doctor reports is **model-upheld judgment (`[J]`)** — whether a plan is "cold," whether a
land "likely skipped its harvest," the doc-budget read's *"condense soon"* advice, and **every
treat decision**. The report claims **only what
the scripts actually returned**; doctor **treats on approval, never silent.** Use the harness
verb discipline throughout — *"the gate returned exit 1 (breach)"*, never *"doctor verified the
tree is broken."*

## Diagnose — strictly READ-ONLY  *(acceptance gate: NO mutation before SELECT/approval)*

Diagnose **reads and runs checks only.** It must not delete a plan, re-wire a hook, edit a
ledger, or touch the tree — those are **Treat** actions, gated on SELECT + explicit approval
below. Run each check and record its result for the report:

### 1. The deterministic gates  *(exit code → status; `[D]`)*

Run each via the Bash tool and classify by exit code — **run them, do not re-implement them.**
**The rule — payload membership and repo-local presence are TWO facts, and you run on the
second.** The **tree gate and the doc-budget gate ship in the release payload**; the
**harness-self gates** (version-sync, shipped-content) reason about the *plugin* rather than the
reading repo, so the release strips them. **Shipping is not delivery:** `init` is what copies a
gate into the adopter's repo, and it delivers **both** of these — but a repo `init` has never
run in still has neither, and that is a presence fact, not a failure. So:
**run each gate iff ITS OWN script is present in THIS repo** — per-script, never per-class. An
ABSENT script is **N-A**, never a breach and never an error. (Per-script presence is the adopter
signal — there is no separate "am I an adopter" flag.)
**NEVER substitute the plugin's own copy of a gate script.** Every gate anchors to its OWN
checkout (`_repo_root()` reads `__file__`) and then measures *that* tree — **never yours**. Run
the plugin's copy from an adopter's project and the verdict is about the plugin clone: from an
**installed** plugin (whose caps config is stripped) that is a "not configured … nothing
measured" no-op note; from a **dev checkout** of the harness it is a green about the harness's
ledgers. Either shape is a verdict about the wrong repo, and that is worse than an honest N-A:
if the script is not in this repo, mark N-A and stop.
**Capture BOTH streams when you run a gate.** A gate's verdict rides **stdout** and its `WARN:`
lines ride **stderr** (the stream contract the shared pre-commit wrapper depends on) — a
stdout-only capture reports a WARN run as a silent green, which is the one classification error
that matters here.

- **`python scripts/claugentic-check_architecture_tree.py`** — exit **0 = green** · exit **1
  = breach** (a missing/stale entry or a zero-coverage glob-drift). It is one of the two
  hook-enforced gates (the doc-budget check is the other) in a repo whose pre-commit wrapper is
  wired; here doctor just runs it ad-hoc and reports. **Always present, always run.**
- **`python scripts/check_versions_synced.py`** — *(harness-self — N-A in an adopter; its
  script is stripped from the release)*. **If the script is present:** exit **0 = green** · exit
  **1 = breach** (`plugin.json` ↔ `marketplace.json` version drift, or a malformed manifest).
  **If absent:** mark **N-A**, do not run.
- **`python scripts/claugentic-check_doc_budgets.py`** — *(in the release payload AND delivered
  into an adopter repo by `init` — one path everywhere, under the managed prefix. Where the
  script IS present it measures THAT repo's
  own ledgers against THAT repo's own caps — it is not harness-self)*. **If present:** exit
  **0 + no `WARN:` line = green** · exit **0 + a `WARN:` line = WARN** (a ledger ≥ 90% of its
  budget — the cue to condense before it hard-breaks) · exit **1 = breach** (a ledger over budget,
  or a broken caps config). **Every cap it enforces comes from
  `.claude/claugentic-doc-budgets.json` — the script holds none of its own**, so a repo with no
  config gets exit 0 and the plain note *"doc budgets are not configured for this repo; nothing
  measured"*. Report that as **green-with-nothing-measured**, never as "budgets pass". **If
  absent** — a repo `init` has not run in, or one adopted before the delivery step existed:
  mark **N-A**, do not run, say that re-running `/claugentic-dev-harness:init` delivers it,
  and do **not** reach for the plugin's own copy (see *The rule* — its verdict is about the
  plugin clone's tree, never this repo's).
- **`python scripts/check_shipped_content.py`** — *(harness-self — N-A in an adopter; its script is
  stripped from the release)*. Scans the SHIPPED tree's text for release/init-contract content
  breaches. **If the script is present:** exit **0 + no `WARN:` line = green** · exit **0 + a
  `WARN:` line = WARN** (the heuristic uncaveated-gate-mention pass flagged a mention to eyeball —
  never a hard fail) · exit **1 = breach** (a stranded `claugentic-dev-harness:<token>` namespace
  literal or a dangling reference to a stripped-uncreated path — the exact-literal cases). **If
  absent:** mark **N-A**, do not run.

A gate's classification is `[D]` — report the **exact** exit status, never your gloss of it.
**N-A is a presence fact** (the script isn't there), not a pass — report it plainly; never
imply a harness-self gate passed when it didn't run.

### 2. Adopter doc-budget advisory  *(config-driven · `[D]` byte / `[J]` "condense soon" · NOT a gate)*

The **read-only, on-demand companion** to the doc-budget gate above — and the **canonical home
for the caps-config reader-contract**: the gate and this advisory are two readers of ONE cap
source, and this section is where that source's shape and edge semantics are defined (the gate's
module docstring describes the gate's behavior and defers here on the schema). The difference is
register, not data: the gate returns an exit code and can fail a run; this read **runs no script,
sets no exit code, and blocks nothing.** Use it to answer *"how close am I?"* on demand — and in
**any repo that has no repo-local gate script** (one `init` has never run in), it is the **only**
budget signal available.

- **The reader-contract — the caps config, stated exactly.**
  `.claude/claugentic-doc-budgets.json` is the ONE cap source per repo. Its root is a JSON
  object, and **every key is a repo-relative path or a flat glob — there are no reserved keys at
  all** (a `"version"` key is read as a path named `version`, not as metadata). **Three entry
  forms, and nothing else:**
  - **Plain integer** — `"docs/claugentic-DECISIONS.md": 60000` — that file's byte cap.
  - **Object with the grace flag** — `"docs/claugentic-ROADMAP.md": {"max": 14000, "reportOnly":
    true}` — the same cap, breach downgraded to a warning (see the grace bullet). `max` is
    required; an **unknown key inside the object is a fail-loud error**, never ignored.
  - **Glob by key** — a key containing `*`, e.g. `"docs/claugentic-decisions/*.md": 14000`. **The
    key's shape IS the declaration** (there is no kind field): the cap fans out and **each match
    is measured independently against that same number**. `*` is allowed **only in the final path
    component**, and `**` is **refused outright** — the natural-looking `docs/**/*.md` matches
    nothing and would pass green under an OK banner, the exact fail-open the refusal prevents. A
    glob matching **nothing** is skipped silently (a cap is declared for a *shape* of file, never
    for the existence of one); a **subdirectory** under a glob'd directory is a WARN, not an error
    (the entry measures a flat directory and does not recurse). **Duplicate keys are fatal** —
    JSON last-wins would silently discard the tighter cap.
- **A glob is the SOLE cap for its matches.** Never add a per-file key beside a glob that already
  covers that file: two caps for one file is the second cap source the one-cap-source invariant
  forbids. **A SPLIT ledger is exactly this case** — if a repo has climbed the escape-valve
  ladder's last rung (`docs/claugentic-WORKFLOW.md` → *The escape-valve ladder*), cap the routing
  index by its own path at its own (deliberately tight) number, and cover **every** part with one
  glob key, so adding a part later needs no config edit.
- **Absent, empty, and broken are THREE different verdicts — never collapse them.**
  - **Absent config** → this read is **skipped: mark N-A, emit no output, no error, no WARN, no
    breach.** An un-configured repo has not opted in, and producing nothing is the point. (An
    absent *key* within a present config = that file is un-capped → skipped too.)
  - **Present with zero entries** → a distinct, *positive* statement: the config exists and
    **declares no budget entries**; nothing was measured. Say that, not "N-A" — the difference is
    what tells a user whether their config was read at all.
  - **Broken** (unreadable, non-UTF-8, unparseable JSON, a non-object root, a duplicate key, a
    non-integer or non-positive cap, an unknown object key, a key shape that could only ever match
    nothing) → **report it loudly as a finding.** A typo in your own cap list must never read as a
    free pass; the gate exits 1 on these **and on any other structural defect** (the list is
    illustrative, not closed — pathological nesting and a non-boolean `reportOnly` are two more),
    and this read must not be softer.
- **Measuring, and the two thresholds.** For each capped file that exists, measure its byte size
  (`len(read_bytes())` — bytes, never char count) and compare to its cap:
  - **A breach is STRICTLY over** — `measured > cap`. A file sitting exactly **at** its cap is
    **not** a breach; it is a WARN.
  - **The WARN band is inclusive at 90%** — `measured >= int(cap * 0.9)` is in the band (the
    gate floors the threshold to a whole byte, so on a cap not divisible by 10 the band opens
    1 byte early — fail-safe in direction). Surface a
    `[J]` "condense soon" advisory carrying the `[D]` byte figure — e.g. *"DECISIONS.md at 92% of
    your configured cap (55200 / 60000 bytes) — condense soon."* The **byte count and the
    comparison are the `[D]` mechanical part**; **"condense soon" is `[J]` judgment.**
  - Below the band, report green for that file. A capped file that **does not exist** is a
    **finding, never a silent skip** — the gate fails loud on it, because a deleted ledger is a
    contract breach.
- **`reportOnly` is a grace, not a cure — and it graces ONLY the size verdict.** With
  `{"max": N, "reportOnly": true}` a strict breach of that entry is downgraded from a failure to a
  tagged warning carrying the **same remediation** (the "you inherited an over-budget ledger; here
  is the signal, land your work" posture). Nothing else moves: a **missing or unreadable** budgeted
  file still fails loud even with the flag set, and a report-only file *within* its cap produces
  nothing special. **A fired grace changes the headline** — the summary states the count of
  report-only breaches instead of claiming "all managed ledgers within budget", and that entry
  renders as **OVER budget**, tagged; a run that passes on a grace must never read as a clean pass.
  **Nothing mechanical clears the flag:** condensing the ledger and deleting `reportOnly` is a
  `[J]` judgement owned by `/condense` and this skill, and the grace re-prints in full on every run
  until a human removes it.
- **Streams, when you read the GATE's output rather than this config:** the verdict rides
  **stdout**, every `WARN:` line rides **stderr**. Capture both, or a WARN run reads as a green one.
- **Honesty (the line to hold):** this read **NEVER claims to be a gate.** Say *"the caps
  config puts DECISIONS at 92% — condense soon"*, never *"the budget gate WARNs"* — there is
  no gate here, only a config-driven advisory. A "condense soon" advisory surfaces as a
  finder-pipeline finding (SELECT below), routed like any other — the condensation itself is
  the existing user-approved-diff treat (`docs/claugentic-WORKFLOW.md` → the condensation pass).
- **OFFER `/condense` as the next step (the ramp, not a dead-end).** When this read surfaces a
  "condense soon" advisory — and equally when the **doc-budget gate returns a `WARN:` line** (a
  ledger ≥90% of its budget) — **OFFER `/claugentic-dev-harness:condense`** as
  the operator that does the work: it runs the ordered condensation procedure (classify-first →
  absorb-landed → promote-must-holds → merge-siblings → trim-locators), proposes a diff, and
  applies it via the **same** user-approved-diff treat below. A WARN/breach here is a **ramp to
  `/condense`, never a dead-end.** (The OFFER is model-surfaced — `/condense` still proposes a diff
  and you approve it; the advisory does not condense anything itself.)

### 3. Plan-scan `.claude/plans/`  *(`[J]` — model-upheld classification)*

Scan the plan files and classify each:

- **Landed** — the file is present, all decomposition boxes are `[x]`, and its Status is
  `Done` (or every remaining item has a close-out disposition). A landed plan that still exists
  means the **plan-removal / Stage-9 harvest close-out was skipped** (a plan is deleted at Land —
  see `docs/claugentic-WORKFLOW.md` → *Plan file lifecycle*). **Flag it.**
- **Cold / stale** — Status not `Done`, git mtime stale, and any Blockers are externally-blocked.
  A plan that lingers on an external blocker should be **deferred-to-a-new-plan or rejected and
  closed**, not left pending (the 0024 disposition rule). **Flag it.**

Whether a plan is "cold" is **your judgment (`[J]`)**, not a script output — label it so.

### 4. Init post-conditions re-asserted  *(read-only checks)*

Confirm the adoption wiring `init` established is still intact (the canonical contract is
`skills/init/SKILL.md` + `docs/claugentic-DECISIONS.md` → *The deterministic gates*; check, don't restate):

- **Pre-commit hook wired — THREE healthy shapes.** Report green on any of:
  - **shared:** `.githooks/pre-commit` present **and** `git config core.hooksPath` = `.githooks`;
  - **solo:** `.git/hooks/pre-commit` present with `core.hooksPath` left at default;
  - **husky-chained:** `core.hooksPath` **resolves to husky** (`.husky` or `.husky/_`) **AND**
    `.husky/pre-commit` contains the managed marker `# >>> claugentic-dev-harness tree gate`
    **AND** `.githooks/pre-commit` is on disk. **This is a HEALTHY wiring, not a hooksPath
    conflict** — do not report it as one.
    **Do NOT inherit `init`'s wider detection rule as a health verdict.** Init also counts a
    bare `.husky/` containing a `pre-commit` with `core.hooksPath` **unset** — correct for
    deciding whether to *offer* a chain, wrong for calling a setup healthy: with hooksPath
    unset git runs `.git/hooks/` and the marker block never executes. That is the ordinary
    pre-`npm install` state of a fresh clone, and it is **green-looking and checking nothing**.

  A non-default existing `core.hooksPath` matching none of these is **reported, never assumed
  broken** (init never clobbers it). **Sub-flags on a husky chain — flags, not conflicts** (the
  chain is recognized; these say what is off about it):
  - **Marker present but UNREACHABLE** *(`[J]` — whether an `exit` above the marker is truly
    unconditional is a control-flow reading, not a measurement)* — an **unconditional `exit`**
    sits above the marker, so the appended block never runs. Report it as **"appended"**, never
    as "chained" or "running".
  - **Missing exec bit on `.husky/pre-commit`** — read the **git index mode**
    (`git ls-files -s .husky/pre-commit` → `100755` executable, `100644` not), **never a
    filesystem stat**: a Windows checkout reports a mode the repo does not carry. Check it
    **unconditionally, on every husky chain** — do NOT scope it to hooks `init` created: init
    records only `- Husky chain: <appended | declined …>`, never "created", so a
    "did init create this?" predicate is unevaluable and would skip the *appended* case, which
    is the common one. Under husky v8 (`core.hooksPath=.husky`) git runs that file directly and
    **skips a non-executable hook silently**; under v9 `.husky/_` sources it and the bit is
    irrelevant — flag it either way.
  - **`.githooks/pre-commit` is git-ignored** — the chain depends on a file that never reaches a
    teammate. `git check-ignore -v .githooks/pre-commit` names the offending rule; report both.
  - **Husky present but not installed in this clone** — a `.husky/` directory (with or without
    the marker) while `core.hooksPath` is **unset or points elsewhere**. Git is running
    `.git/hooks/`, so husky's hooks *and* any chained gate are inert until someone runs
    `npm install` (husky's `prepare` script). Report the state; the remedy is the repo's own
    npm machinery, which the harness neither wires nor checks.

  **Reading the record — asymmetric, deliberately.** A recorded `- Husky chain: declined` line in
  the detected-tooling block means **known-inactive**: informational, not a finding (the user chose
  it). An **ABSENT record proves NOTHING** — `init` records nothing by design when it refuses over
  an ignored wrapper (so a repo that fixes its ignore rules is re-offered), and in solo mode the
  records live in `CLAUDE.local.md`, not `CLAUDE.md`. Never read "no record" as "never offered",
  and never as "declined".
- **Commit-hook interpreter health** *(`[D]` at doctor-run time — read the scope note below)* —
  the wrapper picks the interpreter every chained gate then runs on, so an interpreter it cannot
  find leaves the gate installed and inert on that machine. **Replicate the wrapper's probe
  EXACTLY** — `.githooks/pre-commit` is the source of truth; read it rather than paraphrasing it.
  Iterate the candidates **in order, `python3` then `python`**, and **EXECUTE each** with
  `-c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)'`, stopping at the first that
  exits 0. (The candidate order and the 3.7 floor restated here are **test-pinned to the hook** —
  `tests/test_precommit_wrapper.py` turns red if either home drifts; when the hook's floor moves,
  this section moves in the same change.) **Never `command -v` / `where` / a bare PATH lookup:** resolution-without-execution is
  precisely the Windows-Store-stub false negative — a `python3` shim that resolves, exits
  non-zero, and commonly sits *beside* a working `python` — that this probe exists to defeat.
  - **Probe through `sh` where you have it** (`sh -c '…'`), because the hook's PATH view is not
    doctor's. **"Doctor runs Python, therefore the hook has Python" is a FALSE inference** —
    doctor's interpreter was chosen by the agent runtime, not by `sh` resolving `PATH` at commit
    time. On a machine with no `sh`, say what the fallback can and cannot prove: it proves *an*
    interpreter meeting the floor exists **for the shell doctor ran in**; it does **not** prove the
    hook will find one, and it says nothing about any other teammate's machine.
    **In that fallback, treat "command not found" as a FAILED candidate — never read a stale
    exit code.** Measured in PowerShell: after a `CommandNotFoundException` the shell **retains
    the previous `$LASTEXITCODE` (0)**, so an exit-code read reports a missing `python3` as
    working. Branch on the exception/absence itself, not on the code left behind by whatever ran
    before. A false green on the one row whose whole purpose is not lying about the interpreter
    is the worst outcome available here.
  - **No working candidate ⇒ report SKIPPED as a FLAG, never a WARN.** *WARN* is reserved for a
    gate's literal `WARN:` line, and nothing here produced one. Keep the remedy in the hook's own
    register: **"install Python 3 — the gate resumes on the next commit; no re-init needed."**
    Never point at `/claugentic-dev-harness:init`; re-running init installs no runtime, and the
    hook's own notice deliberately doesn't say it either (a test pins that wording).
  - **Not a treat.** Doctor reports it and stops — installing a runtime is outside the
    bounded-mechanical set, the same boundary the stamped-fence row draws (that set stays four).
- **Managed-file stamps** present and **parseable** — a managed doc/tree's stamp line carries a
  parseable-semver on line 1 (the never-clobber upsert marker).
- **Stamped fence vs the installed plugin** *(read-only — not a gate)* — compare the CLAUDE.md
  `harness:managed` fence's `claugentic-dev-harness@<semver>` stamp against the **installed
  plugin's own** `.claude-plugin/plugin.json` `version` (the plugin the session is running, not
  the adopter repo — an adopter has no `.claude-plugin/` of its own). Stamp **<** plugin =
  **skew**. **Doctor REPORTS it; the remedy is for YOU to re-run
  `/claugentic-dev-harness:init`** (its never-clobber upsert re-stamps the fence) — **this is
  not one of doctor's applied treats** (see *Treat* — that set is exactly four **in count**,
  though the re-wire treat's BOUNDARY grew in 0041 S6: it may now offer to un-ignore the
  wrapper, an action `init` itself refuses to take. Count unchanged, scope not; and init's
  repo-wide blast radius does not meet the treat boundary). The comparison is `[D]` **only where
  both values are readable and both parse as numeric semver**; a missing fence, an unreadable
  manifest, or a non-numeric version is **N-A — never a guess and never a breach.** (The
  SessionStart advisor surfaces the same skew as a one-line user-facing nudge; this is the
  on-demand read of it.)
- **(Shared mode only) the plugin self-reference** in `.claude/settings.json` — the harness in
  `extraKnownMarketplaces` + `enabledPlugins`. **Solo mode has no self-reference by design** — its
  absence in solo mode is **not** a finding (don't flag the intended divergence).

### 5. The Stage-9 harvest signal  *(REPORT-ONLY · `[J]` · soft advisory)*

Flag a **recent landed plan whose land window touched no learning surface** — no
`docs/claugentic-standards/` (**including a `CANDIDATES.md` staging entry** — in an adopter repo
that is where a universal lesson lands, and it must not read as "skipped"), no `CLAUDE.md`, no
`.claude/agents/` (*harness-self only* — an adopter has no such dir), no
`docs/claugentic-WORKFLOW.md` / `DECISIONS.md` / `INVARIANTS.md` edit — as **"harvest likely
skipped"** (Stage-9 is a manual discipline the orchestrator runs at Land; see
`docs/claugentic-WORKFLOW.md` → *The learning loop*). This is a **soft, model-upheld advisory** —
a *might-have-missed*, not a fact.

> **Doctor only REPORTS this signal — it does not run the harvest.** The active retrospect /
> harvest is owned by the `retrospect-harvester` agent (plan 0026 §C5b). Doctor surfaces the flag;
> that actor does the harvest. No double-build.

## Report — a transient green/WARN/breach snapshot  *(NOT a persisted fence)*

Present the diagnose results as a **conversational table** — one row per check, a status of
**green / WARN / breach** (or **flag** for a plan / init / Stage-9 finding), and an honest source
tag. **It is a transient snapshot — never written to a fence, never accumulated;** re-running
doctor regenerates it from scratch.

| Check | Status | Source |
|-------|--------|--------|
| architecture-tree gate | green / breach | `[D]` exit code |
| version-sync gate | green / breach / **N-A** | `[D]` exit code (N-A if script absent — harness-self) |
| doc-budgets gate | green / WARN / breach / **N-A** | `[D]` exit code (+ any `WARN:` line, which arrives on **stderr**); **N-A whenever the script is not in THIS repo** — `init` delivers the repo-local copy, so N-A means init has not run here, or the repo was adopted before the delivery step existed. Never run the plugin's copy instead |
| shipped-content gate | green / WARN / breach / **N-A** | `[D]` exit code (+ `WARN:` line); N-A if script absent — harness-self |
| adopter doc-budget advisory | green / condense-soon / **N-A** | `[J] advisory (read-only — not a gate)` — `[D]` byte figure, `[J]` "condense soon"; N-A if no caps config |
| landed plan present | flag | `[J]` classification |
| cold / stale plan | flag | `[J]` classification |
| init post-condition | green / flag | read-only check |
| hook wiring (shared / solo / **husky-chained**) | green / flag | `[D]` marker presence + `core.hooksPath` + git index mode + `check-ignore`; `[J]` whether an early `exit` above the marker is *unconditional* (control-flow reading, not a measurement). A husky chain is HEALTHY only when hooksPath resolves to husky; an absent `Husky chain:` record proves nothing |
| commit-hook interpreter | green / **flag** | `[D]` probe result **at doctor-run time** — each candidate EXECUTED against the ≥3.7 assertion, never resolved; flag = SKIPPED, and it speaks only for the shell doctor ran in |
| stamped fence vs installed plugin | green / **skew** / **N-A** | `[D] read-only — not a gate`: stamp version vs `plugin.json` version (N-A if either is unreadable/non-numeric); remedy = you re-run `init`, not a treat |
| Stage-9 harvest signal | flag | `[J]` soft advisory |

**`[D]` vs `[J]` is load-bearing, not decoration:** a `[D]` row states the gate's exact exit
result; a `[J]` row is doctor's judgment (a cold-plan call, the Stage-9 signal) and must read as
judgment, never as a mechanical fact.

## SELECT — pick what to act on  *(the shared finder-pipeline gate)*

Present the **WARN / breach + substantive findings** as the finder-pipeline **SELECT** checklist —
one editable `- [ ]` line per finding (contract: `docs/claugentic-WORKFLOW.md` → **The finder
pipeline** → *SELECT*; don't restate the mechanics). The **checked subset is what gets acted on**;
unchecked findings are a per-run skip.

> **No durable doctor reject-memory (deliberate — FLAG).** Unlike `audit` / `product`, doctor keeps
> **no** `rejected-findings` fence. A recurring health issue **SHOULD recur** on every run — the
> report is transient and there is no fence to bloat, so the dismissal-memory machinery is **YAGNI**
> here. A green tree next run is the only "dismissal" that matters; if the breach is still there, it
> resurfaces, by design.

## Treat — on approval, NEVER silent  *(the bounded-mechanical set)*

A checked finding in the **bounded-mechanical set** is **applied directly — no plan needed** — but
**only on your explicit approval, and doctor reports exactly what it did.** The set is precisely
**bounded ∧ reversible (git history recovers it) ∧ no-architectural-decision** (the treat-boundary
in `docs/claugentic-DECISIONS.md`; point at it, don't re-litigate it):

- **Delete a landed / cold plan** — bounded, reversible (git history), no decision.
- **Re-wire the pre-commit hook** — re-establish `.githooks/pre-commit` + `core.hooksPath`
  (shared) or `.git/hooks/pre-commit` (solo); bounded, reversible. **Chain-aware: it REFUSES to
  re-point ANY non-default `core.hooksPath` it did not itself establish** — not merely a
  recognized-healthy chain. The narrower rule has a hole: a repo that *declined* the chain has
  `core.hooksPath=.husky` and no marker, so it is not "recognized-healthy", and re-pointing it
  would **silently switch off every hook that repo owns**. On any husky repo, marked or not, the
  offer is to **CHAIN** (init's marker-guarded append), never to re-point; the treat's other
  actions are the sub-flag repairs (mark `.husky/pre-commit` executable · un-ignore the wrapper),
  and `core.hooksPath` is left to husky.
- **Apply a user-approved doc-condensation diff** for an over-budget / WARN ledger — the diff is
  the one `/claugentic-dev-harness:condense` proposes (the operator that runs the ordered
  condensation procedure); this treat is its **apply path** (reused by `/condense`, not duplicated).
- **Tree hygiene** — add a missing `ARCHITECTURE_TREE.md` entry, drop a stale one, or condense an
  oversized one; bounded, reversible.

> **The doc-condensation treat is safe ONLY because the diff is user-approved before apply — the
> approval IS the decision gate, NOT because condensation is decision-free.** Condensing a ledger
> *is* a judgment about what to keep; doctor shows the diff, you approve it, and that approval is
> what makes it a "just-do-it" treat. Word it that way to yourself — never imply the edit was
> decision-free.

Each treat fires **only on explicit approval** (the SELECT tick is *intent*; the apply still
confirms what it will change). After applying, **report what was done** — never apply silently.

## Substantive findings — NOT treated here  *(→ roadmap → plan → OFFER-BUILD)*

A finding that needs **an architectural decision or a non-trivial fix** is **not** treated by
doctor. Route it:

- **Add it to the roadmap.** In the **harness's own** repo it is normal **Quality / Feature** work
  (the harness *is* the product). In an **adopter** repo it is tooling-maintenance → the existing
  **Later** parking lot with a `harness` / `maintenance` **tag** (no new section — the volume doesn't
  warrant one; YAGNI).
- **Commitment triggers the plan.** Adding it to the roadmap = committing it = the Stage-2 plan
  trigger (`docs/claugentic-WORKFLOW.md` → *Commitment, not capture, triggers the plan*). A
  not-yet-committed finding stays a planless one-liner.
- **OFFER-BUILD.** Then run the finder-pipeline **OFFER-BUILD** step — ask via AskUserQuestion
  *"build these now, or leave them in the roadmap?"*, **default = leave** (offered, never forced).
  Build now → enter the `build` procedure; leave → it persists for a later `/claugentic-dev-harness:build`.

## What doctor is NOT

- **Not `/audit`.** Audit checks *your code* vs the standards catalog; doctor checks the *harness's
  own* wiring/ledgers/plans. They share the pipeline, not the target.
- **Not a new gate.** Doctor **runs** the existing gates — it adds none, wires no hook, and persists
  no fence. The only mechanical facts in its report are the gate scripts' exit codes and the
  interpreter probe (the tree and doc-budget gates wherever their script is present; the two
  harness-self gates only where theirs is, else N-A).
- **Not a silent fixer.** Every treat is on explicit approval, and substantive work goes through the
  roadmap → plan → build pipeline like any other committed item.
