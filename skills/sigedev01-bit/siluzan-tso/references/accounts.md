# 账户管理命令详解

> 所属 skill：`siluzan-tso`。通用选项 `--token <token>` 可覆盖配置文件中的 Token（通常无需传，直接使用 `siluzan-tso login` 保存的配置）。

---

## list-accounts — 查询广告账户列表

```bash
siluzan-tso list-accounts [选项]
```

| 选项                    | 说明                                                                             |
| ----------------------- | -------------------------------------------------------------------------------- | ---------------------- |
| `-m, --media <type>`    | 媒体类型（留空查全部）：`Google \| TikTok \| Yandex \| MetaAd \| BingV2 \| Kwai` |
| `-k, --keyword <text>`  | 按账户名称或 ID 搜索                                                             |
| `-s, --status <status>` | 账户状态：`normal \| invalid \| all`（默认 all）                                 |
| `-p, --page <n>`        | 页码（默认 1）                                                                   |
| `--page-size <n>`       | 每页数量（默认 20）                                                              |
| `--json`                | 输出原始 JSON                                                                    |
| `--unicode`             | 表格使用 Unicode 线框；**默认**为 ASCII `+-                                      | ` 线框（兼容各类终端） |
| `--plain`               | 已默认 ASCII，无需再传；保留兼容旧脚本                                           |

**示例：**

```bash
# 查询所有 Google 账户
siluzan-tso list-accounts -m Google

# 关键字搜索
siluzan-tso list-accounts -k "品牌A"

# 只看正常状态，输出 JSON 供后续处理
siluzan-tso list-accounts -m TikTok -s normal --json

# 分页获取（第 2 页，每页 50 条）
siluzan-tso list-accounts --page 2 --page-size 50
```

**输出字段说明：**

| 字段              | 说明                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| `entityId`        | 丝路赞内部 ID，`delink`/`share`、**`account-active-bills`** 等操作使用此 ID（**不是** `mediaCustomerId`） |
| `mediaCustomerId` | 媒体平台账户数字 ID（Google Customer ID 等）                                                              |
| `name`            | 账户名称                                                                                                  |
| `status`          | 账户状态                                                                                                  |

---

## account-active-bills — 账户激活充值账单明细

查询指定广告账户在平台上的**激活/充值类账单**（与网页账户管理侧一致）。对应 TSO：

`GET {apiBaseUrl}/AccountActiveBills/{Media}/{entityId}`

路径末尾的 **`entityId`** 必须为 **`list-accounts --json`** 返回的账户 **`entityId`**（UUID 形态），**不能**传 `mediaCustomerId` 数字 ID。请求会带 **Datapermission**（与浏览器一致）。

```bash
siluzan-tso account-active-bills -m <媒体> --id <entityId> [--json]
```

| 选项                 | 说明                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| `-m, --media <type>` | 必填：`Google \| TikTok \| Yandex \| MetaAd \| BingV2 \| Kwai`（与路径中媒体段一致） |
| `--id <entityId>`    | 必填：账户 `entityId`                                                                |
| `--json`             | 输出接口原始 JSON                                                                    |

**响应体常用字段（以后端为准）：**

| 字段                                              | 说明                                                                                              |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `totalRU`                                         | 汇总相关数值（如示例中的 2.95）                                                                   |
| `totalResultCount`                                | 账单条数                                                                                          |
| `results[]`                                       | 账单列表                                                                                          |
| `results[].state`                                 | 如 `PaymentSuccessful`                                                                            |
| `results[].billNo` / `payNo` / `checkingNo`       | 账单号、支付单号、对账号                                                                          |
| `results[].data`                                  | 明细：`amounts`、`rechargeAmounts`、`payType`（如 `Wallet`）、`currencyCode`、`mediaAccountId` 等 |
| `results[].beforeAmounts` / `afterAmounts`        | 变动前后余额相关                                                                                  |
| `results[].mediaCustomerId` / `mediaCustomerName` | 媒体侧账户 ID 与名称                                                                              |
| `results[].invoiceState`                          | 如 `Pending`                                                                                      |
| `results[].createdDateTime`                       | 创建时间                                                                                          |

**示例：**

```bash
# 从列表取 entityId
siluzan-tso list-accounts -m Google --json

# 查询该账户激活账单（将下方 UUID 换成实际 entityId）
siluzan-tso account-active-bills -m Google --id 18176820-6204-43c2-9a1f-0d0f5e9eb957

# 原始 JSON，便于脚本解析
siluzan-tso account-active-bills -m Google --id 18176820-6204-43c2-9a1f-0d0f5e9eb957 --json
```

> **勿在文档或聊天中粘贴真实 JWT。** CI 环境基址为 `https://tso-api-ci.siluzan.com`，生产为 `https://tso-api.siluzan.com`（由 `config` / 构建环境决定）。

---

## balance — 查询实时余额

```bash
siluzan-tso balance -m <媒体类型> -a <账户ID列表>
```

| 选项                   | 说明                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `-m, --media <type>`   | 媒体类型（必填）                                                                     |
| `-a, --accounts <ids>` | 账户 `mediaCustomerId`（数字 ID），多个用逗号分隔（必填）。**注意：不是 `entityId`** |
| `--json`               | 输出原始 JSON                                                                        |

**示例：**

```bash
# 查询单个 Google 账户余额（传 mediaCustomerId）
siluzan-tso balance -m Google -a 6326027735

# 查询多个 TikTok 账户余额
siluzan-tso balance -m TikTok -a 1234567890,9876543210

# JSON 输出，供脚本使用
siluzan-tso balance -m Google -a 6326027735 --json
```

---

## stats — 查询投放消耗数据

```bash
siluzan-tso stats -m <媒体类型> [选项]
```

| 选项                   | 说明                                                                          | 默认   |
| ---------------------- | ----------------------------------------------------------------------------- | ------ |
| `-m, --media <type>`   | 媒体类型（必填）                                                              | —      |
| `-a, --accounts <ids>` | 账户 `mediaCustomerId`（数字 ID），逗号分隔（**必填**，接口不支持查全部账户） | —      |
| `--start <YYYY-MM-DD>` | 开始日期                                                                      | 7 天前 |
| `--end <YYYY-MM-DD>`   | 结束日期                                                                      | 昨天   |
| `--json`               | 输出原始 JSON                                                                 | —      |

**示例：**

```bash
# 查询 Google 账户最近 7 天消耗
siluzan-tso stats -m Google -a 6326027735

# 查询 Google 指定月份消耗
siluzan-tso stats -m Google -a 6326027735 --start 2026-03-01 --end 2026-03-31

# 查询多个 Bing 账户消耗
siluzan-tso stats -m BingV2 -a 1234567890,9876543210 --start 2026-03-01

# JSON 输出
siluzan-tso stats -m Google -a 6326027735 --json
```

---

## account-history — 开户申请历史

```bash
siluzan-tso account-history [选项]
```

| 选项                     | 说明                                             |
| ------------------------ | ------------------------------------------------ |
| `-m, --media <type>`     | 媒体类型                                         |
| `-s, --status <status>`  | 申请状态（如 `Approved \| Rejected \| Pending`） |
| `-k, --keyword <text>`   | 账户名/ID 关键字                                 |
| `--start / --end <date>` | 申请日期范围（YYYY-MM-DD）                       |
| `--json`                 | 输出原始 JSON                                    |

**示例：**

```bash
# 查询所有 Google 开户申请
siluzan-tso account-history -m Google

# 查询已审批通过的申请
siluzan-tso account-history --status Approved

# 查询本月申请，JSON 输出
siluzan-tso account-history --start 2026-03-01 --end 2026-03-31 --json
```

**审核状态处理：**

| 状态       | 含义     | 下一步操作                                                                                                                                  |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `Pending`  | 审核中   | 等待，可反复运行此命令轮询；审核周期因媒体而异                                                                                              |
| `Approved` | 审核通过 | 运行 `list-accounts -m <媒体>` 确认账户已出现；引导用户充值激活（`config show` 取 `webUrl`，打开 `{webUrl}/v3/foreign_trade/tso/recharge`） |
| `Rejected` | 被拒     | 查看 `--json` 输出中的 `reason` 字段了解拒绝原因；修改资料后重新提交；若原因不明，引导用户联系丝路赞客服                                    |

---

## account — 账号管理（OAuth 授权 / 解除关联 / Google MCC / 分享）

> 与网页 **`/foreign_trade/tso/manageAccounts`** 对应：`account auth` = 添加授权；`account delink` = 解除授权（从丝路赞解绑账户）；`mcc-bind` / `mcc-unbind` = MCC 绑定与解绑。

### auth — 添加媒体平台 OAuth 授权

在浏览器中打开对应媒体的 OAuth 授权页面，授权后账户自动绑定到丝路赞。

```bash
siluzan-tso account auth -m <媒体类型>
```

| 选项                 | 说明                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| `-m, --media <type>` | 媒体类型（必填）：`Google \| TikTok \| Meta \| Yandex \| BingV2 \| Kwai` |

**示例：**

```bash
# 授权 Google Ads 账户
siluzan-tso account auth -m Google

# 授权 TikTok Ads 账户
siluzan-tso account auth -m TikTok

# 授权 Meta（Facebook）Ads 账户
siluzan-tso account auth -m Meta
```

> CLI 会自动在系统默认浏览器中打开授权页；无法打开时输出 URL 供手动粘贴。授权完成后会跳回丝路赞，账户立即生效。

---

### delink — 解除授权 / 断开账户关联

从当前丝路赞账号下移除媒体账户绑定（网页上常称为「解除授权」或「解绑」）。

```bash
siluzan-tso account delink --id <entityId>
siluzan-tso account delink --ids <id1,id2,id3>
```

| 选项              | 说明                            |
| ----------------- | ------------------------------- |
| `--id <entityId>` | 断开单个账户（使用 `entityId`） |
| `--ids <id1,id2>` | 批量断开多个账户（逗号分隔）    |

**示例：**

```bash
# 断开单个账户
siluzan-tso account delink --id abc123def456

# 批量断开
siluzan-tso account delink --ids abc123,def456,ghi789
```

> `entityId` 来自 `list-accounts --json` 结果中的 `ma.entityId` 字段，**不是** `mediaCustomerId`。

---

### mcc-bind — Google MCC 绑定

将 **子账户**（Google `mediaCustomerId`）挂到指定 **经理账户（MCC）** 下。请求走 **`googleApiUrl`**（与网页一致），需先 `config show` 确认已配置。

```bash
siluzan-tso account mcc-bind --customers <mediaCustomerId> --mcc <MCC客户ID>
siluzan-tso account mcc-bind --customers 111,222 --mcc "333;444"
```

| 选项                | 说明                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------- |
| `--customers <ids>` | 子账户 `mediaCustomerId`，多个逗号分隔（来自 `list-accounts` 的 `ma.mediaCustomerId`） |
| `--mcc <ids>`       | MCC 的客户 ID；多个可用英文逗号、中文逗号、分号、顿号等分隔（与网页输入规则一致）      |
| `--json`            | 输出每个子账户接口的原始返回，便于排查                                                 |

---

### mcc-unbind — Google MCC 解绑

将子账户从指定 MCC 下解除关联，参数含义与 `mcc-bind` 相同。

```bash
siluzan-tso account mcc-unbind --customers <mediaCustomerId> --mcc <MCC客户ID>
```

---

### share — 分享 Google 账户

将 Google 广告账户分享给指定手机号用户（手机号必须已在丝路赞注册）。

```bash
siluzan-tso account share --id <entityId> --phone <手机号>
```

**示例：**

```bash
siluzan-tso account share --id abc123def456 --phone 13800138000
```

---

### unshare — 取消账号分享

```bash
siluzan-tso account unshare --id <entityId> --account-id <userId>
```

| 选项                    | 说明                |
| ----------------------- | ------------------- |
| `--id <entityId>`       | 账户 entityId       |
| `--account-id <userId>` | 被取消分享的用户 ID |

**示例：**

```bash
siluzan-tso account unshare --id abc123def456 --account-id user789
```

---

### share-detail — 查看账号分享详情

```bash
siluzan-tso account share-detail --customer-id <mediaCustomerId>
```

> `--customer-id` 传入的是 `mediaCustomerId`（数字型媒体平台账户 ID），不是 `entityId`。

**示例：**

```bash
siluzan-tso account share-detail --customer-id 1234567890
```

---

## open-account — 开户申请

> **Google 与网页 `/openAnAccount` 的对照**（五步进度、两步表单、币种/时区下拉）：见 **`references/open-account-google-ui.md`**。  
> **各媒体路由、资料、提交接口都不相同**（不只 Google 用 `/openAnAccount`）：见 **`references/open-account-by-media.md`**。

### 广告主组 magKey 说明

**所有媒体（Google / TikTok / Yandex / BingV2 / Kwai）开户均无需手动查询或填写 magKey。**

CLI 与网页行为完全一致：提交时按 `--company`（或 `--advertiser-name` / `--company-name`）在后台自动查找同名广告主组——存在则更新，不存在则创建——再用拿到的 magKey 提交开户。

`--advertiser-id` 在所有媒体开户命令中均为**可选**，仅供调试或特殊场景手动指定。

> `open-account list-groups` 仍可使用，用于查看已有广告主组或排查问题。

---

### Google 开户（无需图片）

**更贴近网页交互：**

```bash
# 交互向导（说明「五步」进度条 + 按网页第 1、2 步顺序提问；需真实终端 TTY）
siluzan-tso open-account google-wizard

# 时区列表（与网页第二步「时区」下拉同一接口，可加 --keyword 过滤）
siluzan-tso open-account google-timezones
siluzan-tso open-account google-timezones --keyword Hong
```

**非交互（脚本 / Agent）：**

```bash
siluzan-tso open-account google \
  --account-name "品牌A美国推广账户" \
  --currency USD \
  --timezone "America/New_York" \
  --invite-email "marketing@brand-a.com" \
  --company "Brand A Inc." \
  --promotion-link "https://www.brand-a.com" \
  --promotion-type b2c
```

> 推广链接可只写域名（如 `www.brand-a.com`），CLI 会自动补 `https://`。  
> 可选：`--industry1` / `--industry2`（网页端行业已弱化，多数情况可不填）。  
> 可选：`--advertiser-id <magKey>` 仅用于调试或必须指定已有组时。

| 选项                        | 说明                                                  | 必填 |
| --------------------------- | ----------------------------------------------------- | ---- |
| `--advertiser-id`           | 广告主组 magKey（**一般不用**，CLI 按公司名自动处理） |      |
| `--account-name`            | 账户名称（≤22字符）                                   | ✅   |
| `--currency`                | 货币：`USD \| CNY`                                    | ✅   |
| `--timezone`                | 时区，如 `Asia/Hong_Kong` / `America/New_York`        | ✅   |
| `--invite-email`            | 受邀邮箱                                              | ✅   |
| `--company`                 | 公司名称（用于匹配/创建广告主组）                     | ✅   |
| `--industry1 / --industry2` | 行业一/二级（可选）                                   |      |
| `--promotion-link`          | 推广链接                                              | ✅   |
| `--promotion-type`          | `b2b \| b2c \| app`                                   | ✅   |
| `--invite-role`             | `Standard \| Admin`（默认 Standard）                  |      |
| `--counts`                  | 开户数量 1-3（默认 1）                                |      |

---

### TikTok 开户辅助查询

开户前，行业 ID、注册地代码、时区代码都有专用查询命令：

```bash
# 注册地代码（--registered-area 的合法值，如 CN / US / SG 等）
siluzan-tso open-account tiktok-areas --keyword China

# 行业列表（两级结构，--industry-id 传叶子节点 ID）
siluzan-tso open-account tiktok-industries --keyword "电商"

# 时区列表（--timezone 的合法值，如 Asia/Shanghai）
siluzan-tso open-account tiktok-timezones --keyword Shanghai
```

> **行业 ID 说明**：`tiktok-industries` 输出中，`▸` 开头为一级分类（不可提交），缩进的子行业为叶子节点，`--industry-id` 传括号内数字。

### TikTok 开户（需要营业执照图片）

```bash
siluzan-tso open-account tiktok \
  --company "Brand A Inc." \
  --account-name "品牌A TikTok账户" \
  --currency USD \
  --timezone "Asia/Shanghai" \
  --industry-id <tiktok-industries 输出的叶子节点 ID> \
  --registered-area CN \
  --promotion-link "https://www.brand-a.com" \
  --license-no "91440300XXXXXXXXXX" \
  --license-file "/path/to/business-license.jpg"
```

> CLI 自动完成：① 上传图片到 TikTok 取得 `license_image_id`；② 存档到丝路赞；③ 按公司名自动创建/关联广告主组；④ 检查是否需要法人银联验证。  
> **注意**：`--company` 和 `--license-no` 需用户手动填写；网页上传执照图片有 OCR 自动识别，CLI 无此功能。

**需要法人银联验证时追加：**

```bash
  --representative-name "张三" \
  --representative-id "440300XXXXXXXXXXXXXXXXX" \
  --unionpay-account "6222XXXXXXXXXXXX" \
  --representative-phone "13800138000"
```

---

### Yandex 开户（无需图片）

```bash
siluzan-tso open-account yandex \
  --company "Brand A Inc." \
  --login "yandex_login_name" \
  --first-name "San" \
  --last-name "Zhang" \
  --email "zs@company.com" \
  --tin "7712345678" \
  --phone "+8613800138000"
```

> **TIN 说明**：税号为普通文本，直接填写纳税人识别号（INN）即可，提交时类型固定为 `FOREIGN_LEGAL`，无需额外选择。不会根据税号自动带出公司名等信息。

---

### Bing/BingV2 开户（需要营业执照图片）

```bash
# 前置：查询 Bing 行业名称（--trade-id 传返回的 name 字段值）
siluzan-tso open-account bing-industries --keyword "科技"

siluzan-tso open-account bing \
  --advertiser-name "深圳XX科技有限公司" \
  --name-short "XX科技" \
  --province "广东省" \
  --city "深圳市" \
  --address "南山区科技园XX路XX号XX大厦" \
  --promotion-link "https://www.brand-a.com" \
  --trade-id "IT/消费电子-其他" \
  --license-file "/path/to/license.jpg"
```

---

### Kwai 开户（需要营业执照图片）

```bash
siluzan-tso open-account kwai \
  --company-name "深圳XX科技有限公司" \
  --licence-id "91440300XXXXXXXXXX" \
  --licence-country CN \
  --licence-location "广东省深圳市南山区科技园XX路XX号" \
  --business-scope "电商零售" \
  --product "品牌A" \
  --ad-type 1 \
  --product-url "https://www.brand-a.com" \
  --licence-id-type ENTERPRISE \
  --account-name "品牌A Kwai账户" \
  --company-name "深圳XX科技有限公司" \
  --industry-id1 "1234" \
  --industry-id2 "5678" \
  --expire-type 2 \
  --target-country US \
  --license-file "/path/to/license.jpg"
```

| 选项               | 说明                                                        |
| ------------------ | ----------------------------------------------------------- |
| `--ad-type`        | `1`=效果广告，`2`=品牌广告                                  |
| `--expire-type`    | `1`=有限期（追加 `--expire-at <毫秒时间戳>`），`2`=长期有效 |
| `--target-country` | 投放目标国家/地区（ISO 代码，如 `US \| GB \| DE`）          |

---

## account close — TikTok 关闭账户

> 仅支持 **TikTok** 账户。关闭后账户停止投放，如需恢复请联系丝路赞客服，操作**不可自助撤销**，谨慎使用。
>
> 对应网页：`/foreign_trade/tso/manageAccounts` → 选中 TikTok 账户 → 关闭账户
>
> **实现说明（与网页 `manageAccounts` 一致）**：先请求 TikTok 网关 `CheckAdvDisable`（不满足条件如余额未清零会失败），再 `POST .../AdvertiserDisable`；Body 为各账户的 **entityId**。你只需传入 `list-accounts` 中的 **mediaCustomerId**，CLI 会解析 entityId；旧版误把 mediaCustomerId 当 Body 会导致 HTTP 成功但关户不生效。

```bash
siluzan-tso account close --accounts <mediaCustomerId>
siluzan-tso account close --accounts <id1,id2,id3>
```

| 选项               | 说明                                                                          |
| ------------------ | ----------------------------------------------------------------------------- |
| `--accounts <ids>` | TikTok 账户 `mediaCustomerId`，多个逗号分隔（来自 `list-accounts -m TikTok`） |
| `--json`           | 输出原始 JSON                                                                 |

**示例：**

```bash
# 先查出要关闭的 TikTok 账户 mediaCustomerId
siluzan-tso list-accounts -m TikTok --json

# 关闭单个账户
siluzan-tso account close --accounts 1234567890123456

# 批量关闭多个账户
siluzan-tso account close --accounts 1234567890123456,9876543210654321
```

---

## account bm-bind — Meta BM 绑定

> 将 Meta 广告账户绑定到指定的 **Business Manager（商务管理平台）**。
>
> 对应网页：`/foreign_trade/tso/manageAccounts` → 选中 Meta 账户 → BM 绑定

```bash
siluzan-tso account bm-bind --account-id <mediaCustomerId> --bm-id <bmId>
```

| 选项                   | 说明                                                              | 必填 |
| ---------------------- | ----------------------------------------------------------------- | ---- |
| `--account-id <id>`    | Meta 广告账户 `mediaCustomerId`（来自 `list-accounts -m MetaAd`） | ✅   |
| `--bm-id <id>`         | Business Manager ID                                               | ✅   |
| `--action-type <type>` | 操作类型（默认 `bind`）                                           |      |
| `--json`               | 输出原始 JSON                                                     |      |

**示例：**

```bash
# 先查出 Meta 账户 mediaCustomerId
siluzan-tso list-accounts --json

# 将账户绑定到指定 BM
siluzan-tso account bm-bind --account-id 123456789012345 --bm-id 987654321098765
```

---

## account withdraw-list / withdraw-submit — Google 被封账户提现

> **仅支持 Google 账户**，其他媒体平台无此功能。
>
> 适用场景：Google 广告账户因违反政策被封禁（`Suspended`），账户内仍有余额，需申请提现退回丝路赞钱包。
>
> **注意**：`list-accounts` 列表中显示的"账户状态"是丝路赞平台侧的 OAuth 授权状态，与 Google 封号无关。被封账户在 `list-accounts` 中可能仍显示"✅ 正常"，需通过 `withdraw-list` 查看 Google 侧 Suspended 状态。

### withdraw-list — 查询可提现的被封账户

```bash
siluzan-tso account withdraw-list [选项]
```

| 选项        | 说明             |
| ----------- | ---------------- |
| `--json`    | 输出原始 JSON    |
| `--verbose` | 显示详细错误信息 |

输出包含：`entityId`（提现时使用）、`mediaCustomerId`、账户名称、**Google状态**（Suspended）、余额、赠送金、货币、是否可提现。

```bash
siluzan-tso account withdraw-list
```

> 余额净额 ≤ 0（余额 ≤ 赠送金）的账户无法提现，会在"可提现"列标注 ❌。

---

### withdraw-submit — 提交提现申请

```bash
siluzan-tso account withdraw-submit --accounts <entityId,...>
```

| 选项               | 说明                                                   | 必填 |
| ------------------ | ------------------------------------------------------ | ---- |
| `--accounts <ids>` | 账户 `entityId`，逗号分隔（来自 `withdraw-list` 输出） | ✅   |
| `--json`           | 输出原始 JSON                                          |      |
| `--verbose`        | 显示详细错误信息                                       |      |

**完整流程示例：**

```bash
# 第一步：查看被封账户列表，确认哪些账户有余额可提现
siluzan-tso account withdraw-list

# 第二步：复制有余额账户的 entityId，提交提现申请
siluzan-tso account withdraw-submit --accounts f2a5ca16-cff9-4a9e-9aea-f7429c3e2696

# 批量提现多个账户
siluzan-tso account withdraw-submit --accounts id1,id2,id3
```

> CLI 自动完成：① 查询各账户余额与货币；② 按 `mediaType=Google` + 货币 + 金额查询管理费率；③ 计算实际扣款金额（含税）；④ 批量提交申请。审核完成后金额退回丝路赞钱包。

---

## account bc-bind — TikTok BC 绑定

> 将 TikTok 广告账户绑定到 **Business Center（BC，商务中心）**。
>
> 对应网页：`/foreign_trade/tso/manageAccounts` → 选中 TikTok 账户 → BC 绑定

```bash
siluzan-tso account bc-bind --customers <mediaCustomerId> --bc-ids <bcId>
```

| 选项                | 说明                                                                              | 必填 |
| ------------------- | --------------------------------------------------------------------------------- | ---- |
| `--customers <ids>` | TikTok 广告账户 `mediaCustomerId`，多个逗号分隔（来自 `list-accounts -m TikTok`） | ✅   |
| `--bc-ids <ids>`    | Business Center ID，多个逗号分隔                                                  | ✅   |
| `--json`            | 输出原始 JSON                                                                     |      |

**示例：**

```bash
# 第一步：查出 TikTok 账户的 mediaCustomerId
siluzan-tso list-accounts -m TikTok

# 第二步：执行绑定
siluzan-tso account bc-bind --customers 6967198846787059714 --bc-ids 7322757300404633602
```

---

## account bc-unbind — TikTok BC 解绑

> 将 TikTok 广告账户从 Business Center 下解绑。注意每次只能解绑一个 BC。

```bash
siluzan-tso account bc-unbind --customers <mediaCustomerId> --bc-id <bcId>
```

| 选项                | 说明                                            | 必填 |
| ------------------- | ----------------------------------------------- | ---- |
| `--customers <ids>` | TikTok 广告账户 `mediaCustomerId`，多个逗号分隔 | ✅   |
| `--bc-id <id>`      | Business Center ID（一次只能解绑一个 BC）       | ✅   |
| `--json`            | 输出原始 JSON                                   |      |

**示例：**

```bash
siluzan-tso account bc-unbind --customers 6967198846787059714 --bc-id 7322757300404633602
```

---

## account email-auth-list — Google 邮箱授权列表

> 查询已向指定 Google 广告账户发出的邮箱访问权限邀请。

```bash
siluzan-tso account email-auth-list -c <mediaCustomerId> [--agent-type <type>]
```

| 选项                     | 说明                                                                       |
| ------------------------ | -------------------------------------------------------------------------- |
| `-c, --customer-id <id>` | Google 广告账户 `mediaCustomerId`（与网页查询参数 `customerId` 一致）      |
| `--agent-type <type>`    | 可选；网关需要时再传（与 `list-accounts --json` 的 `ma.accountType` 一致） |
| `--json`                 | 输出原始 JSON                                                              |

---

## account email-auth — Google 邮箱授权邀请

> 向指定邮箱发送 Google 广告账户访问权限邀请。

```bash
siluzan-tso account email-auth -c <mediaCustomerId> --email <email> [--access-role ReadOnly|Standard]
```

| 选项                     | 说明                                                | 必填 |
| ------------------------ | --------------------------------------------------- | ---- |
| `-c, --customer-id <id>` | Google 广告账户 `mediaCustomerId`                   | ✅   |
| `--email <email>`        | 被授权用户邮箱                                      | ✅   |
| `--agent-type <type>`    | 账户代理类型（来自 `list-accounts --json`）         |      |
| `--access-role <role>`   | 权限类型：`ReadOnly \| Standard`（默认 `Standard`） |      |

**示例：**

```bash
# 授予标准权限
siluzan-tso account email-auth -c 4656789737 --email user@gmail.com

# 授予只读权限
siluzan-tso account email-auth -c 4656789737 --email user@gmail.com --access-role ReadOnly
```

---

## account email-deauth — Google 解除邮箱授权

> 撤销已发出的邮箱授权邀请。先用 `email-auth-list --json` 获取 `invitationId` 和 `resourceName`。

```bash
siluzan-tso account email-deauth -c <mediaCustomerId> --invitation-id <id> --resource-name <name>
```

| 选项                     | 说明                                                             |
| ------------------------ | ---------------------------------------------------------------- |
| `-c, --customer-id <id>` | Google 广告账户 `mediaCustomerId`                                |
| `--invitation-id <id>`   | 邀请 ID（来自 `email-auth-list`）                                |
| `--resource-name <name>` | 资源名称（来自 `email-auth-list --json` 的 `resourceName` 字段） |
| `--agent-type <type>`    | 账户代理类型                                                     |
| `--pending`              | 邀请尚未被接受时加此参数                                         |

---

## 仅限网页的账户管理操作

以下操作涉及图形交互（OAuth 跳转、充值页面等），**当前 CLI 不支持**，需引导用户打开浏览器完成：

| 功能                                    | 媒体   | 网页路径                                       |
| --------------------------------------- | ------ | ---------------------------------------------- |
| **账户激活**（邀请他人激活 / 充值激活） | Google | `{webUrl}/v3/foreign_trade/tso/manageAccounts` |

**Agent 建议话术**：

```bash
# 获取网页基地址
siluzan-tso config show   # 查看 webUrl 字段

# 账户激活（Google）→ 引导至账户管理页
# {webUrl}/v3/foreign_trade/tso/manageAccounts
```
