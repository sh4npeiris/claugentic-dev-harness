# The Harness Playbook — how to drive an AI dev team

A plain-English guide to working *with* this harness, for a capable non-engineer. It turns ad-hoc "vibe coding" into a disciplined practice that produces software able to pass a professional code review. **You don't write code — you make product calls and approve the right things at the right moments.**

## The one-minute model

Substantial work flows through a pipeline: **Triage → Discuss → Plan → Review-the-plan → Spec → Approve → Implement → Verify → Land → Retrospect** (small changes skip straight to Implement + Verify). The agent runs it; **you steer at three points.** Full version: [`WORKFLOW.md`](WORKFLOW.md).

## Your three leverage points

The whole system is built so you steer with **product judgment, not code**:

1. **Brainstorm at Discuss.** Tell the harness *who the user is* and *what "good" means* for this product. The more context here, the better everything downstream. This is your Product-Designer seat.
2. **Approve the Spec.** Nothing gets built before you sign off on *what* will be built and *what "done" means*. You approve intent, not code. This is your steering wheel.
3. **Approve lessons.** When the harness says "I think this should become a standard," you keep or kill it. That's how the standards stay *yours*.

Everything else — reading code, writing it, reviewing it — the harness fans out to specialists so your attention stays on decisions.

## Why it's trustworthy — one real example

The standards catalog in [`standards/`](standards/README.md) was built by the harness, on itself. The build is the proof of the whole approach:

1. **Several agents authored** the deep standards modules in parallel.
2. **Independent skeptics tried to refute** each one — and caught a *made-up citation*, a *misattributed quote*, and *wrong book chapters*, all of which looked perfectly professional.
3. The fixes **re-checked every citation against the real web source.**
4. A final **`grep`** — a plain text search, no AI — confirmed the format was clean.

Every one of those errors would have shipped under a normal "looks good to me" workflow. **That's the point of the harness:** a *different, skeptical* agent reviews the work, and wherever a fact can be checked mechanically, it's checked — not believed. (It's honest about its limits, too: where it can't check something mechanically, it labels the finding as its own judgment, not proof.)

## Using the audit (`/claugentic-dev-harness:audit`)

Run it as a **periodic snapshot**, not a treadmill: the backlog **regenerates** (it doesn't pile up), **Tier 3 is optional polish**, and an **empty Tier 1 + Tier 2 means the code is sound** — your signal to stop, not a prompt to invent work. It **auto-sizes** its effort to the repo (override with `quick` / `standard`). And for the findings that matter most — anything **Tier 1 (correctness, security, data-loss)** — it doesn't just *assert* them: a **second, independent agent reads the actual code and tries to disprove each one**, so false alarms are dropped and the survivors arrive with their proof attached. *(That's an honest reduction of false confidence — it doesn't claim to be an absolute guarantee.)* *(Full operating rules live in the skill's own "How to use it".)*

## When in doubt

Ask the agent to **explain what it just did and why** — it's built to teach you as you go. The goal is that you get better at directing it every cycle. *(A future `…:explain` skill will make this one command.)*

---

## Under the hood (optional — you don't need this to drive it)

**The patterns that produce quality.** These are *how* the harness aims past "standard practice":

- **Fan-out** — many specialists in parallel, each on one piece (speed + focus).
- **Author → adversarial verify** — one agent writes; a *different, skeptical* agent tries to **refute** it. The model that wrote something is the worst judge of it. *This is the core trust move.*
- **Trust the oracle, not the model** — wherever a fact can be checked mechanically (a test, a `grep`, a web-lookup), check it that way. Models produce confident, professional-looking errors; deterministic checks don't.
- **Effort dial** — match review depth to the change's risk; don't run the whole machine on a typo.
- **Loop-until-dry** — for open-ended hunts, keep going until a pass finds nothing new (the long tail is where the real problems hide).
- **Judge-panel / best-of-N** — for a big design fork, generate several approaches, score them, combine the best of each.

**A few terms you'll see.**

- **Characterization / golden-master test** — a test that captures what the code *currently does*, so you can change it and prove the behavior didn't move. The safety net for touching legacy code.
- **Idempotent** — doing it twice is the same as doing it once (safe to retry).
- **Gate / fitness function** — an automatic check that *enforces* a standard; it can't be argued around.
- **Lens** — one quality viewpoint (security, performance, UX…); the harness reviews through several at once.
- **Dual-layer output** — every finding stated technically *and* in plain English ("what this means for you").
- **Slice** — one unit of work small enough to finish completely in a single session, with no half-done leftovers.
