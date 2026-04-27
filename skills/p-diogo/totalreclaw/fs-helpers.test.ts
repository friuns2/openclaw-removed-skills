/**
 * Tests for fs-helpers.ts (3.0.8 consolidation).
 *
 * Covers every helper's happy path, missing-file fallback, and
 * corrupt-input fallback. Isolates all disk I/O under a `mkdtempSync`
 * temp dir so the real `~/.totalreclaw/` is never touched.
 *
 * Run with: npx tsx fs-helpers.test.ts
 *
 * TAP-style output, no jest dependency.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  ensureMemoryHeaderFile,
  loadCredentialsJson,
  writeCredentialsJson,
  deleteCredentialsFile,
  isRunningInDocker,
  deleteFileIfExists,
  type CredentialsFile,
} from './fs-helpers.js';

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

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'tr-fs-helpers-test-'));

const TEST_HEADER = '# Memory\n\n> TotalReclaw is active. Test header.\n\n';

// ---------------------------------------------------------------------------
// loadCredentialsJson — missing, valid, corrupt
// ---------------------------------------------------------------------------

{
  const credsPath = path.join(TMP, 'missing-creds.json');
  assertEq(
    loadCredentialsJson(credsPath),
    null,
    'loadCredentialsJson: returns null when file missing',
  );
}

{
  const credsPath = path.join(TMP, 'valid-creds.json');
  const payload: CredentialsFile = {
    userId: 'u123',
    salt: 'YWJjZGVmZw==',
    mnemonic: 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
  };
  fs.writeFileSync(credsPath, JSON.stringify(payload));
  const loaded = loadCredentialsJson(credsPath);
  assert(loaded !== null, 'loadCredentialsJson: returns non-null for valid JSON');
  assertEq(loaded?.userId, 'u123', 'loadCredentialsJson: userId round-trips');
  assertEq(loaded?.salt, 'YWJjZGVmZw==', 'loadCredentialsJson: salt round-trips');
  assertEq(
    loaded?.mnemonic?.split(/\s+/).length,
    12,
    'loadCredentialsJson: mnemonic word count preserved',
  );
}

{
  const credsPath = path.join(TMP, 'corrupt-creds.json');
  fs.writeFileSync(credsPath, '{not valid json');
  assertEq(
    loadCredentialsJson(credsPath),
    null,
    'loadCredentialsJson: returns null on corrupt JSON (no throw)',
  );
}

{
  const credsPath = path.join(TMP, 'empty-creds.json');
  fs.writeFileSync(credsPath, '');
  assertEq(
    loadCredentialsJson(credsPath),
    null,
    'loadCredentialsJson: returns null on empty file',
  );
}

// ---------------------------------------------------------------------------
// writeCredentialsJson — happy path, creates parent dir, file mode
// ---------------------------------------------------------------------------

{
  const credsPath = path.join(TMP, 'write-simple.json');
  const ok = writeCredentialsJson(credsPath, { userId: 'u1', salt: 'abc' });
  assert(ok, 'writeCredentialsJson: returns true on success');
  assert(fs.existsSync(credsPath), 'writeCredentialsJson: creates file');
  const roundTrip = loadCredentialsJson(credsPath);
  assertEq(roundTrip?.userId, 'u1', 'writeCredentialsJson: round-trips userId');
  assertEq(roundTrip?.salt, 'abc', 'writeCredentialsJson: round-trips salt');
}

{
  // Writes the deep parent dir if absent.
  const deepDir = path.join(TMP, 'a', 'b', 'c');
  const credsPath = path.join(deepDir, 'credentials.json');
  assert(!fs.existsSync(deepDir), 'precondition: deep parent dir does not exist');
  const ok = writeCredentialsJson(credsPath, { userId: 'u-deep' });
  assert(ok, 'writeCredentialsJson: succeeds when parent dir is missing');
  assert(fs.existsSync(credsPath), 'writeCredentialsJson: creates nested dir + file');
}

{
  // File mode should be 0o600 on platforms that support POSIX mode bits.
  const credsPath = path.join(TMP, 'mode-creds.json');
  writeCredentialsJson(credsPath, { userId: 'u-mode' });
  const stat = fs.statSync(credsPath);
  // Mask to the low 9 bits (permission bits); on non-POSIX this may be 0o666.
  // Only enforce on POSIX-ish platforms.
  if (process.platform !== 'win32') {
    const mode = stat.mode & 0o777;
    assertEq(mode, 0o600, 'writeCredentialsJson: file mode is 0o600 on POSIX');
  } else {
    assert(true, 'writeCredentialsJson: file mode check skipped on win32');
  }
}

// ---------------------------------------------------------------------------
// deleteCredentialsFile — existing, missing
// ---------------------------------------------------------------------------

{
  const credsPath = path.join(TMP, 'delete-me.json');
  writeCredentialsJson(credsPath, { userId: 'to-be-deleted' });
  assert(fs.existsSync(credsPath), 'precondition: file exists before delete');
  assertEq(deleteCredentialsFile(credsPath), true, 'deleteCredentialsFile: returns true when file existed');
  assert(!fs.existsSync(credsPath), 'deleteCredentialsFile: removes file');
  assertEq(
    deleteCredentialsFile(credsPath),
    false,
    'deleteCredentialsFile: returns false when file missing',
  );
}

// ---------------------------------------------------------------------------
// ensureMemoryHeaderFile — create, unchanged, updated
// ---------------------------------------------------------------------------

{
  const workspace = path.join(TMP, 'ws-create');
  const memoryMd = path.join(workspace, 'MEMORY.md');
  assert(!fs.existsSync(memoryMd), 'precondition: MEMORY.md does not exist');
  assertEq(
    ensureMemoryHeaderFile(workspace, TEST_HEADER),
    'created',
    'ensureMemoryHeaderFile: returns "created" when file missing',
  );
  assert(fs.existsSync(memoryMd), 'ensureMemoryHeaderFile: creates MEMORY.md');
  const content = fs.readFileSync(memoryMd, 'utf-8');
  assertEq(content, TEST_HEADER, 'ensureMemoryHeaderFile: wrote header exactly');
}

{
  const workspace = path.join(TMP, 'ws-unchanged');
  fs.mkdirSync(workspace, { recursive: true });
  fs.writeFileSync(
    path.join(workspace, 'MEMORY.md'),
    TEST_HEADER + '\n# User notes\nHello.\n',
  );
  assertEq(
    ensureMemoryHeaderFile(workspace, TEST_HEADER),
    'unchanged',
    'ensureMemoryHeaderFile: returns "unchanged" when marker already present',
  );
  const content = fs.readFileSync(path.join(workspace, 'MEMORY.md'), 'utf-8');
  assert(content.includes('# User notes'), 'ensureMemoryHeaderFile: does not rewrite user content');
}

{
  const workspace = path.join(TMP, 'ws-update');
  fs.mkdirSync(workspace, { recursive: true });
  const userContent = '# User notes\nHello.\n';
  fs.writeFileSync(path.join(workspace, 'MEMORY.md'), userContent);
  assertEq(
    ensureMemoryHeaderFile(workspace, TEST_HEADER),
    'updated',
    'ensureMemoryHeaderFile: returns "updated" when marker missing',
  );
  const content = fs.readFileSync(path.join(workspace, 'MEMORY.md'), 'utf-8');
  assertEq(
    content,
    TEST_HEADER + userContent,
    'ensureMemoryHeaderFile: prepends header without clobbering user content',
  );
}

{
  // Custom marker substring — caller controls what to look for.
  const workspace = path.join(TMP, 'ws-custom-marker');
  fs.mkdirSync(workspace, { recursive: true });
  fs.writeFileSync(path.join(workspace, 'MEMORY.md'), 'my-custom-marker\nexisting body\n');
  assertEq(
    ensureMemoryHeaderFile(workspace, '# header\n', 'my-custom-marker'),
    'unchanged',
    'ensureMemoryHeaderFile: respects caller-supplied marker substring',
  );
}

{
  // Error path: pass a path that cannot be created (e.g. a file where we
  // expect a directory). The helper should swallow and return 'error'.
  const blocker = path.join(TMP, 'blocker.txt');
  fs.writeFileSync(blocker, 'I am a file where a dir is expected');
  const memoryParent = path.join(blocker, 'MEMORY.md'); // blocker is a file, not a dir
  const workspaceAsFile = blocker; // workspace == file → join() gives path under file
  const outcome = ensureMemoryHeaderFile(workspaceAsFile, TEST_HEADER);
  assertEq(outcome, 'error', 'ensureMemoryHeaderFile: returns "error" on unrecoverable I/O failure');
  // Keep `memoryParent` referenced so no unused-var lint warning.
  void memoryParent;
}

// ---------------------------------------------------------------------------
// isRunningInDocker — returns boolean, never throws
// ---------------------------------------------------------------------------

{
  const r = isRunningInDocker();
  assert(typeof r === 'boolean', 'isRunningInDocker: returns a boolean');
  // We intentionally do NOT assert a specific value — the helper must
  // tolerate running on bare metal, in CI, or inside a real container.
  // Under a standard macOS dev box it will be `false`; inside the
  // OpenClaw Docker harness it will be `true`. Both are correct.
}

// ---------------------------------------------------------------------------
// deleteFileIfExists — existing, missing, directory-like path
// ---------------------------------------------------------------------------

{
  const filePath = path.join(TMP, 'to-delete.txt');
  fs.writeFileSync(filePath, 'bye');
  assert(fs.existsSync(filePath), 'precondition: file exists');
  deleteFileIfExists(filePath);
  assert(!fs.existsSync(filePath), 'deleteFileIfExists: removes existing file');
}

{
  // Missing file → no throw
  const filePath = path.join(TMP, 'never-existed.txt');
  try {
    deleteFileIfExists(filePath);
    assert(true, 'deleteFileIfExists: no throw on missing file');
  } catch {
    assert(false, 'deleteFileIfExists: no throw on missing file');
  }
}

{
  // Directory path → swallowed (best-effort semantics)
  const dirPath = path.join(TMP, 'not-a-file');
  fs.mkdirSync(dirPath);
  try {
    deleteFileIfExists(dirPath);
    assert(true, 'deleteFileIfExists: no throw when path points to a directory');
  } catch {
    assert(false, 'deleteFileIfExists: no throw when path points to a directory');
  }
  // Directory may still exist — deleteFileIfExists makes no guarantee for dirs.
  // The contract is only "no throw + best-effort on files".
  fs.rmSync(dirPath, { recursive: true, force: true });
}

// ---------------------------------------------------------------------------
// Integration: round-trip write → load → delete → reload
// ---------------------------------------------------------------------------

{
  const credsPath = path.join(TMP, 'integration-creds.json');
  const creds: CredentialsFile = { userId: 'u-int', salt: 'AAAA', mnemonic: 'abc def ghi' };
  assert(writeCredentialsJson(credsPath, creds), 'integration: write succeeds');
  const loaded = loadCredentialsJson(credsPath);
  assertEq(loaded?.mnemonic, 'abc def ghi', 'integration: mnemonic round-trips through disk');
  assert(deleteCredentialsFile(credsPath), 'integration: delete returns true');
  assertEq(
    loadCredentialsJson(credsPath),
    null,
    'integration: load after delete returns null',
  );
}

// ---------------------------------------------------------------------------
// Cleanup + summary
// ---------------------------------------------------------------------------

try { fs.rmSync(TMP, { recursive: true, force: true }); } catch { /* ignore */ }

console.log(`\n# ${passed}/${passed + failed} passed`);
if (failed > 0) {
  console.log('\nSOME TESTS FAILED');
  process.exit(1);
}
console.log('\nALL TESTS PASSED');
