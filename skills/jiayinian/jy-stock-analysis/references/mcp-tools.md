# MCP 工具详细说明

---

## 实时行情类

### AShareLiveQuote
- **功能**：获取 A 股实时行情数据
- **参数**：`query`（股票代码，6 位数字）
- **返回**：最新价、涨跌幅、成交量、市值等
- **使用注意**：必须进行二次核验调用
- **调用示例**：`mcporter call jy-financedata-api.AShareLiveQuote query="600570"`

### IndustryIndexLiveQuote
- **功能**：获取行业指数实时行情
- **参数**：`query`（行业代码）
- **返回**：行业指数涨跌幅、成交量等
- **调用示例**：`mcporter call jy-financedata-api.IndustryIndexLiveQuote query="SW801010"`

### ConceptIndexLiveQuote
- **功能**：获取概念指数实时行情
- **参数**：`query`（概念代码）
- **返回**：概念指数涨跌幅
- **调用示例**：`mcporter call jy-financedata-api.ConceptIndexLiveQuote query="CN001"`

### IndexDailyQuote
- **功能**：获取大盘指数日行情
- **参数**：`query`（指数代码）
- **返回**：指数涨跌幅、成交量等
- **调用示例**：`mcporter call jy-financedata-api.IndexDailyQuote query="000001"`

### StockDailyQuote
- **功能**：获取股票日行情
- **参数**：`query`（股票代码）
- **返回**：开盘价、收盘价、最高价、最低价、涨跌幅、成交量、成交额
- **调用示例**：`mcporter call jy-financedata-api.StockDailyQuote query="600570"`

---

## 公司经营类

### MainOperIncData
- **功能**：获取主营构成数据
- **参数**：`query`（股票代码）
- **返回**：各业务板块收入及占比（最近 5 期）
- **调用示例**：`mcporter call jy-financedata-api.MainOperIncData query="600570"`

### StockValueAnalysis
- **功能**：股票价值分析
- **参数**：`query`（股票代码）
- **返回**：ROE、毛利率、净利率、PE、PB 等
- **调用示例**：`mcporter call jy-financedata-api.StockValueAnalysis query="600570"`

### FinancialDataComparison
- **功能**：同行业财务数据对比
- **参数**：`query`（股票代码）
- **返回**：同行业可比公司财务指标
- **调用示例**：`mcporter call jy-financedata-api.FinancialDataComparison query="600570"`

### FinancialStatement
- **功能**：获取上市公司历史财务报表
- **参数**：`query`（股票代码）
- **返回**：资产负债表、利润表、现金流量表
- **调用示例**：`mcporter call jy-financedata-api.FinancialStatement query="600570"`

### PerformanceExpress
- **功能**：获取业绩快报数据
- **参数**：`query`（股票代码）
- **返回**：最新报告期业绩快报
- **调用示例**：`mcporter call jy-financedata-api.PerformanceExpress query="600570"`

### PerformanceForecast
- **功能**：获取业绩预告
- **参数**：`query`（股票代码）
- **返回**：净利润预期、增速等
- **调用示例**：`mcporter call jy-financedata-api.PerformanceForecast query="600570"`

### CompanyBasicInfo
- **功能**：查询上市公司基本资料
- **参数**：`query`（股票代码）
- **返回**：注册信息、行业、概念、简介等
- **调用示例**：`mcporter call jy-financedata-api.CompanyBasicInfo query="600570"`

---

## 金融问数

### FinQuery
- **功能**：通过自然语言查询金融数据
- **参数**：`query`（自然语言查询语句）
- **示例**：`query="宁德时代 2025 年营收 净利润 ROE 毛利率"`
- **返回**：查询结果数据
- **调用示例**：`mcporter call jy-financedata-tool.FinQuery query="宁德时代 2025 年营收 净利润 ROE 毛利率"`

### MacroIndustryData
- **功能**：宏观行业经济数据
- **参数**：`query`（自然语言查询）
- **返回**：宏观经济与行业经济指标数据
- **调用示例**：`mcporter call jy-financedata-tool.MacroIndustryData query="中国 GDP 增速"`

---

## 行业与概念类

### StockBelongIndustry
- **功能**：获取公司所属行业分类
- **参数**：`query`（股票代码）
- **返回**：申万/中信行业分类信息
- **调用示例**：`mcporter call jy-financedata-api.StockBelongIndustry query="600570"`

### StockBelongConcept
- **功能**：获取股票所属概念板块
- **参数**：`query`（股票代码）
- **返回**：概念板块列表
- **调用示例**：`mcporter call jy-financedata-api.StockBelongConcept query="600570"`

### ConceptConstituentStocks
- **功能**：获取概念板块成分股列表
- **参数**：`query`（概念代码）
- **返回**：成分股列表及对应证券代码
- **调用示例**：`mcporter call jy-financedata-api.ConceptConstituentStocks query="CN001"`

---

## 机构评级与预测类

### InstitutionalRating
- **功能**：获取机构评级汇总统计
- **参数**：`query`（股票代码）
- **返回**：评级机构总数、各评级数量分布
- **调用示例**：`mcporter call jy-financedata-api.InstitutionalRating query="600570"`

### ConsensusExpectationDetail
- **功能**：获取一致预期明细数据
- **参数**：`query`（股票代码）
- **返回**：分析师盈利预测及目标价统计
- **调用示例**：`mcporter call jy-financedata-api.ConsensusExpectationDetail query="600570"`

### ConsensusExpectation
- **功能**：获取一致预期
- **参数**：`query`（股票代码）
- **返回**：未来三年盈利预测数据
- **调用示例**：`mcporter call jy-financedata-api.ConsensusExpectation query="600570"`

---

## 研究观点与舆情类

### FinancialResearchReport
- **功能**：获取研究报告全文摘要
- **参数**：`query`（股票代码）
- **返回**：研报摘要信息
- **调用示例**：`mcporter call jy-financedata-tool.FinancialResearchReport query="600570"`

### CorporateResearchViewpoints
- **功能**：获取公司研究观点汇总
- **参数**：`query`（股票代码）
- **返回**：多篇研报的核心观点
- **调用示例**：`mcporter call jy-financedata-api.CorporateResearchViewpoints query="600570"`

### NewsPublicOpinionList
- **功能**：获取新闻舆情列表
- **参数**：`query`（股票代码）
- **返回**：近期相关新闻及舆情倾向
- **调用示例**：`mcporter call jy-financedata-api.NewsPublicOpinionList query="600570"`

---

## 资金流向类

### AStockCashFlow
- **功能**：获取个股资金流向
- **参数**：`query`（股票代码）
- **返回**：主力/散户净流入流出数据
- **调用示例**：`mcporter call jy-financedata-api.AStockCashFlow query="600570"`

### Top10ShareHolders
- **功能**：获取前十大股东持股信息
- **参数**：`query`（股票代码）
- **返回**：股东名称、持股数、占比等
- **调用示例**：`mcporter call jy-financedata-api.Top10ShareHolders query="600570"`

### Top10FloatShareHolders
- **功能**：获取前十大流通股股东持股信息
- **参数**：`query`（股票代码）
- **返回**：流通股股东名称、持股数、占比等
- **调用示例**：`mcporter call jy-financedata-api.Top10FloatShareHolders query="600570"`

### InstitutionInvestor
- **功能**：获取机构投资者持仓信息
- **参数**：`query`（股票代码）
- **返回**：基金、社保等机构持仓
- **调用示例**：`mcporter call jy-financedata-api.InstitutionInvestor query="600570"`

### RealStockFundFlow
- **功能**：获取个股实时资金流向
- **参数**：`query`（股票代码）
- **返回**：主力、散户资金净额
- **调用示例**：`mcporter call jy-financedata-api.RealStockFundFlow query="600570"`

---

## 技术分析类

### StockRangeQuotation
- **功能**：获取股票区间行情数据
- **参数**：`query`（股票代码）
- **返回**：历史价格走势数据
- **调用示例**：`mcporter call jy-financedata-api.StockRangeQuotation query="600570"`

### StockQuoteTechIndex
- **功能**：获取股票技术指标
- **参数**：`query`（股票代码）
- **返回**：MA、RSI、KDJ、BOLL、MACD 等
- **调用示例**：`mcporter call jy-financedata-api.StockQuoteTechIndex query="600570"`

### IndexRangeQuotation
- **功能**：获取指数区间行情
- **参数**：`query`（指数代码）
- **返回**：指数区间涨跌幅、成交额等
- **调用示例**：`mcporter call jy-financedata-api.IndexRangeQuotation query="000001"`

---

## 工具调用速查表

| 工具名 | 调用路径 | 备注 |
|--------|----------|------|
| FinQuery | jy-financedata-tool.FinQuery | 金融问数 |
| MacroIndustryData | jy-financedata-tool.MacroIndustryData | 宏观行业 |
| FinancialResearchReport | jy-financedata-tool.FinancialResearchReport | 研究报告 |
| FundMultipleFactorFilter | jy-financedata-tool.SmartFundSelection | 智能选基 |
| StockMultipleFactorFilter | jy-financedata-tool.SmartStockSelection | 智能选股 |
| AShareLiveQuote | jy-financedata-api.AShareLiveQuote | 实时行情 |
| MainOperIncData | jy-financedata-api.MainOperIncData | 主营构成 |
| StockValueAnalysis | jy-financedata-api.StockValueAnalysis | 价值分析 |
| StockBelongIndustry | jy-financedata-api.StockBelongIndustry | 行业分类 |
| StockBelongConcept | jy-financedata-api.StockBelongConcept | 概念板块 |
| InstitutionalRating | jy-financedata-api.InstitutionalRating | 机构评级 |
| ConsensusExpectationDetail | jy-financedata-api.ConsensusExpectationDetail | 一致预期明细 |
| PerformanceExpress | jy-financedata-api.PerformanceExpress | 业绩快报 |
| AStockCashFlow | jy-financedata-api.AStockCashFlow | 资金流向 |
| StockRangeQuotation | jy-financedata-api.StockRangeQuotation | 区间行情 |
| CorporateResearchViewpoints | jy-financedata-api.CorporateResearchViewpoints | 研究观点 |
| NewsPublicOpinionList | jy-financedata-api.NewsPublicOpinionList | 新闻舆情 |
| IndustryIndexLiveQuote | jy-financedata-api.IndustryIndexLiveQuote | 行业指数 |
| FinancialDataComparison | jy-financedata-api.FinancialDataComparison | 财务对比 |
| Top10ShareHolders | jy-financedata-api.Top10ShareHolders | 十大股东 |
| InstitutionInvestor | jy-financedata-api.InstitutionInvestor | 机构持仓 |
| IndexDailyQuote | jy-financedata-api.IndexDailyQuote | 指数日行情 |
| StockDailyQuote | jy-financedata-api.StockDailyQuote | 股票日行情 |
| FinancialStatement | jy-financedata-api.FinancialStatement | 财务报表 |
| ConsensusExpectation | jy-financedata-api.ConsensusExpectation | 一致预期 |
| CompanyBasicInfo | jy-financedata-api.CompanyBasicInfo | 公司简介 |
| PerformanceForecast | jy-financedata-api.PerformanceForecast | 业绩预告 |
| ConceptIndexLiveQuote | jy-financedata-api.ConceptIndexLiveQuote | 概念指数 |
| StockQuoteTechIndex | jy-financedata-api.StockQuoteTechIndex | 技术分析 |
| IndexRangeQuotation | jy-financedata-api.IndexRangeQuotation | 指数区间 |
| RealStockFundFlow | jy-financedata-api.RealStockFundFlow | 实时资金流 |
| Top10FloatShareHolders | jy-financedata-api.Top10FloatShareHolders | 十大流通股东 |
| ConceptConstituentStocks | jy-financedata-api.ConceptConstituentStocks | 概念成分股 |

---

## 调用注意事项

1. **参数格式**：所有工具入参均为 `query` 字符串
2. **股票代码**：使用 6 位数字代码（如 600570、300750）
3. **实时行情**：必须二次核验调用
4. **API 频率**：注意调用频率限制，避免触发限流
