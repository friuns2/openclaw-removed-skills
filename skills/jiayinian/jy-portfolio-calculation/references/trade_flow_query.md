# TradeFlowQuery - 交易流水查询工具

## 功能描述

查询模拟组合在指定区间内的交易流水明细。

## 服务器

`jy-financedata-api`

## 调用格式

```bash
mcporter call jy-financedata-api.TradeFlowQuery query='<自然语言描述>'
```

## 输入参数

**`query`** (string, 必需) - 自然语言描述

| 信息 | 说明 | 示例 |
|------|------|------|
| 组合 ID | 完整的 32 位十六进制组合 ID | `0439d6e585034f46846d0a70b5a967e0` |

## 调用示例

### 查询全部交易流水

```bash
mcporter call jy-financedata-api.TradeFlowQuery query='查询组合 0439d6e585034f46846d0a70b5a967e0 的交易流水'
```

### 返回结果

```json
{
  "code": 0,
  "results": [{
    "api_name": "交易流水查询",
    "origin_data": {
      "nlpcolumnname": {
        "transactionDate": "交易日期",
        "secuCode": "证券代码",
        "secuName": "证券名称",
        "transactionTypeDesc": "变动类型",
        "changeQuantity": "变动数量",
        "transactionPrice": "变动价格 (元)",
        "changeAmount": "结算金额 (元)"
      },
      "rows": [
        {
          "transactionDate": "2026-03-20",
          "secuCode": "600519.SH",
          "secuName": "贵州茅台",
          "transactionTypeDesc": "买入",
          "changeQuantity": 346,
          "transactionPrice": 1445,
          "changeAmount": -499970
        },
        {
          "transactionDate": "2026-03-20",
          "secuCode": "601318.SH",
          "secuName": "中国平安",
          "transactionTypeDesc": "买入",
          "changeQuantity": 8369,
          "transactionPrice": 59.74,
          "changeAmount": -499964.06
        }
      ]
    }
  }]
}
```

## 输出表格

| 交易日期 | 证券代码 | 证券名称 | 变动类型 | 变动数量 | 变动价格 (元) | 结算金额 (元) |
|----------|----------|----------|----------|----------|---------------|---------------|
| 2026-03-20 | 600519.SH | 贵州茅台 | 买入 | 346 | 1445 | -499,970 |
| 2026-03-20 | 601318.SH | 中国平安 | 买入 | 8369 | 59.74 | -499,964.06 |

## 字段说明

| 字段 | 说明 |
|------|------|
| `transactionDate` | 交易日期 |
| `secuCode` | 证券代码 |
| `secuName` | 证券名称 |
| `transactionTypeDesc` | 变动类型 (买入/卖出/分红/配股/送股等) |
| `changeQuantity` | 变动数量 |
| `transactionPrice` | 变动价格 (元) |
| `changeAmount` | 结算金额 (元) |

## 注意事项

1. **串行执行**：此工具**不得**与 PortfolioBuild 或 PortfolioRebalance 并行执行
2. **执行时机**：应在建仓或调仓完成后**串行**执行
3. **数据完整性**：输出必须包含所有交易记录，不得删减

## 错误处理

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| 组合 ID 不存在 | 组合 ID 错误 | 检查组合 ID 格式 |
| 无交易记录 | 组合尚未交易 | 确认组合已完成建仓操作 |
