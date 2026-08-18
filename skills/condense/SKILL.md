---
description: >-
  Condense a managed ledger (DECISIONS / ROADMAP / CLAUDE.md / any budgeted doc) that a doc-budget WARN or /doctor's "condense soon" advisory has flagged — two readers of the same per-repo caps config; the advisory is reachable in any repo, the gate's WARN only where its script is present (init delivers a copy, and chains it into your pre-commit wrapper where one is wired) — the executable operator for the WORKFLOW condensation pass. It runs an ordered, guarded procedure: STEP 1 classify EVERY entry before touching anything (the anti-footgun — landed build-records are the PRIMARY target, NEVER preserve them) → absorb landed/superseded records to git history → promote must-hold constraints to their home → merge duplicative siblings → trim re-derivable locators; targets the ~80% band (rejects a diff that re-lands at or above the 90% WARN) and keeps cross-referenced 00NN anchors. It is prose-orchestrated with NO bundled agent and NO mechanical what-to-cut decider — condensation is judgment: this skill CLASSIFIES and PROPOSES a diff, and you APPROVE it. The apply is /doctor's EXISTING user-approved-diff treat-path (reused, not rebuilt) — the approval IS the decision gate. Read-only until you approve.
---

# /claugentic-dev-harness:condense

> **Agent ids:** this skill is prose-orchestrated and spawns no bundled agent itself. There is
> no `/condense` sub-agent and no mechanical cut-decider — the classification and the proposed
> diff are model-upheld judgment, and the human approval is the decision gate.

The **executable operator for the condensation pass — and its one canonical home.**
`docs/claugentic-WORKFLOW.md` → Definition of Done carries the *obligation* (a budget WARN is a
do-it-now signal, discharged inside the current slice) and points here; the procedure itself lives
in this skill, as an **ordered, guarded procedure a non-expert agent can run reliably** — made hard
to get wrong. It is the next step a doc-budget WARN or `/doctor`'s "condense soon"
advisory OFFERs you — **two readers of one cap source**, reachable in different places. Both read
`.claude/claugentic-doc-budgets.json`, and with **no** config neither speaks (your own periodic
review is the cue). `/doctor`'s advisory runs **anywhere**. The **gate's** WARN needs the gate
script to be present in the repo being measured: it is in the release payload **and `init`
delivers a copy into your repo**. Where your **pre-commit wrapper is wired** it is chained in
there too, so the WARN reaches you at every commit — but that is not everywhere: a repo that
kept its own architecture tree has no wrapper, a machine with no working Python skips both
gates, and a wrapper installed by **v0.5.1 or earlier is never auto-chained** (`init` reports
how to adopt the current one). Off that path — and in a repo `init` has not touched at all —
`/doctor`'s advisory is the signal. This skill is the single source for
both the *why* and the *how*, in order; WORKFLOW states the obligation and the escape-valve
ladder, and deliberately does not restate the procedure.

## The one rule that must not be inverted (read this FIRST)

**Landed build-records are the PRIMARY target of a condensation pass — NEVER preserve them.**
A `**00NN — LANDED ...**` narrative is usually the largest, most-condensable thing in the ledger.
Its protection from being re-litigated is **(a) the promoted durable constraint** (a must-hold moved
to `docs/claugentic-INVARIANTS.md` or into the code / managed doc it changed) **plus (b) git
history** — it is **NOT** the kept narrative. So *"do-not-re-litigate"* never licenses *"keep the
full LANDED text."*

The classic underdelivery this skill exists to prevent: an agent told to "preserve the landed
entries" then **nibbles unrelated live rules** and shaves ~4% while the settled bulk sits
untouched — inverting the whole pass. This procedure makes that inversion structurally hard by
forcing **classify-first** (STEP 1) before any edit. If you find yourself protecting a LANDED
narrative, stop: you have inverted the rule.

## How this skill works — three movements

**Classify (read-only) → Propose a diff → Apply on your approval (via `/doctor`'s existing
treat-path) → Re-check.** Nothing is mutated before you approve the diff. This skill runs no
script, sets no exit code, and does not itself decide what to cut — it proposes; you approve.

## STEP 1 — Classify EVERY entry BEFORE touching anything  *(the reliability contract)*

Do this first, for the **whole** ledger, before proposing a single edit. Read each entry and tag it
into exactly one of four buckets. Do not skip to editing — the ordering is the guardrail.

- **landed-record** — a `**00NN — LANDED ...**` entry, a "how we got here" narrative, a plan already
  landed. **The PRIMARY target.** Its live constraint has a permanent home already (promoted
  INVARIANT, or it lives in the code / managed doc it changed) and its story is git history.
  → STEP 2 absorbs it. **Never preserve it.**
- **superseded** — an entry a later decision overrode, a settled trade-off, a value now stale.
  → STEP 2 drops it to git history (lossless — git is the archive; there is no `docs/archive`).
- **live-constraint** — a decision still in force · an open trade-off · a "never do X because Y" a
  future change could re-break. **This is what the ledger exists for — KEEP it.** Condense its
  wording, never its force.
- **must-hold** — a live-constraint that has hardened into a load-bearing invariant ("what must stay
  true or something breaks"). → STEP 3 promotes it to its proper home, then the ledger entry
  becomes a one-line pointer or nothing.

**Sort by *settled-ness*, never by *age*.** An old load-bearing constraint STAYS; a landed-yesterday
build-record GOES. Condensing the *oldest* entries is exactly how a still-live constraint is lost and
history repeats — age is not the axis. The per-entry keep/drop test: *will a future agent need this to
make a correct decision, or is it settled fact git history already holds?*

**Before you finish classifying, grep for cross-references.** For any `00NN` anchor an entry carries,
grep the repo for that anchor (other DECISIONS entries, ROADMAP, plans, WORKFLOW). **If anything
references it, KEEP the anchor** and condense the body around it — a dropped anchor breaks a live
cross-reference. Only a truly unreferenced anchor may go with its entry.

## STEP 2 — Absorb landed + superseded records  *(largest reduction first)*

For each **landed-record** and **superseded** entry: **drop the narrative, keep the constraint.**
Promote-or-locate the still-live constraint (STEP 3 if it is a must-hold; otherwise confirm it already
lives in the code / managed doc it changed), then remove the story. Leave **at most a one-line
pointer** — often nothing. Git history holds the full text; the drop is lossless and recoverable.

**Prevention note (for future Lands):** a landed plan should contribute a forward-looking *keep-line*
or a *promoted INVARIANT*, not a "here's what I built" narrative — the commit message + the changed
files are the build record. If you are absorbing a fat LANDED entry now, that entry should not have
been written that way; the ledger stays lean by not accreting build narratives in the first place.

## STEP 3 — Promote must-hold constraints to their home

For each **must-hold**: move it to where load-bearing truth lives — `docs/claugentic-INVARIANTS.md`
for a "what must stay true or something breaks" invariant, or the relevant `CLAUDE.md` harness block
for durable structural/domain context. Then the ledger entry becomes a **one-line pointer** to that
home, or is dropped entirely. **Promoting into INVARIANTS / CLAUDE.md respects THEIR caps too** — do
not simply relocate the bloat; promote the distilled constraint, not the narrative. **The home list is not closed — the home is whichever doc already OWNS the topic:** a release/runbook step to the release runbook, a review rule to the standards module for its dimension, a role's bar to that role's file. Re-homing to the owner is rung 1 of the escape-valve ladder done properly, and it is what turns an un-cuttable live item into a real reduction. **And where a Stage-9 harvest has already promoted an entry's incident into one of those homes, the ledger's retelling is now a duplicate** — leave a pointer and absorb the story. *(0041 S10b-L8, measured: a ROADMAP needing +631 B against 95 B of levers absorbed the routing with **no** shave — one item re-homed to the release runbook, three retold incidents that recent harvests had promoted into standards modules cut to pointers.)*

## STEP 4 — Merge duplicative siblings — ENTRIES, and the prose around them

Collapse several dated one-liners about one subsystem into **a single dense current-state line** — the
newest truth, not the diff that produced it. One subsystem, one current-state entry.

**Sweep the NON-entry prose too — preamble, how-this-file-works blurbs, section-heading suffixes,
repeated contract restatements.** A ledger accretes explanation the same way it accretes entries, and
boilerplate duplicates across *kinds* of surface where an entry-only read never looks: one rule stated
in the preamble, again under a heading, again inside an entry. State each contract **once**, in the one
place a reader meets it first, and delete the echoes. **This lever is the whole pass on a ledger with no
landed-records to absorb** — a forward backlog (a ROADMAP) holds live work by definition, so STEP 2's
usual primary target is simply absent and STEPS 4-5 carry the reduction. *(0041 S9, measured: a ROADMAP
condensation's single largest win — ~850 B of ~790 net — was one fence contract stated three times in
the preamble and twice more in heading suffixes.)*

## STEP 5 — Trim re-derivable locators

Remove locators a maintainer re-derives from the code: helper/test filenames, line refs, worked-example
notation, dates that are re-derivable from git. Keep the *constraint*; drop the *coordinate*. This is the
finest-grained lever — apply it last, after the structural reductions (STEPS 2-4) have done the heavy work.

## Target the band — and REJECT a diff that re-lands at or above the WARN

Aim to return the ledger **comfortably under the WARN — the ~80% band, not the edge.** A pass that lands
at **89.9%** re-fires the WARN on the very next append and the work repeats — **reject that diff and cut
deeper** (go back up the lever order: more STEP 2 absorption before more STEP 5 trimming). Condense once,
properly. If STEP 5 trimming is the only thing left and it still can't reach the band, you are likely at
the genuinely-all-live wall — see the escape valve below, do not over-cut live constraints to fake the band.

**The accept test (when to stop):** clearing the **WARN with real headroom** is the **pass floor**; the
~80% band is the **aspiration**. Reach the band when absorbable settled bulk still exists (unabsorbed
landed-records, un-merged siblings, un-trimmed locators). But once you have absorbed **every**
landed-record and the remainder is genuinely all-live constraint prose, **clearing the WARN with headroom
IS the pass** — do NOT cut into live force to chase ~80%. (A well-maintained forward-looking ledger often
floors out in the low-80s%, not at ~80% — that is a correct accept, not a shortfall.)

## Propose the diff → surface it → apply via `/doctor`'s existing treat-path

Produce the condensation as a **diff** and surface it for approval. **The apply path is `/doctor`'s
EXISTING "apply a user-approved doc-condensation diff" treat** (`skills/doctor/SKILL.md` → *Treat*) —
**reuse it; do not build a second apply path** (DRY). The honesty framing there is the same, adapted to this skill's voice (doctor is the source of truth):

> The doc-condensation treat is safe **only because the diff is user-approved before apply — the
> approval IS the decision gate**, NOT because condensation is decision-free. Condensing a ledger *is*
> a judgment about what to keep; this skill shows you the diff, you approve it, and that approval is what
> makes the apply a bounded, just-do-it treat. Never imply the edit was decision-free.

This skill **classifies and proposes**; the human **approves the diff**. It never claims to mechanically
decide what to cut — there is no cut-decider. The proposed classification (STEP 1) and the proposed diff
are model-upheld judgment; your approval is the gate.

## Re-check loop — measure after apply

After the diff is applied, **re-measure** the ledger:

- **Under the band (~80%)** → done. Report the before/after byte figure and the new headroom.
- **Still at or over the WARN** → the diff was too shallow: return to the lever order (STEP 2 first) and
  propose a deeper cut, or — if the content is genuinely all-live and cannot reach the band without
  over-cutting live constraints — **the escape-valve ladder is the recourse** — promote durable
  constraints to their home → a deliberate, recorded cap increase → sharding as the last resort. All
  three rungs live in `docs/claugentic-WORKFLOW.md` → the condensation pass (*The escape-valve ladder*);
  the recorded cap-increase rung raises this repo's cap in the per-repo caps config
  (`.claude/claugentic-doc-budgets.json`) with a dated `docs/claugentic-DECISIONS.md` entry.
  **Which edit that is depends on the entry's FORM** (all three are in
  `skills/doctor/SKILL.md` → *Adopter doc-budget advisory*, the reader-contract's one home):
  a **plain integer** → replace the number · an **object** → edit its `"max"` and leave
  `reportOnly` alone (that flag is a separate decision) · a **glob key** → the bump raises the
  cap for **every** file that glob matches, because the glob is the sole cap for its matches;
  a per-file exception beside it would be a second cap source and is deliberately not offered.
  And when a file is over budget on **day one**, the honest instrument is the `reportOnly`
  grace, **never** a cap sized to the file — a cap chosen at the measurement is a ceiling-raise
  wearing another face. This skill references the ladder; it does not build it.

## What `/condense` is NOT

- **Not a mechanical cut-decider.** It classifies and proposes a diff; condensation is judgment and the
  human approval is the decision gate. It never claims to decide cuts mechanically.
- **Not a second apply path.** It reuses `/doctor`'s existing user-approved-diff treat — no duplicate apply
  infrastructure (DRY).
- **Not a new gate or hook.** It runs no script and sets no exit code; the doc-budget WARN and `/doctor`'s
  advisory are the *triggers*, this skill is the *work*. (The gate that emits that WARN does ship with
  the plugin — but it is not *this* skill, and nothing here adds a gate, a hook, or an exit code.)
- **Not the escape valve.** When condensation genuinely can't reach the band, the escape-valve ladder (above)
  is the recourse — not more cutting into live rules.
