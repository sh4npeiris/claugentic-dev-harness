# 0013 — Cross-model fold: an unresolved model family is reported as unresolved, never asserted as same-model fact

- **Status:** Approved (authorized as Slice 5b's spec'd acceptance dogfood — plan 0012, batch sitting 2026-06-11 + the user's autonomous-continuation authorization; the engine run is the acceptance evidence)
- **Roadmap item:** `docs/ROADMAP.md` → harness-audit:backlog fence → Tier 2 → "An unknown model family silently degrades to 'same-model' with no signal" (verified 2026-06-11 thorough audit)
- **References:** `docs/DECISIONS.md` → Cross-model judges · `tests/workflows/cross-script.test.mjs` (the drift pin governs the copied helpers)

## Spec (single slice)

- **In plain English:** Today, when a judge's self-reported model family can't be recognized, the run is *labeled* "same-model review … the judge and the builder are the same model family here" — asserted as fact when the truth is "could not resolve." The conservative trust floor is right (no cross-model claim); the wording is not. After this change the run carries a distinct, honest tag for the unresolved case, and the resolution failure is logged, never silent. **Done means:** unresolved ≠ same-model in every script's fold and report wording; the known-family set is one named constant; the drift pin covers the new pieces. **You're accepting:** no behavior change to when cross-model is *claimed* (still only on confirmed different-family); only the disclosure wording and observability improve.
- **Files & changes:**
  - `workflows/verify.js`, `workflows/audit.js`, `workflows/qa.js` — in the shared helper block: add the verbatim constant `UNRESOLVED_FAMILY_TAG = "could not resolve the judge's model family on this run — no cross-model claim is made (treated as the same-model trust floor, not asserted as fact)."`; add `KNOWN_FAMILIES = ["fable", "opus", "sonnet", "haiku"]` and derive `modelFamily`'s regex from it (one named source); the fold helpers (`sameModelTag` / `crossModelOutcome` / `verificationSummary` / `crossModelClaim` per script) distinguish resolved-same (existing `SAME_MODEL_TAG`) from unresolved (`UNRESOLVED_FAMILY_TAG`); the control flow `log()`s when a self-report fails to resolve. All copies byte-identical (the drift pin).
  - `tests/workflows/*.test.mjs` — update/extend: unresolved → the new verbatim tag, never `SAME_MODEL_TAG`; resolved-same unchanged; `KNOWN_FAMILIES` named-constant pin; cross-script pin extended to the two new constants.
  - `docs/DECISIONS.md` — one dated line under Cross-model judges (the third state; wording-only trust improvement).
- **Acceptance criteria (deterministic-gate-checkable):** `node --test "tests/workflows/*.test.mjs"` green including the new cases; `python -m pytest` green; both gate scripts green; the cross-script drift pin green covering `UNRESOLVED_FAMILY_TAG` + `KNOWN_FAMILIES`.
- **In-scope dimensions:** maintainability-structure · testing · docs-traceability. Trust surface: yes (disclosure wording).
- **Out of scope:** any change to when cross-model is claimed; the run-report renderer wording beyond substituting the correct tag.
