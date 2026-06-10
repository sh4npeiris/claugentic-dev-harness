# The Harness Playbook — how to drive an AI dev team

A plain-English guide to working *with* this harness, for a capable non-engineer. It turns ad-hoc "vibe coding" into a disciplined practice that gives you a real shot at software that passes a professional code review. **You don't write code — you make product calls and approve the right things at the right moments.**

## The one-minute model

Substantial work flows through a pipeline: **Triage → Discuss → Plan → Review-the-plan → Spec → Approve → Implement → Verify → Land → Retrospect** (small changes skip straight to Implement + Verify). The agent runs it; **you steer at three points.** Full version: [`WORKFLOW.md`](WORKFLOW.md).

## Your three leverage points

The whole system is built so you steer **what gets built and what "done" means** — with product judgment. Approving the spec is the steering point; you set intent and bless the plan, and the harness carries the code-shaped detail from there:

1. **Brainstorm at Discuss.** Tell the harness *who the user is* and *what "good" means* for this product. The more context here, the better everything downstream. This is your Product-Designer seat.
2. **Approve the Spec.** Nothing gets built before you sign off on *what* will be built and *what "done" means*. You approve intent, not code. This is your steering wheel.
3. **Approve lessons.** When the harness says "I think this should become a standard," you keep or kill it. That's how the standards stay *yours*.

### How to approve a spec (you don't need to read the code)

When the agent hands you a spec to approve, read the plain-English part and ask yourself:

- **Does this match what I asked for?**
- **Is anything I care about missing?**
- **Are the risks ones I'm OK with?**
- **What does it explicitly NOT do?** (a good spec says so.)

If any answer is "no," say **"this is missing X, please revise"** — you don't have to fix it yourself. And the technical detail below the plain-English block is for the agent and reviewer to check against — **you are not expected to read it.**

Everything else — reading code, writing it, reviewing it — the harness fans out to specialists so your attention stays on decisions.

## Why it's trustworthy

Three moves make the output worth trusting:

1. **A different, skeptical agent reviews the work** and tries to refute it. The author is the worst judge of their own work, so the harness never lets the agent that wrote something be the one that signs off on it.
2. **Anything that can be checked mechanically is checked, not believed** — a test, a `grep`, a web-lookup. Models produce confident, professional-looking errors; a deterministic check doesn't care how confident the prose is.
3. **It's honest about its limits.** Where a claim *can't* be checked mechanically, the harness labels the finding as judgment, not proof — so you always know which is which.

## How to start work

**To start anything — a backlog item or a brand-new project — just tell the agent in plain English what you want** (e.g. "Let's do Tier-1 item 1" or "I want to build X"). It will ask you questions (Discuss), then write a plan and spec for you to approve before any code. That's the go-button: you describe what you want, it drives the workflow.

**If the agent starts writing code without asking you product questions first, say "use the workflow"** — it should pause and ask.

## Using the audit (`/claugentic-dev-harness:audit`)

Run it as a **periodic snapshot**, not a treadmill: the backlog **regenerates** (it doesn't pile up), **Tier 3 is optional polish**, and an **empty Tier 1 + Tier 2 means the code is sound** — your signal to stop, not a prompt to invent work. It **auto-sizes** its effort to the repo (override with `quick` / `standard`). And it doesn't just *assert* its findings: **every surfaced finding (all tiers) gets re-checked** — a separate agent, by default on a **different model family** than the builder (the cross-model judge; a same-family run is tagged as such), reads the actual code and tries to disprove each one, so false alarms are dropped and each survivor is tagged with what came back. *(That's an honest reduction of false confidence — a reduction of shared-blind-spot risk, not an absolute guarantee.)* *(Full operating rules live in the skill's own "How to use it".)*

Once the backlog is written, starting an item is the same go-button as everything else: **tell the agent "let's do Tier-1 item 1"** (or whichever) in plain English, and it runs the workflow from Discuss. To work **more than one** item, the go-button is **`/claugentic-dev-harness:build`**: name several items or a whole tier ("build all of Tier-1"), confirm the order, and it works them one by one to the honest "sound on the audited dimensions" stop-signal — re-checking the code it just touched between items and pausing for you only when new important work surfaces (and never for anything irreversible without asking). You can approve each spec as its turn comes, or say **"spec everything first"** to plan the whole list and approve it in **one sitting** before any building begins.

## When in doubt

Ask the agent to **explain what it just did and why** — it's built to teach you as you go. The goal is that you get better at directing it every cycle.

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
