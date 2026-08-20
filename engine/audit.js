// engine/audit.js -- the audit pipeline (FIND -> PRUNE -> VERIFY) as an executable Workflow script.
// All three notches are scripted: `quick` + `standard` run the per-module lens sweep; `thorough`
// adds a whole-scope blind-spot sweep (FIND) and an adversarial yagni-sentinel prune (PRUNE), both
// on the same dedup -> verify path. renderBacklogFence is the fence format's single source of truth.
//
// The headline guarantee this script makes MECHANICAL: exactly ONE finding-verifier per surviving
// finding (the prose's "re-check every finding" claim).
//
// Distribution: read-from-install-path -- adopters invoke `${CLAUDE_PLUGIN_ROOT}/engine/audit.js`;
// this repo dogfoods `./engine/audit.js`. Never copied into an adopter repo -- see
// docs/claugentic-DECISIONS.md -> Plugin identity & distribution.
//
// Sandbox constraints: NO imports, NO filesystem, NO wall-clock/randomness (the orchestrator stamps
// dates AFTER the run -- the script returns no timestamps). Only `agent()`/`parallel()`/`phase()`/
// `log()`/`args`. Pure decision logic lives in the marked helpers block, unit-tested by
// tests/workflows/audit.test.mjs (extract-and-eval).

export const meta = {
  name: "audit",
  description:
    "Audit pipeline (FIND -> PRUNE -> VERIFY) as a Workflow script: lens fan-out per (module x dir) cell at the dialed depth, coded dedup, synthesis self-review prune (the test-baseline item never pruned), exactly one finding-verifier per surviving finding, deterministic budget cap + resume. quick/standard/thorough -- thorough adds a whole-scope blind-spot sweep (FIND) and an adversarial yagni-sentinel prune (PRUNE). Returns the rendered backlog fence body (renderBacklogFence) for the skill to write between its backlog fence markers.",
};

// --- helpers ---
// Pure functions only -- no closure over tool primitives, so the harness can extract and eval this
// block standalone.

// The judge model, defined ONCE. It NAMES NO MODEL deliberately: naming one assumes the adopter can
// reach that tier, and a harness cannot promise a model it does not provision. A judge INHERITS the
// session's model -- want stronger judges, run the session stronger. Independence here is of ROLE
// and CLEAN CONTEXT, not of model; the RUNNING AS / same-model tag below discloses the relationship
// that actually resulted rather than assuming it away.
const MODELS = { judge: null };

// The bundled-agent namespace prefix -- the ONE source nsAgent adds and bareAgentType strips, so
// the two can never disagree. Copied byte-identical across the four scripts (drift pin).
const AGENT_NAMESPACE = "claugentic-dev-harness";

// Namespace every custom-agent spawn; built-ins (general-purpose, ...) stay bare. Namespaced is
// what the engine WRITES -- the spawn wrapper below derives the bare fallback. See verify.js.
const nsAgent = (name) => `${AGENT_NAMESPACE}:${name}`;

// Strip EVERY leading `<AGENT_NAMESPACE>:` prefix -- the D6 fallback target, DERIVED at runtime.
// Total and IDEMPOTENT; an unprefixed id comes back UNCHANGED, and "unchanged" IS the caller's
// "no fallback exists" signal. Copied byte-identical from verify.js (drift pin; full contract there).
function bareAgentType(agentType) {
  const prefix = `${AGENT_NAMESPACE}:`;
  let bare = typeof agentType === "string" ? agentType : "";
  while (bare.startsWith(prefix)) {
    bare = bare.slice(prefix.length);
  }
  return bare;
}

// The notice a namespace fallback logs before its single bare retry -- it states the trust boundary
// in the log: a namespace retry is NOT a model respawn. Copied byte-identical (drift pin).
function namespaceFallbackNotice(agentType, bare, err) {
  const detail = err && err.message ? err.message : String(err);
  return (
    `agent spawn '${agentType}' failed (${detail}) -- retrying ONCE as the bare name '${bare}' ` +
    `(project-local .claude/agents/ resolution). This is a NAMESPACE retry, not a model respawn: ` +
    `it consumes no respawn budget, keeps the same model options, and changes no cross-model claim.`
  );
}

// The verbatim same-model disclosure tag. Defined once, never rebuilt at a call site (honesty trust
// surface -- the wording cannot drift). Copied verbatim from verify.js.
const SAME_MODEL_TAG =
  "same-model review on this run -- the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED disclosure tag -- the THIRD state: an unrecognized judge family is
// REPORTED unresolved (the same-model trust floor holds, no cross-model claim), never ASSERTED as
// same-model fact. Honesty trust surface; copied byte-identical (drift pin).
const UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run -- no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

// The recognized model families -- the ONE source the modelFamily regex derives from: a new family
// is added HERE, never in a hand-built regex. Copied byte-identical (drift pin).
const KNOWN_FAMILIES = ["fable", "opus", "sonnet", "haiku"];

// The dial -> depth ladder, total over all three notches so depthForDial never returns undefined
// for a valid dial. The ALLOWED-dial set is the boundary check.
const DEPTH_FOR_DIAL = { quick: "focused", standard: "deep", thorough: "exhaustive" };

// -- Product-gap (criteria) mode -- an args MODE, not a fork (plan 0012, Slice 6) --
// With `criteria` instead of modules x dirs, the SAME FIND -> PRUNE -> VERIFY pipeline runs with the
// criteria as the lens source, one cell per criterion. A second script would duplicate the
// dedup/budget/resume/verify machinery (DRY), so the only additive surface is this frozen-schema
// validator + cellsFromCriteria + a criterion-lens prompt + one control-flow branch. The criteria
// list (not a dial) bounds FIND; depth is fixed `deep`; the status-block level is `gap`.
//
// The FROZEN acceptance-criteria schema -- field names exact, may NEVER drift.
// docs/claugentic-PRODUCT_SPEC_TEMPLATE.md embeds the same schema for humans; qa.js owns the RUNTIME
// semantics. Gap mode reads them STATICALLY against the code -- it does NOT run the app.
const CRITERIA_KEYS = ["id", "feature", "flow", "expect", "states", "check"];
const CRITERIA_CHECKS = ["e2e", "api", "manual"];
const CRITERIA_STATES = ["empty", "loading", "error"];
// The status-block level for a gap run (parallels `quick`/`standard`/`thorough` as the level word).
const GAP_LEVEL = "gap";

// The dials this script SUPPORTS end-to-end; `thorough` adds the blind-spot sweep (FIND) and the
// adversarial yagni-sentinel prune (PRUNE). The boundary rejects any unknown dial, naming these.
const SUPPORTED_DIALS = ["quick", "standard", "thorough"];

// The class of the script-synthesized "establish a test baseline" item. applyPrune enforces that a
// finding with this findingKey can NEVER be pruned -- a right-sized audit must never green-light an
// unguarded refactor.
const TEST_BASELINE_CLASS = "missing-test-baseline";

// The whole-scope blind-spot sweep is a single pseudo-cell, so it joins maxCellsPerRun, the
// done/pending lists and resume exactly like any (module x dir) cell: appended LAST at `thorough`
// only, once per audit. Module slug `blindspot`, scope-marker dir `(scope)` -- never a real dir.
function cellKey(moduleName, dir) {
  return `${moduleName}|${dir}`;
}

// Derived via cellKey so the separator has exactly one definition.
const BLINDSPOT_CELL = cellKey("blindspot", "(scope)");

// The verbatim 2-line "how to read this" legend -- the single source for the tag + verification
// glossary, and the most-read trust statement, so it carries the not-a-guarantee caveat.
// renderBacklogFence emits it verbatim, so it cannot drift.
const LEGEND =
  "`refactor` = tidy without changing behavior - `capability-upgrade` = add/upgrade a technology - `dependency-health` = update/patch dependencies - `bug` = fix wrong behavior - `feature` = new behavior.\n" +
  "`(checked against the code)` = a separate agent re-read the code and couldn't refute it - `(could not confirm independently -- model's assertion)` = still just the model's claim - `(! not yet verified -- re-run to confirm)` = budget ran out before checking -- each surfaced finding is re-checked by a separate clean-context agent that never saw the finder's reasoning -- a reduction of rubber-stamping risk, not a mechanical guarantee.";

// The architecturally-sound terminal signal -- the recommended-starting-point IFF Tiers 1 and 2 are
// BOTH empty (the explicit "stop"). Verbatim; the renderer appends the PARTIAL scoping clause.
const TERMINAL_SIGNAL =
  "Sound on the audited dimensions -- what remains is optional polish; you don't need to keep re-auditing.";

// The GAP-mode counterpart. Gap mode reads STATICALLY and never runs the product, so it cannot earn
// the word "sound" -- exactly the over-claim the trust register exists to prevent. It is scoped to
// what was checked and names the check that was NOT run (0043 PS-2).
const GAP_TERMINAL_SIGNAL =
  "No gaps found against the spec's criteria, read STATICALLY -- this did not run your app, so it " +
  "is not evidence the product behaves correctly; the QA workflow is what checks that.";

// The static-only scope line, emitted on EVERY gap fence, pass or fail. The skill says it in chat;
// the fence is the surface that PERSISTS, so it has to carry it too.
const GAP_SCOPE_LINE =
  "_This read the code against the spec -- it did not run the app. Runtime checking is the QA workflow._";

// The verbatim closing "how to start" line -- the user's always-present go-button. Defined once.
const GO_BUTTON =
  "To start anything -- a backlog item or a brand-new project -- just tell the agent in plain English what you want (e.g. 'Let's do Tier-1 item 1' or 'I want to build X'). It will ask you questions (Discuss), then write a plan and spec for you to approve before any code. For a backlog item, the go-button is **`/claugentic-dev-harness:build`** -- point it at one item ('build Tier-1 item 1') and it drives the whole reviewed pipeline for you, pausing only at the spec (before any code) and before anything irreversible (pause points the engine enforces; judging \"irreversible\" is model-upheld).";

// The date placeholder in the status line -- the script has no clock, so the orchestrator replaces
// this token with today's date after the run (Phase 3 file mechanics).
const DATE_PLACEHOLDER = "{{DATE}}";

// The verbatim verification phrase per state -- the verdict->tag map, the inline tag every item
// carries. renderItem emits exactly one, by item.verification.state.
const VERIFICATION_PHRASE = {
  verified: "(checked against the code)",
  unconfirmed: "(could not confirm independently -- model's assertion)",
  deferred: "(! not yet verified -- re-run to confirm)",
};

// Validate ONE acceptance criterion against the FROZEN schema: strict-exact, the six keys and ONLY
// those. Returns an error string naming the offending id (or its index when the id is missing/blank)
// and the exact problem, else null. Used at the boundary AND at enumeration.
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
    return `${at}: unexpected key(s) ${JSON.stringify(extra)} -- the frozen schema is exactly ${JSON.stringify(CRITERIA_KEYS)}`;
  }
  if (missing.length > 0) {
    return `${at}: missing key(s) ${JSON.stringify(missing)} -- the frozen schema is exactly ${JSON.stringify(CRITERIA_KEYS)}`;
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

// Validate the args contract at the boundary (fail loud -- the caller throws on a non-empty list).
// Returns every shape error; empty = valid. TWO mutually-exclusive arg modes:
//   * STANDARD (modules x dirs) -- dial quick|standard|thorough; modules + scopeDirs required.
//   * CRITERIA (product-gap) -- non-empty, frozen-schema-valid, UNIQUE ids; modules/scopeDirs/dial
//     NOT required. The shared fields apply identically to both.
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
      `dial '${args.dial}' is not supported -- supported dials are ${SUPPORTED_DIALS.join("/")}`,
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

// The boundary checks both arg modes share (DRY): excludeSet, maxCellsPerRun, doneCells,
// deferredFindings, priorItems, builderFamily. Returns every error; empty = valid.
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
    errors.push("maxCellsPerRun is required (positive integer -- the deterministic cap)");
  }
  if (args.doneCells !== undefined && !Array.isArray(args.doneCells)) {
    errors.push("doneCells, when provided, must be an array of cell keys");
  }
  if (args.deferredFindings !== undefined && !Array.isArray(args.deferredFindings)) {
    errors.push("deferredFindings, when provided, must be an array of findings");
  }
  if (args.priorItems !== undefined && !Array.isArray(args.priorItems)) {
    errors.push("priorItems, when provided, must be an array (the prior run's resolved items -- verdicts persist)");
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.length === 0) {
    errors.push("builderFamily is required (non-empty string -- the orchestrator's model family)");
  }
  return errors;
}

// Validate the CRITERIA (product-gap) arg mode: a non-empty array of frozen-schema-valid criteria
// with UNIQUE ids, plus the shared checks. modules/scopeDirs/dial are NOT required.
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
        errors.push(`criterion '${criterion.id}': duplicate id -- ids must be unique`);
      }
      seen.add(criterion.id);
    });
  }
  errors.push(...validateSharedArgs(args));
  return errors;
}

// Enumerate the gap-mode pending cells: ONE per criterion, keyed by its unique id, in spec order,
// MINUS anything already in doneCells (the standard resume contract with criterion ids as cells).
// Each cell carries its criterion so the FIND fan-out needs no second lookup. Throws, naming the
// offending id, on a schema violation or an empty list -- redundant with the boundary, but it keeps
// the helper independently safe.
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
      throw new Error(`cellsFromCriteria: duplicate criterion id '${criterion.id}' -- ids must be unique`);
    }
    seen.add(criterion.id);
    if (!done.has(criterion.id)) {
      cells.push({ key: criterion.id, criterion });
    }
  });
  return cells;
}

// The dial -> depth map (total over the three notches).
function depthForDial(dial) {
  return DEPTH_FOR_DIAL[dial];
}

// Map a validated module name to its standards doc path.
function modulePath(moduleName) {
  return `docs/claugentic-standards/${moduleName}.md`;
}

// The cell-key token `<module>|<dir>` (a literal pipe) is the resume contract with the SKILL -- the
// exact format the fence's done-cells / pending-cells lists carry.

// Enumerate the pending cells INTERLEAVED, dir-major: `m0|d0, m1|d0, ..., mK|d0, m0|d1, ...` (loop
// nesting dir OUTER, module INNER). A pure function of input order -- no Set-iteration, no sort --
// so the SAME inputs always yield the SAME ordered remainder. THAT stability IS the resume contract:
// doneCells is a SET the next run subtracts, safe only because the order is reproducible. The
// interleave is also the lens-coverage fix -- a budget-limited prefix covers EVERY lens's TOP dir
// before any lens's second dir, so at maxCellsPerRun >= lens count every lens gets >=1 cell:
// starvation is STRUCTURALLY impossible, no separate floor pass, the ordering IS the floor. At
// `thorough` BLINDSPOT_CELL is appended STRICTLY LAST, so it is deferred first under a tight cap.
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
// overflow to a resume run. The single deterministic cap -- the platform `budget` primitive is a
// backstop only, never the resume contract.
function applyCellBudget(cells, maxCellsPerRun) {
  return {
    run: cells.slice(0, maxCellsPerRun),
    overflow: cells.slice(maxCellsPerRun),
  };
}

// Parse a cell key into module + dir (split on the FIRST pipe -- a dir may contain one, so only the
// first separator is structural).
function parseCellKey(key) {
  const i = key.indexOf("|");
  if (i < 0) {
    return { module: key, dir: "" };
  }
  return { module: key.slice(0, i), dir: key.slice(i + 1) };
}

// Group this run's cells into one batch per module over its scoped dirs -- the fan-out unit, one
// lens-reviewer per batch. First-seen module order; dirs in cell order.
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

// Per-lens coverage -- the structural answer to "did every configured lens speak?" (prong #4). Per
// configured module, in config order, the THREE outcomes a reader must tell apart:
//   * ran-clean -- ran (no cell pending), 0 findings: an explicit CLEAN, not silence.
//   * ran-found -- ran and contributed N findings.
//   * pending   -- ANY of its (module x dir) cells is still pending (budget-deferred or a failed
//                  batch), so the lens NEVER fully ran; N is whatever its run cells surfaced. Never
//                  clean while a cell is pending -- verify.js's coverageGaps honesty.
// The count derives from the kept findings' sourceModule, so it counts what reached the backlog: a
// CLEAN lens ran and left nothing, distinct from a never-run one that never looked. Unit-tested.
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

// Per-criterion coverage -- gap mode's "which parts of my spec does the code DELIVER?" (the met /
// partial / missing report the product spec promises). SEPARATE from lensCoverage on purpose, and it
// does NOT touch parseCellKey: a gap cell IS the raw criterion id, so pending is an exact Set
// membership test and an id containing a `|` cannot be mis-split into a phantom earlier pass.
// Per criterion, in SPEC order:
//   * not-checked -- still pending. A cell that never ran NEVER carries a verdict; "unchecked" is
//                    not a claim about the code.
//   * otherwise   -- the reviewer's `criterionVerdict` FOLDED against surviving evidence, so it can
//                    never outrank the code: "met" + >=1 surviving attributed finding DOWNGRADES to
//                    "partial"; "partial"/"missing" + ZERO surviving attributed findings UPGRADES to
//                    "met". Evidence wins BOTH ways -- that fold is what makes this a report rather
//                    than a relayed claim.
// Attribution is `modules.includes("criterion <id>")`, the engine-assigned list dedupFindings unions
// -- NEVER `sourceModule ===`, which is first-wins under dedup. `findings` is the SURVIVING set the
// fence renders, so a criterion can never read "met" above an item that cites it.
function criterionCoverage(criteria, pendingCells, verdictByCriterion, findings) {
  const pending = new Set(Array.isArray(pendingCells) ? pendingCells : []);
  const verdicts = verdictByCriterion instanceof Map ? verdictByCriterion : new Map();
  const surviving = Array.isArray(findings) ? findings : [];
  return (Array.isArray(criteria) ? criteria : []).map((criterion) => {
    const id = criterion && criterion.id != null ? criterion.id : "";
    const tag = `criterion ${id}`;
    const findingCount = surviving.filter(
      (f) => f && Array.isArray(f.modules) && f.modules.includes(tag),
    ).length;
    const state = pending.has(id)
      ? "not-checked"
      : findingCount > 0
        ? verdicts.get(id) === "missing"
          ? "missing"
          : "partial"
        : "met";
    const feature = criterion && criterion.feature != null ? criterion.feature : "";
    return { id, feature, state, findings: findingCount };
  });
}

// Normalize an issue-class string: lowercase, trim, whitespace -> single hyphens. The deterministic
// dedup identity derives from this; synonyms that still differ stay distinct -- semantic dedup is
// the synthesis agent's job.
function normalizeIssueClass(s) {
  return String(s == null ? "" : s)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-");
}

// The dedup key AND the finding's id: the normalized issueClass. Same KIND of problem collides
// regardless of location; distinct classes at one file:line stay separate.
function findingKey(finding) {
  return normalizeIssueClass(finding && finding.issueClass);
}

// Merge same-key findings across lenses: union of `locations` (the "recurs in N files" roll-up) AND
// of `modules` (the list every coverage report attributes by), WEAKEST confidence wins (a `judgment`
// member downgrades and never upgrades back), first concrete claim/fix kept. Distinct classes stay
// separate; first-seen order; each merged finding carries its computed `findingKey`.
//
// The `modules` union is load-bearing, not cosmetic: `sourceModule` is FIRST-WINS, so two lenses (or
// criteria) surfacing the SAME issueClass collapse to the first source and the second's attribution
// silently disappears -- in gap mode a reachable false MET. Attribute coverage by `modules`, NEVER
// by `sourceModule ===`.
function dedupFindings(findings) {
  const byKey = new Map();
  for (const finding of findings) {
    const key = findingKey(finding);
    const incomingLocations = Array.isArray(finding.locations) ? finding.locations : [];
    const incomingModules = Array.isArray(finding.modules) ? finding.modules : [];
    if (!byKey.has(key)) {
      byKey.set(key, {
        ...finding,
        findingKey: key,
        locations: [...incomingLocations],
        modules: [...incomingModules],
      });
      continue;
    }
    const merged = byKey.get(key);
    for (const loc of incomingLocations) {
      if (!merged.locations.includes(loc)) {
        merged.locations.push(loc);
      }
    }
    for (const mod of incomingModules) {
      if (!merged.modules.includes(mod)) {
        merged.modules.push(mod);
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

// Apply the synthesis cut-list -- drops every cut key EXCEPT findingKey === TEST_BASELINE_CLASS (the
// script-enforced never-prune exception). A cut targeting it is ignored, not honored.
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

// Map module names -> doc paths for a lens prompt.
function modulesToPaths(modules) {
  return modules.map(modulePath);
}

// Build the audit-scope lens prompt (per .claude/agents/lens-reviewer.md): module path, scoped dirs,
// exclude-set, depth word. Audit-scope mode -- there is NO diff.
function buildLensPrompt(moduleName, dirs, excludeSet, depth) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Audit-scope mode (no diff). Your lens is the standards module: ${modulePath(moduleName)}. ` +
    `Audit the existing code in this scope against that module's dimensions only. ` +
    `Scope (prioritized dirs/packages): ${JSON.stringify(dirs)}. ` +
    `Exclude-set (never read -- deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: ${depth}. ` +
    `Return per-issue findings: issueClass, claimPlain, claimTechnical, locations (file:line list), ` +
    `fix, confidence (deterministic|judgment).`
  );
}

// Build the product-gap lens prompt for ONE acceptance criterion (the lens-reviewer's PRODUCT-GAP
// mode). It reads the implementation STATICALLY -- it does NOT run the app, and the prompt says so
// -- and reports missing / partial / diverging behavior per flow step, expectation and required
// state, in the SAME finding shape as buildLensPrompt so the findings join the unchanged dedup ->
// prune -> verify path. The criterion id rides into issueClass guidance. Depth is fixed `deep`.
function buildCriterionLensPrompt(criterion, excludeSet) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Product-gap mode (intent vs implementation -- STATIC code reading; do NOT run the app -- ` +
    `runtime checking is the QA workflow's job). Your lens is ONE acceptance criterion from the ` +
    `product spec; check whether the implementation delivers it. Criterion: ${JSON.stringify(criterion)}. ` +
    `Locate the implementing code via docs/claugentic-ARCHITECTURE_TREE.md (the file index), then READ it ` +
    `statically. For each flow step, each expectation in 'expect', and each required state in ` +
    `'states', report whether the code delivers it -- flag promised-but-missing (the behavior has no ` +
    `implementation) and diverges-from-spec (the implementation contradicts the promise). A 'manual' ` +
    `check still gets a static read for an obvious missing surface, but a human owns the verdict. ` +
    `Exclude-set (never read -- deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: deep. ` +
    `Return per-issue findings: issueClass (prefix with the criterion id '${criterion.id}'), ` +
    `claimPlain, claimTechnical, locations (file:line list), fix, confidence (deterministic|judgment).`
  );
}

// Build the whole-scope blind-spot sweep prompt (`thorough` only -- the lens-reviewer's WHOLE-SCOPE
// mode): no single module, red-team posture, always exhaustive depth. It FINDS only; its findings
// carry `issueClass` like a lens return and join dedupFindings with no special handling.
function buildBlindspotPrompt(scopeDirs, excludeSet) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `You are in WHOLE-SCOPE mode. Audit-scope target (no diff). You have NO single standards ` +
    `module -- your lens is the WHOLE audited scope. Red-team posture: a checklist-driven ` +
    `per-module review just ran over this ` +
    `scope -- hunt what it would STRUCTURALLY miss (emergent architectural smells, integration ` +
    `gaps between components, cross-cutting concerns applied inconsistently, systemic issues that ` +
    `fall BETWEEN the per-module lenses). ` +
    `Scope (prioritized dirs/packages): ${JSON.stringify(scopeDirs)}. ` +
    `Exclude-set (never read -- deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: exhaustive (you are a thorough-only finder). You FIND only -- do NOT verify. ` +
    `Return per-issue findings in the SAME shape as a lens-reviewer: issueClass, claimPlain, ` +
    `claimTechnical, locations (file:line list), fix, confidence (deterministic|judgment).`
  );
}

// Build the adversarial yagni-sentinel prune prompt (`thorough` only): the independent skeptic argues
// the kept set down from a clean context. Returns ONLY a cut-list; applyPrune applies it, and its
// TEST_BASELINE_CLASS protection holds on this second pass too.
function buildSentinelPrompt(keptFindings) {
  return (
    `You are the YAGNI sentinel. An audit has consolidated and pruned a finding set; argue it does ` +
    `TOO MUCH. Independently (clean context -- you are NOT given the synthesis rationale) flag ` +
    `findings that are speculative, gold-plating, premature infrastructure, over-generalization, ` +
    `or scope creep -- the marginal nice-to-haves that should NOT reach the backlog. Do NOT argue ` +
    `against genuinely warranted quality (real security, real edge-cases, real resilience). ` +
    `Return ONLY a cuts list of { findingKey, reason } for everything you would cut. ` +
    `Kept findings: ${JSON.stringify(keptFindings)}.`
  );
}

// Build the synthesis prompt: consolidate -> tier (1|2|3) + exactly one of the five tags +
// plain-English title/why/impact-effort per item -> a cut list with reasons. MODE-BRANCHED on
// `isGap` at EXACTLY TWO clauses; the consolidate/tier/tag/return-shape text is byte-identical in
// both modes (one prompt, one contract -- synthesizer-gate Mode 3):
//   * standard -- a YAGNI right-size prune, plus ONE missing-test-baseline Tier-1 item ONLY when the
//     inputs show untested behavior-bearing code and none exists.
//   * gap -- the CONFORMANCE variant. The lens source is ACCEPTANCE CRITERIA, so YAGNI does not
//     apply: every finding claims the product's OWN spec promises something the code does not do,
//     never a marginal nice-to-have. The test-baseline ADD is DROPPED -- it maps to no criterion, so
//     an engineering to-do can never enter a PRODUCT backlog.
// NEVER manufacture a finding to fill a tier, either mode.
function buildSynthesisPrompt(dedupedFindings, modules, scopeDirs, isGap) {
  const prune = isGap
    ? `and PRUNE it for SPEC CONFORMANCE -- do NOT apply YAGNI. The lens source is acceptance ` +
      `criteria, not engineering standards: every finding is a claim that the product's OWN spec ` +
      `promises something the code does not do, so a promised-but-missing behaviour is never a ` +
      `marginal nice-to-have and may NOT be cut for impact. Cut ONLY (a) exact semantic duplicates ` +
      `(reason "duplicate of <key>") and (b) findings citing no acceptance criterion (reason ` +
      `"no criterion") -- and every cut reason MUST name the criterion id the finding came from. ` +
      `Never manufacture a finding to fill a tier. `
    : `and right-size it (YAGNI -- keep only findings with real impact; cut marginal ` +
      `nice-to-haves; never manufacture a finding to fill a tier). `;
  const baselineAdd = isGap
    ? ``
    : `ADD one item with findingKey "${TEST_BASELINE_CLASS}" at tier 1 ONLY IF the audited code is ` +
      `behavior-bearing and untested and no test baseline exists -- otherwise do not add it. `;
  return (
    `Synthesis self-review of an audit. Consolidate these deduped findings into a tiered, tagged ` +
    `backlog set ` +
    prune +
    `For each kept finding return: findingKey (the issueClass), tier (1|2|3), tag (exactly one of ` +
    `refactor|capability-upgrade|dependency-health|bug|feature), titlePlain, whyPlain, impactEffort. ` +
    `Return a cuts list of { findingKey, reason } for everything you drop (use reason "duplicate of <key>" ` +
    `for semantic duplicates the coded dedup missed). ` +
    baselineAdd +
    `Audited modules: ${JSON.stringify(modules)}. Scope: ${JSON.stringify(scopeDirs)}. ` +
    `Deduped findings: ${JSON.stringify(dedupedFindings)}.`
  );
}

// Build the finding-verifier's CLEAN-CONTEXT input: ONLY the contract keys, so finding-verifier's
// independence is preserved STRUCTURALLY -- the builder cannot emit rationale/transcript fields, and
// any extra fields on the finding are dropped here.
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

// Build the verifier prompt from the clean-context input (refute-first; demands the RUNNING AS
// self-report). NEVER includes the finder's rationale.
function buildVerifierPrompt(input) {
  return (
    `Independently REFUTE this single audit finding against the actual code (refute-first; ` +
    `clean context -- you are NOT given the finder's rationale). ` +
    `Open your response with "RUNNING AS: <model family>" and report it in runningAs. ` +
    `Claim (plain): ${input.claimPlain}. Claim (technical): ${input.claimTechnical}. ` +
    `Locations: ${JSON.stringify(input.locations)}. Source module: ${input.sourceModule}. ` +
    `Finder's confidence label: ${input.confidence}. ` +
    `Exclude-set (never read): ${JSON.stringify(input.excludeSet)}. ` +
    `Return verdict (Verified|Refuted|Unconfirmed), evidence, plainLine.`
  );
}

// Normalize a self-reported model family to a canonical lowercase token. First KNOWN_FAMILIES match
// wins; empty/unknown -> null (the conservative trust floor, never a false cross-model claim).
// Copied verbatim from verify.js.
function modelFamily(report) {
  if (typeof report !== "string") {
    return null;
  }
  const match = report.match(new RegExp(`(${KNOWN_FAMILIES.join("|")})`, "i"));
  return match ? match[1].toLowerCase() : null;
}

// The disclosure decision -- THREE states, one rule; a MISSING self-report (the no-report floor) is
// distinct from a PRESENT one that FAILED to resolve. Copied verbatim from verify.js (state table).
function sameModelTag(builderFamily, judgeFamily) {
  const judgeReported = typeof judgeFamily === "string" && judgeFamily.trim().length > 0;
  if (!judgeReported) {
    return SAME_MODEL_TAG; // no judge self-report at all -> the conservative same-model floor
  }
  const b = modelFamily(builderFamily);
  const j = modelFamily(judgeFamily);
  if (b === null || j === null) {
    return UNRESOLVED_FAMILY_TAG; // a present report could not be resolved -> reported as unresolved
  }
  return b === j ? SAME_MODEL_TAG : null;
}

// Apply the verifier verdicts to the surviving findings. The only representable states are
// verified / unconfirmed / deferred -- NEVER a silent "checked":
//   Verified    -> kept, state 'verified' + evidence
//   Unconfirmed -> kept, state 'unconfirmed'
//   Refuted     -> dropped and counted; the FINDING leaves no other trace, but its verifier's report
//                  rides out in refutedRunningAs -- a reviewer that decided what reaches the backlog
//                  must not vanish from the run's cross-model fold
//   no verdict  -> kept, state 'deferred' (budget ran out / verifier never ran)
// `results` is aligned to `findings` (results[i] verifies findings[i]); missing/null is deferred.
function applyVerdicts(findings, results) {
  const kept = [];
  const refutedRunningAs = [];
  let refutedCount = 0;
  findings.forEach((finding, i) => {
    const result = Array.isArray(results) ? results[i] : undefined;
    const verdict = result && result.verdict ? result.verdict : null;
    if (verdict === "Refuted") {
      refutedCount += 1;
      // A verifier that RAN and refuted pushes its report (null = ran, no self-report -> the
      // conservative floor). Never filter this list: absence is a shorter ARRAY, not a null entry.
      refutedRunningAs.push(result && result.runningAs != null ? result.runningAs : null);
      return; // dropped -- false positive caught before the backlog
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
      // No usable verdict -- the verifier did not run (budget exhausted / null return).
      verification = {
        state: "deferred",
        evidence: "",
        plainLine: "not yet verified -- re-run to confirm",
      };
    }
    kept.push({
      ...finding,
      verification,
      // The verifier's own self-report rides WITH the finding -- verificationSummary must never
      // index a parallel results array (a Refuted finding's removal would misalign it; the
      // 2026-06-11 dogfood audit reproduced a false cross-model claim from exactly that).
      verifierRunningAs: result && result.runningAs != null ? result.runningAs : null,
    });
  });
  return { kept, refutedCount, refutedRunningAs };
}

// Fold the verifier results into the run's verification summary. `crossModel` is true ONLY when
// EVERY verifier returned a confirming different-family self-report (sameModelTag null for each AND
// every finding got a result); otherwise the THREE-state disclosure tag for WHY --
// UNRESOLVED_FAMILY_TAG for a present-but-unresolved family (reported, never asserted same-model
// fact), SAME_MODEL_TAG for a resolved-same or missing report; ANY unresolved report taints the
// whole run. Counts the kept states + the refuted drops. EVERY verifier that RAN votes -- the kept
// findings' reports PLUS `refutedRunningAs`: a refuting verifier decided what reached the backlog,
// so excluding it would let a same-model reviewer decide under a cross-model banner.
function verificationSummary(findings, refutedCount, builderFamily, refutedRunningAs) {
  let verified = 0;
  let unconfirmed = 0;
  let deferred = 0;
  const reports = findings
    .map((f) => (f && f.verifierRunningAs != null ? f.verifierRunningAs : null))
    .concat(Array.isArray(refutedRunningAs) ? refutedRunningAs : []);
  let allConfirmingDifferentFamily = reports.length > 0;
  let sawUnresolved = false;
  findings.forEach((finding) => {
    const v = finding && finding.verification ? finding.verification.state : null;
    if (v === "verified") verified += 1;
    else if (v === "unconfirmed") unconfirmed += 1;
    else deferred += 1;
  });
  reports.forEach((reported) => {
    // A PRESENT non-empty report that does not resolve to a KNOWN family is the unresolved case --
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

// Normalize the args boundary (copied verbatim from verify.js): a scriptPath invocation delivers
// `args` as a JSON STRING (observed 2026-06-11), an inline script the object. Unparseable = loud.
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

// The gap-mode FIND schema: LENS_SCHEMA plus a REQUIRED per-criterion verdict, so the met/partial/
// missing report is carried STRUCTURALLY and validated at the tool-call boundary -- never inferred
// from prompt guidance, never parsed out of an issueClass prefix (that inference made a false MET
// reachable). Standard mode keeps LENS_SCHEMA: a standards module has no verdict to render.
const GAP_LENS_SCHEMA = {
  ...LENS_SCHEMA,
  required: ["lensVerdict", "criterionVerdict", "findings"],
  properties: {
    ...LENS_SCHEMA.properties,
    criterionVerdict: { type: "string", enum: ["met", "partial", "missing"] },
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

// The adversarial yagni-sentinel's cut-list schema (`thorough` PRUNE): ONLY cuts, the same
// { findingKey, reason } shape the synthesis cuts use, applied via the same applyPrune
// (TEST_BASELINE_CLASS still protected).
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

// Apply the synthesis agent's tier/tag/plain-English metadata onto a kept finding, by findingKey. An
// unannotated finding keeps conservative defaults (tier 2, refactor) and is never dropped here --
// the cut-list, via applyPrune, is the only drop path.
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

// Shape a kept+verified finding into the Phase-3 return item contract the renderer consumes.
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

// -- Fence renderer (the backlog fence body's single source of truth) --
// Pure string builders emitting the COMPLETE inner fence body -- NO markers, NO heading, those stay
// SKILL-owned. {{DATE}} is a placeholder the orchestrator stamps after the run (no clock here).
// skills/audit/SKILL.md Phase 3 points HERE as the source of truth -- drift is a unit-test failure,
// not a model-discipline failure.

// The status line -- the resume contract's first line. Cell lists are the verbatim cellKey tokens
// from the result, comma-joined inside [ ]. The date is the placeholder.
function renderStatusLine(result) {
  const done = Array.isArray(result.doneCells) ? result.doneCells : [];
  const pending = Array.isArray(result.pendingCells) ? result.pendingCells : [];
  return (
    `status: ${result.status} - level: ${result.level} - ` +
    `done-cells: [${done.join(", ")}] - pending-cells: [${pending.join(", ")}] - ` +
    `date: ${DATE_PLACEHOLDER}`
  );
}

// One verification phrase per item, by state (verbatim -- the inline trust tag). An unknown/missing
// state degrades to the deferred phrase -- never silently "checked".
function verificationPhrase(state) {
  return VERIFICATION_PHRASE[state] || VERIFICATION_PHRASE.deferred;
}

// The technical-finding line: claim + locations. >1 location reads "recurs in N files: ..."; one
// reads inline; none is honestly omitted.
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

// Render one backlog item -- the exact item format (SKILL Phase 3): title, exactly one tag, the
// inline verification phrase, the dual-layer technical+plain finding, impact+effort, and (when
// verified) the evidence snippet on the technical finding.
function renderItem(item) {
  const state = item.verification ? item.verification.state : "deferred";
  const phrase = verificationPhrase(state);
  const evidence =
    state === "verified" && item.verification && item.verification.evidence
      ? ` Evidence: ${item.verification.evidence}.`
      : "";
  const lines = [];
  // The STABLE id must be on the page: `priorItems` (resume) and the rejected-findings memory
  // (dismissal) are both keyed on findingKey, and the fence is the only artifact that survives a
  // run -- omitting it silently dropped confirmed findings on resume and left dismissals unmatchable.
  // Rendered last so it reads as a marker, not a title (0043 PS-3).
  const key = item.findingKey ? ` \`#${item.findingKey}\`` : "";
  lines.push(`- **${item.titlePlain}** -- \`${item.tag}\` *${phrase}*${key}`);
  lines.push(
    `  - Technical: ${item.claimTechnical}${renderLocations(item.locations)}.${evidence}`,
  );
  lines.push(`  - Plain English: ${item.whyPlain}`);
  lines.push(`  - Impact/effort: ${item.impactEffort}`);
  return lines.join("\n");
}

// Render one tier section (most-urgent-first ordering is the caller's). An empty tier carries an
// explicit "(empty)" note, never a silent gap.
function renderTier(heading, items) {
  const body =
    items.length > 0 ? items.map(renderItem).join("\n") : "_(empty)_";
  return `### ${heading}\n\n${body}`;
}

// The recommended-starting-point line. Tiers 1+2 BOTH empty -> the terminal "sound" signal (plus the
// covered-cells scoping clause on a PARTIAL run); otherwise the first Tier-1 item, else Tier-2.
function renderRecommendation(tier1, tier2, status, level, verificationIncomplete) {
  if (tier1.length === 0 && tier2.length === 0) {
    // A COMPLETE sweep whose VERIFY was budget-truncated must not read as "don't keep re-auditing".
    const scope =
      status === "PARTIAL"
        ? " (scoped to the cells covered this run -- re-run to finish the rest)"
        : verificationIncomplete
          ? " (the budget ran out before every finding was re-checked -- re-run to check the rest)"
          : "";
    const signal = level === "gap" ? GAP_TERMINAL_SIGNAL : TERMINAL_SIGNAL;
    return `**Recommended starting point:** ${signal}${scope}`;
  }
  const first = tier1.length > 0 ? tier1[0] : tier2[0];
  return `**Recommended starting point:** ${first.titlePlain}.`;
}

// The per-lens coverage line (see lensCoverage): one line per configured lens, in config order, with
// its state + finding count -- "CLEAN" for ran-and-found-nothing (an explicit 0, not silence),
// "did not run this pass" for never-ran, so a reader can tell them apart before prioritizing.
// Renders nothing when absent -- never a misleading empty header. The phrase map owns the wording.
const LENS_COVERAGE_PHRASE = {
  "ran-found": (n) => `${n} finding${n === 1 ? "" : "s"}`,
  "ran-clean": () => "CLEAN (ran, found nothing)",
  pending: (n) =>
    n > 0
      ? `did not finish this pass (${n} so far) -- re-run to cover it`
      : "did not run this pass -- re-run to cover it",
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

// The per-criterion coverage line -- the surface that makes "met" distinguishable from "the check
// quietly produced nothing". Structurally the twin of renderLensCoverage (one line per criterion in
// SPEC order, nothing when absent); the two are MUTUALLY EXCLUSIVE by mode and share one slot.
const CRITERION_COVERAGE_PHRASE = {
  met: () => "checked, delivers it",
  partial: (n) => `${n} gap${n === 1 ? "" : "s"}`,
  missing: (n) => `not delivered -- ${n} gap${n === 1 ? "" : "s"}`,
  "not-checked": () => "not checked this run -- re-run to cover it",
};
function renderCriterionCoverage(criterionCoverage) {
  const criteria = Array.isArray(criterionCoverage) ? criterionCoverage : [];
  if (criteria.length === 0) {
    return "";
  }
  const lines = criteria.map((c) => {
    const phrase = (CRITERION_COVERAGE_PHRASE[c.state] || CRITERION_COVERAGE_PHRASE["not-checked"])(
      c.findings || 0,
    );
    const label = c.feature ? `\`${c.id}\` (${c.feature})` : `\`${c.id}\``;
    return `- ${label}: ${phrase}`;
  });
  return `**Criterion coverage** (which parts of your spec does the code deliver?):\n${lines.join("\n")}`;
}

// The verification run-report line, driven by the result's verification block. Dropped findings are
// a trust signal: a COUNT, never a list, worded DISPROVED -- never "could not confirm", which is the
// KEPT unconfirmed state's phrase (VERIFICATION_PHRASE / LEGEND). When crossModel is false the
// cross-model clause is REPLACED by (never joined with) the THREE-state disclosure tag the summary
// computed, so an unresolved run never reads as asserted same-model fact.
function renderRunReport(verification) {
  const v = verification || {};
  const refuted = v.refuted != null ? v.refuted : 0;
  const verified = v.verified != null ? v.verified : 0;
  const unconfirmed = v.unconfirmed != null ? v.unconfirmed : 0;
  const deferred = v.deferred != null ? v.deferred : 0;
  const judgeClause = v.crossModel
    ? "(re-checked by a separate clean-context agent -- a reduction of shared-blind-spot risk, not independence)"
    : v.sameModelTag != null
      ? v.sameModelTag
      : SAME_MODEL_TAG;
  // A budget-truncated VERIFY may never read as "every finding" -- name the shortfall inline.
  const covered =
    deferred > 0
      ? `all but ${deferred} of the findings I surfaced (the budget ran out -- re-run to check them)`
      : "every finding I surfaced";
  // Carried items are RENDERED but never re-checked this pass, so the tallies cannot cover them.
  const carried = v.carried != null ? v.carried : 0;
  const carriedClause =
    carried > 0 ? ` Plus ${carried} carried forward -- verdicts already earned, not re-checked this pass.` : "";
  return (
    `Re-checked ${covered} against the code ${judgeClause}; ` +
    `dropped ${refuted} that were disproved -- ` +
    `verified ${verified} - unconfirmed ${unconfirmed} - deferred ${deferred}.${carriedClause}`
  );
}

// Build the COMPLETE inner fence body. Order: status line, legend, the three tiers
// (most-urgent-first), the recommended starting point, the coverage report (per-lens standard,
// per-criterion gap, omitted when absent), the run report, go-button. NO markers, NO heading.
function renderBacklogFence(result) {
  const items = Array.isArray(result.items) ? result.items : [];
  const tier1 = items.filter((it) => it.tier === 1);
  const tier2 = items.filter((it) => it.tier === 2);
  const tier3 = items.filter((it) => it.tier === 3);
  // ONE coverage slot, two mode-exclusive reports (`lensCoverage` standard, `criterionCoverage`
  // gap); neither is ever present alongside the other, and an absent one renders "" so the fence
  // never grows an empty header.
  const coverageLine =
    renderLensCoverage(result.lensCoverage) || renderCriterionCoverage(result.criterionCoverage);
  const parts = [
    renderStatusLine(result),
    LEGEND,
    renderTier("Tier 1 -- critical", tier1),
    renderTier("Tier 2 -- important", tier2),
    renderTier("Tier 3 -- polish", tier3),
    renderRecommendation(tier1, tier2, result.status, result.level, result.verificationIncomplete),
    ...(coverageLine ? [coverageLine] : []),
    renderRunReport(result.verification),
    // Emitted on EVERY gap fence, pass or fail -- the fence is the surface that persists.
    ...(result.level === "gap" ? [GAP_SCOPE_LINE] : []),
    `*${GO_BUTTON}*`,
  ];
  return parts.join("\n\n");
}

// Resume honesty: a PARTIAL re-run regenerates the WHOLE fence from result.items, so the prior pass's
// RESOLVED findings (verified/unconfirmed -- verdicts persist, never re-verified) must ride in via
// priorItems and merge here; a finding re-surfaced by THIS run supersedes its prior copy on
// findingKey. Without the merge the resumed fence silently dropped confirmed findings -- the gap-mode
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

// The SELECT seam: re-render the fence from an ALREADY-SELECTED item subset while passing
// lensCoverage / criterionCoverage / verification through FULL-SCOPE -- a narrowed item list must
// never narrow the coverage report. The SKILL filters items; the renderer stays the single source of
// the fence format. It validates its own payload because the branch that calls it returns before the
// boundary validator runs. The guard checks the ENVELOPE (object + items array), not per-element
// shape: items are always a subset of the engine's OWN result.items, so a malformed element is
// unreachable and deeper validation would guard an impossible state (YAGNI).
//
// HONESTY CONTRACT, why full-scope and why the SKILL guards the empty case: recomputing coverage/
// verification over the KEPT subset would claim "every lens spoke" about only what the user kept;
// and an EMPTY selection re-rendered here emits the terminal "sound on the audited dimensions"
// signal over a run that DID surface work. So the SKILL must never invoke it with an empty selection
// when the full run carried Tier-1/2 findings. Pinned in audit.test.mjs (both legs).
function renderOnlyResult(payload) {
  if (payload == null || typeof payload !== "object" || !Array.isArray(payload.items)) {
    throw new Error("renderOnly requires an object payload with an items array");
  }
  return { ...payload, renderedBacklog: renderBacklogFence(payload) };
}

// The entry decision (PURE): normalize the args boundary ONCE, then answer the control flow's first
// question -- is this a re-render pass, and over what payload? Returns `{ input, renderOnly }`, null
// on a normal audit pass; renderOnlyResult validates the payload shape.
//
// It reads the PARSED args ON PURPOSE. A scriptPath invocation delivers `args` as a JSON STRING and
// that is the ONLY shape /audit uses, so a seam decided on the RAW args could never fire on the real
// call path: the documented call fell straight through to `audit args invalid`, and a caller that
// re-passed its original args got a SECOND full audit with the whole FIND/PRUNE/VERIFY fan-out.
// Extracted so the decision is unit-pinnable at all (0041 S10a, D1).
function auditEntry(rawArgs) {
  const input = parseArgs(rawArgs);
  const renderOnly =
    input != null && typeof input === "object" && input.renderOnly ? input.renderOnly : null;
  return { input, renderOnly };
}
// --- end helpers ---

// The D6 namespace fallback -- the ONE spawn seam every namespaced agent call goes through. The
// sandbox cannot tell an installed adopter (namespaced ids resolve) from a project-local dogfood
// (only bare names do), so: try namespaced, retry bare ONCE on a THROWN spawn failure, spreading the
// ORIGINAL opts. A null return is a legitimate outcome -- passed through, never retried.
//
// DO NOT thread this through a judge's one-respawn state machine (0041 S10b, D6): a namespace retry
// consumes no respawn budget, never sets forcedSameModel (that flag feeds the same-model
// disclosure), never swallows a two-failure throw, and carries its own `:ns-fallback` label, never
// `:respawn`. Copied byte-identical across the workflow scripts (drift pin); rationale in verify.js.
async function agentWithNamespaceFallback(prompt, opts) {
  try {
    return await agent(prompt, opts);
  } catch (e) {
    const agentType = opts && typeof opts.agentType === "string" ? opts.agentType : "";
    const bare = bareAgentType(agentType);
    if (bare === agentType) {
      throw e; // nothing to strip (a built-in or an already-bare id) -- there is no fallback
    }
    log(namespaceFallbackNotice(agentType, bare, e));
    return await agent(prompt, { ...opts, agentType: bare, label: `${opts.label || agentType}:ns-fallback` });
  }
}

// Spawn a judge (finding-verifier); one respawn on failure (the result then can't confirm a
// different family -> the same-model tag); a second failure marks the finding deferred, never a
// silent skip. The fan-out scales with findings, not files. Each attempt routes through the namespace
// fallback, which resolves INSIDE one attempt -- a bare retry consumes none of the one respawn and
// cannot influence the same-model tag (0041 S10b, D6).
async function spawnVerifier(input) {
  const prompt = buildVerifierPrompt(input);
  const attempt = async (opts) => {
    try {
      return { out: await agentWithNamespaceFallback(prompt, opts) };
    } catch (e) {
      return { out: null, err: e && e.message ? e.message : String(e) };
    }
  };
  const first = await attempt({
    agentType: nsAgent("finding-verifier"),
    ...(MODELS.judge ? { model: MODELS.judge } : {}),
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
  // Both attempts failed -- mark the finding deferred (honest no-silent-skip).
  return null;
}

// -- Top-level control flow (Workflow scripts run in an async context; no module wrapper). --

// Normalize the args boundary ONCE and decide the SELECT seam on the PARSED args -- a scriptPath
// invocation delivers them as a JSON string (auditEntry owns that decision).
const { input, renderOnly: renderOnlySelection } = auditEntry(args);

// The SELECT seam (see renderOnlyResult): an agent-free re-render over an ALREADY-SELECTED subset.
// It returns BEFORE the boundary validator, the FIND/PRUNE/VERIFY pipeline and the isGap branch, so
// it serves audit and gap-mode alike, and it bypasses the validator BY DESIGN -- such a payload
// legitimately carries no dial/modules/scopeDirs. Do not reorder it later.
if (renderOnlySelection !== null) {
  const selectedCount = Array.isArray(renderOnlySelection.items) ? renderOnlySelection.items.length : 0;
  log(`audit renderOnly -- re-rendering the backlog fence over ${selectedCount} selected item(s); no FIND/PRUNE/VERIFY this pass.`);
  return renderOnlyResult(renderOnlySelection);
}

// Validate at the boundary -- fail loud with the full error list.
{
  const errors = validateArgs(input);
  if (errors.length > 0) {
    throw new Error(`audit args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

// ARG MODE: criteria (product-gap) vs the standard modules x dirs sweep. The criteria list bounds
// FIND in gap mode (depth fixed `deep`, level `gap`); the dial drives standard mode.
const isGap = Array.isArray(input.criteria);
const dial = isGap ? GAP_LEVEL : input.dial;
const depth = isGap ? "deep" : depthForDial(input.dial);
const excludeSet = Array.isArray(input.excludeSet) ? input.excludeSet : [];
const doneCellsIn = Array.isArray(input.doneCells) ? input.doneCells : [];
const deferredFindings = Array.isArray(input.deferredFindings) ? input.deferredFindings : [];

// Enumerate this run's pending cells, then split against the per-run cap (the deterministic resume).
// Gap cells ARE the criterion ids; standard cells are (module x dir), with `thorough` appending
// BLINDSPOT_CELL last. Either way the cap + done/pending lists drive resume identically. `batches` is
// the FIND fan-out unit: a module-over-its-dirs batch, or a single-criterion batch.
let runCells;
let overflowCells;
let runHasBlindspot;
let batches;
if (isGap) {
  const gapCells = cellsFromCriteria(input.criteria, doneCellsIn);
  const split = applyCellBudget(gapCells, input.maxCellsPerRun);
  runCells = split.run.map((c) => c.key);
  overflowCells = split.overflow.map((c) => c.key);
  runHasBlindspot = false; // the blind-spot sweep is a standard-mode `thorough` stage
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
  `audit ${isGap ? "mode=gap" : `dial=${dial}`} depth=${depth} -- ${batches.length} ` +
    `${isGap ? "criterion" : "module"} batch(es) this run` +
    `${runHasBlindspot ? " + the blind-spot sweep" : ""}; ` +
    `${overflowCells.length} deferred to resume.`,
);

// --- FIND: one lens call per batch at the dialed depth, in parallel. Standard: a lens-reviewer over
// a module's dirs, and at `thorough` the blind-spot sweep joins the SAME parallel() as one more
// FIND-only task. Gap: a lens-reviewer over ONE criterion (static read). ---
phase("Find");
// FIND-phase guard. parallel() already resolves a throwing thunk to null; this wrapper makes the
// never-crash-the-run property LOCAL and auditable rather than resting on an out-of-repo contract.
// Either way a failed batch returns null and its cells go pending (PARTIAL). It spawns through the
// shared namespace fallback, so a batch is pending only after BOTH ids failed.
async function guardedAgent(prompt, opts) {
  try {
    return await agentWithNamespaceFallback(prompt, opts);
  } catch (e) {
    log(`FIND batch failed (${opts && opts.label ? opts.label : "?"}): ${e && e.message ? e.message : e} -- its cells go pending`);
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
      // Gap mode REQUIRES the per-criterion verdict at the boundary; standard mode has no
      // criterion, so it keeps LENS_SCHEMA unchanged.
      schema: isGap ? GAP_LENS_SCHEMA : LENS_SCHEMA,
      label: isGap ? `gap:${batch.module}` : `lens:${batch.module}`,
      phase: "Find",
    },
  ),
);
if (runHasBlindspot) {
  findTasks.push(() =>
    guardedAgent(buildBlindspotPrompt(input.scopeDirs, excludeSet), {
      agentType: nsAgent("lens-reviewer"),
      schema: LENS_SCHEMA,
      label: "blindspot:(scope)",
      phase: "Find",
    }),
  );
}
const findResults = await parallel(findTasks);

// A batch that errored (null return) sends its cells to pendingCells and the run goes PARTIAL --
// never a silent skip. Surviving batches contribute their findings, each tagged with its module.
const failedCells = [];
const rawFindings = [];
// Gap mode only: the schema-enforced met/partial/missing verdict, keyed by criterion id
// (batch.module IS criterion.id -- engine-assigned, never a model-authored key). A failed batch
// records NOTHING: its cell is already in failedCells, and THAT is what makes the criterion read
// "not checked" rather than carrying a verdict nobody produced.
const verdictByCriterion = new Map();
batches.forEach((batch, i) => {
  const r = findResults[i];
  if (!r || !Array.isArray(r.findings)) {
    log(`lens batch '${batch.module}' did not run (no usable return) -- its cells go pending.`);
    for (const cell of batch.cells) {
      failedCells.push(cell);
    }
    return;
  }
  // The batch source is the criterion id in gap mode, the module's doc path in standard mode. Each
  // finding carries its source so the verifier and the fence can cite it.
  const source = isGap ? `criterion ${batch.module}` : modulePath(batch.module);
  if (isGap) {
    verdictByCriterion.set(batch.module, r.criterionVerdict);
  }
  for (const finding of r.findings) {
    rawFindings.push({ ...finding, sourceModule: source, modules: [source] });
  }
});

// The blind-spot sweep's result is the LAST element of findResults. It joins the same dedup -> prune
// -> verify path with no special handling -- its findings carry issueClass like a lens return,
// sourceModule is the blindspot marker. A failed sweep sends the pseudo-cell to pending (logged) and
// the run goes PARTIAL -- never a silent skip.
if (runHasBlindspot) {
  const blindspotResult = findResults[findResults.length - 1];
  if (!blindspotResult || !Array.isArray(blindspotResult.findings)) {
    log("blind-spot sweep did not run (no usable return) -- the (scope) pseudo-cell goes pending.");
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

// The synthesis "audited scope" framing is mode-aware, though the consolidate/tier/tag logic is
// identical: standard passes module doc paths + scopeDirs, gap passes criterion ids + a fixed label
// (a gap run has no dir scope -- its criteria ARE the scope).
const synthesisModules = isGap ? input.criteria.map((c) => c.id) : modulesToPaths(input.modules);
const synthesisScope = isGap ? ["product-gap: intent vs implementation"] : input.scopeDirs;

let synthesis = await agentWithNamespaceFallback(
  buildSynthesisPrompt(dedupedFindings, synthesisModules, synthesisScope, isGap),
  { agentType: nsAgent("synthesizer-gate"), schema: SYNTHESIS_SCHEMA, label: "synthesis", phase: "Prune" },
);
if (!synthesis || !Array.isArray(synthesis.items)) {
  // Single-point seam: a null synthesis would discard the whole FIND sweep. Retry once before the
  // fail-loud terminal -- the throw stays; never proceed without the prune. The retry passes the
  // SAME isGap: a mode-less respawn would silently restore the engineering prompt (YAGNI prune +
  // test-baseline ADD) on exactly the runs a first synthesis failed.
  synthesis = await agentWithNamespaceFallback(
    buildSynthesisPrompt(dedupedFindings, synthesisModules, synthesisScope, isGap),
    { agentType: nsAgent("synthesizer-gate"), schema: SYNTHESIS_SCHEMA, label: "synthesis:respawn", phase: "Prune" },
  );
}
if (!synthesis || !Array.isArray(synthesis.items)) {
  // The run cannot proceed honestly without the synthesis prune.
  throw new Error("audit prune: synthesis agent returned no usable items after a retry -- cannot proceed.");
}

const annotated = applySynthesisItems(dedupedFindings, synthesis.items);
let survivors = applyPrune(annotated, synthesis.cuts);

// Surface a synthesized missing-test-baseline item when synthesis declared one and dedup/prune did
// not already carry it (added to VERIFY like any finding). NEVER in gap mode -- it maps to no
// acceptance criterion, so the `!isGap` guard holds even if a non-conforming synthesis declares one
// anyway: the prompt is guidance, this is the gate.
if (
  !isGap &&
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

// --- PRUNE (thorough only): the adversarial yagni-sentinel sweep over the survivors -- the
// independent skeptic argues the set down from a clean context, then applyPrune AGAIN (the
// TEST_BASELINE_CLASS protection holds here too). A thorough run that skipped its adversarial prune
// must NOT pretend it ran one: on a null sentinel after one retry, throw. Absent on quick/standard.
if (dial === "thorough") {
  let sentinel = await agentWithNamespaceFallback(buildSentinelPrompt(survivors), {
    agentType: nsAgent("yagni-sentinel"),
    schema: SENTINEL_SCHEMA,
    label: "sentinel",
    phase: "Prune",
  });
  if (!sentinel || !Array.isArray(sentinel.cuts)) {
    sentinel = await agentWithNamespaceFallback(buildSentinelPrompt(survivors), {
      agentType: nsAgent("yagni-sentinel"),
      schema: SENTINEL_SCHEMA,
      label: "sentinel:respawn",
      phase: "Prune",
    });
  }
  if (!sentinel || !Array.isArray(sentinel.cuts)) {
    throw new Error(
      "audit prune: the thorough adversarial yagni-sentinel returned no usable cut-list after a retry -- a thorough run must not pretend it ran the adversarial prune.",
    );
  }
  survivors = applyPrune(survivors, sentinel.cuts);
}

// Re-checked findings = every survivor PLUS any deferredFindings from a prior run, fed straight to
// VERIFY -- prior tags never exempt them from a fresh re-check. Resumed deferred findings never went
// through applySynthesisItems, so default their tier/tag here: a tier-less item silently vanished
// from the rendered tiers while the run-report still counted it (2026-06-11 dogfood).
const normalizedDeferred = deferredFindings.map((f) => ({
  ...f,
  tier: Number.isInteger(f && f.tier) ? f.tier : 2,
  tag: f && typeof f.tag === "string" && f.tag.length > 0 ? f.tag : "refactor",
}));
const toVerify = [...survivors, ...normalizedDeferred];

// --- VERIFY: exactly ONE finding-verifier per finding, in parallel. ---
phase("Verify");
const verifyTasks = toVerify.map((finding) => () =>
  spawnVerifier(buildVerifierInput(finding, excludeSet)),
);
const verifyResults = await parallel(verifyTasks);

const { kept, refutedCount, refutedRunningAs } = applyVerdicts(toVerify, verifyResults);
// Observability: a present verifier self-report that does not resolve to a KNOWN family is LOGGED,
// never silently degraded -- the disclosure becomes UNRESOLVED, not asserted same-model. The
// REFUTING verifiers are swept in too: they voted in the fold, so they are logged.
for (const reported of kept
  .map((f) => (f && f.verifierRunningAs != null ? f.verifierRunningAs : null))
  .concat(refutedRunningAs)) {
  if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
    log(
      `audit: a finding-verifier self-reported an UNRECOGNIZED model family ` +
        `(${JSON.stringify(reported)}) -- reported as unresolved, no cross-model claim made.`,
    );
  }
}
const summary = verificationSummary(kept, refutedCount, input.builderFamily, refutedRunningAs);

// --- Assemble the structured result (the Phase-3 contract; no timestamps -- the orchestrator stamps
// the date). doneCells = input done + this run's swept cells (failed batches stay pending);
// pendingCells = overflow + failed.
const sweptCells = runCells.filter((c) => !failedCells.includes(c));
const doneCells = [...doneCellsIn, ...sweptCells];
const pendingCells = [...overflowCells, ...failedCells];
const items = mergePriorItems(kept.map(toResultItem), input.priorItems);
// How many the merge carried in from a prior pass -- read off the merge's OWN output, never a second
// copy of its filter, so the run-report's numbers reconcile with the list it renders.
const carriedForward = items.length - kept.length;

// Per-lens coverage (standard mode only -- see lensCoverage). Fed the DEDUPED findings, i.e. raw
// lens output after coded dedup and before synthesis prune, so it reports what each lens actually
// surfaced rather than what survived prioritization.
const lensCoverageReport = isGap
  ? undefined
  : lensCoverage(input.modules, pendingCells, dedupedFindings);

// Per-criterion coverage (gap mode only -- see criterionCoverage). Fed `items`, the SURVIVING set
// the fence renders and NOT the deduped set lensCoverage uses, because evidence outranks the
// reviewer's verdict: a finding refuted at VERIFY or cut at PRUNE has stopped being evidence.
const criterionCoverageReport = isGap
  ? criterionCoverage(input.criteria, pendingCells, verdictByCriterion, items)
  : undefined;

const result = {
  status: runStatus(pendingCells),
  // A COMPLETE cell sweep can still carry unverified findings -- say so mechanically.
  verificationIncomplete: summary.deferred > 0,
  level: dial,
  depth,
  doneCells,
  pendingCells,
  items,
  refutedCount,
  verification: { ...summary, carried: carriedForward },
  ...(lensCoverageReport ? { lensCoverage: lensCoverageReport } : {}),
  ...(criterionCoverageReport ? { criterionCoverage: criterionCoverageReport } : {}),
};

// The complete fence body the skill writes between the harness-audit:backlog markers (Phase 3 is
// file mechanics: write this string, replace {{DATE}} with today's date). renderBacklogFence + its
// unit tests own the format -- no free-hand prose, no drift.
return { ...result, renderedBacklog: renderBacklogFence(result) };
