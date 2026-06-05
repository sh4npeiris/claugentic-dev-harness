# Roadmap

The forward backlog for the harness itself — the genuine next steps, newest thinking at top. Each item runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect) in its own session, sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

Status: `NEXT` (queued) · `LATER`.

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own forward roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## Next

| Item | Why it matters | Status |
|------|----------------|--------|
| **Real-app dogfood** — prove `/claugentic-dev-harness:audit` produces a sharp, cited backlog on a real (JS) application. | The cold install is proven; this is the adoption-critical demo — that the audit yields a genuinely useful, accurately-cited backlog on code the harness didn't write. | NEXT |
| **Deterministic trust-gates** — the independent verification track: a `PreToolUse` characterization-tests-first hook + a secret-scan gate. | These are the "teeth" that are today model-upheld. The harness's #1 risk is false confidence from the same model class grading its own work; deterministic, model-independent signals are what make the quality bar real. | NEXT |
| **Test baseline for `scripts/check_architecture_tree.py`** — characterization tests for the one behavior-bearing file (mode dispatch + exit-code contract, the `STALE_PATTERN` regex, path-normalization, stdin-JSON parsing). | It's the linchpin gate the whole harness trusts and it has no safety net — a future tweak could silently stop it catching problems while still reporting "green." Tier-1 of the harness's own audit; lands with the trust-gate work. | NEXT |

## Later

| Item | Why it matters | Status |
|------|----------------|--------|
| **`/claugentic-dev-harness:update`** — re-sync managed copies in an adopter repo via the version stamp. | Closes the lifecycle: init copies, update refreshes. The managed-stamp + fence conventions already define its input contract. | LATER |
| **`/claugentic-dev-harness:explain`** — teach-as-you-go for non-engineers. | Lowers the barrier for the harness's target audience (someone driving AI-assisted development without a deep engineering background). | LATER |
| **Grow the role library** (`.claude/agents/`) as new specialist needs emerge from dogfooding. | The workflow delegates to specialists; more real use surfaces gaps the starter set doesn't cover. | LATER |
| **Capability modules** (Redis, queues, object-storage, …) authored just-in-time. | The catalog modernizes vibe-coded apps (introduce new tech safely), not just cleans code — but these are authored only when a real audit pulls one in (YAGNI). | LATER |
