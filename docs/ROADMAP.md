# Roadmap

The forward backlog for the harness itself. Work runs through `docs/WORKFLOW.md` (triage → plan → review → spec → approve → implement → verify → land → retrospect), sliced so each unit lands complete with no tech debt. Tangents land here, never silently into the current change.

> The harness audits *adopter* repos via `/claugentic-dev-harness:audit`, which writes its own `harness-audit:overview` / `harness-audit:backlog` fences into that repo's `docs/ROADMAP.md`. This file is the product's own roadmap, not a generated audit — an adopter generates theirs by running the skill.

---

## The two standing tracks — growing the libraries (ongoing · just-in-time)

The harness grows as it meets more codebases. Neither track is ever "done" — that's the right shape: additions are made when real use proves a gap, never speculatively.

| Track | How it grows |
|------|--------------|
| **Grow the role library** (`.claude/agents/`) — add specialist agents as real use surfaces gaps the starter set lacks. | The workflow delegates to specialists; when real work keeps hitting a job no existing role owns, that's the signal to add one (and register it in `plugin.json`, the WORKFLOW roster, and the architecture tree). |
| **Grow the standards catalog** (`docs/standards/`) — author new quality modules and capability modules (Redis, queues, object-storage, …) as real projects pull them in. | A real audit or review that needs a bar the catalog doesn't carry is the signal to author it (conforming to `_TEMPLATE.md`, indexed in the catalog README). The catalog modernizes vibe-coded apps, not just cleans code. |
