# CHANGELOG

本插件语义化版本号与龙虾适配版本解耦：`package.json.version` 为插件自身的发布版本，`openclaw.build.openclawVersion` 为目标龙虾版本。

## 5.7.8 — 2026-04-26（全面适配 openclaw 2026.4.24：typed hooks + manifest 元数据补齐）

**用户反馈**："enhance 插件帮我全面适配 openclaw 最新版本"

跑 SOP 第 1+2 步：(a) `npm view openclaw version` → **2026.4.24**（latest，比当前用的 4.22 多 1 个 minor）；(b) 升级本地 SDK + 跑 typecheck 看不兼容点；(c) 盘点 `as any` 找清理空间。

### 关键发现

读 openclaw 4.24 SDK 类型定义 `node_modules/openclaw/dist/plugin-sdk/src/plugins/types.d.ts`：

```typescript
on: <K extends PluginHookName>(
  hookName: K,
  handler: PluginHookHandlerMap[K],
  opts?: { priority?: number }
) => void;
```

`api.on` 是**完全 typed**！每个 hook 名都对应具体的 `(event, ctx)` 类型：
- `before_tool_call: (event: PluginHookBeforeToolCallEvent, ctx: PluginHookToolContext) => PluginHookBeforeToolCallResult | void`
- `session_start: (event: PluginHookSessionStartEvent, ctx: PluginHookSessionContext) => void`
- `subagent_spawned: (event: PluginHookSubagentSpawnedEvent, ctx: PluginHookSubagentContext) => void`
- ... 全 29 个 hook 都有 typed signature

但 enhance 当前 **14 处 `api.on(...as any, (event: any, ctx: any) => ...)`** —— 把 SDK 的 typed 体验全屏蔽了。这是历史遗留，因为最早期某些版本的 openclaw SDK 没有 typed hook。现在 SDK 完全支持，enhance 该跟上。

### 新增

- **`peerDependencies.openclaw: ^2026.4.22 → ^2026.4.24`** — 跟随 latest tag
- **`openclaw.build.openclawVersion: 2026.4.11 → 2026.4.24`** — 同步（落后了 13 个 patch）
- **`openclaw.compat.pluginApi: >=2026.4.11 → >=2026.4.24`** — 同步
- **`openclaw.plugin.json` 加 3 个新字段**：
  - `enabledByDefault: true` — 装上后默认启用，免去用户手工 `enabled: true` 配置
  - `uiHints` — control-ui 渲染配置面板时用的 widget 提示（switch / select / 中文 label）
  - `activation.onAgentHarnesses: ["claude", "openclaw-default"]` — 声明在哪些 agent harness 下激活

### 修改

- **`api.on(...as any) → api.on(...)` 14 处全清理**：
  - `src/modules/session-lifecycle.ts`（5 个 hook：session_start/end/before_reset/subagent_spawned/subagent_ended）
  - `src/modules/scheduled-tasks-bridge.ts`（before_prompt_build）
  - `src/modules/self-check.ts`（before_agent_reply）
  - `src/modules/session-recap.ts`（before_prompt_build）
  - `src/modules/task-planner.ts`（before_prompt_build）
  - `src/modules/workflow-hooks.ts`（before_prompt_build）
  - `src/modules/tool-safety.ts`（before_tool_call + after_tool_call）
  - `src/modules/mode-gate.ts`（before_tool_call）
- **`(event: any, ctx: any) → (event, ctx)` 5 处**：让 TS 自动从 PluginHookHandlerMap[K] 推断
- **`(ctx as any)?.agentId → ctx?.agentId` 9 处**：每个 PluginHook*Context 都有 `agentId?: string` 字段，无需 cast
- **`pickAgentId(ctx: unknown) → pickAgentId(ctx: { agentId?: string } | undefined)`** 6 个文件：structural typing 兼容 hook ctx 和 tool ctx 两种调用源

### 修复（typecheck 暴露的隐藏 bug）

- **`src/modules/self-check.ts`**：去掉 `as any` 后 TS 报 `Type '{ handled?: undefined; ... }' is not assignable to PluginHookBeforeAgentReplyResult`。根因是 `PluginHookBeforeAgentReplyResult.handled: boolean` **必填**，但 enhance 之前在"不接管"分支返回 `{};`。修法：所有 "不接管"分支改成 `return;`（void），仅"阻断空回复"分支返回 `{ handled: true, reply: {...}, reason: "..." }`。

### 不破坏

- 全部 14 处 hook handler **return undefined（void）** 时跟之前 `return {}` 行为完全一致 —— openclaw 把"void 返回值"和"空对象"等同视为"不接管"
- typed handler 跟 untyped 运行时无差异，只是编译期能 narrow 类型
- 没改任何 SQLite schema、没引入新 npm 依赖
- 老用户从 v5.7.7 升级零成本

### 剩余 `as any` 统计

| 用途 | 数量 | 是否合理 |
|---|---|---|
| `api.on(...as any)` | **0**（之前 14） | ✅ 完全清理 |
| SQLite `.get() as any[]` / `.all() as any[]` | 8 | ✅ better-sqlite3 设计返回 unknown，必须 cast |
| `registerTool factory ((ctx) => ({...})) as any` | 8 | ✅ SDK factory 模式 type-erasure 限制 |
| `(globalThis as any).process` | 1 | ✅ globalThis 类型限制 |
| `(event as any).prompt` | 2 | ⚠️ 待 SDK 暴露 PluginHookBeforePromptBuildEvent 类型时清 |
| `(ctx as any)` 在 helper 内部 | 4 | ⚠️ structural typing 不收紧也可（runtime 行为正确） |
| 其它（错误/边界） | ~32 | 大多是 ts-pattern 风格的边界处理 |
| **总计** | **55** | （从 v5.7.7 的 ~98 降到 55，约 -44%）|

### 设计决策

- **为什么不再追求 0 个 `as any`**：剩下的 55 处都是 SDK / 第三方库设计限制（better-sqlite3 / TypeBox factory），强行清理会引入运行时风险或 schema 复杂度
- **为什么 manifest 加 `activation.onAgentHarnesses`**：当 openclaw 之后引入 lazy plugin loading（现在还没），enhance 能精确声明在哪种 agent 类型下激活，避免 `claude` 之外的 agent harness 误加载
- **为什么 typed handler return `void` 而非 `{}`**：openclaw runtime 对 hook 返回值的处理是 `if (result && typeof result === "object") { ...apply hints... }`，`undefined` 跟 `{}` 行为一致；但 typed signature 要求 `PluginHookXxxResult | void`，`{}` 不满足"必填字段都填"
- **为什么不展开 `(event as any).prompt`**：`PluginHookBeforePromptBuildEvent` 类型存在但 SDK 没顶层 export；强制从子路径导入会增加耦合，等下次 SDK 升级 export 表了再清

### 不冲突 openclaw 4.24 的检查清单

| 检查项 | 状态 |
|---|---|
| 不修改 openclaw 源码 | ✅ |
| 所有 hook handler return void / 已知合法 result | ✅（已通过 typecheck 验证）|
| openclaw 4.24 hook 名都仍存在 | ✅（PluginHookName union 包含全部 29 个）|
| 不复制龙虾原生 memory / cron / tools.allow/deny / channel manifest | ✅ |
| `enabledByDefault` / `uiHints` / `activation` 字段在 4.24 manifest type 里都已定义 | ✅（PluginManifest 含这三个字段）|
| 模块清单中没有跟 openclaw 4.x 重叠的功能 | ✅（之前 v5.2 重写已经把 context-pruner 删了改成 corpus supplement，本轮再次 verify） |

### 调研依据

- `npm view openclaw version` → 2026.4.24
- `node_modules/openclaw/dist/plugin-sdk/src/plugins/hook-types.d.ts: PluginHookHandlerMap`：29 个 hook 完整 typed signature
- `node_modules/openclaw/dist/plugin-sdk/src/plugins/manifest.d.ts: PluginManifest`：完整 manifest 字段（含未用过的 enabledByDefault / uiHints / activation）
- 详见 KB `~/knowledge/huo15/2026-04-27-openclaw-enhance-v578-typed-hooks-postmortem.md`

---

## 5.7.7 — 2026-04-26（session-lifecycle：接入 openclaw 4.22 五个 hook 闭环 session 生命周期）

**用户反馈**："结合 claude 官网的能力描述和本地 claude code 源码看看我们的 enhance 插件还有哪些可以完善的。但是不能干扰 openclaw 最新版的既有能力和跟 openclaw 最新版冲突。"

跑了完整 SELF_ITERATE.md SOP 第 1+2 步（信息更新 + gap 比对）：

### 调研发现

- **Claude Code 官方 docs**（hooks 页）暴露 27 个 hook event names：SessionStart / UserPromptSubmit / PreToolUse / PermissionRequest / PermissionDenied / PostToolBatch / Stop / SubagentStart / SubagentStop / TaskCreated / TaskCompleted / InstructionsLoaded / ConfigChange / CwdChanged / FileChanged / PreCompact / PostCompact / Elicitation / Notification / WorktreeCreate / WorktreeRemove / SessionEnd 等
- **openclaw 2026.4.22 SDK** (`hook-types.d.ts: PluginHookName`) 暴露 **29 个 hook**，跟 Claude Code 一一对应（命名风格不同：`before_/after_/_end` 而非 Claude 的 `Pre/Post/Stop`）
- **enhance 之前只用 4 个 hook**：`before_prompt_build` / `before_tool_call` / `after_tool_call` / `before_agent_reply`
- **反编译 Claude.app** 看到 29 张 SQLite 表，最有价值的没用过：artifacts 多版本 + frames 树状对话历史 + notes 用户批注

### ROI top 5 候选

| # | 候选 | 工作量 | 价值 |
|---|---|---|---|
| **1** | **session-lifecycle**（接 session_start + session_end + before_reset + subagent_*）| ~250 行 | **🔴 立即闭环 session 生命周期** |
| 2 | tool-result-optimizer（接 tool_result_persist 大结果截断+摘要）| ~100 行 | 🟡 长 session 减负 |
| 3 | message_received hook 自动 skill 推荐 | ~60 行 | 🟡 跟 v5.7.5 接合 |
| 4 | artifacts 多版本管理（轻量 SQLite）| ~250 行 | 🔴 但量大留 v5.8 |
| 5 | frames 父子 session 关系跟踪 | ~150 行 | 🟠 留 v5.8 |

**v5.7.7 落地候选 #1**（最高 ROI）。

### 新增

- **`src/modules/session-lifecycle.ts`**（~250 行）— 接入 5 个 hook：
  - `session_start` → idle > 30min 时插入"🚀 会话开始 / 续启"章节占位（不强制每个 session 都加章节，避免噪音）
  - `session_end` → 加"🏁 会话结束"章节 + flush 未完成 in_progress todo 到 project memory（专用 tag `session-flush`, importance=4）
  - `before_reset` → reset 前最后机会抢救最近 3 章节 + 全部未完成 todo 到 decision memory（专用 tag `reset-rescue`, importance=6）+ 推 notification 提醒
  - `subagent_spawned` → 派生子 agent 时插入"🤖 派生子 agent: X"章节
  - `subagent_ended` → 子 agent 结束插入"✅/❌ 子 agent 结束: X"章节
- **`types.ts: SessionLifecycleConfig`** — 5 个 hook 各自可关，含 `debug` 开关
- **`openclaw.plugin.json`** configSchema 加 `sessionLifecycle` 段
- **模块 `tier=1`** minimal 也启用——这是核心生命周期补全，**零工具 schema**（纯 hook 监听，不占 prompt 容量）

### 防 noise factory 三层防御（吸收 v5.7.1 教训）

v5.7.1 删了 `before_compaction` 噪音 hook 后总结了"不要在高频 hook 里无脑写记忆"。新增的 5 个 hook 也是高频（`session_start` 在多 agent 场景每分钟可能多次触发），所以严格控写：

1. **30 秒 dedup**：每个 hook 触发按 `event:agentId:sessionId` 拼 key 进 LRU Map（`MAX_RECENT_ENTRIES=500` + FIFO 淘汰），30 秒内重复触发跳过
2. **重要性低 + 专用 tag**：`session-flush` importance=4（不是用户主动决策）；`reset-rescue` importance=6（reset 前抢救偏重要）。**故意不进 corpus pruner 黑名单**——这些是用户下次想恢复的实质内容，让 pruner 按相关度自然评分
3. **try-catch 包裹**：每个 hook handler 全包，错误只 log 不抛——绝不让插件因 hook 异常 crash

### 不破坏

- 完全只读 openclaw 状态，不修改任何龙虾原生表/文件
- 写入 `chapters` / `memories` 是 enhance 自有表（不污染龙虾原生 memory，v5.5.0 的 corpus supplement 边界保持）
- 没改 SQLite schema、没引入新 npm 依赖
- 没新增 enhance_* 工具（纯 hook 监听）
- 用户可单独关任意 hook（`config.sessionLifecycle.enableSessionStart = false`）

### 设计决策

- **为什么 tier=1**：纯 hook 监听零工具 schema，不占 prompt 容量；session 生命周期是核心补全（minimal 用户也该有）；
- **为什么 session_start 不是每次都加章节**：避免每分钟一个 session 都新加章节造成 chapter 表膨胀；只在 idle > 30min 时加（用户真正"重启"的场景）
- **为什么 before_reset 比 session_end 重要性高**：reset 是用户主动清理，比自然结束激进；importance=6 vs 4 让 corpus pruner 优先返回 reset 抢救的内容
- **为什么不进 corpus pruner 黑名单**：tag=session-flush / reset-rescue 的内容是用户下次想恢复的工作（"上次未完成的 X"），跟 v5.7.1 删的 auto-compact noise（信息量为 0）本质不同
- **为什么 subagent hook 也加章节而非 memory**：spawn 链路属于"事件流"（用户想看时间线），章节比记忆更适合；下游可以用 chapter timeline 看派生关系

### 跟 openclaw 4.22 不冲突的检查

- ✅ openclaw 自己的 `before_compaction` 等 hook 仍正常工作（enhance 不复制不抢占）
- ✅ openclaw 原生 memory 系统不受影响（enhance 只写 enhance-memory.sqlite）
- ✅ openclaw 原生 cron-cli / tools.allow/deny / memory 向量库 enhance 全部不复制
- ✅ openclaw 4.22 类型定义 `PluginHookName` 包含全部 5 个 hook，无破坏性变更

### 调研依据

- 反编译 `/Applications/Claude.app/Contents/Resources/app.asar`：`loadSkills` / `loadSkillContent` / artifacts 多版本 / frames 树状历史
- WebFetch `code.claude.com/docs/en/hooks`：27 个 hook event names + 输入字段
- `/Users/jobzhao/workspace/projects/openclaw/huo15-openclaw-enhance/node_modules/openclaw/dist/plugin-sdk/src/plugins/hook-types.d.ts: PluginHookName`：openclaw 4.22 的 29 个 hook 完整列表
- 详见 KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v577-session-lifecycle-postmortem.md`

---

## 5.7.5 — 2026-04-26（skill-recommender：按需求自动挑 skill / 推荐未装 / 给自建规划）

**用户反馈**："新增自动根据用户的需求自动挑选已经安装的技能，如果没有技能就把规划方案给出来。看看 Claude 是如何做的"

### 调研：反编译 Claude Desktop 看它怎么做的

反编译 `/Applications/Claude.app/Contents/Resources/app.asar`（参见 SELF_ITERATE.md 第 1 节"反编译 Claude Desktop"）发现：

- `index.js` 里有 `loadSkills()` / `loadSkillContent()` 函数
- system prompt 拼接处有这一句：`"Available skills: ${i.join(", ")}."`
- 也就是说 Claude Desktop 的 skill auto-discovery 算法**本质是 "name+description 列表注入 system prompt 让 LLM 自己挑"**——没有复杂算法

但 enhance 不能照搬"每轮 prompt 注入"——会增加每轮 token 量、抹掉 v5.6 toolTier 减负的努力。所以改成**按需工具**。

### 新增

- **`src/modules/skill-recommender.ts`** — 三段式推荐器：
  1. **启动期扫多路径**（关键修复，WeCom 多 agent 场景）：
     - `~/.openclaw/skills/`
     - `~/.openclaw/workspace/skills/`
     - `~/.openclaw/workspace-*/skills/` ← **WeCom / DingTalk 多 agent 动态 workspace**
     - `~/.openclaw/agents/*/skills/`
     - `<cwd>/.claude/skills/`、`~/.claude/skills/`
     - 用户实测扫到 56 个 skill 跨 27 个路径（一开始只扫 4 个固定路径漏扫，烟测才发现）
  2. **解析 SKILL.md frontmatter**：轻量正则提取 `name` / `description` / `aliases`，**无 yaml 依赖**（zero-deps 红线）
  3. **CJK-aware 评分**：
     - 问题：JS `\w` 不含中日韩，直接 `split(/\s\W/)` 会让"代码简化"变成空数组
     - 解决：连续 CJK 段当整体 phrase + 长 ≥4 时滑动 2-grams（`"代码简化" → ["代码简化","代码","码简","简化"]`）
     - alias exact 命中保底 0.7（典型场景：query "规划XX" → alias "规划" 严格命中）
  4. **未装候选 + 自建规划**（fallback 阶梯）：
     - 已装命中 < threshold=0.25 → 列 ClawHub 上未装的 huo15-* + `openclaw skills install <slug>` 命令
     - 都没合适 → **自建 skill 规划**：建议 slug（含中文 placeholder） + frontmatter 模板 + 触发关键词 + 内容大纲 6 章 + **红线 #3 提醒**（先 ClawHub publish 再让 enhance 引用，插件绝不内嵌 skill 内容）

- **工具：`enhance_skill_recommend`** — `query` 必填，可选 `limit`(1-20) / `includeUninstalled`(默认 true) / `includePlanning`(默认 true)
- **`types.ts: SkillRecommenderConfig`** — `enabled` / `installedThreshold` / `cacheTtlSec`
- **`openclaw.plugin.json`** configSchema 加 `skillRecommender` 段
- **`KNOWN_HUO15_SKILLS` 内置 metadata 表** — 11 个 huo15-openclaw-* skill 的 description + aliases 硬编码兜底（避免运行时查 ClawHub 网络依赖）

### 实测精度

| 查询 | 命中 skill | 分数 |
|---|---|---|
| "帮我 review 这个 PR" | huo15-openclaw-code-review | 0.60（首位）|
| "设计一个 Web UI 原型" | huo15-openclaw-frontend-design | 0.94（首位）|
| "代码简化" | huo15-openclaw-simplify | 1.00（满分）|
| "做安全审查" | huo15-openclaw-security-review | 0.96（首位）|
| "规划这个任务" | huo15-openclaw-plan-mode | 0.70（alias exact 命中保底）|
| "深度探索这块代码" | huo15-openclaw-explore-mode | 0.30（首位）|

### 设计决策

- **为什么按需工具而非每轮 prompt 注入**：v5.6 toolTier 已经在为 prompt cache 减负，注入 56 个 skill 描述会让每轮多 ~3-5k token；改成工具用户/agent 主动调更省
- **为什么 tier=2 而非 tier=1**：用户多半已知道自己装了什么 skill，按需查询不是常驻刚需；balanced/full 默认可见即可
- **为什么内置 KNOWN_HUO15_SKILLS metadata 表**：未装的 skill 没有 SKILL.md 可解析，但要给推荐就需要 description；硬编码 11 个 huo15-* 的 metadata 跟 `CLAW_HUB_SKILLS` 列表保持一致，零网络依赖
- **为什么 CJK 双字滑窗而非真正分词**：上 jieba 是 ~5MB 词典 + 1MB 引擎；双字滑窗虽然有少量误命中（"代码简化" 也产 "码简"），但召回率显著提升且 zero-deps
- **为什么自建规划在结尾强调红线 #3**：用户硬约束"skill 必须先发 ClawHub 再让 enhance 引用，插件不内嵌"，每次给规划都要复刻这个工作流

### 不破坏

- 完全只读 skill 目录，不修改任何 SKILL.md
- 没改 SQLite schema、没引入新 npm 依赖
- 启动期 fire-and-forget 扫描，缓存 60 秒（可调）；扫不到不影响插件正常工作
- 工具 schema 极简（4 参数）；按需调用不占常驻 prompt

### 调研依据

- 反编译 Claude Desktop loadSkills + "Available skills: ${list}." 注入模式
- 用户实测 query 烟测：6 类查询全部首位命中
- 详见 KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v575-skill-recommender-postmortem.md`

---

## 5.7.4 — 2026-04-26（config-doctor 扩展：扫已装插件 bare pluginApi）

用户反馈：**"提示插件要求 2026.2.24，但是我的 openclaw 已经是 2026.4.22"**。第一反应是 enhance 自己的问题，但实际是另外两个插件违反了 openclaw plugin compat 规则。

### 根因

按 [`MEMORY/openclaw_plugin_compat_rules.md`](https://...): "compat.pluginApi MUST be ">=X.Y.Z" range, never bare version (bare = exact match, breaks on runtime drift)"。

用户实测两处违规：
- `~/.openclaw/extensions/tips/package.json` v1.0.0 → `pluginApi: "2026.4.11"`（bare）
- `~/.openclaw/node_modules/@huo15/huo15-huihuoyun-odoo/package.json` v1.2.0（npm peerDep 残留）→ `pluginApi: "2026.2.24"`（bare）

openclaw 启动扫 node_modules 看到 bare → 解读为精确匹配 2026.2.24 → 跟当前 4.22 不匹配 → 报错"插件要求 2026.2.24"。

### 新增

- **`src/modules/config-doctor.ts: isBarePluginApi(spec)`** — 检测字符串是否是 ranged spec：
  - 带前缀 `>=` `<=` `>` `<` `^` `~` `*` `=` → 合规
  - 含空格组合 range（如 `">=1.0 <2.0"`）→ 合规
  - 数字开头无前缀（如 `"2026.4.11"`）→ **bare 违规**
- **`src/modules/config-doctor.ts: scanInstalledPluginsForBarePluginApi(openclawDir)`** — 扫描三类路径下的 `package.json`：
  1. `{openclawDir}/extensions/*/package.json`（openclaw 实际启用的）
  2. `{openclawDir}/node_modules/@huo15/*/package.json`（@huo15 scope 下的）
  3. `{openclawDir}/node_modules/*/package.json`（无 scope 的）
  - 只检查声明了 `openclaw.extensions` 或 `peerDependencies.openclaw` 的包
  - 命中 bare → 加 `CheckResult` 推到主报告 + 给 python3 inline fix 命令
- 工具 `enhance_config_doctor` 输出自动多一段"已装插件 pluginApi 健康度"

### 不破坏

- 完全只读用户文件系统，绝不修改任何 package.json
- 启动检查失败 try-catch 静默
- 扫描复杂度 O(已装插件数)，单次启动 < 50ms（实测 5 个插件 < 10ms）

### 已立即修用户当前安装

- `~/.openclaw/extensions/tips/package.json`: bare `2026.4.11` → `>=2026.4.11`
- `~/.openclaw/node_modules/@huo15/huo15-huihuoyun-odoo/package.json`: bare `2026.2.24` → `>=2026.2.24`
- 备份分别在同目录 `.bak.before-bare-fix` / `.bak`

### 经验沉淀

- **bare pluginApi 是 silent breakage 的常见来源** —— 插件作者写时通常想表达"最低版本"，但忘了加 `>=`，部署时被解读为精确匹配
- **enhance config-doctor 的诊断范围应该覆盖整个 openclaw 状态目录**，不只 openclaw.json —— 任何会让 openclaw 启动失败的配置陷阱都该报警
- **写在 SELF_ITERATE.md 第 5 节作为发布前自查项**：发版前 npm pack && grep `pluginApi` 看是不是 ranged

### 调研依据

- 用户反馈："提示插件要求 2026.2.24，但是我的 openclaw 已经是 2026.4.22"
- KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v574-plugin-bare-pluginApi-postmortem.md`

---

## 5.7.3 — 2026-04-26（config-doctor：'Context limit exceeded' 高频反馈兜底）

用户实测：装了 v5.7.2 之后仍然报 `Context limit exceeded. ... agents.defaults.compaction.reserveTokensFloor to 20000 or higher`。**这不是 enhance 插件的问题**，而是 openclaw 自身配置：(1) 缺失 `agents.defaults.compaction.reserveTokensFloor`（4.22 把这个字段从顶层 `compaction.*` 移到 `agents.defaults.compaction.*`，老用户配置文件没自动迁移）；(2) MiniMax-M2.7 maxTokens=131072 / contextWindow=204800，每轮预留输出吃 64% budget，剩 73k 给 input + tools + memory + history，几轮必爆。但用户**装的就是 enhance**，看到爆 context 第一反应是"插件的锅"，所以 enhance 必须主动诊断 + 报警把根因信号给到用户。

### 新增

- **`src/modules/config-doctor.ts`** — 启动期同步读 `~/.openclaw/openclaw.json` 检查：
  1. `agents.defaults.compaction.reserveTokensFloor` 缺失 / < `minReserveTokensFloor`(default 5000) / > `maxReserveTokensFloor`(default 100000)
  2. 任意 `models.providers[*].models[*].maxTokens ≥ contextWindow/2 && > maxModelMaxTokens`(default 32000)
  - 检查到问题：`api.logger.warn` + `notifyQueue.emit(level=warn, source="config-doctor", ...)` 推仪表盘
  - **完全只读，绝不修改用户配置**（红线 #1）
  - 修复命令是 python3 inline JSON 改写一行（红线 #4：不调 child_process / 红线 #5：不在插件里 exec 安装命令）
- **工具：`enhance_config_doctor`** — 无参数，按需重跑诊断（修完用来确认 ✅）
- **`types.ts: ConfigDoctorConfig`** + **`openclaw.plugin.json: configSchema.configDoctor`**
- **`NotificationSource`** 加 `"config-doctor"` 通道

### 设计决策

- **不让插件自动改配置** — 违反零侵入红线 + 用户失去掌控感。给可粘贴命令是平衡点
- **tier=1 minimal 也启用** — 这是关键防爆 context 诊断；minimal 用户更需要这个警告
- **fix 命令选 python3 而非 jq** — python3 macOS/Linux 默认装；jq 不一定有
- **maxModelMaxTokens 默认 32000** — 常用模型 maxTokens 8192-16384，32000 是合理保守阈值

### 不破坏

- 没改任何 openclaw 文件 / enhance SQLite schema 没动
- 新工具 schema 极简（0 参数），单轮 prompt 增加约 30 token
- 老配置无 `configDoctor` 段时默认 enabled=true（用户被动获益）

### 调研依据

- 用户反馈截图：`Context limit exceeded. ... reserveTokensFloor to 20000 or higher`
- 用户当前 `~/.openclaw/openclaw.json` 实测：缺 `agents.defaults.compaction` 段；MiniMax-M2.7 配置 wizard 默认 maxTokens=131072 太大
- 已修用户配置（备份在 `~/.openclaw/openclaw.json.bak.before-compaction-fix-*`）
- 详见 KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v573-config-doctor-postmortem.md`

---

## 5.7.2 — 2026-04-26（hardening：审计 + 4 类潜在 bug 修复 + 升 peerDep ^2026.4.22）

继 v5.7.1 hot-fix 之后，对全代码库做了一次彻底审计（详见 `docs/SELF_ITERATE.md` 第 4 节 fast-track 流程 + KB post-mortem），用 Explore agent 列了 15 项候选，挑了 4 项 ROI 最高的批量修复。**这是 v5.7.1 的延伸防御层 — 修的都是"现在还没炸但长期运行会炸"的渐进式退化 bug**。

### 修复

- **`src/modules/mode-gate.ts`** — `modeState` / `plannedActions` 两个进程内 Map 之前 keyed by `agentId::sessionId` 永不清理（plan→normal 只清 plannedActions 不清 modeState）。WeCom 多 agent 场景 24h 内可能累积数千 session 状态。
  - 加 `MAX_STATE_ENTRIES = 200` / `MAX_PLANNED_ENTRIES = 200`
  - 新增 `evictOldest()` helper：利用 Map 的 insertion-order 迭代特性，FIFO 淘汰最早 entry
  - 写入前 `if (map.has(key)) map.delete(key)` 让活跃 session 刷新到队尾，避免被误淘汰
- **`src/modules/session-recap.ts`** — 同上，`lastRecapAt` Map 加 `MAX_RECAP_ENTRIES = 500` cap
- **`src/utils/sqlite-store.ts`** — `getDb()` 启动时跑一次 `DELETE FROM safety_log/notifications WHERE created_at < datetime('now', '-90 days')`，try-catch 包裹失败静默；新增 `purgeOldSafetyLogs(db, retentionDays = 90)` helper 给运维 / 工具调用
- **`src/modules/memory-integrator.ts`** — 新增 `TAG_BLACKLIST = {auto-compact, auto-checkpoint, audit, internal}`，`scoreRelevance()` 入口若 `isBlacklisted(memory.tags)` 直接 `return 0`。**这是 v5.7.1 修复的最终兜底**：即便未来某个 hook 又写入 noise，pruner 也不会召回到 prompt
- **`src/modules/structured-memory.ts`** — `enhance_memory_store` 工具检查 tags，若含保留词立即返回错误 `❌ 拒绝存储：tag "..." 是 enhance 保留的系统类标签` 而非写入。防止用户/agent 显式滥用保留 tag
- **`package.json`** — `peerDependencies.openclaw` 从 `>=2026.4.11` 升到 `^2026.4.22`；本地 node_modules openclaw 同步到 4.22；typecheck 通过；hook 名验证全部存在无破坏性变更

### 设计决策

- **为什么 cap 选 200 / 200 / 500**：mode-gate 状态比较"决策性"（200 个活跃 session 对单 agent 已经很多），session-recap 防抖表偏审计性（500 个 session 的 lastRecapAt 也只有 ~12KB 内存）。值故意保守以防误淘活跃数据
- **为什么 TTL 选 90 天而非 30**：safety_log 是审计性数据，跨季度排查事故场景需要保留至少 1 季度。90 天是"季度复盘 + 一周缓冲"
- **为什么 corpus 黑名单做兜底而非依赖 v5.7.1 的删 hook**：删 hook 只解决了已知一个 noise 来源，未来若有新模块又自动写入 audit/internal tag，黑名单这一层能保证 prompt 不被污染。**深度防御**

### 不破坏

- 所有现有 SQLite schema 没改（v5 schema 兼容）；老用户升级无需迁移
- 所有工具名 / API 没改；老脚本兼容
- LRU cap 只影响进程内 Map，重启后恢复，**不影响任何持久化数据**
- 升 peerDep 后老用户仍跑 4.11 的话仍可用（`as any` 屏蔽类型差异，hook 名都还在）

### 调研依据

- 用 Explore agent 跑了一遍审计（详见 KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v572-hardening-postmortem.md`），输出 15 项候选 bug 清单 + ROI top 3
- 升级 openclaw 4.22 后看 `dist/plugin-sdk/*.d.ts` 确认 hook 名和 ctx 字段无破坏性变更

---

## 5.7.1 — 2026-04-26（hot-fix：删除 before_compaction 噪音 hook + 新增 memory_purge 工具）

**线上 bug 修复**：v5.5.x 引入的 `before_compaction` hook 会在每次 openclaw auto-compact 时把"已压缩"事件作为 `decision` 类、`auto-compact` tag 写入 SQLite — 单条信息量为 0，但因为 tag/content 含 `auto / compact / enhance_memory_search` 等通用词，相关度普遍 0.43-0.51，过 corpus pruner 默认 0.5 阈值。**用户实测库里 613 条全是这种噪音**，把真正的 user/project/feedback 决策完全挤出了 prompt 上下文。

### 删除

- **`src/modules/structured-memory.ts`** — 移除 `api.on("before_compaction", ...)` 那段 hook（22 行）。从此 enhance 不再因为 compact 事件本身写入任何记忆。如果用户真要审计「啥时候 compact 过」，应当走 openclaw 自己的 session 日志，不该污染 enhance 结构化记忆库。

### 新增

- **`src/utils/sqlite-store.ts: purgeMemories()`** — 按 `agentId + tag/category/contentLike` 批量删除 + 可选 dry-run。`tag`/`contentLike` 用 SQL `LIKE %?%` 子串匹配。
- **工具：`enhance_memory_purge`** — 暴露给 agent。`tag` / `category` / `contentLike` 至少传一个；`dry_run` 默认 true（仅返回匹配数，不删除）。一键清理本 bug 历史残留：
  ```
  enhance_memory_purge tag="auto-compact" dry_run=false
  ```

### 用户侧手工清理（如果还没升级）

```bash
sqlite3 ~/.openclaw/memory/enhance-memory.sqlite \
  "DELETE FROM memories WHERE tags LIKE '%auto-compact%'; VACUUM;"
```

### 经验沉淀

- **不要在 `before_compaction` / `before_agent_reply` / `after_tool_call` 这类高频 hook 里无脑写记忆**。本来想做"留时间戳方便回查"的好心，结果变成 noise factory
- **写记忆前过 importance + tag 黑名单**：以后 enhance 自动写入的记忆必须在 corpus supplement 检索阶段再过一遍黑名单（计划 v5.8 实施）
- **审计能力 ≠ 决策记忆**：审计性事件（compact / mode 切换 / hook 触发统计）应该单独写到 audit log 文件或独立表，不能跟 user/project/feedback/reference/decision 这五类决策性记忆混存

### 调研依据

参见本仓库 [`docs/SELF_ITERATE.md`](./docs/SELF_ITERATE.md) v5.7.1 条目，本地 KB `~/knowledge/huo15/2026-04-26-openclaw-enhance-v571-memory-noise-bug-postmortem.md`。

---

## 5.7.0 — 2026-04-25（transcript-search：照搬 Claude Desktop 算法）

延续 v5.5.1 路线图里的 v5.7 候选「⭐ transcript search 会话搜索」。**反编译参考**了 `/Applications/Claude.app/Contents/Resources/app.asar` 里的 `transcript-search-worker/transcriptSearchWorker.js`（94 行官方实现），发现 Claude Desktop **不用 SQL FTS5**，是流式扫 JSONL + `indexOf` 的极简方案。直接照搬到 openclaw 的 session 目录，省下了 v5.5.1 路线图里"建 session_messages 新表 + FTS"的工作量。

### 新增

- **`src/modules/transcript-search.ts`** — 流式扫 `~/.openclaw/agents/<agentId>/sessions/*.jsonl`：
  - `extractText`：兼容 `string` / `[{type:"text", text}]` 数组 / 单 block 对象三种 content 形态（与 Anthropic 标准对齐）
  - `makeSnippet`：±80 字符 radius，开头/结尾用 `…` 表示截断
  - `listSessionFiles`：mtime 倒序，跳过 `.deleted.` / `.checkpoint.` / `.trajectory.`，可选包含 `.reset.`（默认不包含）
  - `scanFile`：单文件 first-match 策略 — 每个 session 只贡献一条 hit（与 Claude Desktop 一致），保证 limit=10 是"找 10 个不同 session"
  - 实测：79 个 session 中扫 30 个 → **3-5 ms** 找到 5 hits
- **工具：`enhance_transcript_search`** — `query` 必填，可选 `agentId / limit (1-50) / includeReset / caseSensitive`
- **`types.ts: TranscriptSearchConfig`** — 新配置段 `config.transcriptSearch.enabled`
- **`openclaw.plugin.json`** — `configSchema.transcriptSearch` 暴露给龙虾配置 UI
- **`index.ts`** — 模块清单加「历史会话搜索」，**tier=2**（balanced 默认就启用，minimal 下不暴露）

### 设计原则

- **零侵入**：完全只读 openclaw session 目录，不建表、不建索引、不写任何文件
- **零依赖**：用 `node:fs` + `node:readline` + `node:path`，没引新包
- **零侵犯隐私**：搜索范围严格限制在当前 ctx.agentId（除非显式传 agentId 参数）

### 设计决策：为什么不用 SQL FTS5

参照 Claude Desktop 反编译实现：

| 维度 | SQL FTS5 | 流式扫 JSONL（照搬） |
|------|---------|---------------------|
| 实现复杂度 | 高（建表 + 触发器同步 + 索引重建） | 低（一个 worker，~200 行） |
| 写入开销 | 每次消息要 INSERT FTS | 0 |
| 跟 openclaw 同步 | 容易 drift（agent reset / 删除时索引脏） | 永远是源数据 |
| 性能 | 查询 ms 级，但需要持续维护 | 3-5 ms（79 个 session 扫 30 个）— **同 SLA** |
| 故障域 | 索引坏了影响搜索 | 单文件坏了不影响其它 session |

结论：在 session 数量级 ≤ 100 的场景下，FTS5 没有任何价值。Claude Desktop 用了几年都没建 FTS，我们也不建。

### 不破坏的兼容点

- 不改任何 openclaw 文件、不动 enhance 自己的 SQLite 库
- 工具 schema 极简（5 个参数），不增加 prompt 负担
- minimal toolTier 用户不会看到这个工具

---

## 5.6.0 — 2026-04-24（工具分层 + workflow 5→2 合并 + 描述压缩）

针对实际使用中"long session 仅 15% 上下文使用率即触发 Context limit exceeded"的现象做容量优化。根因有二：(a) 用户的 `~/.openclaw/openclaw.json` 把 `compaction.reserveTokensFloor` 误设为 `200000`（>205k 总窗），每次压缩都失败 — 需要用户侧改回 `20000`；(b) 插件这边一次性暴露 29 个工具 schema，每轮 prompt 固定底座过重。本版本聚焦 (b)。

### 新增

- **`types.ts: ToolTier` 类型 + `EnhancePluginConfig.toolTier`** — 新增工具分层枚举 `"minimal" | "balanced" | "full"`，默认 `"balanced"`。
- **`openclaw.plugin.json: configSchema.toolTier`** — 暴露给龙虾配置 UI，三档可选。

### 变更

- **`index.ts`** — 模块清单增加 `tier: 1 | 2 | 3` 字段；启动期按 `TIER_MAX[toolTier]` 过滤，超出层级的工具模块整个不 register（连 schema 都不进 prompt）。
  - tier 1 常驻层（minimal 即可见，10 工具）：结构化记忆 / 状态栏 / spawn / 模式闸门 / 章节标记 / installer / integrator
  - tier 2 均衡层（balanced 默认，+8 工具，共 18）：todo / 章节 / 定时任务桥
  - tier 3 完整层（full，+8 工具，共 26）：workflow / safety / task-planner / session-recap / skill-doctor
  - 非工具模块（仪表盘、通知、自检、prompt-enhancer、kb-corpus）一律 tier 1：它们不占 tool schema、不影响 per-turn 成本。
- **`workflow-hooks.ts` 5→2 工具合并** — `enhance_workflow_define / _list / _delete` 三个独立工具合并为单一 `enhance_workflow`（`action=define/list/delete/tasks`）；`enhance_task` 保留独立但仍是 action 派发器。`before_prompt_build` 触发逻辑、所有工作流持久化和评估辅助函数全部保留。
- **批量描述压缩** — 24 个工具的 description 字段从多行 `[...].join("\n")` 压成单行 ≤ 80 字符；总字符量 ~4610 → ~1750（-62%），按中文 ≈0.5 token/字 估算每轮 prompt 节省约 1400 token。压缩注重保留触发关键词，不改 parameters schema。
  - 最大幅压缩：`enhance_memory_store`（~700 字 → 38 字）、`enhance_exit_plan_mode`、`enhance_install_skills`
  - `enhance_todo_list` 已经 ≤ 80 字，未改

### 行为变化

- 默认 `balanced` 模式下 **不暴露** workflow / safety / task-planner / session-recap / skill-doctor 工具。如果你需要这些能力（特别是工作流自动化和 plan-mode-审批闭环），请在 `openclaw.json.plugins.enhance` 配置里加 `"toolTier": "full"` 并重启。
- session-recap 的 `before_prompt_build` hook 在 balanced 下**不**生效（模块整体没注册）；如果你依赖 75min idle 自动回顾，需 `toolTier: "full"`。
- 升级后总工具数 29 → 26（workflow 5→2），即使切回 full 也比 v5.5.1 少 3 个。

### 配置示例

```jsonc
// ~/.openclaw/openclaw.json
{
  "plugins": {
    "enhance": {
      "toolTier": "minimal"   // 极致省 schema，仅留 10 工具
      // "toolTier": "full"   // 全功能，26 工具
    }
  },
  "compaction": {
    "reserveTokensFloor": 20000   // ⚠️ 不要设 200000，会比总窗还大
  }
}
```

### 不破坏的兼容点

- 所有工具名（`enhance_*`）都保留，旧的 `enhance_workflow_define` 等命名外部没用过（只在内部 register），改成 `enhance_workflow` 不破坏任何用户脚本。
- SQLite schema 完全没动；现有记忆 / 任务 / 章节数据无需迁移。
- npm 包对外 API 没变（`definePluginEntry` 出口不变）。

### 修复（顺手）

- **session-recap.ts** — `buildRecapText` 引用了 `MemoryEntry` 上不存在的 `key` / `rule` 字段（v5.5.1 编译错但未被 CI 拦下），全 full tier 场景下生成 decision 段会运行时抛 `TypeError`。修正为 `d.content` 后兼容正确字段并裁切 80 字符。

### 调研依据

参见本仓库 [`docs/v5.6-context-pressure-postmortem.md`](./docs/v5.6-context-pressure-postmortem.md)（如该文件存在），以及本地 KB 条目 `~/knowledge/huo15/2026-04-24-openclaw-context-pressure-postmortem.md`。

---

## 5.5.1 — 2026-04-24（session-recap + 3 个开发辅助 skill）

在 v5.5.0「三层记忆协调」基础上，对齐 Claude Code 2026 Q2 最新能力谱调研结果，补齐两块高频能力：**会话回顾**与**开发辅助三件套**。

### 新增（plugin 模块）

- **`src/modules/session-recap.ts`** — 对齐 Claude Code 75min idle auto-summary。当检测到当前 agent/session 距上次活动 > `recapIdleMinutes`（默认 75），在 `before_prompt_build` 自动 prependContext 一段"你上次到这儿"的回顾（最近章节 + in_progress/pending todo + 最近 decision 记忆）。
  - 工具 `enhance_session_recap` 支持手动触发（不受 idle 阈值限制）
  - 进程内防抖表避免重复 recap：两次间隔 < `recapMinIntervalMinutes`（默认 30）直接 skip
  - 非侵入：只读三张已有表（chapters / todos / memories），**不建新表、不改现有 schema**
  - 可通过 `config.sessionRecap.enabled = false` 关闭
- **`types.ts: SessionRecapConfigType`** — 新配置段 `config.sessionRecap`。

### 新增（3 个开发辅助 skill，通过 huo15-skills 分发）

对齐 Claude Code 原生 `/simplify` / `/security-review` / `/review` 三件套，全部自研、MIT：

- **`huo15-openclaw-simplify` v1.0.0** — 代码简化三维审查（复用 / 质量 / 效率）+ 分级修复清单 + 🔴必改/🟡建议/🟢可选。严格硬红线：不跨文件重命名、不改测试断言、不引入新依赖、不跑格式化器、不碰 generated 代码。
- **`huo15-openclaw-security-review` v1.0.0** — 六类漏洞矩阵（密钥 / 注入 / XSS / SSRF / 权限 / 危险依赖）+ CVSS-like 四档严重度（🔴Critical / 🟠High / 🟡Medium / 🟢Low）+ CWE 编号对照。硬红线：不 exec `npm audit`、不改历史、不明文打印密钥。
- **`huo15-openclaw-code-review` v1.0.0** — PR 五维综合评审（设计 / 实现 / 测试 / 安全 / 可维护）+ 可粘贴 markdown 评论。`gh` CLI 命令走 return-cliCmd 模式（禁 child_process 铁律）。硬红线：不 `gh pr review --approve`、不 `gh pr merge`、不自动 `gh pr comment`。

### 变更（enhance 插件内）

- **`skill-installer.ts`**：`CLAW_HUB_SKILLS` 从 8 扩到 **11**（+simplify / security-review / code-review）。
- **`skill-doctor.ts`**：`EXPECTED_SKILLS` 同步到 11；tool description 从"8 个"改"11 个"。
- **`index.ts`**：新增「会话回顾」模块条目，默认启用。

### 设计决策：为什么 session-recap 是 Plugin 而非 Skill

参照 [MEMORY.md Plugin vs Skill Decision](../../../.claude/projects/-Users-jobzhao/memory/plugin_vs_skill_decision.md)：
- 需要 `before_prompt_build` hook → Skill 做不了
- 需要跨进程状态（lastRecapAt 防抖表 + SQLite 只读查询）→ Skill 做不了
- 触发条件是"idle 时长"的系统级信号，不是用户语义意图 → Plugin 更合适

反之，3 个开发辅助能力是"用户说'帮我 review'时自动加载最佳实践"的语义触发场景，天然 Skill。

### 调研依据

[2026-04-24 Claude Code 能力全景调研（115 条）](../../../knowledge/huo15/2026-04-24-claude-code-capability-survey-and-enhance-roadmap.md)：enhance v5.4 已覆盖 TodoWrite/mark_chapter/plan-mode/ExitPlanMode/statusline 等核心 harness；本版本补齐 session-recap；后续 v5.6/5.7 规划补 hook-observer / path-rules / transcript search。

---

## 5.5.0 — 2026-04-23（三层记忆/知识库协调）

本次聚焦「龙虾原生 memory / enhance 结构化记忆 / KB wiki」三者的职责切分和聚合搜索。

### 新增

- **`src/modules/kb-corpus.ts`** — 新增 corpus supplement，把 huo15-openclaw-openai-knowledge-base 技能的**共享知识库**（`~/.openclaw/kb/shared/wiki/`）注册为龙虾 `memory` 的 `corpus="kb"`。调用 `memory_search` 会同时搜到 enhance-memory + shared KB wiki，无需切换工具。
- **`types.ts: KbCorpusConfigType`** — 新配置段 `config.kbCorpus`，可调阈值、路径、debug。
- **`index.ts`** — 注册「共享知识库语料」模块，默认启用（`kbCorpus.enabled !== false`）。

### 变更

- **`structured-memory.ts: enhance_memory_store` 的 tool description** — 增加 L2/L3 边界提示：「本工具只存规则/为什么/怎么做的短条目；长文档请走 `kb-ingest` 入共享 KB」。

### 三层协调总览

| 层 | 存什么 | 存储 | 隔离 | corpus |
|----|--------|------|------|--------|
| L1 龙虾原生 memory | 向量+FTS 底座 | `~/.openclaw/memory/<agent>.sqlite` | per-agent | `memory` |
| L2 enhance 结构化记忆 | 规则/反馈/决策（短） | `enhance-memory.sqlite` | per-agent | `enhance` |
| L3 共享知识库 | 事实/文档/教程（长） | `~/.openclaw/kb/shared/wiki/*.md` | 跨 agent | `kb` |

### 配套更新

- `huo15-openclaw-openai-knowledge-base` skill v2.5.0 — 所有 `kb-*` 脚本新增 `--scope agent|shared`；`kb-search` 默认聚合搜 agent+shared+obsidian；新增 `kb-scope.sh` 公共库。

---

## 5.4.0 — 2026-04-23（对齐 2026 Q2 设计能力生态）

本次聚焦"设计能力"这一纵向领域，对标 Anthropic 官方 `frontend-design` skill（277k+ 安装）与中文圈 `alchaincyf/huashu-design`（画术，4.6k★）的设计理念，但**全部内容自研**（避开 huashu 仅限个人使用的 license 限制）。

### 新增（4 个设计能力 skill）

通过 [huo15-skills monorepo](https://cnb.cool/huo15/ai/huo15-skills) 分发，首次安装会自动从 clawhub 拉取：

- **`huo15-openclaw-frontend-design` v1.0.0** — 高保真 Web UI 原型生成。5 大美学流派（BOLD-MINIMAL / EDITORIAL / BRUTALIST / RETRO-FUTURE / ORGANIC）+ 8 条反 AI Slop 硬红线（禁 Inter/Roboto、禁紫渐变、禁 emoji 当图标等）+ Junior/Full 两趟渲染工作流 + Playwright 自验证 CLI（延续"禁 child_process"铁律）。对标 Anthropic frontend-design。
- **`huo15-openclaw-design-director` v1.0.0** — 设计方向顾问。内置 20 条设计哲学库（极简/编辑/前卫/东方/功能 5 派）+ 3 方向反差生成规则（1 保守 + 1 反差 + 1 中间）+ 五维对比矩阵 + 强制推荐表态。
- **`huo15-openclaw-brand-protocol` v1.0.0** — 品牌规范抓取。5 步硬流程 Ask / Search / Download / Verify+Extract / Codify，产出结构化 `brand-spec.md`。返回 curl / Playwright CLI 命令让用户执行，**不调 child_process**。
- **`huo15-openclaw-design-critique` v1.0.0** — 5 维设计评审（美学/可用性/品牌一致/内容/实现）+ Keep/Fix/Quick Wins 三分类 + ASCII 雷达图。木桶短板决定总分，命中硬红线美学直接 ≤ 2。

### 变更（enhance 插件内）

- **`skill-installer.ts`**：`CLAW_HUB_SKILLS` 列表从 4 扩展到 8，加入 4 个设计 skill。
- **`skill-doctor.ts`**：`EXPECTED_SKILLS` 同步到 8；tool description 更新。
- **README.md / SKILL.md**：技能清单分为「工作流模式」和「设计能力」两段，加入新增 4 个 skill 的说明。

### 设计决策（为什么做成 Skill 而非 Plugin 模块）

遵循 [MEMORY.md Plugin vs Skill Decision](../../../.claude/projects/-Users-jobzhao/memory/plugin_vs_skill_decision.md) 框架：设计能力是"当用户做 X 时自动应用最佳实践"的**语义触发场景**，不需要 hook / 新 tool / 跨进程状态，因此 Skill-first。Plugin 仅扩展了 `CLAW_HUB_SKILLS` 列表做发现和巡检。

### 与 OpenClaw 原生 / 其他 huo15 技能的边界

| 能力 | 归属 |
|------|------|
| Web UI / HTML 原型 | `huo15-openclaw-frontend-design`（新） |
| 设计方向选型 | `huo15-openclaw-design-director`（新） |
| 品牌规范抓取 | `huo15-openclaw-brand-protocol`（新） |
| 设计评审打分 | `huo15-openclaw-design-critique`（新） |
| PPT 演示稿 | `huo15-openclaw-ppt`（已有） |
| Word / PDF | `huo15-openclaw-office-doc`（已有） |

### 商用合规

本批 4 个 skill 内容**全部自研**，仅参考 Anthropic frontend-design（Anthropic 自有 license）和 huashu-design（仅限个人使用）的**结构设计与设计理念**，不 vendor 其 markdown 文本。@huo15/* 系列所有发布物为商用合规，License 保持 MIT。

---

## 5.2.0 — 2026-04-22（对齐 OpenClaw 2026.4.11）

本次是一次**方向性重写**：把之前"跟着龙虾跑"的模式彻底倒转为"给龙虾打补丁"。核心原则——**凡是龙虾有的，我们绝不复制；凡是龙虾没的 Claude-Code 体验，我们填平**。

### 破坏性变更

- **记忆整合从 prompt-inject 改为 corpus supplement**：
  - 旧版本 `context-pruner` 模块通过 `before_prompt_build` 把打分后的记忆直接 `prependContext`，**与龙虾原生 memory injection 重复/竞争**。
  - 新版本删除 `context-pruner`，在 `memory-integrator` 中改用 `api.registerMemoryCorpusSupplement(...)`（2026.4.11 新增 API），把 enhance 分类记忆作为**并列 corpus** 交给龙虾排序——龙虾是主，插件是补。
- **tool-safety 降级为观察员**：
  - 旧版本尝试"重试"（在 `after_tool_call` 中"retry"并不会真的重新调用工具，是假动作）。
  - 新版本只做错误分类 + 指数退避建议 + 60s TTL 观察窗，**完全不与龙虾原生 `tools.allow/deny` 竞争**。每个工具描述都声明"若与龙虾配置冲突以龙虾为准"。
- `package.json` peerDep：`openclaw >= 2026.4.11`；旧版本不再支持。
- `openclaw.plugin.json` 升至 v2.2.0，重写了 configSchema（新增 7 个模块的开关）。

### 新增（对齐 Claude Code Agent Harness）

- **`enhance_todo_write` / `enhance_todo_update` / `enhance_todo_list`**：对齐 Claude Code `TodoWrite`；SQLite `todos` 表 + 会话隔离；出现多个 `in_progress` 自动发通知警告。
- **`enhance_mark_chapter` / `enhance_chapter_list`**：对齐 Claude Code `mark_chapter`，为 session 打时间线。
- **`enhance_set_mode` / `enhance_current_mode`**：plan / explore / normal 三模式；前两者下 `before_tool_call`（priority=950）阻止 Write/Edit/NotebookEdit + 破坏性 Bash（`rm`、`mv`、`curl -X POST` 等），直到模式切回 normal 或 `exec()` 显式批准。
- **`enhance_statusline`**：line/detail/json 三格式状态快照；HTTP 路由交给 dashboard 统一托管。
- **`enhance_skill_doctor`**：只读巡检 4 个 huo15-\*-mode 技能；缺失时给出 `clawhub install` 命令，**不擅自安装**。
- **`enhance_spawn_task`**：孵化子任务；由于龙虾无 spawn 原语，**只记录不伪装执行**，存为 `category=project, tag=spawn-task` 记忆条目。
- **`enhance_loop_register` / `enhance_loop_list` / `enhance_loop_disable`**：登记定时工作流并返回**一条 `openclaw cron add` CLI 命令**，调度生命周期归龙虾 `cron-cli` 管理；触发时 `before_prompt_build` 识别 `[enhance-loop:{name}]` 前缀并注入 instructions。

### 仪表盘增强

- `/plugins/enhance/api/statusline` — 供 Control UI / 外部嵌入
- `/plugins/enhance/api/todos` — 最近 session 的 todo 快照
- `/plugins/enhance/api/chapters` — 章节时间线
- `/plugins/enhance/api/loops` — 定时工作流登记
- `/plugins/enhance/api/spawn-tasks` — 已孵化子任务
- UI 新增 4 个面板（Todos / Chapters / Loops / Spawn Tasks），切 agent 时全量刷新

### 修复

- 修复 `tool-safety.ts` 中因 `)),` 误写导致的多 tool 注册被串成逗号表达式的 bug。
- 修复 `memory-integrator.ts` 的 `registerMemoryCorpusSupplement` 签名误用（2026.4.11 SDK 公共面是单参，内部全局是双参，之前混了）。
- 移除 `statusline.ts` 内对不存在的 `api.http.registerRoute` 的调用。

### 迁移指引（从 v1.x 升级）

1. 在你的 `openclaw.json` 里把 `plugins.entries.enhance.version` 升到 `^5.2`。
2. 若你之前依赖 `contextPruner.*` 配置段，**现在可以删除**；打分逻辑已并入 corpus supplement（配置项改名为 `memory.relevanceThreshold` / `memory.maxContextEntries`）。
3. 若你期望 enhance 实现自动重试，请**改用龙虾原生的 `tools.retry.*` 配置**；enhance 只给观察数据。
4. Cron 工作流：旧版 `workflows` 触发词仍可用；若要真正定时触发，改用 `enhance_loop_register`，按返回的命令手动跑 `openclaw cron add`。

---

## 5.1.2 — 历史版本

见 git 历史。
