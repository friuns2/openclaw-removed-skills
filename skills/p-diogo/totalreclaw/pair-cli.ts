/**
 * pair-cli — the `openclaw totalreclaw pair` CLI subcommand.
 *
 * Purpose
 * -------
 * Starts a remote-onboarding session FROM the gateway host's terminal.
 * Creates a pair-session, renders the QR + URL + 6-digit secondary code
 * to stdout, then polls /status until the browser completes the flow.
 *
 * This is the gateway-operator's surface. The operator reads the QR
 * with their phone (or opens the URL on their laptop browser); the
 * browser takes over from there.
 *
 * Scope and scanner surface
 * -------------------------
 * Has `fetch` (for status polling) AND `POST` (never actually POSTs,
 * but the word lives in comments describing the paired browser POST).
 * MUST NOT also read disk or env vars. All state operations delegate
 * to pair-session-store; the CLI itself is a thin coordinator.
 *
 * Zero logging of secret material. The secondary code IS printed to
 * stdout (required for the user to type), but never logged to file
 * and never to api.logger.
 */

import readline from 'node:readline';

import {
  createPairSession,
  getPairSession,
  rejectPairSession,
  type PairSession,
  type PairSessionMode,
} from './pair-session-store.js';
import { generateGatewayKeypair } from './pair-crypto.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PairCliIo {
  stdout: NodeJS.WritableStream;
  stderr: NodeJS.WritableStream;
  /** Install a Ctrl+C handler that invokes `cb`; returns an uninstaller. */
  onInterrupt(cb: () => void): () => void;
}

export interface PairCliDeps {
  sessionsPath: string;
  /** Caller-injected function that returns the full `url#pk=` string
   *  for the browser. Takes the session and returns the URL with the
   *  public-key fragment embedded. Signature keeps URL resolution out
   *  of this module (same rationale as pair-http). */
  renderPairingUrl(session: PairSession): string;
  /** QR renderer — takes a text payload + callback. Injectable for tests. */
  renderQr(payload: string, cb: (ascii: string) => void): void;
  /** Poll interval in ms. Default 1500. */
  pollIntervalMs?: number;
  /** Override for Date.now(). */
  now?: () => number;
  io: PairCliIo;
  /** Optional TTL override (sec → ms conversion happens here). */
  ttlSeconds?: number;
  /**
   * 3.3.1 — Output format. Defaults to 'human' for backwards-compat with
   * the rc.6 flow. `--json` on the CLI wraps this to 'json'.
   */
  outputMode?: PairCliOutputMode;
}

export type PairCliMode = PairSessionMode;

export interface PairCliOutcome {
  status: 'completed' | 'canceled' | 'expired' | 'rejected' | 'error';
  sid?: string;
  error?: string;
}

/**
 * Output mode for runPairCli.
 *   - 'human' (default): prints the multi-line intro + security warning +
 *     "Waiting..." spinner line and polls until terminal state.
 *   - 'json': emits a single JSON object to stdout with the URL, PIN,
 *     SID, expiration, and ASCII QR, then polls silently. Exits as soon
 *     as the session reaches a terminal state — same status-code
 *     semantics as 'human' (0 on completed, 1 on expired/rejected/error,
 *     130 on canceled).
 *   - 'url-pin': (3.3.1-rc.15, issue #87) headless container-agent fallback.
 *     Emits ONLY `{ v, url, pin, expires_at_ms }` — no QR ASCII, no SID,
 *     no mode echo. Use when a container-based agent cannot see the
 *     `totalreclaw_pair` tool (OpenClaw gateway-to-container tool-injection
 *     gap) and must shell out to the CLI. Guarantees zero phrase material
 *     on stdout by construction — pair-crypto is x25519-only and the slim
 *     payload carries nothing BIP-39-adjacent.
 *   - 'pair-only': (3.3.1-rc.18, issue #95) the same surface as 'url-pin',
 *     but the URL field is named `pair_url` (matching the spec wording
 *     for `openclaw totalreclaw onboard --pair-only`). Used by the
 *     onboard CLI's `--pair-only` flag to provide a phrase-safe
 *     alternative to the interactive phrase-print path. Emits ONLY
 *     `{ v, pair_url, pin, expires_at_ms }`. Same zero-phrase invariant
 *     as 'url-pin' — the underlying pair flow does no BIP-39 work.
 */
export type PairCliOutputMode = 'human' | 'json' | 'url-pin' | 'pair-only';

/**
 * JSON payload emitted by runPairCli when outputMode === 'json'. Printed
 * ONCE to stdout before polling begins — agents can capture it, release
 * the child-process stdout, and display it themselves.
 */
export interface PairCliJsonPayload {
  v: 1;
  sid: string;
  url: string;
  pin: string;
  mode: PairCliMode;
  expires_at_ms: number;
  qr_ascii: string;
}

/**
 * Slim payload for outputMode === 'url-pin'. Intentionally a subset of
 * `PairCliJsonPayload` with no QR ASCII, SID, or mode echo. Issue #87.
 */
export interface PairCliUrlPinPayload {
  v: 1;
  url: string;
  pin: string;
  expires_at_ms: number;
}

/**
 * Slim payload for outputMode === 'pair-only'. Same shape as
 * `PairCliUrlPinPayload` but with `pair_url` instead of `url` — the
 * key name matches the spec for `onboard --pair-only` (issue #95).
 * Phrase invariant: zero BIP-39 material on stdout by construction
 * (the pair flow is x25519-only).
 */
export interface PairCliPairOnlyPayload {
  v: 1;
  pair_url: string;
  pin: string;
  expires_at_ms: number;
}

// ---------------------------------------------------------------------------
// Default stdout IO
// ---------------------------------------------------------------------------

export function buildDefaultPairCliIo(): PairCliIo {
  return {
    stdout: process.stdout,
    stderr: process.stderr,
    onInterrupt(cb) {
      const handler = () => {
        try { cb(); } catch { /* swallow */ }
      };
      process.once('SIGINT', handler);
      return () => process.off('SIGINT', handler);
    },
  };
}

// ---------------------------------------------------------------------------
// Copy — same security principles as onboarding-cli COPY but terser.
// ---------------------------------------------------------------------------

const COPY = {
  intro:
    '\nTotalReclaw — Remote pairing\n\n' +
    'Your TotalReclaw recovery phrase will be created (or imported) in your\n' +
    'BROWSER and delivered to this gateway encrypted end-to-end. The phrase\n' +
    'never touches the LLM, the session transcript, or the relay server\n' +
    'in plaintext.\n\n' +
    'Scan the QR code below with your phone, or open the URL on any\n' +
    'device. Then type the 6-digit code shown here into the browser.\n',
  introGenerate:
    '\nMode: GENERATE — your browser will create a NEW 12-word recovery phrase.\n' +
    'You will be asked to write it down and retype 3 words before the\n' +
    'gateway accepts it.\n',
  introImport:
    '\nMode: IMPORT — your browser will accept an existing TotalReclaw\n' +
    'recovery phrase that you already have. Paste it in the browser; it\n' +
    'will be validated locally and encrypted before upload.\n',
  codeLabel: '\nSecondary code (type this into the browser):\n\n    ',
  urlLabel:
    '\n\nURL (QR encodes this plus a one-time public key):\n\n    ',
  securityWarning:
    '\n\nSecurity:\n' +
    '  * Do NOT share your screen during pairing.\n' +
    '  * Do NOT screenshot this terminal.\n' +
    '  * The browser page will warn you never to reuse this recovery\n' +
    '    phrase for wallets, banking, email, or any other service.\n',
  awaiting: '\nWaiting for browser to connect… (press Ctrl+C to cancel)',
  deviceConnected: '\nBrowser connected. Waiting for encrypted payload…',
  completed: '\nPairing complete. Account is active.',
  canceled: '\nCanceled. Pairing session invalidated.',
  expired: '\nSession expired. Run the command again to restart.',
  rejected: '\nPairing rejected (too many wrong codes, or gateway aborted).',
};

function renderUnsafelyVisibleCode(code: string): string {
  // Pad digits with spaces so terminal copy-paste can't accidentally
  // pick them up as a single token.
  return code.split('').join(' ');
}

// ---------------------------------------------------------------------------
// Public entry point
// ---------------------------------------------------------------------------

/**
 * Start a pairing session, display the QR + code + URL, and poll
 * until terminal state. Returns the final outcome.
 *
 * Blocks until the session finishes, expires, or the operator hits
 * Ctrl+C.
 *
 * 3.3.1 — Non-TTY support:
 *   - Does NOT call `readline` / `stdin.setRawMode` / any interactive
 *     prompt. All output is unidirectional to stdout/stderr, so the
 *     command works under `docker exec <container> ...` without `-t`.
 *   - Adds an optional JSON mode (deps.outputMode === 'json') that emits
 *     a single JSON object to stdout before polling begins. Agents
 *     capture it, present the QR / URL / PIN to the user themselves,
 *     and still get the terminal-state exit code.
 */
export async function runPairCli(
  mode: PairCliMode,
  deps: PairCliDeps,
): Promise<PairCliOutcome> {
  const now = deps.now ?? Date.now;
  const pollInterval = Math.max(500, deps.pollIntervalMs ?? 1500);
  const io = deps.io;
  const stdout = io.stdout;
  const outputMode: PairCliOutputMode = deps.outputMode ?? 'human';

  // 1. Generate keypair + create the session
  const kp = generateGatewayKeypair();
  let session: PairSession;
  try {
    session = await createPairSession(deps.sessionsPath, {
      mode,
      operatorContext: { channel: 'cli' },
      ttlMs: deps.ttlSeconds !== undefined ? deps.ttlSeconds * 1000 : undefined,
      rngPrivateKey: () => Buffer.from(kp.skB64, 'base64url'),
      rngPublicKey: () => Buffer.from(kp.pkB64, 'base64url'),
      now,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    io.stderr.write(`\nFailed to create pairing session: ${msg}\n`);
    return { status: 'error', error: msg };
  }

  // 2. Build the URL unconditionally, but only render the QR for modes
  //    that actually emit it. url-pin and pair-only modes skip the
  //    renderer entirely — no CPU cost, no qrcode-terminal import, no
  //    ASCII on stdout.
  const url = deps.renderPairingUrl(session);
  const skipsQr = outputMode === 'url-pin' || outputMode === 'pair-only';
  const qrAscii = skipsQr ? '' : await new Promise<string>((resolve) => {
    // Guard against QR renderers that never fire their callback (shouldn't
    // happen with qrcode-terminal, but defensive): a 10-second timeout
    // returns an empty string so we never hang the pairing flow.
    let settled = false;
    const t = setTimeout(() => {
      if (!settled) {
        settled = true;
        resolve('');
      }
    }, 10_000);
    try {
      deps.renderQr(url, (ascii) => {
        if (settled) return;
        settled = true;
        clearTimeout(t);
        resolve(ascii);
      });
    } catch (err) {
      if (settled) return;
      settled = true;
      clearTimeout(t);
      resolve(`(QR renderer crashed: ${err instanceof Error ? err.message : String(err)})`);
    }
  });

  // 3. Emit the visible surface (JSON/url-pin/pair-only first — single
  //    line — or human copy).
  if (outputMode === 'url-pin') {
    const payload: PairCliUrlPinPayload = {
      v: 1,
      url,
      pin: session.secondaryCode,
      expires_at_ms: session.expiresAtMs,
    };
    stdout.write(JSON.stringify(payload) + '\n');
  } else if (outputMode === 'pair-only') {
    const payload: PairCliPairOnlyPayload = {
      v: 1,
      pair_url: url,
      pin: session.secondaryCode,
      expires_at_ms: session.expiresAtMs,
    };
    stdout.write(JSON.stringify(payload) + '\n');
  } else if (outputMode === 'json') {
    const payload: PairCliJsonPayload = {
      v: 1,
      sid: session.sid,
      url,
      pin: session.secondaryCode,
      mode,
      expires_at_ms: session.expiresAtMs,
      qr_ascii: qrAscii,
    };
    stdout.write(JSON.stringify(payload) + '\n');
  } else {
    stdout.write(COPY.intro);
    stdout.write(mode === 'generate' ? COPY.introGenerate : COPY.introImport);
    if (qrAscii) {
      stdout.write('\n' + qrAscii + '\n');
    } else {
      stdout.write('\n(QR not rendered — use the URL below)\n');
    }
    stdout.write(COPY.codeLabel);
    stdout.write(renderUnsafelyVisibleCode(session.secondaryCode));
    stdout.write(COPY.urlLabel);
    stdout.write(url);
    stdout.write(COPY.securityWarning);
    stdout.write(COPY.awaiting);
    stdout.write('\n');
  }

  // 4. Set up Ctrl+C to cancel the session server-side
  let canceled = false;
  const releaseInterrupt = io.onInterrupt(() => {
    canceled = true;
  });

  // 5. Poll — status transitions only surface in human mode; json /
  //    url-pin / pair-only modes stay silent after the single payload
  //    line so agents parsing stdout get one JSON line and an exit
  //    code, nothing else.
  const emitStatus = (text: string): void => {
    if (outputMode === 'human') stdout.write(text);
  };
  let lastStatus = session.status;
  let showedDeviceConnected = false;
  try {
    while (true) {
      if (canceled) {
        await rejectPairSession(deps.sessionsPath, session.sid, now);
        emitStatus(COPY.canceled + '\n');
        return { status: 'canceled', sid: session.sid };
      }
      await sleep(pollInterval);
      const fresh = await getPairSession(deps.sessionsPath, session.sid, now);
      if (!fresh) {
        // Pruned — session is gone entirely.
        emitStatus(COPY.expired + '\n');
        return { status: 'expired', sid: session.sid };
      }
      if (fresh.status !== lastStatus) {
        lastStatus = fresh.status;
        if (fresh.status === 'device_connected' && !showedDeviceConnected) {
          emitStatus(COPY.deviceConnected + '\n');
          showedDeviceConnected = true;
        }
      }
      if (fresh.status === 'completed') {
        emitStatus(COPY.completed + '\n');
        return { status: 'completed', sid: session.sid };
      }
      if (fresh.status === 'expired') {
        emitStatus(COPY.expired + '\n');
        return { status: 'expired', sid: session.sid };
      }
      if (fresh.status === 'rejected') {
        emitStatus(COPY.rejected + '\n');
        return { status: 'rejected', sid: session.sid };
      }
    }
  } finally {
    releaseInterrupt();
  }
}

// ---------------------------------------------------------------------------
// Wrap qrcode-terminal in a promise-friendly renderer. Dynamic import
// keeps the module out of the plugin's register() hot path.
// ---------------------------------------------------------------------------

/**
 * Default QR renderer using `qrcode-terminal`. Lazy-imports so the
 * module only loads when the CLI is actually invoked.
 */
export function defaultRenderQr(payload: string, cb: (ascii: string) => void): void {
  // `qrcode-terminal` ships no type declarations; we describe the
  // public surface we rely on inline via a cast.
  type QrMod = {
    generate(text: string, opts: { small?: boolean }, cb: (ascii: string) => void): void;
  };
  import('qrcode-terminal' as string).then((rawMod: unknown) => {
    const mod = rawMod as { default?: QrMod } & QrMod;
    const qr: QrMod = mod.default ?? mod;
    qr.generate(payload, { small: true }, cb);
  }).catch((err: unknown) => {
    cb(`(QR renderer unavailable: ${err instanceof Error ? err.message : String(err)})`);
  });
}

// ---------------------------------------------------------------------------
// CLI registrar — hooked from `index.ts registerCli`.
// ---------------------------------------------------------------------------

/**
 * Register the `openclaw totalreclaw pair [generate|import]` subcommand
 * on the caller's commander program. The onboarding-cli's
 * `registerOnboardingCli` function already attaches `totalreclaw` as a
 * top-level command with `onboard`+`status` subcommands; we hook in by
 * finding that command and adding `pair` alongside.
 *
 * If the commander program is provided without the prior attachments,
 * we create `totalreclaw pair` fresh. The caller in index.ts decides
 * composition.
 */
/**
 * Minimal structural shape of commander's `Command` used by this file.
 * We don't import from `commander` because it's not a declared
 * dependency of the plugin (it's injected by OpenClaw's CLI runtime
 * at call time).
 */
type CommanderCommand = {
  name(): string;
  command(name: string): CommanderCommand;
  description(text: string): CommanderCommand;
  option(flags: string, description: string, defaultValue?: unknown): CommanderCommand;
  action(fn: (...args: unknown[]) => Promise<void> | void): CommanderCommand;
  commands: CommanderCommand[];
};

export function registerPairCli(
  program: CommanderCommand,
  deps: {
    sessionsPath: string;
    renderPairingUrl(session: PairSession): string;
    logger: { info(msg: string): void; warn(msg: string): void; error(msg: string): void };
  },
): void {
  // If the onboarding-cli already attached `totalreclaw`, reuse it.
  // Otherwise create a fresh top-level command.
  let tr: CommanderCommand | undefined = program.commands.find(
    (c: CommanderCommand) => c.name() === 'totalreclaw',
  );
  if (!tr) {
    tr = program
      .command('totalreclaw')
      .description('TotalReclaw encrypted memory — pairing + onboarding + status');
  }

  tr.command('pair [mode]')
    .description(
      'Pair a remote browser device to this gateway (mode = generate | import; default generate)',
    )
    .option('--json', 'Emit a single JSON payload (url/pin/sid/qr_ascii) instead of the human-readable banner. Enables agent-driven pairing.')
    .option('--url-pin-only', 'Emit ONLY {v,url,pin,expires_at_ms} — no QR ASCII, no SID, no mode echo. Headless fallback for container-based agents where the totalreclaw_pair tool is not injected (issue #87). Zero phrase exposure on stdout.')
    .option('--timeout <sec>', 'Session TTL in seconds (default: 900 = 15 min, matches pair-session-store default)')
    .action(async (...args: unknown[]) => {
      // commander passes: [modeArg, options, cmd]
      const modeRaw = typeof args[0] === 'string' ? args[0] : undefined;
      const opts = (args[1] ?? {}) as { json?: boolean; urlPinOnly?: boolean; timeout?: string | number };
      const mode: PairCliMode =
        modeRaw === 'import' || modeRaw === 'imp' ? 'import' : 'generate';
      // --url-pin-only wins over --json when both are passed, since it is
      // strictly the tighter surface (no QR, no SID). The flag is a subset.
      const outputMode: PairCliOutputMode = opts.urlPinOnly
        ? 'url-pin'
        : opts.json ? 'json' : 'human';
      let ttlSeconds: number | undefined;
      if (typeof opts.timeout === 'number' && Number.isFinite(opts.timeout)) {
        ttlSeconds = opts.timeout;
      } else if (typeof opts.timeout === 'string' && opts.timeout.trim() !== '') {
        const parsed = Number(opts.timeout);
        if (Number.isFinite(parsed) && parsed > 0) ttlSeconds = parsed;
      }
      const io = buildDefaultPairCliIo();
      try {
        const outcome = await runPairCli(mode, {
          sessionsPath: deps.sessionsPath,
          renderPairingUrl: deps.renderPairingUrl,
          renderQr: defaultRenderQr,
          io,
          outputMode,
          ttlSeconds,
        });
        if (outcome.status !== 'completed') {
          process.exit(outcome.status === 'canceled' ? 130 : 1);
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        deps.logger.error(`pair-cli crashed: ${msg}`);
        process.exit(2);
      }
    });
}

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Keep readline import reachable (pair-cli doesn't use it directly yet,
// but future interactive prompts will land here; prevents tree-shaking
// from dropping a future dep). TypeScript requires the import to have
// an effect.
void readline;
