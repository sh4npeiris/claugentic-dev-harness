---
description: >-
  Condense a managed ledger (DECISIONS / ROADMAP / CLAUDE.md / any budgeted doc) flagged by a doc-budget WARN or /doctor's "condense soon" advisory — the canonical home of the condensation procedure WORKFLOW's Definition of Done points at. An ordered, guarded procedure: classify EVERY entry before touching anything (the anti-footgun — landed build-records are the PRIMARY target, NEVER preserve them) → absorb landed/superseded to git history → promote must-holds to their home → merge duplicative siblings → trim re-derivable locators; targets the ~80% band, rejects a diff that re-lands at or above the 90% WARN, and keeps cross-referenced 00NN anchors. Prose-orchestrated, with NO bundled agent and NO mechanical what-to-cut decider — condensation is judgment: it CLASSIFIES and PROPOSES a diff, you APPROVE it, and the apply reuses /doctor's EXISTING user-approved-diff treat-path. The approval IS the decision gate; read-only until you give it.
---

# /claugentic-dev-harness:condense

> **Agent ids:** prose-orchestrated; spawns no bundled agent. There is no `/condense` sub-agent and no
> mechanical cut-decider — the classification and the proposed diff are model-upheld judgment, and the
> human approval is the decision gate.

The **executable operator for the condensation pass — and the one canonical home of its procedure.**
Ownership, so nothing is restated: `docs/claugentic-WORKFLOW.md` → Definition of Done carries the
**obligation** (a budget WARN is a do-it-now signal, discharged inside the current slice) and owns the
**escape-valve ladder**; `/claugentic-dev-harness:doctor` owns the **caps-config reader-contract**; this
skill owns the **procedure**. Two triggers read one cap source (`.claude/claugentic-doc-budgets.json`):
`/doctor`'s "condense soon" advisory, which runs anywhere, and the doc-budget **gate's** WARN, which
needs that gate's script in the repo being measured. With **no** caps config, your own periodic review
is the cue.

## The one rule that must not be inverted (read this FIRST)

**Landed build-records are the PRIMARY target of a condensation pass — NEVER preserve them.** A
`**00NN — LANDED ...**` narrative is usually the largest, most-condensable thing in the ledger. Its
protection from re-litigation is **(a) the promoted durable constraint** (a must-hold moved to
`docs/claugentic-INVARIANTS.md` or into the code / managed doc it changed) **plus (b) git history** — it
is **NOT** the kept narrative. *"Do-not-re-litigate"* never licenses *"keep the full LANDED text."*

The underdelivery this prevents: an agent told to "preserve the landed entries" **nibbles unrelated live
rules**, shaves ~4%, and leaves the settled bulk untouched. **Classify-first (STEP 1) makes that
structurally hard.** If you find yourself protecting a LANDED narrative, you have inverted the rule.

## How this skill works — three movements

**Classify (read-only) → Propose a diff → Apply on your approval (via `/doctor`'s existing treat-path)
→ Re-check.** Nothing is mutated before you approve. This skill runs no script and sets no exit code.

## STEP 1 — Classify EVERY entry BEFORE touching anything  *(the reliability contract)*

Do this first, for the **whole** ledger, before proposing a single edit. Tag each entry into exactly one
of four buckets. Do not skip to editing — the ordering is the guardrail.

- **landed-record** — a `**00NN — LANDED ...**` entry, a "how we got here" narrative, an already-landed
  plan. **The PRIMARY target.** Its live constraint already has a permanent home (a promoted INVARIANT,
  or the code / managed doc it changed) and its story is git history. → STEP 2. **Never preserve it.**
- **superseded** — an entry a later decision overrode, a settled trade-off, a now-stale value. → STEP 2
  drops it to git history (lossless — git is the archive; there is no `docs/archive`).
- **live-constraint** — a decision still in force · an open trade-off · a "never do X because Y" a future
  change could re-break. **This is what the ledger exists for — KEEP it.** Condense its wording, never
  its force.
- **must-hold** — a live-constraint hardened into a load-bearing invariant ("what must stay true or
  something breaks"). → STEP 3; the ledger entry becomes a one-line pointer or nothing.

**Sort by *settled-ness*, never by *age*.** An old load-bearing constraint STAYS; a landed-yesterday
build-record GOES — condensing the *oldest* entries is how a still-live constraint gets lost. The
per-entry test: *will a future agent need this to make a correct decision, or is it settled fact git
history already holds?*

**Before you finish classifying, grep for cross-references.** For any `00NN` anchor an entry carries,
grep the repo (other DECISIONS entries, ROADMAP, plans, WORKFLOW). **If anything references it, KEEP the
anchor** and condense the body around it. Only a truly unreferenced anchor may go with its entry.

## STEP 2 — Absorb landed + superseded records  *(largest reduction first)*

For each **landed-record** and **superseded** entry: **drop the narrative, keep the constraint.**
Promote-or-locate the still-live constraint (STEP 3 if it is a must-hold; otherwise confirm it already
lives in the code / managed doc it changed), then remove the story. Leave **at most a one-line pointer**,
often nothing — git history holds the full text, so the drop is lossless.

**Prevention note (for future Lands):** a landed plan should contribute a forward-looking *keep-line* or
a *promoted INVARIANT*, not a "here's what I built" narrative — the commit message and the changed files
are the build record.

## STEP 3 — Promote must-hold constraints to their home

Move each **must-hold** to where load-bearing truth lives — `docs/claugentic-INVARIANTS.md` for an
invariant, or the relevant `CLAUDE.md` harness block for durable structural/domain context — leaving a
**one-line pointer** or nothing. **Promoting respects the destination's caps too:** promote the distilled
constraint, not the narrative, or you have only relocated the bloat. **The home list is not closed — the
home is whichever doc already OWNS the topic:** a release step to the release runbook, a review rule to
the standards module for its dimension, a role's bar to that role's file. Re-homing to the owner is rung
1 of the escape-valve ladder done properly, and it is what turns an un-cuttable live item into a real
reduction. **Where a Stage-9 harvest has already promoted an entry's incident into one of those homes,
the ledger's retelling is now a duplicate** — leave a pointer and absorb the story.

## STEP 4 — Merge duplicative siblings — ENTRIES, and the prose around them

Collapse several dated one-liners about one subsystem into **a single dense current-state line** — the
newest truth, not the diff that produced it. One subsystem, one current-state entry.

**Sweep the NON-entry prose too — preamble, how-this-file-works blurbs, section-heading suffixes,
repeated contract restatements.** Boilerplate duplicates across *kinds* of surface where an entry-only
read never looks: one rule in the preamble, again under a heading, again inside an entry. State each
contract **once**, where a reader meets it first, and delete the echoes. **This lever is the whole pass
on a ledger with no landed-records to absorb** — a forward backlog (a ROADMAP) holds live work by
definition, so STEP 2's usual target is absent and STEPS 4-5 carry the reduction. *(0041 S9: a ROADMAP
pass's largest single win — ~850 B — was one fence contract stated three times in the preamble and twice
more in heading suffixes.)*

## STEP 5 — Trim re-derivable locators

Remove locators a maintainer re-derives from the code: helper/test filenames, line refs, worked-example
notation, dates re-derivable from git. Keep the *constraint*; drop the *coordinate*. The finest-grained
lever — apply it **last**, after STEPS 2-4 have done the heavy work.

## Target the band — and REJECT a diff that re-lands at or above the WARN

Aim to return the ledger **comfortably under the WARN — the ~80% band, not the edge.** A pass landing at
**89.9%** re-fires the WARN on the very next append and the work repeats — **reject that diff and cut
deeper**, going back up the lever order (more STEP 2 absorption before more STEP 5 trimming).

**The accept test (when to stop):** clearing the **WARN with real headroom** is the **pass floor**; the
~80% band is the **aspiration**. Reach the band while absorbable settled bulk still exists (unabsorbed
landed-records, un-merged siblings, un-trimmed locators). Once **every** landed-record is absorbed and
the remainder is genuinely all-live constraint prose, **clearing the WARN with headroom IS the pass** —
do NOT cut into live force to chase ~80%; take the escape valve below instead. (A well-maintained
forward-looking ledger often floors out in the low-80s% — a correct accept, not a shortfall.)

## Propose the diff → surface it → apply via `/doctor`'s existing treat-path

Produce the condensation as a **diff** and surface it for approval. **The apply path is `/doctor`'s
EXISTING "apply a user-approved doc-condensation diff" treat** (the `claugentic-dev-harness:doctor` skill
→ *Treat*) — **reuse it; do not build a second apply path** (DRY). Its honesty framing carries over
verbatim, doctor being the source of truth: the treat is safe **only because the diff is user-approved
before apply — the approval IS the decision gate**, NOT because condensation is decision-free.
Condensing a ledger *is* a judgment about what to keep. Never imply the edit was decision-free.

## Re-check loop — measure after apply

- **Under the band (~80%)** → **clear any `reportOnly` grace on that entry, THEN** report the
  before/after byte figure and the new headroom. **This step is not optional and nothing mechanical does
  it** — `/doctor`, `init`, and the gate script each say the flag is cleared here and nowhere else, so a
  pass that skips it leaves the ledger graced forever and its cap silently not enforcing: a gate switched
  off invisibly. Editing the entry is a config change — it rides the **same user-approved diff**, and say
  so when you surface it.
- **Still at or over the WARN** → the diff was too shallow: return to the lever order (STEP 2 first) and
  propose a deeper cut — or, if the content is genuinely all-live and cannot reach the band without
  over-cutting live constraints, **take the escape-valve ladder** (`docs/claugentic-WORKFLOW.md` → *The
  escape-valve ladder*, which owns all three rungs; this skill references it, it does not build it). Its
  rung-2 cap increase raises this repo's cap in `.claude/claugentic-doc-budgets.json` with a dated
  `docs/claugentic-DECISIONS.md` entry, and **which edit that is depends on the entry's FORM** (all three
  forms live in the `claugentic-dev-harness:doctor` skill → *Adopter doc-budget advisory*, the
  reader-contract's one home): a **plain integer** → replace the number · an **object** → edit its
  `"max"`, leaving `reportOnly` alone (a separate decision) · a **glob key** → the bump raises the cap for
  **every** file that glob matches, because the glob is the sole cap for its matches; a per-file exception
  beside it would be a second cap source and is deliberately not offered. And when a file is over budget
  on **day one**, the honest instrument is the `reportOnly` grace, **never** a cap sized to the file — a
  cap chosen at the measurement is a ceiling-raise wearing another face.
