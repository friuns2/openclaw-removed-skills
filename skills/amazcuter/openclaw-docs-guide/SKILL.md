# openclaw-knowledge

OpenClaw 学习知识库 - 自动更新的最佳实践指南。

## 作用

这个 Skill 包含我从 OpenClaw 官方文档学习到的重要知识点，用于：
1. 指导系统配置和故障排查
2. 提供快速参考和最佳实践
3. 避免重复错误

## 更新机制

- **自动更新**：每次心跳学习新文档后自动更新
- **来源**：`/mnt/nas/openclaw-docs/` 官方文档
- **格式**：结构化知识卡片

---

## 文件说明

- **SKILL.md** (本文件): 核心知识点速查手册
- **LEARNING_HISTORY.md**: 完整学习历史记录（46篇文档详细笔记）

---

## 核心知识

### 1. 模型配置 (concepts/models.md)

**模型引用格式**：`provider/model`

**当前配置**:
```json
{
  "primary": "kimi-coding/k2p5",
  "fallbacks": ["zai/glm-5"]
}
```

**切换命令**:
```bash
/model kimi-coding/k2p5
/model zai/glm-5
```

---

### 2. 故障转移 (concepts/model-failover.md)

**两阶段故障处理**:
1. 同一 provider 内 Auth profile 轮换
2. 模型回退到 `agents.defaults.model.fallbacks`

**冷却机制**: 1分钟 → 5分钟 → 25分钟 → 1小时

---

### 3. 会话管理 (concepts/session.md)

**重要！多用户隐私隔离**:
```json
{
  "session": {
    "dmScope": "per-channel-peer"
  }
}
```

**常用命令**:
- `/status` - 查看会话状态
- `/context list` - 查看上下文内容
- `/compact` - 压缩上下文释放空间

---

### 4. 定时任务 (concepts/cron.md)

**关键参数**:
```bash
openclaw cron add \
  --name "任务名" \
  --cron "0 8 * * *" \
  --channel telegram \
  --to "8232122155" \  # ← 必须指定接收者
  --announce           # ← 必须启用投递
```

---

### 5. 消息队列 (concepts/queue.md)

**队列模式**:
- `collect` (默认) - 合并消息批量处理
- `steer` - 立即注入当前 run
- `followup` - 当前 run 结束后执行

---

### 6. 上下文压缩 (concepts/compaction.md)

**自动压缩触发**: 接近上下文窗口限制时
**手动压缩**: `/compact [指令]`

---

### 7. 记忆系统 (concepts/memory.md)

**文件结构**:
- `memory/YYYY-MM-DD.md` - 每日日志
- `MEMORY.md` - 长期记忆（主会话加载）

**写入时机**: 决策、偏好、持久事实

---

### 8. 工具配置

**Brave Search**:
```json
{
  "tools": {
    "web": {
      "search": {
        "provider": "brave",
        "apiKey": "..."
      }
    }
  }
}
```

---

### 9. 安全要点

**红线条款**:
- 不泄露私人数据
- 不执行破坏性命令
- 不确定时询问

**多用户场景**: 必须使用 `dmScope: "per-channel-peer"`

---

### 10. 快速命令参考

| 需求 | 命令 |
|------|------|
| 切换模型 | `/model kimi-coding/k2p5` |
| 查看状态 | `/status` |
| 压缩上下文 | `/compact` |
| 查看上下文 | `/context list` |
| 停止当前 run | `/stop` |
| 重置会话 | `/new` |
| 查看工具 | `/tools list` |

---

## 学习进度

- **已完成**: 35/219 篇文档 (16.0%)
- **已完成目录**: concepts/ (27篇), 其他 (8篇)
- **进行中**: gateway/
- **最近学习**: gateway/configuration.md

### 11. Gateway 配置 (gateway/configuration.md)

**配置文件位置**: `~/.openclaw/openclaw.json` (JSON5 格式，支持注释)

**最小配置**:
```json5
{
  agents: { defaults: { workspace: "~/.openclaw/workspace" } },
  channels: { whatsapp: { allowFrom: ["+15555550123"] } },
}
```

**CLI 配置命令**:
```bash
openclaw onboard       # 完整引导
openclaw configure     # 配置向导
openclaw config get agents.defaults.workspace
openclaw config set agents.defaults.heartbeat.every "2h"
openclaw config unset tools.web.search.apiKey
```

---

_最后更新: 2026-03-19_
_更新方式: 自动（心跳学习后）_
