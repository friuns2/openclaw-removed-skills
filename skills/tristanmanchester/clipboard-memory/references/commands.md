# Clipboard Memory — Commands Reference

Full flag and subcommand reference for `clipmem`. This file is kept byte-identical across the OpenClaw-native and portable skill packages.

---

## Decision ladder

Pick the narrowest command that answers the question. Always pass `--format json` (or `--format toon` for plain enumeration) when parsing programmatically.

1. `clipmem recall "<query>" --format json` — best-first ranked answer with alternatives. **Start here.**
2. `clipmem timeline --hours <N> --format json` — chronological capture events. Use when the user says "today", "yesterday", "in order", or "every time".
3. `clipmem recent --hours <N> --format json` — deduplicated recent snapshots. Use for "recent unique things".
4. `clipmem search "<query>" --format json` — direct lexical / FTS match. Use when you need precise substring hits.
5. `clipmem get <snapshot_id> --format json` — nested item/representation detail for a snapshot you already have.
6. `clipmem restore <snapshot_id>` — restore the full stored representation set for a snapshot back onto the macOS clipboard.
7. `clipmem export <snapshot_id> --item <n> --uti <uti> --out <path> [--force]` — raw bytes for binary/image/PDF payloads.
8. `clipmem forget <snapshot_id>` — hard-delete one snapshot and its capture history.
9. `clipmem purge --older-than <duration> [--dry-run]` — prune by `last_observed_at`.
10. `clipmem storage compact [--dry-run] --format json` — reclaim SQLite/WAL disk space without changing content.
11. `clipmem storage optimize-images [--dry-run] [--no-compact] [--limit N] [--format json|--progress jsonl]` — convert eligible stored images to lossless WebP and compact by default.
12. `clipmem settings show --format json` — inspect persistent capture policy.
13. `clipmem ocr status --format json` — inspect local OCR queue and result counts.
14. `clipmem ocr run [--limit N] [--snapshot ID]` — backfill OCR for image snapshots.

---

## Subcommand matrix

| Subcommand | Default `--format` | Supports `toon`? | Purpose |
|---|---|---|---|
| `recall [QUERY]` | `md` | yes | Ranked best-first answer with alternatives |
| `search <QUERY>` | `text` | yes | Lexical / FTS match over the archive |
| `recent` | `text` | yes | Recent unique snapshots (deduplicated) |
| `timeline` | `text` | yes | Chronological capture events (not deduped) |
| `get <SNAPSHOT_ID>` | `text` | **no** | Nested detail for one snapshot |
| `restore <SNAPSHOT_ID>` | text | — | Restore a stored snapshot back onto the clipboard |
| `export <SNAPSHOT_ID>` | — (raw bytes) | — | Write one representation to disk |
| `forget <SNAPSHOT_ID>` | text | — | Hard-delete one snapshot and its capture history |
| `purge` | text | — | Delete old snapshots by `last_observed_at` |
| `storage compact` | text (`json` supported) | — | Reclaim SQLite/WAL disk space |
| `storage optimize-images` | text (`json` supported, progress JSONL available) | — | Convert eligible images to lossless WebP |
| `settings show` | `text` | **no** | Show persistent pause / retention / ignore-list policy |
| `settings pause` | text | — | Persistently pause or resume capture |
| `settings api-key-filter` | text | — | Enable or disable API key filtering |
| `settings ocr` | text | — | Enable or disable local OCR for new image captures |
| `settings retention` | text | — | Set retention to a duration or `forever` |
| `settings ignore add/remove/list` | text (`list` also supports `json`) | **no** | Manage ignored bundle identifiers |
| `ocr status` | text (`json` supported) | — | Local OCR queue and result counts |
| `ocr run` | text (`json` supported) | — | Backfill OCR for stored image snapshots |
| `capture-once` | — | — | Single clipboard capture (setup / ad-hoc) |
| `watch` | — | — | Background daemon; usually a LaunchAgent |
| `setup` | — | — | Seed one capture and start background capture |
| `service status` | text (or `--json`) | — | Background provider state + capture freshness |
| `service start` / `stop` / `uninstall` | — | — | Manage the background watcher service |
| `doctor` | text (or `--json`) | — | SQLite / FTS5 diagnostics |
| `agents openclaw doctor` | text | — | Integration health: PATH, workspace, sandbox |
| `agents openclaw install-skill` | — | — | Write packaged skill files to disk |
| `agents openclaw print-skill` | — | — | Print embedded `SKILL.md` to stdout |
| `agents openclaw uninstall-skill` | — | — | Remove installed skill directory |
| `agents hermes doctor` | text | — | Hermes integration health: PATH, skill discovery |
| `agents hermes install-skill` | — | — | Write packaged Hermes skill to disk |
| `agents hermes print-skill` | — | — | Print embedded Hermes `SKILL.md` to stdout |
| `agents hermes uninstall-skill` | — | — | Remove installed Hermes skill directory |

`--json` is a compatibility alias for `--format json` on `search`, `recent`, `timeline`, `get`, `storage compact`, `storage optimize-images`, `ocr status`, `ocr run`, `capture-once`, and `doctor`.

---

## Output formats

All retrieval commands share the same `--format` set except `get`, which omits `toon`:

- `text` — human-oriented terminal output. Default for `search`, `recent`, `timeline`, `get`. **Do not parse.**
- `md` — compact markdown. Default for `recall`. Human-oriented. **Do not parse.**
- `json` — single structured object with a stable envelope. Parse this.
- `jsonl` — newline-delimited rows. Prefer when streaming many results through a pipe.
- `toon` — flat token-efficient list. Prefer for `timeline`, `search`, `recent`, and `recall` when you only need the top fields. Unsupported on `get`.

---

## Shared retrieval filters

`search`, `recent`, `timeline`, and `recall` accept the same filter set. `get` and `export` accept them as guards against the explicitly targeted snapshot.

**Time window:**

- `--since <RFC3339>` — captures at or after this timestamp (e.g. `2026-04-16T09:00:00Z`).
- `--until <RFC3339>` — captures at or before this timestamp.
- `--hours <N>` — last N hours. `--since` wins if both are provided.

**Source:**

- `--app <name>` — case-insensitive substring match on the recorded frontmost app name.
- `--bundle-id <id>` — case-insensitive exact match on bundle identifier (e.g. `com.apple.Safari`).

**Content shape:**

- `--kind text|html|rtf|url|file|image|pdf|binary|other`. One value per invocation.
- `--has-text`, `--has-url`, `--has-file-url`, `--has-image`, `--has-pdf` — additive presence flags (AND semantics).

**Size:**

- `--min-bytes <N>` / `--max-bytes <N>` — applied to the total snapshot byte count.

### `--kind` values

| Value | Matches |
|---|---|
| `text` | plain text representations |
| `html` | HTML clipboard payloads |
| `rtf` | rich-text format |
| `url` | web URLs |
| `file` | **file URLs (Finder paths)** — not regular files on disk |
| `image` | image blobs (PNG, JPEG, TIFF, etc.) |
| `pdf` | PDF documents |
| `binary` | opaque binary that has no safe text projection |
| `other` | mixed or empty snapshots |

`--kind file` is a common pitfall: it matches clipboard-as-file-URL payloads (things dragged from Finder), not arbitrary files the user happened to reference.

---

## Pagination

List commands (`search`, `recent`, `timeline`) accept `--limit` and `--cursor`:

- `--limit <N>` — 1–250, default 10.
- `--cursor <opaque>` — resume from a `next_cursor` returned by a prior response.

Cursors are tied to the active query, mode, and filters. Changing any of those while paginating will reject the cursor. When a response includes `"truncated": true` and a non-null `next_cursor`, there are more rows.

```bash
clipmem search "git status" --format json --limit 25
clipmem search "git status" --format json --limit 25 --cursor "<next_cursor>"
```

---

## Search modes (`search`, `recall`)

`--mode auto|fts|literal`, default `auto`.

- `auto` — picks FTS or literal per query. Prefers literal for URLs, paths, bundle ids, dotted identifiers, and shell fragments (`--flag=value`, pipes, subshells). Plain prose queries try FTS first.
- `fts` — strict SQLite FTS5. Use when you want to compose boolean queries: `"launchctl" AND bootstrap`.
- `literal` — exact substring match. Use for punctuation-heavy strings like `50%`, `Co-Authored-By:`, or URL fragments.

Rules of thumb:

- Query contains `"`, `AND`, `OR`, `NOT` → `--mode fts`.
- Query contains `/`, `.`, `:`, `%`, or shell metacharacters → `--mode literal`.
- Short natural-language query → let `--mode auto` pick.

---

## `recall` extras

On top of the shared filters:

- `--format md|json|toon` (default `md`).
- `--limit <N>` — ranked candidates to consider (default 5).
- `--full` — expand the best candidate text instead of the compact form.
- `--quote` — force quoted best-text output.
- `--min-score <0.0-1.0>` — threshold below which a query alone is not trusted; falls back to recency / filters.
- `--prefer-recent` — bias ranking toward recency.
- `--prefer-app <name>` — bias toward matching app or bundle id.
- `--hours <N>` — window for the recent-fallback when a query is weak.

If the user has no query but said "the thing I just copied":

```bash
clipmem recall --prefer-recent --hours 24 --format json --limit 5
```

---

## `get`, `restore`, and `export`

```bash
clipmem get <snapshot_id> --format json        # nested representation detail
clipmem get <snapshot_id> --events <N>         # include last N capture events (default 10)
clipmem restore <snapshot_id>                  # restore the whole snapshot to the clipboard
clipmem export <snapshot_id> --item <index> --uti <uti> --out <path> [--force]
```

`get --format json` flattens the common text fields on the root snapshot so agents don't have to walk the representation tree. `get` does **not** support `--format toon`.

`restore` is macOS-only and writes the full stored item/UTI/raw-byte set back onto the general pasteboard. This is a whole-snapshot restore, not a text-only approximation.

`export` writes raw bytes to `--out`. There is no `--format` flag. By default it creates a new file and refuses to replace an existing destination; pass `--force` only to replace an existing regular file. Symlink destinations are rejected. Required arguments: `--item` (0-based), `--uti` (e.g. `public.png`, `public.utf8-plain-text`, `com.adobe.pdf`), `--out`. Inspect `items[].representations[].uti` and `size_bytes` in a prior `get --format json` to choose the right combination.

---

## `forget`, `purge`, `storage`, and `settings`

```bash
clipmem forget <snapshot_id>
clipmem purge --older-than 30d [--dry-run]
clipmem storage compact [--dry-run] [--format json]
clipmem storage optimize-images [--dry-run] [--no-compact] [--limit N] [--format json|--progress jsonl]
clipmem settings show [--format json]
clipmem settings pause on|off
clipmem settings api-key-filter on|off
clipmem settings ocr on|off
clipmem settings retention <duration|forever>
clipmem settings ignore add <bundle_id>
clipmem settings ignore remove <bundle_id>
clipmem settings ignore list [--format json]
clipmem ocr status [--format json]
clipmem ocr run [--limit N] [--snapshot ID] [--retry-failed] [--format json]
```

`forget` is a hard delete. It removes the snapshot row, all child items/representations, and all capture events for that snapshot id via foreign-key cascades.

`purge` computes age from `snapshot_stats.last_observed_at`, not `snapshots.created_at`. Duration grammar is a single integer plus one unit: `Nd`, `Nh`, or `Nm`.

`storage compact` checkpoints WAL state and vacuums SQLite pages back to the filesystem. It never changes clipboard content. `storage optimize-images` rewrites eligible image representations to lossless WebP only when doing so saves meaningful space, then compacts SQLite storage by default; already compressed or skipped rows are not retried by normal runs. Use `--progress jsonl` for streamed `started`, `scanning`, `compacting`, and `complete` progress events. Use `--no-compact` only when batching optimization runs and compacting once at the end.

`settings` is the persistent capture-policy entrypoint. Ignore matching is exact, case-insensitive bundle-id matching only. OCR is opt-in, runs locally through Apple Vision on macOS, and stores text/status separately from raw image bytes.

---

## Global flags

- `--db <path>` — override the SQLite database path. Default: `~/Library/Application Support/clipmem/clipmem.sqlite3` on macOS. Use this only when pointing at an alternate archive (tests, backups).

## Environment

- `CLIPMEM_OPENCLAW_WORKSPACE` — overrides the OpenClaw workspace root used by `agents openclaw install-skill` and `agents openclaw doctor`. Falls back to `openclaw config get agents.defaults.workspace`, then `~/.openclaw/workspace`.
- `HOME` — resolves `~/` in default paths.

---

## Exit codes

- `0` — success
- `1` — uncategorized runtime failure
- `2` — invalid args
- `3` — not found (e.g. snapshot id, representation)
- `4` — unsupported format for this subcommand (e.g. `--format toon` on `get`)
- `5` — database error
- `6` — platform error (macOS API / filesystem)

Scripts can rely on these to distinguish "no such snapshot" (retriable with a different id) from "database locked" (retry with backoff) from "wrong format" (agent bug).

---

## Script-friendly guarantees

- stdout contains only the requested command output.
- stderr contains diagnostics only.
- No interactive prompts anywhere in the CLI.
- List commands use bounded `--limit` defaults and opaque cursor pagination.
- `--format json` output is stable within `schema_version: 2`.
