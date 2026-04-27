# MCP 工具使用说明

## 服务配置

### 已配置服务

| 服务名称 | URL | 用途 |
|----------|-----|------|
| `jy-financedata-tool` | `https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=<JY_API_KEY>` | 研报查询、宏观数据查询 |
| `jy-financedata-api` | `https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=<JY_API_KEY>` | 金融数据查询、综合查询 |

## 工具调用方式

所有工具统一使用 `mcporter call` 命令调用，入参均为 `query`：

```bash
mcporter call <服务名>.<工具名> --query "<查询内容>"
```

## 可用工具列表

### jy-financedata-tool 服务

#### 1. FinancialResearchReport（研报查询）

**用途：** 获取券商研报观点和摘要

**调用示例：**
```bash
mcporter call jy-financedata-tool.FinancialResearchReport --query "资产配置 最新观点"
mcporter call jy-financedata-tool.FinancialResearchReport --query "宏观经济 2026 年 展望"
mcporter call jy-financedata-tool.FinancialResearchReport --query "股票策略 月度金股"
```

**返回数据：**
- 研报标题
- 发布机构
- 发布时间
- 核心观点
- 摘要内容

#### 2. MacroIndustryData（宏观数据查询）

**用途：** 获取宏观经济和行业数据

**调用示例：**
```bash
mcporter call jy-financedata-tool.MacroIndustryData --query "GDP CPI PMI 最新数据"
mcporter call jy-financedata-tool.MacroIndustryData --query "货币供应 M2 社融增量"
mcporter call jy-financedata-tool.MacroIndustryData --query "工业增加值 固定资产投资"
```

**返回数据：**
- 指标名称
- 最新值
- 前值
- 同比/环比
- 数据发布日期

### jy-financedata-api 服务

#### 3. FinQuery（金融数据查询）

**用途：** 获取金融市场价格和估值数据

**调用示例：**
```bash
mcporter call jy-financedata-api.FinQuery --query "沪深 300 估值 PE PB"
mcporter call jy-financedata-api.FinQuery --query "10 年期国债收益率"
mcporter call jy-financedata-api.FinQuery --query "原油 黄金 铜 价格"
```

**返回数据：**
- 标的名称
- 当前价格/估值
- 历史分位
- 涨跌幅

#### 4. FinGeneralQuery（综合查询）

**用途：** 综合金融数据查询

**调用示例：**
```bash
mcporter call jy-financedata-api.FinGeneralQuery --query "行业景气度 最新"
mcporter call jy-financedata-api.FinGeneralQuery --query "资金流向 主力资金"
mcporter call jy-financedata-api.FinGeneralQuery --query "融资融券 余额"
```

**返回数据：**
- 查询结果汇总
- 相关数据指标

## 查询技巧

### 1. 关键词组合

使用关键词组合提高查询精准度：

```bash
# 时间 + 主题
--query "2026 年 3 月 资产配置"

# 主题 + 类型
--query "宏观经济 研报观点"

# 指标 + 频率
--query "CPI 月度 最新"
```

### 2. 多轮查询

复杂需求可分多次查询：

```bash
# 第一次：获取研报
mcporter call jy-financedata-tool.FinancialResearchReport --query "资产配置 3 月"

# 第二次：获取宏观数据
mcporter call jy-financedata-tool.MacroIndustryData --query "GDP CPI PMI"

# 第三次：获取估值数据
mcporter call jy-financedata-api.FinQuery --query "股票 债券 估值"
```

### 3. 数据时效性

- 研报：建议查询近 3 个月数据
- 宏观数据：查询最新可用数据
- 市场价格：查询最新交易日数据

## 常见问题

### Q1: 查询返回空数据

**可能原因：**
- 查询关键词过于具体
- 数据源暂无相关数据

**解决方案：**
- 简化查询关键词
- 尝试同义词或相关词

### Q2: 查询超时

**可能原因：**
- 网络延迟
- 数据量较大

**解决方案：**
- 重试查询
- 简化查询条件

### Q3: 鉴权失败

**可能原因：**
- JY_API_KEY 无效或过期
- 服务配置错误

**解决方案：**
- 检查 JY_API_KEY 是否正确
- 重新配置 MCP 服务
- 联系恒生聚源确认 KEY 状态

## 数据标注规范

在报告中使用数据时，必须标注：

1. **数据来源：** 如"数据来源：恒生聚源 (gildata)"
2. **数据截止：** 如"数据截至 2026-03-31"
3. **发布时间：** 研报需标注发布时间

示例：
```
沪深 300 当前 PE 为 12.5 倍，处于历史 35% 分位（数据来源：恒生聚源，截至 2026-03-31）
```
