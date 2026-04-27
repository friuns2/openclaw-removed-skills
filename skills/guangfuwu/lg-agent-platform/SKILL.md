---
name: lg-agent-platform
version: 1.0.11
description: Cloud Quant & Stock Monitor. Serverless alerts to Feishu/WeChat. Portfolio PnL, minute bars, Python strategy backtesting, and zero-friction feedback. 自动盯盘, 量化交易, 回测, 飞书推送.
license: MIT-0
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "requires": {
        "env": ["LG_AGENT_BASE_URL", "LG_AGENT_TOKEN"]
      }
    }
  }
---

# LG Data Stock Monitor

**赋予您的通用 AI Agent 专业的金融量化与全天候盯盘能力。**
支持 A 股、港股实时行情与分钟线数据，提供 Serverless 云端策略托管及飞书/微信毫秒级预警推送。

🎯 **最佳适用场景**：实时股票预警、持仓盈亏追踪、自动化量化工作流。

![演示](./lg-data-demo.gif)

---

## 🌟 核心亮点

### 1. 🤖 兼容所有主流通用 AI Agent
打破生态壁垒，本技能不仅专供某一平台，而是**完美兼容 Hermes、OpenClaw、Claude Code、GitHub Copilot 等所有支持外挂工具/技能的通用大模型 Agent**。只需简单配置环境变量，您的通用 AI 助手瞬间化身专业量化分析师。

### 2. 🔒 银行级数据隐私隔离 (Privacy First)
**无需向大模型暴露您的敏感财务数据！** 
传统对话模式要求您手动输入持仓数量和成本，极易造成隐私泄露。本技能采用**云端托管架构**，您的真实持仓、账户数据全部安全储存在 `lg-data.cc` 平台。Agent 仅通过加密 Token 安全调用盈亏分析结果，彻底杜绝隐私数据被用于大模型训练的风险。

### 3. ⚡ Serverless 极速预警与零部署
策略云端托管运行，无需您购买第三方行情 API，无需自建服务器维护 Cron 任务，无 Token 消耗税。策略触发后，毫秒级推送到您的飞书机器人或微信 Webhook。

---

## 🛠️ 能做什么

| 核心功能 | 详细说明 |
| :--- | :--- |
| **资产盈亏巡航** | 一键查询持仓明细、当日盈亏、历史收益率，数据由 lg-data.cc 闭环处理。 |
| **云端自动盯盘** | 设置预警条件（突破均线、涨跌幅、换手率等），触发即通知，7x24小时云端值守。 |
| **多终端实时推送** | 策略触发毫秒级推送到飞书、微信 Webhook，不错过任何交易信号。 |
| **实时深度行情** | 获取 A 股、港股实时报价及分钟线数据，为 Agent 提供精准决策依据。 |
| **策略回测** ✨ NEW | 用 Python 写策略、用平台日线数据一键跑历史回测，输出 Sharpe / 最大回撤 / 交易明细 |
| **用户声音收集** | 支持 Agent 代客户提交 Bug 和需求，无缝对接后台反馈系统。 |

---

## 🚀 快速接入 (Quick Start)

只需三步，即可让您的 AI Agent 拥有量化能力：

### 1) 获取您的专属 Token
1. 注册并登录 [lg-data.cc](https://lg-data.cc)
2. 进入 **Account Settings / Token** 页面
3. 创建一个仅包含所需 scopes 的专用 Token（建议先用只读或低权限 Token）
4. 复制您的专属 `LG_AGENT_TOKEN`

### 2) 为您的 Agent 配置环境变量
在您使用的 Agent 终端（如 Hermes、Claude Code、GitHub Copilot 或 OpenClaw）中注入以下环境变量：
```bash
export LG_AGENT_BASE_URL="https://lg-data.cc"
export LG_AGENT_TOKEN="***"
```
公开版仅支持以上 Bearer Token 方式，不支持 session cookie / CSRF 兼容调用。

### 3) 唤醒 Agent，开始对话
现在，您可以直接用自然语言向您的 Agent 下达指令了！

---

## 💬 典型应用场景

### 场景 1：查询私密资产盈亏（数据不落大模型）
> **您：** “帮我查下今天的账户盈亏情况。”
> 
> **Agent（调用 `dataasset.data.get`）：** 
> “为您同步 lg-data.cc 的最新分析结果：
> 💰 **当日盈亏：** +319 元 | **累计浮动：** -19,135 元
> 📊 **持仓明细：** 
> - 中国核电：+2.06%
> - 永和股份：-32.45%
> - 中国联通：-16.25%”

### 场景 2：设定云端智能监控
> **您：** “帮我监控贵州茅台，只要突破MA20均线就通知我。”
> 
> **Agent（调用监控接口）：** 
> “✅ 已在云端成功创建监控任务：
> - **标的**：贵州茅台 (SH600519)
> - **条件**：价格突破 MA20
> - **通知**：飞书/微信推送
> *任务将在 Serverless 云端静默运行，触发时您将立刻收到推送。*”

### 场景 3：测试流程并抓取执行日志

```bash
# 触发执行（异步），记下返回的 executionId
# 自定义参数放在 body 里：key=参数名（以 - / -- 开头），value=参数值
# 后端会自动注入 `-f <procName>` —— body 里不用传 -f（传了也会被忽略）
RESP=$(scripts/lg_agent_exec.sh '{
  "skillId": "process.ingestion.execute",
  "pathParams": {"id": "123"},
  "body": {
    "-start_date": "20260419",
    "-end_date":   "20260420",
    "--env":       "dev"
  }
}')
EXEC_ID=$(echo "$RESP" | jq -r '.executionId')

# 轮询日志，直到 completed=true
OFFSET=0
while :; do
  LOG=$(scripts/lg_agent_exec.sh "{
    "skillId": "process.ingestion.execute.log.get",
    "pathParams": {"id": "123", "executionId": "$EXEC_ID"},
    "query": {"offset": "$OFFSET"}
  }")
  echo "$LOG" | jq -r '.logLines[]'
  [ "$(echo "$LOG" | jq -r '.completed')" = "true" ] && break
  OFFSET=$(echo "$LOG" | jq -r '.nextOffset')
  sleep 1
done
echo "exitCode=$(echo "$LOG" | jq -r '.exitCode')"
```

返回：`status` 由 `running` 过渡到 `completed` 或 `failed`，`exitCode` 为脚本退出码，`logLines` 为增量日志行。

### 场景 4：策略回测（双均线跑茅台）

> **您：** “用双均线（5日/20日）对茅台 SH600519 过去三年跑个回测”

在平台新建一个 `python_script` 流程节点，脚本如下（`lg_utils` 已预装）：

```python
from lg_utils import get_variable
from lg_utils.backtest_examples.dual_ma import DualMA
from lg_utils.backtest_examples.stock_day import run_stock_day_backtest

result = run_stock_day_backtest(
    strategy=DualMA(fast=5, slow=20),
    stock_num="600519",
    start="20220101",
    end="20241231",
    initial_cash=1_000_000,
    commission_bps=3, slippage_bps=1,
)
print(result.summary())
result.export_to_context("maotai_ma520")
```

任务日志里会出现：

```
=== Backtest Summary ===
asset           : stock_day
period          : 20220101 ~ 20241231  (bars=725)
total_return    : 23.1500%
sharpe          : 0.8412
max_drawdown    : 18.2300%
num_trades      : 14
win_rate        : 57.1429%
__LG_BACKTEST_RESULT__:maotai_ma520:{"metrics":...,"trades":...}
```

完整 JSON（含 `trades` / `equity_curve`）会被下游节点或监控面板消费。

## 技能列表

### REST 技能（`scripts/lg_agent_exec.sh` 调用）

> 当前公开版 skill 仅包含只读能力与常规非破坏性写操作。删除、终止、撤销、系统级评估、审批流等高风险/管理类操作不在该公开版 skill 范围内。
> 风险标记：🟢 low / 🟡 medium。所有 `GET` 技能默认对会话用户开放；写操作需显式授予 scope。

### 流程 (Process / Ingestion)

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `process.ingestion.list` | GET | 列出所有流程 | 🟢 |
| `process.ingestion.get` | GET | 根据 id 获取流程详情 | 🟢 |
| `process.ingestion.execute` | POST | 异步触发流程执行（返回 executionId）。`body` 接收自定义 CLI 参数，如 `{"-start_date":"20260419","--env":"dev"}`。后端自动注入 `-f <procName>`，不要自己传 `-f`。 | 🟡 |
| `process.ingestion.execute.log.get` | GET | 按 `executionId` 拉取日志+状态，支持 `offset` 增量轮询。记录持久化在 `process_execution` 表 + 磁盘文件，重启不丢。 | 🟢 |
| `process.component.list` | GET | 列出当前团队可用的步骤组件（含 Markdown 使用说明） | 🟢 |
| `process.pipeline.build` | POST | 一次性创建完整 pipeline（节点+组件+边） | 🟡 |
| `process.pipeline.update` | PUT | **全量更新已有 pipeline**（`PUT /api/ingestions/{id}`，同形 `BuildPipelineRequest`）。`nodes` 省略=仅改名/描述，保留现有步骤；`nodes=[]` 显式清空；`nodes=[...]` 全量替换。每次 PUT 自动写一条 `dacp_meta_proc_version`，可 `/versions/{n}/restore` 回滚。legacy `team_name IS NULL` 的流程会直接 403，需先 backfill。 | 🟡 |

### 调度 (Schedule)

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `schedule.job.list` | GET | 列出调度作业 | 🟢 |
| `schedule.job.get` | GET | 获取调度作业详情 | 🟢 |
| `schedule.instance.list` | GET | 列出作业实例（运行历史） | 🟢 |
| `schedule.instance.log.get` | GET | 按 `jobTriggerId` 拉取作业日志 | 🟢 |
| `schedule.job.plugin.webhook.trigger` | POST | 触发作业绑定的 webhook 插件 | 🟡 |

### 数据源 & 数据资产 (Datasource / Data Asset)

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `datasource.list` | GET | 列出数据源 | 🟢 |
| `datasource.get` | GET | 获取数据源详情 | 🟢 |
| `datasource.list.active` | GET | 列出活跃数据源 | 🟢 |
| `datasource.connection.test` | POST | 测试数据源连接 | 🟡 |
| `dataasset.list` | GET | 列出数据资产 | 🟢 |
| `dataasset.get` | GET | 获取资产详情 | 🟢 |
| `dataasset.schema.get` | GET | 获取资产 schema | 🟢 |
| `dataasset.data.get` | GET | 查询资产数据（盈亏、行情等） | 🟢 |

### 看板 & 工作空间 (Dashboard / Workspace)

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `dashboard.list` | GET | 列出看板 | 🟢 |
| `dashboard.get` | GET | 获取看板详情 | 🟢 |
| `dashboard.data.get` | GET | 一次拿看板所有组件的数据（支持 `maxRows`，默认 100，上限 500） | 🟢 |
| `workspace.list` | GET | 列出工作空间 | 🟢 |
| `workspace.get` | GET | 获取工作空间详情 | 🟢 |

### 订阅 & Marketplace

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `subscription.token.list` | GET | 列出订阅 token | 🟢 |
| `subscription.token.create` | POST | 创建订阅 token | 🟡 |
| `marketplace.item.list` | GET | 列出可订阅的看板/资产 | 🟢 |
| `marketplace.item.subscribe` | POST | 订阅市场条目 | 🟡 |
| `marketplace.item.unsubscribe` | POST | 取消订阅 | 🟡 |

### 指标告警 (Metric Alert)

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `metric.alert.list` | GET | 按 `dashboardId` 列出告警规则 | 🟢 |
| `metric.alert.get` | GET | 按 `ruleCode` 获取规则 | 🟢 |
| `metric.alert.create` | POST | 创建告警规则 | 🟡 |
| `metric.alert.update` | PUT | 更新告警规则 | 🟡 |
| `metric.alert.toggle` | PUT | 启用/停用规则 | 🟡 |
| `metric.alert.test` | POST | 仅测试（无副作用） | 🟡 |
| `metric.alert.evaluate` | POST | 执行评估并按规则触发 webhook | 🟡 |

### Webhook 插件

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `plugin.webhook.send` | POST | 通过数据源发送 webhook | 🟡 |

### 用户注册 & 反馈

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `auth.user.register` | POST | 注册新账号（`teamName` 自动生成为 `tenant_${username}`） | 🟢 |
| `feedback.submit` | POST | 提交反馈/Bug/需求 | 🟢 |
| `feedback.list` | GET | 查看历史反馈与官方回复 | 🟢 |

### Stock Studio（需开通 `stock_studio` 解决方案权限）

| skillId | method | 功能 | 风险 |
|---|---|---|---|
| `stockstudio.portfolio.list` | GET | 查持仓（支持 `account_id`/`market`/`stock_num`/`q`/`limit`/`offset`） | 🟢 |
| `stockstudio.portfolio.create` | POST | 新增持仓条目 | 🟡 |
| `stockstudio.portfolio.update` | PUT | 更新持仓 | 🟡 |
| `stockstudio.trading.list` | GET | 查交易记录 | 🟢 |
| `stockstudio.trading.create` | POST | 录入新交易（自动更新持仓） | 🟡 |

> 技能源在 `app.js` 的 `SKILL_CATALOG`，运行时可通过 `GET /agent/skills` 查询**当前 token 实际可用**的列表（会过滤 scope）。

### Python 工具库 `lg_utils`（在平台 `python_script` 流程节点里 `import` 使用）

平台的 `python_script` 执行器会自动把 `lg_utils` 注入到用户脚本的 `PYTHONPATH`，无需安装。

| 模块 / 函数 | 功能 |
|---|---|
| `lg_utils.get_variable(key, default)` | 读取流程上下文变量（由前端/调度器传入） |
| `lg_utils.get_context()` | 当前团队快照：`assets / datasources / dashboards / processes` |
| `lg_utils.get_asset_data(asset, page, size, order_by, filter_column, filter_value, ...)` | 分页拉团队有权限的资产数据（股票行情、持仓等） |
| `lg_utils.get_connection(ds_name)` / `get_db_config(ds_name)` | 按团队数据源名取 JDBC 连接 |
| **`lg_utils.backtest(strategy, asset, ...)`** ✨ NEW | **策略回测引擎**：单资产、long-only、整数股；输出 Sharpe / Sortino / MaxDD / 胜率 / 交易明细 / equity_curve |
| `lg_utils.backtest_examples.dual_ma.DualMA` ✨ NEW | 内置双均线参考策略 |
| `lg_utils.backtest_examples.stock_day.run_stock_day_backtest` ✨ NEW | 针对平台 `stock_day` 日线表（`OPEN_PRICE/CLOSE_PRICE/day_id/STOCK_NUM`）的快捷封装 |

## 环境要求

### 必需

- `LG_AGENT_BASE_URL` - 平台地址（默认 `https://lg-data.cc`）
- `LG_AGENT_TOKEN` - Bearer Token（公开版唯一认证方式；建议使用最小权限、专用 Token）

## Security Notes

- 公开版 skill 仅支持 Bearer Token 模式，不接受会话 Cookie / CSRF。
- 首次安装建议使用测试账号或低权限 Token 验证读取类能力。
- 当前公开版 skill 仅面向只读与常规非破坏性写操作；删除、终止、审批与其他管理类能力应通过单独的 admin 工具或人工流程处理。
- 写操作应只授予明确需要的 scopes。
- 不要在脚本里硬编码 Token 凭据。

## 注意事项

- 公开版 skill 不包含删除、终止、撤销、审批等高风险管理操作。
- 公开版 helper scripts 只支持 Token 调用，不支持 session/cookie 兼容模式。
- `idempotencyKey` 用于幂等控制，写操作请保持稳定。
- Token 从平台获取，不要硬编码在脚本中。

---

**传送门：** [https://lg-data.cc](https://lg-data.cc)