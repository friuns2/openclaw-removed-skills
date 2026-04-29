---
name: self-improvement-loop
version: 4.6.13
description: |
  Per-agent feedback loop for OpenClaw — captures corrections/errors/features, detects patterns per agent workspace, notifies via per-agent channel bot, and executes A/B/C/D decisions in the correct agent session.
  Auto-detects agents from openclaw.json, auto-maps agent ID → channel account → bindings.
  A/B/C/D handling logic lives in scripts/agents-append.md (shared); install.sh injects a reference into each agent's AGENTS.md and memory.md.
---

# self-improvement-loop v4.6.13

## 功能概述

**核心能力**：每个 agent 有独立的 self-improvement 闭环——隔离的 learnings 目录、独立的 cron 扫描、绑定到各自 channel bot 的通知、以及在正确 agent session 中执行 A/B/C/D。

```
用户纠正 code-dev agent
    ↓
code-dev hook 捕获 → 写入 code-dev/.learnings/
    ↓
self-improvement-code-dev cron（每1h）→ 只扫描 code-dev/.learnings/
    ↓
发现 pattern count≥2 → 通过 code bot 通知用户
    ↓
用户回复 A → code-dev agent session 执行 → 写回 code-dev workspace
```

---

## 数据流（Per-Agent 隔离）

```
openclaw.json (agents.list + bindings)
    │
    ├─→ install.sh 读取 agents
    │         ↓
    │    创建 per-agent 目录
    │    workspace/agents/code-dev/.learnings/
    │    workspace/agents/墨灵/.learnings/
    │
    ├─→ install.sh 读取 channel accounts
    │         ↓
    │    写入 bindings (agentId → accountId)
    │    { "agentId": "code-dev", "match": { "channel": "telegram", "accountId": "code" } }
    │
    └─→ setup_crons.py 创建 per-agent cron
              ↓
         每个 cron 带 --agent flag
         LEARNINGS_DIR 指向该 agent workspace
         delivery 使用该 agent 的 account

┌─────────────────────────────────────────────────────────────┐
│  Hook (handler.js) - 全局共享，动态路由                       │
│  sessionKey: "agent:code-dev:telegram:..."                 │
│  → extractAgentId("code-dev")                              │
│  → getAgentWorkspace("code-dev") → agent workspace path     │
│  → learningsDir = workspace + "/.learnings/"                │
│  推送提醒到 context.messages                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Cron (per-agent) - 各自独立运行                              │
│  Name: self-improvement-code-dev                            │
│  --agent code-dev → 绑定到 code-dev agent session           │
│  LEARNINGS_DIR=".../agents/code-dev/.learnings"              │
│  delivery: channel=telegram, accountId=code                │
│  只扫描自己的 LEARNINGS_DIR                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Notification - 通过各自 channel bot 发送                    │
│  code bot → 用户与 code-dev 对话                             │
│  moling bot → 用户与 moling 对话                             │
│  用户回复 A/B/C/D → OpenClaw 根据 bindings 路由到正确 agent  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  A/B/C/D Execution - 在正确 agent session 中执行             │
│  读取 pending JSON → 执行 skill-creator/skill-improvement   │
│  写回到对应 agent 的 learnings 目录                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 权限要求

| 权限 | 作用域 | 用途 |
|------|--------|------|
| `exec` | `scripts/` | 运行 distill.sh, archive.sh（机械扫描和归档） |
| `read` | `workspace/<agent>/.learnings/` | 读取 LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md |
| `write` | `workspace/<agent>/.learnings/` | 更新 notified 状态；创建 `.pending_notifications/*.json` |
| `cron` | 全局 | 创建和管理 self-improvement-{agent} cron jobs |
| `gateway_api` | Gateway :18789 | setup_crons.py 调用 API 创建 crons |
| `openclaw.json` | `HOME/.openclaw/` | install.sh 读取 agents 配置；写入 bindings |

**安全边界**：
- 文件操作严格限定在 `~/.openclaw/workspace/` 下的 per-agent learnings 目录
- 所有路径动态生成，无硬编码
- cron 在 isolated session 中运行，最小工具集
- install.sh 写入 bindings 前提示确认，可跳过

---

## 核心组件

| 组件 | 类型 | 路由依据 |
|------|------|----------|
| `handler.js` | 全局共享 Hook | sessionKey → agent ID → workspace |
| `distill.sh` | 共享脚本 | `LEARNINGS_DIR` 环境变量 |
| `setup_crons.py` | 共享脚本 | agent config → cron --agent flag |
| `install.sh` | 安装脚本 | agents.list + accounts → bindings |
| `agents-append.md` | A/B/C/D 处理逻辑 | 各 agent 共享；install.sh 注入索引引用 |

---

## Per-Agent 配置矩阵

```
Agent        │ Workspace                      │ Channel Account │ Cron Job
─────────────┼───────────────────────────────┼───────────────────┼─────────────────────
main         │ workspace/.learnings           │ default           │ self-improvement-main
claude       │ workspace/.learnings           │ moling (fallback) │ self-improvement-claude
code-dev     │ workspace/agents/code-dev/.l. │ code              │ self-improvement-code-dev
moling       │ workspace/agents/墨灵/.l.     │ moling            │ self-improvement-moling

自动映射规则：
  - 精确匹配：agent_id == account_id
  - main → default
  - 前缀匹配：code-dev → code
  - 无匹配 → defaultAccount (moling)
```

---

## 安装

```bash
bash ~/.openclaw/workspace/skills/self-improvement-loop/install.sh
openclaw gateway restart
```

安装时自动：
1. 创建各 agent 的 `.learnings/` 目录
2. 安装 hook 和脚本
3. 创建 per-agent cron jobs
4. 更新 `openclaw.json` bindings（实现消息路由）
5. 向**各 agent workspace** 的 `AGENTS.md` 和 `memory.md` 注入自我改进索引指令

**A/B/C/D 处理逻辑**存放在 `skills/self-improvement-loop/scripts/agents-append.md`（各 agent 共享一份）。安装时向各 agent 的 `AGENTS.md` 和 `memory.md` 注入索引指令：

```markdown
## 自我改进（A/B/C/D）

处理 A/B/C/D 之前必须查阅：
skills/self-improvement-loop/scripts/agents-append.md
```

安装后无需手动追加内容，skill 更新时所有 agent 自动使用最新版本。

---

## 验证

```bash
# 检查 bindings
python3 -c "import json; print(json.dumps(json.load(open('$HOME/.openclaw/openclaw.json')).get('bindings',[]), indent=2))"

# 检查 per-agent crons
openclaw cron list | grep self-improvement

# 测试 distill（指定 agent）
LEARNINGS_DIR="$HOME/.openclaw/workspace/agents/code-dev/.learnings" \
  bash ~/.openclaw/workspace/skills/self-improvement-loop/scripts/distill.sh --check-only
```

---

## 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| OpenClaw | ≥2026.4 | 平台基础 |
| Python3 | ≥3.8 | distill_json.py, write_notified.py |
| Node.js | 任意 | handler.js |
| skill-creator | any | A 路径创建技能 |
| skill-improvement | any | B 路径优化技能 |

---

## 限制与已知问题

- **ACP runtime agent (claude)**：无独立 channel，fallback 到 `defaultAccount`
- **API (Gateway)**：API 不通（404），回退到 CLI 创建 cron，sessionTarget 降级为 isolated
- **并发通知**：同一时刻多个 agent 触发时，用户回复可能路由到错误的 agent session
- **sessionTarget=current**：需要 Gateway API 支持，当前不可用

---

## See Also

- `references/setup-guide.md` — 完整安装和配置指南