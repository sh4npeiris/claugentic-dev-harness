# Roadmap

The forward backlog for the harness itself — the genuine next steps, newest thinking at top. Each item runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect) in its own session, sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

Status: `NEXT` (queued) · `LATER`.

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own forward roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## Next

| Item | Why it matters | Status |
|------|----------------|--------|
| **Deterministic trust-gates** — the independent, *model-independent* verification track: a `PreToolUse` characterization-tests-first hook + a secret-scan gate. | The harness's #1 risk is false confidence from the same model class grading its own work. The audit's `finding-verifier` (v0.1.2) *reduces* that; these gates *remove* it wherever a fact is mechanically checkable. The tree-gate now has a test baseline (✓ v0.1.2) to build on. | NEXT |

> **Done (v0.1.2):** Real-app dogfood (an adopter) · the audit's verify-findings pass + `finding-verifier` agent · the tree-gate test baseline (`STALE_PATTERN`→`EXTS`). See `docs/DECISIONS.md` 2026-06-08.

## Later

| Item | Why it matters | Status |
|------|----------------|--------|
| **`/claugentic-dev-harness:update`** — re-sync managed copies in an adopter repo via the version stamp. | Closes the lifecycle: init copies, update refreshes. The managed-stamp + fence conventions already define its input contract. | LATER |
| **`/claugentic-dev-harness:explain`** — teach-as-you-go for non-engineers. | Lowers the barrier for the harness's target audience (someone driving AI-assisted development without a deep engineering background). | LATER |
| **Grow the role library** (`.claude/agents/`) as new specialist needs emerge from dogfooding. | The workflow delegates to specialists; more real use surfaces gaps the starter set doesn't cover. | LATER |
| **Capability modules** (Redis, queues, object-storage, …) authored just-in-time. | The catalog modernizes vibe-coded apps (introduce new tech safely), not just cleans code — but these are authored only when a real audit pulls one in (YAGNI). | LATER |
| **Deepen finding-verification by dial** — `standard` also verifies `deterministic`-labeled findings; `thorough` verifies **all** findings + a second adversarial sweep. | v0.1.2 verifies Tier-1 + security on every dial (the trust floor). Scaling verification by dial is a cost/coverage trade to make once real-audit cost is measured — and it's what the deferred `thorough` level becomes. | LATER |
| **Fail loud when `git` is unavailable** in `scripts/check_architecture_tree.py` — today a missing/failed `git` yields an empty file list, so the gate reports "green" instead of erroring. | The linchpin gate's "green" must be trustworthy; a silent false-green undercuts the whole point. Add the guard + a companion test. | LATER |
