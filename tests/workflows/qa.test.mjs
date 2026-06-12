// tests/workflows/qa.test.mjs — node --test unit tests for the pure helpers of workflows/qa.js.
//
// Same extraction harness as verify.test.mjs / audit.test.mjs: the script is a Workflow-tool
// script (top-level control flow ending in a returned result; tool primitives agent()/parallel()/
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
const SCRIPT_PATH = join(REPO_ROOT, "workflows", "qa.js");

// The verbatim same-model tag — duplicated here on purpose as an independent fixture so a drift in
// the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// Independent verbatim fixtures for the could-not-run finding's load-bearing copy.
const EXPECTED_COULD_NOT_RUN_CLASS = "qa-could-not-run-app";
const EXPECTED_OBSERVED_TAG = "(observed this run — boot log attached)";
const EXPECTED_NO_RUN_REASON =
  'no run command recorded — add a "Run the app:" line to CLAUDE.md\'s detected-tooling block (or pass runCommand)';

/** Extract the marked helpers block and evaluate it, returning the named helpers.
 *
 * Markers are matched line-anchored (`^// --- helpers ---$`) so a mention of the marker text
 * inside the file's header comment is NOT mistaken for the real delimiter. */
function loadHelpers() {
  const src = readFileSync(SCRIPT_PATH, "utf8");
  const startMatch = src.match(/^\/\/ --- helpers ---$/m);
  const endMatch = src.match(/^\/\/ --- end helpers ---$/m);
  assert.ok(startMatch, "helpers block start marker not found (line-anchored) in workflows/qa.js");
  assert.ok(endMatch, "helpers block end marker not found (line-anchored) in workflows/qa.js");
  const start = startMatch.index;
  const end = endMatch.index;
  assert.ok(end > start, "helpers end marker precedes start marker");
  const block = src.slice(start, end);
  const names = [
    "MODELS",
    "SAME_MODEL_TAG",
    "READINESS_TIMEOUT_DEFAULT_SEC",
    "READINESS_TIMEOUT_CAP_SEC",
    "READINESS_PROBE_INTERVAL_SEC",
    "COULD_NOT_RUN_CLASS",
    "OBSERVED_THIS_RUN_TAG",
    "NO_RUN_COMMAND_REASON",
    "parseArgs",
    "parseRunArgs",
    "isRunInputError",
    "isComposeCommand",
    "readinessPlan",
    "bootOutcome",
    "teardownPlan",
    "couldNotRunFinding",
    "BOOT_SCHEMA",
    "TEARDOWN_SCHEMA",
  ];
  // No tool primitives are in scope inside this Function — so if any helper closed over
  // agent()/parallel()/phase()/log(), constructing or calling it would throw here.
  const factory = new Function(`${block}\n; return { ${names.join(", ")} };`);
  return factory();
}

const H = loadHelpers();

/** Build a valid run-args object; override fields per-case. */
function validArgs(overrides = {}) {
  return {
    runCommand: "uvicorn main:app --app-dir eval/fixture-app --port 8123",
    appUrl: "http://localhost:8123",
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

test("COULD_NOT_RUN_CLASS / OBSERVED_THIS_RUN_TAG / NO_RUN_COMMAND_REASON are verbatim (drift pins)", () => {
  assert.equal(H.COULD_NOT_RUN_CLASS, EXPECTED_COULD_NOT_RUN_CLASS);
  assert.equal(H.OBSERVED_THIS_RUN_TAG, EXPECTED_OBSERVED_TAG);
  assert.equal(H.NO_RUN_COMMAND_REASON, EXPECTED_NO_RUN_REASON);
});

// ─────────────────────────────────────────────────────────────────────────────
// parseArgs (copied verbatim — JSON-string boundary)
// ─────────────────────────────────────────────────────────────────────────────
test("parseArgs parses a JSON string and passes an object through", () => {
  assert.deepEqual(H.parseArgs('{"runCommand":"x","appUrl":"y"}'), { runCommand: "x", appUrl: "y" });
  const obj = { runCommand: "x", appUrl: "y" };
  assert.equal(H.parseArgs(obj), obj);
});

test("parseArgs throws loud on unparseable JSON (never a silent empty-args run)", () => {
  assert.throws(() => H.parseArgs("{not json"), /qa args: not valid JSON/);
});

// ─────────────────────────────────────────────────────────────────────────────
// parseRunArgs — defaults, cap, and the no-run-command finding path
// ─────────────────────────────────────────────────────────────────────────────
test("parseRunArgs applies the readiness default and trims/normalizes", () => {
  const { runConfig, errors } = H.parseRunArgs(validArgs({ runCommand: "  uvicorn x  ", appUrl: "  http://h  " }));
  assert.deepEqual(errors, []);
  assert.equal(runConfig.runCommand, "uvicorn x");
  assert.equal(runConfig.appUrl, "http://h");
  assert.equal(runConfig.readinessTimeoutSec, H.READINESS_TIMEOUT_DEFAULT_SEC);
  assert.equal(runConfig.teardownCommand, null);
  assert.deepEqual(runConfig.criteria, []); // 4b seam: absent ⇒ boot-only
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

// ─────────────────────────────────────────────────────────────────────────────
// isComposeCommand
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// readinessPlan — bounded attempts, never zero, never unbounded
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// bootOutcome — fail loud on a missing/malformed report
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// teardownPlan — precedence + the always-reap-the-PID rule
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// couldNotRunFinding — exact shape, deterministic confidence, evidence present
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// Schemas — required field sets pinned (the boot/teardown reports the agents must return)
// ─────────────────────────────────────────────────────────────────────────────
test("BOOT_SCHEMA requires started/ready/attempts (the load-bearing boot fields)", () => {
  assert.deepEqual(H.BOOT_SCHEMA.required, ["started", "ready", "attempts"]);
  assert.equal(H.BOOT_SCHEMA.properties.ready.type, "boolean");
});

test("TEARDOWN_SCHEMA requires toreDown (the teardown contract)", () => {
  assert.deepEqual(H.TEARDOWN_SCHEMA.required, ["toreDown"]);
});

test("isRunInputError: matches exactly the producer's missing-run-input prefixes", () => {
  // The producer/consumer string contract — parseRunArgs emits these prefixes; the partition
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
