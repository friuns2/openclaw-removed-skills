# 各媒体开户：接口与参数技术细节

> 业务流程（步骤、所需资料、审核处理）见 `references/workflows.md` 流程一。  
> 本文件仅记录各媒体的底层接口路径与请求体结构，供排查问题或深度定制时参考。

---

## 路由对照

| 媒体       | 前端路由（path）                  | 说明                                                                                             |
| ---------- | --------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Google** | `/openAnAccount?mediaType=Google` | 与 TikTok 共用 `openAnAccount.vue`；从开户记录进入 Google 时往往先弹 **GGwarn** 合规提示再进表单 |
| **TikTok** | `/openAnAccount?mediaType=TikTok` | 同上组件，`mediaType` 区分字段与提交流程                                                         |
| **Yandex** | `/YandexOpenAnAccount`            | 独立页面 `YandexOpenAnAccount_v2.vue`                                                            |
| **BingV2** | `/bingOpenAnAccount`              | 独立页面 `bingOpenAnAccount.vue`                                                                 |
| **Kwai**   | `/KwaiOpenAnAccount`              | 独立页面 `KwaiOpenAnAccount.vue`                                                                 |

---

## 广告主组（magKey）接口

所有媒体在提交开户前都需要一个广告主组，并取得 `magKey`（MediaAccountGroupId）：

- **查询列表**：`GET {apiBaseUrl}/query/profile/steward-individual` → `profile.mediaAccountGroups[]`，项上 `key` 即 magKey
- **创建**：`PUT {apiBaseUrl}/command/profile/steward-individual`，Header `s-command-type: AddMediaAccountGroup`
- **更新**：`PUT {apiBaseUrl}/command/profile/steward-individual/{id}`，Header `s-command-type: UpdateMediaAccountGroup`

**所有媒体均无需手动查询 magKey**：CLI 对每个媒体都会按 `--company`（或 `--advertiser-name` / `--company-name`）自动查找同名广告主组——存在则更新，不存在则创建——再用拿到的 magKey 提交开户。`--advertiser-id` 在所有开户命令中均为可选，仅供调试时手动指定。

---

## 各媒体提交接口

| CLI 子命令            | 提交接口                                   | Method | 关键 Header / 特点                                                                                                     |
| --------------------- | ------------------------------------------ | ------ | ---------------------------------------------------------------------------------------------------------------------- |
| `open-account google` | `/command/media-account/google`            | POST   | `s-command-type: AddExistingMediaAccountList`；前置自动创建广告主组                                                    |
| `open-account tiktok` | `/command/media-account`（不是 `/google`） | POST   | 同上；前置 `POST .../tiktok/Upload` 上传执照图片；可选 `POST .../command/attachment` 存档、`GET .../CheckUnionpayInfo` |
| `open-account yandex` | `/command/media-account/AddAgencyClient`   | POST   | Body：`MediaAccountGroupId` + `AgencyClientInfo`（登录名、税号、电话等）                                               |
| `open-account bing`   | `/command/media-account/AddBingV2Account`  | POST   | Body：`BingCustomerInfo` / `BingV2AccountInfo` + 执照 `FileId`；前置 `POST .../command/attachment`                     |
| `open-account kwai`   | `/command/media-account/AddKwaiAccount`    | POST   | Body：Kwai 专用主体/行业/执照结构 + `blobstoreKey`；前置 `POST .../KwaiAccount/Management/Upload`                      |

---

## 辅助接口

| 用途              | 接口                                                                                                                | CLI 命令                         |
| ----------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Google 时区列表   | `GET {apiBaseUrl}/query/media-account/Google/TimeZoneInfo/ReadFile`                                                 | `open-account google-timezones`  |
| TikTok 时区列表   | `GET {apiBaseUrl}/query/media-account/tiktok/TikTokTimeZoneInfo/Read`                                               | `open-account tiktok-timezones`  |
| TikTok 行业列表   | `GET {apiBaseUrl}/query/media-account/tiktok/TikTokIndustryInfo/Read`                                               | `open-account tiktok-industries` |
| TikTok 注册地列表 | `GET {apiBaseUrl}/query/media-account/tiktok/TikTokAreacode/Read`                                                   | `open-account tiktok-areas`      |
| Bing 行业列表     | `GET {apiBaseUrl}/query/media-account/bing/BingTradeList/Read`（返回中文行业名，`name` 字段即为 `--trade-id` 的值） | `open-account bing-industries`   |
| 修改 Google 申请  | `PUT .../command/media-account/google/{entityId}`，`s-command-type: UpdateMediaAccount`                             | —                                |
| 修改 TikTok 申请  | `PUT .../command/media-account/{entityId}`，`s-command-type: UpdateMediaAccount`                                    | —                                |
| 修改 Yandex 申请  | `POST .../command/media-account/UpdateAgencyClient/{id}`                                                            | —                                |

## 公司名称（广告主组）联想说明

网页上「公司名称」下拉的数据来自 `GET {apiBaseUrl}/query/profile/steward-individual`（与 `open-account list-groups` 同一接口），**无搜索接口，为本地过滤**。

选中已有广告主后，网页会自动回填推广链接、行业、推广类型等字段。CLI 的 `open-account google` 同样按 `--company` 名称自动匹配或创建广告主组，行为与网页一致。
