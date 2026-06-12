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
    "Runtime verification (QA) as a Workflow script. Slice-4a boot vertical: a boot agent starts the recorded run command detached, probes the readiness URL on a bounded schedule (readinessPlan — never unbounded), and ALWAYS tears down via teardownPlan (explicit override > docker compose down > kill the recorded PID) in a finally so the port is freed on success, boot failure, and mid-run error alike. A boot that never answers within the bound (or a missing/malformed boot report) classifies `failed` (fail loud — never default to success) and produces exactly one lens-shaped `qa-could-not-run-app` finding with the command + probe attempts + boot-log tail as evidence, tagged (observed this run — boot log attached). Flow-driving is Slice 4b.",
  // Bounded call count: boot + teardown = 2 agents in boot-only mode (no criteria). Declared so
  // the tool can cap the run; the structure (no loops) already bounds it.
  budget: { agents: 2 },
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
// --- end helpers ---

// Build the boot agent's prompt from the validated run config + the bounded readiness plan. The
// agent (not the script) has Bash: it starts the command detached and probes the URL.
function bootPrompt(runConfig, plan) {
  const compose = isComposeCommand(runConfig.runCommand);
  const startHint = compose
    ? "This is a docker compose command — it detaches with `-d` (start it so it returns control)."
    : "This is a dev-server command — start it BACKGROUNDED, redirect its stdout+stderr to a log file, and record its PID (return the PID and the log path).";
  return (
    `Runtime QA — BOOT stage only (no flow-driving this run). Start the app and confirm it is ready.\n\n` +
    `Run command: \`${runConfig.runCommand}\`\n` +
    `Readiness URL: ${runConfig.appUrl}\n` +
    `${startHint}\n\n` +
    `Then probe the readiness URL with curl every ~${plan.intervalSec}s, up to ${plan.maxAttempts} attempts ` +
    `(the bounded wait of ${plan.timeoutSec}s — NEVER wait unbounded). Ready = an HTTP response (any 2xx/3xx/4xx ` +
    `means the server answered; a connection refusal/timeout means not-yet).\n\n` +
    `Return the structured report: started, ready, pid (if a dev-server), logPath, logTail (the LAST <=50 lines ` +
    `of the boot log — REQUIRED on failure so the could-not-run finding carries evidence), and attempts (how many ` +
    `probes you made). If the command itself fails to launch, set started=false and put the launch error in logTail. ` +
    `Do NOT tear anything down — the script's teardown stage owns that.`
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

// No runnable command/URL — emit the could-not-run finding and stop (never a fake pass, never a
// silent skip). There is nothing to tear down (nothing was started).
if (runInputErrors.length > 0) {
  log(`qa: cannot run — ${runInputErrors.join("; ")}. Emitting the could-not-run finding.`);
  const finding = couldNotRunFinding(runConfig, null);
  return {
    ran: false,
    mode: "boot-only",
    boot: { started: false, ready: false, attempts: 0 },
    findings: [finding],
    summary:
      "QA did not run: no runnable command was provided. The could-not-run finding names the fix " +
      "(record a Run-the-app line). This is reported, not silently skipped.",
  };
}

const plan = readinessPlan(runConfig);
log(
  `qa boot-only: run=\`${runConfig.runCommand}\` url=${runConfig.appUrl} ` +
    `readiness=${plan.timeoutSec}s (${plan.maxAttempts} probes @ ${plan.intervalSec}s).`,
);

// --- Boot + teardown, with teardown ALWAYS in the finally (success, boot failure, mid-run
// error alike — the port is freed no matter how the run exits). Boot-only this slice; the try
// body is the seam where 4b's flow-driving (criteria → drivers → findings → verify) slots in. ---
let bootReport = null;
let findings = [];
let ready = false;

phase("Boot");
try {
  // agent() returns null on skip/terminal error — and can THROW. Both shapes are the same
  // honest failure: a null/malformed/thrown boot classifies failed and becomes the
  // could-not-run finding, never an uncaught crash with no finding.
  try {
    bootReport = await agent(bootPrompt(runConfig, plan), {
      agentType: "general-purpose",
      schema: BOOT_SCHEMA,
      label: "qa:boot",
      phase: "Boot",
    });
  } catch (bootErr) {
    log(`qa boot agent threw: ${bootErr && bootErr.message ? bootErr.message : bootErr}`);
    bootReport = {
      started: false,
      ready: false,
      attempts: 0,
      logTail: `boot agent error: ${bootErr && bootErr.message ? bootErr.message : String(bootErr)}`,
    };
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

  // ── 4b seam: when criteria are present, the flow-driving stage runs here (drivers per
  // criterion → lens-shaped findings → cross-model finding-verifier). Boot-only this slice:
  // criteria are validated-absent and the run reports mode 'boot-only'. ──
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

return {
  ran: ready,
  mode: "boot-only",
  boot: {
    started: bootReport && bootReport.started === true,
    ready,
    pid: bootReport && bootReport.pid != null ? bootReport.pid : null,
    logPath: bootReport && bootReport.logPath != null ? bootReport.logPath : null,
    attempts: bootReport && bootReport.attempts != null ? bootReport.attempts : 0,
  },
  findings,
  summary: ready
    ? "boot-only run (no criteria provided): the app booted, answered the readiness probe, and was torn down. " +
      "Flow-driving (UX criteria) is Slice 4b — not run here."
    : "boot-only run (no criteria provided): the app could NOT be run — exactly one could-not-run finding was " +
      "emitted with boot-log evidence, and teardown still ran. This is reported, not a pass and not a silent skip.",
};
