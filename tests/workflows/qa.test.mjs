// tests/workflows/qa.test.mjs -- node --test unit tests for the pure helpers of workflows/qa.js.
//
// Same extraction harness as verify.test.mjs / audit.test.mjs: the script is a Workflow-tool
// script (top-level control flow ending in a returned result; tool primitives agent()/parallel()/
// phase()/log() are undefined under node), so we read the file, EXTRACT the marked
// `// --- helpers ---` ... `// --- end helpers ---` block (pure functions + schema/const literals),
// evaluate it via `new Function`, and exercise the helpers standalone. The block must NOT close
// over any tool primitive -- these tests are the proof it doesn't. Run by
// `node --test tests/workflows/*.test.mjs` (and the CI node-tests job).

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { loadHelpersFrom } from "./_load-helpers.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT_PATH = join(REPO_ROOT, "engine", "qa.js");

// The verbatim same-model tag -- duplicated here on purpose as an independent fixture so a drift in
// the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run -- the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED tag -- the third disclosure state. Independent fixture (exact-compare pin).
const EXPECTED_UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run -- no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

// Independent verbatim fixtures for the could-not-run finding's load-bearing copy.
const EXPECTED_COULD_NOT_RUN_CLASS = "qa-could-not-run-app";
const EXPECTED_OBSERVED_TAG = "(observed this run -- boot log attached)";
const EXPECTED_NO_RUN_REASON =
  'no run command recorded -- add a "Run the app:" line to CLAUDE.md\'s detected-tooling block (or pass runCommand)';

const H = loadHelpersFrom(SCRIPT_PATH, [
  "MODELS",
  "SAME_MODEL_TAG",
  "UNRESOLVED_FAMILY_TAG",
  "KNOWN_FAMILIES",
  "modelFamily",
  "sameModelTag",
  "READINESS_TIMEOUT_DEFAULT_SEC",
  "READINESS_TIMEOUT_CAP_SEC",
  "READINESS_PROBE_INTERVAL_SEC",
  "COULD_NOT_RUN_CLASS",
  "OBSERVED_THIS_RUN_TAG",
  "NO_RUN_COMMAND_REASON",
  "CHECK_KINDS",
  "STATE_KINDS",
  "UX_ISSUE_CLASS",
  "MANUAL_NOT_CHECKABLE_REASON",
  "BROWSER_UNAVAILABLE_REASON",
  "parseArgs",
  "parseRunArgs",
  "isRunInputError",
  "artifactBase",
  "bootReportFromError",
  "isComposeCommand",
  "readinessPlan",
  "bootOutcome",
  "teardownPlan",
  "couldNotRunFinding",
  "validateCriteria",
  "criterionPlan",
  "verdictFor",
  "findingsFrom",
  "dedupFindings",
  "sanitizeForPath",
  "screenshotPath",
  "applyVerifierVerdicts",
  "BOOT_SCHEMA",
  "TEARDOWN_SCHEMA",
  "DRIVER_SCHEMA",
  "VERIFIER_SCHEMA",
]);

/** Build a valid run-args object; override fields per-case. */
function validArgs(overrides = {}) {
  return {
    runCommand: "uvicorn main:app --app-dir eval/fixture-app --port 8123",
    appUrl: "http://localhost:8123",
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
    "COULD_NOT_RUN_CLASS",
    "parseArgs",
    "parseRunArgs",
    "isComposeCommand",
    "readinessPlan",
    "bootOutcome",
    "teardownPlan",
    "couldNotRunFinding",
  ]) {
    assert.ok(H[name] !== undefined, `helper '${name}' was not extracted`);
  }
});

test("MODELS.judge is pinned to 'opus' (cross-model contract, copied from verify.js)", () => {
  assert.equal(H.MODELS.judge, "opus");
});

test("SAME_MODEL_TAG is the verbatim cross-script tag (drift pin)", () => {
  assert.equal(H.SAME_MODEL_TAG, EXPECTED_SAME_MODEL_TAG);
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

test("COULD_NOT_RUN_CLASS / OBSERVED_THIS_RUN_TAG / NO_RUN_COMMAND_REASON are verbatim (drift pins)", () => {
  assert.equal(H.COULD_NOT_RUN_CLASS, EXPECTED_COULD_NOT_RUN_CLASS);
  assert.equal(H.OBSERVED_THIS_RUN_TAG, EXPECTED_OBSERVED_TAG);
  assert.equal(H.NO_RUN_COMMAND_REASON, EXPECTED_NO_RUN_REASON);
});

// -----------------------------------------------------------------------------
// parseArgs (copied verbatim -- JSON-string boundary)
// -----------------------------------------------------------------------------
test("parseArgs parses a JSON string and passes an object through", () => {
  assert.deepEqual(H.parseArgs('{"runCommand":"x","appUrl":"y"}'), { runCommand: "x", appUrl: "y" });
  const obj = { runCommand: "x", appUrl: "y" };
  assert.equal(H.parseArgs(obj), obj);
});

test("parseArgs throws loud on unparseable JSON (never a silent empty-args run)", () => {
  assert.throws(() => H.parseArgs("{not json"), /qa args: not valid JSON/);
});

// -----------------------------------------------------------------------------
// parseRunArgs -- defaults, cap, and the no-run-command finding path
// -----------------------------------------------------------------------------
test("parseRunArgs applies the readiness default and trims/normalizes", () => {
  const { runConfig, errors } = H.parseRunArgs(validArgs({ runCommand: "  uvicorn x  ", appUrl: "  http://h  " }));
  assert.deepEqual(errors, []);
  assert.equal(runConfig.runCommand, "uvicorn x");
  assert.equal(runConfig.appUrl, "http://h");
  assert.equal(runConfig.readinessTimeoutSec, H.READINESS_TIMEOUT_DEFAULT_SEC);
  assert.equal(runConfig.teardownCommand, null);
  assert.deepEqual(runConfig.criteria, []); // 4b seam: absent => boot-only
});

test("parseRunArgs clamps readinessTimeoutSec at the 300s cap", () => {
  const { runConfig, errors } = H.parseRunArgs(validArgs({ readinessTimeoutSec: 9999 }));
  assert.deepEqual(errors, []);
  assert.equal(runConfig.readinessTimeoutSec, H.READINESS_TIMEOUT_CAP_SEC);
  assert.equal(H.READINESS_TIMEOUT_CAP_SEC, 300);
});

test("parseRunArgs keeps a readinessTimeoutSec under the cap unchanged", () => {
  const { runConfig } = H.parseRunArgs(validArgs({ readinessTimeoutSec: 45 }));
  assert.equal(runConfig.readinessTimeoutSec, 45);
});

test("parseRunArgs rejects a non-positive readinessTimeoutSec (fail loud)", () => {
  const { errors } = H.parseRunArgs(validArgs({ readinessTimeoutSec: 0 }));
  assert.ok(errors.some((e) => e.includes("readinessTimeoutSec")));
});

test("parseRunArgs accepts an explicit teardownCommand and threads it", () => {
  const { runConfig, errors } = H.parseRunArgs(validArgs({ teardownCommand: "make stop" }));
  assert.deepEqual(errors, []);
  assert.equal(runConfig.teardownCommand, "make stop");
});

test("parseRunArgs rejects a blank teardownCommand when provided", () => {
  const { errors } = H.parseRunArgs(validArgs({ teardownCommand: "   " }));
  assert.ok(errors.some((e) => e.includes("teardownCommand")));
});

test("parseRunArgs flags a missing runCommand on the finding path (not a silent throw)", () => {
  const { errors } = H.parseRunArgs({ appUrl: "http://localhost:8123" });
  assert.ok(errors.some((e) => e.startsWith("runCommand is required")));
});

test("parseRunArgs flags a missing appUrl on the finding path", () => {
  const { errors } = H.parseRunArgs({ runCommand: "uvicorn x" });
  assert.ok(errors.some((e) => e.startsWith("appUrl is required")));
});

test("parseRunArgs flags an empty/whitespace runCommand and appUrl", () => {
  const { errors } = H.parseRunArgs({ runCommand: "   ", appUrl: "" });
  assert.ok(errors.some((e) => e.startsWith("runCommand is required")));
  assert.ok(errors.some((e) => e.startsWith("appUrl is required")));
});

test("parseRunArgs rejects a non-object args value", () => {
  const { errors, runConfig } = H.parseRunArgs(null);
  assert.equal(runConfig, null);
  assert.deepEqual(errors, ["args must be an object"]);
});

test("parseRunArgs rejects a non-array criteria (4b seam type-guard)", () => {
  const { errors } = H.parseRunArgs(validArgs({ criteria: "nope" }));
  assert.ok(errors.some((e) => e.includes("criteria")));
});

// -----------------------------------------------------------------------------
// isComposeCommand
// -----------------------------------------------------------------------------
test("isComposeCommand: docker compose / docker-compose => true", () => {
  assert.equal(H.isComposeCommand("docker compose up -d"), true);
  assert.equal(H.isComposeCommand("docker-compose up"), true);
  assert.equal(H.isComposeCommand("  DOCKER COMPOSE up -d"), true);
});

test("isComposeCommand: dev-server commands => false", () => {
  assert.equal(H.isComposeCommand("npm run dev"), false);
  assert.equal(H.isComposeCommand("uvicorn main:app --port 8123"), false);
  assert.equal(H.isComposeCommand("python manage.py runserver"), false);
});

test("isComposeCommand: non-string => false", () => {
  assert.equal(H.isComposeCommand(null), false);
  assert.equal(H.isComposeCommand(undefined), false);
});

// -----------------------------------------------------------------------------
// readinessPlan -- bounded attempts, never zero, never unbounded
// -----------------------------------------------------------------------------
test("readinessPlan derives bounded attempts from the timeout", () => {
  const plan = H.readinessPlan({ readinessTimeoutSec: 60 });
  assert.equal(plan.intervalSec, H.READINESS_PROBE_INTERVAL_SEC);
  assert.equal(plan.timeoutSec, 60);
  assert.equal(plan.maxAttempts, 30); // ceil(60/2)
});

test("readinessPlan: a sub-interval timeout still probes at least once", () => {
  const plan = H.readinessPlan({ readinessTimeoutSec: 1 });
  assert.ok(plan.maxAttempts >= 1, "never zero attempts");
});

test("readinessPlan: a missing/invalid timeout falls back to the default (never unbounded)", () => {
  const plan = H.readinessPlan({});
  assert.equal(plan.timeoutSec, H.READINESS_TIMEOUT_DEFAULT_SEC);
  assert.ok(Number.isFinite(plan.maxAttempts) && plan.maxAttempts > 0, "bounded fallback");
});

test("readinessPlan clamps an over-cap timeout (defense in depth)", () => {
  const plan = H.readinessPlan({ readinessTimeoutSec: 100000 });
  assert.equal(plan.timeoutSec, H.READINESS_TIMEOUT_CAP_SEC);
});

// -----------------------------------------------------------------------------
// bootOutcome -- fail loud on a missing/malformed report
// -----------------------------------------------------------------------------
test("bootOutcome: ready strictly-true => ready", () => {
  assert.equal(H.bootOutcome({ started: true, ready: true, attempts: 3 }), "ready");
});

test("bootOutcome: ready false => failed", () => {
  assert.equal(H.bootOutcome({ started: true, ready: false, attempts: 30 }), "failed");
});

test("bootOutcome: a missing report => failed (never defaults to success)", () => {
  assert.equal(H.bootOutcome(null), "failed");
  assert.equal(H.bootOutcome(undefined), "failed");
});

test("bootOutcome: a malformed report (ready not a strict bool) => failed", () => {
  assert.equal(H.bootOutcome({ ready: "yes" }), "failed");
  assert.equal(H.bootOutcome({ ready: 1 }), "failed");
  assert.equal(H.bootOutcome("nope"), "failed");
});

// -----------------------------------------------------------------------------
// teardownPlan -- precedence + the always-reap-the-PID rule
// -----------------------------------------------------------------------------
test("teardownPlan: an explicit teardownCommand wins over everything", () => {
  const td = H.teardownPlan(
    { runCommand: "docker compose up -d", teardownCommand: "make stop" },
    { pid: 42 },
  );
  assert.deepEqual(td, { method: "command", command: "make stop" });
});

test("teardownPlan: a compose run defaults to `docker compose down`", () => {
  const td = H.teardownPlan({ runCommand: "docker compose up -d", teardownCommand: null }, null);
  assert.deepEqual(td, { method: "command", command: "docker compose down" });
});

test("teardownPlan: a dev-server run kills the recorded PID", () => {
  const td = H.teardownPlan({ runCommand: "uvicorn main:app", teardownCommand: null }, { pid: 1234 });
  assert.deepEqual(td, { method: "kill", pid: 1234 });
});

test("teardownPlan: a FAILED boot that still recorded a PID yields a kill (never leak a port)", () => {
  const td = H.teardownPlan({ runCommand: "uvicorn main:app", teardownCommand: null }, { started: true, ready: false, pid: 99 });
  assert.deepEqual(td, { method: "kill", pid: 99 });
});

test("teardownPlan: no override, not compose, no PID => an honest no-op method", () => {
  const td = H.teardownPlan({ runCommand: "uvicorn main:app", teardownCommand: null }, null);
  assert.deepEqual(td, { method: "none" });
});

// -----------------------------------------------------------------------------
// couldNotRunFinding -- exact shape, deterministic confidence, evidence present
// -----------------------------------------------------------------------------
test("couldNotRunFinding: a boot-failure finding carries the exact class, confidence, tag, evidence", () => {
  const { runConfig } = H.parseRunArgs(validArgs());
  const f = H.couldNotRunFinding(runConfig, { attempts: 30, logTail: "ImportError: nonexistent" });
  assert.equal(f.issueClass, EXPECTED_COULD_NOT_RUN_CLASS);
  assert.equal(f.confidence, "deterministic");
  assert.equal(f.verificationTag, EXPECTED_OBSERVED_TAG);
  assert.equal(f.evidence.command, runConfig.runCommand);
  assert.equal(f.evidence.appUrl, runConfig.appUrl);
  assert.equal(f.evidence.attempts, 30);
  assert.equal(f.evidence.logTail, "ImportError: nonexistent");
  assert.ok(typeof f.plainEnglish === "string" && f.plainEnglish.length > 0, "non-empty plain-English line");
});

test("couldNotRunFinding: a no-run-command finding (no report) names the fix reason", () => {
  const { runConfig } = H.parseRunArgs({ appUrl: "http://localhost:8123" }); // runConfig has empty runCommand
  const f = H.couldNotRunFinding(runConfig, null);
  assert.equal(f.issueClass, EXPECTED_COULD_NOT_RUN_CLASS);
  assert.equal(f.confidence, "deterministic");
  assert.equal(f.reason, EXPECTED_NO_RUN_REASON);
  assert.equal(f.evidence.command, null);
  assert.equal(f.evidence.attempts, 0);
  assert.ok(f.plainEnglish.includes("could not run") || f.plainEnglish.includes("reported, not"));
});

test("couldNotRunFinding: a boot-failure finding has no no-run reason (reason null)", () => {
  const { runConfig } = H.parseRunArgs(validArgs());
  const f = H.couldNotRunFinding(runConfig, { attempts: 5, logTail: "boom" });
  assert.equal(f.reason, null);
});

test("couldNotRunFinding: tolerates a malformed report (missing fields default safely)", () => {
  const { runConfig } = H.parseRunArgs(validArgs());
  const f = H.couldNotRunFinding(runConfig, {});
  assert.equal(f.evidence.attempts, 0);
  assert.equal(f.evidence.logTail, "");
});

// -----------------------------------------------------------------------------
// Schemas -- required field sets pinned (the boot/teardown reports the agents must return)
// -----------------------------------------------------------------------------
test("BOOT_SCHEMA requires started/ready/attempts (the load-bearing boot fields)", () => {
  assert.deepEqual(H.BOOT_SCHEMA.required, ["started", "ready", "attempts"]);
  assert.equal(H.BOOT_SCHEMA.properties.ready.type, "boolean");
});

test("TEARDOWN_SCHEMA requires toreDown (the teardown contract)", () => {
  assert.deepEqual(H.TEARDOWN_SCHEMA.required, ["toreDown"]);
});

test("isRunInputError: matches exactly the producer's missing-run-input prefixes", () => {
  // The producer/consumer string contract -- parseRunArgs emits these prefixes; the partition
  // must route them to the honest could-not-run finding, never the throw path.
  assert.equal(H.isRunInputError("runCommand is required (record a Run-the-app line)"), true);
  assert.equal(H.isRunInputError("appUrl is required"), true);
  assert.equal(H.isRunInputError("readinessTimeoutSec must be a number"), false);
  assert.equal(H.isRunInputError("criteria, when provided, must be an array"), false);
  assert.equal(H.isRunInputError(null), false);
});

test("isRunInputError: every parseRunArgs missing-input message is matched (producer pin)", () => {
  const { errors } = H.parseRunArgs({});
  const missing = errors.filter((e) => e.includes("required"));
  assert.ok(missing.length >= 2, "expected runCommand + appUrl required errors");
  for (const e of missing) {
    assert.equal(H.isRunInputError(e), true, `partition must route to the finding: ${e}`);
  }
});

// -----------------------------------------------------------------------------
// Slice 4b -- frozen-schema constants + cross-model helpers
// -----------------------------------------------------------------------------
test("CHECK_KINDS / STATE_KINDS are the frozen enums", () => {
  assert.deepEqual(H.CHECK_KINDS, ["e2e", "api", "manual"]);
  assert.deepEqual(H.STATE_KINDS, ["empty", "loading", "error"]);
});

test("UX_ISSUE_CLASS maps each state + flow to the verbatim issueClass (drift pins)", () => {
  assert.equal(H.UX_ISSUE_CLASS.empty, "ux-missing-empty-state");
  assert.equal(H.UX_ISSUE_CLASS.loading, "ux-missing-loading-state");
  assert.equal(H.UX_ISSUE_CLASS.error, "ux-missing-error-state");
  assert.equal(H.UX_ISSUE_CLASS.flow, "ux-broken-flow");
});

test("MANUAL_NOT_CHECKABLE_REASON / BROWSER_UNAVAILABLE_REASON are verbatim (drift pins)", () => {
  assert.equal(H.MANUAL_NOT_CHECKABLE_REASON, "manual by contract");
  assert.equal(H.BROWSER_UNAVAILABLE_REASON, "browser tooling unavailable in this session");
});

test("sameModelTag: matching/missing => same-model tag; present-unresolved => UNRESOLVED; differing => null", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.8"), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.sameModelTag("Fable 5", ""), EXPECTED_SAME_MODEL_TAG); // missing report => same-model floor
  assert.equal(H.sameModelTag("Fable 5", "RUNNING AS: gemini"), EXPECTED_UNRESOLVED_FAMILY_TAG); // present-unresolved
  assert.notEqual(H.sameModelTag("Fable 5", "RUNNING AS: gemini"), EXPECTED_SAME_MODEL_TAG);
  assert.equal(H.sameModelTag("Fable 5", "Opus 4.8"), null); // confirmed different family
});

test("modelFamily normalizes a self-report; garbage/empty => null", () => {
  assert.equal(H.modelFamily("RUNNING AS: Opus 4.8"), "opus");
  assert.equal(H.modelFamily("Fable 5"), "fable");
  assert.equal(H.modelFamily("nonsense"), null);
  assert.equal(H.modelFamily(""), null);
});

// -----------------------------------------------------------------------------
// validateCriteria -- frozen field names, check enum, states enum, unique ids
// -----------------------------------------------------------------------------
function validCriterion(overrides = {}) {
  return {
    id: "AC-1",
    feature: "Add item",
    flow: ["Open the home page", "Type 'milk'", "Click Add"],
    expect: ["the list shows 'milk'"],
    states: ["error"],
    check: "e2e",
    ...overrides,
  };
}

test("validateCriteria: a valid set passes (empty error list)", () => {
  assert.deepEqual(H.validateCriteria([validCriterion(), validCriterion({ id: "AC-2", check: "manual", states: [] })]), []);
});

test("validateCriteria: absent / empty list is valid (boot-only seam stays open)", () => {
  assert.deepEqual(H.validateCriteria(undefined), []);
  assert.deepEqual(H.validateCriteria(null), []);
  assert.deepEqual(H.validateCriteria([]), []);
});

test("validateCriteria: a non-array fails loud", () => {
  assert.deepEqual(H.validateCriteria("nope"), ["criteria must be an array"]);
});

test("validateCriteria: an unknown check is rejected naming the id (never silently filtered)", () => {
  const errs = H.validateCriteria([validCriterion({ check: "snapshot" })]);
  assert.ok(errs.some((e) => e.includes("AC-1") && e.includes("check must be one of")));
});

test("validateCriteria: a bad states value is rejected naming the id", () => {
  const errs = H.validateCriteria([validCriterion({ states: ["empty", "spinning"] })]);
  assert.ok(errs.some((e) => e.includes("AC-1") && e.includes("states entries")));
});

test("validateCriteria: each missing frozen field is named", () => {
  const errs = H.validateCriteria([{ id: "AC-9" }]);
  for (const field of ["feature", "flow", "expect", "states", "check"]) {
    assert.ok(errs.some((e) => e.includes("AC-9") && e.includes(field)), `expected an error for missing ${field}`);
  }
});

test("validateCriteria: an empty flow / expect array is rejected", () => {
  const errs = H.validateCriteria([validCriterion({ flow: [], expect: [] })]);
  assert.ok(errs.some((e) => e.includes("flow is required")));
  assert.ok(errs.some((e) => e.includes("expect is required")));
});

test("validateCriteria: duplicate ids are rejected", () => {
  const errs = H.validateCriteria([validCriterion(), validCriterion()]);
  assert.ok(errs.some((e) => e.includes("duplicate id")));
});

test("validateCriteria: a missing id is named by index, never silently dropped", () => {
  const errs = H.validateCriteria([{ feature: "x", flow: ["a"], expect: ["b"], states: [], check: "e2e" }]);
  assert.ok(errs.some((e) => e.includes("criteria[0]") && e.includes("id is required")));
});

// -----------------------------------------------------------------------------
// criterionPlan -- the drivable / manual partition (manual NEVER driven)
// -----------------------------------------------------------------------------
test("criterionPlan: e2e/api are drivable; manual is partitioned out (never driven)", () => {
  const e2e = validCriterion({ id: "A", check: "e2e" });
  const api = validCriterion({ id: "B", check: "api" });
  const man = validCriterion({ id: "C", check: "manual" });
  const { drivable, manual } = H.criterionPlan([e2e, api, man]);
  assert.deepEqual(drivable.map((c) => c.id), ["A", "B"]);
  assert.deepEqual(manual.map((c) => c.id), ["C"]);
});

// -----------------------------------------------------------------------------
// verdictFor -- the precedence table (fail-loud; never default to pass)
// -----------------------------------------------------------------------------
test("verdictFor: all steps/expects ok and no state-fail => pass", () => {
  const r = { steps: [{ action: "x", ok: true }], expects: [{ expect: "y", ok: true }], states: [], screenshots: [] };
  assert.equal(H.verdictFor(r).verdict, "pass");
});

test("verdictFor: a failed step => fail even with ok expects", () => {
  const r = { steps: [{ action: "x", ok: false, note: "no Add button" }], expects: [{ expect: "y", ok: true }], states: [], screenshots: [] };
  assert.equal(H.verdictFor(r).verdict, "fail");
});

test("verdictFor: a failed expect => fail", () => {
  const r = { steps: [{ action: "x", ok: true }], expects: [{ expect: "y", ok: false }], states: [], screenshots: [] };
  assert.equal(H.verdictFor(r).verdict, "fail");
});

test("verdictFor: a REQUESTED state verdict 'fail' => fail", () => {
  const r = { steps: [{ action: "x", ok: true }], expects: [{ expect: "y", ok: true }], states: [{ state: "empty", verdict: "fail" }], screenshots: [] };
  assert.equal(H.verdictFor(r, ["empty"]).verdict, "fail");
});

test("verdictFor: a not-checkable state with no failure => not-checkable (loading too-fast is honest, not a fail)", () => {
  const r = { steps: [{ action: "x", ok: true }], expects: [{ expect: "y", ok: true }], states: [{ state: "loading", verdict: "not-checkable" }], screenshots: [] };
  const v = H.verdictFor(r, ["loading"]);
  assert.equal(v.verdict, "not-checkable");
  assert.ok(typeof v.reason === "string" && v.reason.length > 0);
});

test("verdictFor: an explicit notCheckable (browser unavailable) => not-checkable + reason, never pass", () => {
  const v = H.verdictFor({ notCheckable: true, notCheckableReason: H.BROWSER_UNAVAILABLE_REASON, steps: [], expects: [], states: [], screenshots: [] });
  assert.equal(v.verdict, "not-checkable");
  assert.equal(v.reason, H.BROWSER_UNAVAILABLE_REASON);
});

test("verdictFor: a missing/malformed report => not-checkable (loudly), never pass", () => {
  assert.equal(H.verdictFor(null).verdict, "not-checkable");
  assert.equal(H.verdictFor("nope").verdict, "not-checkable");
  assert.equal(H.verdictFor(undefined).verdict, "not-checkable");
});

// -----------------------------------------------------------------------------
// findingsFrom -- each issueClass from its failure kind; confidence; evidence; no file:line
// -----------------------------------------------------------------------------
test("findingsFrom: a flow failure with an observed 404 => ux-broken-flow, deterministic", () => {
  const verdicts = [
    {
      id: "AC-1",
      verdict: "fail",
      route: "http://localhost:8123",
      report: {
        steps: [{ action: "Click Add", ok: false, note: "POST returned 404" }],
        expects: [{ expect: "list shows milk", ok: false, evidence: "HTTP 404 from /api/item" }],
        states: [],
        screenshots: ["a.png"],
      },
    },
  ];
  const findings = H.findingsFrom(verdicts);
  const flow = findings.find((f) => f.issueClass === "ux-broken-flow");
  assert.ok(flow, "expected a ux-broken-flow finding");
  assert.equal(flow.confidence, "deterministic");
  assert.equal(flow.criterionId, "AC-1");
  assert.ok(flow.evidence && Array.isArray(flow.evidence.screenshots));
  assert.equal(flow.file_line, undefined, "runtime findings carry no file:line");
  assert.ok(typeof flow.plainEnglish === "string" && flow.plainEnglish.length > 0);
});

test("findingsFrom: a failed empty state => ux-missing-empty-state, deterministic", () => {
  const findings = H.findingsFrom([
    { id: "AC-2", verdict: "fail", route: "http://localhost:8123", report: { steps: [], expects: [], states: [{ state: "empty", verdict: "fail", evidence: "blank <ul>" }], screenshots: ["e.png"] } },
  ]);
  const f = findings.find((x) => x.issueClass === "ux-missing-empty-state");
  assert.ok(f);
  assert.equal(f.confidence, "deterministic");
});

test("findingsFrom: an interpretive flow failure (no observed status) => judgment", () => {
  const findings = H.findingsFrom([
    { id: "AC-3", verdict: "fail", route: "/x", report: { steps: [{ action: "s", ok: false, note: "looked wrong" }], expects: [], states: [], screenshots: [] } },
  ]);
  assert.equal(findings[0].confidence, "judgment");
});

test("findingsFrom: pass / not-checkable verdicts yield no findings", () => {
  const findings = H.findingsFrom([
    { id: "P", verdict: "pass", report: { steps: [], expects: [], states: [], screenshots: [] } },
    { id: "N", verdict: "not-checkable", report: null },
  ]);
  assert.deepEqual(findings, []);
});

// -----------------------------------------------------------------------------
// dedupFindings -- same class+route merges; different route/class stays separate
// -----------------------------------------------------------------------------
test("dedupFindings: same class + route merges (union of criterionIds + screenshots)", () => {
  const merged = H.dedupFindings([
    { issueClass: "ux-broken-flow", route: "/a", criterionId: "AC-1", confidence: "deterministic", evidence: { screenshots: ["1.png"] } },
    { issueClass: "ux-broken-flow", route: "/a", criterionId: "AC-9", confidence: "judgment", evidence: { screenshots: ["2.png"] } },
  ]);
  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].criterionIds.sort(), ["AC-1", "AC-9"]);
  assert.equal(merged[0].confidence, "judgment", "weakest confidence wins");
  assert.deepEqual(merged[0].evidence.screenshots.sort(), ["1.png", "2.png"]);
});

test("dedupFindings: same class, different route stays separate", () => {
  const out = H.dedupFindings([
    { issueClass: "ux-broken-flow", route: "/a", criterionId: "AC-1", evidence: { screenshots: [] } },
    { issueClass: "ux-broken-flow", route: "/b", criterionId: "AC-2", evidence: { screenshots: [] } },
  ]);
  assert.equal(out.length, 2);
});

test("dedupFindings: same route, different class stays separate", () => {
  const out = H.dedupFindings([
    { issueClass: "ux-broken-flow", route: "/a", criterionId: "AC-1", evidence: { screenshots: [] } },
    { issueClass: "ux-missing-empty-state", route: "/a", criterionId: "AC-1", evidence: { screenshots: [] } },
  ]);
  assert.equal(out.length, 2);
});

// -----------------------------------------------------------------------------
// screenshotPath -- sanitization + stable shape under the artifact dir
// -----------------------------------------------------------------------------
test("screenshotPath: stable shape under <artifactDir>/<runLabel>/", () => {
  assert.equal(H.screenshotPath(".qa-artifacts", "qa-2026", "AC-1", "end"), ".qa-artifacts/qa-2026/ac-1-end.png");
});

test("screenshotPath: sanitizes spaces/slashes in ids (cannot escape the artifact dir)", () => {
  const p = H.screenshotPath(".qa-artifacts", "qa run", "AC 1/../x", "broken flow");
  assert.ok(!p.includes(".."), "must not contain a parent-dir escape");
  assert.ok(!p.includes(" "), "must not contain spaces");
  assert.ok(p.startsWith(".qa-artifacts/"), "stays under the artifact dir");
  assert.ok(p.endsWith(".png"));
});

test("screenshotPath: trims a trailing slash on the artifact dir and defaults a blank runLabel", () => {
  assert.equal(H.screenshotPath(".qa-artifacts/", "", "AC-1", "x"), ".qa-artifacts/run/ac-1-x.png");
});

// -----------------------------------------------------------------------------
// applyVerifierVerdicts -- refuted dropped+counted; tags applied; could-not-run exempt
// -----------------------------------------------------------------------------
test("applyVerifierVerdicts: Refuted is dropped and counted", () => {
  const findings = [{ issueClass: "ux-broken-flow", criterionId: "AC-1" }];
  const { kept, refutedCount } = H.applyVerifierVerdicts(findings, [{ verdict: "Refuted", runningAs: "Opus 4.8" }]);
  assert.equal(kept.length, 0);
  assert.equal(refutedCount, 1);
});

test("applyVerifierVerdicts: Verified / Unconfirmed / deferred tags applied", () => {
  const findings = [
    { issueClass: "ux-broken-flow", criterionId: "A" },
    { issueClass: "ux-missing-empty-state", criterionId: "B" },
    { issueClass: "ux-missing-error-state", criterionId: "C" },
  ];
  const { kept } = H.applyVerifierVerdicts(findings, [
    { verdict: "Verified", evidence: "POST /api/item 404s", runningAs: "Opus 4.8" },
    { verdict: "Unconfirmed", runningAs: "Opus 4.8" },
    null, // no verdict => deferred
  ]);
  assert.equal(kept[0].verificationState, "verified");
  assert.equal(kept[0].verificationTag, "(checked against the code)");
  assert.equal(kept[1].verificationState, "unconfirmed");
  assert.equal(kept[1].verificationTag, "(could not confirm independently -- model's assertion)");
  assert.equal(kept[2].verificationState, "deferred");
  assert.equal(kept[2].verificationTag, "(! not yet verified -- re-run to confirm)");
});

test("applyVerifierVerdicts: the could-not-run finding passes through untouched (exempt)", () => {
  const findings = [
    { issueClass: EXPECTED_COULD_NOT_RUN_CLASS, verificationTag: EXPECTED_OBSERVED_TAG },
    { issueClass: "ux-broken-flow", criterionId: "A" },
  ];
  const { kept } = H.applyVerifierVerdicts(findings, [null, { verdict: "Verified", runningAs: "Opus 4.8" }]);
  const cnr = kept.find((f) => f.issueClass === EXPECTED_COULD_NOT_RUN_CLASS);
  assert.ok(cnr, "could-not-run finding kept");
  assert.equal(cnr.verificationTag, EXPECTED_OBSERVED_TAG, "its observed-this-run tag is untouched");
  assert.equal(cnr.verificationState, undefined, "no code-checked verification state is applied");
});

// -----------------------------------------------------------------------------
// Slice 4b schemas -- required field-sets pinned
// -----------------------------------------------------------------------------
test("DRIVER_SCHEMA requires the load-bearing report arrays", () => {
  assert.deepEqual(H.DRIVER_SCHEMA.required, ["steps", "expects", "states", "screenshots"]);
});

test("VERIFIER_SCHEMA requires runningAs (the cross-model self-report)", () => {
  assert.deepEqual(H.VERIFIER_SCHEMA.required, ["runningAs", "verdict", "evidence", "plainLine"]);
  assert.deepEqual(H.VERIFIER_SCHEMA.properties.verdict.enum, ["Verified", "Refuted", "Unconfirmed"]);
});

test("parseRunArgs threads criteria / artifactDir / runLabel (the 4b args)", () => {
  const { runConfig, errors } = H.parseRunArgs(
    validArgs({ criteria: [validCriterion()], artifactDir: ".qa-artifacts", runLabel: "qa-x" }),
  );
  assert.deepEqual(errors, []);
  assert.equal(runConfig.criteria.length, 1);
  assert.equal(runConfig.artifactDir, ".qa-artifacts");
  assert.equal(runConfig.runLabel, "qa-x");
});

test("artifactBase: one source for the artifact-dir default and trailing-slash trim", () => {
  assert.equal(H.artifactBase(undefined), ".qa-artifacts");
  assert.equal(H.artifactBase(""), ".qa-artifacts");
  assert.equal(H.artifactBase("out/dir///"), "out/dir");
  assert.equal(H.artifactBase(".qa-artifacts/"), ".qa-artifacts");
});

test("bootReportFromError: a thrown boot maps to the same failed-report shape a returned failure uses", () => {
  const r = H.bootReportFromError(new Error("spawn failed"));
  assert.equal(r.started, false);
  assert.equal(r.ready, false);
  assert.equal(r.attempts, 0);
  assert.match(r.logTail, /boot agent error: spawn failed/);
  // The downstream path is the SAME honest one: bootOutcome classifies failed, never pass.
  assert.equal(H.bootOutcome(r), "failed");
  const finding = H.couldNotRunFinding({ runCommand: "x", appUrl: "y" }, r);
  assert.match(finding.evidence.logTail, /boot agent error/);
});

test("verdictFor: unrequested state checks never bear on the verdict (the AC-3 regression)", () => {
  const report = {
    steps: [{ action: "open", ok: true }],
    expects: [{ expect: "heading visible", ok: true }],
    states: [
      { state: "empty", verdict: "fail" },
      { state: "error", verdict: "fail" },
    ],
  };
  // states: [] requested -- the extra driver observations are informational only.
  const v = H.verdictFor(report, []);
  assert.equal(v.verdict, "pass");
});

test("verdictFor: a REQUESTED state fail still fails the criterion", () => {
  const report = {
    steps: [{ action: "open", ok: true }],
    expects: [{ expect: "x", ok: true }],
    states: [{ state: "empty", verdict: "fail" }],
  };
  assert.equal(H.verdictFor(report, ["empty"]).verdict, "fail");
});

test("verdictFor: a requested not-checkable state folds to not-checkable, unrequested does not", () => {
  const report = {
    steps: [{ action: "a", ok: true }],
    expects: [{ expect: "x", ok: true }],
    states: [{ state: "loading", verdict: "not-checkable" }],
  };
  assert.equal(H.verdictFor(report, ["loading"]).verdict, "not-checkable");
  assert.equal(H.verdictFor(report, []).verdict, "pass");
});

// -----------------------------------------------------------------------------
// D3 (0041 S10a) -- the driver prompt's ORDER + separator, and the ONE artifact-dir shape
//
// (a) driverPrompt emitted its NARROWING `STATES SCOPE:` constraint BEFORE the role/task framing
//     and joined the two with no separator at all, so the agent read
//     `...never as a states[] entry.Runtime QA -- FLOW-DRIVING...`. The line had already been
//     patched twice (a non-interpolating string, then ASCII) and the ordering survived both --
//     because driverPrompt sat BELOW the helpers block and nothing could see it. It is pure
//     (params + sanitizeForPath + artifactBase + one const), so this slice relocated it INTO the
//     block; these pins are what that relocation buys.
//
// (b) artifactBase was documented as "the ONE source of the artifact-dir shape" and unit-tested
//     while having ZERO call sites; four other places re-implemented it inconsistently, and its
//     `/`-only trim left a trailing backslash on a Windows-style dir.
// -----------------------------------------------------------------------------

/** Lazily load the relocated driver-prompt helper INSIDE each test, so a missing/renamed
 * extraction fails only these pins (naming the helper) rather than aborting the whole file. */
function driverHelpers() {
  return loadHelpersFrom(SCRIPT_PATH, ["driverPrompt", "artifactBase", "screenshotPath", "sanitizeForPath"]);
}

const DRIVER_RUN_CONFIG = { runCommand: "npm run dev", appUrl: "http://localhost:3000" };

test("driverPrompt: the role/task framing comes FIRST, with a blank line before the STATES SCOPE constraint", () => {
  const D = driverHelpers();
  const p = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), "qa-2026", ".qa-artifacts");
  assert.ok(
    p.startsWith('Runtime QA -- FLOW-DRIVING for one acceptance criterion (id AC-1, feature "Add item").'),
    `the prompt must OPEN with the role/task framing; got: ${JSON.stringify(p.slice(0, 120))}`,
  );
  assert.ok(p.includes("\n\nSTATES SCOPE:"), "the narrowing constraint must be its own paragraph");
  assert.ok(
    p.indexOf("STATES SCOPE:") > p.indexOf("Runtime QA -- FLOW-DRIVING"),
    "the narrowing constraint must FOLLOW the framing it narrows",
  );
});

test("driverPrompt: the sentence-glued rendering is gone (the exact defect string)", () => {
  const D = driverHelpers();
  const p = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), "qa-2026", ".qa-artifacts");
  assert.ok(
    !p.includes("entry.Runtime QA"),
    "the STATES SCOPE clause and the framing must never be concatenated with no separator",
  );
  // Pin the paragraph SEQUENCE, not just the one seam the original defect glued: BOTH of the
  // constraint's seams are paragraph breaks, so dropping either separator turns this red.
  const paras = p.split("\n\n");
  assert.match(paras[0], /^Runtime QA -- FLOW-DRIVING for one acceptance criterion/);
  assert.match(paras[1], /^STATES SCOPE: check ONLY the states/);
  assert.match(paras[2], /^App URL: /);
});

test("driverPrompt: the STATES SCOPE clause still names the requested states (and the none-case)", () => {
  const D = driverHelpers();
  const withStates = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion({ states: ["empty", "error"] }), "r", ".qa-artifacts");
  assert.ok(withStates.includes("STATES SCOPE: check ONLY the states listed for THIS criterion (empty, error)"));
  const none = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion({ states: [] }), "r", ".qa-artifacts");
  assert.ok(none.includes("none -- perform NO state checks"));
});

test("driverPrompt: an api criterion gets the HTTP tooling line, an e2e one the Playwright line", () => {
  const D = driverHelpers();
  const api = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion({ check: "api" }), "r", ".qa-artifacts");
  assert.ok(api.includes("drive it over HTTP with curl/fetch via Bash"));
  const e2e = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), "r", ".qa-artifacts");
  assert.ok(e2e.includes("browser tooling unavailable in this session"), "the BROWSER_UNAVAILABLE_REASON const must interpolate");
  assert.ok(e2e.includes("NEVER fake a pass"));
});

test("driverPrompt: the shot dir derives from artifactBase -- a trailing separator never doubles", () => {
  const D = driverHelpers();
  // POSIX-style, the shape the default carries.
  const posix = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), "qa-2026", "out/qa///");
  assert.ok(posix.includes("UNDER `out/qa/qa-2026/`"), `got: ${posix.match(/UNDER `[^`]*`/)}`);
  // Windows-style -- the shape the `/`-only trim silently mangled into `out\qa\/qa-2026`.
  const win = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), "qa-2026", "out\\qa\\");
  assert.ok(win.includes("UNDER `out\\qa/qa-2026/`"), `got: ${win.match(/UNDER `[^`]*`/)}`);
  assert.ok(!win.includes("\\/"), "a Windows-style artifact dir must not leave a backslash beside the joiner");
});

test("driverPrompt: the .png path it tells the agent to SAVE to converges with the path the report CITES", () => {
  const D = driverHelpers();
  // The cross-agent contract: <base>/<runLabel>/<criterionId>-<slug>.png. driverPrompt names the
  // directory the driver saves into; screenshotPath names the file the report cites. If these two
  // ever diverge the report cites a file that was never written.
  const dir = "out/qa/";
  const label = "QA Run 1";
  const cited = D.screenshotPath(dir, label, "AC-1", "end");
  const citedDir = cited.slice(0, cited.lastIndexOf("/"));
  const p = D.driverPrompt(DRIVER_RUN_CONFIG, validCriterion(), label, dir);
  assert.equal(cited, "out/qa/qa-run-1/ac-1-end.png");
  assert.ok(p.includes(`UNDER \`${citedDir}/\``), `driverPrompt must save under ${citedDir}/`);
  assert.ok(p.includes("filenames like `AC-1-<slug>.png`"), "the filename convention must still be stated");
});

test("artifactBase: the trailing-separator trim covers BOTH separators (Windows-style dirs too)", () => {
  // Uses the top-level H deliberately -- this pin is about artifactBase alone and must not be
  // coupled to the driverPrompt relocation loading beside it.
  assert.equal(H.artifactBase("out\\qa\\"), "out\\qa");
  assert.equal(H.artifactBase("out\\qa\\\\"), "out\\qa");
  assert.equal(H.artifactBase("out/qa\\/"), "out/qa");
  // ... and the pre-existing POSIX behavior is unchanged.
  assert.equal(H.artifactBase("out/dir///"), "out/dir");
  assert.equal(H.artifactBase(undefined), ".qa-artifacts");
});

test("qa.js: the artifact-dir default and trim have ONE source -- artifactBase (no re-implementations)", () => {
  const src = readFileSync(SCRIPT_PATH, "utf8");
  // The default literal lives inside artifactBase and nowhere else. Four inconsistent copies is
  // the shape this slice removed; a fifth re-implementation turns this red.
  assert.equal(
    src.split('".qa-artifacts"').length - 1,
    1,
    "the .qa-artifacts default must appear exactly once -- inside artifactBase",
  );
  // The widened trim lives inside artifactBase and nowhere else, and the narrow `/`-only trim
  // (which left a trailing backslash) must be gone entirely.
  assert.equal(
    src.split('.replace(/[\\\\/]+$/, "")').length - 1,
    1,
    "the trailing-separator trim must appear exactly once -- inside artifactBase",
  );
  assert.ok(
    !src.includes('.replace(/\\/+$/, "")'),
    "the `/`-only trailing-slash trim leaves a trailing backslash on a Windows-style dir -- no copy may remain",
  );
});
