// engine/qa.js -- runtime verification (QA) as an executable Workflow script. Two modes, selected by
// whether acceptance criteria are passed (the full contract is `meta.description` below):
//   boot-only (no criteria) -- boot with the recorded run command, probe a readiness URL within a
//     bounded wait, ALWAYS tear down (the port is verifiably freed), and on a boot failure surface
//     the evidence-carrying `qa-could-not-run-app` finding -- never a skip, never a pass.
//   full (criteria passed) -- boot, then one driver agent PER DRIVABLE criterion, run SEQUENTIALLY
//     (criteria mutate shared app state); manual criteria are NEVER driven. Each fail folds to a
//     lens-shaped UX finding (route + evidence, no file:line), deduped on class+route, then EXACTLY
//     ONE finding-verifier per surfaced finding (could-not-run stays exempt with its own tag).
//
// Distribution: read-from-install-path -- adopters invoke `${CLAUDE_PLUGIN_ROOT}/engine/qa.js`; this
// repo dogfoods `./engine/qa.js`. Never copied into an adopter repo -- see
// docs/claugentic-DECISIONS.md -> Plugin identity & distribution.
//
// Sandbox constraints: NO imports, NO filesystem, NO wall-clock/randomness (the orchestrator stamps
// times AFTER the run). Only `agent()`/`parallel()`/`phase()`/`log()`/`args`. The script itself has
// NO Bash and NO clock -- all file/process/clock work happens inside the agents it spawns. Call
// count is structurally bounded (boot + teardown = 2 in boot-only mode) -- no loops. Pure decision
// logic lives in the marked helpers block, unit-tested by tests/workflows/qa.test.mjs.

export const meta = {
  name: "qa",
  description:
    "Runtime verification (QA) as a Workflow script. Boots the recorded run command detached, probes the readiness URL on a bounded schedule (readinessPlan -- never unbounded), and ALWAYS tears down via teardownPlan (explicit override > docker compose down > kill the recorded PID) in a finally so the port is freed on success, boot failure, and mid-run error alike. A boot that never answers within the bound (or a missing/malformed report) classifies `failed` (fail loud -- never default to success) and produces exactly one lens-shaped `qa-could-not-run-app` finding with the command + probe attempts + boot-log tail as evidence, tagged (observed this run -- boot log attached). When acceptance criteria are passed (full mode): one driver agent per drivable criterion runs SEQUENTIALLY in a real browser (Playwright via ToolSearch) or over HTTP (check:api), performs the flow, checks the expects + the named empty/loading/error states, and screenshots under the artifact dir; each criterion folds to a pass|fail|not-checkable verdict (manual criteria are NEVER driven -- listed for a human). Every fail becomes a lens-shaped UX finding (ux-missing-empty-state / ux-missing-loading-state / ux-missing-error-state / ux-broken-flow) and EVERY finding gets exactly one finding-verifier (Refuted dropped+counted, Verified/Unconfirmed/deferred tagged; the could-not-run finding stays exempt). The run claims cross-model only on confirming self-reports.",
  // Bounded call count: boot + teardown + one driver per drivable criterion + one verifier per
  // surfaced finding -- no loops. The static cap is a backstop; the per-run criteria/findings counts
  // are the true bound, computed in code.
  budget: { agents: 40 },
};

// --- helpers ---
// Pure functions only -- no closure over tool primitives, so the harness can extract and eval this
// block standalone.

// The judge model, defined ONCE. It NAMES NO MODEL deliberately: a judge INHERITS the session's
// model, so independence is of ROLE and CLEAN CONTEXT, not of model, and the same-model TAG below
// reports what actually resulted. Pinned byte-identical (drift pin).
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

// The readiness-probe defaults and hard cap. The wait is ALWAYS bounded: the timeout clamps to
// [interval, READINESS_TIMEOUT_CAP] and attempts derive from it -- never zero, never unbounded.
const READINESS_TIMEOUT_DEFAULT_SEC = 60;
const READINESS_TIMEOUT_CAP_SEC = 300;
const READINESS_PROBE_INTERVAL_SEC = 2;

// The issueClass of the "could not run the app" finding -- a boot FACT of this run, not a claim
// about the code, so it carries the observed-this-run tag and NEVER (checked against the code).
const COULD_NOT_RUN_CLASS = "qa-could-not-run-app";

// The verbatim observed-this-run tag the could-not-run finding carries -- a boot fact, distinct
// from the audit's code-checked tags. Defined once (honesty trust surface).
const OBSERVED_THIS_RUN_TAG = "(observed this run -- boot log attached)";

// The verbatim no-run-command reason. Names the durable home (CLAUDE.md's detected-tooling block)
// so the fix is actionable. Defined once.
const NO_RUN_COMMAND_REASON =
  'no run command recorded -- add a "Run the app:" line to CLAUDE.md\'s detected-tooling block (or pass runCommand)';

// -- Slice 4b -- flow-driving constants --

// The acceptance-criterion `check` enum (FROZEN -- PRODUCT_SPEC_TEMPLATE carries it verbatim).
// `e2e` = a real browser (Playwright); `api` = HTTP-only (the driver's Bash/curl); `manual` = NEVER
// executed, listed for a human, verdict not-checkable. validateCriteria rejects anything else,
// naming the offending ids. Copied byte-identical to build-item.js (drift pin).
const CHECK_KINDS = ["e2e", "api", "manual"];

// The product-ux state-bar checks a criterion may request (docs/claugentic-standards/product-ux.md
// -> "Loading / empty / error states"). An empty array = no state checks. FROZEN with the schema.
const STATE_KINDS = ["empty", "loading", "error"];

// The runtime-finding issue classes, one per failed state-check kind + the broken-flow class. These
// fixed strings let dedupFindings key on (issueClass + route) and let the seeded-defect acceptance
// assert on exact classes; lens-shaped findings then join the same dedup -> verifier path.
const UX_ISSUE_CLASS = {
  empty: "ux-missing-empty-state",
  loading: "ux-missing-loading-state",
  error: "ux-missing-error-state",
  flow: "ux-broken-flow",
};

// The verbatim verdict-for-a-manual-criterion text -- NEVER driven, listed for a human with this
// exact reason (honesty trust surface: never silently dropped, never a pass).
const MANUAL_NOT_CHECKABLE_REASON = "manual by contract";

// The verbatim not-checkable reason when the session has no Playwright tooling -- every e2e verdict
// degrades to this, never a pass.
const BROWSER_UNAVAILABLE_REASON = "browser tooling unavailable in this session";

// Normalize the args boundary (copied verbatim from verify.js): a scriptPath invocation delivers
// `args` as a JSON STRING (observed 2026-06-11), an inline script the object. Unparseable = loud.
function parseArgs(raw) {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new Error("qa args: not valid JSON (" + (e && e.message ? e.message : e) + ")");
    }
  }
  return raw;
}

// Validate + normalize the run args at the boundary (FROZEN contract). Returns `{ runConfig, errors }`:
//   - `errors` is every shape error. The caller maps a missing/empty runCommand or appUrl to the
//     could-not-run FINDING, not a silent throw: a QA run that can't run reports that it can't run.
//   - `runConfig` is normalized (defaults applied, readinessTimeoutSec clamped) -- usable only when
//     errors is empty. Absent/empty criteria => a boot-only run.
function parseRunArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return { runConfig: null, errors: ["args must be an object"] };
  }
  const hasRunCommand = typeof args.runCommand === "string" && args.runCommand.trim().length > 0;
  const hasAppUrl = typeof args.appUrl === "string" && args.appUrl.trim().length > 0;
  if (!hasRunCommand) {
    errors.push("runCommand is required (non-empty string -- the recorded command that starts the app)");
  }
  if (!hasAppUrl) {
    errors.push("appUrl is required (non-empty string -- the readiness URL to probe)");
  }
  if (
    args.teardownCommand !== undefined &&
    !(typeof args.teardownCommand === "string" && args.teardownCommand.trim().length > 0)
  ) {
    errors.push("teardownCommand, when provided, must be a non-empty string");
  }
  let readinessTimeoutSec = READINESS_TIMEOUT_DEFAULT_SEC;
  if (args.readinessTimeoutSec !== undefined) {
    if (
      typeof args.readinessTimeoutSec !== "number" ||
      !Number.isFinite(args.readinessTimeoutSec) ||
      args.readinessTimeoutSec <= 0
    ) {
      errors.push("readinessTimeoutSec, when provided, must be a positive number (seconds)");
    } else {
      // Clamp to the hard cap -- never an unbounded wait (the bound is the resilience contract).
      readinessTimeoutSec = Math.min(args.readinessTimeoutSec, READINESS_TIMEOUT_CAP_SEC);
    }
  }
  if (args.criteria !== undefined && !Array.isArray(args.criteria)) {
    errors.push("criteria, when provided, must be an array (Slice 4b -- absent/empty => boot-only)");
  }
  const runConfig = {
    runCommand: hasRunCommand ? args.runCommand.trim() : "",
    appUrl: hasAppUrl ? args.appUrl.trim() : "",
    teardownCommand:
      typeof args.teardownCommand === "string" && args.teardownCommand.trim().length > 0
        ? args.teardownCommand.trim()
        : null,
    readinessTimeoutSec,
    // 4b seam: absent/empty criteria => boot-only. Threaded but unused in this slice.
    criteria: Array.isArray(args.criteria) ? args.criteria : [],
    artifactDir: typeof args.artifactDir === "string" ? args.artifactDir : null,
    runLabel: typeof args.runLabel === "string" ? args.runLabel : null,
  };
  return { runConfig, errors };
}

// Is this a docker compose invocation? `docker compose` (v2) or `docker-compose` (v1) at the start,
// case-insensitive, whitespace-tolerant. Drives the default teardown and the `-d` detached start.
function isComposeCommand(runCommand) {
  if (typeof runCommand !== "string") {
    return false;
  }
  return /^\s*docker(\s+compose|-compose)\b/i.test(runCommand);
}

// The bounded readiness probe plan (PURE -- the boot agent executes it): probe every interval up to
// the bound, ALWAYS >=1 attempt, never unbounded. Returns `{ intervalSec, timeoutSec, maxAttempts }`.
function readinessPlan(runConfig) {
  const timeoutSec =
    runConfig && typeof runConfig.readinessTimeoutSec === "number" && runConfig.readinessTimeoutSec > 0
      ? Math.min(runConfig.readinessTimeoutSec, READINESS_TIMEOUT_CAP_SEC)
      : READINESS_TIMEOUT_DEFAULT_SEC;
  const intervalSec = READINESS_PROBE_INTERVAL_SEC;
  // ceil so the bound is fully covered; floor of 1 so a sub-interval timeout still probes once.
  const maxAttempts = Math.max(1, Math.ceil(timeoutSec / intervalSec));
  return { intervalSec, timeoutSec, maxAttempts };
}

// Classify the boot agent's report into `ready` / `failed`. FAIL LOUD: missing or malformed (not an
// object, or `ready` not strictly true) is `failed` -- the outcome NEVER defaults to success.
function bootOutcome(report) {
  if (!report || typeof report !== "object") {
    return "failed";
  }
  return report.ready === true ? "ready" : "failed";
}

// The teardown instruction (PURE -- the teardown agent executes it). Runs on success, boot failure
// and mid-run error alike (the control flow wraps it in a finally). Precedence:
//   1. an explicit teardownCommand wins (the user's recorded stop command);
//   2. else `docker compose down` when the run command is a compose invocation;
//   3. else kill the PID the boot agent recorded (a backgrounded dev-server).
// A failed boot that recorded a PID still yields a kill -- a half-started process must be reaped,
// never leak a port. Returns `{ method, command? , pid? }`.
function teardownPlan(runConfig, bootReport) {
  if (runConfig && typeof runConfig.teardownCommand === "string" && runConfig.teardownCommand.length > 0) {
    return { method: "command", command: runConfig.teardownCommand };
  }
  if (runConfig && isComposeCommand(runConfig.runCommand)) {
    return { method: "command", command: "docker compose down" };
  }
  const pid = bootReport && bootReport.pid != null ? bootReport.pid : null;
  if (pid != null) {
    return { method: "kill", pid };
  }
  // No override, not compose, no recorded PID -- nothing to stop. The teardown agent reports it as
  // a no-op, never a silent skip.
  return { method: "none" };
}

// Build the one lens-shaped "could not run the app" finding (PURE) -- either a no-run-command
// boundary failure (no boot report) or a boot that never answered. Fixed COULD_NOT_RUN_CLASS;
// confidence 'deterministic' (an observed boot fact of THIS run); evidence = command + probe
// attempts + boot-log tail; the observed-this-run tag, NOT a code-checked claim.
function couldNotRunFinding(runConfig, report) {
  const command = runConfig && runConfig.runCommand ? runConfig.runCommand : null;
  const appUrl = runConfig && runConfig.appUrl ? runConfig.appUrl : null;
  const attempts = report && report.attempts != null ? report.attempts : 0;
  const logTail = report && typeof report.logTail === "string" ? report.logTail : "";
  const reason = command ? null : NO_RUN_COMMAND_REASON;
  const plainEnglish = command
    ? `The app could not be started or never became ready: the recorded command ran but ${appUrl || "the readiness URL"} did not answer within the bounded wait (${attempts} probe attempt(s)). The QA review could not run against a live app -- this is reported, not skipped.`
    : `${NO_RUN_COMMAND_REASON}. The QA review could not run -- this is reported, not skipped.`;
  return {
    issueClass: COULD_NOT_RUN_CLASS,
    confidence: "deterministic",
    verificationTag: OBSERVED_THIS_RUN_TAG,
    plainEnglish,
    reason,
    evidence: {
      command,
      appUrl,
      attempts,
      logTail,
    },
  };
}

// Structured-output schemas as JSON Schema object literals (no imports). The Workflow tool
// validates each agent's structured output against these at the tool-call layer.

// The boot agent's report: started, ready, the recorded PID + log path, the log tail (last <=50
// lines, on failure), and the probe-attempt count. bootOutcome reads `ready` / `started`.
const BOOT_SCHEMA = {
  type: "object",
  required: ["started", "ready", "attempts"],
  properties: {
    started: { type: "boolean" },
    ready: { type: "boolean" },
    pid: { type: ["integer", "string", "null"] },
    logPath: { type: ["string", "null"] },
    logTail: { type: "string" },
    attempts: { type: "integer" },
    // The script has no clock -- the boot agent stamps the run label (artifact-dir leaf) when the
    // skill didn't pass one. Threaded back to the flow-driving stage.
    runLabel: { type: ["string", "null"] },
  },
};

// The teardown agent's report: did it stop the app, and is the port verifiably free afterwards --
// a port still bound is a leaked process, reported loudly.
const TEARDOWN_SCHEMA = {
  type: "object",
  required: ["toreDown"],
  properties: {
    toreDown: { type: "boolean" },
    portFree: { type: ["boolean", "null"] },
    note: { type: "string" },
  },
};

// The driver agent's per-criterion report. One driver per drivable criterion: it performs the flow,
// evaluates each expect, runs the requested state checks, and records the screenshots it saved.
// `notCheckable` is the honest escape hatch -- verdictFor folds it to not-checkable, never a pass.
const DRIVER_SCHEMA = {
  type: "object",
  required: ["steps", "expects", "states", "screenshots"],
  properties: {
    notCheckable: { type: "boolean" },
    notCheckableReason: { type: ["string", "null"] },
    observedStatus: { type: ["integer", "null"] },
    steps: {
      type: "array",
      items: {
        type: "object",
        required: ["action", "ok"],
        properties: {
          action: { type: "string" },
          ok: { type: "boolean" },
          note: { type: ["string", "null"] },
        },
      },
    },
    expects: {
      type: "array",
      items: {
        type: "object",
        required: ["expect", "ok"],
        properties: {
          expect: { type: "string" },
          ok: { type: "boolean" },
          evidence: { type: ["string", "null"] },
        },
      },
    },
    states: {
      type: "array",
      items: {
        type: "object",
        required: ["state", "verdict"],
        properties: {
          state: { type: "string", enum: ["empty", "loading", "error"] },
          verdict: { type: "string", enum: ["pass", "fail", "not-checkable"] },
          evidence: { type: ["string", "null"] },
          note: { type: ["string", "null"] },
        },
      },
    },
    screenshots: { type: "array", items: { type: "string" } },
  },
};

// The finding-verifier's verdict schema (runtime findings re-checked). The self-reported model
// family is REQUIRED -- the run claims cross-model only on a confirming report. Same shape as
// audit.js's VERIFIER_SCHEMA.
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

// -- Slice 4b -- flow-driving helpers (pure; the driver/verifier agents execute the I/O) --

// Validate the acceptance criteria against the FROZEN schema (id/feature/flow/expect/states/check).
// FAIL LOUD: every error names the offending id (or index when the id is missing/duplicate) -- never
// silently filtered, since a dropped criterion is a silently-unchecked promise. An empty/absent list
// is valid (=> boot-only). Returns string[] (empty = valid).
function validateCriteria(criteria) {
  const errors = [];
  if (criteria === undefined || criteria === null) {
    return errors; // absent => boot-only (valid)
  }
  if (!Array.isArray(criteria)) {
    return ["criteria must be an array"];
  }
  const seenIds = new Set();
  criteria.forEach((c, i) => {
    const at = c && typeof c.id === "string" && c.id.length > 0 ? `id '${c.id}'` : `criteria[${i}]`;
    if (!c || typeof c !== "object" || Array.isArray(c)) {
      errors.push(`${at}: each criterion must be an object`);
      return;
    }
    if (typeof c.id !== "string" || c.id.trim().length === 0) {
      errors.push(`criteria[${i}]: id is required (non-empty string)`);
    } else if (seenIds.has(c.id)) {
      errors.push(`${at}: duplicate id -- every criterion id must be unique`);
    } else {
      seenIds.add(c.id);
    }
    if (typeof c.feature !== "string" || c.feature.trim().length === 0) {
      errors.push(`${at}: feature is required (non-empty string)`);
    }
    if (!Array.isArray(c.flow) || c.flow.length === 0) {
      errors.push(`${at}: flow is required (non-empty array of ordered user actions)`);
    } else if (!c.flow.every((s) => typeof s === "string" && s.length > 0)) {
      errors.push(`${at}: flow must be an array of non-empty strings`);
    }
    if (!Array.isArray(c.expect) || c.expect.length === 0) {
      errors.push(`${at}: expect is required (non-empty array of observable outcomes)`);
    } else if (!c.expect.every((s) => typeof s === "string" && s.length > 0)) {
      errors.push(`${at}: expect must be an array of non-empty strings`);
    }
    if (!Array.isArray(c.states)) {
      errors.push(`${at}: states is required (array -- may be empty)`);
    } else if (!c.states.every((s) => STATE_KINDS.includes(s))) {
      errors.push(`${at}: states entries must each be one of ${STATE_KINDS.join("|")}`);
    }
    if (typeof c.check !== "string" || !CHECK_KINDS.includes(c.check)) {
      errors.push(`${at}: check must be one of ${CHECK_KINDS.join("|")} (got ${JSON.stringify(c.check)})`);
    }
  });
  return errors;
}

// Partition the validated criteria into drivable (e2e|api -- one driver each, run SEQUENTIALLY:
// criteria mutate app state, so parallel drivers would interfere) and manual (NEVER driven, listed
// for a human). PURE. Returns `{ drivable, manual }`.
function criterionPlan(criteria) {
  const list = Array.isArray(criteria) ? criteria : [];
  return {
    drivable: list.filter((c) => c.check === "e2e" || c.check === "api"),
    manual: list.filter((c) => c.check === "manual"),
  };
}

// Fold one driver report into a verdict: `pass` / `fail` / `not-checkable` (+ reason).
// Precedence (FAIL LOUD -- never default to pass):
//   - missing/malformed report                                  => not-checkable (loudly)
//   - the driver flagged the run unexecutable (no browser, ...)  => not-checkable + reason
//   - ANY failed step, failed expect, or state verdict 'fail'    => fail
//   - all steps ok AND all expects ok AND no state-fail          => pass
//   - otherwise (some checks not-checkable, none failed)         => not-checkable
function verdictFor(report, requestedStates) {
  if (!report || typeof report !== "object") {
    return { verdict: "not-checkable", reason: "the driver returned no usable report" };
  }
  if (report.notCheckable === true || typeof report.notCheckableReason === "string") {
    return {
      verdict: "not-checkable",
      reason:
        typeof report.notCheckableReason === "string" && report.notCheckableReason.length > 0
          ? report.notCheckableReason
          : "the driver could not execute this criterion",
    };
  }
  const steps = Array.isArray(report.steps) ? report.steps : [];
  const expects = Array.isArray(report.expects) ? report.expects : [];
  // Only the criterion's REQUESTED states bear on the verdict: extra observations are
  // informational evidence, and an unrequested check can never fail a criterion that did not ask
  // for it (2026-06-12 dogfood: AC-3 with states:[] failed on checks it never requested).
  const requested = Array.isArray(requestedStates) ? requestedStates : [];
  const states = (Array.isArray(report.states) ? report.states : []).filter(
    (s) => s && requested.includes(s.state),
  );
  const stepFailed = steps.some((s) => s && s.ok === false);
  const expectFailed = expects.some((e) => e && e.ok === false);
  const stateFailed = states.some((s) => s && s.verdict === "fail");
  if (stepFailed || expectFailed || stateFailed) {
    return { verdict: "fail", reason: null };
  }
  const stateNotCheckable = states.some((s) => s && s.verdict === "not-checkable");
  const allStepsOk = steps.every((s) => s && s.ok === true);
  const allExpectsOk = expects.every((e) => e && e.ok === true);
  if (allStepsOk && allExpectsOk && !stateNotCheckable) {
    return { verdict: "pass", reason: null };
  }
  // No hard failure, but something could not be checked (too-fast-to-observe / unreachable
  // surface). Honest: not-checkable, never a pass and never a fail.
  return {
    verdict: "not-checkable",
    reason: "some checks could not be performed (see the per-check evidence)",
  };
}

// Map a failed criterion's driver report to lens-shaped runtime findings (PURE). One per failure
// kind: a failed FLOW (step/expect) => ux-broken-flow; a failed STATE check => that state's
// ux-missing-*-state class. `deterministic` for an observed protocol fact (a 404/500, an element
// provably absent), `judgment` for an interpretive call. Findings cite route + evidence; `file:line`
// is deliberately ABSENT -- the runtime observes the product, and the verifier locates the code.
// Only `fail` verdicts yield findings.
function findingsFrom(verdicts) {
  const findings = [];
  for (const v of Array.isArray(verdicts) ? verdicts : []) {
    if (!v || v.verdict !== "fail" || !v.report) {
      continue;
    }
    const report = v.report;
    const route = typeof v.route === "string" ? v.route : "";
    const screenshots = Array.isArray(report.screenshots) ? report.screenshots : [];
    const steps = Array.isArray(report.steps) ? report.steps : [];
    const expects = Array.isArray(report.expects) ? report.expects : [];
    const states = Array.isArray(report.states) ? report.states : [];

    const flowFailed = steps.some((s) => s && s.ok === false) || expects.some((e) => e && e.ok === false);
    if (flowFailed) {
      const badStep = steps.find((s) => s && s.ok === false);
      const badExpect = expects.find((e) => e && e.ok === false);
      const observedStatus =
        report.observedStatus != null || (badExpect && /\b(404|500|4\d\d|5\d\d)\b/.test(String(badExpect.evidence || "")));
      findings.push({
        issueClass: UX_ISSUE_CLASS.flow,
        criterionId: v.id,
        route,
        confidence: observedStatus ? "deterministic" : "judgment",
        plainEnglish:
          (badStep && badStep.note) ||
          (badExpect && `Expected "${badExpect.expect}" did not hold`) ||
          "The flow could not be completed as specified.",
        evidence: {
          observedStatus: report.observedStatus != null ? report.observedStatus : null,
          observedText: badExpect ? badExpect.evidence : badStep ? badStep.note : null,
          screenshots,
        },
      });
    }
    for (const st of states) {
      if (!st || st.verdict !== "fail") {
        continue;
      }
      const cls = UX_ISSUE_CLASS[st.state];
      if (!cls) {
        continue; // an unknown state kind never silently becomes a flow finding
      }
      findings.push({
        issueClass: cls,
        criterionId: v.id,
        route,
        // An empty/error state that is provably absent (a blank surface observed) is a
        // deterministic UI fact; a 'loading' judgment is interpretive.
        confidence: st.state === "loading" ? "judgment" : "deterministic",
        plainEnglish:
          st.note ||
          `The ${st.state} state is not handled on this surface (a designed ${st.state} state is missing).`,
        evidence: {
          state: st.state,
          observedText: st.evidence != null ? st.evidence : null,
          screenshots,
        },
      });
    }
  }
  return findings;
}

// Merge duplicate runtime findings, keyed on issueClass + route (the audit's same-class rule,
// route-scoped because the runtime observes a surface, not a file:line). Same class at the same
// route merges (union of criterionIds + screenshots, first concrete plainEnglish, weakest
// confidence wins); distinct classes, or the same class elsewhere, stay separate. First-seen order.
function dedupFindings(findings) {
  const byKey = new Map();
  for (const finding of Array.isArray(findings) ? findings : []) {
    const key = `${finding.issueClass}@@${finding.route || ""}`;
    if (!byKey.has(key)) {
      byKey.set(key, {
        ...finding,
        criterionIds: finding.criterionId != null ? [finding.criterionId] : [],
      });
      continue;
    }
    const merged = byKey.get(key);
    if (finding.criterionId != null && !merged.criterionIds.includes(finding.criterionId)) {
      merged.criterionIds.push(finding.criterionId);
    }
    const inShots = finding.evidence && Array.isArray(finding.evidence.screenshots) ? finding.evidence.screenshots : [];
    if (merged.evidence && Array.isArray(merged.evidence.screenshots)) {
      for (const s of inShots) {
        if (!merged.evidence.screenshots.includes(s)) {
          merged.evidence.screenshots.push(s);
        }
      }
    }
    if (finding.confidence === "judgment") {
      merged.confidence = "judgment"; // weakest wins, never upgraded
    }
  }
  return [...byKey.values()];
}

// Normalize ONE artifact-path segment (PURE): lowercase, non-[a-z0-9._-] -> '-', collapsed, so a
// free-text label or id can never escape the artifact dir or break the path. The ONLY escape guard
// on both live legs (the boundary normalization artifacts.dir reuses, and driverPrompt's shotDir);
// idempotent, so the second application is a no-op.
function sanitizeForPath(s) {
  return String(s == null ? "" : s)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    // Collapse any run of 2+ dots to a single one -- a surviving `..` would be a parent-dir escape.
    .replace(/\.{2,}/g, ".")
    .replace(/^[.-]+|[.-]+$/g, "")
    .replace(/-{2,}/g, "-");
}

// Apply the finding-verifier verdicts to the surfaced runtime findings (PURE) -- audit.js's
// applyVerdicts mapping, runtime-shaped:
//   Verified    -> kept + tag (checked against the code) + evidence
//   Unconfirmed -> kept + tag (could not confirm independently -- model's assertion)
//   Refuted     -> dropped + counted; its verifier's self-report still rides out in refutedRunningAs,
//                  so a reviewer that decided what reaches the backlog stays in the cross-model fold
//   no verdict  -> kept + tag (! not yet verified -- re-run to confirm)  [deferred]
// The COULD-NOT-RUN finding is EXEMPT (a boot fact, not a code claim), passed through untouched with
// its own tag and matched by issueClass, not index. `results` is aligned to `findings`.
function applyVerifierVerdicts(findings, results) {
  const kept = [];
  const refutedRunningAs = [];
  let refutedCount = 0;
  (Array.isArray(findings) ? findings : []).forEach((finding, i) => {
    if (finding && finding.issueClass === COULD_NOT_RUN_CLASS) {
      kept.push({ ...finding }); // exempt -- keeps its observed-this-run tag untouched
      return;
    }
    const result = Array.isArray(results) ? results[i] : undefined;
    const verdict = result && result.verdict ? result.verdict : null;
    if (verdict === "Refuted") {
      refutedCount += 1;
      // A verifier that RAN and refuted pushes its report (null = ran, no self-report -> the
      // conservative floor). Never filter: absence is a shorter ARRAY, not a null entry.
      refutedRunningAs.push(result && result.runningAs != null ? result.runningAs : null);
      return; // dropped
    }
    let verificationTag;
    let verificationState;
    let evidence = "";
    if (verdict === "Verified") {
      verificationState = "verified";
      verificationTag = "(checked against the code)";
      evidence = result && result.evidence != null ? result.evidence : "";
    } else if (verdict === "Unconfirmed") {
      verificationState = "unconfirmed";
      verificationTag = "(could not confirm independently -- model's assertion)";
      evidence = result && result.evidence != null ? result.evidence : "";
    } else {
      verificationState = "deferred";
      verificationTag = "(! not yet verified -- re-run to confirm)";
    }
    kept.push({
      ...finding,
      verificationState,
      verificationTag,
      verifierEvidence: evidence,
      verifierRunningAs: result && result.runningAs != null ? result.runningAs : null,
    });
  });
  return { kept, refutedCount, refutedRunningAs };
}

// The error-partition predicate: which boundary errors become the honest could-not-run FINDING
// (missing run inputs) vs which throw (caller-contract bugs). In the helpers block so the producer
// (parseRunArgs message prefixes) / consumer string contract is test-pinned -- a reworded message
// must turn a test red, never silently reroute a missing runCommand into a throw.
function isRunInputError(msg) {
  return (
    typeof msg === "string" &&
    (msg.startsWith("runCommand is required") || msg.startsWith("appUrl is required"))
  );
}

// The ONE source of the artifact-dir shape: default + trailing-separator trim. driverPrompt and the
// top-level artifactDir both derive from it. BOTH path segments normalize once at the boundary --
// the dir here, the runLabel through sanitizeForPath -- which is what makes the save-path and the
// report-path convergent; a THIRD segment must normalize there too. It once carried this claim with
// ZERO call sites while four places re-implemented it, already drifted. The trim covers BOTH
// separators: a `/`-only trim left a backslash that joined as `out\qa\/<label>` (0041 S10a, D3).
function artifactBase(dir) {
  // Trim FIRST, then default: defaulting first is NOT idempotent (an all-separator dir trims to
  // "" and a second application substitutes the default), and the driver path applies this twice.
  const trimmed = (dir ? String(dir) : "").replace(/[\\/]+$/, "");
  return trimmed.length ? trimmed : ".qa-artifacts";
}

// Map a THROWN boot-agent error to the same failed-boot report shape a returned failure uses -- one
// downstream path (bootOutcome -> couldNotRunFinding), pure so the mapping is unit-pinned.
function bootReportFromError(err) {
  const msg = err && err.message ? err.message : String(err);
  return {
    started: false,
    ready: false,
    attempts: 0,
    logTail: `boot agent error: ${msg}`,
  };
}

// Build the driver agent's prompt for one criterion. The agent reaches Playwright via ToolSearch,
// drives the flow, evaluates the expects, runs the requested state checks, and saves screenshots
// under the artifact dir (the script has no filesystem). The state-check semantics are stated inline
// so the agent applies the product-ux bar, not its own guess.
//
// PURE, so it lives INSIDE the helpers block ON PURPOSE: below the block nothing could test it, and
// the prompt shipped for three releases with its narrowing STATES SCOPE clause emitted BEFORE the
// role framing and glued to it with no separator (`...never as a states[] entry.Runtime QA --
// FLOW-DRIVING...`), through two prior patches. Do not move it back out (0041 S10a, D3).
function driverPrompt(runConfig, criterion, runLabel, artifactDir) {
  const isApi = criterion.check === "api";
  const shotDir = `${artifactBase(artifactDir)}/${sanitizeForPath(runLabel) || "run"}`;
  const toolingLine = isApi
    ? "This is an `api` criterion -- drive it over HTTP with curl/fetch via Bash (no browser). " +
      "Each flow step is a described HTTP call; each expect is a response observable (status, body text, header)."
    : "This is an `e2e` criterion -- drive it in a REAL browser. FIRST load the Playwright browser " +
      "tools via ToolSearch (query 'playwright browser' -- e.g. select the `mcp__playwright__browser_*` " +
      "set), THEN navigate, click, type, and snapshot. If the Playwright tools are unavailable in this " +
      "session, set notCheckable=true and notCheckableReason='" + BROWSER_UNAVAILABLE_REASON + "' -- " +
      "NEVER fake a pass.";
  return (
    // The role/task framing leads; the narrowing STATES SCOPE constraint FOLLOWS it as its own
    // paragraph. Order and the `\n\n` separator are both pinned -- an agent cannot honor a
    // constraint stated before it knows the task, and a glued sentence reads as one run-on.
    `Runtime QA -- FLOW-DRIVING for one acceptance criterion (id ${criterion.id}, feature "${criterion.feature}").\n\n` +
    `STATES SCOPE: check ONLY the states listed for THIS criterion (${(criterion.states || []).length ? criterion.states.join(", ") : "none -- perform NO state checks"}). Any other state observation you happen to make is informational evidence only -- report it in a note, never as a states[] entry.\n\n` +
    `App URL: ${runConfig.appUrl}\n` +
    `${toolingLine}\n\n` +
    `Flow (perform each ordered step; a step you cannot perform fails the criterion at that step, with a note):\n` +
    criterion.flow.map((s, i) => `  ${i + 1}. ${s}`).join("\n") +
    `\n\nExpect (evaluate each AFTER the flow -- ALL must hold for a pass; record evidence: the observed text, ` +
    `element presence/absence, URL, count, or HTTP status):\n` +
    criterion.expect.map((e) => `  - ${e}`).join("\n") +
    `\n\nState checks to run on the surface this criterion lands on (${criterion.states.length ? criterion.states.join(", ") : "none"}):\n` +
    `  - empty: reach the zero-data condition (this run may boot FIXTURE_SEED=0). pass = a designed zero-state ` +
    `(a message/CTA explaining what goes here); fail = a blank void / raw placeholder; zero-data unreachable ` +
    `non-destructively => verdict not-checkable + reason.\n` +
    `  - loading: observe DURING the fetch. pass = a layout-reserved indicator OR a sub-1s render (instant needs ` +
    `no spinner -- the product-ux response-time threshold); fail = a >1s visible blank/jank with no indicator; ` +
    `commonly verdict not-checkable with note 'too fast to observe' -- that is HONEST, not a fail.\n` +
    `  - error: induce a NON-DESTRUCTIVE failure where the flow has one (invalid input, a failing call). pass = a ` +
    `human-readable message + a recovery path; fail = a silent failure / raw stack / dead end; no inducible path => ` +
    `verdict not-checkable + reason.\n\n` +
    `Screenshots: save one end-of-flow screenshot and one per failed step/expect/state UNDER \`${shotDir}/\` ` +
    `(filenames like \`${criterion.id}-<slug>.png\`); return their paths. (For an \`api\` criterion, screenshots ` +
    `may be empty.)\n\n` +
    `Return the structured report: steps [{action, ok, note}], expects [{expect, ok, evidence}], states ` +
    `[{state, verdict, evidence, note}], screenshots [paths], and observedStatus (the HTTP status when one is ` +
    `the load-bearing observation, else null). You MAP plain-English steps to tool calls by judgment -- state ` +
    `that in your notes; you attempt the flow, you do not prove the app correct.`
  );
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

// Build the boot agent's prompt from the validated run config + the bounded readiness plan. The
// agent (not the script) has Bash. When `runLabel` is null the agent ALSO stamps one
// (`qa-<timestamp>`) -- the script has no clock -- and it is threaded back to the drivers.
function bootPrompt(runConfig, plan, runLabel) {
  const compose = isComposeCommand(runConfig.runCommand);
  const startHint = compose
    ? "This is a docker compose command -- it detaches with `-d` (start it so it returns control)."
    : "This is a dev-server command -- start it BACKGROUNDED, redirect its stdout+stderr to a log file, and record its PID (return the PID and the log path).";
  const labelHint =
    runLabel == null
      ? "Also generate a run label `qa-<timestamp>` (e.g. `qa-20260612-143000`) and return it as runLabel -- " +
        "it names the screenshot folder for the flow-driving stage."
      : `The run label is already \`${runLabel}\` -- echo it back as runLabel.`;
  return (
    `Runtime QA -- BOOT stage. Start the app and confirm it is ready.\n\n` +
    `Run command: \`${runConfig.runCommand}\`\n` +
    `Readiness URL: ${runConfig.appUrl}\n` +
    `${startHint}\n\n` +
    `Then probe the readiness URL with curl every ~${plan.intervalSec}s, up to ${plan.maxAttempts} attempts ` +
    `(the bounded wait of ${plan.timeoutSec}s -- NEVER wait unbounded). Ready = an HTTP response (any 2xx/3xx/4xx ` +
    `means the server answered; a connection refusal/timeout means not-yet).\n\n` +
    `${labelHint}\n\n` +
    `Return the structured report: started, ready, pid (if a dev-server), logPath, logTail (the LAST <=50 lines ` +
    `of the boot log -- REQUIRED on failure so the could-not-run finding carries evidence), attempts (how many ` +
    `probes you made), and runLabel. If the command itself fails to launch, set started=false and put the launch ` +
    `error in logTail. Do NOT tear anything down -- the script's teardown stage owns that.`
  );
}

// Build the teardown agent's prompt from the (pure) teardown plan. The agent has Bash; it executes
// the planned method and verifies the port is free.
function teardownPrompt(runConfig, plan) {
  let instruction;
  if (plan.method === "command") {
    instruction = `Stop the app by running: \`${plan.command}\``;
  } else if (plan.method === "kill") {
    instruction = `Stop the app by killing PID ${plan.pid} (and any child processes it spawned).`;
  } else {
    instruction =
      "No explicit stop command, not a compose run, and no PID was recorded -- there may be nothing to stop. " +
      "Check whether anything is still bound to the app's port and stop it if so; otherwise report a no-op.";
  }
  return (
    `Runtime QA -- TEARDOWN stage. Always runs (success, boot failure, or mid-run error).\n\n` +
    `${instruction}\n` +
    `Readiness URL: ${runConfig.appUrl}\n\n` +
    `After stopping, VERIFY the port is free (the app's URL no longer answers / nothing is bound to its port). ` +
    `Return: toreDown (did you stop it), portFree (is the port verifiably free afterwards -- null if you could not check), ` +
    `and a short note. A port still bound is a leaked process -- report it loudly, never a silent success.`
  );
}

// Build the finding-verifier's CLEAN-CONTEXT input for a runtime finding: the claim + route +
// evidence, NEVER the driver's rationale. Runtime findings have no file:line -- the route + observed
// evidence are the anchor, and the verifier locates the implicated code itself.
function verifierPrompt(finding) {
  const ev = finding && finding.evidence ? finding.evidence : {};
  const shots = Array.isArray(ev.screenshots) ? ev.screenshots : [];
  return (
    `Independently REFUTE this single RUNTIME (UX) finding against the actual product code (refute-first; ` +
    `clean context -- you are NOT given the driver's rationale, only the observed claim + route + evidence). ` +
    `Open your response with "RUNNING AS: <model family>" and report it in runningAs.\n\n` +
    `Issue class: ${finding.issueClass}. Criterion: ${finding.criterionId || "(merged)"}. Route: ${finding.route || "(unknown)"}.\n` +
    `Claim (plain English): ${finding.plainEnglish}\n` +
    `Observed evidence: ${JSON.stringify({ observedStatus: ev.observedStatus, observedText: ev.observedText, state: ev.state })}\n` +
    `Screenshots saved this run: ${JSON.stringify(shots)}\n` +
    `Finder's confidence label: ${finding.confidence}\n\n` +
    `This is a RUNTIME observation, not a code line-number claim -- locate the implicated handler/template/route ` +
    `yourself (use docs/claugentic-ARCHITECTURE_TREE.md as the index), READ it, and decide: is the observed UX gap genuinely ` +
    `in the code (a missing empty/error state, a broken POST route), or did the driver misread a state that is ` +
    `actually handled? Return verdict (Verified|Refuted|Unconfirmed), evidence (the proof/disproof with file:line), ` +
    `and one plain-English line.`
  );
}

// Spawn one finding-verifier; one respawn on failure (the result then can't confirm a different
// family -> the same-model tag); a second failure returns null and the finding is marked deferred,
// never a silent skip. audit.js's spawnVerifier, runtime-shaped. Each attempt routes through the
// namespace fallback, which resolves INSIDE one attempt -- a bare retry consumes none of the one
// respawn and cannot influence the same-model tag (0041 S10b, D6).
async function spawnVerifier(finding) {
  const prompt = verifierPrompt(finding);
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
    label: `qa:verify:${finding.criterionId || finding.issueClass}`,
    phase: "Verify",
  });
  if (first.out != null) {
    return first.out;
  }
  const second = await attempt({
    agentType: nsAgent("finding-verifier"),
    schema: VERIFIER_SCHEMA,
    label: `qa:verify:${finding.criterionId || finding.issueClass}:respawn`,
    phase: "Verify",
  });
  if (second.out != null) {
    // Forced no-override respawn: drop the self-report so it can't claim a different family.
    return { ...second.out, runningAs: "" };
  }
  return null;
}

// -- Top-level control flow (Workflow scripts run in an async context; no module wrapper). --

// Validate at the boundary. A missing/empty runCommand or appUrl is NOT a throw -- it is the
// could-not-run finding (a QA run that can't run reports it). Any OTHER shape error fails loud.
const input = parseArgs(args);
const { runConfig, errors } = parseRunArgs(input);

// Partition the errors: the missing-run-inputs class becomes the finding; the rest throw.
const runInputErrors = errors.filter(isRunInputError);
const otherErrors = errors.filter((e) => !runInputErrors.includes(e));
if (otherErrors.length > 0) {
  throw new Error(`qa args invalid:\n  - ${otherErrors.join("\n  - ")}`);
}

// Validate the acceptance criteria (FROZEN schema). Invalid criteria are a caller-contract bug --
// fail loud naming the offending ids, NEVER silently filter (a dropped criterion is a
// silently-unchecked promise). An absent/empty list => boot-only.
{
  const criteriaErrors = validateCriteria(runConfig ? runConfig.criteria : []);
  if (criteriaErrors.length > 0) {
    throw new Error(`qa criteria invalid:\n  - ${criteriaErrors.join("\n  - ")}`);
  }
}

// No runnable command/URL -- emit the could-not-run finding and stop (never a fake pass, never a
// silent skip); nothing was started, so nothing to tear down. Mode stays criteria-derived so a full
// run lacking a command still reports honestly that it could not run.
if (runInputErrors.length > 0) {
  log(`qa: cannot run -- ${runInputErrors.join("; ")}. Emitting the could-not-run finding.`);
  const finding = couldNotRunFinding(runConfig, null);
  const hasCriteria = runConfig && Array.isArray(runConfig.criteria) && runConfig.criteria.length > 0;
  const { manual } = criterionPlan(runConfig ? runConfig.criteria : []);
  return {
    ran: false,
    mode: hasCriteria ? "full" : "boot-only",
    boot: { started: false, ready: false, attempts: 0 },
    verdicts: [],
    findings: [finding],
    refutedCount: 0,
    manualCriteria: manual.map((c) => ({ id: c.id, feature: c.feature })),
    artifacts: { dir: null, screenshots: [] },
    crossModel: SAME_MODEL_TAG,
    summary:
      "QA did not run: no runnable command was provided. The could-not-run finding names the fix " +
      "(record a Run-the-app line). This is reported, not silently skipped.",
  };
}

// Mode + the run label (the artifact-dir leaf). full when any criteria are present; else boot-only.
const criteria = runConfig.criteria;
const mode = criteria.length > 0 ? "full" : "boot-only";
const { drivable, manual } = criterionPlan(criteria);
// Normalized ONCE here, through the one source -- every consumer below (the driver prompt's save
// dir, the returned artifacts.dir) reuses this value, never re-deriving it (0041 S10a, D3).
const artifactDir = artifactBase(runConfig.artifactDir);
// The script has no clock: a runLabel from args wins, else the boot agent stamps `qa-<timestamp>`.
// A null here means "ask the boot agent to generate one".
let runLabel = runConfig.runLabel && runConfig.runLabel.length > 0 ? runConfig.runLabel : null;
const manualCriteria = manual.map((c) => ({
  id: c.id,
  feature: c.feature,
  verdict: "not-checkable",
  reason: MANUAL_NOT_CHECKABLE_REASON,
}));

const plan = readinessPlan(runConfig);
log(
  `qa ${mode}: run=\`${runConfig.runCommand}\` url=${runConfig.appUrl} ` +
    `readiness=${plan.timeoutSec}s (${plan.maxAttempts} probes @ ${plan.intervalSec}s)` +
    (mode === "full"
      ? `; criteria: ${drivable.length} drivable + ${manual.length} manual (listed, never driven).`
      : "."),
);

// --- Boot + teardown, with teardown ALWAYS in the finally (success, boot failure, mid-run error
// alike -- the port is freed however the run exits). The try body holds the flow-driving stage
// (criteria -> drivers -> findings -> cross-model verify) when criteria are present. ---
let bootReport = null;
let findings = [];
let verdicts = [];
let refutedCount = 0;
let refutedRunningAs = [];
let ready = false;
let allScreenshots = [];

phase("Boot");
try {
  // A skip/terminal error returns null, and a spawn can THROW. Both are the same honest failure:
  // null/malformed/thrown classifies failed and becomes the could-not-run finding, never a crash.
  try {
    bootReport = await agent(bootPrompt(runConfig, plan, runLabel), {
      agentType: "general-purpose",
      schema: BOOT_SCHEMA,
      label: "qa:boot",
      phase: "Boot",
    });
  } catch (bootErr) {
    log(`qa boot agent threw: ${bootErr && bootErr.message ? bootErr.message : bootErr}`);
    bootReport = bootReportFromError(bootErr);
  }

  // The boot agent may have stamped the runLabel (the script has no clock) -- adopt it.
  if (runLabel == null && bootReport && typeof bootReport.runLabel === "string" && bootReport.runLabel.length > 0) {
    runLabel = bootReport.runLabel;
  }
  if (runLabel == null) {
    // Last-ditch deterministic label so screenshots still have a home if the agent omitted one.
    runLabel = "qa-run";
  }
  // Normalize ONCE here, at the same boundary the artifact dir is normalized at: joining it raw
  // into artifacts.dir below would cite a directory the driver never wrote to. sanitizeForPath is
  // idempotent, so driverPrompt's second application is a no-op (0041 S10a, D3).
  runLabel = sanitizeForPath(runLabel) || "qa-run";

  const outcome = bootOutcome(bootReport);
  ready = outcome === "ready";
  if (!ready) {
    // The explicit, evidence-carrying could-not-run finding -- never a silent skip, never a pass.
    findings.push(couldNotRunFinding(runConfig, bootReport));
    log(`qa boot FAILED -- ${COULD_NOT_RUN_CLASS} finding emitted with log-tail evidence.`);
  } else {
    log(`qa boot READY after ${bootReport && bootReport.attempts != null ? bootReport.attempts : "?"} probe(s).`);
  }

  // -- Flow-driving (full mode, booted app only): one driver agent per drivable criterion, run
  // SEQUENTIALLY (criteria mutate app state -- parallel drivers would interfere). DRIVE is the
  // QA-judgment seam (runs-correct vs reads-correct, the negative-path push, intent-vs-behavior), so
  // it spawns the `runtime-qa` specialist, NOT the general-purpose used for the mechanical
  // boot/teardown lifecycle. Each report folds to pass|fail|not-checkable; every fail becomes a
  // lens-shaped UX finding. We do NOT drive against a dead app -- every e2e verdict would be a false
  // fail, and the could-not-run finding already stands. --
  if (mode === "full" && ready) {
    phase("Drive");
    for (const criterion of drivable) {
      let report = null;
      try {
        report = await agentWithNamespaceFallback(driverPrompt(runConfig, criterion, runLabel, artifactDir), {
          agentType: nsAgent("runtime-qa"),
          schema: DRIVER_SCHEMA,
          label: `qa:drive:${criterion.id}`,
          phase: "Drive",
        });
      } catch (driveErr) {
        log(`qa driver ${criterion.id} threw: ${driveErr && driveErr.message ? driveErr.message : driveErr}`);
        report = null;
      }
      const { verdict, reason } = verdictFor(report, criterion.states);
      if (report && Array.isArray(report.screenshots)) {
        for (const s of report.screenshots) {
          if (!allScreenshots.includes(s)) allScreenshots.push(s);
        }
      }
      // The route the criterion landed on -- appUrl is the honest default anchor (drivers observe
      // a surface, not a file:line). A criterion may report a more specific route.
      const route = report && typeof report.route === "string" && report.route.length > 0 ? report.route : runConfig.appUrl;
      verdicts.push({ id: criterion.id, feature: criterion.feature, check: criterion.check, verdict, reason, route, report });
      log(`qa criterion ${criterion.id} -> ${verdict}${reason ? ` (${reason})` : ""}.`);
    }

    // Shape the fails into lens-shaped findings, dedup by class+route, then add them alongside any
    // could-not-run finding (none here -- boot was ready).
    const driverFindings = dedupFindings(findingsFrom(verdicts));
    findings.push(...driverFindings);

    // VERIFY: exactly one finding-verifier per surfaced finding (parallel fan-out). The
    // could-not-run finding (none here) would be exempt; driver findings are all re-checked.
    if (findings.length > 0) {
      phase("Verify");
      const toVerify = findings;
      const verifyTasks = toVerify.map((finding) => () =>
        finding.issueClass === COULD_NOT_RUN_CLASS ? Promise.resolve(null) : spawnVerifier(finding),
      );
      const verifyResults = await parallel(verifyTasks);
      const applied = applyVerifierVerdicts(toVerify, verifyResults);
      findings = applied.kept;
      refutedCount = applied.refutedCount;
      refutedRunningAs = applied.refutedRunningAs;
    }
  } else if (mode === "full" && !ready) {
    // Full run requested but the app never booted: the could-not-run finding stands and NO
    // criterion was driven (a dead app manufactures false fails). Every drivable criterion is
    // reported not-checkable with the boot-failure reason -- honest, never a pass.
    for (const criterion of drivable) {
      verdicts.push({
        id: criterion.id,
        feature: criterion.feature,
        check: criterion.check,
        verdict: "not-checkable",
        reason: "the app could not be booted -- see the qa-could-not-run-app finding",
        route: runConfig.appUrl,
        report: null,
      });
    }
  }
} finally {
  phase("Teardown");
  // A throwing teardown inside a finally would REPLACE the boot exception (JS try/finally) and the
  // operator would debug the wrong failure -- so teardown failures are caught and logged loudly,
  // never allowed to mask the original root cause.
  try {
    const td = teardownPlan(runConfig, bootReport);
    const teardownReport = await agent(teardownPrompt(runConfig, td), {
      agentType: "general-purpose",
      schema: TEARDOWN_SCHEMA,
      label: "qa:teardown",
      phase: "Teardown",
    });
    if (!teardownReport || teardownReport.toreDown !== true || teardownReport.portFree === false) {
      log(
        `qa teardown DID NOT cleanly free the port (${teardownReport && teardownReport.note ? teardownReport.note : "no report"}) -- ` +
          "reported, not hidden.",
      );
    }
  } catch (tdErr) {
    log(
      `qa teardown agent threw (${tdErr && tdErr.message ? tdErr.message : tdErr}) -- reported, ` +
        "not hidden; the port may need a manual check. The original run outcome is preserved.",
    );
  }
}

// The run's cross-model claim -- `confirmed` ONLY when EVERY re-checkable finding's verifier returned
// a confirming different-family self-report; otherwise the THREE-state disclosure tag for WHY:
// UNRESOLVED_FAMILY_TAG for a present-but-unresolved family (reported, never asserted same-model
// fact), SAME_MODEL_TAG for a resolved-same or missing report. The could-not-run finding is exempt.
const builderFamily = typeof input.builderFamily === "string" ? input.builderFamily : "";
const reCheckable = findings.filter((f) => f.issueClass !== COULD_NOT_RUN_CLASS);
// EVERY verifier that RAN votes -- the survivors' reports PLUS `refutedRunningAs`. A refuting
// verifier decided what reached the backlog, so excluding it would let a same-model reviewer do the
// deciding under a cross-model banner.
const judgeReports = reCheckable.map((f) => f.verifierRunningAs).concat(refutedRunningAs);
const allConfirmingDifferentFamily =
  judgeReports.length > 0 && judgeReports.every((r) => r != null && sameModelTag(builderFamily, r) === null);
// Observability: a present verifier self-report that does not resolve to a KNOWN family is LOGGED,
// never silently degraded, and taints the disclosure to UNRESOLVED, not asserted same-model.
let sawUnresolved = false;
for (const reported of judgeReports) {
  if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
    sawUnresolved = true;
    log(
      `qa: a finding-verifier self-reported an UNRECOGNIZED model family ` +
        `(${JSON.stringify(reported)}) -- reported as unresolved, no cross-model claim made.`,
    );
  }
}
const crossModel = allConfirmingDifferentFamily
  ? "confirmed"
  : sawUnresolved
    ? UNRESOLVED_FAMILY_TAG
    : SAME_MODEL_TAG;

// The three states are resolved directly above; hardcoding one into the sentence a human actually
// reads is the exact over-claim this register exists to prevent.
const recheckLabel =
  crossModel === "confirmed"
    ? "the cross-model re-check"
    : "the re-check (NOT cross-model on this run -- see the disclosure below)";

const passCount = verdicts.filter((v) => v.verdict === "pass").length;
const failCount = verdicts.filter((v) => v.verdict === "fail").length;
const notCheckableCount = verdicts.filter((v) => v.verdict === "not-checkable").length;

const fullSummary =
  `full run: ${verdicts.length} criteria driven (${passCount} pass - ${failCount} fail - ` +
  `${notCheckableCount} not-checkable) + ${manualCriteria.length} manual (listed for a human, never driven). ` +
  `${findings.length} finding(s) surfaced (${refutedCount} refuted and dropped by ${recheckLabel}). ` +
  `The drivers ATTEMPTED each flow (model-upheld judgment of your plain-English steps) -- measured facts are the ` +
  `observed HTTP/element evidence; asserted are the drivers' interpretive calls. This reduces the risk the product ` +
  `diverged from the criteria; it does not prove the app correct.`;

const bootOnlySummary = ready
  ? "boot-only run (no criteria provided): the app booted, answered the readiness probe, and was torn down. " +
    "No flow-driving (no acceptance criteria)."
  : "boot-only run (no criteria provided): the app could NOT be run -- exactly one could-not-run finding was " +
    "emitted with boot-log evidence, and teardown still ran. This is reported, not a pass and not a silent skip.";

return {
  // full "ran" = ready AND criteria actually exercised; boot-only "ran" = the app booted. A
  // manual-only run drives nothing -> ran false, honestly.
  ran: mode === "full" ? ready && verdicts.length > 0 : ready,
  mode,
  boot: {
    started: bootReport && bootReport.started === true,
    ready,
    pid: bootReport && bootReport.pid != null ? bootReport.pid : null,
    logPath: bootReport && bootReport.logPath != null ? bootReport.logPath : null,
    attempts: bootReport && bootReport.attempts != null ? bootReport.attempts : 0,
  },
  verdicts,
  findings,
  refutedCount,
  manualCriteria,
  // artifactDir is already artifactBase-normalized at the boundary -- no second default or trim.
  artifacts: { dir: mode === "full" ? `${artifactDir}/${runLabel}` : null, screenshots: allScreenshots },
  crossModel: mode === "full" ? crossModel : SAME_MODEL_TAG,
  summary: mode === "full" ? fullSummary : bootOnlySummary,
};
