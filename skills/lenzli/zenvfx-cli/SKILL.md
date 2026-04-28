---
name: zenvfx-cli
description: Use this skill when the user needs to create AI videos, manage canvases, nodes, files, or interact with the ZenVFX platform via CLI. Trigger keywords include "画布", "视频生成", "zenvfx", "canvas", "node", "AI视频", "文生视频".
metadata: {"openclaw": {"emoji": "🎬", "os": ["darwin", "linux"], "requires": {"bins": ["zenvfx"], "env": ["ZENVFX_MCP_TOKEN"]}, "primaryEnv": "ZENVFX_MCP_TOKEN", "install": [{"id": "npm", "kind": "command", "command": "npm install -g @tencent/zenvfx-cli --registry https://mirrors.tencent.com/npm/", "bins": ["zenvfx"], "label": "Install ZenVFX CLI (npm)"}]}}
---

# ZenVFX CLI Skill

## 概述

ZenVFX CLI 是 AI 视频创作平台的命令行工具，通过画布（Canvas）中的节点（Node）+ 连线（Edge）构建 AI 生成任务。

- **CLI 入口**：`zenvfx <command>`
- **输出协议**：stdout 纯 JSON（`{"ok":true,"data":{...}}` / `{"ok":false,"error":{...}}`），解析时用 `2>/dev/null` 过滤 stderr
- **优先级**：系统中若同时存在 `zenvfx-mcp`，**一律优先使用 `zenvfx` CLI**，不要混用两者操作同一画布

---

## 认证与安装

```bash
# 安装
npm install -g @tencent/zenvfx-cli --registry https://mirrors.tencent.com/npm/

# 认证（自动保存 mcpToken/defaultProject/defaultWorkspace 等配置）
zenvfx auth:login <token>          # 可选 --host <host-url>
```

`auth:login` 返回 `saved` 字段标识各配置是否已自动设置。若 `saved.defaultProject` 或 `saved.defaultWorkspace` 为 `false`，需手动补全：

```bash
zenvfx project:list 2>/dev/null              # 查看可用项目
zenvfx project:switch <project-id>           # 一键切换项目（自动更新 workspace）
```

`project:switch` 自动解析 workspace 的规则（仅依赖 `userId`，不依赖 `username`，因为 username 是用户可自定义的别名）：
1. **精确匹配**：`/{projectId}/用户空间/` 下目录名以 `_{userId}` 结尾
2. **模糊匹配**：目录名包含 `userId`
3. 均未命中则清空 `defaultWorkspace`，需手动设置

也可手动设置：
```bash
zenvfx config:set defaultProject <project-id>
zenvfx config:set defaultWorkspace "/<project-id>/用户空间/xxx"
```

也可通过环境变量：`ZENVFX_MCP_TOKEN`、`ZENVFX_PROJECT`

---

## 命令速查

### 配置

| 命令 | 用途 |
|------|------|
| `auth:login <token>` | 一键认证，可选 `--host` |
| `config:set <key> <value>` | 手动设置（key：`host`/`wsHost`/`mcpToken`/`defaultProject`/`defaultUsername`/`defaultUserId`/`defaultWorkspace`） |
| `config:get <key>` / `config:list` | 读取配置 |
| `project:list` | 列出项目 |
| `project:switch <projectId>` | 切换项目（自动更新 defaultProject + defaultWorkspace，workspace 匹配仅依赖 `userId`，不依赖 `username`），可选 `--no-workspace` |

### 文件系统（路径格式：`/<projectId>/目录/文件名`）

| 命令 | 用途 |
|------|------|
| `file:stat --path <p>` | 文件/目录详情 |
| `file:readdir --path <p>` | 目录内容（不递归） |
| `file:mkdir --path <p>` | 创建目录（默认递归） |
| `file:rm --path <p>` | 删除文件/目录 |
| `file:tree --path <p>` | 目录树，可选 `--max-depth` |
| `file:path-to-id --path <p>` | 路径转内部 ID |
| `file:upload --local-file <本地路径> --file-path <ZenFS路径> --project-id <id>` | 上传本地文件到 COS 并注册到 ZenFS，可选 `--title` |

### 画布管理（标 `[S]` 的命令需先 `canvas:open`）

| 命令 | 用途 |
|------|------|
| `canvas:create --name <名称>` | 创建画布，可选 `--path`（默认 `defaultWorkspace`） |
| `canvas:list` | 列出画布，可选 `--list-path` |
| `canvas:open --canvas <path>` | 打开画布（启动 Session） |
| `canvas:info` `[S]` | 查看画布信息 |
| `canvas:save` `[S]` | 手动保存（一般不需要，见下方说明） |
| `canvas:run --node <id>` `[S]` | 运行节点，`--wait` 同步等待（默认超时 10 分钟） |

### 节点操作 `[S]`

| 命令 | 用途 |
|------|------|
| `canvas:node:list` | 列出所有节点 |
| `canvas:node:info --id <id>` | 节点详情（options/values 已 resolve 实际值，含 taskId/taskStatus） |
| `canvas:node:add <type>` | 添加节点，可选 `--name --position "x,y"` |
| `canvas:node:remove --id <id>` | 删除节点 |
| `canvas:node:props --id <id>` | 修改节点自身属性，可选 `--name`（标题）`--position "x,y"`（位置） |
| `canvas:node:set --id <id>` | 设置参数（推荐 `--options-json`） |
| `canvas:node:prompt --id <id> --prompt <text>` | 解析 prompt 中 @占位符，可选 `--model` |

多节点时用 `--position "x,y"` 避免重叠，建议水平间隔 400px。

### 连线操作 `[S]`

| 命令 | 用途 |
|------|------|
| `canvas:edge:list` | 列出所有连线 |
| `canvas:edge:add` | 连线（`--source --source-handle --target --target-handle`） |
| `canvas:edge:remove --id <id>` | 删除连线 |

### 查询（不需 Session）

| 命令 | 用途 |
|------|------|
| `node:list` | 所有可用节点类型定义（本地） |
| `node:defs` | 完整节点定义含模型信息（需认证） |
| `node:model <nodeType>` | 节点支持的模型列表（需认证） |
| `task:status <taskId> --canvas-id <id>` | 查询任务状态 |

### 守护进程

| 命令 | 用途 |
|------|------|
| `daemon:ping` / `daemon:status` / `daemon:stop` | 检测/查看/停止 daemon |

---

## 重要规则

### 1. 连线 handle 必须使用 pinName

`--source-handle` 和 `--target-handle` **必须用节点定义中的 pinName**，不是后端 API 的 field_path。用错会导致连线保存成功但前端不显示。

通过 `node:list` 或 `node:defs` 查询正确的 pinName。常用速查：

| 节点类型 | 输入 pinName | 输出 pinName |
|----------|-------------|-------------|
| `image_generator` | `prompt`, `referenceImage` | `outputImage` |
| `normal_video_generator` | `referenceImage`, `prompt` | `outputVideo` |
| `composite_video_generator` | `inputVideo`, `inputImage`, `prompt` | `outputVideo` |
| `first_to_last_video_generator` | `firstReferenceImage`, `lastReferenceImage`, `prompt` | `outputVideo` |
| `comprehensive_reference_generator` | `inputVideo`, `inputImage`, `inputAudio`, `prompt` | `outputVideo` |

### 2. 编辑命令自动保存 — 不要重复 save

`canvas:node:add`、`canvas:node:remove`、`canvas:node:props`、`canvas:node:set`、`canvas:edge:add`、`canvas:edge:remove` 执行成功后**自动保存画布**，无需额外调用 `canvas:save`。

### 3. 画布路径

`canvas:create` 返回的 `canvasPath` 不含 `.canvas` 后缀，canvas 类命令带不带后缀均可。`file:stat` 等文件命令需要完整文件名（带 `.canvas`）。

---

## 核心流程：生成 AI 视频

```bash
# 0. 认证（一次性）
zenvfx auth:login <your-mcp-token>

# 1. 创建画布
CREATE_RESULT=$(zenvfx canvas:create --name "测试画布" 2>/dev/null)
CANVAS_PATH=$(echo $CREATE_RESULT | grep -o '"canvasPath":"[^"]*"' | sed 's/"canvasPath":"//;s/"$//')

# 2. 打开画布
zenvfx canvas:open --canvas "${CANVAS_PATH}.canvas"

# 3. 添加节点
RESULT=$(zenvfx canvas:node:add normal_video_generator --name "文生视频" --position "0,0" --canvas "${CANVAS_PATH}" 2>/dev/null)
NODE_ID=$(echo $RESULT | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"$//')

# 4. 设置参数（model/clarity 等值须通过 node:model <type> 动态查询，勿硬编码）
zenvfx canvas:node:set --id $NODE_ID --options-json \
  '{"prompt":"傍晚的海边，小孩子嬉戏玩水","model":"kling","clarity":"RESOLUTION_720P","ratio":"16:9","duration":5}' \
  --canvas "${CANVAS_PATH}"

# 5. 运行并等待（推荐 --wait，超时 30 分钟）
zenvfx canvas:run --node $NODE_ID --canvas "${CANVAS_PATH}" --wait --timeout 1800000 2>/dev/null
# 返回: {"status":"completed","outputs":[{"url":"..."}]}
```

**异步模式**：不加 `--wait` 立即返回 `taskId`，再用 `task:status <taskId> --canvas-id <canvasId>` 轮询（建议 10 秒间隔，30 分钟超时）。`canvasId` 通过 `file:path-to-id --path "${CANVAS_PATH}.canvas"` 获取。

---

## 节点信息返回结构

`canvas:node:info --id <id>` 返回的 `options` 和 `values` 数组中，每个条目已 resolve 为：

| 字段 | 说明 |
|------|------|
| `optionName` | 参数名 |
| `refId` | entity 引用 ID |
| `value` | **当前实际值**（set 后可直接通过 info 读回） |
| `type` | 值类型（`text`/`string`/`number`/`unknown`） |

示例：
```json
{
  "options": [
    {"optionName": "prompt", "value": "一只猫咪", "type": "text"},
    {"optionName": "model", "value": "kling", "type": "string"},
    {"optionName": "ratio", "value": "16:9", "type": "string"}
  ]
}
```

---

## 节点参数

通过 `--options-json` 统一传参：

| 参数 | 类型 | 说明 |
|------|------|------|
| `prompt` | string | 提示词 |
| `model` | string | 模型 ID（**必须通过 `node:model <type>` 查询**） |
| `clarity` | string | 分辨率枚举 |
| `ratio` | string | 画幅比例 |
| `duration` | number | 时长秒数（仅视频节点） |

常用节点类型：

| nodeUiType | 说明 |
|---|---|
| `normal_video_generator` | 文生视频 / 图生视频 / 图片参考 |
| `image_generator` | 文生图 / 图生图 |
| `first_to_last_video_generator` | 首尾帧视频 |
| `composite_video_generator` | 视频编辑 / 视频参考 / 动作迁移 |
| `comprehensive_reference_generator` | 全能参考生视频（支持图/视频/音频混合输入） |
| `llm` | 大模型节点（多模态理解，支持 Claude / Gemini / GPT） |
| `text_input` / `image_input` / `video_input` / `audio_input` | 输入节点 |
| `scene_rerender_*` | 场景转绘（首帧/尾帧/首尾帧，自定义节点） |
| `video_relighting_*` | 视频重打光（自定义节点） |
| `character_edit_*` | 角色编辑（人偶化/改变ID/保留ID，自定义节点） |
| `creature_*` | 生物控制（表情/运动，自定义节点） |

**视频节点建议**：模型 `kling` + `RESOLUTION_720P`（比 1080P 快 2-3 倍）。

### Prompt @占位符

prompt 中可用 `@参考图`、`@首帧图1`、`@尾帧图1`、`@参考视频`、`@参考音频` 引用上游输入。通过 `canvas:node:prompt` 命令自动转换为模型特定格式：

| 模型 | `@首帧图1` → | `@尾帧图1` → | `@参考图` → |
|------|-------------|-------------|------------|
| `kling-video-o1` | `<<<image_1>>>` | `<<<image_2>>>` | `<<<image_1>>>` |
| `viduq2-pro` | `@1` | `@2` | `@1` |
| 其他 | `第一张首帧图` | `第一张尾帧图` | `第一张参考图` |

用法：先调用 `canvas:node:prompt` 获取 `resolved` 字段，再写入节点。需连线已建立且上游已完成。

---

## 异常处理

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `AUTH_REQUIRED` | Token 未配置 | `auth:login <token>` |
| `MCP_TOKEN_INVALID` | Token 无效/过期 | 重新获取后 `auth:login` |
| `CANVAS_NOT_FOUND` | 画布不存在 | 检查路径，`file:stat` 确认 |
| `CANVAS_SAVE_FAILED` | 保存失败 | 重试 2-3 次，间隔 3-5 秒 |
| `NODE_NOT_FOUND` | 节点不存在 | `canvas:node:list` 确认 |
| `OPTION_NOT_FOUND` | 无该选项 | `canvas:node:info --id <id>` 查看 |
| `DAEMON_TIMEOUT` | daemon 超时 | `daemon:stop` 后重试 |
| `TASK_SUBMIT_FAILED` | 任务提交失败 | 检查节点参数 |

**daemon 异常强制清理**：
```bash
zenvfx daemon:stop
kill $(cat ~/.config/zenvfx/daemon.pid) 2>/dev/null
rm -f ~/.config/zenvfx/daemon.sock ~/.config/zenvfx/daemon.pid
```
