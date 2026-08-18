// tests/workflows/_load-helpers.mjs — the shared extract-and-eval harness for the
// workflow-script helper tests (single source of truth; was copy-pasted into each
// *.test.mjs before this).
//
// A Workflow-tool script can't be imported wholesale: it is top-level control flow ending
// in a returned result object (no module wrapper beyond `export const meta`) and it calls
// the tool primitives agent()/parallel()/phase()/log()/workflow(), which are undefined
// under node. So each test reads its script, EXTRACTs the marked
// `// --- helpers ---` … `// --- end helpers ---` block (pure functions + schema/const
// literals), evaluates it via `new Function`, and exercises the helpers standalone. The
// block must close over NO tool primitive — `new Function` bodies see only the global
// scope, so constructing/calling a helper that captured a primitive would throw here; that
// is the proof it doesn't.
//
// Each test file passes its own SCRIPT_PATH + the list of helper names it exercises (both
// are genuinely per-file). NOT a `*.test.mjs` file, so `node --test tests/workflows/*.test.mjs`
// (the CI invocation) never collects it as a test.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

/** Extract the marked helpers block from the script at `scriptPath` and return an object of
 * the requested `names`.
 *
 * Markers are matched line-anchored (`^// --- helpers ---$`) so a mention of the marker text
 * inside a script's header comment (e.g. "the marked `// --- helpers ---` block") is NOT
 * mistaken for the real delimiter. */
export function loadHelpersFrom(scriptPath, names) {
  const src = readFileSync(scriptPath, "utf8");
  const startMatch = src.match(/^\/\/ --- helpers ---$/m);
  const endMatch = src.match(/^\/\/ --- end helpers ---$/m);
  assert.ok(startMatch, `helpers block start marker not found (line-anchored) in ${scriptPath}`);
  assert.ok(endMatch, `helpers block end marker not found (line-anchored) in ${scriptPath}`);
  const start = startMatch.index;
  const end = endMatch.index;
  assert.ok(end > start, "helpers end marker precedes start marker");
  const block = src.slice(start, end);
  // No tool primitives are in scope inside this Function — so if any helper closed over
  // agent()/parallel()/phase()/log()/workflow(), constructing or calling it would throw here.
  const factory = new Function(`"use strict";\n${block}\n; return { ${names.join(", ")} };`);
  return factory();
}
