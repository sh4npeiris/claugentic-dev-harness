---
description: Check the harness's OWN health (distinct from /audit, which checks YOUR code vs the standards) — run the existing deterministic gates read-only (architecture-tree always · version-sync + doc-budgets + shipped-content are harness-self, run only where their script is present, else N-A in an adopter), scan for landed/cold plans, re-assert the init post-conditions, and flag a likely-skipped Stage-9 harvest, then report a green/WARN/breach snapshot. It treats only the bounded-mechanical set (delete a landed/cold plan · re-wire the pre-commit hook · apply a user-approved doc-condensation diff · tree hygiene) — and ONLY on your explicit approval, never silently. Anything substantive is routed to the roadmap → plan → offered to build. The diagnose is strictly read-only; nothing is mutated before you select and approve.
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
**The rule:** the **tree gate always ships and always runs**; the **harness-self gates**
(version-sync, doc-budgets, shipped-content) run **iff their script is present** — when a script
is ABSENT (an adopter repo: all are stripped from the release) the gate is **N-A (harness-self —
not shipped to adopters)**, never a breach and never an error. (Per-script presence is the
adopter signal — there is no separate "am I an adopter" flag.)

- **`python scripts/claugentic-check_architecture_tree.py`** — exit **0 = green** · exit **1
  = breach** (a missing/stale entry or a zero-coverage glob-drift). The tree gate is the one
  hook-enforced gate; here doctor just runs it ad-hoc and reports. **Always present, always run.**
- **`python scripts/check_versions_synced.py`** — *(harness-self — N-A in an adopter; its
  script is stripped from the release)*. **If the script is present:** exit **0 = green** · exit
  **1 = breach** (`plugin.json` ↔ `marketplace.json` version drift, or a malformed manifest).
  **If absent:** mark **N-A**, do not run.
- **`python scripts/check_doc_budgets.py`** — *(harness-self — N-A in an adopter; its script is
  stripped from the release)*. **If the script is present:** exit **0 + no `WARN:` line = green**
  · exit **0 + a `WARN:` line = WARN** (a ledger ≥ 90% of its budget — the cue to condense before
  it hard-breaks) · exit **1 = breach** (a ledger over budget). **The INVARIANTS cap already lives
  in this script** (added in 0024 S3) — doctor just runs it; **there is no script change.**
  **If absent:** mark **N-A**, do not run.
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

The **adopter-portable** companion to the harness-self doc-budgets gate above. Where that
gate is stripped from the release (so an adopter's repo never produces its WARN), this read
gives an adopter the **same "condense soon" signal** — sourced not from a gate but from a
per-repo caps config the adopter owns. It is **read-only and advisory**, never a gate: it
runs no script, sets no exit code, and blocks nothing.

- **The caps source is ONE file:** `.claude/claugentic-doc-budgets.json` — a JSON map
  `{ "<relpath>": <max_bytes>, ... }` (repo-relative path → integer byte cap). This is the
  **single adopter-side cap list.** Never read `scripts/check_doc_budgets.py`'s `DOC_BUDGETS`
  for this — those are the harness's OWN harness-tuned caps (a separate, **harness-self**
  concern; that script is **stripped from the release** and fail-louds on adopter files, which
  is exactly why this config-driven read exists instead).
- **A SPLIT ledger needs one caps key per part.** If a repo has climbed the escape-valve
  ladder's last rung (`docs/claugentic-WORKFLOW.md` → *The escape-valve ladder*) and split a
  ledger into a routing index plus per-topic parts, add **one key per file** — the index at
  its own (deliberately tight) cap, and each part at the shared per-part cap. The map is flat
  and has **no glob support**, so an unlisted part is simply un-capped and skipped here; that
  is the honest cost of the flat shape, not a silent pass on a file this read claims to watch.
- **Skip-when-absent is the default (HARD rule).** If `.claude/claugentic-doc-budgets.json`
  is **not present**, this read is **silently skipped — mark N-A, emit no output, no error,
  no WARN, no breach.** An un-configured repo (the adopter default, and the harness's own repo)
  produces *nothing* here. This is the exact safety property that let the harness gate be
  stripped; the portable read inherits it — it must never fail-loud on a repo that hasn't
  opted in. (An absent *key* for a present config = that file is un-capped → skipped too.)
- **When the config is present:** for each capped file that exists, measure its byte size
  (`len(read_bytes())` — bytes, never char count) and compare to its cap. At **≥90% of the
  cap**, surface a `[J]` "condense soon" advisory carrying the `[D]` byte figure — e.g.
  *"DECISIONS.md at 92% of your configured cap (55200 / 60000 bytes) — condense soon."* The
  **byte count and the 90% comparison are the `[D]` mechanical part**; **"condense soon" is
  `[J]` judgment** — an advisory, never a gate verdict. Below 90% report green for that file;
  a capped file that doesn't exist is skipped (nothing to measure).
- **Honesty (the line to hold):** this read **NEVER claims to be a gate.** Say *"the caps
  config puts DECISIONS at 92% — condense soon"*, never *"the budget gate WARNs"* — there is
  no gate here, only a config-driven advisory. A "condense soon" advisory surfaces as a
  finder-pipeline finding (SELECT below), routed like any other — the condensation itself is
  the existing user-approved-diff treat (`docs/claugentic-WORKFLOW.md` → the condensation pass).
- **OFFER `/condense` as the next step (the ramp, not a dead-end).** When this read surfaces a
  "condense soon" advisory — and equally when the harness-self **doc-budgets gate returns a
  `WARN:` line** (a ledger ≥90% of its budget) — **OFFER `/claugentic-dev-harness:condense`** as
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

- **Pre-commit hook wired** — **shared mode:** `.githooks/pre-commit` present **and**
  `git config core.hooksPath` = `.githooks`; **solo mode:** `.git/hooks/pre-commit` present
  with `core.hooksPath` left at default. A non-default existing `core.hooksPath` that isn't the
  harness's is **reported, never assumed broken** (init never clobbers it).
- **Managed-file stamps** present and **parseable** — a managed doc/tree's stamp line carries a
  parseable-semver on line 1 (the never-clobber upsert marker).
- **Stamped fence vs the installed plugin** — compare the CLAUDE.md `harness:managed` fence's
  `claugentic-dev-harness@<semver>` stamp against the **installed plugin's own**
  `.claude-plugin/plugin.json` `version` (the plugin the session is running, not the adopter
  repo — an adopter has no `.claude-plugin/` of its own). Stamp **<** plugin = **skew**, and the
  treat is **re-run `/claugentic-dev-harness:init`** (already an init concern — the never-clobber
  upsert re-stamps; **not** a new treat class). The comparison is `[D]` **only where both values
  are readable and both parse as numeric semver**; a missing fence, an unreadable manifest, or a
  non-numeric version is **N-A — never a guess and never a breach.** (The SessionStart advisor
  surfaces the same skew as a one-line user-facing nudge; this row is the on-demand read of it.)
- **(Shared mode only) the plugin self-reference** in `.claude/settings.json` — the harness in
  `extraKnownMarketplaces` + `enabledPlugins`. **Solo mode has no self-reference by design** — its
  absence in solo mode is **not** a finding (don't flag the intended divergence).

### 5. The Stage-9 harvest signal  *(REPORT-ONLY · `[J]` · soft advisory)*

Flag a **recent landed plan whose land window touched no learning surface** — no
`docs/claugentic-standards/`, no `CLAUDE.md`, no `.claude/agents/`, no
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
| doc-budgets gate | green / WARN / breach / **N-A** | `[D]` exit code (+ `WARN:` line); N-A if script absent — harness-self |
| shipped-content gate | green / WARN / breach / **N-A** | `[D]` exit code (+ `WARN:` line); N-A if script absent — harness-self |
| adopter doc-budget advisory | green / condense-soon / **N-A** | `[J] advisory (read-only — not a gate)` — `[D]` byte figure, `[J]` "condense soon"; N-A if no caps config |
| landed plan present | flag | `[J]` classification |
| cold / stale plan | flag | `[J]` classification |
| init post-condition | green / flag | read-only check |
| stamped fence vs installed plugin | green / **skew** / **N-A** | `[D]` stamp version vs `plugin.json` version (N-A if either is unreadable/non-numeric) |
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
  (shared) or `.git/hooks/pre-commit` (solo); bounded, reversible.
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
  no fence. The only mechanical facts in its report are the gate scripts' exit codes (the tree gate
  always; the three harness-self gates only where their script is present, else N-A).
- **Not a silent fixer.** Every treat is on explicit approval, and substantive work goes through the
  roadmap → plan → build pipeline like any other committed item.
