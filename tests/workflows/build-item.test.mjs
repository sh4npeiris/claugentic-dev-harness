// tests/workflows/build-item.test.mjs -- node --test unit tests for the pure helpers of
// engine/build-item.js.
//
// Same extract-and-eval harness as verify.test.mjs / qa.test.mjs: build-item.js is a
// Workflow-tool script (top-level control flow ending in a returned result; it calls the tool
// primitives agent()/parallel()/phase()/log()/workflow(), undefined under node), so we read the
// file, EXTRACT the marked `// --- helpers ---` ... `// --- end helpers ---` block (pure functions
// + schema literals), evaluate it via `new Function`, and exercise the helpers standalone. The
// block must close over NO tool primitive -- these tests are the proof it doesn't. Run by
// `node --test "tests/workflows/*.test.mjs"` (and the CI node-tests job).

import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { loadHelpersFrom } from "./_load-helpers.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT_PATH = join(REPO_ROOT, "engine", "build-item.js");

// The verbatim same-model tag -- duplicated here on purpose as an independent fixture so a drift
// in the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run -- the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED tag -- the third disclosure state. Independent fixture (exact-compare pin).
const EXPECTED_UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run -- no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

const H = loadHelpersFrom(SCRIPT_PATH, [
  "SAME_MODEL_TAG",
  "UNRESOLVED_FAMILY_TAG",
  "KNOWN_FAMILIES",
  "modelFamily",
  "sameModelTag",
  "parseArgs",
  "DEFAULT_MAX_ITERATIONS",
  "CRITERION_KEYS",
  "CHECK_KINDS",
  "validateArgs",
  "maxIterationsFor",
  "criteriaBlockers",
  "childScriptPath",
  "gatesGreen",
  "qaGreen",
  "outOfScopeTier12",
  "nextAction",
  "residualReport",
  "foldResidual",
  "crossModelClaim",
  "IMPLEMENT_SCHEMA",
  "GATES_SCHEMA",
  "MAX_STAGE_TIMEOUT_SEC",
  "DEFAULT_STAGE_TIMEOUTS",
  "resolveStageTimeouts",
  "qaChildArgs",
  "implementPrompt",
  "gatesPrompt",
]);

/** Build a valid args object; override fields per-case. */
function validArgs(overrides = {}) {
  return {
    item: {
      id: "T2-unknown-family",
      title: "An unknown model family silently degrades to same-model",
      tag: "refactor",
      planPath: ".claude/plans/0099-x.md",
      specText: "Add a third explicit 'unresolved' state to the cross-model fold so the run report ...",
      acceptanceCriteria: [],
    },
    repo: {
      root: "/repo",
      baseBranch: "main",
      gateCommands: ['node --test "tests/workflows/*.test.mjs"', "python -m pytest"],
      runApp: null,
      pluginRoot: "/plugins/cache/claugentic-dev-harness/0.1.23",
    },
    caps: { maxIterations: 3 },
    builderFamily: "Fable 5",
    ...overrides,
  };
}

// -----------------------------------------------------------------------------
// Extraction harness + the copied trust-surface pins
// -----------------------------------------------------------------------------
test("extraction harness finds the marked block and all helper names", () => {
  for (const name of [
    "SAME_MODEL_TAG",
    "modelFamily",
    "sameModelTag",
    "parseArgs",
    "validateArgs",
    "maxIterationsFor",
    "criteriaBlockers",
    "childScriptPath",
    "gatesGreen",
    "qaGreen",
    "outOfScopeTier12",
    "nextAction",
    "residualReport",
    "foldResidual",
    "crossModelClaim",
  ]) {
    assert.ok(H[name] !== undefined, `helper '${name}' was not extracted`);
  }
});

test("SAME_MODEL_TAG is the verbatim string (drift pin)", () => {
  assert.equal(H.SAME_MODEL_TAG, EXPECTED_SAME_MODEL_TAG);
});

test("modelFamily normalizes a self-reported family / null on garbage (copied from verify.js)", () => {
  assert.equal(H.modelFamily("Opus 4.8"), "opus");
  assert.equal(H.modelFamily("Fable 5"), "fable");
  assert.equal(H.modelFamily("a totally unknown model"), null);
  assert.equal(H.modelFamily(""), null);
  assert.equal(H.modelFamily(42), null);
});

// -----------------------------------------------------------------------------
// sameModelTag -- verbatim tag on match / missing; null only on a confirmed different family
// -----------------------------------------------------------------------------
test("sameModelTag: same family -> the verbatim tag (string equality)", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.1"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag: a MISSING judge report (null/empty) is the same-model floor", () => {
  assert.equal(H.sameModelTag("Fable 5", ""), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.sameModelTag("Fable 5", null), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag: a PRESENT but unrecognized family reports UNRESOLVED (never same-model fact)", () => {
  assert.equal(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.notEqual(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag: a confirmed different family -> null (the sole cross-model case)", () => {
  assert.equal(H.sameModelTag("Fable 5", "Opus 4.8"), null);
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

// -----------------------------------------------------------------------------
// parseArgs -- the JSON-string boundary
// -----------------------------------------------------------------------------
test("parseArgs parses a JSON-string args delivery (the scriptPath boundary)", () => {
  assert.deepEqual(H.parseArgs('{"builderFamily":"Fable 5"}'), { builderFamily: "Fable 5" });
});

test("parseArgs passes an object through untouched", () => {
  const obj = { builderFamily: "Fable 5" };
  assert.equal(H.parseArgs(obj), obj);
});

test("parseArgs fails loud on an unparseable string", () => {
  assert.throws(() => H.parseArgs("{not json"), /not valid JSON/);
});

// -----------------------------------------------------------------------------
// validateArgs -- boundary validation, fail loud
// -----------------------------------------------------------------------------
test("validateArgs accepts a well-formed args object", () => {
  const { ok, errors } = H.validateArgs(validArgs());
  assert.deepEqual(errors, []);
  assert.equal(ok, true);
});

test("validateArgs rejects a non-object arg", () => {
  assert.deepEqual(H.validateArgs(null), { ok: false, errors: ["args must be an object"] });
});

test("validateArgs flags a missing item.id and item.specText", () => {
  const { errors } = H.validateArgs(validArgs({ item: { acceptanceCriteria: [] } }));
  assert.ok(errors.some((e) => e.includes("item.id")));
  assert.ok(errors.some((e) => e.includes("item.specText")));
});

test("validateArgs flags an empty gateCommands (zero gates would make 'green' a lie)", () => {
  const args = validArgs();
  args.repo.gateCommands = [];
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("gateCommands")));
});

test("validateArgs flags a missing repo.baseBranch / repo.root / repo.pluginRoot", () => {
  const { errors } = H.validateArgs(
    validArgs({ repo: { gateCommands: ["x"], runApp: null } }),
  );
  assert.ok(errors.some((e) => e.includes("repo.root")));
  assert.ok(errors.some((e) => e.includes("repo.baseBranch")));
  assert.ok(errors.some((e) => e.includes("repo.pluginRoot")));
});

test("validateArgs flags a missing builderFamily", () => {
  const { errors } = H.validateArgs(validArgs({ builderFamily: undefined }));
  assert.ok(errors.some((e) => e.includes("builderFamily")));
});

test("validateArgs flags a criterion with a renamed field (the frozen-schema guard)", () => {
  const args = validArgs();
  // 'steps' instead of 'flow' -- a frozen-schema drift.
  args.item.acceptanceCriteria = [
    { id: "AC-1", feature: "f", steps: ["a"], expect: ["b"], states: [], check: "e2e" },
  ];
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("must be exactly")));
});

test("validateArgs accepts a well-formed acceptance criterion", () => {
  const args = validArgs();
  args.item.acceptanceCriteria = [
    { id: "AC-1", feature: "f", flow: ["a"], expect: ["b"], states: [], check: "e2e" },
  ];
  args.repo.runApp = "uvicorn main:app";
  const { ok, errors } = H.validateArgs(args);
  assert.deepEqual(errors, []);
  assert.equal(ok, true);
});

test("validateArgs flags acceptanceCriteria that is not an array", () => {
  const args = validArgs();
  args.item.acceptanceCriteria = { id: "AC-1" };
  const { errors } = H.validateArgs(args);
  assert.ok(errors.some((e) => e.includes("acceptanceCriteria")));
});

// -----------------------------------------------------------------------------
// validateArgs -- caps.stageTimeouts (per-stage duration bound; fail loud, never silent-clamp)
// -----------------------------------------------------------------------------
test("validateArgs accepts a valid caps.stageTimeouts", () => {
  const args = validArgs();
  args.caps.stageTimeouts = { implement: 600, gates: 300, qaBoot: 120 };
  const { ok, errors } = H.validateArgs(args);
  assert.deepEqual(errors, []);
  assert.equal(ok, true);
});

test("validateArgs accepts an explicit-null stageTimeouts (null is an accepted absent-form)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = null;
  const { ok, errors } = H.validateArgs(args);
  assert.deepEqual(errors, []);
  assert.equal(ok, true);
});

test("validateArgs rejects a non-object stageTimeouts (named field)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = 600;
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("caps.stageTimeouts")));
});

test("validateArgs rejects an ARRAY stageTimeouts (an array must not silently mean 'all defaults')", () => {
  const args = validArgs();
  args.caps.stageTimeouts = []; // Array.isArray reject arm -- without it, [] would slip through as an object
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("caps.stageTimeouts") && e.includes("must be an object")));
});

test("validateArgs rejects an unknown stageTimeouts key (a typo can't fall back to default)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = { qaboot: 120 }; // typo for qaBoot
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("unknown stage 'qaboot'")));
});

test("validateArgs rejects a non-integer stageTimeouts value (named field)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = { gates: 12.5 };
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("caps.stageTimeouts.gates")));
});

test("validateArgs rejects a <=0 stageTimeouts value (named field)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = { implement: 0 };
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("caps.stageTimeouts.implement")));
});

test("validateArgs rejects a stageTimeouts value > 600 (the Bash-tool hard max -- never silently clamped)", () => {
  const args = validArgs();
  args.caps.stageTimeouts = { gates: 800 };
  const { ok, errors } = H.validateArgs(args);
  assert.equal(ok, false);
  assert.ok(errors.some((e) => e.includes("caps.stageTimeouts.gates") && e.includes("600")));
});

// -----------------------------------------------------------------------------
// resolveStageTimeouts -- per-stage distinct defaults; qaBoot stays null when unset (no engine default)
// -----------------------------------------------------------------------------
test("resolveStageTimeouts: defaults when caps/stageTimeouts absent (implement 600, gates 600, qaBoot null)", () => {
  assert.deepEqual(H.resolveStageTimeouts(undefined), { implement: 600, gates: 600, qaBoot: null });
  assert.deepEqual(H.resolveStageTimeouts({}), { implement: 600, gates: 600, qaBoot: null });
  assert.deepEqual(H.resolveStageTimeouts({ stageTimeouts: {} }), { implement: 600, gates: 600, qaBoot: null });
  assert.equal(H.MAX_STAGE_TIMEOUT_SEC, 600);
  assert.deepEqual(H.DEFAULT_STAGE_TIMEOUTS, { implement: 600, gates: 600, qaBoot: null });
});

test("resolveStageTimeouts: a per-stage override wins", () => {
  assert.deepEqual(
    H.resolveStageTimeouts({ stageTimeouts: { implement: 300, gates: 120, qaBoot: 90 } }),
    { implement: 300, gates: 120, qaBoot: 90 },
  );
  // a partial override leaves the others at their defaults
  assert.deepEqual(
    H.resolveStageTimeouts({ stageTimeouts: { gates: 200 } }),
    { implement: 600, gates: 200, qaBoot: null },
  );
});

test("resolveStageTimeouts: qaBoot stays null when unset (qa.js owns the boot default/clamp)", () => {
  assert.equal(H.resolveStageTimeouts({ stageTimeouts: { implement: 300 } }).qaBoot, null);
  assert.equal(H.resolveStageTimeouts({}).qaBoot, null);
});

test("resolveStageTimeouts: an explicit-null stageTimeouts maps to all defaults (the top-level guard)", () => {
  // null is a legal absent-form (validateArgs accepts it) -- only the `typeof === 'object' && !== null`
  // guard keeps it from being read as a non-empty override; pin that it resolves to all defaults.
  assert.deepEqual(H.resolveStageTimeouts({ stageTimeouts: null }), { implement: 600, gates: 600, qaBoot: null });
});

// -----------------------------------------------------------------------------
// qaChildArgs -- readinessTimeoutSec iff qaBoot != null; threads the rest unchanged
// -----------------------------------------------------------------------------
test("qaChildArgs: omits readinessTimeoutSec when qaBoot is null (qa.js applies its own 60s default)", () => {
  const item = { id: "T1", appUrl: "" };
  const repo = { runApp: "uvicorn main:app", appUrl: "http://localhost:8000" };
  const criteria = [{ id: "AC-1" }];
  const out = H.qaChildArgs(item, repo, criteria, "Opus 4.8", 2, null);
  assert.equal("readinessTimeoutSec" in out, false);
  assert.equal(out.criteria, criteria);
  assert.equal(out.runCommand, "uvicorn main:app");
  assert.equal(out.appUrl, "http://localhost:8000"); // falls back to repo.appUrl
  assert.equal(out.builderFamily, "Opus 4.8");
  assert.equal(out.runLabel, "build-T1-iter2");
});

test("qaChildArgs: includes readinessTimeoutSec when qaBoot is set (pass-through-when-set)", () => {
  const item = { id: "T1", appUrl: "http://item-url" };
  const repo = { runApp: "npm start", appUrl: "http://repo-url" };
  const out = H.qaChildArgs(item, repo, [], "Fable 5", 1, 150);
  assert.equal(out.readinessTimeoutSec, 150);
  assert.equal(out.appUrl, "http://item-url"); // item.appUrl wins over repo.appUrl
});

// -----------------------------------------------------------------------------
// maxIterationsFor -- default + override
// -----------------------------------------------------------------------------
test("maxIterationsFor: default is 3, an override wins, a bad value falls back", () => {
  assert.equal(H.maxIterationsFor(undefined), 3);
  assert.equal(H.maxIterationsFor({}), 3);
  assert.equal(H.maxIterationsFor({ maxIterations: 5 }), 5);
  assert.equal(H.maxIterationsFor({ maxIterations: 0 }), 3);
  assert.equal(H.maxIterationsFor({ maxIterations: 2.5 }), 3);
  assert.equal(H.DEFAULT_MAX_ITERATIONS, 3);
});

// -----------------------------------------------------------------------------
// criteriaBlockers -- manual criteria escalate to blocked
// -----------------------------------------------------------------------------
test("criteriaBlockers: e2e/api -> empty; a manual criterion -> its id", () => {
  assert.deepEqual(
    H.criteriaBlockers([
      { id: "AC-1", check: "e2e" },
      { id: "AC-2", check: "api" },
    ]),
    [],
  );
  assert.deepEqual(
    H.criteriaBlockers([
      { id: "AC-1", check: "e2e" },
      { id: "AC-3", check: "manual" },
    ]),
    ["AC-3"],
  );
  assert.deepEqual(H.criteriaBlockers([]), []);
  assert.deepEqual(H.criteriaBlockers(undefined), []);
});

// -----------------------------------------------------------------------------
// childScriptPath -- joins/normalizes; throws on empty root
// -----------------------------------------------------------------------------
test("childScriptPath joins the plugin root and the script name", () => {
  assert.equal(H.childScriptPath("/plugins/x/0.1.23", "verify.js"), "/plugins/x/0.1.23/engine/verify.js");
});

test("childScriptPath normalizes a trailing slash", () => {
  assert.equal(H.childScriptPath("/plugins/x/0.1.23/", "qa.js"), "/plugins/x/0.1.23/engine/qa.js");
});

test("childScriptPath throws on an empty/whitespace root (fail loud)", () => {
  assert.throws(() => H.childScriptPath("", "verify.js"), /pluginRoot is empty/);
  assert.throws(() => H.childScriptPath("   ", "verify.js"), /pluginRoot is empty/);
});

// -----------------------------------------------------------------------------
// gatesGreen -- exit codes decide; a malformed result fails loud
// -----------------------------------------------------------------------------
test("gatesGreen: all-zero is green", () => {
  const r = H.gatesGreen([
    { command: "pytest", exitCode: 0 },
    { command: "node --test", exitCode: 0 },
  ]);
  assert.equal(r.green, true);
  assert.deepEqual(r.failures, []);
});

test("gatesGreen: one nonzero names the failing command + keeps the output tail", () => {
  const r = H.gatesGreen([
    { command: "pytest", exitCode: 1, outputTail: "1 failed" },
    { command: "node --test", exitCode: 0 },
  ]);
  assert.equal(r.green, false);
  assert.equal(r.failures.length, 1);
  assert.equal(r.failures[0].command, "pytest");
  assert.equal(r.failures[0].exitCode, 1);
  assert.equal(r.failures[0].outputTail, "1 failed");
});

test("gatesGreen: a missing/non-numeric exitCode is a FAILURE (fail loud, never fail-open)", () => {
  const r = H.gatesGreen([{ command: "pytest" }]);
  assert.equal(r.green, false);
  assert.ok(r.failures[0].reason.includes("non-numeric exitCode") || r.failures[0].reason.includes("missing"));
});

test("gatesGreen: a non-array results input fails loud, never reads as a pass", () => {
  assert.equal(H.gatesGreen(null).green, false);
  assert.equal(H.gatesGreen(undefined).green, false);
});

// -----------------------------------------------------------------------------
// qaGreen -- anything != pass fails; could-not-run is a failure
// -----------------------------------------------------------------------------
test("qaGreen: all-pass verdicts -> green", () => {
  const r = H.qaGreen({ verdicts: [{ id: "AC-1", verdict: "pass" }, { id: "AC-2", verdict: "pass" }], findings: [] });
  assert.equal(r.green, true);
});

test("qaGreen: a fail verdict AND a could-not-run finding are both named failing", () => {
  const r = H.qaGreen({
    verdicts: [{ id: "AC-1", verdict: "fail", reason: "broken flow" }],
    findings: [{ issueClass: "qa-could-not-run-app" }],
  });
  assert.equal(r.green, false);
  // both the boot failure and the failing criterion show up
  assert.ok(r.failures.some((f) => f.criterionId === "(boot)"));
  assert.ok(r.failures.some((f) => f.criterionId === "AC-1"));
});

test("qaGreen: a not-checkable verdict counts as failing (never a silent skip)", () => {
  const r = H.qaGreen({ verdicts: [{ id: "AC-1", verdict: "not-checkable", reason: "browser unavailable" }], findings: [] });
  assert.equal(r.green, false);
  assert.equal(r.failures[0].verdict, "not-checkable");
});

test("qaGreen: a non-object qa result fails loud, never green", () => {
  assert.equal(H.qaGreen(null).green, false);
});

// -----------------------------------------------------------------------------
// outOfScopeTier12 -- tiers 1/2 escalate, 3 ignored, unclassified escalates
// -----------------------------------------------------------------------------
test("outOfScopeTier12: tiers 1 and 2 are caught, tier 3 is ignored", () => {
  const out = H.outOfScopeTier12([
    { tier: 1, claim: "a" },
    { tier: 2, claim: "b" },
    { tier: 3, claim: "c" },
  ]);
  assert.equal(out.length, 2);
  assert.deepEqual(out.map((f) => f.claim), ["a", "b"]);
});

test("outOfScopeTier12: an unclassified tier escalates (conservative, never silently dropped)", () => {
  const out = H.outOfScopeTier12([{ claim: "no tier" }, { tier: "bad", claim: "garbage tier" }]);
  assert.equal(out.length, 2);
});

test("outOfScopeTier12: empty/non-array input -> empty", () => {
  assert.deepEqual(H.outOfScopeTier12([]), []);
  assert.deepEqual(H.outOfScopeTier12(undefined), []);
});

// -----------------------------------------------------------------------------
// nextAction -- the priority-ordered decision
// -----------------------------------------------------------------------------
function state(overrides = {}) {
  return {
    iteration: 1,
    maxIterations: 3,
    gatesGreen: true,
    verifyPass: true,
    qaGreenOrNA: true,
    irreversibleNeeded: null,
    newTier12: [],
    ...overrides,
  };
}

test("nextAction: all green -> 'green'", () => {
  assert.equal(H.nextAction(state()), "green");
});

test("nextAction: irreversibleNeeded wins even when everything else is green", () => {
  assert.equal(H.nextAction(state({ irreversibleNeeded: { action: "push", consequence: "x" } })), "needs-irreversible");
});

test("nextAction: a new Tier-1/2 finding wins over green (but not over irreversible)", () => {
  assert.equal(H.nextAction(state({ newTier12: [{ tier: 1 }] })), "new-tier12");
  // irreversible outranks new-tier12
  assert.equal(
    H.nextAction(state({ irreversibleNeeded: { action: "a" }, newTier12: [{ tier: 1 }] })),
    "needs-irreversible",
  );
});

test("nextAction: not green, under the cap -> 'fix'", () => {
  assert.equal(H.nextAction(state({ gatesGreen: false, iteration: 1, maxIterations: 3 })), "fix");
});

test("nextAction: not green, at the cap (red gates) -> 'cap-stop'", () => {
  assert.equal(H.nextAction(state({ gatesGreen: false, iteration: 3, maxIterations: 3 })), "cap-stop");
  assert.equal(H.nextAction(state({ verifyPass: false, iteration: 3, maxIterations: 3 })), "cap-stop");
  assert.equal(H.nextAction(state({ qaGreenOrNA: false, iteration: 3, maxIterations: 3 })), "cap-stop");
});

test("nextAction: green even at the cap -> 'green' (the cap only stops a RED run)", () => {
  assert.equal(H.nextAction(state({ iteration: 3, maxIterations: 3 })), "green");
});

test("nextAction: the full priority order (irreversible > new-tier12 > green > cap > fix)", () => {
  // green outranks cap-stop (handled above); here: a red run under the cap is 'fix' not 'cap-stop'.
  assert.equal(H.nextAction(state({ gatesGreen: false, verifyPass: false, iteration: 2, maxIterations: 3 })), "fix");
});

test("nextAction: a malformed state throws (never a default)", () => {
  assert.throws(() => H.nextAction(null), /state must be an object/);
  assert.throws(() => H.nextAction(state({ iteration: 0 })), /iteration must be a positive integer/);
  assert.throws(() => H.nextAction(state({ gatesGreen: "yes" })), /gatesGreen must be a boolean/);
  assert.throws(() => H.nextAction(state({ verifyPass: undefined })), /verifyPass must be a boolean/);
  assert.throws(() => H.nextAction(state({ qaGreenOrNA: 1 })), /qaGreenOrNA must be a boolean/);
});

// -----------------------------------------------------------------------------
// residualReport -- shape
// -----------------------------------------------------------------------------
test("residualReport: assembles the four residual fields", () => {
  const r = H.residualReport({
    iteration: 3,
    failingGates: [{ command: "pytest", exitCode: 1 }],
    openFindings: [{ dimension: "testing", status: "gap" }],
    failingCriteria: [{ criterionId: "AC-1", verdict: "fail" }],
  });
  assert.deepEqual(r.failingGates, [{ command: "pytest", exitCode: 1 }]);
  assert.equal(r.openFindings.length, 1);
  assert.equal(r.failingCriteria.length, 1);
  assert.equal(r.iterationsUsed, 3);
});

test("residualReport: missing fields default to empty arrays / 0", () => {
  const r = H.residualReport({});
  assert.deepEqual(r.failingGates, []);
  assert.deepEqual(r.openFindings, []);
  assert.deepEqual(r.failingCriteria, []);
  assert.equal(r.iterationsUsed, 0);
});

// -----------------------------------------------------------------------------
// foldResidual -- the next-iteration fix brief
// -----------------------------------------------------------------------------
test("foldResidual: collects failing gates + open (non-met) verify findings + failing criteria", () => {
  const brief = H.foldResidual(
    { failures: [{ command: "pytest", exitCode: 1 }] },
    { findings: [{ status: "gap", dimension: "testing" }, { status: "met", dimension: "security" }] },
    { failures: [{ criterionId: "AC-1" }] },
  );
  assert.equal(brief.failingGates.length, 1);
  // only the non-met finding is folded in
  assert.equal(brief.verifyFindings.length, 1);
  assert.equal(brief.verifyFindings[0].dimension, "testing");
  assert.equal(brief.failingCriteria.length, 1);
});

test("foldResidual: null stages fold to empty arrays, never a crash", () => {
  const brief = H.foldResidual(null, null, null);
  assert.deepEqual(brief.failingGates, []);
  assert.deepEqual(brief.verifyFindings, []);
  assert.deepEqual(brief.failingCriteria, []);
});

// -----------------------------------------------------------------------------
// crossModelClaim -- confirmed only on all-confirming-different-family
// -----------------------------------------------------------------------------
test("crossModelClaim: every child confirms a different family -> 'confirmed'", () => {
  assert.equal(H.crossModelClaim("Fable 5", ["Opus 4.8", "Opus 4.1"]), "confirmed");
});

test("crossModelClaim: any same-family child -> the verbatim same-model tag", () => {
  assert.equal(H.crossModelClaim("Fable 5", ["Opus 4.8", "Fable 5"]), EXPECTED_SAME_MODEL_TAG);
});

test("crossModelClaim: no judge report at all -> the same-model tag (never claim on silence)", () => {
  assert.equal(H.crossModelClaim("Fable 5", []), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.crossModelClaim("Fable 5", [null, ""]), EXPECTED_SAME_MODEL_TAG);
});

// -----------------------------------------------------------------------------
// Schema field-set pins -- the consumed contract (drift guard)
// -----------------------------------------------------------------------------
test("schema field-set pins: IMPLEMENT_SCHEMA / GATES_SCHEMA required arrays", () => {
  assert.deepEqual(H.IMPLEMENT_SCHEMA.required, ["summary", "branch", "touchedFiles", "modelFamily"]);
  assert.deepEqual(H.GATES_SCHEMA.required, ["results"]);
  assert.deepEqual(H.GATES_SCHEMA.properties.results.items.required, ["command", "exitCode"]);
});

test("CRITERION_KEYS / CHECK_KINDS pin the frozen acceptance-criteria contract", () => {
  assert.deepEqual(H.CRITERION_KEYS, ["id", "feature", "flow", "expect", "states", "check"]);
  assert.deepEqual(H.CHECK_KINDS, ["e2e", "api", "manual"]);
});

test("foldResidual: a null verify result is an explicit could-not-run entry, never an empty brief", () => {
  const r = H.foldResidual({ failures: [] }, null, null);
  assert.equal(r.verifyFindings.length, 0);
  assert.equal(r.stageCouldNotRun.length, 1);
  assert.match(r.stageCouldNotRun[0], /verify could not run/);
  assert.match(r.stageCouldNotRun[0], /infrastructure failure/);
});

test("foldResidual: a ran-clean verify (empty findings) carries NO could-not-run entry", () => {
  const r = H.foldResidual({ failures: [] }, { verdict: "PASS", findings: [] }, null);
  assert.equal(r.stageCouldNotRun.length, 0);
});

test("foldResidual: a could-not-run QA stage is an explicit entry", () => {
  const qa = H.qaGreen(null);
  const r = H.foldResidual({ failures: [] }, { verdict: "PASS", findings: [] }, qa);
  assert.equal(r.stageCouldNotRun.length, 1);
  assert.match(r.stageCouldNotRun[0], /qa could not run/);
});

test("residualReport: carries stageCouldNotRun through to the terminal report", () => {
  const rep = H.residualReport({ failingGates: [], openFindings: [], failingCriteria: [], stageCouldNotRun: ["verify could not run -- x"], iteration: 2 });
  assert.deepEqual(rep.stageCouldNotRun, ["verify could not run -- x"]);
});

test("qaGreen: couldNotRun is true only when the stage produced no usable result", () => {
  assert.equal(H.qaGreen(null).couldNotRun, true);
  assert.equal(H.qaGreen({ verdicts: [], findings: [] }).couldNotRun, false);
});

// -----------------------------------------------------------------------------
// gatesPrompt / implementPrompt -- the resolved bound + the Bash-tool `timeout` mandate
// -----------------------------------------------------------------------------
const PROMPT_ITEM = { id: "T1", title: "An item", tag: "feat", specText: "Build the thing." };
const PROMPT_REPO = { root: "/repo", baseBranch: "main", gateCommands: ["pytest", "node --test"], runApp: "npm start" };

test("gatesPrompt: carries the resolved timeout + mandates the Bash tool's `timeout` parameter (not a shell command)", () => {
  const p = H.gatesPrompt(PROMPT_REPO, "feat/x", "/wt", 300);
  assert.match(p, /300s/);
  assert.match(p, /Bash tool's `timeout` PARAMETER/);
  assert.match(p, /NOT a shell `timeout` command/);
  // names the Windows no-op trap so a future edit can't quietly drop it
  assert.match(p, /Windows/);
});

test("gatesPrompt: carries the 124 timeout convention (the fail-closed leg) + per-command, never a stage total", () => {
  // A NON-default timeout (217, not 600) so a mutant that hardcodes "600s" into either interpolation
  // site dies: the value must appear at BOTH the per-command instruction AND the 124 timeout sentence.
  const p = H.gatesPrompt(PROMPT_REPO, "feat/x", null, 217);
  // per-command instruction site carries the resolved value
  assert.match(p, /timeout` PARAMETER set to 217s/);
  // the "hits the ...s timeout" 124 sentence carries the SAME value (not a hardcoded 600s)
  assert.match(p, /hits the 217s\s*\n?\s*timeout/);
  assert.equal(p.includes("600s"), false); // no stray hardcoded default leaked into either site
  assert.match(p, /exitCode 124/);
  assert.match(p, /named timeout convention/);
  // reconciled with the standing "report the real number, never an opinion" rule
  assert.match(p, /never an opinion/);
  assert.match(p, /PER-COMMAND, never a stage total/);
});

test("implementPrompt: carries the resolved bound + the Bash-tool `timeout` + treat-as-failure/never-hang (instruction-only)", () => {
  const p = H.implementPrompt(PROMPT_ITEM, PROMPT_REPO, null, null, 450);
  assert.match(p, /450s/);
  assert.match(p, /Bash tool's `timeout` PARAMETER/);
  assert.match(p, /NOT a shell `timeout` command/);
  assert.match(p, /treat it as a FAILURE/);
  assert.match(p, /NEVER hang/);
});

test("implementPrompt: the fix-iteration path also carries the anti-hang bound", () => {
  const residual = { failingGates: [{ command: "pytest", exitCode: 1 }], verifyFindings: [], failingCriteria: [] };
  const p = H.implementPrompt(PROMPT_ITEM, PROMPT_REPO, residual, "feat/x", 200);
  assert.match(p, /Build-to-green -- FIX/);
  assert.match(p, /200s/);
  assert.match(p, /Bash tool's `timeout` PARAMETER/);
});
