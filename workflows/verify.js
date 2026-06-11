// workflows/verify.js — the Stage-7 Verify panel as an executable Workflow script.
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped
// plugin install dir (`${CLAUDE_PLUGIN_ROOT}/workflows/verify.js`); this repo dogfoods it
// via the repo-local `./workflows/verify.js` (the working tree IS the plugin source).
// Never copied into an adopter repo (no managed-stamp/refresh surface) — see
// docs/DECISIONS.md → Harness v2.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps times after the
// run). Only the tool primitives `agent()`/`parallel()`/`phase()`/`log()`/`args`. Call
// count is structurally bounded by the roster — no loops. Pure decision logic lives in the
// marked `// --- helpers ---` block and is unit-tested by tests/workflows/verify.test.mjs
// (extract-and-eval), so the prose→script move tests the judgment, not just inspects it.

export const meta = {
  name: "verify",
  description:
    "Stage-7 Verify panel: diff-scoped lens fan-out + yagni + (trust-surface) honesty + architect synthesis with coded cross-model tagging",
};

// --- helpers ---
// Pure functions only — they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The judge model family, defined ONCE (single source of truth). Later scripts copy this
// block convention. A coded `model:` param is the wired cross-model spawn the prose used to
// uphold; the same-model TAG (below) stays the per-run honesty guard.
const MODELS = { judge: "opus" };

// The verbatim same-model disclosure tag. Defined once; never reconstructed by hand at a
// call site, so the wording cannot drift (honesty trust surface).
const SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// The 11 standards-catalog slugs. The script can't read the filesystem, so this literal is
// the source of truth here — and tests/workflows/verify.test.mjs pins it set-equal to the
// real docs/standards/*.md basenames (read via node:fs), killing list drift mechanically.
const KNOWN_MODULES = [
  "api-and-contracts",
  "data-and-persistence",
  "docs-traceability",
  "internationalization",
  "maintainability-structure",
  "observability-ops",
  "performance-efficiency",
  "product-ux",
  "reliability-resilience",
  "security",
  "testing",
];

// Validate the args contract at the boundary (fail loud — the caller throws on a non-empty
// list). Returns every shape error PLUS any dimension not in the catalog; empty array = valid.
function validateArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return ["args must be an object"];
  }
  const hasDiffRef = typeof args.diffRef === "string" && args.diffRef.length > 0;
  const hasFiles = Array.isArray(args.files) && args.files.length > 0;
  if (!hasDiffRef && !hasFiles) {
    errors.push("at least one of diffRef (non-empty string) or files (non-empty array) is required");
  }
  if (typeof args.specPath !== "string" || args.specPath.length === 0) {
    errors.push("specPath is required (non-empty string)");
  }
  if (!Array.isArray(args.dimensions) || args.dimensions.length === 0) {
    errors.push("dimensions is required (non-empty array of in-scope module slugs)");
  } else {
    for (const dim of args.dimensions) {
      if (!KNOWN_MODULES.includes(dim)) {
        errors.push(`unknown dimension '${dim}' — not a docs/standards/ module slug`);
      }
    }
  }
  if (typeof args.trustSurface !== "boolean") {
    errors.push("trustSurface is required (boolean — explicit decision at the boundary, never defaulted)");
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.length === 0) {
    errors.push("builderFamily is required (non-empty string — the family that authored the diff)");
  }
  return errors;
}

// Map validated dimension slugs to their module doc paths (assumes validated input).
function modulesFor(dimensions) {
  return dimensions.map((slug) => `docs/standards/${slug}.md`);
}

// Normalize a self-reported model family to a canonical lowercase token. First regex match
// wins; empty / unknown → null (conservative — degrades to the same-model tag, never to a
// false cross-model claim).
function modelFamily(report) {
  if (typeof report !== "string") {
    return null;
  }
  const match = report.match(/(fable|opus|sonnet|haiku)/i);
  return match ? match[1].toLowerCase() : null;
}

// The same-model disclosure decision. Returns the verbatim tag when the normalized families
// match OR either fails to resolve; null ONLY when both resolve and differ (the sole
// cross-model case). One rule, detection included.
function sameModelTag(builderFamily, judgeFamily) {
  const b = modelFamily(builderFamily);
  const j = modelFamily(judgeFamily);
  if (b === null || j === null) {
    return SAME_MODEL_TAG;
  }
  return b === j ? SAME_MODEL_TAG : null;
}

// Fold the judges' self-reports into the run's cross-model claim. `claimed` is true IFF the
// report list is non-empty AND sameModelTag is null for EVERY judge (a confirming
// different-family self-report from each). Otherwise claimed:false + the same-model tag.
function crossModelOutcome(builderFamily, judgeReports) {
  if (!Array.isArray(judgeReports) || judgeReports.length === 0) {
    return { claimed: false, tag: SAME_MODEL_TAG };
  }
  for (const report of judgeReports) {
    if (sameModelTag(builderFamily, report) !== null) {
      return { claimed: false, tag: SAME_MODEL_TAG };
    }
  }
  return { claimed: true, tag: null };
}

// The dedup identity for a gap finding: normalized `file:line` + lowercased dimension. Two
// lenses flagging the same line for the same dimension collide; distinct dimensions at one
// line stay separate.
function dedupKey(finding) {
  const fileLine = String(finding && finding.file_line != null ? finding.file_line : "")
    .trim()
    .replace(/\s+/g, "");
  const dimension = String(finding && finding.dimension != null ? finding.dimension : "")
    .trim()
    .toLowerCase();
  return `${fileLine}|${dimension}`;
}

// Merge duplicate gap findings across lenses: union of `sources` (the modules that flagged
// it), keep the FIRST concrete fix, and prefer `deterministic` confidence (a gate could
// prove it) over `judgment`. Preserves first-seen order.
function dedupFindings(findings) {
  const byKey = new Map();
  for (const finding of findings) {
    const key = dedupKey(finding);
    const source = finding.dimension;
    if (!byKey.has(key)) {
      const sources = [];
      if (source != null && source !== "") {
        sources.push(source);
      }
      byKey.set(key, {
        ...finding,
        sources,
      });
      continue;
    }
    const merged = byKey.get(key);
    if (source != null && source !== "" && !merged.sources.includes(source)) {
      merged.sources.push(source);
    }
    if ((merged.fix == null || merged.fix === "") && finding.fix != null && finding.fix !== "") {
      merged.fix = finding.fix;
    }
    if (merged.confidence !== "deterministic" && finding.confidence === "deterministic") {
      merged.confidence = "deterministic";
    }
  }
  return [...byKey.values()];
}

// Derive the panel roster from the validated args: one lens-reviewer per in-scope module,
// the yagni-sentinel, the honesty-reviewer IFF this is a trust surface (judge-pinned), and
// the architect-reviewer synthesis (judge-pinned). Logged up front and echoed in the result.
function panelRoster(args) {
  const roster = [];
  for (const modulePath of modulesFor(args.dimensions)) {
    roster.push({ role: `lens:${modulePath}`, agentType: "lens-reviewer" });
  }
  roster.push({ role: "yagni", agentType: "yagni-sentinel" });
  if (args.trustSurface) {
    roster.push({ role: "honesty", agentType: "honesty-reviewer", model: MODELS.judge });
  }
  roster.push({ role: "synthesis", agentType: "architect-reviewer", model: MODELS.judge });
  return roster;
}

// Normalize the args boundary. A scriptPath invocation delivers `args` as a JSON STRING
// (observed runtime behavior, 2026-06-11); an inline script may receive the object itself.
// Accept both; an unparseable string fails loud — never a silent empty-args run.
function parseArgs(raw) {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new Error("verify args: not valid JSON (" + (e && e.message ? e.message : e) + ")");
    }
  }
  return raw;
}

// Decide a judge spawn's outcome from its attempts — PURE so the retry contract is
// unit-testable. An attempt is { out } (out === null counts as failure: agent() returns null
// on skip/terminal error) or { out: null, err }. First success → cross-model eligible;
// retry success → forcedSameModel; first failure with no retry yet → { needRetry: true };
// both failed → throw. Never a silent partial PASS.
function judgeOutcome(role, agentType, first, second) {
  if (first && first.out != null) return { out: first.out, forcedSameModel: false };
  if (second === undefined) return { needRetry: true };
  if (second && second.out != null) return { out: second.out, forcedSameModel: true };
  const firstErr = first && first.err ? first.err : "null return (skipped or terminal error)";
  const secondErr = second && second.err ? second.err : "null return (skipped or terminal error)";
  throw new Error(
    `verify panel: judge '${role}' (${agentType}) failed twice — first: ${firstErr}; ` +
      `respawn (no model override): ${secondErr}. Never a silent partial PASS.`,
  );
}

// Panel-coverage honesty: a lens that returned null/unusable output (skipped or errored) must
// surface as an explicit could-not-run GAP — an unrun review must never read as a clean
// dimension. Returns one deterministic gap finding per unrun module; empty when all ran.
function coverageGaps(lensReturns, modulePaths) {
  const gaps = [];
  modulePaths.forEach((modulePath, i) => {
    const r = lensReturns[i];
    if (!r || !Array.isArray(r.findings)) {
      gaps.push({
        dimension: modulePath,
        status: "gap",
        fix:
          "lens did not run (no usable return) — this module was NOT audited; re-run the panel. " +
          "An unrun lens is never treated as clean.",
        file_line: "(panel coverage)",
        confidence: "deterministic",
        plain_english:
          `The ${modulePath} reviewer never reported back, so that part of the review did not ` +
          "happen — it must be re-run, not assumed fine.",
      });
    }
  });
  return gaps;
}

// Split the ordered parallel() results back into panel roles. parallel() preserves INPUT
// ORDER (each thunk's result lands at its input index) — this helper pins that arithmetic
// behind a unit test instead of leaving it inline on an undocumented primitive contract.
function splitPanelResults(panelResults, lensCount, hasHonesty) {
  return {
    lensReturns: panelResults.slice(0, lensCount),
    yagni: panelResults[lensCount],
    honestyJudge: hasHonesty ? panelResults[lensCount + 1] : null,
  };
}

// Structured-output schemas as JSON Schema object literals (no imports). The Workflow tool
// validates each agent's structured output against these at the tool-call layer.
const LENS_SCHEMA = {
  type: "object",
  required: ["verdict", "findings"],
  properties: {
    verdict: { type: "string", enum: ["CLEAN", "GAPS"] },
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["dimension", "status", "fix", "file_line", "confidence", "plain_english"],
        properties: {
          dimension: { type: "string" },
          status: { type: "string", enum: ["met", "gap"] },
          fix: { type: "string" },
          file_line: { type: "string" },
          confidence: { type: "string", enum: ["deterministic", "judgment"] },
          plain_english: { type: "string" },
        },
      },
    },
  },
};

const YAGNI_SCHEMA = {
  type: "object",
  required: ["verdict", "cuts"],
  properties: {
    verdict: { type: "string", enum: ["PROPORTIONATE", "OVER-BUILT"] },
    cuts: {
      type: "array",
      items: {
        type: "object",
        required: ["what", "why_not_now"],
        properties: {
          what: { type: "string" },
          why_not_now: { type: "string" },
          where_instead: { type: "string" },
        },
      },
    },
  },
};

const HONESTY_SCHEMA = {
  type: "object",
  required: ["reported_model_family", "verdict", "findings"],
  properties: {
    reported_model_family: { type: "string" },
    verdict: { type: "string", enum: ["CLEAN", "OVERCLAIMS"] },
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["claim", "file_line", "why", "severity"],
        properties: {
          claim: { type: "string" },
          file_line: { type: "string" },
          why: { type: "string" },
          rewrite: { type: "string" },
          severity: { type: "string", enum: ["blocking", "should-fix", "nit"] },
        },
      },
    },
  },
};

const SYNTHESIS_SCHEMA = {
  type: "object",
  required: ["reported_model_family", "verdict", "findings", "missed_dimensions", "dod_check", "plain_english_summary"],
  properties: {
    reported_model_family: { type: "string" },
    verdict: { type: "string", enum: ["PASS", "CHANGES_REQUIRED"] },
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["dimension", "status", "fix", "file_line"],
        properties: {
          dimension: { type: "string" },
          status: { type: "string", enum: ["met", "gap"] },
          fix: { type: "string" },
          file_line: { type: "string" },
        },
      },
    },
    missed_dimensions: { type: "array", items: { type: "string" } },
    dod_check: { type: "string" },
    plain_english_summary: { type: "string" },
  },
};
// --- end helpers ---

// Spawn a judge with the cross-model `model:` pin; one respawn without it on failure
// (force-tagged same-model); the decision logic lives in the PURE judgeOutcome helper.
async function spawnJudge(role, agentType, prompt, schema) {
  const attempt = async (opts) => {
    try {
      return { out: await agent(prompt, opts) };
    } catch (e) {
      return { out: null, err: e && e.message ? e.message : String(e) };
    }
  };
  const first = await attempt({ agentType, model: MODELS.judge, schema, label: role });
  let decision = judgeOutcome(role, agentType, first);
  if (decision.needRetry) {
    const second = await attempt({ agentType, schema, label: `${role}:respawn` });
    decision = judgeOutcome(role, agentType, first, second);
  }
  return decision;
}

// ── Top-level control flow (Workflow scripts run in an async context; no module wrapper). ──

// Validate at the boundary — fail loud with the full error list.
const input = parseArgs(args);
{
  const errors = validateArgs(input);
  if (errors.length > 0) {
    throw new Error(`verify args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

const roster = panelRoster(input);
const modulesAudited = modulesFor(input.dimensions);
log(`verify panel roster (${roster.length} roles): ${roster.map((r) => r.role).join(", ")}`);

const diffScope = input.diffRef ? `diffRef=${input.diffRef}` : `files=${JSON.stringify(input.files)}`;

// --- Panel phase: one lens per module + yagni + (trust-surface) honesty, in parallel. ---
phase("Panel");
const lensTasks = modulesAudited.map((modulePath) => () =>
  agent(
    `Verify-diff mode. Your lens is the standards module: ${modulePath}. ` +
      `Audit the change against that module's dimensions only. ` +
      `Diff scope: ${diffScope}. ` +
      `Spec: ${input.specPath}.`,
    { agentType: "lens-reviewer", schema: LENS_SCHEMA, label: `lens:${modulePath}`, phase: "Panel" },
  ),
);

const panelTasks = [
  ...lensTasks,
  () =>
    agent(
      `Argue this change is too much. Diff scope: ${diffScope}. ` +
        `Spec: ${input.specPath}. Return a cut-list of over-build with where-instead.`,
      { agentType: "yagni-sentinel", schema: YAGNI_SCHEMA, label: "yagni", phase: "Panel" },
    ),
];

// The honesty reviewer (trust-surface only) is a JUDGE — it fans out in the same panel,
// but via spawnJudge so it carries the model: pin + the one-respawn-on-error contract.
const hasHonesty = input.trustSurface === true;
if (hasHonesty) {
  panelTasks.push(() =>
    spawnJudge(
      "honesty",
      "honesty-reviewer",
      `Refute the CHANGED COPY only (docs/agent/tree prose in this diff) for over-claim. ` +
        `Open with RUNNING AS: <model family> and report it in reported_model_family. ` +
        `Diff scope: ${diffScope}. ` +
        `Spec: ${input.specPath}.`,
      HONESTY_SCHEMA,
    ),
  );
}

const panelResults = await parallel(panelTasks);
// parallel() preserves input order; splitPanelResults pins the index arithmetic (tested).
// spawnJudge returns { out, forcedSameModel }; a forced respawn counts as same-model.
const { lensReturns, yagni, honestyJudge } = splitPanelResults(
  panelResults,
  lensTasks.length,
  hasHonesty,
);
const honesty = honestyJudge ? honestyJudge.out : null;
const honestyReportedFamily =
  honestyJudge && !honestyJudge.forcedSameModel && honestyJudge.out
    ? honestyJudge.out.reported_model_family
    : null;

// Dedup the lens GAP findings in code (across-lens duplicate gaps collapse to one).
const lensGaps = [];
for (const lensReturn of lensReturns) {
  const findings = lensReturn && Array.isArray(lensReturn.findings) ? lensReturn.findings : [];
  for (const finding of findings) {
    if (finding && finding.status === "gap") {
      lensGaps.push(finding);
    }
  }
}
const unrunGaps = coverageGaps(lensReturns, modulesAudited);
const dedupedFindings = dedupFindings([...lensGaps, ...unrunGaps]);
const panelDegraded = unrunGaps.length > 0 || yagni == null;

// --- Synthesis phase: architect-reviewer over the deduped findings + yagni + honesty. ---
phase("Synthesis");
const synthesisResult = await spawnJudge(
  "synthesis",
  "architect-reviewer",
  `Synthesizer mode. Consolidate the panel into one verdict. ` +
    `Open with RUNNING AS: <model family> and report it in reported_model_family. ` +
    `Deduped lens findings: ${JSON.stringify(dedupedFindings)}. ` +
    `Yagni cut-list: ${JSON.stringify(yagni)}. ` +
    `Honesty findings: ${JSON.stringify(honesty)}. ` +
    `Spec: ${input.specPath}. Diff scope: ${diffScope}. ` +
    `Run the Definition-of-Done check; flag any relevant dimension the spec missed.`,
  SYNTHESIS_SCHEMA,
);
const synthesis = synthesisResult.out;

// Compute the cross-model claim in code from the judges' self-reports. A respawn forced to
// the default model is treated as same-model (no confirming different-family report).
const judges = [];
if (input.trustSurface) {
  judges.push({ role: "honesty", reportedFamily: honestyReportedFamily });
}
judges.push({
  role: "synthesis",
  reportedFamily: synthesisResult.forcedSameModel ? null : synthesis ? synthesis.reported_model_family : null,
});
const crossModel = crossModelOutcome(
  input.builderFamily,
  judges.map((j) => j.reportedFamily),
);

return {
  // The script never overrides judgment — the verdict is passed through from synthesis.
  verdict: synthesis ? synthesis.verdict : "CHANGES_REQUIRED",
  crossModel: { claimed: crossModel.claimed, tag: crossModel.tag, judges },
  findings: synthesis ? synthesis.findings : [],
  yagni: yagni == null ? { couldNotRun: true } : yagni,
  panelDegraded,
  honesty: input.trustSurface ? honesty : { skipped: "trustSurface=false" },
  panel: roster,
  modulesAudited,
};
