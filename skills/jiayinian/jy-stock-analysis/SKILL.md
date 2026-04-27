---
name: jy-stock-analysis
description: 基于恒生聚源金融数据库 (MCP) 进行全面的个股分析与诊断。覆盖企业营收、行业动态、概念热点、市场行情四大维度，提供实时行情、财务分析（杜邦框架）、估值分析、资金流向、技术分析、机构评级、盈利预测等功能。使用场景：当用户需要分析具体股票时触发，例如"分析一下宁德时代"、"中际旭创值得投资吗"、"贵州茅台估值水平"等。Comprehensive individual stock analysis based on MCP GILData Financial Database, covering corporate revenue, industry dynamics, concept hotspots, and market conditions. Provides real-time quotes, financial analysis (DuPont framework), valuation, capital flow, technical analysis, institutional ratings, and earnings forecasts. Use case: Triggered when user needs to analyze a specific stock, e.g., "Analyze CATL", "Is Zhongji Innolight worth investing?", "Kweichow Moutai valuation". 本 Skill 仅提供客观数据分析，不构成任何投资建议。This Skill provides objective data analysis only and does not constitute any investment advice.
version: 1.0.0
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

# 个股分析（jy-stock-analysis）

基于恒生聚源金融数据库 (MCP) 进行全面的个股分析与诊断，覆盖企业营收、行业动态、概念热点、市场行情四大维度。

**重要声明**：本 Skill 仅提供客观数据分析，不构成任何投资建议。股市有风险，投资需谨慎。

---

## 功能范围

| 模块 | 功能描述 |
|------|----------|
| 实时行情 | 最新价、涨跌幅、成交量、市值等（强制二次核验） |
| 公司经营 | 主营构成、财务指标趋势、重大事项 |
| 行业动态 | 行业分类、指数表现、产业链分析 |
| 概念热点 | 概念板块、机构评级、盈利预测、目标价 |
| 行情分析 | 估值分析、资金流向、技术指标 |

**触发场景**：
- "分析一下宁德时代" / "中际旭创值得投资吗"
- "贵州茅台的估值水平" / "腾讯控股财务数据"
- "300750 这只股票怎么样"

---

## 查询建议

**查询要素**：股票名称或代码（如"宁德时代"或"300750"）

**查询写法**：
- 直接给出股票名称：`分析一下比亚迪`
- 给出股票代码：`看看 002594`
- 指定分析维度：`分析一下茅台的估值水平`

---

## 查询示例

```
分析一下宁德时代
帮我看看贵州茅台的财务数据
300750 这只股票怎么样
腾讯控股的估值水平如何
```

---

## 环境检查与配置

**每次使用前必须检查 mcporter 安装和 MCP 服务配置！**

### 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装**：
```bash
npm install -g mcporter
mcporter --version
```

### 步骤 2：检查 MCP 服务配置

```bash
mcporter list
```

**预期输出**（必须包含）：
- `jy-financedata-tool`
- `jy-financedata-api`

**如未配置**，获取 JY_API_KEY 并配置：

#### 2.1 获取 JY_API_KEY

向恒生聚源申请（首次配置，配置一次即可）：
- **申请邮箱**：datamap@gildata.com
- **邮件标题**：数据地图 KEY 申请 -XX 公司 - 申请人姓名
- **正文**：姓名、手机号、公司全称、部门、岗位、申请用途、Skill 列表

#### 2.2 配置 MCP 服务

```bash
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

#### 2.3 验证配置

```bash
mcporter list
```

### 步骤 3：OpenClaw 配置（如未配置）

**mcporter 配置路径**：
- Windows: `C:\Users\用户名\config\mcporter.json`

**编辑 openclaw.json**：
```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": { "MCPORTER_CONFIG": "C:\\Users\\用户名\\config\\mcporter.json" }
      }
    }
  }
}
```

**重启 OpenClaw**：`openclaw gateway restart`

---

## MCP 工具调用参考

| 工具名 | 功能 | 调用示例 |
|--------|------|----------|
| `FinQuery` | 金融问数，自然语言查询金融数据 | `mcporter call jy-financedata-tool.FinQuery query="查询内容"` |
| `MacroIndustryData` | 宏观行业经济数据 | `mcporter call jy-financedata-tool.MacroIndustryData query="查询内容"` |
| `FinancialResearchReport` | 研究报告全文摘要 | `mcporter call jy-financedata-tool.FinancialResearchReport query="股票代码"` |
| `FundMultipleFactorFilter` | 智能选基 | `mcporter call jy-financedata-tool.SmartFundSelection query="筛选条件"` |
| `StockMultipleFactorFilter` | 智能选股 | `mcporter call jy-financedata-tool.SmartStockSelection query="筛选条件"` |
| `AShareLiveQuote` | A 股实时行情 | `mcporter call jy-financedata-api.AShareLiveQuote query="600570"` |
| `MainOperIncData` | 主营构成 | `mcporter call jy-financedata-api.MainOperIncData query="600570"` |
| `StockValueAnalysis` | 股票价值分析（PE/PB/ROE 等） | `mcporter call jy-financedata-api.StockValueAnalysis query="600570"` |
| `StockBelongIndustry` | 所属行业分类 | `mcporter call jy-financedata-api.StockBelongIndustry query="600570"` |
| `StockBelongConcept` | 所属概念板块 | `mcporter call jy-financedata-api.StockBelongConcept query="600570"` |
| `InstitutionalRating` | 机构评级 | `mcporter call jy-financedata-api.InstitutionalRating query="600570"` |
| `ConsensusExpectationDetail` | 一致预期明细 | `mcporter call jy-financedata-api.ConsensusExpectationDetail query="600570"` |
| `PerformanceExpress` | 业绩快报 | `mcporter call jy-financedata-api.PerformanceExpress query="600570"` |
| `PerformanceForecast` | 业绩预告 | `mcporter call jy-financedata-api.PerformanceForecast query="600570"` |
| `AStockCashFlow` | 个股资金流向 | `mcporter call jy-financedata-api.AStockCashFlow query="600570"` |
| `StockRangeQuotation` | 股票区间行情 | `mcporter call jy-financedata-api.StockRangeQuotation query="600570"` |
| `CorporateResearchViewpoints` | 公司研究观点 | `mcporter call jy-financedata-api.CorporateResearchViewpoints query="600570"` |
| `NewsPublicOpinionList` | 新闻舆情 | `mcporter call jy-financedata-api.NewsPublicOpinionList query="600570"` |
| `IndustryIndexLiveQuote` | 行业指数实时行情 | `mcporter call jy-financedata-api.IndustryIndexLiveQuote query="SW801010"` |
| `ConceptIndexLiveQuote` | 概念指数实时行情 | `mcporter call jy-financedata-api.ConceptIndexLiveQuote query="CN001"` |
| `FinancialDataComparison` | 同行业财务数据比较 | `mcporter call jy-financedata-api.FinancialDataComparison query="600570"` |
| `Top10ShareHolders` | 十大股东 | `mcporter call jy-financedata-api.Top10ShareHolders query="600570"` |
| `InstitutionInvestor` | 机构投资者持仓 | `mcporter call jy-financedata-api.InstitutionInvestor query="600570"` |
| `IndexDailyQuote` | 指数日行情 | `mcporter call jy-financedata-api.IndexDailyQuote query="000001"` |
| `StockQuoteTechIndex` | 股票技术分析 | `mcporter call jy-financedata-api.StockQuoteTechIndex query="600570"` |
| `FinancialStatement` | 财务报表 | `mcporter call jy-financedata-api.FinancialStatement query="600570"` |
| `ConsensusExpectation` | 一致预期 | `mcporter call jy-financedata-api.ConsensusExpectation query="600570"` |
| `CompanyBasicInfo` | 公司简介 | `mcporter call jy-financedata-api.CompanyBasicInfo query="600570"` |
| `StockDailyQuote` | 股票日行情 | `mcporter call jy-financedata-api.StockDailyQuote query="600570"` |

---

## ⚠️ 强制执行流程（每次执行前必读）

**执行本技能前，必须按顺序完成以下步骤，不可跳过！**

### 步骤 0：完整阅读技能文件（强制）

1. **阅读主技能文件**：`SKILL.md`（本文档）
2. **阅读所有 references 文件**（按顺序）：
   - `references/data-validation.md` — 数据核验清单
   - `references/report-template.md` — 报告模板格式
   - `references/mcp-tools.md` — MCP 工具详细说明
   - `references/analysis-framework.md` — 分析框架详解

3. **确认理解以下关键点**：
   - [ ] 实时行情必须二次核验
   - [ ] 表格数据必须无错行错列，合计正确
   - [ ] 机构评级数量合计必须等于覆盖机构总数
   - [ ] 目标价逻辑：最高价≥平均价≥中位数≥最低价
   - [ ] 报告格式必须严格按照 template 执行
   - [ ] 免责声明不可省略

**未完成上述阅读和确认，不得执行后续分析步骤！**

---

## 核心工作流程

### 步骤 1：识别股票代码

从用户输入提取股票名称或代码，无法确定时询问用户。

### 步骤 2：执行五大模块分析（并发调用）

| 模块 | 关键工具 |
|------|----------|
| 实时行情 | `AShareLiveQuote`（二次核验） |
| 公司经营 | `MainOperIncData`, `FinQuery`, `StockValueAnalysis` |
| 行业动态 | `StockBelongIndustry`, `IndustryIndexLiveQuote` |
| 概念热点 | `StockBelongConcept`, `InstitutionalRating`, `ConsensusExpectationDetail` |
| 行情分析 | `AStockCashFlow`, `StockRangeQuotation`, `StockQuoteTechIndex` |

### 步骤 3：数据核验（强制）

**实时行情二次核验**：
- 两次调用 `AShareLiveQuote` 必须一致
- 验证：涨跌幅 = (最新价 - 昨收)/昨收×100%
- 验证：市值 = 最新价×总股本

**表格核验**：无错行错列，合计正确，占比和=100%

详见 [references/data-validation.md](references/data-validation.md)。

### 步骤 4：生成分析报告（严格按模板执行）

**报告必须包含以下模块，不可省略**：

1. **实时行情表** — 数据已二次核验标注
2. **公司经营** — 主营构成 + 财务指标趋势（最近 5 期）
3. **行业动态** — 行业分类 + 产业链分析
4. **概念热点** — 概念板块 + 机构评级 + 盈利预测 + 目标价 + 研报观点
5. **行情分析** — 估值分析 + 资金流向 + 技术分析
6. **综合分析** — 核心优势 + 主要风险 + 总结
7. **免责声明** — 必须包含，不可省略

**格式要求**：
- 所有表格必须无错行错列
- 合计/总计项必须计算正确
- 占比之和必须为 100%（容差<0.1%）
- 金额单位统一为亿元
- 百分比变动标注 pct

详见 [references/report-template.md](references/report-template.md)。

### 步骤 5：最终核验（发布前必做）

**发布报告前，必须完成以下核验清单**：

- [ ] 实时行情二次核验通过
- [ ] 所有表格无错行错列
- [ ] 合计/总计项计算正确
- [ ] 占比之和为 100%
- [ ] 机构数量合计正确
- [ ] 目标价逻辑正确（最高≥平均≥中位数≥最低）
- [ ] 上涨空间计算准确
- [ ] 免责声明已包含
- [ ] 数据基准日已标注

**任何一项未通过，必须修正后重新核验**！

---

## 快速开始

**⚠️ 再次提醒：执行前已完整阅读 SKILL.md 和所有 references 文件**？

- [ ] 已阅读 `SKILL.md`
- [ ] 已阅读 `references/data-validation.md`
- [ ] 已阅读 `references/report-template.md`
- [ ] 已阅读 `references/mcp-tools.md`
- [ ] 已阅读 `references/analysis-framework.md`

### 工具调用命令（所有入参均为 query）

```bash
# 实时行情（二次核验）
mcporter call jy-financedata-api.AShareLiveQuote query="股票代码"
mcporter call jy-financedata-api.AShareLiveQuote query="股票代码"

# 公司经营
mcporter call jy-financedata-api.MainOperIncData query="股票代码"         # 主营构成
mcporter call jy-financedata-tool.FinQuery query="股票名称 营收 净利润 ROE"  # 财务查询
mcporter call jy-financedata-api.StockValueAnalysis query="股票代码"      # 价值分析

# 行业动态
mcporter call jy-financedata-api.StockBelongIndustry query="股票代码"     # 行业分类
mcporter call jy-financedata-api.IndustryIndexLiveQuote query="行业代码"  # 行业指数

# 概念热点
mcporter call jy-financedata-api.StockBelongConcept query="股票代码"          # 概念板块
mcporter call jy-financedata-api.InstitutionalRating query="股票代码"         # 机构评级
mcporter call jy-financedata-api.ConsensusExpectationDetail query="股票代码"  # 一致预期

# 行情分析
mcporter call jy-financedata-api.AStockCashFlow query="股票代码"         # 资金流向
mcporter call jy-financedata-api.StockRangeQuotation query="股票代码"    # 区间行情
mcporter call jy-financedata-api.StockQuoteTechIndex query="股票代码"    # 技术分析

# 研报观点
mcporter call jy-financedata-tool.FinancialResearchReport query="股票代码"    # 研报摘要
mcporter call jy-financedata-api.CorporateResearchViewpoints query="股票代码" # 研究观点
mcporter call jy-financedata-api.NewsPublicOpinionList query="股票代码"       # 新闻舆情
```

### 数据获取策略

1. **并发调用**：五大模块尽量并发执行
2. **实时行情优先**：先核验基础数据
3. **按需调用**：根据用户关注点调整
4. **失败重试**：单个失败重试 1-2 次

---

## 资源清单

```
skills/jy-stock-analysis/
├── SKILL.md
├── references/
│   ├── execution-checklist.md  # 执行清单（强制执行）
│   ├── data-validation.md      # 数据核验清单
│   ├── report-template.md      # 报告模板
│   ├── mcp-tools.md            # 工具说明
│   └── analysis-framework.md   # 分析框架
└── .learnings/                 # 运行日志（可选，用于记录执行历史）
```

**重要**：每次执行前必须阅读 `references/execution-checklist.md`，按步骤逐项完成！

---

## 输出格式要求

- 财务表格：最近 5 期数据，含同比变化
- 金额单位：亿元；百分比变动：pct
- 机构评级：机构总数、各评级数量/占比、最新日期
- 目标价：最高/最低/平均/中位数、上涨空间
- 研报观点：至少 3-5 篇，日期倒序

---

## 注意事项

1. **数据时效**：行情实时/T+1，财务为最新报告期
2. **行业分类**：使用申万行业分类
3. **估值选择**：高 PE 行业用 PE，低 PB 行业用 PB
4. **免责声明**：必备，不可省略
5. **预测标注**：明确预测截止日期和最新评级日期
6. **强制阅读**：每次执行前必须完整阅读 SKILL.md 和所有 references 文件
7. **数据核验**：必须完成步骤 5 的最终核验清单才能发布报告

## 执行检查清单（每次执行必做）

**执行前确认**：
- [ ] 已完整阅读 SKILL.md
- [ ] 已完整阅读 references/data-validation.md
- [ ] 已完整阅读 references/report-template.md
- [ ] 已完整阅读 references/mcp-tools.md
- [ ] 已完整阅读 references/analysis-framework.md
- [ ] 理解数据核验要求
- [ ] 理解报告格式要求

**执行中确认**：
- [ ] 实时行情已二次核验
- [ ] 表格数据已核验（无错行错列）
- [ ] 合计/总计项已验算
- [ ] 占比之和为 100%

**发布前确认**：
- [ ] 完成步骤 5 最终核验清单
- [ ] 免责声明已包含
- [ ] 数据基准日已标注

---

## 限制

1. **市场限制**：仅支持 A 股，港股/美股需其他工具
2. **行情**：非交易时段为最近收盘价
3. **财务**：最新已披露报告期
4. **投资建议**：不提供买卖建议
5. **API 频率**：注意调用频率限制

---

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| mcporter 不存在 | 未安装 | `npm install -g mcporter` |
| 服务未找到 | 未配置 | `mcporter list` 检查后配置 |
| KEY 无效 | 过期/错误 | 重新申请 |
| 数据为空 | 代码错误/停牌 | 确认代码正确 |
| 调用超时 | 网络/限流 | 稍后重试 |
| 工具不存在 | 服务配置错误 | 检查 MCP 服务配置是否正确 |

**检查清单**：
- [ ] mcporter 已安装
- [ ] 两个 MCP 服务已配置
- [ ] JY_API_KEY 有效
- [ ] OpenClaw 已重启
- [ ] 股票代码正确（6 位数字）
- [ ] 工具调用路径正确

---

## 版本历史

### V1.0.0 (2026-04-01)
- 初始版本发布
- 基于恒生聚源金融数据库 (MCP) 提供全面的个股分析功能
- 覆盖实时行情、公司经营、行业动态、概念热点、行情分析五大模块
- 强制数据核验机制：实时行情二次核验、表格结构核验、逻辑一致性检查
- 标准化报告模板：7 大模块 + 免责声明
- 完整执行清单：执行前/执行中/发布前三阶段确认
