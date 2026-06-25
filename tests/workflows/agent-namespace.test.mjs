// tests/workflows/agent-namespace.test.mjs — the bundled-agent-namespace regression guard.
//
// Bundled agents resolve for an INSTALLED adopter only as `claugentic-dev-harness:<agent>`;
// bare names resolve only when this repo dogfoods with project-local `.claude/agents/`. So
// every CUSTOM-agent spawn in the engine scripts must be namespaced — bare names crashed
// /audit and /build for every adopter at the first spawn (an adopter pilot, 2026-06-15).
// Built-ins (`general-purpose`, `Explore`, `Plan`) stay BARE.
//
// This is a SOURCE-LEVEL guard (a verb-and-string grep, not a helper unit test): the
// load-bearing spawn sites live in the control-flow section below `// --- end helpers ---`,
// which the extract-and-eval harness never exercises — and two of verify.js's judge spawns
// pass the agentType as a POSITIONAL arg, not an `agentType:` object key, so an `agentType:`
// grep would miss them. The technique is robust to both shapes: remove every
// `nsAgent("<name>")` substring, then assert NO bare double-quoted `"<name>"` remains. (The
// Stage-9 lesson→gate for this class of bug.)

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, "..", "..");

// Every engine script that spawns agents.
const ENGINE_SCRIPTS = ["audit.js", "verify.js", "build-item.js", "qa.js"];

// The full set of this plugin's CUSTOM bundled agents — the names that MUST be namespaced at
// every spawn site. (Built-ins like `general-purpose` are deliberately NOT in this set.)
const CUSTOM_AGENTS = [
  "synthesizer-gate",
  "implementer",
  "product-designer",
  "lens-reviewer",
  "yagni-sentinel",
  "finding-verifier",
  "honesty-reviewer",
];

function readEngine(name) {
  return readFileSync(join(REPO_ROOT, "engine", name), "utf8");
}

// Escape a literal for use inside a RegExp.
function esc(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

for (const script of ENGINE_SCRIPTS) {
  test(`agent namespace: every custom-agent spawn in engine/${script} is namespaced (no bare "<name>")`, () => {
    const src = readEngine(script);
    for (const name of CUSTOM_AGENTS) {
      // Strip every legitimate namespaced spawn `nsAgent("<name>")`, then assert the bare
      // double-quoted literal `"<name>"` is gone. Any residual is an un-namespaced spawn — the
      // exact bug this guards against. (A custom name appears elsewhere only inside comments and
      // backtick prompt strings, never as a standalone double-quoted literal, so nothing
      // legitimate is excluded.)
      const stripped = src.split(`nsAgent("${name}")`).join("");
      const bare = new RegExp(`"${esc(name)}"`);
      assert.ok(
        !bare.test(stripped),
        `engine/${script}: bare "${name}" found outside nsAgent(...) — every custom-agent spawn must be namespaced as nsAgent("${name}")`,
      );
    }
  });
}

test("agent namespace: built-ins are NEVER namespaced (no nsAgent(\"general-purpose\") in any engine script)", () => {
  for (const script of ENGINE_SCRIPTS) {
    const src = readEngine(script);
    assert.ok(
      !src.includes('nsAgent("general-purpose")'),
      `engine/${script}: general-purpose is a BUILT-IN and must stay bare — never nsAgent("general-purpose")`,
    );
  }
});

test('agent namespace: the general-purpose built-in stays BARE where it is spawned (qa.js, build-item.js)', () => {
  // qa.js spawns general-purpose for boot/drive/teardown; build-item.js for the gates stage.
  // These are built-ins — the bare double-quoted literal must remain.
  for (const script of ["qa.js", "build-item.js"]) {
    const src = readEngine(script);
    assert.ok(
      src.includes('"general-purpose"'),
      `engine/${script}: expected the bare built-in "general-purpose" spawn to remain`,
    );
  }
});
