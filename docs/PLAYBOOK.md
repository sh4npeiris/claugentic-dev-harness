# The Harness Playbook — how to drive an AI dev team

The plain-English guide to working *with* this harness, written for a capable non-engineer. The harness turns ad-hoc "vibe coding" into a disciplined practice that produces software able to pass a professional code review. **You don't need to write code — you make product calls and approve the right things at the right moments.**

## The one-minute model

Substantial work flows through a pipeline: **Triage → Discuss → Plan → Review-the-plan → Spec → Approve → Implement → Verify → Land → Retrospect** (small changes skip to Implement + Verify). The agent runs it; you steer at three points. Full version: [`WORKFLOW.md`](WORKFLOW.md).

## Your three leverage points

The whole system is built so you steer with **product judgment, not code**:

1. **Brainstorm at Discuss.** Tell the harness *who the user is* and *what "good" means* for this product. The more context here, the better everything downstream. This is your Product-Designer seat.
2. **Approve the Spec.** Nothing gets built before you sign off on *what* will be built and *what "done" means*. You approve intent, not code. This is your steering wheel.
3. **Approve lessons.** When the harness says "I think this should become a standard," you keep or kill it. That's how the standards stay *yours*.

Everything else — reading code, writing it, reviewing it — the harness fans out to specialists so your attention stays on decisions.

## The patterns that produce quality (and when each fires)

These are *how* the harness aims past "standard practice." You'll see their names in `/workflows`:

- **Fan-out** — many specialists in parallel, each on one piece. *Why:* speed, and each agent stays focused. *Used for:* authoring many things at once, reviewing through many lenses.
- **Author → adversarial verify** — one agent writes; a *different, skeptical* agent tries to **refute** it. *Why:* the model that wrote something is the worst judge of it; an independent skeptic catches the confident mistakes. **This is the core trust move.**
- **Trust the oracle, not the model** — wherever a fact can be checked *mechanically* (a test, a `grep`, a web-lookup), the harness checks it that way instead of believing the model's word. *Why:* models produce confident, professional-looking errors; deterministic checks don't.
- **Effort dial** — match review depth to the change's risk. *Why:* running the whole machine on a typo wastes time and money and kills your velocity.
- **Loop-until-dry** — for open-ended hunts (find all the issues), keep going until a pass finds nothing new. *Why:* the long tail is where the real problems hide.
- **Judge-panel / best-of-N** — for a big design fork, generate several independent approaches, score them, and combine the best of each. *Why:* the first idea is rarely the best — this "takes the best of all possibilities."

## A real worked example (this harness built its own standards this way)

The standards catalog in [`standards/`](standards/README.md) was built by the harness, on itself:

1. **5 agents authored** the deep standards modules in parallel *(fan-out)*.
2. **5 skeptics tried to refute** each *(adversarial verify)* — and caught a *made-up citation*, a *misattributed quote*, and *wrong book chapters*, all of which looked perfectly professional.
3. The fixes **re-checked every citation against the real web source** *(trust the oracle)*.
4. A final **`grep`** — a plain text search, no AI — confirmed the format was clean *(deterministic check)*.

Every one of those errors would have shipped under a normal "looks good to me" workflow. **Catching them is the harness.**

## Mini-glossary (terms you'll see)

- **Characterization / golden-master test** — a test that captures what the code *currently does*, so you can change it and prove the behavior didn't move. The safety net for touching legacy code.
- **Idempotent** — doing it twice is the same as doing it once (safe to retry).
- **Fitness function / gate** — an automatic check that *enforces* a standard; it can't be argued around.
- **Lens** — one quality viewpoint (security, performance, UX…); the harness reviews through several at once.
- **Effort dial** — the knob that scales review depth to risk.
- **Dual-layer output** — every finding stated technically *and* in plain English ("what this means for you").
- **Slice** — one unit of work small enough to finish completely in a single session, with no half-done leftovers.

## When in doubt

Ask the agent to **explain what it just did and why** — it's built to teach you as you go (a `/harness-explain` skill will make this one command once the plugin's skills land). The goal is that you get better at directing it every cycle.
