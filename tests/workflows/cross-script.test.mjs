// tests/workflows/cross-script.test.mjs — the cross-script drift pin.
//
// The Workflow sandbox forbids imports, so the trust-surface helpers (MODELS, the
// same-model tag, the unresolved-family tag, the known-families list, modelFamily,
// sameModelTag, parseArgs) are COPIED between scripts. This test makes the "copied
// verbatim" comment a gate: the copies must stay byte-identical (parseArgs may differ
// ONLY by its own script name in the error string). A divergent edit to any copy turns
// this red. As of Slice 4b, qa.js carries the full cross-model contract (MODELS +
// SAME_MODEL_TAG + modelFamily + sameModelTag + parseArgs) — the same set verify.js /
// audit.js define. As of Slice 5b, build-item.js carries the cross-model fold helpers it
// actually uses (SAME_MODEL_TAG + modelFamily + sameModelTag + parseArgs) but NOT MODELS —
// it spawns no judge directly (the pins live in the verify.js / qa.js children it calls),
// so an unused MODELS copy here would be dead code. As of plan 0013 the third disclosure
// state lands: UNRESOLVED_FAMILY_TAG + KNOWN_FAMILIES join the pinned set (modelFamily now
// derives its regex from KNOWN_FAMILIES, and sameModelTag references UNRESOLVED_FAMILY_TAG —
// so every script that copies those helpers must carry both new constants byte-identical).
// The pin checks only the helpers a script DEFINES, so build-item.js joins the pin for the
// six it carries.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const ALL_SCRIPTS = [
  "engine/verify.js",
  "engine/audit.js",
  "engine/qa.js",
  "engine/build-item.js",
].map((p) => ({
  path: p,
  text: readFileSync(join(root, p), "utf-8"),
}));

// The `async ` prefix is accepted so a shared SPAWN wrapper (agentWithNamespaceFallback, 0041
// S10b) is extractable by the same `^function`-to-closing-brace branch. Without it the wrapper
// silently extracts as `null` and drops out of the pinned set entirely.
function extract(text, name, path) {
  const fn = text.match(new RegExp(`^(?:async )?function ${name}\\([^)]*\\) \\{[\\s\\S]*?^\\}`, "m"));
  if (fn) return fn[0];
  const c = text.match(new RegExp(`^const ${name} =[ \\n][\\s\\S]*?;$`, "m"));
  if (c) return c[0];
  return null;
}

// Each copied helper must stay byte-identical across EVERY script that defines it. A script may
// legitimately not define a helper (a script that spawns no judge would not carry the cross-model
// helpers). The pin requires the helper to be present in ≥2 scripts (so it IS actually pinned),
// then asserts byte-identity across exactly those.
function scriptsDefining(name) {
  return ALL_SCRIPTS.map((s) => ({ path: s.path, code: extract(s.text, name, s.path) })).filter(
    (s) => s.code !== null,
  );
}

const PINNED_HELPERS = [
  "MODELS",
  "SAME_MODEL_TAG",
  "UNRESOLVED_FAMILY_TAG",
  "KNOWN_FAMILIES",
  "modelFamily",
  "sameModelTag",
  "nsAgent",
  // 0041 S10b (D6): the namespace-fallback set. AGENT_NAMESPACE is the ONE source nsAgent adds
  // and bareAgentType strips; namespaceFallbackNotice is the logged trust-boundary wording; the
  // spawn wrapper itself is copied byte-identical across all four scripts. A helper is pinned
  // ONLY if its name appears in this array -- a new shared helper is unpinned until it is added.
  "AGENT_NAMESPACE",
  "bareAgentType",
  "namespaceFallbackNotice",
  "agentWithNamespaceFallback",
];

for (const name of PINNED_HELPERS) {
  test(`drift pin: ${name} is byte-identical across every workflow script that defines it`, () => {
    const defs = scriptsDefining(name);
    assert.ok(defs.length >= 2, `${name} must be pinned across ≥2 scripts (found in: ${defs.map((d) => d.path).join(", ") || "none"})`);
    const [first, ...rest] = defs;
    for (const other of rest) {
      assert.equal(other.code, first.code, `${name} has drifted between ${first.path} and ${other.path}`);
    }
  });
}

// -----------------------------------------------------------------------------
// The extractor's own integrity (0041 S10b, trap 4) -- WITHOUT this the drift pin can pass
// while pinning almost nothing.
//
// The `const` branch is LAZY: `^const <name> =[ \n][\s\S]*?;$` stops at the FIRST line ending
// in `;`. Rewrite a single-expression arrow as a multi-statement body and the pin silently
// compares a truncated FRAGMENT across all four files -- green, and guarding nothing. A
// truncated fragment is detectable: its brackets do not balance.
// -----------------------------------------------------------------------------
function balanced(code) {
  const counts = { "{": 0, "}": 0, "(": 0, ")": 0, "[": 0, "]": 0 };
  for (const ch of code) {
    if (ch in counts) counts[ch] += 1;
  }
  return counts["{"] === counts["}"] && counts["("] === counts[")"] && counts["["] === counts["]"];
}

test("drift-pin integrity: every extracted helper is a WHOLE declaration, not a lazily-truncated fragment", () => {
  let checked = 0;
  for (const name of PINNED_HELPERS.concat(["parseArgs"])) {
    const defs = scriptsDefining(name);
    assert.ok(defs.length >= 2, `${name} is defined in fewer than 2 scripts -- the pin is vacuous`);
    for (const def of defs) {
      assert.ok(
        balanced(def.code),
        `${name} extracted from ${def.path} has unbalanced brackets -- the extractor truncated it, ` +
          `so byte-identity is being asserted over a FRAGMENT:\n${def.code}`,
      );
      checked += 1;
    }
  }
  // Corpus floor: a regex change that silently stopped matching must not pass vacuously.
  assert.ok(checked >= 20, `expected >= 20 extracted declarations to check, got ${checked}`);
});

test("drift-pin integrity: nsAgent stays the SINGLE-EXPRESSION const shape the extractor needs", () => {
  const defs = scriptsDefining("nsAgent");
  assert.equal(defs.length, 4, "nsAgent must be defined in all four engine scripts");
  for (const def of defs) {
    assert.ok(
      !def.code.includes("\n"),
      `${def.path}: nsAgent must stay a ONE-LINE single-expression const -- a multi-statement ` +
        `arrow body makes the drift pin compare a truncated fragment (trap 4):\n${def.code}`,
    );
    assert.match(def.code, /^const nsAgent = \(name\) => `.*`;$/, `${def.path}: unexpected nsAgent shape`);
  }
});

test("drift pin: parseArgs differs only by its own script name across all scripts", () => {
  const norm = (s) => s.replace(/\b(verify|audit|qa|build-item) args\b/g, "SCRIPT args");
  const defs = scriptsDefining("parseArgs");
  assert.ok(defs.length >= 2, "parseArgs must be pinned across ≥2 scripts");
  const [first, ...rest] = defs;
  for (const other of rest) {
    assert.equal(
      norm(other.code),
      norm(first.code),
      `parseArgs has drifted beyond the script-name string between ${first.path} and ${other.path}`,
    );
  }
});
