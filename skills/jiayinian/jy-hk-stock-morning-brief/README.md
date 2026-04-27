# jy-hk-stock-morning-brief

生成《港股资讯早报》—— 专业港股市场分析师角色，基于聚源数据 MCP 接口（通过 mcporter 调用）分析前一交易日市场动态。

## 快速开始

### 1. 安装 mcporter

```bash
npm install -g mcporter
```

### 2. 申请 JY_API_KEY

发送邮件至 `datamap@gildata.com` 申请聚源数据 API 密钥。

### 3. 配置 MCP 服务

```bash
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### 4. 使用技能

在 OpenClaw 中输入：
```
生成港股早报
```

## 文档

- [SKILL.md](SKILL.md) - 完整技能说明
- [references/hk-holidays.md](references/hk-holidays.md) - 港股假期日历
- [references/report-examples.md](references/report-examples.md) - 报告样例
- [references/api-mapping.md](references/api-mapping.md) - **API 映射与数据溯源指南**（新增）

## 脚本

- [scripts/fetch_hk_data.py](scripts/fetch_hk_data.py) - 数据获取脚本（mcporter 调用）
- [scripts/generate_pdf.py](scripts/generate_pdf.py) - PDF 生成脚本

## 数据溯源

生成的报告中每个数据项均标注具体 API 来源，例如：
- 指数行情 → `（来源：HKDailyIndexQuote）`
- 板块表现 → `（来源：SectorPerformance）`
- 券商研报 → `（来源：IndustryAnalysisViewpoints）`

详见 [references/api-mapping.md](references/api-mapping.md)。
