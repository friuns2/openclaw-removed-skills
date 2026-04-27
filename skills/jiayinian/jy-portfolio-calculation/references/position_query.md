# PortfolioPositionQuery - 成分券查询工具

## 功能描述

检索模拟组合在指定日期的持仓明细，包括证券代码、权重及市值等。

## 服务器

`jy-financedata-api`

## 调用格式

```bash
mcporter call jy-financedata-api.PortfolioPositionQuery query='<自然语言描述>'
```

## 输入参数

**`query`** (string, 必需) - 自然语言描述

| 信息 | 说明 | 示例 |
|------|------|------|
| 组合 ID | 完整的 32 位十六进制组合 ID | `0439d6e585034f46846d0a70b5a967e0` |

## 调用示例

### 查询全部成分券

```bash
mcporter call jy-financedata-api.PortfolioPositionQuery query='查询组合 0439d6e585034f46846d0a70b5a967e0 的持仓'
```

### 返回结果

```json
{
  "code": 0,
  "results": [{
    "api_name": "组合持仓查询",
    "origin_data": {
      "nlpcolumnname": {
        "secuCode": "证券代码",
        "secuName": "证券简称",
        "realPosition": "单券持仓权重 (%)",
        "quantity": "单券持仓数量",
        "price": "公允价值 (元)",
        "totalAssets": "单券持仓总市值 (元)",
        "costPrice": "单券成本单价 (元)",
        "costProfit": "单券持仓总成本 (元)"
      },
      "rows": [
        {
          "secuCode": "600519.SH",
          "secuName": "贵州茅台",
          "realPosition": 50.32,
          "quantity": 346,
          "price": 1408.07,
          "totalAssets": 487192.22,
          "costPrice": 1445,
          "costProfit": 499970
        },
        {
          "secuCode": "601318.SH",
          "secuName": "中国平安",
          "realPosition": 49.68,
          "quantity": 8369,
          "price": 57.47,
          "totalAssets": 480966.43,
          "costPrice": 59.74,
          "costProfit": 499964.06
        }
      ]
    }
  }]
}
```

## 输出表格

| 证券代码 | 证券简称 | 持仓数量 | 持仓权重 (%) | 公允价值 (元) | 持仓总市值 (元) | 成本单价 (元) | 持仓总成本 (元) |
|----------|----------|----------|--------------|---------------|-----------------|---------------|-----------------|
| 600519.SH | 贵州茅台 | 346 | 50.32 | 1408.07 | 487,192.22 | 1445 | 499,970 |
| 601318.SH | 中国平安 | 8369 | 49.68 | 57.47 | 480,966.43 | 59.74 | 499,964.06 |

## 字段说明

| 字段 | 说明 |
|------|------|
| `secuCode` | 证券代码 (带后缀，如 `.SH`) |
| `secuName` | 证券简称 |
| `realPosition` | 单券持仓权重 (%) |
| `quantity` | 单券持仓数量 |
| `price` | 公允价值 (元) |
| `totalAssets` | 单券持仓总市值 (元) |
| `costPrice` | 单券成本单价 (元) |
| `costProfit` | 单券持仓总成本 (元) |

## 注意事项

1. **串行执行**：此工具**不得**与 PortfolioBuild 或 PortfolioRebalance 并行执行
2. **执行时机**：应在建仓或调仓完成后**串行**执行
3. **数据完整性**：输出必须包含所有字段，不得删减

## 错误处理

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| 组合 ID 不存在 | 组合 ID 错误 | 检查组合 ID 格式 |
| 无持仓数据 | 组合尚未建仓 | 确认组合已完成建仓操作 |
