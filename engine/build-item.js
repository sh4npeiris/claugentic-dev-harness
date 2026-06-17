// engine/build-item.js — the build-to-green inner loop as an executable Workflow script.
//
// The engine the 5a autonomy ladder unlocks: take ONE approved item and iterate
//   implement (worktree) → deterministic gates → Verify panel → QA flows → fix
// until everything is green or the iteration/budget cap hits. The script NEVER lands,
// pushes, merges, or touches git history by construction — EVERY terminal status is a
// return-to-orchestrator (the before-land pause, the irreversible hard-stop, and the
// re-triage on a new Tier-1/2 finding all belong to the orchestrator/skill, not the script).
//
// The two later stages (Verify, QA) are run via the ONE-LEVEL platform child call
// `workflow({scriptPath}, childArgs)` — so the panel/QA wiring (judge model pins, the
// same-model tagging, the runtime finding shapes) has a SINGLE source of truth in
// verify.js / qa.js; an inlined copy here would drift (DRY). build-item.js spawns NO judge
// directly, so it carries no `MODELS` block — only the run-level `sameModelTag` to fold the
// children's self-reports into the terminal cross-model claim.
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped plugin
// install dir (`${CLAUDE_PLUGIN_ROOT}/engine/build-item.js`); this repo dogfoods it via the
// repo-local `./engine/build-item.js` (the working tree IS the plugin source). Never copied
// into an adopter repo (no managed-stamp/refresh surface) — see docs/claugentic-DECISIONS.md → Plugin identity & distribution.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps times AFTER the run).
// Only the tool primitives `agent()`/`parallel()`/`pipeline()`/`phase()`/`log()`/`args`/`budget`
// + the one-level `workflow()` child call. Pure decision logic lives in the marked
// `// --- helpers ---` block and is unit-tested by tests/workflows/build-item.test.mjs
// (extract-and-eval), so the prose->script move tests the judgment, not just inspects it.
//
// Per-stage duration bound (caps.stageTimeouts) — the THREE-WAY enforcement register (the
// honesty contract; the three bounded stages do NOT enforce equally, and the copy must say so).
// The script has no wall-clock, so it CANNOT time a stage itself; the only lever is the Bash
// tool's `timeout` parameter on the commands the stage agents run — a PER-COMMAND bound, NEVER a
// stage wall-clock total (a gates stage of k commands can legitimately take ~k×bound plus the
// agent's reasoning). The register:
//   - gates    — agent-applied per-command Bash-tool timeout + a MECHANICAL red decision: a
//                timed-out command reports exitCode 124 (the named no-exit-observed convention)
//                and `gatesGreen` reads that reported code as red. Strongest.
//   - qaBoot   — a MECHANICAL clamp in qa.js (parseRunArgs Math.min ≤ 300s) + an agent-executed
//                bounded readiness probe. Mechanical bound, agent-executed probe.
//   - implement/fix — an INSTRUCTION-ONLY anti-hang nudge: IMPLEMENT_SCHEMA has NO exit-code
//                channel, so there is no mechanical consumer; a runaway is left to surface
//                downstream (the gates stage + the iteration cap) WHEN it manifests there —
//                nothing in this stage bounds it. Model-upheld end to end (NOT "fail-closed").
// Residual: a single legitimate command that genuinely exceeds the Bash-tool 600s hard max cannot
// be bounded-and-completed in one foreground call — that repo's suite must be split, or it is not
// bounded-runnable. No mechanism here bounds a stage's TOTAL wall-clock.

export const meta = {
  name: "build-item",
  description:
    "The build-to-green engine: one approved item iterated implement (implementer-architect in a worktree) → deterministic gates (an agent runs the repo's gate commands; pass/fail is exit codes) → Verify panel (the verify.js child workflow) → QA flows (the qa.js child workflow, only when machine-checkable acceptance criteria exist) → fix, until green or the iteration/budget cap. The script NEVER lands/pushes/merges/touches git — every terminal status is a return-to-orchestrator: green (the before-land pause is the orchestrator's), needs-irreversible (the irreversible hard-stop), new-tier12 (a finding outside the item — re-triage), not-green (the cap: 'not green; here is the residual', nothing partial landed), blocked (a boundary error, e.g. a manual criterion or criteria with no run-app command). A green close-out claims only 'passed the deterministic gates and the reviewers' audit on this run' — a reduction of unwatched-run risk, never a substitute for the unbuilt deterministic trust-gates, never 'proven correct'.",
  // Bounded call count: per iteration = 1 implement/fix + 1 gates agent + 1 verify child + (≤1
  // qa child) — no unbounded loops (maxIterations caps it). The static budget below is a
  // backstop; caps.maxIterations is the true bound, enforced in code by nextAction.
  budget: { agents: 60 },
};

// --- helpers ---
// Pure functions only — they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The verbatim same-model disclosure tag. Defined once; never reconstructed by hand at a call
// site, so the wording cannot drift (honesty trust surface). Copied verbatim from verify.js.
const SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// Bundled agents resolve only as `claugentic-dev-harness:<agent>` for an installed adopter
// (bare names resolve only when dogfooded with project-local .claude/agents/). Namespace every
// custom-agent spawn; built-ins (general-purpose, …) stay bare. Pure → unit-tested.
const nsAgent = (name) => `claugentic-dev-harness:${name}`;

// The verbatim UNRESOLVED disclosure tag — the THIRD state, distinct from SAME_MODEL_TAG. When a
// judge's self-reported family can't be recognized, the run is reported as unresolved (the
// conservative same-model trust floor still holds — no cross-model claim) rather than ASSERTED to
// be same-model fact. Defined once so the wording cannot drift (honesty trust surface). Copied
// byte-identical across the workflow scripts (cross-script drift pin). Carried here so the copied
// sameModelTag below stays byte-identical and evaluable, even though this script spawns no judge.
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
// from verify.js (see there for the full state table). This script spawns no judge — but its
// CHILDREN do, so the run-level cross-model claim in the terminal report derives from the
// children's self-reports via this one rule.
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

// Normalize the args boundary. A scriptPath invocation delivers `args` as a JSON STRING
// (observed runtime behavior, 2026-06-11); an inline script may receive the object itself.
// Accept both; an unparseable string fails loud — never a silent empty-args run. Copied
// verbatim from verify.js (modulo the script-name string the cross-script drift pin allows).
function parseArgs(raw) {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new Error("build-item args: not valid JSON (" + (e && e.message ? e.message : e) + ")");
    }
  }
  return raw;
}

// The default iteration cap when caps.maxIterations is absent — matches the SKILL's bounded
// 2–3 implement→verify attempts (docs/claugentic-WORKFLOW.md / skills/build SKILL step 6).
const DEFAULT_MAX_ITERATIONS = 3;

// The Bash-tool hard max for a single command's `timeout` parameter (600000ms = 600s). The single
// ceiling constant — referenced, never re-hardcoded as a bare 600. validateArgs rejects (never
// silently clamps) a stageTimeout above it: a "configurable 800" that can't be honored is a lie.
const MAX_STAGE_TIMEOUT_SEC = 600;

// Per-stage DISTINCT defaults (a gate suite and a boot probe have very different legitimate
// durations). implement/gates default to the loosest-safe Bash-tool max; `qaBoot` has NO engine
// default (`null` = not set) — qa.js owns the boot default (60s) and clamp (300s), so no
// 60/300 literal is duplicated into this script (DRY) and the engine's boot default is unchanged.
const DEFAULT_STAGE_TIMEOUTS = { implement: MAX_STAGE_TIMEOUT_SEC, gates: MAX_STAGE_TIMEOUT_SEC, qaBoot: null };

// The exact key set for caps.stageTimeouts — a typo'd stage (`qaboot`, `implment`) must fail loud,
// never silently fall back to the default (the frozen-criterion exact-key precedent below). DERIVED
// from DEFAULT_STAGE_TIMEOUTS (single source of truth — a new stage is added in ONE place, never a
// second hand-maintained list that must agree with it forever).
const STAGE_TIMEOUT_KEYS = Object.keys(DEFAULT_STAGE_TIMEOUTS);

// Resolve the per-stage duration bounds from caps.stageTimeouts (per-stage distinct defaults).
// PURE — the boundary already validated/rejected out-of-range values (validateArgs), so there is
// NO clamping here; this just applies the defaults. implement/gates default to MAX_STAGE_TIMEOUT_SEC;
// `qaBoot` stays `null` when unset (qa.js stays the sole boot default-and-clamp owner).
function resolveStageTimeouts(caps) {
  const st = caps && typeof caps.stageTimeouts === "object" && caps.stageTimeouts !== null ? caps.stageTimeouts : {};
  // No re-validation here: validateArgs already rejected every invalid value at the boundary (the
  // script throws before this helper runs), so re-checking the predicate would (a) duplicate the
  // boundary contract (DRY) and (b) silently fall back to the default on a bad type — contradicting
  // both this function's own no-clamping rule and the slice's fail-loud register. An explicit-null
  // value is impossible to reach (validateArgs only accepts positive integers or `undefined`).
  const pick = (key) => (st[key] !== undefined ? st[key] : DEFAULT_STAGE_TIMEOUTS[key]);
  return { implement: pick("implement"), gates: pick("gates"), qaBoot: pick("qaBoot") };
}

// The frozen acceptance-criterion field names (must match qa.js's frozen schema EXACTLY — a
// renamed field here would silently diverge the contract). validateArgs guards every criterion
// against this set so a typo'd spec fails loud, not silently unchecked.
const CRITERION_KEYS = ["id", "feature", "flow", "expect", "states", "check"];
// The criterion `check` enum (frozen — qa.js CHECK_KINDS). `manual` needs a human → the item
// stays in checkpoint (5a should have declined; the script re-validates and blocks).
const CHECK_KINDS = ["e2e", "api", "manual"];

// Validate the args contract at the boundary. Returns `{ ok, errors }` — the control flow
// throws on a non-empty error list (fail loud; nothing defaults silently). Empty gateCommands
// is an ERROR by design: zero gates would make a "green" verdict a lie.
function validateArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return { ok: false, errors: ["args must be an object"] };
  }
  // item
  const item = args.item;
  if (!item || typeof item !== "object") {
    errors.push("item is required (object: id, title, tag, planPath, specText, acceptanceCriteria)");
  } else {
    if (typeof item.id !== "string" || item.id.trim().length === 0) {
      errors.push("item.id is required (non-empty string)");
    }
    if (typeof item.specText !== "string" || item.specText.trim().length === 0) {
      errors.push("item.specText is required (non-empty string — the approved spec section, verbatim)");
    }
    // acceptanceCriteria: may be [] (no machine-checkable criteria) but must be an array.
    if (item.acceptanceCriteria !== undefined && !Array.isArray(item.acceptanceCriteria)) {
      errors.push("item.acceptanceCriteria, when provided, must be an array (the frozen-schema criteria; may be [])");
    } else if (Array.isArray(item.acceptanceCriteria)) {
      item.acceptanceCriteria.forEach((c, i) => {
        const at = c && typeof c.id === "string" && c.id.length > 0 ? `acceptanceCriteria id '${c.id}'` : `acceptanceCriteria[${i}]`;
        if (!c || typeof c !== "object" || Array.isArray(c)) {
          errors.push(`${at}: each criterion must be an object`);
          return;
        }
        // Frozen-schema guard: exactly the six keys — a renamed/extra field is a contract drift.
        const keys = Object.keys(c).sort();
        const expected = [...CRITERION_KEYS].sort();
        if (keys.length !== expected.length || !expected.every((k, idx) => k === keys[idx])) {
          errors.push(`${at}: criterion fields must be exactly {${CRITERION_KEYS.join(", ")}} (got {${Object.keys(c).join(", ")}})`);
        }
        if (c.check !== undefined && !CHECK_KINDS.includes(c.check)) {
          errors.push(`${at}: check must be one of ${CHECK_KINDS.join("|")}`);
        }
      });
    }
  }
  // repo
  const repo = args.repo;
  if (!repo || typeof repo !== "object") {
    errors.push("repo is required (object: root, baseBranch, gateCommands, runApp, pluginRoot)");
  } else {
    if (typeof repo.root !== "string" || repo.root.trim().length === 0) {
      errors.push("repo.root is required (non-empty string)");
    }
    if (typeof repo.baseBranch !== "string" || repo.baseBranch.trim().length === 0) {
      errors.push("repo.baseBranch is required (non-empty string — the branch the worktree diffs against)");
    }
    if (!Array.isArray(repo.gateCommands) || repo.gateCommands.length === 0) {
      errors.push("repo.gateCommands is required (non-empty array — zero gates would make 'green' a lie)");
    } else if (!repo.gateCommands.every((g) => typeof g === "string" && g.trim().length > 0)) {
      errors.push("repo.gateCommands must be an array of non-empty command strings");
    }
    if (typeof repo.pluginRoot !== "string" || repo.pluginRoot.trim().length === 0) {
      errors.push("repo.pluginRoot is required (non-empty string — the expanded ${CLAUDE_PLUGIN_ROOT} for the child workflow paths)");
    }
    // runApp may be null (no app) but must be a string when present.
    if (repo.runApp !== undefined && repo.runApp !== null && typeof repo.runApp !== "string") {
      errors.push("repo.runApp, when provided, must be a string or null");
    }
  }
  // caps
  if (args.caps !== undefined && args.caps !== null) {
    if (typeof args.caps !== "object") {
      errors.push("caps, when provided, must be an object ({ maxIterations?, budget?, stageTimeouts? })");
    } else {
      if (
        args.caps.maxIterations !== undefined &&
        (typeof args.caps.maxIterations !== "number" || !Number.isInteger(args.caps.maxIterations) || args.caps.maxIterations < 1)
      ) {
        errors.push("caps.maxIterations, when provided, must be a positive integer");
      }
      // stageTimeouts (per-stage duration bound, seconds). Fail loud, never silent-clamp: a non-object,
      // any unknown key (exact-key set — a typo'd stage can't fall back to default), a non-integer or
      // ≤0 value, or a value > MAX_STAGE_TIMEOUT_SEC (a bound the Bash tool can't honor is rejected).
      const st = args.caps.stageTimeouts;
      if (st !== undefined && st !== null) {
        if (typeof st !== "object" || Array.isArray(st)) {
          errors.push("caps.stageTimeouts, when provided, must be an object ({ implement?, gates?, qaBoot? } — positive integer seconds)");
        } else {
          for (const k of Object.keys(st)) {
            if (!STAGE_TIMEOUT_KEYS.includes(k)) {
              errors.push(`caps.stageTimeouts: unknown stage '${k}' — must be one of {${STAGE_TIMEOUT_KEYS.join(", ")}}`);
            }
          }
          for (const k of STAGE_TIMEOUT_KEYS) {
            const v = st[k];
            if (v === undefined) continue;
            if (typeof v !== "number" || !Number.isInteger(v) || v <= 0) {
              errors.push(`caps.stageTimeouts.${k}, when provided, must be a positive integer (seconds)`);
            } else if (v > MAX_STAGE_TIMEOUT_SEC) {
              errors.push(`caps.stageTimeouts.${k} must be ≤ ${MAX_STAGE_TIMEOUT_SEC} (the Bash-tool hard max; a higher bound cannot be honored — split the suite, never silently clamped)`);
            }
          }
        }
      }
    }
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.trim().length === 0) {
    errors.push("builderFamily is required (non-empty string — the orchestrator's session model family, the cross-model fallback)");
  }
  return { ok: errors.length === 0, errors };
}

// Resolve the iteration cap from caps.maxIterations (default 3). PURE — the boundary already
// validated the type; this just applies the default.
function maxIterationsFor(caps) {
  if (caps && typeof caps.maxIterations === "number" && Number.isInteger(caps.maxIterations) && caps.maxIterations >= 1) {
    return caps.maxIterations;
  }
  return DEFAULT_MAX_ITERATIONS;
}

// Which acceptance criteria can never be attempted unwatched (a `check: "manual"` criterion
// needs a human mid-run). Returns the offending ids — a non-empty result is a terminal
// `blocked` (5a should have declined; the script re-validates, never silently waives a manual
// criterion). PURE.
function criteriaBlockers(criteria) {
  const list = Array.isArray(criteria) ? criteria : [];
  return list.filter((c) => c && c.check === "manual").map((c, i) => (c && c.id != null ? c.id : `criteria[${i}]`));
}

// Join the plugin root and a child-workflow script name into the scriptPath for the one-level
// `workflow()` child call. Throws on an empty/whitespace root (fail loud — a missing pluginRoot
// would silently resolve to a relative path and run the WRONG script, or none). PURE.
function childScriptPath(pluginRoot, name) {
  if (typeof pluginRoot !== "string" || pluginRoot.trim().length === 0) {
    throw new Error(`childScriptPath: pluginRoot is empty — cannot resolve the '${name}' child workflow path`);
  }
  if (typeof name !== "string" || name.trim().length === 0) {
    throw new Error("childScriptPath: name is required");
  }
  const root = pluginRoot.replace(/[\\/]+$/, "");
  return `${root}/engine/${name}`;
}

// Decide whether the deterministic gates are green from the gates agent's per-command results.
// Returns `{ green, failures }` — a missing/non-numeric exitCode counts as a FAILURE (fail loud,
// never fail-open: a malformed result must never read as a pass). green iff every command
// reported exitCode === 0. PURE.
function gatesGreen(results) {
  const list = Array.isArray(results) ? results : null;
  if (list === null) {
    return { green: false, failures: [{ command: "(no gate results)", reason: "the gates agent returned no results array" }] };
  }
  const failures = [];
  for (const r of list) {
    const command = r && typeof r.command === "string" ? r.command : "(unnamed command)";
    if (!r || typeof r.exitCode !== "number" || !Number.isFinite(r.exitCode)) {
      failures.push({ command, reason: "missing or non-numeric exitCode", outputTail: r && r.outputTail != null ? r.outputTail : null });
    } else if (r.exitCode !== 0) {
      failures.push({ command, exitCode: r.exitCode, outputTail: r.outputTail != null ? r.outputTail : null });
    }
  }
  return { green: failures.length === 0, failures };
}

// Decide whether the QA stage is green from qa.js's verdicts. Returns `{ green, failures }`.
// Anything other than a `pass` verdict — including `not-checkable` and the could-not-run finding
// (which surfaces as a fail/non-pass) — counts as a FAILURE: a broken boot may be the
// implementer's regression, fixable in-loop, never a silent skip. An empty verdicts list with no
// findings is treated as green-or-not-applicable by the CALLER (qaGreen is only consulted when QA
// actually ran). PURE.
function qaGreen(qaResult) {
  if (!qaResult || typeof qaResult !== "object") {
    return { couldNotRun: true, green: false, failures: [{ criterionId: "(qa)", reason: "QA stage returned no usable result" }] };
  }
  const failures = [];
  // A could-not-run finding (boot failed) fails QA — never a silent skip.
  const findings = Array.isArray(qaResult.findings) ? qaResult.findings : [];
  for (const f of findings) {
    if (f && f.issueClass === "qa-could-not-run-app") {
      failures.push({ criterionId: "(boot)", reason: "the app could not be run — see the qa-could-not-run-app finding", issueClass: f.issueClass });
    }
  }
  const verdicts = Array.isArray(qaResult.verdicts) ? qaResult.verdicts : [];
  for (const v of verdicts) {
    if (!v || v.verdict !== "pass") {
      failures.push({
        criterionId: v && v.id != null ? v.id : "(unnamed)",
        verdict: v && v.verdict != null ? v.verdict : "(none)",
        reason: v && v.reason != null ? v.reason : null,
      });
    }
  }
  return { couldNotRun: false, green: failures.length === 0, failures };
}

// The tier-1/2 subset of an implementer's out-of-scope findings — these escalate to the
// orchestrator (a finding OUTSIDE the item; never folded silently into the item's fix brief).
// Tier 3 (polish) is ignored here (it is roadmap noise, not a build interrupt). A finding with a
// missing/invalid tier is treated as in-scope-of-escalation (tier ≤ 2) conservatively — an
// unclassified important finding must never be silently dropped. PURE.
function outOfScopeTier12(findings) {
  const list = Array.isArray(findings) ? findings : [];
  return list.filter((f) => {
    if (!f || typeof f !== "object") return false;
    const tier = typeof f.tier === "number" ? f.tier : Number(f.tier);
    if (!Number.isFinite(tier)) return true; // unclassified → escalate (conservative, never drop)
    return tier <= 2;
  });
}

// The priority-ordered decision for one iteration's folded state. The order is LOAD-BEARING:
//   irreversibleNeeded > new-tier12 > green > cap-stop > fix.
// An irreversible need or a new Tier-1/2 finding interrupts EVEN a green run (the orchestrator
// must decide). green requires gates green ∧ verify PASS ∧ QA green-or-not-applicable. Otherwise,
// at/over the cap → cap-stop (report the residual; nothing partial lands); else fix. Throws on a
// malformed state (a missing required field is a caller bug, not a default). PURE.
function nextAction(state) {
  if (!state || typeof state !== "object") {
    throw new Error("nextAction: state must be an object");
  }
  if (typeof state.iteration !== "number" || !Number.isInteger(state.iteration) || state.iteration < 1) {
    throw new Error("nextAction: state.iteration must be a positive integer");
  }
  if (typeof state.maxIterations !== "number" || !Number.isInteger(state.maxIterations) || state.maxIterations < 1) {
    throw new Error("nextAction: state.maxIterations must be a positive integer");
  }
  if (typeof state.gatesGreen !== "boolean") {
    throw new Error("nextAction: state.gatesGreen must be a boolean");
  }
  if (typeof state.verifyPass !== "boolean") {
    throw new Error("nextAction: state.verifyPass must be a boolean");
  }
  if (typeof state.qaGreenOrNA !== "boolean") {
    throw new Error("nextAction: state.qaGreenOrNA must be a boolean");
  }
  if (state.irreversibleNeeded) {
    return "needs-irreversible";
  }
  if (Array.isArray(state.newTier12) && state.newTier12.length > 0) {
    return "new-tier12";
  }
  if (state.gatesGreen && state.verifyPass && state.qaGreenOrNA) {
    return "green";
  }
  if (state.iteration >= state.maxIterations) {
    return "cap-stop";
  }
  return "fix";
}

// Build the residual report at the cap (the "not green; here is the residual" contract). PURE —
// collects the failing gates, the open verify findings, and the failing QA criteria into one
// structured object the orchestrator surfaces to the user. Nothing here lands; the branch is left
// for inspection.
function residualReport(state) {
  const s = state && typeof state === "object" ? state : {};
  return {
    failingGates: Array.isArray(s.failingGates) ? s.failingGates : [],
    openFindings: Array.isArray(s.openFindings) ? s.openFindings : [],
    failingCriteria: Array.isArray(s.failingCriteria) ? s.failingCriteria : [],
    stageCouldNotRun: Array.isArray(s.stageCouldNotRun) ? s.stageCouldNotRun : [],
    iterationsUsed: typeof s.iteration === "number" ? s.iteration : 0,
  };
}

// Fold one iteration's residual into the next iteration's fix brief (PURE). The fix agent gets
// the failing gate output tails + the open verify findings + the failing QA criteria — exactly
// the work that is still red, nothing else. An empty residual means there is nothing to fix
// (the caller would not be in `fix` then) — returns an empty brief honestly.
function foldResidual(gates, verifyResult, qa) {
  const failingGates = gates && Array.isArray(gates.failures) ? gates.failures : [];
  // A null stage result means the stage DID NOT RUN (a child workflow threw / returned null) —
  // an infrastructure failure, NOT a clean stage. Folding zero findings for it would hand the
  // next fix iteration an empty brief for a problem code cannot fix (the 2026-06-12 Verify
  // panel's must-fix) — so the fold carries an explicit could-not-run entry instead.
  const stageCouldNotRun = [];
  const verifyFindings = Array.isArray(verifyResult && verifyResult.findings)
    ? verifyResult.findings.filter((f) => f && f.status !== "met")
    : [];
  if (verifyResult == null) {
    stageCouldNotRun.push(
      "verify could not run (the child workflow threw or returned nothing) — an infrastructure failure, not a code finding; re-run or fix the harness invocation, the diff is not implicated",
    );
  }
  const failingCriteria = qa && qa.failures && Array.isArray(qa.failures) ? qa.failures : [];
  if (qa && qa.couldNotRun === true) {
    stageCouldNotRun.push(
      "qa could not run (the child workflow threw or returned nothing) — an infrastructure failure, not a code finding",
    );
  }
  return { failingGates, verifyFindings, failingCriteria, stageCouldNotRun };
}

// The run-level cross-model claim for the terminal report, folded from the children's
// self-reported judge families. `confirmed` ONLY when every child that ran reported a confirming
// different-family judge; otherwise the verbatim same-model tag. A child that did not run (e.g.
// QA skipped with no criteria) contributes no judge report and never blocks a confirmation on its
// own — only a present-but-same/unresolved report does. PURE.
function crossModelClaim(builderFamily, judgeFamilies) {
  const reports = (Array.isArray(judgeFamilies) ? judgeFamilies : []).filter((j) => j != null && j !== "");
  if (reports.length === 0) {
    return SAME_MODEL_TAG; // no confirming report at all → never claim cross-model
  }
  for (const j of reports) {
    if (sameModelTag(builderFamily, j) !== null) {
      return SAME_MODEL_TAG;
    }
  }
  return "confirmed";
}

// Structured-output schemas as JSON Schema object literals (no imports). The Workflow tool
// validates each agent's structured output against these at the tool-call layer.

// The implementer/fixer agent's report. The BRANCH is the durable artifact (a torn-down worktree
// is recreated from it). outOfScopeFindings + irreversibleNeeded are the escalation channels —
// the implementer REPORTS them, it never builds out-of-scope or performs anything irreversible.
const IMPLEMENT_SCHEMA = {
  type: "object",
  required: ["summary", "branch", "touchedFiles", "modelFamily"],
  properties: {
    summary: { type: "string" },
    branch: { type: "string" },
    worktreePath: { type: ["string", "null"] },
    touchedFiles: { type: "array", items: { type: "string" } },
    modelFamily: { type: "string" },
    outOfScopeFindings: {
      type: "array",
      items: {
        type: "object",
        required: ["tier", "claim"],
        properties: {
          tier: { type: ["integer", "string"] },
          claim: { type: "string" },
          fileLine: { type: ["string", "null"] },
        },
      },
    },
    irreversibleNeeded: {
      type: ["object", "null"],
      properties: {
        action: { type: "string" },
        consequence: { type: "string" },
      },
    },
  },
};

// The deterministic-gates agent's report: one entry per gateCommand with its RAW exit code (the
// prompt demands the actual exit code, not an opinion) + an output tail for the fix brief.
const GATES_SCHEMA = {
  type: "object",
  required: ["results"],
  properties: {
    results: {
      type: "array",
      items: {
        type: "object",
        required: ["command", "exitCode"],
        properties: {
          command: { type: "string" },
          exitCode: { type: "integer" },
          outputTail: { type: ["string", "null"] },
        },
      },
    },
  },
};

// Build the implement/fix agent's prompt. Iteration 1 IMPLEMENTS the spec from scratch; later
// iterations FIX the named residual on the same branch. The standing rules are identical on both
// paths — they are the engine's non-negotiable safety contract (no scope invention, nothing
// irreversible, update the tree, commit on the work branch). The branch is the durable artifact.
// `implementTimeoutSec` is the per-command anti-hang bound — an INSTRUCTION-ONLY nudge here:
// IMPLEMENT_SCHEMA has no exit-code channel, so there is no mechanical consumer; a runaway is left to
// surface downstream (the gates stage + the iteration cap) WHEN it manifests there — nothing in this
// stage bounds it (model-upheld, NOT a mechanical fail-closed).
function implementPrompt(item, repo, residual, branch, implementTimeoutSec) {
  const isFirst = residual == null;
  const standingRules =
    `STANDING RULES (non-negotiable):\n` +
    `  - Build ONLY this item's spec. An out-of-scope finding is REPORTED in outOfScopeFindings (tier + claim + fileLine), NEVER built.\n` +
    `  - NEVER push, deploy, delete data, spend, or take any irreversible/external action. If the item genuinely needs one, set irreversibleNeeded {action, consequence} and STOP — the orchestrator decides, not you.\n` +
    `  - Bound any long-running command (build, test, install) with the Bash tool's \`timeout\` PARAMETER, set to at most ${implementTimeoutSec}s — NOT a shell \`timeout\` command (unreliable cross-platform; a no-op delay on Windows). This is per-command, not a stage total. If a command hits the bound, treat it as a FAILURE and report it — NEVER hang waiting.\n` +
    `  - Update docs/claugentic-ARCHITECTURE_TREE.md for any file add/move/remove, and docs/claugentic-DECISIONS.md for any non-trivial decision.\n` +
    `  - Commit your work on the work branch (the branch is the durable artifact — later fix passes recreate the worktree from it if the platform tore it down). Report the branch name.\n` +
    `  - Report your model family (open with "RUNNING AS: <family>" and set modelFamily).`;
  const repoFacts =
    `Repo: root=${repo.root} · baseBranch=${repo.baseBranch}` +
    (repo.runApp ? ` · run-the-app=\`${repo.runApp}\`` : " · (no run-the-app command recorded)") + ".";
  if (isFirst) {
    return (
      `Build-to-green — IMPLEMENT (iteration 1) for item "${item.title || item.id}" (${item.tag || "untagged"}).\n\n` +
      `Work in an ISOLATED WORKTREE off ${repo.baseBranch}. ${repoFacts}\n\n` +
      `THE APPROVED SPEC (build exactly this — no more, no less):\n${item.specText}\n\n` +
      `${standingRules}`
    );
  }
  // Fix iteration: the residual is the only work. Same branch.
  return (
    `Build-to-green — FIX (a later iteration) for item "${item.title || item.id}". Work on the SAME branch \`${branch}\` ` +
    `(recreate the worktree from it if needed). ${repoFacts}\n\n` +
    `THE RESIDUAL TO FIX (this is the ONLY work — fix exactly what is red below; do not refactor beyond it):\n` +
    `  Failing deterministic gates:\n${JSON.stringify(residual.failingGates, null, 2)}\n` +
    `  Open Verify findings (status != met):\n${JSON.stringify(residual.verifyFindings, null, 2)}\n` +
    `  Failing QA criteria:\n${JSON.stringify(residual.failingCriteria, null, 2)}\n\n` +
    `For reference, the item's approved spec:\n${item.specText}\n\n` +
    `${standingRules}`
  );
}

// Build the deterministic-gates agent's prompt — run EVERY gate command in the worktree and
// return the RAW exit code per command (pass/fail is exit codes, not opinion — this is the
// mechanical-once-invoked stage). The output tail feeds the fix brief on a red gate.
// `gatesTimeoutSec` is the per-command Bash-tool `timeout` bound; a timed-out command observes NO
// real exit code, so it is reported as the named 124 timeout convention (the one allowed
// non-observed code) → `gatesGreen` reads it as red (mechanical). PER-COMMAND, never a stage total.
function gatesPrompt(repo, branch, worktreePath, gatesTimeoutSec) {
  return (
    `Build-to-green — DETERMINISTIC GATES. Run each command below in the work tree for branch \`${branch}\`` +
    (worktreePath ? ` (worktree at ${worktreePath})` : "") +
    `, from the repo root ${repo.root}. Run them ALL even if an earlier one fails.\n\n` +
    `Commands:\n${repo.gateCommands.map((g, i) => `  ${i + 1}. ${g}`).join("\n")}\n\n` +
    `Run EACH command via the Bash tool's \`timeout\` PARAMETER set to ${gatesTimeoutSec}s — NOT a shell \`timeout\` ` +
    `command (unreliable cross-platform; a no-op delay on Windows). This bound is PER-COMMAND, never a stage total.\n\n` +
    `For EACH command return { command, exitCode (the ACTUAL process exit code — 0 = pass, non-zero = fail; ` +
    `report the real number, never an opinion. The ONE exception: a command that hits the ${gatesTimeoutSec}s ` +
    `timeout observes no real exit code — report exitCode 124, the named timeout convention, and note the timeout ` +
    `in outputTail; this is a no-exit-observed convention, NOT an opinion about pass/fail), outputTail (the last ` +
    `~30 lines of its output, REQUIRED when exitCode != 0 so the fix step has evidence) }. Do not interpret or ` +
    `summarize pass/fail — only the exit codes decide.`
  );
}

// Build the qa.js child-workflow args (a PURE builder, extracted from the inline call so the
// threading is unit-testable). `readinessTimeoutSec` is included ONLY when `qaBoot != null`
// (pass-through-when-set): when unset, the key is omitted so qa.js applies its own 60s default —
// qa.js stays the sole boot default-and-clamp owner (no 60/300 literal duplicated here).
function qaChildArgs(item, repo, criteria, builderFamily, iteration, qaBoot) {
  const out = {
    criteria,
    runCommand: repo.runApp,
    appUrl: item.appUrl || (repo.appUrl || ""),
    builderFamily,
    runLabel: `build-${item.id}-iter${iteration}`,
  };
  if (qaBoot != null) {
    out.readinessTimeoutSec = qaBoot;
  }
  return out;
}
// --- end helpers ---

// ── Top-level control flow (Workflow scripts run in an async context; no module wrapper). ──
//
// Validate at the boundary — fail loud with the full error list. EVERY terminal status below is a
// RETURN; there is NO push/merge/land step anywhere in this script by construction.
const input = parseArgs(args);
{
  const { ok, errors } = validateArgs(input);
  if (!ok) {
    throw new Error(`build-item args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

const item = input.item;
const repo = input.repo;
const criteria = Array.isArray(item.acceptanceCriteria) ? item.acceptanceCriteria : [];
const maxIterations = maxIterationsFor(input.caps);
// The per-stage duration bounds — see the three-way register in the header. (qaBoot stays null when
// unset → qa.js's own default.)
const stageTimeouts = resolveStageTimeouts(input.caps);
const builderFamily = input.builderFamily;

// Boundary blocks (terminal `blocked` — never an unwatched run that can't honestly complete):
//   - a manual criterion needs a human (5a should have declined; re-validate here).
//   - criteria present with no run-the-app command ⇒ criteria that can't be attempted.
{
  const manualIds = criteriaBlockers(criteria);
  if (manualIds.length > 0) {
    log(`build-item: BLOCKED — manual acceptance criteria cannot run unwatched: ${manualIds.join(", ")}.`);
    return {
      status: "blocked",
      reason: `acceptance criteria require a human mid-run (check: "manual"): ${manualIds.join(", ")}. ` +
        `Build-to-green cannot attempt a manual criterion — run this item in checkpoint mode.`,
      manualCriteria: manualIds,
    };
  }
  if (criteria.length > 0 && !repo.runApp) {
    log(`build-item: BLOCKED — ${criteria.length} acceptance criteria present but no run-the-app command recorded.`);
    return {
      status: "blocked",
      reason: `this item carries ${criteria.length} machine-checkable acceptance criteria but the repo records no ` +
        `run-the-app command, so QA cannot attempt them — they can't be waived silently. Record a Run-the-app ` +
        `command (CLAUDE.md detected-tooling block) or run this item in checkpoint mode.`,
      criteriaCount: criteria.length,
    };
  }
}

const verifyScript = childScriptPath(repo.pluginRoot, "verify.js");
const qaScript = criteria.length > 0 ? childScriptPath(repo.pluginRoot, "qa.js") : null;

log(
  `build-item: "${item.title || item.id}" (${item.tag || "untagged"}) — up to ${maxIterations} iteration(s); ` +
    `${repo.gateCommands.length} gate command(s); ` +
    (criteria.length > 0 ? `${criteria.length} acceptance criteria (QA will run).` : "no acceptance criteria (QA not run — reported, not silent)."),
);

// The implement-once / fix-loop. Iteration 1 implements; later iterations fix the named residual.
// The branch is the durable artifact threaded across iterations.
let branch = null;
let worktreePath = null;
let implementReport = null;
let residual = null; // null on iteration 1 → implement; set on later iterations → fix
let lastGates = null;
let lastVerify = null;
let lastQa = null;
let iterationsUsed = 0;
let terminal = null; // set to a result object when the loop reaches a terminal status

const judgeFamilies = [];

// children's self-reported judge families → the run-level cross-model claim
let qaConfirmedCrossModel = false; // qa.js folds to a string (no family to mirror) — read below + surfaced in the result

for (let iteration = 1; iteration <= maxIterations; iteration++) {
  iterationsUsed = iteration;
  phase(`iteration-${iteration}`);

  // 1. Implement (iteration 1) or Fix (later) — implementer-architect in a worktree (first only;
  //    later iterations reuse the branch). agent() returns null AND can throw — guard both.
  let report = null;
  try {
    report = await agent(implementPrompt(item, repo, residual, branch, stageTimeouts.implement), {
      agentType: nsAgent("implementer-architect"),
      // Worktree ownership: the platform auto-reclaims an UNCHANGED worktree; a changed one
      // survives every terminal return — the ORCHESTRATOR reclaims it after land (green) or
      // keeps it for inspection (cap-stop/escalation). The BRANCH is the durable artifact.
      ...(iteration === 1 ? { isolation: "worktree" } : {}),
      schema: IMPLEMENT_SCHEMA,
      label: iteration === 1 ? "build:implement" : `build:fix:${iteration}`,
      phase: `iteration-${iteration}`,
    });
  } catch (e) {
    log(`build-item: implement/fix agent threw on iteration ${iteration}: ${e && e.message ? e.message : e}`);
    report = null;
  }
  if (report == null) {
    // The implementer never reported — we cannot proceed honestly (no branch, no work). This is a
    // terminal blocked, not a silent retry: a null implement is a build failure to surface.
    terminal = {
      status: "blocked",
      reason: `the implementer agent returned no usable report on iteration ${iteration} — the build could not proceed. ` +
        `Nothing was landed.`,
      iterationsUsed,
    };
    break;
  }
  implementReport = report;
  if (report.branch) branch = report.branch;
  if (report.worktreePath) worktreePath = report.worktreePath;
  const implementerFamily = typeof report.modelFamily === "string" ? report.modelFamily : "";

  // Escalations from the implementer BEFORE the gates — an irreversible need or a new Tier-1/2
  // out-of-scope finding returns to the orchestrator (never folded silently into the item).
  if (report.irreversibleNeeded) {
    terminal = {
      status: "needs-irreversible",
      irreversible: report.irreversibleNeeded,
      branch,
      worktreePath,
      iterationsUsed,
    };
    break;
  }
  const escalations = outOfScopeTier12(report.outOfScopeFindings);
  if (escalations.length > 0) {
    terminal = {
      status: "new-tier12",
      newFindings: escalations,
      branch,
      worktreePath,
      iterationsUsed,
    };
    break;
  }

  // 2. Deterministic gates — an agent runs every gate command; pass/fail is exit codes (mechanical
  //    once invoked). A null/throwing gates agent fails the gates loud (never fail-open).
  phase(`iteration-${iteration}-gates`);
  let gatesReport = null;
  try {
    gatesReport = await agent(gatesPrompt(repo, branch, worktreePath, stageTimeouts.gates), {
      agentType: "general-purpose",
      schema: GATES_SCHEMA,
      label: `build:gates:${iteration}`,
      phase: `iteration-${iteration}`,
    });
  } catch (e) {
    log(`build-item: gates agent threw on iteration ${iteration}: ${e && e.message ? e.message : e}`);
    gatesReport = null;
  }
  lastGates = gatesGreen(gatesReport ? gatesReport.results : null);
  log(`build-item: iteration ${iteration} gates ${lastGates.green ? "GREEN" : `RED (${lastGates.failures.length} failing)`}.`);

  // 3. Verify panel — the one-level verify.js child workflow (single source of truth for the
  //    panel; an inlined copy would drift — DRY). The diff scope is the branch vs the base branch.
  //    The builder family is the implementer's self-report, falling back to args.builderFamily.
  phase(`iteration-${iteration}-verify`);
  let verifyResult = null;
  try {
    verifyResult = await workflow(
      { scriptPath: verifyScript },
      {
        diffRef: `${repo.baseBranch}...${branch}`,
        specPath: item.planPath || "(spec provided inline)",
        dimensions: Array.isArray(item.dimensions) && item.dimensions.length > 0 ? item.dimensions : ["maintainability-structure", "testing"],
        trustSurface: item.trustSurface === true,
        builderFamily: implementerFamily || builderFamily,
      },
    );
  } catch (e) {
    log(`build-item: verify child workflow threw on iteration ${iteration}: ${e && e.message ? e.message : e}`);
    verifyResult = null;
  }
  lastVerify = verifyResult;
  const verifyPass = !!(verifyResult && verifyResult.verdict === "PASS");
  // Capture the child's judge self-report for the run-level cross-model claim.
  if (verifyResult && verifyResult.crossModel) {
    if (verifyResult.crossModel.claimed === true) {
      // The child confirmed cross-model — record a placeholder confirming family (a non-null,
      // resolvable-different token). The child already computed the claim; we mirror it.
      // Mirror the child's ACTUAL confirming judge families — a synthetic token would fail
      // modelFamily resolution and permanently read as non-confirming (the engine dogfood's
      // escalated Tier-2: the run-level claim could never report confirmed).
      const childJudges = Array.isArray(verifyResult.crossModel.judges)
        ? verifyResult.crossModel.judges
        : [];
      const reported = childJudges
        .map((j) => (j && j.reportedFamily != null ? j.reportedFamily : null))
        .filter((f) => f != null);
      if (reported.length > 0) {
        judgeFamilies.push(...reported);
      } else {
        // Claimed but no per-judge reports exposed — conservative: a non-confirming signal.
        judgeFamilies.push(null);
      }
    } else {
      judgeFamilies.push(null); // not confirmed → contributes a same-model signal
    }
  }
  log(`build-item: iteration ${iteration} verify ${verifyPass ? "PASS" : "CHANGES_REQUIRED/unavailable"}.`);

  // 4. QA flows — only when machine-checkable criteria exist. The qa.js child workflow drives the
  //    criteria against the running app; could-not-run is a FAILURE (fixable in-loop, never a
  //    silent skip). No criteria → the stage is reported-not-run, never silently absent.
  let qaGreenOrNA = true;
  if (criteria.length > 0) {
    phase(`iteration-${iteration}-qa`);
    let qaResult = null;
    try {
      qaResult = await workflow(
        { scriptPath: qaScript },
        qaChildArgs(item, repo, criteria, implementerFamily || builderFamily, iteration, stageTimeouts.qaBoot),
      );
    } catch (e) {
      log(`build-item: qa child workflow threw on iteration ${iteration}: ${e && e.message ? e.message : e}`);
      qaResult = null;
    }
    lastQa = qaGreen(qaResult);
    qaGreenOrNA = lastQa.green;
    if (qaResult && qaResult.crossModel) {
      // qa.js exposes only its folded string, not per-judge reports. A CONFIRMED qa fold
      // already required all-confirming different-family judges inside the child — it has no
      // family token to mirror, so it contributes NOTHING to the engine-level family fold
      // (never a manufactured token, never a false non-confirming null). Anything but
      // confirmed pushes the conservative non-confirming signal.
      if (qaResult.crossModel === "confirmed") {
        qaConfirmedCrossModel = true;
      } else {
        judgeFamilies.push(null);
      }
    }
    log(`build-item: iteration ${iteration} qa ${qaGreenOrNA ? "GREEN" : `RED (${lastQa.failures.length} failing)`}.`);
  } else {
    lastQa = null;
    log(`build-item: iteration ${iteration} — QA not run — no acceptance criteria on this item.`);
  }

  // 5. Decide — the priority-ordered nextAction (escalations were already returned above; this
  //    folds gates/verify/qa into green | cap-stop | fix).
  const decision = nextAction({
    iteration,
    maxIterations,
    gatesGreen: lastGates.green,
    verifyPass,
    qaGreenOrNA,
    irreversibleNeeded: null,
    newTier12: [],
  });

  if (decision === "green") {
    terminal = { status: "green" };
    break;
  }
  if (decision === "cap-stop") {
    const openFindings = lastVerify && Array.isArray(lastVerify.findings)
      ? lastVerify.findings.filter((f) => f && f.status !== "met")
      : [];
    terminal = {
      status: "not-green",
      residual: residualReport({
        iteration,
        failingGates: lastGates.failures,
        openFindings,
        failingCriteria: lastQa ? lastQa.failures : [],
      }),
    };
    break;
  }

  // decision === "fix": fold the residual into the next iteration's brief and loop.
  residual = foldResidual(lastGates, lastVerify, lastQa);
  log(`build-item: iteration ${iteration} not green — folding the residual into iteration ${iteration + 1}.`);
}

// The run-level cross-model claim, folded from the children's self-reports.
const crossModel = crossModelClaim(builderFamily, judgeFamilies);

// Assemble the terminal report. Every status below is a RETURN — the script never lands/pushes.
if (terminal == null) {
  // The loop ran to the cap without a terminal branch (defensive — nextAction would have set
  // cap-stop). Treat as not-green with the last residual so we never return a silent partial.
  const openFindings = lastVerify && Array.isArray(lastVerify.findings)
    ? lastVerify.findings.filter((f) => f && f.status !== "met")
    : [];
  terminal = {
    status: "not-green",
    residual: residualReport({
      iteration: iterationsUsed,
      failingGates: lastGates ? lastGates.failures : [],
      openFindings,
      failingCriteria: lastQa ? lastQa.failures : [],
    }),
  };
}

const base = {
  status: terminal.status,
  branch: branch,
  worktreePath: worktreePath,
  iterationsUsed,
  gates: lastGates ? { green: lastGates.green, failures: lastGates.failures } : null,
  verify: lastVerify ? { verdict: lastVerify.verdict, crossModel: lastVerify.crossModel } : null,
  qa: criteria.length > 0
    ? { ran: !!lastQa, green: lastQa ? lastQa.green : false, failures: lastQa ? lastQa.failures : [] }
    : { ran: false, reason: "QA not run — no acceptance criteria on this item" },
  qaConfirmedCrossModel,
  crossModel,
  summary: implementReport ? implementReport.summary : null,
};

if (terminal.status === "green") {
  return {
    ...base,
    // The honesty register, verbatim — never "proven correct", never a land claim. The before-land
    // pause is the ORCHESTRATOR's; this script returns green and stops.
    closeOut:
      "passed the deterministic gates and the reviewers' audit on this run — a reduction of unwatched-run risk, " +
      "never a substitute for the unbuilt deterministic trust-gates.",
  };
}
if (terminal.status === "not-green") {
  return {
    ...base,
    headline: "not green; here is the residual",
    residual: terminal.residual,
    note: "nothing partial landed — the branch is left for inspection, nothing merged.",
  };
}
if (terminal.status === "new-tier12") {
  return { ...base, newFindings: terminal.newFindings, note: "a finding outside this item surfaced — returned for re-triage, never folded silently into the item." };
}
if (terminal.status === "needs-irreversible") {
  return { ...base, irreversible: terminal.irreversible, note: "an irreversible action is needed — returned to the orchestrator; the script never performs it." };
}
// blocked
return { ...base, reason: terminal.reason, manualCriteria: terminal.manualCriteria || null };
