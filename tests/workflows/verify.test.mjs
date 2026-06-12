// tests/workflows/verify.test.mjs — node --test unit tests for the pure helpers of
// workflows/verify.js.
//
// The script can't be imported wholesale: it is a Workflow-tool script — top-level control
// flow ending in a returned result object (no module wrapper beyond `export const meta`) —
// and it calls the tool primitives agent()/parallel()/phase()/log(), which are undefined
// under node. So we read the file, EXTRACT the marked `// --- helpers ---` … `// --- end helpers
// ---` block (pure functions + schema literals), evaluate it via `new Function`, and exercise the helpers
// standalone. The block must NOT close over any tool primitive — these tests are the proof it
// doesn't. Run by `node --test tests/workflows/` (and the CI node-tests job).

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");
const SCRIPT_PATH = join(REPO_ROOT, "workflows", "verify.js");
const STANDARDS_DIR = join(REPO_ROOT, "docs", "standards");

// The verbatim same-model tag — duplicated here on purpose as an independent fixture so a
// drift in the script's wording is caught by an exact string compare (the test is the pin).
const EXPECTED_SAME_MODEL_TAG =
  "same-model review on this run — the judge and the builder are the same model family here.";

// The verbatim UNRESOLVED tag — the third disclosure state. Independent fixture (exact-compare pin).
const EXPECTED_UNRESOLVED_FAMILY_TAG =
  "could not resolve the judge's model family on this run — no cross-model claim is made (treated as the same-model trust floor, not asserted as fact).";

/** Extract the marked helpers block and evaluate it, returning the named helpers.
 *
 * Markers are matched line-anchored (`^// --- helpers ---$`) so a mention of the marker text
 * inside the file's header comment (e.g. "the marked `// --- helpers ---` block") is NOT
 * mistaken for the real delimiter. */
function loadHelpers() {
  const src = readFileSync(SCRIPT_PATH, "utf8");
  const startMatch = src.match(/^\/\/ --- helpers ---$/m);
  const endMatch = src.match(/^\/\/ --- end helpers ---$/m);
  assert.ok(startMatch, "helpers block start marker not found (line-anchored) in workflows/verify.js");
  assert.ok(endMatch, "helpers block end marker not found (line-anchored) in workflows/verify.js");
  const start = startMatch.index;
  const end = endMatch.index;
  assert.ok(end > start, "helpers end marker precedes start marker");
  const block = src.slice(start, end);
  const names = [
    "MODELS",
    "SAME_MODEL_TAG",
    "UNRESOLVED_FAMILY_TAG",
    "KNOWN_FAMILIES",
    "KNOWN_MODULES",
    "validateArgs",
    "modulesFor",
    "modelFamily",
    "sameModelTag",
    "crossModelOutcome",
    "dedupKey",
    "dedupFindings",
    "panelRoster",
    "parseArgs",
    "judgeOutcome",
    "coverageGaps",
    "splitPanelResults",
    "LENS_SCHEMA",
    "YAGNI_SCHEMA",
    "HONESTY_SCHEMA",
    "SYNTHESIS_SCHEMA",
  ];
  // No tool primitives are in scope inside this Function — so if any helper closed over
  // agent()/parallel()/phase()/log(), constructing or calling it would throw here.
  const factory = new Function(`${block}\n; return { ${names.join(", ")} };`);
  return factory();
}

const H = loadHelpers();

/** Build a valid args object; override fields per-case. */
function validArgs(overrides = {}) {
  return {
    diffRef: "main...HEAD",
    specPath: ".claude/plans/0012-harness-v2-executable-choreography.md",
    dimensions: ["testing", "security"],
    trustSurface: false,
    builderFamily: "Fable 5",
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
    "UNRESOLVED_FAMILY_TAG",
    "KNOWN_FAMILIES",
    "KNOWN_MODULES",
    "validateArgs",
    "modulesFor",
    "modelFamily",
    "sameModelTag",
    "crossModelOutcome",
    "dedupKey",
    "dedupFindings",
    "panelRoster",
  ]) {
    assert.ok(H[name] !== undefined, `helper '${name}' was not extracted`);
  }
});

test("MODELS.judge is pinned to 'opus' (cross-model contract)", () => {
  assert.equal(H.MODELS.judge, "opus");
});

// ─────────────────────────────────────────────────────────────────────────────
// KNOWN_MODULES — the mechanical pin against the real docs/standards/*.md basenames
// ─────────────────────────────────────────────────────────────────────────────
test("KNOWN_MODULES equals the real docs/standards/*.md slugs (minus _TEMPLATE/README)", () => {
  const onDisk = readdirSync(STANDARDS_DIR)
    .filter((f) => f.endsWith(".md"))
    .map((f) => f.slice(0, -".md".length))
    .filter((slug) => slug !== "_TEMPLATE" && slug !== "README");
  assert.deepEqual(new Set(H.KNOWN_MODULES), new Set(onDisk));
  // No duplicates in the pinned literal.
  assert.equal(H.KNOWN_MODULES.length, new Set(H.KNOWN_MODULES).size);
});

// ─────────────────────────────────────────────────────────────────────────────
// validateArgs — boundary validation, fail loud
// ─────────────────────────────────────────────────────────────────────────────
test("validateArgs accepts a well-formed args object", () => {
  assert.deepEqual(H.validateArgs(validArgs()), []);
});

test("validateArgs accepts files instead of diffRef", () => {
  const args = validArgs({ diffRef: undefined, files: ["a.js", "b.js"] });
  assert.deepEqual(H.validateArgs(args), []);
});

test("validateArgs flags missing diffRef AND files", () => {
  const args = validArgs({ diffRef: undefined, files: undefined });
  const errors = H.validateArgs(args);
  assert.ok(errors.some((e) => e.includes("diffRef") && e.includes("files")));
});

test("validateArgs flags empty dimensions", () => {
  const errors = H.validateArgs(validArgs({ dimensions: [] }));
  assert.ok(errors.some((e) => e.includes("dimensions")));
});

test("validateArgs flags an unknown dimension by name", () => {
  const errors = H.validateArgs(validArgs({ dimensions: ["security", "not-a-module"] }));
  assert.ok(errors.some((e) => e.includes("not-a-module")));
});

test("validateArgs flags a missing specPath", () => {
  const errors = H.validateArgs(validArgs({ specPath: undefined }));
  assert.ok(errors.some((e) => e.includes("specPath")));
});

test("validateArgs flags a missing builderFamily", () => {
  const errors = H.validateArgs(validArgs({ builderFamily: undefined }));
  assert.ok(errors.some((e) => e.includes("builderFamily")));
});

test("validateArgs flags a missing/non-boolean trustSurface (never defaulted)", () => {
  const errors = H.validateArgs(validArgs({ trustSurface: undefined }));
  assert.ok(errors.some((e) => e.includes("trustSurface")));
});

test("validateArgs rejects a non-object arg", () => {
  assert.deepEqual(H.validateArgs(null), ["args must be an object"]);
});

// ─────────────────────────────────────────────────────────────────────────────
// modulesFor — slug → module path
// ─────────────────────────────────────────────────────────────────────────────
test("modulesFor maps slugs to docs/standards/<slug>.md paths", () => {
  assert.deepEqual(H.modulesFor(["security", "testing"]), [
    "docs/standards/security.md",
    "docs/standards/testing.md",
  ]);
});

// ─────────────────────────────────────────────────────────────────────────────
// modelFamily — normalization (incl. null on unknown)
// ─────────────────────────────────────────────────────────────────────────────
test("modelFamily normalizes a self-reported family to a canonical token", () => {
  assert.equal(H.modelFamily("Opus 4.8"), "opus");
  assert.equal(H.modelFamily("Fable 5"), "fable");
  assert.equal(H.modelFamily("RUNNING AS: Sonnet 4"), "sonnet");
  assert.equal(H.modelFamily("haiku"), "haiku");
});

test("modelFamily returns null on garbage/empty/non-string", () => {
  assert.equal(H.modelFamily("a totally unknown model"), null);
  assert.equal(H.modelFamily(""), null);
  assert.equal(H.modelFamily(null), null);
  assert.equal(H.modelFamily(undefined), null);
  assert.equal(H.modelFamily(42), null);
});

// ─────────────────────────────────────────────────────────────────────────────
// sameModelTag — the verbatim tag string + both-resolve-and-differ → null
// ─────────────────────────────────────────────────────────────────────────────
test("sameModelTag returns the verbatim tag when families match", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.1"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns the verbatim tag string exactly (drift pin)", () => {
  assert.equal(H.SAME_MODEL_TAG, EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns null only when both resolve and differ", () => {
  assert.equal(H.sameModelTag("Fable 5", "Opus 4.8"), null);
});

test("sameModelTag returns the UNRESOLVED tag (the third state) when either family fails to resolve", () => {
  assert.equal(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.equal(H.sameModelTag("", "Opus 4.8"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.equal(H.sameModelTag(null, "Opus 4.8"), EXPECTED_UNRESOLVED_FAMILY_TAG);
  // An unresolved family is NEVER asserted as same-model fact.
  assert.notEqual(H.sameModelTag("Fable 5", "unknown thing"), EXPECTED_SAME_MODEL_TAG);
});

test("sameModelTag returns SAME_MODEL_TAG only on a resolved-same match (not unresolved)", () => {
  assert.equal(H.sameModelTag("Opus 4.8", "Opus 4.1"), EXPECTED_SAME_MODEL_TAG);
});

test("UNRESOLVED_FAMILY_TAG is the verbatim third-state string (drift pin)", () => {
  assert.equal(H.UNRESOLVED_FAMILY_TAG, EXPECTED_UNRESOLVED_FAMILY_TAG);
  // The three disclosure states are distinct strings.
  assert.notEqual(H.UNRESOLVED_FAMILY_TAG, H.SAME_MODEL_TAG);
});

test("KNOWN_FAMILIES is the one named source the modelFamily regex derives from", () => {
  assert.deepEqual(H.KNOWN_FAMILIES, ["fable", "opus", "sonnet", "haiku"]);
  // Every named family resolves through the derived regex (the regex IS this list).
  for (const fam of H.KNOWN_FAMILIES) {
    assert.equal(H.modelFamily(`RUNNING AS: ${fam}`), fam);
  }
  // A family NOT in the list does not resolve — the list is the sole gate.
  assert.equal(H.modelFamily("RUNNING AS: gemini"), null);
});

// ─────────────────────────────────────────────────────────────────────────────
// crossModelOutcome — claimed-iff logic
// ─────────────────────────────────────────────────────────────────────────────
test("crossModelOutcome claims cross-model when every judge confirms a different family", () => {
  const out = H.crossModelOutcome("Fable 5", ["Opus 4.8", "Opus 4.1"]);
  assert.deepEqual(out, { claimed: true, tag: null });
});

test("crossModelOutcome does NOT claim when any judge is same-family", () => {
  const out = H.crossModelOutcome("Fable 5", ["Opus 4.8", "Fable 5"]);
  assert.equal(out.claimed, false);
  assert.equal(out.tag, EXPECTED_SAME_MODEL_TAG);
});

test("crossModelOutcome does NOT claim when a judge report is missing (null) → same-model floor", () => {
  const out = H.crossModelOutcome("Fable 5", ["Opus 4.8", null]);
  assert.equal(out.claimed, false);
  // A MISSING (null) report is the no-self-report same-model floor, not the unresolved state.
  assert.equal(out.tag, EXPECTED_SAME_MODEL_TAG);
});

test("crossModelOutcome reports UNRESOLVED (never same-model fact) when a judge family is unrecognized", () => {
  const out = H.crossModelOutcome("Fable 5", ["Opus 4.8", "RUNNING AS: gemini"]);
  assert.equal(out.claimed, false);
  assert.equal(out.tag, EXPECTED_UNRESOLVED_FAMILY_TAG);
  assert.notEqual(out.tag, EXPECTED_SAME_MODEL_TAG);
});

test("crossModelOutcome reports UNRESOLVED when the BUILDER family is unrecognized", () => {
  const out = H.crossModelOutcome("some-unknown-builder", ["Opus 4.8"]);
  assert.equal(out.claimed, false);
  assert.equal(out.tag, EXPECTED_UNRESOLVED_FAMILY_TAG);
});

test("crossModelOutcome does NOT claim on an empty report list", () => {
  const out = H.crossModelOutcome("Fable 5", []);
  assert.equal(out.claimed, false);
  assert.equal(out.tag, EXPECTED_SAME_MODEL_TAG);
});

// ─────────────────────────────────────────────────────────────────────────────
// dedupKey / dedupFindings — merge semantics
// ─────────────────────────────────────────────────────────────────────────────
test("dedupKey normalizes file:line whitespace and lowercases dimension", () => {
  const a = H.dedupKey({ file_line: "src/a.js : 12", dimension: "Security" });
  const b = H.dedupKey({ file_line: "src/a.js:12", dimension: "security" });
  assert.equal(a, b);
});

test("dedupFindings merges same file:line + dimension across lenses, unioning sources", () => {
  const merged = H.dedupFindings([
    { dimension: "security", status: "gap", file_line: "a.js:1", fix: "fix A", confidence: "judgment" },
    { dimension: "security", status: "gap", file_line: "a.js:1", fix: "fix B", confidence: "deterministic" },
  ]);
  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].sources, ["security"]);
  // First concrete fix kept; deterministic confidence preferred.
  assert.equal(merged[0].fix, "fix A");
  assert.equal(merged[0].confidence, "deterministic");
});

test("dedupFindings keeps distinct dimensions at the same line separate", () => {
  const merged = H.dedupFindings([
    { dimension: "security", status: "gap", file_line: "a.js:1", fix: "x", confidence: "judgment" },
    { dimension: "testing", status: "gap", file_line: "a.js:1", fix: "y", confidence: "judgment" },
  ]);
  assert.equal(merged.length, 2);
});

test("dedupFindings prefers the first concrete fix when an earlier one is empty", () => {
  const merged = H.dedupFindings([
    { dimension: "security", status: "gap", file_line: "a.js:1", fix: "", confidence: "judgment" },
    { dimension: "security", status: "gap", file_line: "a.js:1", fix: "real fix", confidence: "judgment" },
  ]);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].fix, "real fix");
});

// ─────────────────────────────────────────────────────────────────────────────
// panelRoster — derivation incl. trustSurface on/off
// ─────────────────────────────────────────────────────────────────────────────
test("panelRoster derives one lens per module + yagni + synthesis (trustSurface off)", () => {
  const roster = H.panelRoster(validArgs({ trustSurface: false, dimensions: ["security", "testing"] }));
  const roles = roster.map((r) => r.role);
  assert.deepEqual(roles, [
    "lens:docs/standards/security.md",
    "lens:docs/standards/testing.md",
    "yagni",
    "synthesis",
  ]);
  // No honesty role when trustSurface is off.
  assert.ok(!roster.some((r) => r.role === "honesty"));
  // The synthesis judge carries the model pin.
  assert.equal(roster.find((r) => r.role === "synthesis").model, "opus");
});

test("panelRoster includes the honesty judge when trustSurface is on", () => {
  const roster = H.panelRoster(validArgs({ trustSurface: true, dimensions: ["security"] }));
  const honesty = roster.find((r) => r.role === "honesty");
  assert.ok(honesty, "honesty role missing on a trust surface");
  assert.equal(honesty.agentType, "honesty-reviewer");
  assert.equal(honesty.model, "opus");
});

test("parseArgs parses a JSON-string args delivery (the scriptPath boundary)", () => {
  const out = H.parseArgs('{"diffRef": "HEAD", "trustSurface": true}');
  assert.deepEqual(out, { diffRef: "HEAD", trustSurface: true });
});

test("parseArgs passes an object through untouched", () => {
  const obj = { diffRef: "HEAD" };
  assert.equal(H.parseArgs(obj), obj);
});

test("parseArgs fails loud on an unparseable string", () => {
  assert.throws(() => H.parseArgs("{not json"), /not valid JSON/);
});

test("judgeOutcome: first success is cross-model eligible", () => {
  const d = H.judgeOutcome("synthesis", "architect-reviewer", { out: { verdict: "PASS" } });
  assert.deepEqual(d, { out: { verdict: "PASS" }, forcedSameModel: false });
});

test("judgeOutcome: first failure with no second attempt asks for the retry", () => {
  assert.deepEqual(
    H.judgeOutcome("synthesis", "architect-reviewer", { out: null, err: "boom" }),
    { needRetry: true },
  );
  // A null return (skipped agent) is a failure too — never a usable judge verdict.
  assert.deepEqual(H.judgeOutcome("synthesis", "architect-reviewer", { out: null }), { needRetry: true });
});

test("judgeOutcome: retry success is force-tagged same-model", () => {
  const d = H.judgeOutcome("honesty", "honesty-reviewer", { out: null, err: "x" }, { out: { verdict: "CLEAN" } });
  assert.equal(d.forcedSameModel, true);
});

test("judgeOutcome: two failures throw — never a silent partial PASS", () => {
  assert.throws(
    () => H.judgeOutcome("synthesis", "architect-reviewer", { out: null, err: "a" }, { out: null, err: "b" }),
    /failed twice.*Never a silent partial PASS/s,
  );
});

test("coverageGaps: a null lens return becomes an explicit deterministic could-not-run gap", () => {
  const ok = { verdict: "CLEAN", findings: [] };
  const gaps = H.coverageGaps([ok, null], ["docs/standards/testing.md", "docs/standards/security.md"]);
  assert.equal(gaps.length, 1);
  assert.equal(gaps[0].dimension, "docs/standards/security.md");
  assert.equal(gaps[0].status, "gap");
  assert.equal(gaps[0].confidence, "deterministic");
});

test("coverageGaps: all lenses ran → no gaps", () => {
  const ok = { verdict: "CLEAN", findings: [] };
  assert.deepEqual(H.coverageGaps([ok, ok], ["a", "b"]), []);
});

test("crossModelOutcome: an unresolvable BUILDER family reports UNRESOLVED, never a claim", () => {
  const r = H.crossModelOutcome("unknown-builder", ["Opus 4.8"]);
  assert.equal(r.claimed, false);
  // Unresolved is reported AS unresolved — never asserted as same-model fact.
  assert.equal(r.tag, EXPECTED_UNRESOLVED_FAMILY_TAG);
});

test("splitPanelResults: input-order arithmetic, honesty on", () => {
  const r = H.splitPanelResults(["l1", "l2", "y", "h"], 2, true);
  assert.deepEqual(r, { lensReturns: ["l1", "l2"], yagni: "y", honestyJudge: "h" });
});

test("splitPanelResults: honesty off → honestyJudge is null", () => {
  const r = H.splitPanelResults(["l1", "y"], 1, false);
  assert.deepEqual(r, { lensReturns: ["l1"], yagni: "y", honestyJudge: null });
});

test("schema field-set pins: the required arrays are the consumed contract (drift guard)", () => {
  assert.deepEqual(H.LENS_SCHEMA.required, ["verdict", "findings"]);
  assert.deepEqual(H.LENS_SCHEMA.properties.findings.items.required,
    ["dimension", "status", "fix", "file_line", "confidence", "plain_english"]);
  assert.deepEqual(H.YAGNI_SCHEMA.required, ["verdict", "cuts"]);
  assert.deepEqual(H.HONESTY_SCHEMA.required, ["reported_model_family", "verdict", "findings"]);
  assert.deepEqual(H.SYNTHESIS_SCHEMA.required,
    ["reported_model_family", "verdict", "findings", "missed_dimensions", "dod_check", "plain_english_summary"]);
});

test("dedupFindings: deterministic confidence is never downgraded by a later judgment dup", () => {
  const merged = H.dedupFindings([
    { dimension: "d", status: "gap", fix: "f", file_line: "a.js:1", confidence: "deterministic" },
    { dimension: "d", status: "gap", fix: "f2", file_line: "a.js:1", confidence: "judgment" },
  ]);
  assert.equal(merged.length, 1);
  assert.equal(merged[0].confidence, "deterministic");
});

test("dedupFindings: a three-way duplicate collapses to one, first non-empty fix wins", () => {
  const merged = H.dedupFindings([
    { dimension: "d", status: "gap", fix: "", file_line: "a.js:1", confidence: "judgment" },
    { dimension: "d", status: "gap", fix: "the fix", file_line: "a.js:1", confidence: "judgment" },
    { dimension: "d", status: "gap", fix: "later fix", file_line: "a.js:1", confidence: "judgment" },
  ]);
  assert.equal(merged.length, 1);
  // The dedup key includes the dimension, so same-key dups share one source entry.
  assert.deepEqual(merged[0].sources, ["d"]);
  assert.equal(merged[0].fix, "the fix");
});
