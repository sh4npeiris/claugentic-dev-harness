// tests/workflows/cross-script.test.mjs — the cross-script drift pin.
//
// The Workflow sandbox forbids imports, so the trust-surface helpers (MODELS, the
// same-model tag, modelFamily, sameModelTag, parseArgs) are COPIED between scripts.
// This test makes the "copied verbatim" comment a gate: the copies must stay
// byte-identical (parseArgs may differ ONLY by its own script name in the error
// string). A divergent edit to either copy turns this red.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPTS = ["workflows/verify.js", "workflows/audit.js"].map((p) => ({
  path: p,
  text: readFileSync(join(root, p), "utf-8"),
}));

function extract(text, name, path) {
  const fn = text.match(new RegExp(`^function ${name}\\([^)]*\\) \\{[\\s\\S]*?^\\}`, "m"));
  if (fn) return fn[0];
  const c = text.match(new RegExp(`^const ${name} =[ \\n][\\s\\S]*?;$`, "m"));
  if (c) return c[0];
  assert.fail(`${name} not found in ${path}`);
}

for (const name of ["MODELS", "SAME_MODEL_TAG", "modelFamily", "sameModelTag"]) {
  test(`drift pin: ${name} is byte-identical across the workflow scripts`, () => {
    const [a, b] = SCRIPTS.map((s) => extract(s.text, name, s.path));
    assert.equal(a, b, `${name} has drifted between verify.js and audit.js`);
  });
}

test("drift pin: parseArgs differs only by its own script name", () => {
  const norm = (s) => s.replace(/\b(verify|audit) args\b/g, "SCRIPT args");
  const [a, b] = SCRIPTS.map((s) => extract(s.text, "parseArgs", s.path));
  assert.equal(norm(a), norm(b), "parseArgs has drifted beyond the script-name string");
});
