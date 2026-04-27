# TikTok 广告主账户 — 周期分析报告（模板纲要）

> 统计区间：`{startDate}` ~ `{endDate}`  
> 账户：`{mediaCustomerId}`（`{mediaCustomerName}`）

与 TSO **`reporting/media-account/TikTok/{mediaCustomerId}/...`** 及周期报告常见数据块对齐：总览、广告层级（系列 / 组 / 广告）、素材视频、受众（含性别/年龄/兴趣合并块）、地域与设备可分别从广告/受众维度接口归纳（**以实际 JSON 字段为准**）。

---

## 1. 执行摘要（总览）

- 账户级消耗、展示、点击、转化、CTR、CPC 等（接口返回结构因版本可能略有差异）
- **CLI**：`siluzan-tso report tiktok-overview -a <mediaCustomerId> [--start YYYY-MM-DD --end YYYY-MM-DD] [--json]`
- **HTTP**：`GET {tsoApiBaseUrl}/reporting/media-account/TikTok/{id}/OverviewSectionData?startDate=&endDate=`

## 2. 广告结构（系列 / 广告组 / 广告）

- 系列：`report tiktok-campaigns` → `CampaignSectionData`（Query：`startDate`、`endDate`、`take`，默认 `take=100`）
- 广告组：`report tiktok-ad-groups` → `AdGroupReport`
- 广告：`report tiktok-ads` → `AdReport`

## 3. 素材与创意（视频）

- **CLI**：`siluzan-tso report tiktok-videos -a <id> [--start … --end …] [--take N] [--json]`
- **HTTP**：`.../VideoReport?startDate=&endDate=&take=`

## 4. 受众分析

- 单维度：`report tiktok-audience -a <id> -d <dimension> [--take N] [--json]`  
  可选 `dimension`：`gender` | `age` | `interest_category` | `country_code` | `platform` | `language`
- **HTTP**：`.../AudienceReport?startDate=&endDate=&take=&dimensions=<dim>`
- 周期报告中常与网页一致的三块合并：`report tiktok-audience-merged`（**固定输出合并 JSON**，含 `gender` / `age` / `interest_category` 三次响应）

## 5. 地域 / 兴趣辅助数据

- 地区代码枚举：`report tiktok-areacode` → `GET {mainApiUrl}/query/media-account/tiktok/TikTokAreacode/Read`（解析地域报表、对照名称时使用）
- 兴趣类目树：`report tiktok-interest-list -a <id>` → 需配置 **`tiktokApiUrl`**（`GetInterestList?mediaCustomerId=`）

## 6. 附录

- 日期规则：`--start` / `--end` **同传或同省略**；省略时默认**近 7 天（截至昨天）**，与 `report meta-overview`、`google-analysis` 一致。
- 鉴权：与 TSO 其他接口相同（`config show` 中 `tsoApiBaseUrl` / Token）。
- 与 steward「优化报告」区别：见 `meta-period-report.md` 末节说明；`report list/create` 为成品报告流，本模板对应**实时分析 JSON**。

---

### CLI 速查表

| 数据块                 | 子命令                          |
| ---------------------- | ------------------------------- |
| 总览                   | `report tiktok-overview`        |
| 系列                   | `report tiktok-campaigns`       |
| 广告组                 | `report tiktok-ad-groups`       |
| 广告                   | `report tiktok-ads`             |
| 视频素材               | `report tiktok-videos`          |
| 受众（单维）           | `report tiktok-audience -d …`   |
| 受众（性别+年龄+兴趣） | `report tiktok-audience-merged` |
| 地区码                 | `report tiktok-areacode`        |
| 兴趣列表               | `report tiktok-interest-list`   |
