---
name: rocky-know-how
description: "经验诀窍技能 Hook v3.3.0 — agent_end 实时 memory 扫描，AI 全权决策（新增/追加/跳过），工作区文件大小变化检测"
metadata: {"openclaw":{"export":"handler","emoji":"📚","events":["agent:bootstrap","agent_end"]}}
---

# rocky-know-how Hook v3.3.0

Agent 启动时自动注入经验诀窍提醒（含动态统计）到 bootstrap 上下文。
每个 agent 回合结束后通过 `agent_end` 插件实时扫描 memory 提取经验。

## 支持的事件

| 事件 | 触发时机 | 功能 |
|------|----------|------|
| `agent:bootstrap` | AI 启动 | 注入经验提醒（含本地经验统计） + 扫描 memory 提取新经验 |
| `agent_end` (插件) | 每轮对话结束 | 实时检测 memory 文件变化 → LLM 判断 → 新增/追加/跳过 |

## v3.3.0 经验记录流程

### agent_end 驱动（核心）

> `agent_end` 在每轮 agent 对话完成后触发，由 `rocky-know-how-end` 插件调用 handler.processMemoryDir。

```
before_compaction 触发
    │
    ▼
① 保存会话上下文到 pending/*.json
    │
    ▼
② 调用 processPendingItem()
    ├─ 提取 task/tools/errors
    ├─ 调用 LLM 提取 problem/solution/prevention
    └─ 写入 experiences.md
    │
    ▼
③ 调用 auto-review.sh
    ├─ 同类经验检测
    └─ 自动晋升检查（Tag → TOOLS.md）
    │
    ▼
压缩继续（compact() 执行）
```

### bootstrap 启动（兜底）

```
agent:bootstrap 触发
    ├─ 注入经验提醒到 systemPrompt
    └─ 检查 drafts/ → 有旧草稿则处理（防积压）
```

## 功能

- **before_compaction 驱动** — 压缩前同步执行经验记录
- **自动注入** — agent:bootstrap 事件触发
- **草稿缓冲** — 多轮调试不写半成品
- **动态工作区** — 自动从 sessionKey 推导 workspace 路径
- **跨 workspace** — 支持 shared 目录和全局安装

## 启用方式

```bash
bash install.sh
```

> 注意：`memoryFlush` 配置依然保留用于写 memory/*.md 文件，但经验记录已改为 `before_compaction` 驱动。
