# Meta（Facebook）账户 — 周期分析报告（模板纲要）

> 统计区间：`{startDate}` ~ `{endDate}`  
> 账户：`{mediaCustomerId}`（`{mediaCustomerName}`）

当前 TSO 侧 **Meta** 与 MarkAI `useAnalysisAction/api/meta.js` 对齐的拉数入口仅为 **账户总览**；系列/关键词/地域等维度若后端后续开放，可再扩展子命令并补全下列章节。

---

## 1. 执行摘要

- 总消耗、余额（若有）、活跃天数、日均消耗、优化得分（接口若为 0–1，展示时 ×100 与前端一致）
- 本期 / 上期：展示、点击、消耗、转化、CTR、CVR、CPC、CPA
- **CLI**：`siluzan-tso report meta-overview -a <mediaCustomerId> [--start YYYY-MM-DD --end YYYY-MM-DD]`
- **HTTP（TSO）**：`GET {tsoApiBaseUrl}/reporting/media-account/MetaAd/{mediaCustomerId}/OverviewSectionData?startDate=&endDate=`

## 2. 深度分析（占位）

- 待后端提供与 TikTok/Google 同结构的 `CampaignSectionData`、`DeviceSectionData` 等路径后，在此补充章节与对应 CLI。

## 3. 附录

- 原始 JSON：`report meta-overview -a <id> --start … --end … --json`
- 拉取时间、环境（`config show` 中 `tsoApiBaseUrl`）

---

### 与 steward「优化报告」的区别

- `report list/create`：TSO **steward** 优化报告（邮件/网页成品报告流）。
- `report meta-overview`：**实时分析总览** JSON，用于 Agent 拼 Markdown 报告或巡检，与 `google-analysis overview` 角色类似，但走 **TSO API** 且路径含 **`MetaAd`** 媒体段。
