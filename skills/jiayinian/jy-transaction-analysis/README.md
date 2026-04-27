# jy-transaction-analysis Skill

A 股交易流水分析 Skill，基于恒生聚源 MCP 金融数据库生成专业的《交易片段行为速览》HTML 报告。

## 快速开始

### 1. 安装依赖

```bash
npm install -g mcporter
```

### 2. 申请 JY_API_KEY

向恒生聚源官方邮箱发送邮件申请：
- **邮箱**：datamap@gildata.com
- **标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名

### 3. 配置 MCP 服务

```bash
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### 4. 验证配置

```bash
mcporter list
```

## 使用示例

```
# 粘贴交易流水文本进行分析
交易日期  证券代码  证券名称  操作  成交数量  成交价格  成交金额
2026-03-20  600000  浦发银行  买入  10000  8.50  85000
2026-03-22  600000  浦发银行  卖出  10000  8.80  88000

# 或直接请求
帮我分析这段交易流水
看看我最近的交易表现
生成交易行为分析报告
```

## 文件结构

```
jy-transaction-analysis/
├── SKILL.md              # 主技能文件
├── README.md             # 说明文档
└── references/           # 参考资料
    ├── report-template.html    # HTML 报告模板
    ├── parse-rules.md          # 文本解析规则
    ├── analysis-rules.md       # 分析规则详解
    └── mcporter-config.md      # mcporter 配置说明
```

## 触发词

- 交易流水分析
- 分析我的交易
- 交易行为报告
- 交易表现评估
- 买卖记录分析

## 报告内容

1. **📋 数据解析概要** — 交易笔数、闭环交易、累计盈亏、胜率等
2. **📈 大盘背景** — 沪深 300 指数走势 + 市场阶段判断
3. **🔄 闭环交易识别** — 完整买卖闭环明细
4. **🔬 关键交易剖析** — 每笔关键交易的详细分析
5. **👤 用户行为画像** — 板块分布、持仓周期、关键发现
6. **💡 观察性总结** — 风险点 + 改进建议

## 注意事项

1. 首次使用前必须完成 mcporter 安装和 MCP 服务配置
2. JY_API_KEY 需妥善保管，不要泄露
3. 所有分析基于真实行情数据，不编造信息
4. 输出为 HTML 格式报告，支持桌面/手机浏览
5. 报告中的建议仅供参考，不构成投资建议

## 技术支持

- 恒生聚源：datamap@gildata.com
- Skill 下载：https://clawhub.ai/
