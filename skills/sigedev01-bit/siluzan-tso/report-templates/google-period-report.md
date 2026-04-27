# Google 账户分析报告

> 统计区间：`{startDate}` ~ `{endDate}`  
> 账户：`{mediaCustomerId}`

---

## 默认报告维度

生成报告时，**默认包含**以下 8 个维度：

| #   | 维度                                                 | CLI                                 |
| --- | ---------------------------------------------------- | ----------------------------------- |
| 1   | 执行摘要（消耗/展示/点击/转化/CTR/CPC/CPA 本期概览） | `google-analysis overview`          |
| 2   | 每日投放趋势（按日消耗/点击/转化曲线）               | `google-analysis daily-metrics`     |
| 3   | 月度汇总（全周期汇总数据）                           | `google-analysis dimension-summary` |
| 4   | 广告系列表现（预算/出价策略/各系列消耗与效果）       | `google-analysis campaigns`         |
| 5   | 设备分布（PC/移动/平板 消耗/点击/转化）              | `google-analysis devices`           |
| 6   | 地域分布（国家/地区 消耗占比）                       | `google-analysis geographic`        |
| 7   | 关键词表现（词/消耗/CTR/CPC 排行）                   | `google-analysis keywords`          |
| 8   | 优化建议（根据以上数据给出可执行改进建议）           | 不额外拉数，基于已有数据撰写        |

**在执行任何数据拉取之前**，先向用户展示以下可选维度，询问是否需要追加：

---

## 平台支持的全部可选维度

| 维度          | CLI                                  | 备注                                 |
| ------------- | ------------------------------------ | ------------------------------------ |
| 受众分布      | `google-analysis audience`           | 可分 `SystemDefined` / `UserDefined` |
| 搜索词报告    | `google-analysis search-terms`       | 高消耗搜索词与关键词匹配关系         |
| 广告创意表现  | `google-analysis ads`                | 广告标题/类型/到达网址               |
| 附加信息      | `google-analysis extensions`         | 附加链接/电话/宣传信息等状态         |
| 图片/视频素材 | `google-analysis materials`          | 图片 + 视频合并视图                  |
| 账户落地页    | `google-analysis final-urls`         | 主投放域名/落地页（不传日期）        |
| 黄金账户评分  | `google-analysis gold-account`       | 健康度评分与各项达标状态             |
| 广告质量指标  | `google-analysis ads-index`          | 质量得分汇总                         |
| 转化动作配置  | `google-analysis conversion-actions` | 已配置的转化目标列表                 |
| 账户结构统计  | `google-analysis resource-counts`    | 系列/组/广告/词数量                  |
| 广告系列类型  | `google-analysis campaign-types`     | 系列类型分布（不传日期）             |

---

## 拉数顺序（默认 8 个维度）

```bash
siluzan-tso google-analysis overview          -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis daily-metrics     -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis dimension-summary -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis campaigns         -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis devices           -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis geographic        -a <id> --start <s> --end <e> --json
siluzan-tso google-analysis keywords          -a <id> --start <s> --end <e> --json
```
