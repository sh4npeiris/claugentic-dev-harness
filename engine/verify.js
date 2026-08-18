// engine/verify.js -- the Stage-7 Verify panel as an executable Workflow script.
//
// Distribution: read-from-install-path. Adopters invoke this from the version-stamped
// plugin install dir (`${CLAUDE_PLUGIN_ROOT}/engine/verify.js`); this repo dogfoods it
// via the repo-local `./engine/verify.js` (the working tree IS the plugin source).
// Never copied into an adopter repo (no managed-stamp/refresh surface) -- see
// docs/claugentic-DECISIONS.md -> Plugin identity & distribution.
//
// Workflow-script constraints (the tool runs this inside its sandbox): NO imports, NO
// filesystem APIs, NO wall-clock / randomness (the orchestrator stamps times after the
// run). Only the tool primitives `agent()`/`parallel()`/`phase()`/`log()`/`args`. The lens
// fan-out IS a loop (one `.map()` over the in-scope modules), and the roster is built from
// caller-supplied `dimensions` -- so the bound comes from the standards CATALOG, not from the
// caller: `dimensions` is validated for membership and de-duplicated, capping the panel at
// KNOWN_MODULES.length lenses + yagni + the trust-surface honesty judge + synthesis. Agent
// CALLS are a small constant multiple of that (each judge may respawn once; any spawn may
// retry once bare via the namespace fallback). Pure decision logic lives in the marked
// `// --- helpers ---` block and is unit-tested by tests/workflows/verify.test.mjs
// (extract-and-eval), so the prose->script move tests the judgment, not just inspects it.

export const meta = {
  name: "verify",
  description:
    "Stage-7 Verify panel: diff-scoped lens fan-out + yagni + (trust-surface) honesty + architect synthesis with coded cross-model tagging",
};

// --- helpers ---
// Pure functions only -- they reference solely their params and each other (no closure over
// tool primitives), so the test harness can extract this block and evaluate it standalone.

// The judge model family, defined ONCE (single source of truth). Later scripts copy this
// block convention. A coded `model:` param is the wired cross-model spawn the prose used to
// uphold; the same-model TAG (below) stays the per-run honesty guard.
const MODELS = { judge: "opus" };

// The bundled-agent namespace prefix -- the ONE source both nsAgent (which adds it) and
// bareAgentType (which strips it) read, so the two can never disagree about what a namespaced id
// looks like. Copied byte-identical across the workflow scripts (cross-script drift pin).
const AGENT_NAMESPACE = "claugentic-dev-harness";

// Bundled agents resolve as `<AGENT_NAMESPACE>:<agent>` for an installed adopter (bare names
// resolve only when dogfooded with project-local .claude/agents/). Namespace every custom-agent
// spawn; built-ins (general-purpose, ...) stay bare. Namespaced stays what the engine WRITES --
// the spawn wrapper below the helpers block retries bare ONCE on a thrown spawn failure, and
// DERIVES that bare name rather than storing it. Pure -> unit-tested.
const nsAgent = (name) => `${AGENT_NAMESPACE}:${name}`;

// Strip EVERY leading `<AGENT_NAMESPACE>:` prefix from an agent id, yielding the bare name a
// project-local .claude/agents/ dir resolves -- the D6 fallback target, DERIVED at runtime so no
// bare agent name is ever written as a literal in engine source. Total and IDEMPOTENT
// (bareAgentType(bareAgentType(x)) === bareAgentType(x)), so a doubly-namespaced id can never be
// half-stripped. An id with no prefix comes back UNCHANGED, and "unchanged" IS the "no fallback
// exists" signal the caller tests by comparison -- a built-in like general-purpose, or another
// plugin's namespace, which is not ours to strip; a non-string maps to "". Copied byte-identical
// across the workflow scripts (cross-script drift pin).
function bareAgentType(agentType) {
  const prefix = `${AGENT_NAMESPACE}:`;
  let bare = typeof agentType === "string" ? agentType : "";
  while (bare.startsWith(prefix)) {
    bare = bare.slice(prefix.length);
  }
  return bare;
}

// The one-line notice a namespace fallback logs before its single bare retry. Pure (message only
// -- the caller owns log() and the retry), so the wording is unit-pinnable from the helpers
// block. It states the trust boundary in the run log itself: a namespace retry is NOT a model
// respawn. Copied byte-identical across the workflow scripts (cross-script drift pin).
function namespaceFallbackNotice(agentType, bare, err) {
  const detail = err && err.message ? err.message : String(err);
  return (
    `agent spawn '${agentType}' failed (${detail}) -- retrying ONCE as the bare name '${bare}' ` +
    `(project-local .claude/agents/ resolution). This is a NAMESPACE retry, not a model respawn: ` +
    `it consumes no respawn budget, keeps the same model options, and changes no cross-model claim.`
  );
}

// The verbatim same-model disclosure tag. Defined once; never reconstructed by hand at a
// call site, so the wording cannot drift (honesty trust surface).
const SAME_MODEL_TAG =
  "same-model review on this run -- the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED disclosure tag -- the THIRD state, distinct from SAME_MODEL_TAG. When a
// judge's self-reported family can't be recognized, the run is reported as unresolved (the
// conservative same-model trust floor still holds -- no cross-model claim) rather than ASSERTED to
// be same-model fact. Defined once so the wording cannot drift (honesty trust surface). Copied
// byte-identical across the workflow scripts (cross-script drift pin).
const UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run -- no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

// The recognized model families -- the ONE named source the modelFamily regex derives from (single
// source of truth: a new family is added HERE, never in a hand-built regex). Copied byte-identical
// across the workflow scripts (cross-script drift pin).
const KNOWN_FAMILIES = ["fable", "opus", "sonnet", "haiku"];

// The 11 standards-catalog slugs. The script can't read the filesystem, so this literal is
// the source of truth here -- and tests/workflows/verify.test.mjs pins it set-equal to the
// real docs/claugentic-standards/*.md basenames (read via node:fs), killing list drift mechanically.
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

// Test-path patterns: a changed file that exercises behavior assertions. Reasonably broad
// across ecosystems -- name-substring (`test`/`spec`), dir-segment (`tests/`/`__tests__/`),
// dotted-suffix (`.test.`/`.spec.`), and python (`test_*.py`/`*_test.py`). The list is the
// single source of the "diff touches tests" signal (piece #2). Match is case-insensitive and
// works on a posix-or-windows path (separators normalized). Documented patterns:
//   *test* - *spec* - tests/ - __tests__/ - *.test.* - *.spec.* - test_*.py - *_test.py
function isTestPath(path) {
  if (typeof path !== "string" || path.length === 0) {
    return false;
  }
  const p = path.replace(/\\/g, "/").toLowerCase();
  const base = p.split("/").pop() || "";
  return (
    /(^|\/)__tests__\//.test(p) ||
    /(^|\/)tests?\//.test(p) ||
    /\.(test|spec)\./.test(base) ||
    /^test_.*\.py$/.test(base) ||
    /_test\.py$/.test(base) ||
    base.includes("test") ||
    base.includes("spec")
  );
}

// The "diff touches tests" signal, computed from verify.js's ACTUAL inputs (single rule).
// Two inputs can carry it: `files` (a concrete changed-file list -- matched mechanically here)
// and `testDiff` (an explicit boolean the caller sets when it has only the opaque `diffRef`
// and already knows the diff touched tests). Either positive => the testing lens is required.
function diffTouchesTests(args) {
  if (Array.isArray(args.files) && args.files.some(isTestPath)) {
    return true;
  }
  return args.testDiff === true;
}

// Validate the args contract at the boundary (fail loud -- the caller throws on a non-empty
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
    for (const dim of new Set(args.dimensions)) {
      if (!KNOWN_MODULES.includes(dim)) {
        errors.push(`unknown dimension '${dim}' -- not a docs/claugentic-standards/ module slug`);
      }
    }
    // Piece #2 -- force-include the testing lens on a test-diff (mechanical where the signal
    // exists; in-sandbox, no globs/fs). When the change touches tests, the testing lens MUST be
    // in the panel -- a green suite can hide a loosened assertion, and finding-verifier only
    // refutes SURFACED findings. Fail loud (the caller adds it deliberately): a test-touching
    // diff with `testing` absent is a contract error, never silently allowed.
    if (diffTouchesTests(args) && !args.dimensions.includes("testing")) {
      errors.push(
        "the change touches test files but 'testing' is not in dimensions -- the testing lens is " +
          "mandatory on a test-diff (add 'testing' to dimensions); never verify a test change without it",
      );
    }
  }
  if (typeof args.trustSurface !== "boolean") {
    errors.push("trustSurface is required (boolean -- explicit decision at the boundary, never defaulted)");
  }
  if (typeof args.builderFamily !== "string" || args.builderFamily.length === 0) {
    errors.push("builderFamily is required (non-empty string -- the family that authored the diff)");
  }
  return errors;
}

// Map validated dimension slugs to their module doc paths (assumes validated input).
function modulesFor(dimensions) {
  return dimensions.map((slug) => `docs/claugentic-standards/${slug}.md`);
}

// De-duplicate the caller's dimension list, preserving first-seen order. validateArgs checks
// dimension MEMBERSHIP only -- it is a pure predicate and must stay one -- so without this the
// lens fan-out is sized by the CALLER's array: `dimensions: Array(200).fill("security")`
// validates clean and spawns 200 lens agents over one module. After it, the fan-out is bounded
// by the catalog (at most KNOWN_MODULES.length lenses), which is what makes the header's bound
// claim true. NON-MUTATING, and it returns a NEW array even when there is nothing to drop:
// build-item.js's verifyChildArgs passes its `named` branch through with NO copy, so an in-place
// dedupe would mutate the caller's item across build-to-green iterations. Applied ONCE at the
// boundary and fed to BOTH consumers -- panelRoster and modulesAudited derive independently from
// `dimensions`, and deduping one only would break the lensReturns[i] <-> modulesAudited[i]
// pairing coverageGaps relies on. IDEMPOTENT: dedupeDimensions(dedupeDimensions(x)) deep-equals
// dedupeDimensions(x). (0041 S10b, D4)
function dedupeDimensions(dimensions) {
  return Array.isArray(dimensions) ? [...new Set(dimensions)] : [];
}

// Normalize a self-reported model family to a canonical lowercase token. First KNOWN_FAMILIES
// match wins (the regex derives from that one named source -- no second hand-built family list);
// empty / unknown -> null (conservative -- an unresolved family degrades to the trust floor, never
// to a false cross-model claim).
function modelFamily(report) {
  if (typeof report !== "string") {
    return null;
  }
  const match = report.match(new RegExp(`(${KNOWN_FAMILIES.join("|")})`, "i"));
  return match ? match[1].toLowerCase() : null;
}

// The disclosure decision -- THREE states, one rule (detection included). The distinction is
// between a MISSING self-report (the deliberate no-report / forced-respawn floor) and a PRESENT
// self-report that FAILED to resolve (a genuine "could not resolve the family"):
//   - judge self-report is absent (null/undefined/empty)   -> SAME_MODEL_TAG  (the no-report floor --
//                                                             e.g. a forced same-model respawn)
//   - a PRESENT family (either side) fails to resolve        -> UNRESOLVED_FAMILY_TAG (reported
//                                                             unresolved, NEVER asserted same-model)
//   - both resolve and MATCH                                 -> SAME_MODEL_TAG  (resolved-same fact)
//   - both resolve and DIFFER                                -> null            (sole cross-model case)
// The cross-model claim keys off `=== null` (unchanged: claimed ONLY on confirmed different-family);
// only the non-null DISCLOSURE wording now distinguishes resolved-same from unresolved.
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

// Fold the judges' self-reports into the run's cross-model claim. `claimed` is true IFF the
// report list is non-empty AND sameModelTag is null for EVERY judge (a confirming
// different-family self-report from each). Otherwise claimed:false + the disclosure tag for WHY:
// an UNRESOLVED judge family yields UNRESOLVED_FAMILY_TAG (reported as unresolved, never asserted
// same-model fact); a resolved-same judge yields SAME_MODEL_TAG. An empty report list is the
// no-judge same-model trust floor. The first non-confirming judge sets the tag (its own state).
function crossModelOutcome(builderFamily, judgeReports) {
  if (!Array.isArray(judgeReports) || judgeReports.length === 0) {
    return { claimed: false, tag: SAME_MODEL_TAG };
  }
  for (const report of judgeReports) {
    const tag = sameModelTag(builderFamily, report);
    if (tag !== null) {
      return { claimed: false, tag };
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
// the synthesizer-gate synthesis (judge-pinned). Logged up front and echoed in the result.
function panelRoster(args) {
  const roster = [];
  for (const modulePath of modulesFor(args.dimensions)) {
    roster.push({ role: `lens:${modulePath}`, agentType: nsAgent("lens-reviewer") });
  }
  roster.push({ role: "yagni", agentType: nsAgent("yagni-sentinel") });
  if (args.trustSurface) {
    roster.push({ role: "honesty", agentType: nsAgent("honesty-reviewer"), model: MODELS.judge });
  }
  roster.push({ role: "synthesis", agentType: nsAgent("synthesizer-gate"), model: MODELS.judge });
  return roster;
}

// Normalize the args boundary. A scriptPath invocation delivers `args` as a JSON STRING
// (observed runtime behavior, 2026-06-11); an inline script may receive the object itself.
// Accept both; an unparseable string fails loud -- never a silent empty-args run.
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

// Decide a judge spawn's outcome from its attempts -- PURE so the retry contract is
// unit-testable. An attempt is { out } (out === null counts as failure: agent() returns null
// on skip/terminal error) or { out: null, err }. First success -> cross-model eligible;
// retry success -> forcedSameModel; first failure with no retry yet -> { needRetry: true };
// both failed -> throw. Never a silent partial PASS.
function judgeOutcome(role, agentType, first, second) {
  if (first && first.out != null) return { out: first.out, forcedSameModel: false };
  if (second === undefined) return { needRetry: true };
  if (second && second.out != null) return { out: second.out, forcedSameModel: true };
  const firstErr = first && first.err ? first.err : "null return (skipped or terminal error)";
  const secondErr = second && second.err ? second.err : "null return (skipped or terminal error)";
  throw new Error(
    `verify panel: judge '${role}' (${agentType}) failed twice -- first: ${firstErr}; ` +
      `respawn (no model override): ${secondErr}. Never a silent partial PASS.`,
  );
}

// The one-line notice the panel guard logs before degrading a failed thunk to null. PURE
// (message only -- the caller owns log() and the null return), because the guard itself closes
// over agent()/log() and lives below this block where no test can reach it; extracting the
// wording is what makes the degradation contract unit-pinnable at all. It names both consumers
// honestly: an unrun LENS becomes a deterministic coverage gap and forces CHANGES_REQUIRED (via
// coverageGaps -> finalVerdict), while an unrun YAGNI only marks the panel degraded.
// (0041 S10b, D4)
function guardFailure(err, label) {
  const detail = err && err.message ? err.message : String(err);
  return (
    `verify panel: thunk '${label || "(unlabeled)"}' failed -- ${detail}. Degrading to null IN ` +
    `POSITION (parallel() arity preserved): an unrun lens becomes a deterministic coverage gap ` +
    `and forces CHANGES_REQUIRED; an unrun yagni leaves the panel degraded. Never a crashed run.`
  );
}

// Panel-coverage honesty: a lens that returned null/unusable output (skipped or errored) must
// surface as an explicit could-not-run GAP -- an unrun review must never read as a clean
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
          "lens did not run (no usable return) -- this module was NOT audited; re-run the panel. " +
          "An unrun lens is never treated as clean.",
        file_line: "(panel coverage)",
        confidence: "deterministic",
        plain_english:
          `The ${modulePath} reviewer never reported back, so that part of the review did not ` +
          "happen -- it must be re-run, not assumed fine.",
      });
    }
  });
  return gaps;
}

// Piece #1 -- mechanical presence-assertion on the panel's OWN outputs (honestly NOT a
// completeness gate over the diff). The verdict is normally passed through from synthesis; but
// a panel where a NAMED lens produced no usable result must NEVER report all-green, even if the
// synthesis judge said PASS. So when there is at least one deterministic could-not-run gap (the
// presence check on `lensReturns` that `coverageGaps` already computes), force CHANGES_REQUIRED.
// This is a presence check on the panel's OWN results -- no filesystem, no globs, no completeness
// claim over the diff, no second-guessing which lenses were selected. PURE so it is unit-tested.
function finalVerdict(synthesisVerdict, unrunLensCount) {
  if (unrunLensCount > 0) {
    return "CHANGES_REQUIRED"; // a named lens silently no-showed -- never report all-green
  }
  return synthesisVerdict === "PASS" ? "PASS" : "CHANGES_REQUIRED";
}

// Split the ordered parallel() results back into panel roles. parallel() preserves INPUT
// ORDER (each thunk's result lands at its input index) -- this helper pins that arithmetic
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

// The D6 namespace fallback -- the ONE spawn seam every namespaced agent call goes through.
// Bundled agents resolve as `<AGENT_NAMESPACE>:<agent>` for an installed adopter and only as BARE
// names in a project-local dogfood session; this sandbox cannot detect which world it is in (no
// imports, no filesystem, no env), so try-namespaced-then-retry-bare is the only implementable
// form. It fires ONLY on a THROWN spawn failure: a null return is a legitimate agent outcome (a
// skip or terminal error) and is passed through untouched, never retried. The retry spreads the
// ORIGINAL opts, so a judge's `model:` pin survives it.
//
// DO NOT thread this through a judge's one-respawn state machine (0041 S10b, D6). A namespace
// retry must never consume the respawn budget, never set forcedSameModel (that flag feeds the
// same-model disclosure), never swallow a two-failure throw, and never reuse the `:respawn`
// label -- it carries its own `:ns-fallback` label so the run log can tell the two apart.
// Copied byte-identical across the workflow scripts (cross-script drift pin).
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

// Panel-phase guard, for the LENS and YAGNI thunks ONLY. The platform's parallel() already
// resolves a throwing thunk to null (it never rejects) -- this wrapper makes the never-crash-the
// -run property LOCAL and auditable instead of resting on an out-of-repo tool contract, and it
// LOGS the failure the platform would otherwise swallow without a word. It returns null IN
// POSITION, preserving parallel()'s arity: splitPanelResults slices by INDEX and coverageGaps
// pairs lensReturns[i] with modulesAudited[i], so any guard that filtered, compacted, chunked or
// reshaped the results would misalign the pairing and name the WRONG module as unrun.
//
// NEVER apply this to the honesty thunk, and never blanket-map it over panelTasks (0041 S10b,
// D4): honesty is a spawnJudge call in the SAME parallel(), and guardFailure's message is FALSE
// for it -- coverageGaps walks lensReturns only, so an unrun honesty judge yields no coverage gap
// and no forced CHANGES_REQUIRED. That is the reason, and it is NOT "so the throw stays loud".
// MEASURED 2026-08-17: parallel() swallows judgeOutcome's two-failure throw with or without a
// guard -- a twice-failed honesty judge already returns honesty: null, panelDegraded: false and an
// unchanged verdict, with no log line; a guard would only ADD one. Unguarded is NOT loud. Making
// it visible, and deciding whether it degrades or blocks, moves finalVerdict/panelDegraded
// semantics -- routed to the harness's own backlog, not fixed here (0041 S10b).
async function guardedPanelAgent(prompt, opts) {
  try {
    return await agentWithNamespaceFallback(prompt, opts);
  } catch (e) {
    log(guardFailure(e, opts && opts.label));
    return null;
  }
}

// Spawn a judge with the cross-model `model:` pin; one respawn without it on failure
// (force-tagged same-model); the decision logic lives in the PURE judgeOutcome helper. The
// attempt routes through the namespace fallback, which resolves INSIDE one attempt: a bare retry
// therefore consumes no respawn budget and cannot influence forcedSameModel (0041 S10b, D6).
async function spawnJudge(role, agentType, prompt, schema) {
  const attempt = async (opts) => {
    try {
      return { out: await agentWithNamespaceFallback(prompt, opts) };
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

// -- Top-level control flow (Workflow scripts run in an async context; no module wrapper). --

// Validate at the boundary -- fail loud with the full error list.
const input = parseArgs(args);
{
  const errors = validateArgs(input);
  if (errors.length > 0) {
    throw new Error(`verify args invalid:\n  - ${errors.join("\n  - ")}`);
  }
}

// De-duplicate ONCE, at the boundary, and feed BOTH consumers from the SAME array. The roster and
// modulesAudited derive independently, and coverageGaps pairs them by index -- deduping one only
// would name the wrong module as unrun (0041 S10b, D4). Do not move this into validateArgs: that
// is a pure predicate, and mutating the caller's array would corrupt build-item.js's item across
// build-to-green iterations.
const dimensions = dedupeDimensions(input.dimensions);
if (dimensions.length !== input.dimensions.length) {
  // A narrowed panel is never a silent default: say what the caller asked for and what ran.
  log(
    `verify: dimensions de-duplicated -- ${input.dimensions.length} requested, ${dimensions.length} ` +
      `distinct module(s) audited. The lens fan-out is bounded by the standards catalog, never by ` +
      `the length of the caller's array.`,
  );
}
const roster = panelRoster({ ...input, dimensions });
const modulesAudited = modulesFor(dimensions);
log(`verify panel roster (${roster.length} roles): ${roster.map((r) => r.role).join(", ")}`);

const diffScope = input.diffRef ? `diffRef=${input.diffRef}` : `files=${JSON.stringify(input.files)}`;

// --- Panel phase: one lens per module + yagni + (trust-surface) honesty, in parallel. ---
phase("Panel");
const lensTasks = modulesAudited.map((modulePath) => () =>
  guardedPanelAgent(
    `Verify-diff mode. Your lens is the standards module: ${modulePath}. ` +
      `Audit the change against that module's dimensions only. ` +
      `Locate the implementing code via docs/claugentic-ARCHITECTURE_TREE.md (the file index) ` +
      `instead of reading whole files. ` +
      `Diff scope: ${diffScope}. ` +
      `Spec: ${input.specPath}.`,
    { agentType: nsAgent("lens-reviewer"), schema: LENS_SCHEMA, label: `lens:${modulePath}`, phase: "Panel" },
  ),
);

// The lens and yagni thunks are guarded (null in position, logged); the honesty thunk below is
// NOT -- guardFailure's wording is false for a judge (see the guard). That does NOT make its
// two-failure throw loud: parallel() swallows it either way (0041 S10b, D4, trap 1; ROADMAP).
const panelTasks = [
  ...lensTasks,
  () =>
    guardedPanelAgent(
      `Argue this change is too much. Diff scope: ${diffScope}. ` +
        `Spec: ${input.specPath}. Return a cut-list of over-build with where-instead.`,
      { agentType: nsAgent("yagni-sentinel"), schema: YAGNI_SCHEMA, label: "yagni", phase: "Panel" },
    ),
];

// The honesty reviewer (trust-surface only) is a JUDGE -- it fans out in the same panel,
// but via spawnJudge so it carries the model: pin + the one-respawn-on-error contract.
const hasHonesty = input.trustSurface === true;
if (hasHonesty) {
  panelTasks.push(() =>
    spawnJudge(
      "honesty",
      nsAgent("honesty-reviewer"),
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
// Piece #1 -- observability: a named lens that produced no usable result is LOGGED loudly here
// (it also forces CHANGES_REQUIRED at the return via finalVerdict), so an unrun lens never reads
// as a silently-clean dimension. Presence-check on the panel's own outputs -- not a completeness
// claim over the diff.
if (unrunGaps.length > 0) {
  log(
    `verify: ${unrunGaps.length} named lens(es) produced NO usable result ` +
      `(${unrunGaps.map((g) => g.dimension).join(", ")}) -- forcing CHANGES_REQUIRED; ` +
      `a named lens cannot silently no-show from the panel's own outputs.`,
  );
}

// --- Synthesis phase: synthesizer-gate over the deduped findings + yagni + honesty. ---
phase("Synthesis");
const synthesisResult = await spawnJudge(
  "synthesis",
  nsAgent("synthesizer-gate"),
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
// Observability: a self-report that failed to resolve is LOGGED, never silently degraded. A
// forced-respawn judge carries a null/empty reportedFamily by design (already same-model) -- only a
// PRESENT non-empty but unrecognized report is the noteworthy unresolved case (aligned with
// sameModelTag's missing-vs-present-unresolved split).
for (const judge of judges) {
  const reported = judge.reportedFamily;
  if (typeof reported === "string" && reported.trim().length > 0 && modelFamily(reported) === null) {
    log(
      `verify: judge '${judge.role}' self-reported an UNRECOGNIZED model family ` +
        `(${JSON.stringify(reported)}) -- reported as unresolved, no cross-model claim made.`,
    );
  }
}
const crossModel = crossModelOutcome(
  input.builderFamily,
  judges.map((j) => j.reportedFamily),
);

return {
  // The script never overrides JUDGMENT -- synthesis owns the verdict. The ONE mechanical
  // override is the presence-assertion (finalVerdict): a named lens that produced no usable
  // result forces CHANGES_REQUIRED so the panel can never report all-green with one of its own
  // named lenses missing. This is a presence-check on the panel's outputs, not a diff-coverage gate.
  verdict: finalVerdict(synthesis ? synthesis.verdict : "CHANGES_REQUIRED", unrunGaps.length),
  crossModel: { claimed: crossModel.claimed, tag: crossModel.tag, judges },
  findings: synthesis ? synthesis.findings : [],
  yagni: yagni == null ? { couldNotRun: true } : yagni,
  panelDegraded,
  honesty: input.trustSurface ? honesty : { skipped: "trustSurface=false" },
  panel: roster,
  modulesAudited,
};
