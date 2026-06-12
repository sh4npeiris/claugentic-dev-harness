// tests/workflows/audit.test.mjs — node --test unit tests for the pure helpers of
// workflows/audit.js.
//
// Same extraction harness as verify.test.mjs (Slice 2): the script is a Workflow-tool script
// (top-level control flow ending in a returned result; tool primitives agent()/parallel()/
// phase()/log() are undefined under node), so we read the file, EXTRACT the marked
// `// --- helpers ---` … `// --- end helpers ---` block (pure functions + schema/const literals),
// evaluate it via `new Function`, and exercise the helpers standalone. The block must NOT close
// over any tool primitive — these tests are the proof it doesn't. Run by
// `node --test tests/workflows/*.test.mjs` (and the CI node-tests job).

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT_PATH = join(REPO_ROOT, "workflows", "audit.js");

// The verbatim same-model tag — duplicated here on purpose as an independent fixture so a drift
// in the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

/** Extract the marked helpers block and evaluate it, returning the named helpers.
 *
 * Markers are matched line-anchored (`^// --- helpers ---$`) so a mention of the marker text
 * inside the file's header comment is NOT mistaken for the real delimiter. */
function loadHelpers() {
  const src = readFileSync(SCRIPT_PATH, "utf8");
  const startMatch = src.match(/^\/\/ --- helpers ---$/m);
  const endMatch = src.match(/^\/\/ --- end helpers ---$/m);
  assert.ok(startMatch, "helpers block start marker not found (line-anchored) in workflows/audit.js");
  assert.ok(endMatch, "helpers block end marker not found (line-anchored) in workflows/audit.js");
  const start = startMatch.index;
  const end = endMatch.index;
  assert.ok(end > start, "helpers end marker precedes start marker");
  const block = src.slice(start, end);
  const names = [
    "MODELS",
    "SAME_MODEL_TAG",
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
    "LENS_SCHEMA",
    "SYNTHESIS_SCHEMA",
    "VERIFIER_SCHEMA",
  ];
  // No tool primitives are in scope inside this Function — so if any helper closed over
  // agent()/parallel()/phase()/log(), constructing or calling it would throw here.
  const factory = new Function(`${block}\n; return { ${names.join(", ")} };`);
  return factory();
}

const H = loadHelpers();

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

// ─────────────────────────────────────────────────────────────────────────────
// Extraction harness + contract pins
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// validateArgs — boundary validation, fail loud; thorough-unsupported
// ─────────────────────────────────────────────────────────────────────────────
test("validateArgs accepts a well-formed quick/standard args object", () => {
  assert.deepEqual(H.validateArgs(validArgs({ dial: "quick" })), []);
  assert.deepEqual(H.validateArgs(validArgs({ dial: "standard" })), []);
});

test("validateArgs rejects 'thorough' with the named not-yet-supported message", () => {
  const errors = H.validateArgs(validArgs({ dial: "thorough" }));
  assert.ok(
    errors.some((e) => e.includes("thorough") && e.includes("Slice 3b") && e.includes("prose path")),
    `expected a thorough/Slice-3b message, got: ${JSON.stringify(errors)}`,
  );
});

test("validateArgs rejects an unknown dial", () => {
  const errors = H.validateArgs(validArgs({ dial: "ludicrous" }));
  assert.ok(errors.some((e) => e.includes("ludicrous") && e.includes("not supported")));
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

// ─────────────────────────────────────────────────────────────────────────────
// depthForDial — the one ladder map
// ─────────────────────────────────────────────────────────────────────────────
test("depthForDial maps the full ladder quick->focused, standard->deep, thorough->exhaustive", () => {
  assert.equal(H.depthForDial("quick"), "focused");
  assert.equal(H.depthForDial("standard"), "deep");
  assert.equal(H.depthForDial("thorough"), "exhaustive");
});

// ─────────────────────────────────────────────────────────────────────────────
// cellKey / enumerateCells / applyCellBudget / groupByModule — cell math
// ─────────────────────────────────────────────────────────────────────────────
test("cellKey produces the exact <module>×<dir> resume token", () => {
  assert.equal(H.cellKey("security", "src/api"), "security×src/api");
});

test("parseCellKey round-trips cellKey (split on first separator)", () => {
  assert.deepEqual(H.parseCellKey(H.cellKey("security", "src/api")), { module: "security", dir: "src/api" });
});

test("enumerateCells emits module×dir in (module, dir) order", () => {
  const cells = H.enumerateCells(["security", "testing"], ["a", "b"], []);
  assert.deepEqual(cells, ["security×a", "security×b", "testing×a", "testing×b"]);
});

test("enumerateCells excludes doneCells and never re-enumerates them", () => {
  const cells = H.enumerateCells(["security", "testing"], ["a", "b"], ["security×a", "testing×b"]);
  assert.deepEqual(cells, ["security×b", "testing×a"]);
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

test("groupByModule batches cells by module preserving order", () => {
  const batches = H.groupByModule(["security×a", "security×b", "testing×a"]);
  assert.equal(batches.length, 2);
  assert.deepEqual(batches[0], { module: "security", dirs: ["a", "b"], cells: ["security×a", "security×b"] });
  assert.deepEqual(batches[1], { module: "testing", dirs: ["a"], cells: ["testing×a"] });
});

// ─────────────────────────────────────────────────────────────────────────────
// normalizeIssueClass / findingKey
// ─────────────────────────────────────────────────────────────────────────────
test("normalizeIssueClass lowercases, trims, and hyphenates whitespace", () => {
  assert.equal(H.normalizeIssueClass("  Missing Input   Validation "), "missing-input-validation");
});

test("findingKey is the normalized issueClass", () => {
  assert.equal(H.findingKey({ issueClass: "Missing Input Validation" }), "missing-input-validation");
});

// ─────────────────────────────────────────────────────────────────────────────
// dedupFindings — same-key roll-up, weakest-confidence-wins, distinct classes separate
// ─────────────────────────────────────────────────────────────────────────────
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

test("dedupFindings: weakest confidence wins — a judgment member downgrades the merge", () => {
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

// ─────────────────────────────────────────────────────────────────────────────
// applyPrune — the test-baseline never-prune exception
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// buildVerifierInput — structural independence: emits ONLY the contract keys
// ─────────────────────────────────────────────────────────────────────────────
test("buildVerifierInput emits exactly the contract keys (rationale/transcript dropped)", () => {
  const input = H.buildVerifierInput(
    {
      claimPlain: "no limit on the query",
      claimTechnical: "SELECT without LIMIT",
      locations: ["db.js:40"],
      sourceModule: "docs/standards/performance-efficiency.md",
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
  const input = H.buildVerifierInput({ modules: ["docs/standards/security.md"] }, []);
  assert.equal(input.sourceModule, "docs/standards/security.md");
});

test("buildVerifierPrompt never contains the words rationale/transcript and demands RUNNING AS", () => {
  const input = H.buildVerifierInput({ claimPlain: "x", claimTechnical: "y", locations: [], confidence: "judgment" }, []);
  const prompt = H.buildVerifierPrompt(input);
  assert.ok(prompt.includes("RUNNING AS"));
  assert.ok(prompt.includes("refute-first") || prompt.includes("REFUTE"));
});

// ─────────────────────────────────────────────────────────────────────────────
// sameModelTag — verbatim string, copied from verify.js
// ─────────────────────────────────────────────────────────────────────────────
test("SAME_MODEL_TAG is the verbatim string (drift pin)", () => {
  assert.equal(H.SAME_MODEL_TAG, EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns the verbatim tag when families match", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.1"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns the tag when a report is missing/unresolved", () => {
  assert.equal(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.sameModelTag(null, "Opus 4.8"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns null only on a confirming different family", () => {
  assert.equal(H.sameModelTag("Fable 5", "Opus 4.8"), null);
});

// ─────────────────────────────────────────────────────────────────────────────
// applyVerdicts — all three verdict mappings + no-verdict->deferred
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// verificationSummary — crossModel only on all-confirming-different-family
// ─────────────────────────────────────────────────────────────────────────────
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
  assert.equal(s.sameModelTag, EXPECTED_SAME_MODEL_TAG);
  assert.equal(s.deferred, 1);
});

test("verificationSummary does not claim crossModel on an empty finding set", () => {
  const s = H.verificationSummary([], 0, "Fable 5");
  assert.equal(s.crossModel, false);
});

// ─────────────────────────────────────────────────────────────────────────────
// runStatus
// ─────────────────────────────────────────────────────────────────────────────
test("runStatus is COMPLETE on empty pending, PARTIAL otherwise", () => {
  assert.equal(H.runStatus([]), "COMPLETE");
  assert.equal(H.runStatus(["security×src"]), "PARTIAL");
});

// ─────────────────────────────────────────────────────────────────────────────
// parseArgs — the scriptPath JSON-string boundary (copied from verify.js)
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// Schema field-set pins (drift guard) — incl. runningAs on the verifier
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// applySynthesisItems / toResultItem — annotation + result shaping
// ─────────────────────────────────────────────────────────────────────────────
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
    modules: ["docs/standards/security.md"],
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
  assert.deepEqual(item.modules, ["docs/standards/security.md"]);
  assert.equal(item.verification.state, "verified");
  assert.equal(item.tag, "bug");
});

// ─────────────────────────────────────────────────────────────────────────────
// The production-shaped composition: applyVerdicts → verificationSummary, with a
// Refuted finding AHEAD of a survivor. Regression for the 2026-06-11 dogfood Tier-1:
// on the old parallel-arrays seam this produced a FALSE cross-model claim (the
// summary read the refuted finding's verifier instead of the survivor's own).
// ─────────────────────────────────────────────────────────────────────────────
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
  // The survivor's verifier is Fable — same family as the builder — so crossModel MUST be
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
  assert.equal(kept[1].verifierRunningAs, null); // deferred — no report, never a claim
});
