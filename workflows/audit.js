// workflows/audit.js — the audit pipeline (FIND -> PRUNE -> VERIFY) as an executable
// Workflow script. Slice 3a: `quick` + `standard` only (`thorough` is rejected at the
// boundary and routes to the prose path until Slice 3b adds its stages).
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped plugin
// install dir (`${CLAUDE_PLUGIN_ROOT}/workflows/audit.js`); this repo dogfoods it via the
// repo-local `./workflows/audit.js` (the working tree IS the plugin source). Never copied into
// an adopter repo (no managed-stamp/refresh surface) — see docs/DECISIONS.md -> Harness v2.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps dates AFTER the run —
// the script returns no timestamps). Only the tool primitives `agent()`/`parallel()`/
// `phase()`/`log()`/`args`. Pure decision logic lives in the marked `// --- helpers ---` block
// and is unit-tested by tests/workflows/audit.test.mjs (extract-and-eval), so the prose->script
// move tests the judgment, not just inspects it.
//
// The headline guarantee this script makes mechanical: exactly ONE finding-verifier per
// surviving finding (the prose's "re-check every finding" claim), with the cross-model judge
// pinned as a literal `model:` parameter.

export const meta = {
  name: "audit",
  description:
    "Audit pipeline (FIND -> PRUNE -> VERIFY) as a Workflow script: lens fan-out per (module x dir) cell at the dialed depth, coded dedup, synthesis self-review prune (the test-baseline item never pruned), exactly one finding-verifier per surviving finding (judge-pinned cross-model), deterministic budget cap + resume. quick/standard only (thorough -> prose path until Slice 3b).",
};

// --- helpers ---
// Pure functions only — they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The judge model family, defined ONCE (single source of truth). Copied verbatim from
// verify.js (Slice 2) — the shared cross-model contract. A coded `model:` param is the wired
// cross-model spawn the prose used to uphold; the same-model TAG (below) stays the per-run
// honesty guard.
const MODELS = { judge: "opus" };

// The verbatim same-model disclosure tag. Defined once; never reconstructed by hand at a call
// site, so the wording cannot drift (honesty trust surface). Copied verbatim from verify.js.
const SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// The dial -> depth ladder (one map, complete for all three notches). The ALLOWED-dial set is
// the boundary check (validateArgs); the map itself is total so depthForDial never returns
// undefined for a valid dial.
const DEPTH_FOR_DIAL = { quick: "focused", standard: "deep", thorough: "exhaustive" };

// The dials this script SUPPORTS end-to-end. `thorough` is a known dial (in the depth map) but
// not yet a supported run — Slice 3b adds its stages; until then the skill runs it on the prose
// path. The boundary rejects it with a message that names Slice 3b.
const SUPPORTED_DIALS = ["quick", "standard"];

// The class of the script-synthesized "establish a test baseline" item. A finding with this
// findingKey can NEVER be pruned (applyPrune enforces it) — a partial/right-sized audit must
// never green-light an unguarded refactor.
const TEST_BASELINE_CLASS = "missing-test-baseline";

// Validate the args contract at the boundary (fail loud — the caller throws on a non-empty
// list). Returns every shape error; empty array = valid. `thorough` is rejected with the exact
// not-yet-supported message naming Slice 3b (the headline 3a boundary).
function validateArgs(args) {
  const errors = [];
  if (!args || typeof args !== "object") {
    return ["args must be an object"];
  }
  if (typeof args.dial !== "string" || !SUPPORTED_DIALS.includes(args.dial)) {
    if (args.dial === "thorough") {
      errors.push(
        "dial 'thorough' is not supported by this script yet — Slice 3b adds thorough; the skill runs thorough via the prose path until then",
      );
    } else {
      errors.push(
        `dial '${args.dial}' is not supported by this script yet — Slice 3b adds thorough; the skill runs thorough via the prose path until then`,
      );
    }
  }
  if (!Array.isArray(args.modules) || args.modules.length === 0) {
    errors.push("modules is required (non-empty array of standards-module names)");
  } else if (!args.modules.every((m) => typeof m === "string" && m.length > 0)) {
    errors.push("modules must be an array of non-empty strings");
  }
  if (!Array.isArray(args.scopeDirs) || args.scopeDirs.length === 0) {
    errors.push("scopeDirs is required (non-empty array of prioritized directories)");
  } else if (!args.scopeDirs.every((d) => typeof d === "string" && d.length > 0)) {
    errors.push("scopeDirs must be an array of non-empty strings");
  }
  if (args.excludeSet !== undefined && !Array.isArray(args.excludeSet)) {
    errors.push("excludeSet, when provided, must be an array of strings");
  }
  if (
    typeof args.maxCellsPerRun !== "number" ||
    !Number.isInteger(args.maxCellsPerRun) ||
    args.maxCellsPerRun <= 0
  ) {
    errors.push("maxCellsPerRun is required (positive integer — the deterministic cap)");
  }
  if (args.doneCells !== undefined && !Array.isArray(args.doneCells)) {
    errors.push("doneCells, when provided, must be an array of cell keys");
  }
  if (args.deferredFindings !== undefined && !Array.isArray(args.deferredFindings)) {
    errors.push("deferredFindings, when provided, must be an array of findings");
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.length === 0) {
    errors.push("builderFamily is required (non-empty string — the orchestrator's model family)");
  }
  return errors;
}

// The dial -> depth map (assumes a validated dial; total over the three notches).
function depthForDial(dial) {
  return DEPTH_FOR_DIAL[dial];
}

// Map a validated module name to its standards doc path (assumes validated input).
function modulePath(moduleName) {
  return `docs/standards/${moduleName}.md`;
}

// The exact cell-key token format the fence's done-cells / pending-cells lists carry — this is
// the resume contract with the SKILL. `<module>x<dir>` (a literal multiplication sign).
function cellKey(moduleName, dir) {
  return `${moduleName}×${dir}`;
}

// Enumerate the pending cells: module x prioritized dir, in (module, dir) order, MINUS any cell
// already in doneCells (never re-enumerated). Returns ordered cell keys.
function enumerateCells(modules, scopeDirs, doneCells) {
  const done = new Set(Array.isArray(doneCells) ? doneCells : []);
  const cells = [];
  for (const moduleName of modules) {
    for (const dir of scopeDirs) {
      const key = cellKey(moduleName, dir);
      if (!done.has(key)) {
        cells.push(key);
      }
    }
  }
  return cells;
}

// Split the ordered pending cells against the per-run cap: the first N run this pass, the rest
// overflow to a resume run. The single deterministic cap (the platform `budget` primitive, where
// supported, is a backstop only — never the resume contract).
function applyCellBudget(cells, maxCellsPerRun) {
  return {
    run: cells.slice(0, maxCellsPerRun),
    overflow: cells.slice(maxCellsPerRun),
  };
}

// Parse a cell key back into its module + dir parts (split on the first multiplication sign;
// dirs may themselves contain one, so only the first separator is structural).
function parseCellKey(key) {
  const i = key.indexOf("×");
  if (i < 0) {
    return { module: key, dir: "" };
  }
  return { module: key.slice(0, i), dir: key.slice(i + 1) };
}

// Group this run's cells into one batch per module over its scoped dirs (the fan-out unit — one
// lens-reviewer per module batch). Preserves first-seen module order; dirs in cell order.
function groupByModule(runCells) {
  const byModule = new Map();
  for (const key of runCells) {
    const { module, dir } = parseCellKey(key);
    if (!byModule.has(module)) {
      byModule.set(module, { module, dirs: [], cells: [] });
    }
    const batch = byModule.get(module);
    batch.dirs.push(dir);
    batch.cells.push(key);
  }
  return [...byModule.values()];
}

// Normalize an issue-class string: lowercase, trim, collapse internal whitespace to single
// hyphens. The deterministic dedup identity is derived from this (synonym slugs that differ
// after normalization stay distinct — semantic dedup is the synthesis agent's job).
function normalizeIssueClass(s) {
  return String(s == null ? "" : s)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-");
}

// The dedup key AND the finding's id: the normalized issueClass. Two findings of the same KIND
// of problem collide regardless of location; distinct classes at one file:line stay separate.
function findingKey(finding) {
  return normalizeIssueClass(finding && finding.issueClass);
}

// Merge same-key findings across lenses: union of `locations` (the "recurs in N files" roll-up),
// WEAKEST confidence wins (any `judgment` member => merged finding is `judgment`, never
// upgraded), keep the first concrete claim/fix. Distinct classes stay separate. Preserves
// first-seen order. Each merged finding carries its computed `findingKey`.
function dedupFindings(findings) {
  const byKey = new Map();
  for (const finding of findings) {
    const key = findingKey(finding);
    const incomingLocations = Array.isArray(finding.locations) ? finding.locations : [];
    if (!byKey.has(key)) {
      byKey.set(key, {
        ...finding,
        findingKey: key,
        locations: [...incomingLocations],
      });
      continue;
    }
    const merged = byKey.get(key);
    for (const loc of incomingLocations) {
      if (!merged.locations.includes(loc)) {
        merged.locations.push(loc);
      }
    }
    if ((merged.fix == null || merged.fix === "") && finding.fix != null && finding.fix !== "") {
      merged.fix = finding.fix;
    }
    if (
      (merged.claimTechnical == null || merged.claimTechnical === "") &&
      finding.claimTechnical != null &&
      finding.claimTechnical !== ""
    ) {
      merged.claimTechnical = finding.claimTechnical;
    }
    if (
      (merged.claimPlain == null || merged.claimPlain === "") &&
      finding.claimPlain != null &&
      finding.claimPlain !== ""
    ) {
      merged.claimPlain = finding.claimPlain;
    }
    // Weakest confidence wins: a `judgment` member downgrades the merged finding; once
    // judgment, it never upgrades back to deterministic.
    if (finding.confidence === "judgment") {
      merged.confidence = "judgment";
    }
  }
  return [...byKey.values()];
}

// Apply the synthesis cut-list — drops every cut key EXCEPT a finding whose findingKey ===
// TEST_BASELINE_CLASS (the script-enforced never-prune-the-test-baseline exception). A cut
// targeting the test-baseline item is silently ignored, not honored.
function applyPrune(findings, cuts) {
  const cutKeys = new Set(
    (Array.isArray(cuts) ? cuts : [])
      .map((c) => (c && c.findingKey != null ? normalizeIssueClass(c.findingKey) : null))
      .filter((k) => k !== null),
  );
  return findings.filter((finding) => {
    const key = findingKey(finding);
    if (key === TEST_BASELINE_CLASS) {
      return true; // never pruned, whatever the cut-list says
    }
    return !cutKeys.has(key);
  });
}

// Map module names -> doc paths for a lens prompt (assumes validated input).
function modulesToPaths(modules) {
  return modules.map(modulePath);
}

// Build the audit-scope lens prompt (per .claude/agents/lens-reviewer.md): the module path, the
// scoped dirs, the exclude-set, and the depth word. Audit-scope mode — there is NO diff.
function buildLensPrompt(moduleName, dirs, excludeSet, depth) {
  const exclude = Array.isArray(excludeSet) ? excludeSet : [];
  return (
    `Audit-scope mode (no diff). Your lens is the standards module: ${modulePath(moduleName)}. ` +
    `Audit the existing code in this scope against that module's dimensions only. ` +
    `Scope (prioritized dirs/packages): ${JSON.stringify(dirs)}. ` +
    `Exclude-set (never read — deps, build output, secrets): ${JSON.stringify(exclude)}. ` +
    `Read at depth: ${depth}. ` +
    `Return per-issue findings: issueClass, claimPlain, claimTechnical, locations (file:line list), ` +
    `fix, confidence (deterministic|judgment).`
  );
}

// Build the synthesis prompt: consolidate -> tier (1|2|3) + exactly one of the five tags +
// plain-English title/why/impact-effort per item -> a YAGNI right-size cut list with reasons
// (incl. "duplicate of <key>" cuts). ADD one missing-test-baseline Tier-1 item ONLY when the
// inputs show untested behavior-bearing code and none exists; NEVER manufacture a finding to
// fill a tier. This is the prose's quick/standard "synthesis self-review", delegated.
function buildSynthesisPrompt(dedupedFindings, modules, scopeDirs) {
  return (
    `Synthesis self-review of an audit. Consolidate these deduped findings into a tiered, tagged ` +
    `backlog set and right-size it (YAGNI — keep only findings with real impact; cut marginal ` +
    `nice-to-haves; never manufacture a finding to fill a tier). ` +
    `For each kept finding return: findingKey (the issueClass), tier (1|2|3), tag (exactly one of ` +
    `refactor|capability-upgrade|dependency-health|bug|feature), titlePlain, whyPlain, impactEffort. ` +
    `Return a cuts list of { findingKey, reason } for everything you drop (use reason "duplicate of <key>" ` +
    `for semantic duplicates the coded dedup missed). ` +
    `ADD one item with findingKey "${TEST_BASELINE_CLASS}" at tier 1 ONLY IF the audited code is ` +
    `behavior-bearing and untested and no test baseline exists — otherwise do not add it. ` +
    `Audited modules: ${JSON.stringify(modules)}. Scope: ${JSON.stringify(scopeDirs)}. ` +
    `Deduped findings: ${JSON.stringify(dedupedFindings)}.`
  );
}

// Build the finding-verifier's CLEAN-CONTEXT input. Returns ONLY the contract keys — the
// independence of .claude/agents/finding-verifier.md is preserved STRUCTURALLY: the builder
// cannot emit rationale/transcript fields (any extra fields on the finding are dropped here).
function buildVerifierInput(finding, excludeSet) {
  return {
    claimPlain: finding && finding.claimPlain != null ? finding.claimPlain : "",
    claimTechnical: finding && finding.claimTechnical != null ? finding.claimTechnical : "",
    locations: finding && Array.isArray(finding.locations) ? finding.locations : [],
    sourceModule:
      finding && finding.sourceModule != null
        ? finding.sourceModule
        : finding && Array.isArray(finding.modules) && finding.modules.length > 0
          ? finding.modules[0]
          : "",
    confidence: finding && finding.confidence != null ? finding.confidence : "judgment",
    excludeSet: Array.isArray(excludeSet) ? excludeSet : [],
  };
}

// Build the verifier prompt from the clean-context input (refute-first posture; demands the
// RUNNING AS self-report). NEVER includes the finder's rationale.
function buildVerifierPrompt(input) {
  return (
    `Independently REFUTE this single audit finding against the actual code (refute-first; ` +
    `clean context — you are NOT given the finder's rationale). ` +
    `Open your response with "RUNNING AS: <model family>" and report it in runningAs. ` +
    `Claim (plain): ${input.claimPlain}. Claim (technical): ${input.claimTechnical}. ` +
    `Locations: ${JSON.stringify(input.locations)}. Source module: ${input.sourceModule}. ` +
    `Finder's confidence label: ${input.confidence}. ` +
    `Exclude-set (never read): ${JSON.stringify(input.excludeSet)}. ` +
    `Return verdict (Verified|Refuted|Unconfirmed), evidence, plainLine.`
  );
}

// The same-model disclosure decision — copied verbatim from verify.js. Returns the verbatim tag
// when families match OR either fails to resolve; null ONLY when both resolve and differ (the
// sole cross-model case).
function modelFamily(report) {
  if (typeof report !== "string") {
    return null;
  }
  const match = report.match(/(fable|opus|sonnet|haiku)/i);
  return match ? match[1].toLowerCase() : null;
}

function sameModelTag(builderFamily, judgeFamily) {
  const b = modelFamily(builderFamily);
  const j = modelFamily(judgeFamily);
  if (b === null || j === null) {
    return SAME_MODEL_TAG;
  }
  return b === j ? SAME_MODEL_TAG : null;
}

// Apply the verifier verdicts to the surviving findings. Mapping (the only representable states
// are verified / unconfirmed / deferred — NEVER a silent "checked"):
//   Verified   -> kept, verification.state = 'verified'   + evidence
//   Unconfirmed-> kept, verification.state = 'unconfirmed'
//   Refuted    -> dropped (counted in refutedCount; its only trace is the count)
//   no verdict -> kept, verification.state = 'deferred'   (budget ran out / verifier never ran)
// `results` is a parallel array aligned to `findings` (results[i] verifies findings[i]); a
// missing/null result is the deferred case (the verifier did not run).
function applyVerdicts(findings, results) {
  const kept = [];
  let refutedCount = 0;
  findings.forEach((finding, i) => {
    const result = Array.isArray(results) ? results[i] : undefined;
    const verdict = result && result.verdict ? result.verdict : null;
    if (verdict === "Refuted") {
      refutedCount += 1;
      return; // dropped — false positive caught before the backlog
    }
    let verification;
    if (verdict === "Verified") {
      verification = {
        state: "verified",
        evidence: result && result.evidence != null ? result.evidence : "",
        plainLine: result && result.plainLine != null ? result.plainLine : "",
      };
    } else if (verdict === "Unconfirmed") {
      verification = {
        state: "unconfirmed",
        evidence: result && result.evidence != null ? result.evidence : "",
        plainLine: result && result.plainLine != null ? result.plainLine : "",
      };
    } else {
      // No usable verdict — the verifier did not run (budget exhausted / null return).
      verification = {
        state: "deferred",
        evidence: "",
        plainLine: "not yet verified — re-run to confirm",
      };
    }
    kept.push({
      ...finding,
      verification,
      // The verifier's own self-report rides WITH the finding — verificationSummary must never
      // index a parallel results array (a Refuted finding's removal would misalign it; the
      // 2026-06-11 dogfood audit reproduced a false cross-model claim from exactly that).
      verifierRunningAs: result && result.runningAs != null ? result.runningAs : null,
    });
  });
  return { kept, refutedCount };
}

// Fold the verifier results into the run's verification summary. `crossModel` is true ONLY when
// EVERY verifier returned a confirming self-report of a different family (sameModelTag null for
// each AND every finding got a result) — the run claims cross-model only then; otherwise it
// carries the verbatim same-model tag. Counts the kept verification states + the refuted drops.
function verificationSummary(findings, refutedCount, builderFamily) {
  let verified = 0;
  let unconfirmed = 0;
  let deferred = 0;
  let allConfirmingDifferentFamily = findings.length > 0;
  findings.forEach((finding) => {
    const v = finding && finding.verification ? finding.verification.state : null;
    if (v === "verified") verified += 1;
    else if (v === "unconfirmed") unconfirmed += 1;
    else deferred += 1;
    const reported = finding && finding.verifierRunningAs != null ? finding.verifierRunningAs : null;
    if (reported === null || sameModelTag(builderFamily, reported) !== null) {
      allConfirmingDifferentFamily = false;
    }
  });
  const crossModel = allConfirmingDifferentFamily;
  return {
    verified,
    unconfirmed,
    deferred,
    refuted: refutedCount,
    crossModel,
    sameModelTag: crossModel ? null : SAME_MODEL_TAG,
  };
}

// The run's COMPLETE/PARTIAL status, derived from the pending-cell list (the resume contract).
function runStatus(pendingCells) {
  return Array.isArray(pendingCells) && pendingCells.length > 0 ? "PARTIAL" : "COMPLETE";
}

// Normalize the args boundary — copied verbatim from verify.js. A scriptPath invocation delivers
// `args` as a JSON STRING (observed runtime behavior, 2026-06-11); an inline script may receive
// the object itself. Accept both; an unparseable string fails loud — never a silent empty-args run.
function parseArgs(raw) {
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new Error("audit args: not valid JSON (" + (e && e.message ? e.message : e) + ")");
    }
  }
  return raw;
}

// Structured-output schemas as JSON Schema object literals (no imports). The Workflow tool
// validates each agent's structured output against these at the tool-call layer.
const LENS_SCHEMA = {
  type: "object",
  required: ["lensVerdict", "findings"],
  properties: {
    lensVerdict: { type: "string", enum: ["CLEAN", "GAPS"] },
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["issueClass", "claimPlain", "claimTechnical", "locations", "fix", "confidence"],
        properties: {
          issueClass: { type: "string" },
          claimPlain: { type: "string" },
          claimTechnical: { type: "string" },
          locations: { type: "array", items: { type: "string" } },
          fix: { type: "string" },
          confidence: { type: "string", enum: ["deterministic", "judgment"] },
        },
      },
    },
  },
};

const SYNTHESIS_SCHEMA = {
  type: "object",
  required: ["items", "cuts"],
  properties: {
    items: {
      type: "array",
      items: {
        type: "object",
        required: ["findingKey", "tier", "tag", "titlePlain", "whyPlain", "impactEffort"],
        properties: {
          findingKey: { type: "string" },
          tier: { type: "integer", enum: [1, 2, 3] },
          tag: {
            type: "string",
            enum: ["refactor", "capability-upgrade", "dependency-health", "bug", "feature"],
          },
          titlePlain: { type: "string" },
          whyPlain: { type: "string" },
          impactEffort: { type: "string" },
        },
      },
    },
    cuts: {
      type: "array",
      items: {
        type: "object",
        required: ["findingKey", "reason"],
        properties: {
          findingKey: { type: "string" },
          reason: { type: "string" },
        },
      },
    },
  },
};

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

// Apply the synthesis agent's tier/tag/plain-English item metadata onto a kept finding, by
// findingKey. A finding the synthesis did not annotate keeps conservative defaults (tier 2,
// refactor) — never silently dropped here (the cut-list is the only drop path, via applyPrune).
function applySynthesisItems(findings, items) {
  const byKey = new Map(
    (Array.isArray(items) ? items : []).map((it) => [normalizeIssueClass(it.findingKey), it]),
  );
  return findings.map((finding) => {
    const it = byKey.get(findingKey(finding));
    return {
      ...finding,
      tier: it && it.tier != null ? it.tier : 2,
      tag: it && it.tag != null ? it.tag : "refactor",
      titlePlain: it && it.titlePlain != null ? it.titlePlain : finding.claimPlain || "",
      whyPlain: it && it.whyPlain != null ? it.whyPlain : "",
      impactEffort: it && it.impactEffort != null ? it.impactEffort : "",
    };
  });
}

// Shape a kept+verified finding into the Phase-3 return item contract (the renderer in Slice 3b
// consumes this; 3a returns the structured object, the orchestrator renders the fence).
function toResultItem(finding) {
  return {
    findingKey: findingKey(finding),
    modules: Array.isArray(finding.modules)
      ? finding.modules
      : finding.sourceModule != null
        ? [finding.sourceModule]
        : [],
    tier: finding.tier,
    tag: finding.tag,
    titlePlain: finding.titlePlain != null ? finding.titlePlain : "",
    claimTechnical: finding.claimTechnical != null ? finding.claimTechnical : "",
    locations: Array.isArray(finding.locations) ? finding.locations : [],
    whyPlain: finding.whyPlain != null ? finding.whyPlain : "",
    impactEffort: finding.impactEffort != null ? finding.impactEffort : "",
    confidence: finding.confidence != null ? finding.confidence : "judgment",
    verification: finding.verification,
  };
}
// --- end helpers ---

// Spawn a judge (finding-verifier) with the cross-model `model:` pin; one respawn without it on
// failure (the result then can't confirm a different family -> the run carries the same-model
// tag); on a second failure the finding is marked deferred (never a silent skip). The verifier
// fan-out scales with findings, not files, so this stays cheap.
async function spawnVerifier(input) {
  const prompt = buildVerifierPrompt(input);
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
    label: `verify:${input.sourceModule}`,
    phase: "Verify",
  });
  if (first.out != null) {
    return first.out;
  }
  const second = await attempt({
    agentType: "finding-verifier",
    schema: VERIFIER_SCHEMA,
    label: `verify:${input.sourceModule}:respawn`,
    phase: "Verify",
  });
  if (second.out != null) {
    // Forced no-override respawn: drop the self-report so it can't claim a different family.
    return { ...second.out, runningAs: "" };
  }
  // Both attempts failed — mark the finding deferred (honest no-silent-skip).
  return null;
}

// ── Top-level control flow (Workflow scripts run in an async context; no module wrapper). ──

// Validate at the boundary — fail loud with the full error list.
const input = parseArgs(args);
{
  const errors = validateArgs(input);
  if (errors.length > 0) {
    throw new Error(`audit args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

const dial = input.dial;
const depth = depthForDial(dial);
const excludeSet = Array.isArray(input.excludeSet) ? input.excludeSet : [];
const doneCellsIn = Array.isArray(input.doneCells) ? input.doneCells : [];
const deferredFindings = Array.isArray(input.deferredFindings) ? input.deferredFindings : [];

// Enumerate the pending cells, then split against the per-run cap (the deterministic resume).
const pending = enumerateCells(input.modules, input.scopeDirs, doneCellsIn);
const { run: runCells, overflow: overflowCells } = applyCellBudget(pending, input.maxCellsPerRun);
const batches = groupByModule(runCells);
log(
  `audit dial=${dial} depth=${depth} — ${runCells.length} cell(s) this run across ` +
    `${batches.length} module batch(es); ${overflowCells.length} deferred to resume.`,
);

// --- FIND: one lens-reviewer per module batch at the dialed depth, in parallel. ---
phase("Find");
const findTasks = batches.map((batch) => () =>
  agent(buildLensPrompt(batch.module, batch.dirs, excludeSet, depth), {
    agentType: "lens-reviewer",
    schema: LENS_SCHEMA,
    label: `lens:${batch.module}`,
    phase: "Find",
  }),
);
const findResults = await parallel(findTasks);

// A batch that errored (null return) sends its cells to pendingCells — never a silent skip; the
// run goes PARTIAL. Surviving batches contribute their findings, each tagged with its module.
const failedCells = [];
const rawFindings = [];
batches.forEach((batch, i) => {
  const r = findResults[i];
  if (!r || !Array.isArray(r.findings)) {
    log(`lens batch '${batch.module}' did not run (no usable return) — its cells go pending.`);
    for (const cell of batch.cells) {
      failedCells.push(cell);
    }
    return;
  }
  for (const finding of r.findings) {
    rawFindings.push({ ...finding, sourceModule: modulePath(batch.module), modules: [modulePath(batch.module)] });
  }
});

// --- PRUNE: code dedup, then synthesis self-review, then applyPrune (test-baseline protected). ---
phase("Prune");
const dedupedFindings = dedupFindings(rawFindings);

let synthesis = await agent(
  buildSynthesisPrompt(dedupedFindings, modulesToPaths(input.modules), input.scopeDirs),
  { agentType: "architect-reviewer", schema: SYNTHESIS_SCHEMA, label: "synthesis", phase: "Prune" },
);
if (!synthesis || !Array.isArray(synthesis.items)) {
  // Single-point seam: a null synthesis would discard the whole FIND sweep. Retry once
  // before the fail-loud terminal (the throw stays — never proceed without the prune).
  synthesis = await agent(
    buildSynthesisPrompt(dedupedFindings, modulesToPaths(input.modules), input.scopeDirs),
    { agentType: "architect-reviewer", schema: SYNTHESIS_SCHEMA, label: "synthesis:respawn", phase: "Prune" },
  );
}
if (!synthesis || !Array.isArray(synthesis.items)) {
  // The run cannot proceed honestly without the synthesis prune.
  throw new Error("audit prune: synthesis agent returned no usable items after a retry — cannot proceed.");
}

const annotated = applySynthesisItems(dedupedFindings, synthesis.items);
let survivors = applyPrune(annotated, synthesis.cuts);

// Surface a synthesized missing-test-baseline item if synthesis declared one and dedup/prune
// didn't already carry it (it is added to VERIFY like any finding).
if (
  synthesis.items.some((it) => normalizeIssueClass(it.findingKey) === TEST_BASELINE_CLASS) &&
  !survivors.some((f) => findingKey(f) === TEST_BASELINE_CLASS)
) {
  const baselineItem = synthesis.items.find(
    (it) => normalizeIssueClass(it.findingKey) === TEST_BASELINE_CLASS,
  );
  survivors.push({
    issueClass: TEST_BASELINE_CLASS,
    claimPlain: baselineItem.whyPlain || "Behavior-bearing code lacks a test baseline.",
    claimTechnical: baselineItem.titlePlain || "Establish a test baseline.",
    locations: [],
    confidence: "judgment",
    modules: ["docs/standards/testing.md"],
    sourceModule: "docs/standards/testing.md",
    tier: 1,
    tag: baselineItem.tag || "refactor",
    titlePlain: baselineItem.titlePlain || "Establish a test baseline",
    whyPlain: baselineItem.whyPlain || "",
    impactEffort: baselineItem.impactEffort || "",
  });
}

// Re-checked findings include every survivor PLUS any deferredFindings from a prior run (fed
// straight to VERIFY — their prior tags don't exempt them from a fresh re-check this run).
const toVerify = [...survivors, ...deferredFindings];

// --- VERIFY: exactly ONE finding-verifier per finding, judge-pinned, in parallel. ---
phase("Verify");
const verifyTasks = toVerify.map((finding) => () =>
  spawnVerifier(buildVerifierInput(finding, excludeSet)),
);
const verifyResults = await parallel(verifyTasks);

const { kept, refutedCount } = applyVerdicts(toVerify, verifyResults);
const summary = verificationSummary(kept, refutedCount, input.builderFamily);

// --- Assemble the structured result (the Phase-3 contract; no timestamps — the orchestrator
// stamps the date when it renders the fence). doneCells = input done ∪ this run's swept cells
// (the failed batches' cells stay pending); pendingCells = overflow ∪ failed.
const sweptCells = runCells.filter((c) => !failedCells.includes(c));
const doneCells = [...doneCellsIn, ...sweptCells];
const pendingCells = [...overflowCells, ...failedCells];
const items = kept.map(toResultItem);

return {
  status: runStatus(pendingCells),
  // A COMPLETE cell sweep can still carry unverified findings — say so mechanically.
  verificationIncomplete: summary.deferred > 0,
  level: dial,
  depth,
  doneCells,
  pendingCells,
  items,
  refutedCount,
  verification: summary,
};
