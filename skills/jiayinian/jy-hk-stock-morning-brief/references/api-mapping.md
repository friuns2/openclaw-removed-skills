# API 映射与数据溯源指南

本文档列出《港股资讯早报》技能使用的所有聚源 MCP API 及其对应的报告章节，便于数据溯源标注。

---

## API 调用与报告章节映射

### 一、趋势展望

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 恒指/国指/科指行情 | `HKDailyIndexQuote` | `mcporter call gildata_datamap-sse.HKDailyIndexQuote query="恒生指数 2026-03-31 收盘价 涨跌幅"` | `（来源：HKDailyIndexQuote）` |
| 板块涨跌幅排行 | `SectorPerformance` / `FinancialDataAPI` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="港股板块 2026-03-31 涨跌幅排行"` | `（来源：SectorPerformance）` |
| 个股涨跌幅排行 | `StockRanking` / `FinancialDataAPI` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="港股个股 2026-03-31 涨跌幅 排行"` | `（来源：StockRanking）` |
| 指数分时走势 | `IndexTimeseries` | `mcporter call gildata_datamap-sse.IndexTimeseries query="恒生指数 2026-03-31 分时"` | `（来源：IndexTimeseries）` |

---

### 二、要闻点评

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 上市公司公告 | `HKStockAnnouncement` / `FinancialDataAPI` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="港股上市公司 2026-03-31 公告 财报"` | `（来源：HKStockAnnouncement）` |
| 市场重要新闻 | `MarketNews` / `FinancialDataAPI` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="港股市场 2026-03-31 重要新闻"` | `（来源：MarketNews）` |

---

### 三、数据追踪

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 南向资金流向 | `SouthboundFlow` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="南向资金 2026-03-31 净流入"` | `（来源：SouthboundFlow）` |
| 港股通活跃成交股 | `ActiveStocks` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="港股通十大活跃成交股 2026-03-31"` | `（来源：ActiveStocks）` |

**注意**：如 API 返回空结果，标注"（聚源 MCP 暂未覆盖，建议通过 hkex.com.hk 查询）"

---

### 四、行业全景

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 行业分析观点 | `IndustryAnalysisViewpoints` | `mcporter call gildata_datamap-sse.IndustryAnalysisViewpoints query="港股 行业分析 2026-03-31"` | `（来源：IndustryAnalysisViewpoints）` |
| 板块资金流向 | `IndustryConstituentStocks` | `mcporter call gildata_datamap-sse.IndustryConstituentStocks query="航空运输业 成分股"` | `（来源：IndustryConstituentStocks）` |

---

### 五、港股攻略

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 券商研报观点 | `CorporateResearchViewpoints` | `mcporter call gildata_datamap-sse.CorporateResearchViewpoints query="港股 券商研报 评级"` | `（来源：CorporateResearchViewpoints）` |
| 行业研报观点 | `IndustryAnalysisViewpoints` | `mcporter call gildata_datamap-sse.IndustryAnalysisViewpoints query="非银金融 行业分析"` | `（来源：IndustryAnalysisViewpoints）` |
| 机构评级 | `ConsensusExpectation` | `mcporter call gildata_datamap-sse.ConsensusExpectation query="腾讯控股 机构评级 目标价"` | `（来源：ConsensusExpectation）` |

---

### 六、环球视野

| 报告内容 | MCP API | mcporter 调用示例 | 标注格式 |
|----------|---------|------------------|----------|
| 美股行情 | `USStockDailyQuotes` | `mcporter call gildata_datamap-sse.USStockDailyQuotes query="纳斯达克 2026-03-31 收盘价"` | `（来源：USStockDailyQuotes）` |
| 欧股行情 | `GlobalMarkets` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="英国富时 100 2026-03-31"` | `（来源：GlobalMarkets）` |
| 亚太市场 | `HKStockDailyQuotes` / `GlobalMarkets` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="日经 225 2026-03-31"` | `（来源：GlobalMarkets）` |
| 经济数据日历 | `EconomicCalendar` | `mcporter call gildata_datamap-sse.FinancialDataAPI query="经济数据日历 2026-04-01"` | `（来源：EconomicCalendar）` |

---

## 数据标注规范

### 1. 表格数据标注

在表格下方统一标注：

```markdown
| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| 恒指 | 24788.14 | +37.35 | +0.15% |

*数据来源：HKDailyIndexQuote*
```

### 2. 文字描述标注

在段落末尾标注：

```markdown
航空运输业昨日领涨，涨幅达 2.87%（来源：SectorPerformance）。
```

### 3. 研报观点标注

包含机构、日期、来源：

```markdown
**华泰证券**（2026-01-04）：2025 年港股日均成交额同比 +89%（来源：IndustryAnalysisViewpoints）。
```

### 4. 暂缺数据标注

明确说明原因并提供替代方案：

```markdown
*数据暂缺（聚源 MCP 暂未覆盖，建议通过 hkex.com.hk 查询）*
```

---

## 聚源 MCP 覆盖范围

### ✅ 已覆盖

- 港股指数行情（恒指、国指、科指）
- 港股板块表现
- 港股个股排行
- 港股上市公司公告
- 券商研报观点
- 美股部分数据（个股、纳斯达克）
- 经济数据日历

### ⚠️ 暂不覆盖（2026-04 验证）

- 南向资金流向（港股通资金数据）
- 港股通十大活跃成交股
- 欧洲股市数据
- 道琼斯工业平均指数
- 标普 500 指数

---

## 常用查询语句模板

```bash
# 指数行情
mcporter call gildata_datamap-sse.HKDailyIndexQuote query="[指数名称] [日期] 收盘价 涨跌幅 成交量 成交额"

# 板块表现
mcporter call gildata_datamap-sse.FinancialDataAPI query="[日期] 港股板块 涨跌幅排行 前 10"

# 公司公告
mcporter call gildata_datamap-sse.FinancialDataAPI query="港股上市公司 [日期] 公告 财报 盈利预警"

# 券商研报
mcporter call gildata_datamap-sse.IndustryAnalysisViewpoints query="港股 [行业] 券商研报 行业分析 [日期]"

# 美股行情
mcporter call gildata_datamap-sse.USStockDailyQuotes query="[日期] 美股 [指数/股票] 收盘价 涨跌幅"
```

---

*文档更新：2026-04-01*
*验证环境：聚源 MCP (gildata_datamap-sse)*
