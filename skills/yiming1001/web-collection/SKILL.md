---
name: web-collection
description: Browser plugin data collection via a local bridge or cloud dispatch to a connected local connector, in strict synchronous closed-loop mode. Cloud mode includes async command-result querying. Use for Douyin, TikTok, Xiaohongshu, Amazon, and Bilibili collection tasks.
---

# Web Collection

Use this skill for browser-extension collection tasks on:

- Douyin
- TikTok
- Xiaohongshu
- Amazon
- Bilibili

## Human Tutorial

This skill is implementation-oriented. For end-user onboarding and step-by-step human instructions, use:

- https://vcn5grhrq8y0.feishu.cn/wiki/BGUhwC0cKimwTJkXDSuc0YFBnib

When the user asks "how to use it" or needs UI-level operation guidance, prefer this tutorial and keep the response aligned with its wording.

For complex or ambiguous requests, read [references/learning-guide.md](references/learning-guide.md) before deciding what to ask or run.

## Core Rules

1. Use the user's normal Chrome environment, not the isolated `openclaw` browser profile.
2. Prefer the connector flow over generic browser tooling.
3. Never ask for configuration that is already present in environment variables.
4. Local and cloud use the same recommended defaults and overall collection flow.
5. Cloud adds only two extra required values: `id` and `token`.
6. Default to synchronous closed-loop execution.
7. Do not reply before the collection script finishes.
8. Choose one execution mode first:
   - `local`: talk to the local bridge directly and only run the local send-command script
   - `cloud`: call the cloud connector dispatch API and only run the cloud send-command script
9. In `cloud` mode, do not rewrite the collection payload. Only wrap it in:
   - `device_id`
   - `action`
   - `payload`

## First-Time Setup

This skill uses one preferences file:

`$OPENCLAW_STATE_DIR/skill-state/web-collection/preferences.json`

Fallback:

`$HOME/.openclaw/skill-state/web-collection/preferences.json`

Helper script:

```bash
bash {baseDir}/scripts/export_preference.sh show
bash {baseDir}/scripts/export_preference.sh check
bash {baseDir}/scripts/export_preference.sh apply-recommended
bash {baseDir}/scripts/export_preference.sh set-key defaultConnectionMode cloud
bash {baseDir}/scripts/export_preference.sh set-key defaultCloudDeviceId desktop-local-smoke-fix
bash {baseDir}/scripts/export_preference.sh set-key defaultCloudToken <user_api_key>
bash {baseDir}/scripts/export_preference.sh set-key defaultExportMode csv
```

Required defaults:

- `defaultExportMode`
- `defaultMaxItems`
- `defaultFetchDetail`
- `defaultDetailSpeed`

Mode-specific defaults:

- `local`
  - no extra required key if the default local bridge URL works
- `cloud`
  - cloud base URL is fixed to `https://i-sync.cn` by default
  - `defaultCloudDeviceId` only when it is not already provided by environment variables
  - `defaultCloudToken` only when it is not already provided by environment variables

`run.sh` enforces this. If these are incomplete, collection must not start.

### First-run flow

On first use:

1. Determine the execution mode first.
2. If the mode is `cloud`, collect these values only when they are not already available from environment variables or stored preferences:
   - `defaultCloudDeviceId`
   - `defaultCloudToken`
3. Then handle the common defaults:
   - 导出方式
   - 默认采集条数
   - 是否默认采集详情
   - 默认采集速度
4. Ask only one question for the common defaults:
   - `推荐配置`
   - `自己配置`
5. If the user chooses `推荐配置`, run:

```bash
bash {baseDir}/scripts/export_preference.sh apply-recommended
```

6. If the user chooses `自己配置`, ask for all four values in one message, not one by one.
7. Only continue when `check` passes.

Preferred cloud prompt:

```text
检测到你要走云端分发，还需要这两个配置：
- device_id
- API token

请一次性发给我。
```

Preferred quick-reply prompt for common defaults:

```text
常用配置还需要确认一次。
这些配置包括：
- 导出方式
- 默认采集条数
- 是否默认采集详情
- 默认采集速度
你可以直接用推荐配置，也可以自己配置。
[[quick_replies: 推荐配置, 自己配置]]
```

Preferred custom-config prompt:

```text
好，我们一次性把默认配置定好。请直接按下面格式回复：

导出方式：CSV / 多维表格
默认采集条数：10 / 20 / 50 / 100
是否默认采集详情：是 / 否
默认采集速度：fast / medium / slow

说明：
- 多维表格：适合查看、筛选、分享
- CSV：适合本地保存
- 采集详情：开启后结果更完整，但一般更慢
- 采集速度：推荐 fast
```

Recommended defaults:

- 运行位置：`local`
- 导出方式：`多维表格`
- 采集条数：`20`
- 采集详情：`true`
- 采集速度：`fast`

## Cloud Mode

Use `cloud` mode when the collection request should be sent to the platform backend first, and then dispatched to the user's connected local connector.

Cloud responsibilities:

- call `/api/v1/connector/cloud/dispatch`
- authenticate with `Authorization: Bearer <user_api_key>`
- include `device_id`
- keep the collection body unchanged inside `payload`
- enforce a strict cloud payload template before dispatch to avoid missing fields
  - default fallback when missing: `maxItems=20`, `mode=search`, `interval=300`, `fetchDetail=true`, `detailSpeed=fast`
- poll `/api/v1/connector/cloud/commands/{command_id}` for final status and result
- if single-command query is unavailable, fallback to `/api/v1/connector/cloud/commands?device_id=...`
- treat `result` + `task_updates` as the source of completion snapshot

Do not:

- call the user's local `19820` port from the cloud path
- rewrite `payload` semantics
- mix local admin token logic into cloud requests

## Connector Command Ladder

When collection fails, parameters look incomplete, or status is unclear, run connector checks in this order instead of guessing.

Layer 1: capability

- `GET /api/help`
- `GET /api/routes`
- `GET /api/filters` (or platform/method scoped)

Layer 2: diagnostics

- `GET /api/status`
- `GET /api/platform-state`
- `GET /api/cloud/status`
- `POST /api/preflight` with the final request body

Layer 3: execution and tracking

- `POST /api/collect`
- `GET /api/tasks/:id` (local mode)
- `GET /api/v1/connector/cloud/commands/{command_id}` (cloud mode, preferred)
- `GET /api/v1/connector/cloud/commands?device_id=...` (cloud fallback)
- `POST /api/stop` or `POST /api/reset` when stuck

Local command template (admin token required):

```bash
TOKEN="$(cat ~/.meixi-connector/bridge-admin-token.txt)"
curl -s -H "x-connector-admin-token: $TOKEN" "http://127.0.0.1:19820/api/status"
```

Cloud command template (async result):

```bash
curl -s -H "Authorization: Bearer <token_or_api_key>" \
  "https://i-sync.cn/api/v1/connector/cloud/commands/<command_id>"
```

## Export Behavior

- `bitable`
  - run with `--export-target bitable`
  - expect `export.tableUrl` on success
- `csv`
  - run with `--export-target csv`
  - do not require a table link in the final reply

## Entry Point

Preferred wrapper:

```bash
bash {baseDir}/scripts/run.sh ...
```

The wrapper:

- runs `scripts/preflight_check.sh` first
- applies stored preferences
- enforces required setup
- runs either local bridge mode or cloud dispatch mode
- local mode dispatches only through `scripts/collect_and_export_loop.sh`
- cloud mode dispatches only through `scripts/cloud_dispatch_loop.sh`
- never mixes the local and cloud send-command scripts

## Bundled Resources

- `scripts/preflight_check.sh`
  - validates required defaults before dispatch
  - treats environment-variable configuration as already satisfied and never asks for it
- `scripts/run.sh`
  - chooses exactly one dispatch path based on `connection-mode`
  - never mixes local and cloud send-command scripts
- `scripts/collect_and_export_loop.sh`
  - local-only send-command script
- `scripts/cloud_dispatch_loop.sh`
  - cloud-only send-command script
- `scripts/export_preference.sh`
  - stores reusable defaults and masks cloud token in human-readable output
- `references/learning-guide.md`
  - compact guidance for complex requests and asking rules

## Common Commands

Douyin keyword search:

```bash
bash {baseDir}/scripts/run.sh \
  --platform douyin \
  --keyword "AI" \
  --ensure-bridge
```

Douyin keyword search via cloud dispatch:

```bash
bash {baseDir}/scripts/run.sh \
  --connection-mode cloud \
  --cloud-device-id desktop-local-smoke-fix \
  --cloud-token '<user_api_key>' \
  --platform douyin \
  --keyword "AI员工"
```

Amazon keyword search:

```bash
bash {baseDir}/scripts/run.sh \
  --platform amazon \
  --keyword "Chinese porcelain" \
  --ensure-bridge
```

Bilibili keyword search:

```bash
bash {baseDir}/scripts/run.sh \
  --platform bilibili \
  --keyword "古董" \
  --ensure-bridge
```

## Platform Defaults

Wrapper defaults:

- `douyin` => `videoKeyword`
- `tiktok` => `keywordSearch`
- `xiaohongshu` => `keywordSearch`
- `amazon` => `keywordSearch`
- `bilibili` => `keywordSearch`

Supported methods:

- `douyin`: `videoKeyword`, `creatorKeyword`, `creatorLink`, `creatorVideo`, `videoComment`, `videoInfo`, `videoLink`
- `tiktok`: `keywordSearch`, `userVideo`, `tiktokComment`, `tiktokCreatorKeyword`, `tiktokCreatorLink`
- `xiaohongshu`: `keywordSearch`, `creatorNote`, `creatorLink`, `creatorKeyword`, `noteLink`, `noteComment`
- `amazon`: `keywordSearch`, `productLink`, `productReview`
- `bilibili`: `keywordSearch`, `videoInfo`, `creatorVideo`, `bilibiliComment`

## Closed Loop

`local` mode:

1. verify `pluginConnected=true`
2. wait for idle state
3. start `/api/collect`
4. handle `TASK_RUNNING` via `stop -> wait idle -> retry`
5. poll `/api/tasks/<taskId>` until `completed` or `error`
6. if export is required, verify the expected export result

`cloud` mode:

1. query `/api/v1/connector/cloud/status?device_id=...`
2. dispatch `action=collect` to `/api/v1/connector/cloud/dispatch`
3. keep querying command result (`/api/v1/connector/cloud/commands/{command_id}` preferred)
4. after each poll, refresh current collection state from command status
5. wait for `completed` or terminal error state
6. on completion, read `result` and `task_updates` for records/count/export snapshot and include key fields in the final reply

Quick query examples:

```bash
curl -H "Authorization: Bearer <token_or_api_key>" \
  "https://i-sync.cn/api/v1/connector/cloud/commands?device_id=<device_id>"
```

```bash
curl -H "Authorization: Bearer <token_or_api_key>" \
  "https://i-sync.cn/api/v1/connector/cloud/commands/<command_id>"
```

## Final Reply

When successful:

1. Mention whether the run used `local` or `cloud` mode.
2. If `cloud` mode was used, include the command status.
3. If export mode is `bitable` and `export.tableUrl` exists, include the table link first.
4. If export mode is `csv`, explicitly say export mode is CSV.
5. Then include:
   - status
   - export status
   - collected count
   - short analysis

When `bitable` export is expected but no table link exists, explicitly say export did not finish correctly.

## Troubleshooting

- `pluginConnected=false`
  - Chrome/plugin is not connected to the bridge
- bridge/status mismatch
  - in `local` mode, ensure collect, status, and stop all use the same local base URL
- cloud dispatch auth failed
  - check `defaultCloudToken`
- cloud dispatch could not reach device
  - check `defaultCloudDeviceId` and whether the local connector is online
- `TASK_RUNNING`
  - use stop + retry, or `--force-stop-before-start`
- long record output hiding key fields
  - trust the connector loop's compact summary output rather than raw task JSON
