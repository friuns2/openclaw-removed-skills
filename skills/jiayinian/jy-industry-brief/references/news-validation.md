# 新闻核验清单与时效性验证

## 数据源优先级

### 优先顺序
1. **IndustryNewsFlash**（核心数据源）- MCP 行业快讯接口
2. **NewsPublicOpinionList** - MCP 新闻舆情
3. **FinancialResearchReport** - MCP 研究报告
4. **CorporateResearchViewpoints** - MCP 研报观点

### 调用策略
- 首先调用 `IndustryNewsFlash` 获取 24 小时行业快讯
- 如数据不足，调用 `NewsPublicOpinionList` 补充（多家公司聚合）
- 使用 `FinancialResearchReport` 获取备选简读素材
- 使用 `CorporateResearchViewpoints` 获取研报观点
- 合并去重后筛选最权威来源

### MCP 工具调用方式
```bash
mcporter call jy-financedata-api.IndustryNewsFlash query="行业名称"
mcporter call jy-financedata-api.NewsPublicOpinionList query="相关股票代码"
mcporter call jy-financedata-tool.FinancialResearchReport query="行业名称 行业分析"
mcporter call jy-financedata-api.CorporateResearchViewpoints query="行业名称"
```

## 时效性验证

### 24 小时新闻验证
- 所有"重要新闻信息"和"行业企业动态"必须为 24 小时内发布
- MCP 返回的数据应检查时间戳
- 如 MCP 未提供时间信息，需通过来源链接确认

### 备选简读素材验证
- 可放宽至 7 天内
- 优先选择深度分析、技术报告类内容
- 确保内容质量高于时效性

## 来源验证

### 可信来源优先级
1. **官方来源**（最高优先级）
   - 政府官网（发改委、工信部等）
   - 行业协会官网（中汽协、半导体协会等）
   - 上市公司公告

2. **权威媒体**（高优先级）
   - 新华社、人民日报
   - 财新、第一财经
   - 路透社、彭博社

3. **行业媒体**（中优先级）
   - 36 氪、虎嗅
   - 行业垂直媒体

4. **其他来源**（低优先级）
   - 自媒体、博客
   - 社交媒体

### 来源标注规范
- 只有一条来源时，来源后面**不要加逗号**
- 多条来源时，用顿号分隔
- 来源名称应简洁明了

## 去重验证

### 重复新闻判定
- 同一事件被多家媒体报道 → 选择最权威来源
- 同一新闻不同标题 → 选择信息量最大的版本
- 连续报道的同一事件 → 选择最新进展版本

### 去重流程
1. 提取新闻核心事件关键词
2. 对比各新闻的事件主体、时间、内容
3. 保留最完整、最权威的版本
4. 在报告中只呈现一次

## 内容质量验证

### 重要新闻信息
- 避免仅聚焦于单一公司的新闻报道
- 新闻量不少于 3 条
- 涵盖宏观、政策、行业整体动态

### 行业企业动态
- 着重展示公司具体行动和变化
- 包括新产品发布、战略合作、技术进展等
- 新闻量不少于 5 条

## 配置检查

- [ ] 已连接 MCP 聚源金融数据库
- [ ] `IndustryNewsFlash` 工具可用

## 核验清单

- [ ] 已调用 `IndustryNewsFlash` 获取行业快讯（必需）
- [ ] 数据不足时已调用 `NewsPublicOpinionList` 补充
- [ ] 所有新闻均为 24 小时内发布（备选简读素材可 7 天）
- [ ] 每条新闻都标注了来源
- [ ] 来源格式正确（单条来源无逗号）
- [ ] 无重复新闻
- [ ] 重要新闻信息不少于 3 条
- [ ] 行业企业动态不少于 5 条
- [ ] 每条信息都有序号标识（①②③...）
- [ ] 严格按用户指定行业检索，无无关新闻
