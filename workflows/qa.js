// workflows/qa.js — runtime verification (QA) as an executable Workflow script.
//
// Slice 4a scope: the BOOT VERTICAL only — start the app with the recorded run command,
// probe a readiness URL within a bounded wait, ALWAYS tear down (the port is verifiably
// freed), and on a boot failure surface the explicit, evidence-carrying "could not run the
// app" finding (issueClass `qa-could-not-run-app`) — never a silent skip, never a fake pass.
// Flow-driving (Playwright criteria → lens-shaped UX findings → cross-model verify) is Slice
// 4b; the control flow leaves a clear seam for it (the boot/teardown wrapper, the criteria
// args fields are reserved-and-validated-absent, the output carries `mode: 'boot-only'`).
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped plugin
// install dir (`${CLAUDE_PLUGIN_ROOT}/workflows/qa.js`); this repo dogfoods it via the
// repo-local `./workflows/qa.js` (the working tree IS the plugin source). Never copied into an
// adopter repo (no managed-stamp/refresh surface) — see docs/DECISIONS.md -> Harness v2.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps times AFTER the run).
// Only the tool primitives `agent()`/`parallel()`/`phase()`/`log()`/`args`. The script itself
// has NO Bash and NO clock — all file/process/clock work happens inside the agents it spawns
// (the boot agent starts the app and probes it; the teardown agent stops it). Call count is
// structurally bounded (boot + teardown = 2 in boot-only mode) — no loops. Pure decision logic
// lives in the marked `// --- helpers ---` block and is unit-tested by tests/workflows/qa.test.mjs
// (extract-and-eval), so the prose->script move tests the judgment, not just inspects it.

export const meta = {
  name: "qa",
  description:
    "Runtime verification (QA) as a Workflow script. Boots the recorded run command detached, probes the readiness URL on a bounded schedule (readinessPlan — never unbounded), and ALWAYS tears down via teardownPlan (explicit override > docker compose down > kill the recorded PID) in a finally so the port is freed on success, boot failure, and mid-run error alike. A boot that never answers within the bound (or a missing/malformed report) classifies `failed` (fail loud — never default to success) and produces exactly one lens-shaped `qa-could-not-run-app` finding with the command + probe attempts + boot-log tail as evidence, tagged (observed this run — boot log attached). When acceptance criteria are passed (full mode): one driver agent per drivable criterion runs SEQUENTIALLY in a real browser (Playwright via ToolSearch) or over HTTP (check:api), performs the flow, checks the expects + the named empty/loading/error states, and screenshots under the artifact dir; each criterion folds to a pass|fail|not-checkable verdict (manual criteria are NEVER driven — listed for a human). Every fail becomes a lens-shaped UX finding (ux-missing-empty-state / ux-missing-loading-state / ux-missing-error-state / ux-broken-flow) and EVERY finding gets exactly one cross-model finding-verifier (model: MODELS.judge — Refuted dropped+counted, Verified/Unconfirmed/deferred tagged; the could-not-run finding stays exempt). The run claims cross-model only on confirming self-reports.",
  // Bounded call count: boot + teardown + one driver per drivable criterion + one verifier per
  // surfaced finding — no loops. The static cap below is a backstop; the structure already bounds
  // it (the per-run criteria/findings counts are the true bound, computed in code).
  budget: { agents: 40 },
};

// --- helpers ---
// Pure functions only — they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The judge model family, defined ONCE (single source of truth). Copied VERBATIM from
// verify.js (Slice 2) / audit.js (Slice 3a) — the shared cross-model contract, pinned
// byte-identical across the workflow scripts by tests/workflows/cross-script.test.mjs. Slice 4b
// uses MODELS.judge on every finding-verifier; in the boot-only vertical it stays defined here
// so the copied block is whole (no partial-copy drift).
const MODELS = { judge: "opus" };

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

// The readiness-probe defaults and the hard cap. The wait is ALWAYS bounded: the timeout is
// clamped to [interval, READINESS_TIMEOUT_CAP] and attempts derive from it — never zero, never
// unbounded (the qa.js flakiness mitigation — see plan Risks).
const READINESS_TIMEOUT_DEFAULT_SEC = 60;
const READINESS_TIMEOUT_CAP_SEC = 300;
const READINESS_PROBE_INTERVAL_SEC = 2;

// The issueClass of the explicit "could not run the app" finding — a boot FACT of this run, not
// a claim about the code. Tagged (observed this run — boot log attached), NEVER
// (checked against the code). Defined once so the class string can't drift.
const COULD_NOT_RUN_CLASS = "qa-could-not-run-app";

// The verbatim observed-this-run verification tag the could-not-run finding carries — a boot
// fact, distinct from the audit's code-checked tags. Defined once (honesty trust surface).
const OBSERVED_THIS_RUN_TAG = "(observed this run — boot log attached)";

// The verbatim no-run-command reason — the could-not-run finding's reason when no runnable
// command was recorded/passed. Names the durable home (CLAUDE.md's detected-tooling block) so
// the fix is actionable. Defined once.
const NO_RUN_COMMAND_REASON =
  'no run command recorded — add a "Run the app:" line to CLAUDE.md\'s detected-tooling block (or pass runCommand)';

// ── Slice 4b — flow-driving constants ──

// The acceptance-criterion `check` enum (FROZEN — Slice 6's PRODUCT_SPEC_TEMPLATE carries it
// verbatim). `e2e` = drive through a real browser (Playwright); `api` = HTTP-only (the driver's
// Bash/curl); `manual` = NEVER executed — listed for a human, verdict not-checkable (manual by
// contract). Defined once; validateCriteria rejects anything else, naming the offending ids.
const CHECK_KINDS = ["e2e", "api", "manual"];

// The product-ux state-bar checks a criterion may request (per docs/standards/product-ux.md →
// "Loading / empty / error states"). Subset of these three; an empty array = no state checks.
// FROZEN with the schema. validateCriteria rejects any other value.
const STATE_KINDS = ["empty", "loading", "error"];

// The runtime-finding issue classes, one per failed state-check kind + the broken-flow class.
// Lens-shaped findings join the same dedup → finding-verifier path as code-audit findings; these
// fixed class strings let dedupFindings key on (issueClass + route) and let the seeded-defect
// acceptance assert on exact classes. Defined once so the strings can't drift.
const UX_ISSUE_CLASS = {
  empty: "ux-missing-empty-state",
  loading: "ux-missing-loading-state",
  error: "ux-missing-error-state",
  flow: "ux-broken-flow",
};

// The verbatim verdict-for-a-manual-criterion text — a manual criterion is NEVER driven; it is
// listed for a human with this exact reason. Defined once (honesty trust surface — a manual
// criterion must never read as silently dropped or as a pass).
const MANUAL_NOT_CHECKABLE_REASON = "manual by contract";

// The verbatim not-checkable reason when the session has no Playwright browser tooling — every
// e2e verdict degrades to this, never a silent pass. Defined once.
const BROWSER_UNAVAILABLE_REASON = "browser tooling unavailable in this session";

// Normalize the args boundary — copied verbatim from verify.js. A scriptPath invocation delivers
// `args` as a JSON STRING (observed runtime behavior, 2026-06-11); an inline script may receive
// the object itself. Accept both; an unparseable string fails loud — never a silent empty-args run.
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

// Validate + normalize the run args at the boundary (FROZEN contract — Slice 5b builds against
// it). Returns `{ runConfig, errors }`:
//   - `errors` is every shape error (fail loud — the caller maps a missing/empty runCommand or
//     appUrl to the could-not-run FINDING, not a silent throw: a QA run that can't run reports it).
//   - `runConfig` is the normalized config (defaults applied, readinessTimeoutSec clamped to the
//     cap) — usable only when errors is empty.
// The 4b-reserved fields (criteria/artifactDir/runLabel) are accepted and threaded but unused in
// boot-only mode (absent/empty criteria ⇒ a boot-only run — the seam for 4b).
function parseRunArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return { runConfig: null, errors: ["args must be an object"] };
  }
  const hasRunCommand = typeof args.runCommand === "string" && args.runCommand.trim().length > 0;
  const hasAppUrl = typeof args.appUrl === "string" && args.appUrl.trim().length > 0;
  if (!hasRunCommand) {
    errors.push("runCommand is required (non-empty string — the recorded command that starts the app)");
  }
  if (!hasAppUrl) {
    errors.push("appUrl is required (non-empty string — the readiness URL to probe)");
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
      // Clamp to the hard cap — never an unbounded wait (the bound is the resilience contract).
      readinessTimeoutSec = Math.min(args.readinessTimeoutSec, READINESS_TIMEOUT_CAP_SEC);
    }
  }
  if (args.criteria !== undefined && !Array.isArray(args.criteria)) {
    errors.push("criteria, when provided, must be an array (Slice 4b — absent/empty ⇒ boot-only)");
  }
  const runConfig = {
    runCommand: hasRunCommand ? args.runCommand.trim() : "",
    appUrl: hasAppUrl ? args.appUrl.trim() : "",
    teardownCommand:
      typeof args.teardownCommand === "string" && args.teardownCommand.trim().length > 0
        ? args.teardownCommand.trim()
        : null,
    readinessTimeoutSec,
    // 4b seam: absent/empty criteria ⇒ boot-only. Threaded but unused in this slice.
    criteria: Array.isArray(args.criteria) ? args.criteria : [],
    artifactDir: typeof args.artifactDir === "string" ? args.artifactDir : null,
    runLabel: typeof args.runLabel === "string" ? args.runLabel : null,
  };
  return { runConfig, errors };
}

// Is this run command a docker compose invocation? `docker compose …` (v2) or `docker-compose …`
// (v1) at the start of the command, case-insensitive, whitespace-tolerant. Drives the default
// teardown (`docker compose down`) and the detached-start convention (compose uses `-d`).
function isComposeCommand(runCommand) {
  if (typeof runCommand !== "string") {
    return false;
  }
  return /^\s*docker(\s+compose|-compose)\b/i.test(runCommand);
}

// The bounded readiness probe plan (PURE — the boot agent executes it). Derives the probe
// schedule from the validated timeout: probe every interval up to the bound, ALWAYS at least one
// attempt, never unbounded. Returns `{ intervalSec, timeoutSec, maxAttempts }`.
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

// Classify the boot agent's structured report into `ready` / `failed`. FAIL LOUD: a missing or
// malformed report (not an object, or `ready` not strictly true) classifies `failed` — the boot
// outcome NEVER defaults to success on a degraded report.
function bootOutcome(report) {
  if (!report || typeof report !== "object") {
    return "failed";
  }
  return report.ready === true ? "ready" : "failed";
}

// The teardown instruction (PURE — the teardown agent executes it). Runs on success, boot
// failure, and mid-run error alike (the control flow wraps it in a finally). Precedence:
//   1. an explicit teardownCommand wins (the user's recorded stop command);
//   2. else `docker compose down` when the run command is a compose invocation;
//   3. else kill the PID the boot agent recorded (a backgrounded dev-server).
// A failed boot that still recorded a PID yields a kill (a half-started process must be reaped —
// never leak a port). Returns `{ method, command? , pid? }`.
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
  // No override, not compose, no recorded PID — nothing to stop (the app never started a
  // process we can name). Honest: the teardown agent reports it as a no-op, never a silent skip.
  return { method: "none" };
}

// Build the one lens-shaped "could not run the app" finding (PURE). Either a no-run-command
// boundary failure (no boot report) or a boot that never answered. issueClass is the fixed
// COULD_NOT_RUN_CLASS; confidence is 'deterministic' (an observed boot fact of THIS run);
// evidence carries the command + probe attempts + the boot-log tail; the verification tag is the
// observed-this-run tag (NOT a code-checked claim). A QA run that didn't run reports that it
// didn't run.
function couldNotRunFinding(runConfig, report) {
  const command = runConfig && runConfig.runCommand ? runConfig.runCommand : null;
  const appUrl = runConfig && runConfig.appUrl ? runConfig.appUrl : null;
  const attempts = report && report.attempts != null ? report.attempts : 0;
  const logTail = report && typeof report.logTail === "string" ? report.logTail : "";
  const reason = command ? null : NO_RUN_COMMAND_REASON;
  const plainEnglish = command
    ? `The app could not be started or never became ready: the recorded command ran but ${appUrl || "the readiness URL"} did not answer within the bounded wait (${attempts} probe attempt(s)). The QA review could not run against a live app — this is reported, not skipped.`
    : `${NO_RUN_COMMAND_REASON}. The QA review could not run — this is reported, not skipped.`;
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

// The boot agent's report: did it start, did it become ready, the recorded PID + log path, the
// log tail (last <=50 lines, on failure), and the probe-attempt count. `ready` and `started` are
// the load-bearing booleans bootOutcome reads.
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
    // The script has no clock — the boot agent stamps the run label (artifact-dir leaf) when the
    // skill didn't pass one. Threaded back to the flow-driving stage.
    runLabel: { type: ["string", "null"] },
  },
};

// The teardown agent's report: did it stop the app, and is the port verifiably free afterwards
// (the teardown contract — a port still bound is a leaked process, reported loudly).
const TEARDOWN_SCHEMA = {
  type: "object",
  required: ["toreDown"],
  properties: {
    toreDown: { type: "boolean" },
    portFree: { type: ["boolean", "null"] },
    note: { type: "string" },
  },
};

// The driver agent's per-criterion report (Slice 4b). One driver per drivable criterion: it
// performs the flow, evaluates each expect, runs the requested state checks, and records the
// screenshots it saved. `notCheckable` is the honest escape hatch (browser tooling unavailable /
// a step that cannot be performed at all) — verdictFor folds it to not-checkable, never a pass.
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

// The finding-verifier's verdict schema (Slice 4b — runtime findings re-checked cross-model). The
// self-reported model family is REQUIRED (the run claims cross-model only on a confirming report).
// Same shape audit.js's VERIFIER_SCHEMA uses.
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

// ── Slice 4b — flow-driving helpers (pure; the driver/verifier agents execute the I/O) ──

// Validate the acceptance criteria at the boundary against the FROZEN schema (field names are
// frozen: id/feature/flow/expect/states/check). FAIL LOUD: returns every error naming the
// offending id (or index when the id itself is missing/duplicate) — invalid input is NEVER
// silently filtered (a dropped criterion would be a silently-unchecked promise). An empty/absent
// list is valid (⇒ a boot-only run — the seam stays open). Returns string[] (empty = valid).
function validateCriteria(criteria) {
  const errors = [];
  if (criteria === undefined || criteria === null) {
    return errors; // absent ⇒ boot-only (valid)
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
      errors.push(`${at}: duplicate id — every criterion id must be unique`);
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
      errors.push(`${at}: states is required (array — may be empty)`);
    } else if (!c.states.every((s) => STATE_KINDS.includes(s))) {
      errors.push(`${at}: states entries must each be one of ${STATE_KINDS.join("|")}`);
    }
    if (typeof c.check !== "string" || !CHECK_KINDS.includes(c.check)) {
      errors.push(`${at}: check must be one of ${CHECK_KINDS.join("|")} (got ${JSON.stringify(c.check)})`);
    }
  });
  return errors;
}

// Partition the validated criteria into the drivable set (e2e|api — one driver each, run
// SEQUENTIALLY: criteria mutate app state, so parallel drivers would interfere) and the manual
// set (NEVER driven — listed for a human). PURE. Returns `{ drivable, manual }`.
function criterionPlan(criteria) {
  const list = Array.isArray(criteria) ? criteria : [];
  return {
    drivable: list.filter((c) => c.check === "e2e" || c.check === "api"),
    manual: list.filter((c) => c.check === "manual"),
  };
}

// Fold one driver agent's structured report into a verdict: `pass` / `fail` / `not-checkable`
// (+ reason). Precedence (FAIL LOUD — never default to pass):
//   - missing/malformed report ⇒ not-checkable (loudly — the driver did not report)
//   - the driver flagged the run unexecutable (e.g. browser tooling unavailable) ⇒ not-checkable + reason
//   - ANY failed step, failed expect, or state verdict 'fail' ⇒ fail
//   - all steps ok ∧ all expects ok ∧ no state-fail ⇒ pass
//   - otherwise (some checks were themselves not-checkable, none failed) ⇒ not-checkable
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
  // Only the criterion's REQUESTED states bear on the verdict — a driver may report extra
  // state observations (they are informational evidence), but an unrequested state check can
  // never fail a criterion that did not ask for it (the 2026-06-12 dogfood: AC-3 with
  // states:[] failed on checks it never requested).
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
  // No hard failure, but something could not be checked (a state was too-fast-to-observe / a
  // surface was unreachable). Honest: not-checkable, never a pass and never a fail.
  return {
    verdict: "not-checkable",
    reason: "some checks could not be performed (see the per-check evidence)",
  };
}

// Map a failed criterion's driver report to lens-shaped runtime findings (PURE). One finding per
// failure kind: a failed FLOW (step/expect failure) ⇒ ux-broken-flow; a failed STATE check ⇒ the
// state's ux-missing-*-state class. `confidence: 'deterministic'` for an observed protocol fact
// (a 404/500, an element provably absent); `'judgment'` for an interpretive call. Runtime findings
// cite the route + evidence; `file:line` is intentionally ABSENT (the runtime observes the
// product, not the source — the verifier locates the code itself). Only `fail` verdicts yield
// findings (pass / not-checkable do not).
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

// Merge duplicate runtime findings — keyed on issueClass + route (the audit's same-class dedup
// rule, route-scoped because the runtime observes a product surface, not a file:line). Same class
// at the same route merges (union of criterionIds + screenshots, first concrete plainEnglish,
// weakest confidence wins). Distinct classes — or the same class at a different route — stay
// separate. PURE; preserves first-seen order.
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

// Build the screenshot path under the artifact dir (PURE). Convention:
// `<artifactDir>/<runLabel>/<criterionId>-<slug>.png`. ids/slugs are sanitized (lowercase,
// spaces/slashes/other non-[a-z0-9-_] → '-', collapsed) so a free-text id can never escape the
// artifact dir or break the path. The script can't touch the filesystem — this only NAMES the
// path the driver agent saves to.
function sanitizeForPath(s) {
  return String(s == null ? "" : s)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    // Collapse any run of 2+ dots to a single one — a surviving `..` would be a parent-dir escape.
    .replace(/\.{2,}/g, ".")
    .replace(/^[.-]+|[.-]+$/g, "")
    .replace(/-{2,}/g, "-");
}

function screenshotPath(artifactDir, runLabel, criterionId, slug) {
  const dir = artifactDir && String(artifactDir).length > 0 ? String(artifactDir).replace(/\/+$/, "") : ".qa-artifacts";
  const label = sanitizeForPath(runLabel) || "run";
  const id = sanitizeForPath(criterionId) || "criterion";
  const tail = sanitizeForPath(slug) || "shot";
  return `${dir}/${label}/${id}-${tail}.png`;
}

// Apply the finding-verifier verdicts to the surfaced runtime findings (PURE). Mirrors audit.js's
// applyVerdicts mapping, runtime-shaped:
//   Verified   -> kept, verificationTag (checked against the code) + evidence
//   Unconfirmed-> kept, verificationTag (could not confirm independently — model's assertion)
//   Refuted    -> dropped + counted (a false positive caught before the backlog)
//   no verdict -> kept, verificationTag (⚠ not yet verified — re-run to confirm)  [deferred]
// The COULD-NOT-RUN finding is EXEMPT: it carries its own observed-this-run boot-fact tag and is
// passed through untouched (a boot fact, not a code claim). `results` is aligned to `findings`
// (results[i] verifies findings[i]); the could-not-run finding is matched by issueClass, not index.
function applyVerifierVerdicts(findings, results) {
  const kept = [];
  let refutedCount = 0;
  (Array.isArray(findings) ? findings : []).forEach((finding, i) => {
    if (finding && finding.issueClass === COULD_NOT_RUN_CLASS) {
      kept.push({ ...finding }); // exempt — keeps its observed-this-run tag untouched
      return;
    }
    const result = Array.isArray(results) ? results[i] : undefined;
    const verdict = result && result.verdict ? result.verdict : null;
    if (verdict === "Refuted") {
      refutedCount += 1;
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
      verificationTag = "(could not confirm independently — model's assertion)";
      evidence = result && result.evidence != null ? result.evidence : "";
    } else {
      verificationState = "deferred";
      verificationTag = "(⚠ not yet verified — re-run to confirm)";
    }
    kept.push({
      ...finding,
      verificationState,
      verificationTag,
      verifierEvidence: evidence,
      verifierRunningAs: result && result.runningAs != null ? result.runningAs : null,
    });
  });
  return { kept, refutedCount };
}

// The error-partition predicate: which boundary errors become the honest could-not-run
// FINDING (missing run inputs) vs which throw (caller-contract bugs). Lives in the helpers
// block so the producer (parseRunArgs message prefixes) / consumer (the partition) string
// contract is pinned by tests — a reworded message must turn a test red, never silently
// reroute a missing runCommand into a throw.
function isRunInputError(msg) {
  return (
    typeof msg === "string" &&
    (msg.startsWith("runCommand is required") || msg.startsWith("appUrl is required"))
  );
}

// The ONE source of the artifact-dir shape: default + trailing-slash trim. screenshotPath,
// driverPrompt, the top-level default, and the returned artifacts.dir all derive from this —
// the save-path and the report-path cannot diverge.
function artifactBase(dir) {
  return (dir && String(dir).length ? String(dir) : ".qa-artifacts").replace(/\/+$/, "");
}

// Map a THROWN boot-agent error to the same failed-boot report shape a returned failure uses —
// one downstream path (bootOutcome -> couldNotRunFinding), pure so the mapping is unit-pinned.
function bootReportFromError(err) {
  const msg = err && err.message ? err.message : String(err);
  return {
    started: false,
    ready: false,
    attempts: 0,
    logTail: `boot agent error: ${msg}`,
  };
}
// --- end helpers ---

// Build the boot agent's prompt from the validated run config + the bounded readiness plan. The
// agent (not the script) has Bash: it starts the command detached and probes the URL. When
// `runLabel` is null the agent ALSO stamps one (`qa-<timestamp>`) — the script has no clock, so
// the artifact-dir leaf is generated here and threaded back to the drivers.
function bootPrompt(runConfig, plan, runLabel) {
  const compose = isComposeCommand(runConfig.runCommand);
  const startHint = compose
    ? "This is a docker compose command — it detaches with `-d` (start it so it returns control)."
    : "This is a dev-server command — start it BACKGROUNDED, redirect its stdout+stderr to a log file, and record its PID (return the PID and the log path).";
  const labelHint =
    runLabel == null
      ? "Also generate a run label `qa-<timestamp>` (e.g. `qa-20260612-143000`) and return it as runLabel — " +
        "it names the screenshot folder for the flow-driving stage."
      : `The run label is already \`${runLabel}\` — echo it back as runLabel.`;
  return (
    `Runtime QA — BOOT stage. Start the app and confirm it is ready.\n\n` +
    `Run command: \`${runConfig.runCommand}\`\n` +
    `Readiness URL: ${runConfig.appUrl}\n` +
    `${startHint}\n\n` +
    `Then probe the readiness URL with curl every ~${plan.intervalSec}s, up to ${plan.maxAttempts} attempts ` +
    `(the bounded wait of ${plan.timeoutSec}s — NEVER wait unbounded). Ready = an HTTP response (any 2xx/3xx/4xx ` +
    `means the server answered; a connection refusal/timeout means not-yet).\n\n` +
    `${labelHint}\n\n` +
    `Return the structured report: started, ready, pid (if a dev-server), logPath, logTail (the LAST <=50 lines ` +
    `of the boot log — REQUIRED on failure so the could-not-run finding carries evidence), attempts (how many ` +
    `probes you made), and runLabel. If the command itself fails to launch, set started=false and put the launch ` +
    `error in logTail. Do NOT tear anything down — the script's teardown stage owns that.`
  );
}

// Build the teardown agent's prompt from the (pure) teardown plan. The agent has Bash; it
// executes the planned method and verifies the port is free.
function teardownPrompt(runConfig, plan) {
  let instruction;
  if (plan.method === "command") {
    instruction = `Stop the app by running: \`${plan.command}\``;
  } else if (plan.method === "kill") {
    instruction = `Stop the app by killing PID ${plan.pid} (and any child processes it spawned).`;
  } else {
    instruction =
      "No explicit stop command, not a compose run, and no PID was recorded — there may be nothing to stop. " +
      "Check whether anything is still bound to the app's port and stop it if so; otherwise report a no-op.";
  }
  return (
    `Runtime QA — TEARDOWN stage. Always runs (success, boot failure, or mid-run error).\n\n` +
    `${instruction}\n` +
    `Readiness URL: ${runConfig.appUrl}\n\n` +
    `After stopping, VERIFY the port is free (the app's URL no longer answers / nothing is bound to its port). ` +
    `Return: toreDown (did you stop it), portFree (is the port verifiably free afterwards — null if you could not check), ` +
    `and a short note. A port still bound is a leaked process — report it loudly, never a silent success.`
  );
}

// Build the driver agent's prompt for one criterion (Slice 4b). The agent reaches the session's
// Playwright tools via ToolSearch (workflow agents load deferred MCP tools that way), drives the
// flow, evaluates the expects, runs the requested state checks, and saves screenshots under the
// artifact dir (the script itself has no filesystem — the agent does the saving). The state-check
// semantics are stated inline so the agent applies the product-ux bar, not its own guess.
function driverPrompt(runConfig, criterion, runLabel, artifactDir) {
  const isApi = criterion.check === "api";
  const shotDir = `${(artifactDir || ".qa-artifacts").replace(/\/+$/, "")}/${sanitizeForPath(runLabel) || "run"}`;
  const toolingLine = isApi
    ? "This is an `api` criterion — drive it over HTTP with curl/fetch via Bash (no browser). " +
      "Each flow step is a described HTTP call; each expect is a response observable (status, body text, header)."
    : "This is an `e2e` criterion — drive it in a REAL browser. FIRST load the Playwright browser " +
      "tools via ToolSearch (query 'playwright browser' — e.g. select the `mcp__playwright__browser_*` " +
      "set), THEN navigate, click, type, and snapshot. If the Playwright tools are unavailable in this " +
      "session, set notCheckable=true and notCheckableReason='" + BROWSER_UNAVAILABLE_REASON + "' — " +
      "NEVER fake a pass.";
  return (

    `STATES SCOPE: check ONLY the states listed for THIS criterion (${(criterion.states || []).length ? criterion.states.join(", ") : "none — perform NO state checks"}). Any other state observation you happen to make is informational evidence only — report it in a note, never as a states[] entry.` +
        `Runtime QA — FLOW-DRIVING for one acceptance criterion (id ${criterion.id}, feature "${criterion.feature}").\n\n` +
    `App URL: ${runConfig.appUrl}\n` +
    `${toolingLine}\n\n` +
    `Flow (perform each ordered step; a step you cannot perform fails the criterion at that step, with a note):\n` +
    criterion.flow.map((s, i) => `  ${i + 1}. ${s}`).join("\n") +
    `\n\nExpect (evaluate each AFTER the flow — ALL must hold for a pass; record evidence: the observed text, ` +
    `element presence/absence, URL, count, or HTTP status):\n` +
    criterion.expect.map((e) => `  - ${e}`).join("\n") +
    `\n\nState checks to run on the surface this criterion lands on (${criterion.states.length ? criterion.states.join(", ") : "none"}):\n` +
    `  - empty: reach the zero-data condition (this run may boot FIXTURE_SEED=0). pass = a designed zero-state ` +
    `(a message/CTA explaining what goes here); fail = a blank void / raw placeholder; zero-data unreachable ` +
    `non-destructively ⇒ verdict not-checkable + reason.\n` +
    `  - loading: observe DURING the fetch. pass = a layout-reserved indicator OR a sub-1s render (instant needs ` +
    `no spinner — the product-ux response-time threshold); fail = a >1s visible blank/jank with no indicator; ` +
    `commonly verdict not-checkable with note 'too fast to observe' — that is HONEST, not a fail.\n` +
    `  - error: induce a NON-DESTRUCTIVE failure where the flow has one (invalid input, a failing call). pass = a ` +
    `human-readable message + a recovery path; fail = a silent failure / raw stack / dead end; no inducible path ⇒ ` +
    `verdict not-checkable + reason.\n\n` +
    `Screenshots: save one end-of-flow screenshot and one per failed step/expect/state UNDER \`${shotDir}/\` ` +
    `(filenames like \`${criterion.id}-<slug>.png\`); return their paths. (For an \`api\` criterion, screenshots ` +
    `may be empty.)\n\n` +
    `Return the structured report: steps [{action, ok, note}], expects [{expect, ok, evidence}], states ` +
    `[{state, verdict, evidence, note}], screenshots [paths], and observedStatus (the HTTP status when one is ` +
    `the load-bearing observation, else null). You MAP plain-English steps to tool calls by judgment — state ` +
    `that in your notes; you attempt the flow, you do not prove the app correct.`
  );
}

// Build the finding-verifier's CLEAN-CONTEXT input for a runtime finding (Slice 4b). The verifier
// gets the claim + route + evidence (NEVER the driver's rationale) and locates the implicated code
// itself to attempt a refutation. Runtime findings have no file:line — the route + observed
// evidence are the anchor.
function verifierPrompt(finding) {
  const ev = finding && finding.evidence ? finding.evidence : {};
  const shots = Array.isArray(ev.screenshots) ? ev.screenshots : [];
  return (
    `Independently REFUTE this single RUNTIME (UX) finding against the actual product code (refute-first; ` +
    `clean context — you are NOT given the driver's rationale, only the observed claim + route + evidence). ` +
    `Open your response with "RUNNING AS: <model family>" and report it in runningAs.\n\n` +
    `Issue class: ${finding.issueClass}. Criterion: ${finding.criterionId || "(merged)"}. Route: ${finding.route || "(unknown)"}.\n` +
    `Claim (plain English): ${finding.plainEnglish}\n` +
    `Observed evidence: ${JSON.stringify({ observedStatus: ev.observedStatus, observedText: ev.observedText, state: ev.state })}\n` +
    `Screenshots saved this run: ${JSON.stringify(shots)}\n` +
    `Finder's confidence label: ${finding.confidence}\n\n` +
    `This is a RUNTIME observation, not a code line-number claim — locate the implicated handler/template/route ` +
    `yourself (use docs/ARCHITECTURE_TREE.md as the index), READ it, and decide: is the observed UX gap genuinely ` +
    `in the code (a missing empty/error state, a broken POST route), or did the driver misread a state that is ` +
    `actually handled? Return verdict (Verified|Refuted|Unconfirmed), evidence (the proof/disproof with file:line), ` +
    `and one plain-English line.`
  );
}

// Spawn one finding-verifier with the cross-model `model:` pin; one no-override respawn on failure
// (the result then can't confirm a different family → the run carries the same-model tag); a
// second failure returns null (the finding is then marked deferred — never a silent skip). Copied
// in spirit from audit.js's spawnVerifier (runtime-shaped).
async function spawnVerifier(finding) {
  const prompt = verifierPrompt(finding);
  const attempt = async (opts) => {
    try {
      return { out: await agent(prompt, opts) };
    } catch (e) {
      return { out: null, err: e && e.message ? e.message : String(e) };
    }
  };
  const first = await attempt({
    agentType: "finding-verifier",
    model: MODELS.judge,
    schema: VERIFIER_SCHEMA,
    label: `qa:verify:${finding.criterionId || finding.issueClass}`,
    phase: "Verify",
  });
  if (first.out != null) {
    return first.out;
  }
  const second = await attempt({
    agentType: "finding-verifier",
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

// ── Top-level control flow (Workflow scripts run in an async context; no module wrapper). ──

// Validate at the boundary. A missing/empty runCommand or appUrl is NOT a silent throw — it is
// the could-not-run finding (a QA run that can't run reports that it can't run). Any OTHER shape
// error (bad types on the optional fields) fails loud — those are caller-contract bugs.
const input = parseArgs(args);
const { runConfig, errors } = parseRunArgs(input);

// Partition the errors: the missing-run-inputs class becomes the finding; the rest throw.
const runInputErrors = errors.filter(isRunInputError);
const otherErrors = errors.filter((e) => !runInputErrors.includes(e));
if (otherErrors.length > 0) {
  throw new Error(`qa args invalid:\n  - ${otherErrors.join("\n  - ")}`);
}

// Validate the acceptance criteria at the boundary (FROZEN schema). Invalid criteria are a
// caller-contract bug (a malformed spec) — fail loud naming the offending ids, NEVER silently
// filter (a dropped criterion is a silently-unchecked promise). An absent/empty list ⇒ boot-only.
{
  const criteriaErrors = validateCriteria(runConfig ? runConfig.criteria : []);
  if (criteriaErrors.length > 0) {
    throw new Error(`qa criteria invalid:\n  - ${criteriaErrors.join("\n  - ")}`);
  }
}

// No runnable command/URL — emit the could-not-run finding and stop (never a fake pass, never a
// silent skip). There is nothing to tear down (nothing was started). Mode is the criteria-derived
// mode so a full run that lacks a command still reports honestly that it could not run.
if (runInputErrors.length > 0) {
  log(`qa: cannot run — ${runInputErrors.join("; ")}. Emitting the could-not-run finding.`);
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
const artifactDir = runConfig.artifactDir && runConfig.artifactDir.length > 0 ? runConfig.artifactDir : ".qa-artifacts";
// The script has no clock: a runLabel from args wins; else the boot agent stamps `qa-<timestamp>`
// (threaded below). A null here means "ask the boot agent to generate one".
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

// --- Boot + teardown, with teardown ALWAYS in the finally (success, boot failure, mid-run
// error alike — the port is freed no matter how the run exits). The try body holds the
// flow-driving stage (criteria → drivers → findings → cross-model verify) when criteria are
// present; boot-only when none. ---
let bootReport = null;
let findings = [];
let verdicts = [];
let refutedCount = 0;
let ready = false;
let allScreenshots = [];

phase("Boot");
try {
  // agent() returns null on skip/terminal error — and can THROW. Both shapes are the same
  // honest failure: a null/malformed/thrown boot classifies failed and becomes the
  // could-not-run finding, never an uncaught crash with no finding.
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

  // The boot agent may have stamped the runLabel (the script has no clock) — adopt it.
  if (runLabel == null && bootReport && typeof bootReport.runLabel === "string" && bootReport.runLabel.length > 0) {
    runLabel = bootReport.runLabel;
  }
  if (runLabel == null) {
    // Last-ditch deterministic label so screenshots still have a home if the agent omitted one.
    runLabel = "qa-run";
  }

  const outcome = bootOutcome(bootReport);
  ready = outcome === "ready";
  if (!ready) {
    // The explicit, evidence-carrying could-not-run finding — never a silent skip, never a pass.
    findings.push(couldNotRunFinding(runConfig, bootReport));
    log(`qa boot FAILED — ${COULD_NOT_RUN_CLASS} finding emitted with log-tail evidence.`);
  } else {
    log(`qa boot READY after ${bootReport && bootReport.attempts != null ? bootReport.attempts : "?"} probe(s).`);
  }

  // ── Flow-driving (full mode only, and only when the app booted): one driver agent per
  // drivable criterion, run SEQUENTIALLY (criteria mutate app state — parallel drivers would
  // interfere). Each driver's report folds to a pass|fail|not-checkable verdict; every fail
  // becomes a lens-shaped UX finding. A boot failure already produced the could-not-run finding;
  // we do NOT drive against a dead app (every e2e verdict would be a false fail). ──
  if (mode === "full" && ready) {
    phase("Drive");
    for (const criterion of drivable) {
      let report = null;
      try {
        report = await agent(driverPrompt(runConfig, criterion, runLabel, artifactDir), {
          agentType: "general-purpose",
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
      // The route the criterion landed on — the appUrl is the honest default anchor (drivers
      // observe a surface, not a file:line). A criterion may report a more specific route.
      const route = report && typeof report.route === "string" && report.route.length > 0 ? report.route : runConfig.appUrl;
      verdicts.push({ id: criterion.id, feature: criterion.feature, check: criterion.check, verdict, reason, route, report });
      log(`qa criterion ${criterion.id} → ${verdict}${reason ? ` (${reason})` : ""}.`);
    }

    // Shape the fails into lens-shaped findings, dedup by class+route, then add them to the
    // findings list ALONGSIDE any could-not-run finding (which, here, there is none — boot was ready).
    const driverFindings = dedupFindings(findingsFrom(verdicts));
    findings.push(...driverFindings);

    // VERIFY: exactly one cross-model finding-verifier per surfaced finding (parallel fan-out).
    // The could-not-run finding (none here) would be exempt; driver findings are all re-checked.
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
    }
  } else if (mode === "full" && !ready) {
    // Full run requested, but the app never booted — the could-not-run finding stands and NO
    // criterion was driven (driving a dead app would manufacture false fails). Every drivable
    // criterion is reported not-checkable with the boot-failure reason — honest, never a pass.
    for (const criterion of drivable) {
      verdicts.push({
        id: criterion.id,
        feature: criterion.feature,
        check: criterion.check,
        verdict: "not-checkable",
        reason: "the app could not be booted — see the qa-could-not-run-app finding",
        route: runConfig.appUrl,
        report: null,
      });
    }
  }
} finally {
  phase("Teardown");
  // A throwing teardown inside a finally would REPLACE the boot exception (JS try/finally
  // semantics) and the operator would debug the wrong failure — so teardown failures are
  // caught, logged loudly, and never allowed to mask the original root cause.
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
        `qa teardown DID NOT cleanly free the port (${teardownReport && teardownReport.note ? teardownReport.note : "no report"}) — ` +
          "reported, not hidden.",
      );
    }
  } catch (tdErr) {
    log(
      `qa teardown agent threw (${tdErr && tdErr.message ? tdErr.message : tdErr}) — reported, ` +
        "not hidden; the port may need a manual check. The original run outcome is preserved.",
    );
  }
}

// The run's cross-model claim — `confirmed` ONLY when EVERY re-checkable finding's verifier
// returned a confirming self-report of a different family than the builder; otherwise the
// disclosure tag for WHY. The non-confirmed tag is now THREE-state: a present-but-UNRESOLVED
// verifier family yields UNRESOLVED_FAMILY_TAG (reported unresolved, never asserted same-model
// fact); a resolved-same (or missing-report) verifier yields SAME_MODEL_TAG. The could-not-run
// finding is exempt — it carries no verifier self-report. The builder family is the orchestrator's
// session family (passed as args.builderFamily when known).
const builderFamily = typeof input.builderFamily === "string" ? input.builderFamily : "";
const reCheckable = findings.filter((f) => f.issueClass !== COULD_NOT_RUN_CLASS);
const allConfirmingDifferentFamily =
  reCheckable.length > 0 &&
  reCheckable.every((f) => f.verifierRunningAs != null && sameModelTag(builderFamily, f.verifierRunningAs) === null);
// Observability: a verifier self-report that is present but does not resolve to a KNOWN family is
// LOGGED, never silently degraded — and taints the disclosure to UNRESOLVED, not asserted same-model.
let sawUnresolved = false;
for (const f of reCheckable) {
  const reported = f.verifierRunningAs;
  if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
    sawUnresolved = true;
    log(
      `qa: a finding-verifier self-reported an UNRECOGNIZED model family ` +
        `(${JSON.stringify(reported)}) — reported as unresolved, no cross-model claim made.`,
    );
  }
}
const crossModel = allConfirmingDifferentFamily
  ? "confirmed"
  : sawUnresolved
    ? UNRESOLVED_FAMILY_TAG
    : SAME_MODEL_TAG;

const passCount = verdicts.filter((v) => v.verdict === "pass").length;
const failCount = verdicts.filter((v) => v.verdict === "fail").length;
const notCheckableCount = verdicts.filter((v) => v.verdict === "not-checkable").length;

const fullSummary =
  `full run: ${verdicts.length} criteria driven (${passCount} pass · ${failCount} fail · ` +
  `${notCheckableCount} not-checkable) + ${manualCriteria.length} manual (listed for a human, never driven). ` +
  `${findings.length} finding(s) surfaced (${refutedCount} refuted and dropped by the cross-model re-check). ` +
  `The drivers ATTEMPTED each flow (model-upheld judgment of your plain-English steps) — measured facts are the ` +
  `observed HTTP/element evidence; asserted are the drivers' interpretive calls. This reduces the risk the product ` +
  `diverged from the criteria; it does not prove the app correct.`;

const bootOnlySummary = ready
  ? "boot-only run (no criteria provided): the app booted, answered the readiness probe, and was torn down. " +
    "No flow-driving (no acceptance criteria)."
  : "boot-only run (no criteria provided): the app could NOT be run — exactly one could-not-run finding was " +
    "emitted with boot-log evidence, and teardown still ran. This is reported, not a pass and not a silent skip.";

return {
  // full mode "ran" = the app was ready AND criteria were actually exercised;
  // boot-only "ran" = the app booted. A manual-only run drives nothing → ran false, honest.
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
  artifacts: { dir: mode === "full" ? `${artifactDir.replace(/\/+$/, "")}/${runLabel}` : null, screenshots: allScreenshots },
  crossModel: mode === "full" ? crossModel : SAME_MODEL_TAG,
  summary: mode === "full" ? fullSummary : bootOnlySummary,
};
