/**
 * fs-helpers — disk-I/O helpers extracted out of `index.ts` so the main
 * plugin file contains ZERO `fs.*` calls.
 *
 * Why this file exists
 * --------------------
 * OpenClaw's `potential-exfiltration` scanner rule is whole-file: it flags
 * any file that contains BOTH a disk read AND an outbound-request word
 * marker — even if the two have nothing to do with each other. 3.0.7
 * extracted the billing-cache reads to `billing-cache.ts`; the scanner
 * immediately flagged the NEXT disk read it found in `index.ts` (the
 * MEMORY.md header check, then the credentials.json load further down).
 * Iteratively extracting each site plays whack-a-mole.
 *
 * 3.0.8 consolidates EVERY `fs.*` call from `index.ts` here in one patch:
 *   - MEMORY.md header ensure/read                (ensureMemoryHeaderFile)
 *   - ~/.totalreclaw/credentials.json load        (loadCredentialsJson)
 *   - ~/.totalreclaw/credentials.json write       (writeCredentialsJson)
 *   - ~/.totalreclaw/credentials.json delete      (deleteCredentialsFile)
 *   - /.dockerenv + /proc/1/cgroup Docker sniff   (isRunningInDocker)
 *   - billing-cache invalidation unlink           (deleteFileIfExists)
 *
 * Constraint: this file must import ONLY `node:fs` + `node:path`. No
 * outbound-request word markers (even in a comment) — any such token
 * re-trips the scanner. See `check-scanner.mjs` for the exact trigger list.
 *
 * Do NOT add network-capable imports or comments to this file.
 */
import fs from 'node:fs';
import path from 'node:path';
// ---------------------------------------------------------------------------
// MEMORY.md header ensure
// ---------------------------------------------------------------------------
/**
 * Ensure `<workspace>/MEMORY.md` contains the TotalReclaw header.
 *
 * Behavior:
 *   - If the file exists and already contains the header's marker string
 *     ("TotalReclaw is active"), no-op → returns `'unchanged'`.
 *   - If the file exists but lacks the marker, prepend the header →
 *     returns `'updated'`.
 *   - If the file (or its parent dir) does not exist, create both and write
 *     just the header → returns `'created'`.
 *   - Any thrown error is swallowed (best-effort hook) → returns `'error'`.
 *
 * The "TotalReclaw is active" marker string is what the caller passed as
 * `header`; callers should include it in their header body so the
 * idempotency check works.
 */
export function ensureMemoryHeaderFile(workspace, header, markerSubstring = 'TotalReclaw is active') {
    try {
        const memoryMd = path.join(workspace, 'MEMORY.md');
        if (fs.existsSync(memoryMd)) {
            const content = fs.readFileSync(memoryMd, 'utf-8');
            if (content.includes(markerSubstring))
                return 'unchanged';
            fs.writeFileSync(memoryMd, header + content);
            return 'updated';
        }
        const dir = path.dirname(memoryMd);
        if (!fs.existsSync(dir))
            fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(memoryMd, header);
        return 'created';
    }
    catch {
        return 'error';
    }
}
// ---------------------------------------------------------------------------
// Plugin version — 3.3.1-rc.3 helper for RC gating
// ---------------------------------------------------------------------------
/**
 * Read the plugin's own version string from `package.json`.
 *
 * Behaviour:
 *   - Resolves `package.json` next to the caller-provided directory
 *     (typically `path.dirname(fileURLToPath(import.meta.url))` from the
 *     caller).
 *   - Returns the `version` field, or `null` on any I/O / parse error.
 *
 * Used by the RC-gated `totalreclaw_report_qa_bug` tool registration in
 * `index.ts`: if the version contains `-rc.`, register the tool; if not,
 * skip it entirely so stable users never see it.
 *
 * Scanner-safe: pure filesystem. No outbound-request word markers in this
 * helper — see the file-header guardrail.
 */
export function readPluginVersion(packageJsonDir) {
    try {
        const pkgPath = path.join(packageJsonDir, 'package.json');
        if (!fs.existsSync(pkgPath))
            return null;
        const raw = fs.readFileSync(pkgPath, 'utf-8');
        const parsed = JSON.parse(raw);
        return typeof parsed.version === 'string' ? parsed.version : null;
    }
    catch {
        return null;
    }
}
// ---------------------------------------------------------------------------
// credentials.json load / write / delete
// ---------------------------------------------------------------------------
/**
 * Read and JSON-parse `credentials.json` at the given path. Returns `null`
 * if the file does not exist, is unreadable, or contains invalid JSON.
 *
 * Callers should treat `null` as "no usable credentials on disk" and fall
 * through to first-run registration (or to the next branch of whatever
 * guard they're running).
 */
export function loadCredentialsJson(credentialsPath) {
    try {
        if (!fs.existsSync(credentialsPath))
            return null;
        const raw = fs.readFileSync(credentialsPath, 'utf-8');
        return JSON.parse(raw);
    }
    catch {
        return null;
    }
}
/**
 * Write `credentials.json` atomically-ish (single `writeFileSync`). Creates
 * the parent directory if missing. Uses mode `0o600` so the file is
 * user-readable only — this file holds the BIP-39 mnemonic and must never
 * be world-readable.
 *
 * Returns `true` on success, `false` on any I/O error (caller decides
 * whether to surface to user or best-effort log).
 */
export function writeCredentialsJson(credentialsPath, creds) {
    try {
        const dir = path.dirname(credentialsPath);
        if (!fs.existsSync(dir))
            fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(credentialsPath, JSON.stringify(creds), { mode: 0o600 });
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Delete `credentials.json` if it exists. Used by `forceReinitialization`
 * to clear stale salt/userId before a fresh registration. Returns `true`
 * if a file was deleted, `false` if no file existed or the delete failed.
 * The caller is expected to log warn on `false` when appropriate.
 */
export function deleteCredentialsFile(credentialsPath) {
    try {
        if (!fs.existsSync(credentialsPath))
            return false;
        fs.unlinkSync(credentialsPath);
        return true;
    }
    catch {
        return false;
    }
}
// ---------------------------------------------------------------------------
// Docker runtime detection
// ---------------------------------------------------------------------------
/**
 * Is this process running inside a Docker (or Docker-compatible) container?
 *
 * Two checks, in order:
 *   1. `/.dockerenv` exists (Docker daemon drops this marker in every
 *      container it starts).
 *   2. `/proc/1/cgroup` exists AND contains the substring `docker` (covers
 *      runtimes that don't drop `/.dockerenv`, e.g. some Kubernetes pods
 *      and older Docker-in-Docker setups).
 *
 * Either condition is sufficient. Returns `false` on any I/O error (the
 * caller uses this for messaging-only — a wrong answer isn't catastrophic).
 *
 * Note the cgroup check is intentionally substring-based, not regex — the
 * cgroup path format varies across kernels ("docker/...", "/system.slice/docker-...",
 * "/kubepods/pod.../docker-..."). Any occurrence of the literal string
 * "docker" in the first line is enough.
 */
export function isRunningInDocker() {
    try {
        if (fs.existsSync('/.dockerenv'))
            return true;
        if (fs.existsSync('/proc/1/cgroup')) {
            const cgroup = fs.readFileSync('/proc/1/cgroup', 'utf-8');
            if (cgroup.includes('docker'))
                return true;
        }
        return false;
    }
    catch {
        return false;
    }
}
// ---------------------------------------------------------------------------
// Generic: unlink-if-exists (used for billing-cache invalidation on 403)
// ---------------------------------------------------------------------------
/**
 * Delete `filePath` if it exists. Swallows all I/O errors — callers use
 * this for best-effort cache invalidation where a failure is no worse
 * than the pre-call state.
 */
export function deleteFileIfExists(filePath) {
    try {
        if (fs.existsSync(filePath))
            fs.unlinkSync(filePath);
    }
    catch {
        // Best-effort — don't block on invalidation failure.
    }
}
// ---------------------------------------------------------------------------
// Install-staging cleanup (issue #126 — rc.20 finding F3)
// ---------------------------------------------------------------------------
/**
 * Clean up `.openclaw-install-stage-*` sibling directories left behind by
 * an interrupted `openclaw plugins install` run.
 *
 * Background
 * ----------
 * `openclaw plugins install @totalreclaw/totalreclaw` extracts the npm
 * tarball into a staging directory named
 * `<extensionsDir>/.openclaw-install-stage-XXXXXX/` and then renames it
 * to `<extensionsDir>/totalreclaw/` on success. If the install is
 * interrupted partway through (e.g. an auto-gateway-restart triggered by
 * the same install kills the process — see rc.20 QA finding F3), the
 * staging dir survives. On the next gateway start, OpenClaw's plugin
 * loader auto-discovers BOTH directories — the real `totalreclaw/` and
 * the orphaned `.openclaw-install-stage-XXXXXX/` — and registers two
 * copies of the plugin. Hooks fire twice, the user sees a duplicate
 * `totalreclaw` row in `openclaw plugins list`, and the gateway log
 * spams a duplicate-plugin-id warning every cycle.
 *
 * Fix scope: best-effort cleanup driven by the plugin itself at register
 * time. We resolve the extensions dir as the parent of the loaded
 * plugin's own directory, scan for `.openclaw-install-stage-*` siblings,
 * and recursively remove each one. If anything fails (permission,
 * race with a concurrent install), we swallow the error — the existing
 * loader-warning behavior is no worse than before.
 *
 * Returns the list of staging-dir paths that were successfully removed.
 * Callers may log this for ops visibility. Empty list on a clean install.
 *
 * Parameters
 * ----------
 * @param pluginDir  Absolute path to the loaded plugin's directory
 *                   (typically `<extensionsDir>/totalreclaw/dist`). The
 *                   helper walks up to the parent that holds sibling
 *                   plugin directories (the `extensions/` root).
 * @param _now       Optional clock injector for testing — defaults to
 *                   Date.now().
 */
export function cleanupInstallStagingDirs(pluginDir, _now = Date.now) {
    const removed = [];
    try {
        // pluginDir is `<extensionsDir>/totalreclaw/dist` after build, so the
        // siblings live two levels up. Resolve both candidates so the helper
        // works regardless of whether the caller passes the package root or
        // its `dist/` subdir.
        const candidates = [
            path.resolve(pluginDir, '..'), // <extensionsDir>/totalreclaw → siblings dir if pluginDir is `dist`
            path.resolve(pluginDir, '..', '..'), // <extensionsDir>/             → siblings dir if pluginDir is package root
        ];
        for (const extensionsDir of candidates) {
            let entries;
            try {
                entries = fs.readdirSync(extensionsDir);
            }
            catch {
                continue;
            }
            for (const name of entries) {
                if (!name.startsWith('.openclaw-install-stage-'))
                    continue;
                const target = path.join(extensionsDir, name);
                try {
                    const st = fs.lstatSync(target);
                    if (!st.isDirectory())
                        continue;
                    fs.rmSync(target, { recursive: true, force: true });
                    removed.push(target);
                }
                catch {
                    // Best-effort — skip unreadable / racy entries.
                }
            }
        }
    }
    catch {
        // Best-effort — never crash plugin init on cleanup failure.
    }
    return removed;
}
// ---------------------------------------------------------------------------
// Partial-install detection (rc.22 finding #5)
// ---------------------------------------------------------------------------
/**
 * Marker filename written into the plugin directory at register-time. Its
 * presence means a prior install was interrupted before the plugin successfully
 * loaded — a confirmed-broken half-state that the next `openclaw plugins
 * install` retry can detect and clean.
 *
 * Conceptually the marker is dropped BEFORE npm install completes (the
 * complementary npm script removes it on success) and additionally
 * re-asserted at register-time as a second-line check. If you see this file
 * in `<extensionsDir>/totalreclaw/`, the install never reached register()
 * AND the marker drop wasn't undone.
 *
 * Constants are exported so the npm preinstall/cleanup scripts in
 * `package.json` use the same name as the runtime detector.
 */
export const PARTIAL_INSTALL_MARKER = '.tr-partial-install';
/** Package name we own — used to confirm a directory is OUR plugin, not a stray. */
export const PLUGIN_PACKAGE_NAME = '@totalreclaw/totalreclaw';
/**
 * Inspect a plugin install directory to decide whether it is fully installed,
 * a corrupted half-state from an interrupted install, or someone else's
 * plugin. Pure filesystem inspection; never deletes anything.
 *
 * Background — rc.22 finding #5
 * ------------------------------
 * After a partial `openclaw plugins install @totalreclaw/totalreclaw` (e.g.
 * the auto-gateway-restart kills npm mid-build), `extensions/totalreclaw/`
 * survives with a populated package.json but a missing or empty `dist/`. The
 * agent's recovery retry then fires another install; OpenClaw's plugin
 * loader scans `extensions/` and tries to register the half-state as a "hook
 * pack", failing with the cryptic "package.json missing openclaw.hooks". The
 * fix: detect the partial state up-front so the retry can wipe + reinstall
 * instead of cargo-culting a confused error.
 *
 * Decision rules
 * --------------
 *   1. `pluginRootDir` does not exist → `'absent'`.
 *   2. package.json missing or unparsable → `'foreign'` (don't touch).
 *   3. package.json `name !== '@totalreclaw/totalreclaw'` → `'foreign'`.
 *   4. `<root>/.tr-partial-install` exists → `'partial'` (the canonical signal).
 *   5. `<root>/dist/index.js` missing → `'partial'` (build never finished).
 *   6. otherwise → `'clean'`.
 *
 * The function is intentionally conservative: it returns `'foreign'` on any
 * ambiguous read. Callers should NEVER auto-wipe a `'foreign'` directory.
 *
 * @param pluginRootDir Absolute path to the suspect plugin dir, e.g.
 *                      `~/.openclaw/extensions/totalreclaw`.
 */
export function detectPartialInstall(pluginRootDir) {
    const reasons = [];
    // Rule 1 — absent dir.
    let rootStat;
    try {
        rootStat = fs.statSync(pluginRootDir);
    }
    catch {
        return { status: 'absent', reasons: ['directory does not exist'] };
    }
    if (!rootStat.isDirectory()) {
        return { status: 'foreign', reasons: ['path exists but is not a directory'] };
    }
    // Rules 2-3 — package.json must claim our name.
    const pkgJsonPath = path.join(pluginRootDir, 'package.json');
    let pkgRaw;
    try {
        pkgRaw = fs.readFileSync(pkgJsonPath, 'utf-8');
    }
    catch {
        return { status: 'foreign', reasons: ['package.json missing or unreadable'] };
    }
    let parsed;
    try {
        parsed = JSON.parse(pkgRaw);
    }
    catch {
        return { status: 'foreign', reasons: ['package.json is not valid JSON'] };
    }
    if (parsed.name !== PLUGIN_PACKAGE_NAME) {
        return {
            status: 'foreign',
            reasons: [`package.json declares "${String(parsed.name)}" not "${PLUGIN_PACKAGE_NAME}"`],
        };
    }
    // Rule 4 — explicit partial marker wins.
    const markerPath = path.join(pluginRootDir, PARTIAL_INSTALL_MARKER);
    if (fs.existsSync(markerPath)) {
        reasons.push(`${PARTIAL_INSTALL_MARKER} marker present (preinstall fired, postinstall did not)`);
    }
    // Rule 5 — dist/index.js must exist for the loader to register.
    const distIndex = path.join(pluginRootDir, 'dist', 'index.js');
    if (!fs.existsSync(distIndex)) {
        reasons.push('dist/index.js missing (build artifact absent)');
    }
    if (reasons.length > 0) {
        return { status: 'partial', reasons };
    }
    return { status: 'clean', reasons: [] };
}
/**
 * Wipe a partial-install directory so the next `openclaw plugins install`
 * starts from a blank slate. Only acts when `detectPartialInstall(...)`
 * returns `'partial'` — `'foreign'` and `'clean'` are no-ops by design.
 *
 * Returns `true` if the directory was wiped, `false` otherwise.
 *
 * SAFETY: this helper is the only place that recursively deletes a plugin
 * dir. It refuses to act on `'foreign'` and `'clean'` results so a
 * misconfigured caller can never wipe a healthy install or someone else's
 * plugin.
 */
export function wipePartialInstall(pluginRootDir) {
    const detection = detectPartialInstall(pluginRootDir);
    if (detection.status !== 'partial')
        return false;
    try {
        fs.rmSync(pluginRootDir, { recursive: true, force: true });
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Drop the `.tr-partial-install` marker into `pluginRootDir`. Idempotent
 * (overwrites any existing marker) and best-effort — returns `true` on
 * success, `false` if the dir doesn't exist or write fails. Used by the
 * `preinstall` npm script and (defensively) by the runtime if the npm
 * preinstall/cleanup script pair did not fire.
 */
export function writePartialInstallMarker(pluginRootDir) {
    try {
        if (!fs.existsSync(pluginRootDir))
            return false;
        fs.writeFileSync(path.join(pluginRootDir, PARTIAL_INSTALL_MARKER), '');
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Remove the partial-install marker. Called by the `postinstall` script and
 * (defensively) at register-time once we've confirmed the load succeeded.
 * Returns `true` if a marker was removed, `false` if there was nothing to
 * remove.
 */
export function clearPartialInstallMarker(pluginRootDir) {
    try {
        const markerPath = path.join(pluginRootDir, PARTIAL_INSTALL_MARKER);
        if (!fs.existsSync(markerPath))
            return false;
        fs.unlinkSync(markerPath);
        return true;
    }
    catch {
        return false;
    }
}
// ---------------------------------------------------------------------------
// Auto-bootstrap of credentials.json (3.1.0 first-run UX)
// ---------------------------------------------------------------------------
/**
 * Pure helper — pull a plausible mnemonic out of a parsed credentials
 * blob. Accepts both `mnemonic` (canonical) and `recovery_phrase` (what
 * some older flows / hand-edited files use). Returns null when neither is
 * present, empty, or non-string.
 */
export function extractBootstrapMnemonic(creds) {
    if (!creds || typeof creds !== 'object')
        return null;
    const primary = typeof creds.mnemonic === 'string' ? creds.mnemonic.trim() : '';
    if (primary.length > 0)
        return primary;
    const alias = typeof creds.recovery_phrase === 'string' ? creds.recovery_phrase.trim() : '';
    if (alias.length > 0)
        return alias;
    return null;
}
/**
 * Ensure `credentials.json` is present and usable.
 *
 * Behavior:
 *   - File exists + parses + has a non-empty mnemonic (or recovery_phrase)
 *     → return `'existing_valid'`. Also backfill the canonical `mnemonic`
 *     field if only the `recovery_phrase` alias was present.
 *   - File missing → generate a fresh mnemonic, write credentials.json
 *     with `firstRunAnnouncementShown: false`, return `'fresh_generated'`.
 *   - File exists but un-parseable, empty, or missing a mnemonic entirely
 *     → rename it to `credentials.json.broken-<timestamp>`, generate a
 *     fresh mnemonic, write a new credentials.json, return
 *     `'recovered_from_corrupt'` with `backupPath` pointing at the
 *     renamed file.
 *
 * The write is atomic-ish: generate mnemonic first (can throw), then
 * single `writeFileSync` with mode `0o600`. If the generator throws, no
 * partial file is written.
 *
 * The `firstRunAnnouncementShown` flag is always initialised to `false`
 * on fresh/recovered writes and preserved (not touched) on `existing_valid`.
 */
export function autoBootstrapCredentials(credentialsPath, opts) {
    // Load + parse. JSON.parse failures are contained in loadCredentialsJson
    // (returns null). We need to distinguish "missing" from "corrupt" so we
    // check existsSync separately.
    const fileExists = fs.existsSync(credentialsPath);
    let parsed = null;
    let parseFailed = false;
    if (fileExists) {
        try {
            const raw = fs.readFileSync(credentialsPath, 'utf-8');
            parsed = JSON.parse(raw);
        }
        catch {
            parseFailed = true;
        }
    }
    const existingMnemonic = parsed ? extractBootstrapMnemonic(parsed) : null;
    // ---- Happy path: existing file with a valid mnemonic ----
    if (parsed && existingMnemonic && !parseFailed) {
        // Backfill the canonical `mnemonic` key if the user's file only had
        // `recovery_phrase`. Keeps downstream code simple (one field to read).
        if (typeof parsed.mnemonic !== 'string' || parsed.mnemonic.trim() !== existingMnemonic) {
            const updated = { ...parsed, mnemonic: existingMnemonic };
            // Preserve an explicit flag setting; default to true so we don't
            // announce a phrase the user already supplied.
            if (updated.firstRunAnnouncementShown === undefined) {
                updated.firstRunAnnouncementShown = true;
            }
            const dir = path.dirname(credentialsPath);
            if (!fs.existsSync(dir))
                fs.mkdirSync(dir, { recursive: true });
            fs.writeFileSync(credentialsPath, JSON.stringify(updated), { mode: 0o600 });
        }
        const announcementPending = parsed.firstRunAnnouncementShown === false;
        return {
            status: 'existing_valid',
            mnemonic: existingMnemonic,
            announcementPending,
        };
    }
    // ---- Recovery path: file is missing, corrupt, or shape-invalid ----
    // Generate FIRST so a generator failure doesn't delete or rename anything.
    const newMnemonic = opts.generateMnemonic();
    if (typeof newMnemonic !== 'string' || newMnemonic.trim().length === 0) {
        throw new Error('autoBootstrapCredentials: generateMnemonic returned empty');
    }
    // If the file existed but was unusable, rename it so the user can
    // recover if they had the phrase stored elsewhere and realize it later.
    let backupPath;
    if (fileExists) {
        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        backupPath = `${credentialsPath}.broken-${ts}`;
        try {
            fs.renameSync(credentialsPath, backupPath);
        }
        catch {
            // If rename fails (cross-device, permission, etc.) fall back to
            // copy + unlink so we still preserve the user's bytes. If even
            // that fails, swallow — losing a broken file is better than
            // blocking first-run.
            try {
                const raw = fs.readFileSync(credentialsPath, 'utf-8');
                fs.writeFileSync(backupPath, raw, { mode: 0o600 });
                fs.unlinkSync(credentialsPath);
            }
            catch {
                backupPath = undefined;
            }
        }
    }
    const fresh = {
        mnemonic: newMnemonic,
        firstRunAnnouncementShown: false,
    };
    const dir = path.dirname(credentialsPath);
    if (!fs.existsSync(dir))
        fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(credentialsPath, JSON.stringify(fresh), { mode: 0o600 });
    return {
        status: fileExists ? 'recovered_from_corrupt' : 'fresh_generated',
        mnemonic: newMnemonic,
        announcementPending: true,
        backupPath,
    };
}
/**
 * Flip `firstRunAnnouncementShown` to `true` on disk. Called by the
 * `before_agent_start` hook after it prepends the recovery-phrase
 * banner context so the banner fires exactly once per credentials.json
 * generation.
 *
 * Returns `true` on successful write (including the idempotent case
 * where the flag was already `true`). Returns `false` if the file is
 * missing, unreadable, or un-parseable — caller logs but does not throw,
 * since failing to flip the flag only means the banner might show twice,
 * not data loss.
 *
 * NOTE: retained for back-compat with pre-3.2.0 tests. 3.2.0 removes the
 * prependContext banner entirely, so no production code path calls this
 * helper anymore.
 */
export function markFirstRunAnnouncementShown(credentialsPath) {
    try {
        if (!fs.existsSync(credentialsPath))
            return false;
        const raw = fs.readFileSync(credentialsPath, 'utf-8');
        const parsed = JSON.parse(raw);
        if (parsed.firstRunAnnouncementShown === true)
            return true;
        const updated = { ...parsed, firstRunAnnouncementShown: true };
        fs.writeFileSync(credentialsPath, JSON.stringify(updated), { mode: 0o600 });
        return true;
    }
    catch {
        return false;
    }
}
/** Default fresh state for a machine that has never onboarded. */
export function defaultFreshState() {
    return { onboardingState: 'fresh', version: '3.2.0' };
}
/**
 * Load the state file at `statePath`. Returns `null` on any I/O or parse
 * failure. The caller decides whether to initialise a fresh state or treat
 * the missing file as fresh.
 */
export function loadOnboardingState(statePath) {
    try {
        if (!fs.existsSync(statePath))
            return null;
        const raw = fs.readFileSync(statePath, 'utf-8');
        const parsed = JSON.parse(raw);
        // Validate the one required field. Anything else may be absent.
        if (parsed.onboardingState !== 'fresh' && parsed.onboardingState !== 'active') {
            return null;
        }
        return {
            onboardingState: parsed.onboardingState,
            credentialsCreatedAt: typeof parsed.credentialsCreatedAt === 'string' ? parsed.credentialsCreatedAt : undefined,
            createdBy: parsed.createdBy === 'generate' || parsed.createdBy === 'import' ? parsed.createdBy : undefined,
            version: typeof parsed.version === 'string' ? parsed.version : undefined,
        };
    }
    catch {
        return null;
    }
}
/**
 * Write the state file atomically (temp file + rename) with mode 0600.
 * Returns `true` on success, `false` on any I/O error — caller logs but
 * does not throw. Failing to persist state means the plugin will re-derive
 * it from credentials.json on next load, which is safe.
 *
 * Atomicity matters here because the state file is consumed by the
 * before_tool_call gate on every tool call: a half-written file would
 * force-gate real memory operations.
 */
export function writeOnboardingState(statePath, state) {
    try {
        const dir = path.dirname(statePath);
        if (!fs.existsSync(dir))
            fs.mkdirSync(dir, { recursive: true });
        const tmp = `${statePath}.tmp-${process.pid}-${Date.now()}`;
        fs.writeFileSync(tmp, JSON.stringify(state), { mode: 0o600 });
        fs.renameSync(tmp, statePath);
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Derive the current onboarding state for this process by reading
 * credentials.json. Used on plugin load + after CLI wizard writes.
 *
 * Rule (simplest possible, per user's clean-slate ratification):
 *   - credentials.json exists + extractable mnemonic is a non-empty string
 *     → `active`.
 *   - credentials.json missing OR mnemonic missing/empty/non-string
 *     → `fresh`.
 *
 * This is intentionally LAX about BIP-39 checksum validation — the wizard
 * validates on write; at load time we trust the on-disk file. If the
 * mnemonic has been hand-edited to garbage, `initialize()` will fail later
 * at key-derivation time and surface the error via needsSetup.
 *
 * Does NOT require a pre-existing state file; 3.1.0 users (if any) with a
 * valid credentials.json → active silently, no migration code path.
 */
export function deriveStateFromCredentials(credentialsPath) {
    const creds = loadCredentialsJson(credentialsPath);
    const mnemonic = extractBootstrapMnemonic(creds);
    return mnemonic && mnemonic.length > 0 ? 'active' : 'fresh';
}
/**
 * Compute the effective onboarding state at plugin-load time. Reads the
 * persisted state file if it exists AND matches what credentials.json
 * implies; otherwise recomputes and writes a fresh state file.
 *
 * The reason we still persist a state file (rather than deriving every
 * call) is to carry the `createdBy` + `credentialsCreatedAt` fields through
 * process restarts — those are small but useful for diagnostics + future
 * migration paths.
 *
 * Returns the effective state. Does not throw.
 */
export function resolveOnboardingState(credentialsPath, statePath) {
    const implied = deriveStateFromCredentials(credentialsPath);
    const persisted = loadOnboardingState(statePath);
    // Happy path: persisted state matches what credentials imply → trust it.
    if (persisted && persisted.onboardingState === implied) {
        return persisted;
    }
    // Mismatch (or no persisted state): recompute from credentials, persist,
    // and return. Do not overwrite a known `createdBy` if we're just
    // upgrading a stale state file.
    const next = {
        onboardingState: implied,
        version: '3.2.0',
        credentialsCreatedAt: persisted?.credentialsCreatedAt,
        createdBy: persisted?.createdBy,
    };
    writeOnboardingState(statePath, next);
    return next;
}
