# Roadmap

The forward backlog for the harness itself — the genuine next steps, newest thinking at top. Each item runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect) in its own session, sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

Status: `NEXT` (queued) · `LATER`.

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own forward roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## Next

_Ordered by recommended sequence (top = first). Items 1–3 are the critical path to "usable to drive a real product end-to-end"; 4–5 earn honest autopilot; 6 is an independent refactor._

| # | Item | Why it matters | Status |
|---|------|----------------|--------|
| 1 | **Journey / usability fixes** — close the "no go-button" blocker (a plain "how to start" line + an interactive post-audit triage so the user picks what to commit), branch `init`/Quickstart on repo-state (code → audit · empty → start building), audit progress beats + "empty Tier-1+2 = success", make `INCLUDE_GLOBS` **self-correct** when real source appears (else the one mechanical gate silently rots), a backlog "how to read this" legend, a beginner on-ramp. | The journey review found **both** paths (existing repo · new project) dead-end one step before the payoff — there's no literal way to *start the work*. Cheapest, highest-impact; unblocks the colleagues already using it. | ✅ **DONE** — plan 0003 (3 slices; `949c3b4`/`4c1e67b`/`79fe61b`). _Deferred to #3: the interactive post-audit triage (only the doc "how to start" line + repo-state branching shipped)._ |
| 2 | **Thorough audit** (`thorough` dial) — verify **all** findings (not just Tier-1 + security) + a second adversarial sweep; `standard` additionally verifies `deterministic`-labeled findings. | A serious, exhaustive audit for a real product (e.g. before driving a half-built one to completion). The deferred deeper dial. | NEXT |
| 3 | **Build mode (autonomous, trust-dialed)** — after audit: interactive triage → "start now?" → an orchestrator that works the roadmap **item-by-item to the stop-signal** (Tier-1+2 empty). Two modes: **checkpoint** (pause at each decision — trustworthy today) and **autopilot** (do it all, surface decisions + a summary — *earned*, see #4–5). Hard stops on irreversible actions; genuinely-new features → roadmap for approval (no runaway scope). | The flagship: a team-of-professionals-**with-guardrails** builds your roadmap to production, you choose how closely to watch. Checkpoint mode is safe + buildable now; autopilot is gated on the trust mechanisms below. | NEXT |
| 4 | **Cross-model adjudication at the verify gates** — the *judge* (architect-reviewer · finding-verifier) runs on a **different, independent model** than the builder, so it isn't the same model class grading itself. *(Candidate: a newer overseer model — verify it's real, capable, and wireable as an agent model first.)* | The most practical answer to the harness's #1 risk (self-grading) and the key to **honest** autopilot — a heterogeneous judge is real independence. Agents already take a `model` override, so builder=Claude / judge=other is a clean wiring. | NEXT |
| 5 | **Deterministic trust-gates** — the model-*independent* track: a `PreToolUse` characterization-tests-first hook + a secret-scan gate. | The mechanical CI. With #4, this is what makes autopilot *trustworthy* rather than asserted — tests mechanically gate every slice. | NEXT |
| 6 | **Plugin-read architecture** *(supersedes `/...:update`)* — agents read standards/workflow from `${CLAUDE_PLUGIN_ROOT}/docs/…`; `init` shrinks + becomes refresh-capable. Validated (Slice 0); see plan `0002`. | One source of truth refreshed by the marketplace → deletes `/update` + the copy-staleness problem. Independent of the autonomy work. | NEXT |

## Later — growing the two libraries (ongoing · just-in-time)

Once everything in **Next** ships, the only standing work is growing the harness's two libraries as it meets more codebases. Neither is ever "done" — they grow as the harness sees more projects, which is the right shape for LATER.

| Track | Why it matters | Status |
|------|----------------|--------|
| **Grow the role library** (`.claude/agents/`) — add specialist agents as real use surfaces gaps the starter set lacks. | The workflow delegates to specialists; more real use surfaces gaps. Add a role when a gap is *real*, never speculatively. | LATER |
| **Grow the standards catalog** — author **capability modules** (Redis, queues, object-storage, …) as real projects pull them in. | The catalog modernizes vibe-coded apps (introduce new tech safely), not just cleans code — authored just-in-time when a real audit pulls one in (YAGNI). | LATER |
| **Partial-coverage glob drift** — the tree-check today flags only the **zero-coverage** case (`INCLUDE_GLOBS` watches *nothing* while source exists, plan 0003 Slice 3). Extend it to the narrower case: a repo whose globs already match files **grows a second, un-globbed stack**. | Built when a real adopter hits it (YAGNI — the lean zero-coverage check is correct + complete for the stated failure; a per-stack check risks re-introducing the rot it kills, see DECISIONS plan-0003). | LATER |
