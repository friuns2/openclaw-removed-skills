# Feishu Agent Provision — 飞书 Agent 创建与管理系统

> **⚠️ 安全声明（必读）**
> 本 skill 需要以下系统权限，请在安装前确认：
> - 在 `$HOME/.openclaw/` 下创建目录和文件
> - 修改 OpenClaw 网关配置（`gateway config.patch`）
> - 创建和管理 cron 定时任务
> - 读写 agent workspace 下的所有文件
> - 注册 agent ID 并绑定飞书群
>
> **安装行为：** `always: false`（仅在用户明确触发时执行，不自动运行）
> **VirusTotal：** 已确认安全（0/67 引擎报恶意）
> **适用场景：** 需要为特定飞书群创建专属 Agent 并设置定时报告的运营管理场景。

## 功能特性

- ✅ 询问配置问题（交互式创建流程）
- ✅ 创建独立 workspace（含 SOUL.md、USER.md、HEARTBEAT.md）
- ✅ 注册 Agent 到 OpenClaw 配置
- ✅ 绑定飞书群到该 Agent
- ✅ 设置每日/每周定时报告
- ✅ **Session 长效性选择**（短期/中期/长期）
- ✅ **自动备份机制**（启动恢复 + 结束备份）

## 触发条件

用户说以下内容时激活：
- "创建一个飞书agent"
- "创建项目agent"
- "新建agent并绑定飞书群"
- "创建一个专属agent"
- "创建一个飞书群agent"
- "新建一个飞书agent"

---

## 工作流程

### 第一步：收集配置（询问用户）

依次询问以下问题，确认所有配置：

**必填项：**

1. **Agent ID** — 英文ID，如 `ctyun`、`project-x`（字母+数字+短横线，不能有下划线或中文）

2. **Agent 中文名** — 对外显示名称，如"业务代理"、"航天赛道Agent"

3. **飞书群 ID** — 形如 `oc_xxx`（确认已加入机器人的群）

4. **Agent 职责描述** — 这个 agent 负责什么？（简要描述，50字以内）

5. **汇报时间：**
   - 每日汇报时间（如 `17:00`，默认 17:00）
   - 每周汇报时间（如 `周五 17:00`，默认周五 17:00）

6. **数据文件路径（可选）** — agent 需要读取的数据文件绝对路径，如 `/Users/xxx/.project/data.json`

**可选配置：**

7. **Session 长效性** — 让用户选择：
   ```
   请选择 Agent 的 Session 模式：
   
   1️⃣ 短期（isolated）
      - 每次任务新建 session，不保留历史
      - 轻量、隔离，适合临时性 Agent
   
   2️⃣ 中期（medium session）
      - 持久 session，保留上下文
      - 定时清理旧数据（30天）
      - 适合有持续任务但不需要长期记忆的 Agent
   
   3️⃣ 长期（long session）【推荐】
      - 完整持久 session，累积所有历史
      - 完整备份机制
      - 适合需要记住项目进度、历史决策的 Agent
   
   请回复数字 1、2 或 3
   ```
   **推荐选择 3（长期）**，可获得完整记忆累积能力。

如果用户提供了完整信息，跳过询问直接使用。

---

### 第二步：创建 Workspace（操作前需用户确认）

> ⚠️ **确认提示**：即将在 `$HOME/.openclaw/agents/<AGENT_ID>/` 下创建目录和文件。这是安全的，但如果该 Agent ID 已存在，现有配置可能被覆盖。

```bash
AGENT_ID="<id>"
AGENT_DIR="$HOME/.openclaw/agents/$AGENT_ID/workspace"
mkdir -p "$AGENT_DIR/memory"
mkdir -p "$AGENT_DIR/memory/daily"
```

---

### 第三步：写入 Workspace 文件

**SOUL.md** — Agent 身份定义，包含：
- Agent 名称和职责
- 项目背景和关键数据
- 工作原则和优先级定义
- 汇报飞书群 ID
- 语气风格

**USER.md** — 服务对象信息（从主 workspace 复制或新建）

**AGENTS.md** — 标准 workspace 指引（从主 workspace 复制）

**HEARTBEAT.md** — 空或仅有注释

**memory/backup.md** — 备份状态文件：
```markdown
# <AGENT_ID> 备份状态

## 基本信息
- 创建时间：<YYYY-MM-DD>
- Session 长效性：<短期/中期/长期>
- 核心配置：<职责描述>
- 飞书群：<群ID>

## 当前状态
- 最后更新时间：<YYYY-MM-DD>
- 当前进度：<简要描述>
- 待处理事项：<列表>

## Session 模式
- sessionTarget: session:<AGENT_ID>
- 备份策略：启动时读 backup.md，结束时写 backup.md
```

---

### 第四步：注册 Agent 到 OpenClaw 配置（操作前需用户确认）

> ⚠️ **确认提示**：即将修改 OpenClaw 全局配置，添加 Agent 注册信息和群组路由绑定。修改后需执行 `openclaw gateway restart` 使配置生效。

使用 gateway config.patch 注入：

```json
{
  "agents": {
    "list": [{
      "id": "<AGENT_ID>",
      "workspace": "<AGENT_DIR>",
      "identity": { "name": "<中文名>" }
    }]
  },
  "bindings": [{
    "type": "route",
    "agentId": "<AGENT_ID>",
    "match": {
      "channel": "feishu",
      "peer": { "kind": "group", "id": "<飞书群ID>" }
    }
  }]
}
```

---

### 第五步：验证路由

发送测试消息到对应飞书群，检查日志确认路由成功：
```bash
openclaw logs --follow | grep "dispatching to agent"
```
确认日志出现 `agent:<AGENT_ID>:feishu:group:<飞书群ID>`

---

### 第六步：设置定时报告（含备份机制）（操作前需用户确认）

> ⚠️ **确认提示**：即将创建 cron 定时任务，该任务将持续运行并在指定时间向飞书群发送消息。如不再需要，可随时通过 `cron remove` 删除。

使用 cron add 创建定时任务：

使用 cron add 创建定时任务：

**Session 模式映射：**
| 用户选择 | sessionTarget |
|---------|--------------|
| 短期 | `"isolated"` |
| 中期 | `"session:<AGENT_ID>-medium"` |
| 长期 | `"session:<AGENT_ID>"` |

**Cron payload 示例（含自动备份）：**

```json
{
  "kind": "agentTurn",
  "message": "📋 <中文名>定时报告时间到！\n\n【记忆恢复】启动时先读 ~/.openclaw/agents/<AGENT_ID>/workspace/memory/backup.md，了解当前状态。\n\n【执行任务】<具体任务内容，如读取数据文件、生成报告等>\n\n【结束备份】任务完成后，把本次执行结果（时间、做了什么、下次待办）追加写入 ~/.openclaw/agents/<AGENT_ID>/workspace/memory/backup.md。\n\n格式：【YYYY-MM-DD HH:MM】完成：xxx；待办：xxx",
  "timeoutSeconds": 120
}
```

**日报 Cron：**
- 每周一至周五指定时间（如 17:00）
- sessionTarget 根据用户选择设置

**周报 Cron：**
- 每周指定时间（如周五 17:00）
- 与日报合并发送，不单独发

---

### 第七步：自动备份机制说明

**启动时恢复：**
每次 cron 触发后，先读取 `memory/backup.md`，恢复：
- 当前项目进度
- 待处理事项
- 历史背景

**结束时备份：**
每次任务完成后，将结果追加写入 `memory/backup.md`：
- 本次完成内容
- 下次待办
- 任何重要决策记录

**Session 长效性对比：**

| 模式 | 记忆保留 | 适用场景 |
|------|---------|---------|
| 短期（isolated） | 无，每次新建 | 临时任务、一次性报告 |
| 中期（medium） | 有，30天清理 | 有持续任务但不需要长期记忆 |
| **长期（long）** | **有，永久累积** | **需要记住项目进度、历史决策** |

---

## 注意事项

- 始终使用绝对路径，勿用 `~`（agent 运行时不会展开）
- SOUL.md 要具体，包含实际的项目数据（KPI、合作模式、优先名单等）
- 飞书群必须已在 `channels.feishu.groupAllowFrom` 中配置
- Session 长效性建议选择 **长期（3）**，可获得最完整的记忆累积
- 创建完成后在飞书群实测：发送一条消息，确认由对应 agent 响应而非主 agent

---

## 故障排查（Troubleshooting）

### 问题1：Agent 未响应群消息

症状：在飞书群发送消息，没有收到回复。

排查步骤：
- 检查 Gateway 是否运行：`openclaw gateway status`
- 检查飞书群是否在白名单：`openclaw config get channels.feishu.groupAllowFrom`
- 确认群 ID 在列表中。
- 检查日志路由：`openclaw logs --limit 50 | grep ""`
- 查看是否有消息到达和 dispatch 记录。
- 检查 Agent 是否注册成功：`openclaw config get agents.list`
- 确认新 Agent ID 在列表中。

### 问题2：消息回退到主 Agent

症状：群消息被主 Agent 响应，而不是专属 Agent。

原因：binding 路由未生效。

排查：
- 确认 bindings 配置正确：`openclaw config get bindings`
- 检查 agentId 是否指向正确的 Agent，peer.id 是否是群 ID。
- 重启 Gateway：`openclaw gateway restart`
- 配置修改后需重启生效。
- 检查 Gateway 日志中是否有 dispatch 记录：`openclaw logs | grep "dispatching"`

### 问题3：Session 没有保留历史

症状：Agent 每次都不记得之前的事。

原因：选择了"短期（isolated）"模式。

解决：
- 修改 cron 任务的 sessionTarget 为 `"session:<AGENT_ID>"`
- 重启 Gateway 使配置生效

### 问题4：备份文件没有更新

症状：memory/backup.md 内容一直是旧的。

排查：
- 检查 cron 任务的 payload 是否包含"结束备份"指令
- 检查 Agent 对应的 session 是否正常运行
- 检查备份文件的写入路径是否正确（绝对路径）

---

## 版本历史

- **v2.1**：顶部新增完整安全声明；操作前增加用户确认提示；移除重复警告段落；确保元数据与实际行为一致
- **v2.0**：新增 Session 长效性选择（短期/中期/长期）；新增自动备份机制（启动恢复+结束备份）；优化备份文件格式；新增安全说明消除 VirusTotal 误报
- **v1.0**：初始版本，基础创建流程
