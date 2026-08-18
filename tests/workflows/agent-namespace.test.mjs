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
  "runtime-qa",
  "retrospect-harvester",
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

// =============================================================================
// 0041 Slice 10b (D6) -- the namespace FALLBACK, pinned at source level.
//
// Namespaced ids stay what the engine WRITES; the fallback is a single bare retry on a THROWN
// spawn failure, so a project-local dogfood session resolves without the source shim the
// v0.5.0 eval baseline had to carry. Two properties have to hold together:
//   (1) every namespaced spawn actually ROUTES through the wrapper (an unrouted site
//       re-creates the defect for exactly the spawn it guards), and
//   (2) the bare name is DERIVED from the namespaced id at runtime -- a literal table would
//       turn the bare-name guard above red, which is the construction that forbids it.
// =============================================================================

// The control-flow region of an engine script: everything below the line-anchored end-helpers
// marker. verify.js's panelRoster also names agents via nsAgent(), but that is roster METADATA
// inside the helpers block, not a spawn -- scoping to the control flow excludes it.
function controlFlowOf(script) {
  const src = readEngine(script);
  const marks = src.match(/^\/\/ --- end helpers ---$/gm) || [];
  assert.equal(marks.length, 1, `expected exactly ONE line-anchored end-helpers marker in engine/${script}`);
  return src.slice(src.search(/^\/\/ --- end helpers ---$/m));
}

// The index of the LAST `<name>(` call opener strictly before `upto`, ignoring matches that are
// part of a longer identifier or a property access (so `agentWithNamespaceFallback(` and
// `guardedPanelAgent(` are never mistaken for a bare `agent(`).
function lastCallBefore(src, upto, name) {
  const re = new RegExp(`(^|[^A-Za-z0-9_$.])${esc(name)}\\(`, "g");
  let last = -1;
  let m;
  while ((m = re.exec(src)) !== null) {
    const idx = m.index + m[1].length;
    if (idx >= upto) break;
    last = idx;
  }
  return last;
}

// The callers that are allowed to hold a namespaced agent id: the fallback wrapper itself and
// the wrappers that delegate to it (each pinned separately below).
const ROUTED_CALLERS = [
  "agentWithNamespaceFallback",
  "guardedPanelAgent",
  "guardedAgent",
  "spawnJudge",
  "attempt",
];

// Corpus floors -- a scan that silently stopped finding spawn sites must fail loud, not pass
// vacuously. These are FLOORS (>=), so adding a spawn site does not turn them red.
const NAMESPACED_SPAWN_FLOOR = {
  "verify.js": 4,
  "audit.js": 8,
  "qa.js": 3,
  "build-item.js": 1,
};

for (const script of ENGINE_SCRIPTS) {
  test(`namespace fallback: every namespaced spawn in engine/${script} routes through the fallback wrapper`, () => {
    const flow = controlFlowOf(script);
    const sites = [];
    const re = /nsAgent\("/g;
    let m;
    while ((m = re.exec(flow)) !== null) {
      sites.push(m.index);
    }
    assert.ok(
      sites.length >= NAMESPACED_SPAWN_FLOOR[script],
      `engine/${script}: expected >= ${NAMESPACED_SPAWN_FLOOR[script]} namespaced spawn sites in the control flow, found ${sites.length}`,
    );
    for (const at of sites) {
      const bare = lastCallBefore(flow, at, "agent");
      const routed = Math.max(...ROUTED_CALLERS.map((n) => lastCallBefore(flow, at, n)));
      assert.ok(
        routed > bare,
        `engine/${script}: the namespaced spawn at offset ${at} is handed to a BARE agent( call ` +
          `(nearest routed caller at ${routed}, bare agent( at ${bare}) -- every namespaced spawn ` +
          `must go through agentWithNamespaceFallback, or that spawn has no fallback at all:\n` +
          flow.slice(Math.max(0, at - 200), at + 60),
      );
    }
  });

  test(`namespace fallback: engine/${script} derives the bare name -- no hardcoded agent-name table`, () => {
    const flow = controlFlowOf(script);
    const wrapper = flow.match(/^async function agentWithNamespaceFallback\([\s\S]*?^\}/m);
    assert.ok(wrapper, `engine/${script}: agentWithNamespaceFallback not found in the control flow`);
    assert.match(wrapper[0], /bareAgentType\(/, `engine/${script}: the fallback name must be DERIVED at runtime`);
    for (const name of CUSTOM_AGENTS) {
      assert.ok(
        !wrapper[0].includes(name),
        `engine/${script}: the fallback wrapper names '${name}' -- the bare name must be derived from ` +
          `the namespaced id, never enumerated (a literal table also turns the bare-name guard above red)`,
      );
    }
  });

  test(`namespace fallback: engine/${script}'s judge attempt closure delegates to the wrapper`, () => {
    const flow = controlFlowOf(script);
    const attempts = flow.match(/const attempt = async \(opts\) => \{[\s\S]*?^  \};/gm) || [];
    if (attempts.length === 0) {
      // build-item.js spawns no judge directly -- nothing to delegate.
      assert.equal(script, "build-item.js", `engine/${script}: expected an attempt closure to pin`);
      return;
    }
    for (const body of attempts) {
      assert.match(
        body,
        /agentWithNamespaceFallback\(prompt, opts\)/,
        `engine/${script}: an attempt closure still calls the raw agent primitive -- its judge spawn has no namespace fallback`,
      );
    }
  });
}

test("namespace fallback: the retry is NOT a model respawn in any engine script", () => {
  for (const script of ENGINE_SCRIPTS) {
    const flow = controlFlowOf(script);
    const wrapper = flow.match(/^async function agentWithNamespaceFallback\([\s\S]*?^\}/m);
    assert.ok(wrapper, `engine/${script}: agentWithNamespaceFallback not found`);
    const body = wrapper[0];
    assert.ok(
      !/forcedSameModel/.test(body),
      `engine/${script}: a namespace retry must never touch forcedSameModel -- that flag feeds the same-model disclosure`,
    );
    assert.ok(
      !/:respawn/.test(body),
      `engine/${script}: a namespace retry must never reuse the :respawn label -- the run log could not tell the two apart`,
    );
    assert.match(body, /:ns-fallback/, `engine/${script}: the namespace retry needs its own label`);
    assert.match(
      body,
      /\{ \.\.\.opts, agentType: bare/,
      `engine/${script}: the retry must spread the ORIGINAL opts so the judge model: pin survives it`,
    );
  }
});

test('agent namespace: the general-purpose built-in stays BARE where it is spawned (qa.js, build-item.js)', () => {
  // qa.js spawns general-purpose for the mechanical boot/teardown lifecycle (the DRIVE step is the
  // namespaced runtime-qa specialist); build-item.js spawns it for the gates stage. These remaining
  // uses are built-ins — the bare double-quoted literal must remain.
  for (const script of ["qa.js", "build-item.js"]) {
    const src = readEngine(script);
    assert.ok(
      src.includes('"general-purpose"'),
      `engine/${script}: expected the bare built-in "general-purpose" spawn to remain`,
    );
  }
});

// D6's headline claim is "every ENGINE spawn of a bundled agent routes through the wrapper".
// The positional pin above answers "is each nsAgent( site routed?", which a one-line hoist of the
// id into a const defeats. This asks the INVERSE, which a hoist cannot dodge: does any raw agent(
// outside the wrapper name anything but a built-in? (0041 S10b Stage-7, measured survivor MX4.)
const BUILT_INS = ["general-purpose", "Explore", "Plan"];
function decommented(src) {
  return src.replace(/^(\s*)\/\/.*$/gm, "$1").replace(/([^:"'`])\/\/.*$/gm, "$1");
}
test("namespace fallback: no RAW agent() spawn outside the wrapper names anything but a BUILT-IN", () => {
  let checked = 0;
  for (const script of ENGINE_SCRIPTS) {
    const flow = decommented(controlFlowOf(script));
    const wrapper = flow.match(/^async function agentWithNamespaceFallback\([\s\S]*?^\}/m);
    assert.ok(wrapper, `engine/${script}: agentWithNamespaceFallback not found`);
    const wStart = flow.indexOf(wrapper[0]);
    const wEnd = wStart + wrapper[0].length;
    const re = /(^|[^A-Za-z0-9_$.])agent\(/g;
    let m;
    while ((m = re.exec(flow)) !== null) {
      const at = m.index + m[1].length;
      if (at >= wStart && at < wEnd) continue;
      const opts = flow.slice(at, at + 400);
      assert.ok(
        BUILT_INS.some((b) => opts.includes(`"${b}"`)),
        `engine/${script}: a RAW agent( spawn outside agentWithNamespaceFallback names no BUILT-IN ` +
          `-- it has no namespace fallback:\n${opts.slice(0, 220)}`,
      );
      checked += 1;
    }
  }
  assert.ok(checked >= 3, `expected >= 3 raw built-in spawn sites across the engine, got ${checked}`);
});
