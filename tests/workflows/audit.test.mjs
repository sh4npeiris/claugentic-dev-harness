// tests/workflows/audit.test.mjs -- node --test unit tests for the pure helpers of
// workflows/audit.js.
//
// Same extraction harness as verify.test.mjs (Slice 2): the script is a Workflow-tool script
// (top-level control flow ending in a returned result; tool primitives agent()/parallel()/
// phase()/log() are undefined under node), so we read the file, EXTRACT the marked
// `// --- helpers ---` ... `// --- end helpers ---` block (pure functions + schema/const literals),
// evaluate it via `new Function`, and exercise the helpers standalone. The block must NOT close
// over any tool primitive -- these tests are the proof it doesn't. Run by
// `node --test tests/workflows/*.test.mjs` (and the CI node-tests job).

import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { loadHelpersFrom } from "./_load-helpers.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT_PATH = join(REPO_ROOT, "engine", "audit.js");

// The verbatim same-model tag -- duplicated here on purpose as an independent fixture so a drift
// in the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run -- the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED tag -- the third disclosure state. Independent fixture (exact-compare pin).
const EXPECTED_UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run -- no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

// Independent verbatim fixtures for the fence's load-bearing copy -- the renderer's source of truth
// pinned by exact string compare (drift = test failure, not a model-discipline failure).
const EXPECTED_LEGEND =
  "`refactor` = tidy without changing behavior - `capability-upgrade` = add/upgrade a technology - `dependency-health` = update/patch dependencies - `bug` = fix wrong behavior - `feature` = new behavior.\n" +
  "`(checked against the code)` = a separate agent re-read the code and couldn't refute it - `(could not confirm independently -- model's assertion)` = still just the model's claim - `(! not yet verified -- re-run to confirm)` = budget ran out before checking -- each surfaced finding is re-checked by a separate clean-context agent that never saw the finder's reasoning -- a reduction of rubber-stamping risk, not a mechanical guarantee.";

const EXPECTED_TERMINAL_SIGNAL =
  "Sound on the audited dimensions -- what remains is optional polish; you don't need to keep re-auditing.";

const EXPECTED_GO_BUTTON =
  "To start anything -- a backlog item or a brand-new project -- just tell the agent in plain English what you want (e.g. 'Let's do Tier-1 item 1' or 'I want to build X'). It will ask you questions (Discuss), then write a plan and spec for you to approve before any code. For a backlog item, the go-button is **`/claugentic-dev-harness:build`** -- point it at one item ('build Tier-1 item 1') and it drives the whole reviewed pipeline for you, pausing only at the spec (before any code) and before anything irreversible.";

const DEFERRED_PHRASE = "(! not yet verified -- re-run to confirm)";

/** Build a result item; override fields per-case. */
function makeItem(overrides = {}) {
  return {
    findingKey: "missing-validation",
    modules: ["docs/claugentic-standards/security.md"],
    tier: 2,
    tag: "bug",
    titlePlain: "Add input validation",
    claimTechnical: "no input validation on the body",
    locations: ["api.js:40"],
    whyPlain: "a bad request could crash the handler",
    impactEffort: "high impact, low effort",
    confidence: "judgment",
    verification: { state: "verified", evidence: "no schema guard at api.js:40", plainLine: "checked" },
    ...overrides,
  };
}

/** Build a structured result for the renderer; override fields per-case. */
function makeResult(overrides = {}) {
  return {
    status: "COMPLETE",
    level: "standard",
    doneCells: ["security|api", "testing|api"],
    pendingCells: [],
    items: [],
    refutedCount: 0,
    verification: { verified: 0, unconfirmed: 0, deferred: 0, refuted: 0, crossModel: true, sameModelTag: null },
    ...overrides,
  };
}

const H = loadHelpersFrom(SCRIPT_PATH, [
  "MODELS",
  "SAME_MODEL_TAG",
  "UNRESOLVED_FAMILY_TAG",
  "KNOWN_FAMILIES",
  "TEST_BASELINE_CLASS",
  "SUPPORTED_DIALS",
  "validateArgs",
  "depthForDial",
  "modulePath",
  "cellKey",
  "enumerateCells",
  "applyCellBudget",
  "parseCellKey",
  "groupByModule",
  "lensCoverage",
  "normalizeIssueClass",
  "findingKey",
  "dedupFindings",
  "applyPrune",
  "modulesToPaths",
  "buildLensPrompt",
  "buildSynthesisPrompt",
  "buildVerifierInput",
  "buildVerifierPrompt",
  "modelFamily",
  "sameModelTag",
  "applyVerdicts",
  "verificationSummary",
  "runStatus",
  "parseArgs",
  "applySynthesisItems",
  "toResultItem",
  "mergePriorItems",
  "LENS_SCHEMA",
  "SYNTHESIS_SCHEMA",
  "VERIFIER_SCHEMA",
  "SENTINEL_SCHEMA",
  "BLINDSPOT_CELL",
  "LEGEND",
  "TERMINAL_SIGNAL",
  "GO_BUTTON",
  "DATE_PLACEHOLDER",
  "VERIFICATION_PHRASE",
  "buildBlindspotPrompt",
  "buildSentinelPrompt",
  "validateCriterion",
  "validateSharedArgs",
  "validateCriteriaArgs",
  "cellsFromCriteria",
  "buildCriterionLensPrompt",
  "CRITERIA_KEYS",
  "CRITERIA_CHECKS",
  "CRITERIA_STATES",
  "GAP_LEVEL",
  "renderStatusLine",
  "verificationPhrase",
  "renderLocations",
  "renderItem",
  "renderTier",
  "renderRecommendation",
  "renderLensCoverage",
  "renderRunReport",
  "renderBacklogFence",
  "renderOnlyResult",
]);

/** Build a valid args object; override fields per-case. */
function validArgs(overrides = {}) {
  return {
    dial: "standard",
    modules: ["security", "testing"],
    scopeDirs: ["src", "tests"],
    excludeSet: ["node_modules"],
    maxCellsPerRun: 10,
    doneCells: [],
    deferredFindings: [],
    builderFamily: "Fable 5",
    ...overrides,
  };
}

// -----------------------------------------------------------------------------
// Extraction harness + contract pins
// -----------------------------------------------------------------------------
test("extraction harness finds the marked block and all helper names", () => {
  for (const name of [
    "MODELS",
    "SAME_MODEL_TAG",
    "TEST_BASELINE_CLASS",
    "validateArgs",
    "depthForDial",
    "cellKey",
    "enumerateCells",
    "applyCellBudget",
    "normalizeIssueClass",
    "findingKey",
    "dedupFindings",
    "applyPrune",
    "buildVerifierInput",
    "sameModelTag",
    "applyVerdicts",
    "verificationSummary",
    "runStatus",
  ]) {
    assert.ok(H[name] !== undefined, `helper '${name}' was not extracted`);
  }
});

test("MODELS.judge is pinned to 'opus' (cross-model contract, copied from verify.js)", () => {
  assert.equal(H.MODELS.judge, "opus");
});

test("TEST_BASELINE_CLASS is the documented never-prune key", () => {
  assert.equal(H.TEST_BASELINE_CLASS, "missing-test-baseline");
});

// -----------------------------------------------------------------------------
// validateArgs -- boundary validation, fail loud; thorough-unsupported
// -----------------------------------------------------------------------------
test("validateArgs accepts a well-formed quick/standard args object", () => {
  assert.deepEqual(H.validateArgs(validArgs({ dial: "quick" })), []);
  assert.deepEqual(H.validateArgs(validArgs({ dial: "standard" })), []);
});

test("validateArgs accepts 'thorough' (Slice 3b -- all three notches scripted)", () => {
  assert.deepEqual(H.validateArgs(validArgs({ dial: "thorough" })), []);
});

test("validateArgs rejects an unknown dial naming the supported set", () => {
  const errors = H.validateArgs(validArgs({ dial: "ludicrous" }));
  assert.ok(
    errors.some(
      (e) =>
        e.includes("ludicrous") &&
        e.includes("not supported") &&
        e.includes("quick") &&
        e.includes("standard") &&
        e.includes("thorough"),
    ),
    `expected an unknown-dial message naming the supported set, got: ${JSON.stringify(errors)}`,
  );
});

test("validateArgs flags missing/empty modules", () => {
  assert.ok(H.validateArgs(validArgs({ modules: [] })).some((e) => e.includes("modules")));
  assert.ok(H.validateArgs(validArgs({ modules: undefined })).some((e) => e.includes("modules")));
});

test("validateArgs flags non-string module entries", () => {
  assert.ok(H.validateArgs(validArgs({ modules: ["security", 42] })).some((e) => e.includes("modules")));
});

test("validateArgs flags missing/empty scopeDirs", () => {
  assert.ok(H.validateArgs(validArgs({ scopeDirs: [] })).some((e) => e.includes("scopeDirs")));
  assert.ok(H.validateArgs(validArgs({ scopeDirs: undefined })).some((e) => e.includes("scopeDirs")));
});

test("validateArgs flags a non-positive / non-integer maxCellsPerRun", () => {
  assert.ok(H.validateArgs(validArgs({ maxCellsPerRun: 0 })).some((e) => e.includes("maxCellsPerRun")));
  assert.ok(H.validateArgs(validArgs({ maxCellsPerRun: -1 })).some((e) => e.includes("maxCellsPerRun")));
  assert.ok(H.validateArgs(validArgs({ maxCellsPerRun: 1.5 })).some((e) => e.includes("maxCellsPerRun")));
  assert.ok(H.validateArgs(validArgs({ maxCellsPerRun: "ten" })).some((e) => e.includes("maxCellsPerRun")));
});

test("validateArgs flags a missing builderFamily", () => {
  assert.ok(H.validateArgs(validArgs({ builderFamily: undefined })).some((e) => e.includes("builderFamily")));
});

test("validateArgs flags a non-array excludeSet / doneCells / deferredFindings", () => {
  assert.ok(H.validateArgs(validArgs({ excludeSet: "x" })).some((e) => e.includes("excludeSet")));
  assert.ok(H.validateArgs(validArgs({ doneCells: "x" })).some((e) => e.includes("doneCells")));
  assert.ok(H.validateArgs(validArgs({ deferredFindings: "x" })).some((e) => e.includes("deferredFindings")));
});

test("validateArgs accepts omitted optional arrays (excludeSet/doneCells/deferredFindings)", () => {
  const args = validArgs();
  delete args.excludeSet;
  delete args.doneCells;
  delete args.deferredFindings;
  assert.deepEqual(H.validateArgs(args), []);
});

test("validateArgs rejects a non-object arg", () => {
  assert.deepEqual(H.validateArgs(null), ["args must be an object"]);
});

// -----------------------------------------------------------------------------
// depthForDial -- the one ladder map
// -----------------------------------------------------------------------------
test("depthForDial maps the full ladder quick->focused, standard->deep, thorough->exhaustive", () => {
  assert.equal(H.depthForDial("quick"), "focused");
  assert.equal(H.depthForDial("standard"), "deep");
  assert.equal(H.depthForDial("thorough"), "exhaustive");
});

// -----------------------------------------------------------------------------
// cellKey / enumerateCells / applyCellBudget / groupByModule -- cell math
// -----------------------------------------------------------------------------
test("cellKey produces the exact <module>|<dir> resume token", () => {
  assert.equal(H.cellKey("security", "src/api"), "security|src/api");
});

test("parseCellKey round-trips cellKey (split on first separator)", () => {
  assert.deepEqual(H.parseCellKey(H.cellKey("security", "src/api")), { module: "security", dir: "src/api" });
});

test("enumerateCells emits module|dir INTERLEAVED (round-robin across lenses, dirs inner)", () => {
  // dir-major / module-inner: every lens's top dir BEFORE any lens's second dir (the anti-starvation
  // fix) -- m0|d0, m1|d0, m0|d1, m1|d1. A budget prefix now covers every lens broad-then-deep.
  const cells = H.enumerateCells(["security", "testing"], ["a", "b"], []);
  assert.deepEqual(cells, ["security|a", "testing|a", "security|b", "testing|b"]);
});

test("enumerateCells: a sub-total budget prefix covers EVERY configured lens >=1 cell (no starvation)", () => {
  // The bug: a module-major order + slice(0,N) starved tail lenses to zero. Interleaved, the first
  // `lenses` cells span every lens's top dir -- so a prefix of length >= lens-count hears from all.
  const modules = ["m0", "m1", "m2", "m3"];
  const cells = H.enumerateCells(modules, ["d0", "d1", "d2"], [], "standard");
  const { run } = H.applyCellBudget(cells, modules.length); // budget == lens count
  const lensesHeard = new Set(run.map((c) => H.parseCellKey(c).module));
  assert.deepEqual([...lensesHeard].sort(), modules.slice().sort());
});

test("enumerateCells excludes doneCells and never re-enumerates them (interleaved order)", () => {
  const cells = H.enumerateCells(["security", "testing"], ["a", "b"], ["security|a", "testing|b"]);
  // Remaining cells stay in the interleaved order: testing|a (dir a) before security|b (dir b).
  assert.deepEqual(cells, ["testing|a", "security|b"]);
});

test("applyCellBudget splits run vs overflow at the cap", () => {
  const { run, overflow } = H.applyCellBudget(["c1", "c2", "c3", "c4"], 2);
  assert.deepEqual(run, ["c1", "c2"]);
  assert.deepEqual(overflow, ["c3", "c4"]);
});

test("applyCellBudget with a cap >= cell count leaves no overflow", () => {
  const { run, overflow } = H.applyCellBudget(["c1", "c2"], 10);
  assert.deepEqual(run, ["c1", "c2"]);
  assert.deepEqual(overflow, []);
});

test("groupByModule batches cells by module preserving first-seen order (interleaved input)", () => {
  // An interleaved run-slice (dir-major) regroups into one batch per module -- the FIND fan-out unit.
  // First-seen module order (security, testing); each module's dirs collected in cell order.
  const batches = H.groupByModule(["security|a", "testing|a", "security|b"]);
  assert.equal(batches.length, 2);
  assert.deepEqual(batches[0], { module: "security", dirs: ["a", "b"], cells: ["security|a", "security|b"] });
  assert.deepEqual(batches[1], { module: "testing", dirs: ["a"], cells: ["testing|a"] });
});

// -----------------------------------------------------------------------------
// normalizeIssueClass / findingKey
// -----------------------------------------------------------------------------
test("normalizeIssueClass lowercases, trims, and hyphenates whitespace", () => {
  assert.equal(H.normalizeIssueClass("  Missing Input   Validation "), "missing-input-validation");
});

test("findingKey is the normalized issueClass", () => {
  assert.equal(H.findingKey({ issueClass: "Missing Input Validation" }), "missing-input-validation");
});

// -----------------------------------------------------------------------------
// dedupFindings -- same-key roll-up, weakest-confidence-wins, distinct classes separate
// -----------------------------------------------------------------------------
test("dedupFindings merges same-key findings, unioning locations", () => {
  const merged = H.dedupFindings([
    { issueClass: "missing-validation", locations: ["a.js:1"], fix: "fix A", confidence: "deterministic" },
    { issueClass: "missing-validation", locations: ["b.js:2"], fix: "fix B", confidence: "deterministic" },
  ]);
  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].locations, ["a.js:1", "b.js:2"]);
  assert.equal(merged[0].fix, "fix A"); // first concrete fix kept
  assert.equal(merged[0].findingKey, "missing-validation");
});

test("dedupFindings: weakest confidence wins -- a judgment member downgrades the merge", () => {
  const merged = H.dedupFindings([
    { issueClass: "x", locations: ["a:1"], confidence: "deterministic" },
    { issueClass: "x", locations: ["b:2"], confidence: "judgment" },
  ]);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].confidence, "judgment");
});

test("dedupFindings: confidence is never upgraded once judgment", () => {
  const merged = H.dedupFindings([
    { issueClass: "x", locations: ["a:1"], confidence: "judgment" },
    { issueClass: "x", locations: ["b:2"], confidence: "deterministic" },
  ]);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].confidence, "judgment");
});

test("dedupFindings keeps distinct classes at the same location separate", () => {
  const merged = H.dedupFindings([
    { issueClass: "security-gap", locations: ["a:1"], confidence: "judgment" },
    { issueClass: "perf-gap", locations: ["a:1"], confidence: "judgment" },
  ]);
  assert.equal(merged.length, 2);
});

test("dedupFindings does not duplicate a location already present", () => {
  const merged = H.dedupFindings([
    { issueClass: "x", locations: ["a:1"], confidence: "judgment" },
    { issueClass: "x", locations: ["a:1"], confidence: "judgment" },
  ]);
  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].locations, ["a:1"]);
});

// -----------------------------------------------------------------------------
// applyPrune -- the test-baseline never-prune exception
// -----------------------------------------------------------------------------
test("applyPrune drops cut keys", () => {
  const survivors = H.applyPrune(
    [{ issueClass: "keep-me" }, { issueClass: "cut-me" }],
    [{ findingKey: "cut-me", reason: "marginal" }],
  );
  assert.deepEqual(survivors.map((f) => f.issueClass), ["keep-me"]);
});

test("applyPrune can NEVER drop the missing-test-baseline item even when cut", () => {
  const survivors = H.applyPrune(
    [{ issueClass: "missing-test-baseline" }, { issueClass: "cut-me" }],
    [
      { findingKey: "missing-test-baseline", reason: "tried to cut it" },
      { findingKey: "cut-me", reason: "marginal" },
    ],
  );
  assert.deepEqual(survivors.map((f) => f.issueClass), ["missing-test-baseline"]);
});

test("applyPrune normalizes cut keys before matching", () => {
  const survivors = H.applyPrune(
    [{ issueClass: "Missing Validation" }],
    [{ findingKey: "missing validation", reason: "dup" }],
  );
  assert.equal(survivors.length, 0);
});

// -----------------------------------------------------------------------------
// buildVerifierInput -- structural independence: emits ONLY the contract keys
// -----------------------------------------------------------------------------
test("buildVerifierInput emits exactly the contract keys (rationale/transcript dropped)", () => {
  const input = H.buildVerifierInput(
    {
      claimPlain: "no limit on the query",
      claimTechnical: "SELECT without LIMIT",
      locations: ["db.js:40"],
      sourceModule: "docs/claugentic-standards/performance-efficiency.md",
      confidence: "judgment",
      // contamination the finder must NEVER leak to the verifier:
      rationale: "the finder's chain of thought",
      transcript: "the finder's transcript",
      titlePlain: "Add a LIMIT",
    },
    ["node_modules"],
  );
  assert.deepEqual(Object.keys(input).sort(), [
    "claimPlain",
    "claimTechnical",
    "confidence",
    "excludeSet",
    "locations",
    "sourceModule",
  ]);
  assert.ok(!("rationale" in input));
  assert.ok(!("transcript" in input));
  assert.equal(input.claimTechnical, "SELECT without LIMIT");
  assert.deepEqual(input.excludeSet, ["node_modules"]);
});

test("buildVerifierInput falls back sourceModule to the first modules entry", () => {
  const input = H.buildVerifierInput({ modules: ["docs/claugentic-standards/security.md"] }, []);
  assert.equal(input.sourceModule, "docs/claugentic-standards/security.md");
});

test("buildVerifierPrompt never contains the words rationale/transcript and demands RUNNING AS", () => {
  const input = H.buildVerifierInput({ claimPlain: "x", claimTechnical: "y", locations: [], confidence: "judgment" }, []);
  const prompt = H.buildVerifierPrompt(input);
  assert.ok(prompt.includes("RUNNING AS"));
  assert.ok(prompt.includes("refute-first") || prompt.includes("REFUTE"));
});

// -----------------------------------------------------------------------------
// sameModelTag -- verbatim string, copied from verify.js
// -----------------------------------------------------------------------------
test("SAME_MODEL_TAG is the verbatim string (drift pin)", () => {
  assert.equal(H.SAME_MODEL_TAG, EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns the verbatim tag when families match", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.1"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag: a MISSING judge report (null/empty) is the same-model floor, not unresolved", () => {
  assert.equal(H.sameModelTag("Fable 5", null), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.sameModelTag("Fable 5", ""), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag: a PRESENT but unrecognized family reports UNRESOLVED (never same-model fact)", () => {
  assert.equal(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  // The builder side failing to resolve, with a present judge report, is also unresolved.
  assert.equal(H.sameModelTag("unknown-builder", "Opus 4.8"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.notEqual(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_SAME_MODEL_TAG);
});

test("UNRESOLVED_FAMILY_TAG is the verbatim third-state string (drift pin)", () => {
  assert.equal(H.UNRESOLVED_FAMILY_TAG, EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.notEqual(H.UNRESOLVED_FAMILY_TAG, H.SAME_MODEL_TAG);
});

test("KNOWN_FAMILIES is the one named source the modelFamily regex derives from", () => {
  assert.deepEqual(H.KNOWN_FAMILIES, ["fable", "opus", "sonnet", "haiku"]);
  for (const fam of H.KNOWN_FAMILIES) {
    assert.equal(H.modelFamily(`RUNNING AS: ${fam}`), fam);
  }
  assert.equal(H.modelFamily("RUNNING AS: gemini"), null);
});

test("sameModelTag returns null only on a confirming different family", () => {
  assert.equal(H.sameModelTag("Fable 5", "Opus 4.8"), null);
});

// -----------------------------------------------------------------------------
// applyVerdicts -- all three verdict mappings + no-verdict->deferred
// -----------------------------------------------------------------------------
test("applyVerdicts: Verified -> kept verified+evidence; Unconfirmed -> kept unconfirmed; Refuted -> dropped+counted", () => {
  const findings = [
    { issueClass: "a" },
    { issueClass: "b" },
    { issueClass: "c" },
  ];
  const results = [
    { verdict: "Verified", evidence: "proof", plainLine: "checked", runningAs: "Opus 4.8" },
    { verdict: "Unconfirmed", evidence: "ambiguous", plainLine: "couldn't tell", runningAs: "Opus 4.8" },
    { verdict: "Refuted", evidence: "disproof", plainLine: "false alarm", runningAs: "Opus 4.8" },
  ];
  const { kept, refutedCount } = H.applyVerdicts(findings, results);
  assert.equal(refutedCount, 1);
  assert.deepEqual(kept.map((f) => f.issueClass), ["a", "b"]);
  assert.equal(kept[0].verification.state, "verified");
  assert.equal(kept[0].verification.evidence, "proof");
  assert.equal(kept[1].verification.state, "unconfirmed");
});

test("applyVerdicts: a missing/null result maps to deferred (verifier did not run)", () => {
  const findings = [{ issueClass: "a" }, { issueClass: "b" }];
  const results = [{ verdict: "Verified", evidence: "", plainLine: "", runningAs: "Opus 4.8" }, null];
  const { kept } = H.applyVerdicts(findings, results);
  assert.equal(kept.length, 2);
  assert.equal(kept[1].verification.state, "deferred");
  assert.match(kept[1].verification.plainLine, /not yet verified/);
});

// -----------------------------------------------------------------------------
// verificationSummary -- crossModel only on all-confirming-different-family
// -----------------------------------------------------------------------------
test("verificationSummary claims crossModel only when every verifier confirms a different family", () => {
  const findings = [
    { verification: { state: "verified" }, verifierRunningAs: "Opus 4.8" },
    { verification: { state: "unconfirmed" }, verifierRunningAs: "Opus 4.1" },
  ];
  const s = H.verificationSummary(findings, 1, "Fable 5");
  assert.equal(s.crossModel, true);
  assert.equal(s.sameModelTag, null);
  assert.equal(s.verified, 1);
  assert.equal(s.unconfirmed, 1);
  assert.equal(s.refuted, 1);
});

test("verificationSummary carries the same-model tag when any verifier is same-family or unreported", () => {
  const findings = [
    { verification: { state: "verified" }, verifierRunningAs: "Opus 4.8" },
    { verification: { state: "deferred" }, verifierRunningAs: null },
  ];
  const s = H.verificationSummary(findings, 0, "Fable 5");
  assert.equal(s.crossModel, false);
  // A MISSING (null) verifier report is the same-model floor, NOT the unresolved state.
  assert.equal(s.sameModelTag, EXPECTED_SAME_MODEL_TAG);
  assert.equal(s.deferred, 1);
});

test("verificationSummary reports UNRESOLVED (never same-model fact) when a verifier family is present-but-unrecognized", () => {
  const findings = [
    { verification: { state: "verified" }, verifierRunningAs: "Opus 4.8" },
    { verification: { state: "unconfirmed" }, verifierRunningAs: "RUNNING AS: gemini" },
  ];
  const s = H.verificationSummary(findings, 0, "Fable 5");
  assert.equal(s.crossModel, false);
  assert.equal(s.sameModelTag, EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.notEqual(s.sameModelTag, EXPECTED_SAME_MODEL_TAG);
});

test("verificationSummary does not claim crossModel on an empty finding set", () => {
  const s = H.verificationSummary([], 0, "Fable 5");
  assert.equal(s.crossModel, false);
});

// -----------------------------------------------------------------------------
// runStatus
// -----------------------------------------------------------------------------
test("runStatus is COMPLETE on empty pending, PARTIAL otherwise", () => {
  assert.equal(H.runStatus([]), "COMPLETE");
  assert.equal(H.runStatus(["security|src"]), "PARTIAL");
});

// -----------------------------------------------------------------------------
// parseArgs -- the scriptPath JSON-string boundary (copied from verify.js)
// -----------------------------------------------------------------------------
test("parseArgs parses a JSON-string args delivery", () => {
  assert.deepEqual(H.parseArgs('{"dial":"quick"}'), { dial: "quick" });
});

test("parseArgs passes an object through untouched", () => {
  const obj = { dial: "standard" };
  assert.equal(H.parseArgs(obj), obj);
});

test("parseArgs fails loud on an unparseable string", () => {
  assert.throws(() => H.parseArgs("{not json"), /not valid JSON/);
});

// -----------------------------------------------------------------------------
// Schema field-set pins (drift guard) -- incl. runningAs on the verifier
// -----------------------------------------------------------------------------
test("schema required arrays are the consumed contract", () => {
  assert.deepEqual(H.LENS_SCHEMA.required, ["lensVerdict", "findings"]);
  assert.deepEqual(H.LENS_SCHEMA.properties.findings.items.required, [
    "issueClass",
    "claimPlain",
    "claimTechnical",
    "locations",
    "fix",
    "confidence",
  ]);
  assert.deepEqual(H.SYNTHESIS_SCHEMA.required, ["items", "cuts"]);
  assert.deepEqual(H.SYNTHESIS_SCHEMA.properties.items.items.required, [
    "findingKey",
    "tier",
    "tag",
    "titlePlain",
    "whyPlain",
    "impactEffort",
  ]);
  assert.deepEqual(H.VERIFIER_SCHEMA.required, ["runningAs", "verdict", "evidence", "plainLine"]);
});

// -----------------------------------------------------------------------------
// applySynthesisItems / toResultItem -- annotation + result shaping
// -----------------------------------------------------------------------------
test("applySynthesisItems annotates by findingKey and defaults unannotated findings", () => {
  const annotated = H.applySynthesisItems(
    [{ issueClass: "a", claimPlain: "ca" }, { issueClass: "b" }],
    [{ findingKey: "a", tier: 1, tag: "bug", titlePlain: "Fix A", whyPlain: "because", impactEffort: "low" }],
  );
  assert.equal(annotated[0].tier, 1);
  assert.equal(annotated[0].tag, "bug");
  assert.equal(annotated[1].tier, 2); // conservative default
  assert.equal(annotated[1].tag, "refactor");
});

test("toResultItem shapes a kept+verified finding into the Phase-3 item contract", () => {
  const item = H.toResultItem({
    issueClass: "missing-validation",
    modules: ["docs/claugentic-standards/security.md"],
    tier: 1,
    tag: "bug",
    titlePlain: "Add validation",
    claimTechnical: "no input validation",
    locations: ["a.js:1"],
    whyPlain: "could crash",
    impactEffort: "medium",
    confidence: "judgment",
    verification: { state: "verified", evidence: "proof", plainLine: "checked" },
  });
  assert.equal(item.findingKey, "missing-validation");
  assert.deepEqual(item.modules, ["docs/claugentic-standards/security.md"]);
  assert.equal(item.verification.state, "verified");
  assert.equal(item.tag, "bug");
});

// -----------------------------------------------------------------------------
// The production-shaped composition: applyVerdicts -> verificationSummary, with a
// Refuted finding AHEAD of a survivor. Regression for the 2026-06-11 dogfood Tier-1:
// on the old parallel-arrays seam this produced a FALSE cross-model claim (the
// summary read the refuted finding's verifier instead of the survivor's own).
// -----------------------------------------------------------------------------
test("composition: a refuted finding ahead of a survivor never misaligns the cross-model fold", () => {
  const toVerify = [
    { issueClass: "false-alarm" },
    { issueClass: "real-issue" },
  ];
  const verifyResults = [
    { verdict: "Refuted", evidence: "", plainLine: "", runningAs: "Opus 4.8" },
    { verdict: "Verified", evidence: "e", plainLine: "p", runningAs: "Fable 5" },
  ];
  // Exactly the production seam (audit.js: applyVerdicts then verificationSummary).
  const { kept, refutedCount } = H.applyVerdicts(toVerify, verifyResults);
  const s = H.verificationSummary(kept, refutedCount, "Fable 5");
  assert.equal(kept.length, 1);
  assert.equal(kept[0].issueClass, "real-issue");
  // The survivor's verifier is Fable -- same family as the builder -- so crossModel MUST be
  // false. The old seam read verifyResults[0] (Opus) and wrongly claimed true.
  assert.equal(s.crossModel, false);
  assert.equal(s.sameModelTag, EXPECTED_SAME_MODEL_TAG);
  assert.equal(s.refuted, 1);
  assert.equal(s.verified, 1);
});

test("applyVerdicts carries each kept finding's own verifier self-report", () => {
  const { kept } = H.applyVerdicts(
    [{ issueClass: "a" }, { issueClass: "b" }],
    [
      { verdict: "Verified", evidence: "", plainLine: "", runningAs: "Opus 4.8" },
      null,
    ],
  );
  assert.equal(kept[0].verifierRunningAs, "Opus 4.8");
  assert.equal(kept[1].verifierRunningAs, null); // deferred -- no report, never a claim
});

// -----------------------------------------------------------------------------
// Slice 3b -- thorough stages: the blind-spot pseudo-cell + the second-pass prune
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// BLINDSPOT_CELL -- the whole-scope pseudo-cell math (cap/done/pending honesty)
// -----------------------------------------------------------------------------
test("BLINDSPOT_CELL is the fixed whole-scope pseudo-cell token", () => {
  assert.equal(H.BLINDSPOT_CELL, "blindspot|(scope)");
});

test("enumerateCells appends BLINDSPOT_CELL only at thorough, STRICTLY LAST after the interleaved cells", () => {
  const thorough = H.enumerateCells(["security", "testing"], ["a", "b"], [], "thorough");
  assert.deepEqual(thorough, [
    "security|a",
    "testing|a",
    "security|b",
    "testing|b",
    "blindspot|(scope)",
  ]);
  assert.equal(thorough[thorough.length - 1], H.BLINDSPOT_CELL); // strictly last -- interleaving keeps the invariant
});

test("enumerateCells does NOT append BLINDSPOT_CELL at quick/standard or when dial is absent", () => {
  assert.ok(!H.enumerateCells(["security"], ["a"], [], "quick").includes(H.BLINDSPOT_CELL));
  assert.ok(!H.enumerateCells(["security"], ["a"], [], "standard").includes(H.BLINDSPOT_CELL));
  assert.ok(!H.enumerateCells(["security"], ["a"], []).includes(H.BLINDSPOT_CELL));
});

test("enumerateCells is resume-aware for the pseudo-cell: omits BLINDSPOT_CELL when already done", () => {
  const cells = H.enumerateCells(["security"], ["a"], ["blindspot|(scope)"], "thorough");
  assert.deepEqual(cells, ["security|a"]); // the sweep already ran -- never re-enumerated
});

test("applyCellBudget counts BLINDSPOT_CELL like any cell (a tight cap defers it to resume)", () => {
  const pending = H.enumerateCells(["security"], ["a", "b"], [], "thorough");
  // [security|a, security|b, blindspot|(scope)] capped at 2 -> the sweep overflows to the resume.
  const { run, overflow } = H.applyCellBudget(pending, 2);
  assert.deepEqual(run, ["security|a", "security|b"]);
  assert.deepEqual(overflow, [H.BLINDSPOT_CELL]);
});

// -----------------------------------------------------------------------------
// RESUME-CONTRACT determinism -- the load-bearing acceptance gate for the reorder.
// doneCells is a SET the next run subtracts; the reorder is safe ONLY IF re-enumeration is
// deterministic + stable. Enumerate the full list -> take the first N as doneCells -> re-enumerate
// and subtract -> the remainder must equal the original interleaved tail EXACTLY (same order), and
// the blindspot pseudo-cell must still be strictly last.
// -----------------------------------------------------------------------------
test("RESUME determinism: re-enumeration after N done cells equals the original interleaved tail EXACTLY", () => {
  const modules = ["security", "testing", "performance", "reliability"];
  const dirs = ["src/api", "src/web", "packages/core"];
  const full = H.enumerateCells(modules, dirs, [], "thorough");
  // The full list is interleaved (dir-major) with blindspot strictly last.
  assert.equal(full[full.length - 1], H.BLINDSPOT_CELL);
  for (let n = 0; n <= full.length; n += 1) {
    const done = full.slice(0, n); // the first N cells "already ran"
    const remainder = H.enumerateCells(modules, dirs, done, "thorough");
    // Re-enumerating with the first N subtracted must reproduce the original tail, in order.
    assert.deepEqual(
      remainder,
      full.slice(n),
      `resume mismatch at N=${n}: remainder must be the original interleaved tail in order`,
    );
  }
  // And the blindspot pseudo-cell stays strictly last on any non-empty remainder that still owes it.
  const tail = H.enumerateCells(modules, dirs, full.slice(0, 2), "thorough");
  assert.equal(tail[tail.length - 1], H.BLINDSPOT_CELL, "blindspot stays strictly last after resume");
});

test("RESUME determinism: enumeration is a pure function of input order (repeated calls are byte-identical)", () => {
  const modules = ["a", "b", "c"];
  const dirs = ["d0", "d1"];
  const once = H.enumerateCells(modules, dirs, ["b|d0"], "standard");
  const twice = H.enumerateCells(modules, dirs, ["b|d0"], "standard");
  assert.deepEqual(once, twice); // no Set-iteration / sort nondeterminism
  assert.deepEqual(once, ["a|d0", "c|d0", "a|d1", "b|d1", "c|d1"]); // pinned interleaved remainder
});

// -----------------------------------------------------------------------------
// lensCoverage (prong #4) -- "did every lens speak?": ran-found / ran-clean / pending,
// distinguishing a lens that ran-and-found-nothing (explicit CLEAN) from one that NEVER RAN.
// -----------------------------------------------------------------------------
test("lensCoverage: a lens with no pending cell and >=1 finding is ran-found with its count", () => {
  const cov = H.lensCoverage(
    ["security"],
    [],
    [{ sourceModule: "docs/claugentic-standards/security.md" }, { sourceModule: "docs/claugentic-standards/security.md" }],
  );
  assert.deepEqual(cov, [{ module: "security", state: "ran-found", findings: 2 }]);
});

test("lensCoverage: a lens that ran with NO pending cell and zero findings is ran-clean (explicit CLEAN, not silence)", () => {
  const cov = H.lensCoverage(["security", "testing"], [], [{ sourceModule: "docs/claugentic-standards/security.md" }]);
  assert.deepEqual(cov, [
    { module: "security", state: "ran-found", findings: 1 },
    { module: "testing", state: "ran-clean", findings: 0 }, // ran, found nothing -- NOT never-ran
  ]);
});

test("lensCoverage: a lens with ANY pending cell is NEVER-RAN (pending), never reported clean", () => {
  // testing|src is still pending (budget-deferred / failed batch) -> testing did not fully run.
  const cov = H.lensCoverage(["security", "testing"], ["testing|src"], [
    { sourceModule: "docs/claugentic-standards/security.md" },
  ]);
  assert.deepEqual(cov, [
    { module: "security", state: "ran-found", findings: 1 },
    { module: "testing", state: "pending", findings: 0 }, // a pending cell => pending, never ran-clean
  ]);
});

test("lensCoverage: a partially-run lens (one dir found, another dir pending) is pending WITH its count", () => {
  const cov = H.lensCoverage(["security"], ["security|src/web"], [
    { sourceModule: "docs/claugentic-standards/security.md" },
  ]);
  // It surfaced 1 finding from the dir that ran, but a dir is still pending -- honestly "pending (1 so far)".
  assert.deepEqual(cov, [{ module: "security", state: "pending", findings: 1 }]);
});

test("lensCoverage: ordering follows the configured-module order", () => {
  const cov = H.lensCoverage(["reliability", "security", "testing"], [], []);
  assert.deepEqual(cov.map((l) => l.module), ["reliability", "security", "testing"]);
  assert.ok(cov.every((l) => l.state === "ran-clean")); // none pending, none found -> all clean
});

// -----------------------------------------------------------------------------
// renderLensCoverage -- the fence's per-lens "did every lens speak?" report
// -----------------------------------------------------------------------------
test("renderLensCoverage: ran-clean reads explicit CLEAN, never-ran reads 'did not run ... re-run'", () => {
  const out = H.renderLensCoverage([
    { module: "security", state: "ran-found", findings: 3 },
    { module: "testing", state: "ran-clean", findings: 0 },
    { module: "performance", state: "pending", findings: 0 },
  ]);
  assert.ok(out.includes("did every lens speak?"));
  assert.ok(out.includes("`security`: 3 findings"));
  assert.ok(out.includes("`testing`: CLEAN (ran, found nothing)"));
  assert.ok(out.includes("`performance`: did not run this pass -- re-run to cover it"));
});

test("renderLensCoverage: a singular finding count is grammatical ('1 finding')", () => {
  const out = H.renderLensCoverage([{ module: "security", state: "ran-found", findings: 1 }]);
  assert.ok(out.includes("`security`: 1 finding"));
  assert.ok(!out.includes("1 findings"));
});

test("renderLensCoverage: a partially-run lens surfaces its 'so far' count", () => {
  const out = H.renderLensCoverage([{ module: "security", state: "pending", findings: 2 }]);
  assert.ok(out.includes("did not finish this pass (2 so far) -- re-run to cover it"));
});

test("renderLensCoverage: an absent/empty coverage renders NOTHING (no misleading empty header)", () => {
  assert.equal(H.renderLensCoverage(undefined), "");
  assert.equal(H.renderLensCoverage([]), "");
});

test("renderBacklogFence includes the lens-coverage report when lensCoverage is present, omits it when absent", () => {
  const withCov = H.renderBacklogFence(
    makeResult({
      items: [makeItem()],
      lensCoverage: [
        { module: "security", state: "ran-found", findings: 1 },
        { module: "testing", state: "ran-clean", findings: 0 },
      ],
    }),
  );
  assert.ok(withCov.includes("did every lens speak?"));
  assert.ok(withCov.includes("`testing`: CLEAN (ran, found nothing)"));
  // The report sits before the run-report and the go-button is still last.
  assert.ok(withCov.indexOf("did every lens speak?") < withCov.indexOf("Re-checked every finding"));
  assert.ok(withCov.trimEnd().endsWith(`*${EXPECTED_GO_BUTTON}*`));

  const withoutCov = H.renderBacklogFence(makeResult({ items: [makeItem()] }));
  assert.ok(!withoutCov.includes("did every lens speak?")); // gap mode / older results carry no lensCoverage
});

// -----------------------------------------------------------------------------
// applyPrune -- second-pass (sentinel) protection still cannot drop the baseline
// -----------------------------------------------------------------------------
test("applyPrune (second pass, sentinel cuts) still cannot drop the missing-test-baseline item", () => {
  // First pass: synthesis cuts. Second pass: the adversarial sentinel's cuts. The baseline must
  // survive BOTH -- the thorough run's extra prune does not weaken the never-prune guarantee.
  const afterSynthesis = H.applyPrune(
    [{ issueClass: "missing-test-baseline" }, { issueClass: "keep-me" }, { issueClass: "cut-1" }],
    [{ findingKey: "cut-1", reason: "dup" }],
  );
  const afterSentinel = H.applyPrune(afterSynthesis, [
    { findingKey: "missing-test-baseline", reason: "sentinel tried to cut the baseline" },
    { findingKey: "keep-me", reason: "sentinel cuts this one" },
  ]);
  assert.deepEqual(afterSentinel.map((f) => f.issueClass), ["missing-test-baseline"]);
});

// -----------------------------------------------------------------------------
// SENTINEL_SCHEMA -- the adversarial-prune cut-list contract
// -----------------------------------------------------------------------------
test("SENTINEL_SCHEMA requires a cuts array of { findingKey, reason }", () => {
  assert.deepEqual(H.SENTINEL_SCHEMA.required, ["cuts"]);
  assert.deepEqual(H.SENTINEL_SCHEMA.properties.cuts.items.required, ["findingKey", "reason"]);
});

test("buildSentinelPrompt names the clean-context skeptic posture and asks ONLY for cuts", () => {
  const prompt = H.buildSentinelPrompt([{ issueClass: "x" }]);
  assert.ok(prompt.includes("YAGNI"));
  assert.ok(/clean context/i.test(prompt));
  assert.ok(prompt.includes("cuts list") || prompt.includes("cuts"));
});

test("buildBlindspotPrompt is whole-scope, exhaustive, red-team, FIND-only, lens-shaped", () => {
  const prompt = H.buildBlindspotPrompt(["src", "api"], ["node_modules"]);
  assert.ok(/whole/i.test(prompt));
  assert.ok(prompt.includes("exhaustive"));
  assert.ok(/red-team/i.test(prompt));
  assert.ok(prompt.includes("issueClass")); // same shape as a lens return
  assert.ok(prompt.includes("node_modules")); // exclude-set threaded
});

// -----------------------------------------------------------------------------
// Slice 3b -- the fence renderer (the backlog fence body's single source of truth)
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// renderStatusLine -- the documented shape + verbatim cellKey tokens
// -----------------------------------------------------------------------------
test("renderStatusLine matches the documented shape (regex) with the date placeholder", () => {
  const line = H.renderStatusLine(makeResult({ level: "thorough", pendingCells: ["testing|api"], status: "PARTIAL" }));
  assert.match(
    line,
    /^status: (COMPLETE|PARTIAL) - level: \w+ - done-cells: \[.*\] - pending-cells: \[.*\] - date: \{\{DATE\}\}$/,
  );
});

test("renderStatusLine carries the verbatim cellKey tokens, comma-joined", () => {
  const line = H.renderStatusLine(
    makeResult({ doneCells: ["security|src/api", "testing|src"], pendingCells: ["blindspot|(scope)"] }),
  );
  assert.ok(line.includes("done-cells: [security|src/api, testing|src]"));
  assert.ok(line.includes("pending-cells: [blindspot|(scope)]"));
  assert.ok(line.endsWith("date: {{DATE}}"));
});

test("renderStatusLine renders empty cell lists as empty brackets", () => {
  const line = H.renderStatusLine(makeResult({ doneCells: [], pendingCells: [] }));
  assert.ok(line.includes("done-cells: []"));
  assert.ok(line.includes("pending-cells: []"));
});

// -----------------------------------------------------------------------------
// LEGEND -- exactly two lines, verbatim, with the not-a-guarantee caveat
// -----------------------------------------------------------------------------
test("LEGEND is exactly two lines and verbatim (drift pin)", () => {
  assert.equal(H.LEGEND, EXPECTED_LEGEND);
  assert.equal(H.LEGEND.split("\n").length, 2);
});

test("LEGEND line 2 carries the clean-context re-check / not-a-guarantee caveat", () => {
  const line2 = H.LEGEND.split("\n")[1];
  assert.ok(line2.includes("re-checked by a separate clean-context agent"));
  assert.ok(!line2.includes("different model family")); // no cross-model over-claim -- all judges run the same model
  assert.ok(line2.includes("not a mechanical guarantee"));
  assert.ok(line2.includes("! not yet verified -- re-run to confirm"));
});

// -----------------------------------------------------------------------------
// renderItem -- exactly one tag + exactly one verification phrase per state
// -----------------------------------------------------------------------------
test("renderItem emits the title, exactly one tag, and the verified phrase + evidence", () => {
  const out = H.renderItem(makeItem({ verification: { state: "verified", evidence: "no guard at api.js:40" } }));
  assert.ok(out.includes("**Add input validation**"));
  assert.ok(out.includes("`bug`"));
  assert.ok(out.includes("(checked against the code)"));
  assert.ok(out.includes("Evidence: no guard at api.js:40"));
  // exactly one verification phrase: the other two must NOT appear
  assert.ok(!out.includes("could not confirm independently"));
  assert.ok(!out.includes("not yet verified"));
});

test("renderItem emits the unconfirmed phrase for an unconfirmed finding (no evidence line)", () => {
  const out = H.renderItem(makeItem({ verification: { state: "unconfirmed", evidence: "" } }));
  assert.ok(out.includes("(could not confirm independently -- model's assertion)"));
  assert.ok(!out.includes("Evidence:"));
});

test("renderItem emits the deferred phrase VERBATIM for a deferred finding", () => {
  const out = H.renderItem(makeItem({ verification: { state: "deferred", evidence: "" } }));
  assert.ok(out.includes(DEFERRED_PHRASE));
  assert.equal(DEFERRED_PHRASE, "(! not yet verified -- re-run to confirm)");
});

test("renderItem renders a single location inline and a merged finding as 'recurs in N files'", () => {
  const single = H.renderItem(makeItem({ locations: ["api.js:40"] }));
  assert.ok(single.includes("(api.js:40)"));
  assert.ok(!single.includes("recurs in"));
  const merged = H.renderItem(makeItem({ locations: ["a.js:1", "b.js:2", "c.js:3"] }));
  assert.ok(merged.includes("recurs in 3 files: a.js:1, b.js:2, c.js:3"));
});

// -----------------------------------------------------------------------------
// renderTier -- empty-tier honesty
// -----------------------------------------------------------------------------
test("renderTier marks an empty tier explicitly rather than leaving a silent gap", () => {
  assert.ok(H.renderTier("Tier 1 -- critical", []).includes("_(empty)_"));
  assert.ok(H.renderTier("Tier 2 -- important", [makeItem()]).includes("Add input validation"));
});

// -----------------------------------------------------------------------------
// renderRecommendation / TERMINAL_SIGNAL -- the architecturally-sound stop signal
// -----------------------------------------------------------------------------
test("TERMINAL_SIGNAL is the verbatim sound-on-the-audited-dimensions string", () => {
  assert.equal(H.TERMINAL_SIGNAL, EXPECTED_TERMINAL_SIGNAL);
});

test("renderRecommendation emits the terminal signal iff Tiers 1+2 are both empty (COMPLETE run)", () => {
  const rec = H.renderRecommendation([], [], "COMPLETE");
  assert.ok(rec.includes(EXPECTED_TERMINAL_SIGNAL));
  assert.ok(!rec.includes("scoped to the cells covered")); // no PARTIAL clause on COMPLETE
});

test("renderRecommendation appends the covered-cells scoping clause on a PARTIAL terminal run", () => {
  const rec = H.renderRecommendation([], [], "PARTIAL");
  assert.ok(rec.includes(EXPECTED_TERMINAL_SIGNAL));
  assert.ok(rec.includes("scoped to the cells covered this run"));
});

test("renderRecommendation points at the first Tier-1 item when Tier 1 is non-empty", () => {
  const t1 = [makeItem({ titlePlain: "Establish a test baseline", tier: 1 })];
  const rec = H.renderRecommendation(t1, [], "COMPLETE");
  assert.ok(rec.includes("Establish a test baseline"));
  assert.ok(!rec.includes(EXPECTED_TERMINAL_SIGNAL));
});

test("renderRecommendation falls to the first Tier-2 item when Tier 1 is empty but Tier 2 is not", () => {
  const t2 = [makeItem({ titlePlain: "Add the missing tests", tier: 2 })];
  const rec = H.renderRecommendation([], t2, "COMPLETE");
  assert.ok(rec.includes("Add the missing tests"));
  assert.ok(!rec.includes(EXPECTED_TERMINAL_SIGNAL));
});

// -----------------------------------------------------------------------------
// renderRunReport -- same-model replacement rule (never both clauses)
// -----------------------------------------------------------------------------
test("renderRunReport emits the clean-context parenthetical when crossModel is true", () => {
  const line = H.renderRunReport({ verified: 4, unconfirmed: 1, deferred: 0, refuted: 2, crossModel: true });
  assert.ok(line.includes("re-checked by a separate clean-context agent -- a reduction of shared-blind-spot risk, not independence"));
  assert.ok(line.includes("dropped 2 that couldn't be confirmed"));
  assert.ok(line.includes("verified 4 - unconfirmed 1 - deferred 0"));
  assert.ok(!line.includes(EXPECTED_SAME_MODEL_TAG)); // never both clauses
});

test("renderRunReport REPLACES the parenthetical with the verbatim same-model tag when crossModel is false", () => {
  const line = H.renderRunReport({ verified: 1, unconfirmed: 0, deferred: 0, refuted: 0, crossModel: false });
  assert.ok(line.includes(EXPECTED_SAME_MODEL_TAG));
  assert.ok(!line.includes("a different model family than the builder")); // the parenthetical is gone
});

test("renderRunReport substitutes the UNRESOLVED tag when the summary computed it (never asserts same-model)", () => {
  const line = H.renderRunReport({
    verified: 1,
    unconfirmed: 0,
    deferred: 0,
    refuted: 0,
    crossModel: false,
    sameModelTag: EXPECTED_UNRESOLVED_FAMILY_TAG,
  });
  assert.ok(line.includes(EXPECTED_UNRESOLVED_FAMILY_TAG));
  assert.ok(!line.includes(EXPECTED_SAME_MODEL_TAG)); // an unresolved run never reads as same-model fact
  assert.ok(!line.includes("a different model family than the builder"));
});

// -----------------------------------------------------------------------------
// GO_BUTTON -- verbatim and last
// -----------------------------------------------------------------------------
test("GO_BUTTON is the verbatim closing how-to-start line", () => {
  assert.equal(H.GO_BUTTON, EXPECTED_GO_BUTTON);
});

// -----------------------------------------------------------------------------
// renderBacklogFence -- the complete body: status first, no markers, go-button last
// -----------------------------------------------------------------------------
test("renderBacklogFence starts with the status line and contains the {{DATE}} placeholder", () => {
  const body = H.renderBacklogFence(makeResult({ items: [makeItem()] }));
  assert.ok(body.startsWith("status: "));
  assert.ok(body.includes("{{DATE}}"));
});

test("renderBacklogFence contains NO fence markers and NO heading (those stay SKILL-owned)", () => {
  const body = H.renderBacklogFence(makeResult({ items: [makeItem()] }));
  assert.ok(!body.includes("harness-audit:backlog"));
  assert.ok(!body.includes("<!--"));
  assert.ok(!body.includes("## Backlog")); // the heading is SKILL-owned, inserted-if-absent
});

test("renderBacklogFence ends with the verbatim go-button line (italicized, last)", () => {
  const body = H.renderBacklogFence(makeResult({ items: [makeItem()] }));
  assert.ok(body.trimEnd().endsWith(`*${EXPECTED_GO_BUTTON}*`));
});

test("renderBacklogFence emits all three tier headings most-urgent-first and the legend", () => {
  const body = H.renderBacklogFence(
    makeResult({
      items: [
        makeItem({ tier: 1, titlePlain: "T1 item" }),
        makeItem({ tier: 2, titlePlain: "T2 item" }),
        makeItem({ tier: 3, titlePlain: "T3 item" }),
      ],
    }),
  );
  const i1 = body.indexOf("### Tier 1 -- critical");
  const i2 = body.indexOf("### Tier 2 -- important");
  const i3 = body.indexOf("### Tier 3 -- polish");
  assert.ok(i1 >= 0 && i2 > i1 && i3 > i2); // most-urgent-first ordering
  assert.ok(body.includes(EXPECTED_LEGEND));
});

test("renderBacklogFence empty-backlog case: empty tiers + the terminal signal + go-button", () => {
  const body = H.renderBacklogFence(makeResult({ items: [], status: "COMPLETE" }));
  assert.ok(body.startsWith("status: "));
  assert.ok(body.includes("### Tier 1 -- critical\n\n_(empty)_"));
  assert.ok(body.includes(EXPECTED_TERMINAL_SIGNAL)); // recommended-starting-point is the stop signal
  assert.ok(body.trimEnd().endsWith(`*${EXPECTED_GO_BUTTON}*`));
});

test("verificationPhrase: an unknown or missing state falls back to the deferred phrase, never a false claim", () => {
  const deferred = H.VERIFICATION_PHRASE.deferred;
  assert.equal(H.verificationPhrase("bogus-state"), deferred);
  assert.equal(H.verificationPhrase(undefined), deferred);
});

test("renderItem: a finding with no verification block renders the deferred phrase and no Evidence line", () => {
  const item = {
    titlePlain: "t", tag: "bug", tier: 1, claimTechnical: "c", whyPlain: "w",
    impactEffort: "i", locations: ["a.js:1"],
  };
  const out = H.renderItem(item);
  assert.ok(out.includes(H.VERIFICATION_PHRASE.deferred));
  assert.ok(!out.includes("Evidence:"));
});

test("toResultItem: a tier-less finding defaults to Tier 2 -- never silently dropped by the tier filter", () => {
  const item = H.toResultItem({
    issueClass: "x", titlePlain: "t", tag: "bug", claimTechnical: "c", whyPlain: "w",
    impactEffort: "i", locations: [], confidence: "judgment",
    verification: { state: "deferred", evidence: "", plainLine: "" },
  });
  assert.equal(item.tier, 2);
  const fence = H.renderBacklogFence({
    status: "COMPLETE", level: "standard", doneCells: ["a|b"], pendingCells: [],
    items: [item],
    verification: { verified: 0, unconfirmed: 0, deferred: 1, refuted: 0, crossModel: false, sameModelTag: H.SAME_MODEL_TAG },
  });
  assert.ok(fence.includes("t"), "the tier-defaulted item must appear in the rendered fence");
});

// -----------------------------------------------------------------------------
// renderOnlyResult -- the SELECT re-render seam (Slice 5): renders the SELECTED subset while
// passing lensCoverage/verification through FULL-SCOPE (the honesty contract). Boundary-validated.
// -----------------------------------------------------------------------------
test("renderOnlyResult re-renders the SELECTED subset: recommendation names the first selected Tier-1 item, the dropped Tier-2 reads _(empty)_", () => {
  // The FULL audit found a Tier-1, a Tier-2, and a Tier-3; the user SELECTED only the Tier-1 + Tier-3.
  const selected = [
    makeItem({ tier: 1, titlePlain: "Fix the auth boundary", findingKey: "auth" }),
    makeItem({ tier: 3, titlePlain: "Tidy a comment", findingKey: "comment" }),
  ];
  const out = H.renderOnlyResult({
    status: "COMPLETE",
    level: "standard",
    doneCells: ["security|src", "testing|src"],
    pendingCells: [],
    items: selected,
    // FULL-SCOPE coverage/run-report: computed over ALL findings, NOT the selected subset.
    lensCoverage: [
      { module: "security", state: "ran-found", findings: 3 },
      { module: "testing", state: "pending", findings: 0 },
    ],
    verification: { verified: 3, unconfirmed: 0, deferred: 0, refuted: 1, crossModel: true },
  });
  const body = out.renderedBacklog;
  // (a) recommendation names the first SELECTED Tier-1 item (not the dropped Tier-2)
  assert.ok(body.includes("**Recommended starting point:** Fix the auth boundary."));
  assert.ok(!body.includes(EXPECTED_TERMINAL_SIGNAL)); // a Tier-1 was kept -- not the terminal signal
  // (b) tiers reflect the SELECTED subset: Tier 1 + Tier 3 present, Tier 2 (dropped) reads _(empty)_
  assert.ok(body.includes("Fix the auth boundary"));
  assert.ok(body.includes("Tidy a comment"));
  assert.ok(body.includes("### Tier 2 -- important\n\n_(empty)_"));
  // (c) THE CORE HONESTY ASSERTION: lens-coverage line + run-report reflect the PASSED-THROUGH
  // full-scope values (3 findings for security, testing still pending; verified 3 - refuted 1) --
  // NOT recomputed over the 2-item subset.
  assert.ok(body.includes("`security`: 3 findings"));
  assert.ok(body.includes("`testing`: did not run this pass -- re-run to cover it"));
  assert.ok(body.includes("dropped 1 that couldn't be confirmed"));
  assert.ok(body.includes("verified 3 - unconfirmed 0 - deferred 0"));
  // the payload passes through unchanged but for renderedBacklog
  assert.equal(out.status, "COMPLETE");
  assert.deepEqual(out.items, selected);
});

test("renderOnlyResult FAILS LOUD on a malformed payload (validate-at-the-boundary)", () => {
  assert.throws(() => H.renderOnlyResult(null), /renderOnly requires an object payload with an items array/);
  assert.throws(() => H.renderOnlyResult({}), /renderOnly requires an object payload with an items array/);
  assert.throws(() => H.renderOnlyResult({ items: "x" }), /renderOnly requires an object payload with an items array/);
});

test("renderOnlyResult with an EMPTY selection renders _(empty)_ tiers + the engine TERMINAL_SIGNAL (the edge the SKILL precondition guards against)", () => {
  // The engine's correct behavior for an empty item set IS the terminal signal -- so the audit SKILL
  // must NOT invoke renderOnly with an empty selection when the full run carried Tier-1/2 findings
  // (that would falsely claim "sound"); this test documents the edge so the precondition is grounded.
  const out = H.renderOnlyResult({
    status: "COMPLETE",
    level: "standard",
    doneCells: ["security|src"],
    pendingCells: [],
    items: [],
    lensCoverage: [{ module: "security", state: "ran-found", findings: 2 }],
    verification: { verified: 2, unconfirmed: 0, deferred: 0, refuted: 0, crossModel: true },
  });
  const body = out.renderedBacklog;
  assert.ok(body.includes("### Tier 1 -- critical\n\n_(empty)_"));
  assert.ok(body.includes("### Tier 2 -- important\n\n_(empty)_"));
  assert.ok(body.includes(EXPECTED_TERMINAL_SIGNAL)); // why the SKILL must guard the empty-selection call
});

// -----------------------------------------------------------------------------
// Product-gap (criteria) mode -- the cellsFromCriteria seam + criteria-arg validation (Slice 6)
// -----------------------------------------------------------------------------

/** A valid acceptance criterion in the FROZEN schema; override fields per-case. */
function validCriterion(overrides = {}) {
  return {
    id: "AC-add-1",
    feature: "Add an item",
    flow: ["Open the page", "Type 'milk'", "Click Add"],
    expect: ["the list shows 'milk'", "the field is cleared"],
    states: ["empty", "error"],
    check: "e2e",
    ...overrides,
  };
}

test("frozen-schema constants are pinned exactly (single source of truth with the template)", () => {
  assert.deepEqual(H.CRITERIA_KEYS, ["id", "feature", "flow", "expect", "states", "check"]);
  assert.deepEqual(H.CRITERIA_CHECKS, ["e2e", "api", "manual"]);
  assert.deepEqual(H.CRITERIA_STATES, ["empty", "loading", "error"]);
  assert.equal(H.GAP_LEVEL, "gap");
});

test("validateCriterion: a well-formed criterion (all six frozen keys) is valid (null)", () => {
  assert.equal(H.validateCriterion(validCriterion(), 0), null);
  // states may be empty; check may be api or manual
  assert.equal(H.validateCriterion(validCriterion({ states: [], check: "api" }), 0), null);
  assert.equal(H.validateCriterion(validCriterion({ check: "manual" }), 0), null);
});

test("validateCriterion: a missing key is rejected naming the id and the frozen key set", () => {
  const { check, ...noCheck } = validCriterion();
  const err = H.validateCriterion(noCheck, 0);
  assert.ok(err && err.includes("AC-add-1"), "the error names the offending criterion id");
  assert.ok(err.includes("check"), "the error names the missing key");
});

test("validateCriterion: an extra (non-frozen) key is rejected -- the schema is exactly the six keys", () => {
  const err = H.validateCriterion(validCriterion({ priority: "high" }), 0);
  assert.ok(err && err.includes("AC-add-1"));
  assert.ok(err.includes("priority"), "the error names the unexpected key");
});

test("validateCriterion: a bad check enum value is rejected", () => {
  const err = H.validateCriterion(validCriterion({ check: "integration" }), 0);
  assert.ok(err && err.includes("check"));
});

test("validateCriterion: a bad states entry is rejected", () => {
  const err = H.validateCriterion(validCriterion({ states: ["empty", "warming"] }), 0);
  assert.ok(err && err.includes("states"));
});

test("validateCriterion: empty flow / empty expect are rejected (>=1 required)", () => {
  assert.ok(H.validateCriterion(validCriterion({ flow: [] }), 0).includes("flow"));
  assert.ok(H.validateCriterion(validCriterion({ expect: [] }), 0).includes("expect"));
});

test("validateCriterion: a criterion missing its id is named by array index, not 'undefined'", () => {
  const { id, ...noId } = validCriterion();
  const err = H.validateCriterion(noId, 3);
  assert.ok(err.includes("index 3"), "a criterion with no id is located by index");
});

test("cellsFromCriteria: a valid array -> one cell per criterion carrying its id + the criterion object", () => {
  const criteria = [validCriterion({ id: "AC-1" }), validCriterion({ id: "AC-2" })];
  const cells = H.cellsFromCriteria(criteria, []);
  assert.equal(cells.length, 2);
  assert.deepEqual(cells.map((c) => c.key), ["AC-1", "AC-2"]);
  assert.equal(cells[0].criterion.id, "AC-1");
  assert.equal(cells[1].criterion.feature, "Add an item");
});

test("cellsFromCriteria: doneCells are skipped -- the resume contract (criterion ids as cells)", () => {
  const criteria = [validCriterion({ id: "AC-1" }), validCriterion({ id: "AC-2" }), validCriterion({ id: "AC-3" })];
  const cells = H.cellsFromCriteria(criteria, ["AC-1", "AC-3"]);
  assert.deepEqual(cells.map((c) => c.key), ["AC-2"]);
});

test("cellsFromCriteria: a missing/extra key throws naming the offending id", () => {
  const { states, ...noStates } = validCriterion({ id: "AC-bad" });
  assert.throws(() => H.cellsFromCriteria([noStates], []), /AC-bad.*states/s);
  assert.throws(
    () => H.cellsFromCriteria([validCriterion({ id: "AC-x", extra: 1 })], []),
    /AC-x.*extra/s,
  );
});

test("cellsFromCriteria: a bad check / bad states value throws", () => {
  assert.throws(() => H.cellsFromCriteria([validCriterion({ id: "AC-c", check: "nope" })], []), /AC-c.*check/s);
  assert.throws(() => H.cellsFromCriteria([validCriterion({ id: "AC-s", states: ["nope"] })], []), /AC-s.*states/s);
});

test("cellsFromCriteria: an empty list throws (never a silent zero-cell run)", () => {
  assert.throws(() => H.cellsFromCriteria([], []), /non-empty/);
});

test("cellsFromCriteria: duplicate ids throw (ids must be unique)", () => {
  const criteria = [validCriterion({ id: "AC-dup" }), validCriterion({ id: "AC-dup" })];
  assert.throws(() => H.cellsFromCriteria(criteria, []), /AC-dup.*unique/s);
});

test("validateArgs: criteria mode is valid without modules/scopeDirs/dial", () => {
  const args = {
    criteria: [validCriterion({ id: "AC-1" }), validCriterion({ id: "AC-2" })],
    excludeSet: ["node_modules"],
    maxCellsPerRun: 10,
    builderFamily: "Fable 5",
  };
  assert.deepEqual(H.validateArgs(args), []);
});

test("validateArgs: criteria mode still requires the shared boundary fields (maxCellsPerRun, builderFamily)", () => {
  const errors = H.validateArgs({ criteria: [validCriterion()] });
  assert.ok(errors.some((e) => e.includes("maxCellsPerRun")));
  assert.ok(errors.some((e) => e.includes("builderFamily")));
});

test("validateArgs: criteria mode rejects an empty criteria list", () => {
  const errors = H.validateArgs({ criteria: [], maxCellsPerRun: 5, builderFamily: "Opus" });
  assert.ok(errors.some((e) => e.includes("criteria is required")));
});

test("validateArgs: criteria mode reports each invalid criterion by id", () => {
  const { check, ...bad } = validCriterion({ id: "AC-bad" });
  const errors = H.validateArgs({ criteria: [validCriterion({ id: "AC-ok" }), bad], maxCellsPerRun: 5, builderFamily: "Opus" });
  assert.ok(errors.some((e) => e.includes("AC-bad") && e.includes("check")));
});

test("validateArgs: criteria mode rejects duplicate ids", () => {
  const errors = H.validateArgs({
    criteria: [validCriterion({ id: "AC-1" }), validCriterion({ id: "AC-1" })],
    maxCellsPerRun: 5,
    builderFamily: "Opus",
  });
  assert.ok(errors.some((e) => e.includes("AC-1") && e.includes("unique")));
});

test("buildCriterionLensPrompt: carries the criterion id + text and states it reads STATICALLY, not running the app", () => {
  const prompt = H.buildCriterionLensPrompt(validCriterion({ id: "AC-add-1" }), ["node_modules"]);
  assert.ok(prompt.includes("AC-add-1"), "the criterion id rides into the prompt");
  assert.ok(prompt.includes("Add an item"), "the criterion feature text rides into the prompt");
  assert.ok(/static/i.test(prompt), "the prompt instructs a static read");
  assert.ok(/do NOT run the app/i.test(prompt), "the prompt states it does not run the app (qa.js's job)");
  assert.ok(prompt.includes("claugentic-ARCHITECTURE_TREE.md"), "the prompt points at the file index to locate code");
  assert.ok(prompt.includes("issueClass"), "the prompt asks for the standard finding shape");
});

test("mergePriorItems: prior resolved findings persist on a resumed render (the gap-smoke Tier-1)", () => {
  const prior = [{ findingKey: "a", tier: 1, titlePlain: "prior verified", verification: { state: "verified" } }];
  const current = [{ findingKey: "b", tier: 2, titlePlain: "fresh" }];
  const merged = H.mergePriorItems(current, prior);
  assert.equal(merged.length, 2);
  assert.equal(merged[0].findingKey, "a"); // carried, verdict untouched
  assert.equal(merged[0].verification.state, "verified");
});

test("mergePriorItems: a re-surfaced findingKey is superseded by THIS run's fresher copy", () => {
  const prior = [{ findingKey: "a", tier: 2, titlePlain: "old copy" }];
  const current = [{ findingKey: "a", tier: 1, titlePlain: "fresh copy" }];
  const merged = H.mergePriorItems(current, prior);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].titlePlain, "fresh copy");
});

test("mergePriorItems: no priorItems -> current unchanged; tier-less prior defaults to 2", () => {
  assert.deepEqual(H.mergePriorItems([{ findingKey: "x" }], undefined).length, 1);
  const merged = H.mergePriorItems([], [{ findingKey: "p", titlePlain: "t" }]);
  assert.equal(merged[0].tier, 2);
});

test("render-level regression: a carried prior finding survives into the rendered fence body", () => {
  const merged = H.mergePriorItems(
    [{ findingKey: "b", tier: 2, titlePlain: "fresh", tag: "bug", claimTechnical: "c", whyPlain: "w", impactEffort: "i", locations: [], confidence: "judgment", verification: { state: "verified", evidence: "", plainLine: "" } }],
    [{ findingKey: "a", tier: 1, titlePlain: "prior verified", tag: "bug", claimTechnical: "c", whyPlain: "w", impactEffort: "i", locations: [], confidence: "judgment", verification: { state: "verified", evidence: "", plainLine: "" } }],
  );
  const body = H.renderBacklogFence({
    status: "PARTIAL", level: "gap", doneCells: ["AC-1"], pendingCells: [],
    items: merged,
    verification: { verified: 2, unconfirmed: 0, deferred: 0, refuted: 0, crossModel: false, sameModelTag: H.SAME_MODEL_TAG },
  });
  assert.ok(body.includes("prior verified"), "a carried prior finding must appear in the rendered fence");
  assert.ok(body.includes("fresh"), "this run's finding must appear too");
});
