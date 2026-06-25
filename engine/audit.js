// engine/audit.js — the audit pipeline (FIND -> PRUNE -> VERIFY) as an executable
// Workflow script. All three notches are scripted: `quick` + `standard` run the per-module
// lens sweep; `thorough` additionally runs a whole-scope blind-spot sweep (FIND) and an
// adversarial yagni-sentinel prune (PRUNE) — both wired into the same dedup -> verify path.
// The Phase-3 backlog fence body is rendered by a pure helper (renderBacklogFence) — the
// fence format's single source of truth, unit-tested so it can't drift from the documented shape.
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped plugin
// install dir (`${CLAUDE_PLUGIN_ROOT}/engine/audit.js`); this repo dogfoods it via the
// repo-local `./engine/audit.js` (the working tree IS the plugin source). Never copied into
// an adopter repo (no managed-stamp/refresh surface) — see docs/claugentic-DECISIONS.md → Plugin identity & distribution.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps dates AFTER the run —
// the script returns no timestamps). Only the tool primitives `agent()`/`parallel()`/
// `phase()`/`log()`/`args`. Pure decision logic lives in the marked `// --- helpers ---` block
// and is unit-tested by tests/workflows/audit.test.mjs (extract-and-eval), so the prose->script
// move tests the judgment, not just inspects it.
//
// The headline guarantee this script makes mechanical: exactly ONE finding-verifier per
// surviving finding (the prose's "re-check every finding" claim), with the cross-model judge
// pinned as a literal `model:` parameter.

export const meta = {
  name: "audit",
  description:
    "Audit pipeline (FIND -> PRUNE -> VERIFY) as a Workflow script: lens fan-out per (module x dir) cell at the dialed depth, coded dedup, synthesis self-review prune (the test-baseline item never pruned), exactly one finding-verifier per surviving finding (judge-pinned cross-model), deterministic budget cap + resume. quick/standard/thorough — thorough adds a whole-scope blind-spot sweep (FIND) and an adversarial yagni-sentinel prune (PRUNE). Returns the rendered backlog fence body (renderBacklogFence) for the skill to write between its backlog fence markers.",
};

// --- helpers ---
// Pure functions only — they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The judge model, defined ONCE (single source of truth). `opus` is the MOST-CAPABLE tier
// alias — it auto-resolves to the current top model, never a frozen version; change here (and
// the agents' `model:` frontmatter) if the top tier is ever renamed. Judges run the most
// capable available model; review independence is of role + clean context, not of model. The
// RUNNING AS / same-model tag (below) stays an honest per-run model-relationship reporter.
const MODELS = { judge: "opus" };

// Bundled agents resolve only as `claugentic-dev-harness:<agent>` for an installed adopter
// (bare names resolve only when dogfooded with project-local .claude/agents/). Namespace every
// custom-agent spawn; built-ins (general-purpose, …) stay bare. Pure → unit-tested.
const nsAgent = (name) => `claugentic-dev-harness:${name}`;

// The verbatim same-model disclosure tag. Defined once; never reconstructed by hand at a call
// site, so the wording cannot drift (honesty trust surface). Copied verbatim from verify.js.
const SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED disclosure tag — the THIRD state, distinct from SAME_MODEL_TAG. When a
// judge's self-reported family can't be recognized, the run is reported as unresolved (the
// conservative same-model trust floor still holds — no cross-model claim) rather than ASSERTED to
// be same-model fact. Defined once so the wording cannot drift (honesty trust surface). Copied
// byte-identical across the workflow scripts (cross-script drift pin).
const UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run — no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

// The recognized model families — the ONE named source the modelFamily regex derives from (single
// source of truth: a new family is added HERE, never in a hand-built regex). Copied byte-identical
// across the workflow scripts (cross-script drift pin).
const KNOWN_FAMILIES = ["fable", "opus", "sonnet", "haiku"];

// The dial -> depth ladder (one map, complete for all three notches). The ALLOWED-dial set is
// the boundary check (validateArgs); the map itself is total so depthForDial never returns
// undefined for a valid dial.
const DEPTH_FOR_DIAL = { quick: "focused", standard: "deep", thorough: "exhaustive" };

// ── Product-gap (criteria) mode — an args mode, NOT a fork (plan 0012, Slice 6) ──
// When args carry `criteria` (a product-spec's acceptance-criteria array) instead of modules×dirs,
// the SAME FIND -> PRUNE -> VERIFY pipeline runs with the criteria as the lens source: one cell per
// criterion. A second script would duplicate the dedup/budget/resume/verify machinery (DRY) — so
// the only additive surface is this frozen-schema validator + cellsFromCriteria + a criterion-lens
// prompt, plus one control-flow branch. The criteria list (not a dial) bounds FIND; lens depth is
// fixed at `deep`; the status-block level value is `gap`.
//
// The FROZEN acceptance-criteria schema — field names exact, may NEVER drift. Single source of
// truth: docs/claugentic-PRODUCT_SPEC_TEMPLATE.md embeds the same schema for humans; the runtime semantics
// are owned by qa.js (runtime). Here gap mode reads them
// STATICALLY against the code — it does NOT run the app (that is qa.js's job).
const CRITERIA_KEYS = ["id", "feature", "flow", "expect", "states", "check"];
const CRITERIA_CHECKS = ["e2e", "api", "manual"];
const CRITERIA_STATES = ["empty", "loading", "error"];
// The status-block level for a gap run (parallels `quick`/`standard`/`thorough` as the level word).
const GAP_LEVEL = "gap";

// The dials this script SUPPORTS end-to-end. All three notches are scripted: `thorough` adds the
// blind-spot sweep (FIND) and the adversarial yagni-sentinel prune (PRUNE). The boundary rejects
// any unknown dial with a message naming what's supported.
const SUPPORTED_DIALS = ["quick", "standard", "thorough"];

// The class of the script-synthesized "establish a test baseline" item. A finding with this
// findingKey can NEVER be pruned (applyPrune enforces it) — a partial/right-sized audit must
// never green-light an unguarded refactor.
const TEST_BASELINE_CLASS = "missing-test-baseline";

// The whole-scope blind-spot sweep, modeled as a single pseudo-cell so it participates in
// maxCellsPerRun, the done/pending lists, and resume exactly like any (module × dir) cell. It is
// appended LAST (after the prioritized module cells) at `thorough` only, runs once per audit, and
// a capped run defers it to the resume run like any overflow cell. Module slug `blindspot`,
// scope-marker dir `(scope)` — a fixed, never-a-real-dir token.
function cellKey(moduleName, dir) {
  return `${moduleName}×${dir}`;
}

// Derived via cellKey so the separator has exactly one definition.
const BLINDSPOT_CELL = cellKey("blindspot", "(scope)");

// The verbatim 2-line "how to read this" legend — the fence's single source of truth for the tag
// + verification glossary (the most-read trust statement carries the not-a-guarantee / cross-model
// caveat). Defined once here; renderBacklogFence emits it verbatim so it cannot drift.
const LEGEND =
  "`refactor` = tidy without changing behavior · `capability-upgrade` = add/upgrade a technology · `dependency-health` = update/patch dependencies · `bug` = fix wrong behavior · `feature` = new behavior.\n" +
  "`(checked against the code)` = a separate agent re-read the code and couldn't refute it · `(could not confirm independently — model's assertion)` = still just the model's claim · `(⚠ not yet verified — re-run to confirm)` = budget ran out before checking — each surfaced finding is re-checked by a separate clean-context agent that never saw the finder's reasoning — a reduction of rubber-stamping risk, not a mechanical guarantee.";

// The architecturally-sound terminal signal — emitted as the recommended-starting-point IFF Tiers
// 1 and 2 both come back empty (the explicit "stop" signal). Verbatim; the PARTIAL covered-cells
// scoping clause is appended by the renderer at run time.
const TERMINAL_SIGNAL =
  "Sound on the audited dimensions — what remains is optional polish; you don't need to keep re-auditing.";

// The verbatim closing "how to start" line — the user's always-present go-button. Defined once so
// the wording cannot drift.
const GO_BUTTON =
  "To start anything — a backlog item or a brand-new project — just tell the agent in plain English what you want (e.g. 'Let's do Tier-1 item 1' or 'I want to build X'). It will ask you questions (Discuss), then write a plan and spec for you to approve before any code. For a backlog item, the go-button is **`/claugentic-dev-harness:build`** — point it at one item ('build Tier-1 item 1') and it drives the whole reviewed pipeline for you, pausing only at the spec (before any code) and before anything irreversible.";

// The date placeholder the renderer leaves in the status line — the script has no clock, so the
// orchestrator replaces this token with today's date after the run (Phase 3 file mechanics).
const DATE_PLACEHOLDER = "{{DATE}}";

// The verbatim verification phrase per state — the inline tag every item carries (the verdict→tag
// map). Defined once; renderItem emits exactly one, by item.verification.state.
const VERIFICATION_PHRASE = {
  verified: "(checked against the code)",
  unconfirmed: "(could not confirm independently — model's assertion)",
  deferred: "(⚠ not yet verified — re-run to confirm)",
};

// Validate ONE acceptance criterion against the FROZEN schema. Returns an error string naming the
// offending criterion id (or its array index when the id itself is missing/blank) and the exact
// problem, or null when valid. Used by both validateArgs (boundary) and cellsFromCriteria (the
// fail-loud throw at enumeration). The rule is strict-exact: the six frozen keys and ONLY those.
function validateCriterion(criterion, index) {
  const at =
    criterion && typeof criterion.id === "string" && criterion.id.length > 0
      ? `criterion '${criterion.id}'`
      : `criterion at index ${index}`;
  if (!criterion || typeof criterion !== "object" || Array.isArray(criterion)) {
    return `${at}: must be an object`;
  }
  const keys = Object.keys(criterion);
  const extra = keys.filter((k) => !CRITERIA_KEYS.includes(k));
  const missing = CRITERIA_KEYS.filter((k) => !keys.includes(k));
  if (extra.length > 0) {
    return `${at}: unexpected key(s) ${JSON.stringify(extra)} — the frozen schema is exactly ${JSON.stringify(CRITERIA_KEYS)}`;
  }
  if (missing.length > 0) {
    return `${at}: missing key(s) ${JSON.stringify(missing)} — the frozen schema is exactly ${JSON.stringify(CRITERIA_KEYS)}`;
  }
  if (typeof criterion.id !== "string" || criterion.id.length === 0) {
    return `${at}: id must be a non-empty string`;
  }
  if (typeof criterion.feature !== "string" || criterion.feature.length === 0) {
    return `${at}: feature must be a non-empty string`;
  }
  if (!Array.isArray(criterion.flow) || criterion.flow.length === 0 || !criterion.flow.every((s) => typeof s === "string" && s.length > 0)) {
    return `${at}: flow must be a non-empty array of non-empty strings`;
  }
  if (!Array.isArray(criterion.expect) || criterion.expect.length === 0 || !criterion.expect.every((s) => typeof s === "string" && s.length > 0)) {
    return `${at}: expect must be a non-empty array of non-empty strings`;
  }
  if (!Array.isArray(criterion.states) || !criterion.states.every((s) => CRITERIA_STATES.includes(s))) {
    return `${at}: states must be an array, each entry one of ${JSON.stringify(CRITERIA_STATES)} (may be empty)`;
  }
  if (typeof criterion.check !== "string" || !CRITERIA_CHECKS.includes(criterion.check)) {
    return `${at}: check must be one of ${JSON.stringify(CRITERIA_CHECKS)}`;
  }
  return null;
}

// Validate the args contract at the boundary (fail loud — the caller throws on a non-empty
// list). Returns every shape error; empty array = valid. TWO mutually-exclusive arg modes:
//   * STANDARD (modules×dirs): the dial must be one of quick|standard|thorough; modules + scopeDirs
//     required.
//   * CRITERIA (product-gap): `args.criteria` present — a non-empty array, each criterion valid
//     against the frozen schema with a UNIQUE id; modules/scopeDirs/dial are NOT required (the
//     criteria list bounds FIND, depth is fixed at `deep`, level is `gap`). `excludeSet`,
//     `maxCellsPerRun`, `builderFamily`, `doneCells`, `deferredFindings` apply identically.
function validateArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return ["args must be an object"];
  }
  if (args.criteria !== undefined) {
    return validateCriteriaArgs(args);
  }
  if (typeof args.dial !== "string" || !SUPPORTED_DIALS.includes(args.dial)) {
    errors.push(
      `dial '${args.dial}' is not supported — supported dials are ${SUPPORTED_DIALS.join("/")}`,
    );
  }
  if (!Array.isArray(args.modules) || args.modules.length === 0) {
    errors.push("modules is required (non-empty array of standards-module names)");
  } else if (!args.modules.every((m) => typeof m === "string" && m.length > 0)) {
    errors.push("modules must be an array of non-empty strings");
  }
  if (!Array.isArray(args.scopeDirs) || args.scopeDirs.length === 0) {
    errors.push("scopeDirs is required (non-empty array of prioritized directories)");
  } else if (!args.scopeDirs.every((d) => typeof d === "string" && d.length > 0)) {
    errors.push("scopeDirs must be an array of non-empty strings");
  }
  errors.push(...validateSharedArgs(args));
  return errors;
}

// The boundary checks both arg modes share (single source of truth — DRY): excludeSet,
// maxCellsPerRun, doneCells, deferredFindings, builderFamily. Returns every error; empty = valid.
function validateSharedArgs(args) {
  const errors = [];
  if (args.excludeSet !== undefined && !Array.isArray(args.excludeSet)) {
    errors.push("excludeSet, when provided, must be an array of strings");
  }
  if (
    typeof args.maxCellsPerRun !== "number" ||
    !Number.isInteger(args.maxCellsPerRun) ||
    args.maxCellsPerRun <= 0
  ) {
    errors.push("maxCellsPerRun is required (positive integer — the deterministic cap)");
  }
  if (args.doneCells !== undefined && !Array.isArray(args.doneCells)) {
    errors.push("doneCells, when provided, must be an array of cell keys");
  }
  if (args.deferredFindings !== undefined && !Array.isArray(args.deferredFindings)) {
    errors.push("deferredFindings, when provided, must be an array of findings");
  }
  if (args.priorItems !== undefined && !Array.isArray(args.priorItems)) {
    errors.push("priorItems, when provided, must be an array (the prior run's resolved items — verdicts persist)");
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.length === 0) {
    errors.push("builderFamily is required (non-empty string — the orchestrator's model family)");
  }
  return errors;
}

// Validate the CRITERIA (product-gap) arg mode. `args.criteria` must be a non-empty array of
// frozen-schema-valid criteria with UNIQUE ids; the shared boundary checks apply identically. The
// standard modules/scopeDirs/dial fields are NOT required (the criteria list bounds FIND).
function validateCriteriaArgs(args) {
  const errors = [];
  if (!Array.isArray(args.criteria) || args.criteria.length === 0) {
    errors.push("criteria is required (non-empty array of acceptance criteria) in product-gap mode");
  } else {
    const seen = new Set();
    args.criteria.forEach((criterion, i) => {
      const err = validateCriterion(criterion, i);
      if (err) {
        errors.push(err);
        return;
      }
      if (seen.has(criterion.id)) {
        errors.push(`criterion '${criterion.id}': duplicate id — ids must be unique`);
      }
      seen.add(criterion.id);
    });
  }
  errors.push(...validateSharedArgs(args));
  return errors;
}

// Enumerate the gap-mode pending cells: ONE cell per criterion, keyed by its (unique) id, in spec
// order, MINUS any cell already in doneCells (never re-enumerated — the same resume contract as the
// standard mode, with criterion ids as the cells). Each returned cell carries the criterion object
// so the FIND fan-out can build a per-criterion lens prompt without a second lookup. Fails loud
// (throws naming the offending id/key) on a criterion that violates the frozen schema or on an
// empty list — the boundary already validated, but this keeps the helper independently safe.
function cellsFromCriteria(criteria, doneCells) {
  if (!Array.isArray(criteria) || criteria.length === 0) {
    throw new Error("cellsFromCriteria: criteria must be a non-empty array");
  }
  const done = new Set(Array.isArray(doneCells) ? doneCells : []);
  const seen = new Set();
  const cells = [];
  criteria.forEach((criterion, i) => {
    const err = validateCriterion(criterion, i);
    if (err) {
      throw new Error(`cellsFromCriteria: ${err}`);
    }
    if (seen.has(criterion.id)) {
      throw new Error(`cellsFromCriteria: duplicate criterion id '${criterion.id}' — ids must be unique`);
    }
    seen.add(criterion.id);
    if (!done.has(criterion.id)) {
      cells.push({ key: criterion.id, criterion });
    }
  });
  return cells;
}

// The dial -> depth map (assumes a validated dial; total over the three notches).
function depthForDial(dial) {
  return DEPTH_FOR_DIAL[dial];
}

// Map a validated module name to its standards doc path (assumes validated input).
function modulePath(moduleName) {
  return `docs/claugentic-standards/${moduleName}.md`;
}

// The exact cell-key token format the fence's done-cells / pending-cells lists carry — this is
// the resume contract with the SKILL. `<module>x<dir>` (a literal multiplication sign).

// Enumerate the pending cells INTERLEAVED — round-robin across lenses, priority dirs INNER
// (dir-major): `m0×d0, m1×d0, …, mK×d0, m0×d1, m1×d1, …`. The loop nesting is dir OUTER, module
// INNER — a pure function of input order (no Set-iteration / sort dependence), so re-enumeration is
// deterministic and stable: the SAME (modules, scopeDirs, doneCells, dial) always yield the SAME
// ordered remainder. That stability is the resume contract — doneCells is a SET the next run
// subtracts, safe ONLY because the order is reproducible. The interleave is the lens-coverage fix:
// a budget-limited prefix (applyCellBudget's slice(0,N)) now covers EVERY lens's TOP dir before any
// lens's second dir (broad-then-deep), so when maxCellsPerRun ≥ lens count every configured lens
// gets ≥1 cell — starvation is STRUCTURALLY impossible at a sane budget (no separate floor pass; the
// ordering IS the floor). MINUS any cell already in doneCells (never re-enumerated). At `thorough`,
// the whole-scope BLINDSPOT_CELL is appended STRICTLY LAST (after all real cells) when not already
// done — so the sweep participates in the cap, the done/pending lists, and resume exactly like any
// cell, and is the last cell deferred under a tight budget. Returns ordered cell keys.
function enumerateCells(modules, scopeDirs, doneCells, dial) {
  const done = new Set(Array.isArray(doneCells) ? doneCells : []);
  const cells = [];
  for (const dir of scopeDirs) {
    for (const moduleName of modules) {
      const key = cellKey(moduleName, dir);
      if (!done.has(key)) {
        cells.push(key);
      }
    }
  }
  if (dial === "thorough" && !done.has(BLINDSPOT_CELL)) {
    cells.push(BLINDSPOT_CELL);
  }
  return cells;
}

// Split the ordered pending cells against the per-run cap: the first N run this pass, the rest
// overflow to a resume run. The single deterministic cap (the platform `budget` primitive, where
// supported, is a backstop only — never the resume contract).
function applyCellBudget(cells, maxCellsPerRun) {
  return {
    run: cells.slice(0, maxCellsPerRun),
    overflow: cells.slice(maxCellsPerRun),
  };
}

// Parse a cell key back into its module + dir parts (split on the first multiplication sign;
// dirs may themselves contain one, so only the first separator is structural).
function parseCellKey(key) {
  const i = key.indexOf("×");
  if (i < 0) {
    return { module: key, dir: "" };
  }
  return { module: key.slice(0, i), dir: key.slice(i + 1) };
}

// Group this run's cells into one batch per module over its scoped dirs (the fan-out unit — one
// lens-reviewer per module batch). Preserves first-seen module order; dirs in cell order.
function groupByModule(runCells) {
  const byModule = new Map();
  for (const key of runCells) {
    const { module, dir } = parseCellKey(key);
    if (!byModule.has(module)) {
      byModule.set(module, { module, dirs: [], cells: [] });
    }
    const batch = byModule.get(module);
    batch.dirs.push(dir);
    batch.cells.push(key);
  }
  return [...byModule.values()];
}

// Per-lens coverage — the structural answer to "did every configured lens speak?" (prong #4). For
// each configured module (in config order) classify its state and finding count, distinguishing the
// THREE honest outcomes a reader must tell apart before prioritizing:
//   * ran-clean  — the lens RAN (none of its cells are pending) and found 0 findings (an explicit
//                  CLEAN, not silence) → { state: "ran-clean", findings: 0 }
//   * ran-found  — the lens ran and contributed N findings → { state: "ran-found", findings: N }
//   * pending    — at least one of the lens's cells is still pending (budget-deferred or a failed
//                  batch) so the lens NEVER fully ran → { state: "pending", findings: N } (N is
//                  whatever its run cells did surface — never claimed clean while a cell is pending)
// A lens is "pending" if ANY of its (module × dir) cells sits in pendingCells — the same ran-vs-unrun
// honesty verify.js's coverageGaps enforces (never report a partial sweep as a clean lens). The
// per-lens count is derived from the kept findings' sourceModule (the module doc path), so it counts
// what actually reached the backlog after dedup/prune/verify — a CLEAN lens is one that ran and left
// nothing, distinct from a never-run lens that left nothing because it never looked. Pure → unit-tested.
function lensCoverage(modules, pendingCells, findings) {
  const pending = new Set(Array.isArray(pendingCells) ? pendingCells : []);
  const counts = new Map();
  for (const finding of Array.isArray(findings) ? findings : []) {
    const src = finding && finding.sourceModule != null ? finding.sourceModule : null;
    if (src == null) {
      continue;
    }
    counts.set(src, (counts.get(src) || 0) + 1);
  }
  return (Array.isArray(modules) ? modules : []).map((moduleName) => {
    const path = modulePath(moduleName);
    const findingCount = counts.get(path) || 0;
    const hasPendingCell = [...pending].some((cell) => parseCellKey(cell).module === moduleName);
    const state = hasPendingCell ? "pending" : findingCount > 0 ? "ran-found" : "ran-clean";
    return { module: moduleName, state, findings: findingCount };
  });
}

// Normalize an issue-class string: lowercase, trim, collapse internal whitespace to single
// hyphens. The deterministic dedup identity is derived from this (synonym slugs that differ
// after normalization stay distinct — semantic dedup is the synthesis agent's job).
function normalizeIssueClass(s) {
  return String(s == null ? "" : s)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-");
}

// The dedup key AND the finding's id: the normalized issueClass. Two findings of the same KIND
// of problem collide regardless of location; distinct classes at one file:line stay separate.
function findingKey(finding) {
  return normalizeIssueClass(finding && finding.issueClass);
}

// Merge same-key findings across lenses: union of `locations` (the "recurs in N files" roll-up),
// WEAKEST confidence wins (any `judgment` member => merged finding is `judgment`, never
// upgraded), keep the first concrete claim/fix. Distinct classes stay separate. Preserves
// first-seen order. Each merged finding carries its computed `findingKey`.
function dedupFindings(findings) {
  const byKey = new Map();
  for (const finding of findings) {
    const key = findingKey(finding);
    const incomingLocations = Array.isArray(finding.locations) ? finding.locations : [];
    if (!byKey.has(key)) {
      byKey.set(key, {
        ...finding,
        findingKey: key,
        locations: [...incomingLocations],
      });
      continue;
    }
    const merged = byKey.get(key);
    for (const loc of incomingLocations) {
      if (!merged.locations.includes(loc)) {
        merged.locations.push(loc);
      }
    }
    if ((merged.fix == null || merged.fix === "") && finding.fix != null && finding.fix !== "") {
      merged.fix = finding.fix;
    }
    if (
      (merged.claimTechnical == null || merged.claimTechnical === "") &&
      finding.claimTechnical != null &&
      finding.claimTechnical !== ""
    ) {
      merged.claimTechnical = finding.claimTechnical;
    }
    if (
      (merged.claimPlain == null || merged.claimPlain === "") &&
      finding.claimPlain != null &&
      finding.claimPlain !== ""
    ) {
      merged.claimPlain = finding.claimPlain;
    }
    // Weakest confidence wins: a `judgment` member downgrades the merged finding; once
    // judgment, it never upgrades back to deterministic.
    if (finding.confidence === "judgment") {
      merged.confidence = "judgment";
    }
  }
  return [...byKey.values()];
}

// Apply the synthesis cut-list — drops every cut key EXCEPT a finding whose findingKey ===
// TEST_BASELINE_CLASS (the script-enforced never-prune-the-test-baseline exception). A cut
// targeting the test-baseline item is silently ignored, not honored.
function applyPrune(findings, cuts) {
  const cutKeys = new Set(
    (Array.isArray(cuts) ? cuts : [])
      .map((c) => (c && c.findingKey != null ? normalizeIssueClass(c.findingKey) : null))
      .filter((k) => k !== null),
  );
  return findings.filter((finding) => {
    const key = findingKey(finding);
    if (key === TEST_BASELINE_CLASS) {
      return true; // never pruned, whatever the cut-list says
    }
    return !cutKeys.has(key);
  });
}

// Map module names -> doc paths for a lens prompt (assumes validated input).
function modulesToPaths(modules) {
  return modules.map(modulePath);
}

// Build the audit-scope lens prompt (per .claude/agents/lens-reviewer.md): the module path, the
// scoped dirs, the exclude-set, and the depth word. Audit-scope mode — there is NO diff.
function buildLensPrompt(moduleName, dirs, excludeSet, depth) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Audit-scope mode (no diff). Your lens is the standards module: ${modulePath(moduleName)}. ` +
    `Audit the existing code in this scope against that module's dimensions only. ` +
    `Scope (prioritized dirs/packages): ${JSON.stringify(dirs)}. ` +
    `Exclude-set (never read — deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: ${depth}. ` +
    `Return per-issue findings: issueClass, claimPlain, claimTechnical, locations (file:line list), ` +
    `fix, confidence (deterministic|judgment).`
  );
}

// Build the product-gap lens prompt for ONE acceptance criterion (criteria mode). The lens reads
// the implementation STATICALLY against this criterion — it does NOT run the app (runtime checking
// is qa.js's job; the prompt says so) — and reports missing / partial / diverging behavior per flow
// step, expectation, and required state, in the SAME finding shape as buildLensPrompt so the
// findings join the unchanged dedup -> prune -> verify path. The criterion id rides into issueClass
// guidance so a finding cites which criterion it came from. Depth is fixed at `deep`.
function buildCriterionLensPrompt(criterion, excludeSet) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Product-gap mode (intent vs implementation — STATIC code reading; do NOT run the app — ` +
    `runtime checking is the QA workflow's job). Your lens is ONE acceptance criterion from the ` +
    `product spec; check whether the implementation delivers it. Criterion: ${JSON.stringify(criterion)}. ` +
    `Locate the implementing code via docs/claugentic-ARCHITECTURE_TREE.md (the file index), then READ it ` +
    `statically. For each flow step, each expectation in 'expect', and each required state in ` +
    `'states', report whether the code delivers it — flag promised-but-missing (the behavior has no ` +
    `implementation) and diverges-from-spec (the implementation contradicts the promise). A 'manual' ` +
    `check still gets a static read for an obvious missing surface, but a human owns the verdict. ` +
    `Exclude-set (never read — deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: deep. ` +
    `Return per-issue findings: issueClass (prefix with the criterion id '${criterion.id}'), ` +
    `claimPlain, claimTechnical, locations (file:line list), fix, confidence (deterministic|judgment).`
  );
}

// Build the whole-scope blind-spot sweep prompt (`thorough` only — per
// .claude/agents/blindspot-reviewer.md): no single module, the whole scope, red-team posture,
// always exhaustive depth. It FINDS only; its findings carry `issueClass` like a lens return and
// join the same dedupFindings path with no special handling.
function buildBlindspotPrompt(scopeDirs, excludeSet) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Audit-scope mode (no diff). You have NO single standards module — your lens is the WHOLE ` +
    `audited scope. Red-team posture: a checklist-driven per-module review just ran over this ` +
    `scope — hunt what it would STRUCTURALLY miss (emergent architectural smells, integration ` +
    `gaps between components, cross-cutting concerns applied inconsistently, systemic issues that ` +
    `fall BETWEEN the per-module lenses). ` +
    `Scope (prioritized dirs/packages): ${JSON.stringify(scopeDirs)}. ` +
    `Exclude-set (never read — deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: exhaustive (you are a thorough-only finder). You FIND only — do NOT verify. ` +
    `Return per-issue findings in the SAME shape as a lens-reviewer: issueClass, claimPlain, ` +
    `claimTechnical, locations (file:line list), fix, confidence (deterministic|judgment).`
  );
}

// Build the adversarial yagni-sentinel prune prompt (`thorough` only — per
// .claude/agents/yagni-sentinel.md): the independent skeptic argues the kept consolidated finding
// set down from a clean context. Returns ONLY a cut-list; the script applies it via applyPrune
// (the TEST_BASELINE_CLASS protection holds on this second pass too).
function buildSentinelPrompt(keptFindings) {
  return (
    `You are the YAGNI sentinel. An audit has consolidated and pruned a finding set; argue it does ` +
    `TOO MUCH. Independently (clean context — you are NOT given the synthesis rationale) flag ` +
    `findings that are speculative, gold-plating, premature infrastructure, over-generalization, ` +
    `or scope creep — the marginal nice-to-haves that should NOT reach the backlog. Do NOT argue ` +
    `against genuinely warranted quality (real security, real edge-cases, real resilience). ` +
    `Return ONLY a cuts list of { findingKey, reason } for everything you would cut. ` +
    `Kept findings: ${JSON.stringify(keptFindings)}.`
  );
}

// Build the synthesis prompt: consolidate -> tier (1|2|3) + exactly one of the five tags +
// plain-English title/why/impact-effort per item -> a YAGNI right-size cut list with reasons
// (incl. "duplicate of <key>" cuts). ADD one missing-test-baseline Tier-1 item ONLY when the
// inputs show untested behavior-bearing code and none exists; NEVER manufacture a finding to
// fill a tier. This is the prose's quick/standard "synthesis self-review", delegated.
function buildSynthesisPrompt(dedupedFindings, modules, scopeDirs) {
  return (
    `Synthesis self-review of an audit. Consolidate these deduped findings into a tiered, tagged ` +
    `backlog set and right-size it (YAGNI — keep only findings with real impact; cut marginal ` +
    `nice-to-haves; never manufacture a finding to fill a tier). ` +
    `For each kept finding return: findingKey (the issueClass), tier (1|2|3), tag (exactly one of ` +
    `refactor|capability-upgrade|dependency-health|bug|feature), titlePlain, whyPlain, impactEffort. ` +
    `Return a cuts list of { findingKey, reason } for everything you drop (use reason "duplicate of <key>" ` +
    `for semantic duplicates the coded dedup missed). ` +
    `ADD one item with findingKey "${TEST_BASELINE_CLASS}" at tier 1 ONLY IF the audited code is ` +
    `behavior-bearing and untested and no test baseline exists — otherwise do not add it. ` +
    `Audited modules: ${JSON.stringify(modules)}. Scope: ${JSON.stringify(scopeDirs)}. ` +
    `Deduped findings: ${JSON.stringify(dedupedFindings)}.`
  );
}

// Build the finding-verifier's CLEAN-CONTEXT input. Returns ONLY the contract keys — the
// independence of .claude/agents/finding-verifier.md is preserved STRUCTURALLY: the builder
// cannot emit rationale/transcript fields (any extra fields on the finding are dropped here).
function buildVerifierInput(finding, excludeSet) {
  return {
    claimPlain: finding && finding.claimPlain != null ? finding.claimPlain : "",
    claimTechnical: finding && finding.claimTechnical != null ? finding.claimTechnical : "",
    locations: finding && Array.isArray(finding.locations) ? finding.locations : [],
    sourceModule:
      finding && finding.sourceModule != null
        ? finding.sourceModule
        : finding && Array.isArray(finding.modules) && finding.modules.length > 0
          ? finding.modules[0]
          : "",
    confidence: finding && finding.confidence != null ? finding.confidence : "judgment",
    excludeSet: Array.isArray(excludeSet) ? excludeSet : [],
  };
}

// Build the verifier prompt from the clean-context input (refute-first posture; demands the
// RUNNING AS self-report). NEVER includes the finder's rationale.
function buildVerifierPrompt(input) {
  return (
    `Independently REFUTE this single audit finding against the actual code (refute-first; ` +
    `clean context — you are NOT given the finder's rationale). ` +
    `Open your response with "RUNNING AS: <model family>" and report it in runningAs. ` +
    `Claim (plain): ${input.claimPlain}. Claim (technical): ${input.claimTechnical}. ` +
    `Locations: ${JSON.stringify(input.locations)}. Source module: ${input.sourceModule}. ` +
    `Finder's confidence label: ${input.confidence}. ` +
    `Exclude-set (never read): ${JSON.stringify(input.excludeSet)}. ` +
    `Return verdict (Verified|Refuted|Unconfirmed), evidence, plainLine.`
  );
}

// Normalize a self-reported model family to a canonical lowercase token. First KNOWN_FAMILIES
// match wins (the regex derives from that one named source — no second hand-built family list);
// empty / unknown → null (conservative — an unresolved family degrades to the trust floor, never
// to a false cross-model claim). Copied verbatim from verify.js.
function modelFamily(report) {
  if (typeof report !== "string") {
    return null;
  }
  const match = report.match(new RegExp(`(${KNOWN_FAMILIES.join("|")})`, "i"));
  return match ? match[1].toLowerCase() : null;
}

// The disclosure decision — THREE states, one rule (detection included). The distinction is
// between a MISSING self-report (the deliberate no-report / forced-respawn floor) and a PRESENT
// self-report that FAILED to resolve (a genuine "could not resolve the family"). Copied verbatim
// from verify.js (see there for the full state table).
function sameModelTag(builderFamily, judgeFamily) {
  const judgeReported = typeof judgeFamily === "string" && judgeFamily.trim().length > 0;
  if (!judgeReported) {
    return SAME_MODEL_TAG; // no judge self-report at all → the conservative same-model floor
  }
  const b = modelFamily(builderFamily);
  const j = modelFamily(judgeFamily);
  if (b === null || j === null) {
    return UNRESOLVED_FAMILY_TAG; // a present report could not be resolved → reported as unresolved
  }
  return b === j ? SAME_MODEL_TAG : null;
}

// Apply the verifier verdicts to the surviving findings. Mapping (the only representable states
// are verified / unconfirmed / deferred — NEVER a silent "checked"):
//   Verified   -> kept, verification.state = 'verified'   + evidence
//   Unconfirmed-> kept, verification.state = 'unconfirmed'
//   Refuted    -> dropped (counted in refutedCount; its only trace is the count)
//   no verdict -> kept, verification.state = 'deferred'   (budget ran out / verifier never ran)
// `results` is a parallel array aligned to `findings` (results[i] verifies findings[i]); a
// missing/null result is the deferred case (the verifier did not run).
function applyVerdicts(findings, results) {
  const kept = [];
  let refutedCount = 0;
  findings.forEach((finding, i) => {
    const result = Array.isArray(results) ? results[i] : undefined;
    const verdict = result && result.verdict ? result.verdict : null;
    if (verdict === "Refuted") {
      refutedCount += 1;
      return; // dropped — false positive caught before the backlog
    }
    let verification;
    if (verdict === "Verified") {
      verification = {
        state: "verified",
        evidence: result && result.evidence != null ? result.evidence : "",
        plainLine: result && result.plainLine != null ? result.plainLine : "",
      };
    } else if (verdict === "Unconfirmed") {
      verification = {
        state: "unconfirmed",
        evidence: result && result.evidence != null ? result.evidence : "",
        plainLine: result && result.plainLine != null ? result.plainLine : "",
      };
    } else {
      // No usable verdict — the verifier did not run (budget exhausted / null return).
      verification = {
        state: "deferred",
        evidence: "",
        plainLine: "not yet verified — re-run to confirm",
      };
    }
    kept.push({
      ...finding,
      verification,
      // The verifier's own self-report rides WITH the finding — verificationSummary must never
      // index a parallel results array (a Refuted finding's removal would misalign it; the
      // 2026-06-11 dogfood audit reproduced a false cross-model claim from exactly that).
      verifierRunningAs: result && result.runningAs != null ? result.runningAs : null,
    });
  });
  return { kept, refutedCount };
}

// Fold the verifier results into the run's verification summary. `crossModel` is true ONLY when
// EVERY verifier returned a confirming self-report of a different family (sameModelTag null for
// each AND every finding got a result) — the run claims cross-model only then; otherwise it
// carries the disclosure tag for WHY. The non-cross-model tag is now THREE-state: a present-but-
// UNRESOLVED verifier family yields UNRESOLVED_FAMILY_TAG (reported unresolved, never asserted
// same-model fact); a resolved-same (or missing-report) verifier yields SAME_MODEL_TAG. Any
// unresolved report taints the whole run's disclosure to UNRESOLVED. Counts the kept verification
// states + the refuted drops.
function verificationSummary(findings, refutedCount, builderFamily) {
  let verified = 0;
  let unconfirmed = 0;
  let deferred = 0;
  let allConfirmingDifferentFamily = findings.length > 0;
  let sawUnresolved = false;
  findings.forEach((finding) => {
    const v = finding && finding.verification ? finding.verification.state : null;
    if (v === "verified") verified += 1;
    else if (v === "unconfirmed") unconfirmed += 1;
    else deferred += 1;
    const reported = finding && finding.verifierRunningAs != null ? finding.verifierRunningAs : null;
    // A PRESENT non-empty report that does not resolve to a KNOWN family is the unresolved case —
    // distinct from a missing/empty report (a forced-respawn / no self-report) which stays the
    // same-model floor (the same missing-vs-present split sameModelTag uses).
    if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
      sawUnresolved = true;
    }
    if (reported === null || sameModelTag(builderFamily, reported) !== null) {
      allConfirmingDifferentFamily = false;
    }
  });
  const crossModel = allConfirmingDifferentFamily;
  return {
    verified,
    unconfirmed,
    deferred,
    refuted: refutedCount,
    crossModel,
    sameModelTag: crossModel ? null : sawUnresolved ? UNRESOLVED_FAMILY_TAG : SAME_MODEL_TAG,
  };
}

// The run's COMPLETE/PARTIAL status, derived from the pending-cell list (the resume contract).
function runStatus(pendingCells) {
  return Array.isArray(pendingCells) && pendingCells.length > 0 ? "PARTIAL" : "COMPLETE";
}

// Normalize the args boundary — copied verbatim from verify.js. A scriptPath invocation delivers
// `args` as a JSON STRING (observed runtime behavior, 2026-06-11); an inline script may receive
// the object itself. Accept both; an unparseable string fails loud — never a silent empty-args run.
function parseArgs(raw) {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new Error("audit args: not valid JSON (" + (e && e.message ? e.message : e) + ")");
    }
  }
  return raw;
}

// Structured-output schemas as JSON Schema object literals (no imports). The Workflow tool
// validates each agent's structured output against these at the tool-call layer.
const LENS_SCHEMA = {
  type: "object",
  required: ["lensVerdict", "findings"],
  properties: {
    lensVerdict: { type: "string", enum: ["CLEAN", "GAPS"] },
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["issueClass", "claimPlain", "claimTechnical", "locations", "fix", "confidence"],
        properties: {
          issueClass: { type: "string" },
          claimPlain: { type: "string" },
          claimTechnical: { type: "string" },
          locations: { type: "array", items: { type: "string" } },
          fix: { type: "string" },
          confidence: { type: "string", enum: ["deterministic", "judgment"] },
        },
      },
    },
  },
};

const SYNTHESIS_SCHEMA = {
  type: "object",
  required: ["items", "cuts"],
  properties: {
    items: {
      type: "array",
      items: {
        type: "object",
        required: ["findingKey", "tier", "tag", "titlePlain", "whyPlain", "impactEffort"],
        properties: {
          findingKey: { type: "string" },
          tier: { type: "integer", enum: [1, 2, 3] },
          tag: {
            type: "string",
            enum: ["refactor", "capability-upgrade", "dependency-health", "bug", "feature"],
          },
          titlePlain: { type: "string" },
          whyPlain: { type: "string" },
          impactEffort: { type: "string" },
        },
      },
    },
    cuts: {
      type: "array",
      items: {
        type: "object",
        required: ["findingKey", "reason"],
        properties: {
          findingKey: { type: "string" },
          reason: { type: "string" },
        },
      },
    },
  },
};

const VERIFIER_SCHEMA = {
  type: "object",
  required: ["runningAs", "verdict", "evidence", "plainLine"],
  properties: {
    runningAs: { type: "string" },
    verdict: { type: "string", enum: ["Verified", "Refuted", "Unconfirmed"] },
    evidence: { type: "string" },
    plainLine: { type: "string" },
  },
};

// The adversarial yagni-sentinel's cut-list schema (`thorough` PRUNE stage). It returns ONLY cuts
// (same { findingKey, reason } shape the synthesis cuts use) — the script applies them via the
// same applyPrune (TEST_BASELINE_CLASS still protected).
const SENTINEL_SCHEMA = {
  type: "object",
  required: ["cuts"],
  properties: {
    cuts: {
      type: "array",
      items: {
        type: "object",
        required: ["findingKey", "reason"],
        properties: {
          findingKey: { type: "string" },
          reason: { type: "string" },
        },
      },
    },
  },
};

// Apply the synthesis agent's tier/tag/plain-English item metadata onto a kept finding, by
// findingKey. A finding the synthesis did not annotate keeps conservative defaults (tier 2,
// refactor) — never silently dropped here (the cut-list is the only drop path, via applyPrune).
function applySynthesisItems(findings, items) {
  const byKey = new Map(
    (Array.isArray(items) ? items : []).map((it) => [normalizeIssueClass(it.findingKey), it]),
  );
  return findings.map((finding) => {
    const it = byKey.get(findingKey(finding));
    return {
      ...finding,
      tier: it && it.tier != null ? it.tier : 2,
      tag: it && it.tag != null ? it.tag : "refactor",
      titlePlain: it && it.titlePlain != null ? it.titlePlain : finding.claimPlain || "",
      whyPlain: it && it.whyPlain != null ? it.whyPlain : "",
      impactEffort: it && it.impactEffort != null ? it.impactEffort : "",
    };
  });
}

// Shape a kept+verified finding into the Phase-3 return item contract (the renderer in Slice 3b
// consumes this; 3a returns the structured object, the orchestrator renders the fence).
function toResultItem(finding) {
  return {
    findingKey: findingKey(finding),
    modules: Array.isArray(finding.modules)
      ? finding.modules
      : finding.sourceModule != null
        ? [finding.sourceModule]
        : [],
    tier: Number.isInteger(finding.tier) ? finding.tier : 2,
    tag: finding.tag,
    titlePlain: finding.titlePlain != null ? finding.titlePlain : "",
    claimTechnical: finding.claimTechnical != null ? finding.claimTechnical : "",
    locations: Array.isArray(finding.locations) ? finding.locations : [],
    whyPlain: finding.whyPlain != null ? finding.whyPlain : "",
    impactEffort: finding.impactEffort != null ? finding.impactEffort : "",
    confidence: finding.confidence != null ? finding.confidence : "judgment",
    verification: finding.verification,
  };
}

// ── Fence renderer (the backlog fence body's single source of truth) ──
// Pure string builders. Together they emit the COMPLETE inner fence body (NO markers, NO heading —
// those stay SKILL-owned): status line, legend, tiers most-urgent-first, recommended starting
// point, the closing go-button. {{DATE}} is a placeholder the orchestrator stamps after the run
// (the script has no clock). The format rules in skills/audit/SKILL.md Phase 3 point HERE as the
// source of truth — drift is now a unit-test failure, not a model-discipline failure.

// The status line — the resume contract's first line. Cell lists are the verbatim cellKey tokens
// from the result (done/pending), comma-joined inside [ ]. The date is the placeholder.
function renderStatusLine(result) {
  const done = Array.isArray(result.doneCells) ? result.doneCells : [];
  const pending = Array.isArray(result.pendingCells) ? result.pendingCells : [];
  return (
    `status: ${result.status} · level: ${result.level} · ` +
    `done-cells: [${done.join(", ")}] · pending-cells: [${pending.join(", ")}] · ` +
    `date: ${DATE_PLACEHOLDER}`
  );
}

// One verification phrase per item, by state (verbatim — the inline trust tag). An unknown/missing
// state degrades to the deferred phrase (honest — never silently "checked").
function verificationPhrase(state) {
  return VERIFICATION_PHRASE[state] || VERIFICATION_PHRASE.deferred;
}

// The technical-finding line: the claim + its locations. A merged systemic finding (>1 location)
// reads "recurs in N files: …"; a single location reads inline; no location is honestly omitted.
function renderLocations(locations) {
  const locs = Array.isArray(locations) ? locations : [];
  if (locs.length === 0) {
    return "";
  }
  if (locs.length === 1) {
    return ` (${locs[0]})`;
  }
  return ` (recurs in ${locs.length} files: ${locs.join(", ")})`;
}

// Render one backlog item — the exact item format (SKILL Phase 3): title, exactly one tag, the
// inline verification phrase, the dual-layer technical+plain finding, impact+effort, and (when
// verified) the evidence snippet attached to the technical finding.
function renderItem(item) {
  const state = item.verification ? item.verification.state : "deferred";
  const phrase = verificationPhrase(state);
  const evidence =
    state === "verified" && item.verification && item.verification.evidence
      ? ` Evidence: ${item.verification.evidence}.`
      : "";
  const lines = [];
  lines.push(`- **${item.titlePlain}** — \`${item.tag}\` *${phrase}*`);
  lines.push(
    `  - Technical: ${item.claimTechnical}${renderLocations(item.locations)}.${evidence}`,
  );
  lines.push(`  - Plain English: ${item.whyPlain}`);
  lines.push(`  - Impact/effort: ${item.impactEffort}`);
  return lines.join("\n");
}

// Render one tier section (most-urgent-first ordering is the caller's). An empty tier carries an
// explicit "(empty)" note rather than a silent gap.
function renderTier(heading, items) {
  const body =
    items.length > 0 ? items.map(renderItem).join("\n") : "_(empty)_";
  return `### ${heading}\n\n${body}`;
}

// The recommended-starting-point line. When Tiers 1+2 are BOTH empty it IS the terminal "sound"
// signal (with the covered-cells scoping clause appended on a PARTIAL run); otherwise it points at
// the first Tier-1 item, else the first Tier-2 item.
function renderRecommendation(tier1, tier2, status) {
  if (tier1.length === 0 && tier2.length === 0) {
    const scope =
      status === "PARTIAL"
        ? " (scoped to the cells covered this run — re-run to finish the rest)"
        : "";
    return `**Recommended starting point:** ${TERMINAL_SIGNAL}${scope}`;
  }
  const first = tier1.length > 0 ? tier1[0] : tier2[0];
  return `**Recommended starting point:** ${first.titlePlain}.`;
}

// The per-lens coverage line — the structural "did every lens speak?" report (prong #4). One line
// per configured lens, in config order, stating its state + finding count: a lens that RAN and found
// nothing reads "CLEAN" (an explicit 0, not silence); a lens that NEVER RAN (budget-deferred / failed
// batch) reads "did not run this pass — re-run to cover it" so a reader can tell ran-clean from
// never-ran before prioritizing. Renders nothing when no lensCoverage is present (gap mode / older
// results) — never a misleading empty header. The verdict-phrase map is the single source of truth.
const LENS_COVERAGE_PHRASE = {
  "ran-found": (n) => `${n} finding${n === 1 ? "" : "s"}`,
  "ran-clean": () => "CLEAN (ran, found nothing)",
  pending: (n) =>
    n > 0
      ? `did not finish this pass (${n} so far) — re-run to cover it`
      : "did not run this pass — re-run to cover it",
};
function renderLensCoverage(lensCoverage) {
  const lenses = Array.isArray(lensCoverage) ? lensCoverage : [];
  if (lenses.length === 0) {
    return "";
  }
  const lines = lenses.map((l) => {
    const phrase = (LENS_COVERAGE_PHRASE[l.state] || LENS_COVERAGE_PHRASE.pending)(l.findings || 0);
    return `- \`${l.module}\`: ${phrase}`;
  });
  return `**Lens coverage** (did every lens speak?):\n${lines.join("\n")}`;
}

// The verification run-report line — driven by the result's verification block. Frames the dropped
// findings as a trust signal (a COUNT, never a list). When crossModel is false the parenthetical
// cross-model clause is REPLACED by the disclosure tag the summary computed — the THREE-state tag
// (SAME_MODEL_TAG for resolved-same, UNRESOLVED_FAMILY_TAG when a verifier family was unresolved),
// so an unresolved run never reads as asserted same-model fact (never both clauses).
function renderRunReport(verification) {
  const v = verification || {};
  const refuted = v.refuted != null ? v.refuted : 0;
  const verified = v.verified != null ? v.verified : 0;
  const unconfirmed = v.unconfirmed != null ? v.unconfirmed : 0;
  const deferred = v.deferred != null ? v.deferred : 0;
  const judgeClause = v.crossModel
    ? "(re-checked by a separate clean-context agent — a reduction of shared-blind-spot risk, not independence)"
    : v.sameModelTag != null
      ? v.sameModelTag
      : SAME_MODEL_TAG;
  return (
    `Re-checked every finding I surfaced against the code ${judgeClause}; ` +
    `dropped ${refuted} that couldn't be confirmed — ` +
    `verified ${verified} · unconfirmed ${unconfirmed} · deferred ${deferred}.`
  );
}

// Build the COMPLETE inner fence body from the structured result. Order: status line, legend,
// the three tiers (most-urgent-first), the recommended starting point, the per-lens coverage report
// (did every lens speak? — omitted when absent), the run report, the go-button. NO fence markers,
// NO heading (SKILL-owned). {{DATE}} stays a placeholder.
function renderBacklogFence(result) {
  const items = Array.isArray(result.items) ? result.items : [];
  const tier1 = items.filter((it) => it.tier === 1);
  const tier2 = items.filter((it) => it.tier === 2);
  const tier3 = items.filter((it) => it.tier === 3);
  const lensCoverageLine = renderLensCoverage(result.lensCoverage);
  const parts = [
    renderStatusLine(result),
    LEGEND,
    renderTier("Tier 1 — critical", tier1),
    renderTier("Tier 2 — important", tier2),
    renderTier("Tier 3 — polish", tier3),
    renderRecommendation(tier1, tier2, result.status),
    ...(lensCoverageLine ? [lensCoverageLine] : []),
    renderRunReport(result.verification),
    `*${GO_BUTTON}*`,
  ];
  return parts.join("\n\n");
}

// Resume honesty: a PARTIAL re-run regenerates the WHOLE fence from result.items, so the
// prior pass's RESOLVED findings (verified/unconfirmed — their verdicts persist, they are
// not re-verified) must be carried forward via args.priorItems and merged here. A finding
// re-surfaced by THIS run supersedes its prior copy (fresher verdict wins on findingKey).
// Without this merge the resumed fence silently dropped confirmed findings — the gap-mode
// smoke's verified Tier-1 (2026-06-12).
function mergePriorItems(currentItems, priorItems) {
  const current = Array.isArray(currentItems) ? currentItems : [];
  const prior = Array.isArray(priorItems) ? priorItems : [];
  const currentKeys = new Set(current.map((it) => it && it.findingKey).filter(Boolean));
  const carried = prior.filter(
    (it) => it && it.findingKey && !currentKeys.has(it.findingKey),
  ).map((it) => ({
    ...it,
    tier: Number.isInteger(it.tier) ? it.tier : 2,
  }));
  return [...carried, ...current];
}
// --- end helpers ---

// Spawn a judge (finding-verifier) with the cross-model `model:` pin; one respawn without it on
// failure (the result then can't confirm a different family -> the run carries the same-model
// tag); on a second failure the finding is marked deferred (never a silent skip). The verifier
// fan-out scales with findings, not files, so this stays cheap.
async function spawnVerifier(input) {
  const prompt = buildVerifierPrompt(input);
  const attempt = async (opts) => {
    try {
      return { out: await agent(prompt, opts) };
    } catch (e) {
      return { out: null, err: e && e.message ? e.message : String(e) };
    }
  };
  const first = await attempt({
    agentType: nsAgent("finding-verifier"),
    model: MODELS.judge,
    schema: VERIFIER_SCHEMA,
    label: `verify:${input.sourceModule}`,
    phase: "Verify",
  });
  if (first.out != null) {
    return first.out;
  }
  const second = await attempt({
    agentType: nsAgent("finding-verifier"),
    schema: VERIFIER_SCHEMA,
    label: `verify:${input.sourceModule}:respawn`,
    phase: "Verify",
  });
  if (second.out != null) {
    // Forced no-override respawn: drop the self-report so it can't claim a different family.
    return { ...second.out, runningAs: "" };
  }
  // Both attempts failed — mark the finding deferred (honest no-silent-skip).
  return null;
}

// ── Top-level control flow (Workflow scripts run in an async context; no module wrapper). ──

// Validate at the boundary — fail loud with the full error list.
const input = parseArgs(args);
{
  const errors = validateArgs(input);
  if (errors.length > 0) {
    throw new Error(`audit args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

// ARG MODE: criteria (product-gap) vs the standard modules×dirs sweep. The criteria list bounds
// FIND in gap mode (depth fixed at `deep`, level `gap`); the dial drives the standard mode.
const isGap = Array.isArray(input.criteria);
const dial = isGap ? GAP_LEVEL : input.dial;
const depth = isGap ? "deep" : depthForDial(input.dial);
const excludeSet = Array.isArray(input.excludeSet) ? input.excludeSet : [];
const doneCellsIn = Array.isArray(input.doneCells) ? input.doneCells : [];
const deferredFindings = Array.isArray(input.deferredFindings) ? input.deferredFindings : [];

// Enumerate this run's pending cells, then split against the per-run cap (the deterministic resume).
// In gap mode the cells ARE the criterion ids (one cell per criterion); in standard mode the cells
// are (module × dir) and `thorough` appends the whole-scope BLINDSPOT_CELL last. Either way the cap
// + done/pending lists drive resume identically. `batches` is the FIND fan-out unit (one lens call
// per batch): a module-over-its-dirs batch in standard mode, a single-criterion batch in gap mode.
let runCells;
let overflowCells;
let runHasBlindspot;
let batches;
if (isGap) {
  const gapCells = cellsFromCriteria(input.criteria, doneCellsIn);
  const split = applyCellBudget(gapCells, input.maxCellsPerRun);
  runCells = split.run.map((c) => c.key);
  overflowCells = split.overflow.map((c) => c.key);
  runHasBlindspot = false; // the blind-spot sweep is a standard-mode `thorough` stage; gap has none
  batches = split.run.map((c) => ({
    module: c.criterion.id,
    dirs: [],
    cells: [c.key],
    criterion: c.criterion,
  }));
} else {
  const pending = enumerateCells(input.modules, input.scopeDirs, doneCellsIn, input.dial);
  const split = applyCellBudget(pending, input.maxCellsPerRun);
  runCells = split.run;
  overflowCells = split.overflow;
  runHasBlindspot = runCells.includes(BLINDSPOT_CELL);
  const moduleCells = runCells.filter((c) => c !== BLINDSPOT_CELL);
  batches = groupByModule(moduleCells);
}
log(
  `audit ${isGap ? "mode=gap" : `dial=${dial}`} depth=${depth} — ${batches.length} ` +
    `${isGap ? "criterion" : "module"} batch(es) this run` +
    `${runHasBlindspot ? " + the blind-spot sweep" : ""}; ` +
    `${overflowCells.length} deferred to resume.`,
);

// --- FIND: one lens call per batch at the dialed depth, in parallel. In standard mode each batch is
// a `lens-reviewer` over a module's dirs; at `thorough` the whole-scope blind-spot sweep joins the
// SAME parallel() as one more task (it FINDS only). In gap mode each batch is a `lens-reviewer` over
// ONE acceptance criterion (static intent-vs-implementation read). ---
phase("Find");
// FIND-phase guard. The platform's parallel() already resolves a throwing thunk to null
// (it never rejects) — this wrapper makes the never-crash-the-run property LOCAL and
// auditable instead of resting on an out-of-repo tool contract; either way a failed batch
// returns null and its cells go pending (PARTIAL), never a crashed run.
async function guardedAgent(prompt, opts) {
  try {
    return await agent(prompt, opts);
  } catch (e) {
    log(`FIND batch failed (${opts && opts.label ? opts.label : "?"}): ${e && e.message ? e.message : e} — its cells go pending`);
    return null;
  }
}

const findTasks = batches.map((batch) => () =>
  guardedAgent(
    isGap
      ? buildCriterionLensPrompt(batch.criterion, excludeSet)
      : buildLensPrompt(batch.module, batch.dirs, excludeSet, depth),
    {
      agentType: nsAgent("lens-reviewer"),
      schema: LENS_SCHEMA,
      label: isGap ? `gap:${batch.module}` : `lens:${batch.module}`,
      phase: "Find",
    },
  ),
);
if (runHasBlindspot) {
  findTasks.push(() =>
    guardedAgent(buildBlindspotPrompt(input.scopeDirs, excludeSet), {
      agentType: nsAgent("blindspot-reviewer"),
      schema: LENS_SCHEMA,
      label: "blindspot:(scope)",
      phase: "Find",
    }),
  );
}
const findResults = await parallel(findTasks);

// A batch that errored (null return) sends its cells to pendingCells — never a silent skip; the
// run goes PARTIAL. Surviving batches contribute their findings, each tagged with its module.
const failedCells = [];
const rawFindings = [];
batches.forEach((batch, i) => {
  const r = findResults[i];
  if (!r || !Array.isArray(r.findings)) {
    log(`lens batch '${batch.module}' did not run (no usable return) — its cells go pending.`);
    for (const cell of batch.cells) {
      failedCells.push(cell);
    }
    return;
  }
  // In gap mode the batch source is the criterion id (not a standards-module path); in standard
  // mode it is the module's doc path. Each finding carries its source so the verifier and the
  // fence can cite it.
  const source = isGap ? `criterion ${batch.module}` : modulePath(batch.module);
  for (const finding of r.findings) {
    rawFindings.push({ ...finding, sourceModule: source, modules: [source] });
  }
});

// The blind-spot sweep's result is the LAST element of findResults (it was pushed last). It joins
// the same dedup -> prune -> verify path with no special handling — its findings carry issueClass
// like a lens return; sourceModule is the blindspot scope marker. A failed sweep sends the
// pseudo-cell to pending (logged), the run goes PARTIAL — never a silent skip.
if (runHasBlindspot) {
  const blindspotResult = findResults[findResults.length - 1];
  if (!blindspotResult || !Array.isArray(blindspotResult.findings)) {
    log("blind-spot sweep did not run (no usable return) — the (scope) pseudo-cell goes pending.");
    failedCells.push(BLINDSPOT_CELL);
  } else {
    for (const finding of blindspotResult.findings) {
      rawFindings.push({ ...finding, sourceModule: "blindspot", modules: ["blindspot"] });
    }
  }
}

// --- PRUNE: code dedup, then synthesis self-review, then applyPrune (test-baseline protected). ---
phase("Prune");
const dedupedFindings = dedupFindings(rawFindings);

// The synthesis "audited scope" framing is mode-aware (the consolidate/tier/tag logic is identical):
// standard mode passes the module doc paths + scopeDirs; gap mode passes the criterion ids + a
// fixed scope label (the gap run has no dir scope — the criteria ARE the scope).
const synthesisModules = isGap ? input.criteria.map((c) => c.id) : modulesToPaths(input.modules);
const synthesisScope = isGap ? ["product-gap: intent vs implementation"] : input.scopeDirs;

let synthesis = await agent(
  buildSynthesisPrompt(dedupedFindings, synthesisModules, synthesisScope),
  { agentType: nsAgent("architect-reviewer"), schema: SYNTHESIS_SCHEMA, label: "synthesis", phase: "Prune" },
);
if (!synthesis || !Array.isArray(synthesis.items)) {
  // Single-point seam: a null synthesis would discard the whole FIND sweep. Retry once
  // before the fail-loud terminal (the throw stays — never proceed without the prune).
  synthesis = await agent(
    buildSynthesisPrompt(dedupedFindings, synthesisModules, synthesisScope),
    { agentType: nsAgent("architect-reviewer"), schema: SYNTHESIS_SCHEMA, label: "synthesis:respawn", phase: "Prune" },
  );
}
if (!synthesis || !Array.isArray(synthesis.items)) {
  // The run cannot proceed honestly without the synthesis prune.
  throw new Error("audit prune: synthesis agent returned no usable items after a retry — cannot proceed.");
}

const annotated = applySynthesisItems(dedupedFindings, synthesis.items);
let survivors = applyPrune(annotated, synthesis.cuts);

// Surface a synthesized missing-test-baseline item if synthesis declared one and dedup/prune
// didn't already carry it (it is added to VERIFY like any finding).
if (
  synthesis.items.some((it) => normalizeIssueClass(it.findingKey) === TEST_BASELINE_CLASS) &&
  !survivors.some((f) => findingKey(f) === TEST_BASELINE_CLASS)
) {
  const baselineItem = synthesis.items.find(
    (it) => normalizeIssueClass(it.findingKey) === TEST_BASELINE_CLASS,
  );
  survivors.push({
    issueClass: TEST_BASELINE_CLASS,
    claimPlain: baselineItem.whyPlain || "Behavior-bearing code lacks a test baseline.",
    claimTechnical: baselineItem.titlePlain || "Establish a test baseline.",
    locations: [],
    confidence: "judgment",
    modules: ["docs/claugentic-standards/testing.md"],
    sourceModule: "docs/claugentic-standards/testing.md",
    tier: 1,
    tag: baselineItem.tag || "refactor",
    titlePlain: baselineItem.titlePlain || "Establish a test baseline",
    whyPlain: baselineItem.whyPlain || "",
    impactEffort: baselineItem.impactEffort || "",
  });
}

// --- PRUNE (thorough only): the adversarial yagni-sentinel sweep over the consolidated survivors
// — the independent skeptic argues the set down from a clean context, then applyPrune AGAIN (the
// TEST_BASELINE_CLASS protection holds on this second pass too). A thorough run that skipped its
// adversarial prune must NOT pretend it ran one: on a null sentinel after one retry, throw. On
// quick/standard this stage does not exist.
if (dial === "thorough") {
  let sentinel = await agent(buildSentinelPrompt(survivors), {
    agentType: nsAgent("yagni-sentinel"),
    schema: SENTINEL_SCHEMA,
    label: "sentinel",
    phase: "Prune",
  });
  if (!sentinel || !Array.isArray(sentinel.cuts)) {
    sentinel = await agent(buildSentinelPrompt(survivors), {
      agentType: nsAgent("yagni-sentinel"),
      schema: SENTINEL_SCHEMA,
      label: "sentinel:respawn",
      phase: "Prune",
    });
  }
  if (!sentinel || !Array.isArray(sentinel.cuts)) {
    throw new Error(
      "audit prune: the thorough adversarial yagni-sentinel returned no usable cut-list after a retry — a thorough run must not pretend it ran the adversarial prune.",
    );
  }
  survivors = applyPrune(survivors, sentinel.cuts);
}

// Re-checked findings include every survivor PLUS any deferredFindings from a prior run (fed
// straight to VERIFY — their prior tags don't exempt them from a fresh re-check this run).
// Resumed deferred findings never passed through applySynthesisItems, so default their
// tier/tag here — a tier-less item would silently vanish from the rendered tiers while the
// run-report still counted it (the 2026-06-11 thorough dogfood's verified Tier-1).
const normalizedDeferred = deferredFindings.map((f) => ({
  ...f,
  tier: Number.isInteger(f && f.tier) ? f.tier : 2,
  tag: f && typeof f.tag === "string" && f.tag.length > 0 ? f.tag : "refactor",
}));
const toVerify = [...survivors, ...normalizedDeferred];

// --- VERIFY: exactly ONE finding-verifier per finding, judge-pinned, in parallel. ---
phase("Verify");
const verifyTasks = toVerify.map((finding) => () =>
  spawnVerifier(buildVerifierInput(finding, excludeSet)),
);
const verifyResults = await parallel(verifyTasks);

const { kept, refutedCount } = applyVerdicts(toVerify, verifyResults);
// Observability: a verifier self-report that is present but does not resolve to a KNOWN family is
// LOGGED, never silently degraded — the disclosure becomes UNRESOLVED, not asserted same-model.
for (const finding of kept) {
  const reported = finding && finding.verifierRunningAs != null ? finding.verifierRunningAs : null;
  if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
    log(
      `audit: a finding-verifier self-reported an UNRECOGNIZED model family ` +
        `(${JSON.stringify(reported)}) — reported as unresolved, no cross-model claim made.`,
    );
  }
}
const summary = verificationSummary(kept, refutedCount, input.builderFamily);

// --- Assemble the structured result (the Phase-3 contract; no timestamps — the orchestrator
// stamps the date when it renders the fence). doneCells = input done ∪ this run's swept cells
// (the failed batches' cells stay pending); pendingCells = overflow ∪ failed.
const sweptCells = runCells.filter((c) => !failedCells.includes(c));
const doneCells = [...doneCellsIn, ...sweptCells];
const pendingCells = [...overflowCells, ...failedCells];
const items = mergePriorItems(kept.map(toResultItem), input.priorItems);

// Per-lens coverage (standard mode only — gap mode's "lenses" are criteria, not standards modules).
// Counts each configured lens's deduped-finding contribution and flags any lens whose cells are still
// pending (budget-deferred / failed batch) so the fence can confirm "did every lens speak?" — the
// prong-4 anti-starvation report (distinguishes ran-clean from never-ran). Derived from the deduped
// findings (the raw lens output after coded dedup, before synthesis prune) so it reflects what each
// lens actually surfaced, not what survived prioritization.
const lensCoverageReport = isGap
  ? undefined
  : lensCoverage(input.modules, pendingCells, dedupedFindings);

const result = {
  status: runStatus(pendingCells),
  // A COMPLETE cell sweep can still carry unverified findings — say so mechanically.
  verificationIncomplete: summary.deferred > 0,
  level: dial,
  depth,
  doneCells,
  pendingCells,
  items,
  refutedCount,
  verification: summary,
  ...(lensCoverageReport ? { lensCoverage: lensCoverageReport } : {}),
};

// The complete fence body the skill writes between the harness-audit:backlog markers (Phase 3 is
// now file mechanics: write this string, replace {{DATE}} with today's date). The format's single
// source of truth is renderBacklogFence + its unit tests — no free-hand prose, no drift.
return { ...result, renderedBacklog: renderBacklogFence(result) };
