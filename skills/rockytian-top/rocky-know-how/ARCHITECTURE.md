# 🏗️ rocky-know-how 完整架构设计 (v3.4.8)

> 技能插件的所有流程架构、组件关系、数据流、部署拓扑总览

---

## 📐 架构原则

1. **松耦合** — Hook 仅触发，不阻塞主流程
2. **分层存储** — HOT (memory) / WARM (domains) / COLD (archive)
3. **安全第一** — 并发锁、路径检测、正则转义
4. **可观测** — 日志、统计、心跳全覆盖
5. **向后兼容** — 支持 OpenClaw 2026.4.x+，Hook 事件动态检测

---

## 🎯 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenClaw Gateway                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Session Manager                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │   Agent A   │  │   Agent B   │  │   Agent C   │         │  │
│  │  │ (大杰)      │  │ (大梅)      │  │ (大青)      │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            │                                          │
│  ┌─────────────────────────┴──────────────────────────────────────┐ │
│  │               Plugin System (Hook Engine)                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  rocky-know-how Handler (~/.openclaw/skills/.../hooks/  │ │ │
│  │  │           handler.js - 4事件处理)                        │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Shared Data Directory (~/.openclaw/.learnings/)    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  📁 experiences.md       ← 主经验库（所有正式条目）              ││
│  │  📁 memory.md            ← HOT层（最近7天，≤100行）              ││
│  │  📁 domains/             ← WARM层（领域隔离）                    ││
│  │  │   infra.md            ← 运维领域                              ││
│  │  │   wx.newstt.md        ← 公众号领域                            ││
│  │  │   code.md             ← 开发领域                              ││
│  │  │   ...                 ← 其他领域                              ││
│  │  ├── projects/           ← 项目隔离（可选）                      ││
│  │  ├── drafts/             ← 草稿（pending_review）                ││
│  │  │   ├── draft-xxx.json  ← 自动生成的草稿                       ││
│  │  │   └── archive/        ← 超期草稿归档                         ││
│  │  ├── index.md            ← 存储索引（HOT/WARM/COLD 列表）       ││
│  │  └── .summarize.log      ← summarize-drafts.sh 输出            ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Skill Scripts (~/.openclaw/skills/)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │search.sh │ │record.sh │ │promote.sh│ │compact.sh│ │import.sh ││
│  │🔍 搜索   │ │✍️ 写入   │ │🚀 晋升   │ │🗜️ 压缩   │ │📥 导入   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │archive.sh│ │clean.sh  │ │stats.sh  │ │vectors.sh│ │lib/      ││
│  │📦 归档   │ │🧹 清理   │ │📊 统计   │ │🔧 向量   │ │公共函数  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  hooks/                                                         ││
│  │  └── openclaw/                                                  ││
│  │       ├── HOOK.md          ← Hook 说明文档                       ││
│  │       └── handler.js       ← Hook 处理器（4事件）                ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 组件清单

### 1. Hook Handler (`hooks/handler.js`)

**职责**：响应 OpenClaw 4个 Hook 事件，生成草稿、保存状态、记录摘要。

**事件处理**：

| 事件 | 触发时机 | Handler 动作 | 输出 |
|------|----------|--------------|------|
| `agent:bootstrap` | Agent 启动 | 注入经验提醒 + 检查草稿（仅提醒） | 虚拟文件（会话上下文） |
| `before_compaction` | 压缩前 | 保存会话状态 → `.compaction-state.tmp` | 临时文件 |
| `after_compaction` | 压缩后 | 生成会话总结 → `session-summaries.md` | 附加文件 |
| `before_reset` | 重置前（会话结束） | **提取会话信息** → 生成草稿 JSON | `drafts/draft-{sessionKey}.json` |

**核心逻辑**（handler.js L147-165）：
```javascript
if (event.type === 'before_reset') {
  const messages = event.messages || event.context?.messages || [];
  const task = extractTask(messages);      // 提取用户任务
  const tools = extractTools(messages);    // 提取工具列表
  const errors = extractErrors(messages);  // 提取错误信息

  if (task && errors.length > 0) {  // 有任务 + 有错误（表示解决过程）
    saveCompactionState(sessionKey, env, { task, tools, errors });
    // → 生成草稿文件
  }
}
```

**关键特性**：
- ✅ 跨 workspace 自动推导路径（`OPENCLAW_STATE_DIR` / `OPENCLAW_WORKSPACE`）
- ✅ 子 agent 跳过（避免重复注入）
- ✅ 虚拟文件（不污染工作区）
- ✅ 错误容错（JSON 解析失败 → 跳过）

---

### 2. 脚本库 (`scripts/`)

| 脚本 | 职责 | 输入 | 输出 | 锁 |
|------|------|------|------|-----|
| `search.sh` | 搜索经验（关键词/向量） | 关键词、标签、领域 | 搜索结果（Markdown 表格） | ❌ |
| `record.sh` | 写入正式经验 | 问题/过程/方案/预防/tags/area | `experiences.md` + `memory.md` + `domains/` | ✅ `.write_lock` |
| `promote.sh` | Tag 晋升检查 | 扫描所有经验 | `TOOLS.md`（如果≥3次） | ✅ |
| `compact.sh` | 压缩 experiences.md | 去重、合并相似条目 | 压缩后的 `experiences.md` | ✅ |
| `archive.sh` | 归档旧数据 | 日期/标签过滤 | `archive/YYYY-MM/` | ✅ |
| `clean.sh` | 清理测试/垃圾数据 | 标签、日期范围 | 删除对应条目 | ✅ |
| `import.sh` | 从 memory 导入历史教训 | 正则匹配 | 追加到 `experiences.md` | ✅ |
| `stats.sh` | 统计报表 | 无 | 总条数、Tag 分布、领域分布 | ❌ |
| `summarize-drafts.sh` | 批量审核草稿 | 扫描 `drafts/` | `.summarize.log`（建议命令） | ❌ |
| `vectors.sh` | 向量索引管理 | `--rebuild`、`--update` | `vectors/` 目录 | ✅ |

**公共库** (`scripts/lib/`):
- `common.sh` - 路径、锁、日志、错误处理
- `vectors.sh` - 向量搜索引擎（LM Studio 集成）
- `domains.sh` - 领域推断逻辑
- `tags.sh` - 标签归一化

---

### 3. 数据存储 (`~/.openclaw/.learnings/`)

```
.learnings/                    # 根目录（所有 agent 共享）
├── experiences.md             # 主数据库（Markdown 表格）
│   ## [EXP-20260424-0121]
│   ### 问题
│   ### 踩坑过程
│   ### 正确方案
│   ### 预防
│   **Tags:** tag1,tag2
│   **Area:** infra
│
├── memory.md                  # HOT 层（最近7天，≤100行）
│   ## 2026-04-24
│   - Tag: nginx (使用3次) → 晋升 TOOLS.md
│   - 问题: Nginx 502 修复
│
├── domains/                   # WARM 层（领域隔离）
│   ├── infra.md              # 运维领域（nginx, docker, redis...）
│   ├── wx.newstt.md          # 公众号领域（ocr, wechat...）
│   ├── code.md               # 开发领域（php, mysql...）
│   └── ...                   # 其他领域
│
├── projects/                  # COLD 层（项目隔离，可选）
│   ├── current-app.md
│   └── side-project.md
│
├── drafts/                    # 草稿（待审核）
│   ├── draft-1776958084440-qad5k6.json
│   └── archive/              # 超期草稿归档（30天）
│
├── vectors/                   # 向量索引（LM Studio 可用时）
│   ├── index.faiss           # FAISS 索引文件
│   └── metadata.json         # ID → 内容映射
│
├── session-summaries.md       # after_compaction 生成的会话总结
├── .compaction-state.tmp      # before_compaction 保存的临时状态
├── .summarize.log            # summarize-drafts.sh 输出建议
├── .write_lock               # 并发写锁目录（防止多进程冲突）
├── index.md                  # 存储索引（HOT/WARM/COLD 列表）
└── heartbeat-state.md        # 心跳状态记录
```

---

## 🔄 完整数据流

### 场景：用户遇到 Nginx 502 错误

```
1. 用户对话开始
   User: "Nginx 502 怎么修复？"
   ↓
   Agent (大杰) 尝试解决
   ↓
2. 失败 2 次（自动搜索）
   ├─ 第1次: 改配置 → 失败
   ├─ 第2次: 重启 php-fpm → 失败
   ↓
   触发 search.sh "502 nginx"
   ↓
   找到经验: EXP-20260420-001 "Nginx 502: restart php-fpm"
   ↓
3. 按方案执行成功
   Agent: "已修复，重启 php-fpm 并调整 pm.max_children"
   ↓
4. 会话结束（before_reset Hook 触发）
   ↓
   handler.js 分析 messages:
   ├─ task: "修复 Nginx 502"
   ├─ tools: ["search.sh", "edit", "exec"]
   └─ errors: ["502 Bad Gateway", "php-fpm 连接超时"]
   ↓
   生成草稿: drafts/draft-agent:dajie-xxx.json
   状态: "pending_review"
   ↓
5. [人工审核阶段]
   ├─ 方式1: 批量审核
   │  $ summarize-drafts.sh
   │  → 输出建议: "值得记录: 是 | record.sh 'Nginx 502'..."
   │  $ 复制并执行 record.sh 命令
   │
   └─ 方式2: 直接查看草稿
      $ cat drafts/draft-*.json
      $ record.sh "Nginx 502" "php-fpm 连接超时" "restart + 调 pm.max_children" "..."
   ↓
6. record.sh 执行（持有 .write_lock）
   ├─ 去重检查（70% 重叠拦截）
   ├─ 生成 ID: EXP-20260424-0121
   ├─ 写入 experiences.md
   ├─ 同步 memory.md（HOT 层）
   ├─ 同步 domains/infra.md（WARM 层）
   └─ 释放锁
   ↓
7. Tag 统计 & 晋升
   ├─ Tag "nginx" 累计出现 3 次
   ├─ 触发 promote.sh
   └─ 写入 TOOLS.md（"Nginx 502 修复：restart php-fpm + 调参数"）
   ↓
8. 后续搜索
   $ search.sh "502 nginx"
   → 找到这条经验 ✅
```

---

## 🔌 Hook 事件时序图

```
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw Session Lifecycle                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐                                            │
│  │ Agent 启动     │                                            │
│  └───────┬───────┘                                            │
│          │                                                     │
│          ▼                                                     │
│  ┌─────────────────────────────┐                              │
│  │ agent:bootstrap Hook        │                              │
│  │ - 注入经验提醒到上下文        │                              │
│  │ - 检查未审核草稿（仅提醒）    │                              │
│  └─────────────┬───────────────┘                              │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────────┐                              │
│  │  正常对话 + 工具调用         │                              │
│  │  (用户问题 → Agent 尝试)     │                              │
│  └─────────────┬───────────────┘                              │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────────┐                              │
│  │ before_compaction Hook      │                              │
│  │ - 保存会话状态               │                              │
│  │    (.compaction-state.tmp)  │                              │
│  │ - 用于后续分析               │                              │
│  └─────────────┬───────────────┘                              │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────────┐                              │
│  │  after_compaction Hook      │                              │
│  │ - 生成会话总结              │                              │
│  │    (session-summaries.md)   │                              │
│  └─────────────┬───────────────┘                              │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────────┐                              │
│  │   before_reset Hook         │                              │
│  │   (会话压缩/重置前)          │                              │
│  │   - 提取 task/tools/errors  │                              │
│  │   - 生成草稿 JSON            │                              │
│  │     (drafts/draft-*.json)   │                              │
│  │   - 状态: pending_review    │                              │
│  └─────────────┬───────────────┘                              │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────────┐                              │
│  │   会话结束 / 压缩完成        │                              │
│  └─────────────────────────────┘                              │
│                                                                 │
│  [下一会话启动]                                                 │
│  ┌───────────────┐                                            │
│  │ agent:bootstrap │                                           │
│  │ (再次触发)     │                                            │
│  └───────┬───────┘                                            │
│          │                                                     │
│          ▼                                                     │
│  ┌─────────────────────────────┐                              │
│  │  检查草稿（仅提醒）          │                              │
│  │  "有 N 个草稿待审核"         │                              │
│  └─────────────────────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**关键时序**：
1. `before_reset` 是**最后一个 Hook**，会话结束时触发
2. 草稿生成后，**不会自动写入** `experiences.md`
3. 下次 `bootstrap` 只**提醒**有草稿，不自动判断或写入
4. 审核必须**人工干预**（执行 `record.sh`）

---

## 🗃️ 存储分层策略

### HOT 层 (`memory.md`)

- **内容**：最近 7 天的关键教训（≤100 行）
- **更新时机**：`record.sh` 同步写入 + `compact.sh` 截断
- **用途**：快速记忆，`memory_search` 直接搜索
- **压缩规则**：行数 >100 → 保留最近 7 天 → 截断旧条目

示例：
```markdown
## 2026-04-24
- Tag: nginx (使用3次) → 晋升 TOOLS.md
- 问题: Nginx 502 修复（重启 php-fpm + 调 pm.max_children）
- 来源: EXP-20260424-0121
```

### WARM 层 (`domains/{area}.md`)

- **内容**：按领域分类的经验（infra、wx.newstt、code...）
- **更新时机**：`record.sh` 根据 `area` 字段写入对应文件
- **用途**：领域隔离，`search.sh --area` 快速过滤
- **结构**：每个领域独立文件，便于管理和查看

示例（`domains/infra.md`）：
```markdown
# Infra Domain Learnings

## [EXP-20260424-0121] Nginx 502 修复

**问题**: Nginx 502 Bad Gateway
**方案**: restart php-fpm + 调整 pm.max_children
**Tags**: nginx,php-fpm,502
```

### COLD 层 (`archive/` + `experiences.md` 历史）

- **内容**：超过 30 天的旧经验 + 压缩后的合并条目
- **更新时机**：`archive.sh` 每月归档 + `compact.sh` 合并相似条目
- **用途**：长期存储，不占用 HOT/WARM 内存
- **访问**：需手动查看 `archive/YYYY-MM/` 目录

---

## 🔐 安全机制

### 并发控制

| 机制 | 用途 | 实现 |
|------|------|------|
| `.write_lock` 目录锁 | 防止多进程同时写入 `experiences.md` | `mkdir .write_lock` 原子操作 |
| 锁等待超时 | 避免死锁 | 5 秒等待，失败则跳过 |
| 锁释放 | 写入完成后删除锁目录 | `rm -rf .write_lock` |

**record.sh 锁逻辑**：
```bash
if mkdir "$LEARNINGS_DIR/.write_lock" 2>/dev/null; then
  # 获得锁，执行写入
  write_to_experiences
  rmdir "$LEARNINGS_DIR/.write_lock"
else
  echo "⚠️ 锁已被占用，跳过本次写入"
  exit 0
fi
```

### 输入验证

| 脚本 | 漏洞类型 | 修复方式 |
|------|----------|----------|
| `search.sh` | H1: 正则注入 | `FILTER_DOMAIN`/`FILTER_PROJECT` 双引号转义 |
| `import.sh` | H2: 路径穿越 | 检测 `../`，拒绝危险路径 |
| `search.sh` | M1: 反斜杠穿越 | `validate_name()` 增加 `\` 检测 |

### 数据保护

- ✅ **去重检查**：70% 标签重叠 → 拦截重复经验
- ✅ **草稿隔离**：`drafts/` 目录不参与搜索，需审核才入库
- ✅ **日志脱敏**：不记录敏感信息（密码、密钥）
- ✅ **权限控制**：`.learnings/` 目录 `700`（仅所有者可读写）

---

## 📊 运维监控

### 心跳检查 (`HEARTBEAT.md`)

**触发方式**：cron 或手动触发

**检查内容**：
1. `memory.md` 行数（>100 → 触发压缩）
2. `experiences.md` 重复率（>51 条 → 触发去重）
3. `drafts/` 草稿数（>10 个 → 提醒审核）
4. 各文件更新时间（超过 7 天未更新 → 警告）

**输出**：
- `heartbeat-state.md` - 状态记录
- 控制台消息 - 异常时上报

### 压缩策略 (`compact.sh`)

| 触发条件 | 动作 | 频率 |
|----------|------|------|
| `memory.md` >100 行 | 截断至 ≤100 行 | 自动（心跳） |
| `experiences.md` 重复条目 >51 | 去重合并 | 手动或 cron |
| 草稿超过 30 天 | 移至 `archive/` | 自动（cron） |

**压缩流程**：
1. 分析 `experiences.md`（去重、合并相似条目）
2. 保存当前会话状态（`before_compaction` Hook）
3. 压缩 `experiences.md`
4. 截断 `memory.md` 至 ≤100 行（Bug #4 修复）
5. 更新 `index.md`
6. 记录会话总结（`after_compaction` Hook）

---

## 🎯 扩展点

### 添加新 Hook 事件

1. 修改 `hooks/handler.js`：
```javascript
if (event.type === 'new_event') {
  // 你的逻辑
  return { handled: true };
}
```

2. 更新 `openclaw.json`：
```json
{
  "plugins": {
    "entries": {
      "rocky-know-how": {
        "events": ["agent:bootstrap", "before_compaction", "after_compaction", "before_reset", "new_event"]
      }
    }
  }
}
```

3. 重启网关：`openclaw gateway restart`

### 添加新脚本

1. 创建脚本文件：`scripts/my-script.sh`
2. 引用公共库：`source "$(dirname "$0")/lib/common.sh"`
3. 使用标准函数：`get_state_dir`、`log`、`error_exit`
4. 更新 `README.md` 和 `INDEX.md` 文档
5. （可选）添加到 `QUICKSTART.md` 速查表

### 添加新领域

编辑 `scripts/lib/domains.sh`，增加领域推断规则：
```bash
case "$TASK_DESC" in
  *公众号*|*微信*)
    AREA="wx.newstt"
    ;;
  *运维*|*服务器*)
    AREA="infra"
    ;;
  *)
    AREA="global"  # 默认
    ;;
esac
```

---

## 🧩 与其他技能/系统的集成

### 1. 与 OpenClaw 核心

| 集成点 | 方式 | 说明 |
|--------|------|------|
| Plugin System | `plugins.entries` | Hook 配置 |
| Hook Events | `handler.js` 监听 | 4个生命周期事件 |
| Session Context | 虚拟文件注入 | `agent:bootstrap` 提醒 |
| Gateway Logs | 输出到 `~/.openclaw/logs/` | 调试用 |

### 2. 与 LM Studio（向量搜索）

| 组件 | 用途 | 配置 |
|------|------|------|
| Embedding API | `http://localhost:1234/v1/embeddings` | 默认端口 |
| 模型 | `text-embedding-bge-large-zh-v1.5` | 1024维，中文优化 |
| 降级策略 | 检测失败 → 自动切关键词搜索 | 无感切换 |

### 3. 与 NapCat QQ 机器人

**不直接集成**，但可通过以下方式协同：
- 大瑞/大朵等 agent 调用 `search.sh` 获取经验
- 经验库作为团队知识库，所有 agent 共享

---

## 🚀 部署拓扑

### 单机部署（当前）

```
Mac mini (OpenClaw Gateway)
├─ ~/.openclaw/
│  ├─ gateway/              ← 网关进程
│  ├─ skills/rocky-know-how/← 技能脚本
│  └─ .learnings/           ← 共享数据（所有 agent 访问）
└─ agents/
   ├─ fs-daying/            ← 大颖（调度）
   ├─ fs-dajie/             ← 大杰（开发）
   └─ ...
```

**访问路径**：
- 所有 agent → `~/.openclaw/.learnings/`（符号链接或绝对路径）
- Hook Handler → 通过 `OPENCLAW_STATE_DIR` 环境变量推导

### 多机部署（未来）

```
VPS1 (生产)
├─ ~/.openclaw/.learnings/    ← 主库（同步到 VPS2）
└─ agent:fs-dajie

VPS2 (备份)
├─ ~/.openclaw/.learnings/    ← 从 VPS1 同步（rsync）
└─ agent:fs-daqing
```

**同步策略**：
- `rsync` 定时同步（cron 每 5 分钟）
- 冲突解决：时间戳最新者优先
- 锁机制跨机需 NFS（暂不支持）

---

## 📈 性能指标

| 指标 | 目标值 | 实测值 | 说明 |
|------|--------|--------|------|
| 搜索响应时间 | <1s | 0.3s (1000条) | 关键词搜索 |
| 写入延迟 | <0.5s | 0.2s | 持有锁期间 |
| 压缩速度 | 1000条/秒 | 1200条/秒 | `compact.sh` |
| 向量搜索 | <2s | 1.5s (LM Studio) | embedding 模型加载后 |
| Hook 触发延迟 | <10ms | 5ms | 事件 → Handler 执行 |

---

## 🛠️ 开发指南

### 调试 Hook

```bash
# 查看 Hook 日志
tail -f ~/.openclaw/logs/gateway.log | grep rocky-know-how

# 测试 Hook 手动触发
# 编辑 ~/.openclaw/openclaw.json，临时添加测试事件
{
  "plugins": {
    "entries": {
      "rocky-know-how": {
        "events": ["agent:bootstrap", "before_reset"]
      }
    }
  }
}
# 重启网关，观察日志
```

### 调试脚本

```bash
# 开启调试模式
export DEBUG=1
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --debug "test"

# 查看详细日志
tail -50 ~/.openclaw/.learnings/.summarize.log
```

### 添加日志

```javascript
// hooks/handler.js
console.log(`[rocky-know-how] event=${event.type} sessionKey=${sessionKey}`);
```

---

## 📚 文档索引

| 文档 | 用途 | 阅读对象 |
|------|------|----------|
| **本文件** `ARCHITECTURE.md` | 完整架构总览 | 开发者、架构师 |
| `README.md` | 功能特性 + 安装 | 所有用户 |
| `QUICKSTART.md` | 30秒快速上手 | 新用户 |
| `setup.md` | 详细安装配置 | 运维（大青） |
| `operations.md` | 操作手册 + 流程 | 所有用户 |
| `advanced-features.md` | 三大核心创新详解 | 高级用户 |
| `HOOK.md` | Hook 机制说明 | 开发者 |
| `scaling.md` | 存储优化 + 压缩 | 运维（大青） |
| `heartbeat-rules.md` | 心跳监控规则 | 运维（大瑞） |
| `boundaries.md` | 安全边界 + 红旗警告 | 安全审计 |
| `FAQ.md` | 17个常见问题 | 所有用户 |
| `INDEX.md` | 文档导航地图 | 所有用户 |
| `CHANGELOG.md` | 版本历史 | 所有用户 |

---

## 🔄 版本演进

| 版本 | 日期 | 重大变更 |
|------|------|----------|
| **2.8.8** | 2026-04-24 | 📐 **新增** ARCHITECTURE.md（本文件）；文档重大更正：明确两阶段机制 |
| 2.8.7 | 2026-04-24 | 文档统一：批量更新版本号为 2.8.6 |
| 2.8.6 | 2026-04-24 | Hook 升级：支持 OpenClaw 2026.4.21 新事件；新增 INDEX.md、FAQ.md |
| 2.8.3 | 2026-04-24 | 🔒 安全加固：H1/H2 漏洞修复；Bug #4 修复（memory.md 压缩） |
| 2.8.2 | 2026-04-24 | 🔐 并发锁、Hook 路径动态化、标签格式统一 |
| 2.8.1 | 2026-04-23 | 🔒 正则转义、路径检测、Hook 自动配置 |
| 2.7.1 | 2026-04-21 | 支持 OpenClaw 2026.4.21 新 Hook 事件 |
| 2.5.1 | 2026-04-15 | 退回简单版，移除 hook 注入 |

---

## 📞 反馈与贡献

- **Issues**: https://github.com/rockytian-top/openclaw-rocky-skills/issues
- **文档改进**: 提交 PR 到 `main` 分支
- **功能建议**: 在 `INDEX.md` 的"按任务快速查找"中缺失的功能即为待补充

---

**最后更新**: 2026-04-24 v2.9.1  
**维护人**: 大颖 (fs-daying)  
**状态**: ✅ 生产就绪，架构稳定
