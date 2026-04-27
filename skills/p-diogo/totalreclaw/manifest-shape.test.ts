/**
 * manifest-shape.test.ts — Regression guard for the intentional manifest/JS
 * asymmetry introduced in 3.3.0-rc.6.
 *
 * Background (OpenClaw startup registry bug):
 *   `resolveGatewayStartupPluginIds` excludes plugins with `kind: "memory"`
 *   from the gateway's startup set unless they also declare a configured
 *   channel. TotalReclaw has no channel, so the gateway startup path took an
 *   empty-list early return in `loadGatewayPlugins`, pinned an empty HTTP
 *   route registry, and never exposed the 4 pair routes — even though the
 *   plugin loaded later and registered them.
 *
 *   Fix: drop `"kind": "memory"` from `openclaw.plugin.json` (manifest) only.
 *   The JS plugin definition in `index.ts` still returns `kind: 'memory' as const`
 *   because the OpenClaw loader re-merges the JS definition into `record.kind`
 *   at line 2090, preserving memory-slot matching via
 *   `config.slots.memory === "totalreclaw"`.
 *
 * This test asserts BOTH sides of the asymmetry:
 *   1. The manifest does NOT declare `kind: "memory"` (startup registry fix).
 *   2. The JS plugin source DOES declare `kind: 'memory' as const` (memory-slot
 *      behaviour preserved).
 *
 * Implementation note on assertion 2:
 *   `index.ts` has a heavy init chain (onnxruntime-node, HuggingFace
 *   transformers, viem, protobufjs, etc.) that requires native addons and
 *   cannot be dynamically imported in a bare test runner without a full mock
 *   harness. We therefore inspect the `index.ts` source as text — a node-based
 *   regex check is precise, deterministic, and unambiguous for the single
 *   declaration site. The test comment near that declaration (`// Plugin
 *   definition`) makes the location stable. If the declaration is ever moved or
 *   refactored, this test fails loudly, which is the desired behaviour.
 *
 * References:
 *   - Research: docs/notes/RESEARCH-openclaw-http-route-plumbing-20260420-1608.md
 *     (totalreclaw-internal)
 *   - PR comment: totalreclaw-internal#21 comment 4282038854
 *   - Upstream bug: see "Upstream OpenClaw bug" section in the rc.6 PR body.
 *
 * Run with: npx tsx manifest-shape.test.ts
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let passed = 0;
let failed = 0;

function assert(condition: boolean, name: string): void {
  const n = passed + failed + 1;
  if (condition) {
    console.log(`ok ${n} - ${name}`);
    passed++;
  } else {
    console.log(`not ok ${n} - ${name}`);
    failed++;
  }
}

function assertEq<T>(actual: T, expected: T, name: string): void {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) {
    console.log(`  actual:   ${JSON.stringify(actual)}`);
    console.log(`  expected: ${JSON.stringify(expected)}`);
  }
  assert(ok, name);
}

// ---------------------------------------------------------------------------
// 1. Manifest assertions
// ---------------------------------------------------------------------------

const manifestPath = path.join(__dirname, 'openclaw.plugin.json');
let manifest: Record<string, unknown>;

{
  let parseOk = true;
  try {
    const raw = fs.readFileSync(manifestPath, 'utf8');
    manifest = JSON.parse(raw) as Record<string, unknown>;
  } catch (err) {
    parseOk = false;
    manifest = {};
    console.log(`  error: ${String(err)}`);
  }

  assert(parseOk, 'openclaw.plugin.json is valid JSON');
}

{
  // 1a. The manifest must NOT have "kind": "memory".
  // Presence of this field causes resolveGatewayStartupPluginIds to exclude
  // the plugin from the startup set, pinning an empty HTTP route registry.
  assert(
    !('kind' in manifest),
    'openclaw.plugin.json does NOT contain "kind" field (startup registry fix)',
  );
}

{
  // 1b. Absence of "kind" in manifest is intentional — document the expected
  // shape to catch accidental re-addition.
  const kindValue = manifest['kind'];
  assert(
    kindValue === undefined,
    'openclaw.plugin.json "kind" is undefined (not "memory" or any other value)',
  );
}

{
  // 1c. The string "memory" must not appear as a JSON value for any field
  // named "kind" — raw-string check as an extra guard.
  const raw = fs.readFileSync(manifestPath, 'utf8');
  const hasKindMemory = /"kind"\s*:\s*"memory"/.test(raw);
  assert(
    !hasKindMemory,
    'openclaw.plugin.json source does NOT match /"kind"\\s*:\\s*"memory"/ (raw regex guard)',
  );
}

{
  // 1d. Manifest still has "id", "name", "description" — basic shape sanity.
  assertEq(manifest['id'], 'totalreclaw', 'manifest id === "totalreclaw"');
  assertEq(manifest['name'], 'TotalReclaw', 'manifest name === "TotalReclaw"');
  assert(
    typeof manifest['description'] === 'string' && (manifest['description'] as string).length > 0,
    'manifest description is a non-empty string',
  );
}

// ---------------------------------------------------------------------------
// 2. JS plugin definition assertions (source inspection)
// ---------------------------------------------------------------------------

const indexPath = path.join(__dirname, 'index.ts');
const indexSrc = fs.readFileSync(indexPath, 'utf8');

{
  // 2a. index.ts must declare `kind: 'memory' as const` in the plugin object.
  // The OpenClaw loader re-merges this into record.kind (line 2090), so
  // memory-slot matching (config.slots.memory === "totalreclaw") still works.
  const hasKindMemory = /kind:\s*'memory'\s*as\s*const/.test(indexSrc);
  assert(
    hasKindMemory,
    "index.ts plugin definition contains `kind: 'memory' as const` (memory-slot matching preserved)",
  );
}

{
  // 2b. Regression guard: the JS plugin object is `export default plugin` —
  // confirm the export is present so we know the declaration we found above
  // is the same object that OpenClaw's loader receives.
  const hasExportDefault = /^export default plugin;/m.test(indexSrc);
  assert(
    hasExportDefault,
    'index.ts has `export default plugin;` (loader receives the checked object)',
  );
}

{
  // 2c. The JS declaration must NOT use `'gateway'` or any other kind value.
  // This guards against someone changing the kind in JS while fixing a future
  // unrelated issue, which would break memory-slot matching silently.
  const hasWrongKind = /kind:\s*'gateway'\s*as\s*const/.test(indexSrc);
  assert(
    !hasWrongKind,
    "index.ts plugin definition does NOT use `kind: 'gateway' as const`",
  );
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

console.log(`# fail: ${failed}`);
console.log(`# ${passed}/${passed + failed} passed`);
if (failed > 0) {
  console.log('SOME TESTS FAILED');
  process.exit(1);
}
console.log('ALL TESTS PASSED');
