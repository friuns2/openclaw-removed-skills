# Google 账户 — 诊断类报告（模板纲要）

> 统计区间：`{startDate}` ~ `{endDate}`  
> 账户：`{mediaCustomerId}`（`{mediaCustomerName}`）

按章节组织结论与建议；各节所需数据与建议 CLI 如下（均支持 `--json`）。

---

## 1. 账户画像与落地页

- 主投放域名 / 落地页线索（若有）
- **CLI**：`google-analysis final-urls`（无日期参数）

## 2. 核心指标快照

- 本期消耗、展示、点击、转化、CTR、CVR、CPA 等
- **CLI**：`google-analysis overview`、`google-analysis dimension-summary`

## 3. 账户结构与转化目标

- 系列/组/广告等数量级（以接口返回为准）
- 已配置的转化动作列表摘要
- **CLI**：`google-analysis resource-counts`、`google-analysis conversion-actions`

## 4. 黄金账户与健康度

- 得分与各项是否达标（转化跟踪、GA、RSA、附加信息、否定词、受众、出价策略等）
- **CLI**：`google-analysis gold-account`

## 5. 广告系列类型与分布

- 各类型系列占比或列表摘要
- **CLI**：`google-analysis campaign-types`（无日期参数）

## 6. 重点维度对比（本期 vs 上期）

- 系列、地域、关键词：建议各拉两段时间分别对比（脚本层控制 `--start` / `--end`）
- **CLI**：`google-analysis campaigns`、`google-analysis geographic`、`google-analysis keywords`

## 7. 转化成本曲线

- 按日 CPA / 转化数趋势
- **CLI**：`google-analysis daily-metrics`

## 8. 设备、地域、受众（全量表）

- 设备、国家/地区、系统定义受众、自定义受众
- **CLI**：`google-analysis devices`、`google-analysis geographic`、`google-analysis audience`（`SystemDefined` / `UserDefined`）

## 9. 搜索词与广告创意

- 高消耗搜索词、与关键词匹配关系
- 高消耗搜索广告标题、类型、到达网址
- **CLI**：`google-analysis search-terms`、`google-analysis ads`

## 10. 附加信息与素材

- 附加链接/电话/宣传信息等状态与层级
- 图片 / 视频素材消耗（若需合并视图）
- **CLI**：`google-analysis extensions`（可选 `--level`）、`google-analysis materials` 或分别 `asset-images`、`videos`

## 11. 质量得分（汇总）

- **CLI**：`google-analysis ads-index`

## 12. 总结与行动项

- 优先修复项（健康度未达标项）
- 预算/出价/关键词/搜索词否词等可执行清单

---

### 并行拉取提示

诊断场景可在同一统计区间内并行执行多条 `google-analysis`（注意网关限流）；合并后再套入本模板各章节。
