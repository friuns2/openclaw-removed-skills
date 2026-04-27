# PortfolioIndicatorQuery - 组合指标查询工具

## 功能描述

查询模拟组合的业绩、风险、收益等指标数据。

## 服务器

`jy-financedata-api`

## 调用格式

```bash
mcporter call jy-financedata-api.PortfolioIndicatorQuery query='<自然语言描述>'
```

## 输入参数

**`query`** (string, 必需) - 自然语言描述

| 信息 | 说明 | 示例 |
|------|------|------|
| 组合 ID | 完整的 32 位十六进制组合 ID | `0439d6e585034f46846d0a70b5a967e0` |

## 调用示例

### 查询绩效指标

```bash
mcporter call jy-financedata-api.PortfolioIndicatorQuery query='查询组合 0439d6e585034f46846d0a70b5a967e0 的绩效指标'
```

### 返回结果

```json
{
  "code": 0,
  "results": [{
    "api_name": "组合指标查询",
    "origin_data": {
      "nlpcolumnname": {
        "totalAssets": "总资产",
        "netAssets": "净资产",
        "nv": "净值",
        "dailyProfitRate": "日收益率 (%)",
        "totalReturn": "总收益率 (%)",
        "maxRetreat": "最大回撤 (%)",
        "toNowSharpe": "夏普比率",
        "weekReturn": "组合本周回报率 (%)",
        "monthReturn": "组合本月回报率 (%)",
        "yearReturn": "组合本年回报率 (%)",
        "tonowReReturn": "累计超额收益率 (%)"
      },
      "rows": [{
        "totalAssets": 968224.59,
        "netAssets": 968224.59,
        "nv": 0.96822459,
        "dailyProfitRate": -3.177541,
        "totalReturn": -3.177541,
        "maxRetreat": 3.177541,
        "toNowSharpe": -9.64306403,
        "weekReturn": -3.177541,
        "monthReturn": -3.177541,
        "yearReturn": -3.177541,
        "tonowReReturn": 0.894759
      }]
    }
  }]
}
```

## 输出表格

### 核心指标

| 指标名称 | 数值 | 说明 |
|----------|------|------|
| 总资产 | 968,224.59 | 元 |
| 净资产 | 968,224.59 | 元 |
| 净值 | 0.968 | - |
| 总收益率 | -3.18% | 建仓至今 |
| 最大回撤 | 3.18% | 历史最大 |
| 夏普比率 | -9.64 | 风险调整后收益 |
| 超额收益 | 0.89% | 相对基准 |

### 周期收益

| 指标 | 数值 |
|------|------|
| 本周收益 | -3.18% |
| 本月收益 | -3.18% |
| 本年收益 | -3.18% |

## 字段说明

| 字段 | 说明 |
|------|------|
| `totalAssets` | 总资产 |
| `netAssets` | 净资产 |
| `nv` | 净值 |
| `dailyProfitRate` | 日收益率 (%) |
| `totalReturn` | 总收益率 (%) |
| `maxRetreat` | 最大回撤 (%) |
| `toNowSharpe` | 夏普比率 |
| `weekReturn` | 本周回报率 (%) |
| `monthReturn` | 本月回报率 (%) |
| `yearReturn` | 本年回报率 (%) |
| `tonowReReturn` | 累计超额收益率 (%) |

## 注意事项

1. **串行执行**：此工具**不得**与 PortfolioBuild 或 PortfolioRebalance 并行执行
2. **执行时机**：应在建仓或调仓完成后**串行**执行
3. **数据完整性**：输出必须包含所有可用指标，不得删减

## 错误处理

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| 组合 ID 不存在 | 组合 ID 错误 | 检查组合 ID 格式 |
| 数据不足 | 组合交易历史太短 | 某些指标需要足够的历史数据才能计算 |
