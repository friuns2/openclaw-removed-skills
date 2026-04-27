---
name: jy-hk-stock-morning-brief
description: 生成《港股资讯早报》——专业港股市场分析师角色，基于聚源数据 MCP 接口（通过 mcporter 调用）分析前一交易日市场动态、板块个股、公司公告、研报观点、南向资金、行业全景、外围市场等，为早盘投资者提供决策参考。触发词：港股早报、港股资讯早报、HK 早报、港股日报、恒指复盘、港股复盘。Generate HK Stock Morning Brief via GILData MCP (mcporter), analyzing previous trading day for investors. Trigger on HK market briefing requests.
metadata:
  openclaw:
    requires:
      bins: ["node", "npm", "mcporter"]
    install:
      - id: install-mcporter
        kind: node
        package: mcporter
        label: Install mcporter via npm
---

# 【港股资讯早报】

专业港股市场分析师角色，通过 `mcporter call` 调用聚源数据 MCP 服务，生成前一交易日市场分析报告。

## 功能范围

1. **趋势展望** — 恒指/国指/科指行情、市场综述、热点聚焦
2. **要闻点评** — 上市公司公告、重要新闻深度解读
3. **数据追踪** — 南向资金流向、港股通十大活跃成交股
4. **行业全景** — 聚焦行业核心动态、前景与机遇
5. **港股攻略** — 大行评级精选、目标价、大类资产观察
6. **环球视野** — 隔夜外围市场、经济数据前瞻

输出：Markdown + PDF（可选），所有数据标注来源与时间戳。

## 查询建议

- **目标日期**：默认前一港股交易日（自动排除周末及假期）
- **数据范围**：T-1 日收盘后至今日开盘前的公告/新闻为重点

查询示例：`生成港股早报`、`帮我写今天的港股资讯早报`、`分析昨日港股市场表现`

## 环境检查与配置

**每次使用前必须检查 mcporter 安装和 MCP 服务配置！**

### 步骤 1：检查 mcporter 安装

```bash
mcporter --version
# 如未安装：npm install -g mcporter
```

### 步骤 2：检查 MCP 服务配置

```bash
mcporter list
# 预期输出：必须包含 jy-financedata-tool 和 jy-financedata-api
```

**如未配置，需获取 JY_API_KEY**：

**申请邮箱**：datamap@gildata.com  
**邮件标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名  
**正文**：姓名、手机号、公司/单位全称、所属部门、岗位、MCP_KEY 申请用途、Skill 申请列表、是否需要 Skill 安装包

申请通过后获取工具版和接口版 KEY，然后配置：

```bash
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
mcporter list  # 验证
```

**没有 JY_API_KEY 无法调用服务，必须先完成配置。**

### 步骤 3：OpenClaw 配置

编辑 `~/.openclaw/openclaw.json` 添加 mcporter 配置（详见 README.md），然后 `openclaw gateway restart`。

## 核心工作流程

工具调用可并发执行提速。详细 API 映射见 `references/api-mapping.md`。

**步骤 1**：确定前一港股交易日（排除周末、假期），参考 `references/hk-holidays.md`。

**步骤 2-5**：通过 `mcporter call` 并发获取数据（指数、板块、公告、研报、外围市场），所有工具入参均为 `query`。

**步骤 6**：生成 Markdown 报告（标注 API 来源）+ echarts 图表 + PDF，保存至 `/home/liust/openclaw/workspace/reports/`。

## 标准报告结构

详见 `references/report-examples.md` 完整样例和 `references/api-mapping.md` API 溯源标注指南。

**模板要点**：
- 每个数据项标注具体 API 来源（如 `（来源：HKDailyIndexQuote）`）
- 表格数据在下方统一标注
- 暂缺数据注明"（聚源 MCP 暂未覆盖，建议通过 XX 查询）"
- 末尾添加"数据说明"章节，列出已覆盖/未覆盖的 API

## 快速开始

**首次使用**：完成「环境检查与配置」所有步骤。  
**日常使用**：输入 `生成港股早报`，技能自动完成全流程。

**数据获取策略**：`jy-financedata-api` 获取结构化行情数据，`jy-financedata-tool` 获取公告/研报/新闻文本，所有工具入参均为 `query`，并发调用提速。

## 资源清单

```
~/openclaw/workspace/skills/jy-hk-stock-morning-brief/
├── SKILL.md                      # 本技能说明
├── README.md                     # 快速入门
├── references/
│   ├── hk-holidays.md            # 港股假期日历（2026 年）
│   ├── report-examples.md        # 完整报告样例
│   └── api-mapping.md            # API 映射与数据溯源指南（新增）
└── scripts/
    ├── fetch_hk_data.py          # 数据获取脚本（mcporter 调用）
    └── generate_pdf.py           # PDF 生成脚本
```

**references/api-mapping.md**：列出所有 MCP API 与报告章节的映射关系，包含 mcporter 调用示例和标注格式，生成报告时请查阅。

## 特殊情况处理

| 情况 | 处理方式 |
|------|----------|
| 数据缺失 | 注明"数据暂缺"，不编造 |
| 无重大公告 | 简化"要闻点评"或注明"无重大公告" |
| 非交易日 | 说明"分析最近交易日（X 月 X 日）数据" |
| 财报季密集 | 优先处理财报相关公告 |
| 市场大幅波动（±3%） | 重点分析驱动因素 |

## 输出要求

Markdown + PDF 双版本，保存至 `/home/liust/openclaw/workspace/reports/`，含 echarts 图表，简体中文专业风格。

**数据溯源标注**：每个数据项标注具体 API 来源（详见 `references/api-mapping.md` 完整映射表），暂缺数据注明"聚源 MCP 暂未覆盖"并提供替代查询建议。

## 限制

数据必须来自聚源数据 MCP；仅分析 T-1 日数据；必须配置有效 JY_API_KEY；报告末尾必须包含免责声明。

## 注意事项

严禁预测当日走势；每个数据项标注具体 API 来源（详见 `references/api-mapping.md`）；所有数据注明交易日期；暂缺数据标注"聚源 MCP 暂未覆盖"并提供替代查询建议；PDF 检查排版和图表渲染。
