# TSO 业务流程（多命令组合）

> 本文件记录需要多个 `siluzan-tso` 命令**按顺序配合**才能完成的业务场景。
> 单命令用法见各子 Skill 文件；这里只记录"命令怎么串联起来用"。

---

## 流程一：新账户开通（Google / TikTok / Yandex / Bing / Kwai）

对应页面：`/accountOpeningHistory`

> **网页完整链接（微前端）**：`{webUrl}/v3/foreign_trade/tso/accountOpeningHistory?tso=%2Fv3umijs%2Ftso%2FaccountOpeningHistory`（与 CLI `account-history` 同源数据）。开户提交后若需用户在网页确认，应打开此「开户记录」页，**不要**误链到「媒体账户」`manageAccounts`。

### 业务背景

用户在丝路赞上还没有某媒体账户时，需要提交开户申请并跟踪审核进度。**各媒体所需资料和命令参数完全不同，不要混用。**

> **AI Agent 注意**：`open-account google-wizard` 需要真实 TTY，Agent 环境无法使用，始终用非交互命令。

---

### Google 开户

**所需信息**：公司名称、推广网址、推广类型（b2b/b2c/app）、账户名称、币种（CNY/USD）、时区、邀请邮箱（需 `.com` 结尾）

**常用时区速查**（完整列表：`siluzan-tso open-account google-timezones`）：

| 时区 Code             | 含义                           |
| --------------------- | ------------------------------ |
| `Asia/Shanghai`       | 北京/上海（选 CNY 时的默认值） |
| `Asia/Hong_Kong`      | 香港（选 USD 时的默认值）      |
| `America/New_York`    | 美东                           |
| `America/Los_Angeles` | 美西                           |
| `Europe/London`       | 伦敦                           |

```bash
# 第一步：提交开户申请（无需提前查 magKey，CLI 按公司名自动关联）
siluzan-tso open-account google \
  --company "Brand A Inc." \
  --promotion-link "https://www.brand-a.com" \
  --promotion-type b2c \
  --account-name "品牌A美国推广账户" \
  --currency USD \
  --timezone "America/New_York" \
  --invite-email "marketing@brand-a.com"

# 第二步：轮询审核进度
siluzan-tso account-history -m Google

# 第三步：审核通过后确认账户已出现
siluzan-tso list-accounts -m Google

# 第四步：充值激活（必须网页完成）
# siluzan-tso config show 取 webUrl，打开：{webUrl}/v3/foreign_trade/tso/recharge
# 美元账户最低约 100 USD，人民币账户约 700 CNY
```

---

### TikTok 开户

**所需信息**：营业执照图片本地路径、执照编号、公司名、注册地代码、行业 ID（叶子节点）、推广链接、账户名称、币种、时区

> **执照 OCR 提示**：网页上传执照图片后系统会自动 OCR 识别公司名称和社会信用代码。CLI 不做 OCR，需用户手动提供 `--company` 和 `--license-no`。

```bash
# 前置：查询注册地合法代码（如不确定）
siluzan-tso open-account tiktok-areas --keyword China

# 前置：查询行业 ID（选叶子节点，即缩进的子行业）
siluzan-tso open-account tiktok-industries --keyword "电商"

# 前置：查询时区代码（如不确定）
siluzan-tso open-account tiktok-timezones --keyword Shanghai

# 提交开户（CLI 自动按公司名创建/关联广告主组，无需 magKey）
siluzan-tso open-account tiktok \
  --company "Brand A Inc." \
  --account-name "品牌A TikTok账户" \
  --currency USD \
  --timezone "Asia/Shanghai" \
  --industry-id <tiktok-industries 输出的叶子节点 ID> \
  --registered-area CN \
  --promotion-link "https://www.brand-a.com" \
  --license-no "91440300XXXXXXXXXX" \
  --license-file "/path/to/license.jpg"

# 轮询审核进度
siluzan-tso account-history -m TikTok
```

---

### Yandex 开户

**所需信息**：公司名称、Yandex 登录名、邮箱、税号（TIN）、电话

```bash
# 提交开户（CLI 自动按公司名创建/关联广告主组，无需 magKey）
siluzan-tso open-account yandex \
  --company "Brand A Inc." \
  --login "brandainc_yandex" \
  --first-name "San" \
  --last-name "Zhang" \
  --email "contact@brand-a.com" \
  --tin "XXXXXXXXXX" \
  --phone "+86XXXXXXXXXXX"

# 轮询审核进度
siluzan-tso account-history -m Yandex
```

---

### BingV2 开户

**所需信息**：广告主全称/简称、地址（省市区）、推广链接、行业名称、营业执照图片本地路径

```bash
# 前置：查询行业名称（将输出的 name 值传给 --trade-id）
siluzan-tso open-account bing-industries --keyword "科技"

# 提交开户（CLI 自动按公司名创建/关联广告主组，无需 magKey）
siluzan-tso open-account bing \
  --advertiser-name "深圳XX科技有限公司" \
  --name-short "XX科技" \
  --province "广东省" \
  --city "深圳市" \
  --address "南山区科技园XX路XX号XX大厦" \
  --promotion-link "https://www.brand-a.com" \
  --trade-id "IT/消费电子-其他" \
  --license-file "/path/to/license.jpg"

# 轮询审核进度
siluzan-tso account-history -m BingV2
```

---

### Kwai 开户

**所需信息**：公司名称、主体信息、行业多级 ID、产品网址、账户类型、营业执照图片本地路径

```bash
# 提交开户（CLI 自动按公司名创建/关联广告主组，无需 magKey）
siluzan-tso open-account kwai \
  --company-name "深圳XX科技有限公司" \
  --licence-id "91440300XXXXXXXXXX" \
  --licence-country CN \
  --licence-location "广东省深圳市南山区XX路XX号" \
  --business-scope "电商零售" \
  --product "品牌A" \
  --ad-type 1 \
  --product-url "https://www.brand-a.com" \
  --licence-id-type ENTERPRISE \
  --account-name "品牌A Kwai账户" \
  --industry-id1 "1234" \
  --industry-id2 "5678" \
  --expire-type 2 \
  --target-country US \
  --license-file "/path/to/license.jpg"

# 轮询审核进度
siluzan-tso account-history -m Kwai
```

---

### 审核结果处理

```bash
# 查询审核状态
siluzan-tso account-history -m Google
```

| 状态       | 含义     | 下一步                                                                                                                |
| ---------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| `Pending`  | 审核中   | 等待，可反复轮询                                                                                                      |
| `Approved` | 审核通过 | `list-accounts` 确认账户出现；引导用户充值激活（见各媒体第四步）                                                      |
| `Rejected` | 被拒     | 查看拒绝原因（`account-history --json` 的 `reason` 字段）；修改资料后重新提交；如无法确定原因，引导用户联系丝路赞客服 |

---

## 流程二：AI 智投创建 → 审核 → 发布

对应页面：`/advertising/AICreation`（创建向导）、`/advertising/AICreationList`（记录列表）。`ad smart` 与 `ad batch` 详解见 **`references/aigc.md`**。

### 业务背景

AI 智投会生成一份 Google 广告草稿（包含系列/组/关键词/广告语/地理位置），用户在网页上填写后保存为草稿。AI Agent 的职责是：查询草稿状态、按需修改草稿字段、在用户确认后发布。

> **AI 智投草稿（从零开始）** 必须在网页 `/advertising/AICreation` 上填写向导并保存为草稿，CLI 不支持该向导的初始创建步骤。
>
> 如需用 CLI 直接创建广告系列/组/关键词/广告创意（不经过 AI 智投向导），请参考 **流程三**（`ad campaign-create` / `ad adgroup-create` / `ad ad-create` / `ad keyword-create`）。

### 步骤

```bash
# 第一步：查询 AI 智投草稿列表，找到目标记录
siluzan-tso ad batch list --customer-id <mediaCustomerId>

# 过滤只看未发布草稿
siluzan-tso ad batch list --state Unpublished --json

# 第二步：查看草稿详情（包含完整的广告系列/关键词/预算等配置）
siluzan-tso ad batch get --id <recordId>

# 第三步（可选）：修改草稿中的字段
# 只有 draftStatus = "Draft" 的记录才可更新
siluzan-tso ad batch update --id <recordId> \
  --budget 50000 \
  --campaign-name "品牌A春季促销" \
  --url "https://www.brand-a.com/spring-sale"

# 第四步：发布草稿（提交给 Google 异步创建广告）
siluzan-tso ad batch publish --id <recordId>

# 第五步：发布后跟踪创建状态（Creating → Successfully / Failed）
siluzan-tso ad batch list --customer-id <mediaCustomerId>

# 发布成功后，在 Google 广告管理中验证系列已出现
siluzan-tso ad campaigns -a <mediaCustomerId>
```

**状态流转**：

```
Unpublished（草稿）
  → publish 命令执行后
Creating（Google 异步创建中）
  → 成功
Successfully（创建成功）
  → 失败
Failed / HasFailed（部分或全部失败）
```

**常见场景**：

- 草稿已有字段不满足需求 → `update` 修改后 `publish`
- 创建失败 → `get` 查看详情，检查错误信息，网页上修正后再从 `update` 开始

---

## 流程三：Google 广告创建与精细管理

对应页面：`/advertising/AICreation`（广告系列创建）、`/advertising/adManagement`（广告组/关键词/广告/附加信息/地理位置管理）

### 业务背景

**广告系列（Campaign）只能通过 AI 创建流程生成**——无论是网页向导还是 CLI，底层均调用同一套 AI 创建 API（`/command/campaign-creation-record/campaign-batch-asyncs`）。`ad campaign-create` 等价于网页 AI 智投向导，跳过草稿步骤直接发布，不是独立的"手动创建"接口。

**广告组、关键词、广告创意、附加信息、地理位置**则通过直连 Google API 的命令（`adgroup-create`、`keyword-create`、`ad-create`、`extension`、`geo`）完成，对应 `/advertising/adManagement` 页面的手动操作。

**创建路径选择：**

```
用户要创建 Google 广告
├─ 有已保存的 AI 智投草稿（网页向导填写的）？
│    └─ 是 → 流程二（ad batch update/publish）
├─ 需要 AI 辅助规划关键词/预算/地区分配？
│    └─ 是 → 流程十三（ad smart prepare → ad campaign-create 一体化）
└─ 已知所有参数，直接创建？
     └─ 是 → 本流程（ad campaign-create，内部走 AI 创建 API）
```

### 场景 A：一体化创建（系列 + 关键词 + 广告，推荐）

一条命令完成全部内容，等同于网页向导发布行为。

```bash
# 前置：获取地理位置 ID
siluzan-tso ad geo search -a <mediaCustomerId> -q "United States"
# 记录 id（如美国 = 2840）

# 一体化创建（含关键词和广告创意）
siluzan-tso ad campaign-create \
  -a <mediaCustomerId> \
  --customer-name "<mediaAccountName>" \
  --name "品牌推广_US_搜索" \
  --budget 100 \
  --bidding TARGET_SPEND \
  --location-ids 2840 \
  --adgroup-name "核心词_跑步鞋" \
  --max-cpc 5 \
  --url "https://www.brand-a.com/running-shoes" \
  --keywords "running shoes,sport shoes,trail running" \
  --headlines "专业跑步鞋,轻量透气设计,品牌直销价" \
  --descriptions "全球百万跑者信赖，专业助力每一步。,免费配送，30天无理由退换。" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --path1 "跑步鞋" \
  --path2 "特惠"

# 记录返回的任务 ID，轮询创建状态（Creating → Successfully）
siluzan-tso ad batch get --id <taskId>

# 创建完成后确认系列已出现，并获取 campaignId 供后续精细操作
siluzan-tso ad campaigns -a <mediaCustomerId> --json
```

**关键词格式说明**：

- `running shoes` → 广泛匹配（BROAD）
- `"running shoes"` → 词组匹配（PHRASE）
- `[running shoes]` → 精确匹配（EXACT）
- 逗号分隔多个关键词，可混用三种格式

### 场景 B：仅创建系列骨架，后续精细添加

适合需要精细控制每个广告组、关键词、广告创意的场景。

```bash
# 第一步：创建广告系列骨架（含空广告组，无关键词和广告）
siluzan-tso ad campaign-create \
  -a <mediaCustomerId> \
  --customer-name "<mediaAccountName>" \
  --name "品牌推广_US_搜索" \
  --budget 100 \
  --bidding TARGET_SPEND \
  --location-ids 2840 \
  --adgroup-name "核心词_跑步鞋" \
  --max-cpc 5

# 第二步：等待创建完成
siluzan-tso ad batch get --id <taskId>
# 等 status → Successfully

# 第三步：查询广告系列，获取 campaignId 和 adGroupId
siluzan-tso ad campaigns -a <mediaCustomerId> --json
siluzan-tso ad groups -a <mediaCustomerId> --json

# 第四步（可选）：关键词推荐辅助选词
siluzan-tso keyword -k "跑步鞋,running shoes" --exclude "cheap,kids"

# 第五步：添加关键词
siluzan-tso ad keyword-create \
  -a <mediaCustomerId> \
  --campaign-id <campaignId> \
  --campaign-name "<campaignName>" \
  --adgroup-id <adGroupId> \
  --adgroup-name "核心词_跑步鞋" \
  --keywords "跑步鞋,专业跑鞋,running shoes"

# 第六步（可选）：添加否定关键词
siluzan-tso ad keyword-negative-create \
  -a <mediaCustomerId> \
  --campaign-id <campaignId> \
  --campaign-name "<campaignName>" \
  --keywords "免费,破解,二手"

# 第七步：创建广告创意
siluzan-tso ad ad-create \
  -a <mediaCustomerId> \
  --adgroup-id <adGroupId> \
  --adgroup-name "核心词_跑步鞋" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --headlines "专业跑步鞋,轻量透气设计,品牌直销价" \
  --descriptions "全球百万跑者信赖，专业助力每一步。,免费配送，30天无理由退换。" \
  --path1 "跑步鞋" \
  --path2 "特惠"

# 验证广告已创建
siluzan-tso ad list -a <mediaCustomerId>
```

### 广告效果调整（日常运营）

```bash
# 暂停效果差的广告组
siluzan-tso ad adgroup-status -a <mediaCustomerId> --id <adGroupId> --status Paused

# 恢复广告组
siluzan-tso ad adgroup-status -a <mediaCustomerId> --id <adGroupId> --status Enabled

# 暂停广告系列（状态切换）
siluzan-tso ad campaign-status -a <mediaCustomerId> --id <campaignId> --status Paused

# 删除效果差的广告
siluzan-tso ad ad-delete -a <mediaCustomerId> --id <adId>

# 查看并清理否定关键词
siluzan-tso ad keywords -a <mediaCustomerId> --negative --json
siluzan-tso ad keyword-negative-delete -a <mediaCustomerId> --id <negKwId>
```

---

## 流程四：AI 广告优化建议查看与执行

对应页面：`/advertising/intelligentOptimization`（v2）。`optimize` 命令与脱管账户说明见 **`references/optimize.md`**。

### 业务背景

AI 优化模块会分析账户的投放数据，给出优化建议（如调整出价策略、添加关键词、暂停低效广告组等）。CLI 支持查看优化列表和记录，具体执行操作通过广告管理命令完成。

```bash
# 第一步：查看账户级优化建议列表（当前仍托管）
siluzan-tso optimize list -a <mediaCustomerId>

# 已不在 Siluzan 托管：勿用 -a（接口常 0 条）。用全量翻页 + 客户端筛 Google 客户号，再取 items[].id
# siluzan-tso optimize list --match-media-customer-id <mediaCustomerId> [--start YYYY-MM-DD] --json

# 第二步：系列级优化记录（可选日期；脱管账户勿依赖 -a）
siluzan-tso optimize records --start 2026-03-01

# 第三步：广告系列级明细（parentId = 上一步 list 里某批次的 id / entityId）
siluzan-tso optimize children --parent-id <parentId>

# 单条详情：id 可为 list 批次 id，或 records --json 的 items[].id
siluzan-tso optimize get --id <recordUuid>

# 根据建议执行操作（以"暂停低效广告组"为例）
siluzan-tso ad adgroup-status -a <mediaCustomerId> --id <adGroupId> --status Paused

# 根据建议执行操作（以"添加关键词"为例）
siluzan-tso ad keyword-create \
  -a <mediaCustomerId> \
  --campaign-id <campaignId> \
  --campaign-name "<campaignName>" \
  --adgroup-id <adGroupId> \
  --adgroup-name "<adGroupName>" \
  --keywords "AI推荐词1,AI推荐词2"
```

> 优化建议的具体执行方案详情（如具体要加哪些词、调整哪些出价）需在网页 `/advertising/intelligentOptimizationDetails` 查看完整报告后再操作。

---

## 流程五：智能预警规则完整管理

对应页面：`/tool/forewarning`、`/tool/earlyWarningConfig`

### 业务背景

预警规则用于监控账户的消耗/CPC/转化等指标，超过阈值时通知相关人员。典型场景：「日消费超过 500 元立即通知」「CPC 高于 10 元停止投放」。

```bash
# 第一步：查看已有预警规则，了解当前配置
siluzan-tso forewarning list -m Google

# 第二步：创建新的预警规则
# 场景：Google 账户日消费超过 500 元，每 15 分钟检查一次
siluzan-tso forewarning create \
  -m Google \
  --name "日消费超限预警" \
  --accounts "<entityId1>,<entityId2>" \
  --field cost \
  --operator GREATER_EQUALS \
  --value 500 \
  --days 1 \
  --frequency QuarterHour \
  --notify "<notifyEntityId>"

# 第三步：验证规则已创建（查看规则详情确认配置正确）
siluzan-tso forewarning list -m Google
siluzan-tso forewarning get -m Google --id <ruleId>

# 第四步：查看规则触发记录（规则运行后）
siluzan-tso forewarning records -m Google --rule-id <ruleId>

# 第五步（日常操作）：暂时关闭规则（如节假日调整策略）
siluzan-tso forewarning stop -m Google --id <ruleId>

# 恢复规则
siluzan-tso forewarning start -m Google --id <ruleId>

# 修改规则阈值
siluzan-tso forewarning update \
  -m Google \
  --id <ruleId> \
  --name "日消费超限预警（修改版）" \
  --accounts "<entityId1>" \
  --field cost \
  --operator GREATER_EQUALS \
  --value 800

# 删除不再需要的规则
siluzan-tso forewarning delete -m Google --id <ruleId>
```

**预警 + 广告管理联动场景**：

```bash
# 查看触发了预警的账户
siluzan-tso forewarning records -m Google --start 2026-03-20 --json

# 确认对应账户的实际消耗
siluzan-tso stats -m Google -a <entityId> --start 2026-03-20

# 根据情况暂停对应广告系列
siluzan-tso ad campaign-status -a <mediaCustomerId> --id <campaignId> --status Paused
```

---

## 流程六：优化报告生成 → 推送管理

对应页面：`/dataReport/optimizationReport`、`/dataReport/pushRecord`。命令与接口详解见 **`references/reporting.md`**。

### 业务背景

每月/每周为客户生成投放数据报告，设置自动推送，客户可通过网页链接查看。

```bash
# 第一步：查询可生成报告的账户列表
siluzan-tso list-accounts -m Google --json

# 第二步：批量生成上月日报（-a 传 mediaCustomerId，不是 entityId）
siluzan-tso report create \
  -m Google \
  -a <mediaCustomerId1>,<mediaCustomerId2> \
  -t Daily \
  --start 2026-03-01 \
  --end 2026-03-31

# 第三步：轮询报告生成状态（reportReady=true 表示已生成完成）
siluzan-tso report list -m Google --status true

# 第四步：获取报告查看链接（viewUrl 字段已直接包含在输出中，无需手动拼接）
siluzan-tso report list -m Google
# 表格中 viewUrl 列即为可点击的网页链接；--json 输出时每条记录含 viewUrl 字段

# 第五步：查看推送配置列表（是否已开启自动推送；接口同 GET .../query/report-push/settings/Google）
siluzan-tso report push list -m Google
# siluzan-tso report push list -m Google --json   # items[].entityId / id 用于启停删、history、update
# siluzan-tso report push receive-emails -m Google [--json]   # 历史收件邮箱，与网页推送配置下拉同源

# 推送记录（网页 /dataReport/pushRecord?entityId=...）
# siluzan-tso report push history -m Google --setting-id <推送规则entityId> --json

# 新建 / 编辑（网页弹窗；--media-accounts 为 ma.entityId）
# siluzan-tso report push create -m Google --name "..." --media-accounts <id,...> --emails a@b.com --types Daily
# siluzan-tso report push update -m Google --id <配置id> --name "..." --media-accounts ... --emails ... --types Daily,Weekly

# 第六步：启动/停止推送（--id 为推送配置 entityId，与网页开关一致）
siluzan-tso report push start -m Google --id <推送配置UUID>
siluzan-tso report push stop  -m Google --id <推送配置UUID>

# 清理旧报告
siluzan-tso report delete --ids <id1>,<id2>
```

---

## 流程六点五：账户分析报告（CLI 拉数 + Agent 撰稿）

对应能力：`google-analysis`、`report meta-overview`、`report tiktok-*`、`report bing-*` 与 `report-templates/*.md`。子命令与模板索引见 **`references/account-analytics.md`**。

### 与流程六的区别

| 流程六                                                       | 流程六点五                                                   |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| TSO **优化报告**：`report create` / `list` / 推送 / 查看链接 | Agent **撰写**的分析报告：CLI 取数后按纲要组织 Markdown/HTML |

### 步骤

1. 确认账户 ID（`list-accounts`）与日期区间。
2. 选定对应媒体的 `report-templates/*.md`（Google 用 `google-period-report.md`，其他类推）。
3. 按该 `*.md` 的**默认维度**直接拉数；同时向用户发消息，展示**可选追加维度**列表（见该 `*.md`），询问是否追加。
4. 用默认维度数据撰写报告；用户追加的维度数据到位后，补充在末尾。
5. 可选：按 `report-template*.html` 选择 HTML 样式输出（未指定时默认 `report-template.html`）。

---

## 流程七：开票申请完整流程

对应页面：`/recharge/invoicingApplicationList`、`/recharge/invoiceList`

### 业务背景

充值后需要申请发票。流程：查询可开票订单 → 确认订单 `entityId` → 按**币种**选择发票类型（人民币仅增值税票，美金等仅形式发票 PI）→ 提交开票申请 → 跟踪状态。

```bash
# 第一步：查询可开票订单（按媒体和币种筛选）
siluzan-tso invoice billable -m Google -c USD --json
# 记录目标订单的 entityId（字段名 entityId，不是过时的 billId）

# 若需要查询钱包充值的可开票金额
siluzan-tso invoice billable --wallet --json

# 第二步：提交开票申请（USD 订单示例：仅 PI + 英文抬头与地址）
siluzan-tso invoice apply \
  --bill-ids "entityId1,entityId2" \
  --bill-type AmountAccount \
  --invoice-type PI \
  --media Google \
  --company-name-en "Example Co., Ltd." \
  --registered-address-en "Room 101, Example City" \
  --recipient-name "张三" \
  --recipient-phone 13800138000

# 人民币订单请使用 --invoice-type VATI 或 VATSI，并填写 --company-name、--tax-id、--title、--company-phone 等（见 finance.md）

# 第三步：查询开票申请状态
siluzan-tso invoice list --start 2026-03-01
```

---

## 流程八：广告线索数据提取与跟进

对应页面：`/clue-form`。`clue` 命令参数见 **`references/clue.md`**。

### 业务背景

广告投放后，用户在 TikTok/Meta 广告中填写了表单（留资），需要定期拉取线索数据、联系潜在客户。

```bash
# 第一步：确认有哪些 TikTok/Meta 账户
siluzan-tso list-accounts -m TikTok
siluzan-tso list-accounts --json | Select-String "MetaAd"  # 或用 --json 过滤

# 第二步：拉取 TikTok 线索（按区域分类查看）
# 全部区域
siluzan-tso clue -m TikTok -a <advertiserId>

# 只看欧洲区域
siluzan-tso clue -m TikTok -a <advertiserId> --region eu

# 导出为 JSON 供后续处理
siluzan-tso clue -m TikTok -a <advertiserId> --json > tiktok-leads.json

# 第三步：拉取 Meta 线索（指定日期范围）
siluzan-tso clue -m Meta -a <pageId> \
  --start 2026-03-01 \
  --end 2026-03-31 \
  --json > meta-leads.json
```

**定期线索提取（建议每日/每周执行）**：

```bash
# TikTok 全账户线索（如有多个 advertiserId，逐个执行）
siluzan-tso list-accounts -m TikTok --json
# 对每个账户：
siluzan-tso clue -m TikTok -a <advertiserId> --json

# Meta 线索（本周）
siluzan-tso clue -m Meta -a <pageId> \
  --start 2026-03-17 \
  --end 2026-03-20 \
  --json
```

---

## 流程九：账户权限管理（分享/断开/OAuth 重授权/MCC）

对应页面：`/foreign_trade/tso/manageAccounts`、`/accountOpeningHistory`

### 业务背景

团队成员需要共享某个 Google 账户，或者账户 OAuth Token 过期需要重新授权，或者需要将某个账户从丝路赞平台解绑。

```bash
# ─── 场景A：将账户分享给团队成员 ───

# 第一步：确认要分享的账户 entityId
siluzan-tso list-accounts -m Google --json
# 找到目标账户的 entityId（不是 mediaCustomerId！）

# 第二步：分享给指定手机号（手机号需已在丝路赞注册）
siluzan-tso account share --id <entityId> --phone 13800138000

# 第三步：确认分享状态
siluzan-tso account share-detail --customer-id <mediaCustomerId>

# 第四步（如需取消）：取消分享
siluzan-tso account unshare --id <entityId> --account-id <userId>


# ─── 场景B：OAuth Token 过期，重新授权 ───

# 检查账户状态（invalidOAuthToken = true 表示需要重新授权）
siluzan-tso list-accounts -m Google --json

# 重新触发 OAuth 授权流程（会在浏览器打开授权页）
siluzan-tso account auth -m Google

# 授权完成后验证账户恢复正常
siluzan-tso list-accounts -m Google


# ─── 场景C：从平台解绑账户 ───

# 先查出 entityId
siluzan-tso list-accounts -m Google --json

# 断开单个账户（操作前确认账户名/ID 正确）
siluzan-tso account delink --id <entityId>

# 批量断开多个账户
siluzan-tso account delink --ids <id1>,<id2>,<id3>

# 验证账户已从列表移除
siluzan-tso list-accounts -m Google


# ─── 场景D：Google MCC 绑定 / 解绑 ───

# 先确认 googleApiUrl（与 ad / keyword 同源）
siluzan-tso config show

# 从列表中取子账户的 mediaCustomerId（数字 ID），不是 entityId
siluzan-tso list-accounts -m Google --json

# 将一个或多个子账户绑定到指定 MCC（多个 MCC ID 可用逗号或分号分隔）
siluzan-tso account mcc-bind --customers <mediaCustomerId1>,<mediaCustomerId2> --mcc <MCC客户ID>

# 解绑：从子账户上移除与某 MCC 的关联
siluzan-tso account mcc-unbind --customers <mediaCustomerId> --mcc <MCC客户ID>

# 需要排查接口返回时加 --json
siluzan-tso account mcc-bind --customers <mediaCustomerId> --mcc <MCC客户ID> --json
```

---

## 流程十：投放数据快速巡检（日/周例行）

### 业务背景

运营人员每天/每周需要快速了解各媒体账户的消耗情况、余额预警和报告状态。

```bash
# ─── 日巡检（每天早上执行）───

# 查看各媒体账户余额（确保余额充足）
# 注意：balance -a 传 mediaCustomerId（数字ID），不是 entityId
siluzan-tso list-accounts -m Google --json
siluzan-tso balance -m Google -a <mediaCustomerId1>,<mediaCustomerId2>
siluzan-tso balance -m TikTok -a <mediaCustomerId3>

# 查看昨天的消耗数据（-a 必填，传 mediaCustomerId）
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)
siluzan-tso stats -m Google -a <mediaCustomerId> --start $YESTERDAY --end $YESTERDAY
siluzan-tso stats -m TikTok -a <mediaCustomerId> --start $YESTERDAY --end $YESTERDAY

# 检查是否有预警触发
siluzan-tso forewarning records -m Google --start $YESTERDAY
siluzan-tso forewarning records -m TikTok --start $YESTERDAY


# ─── 周巡检（每周一执行）───

# 查询上周消耗（-a 必填，传 mediaCustomerId）
siluzan-tso stats -m Google -a <mediaCustomerId> --start 2026-03-11 --end 2026-03-17
siluzan-tso stats -m TikTok -a <mediaCustomerId> --start 2026-03-11 --end 2026-03-17

# 检查 AI 智投创建状态（有无失败记录）
siluzan-tso ad batch list --state Failed
siluzan-tso ad batch list --state HasFailed

# 检查线索数据
siluzan-tso clue -m TikTok -a <advertiserId> --json
siluzan-tso clue -m Meta -a <pageId> --start 2026-03-11 --end 2026-03-17 --json

# 查看本周优化建议（托管中）
siluzan-tso optimize list -a <mediaCustomerId>
# 已脱管：optimize list --match-media-customer-id <mediaCustomerId> --json → items[].id
# siluzan-tso optimize get --id <id>
# siluzan-tso optimize children --parent-id <id>
```

---

## 流程十一：媒体转账记录核查

对应页面：`/recharge/accountTransfer`

### 业务背景

充值到丝路赞账户后，需要查询媒体转账到账情况，确认账户余额是否已更新。

```bash
# 查询 Google 账户最近转账
siluzan-tso transfer list -m Google

# 查询指定时间段内的转账
siluzan-tso transfer list -m TikTok --start 2026-03-01 --end 2026-03-31

# JSON 输出供对账使用
siluzan-tso transfer list -m Google --json

# 对账：转账到账后查询账户余额（传 mediaCustomerId）
siluzan-tso balance -m Google -a <mediaCustomerId>
```

---

## 流程十三：Google AIGC 广告智投方案生成（全 CLI，无需打开浏览器）

对应功能：`ad smart prepare`（数据收集）→ AI Agent 规划 → `ad` 系列命令落地

### 业务背景

AI Agent 全程辅助的 Google 广告方案生成：CLI 负责调用平台 AI 接口收集行业、关键词、地区预算等结构化数据，AI Agent 据此生成完整的广告方案（系列/组/关键词/广告语），再通过 `ad` 命令直接在 Google Ads 账户中落地创建。**全程无需打开浏览器。**

### 完整业务流程

```
ad smart prepare → 收集行业/关键词/地区预算等规划数据
AI Agent 分析    → 基于数据生成完整广告方案（系列结构/关键词/广告语）
ad adgroup-create → 在现有广告系列下创建广告组
ad keyword-create → 添加推荐关键词
ad ad-create      → 创建广告创意（RSA）
```

### 步骤

```bash
# 第一步：确认 Google 账户（取 mediaCustomerId）
siluzan-tso list-accounts -m Google --json

# 第二步：收集 AIGC 方案规划数据
# 命令会自动完成：链接验证 → 行业匹配 → 语言获取 → 关键词推荐 → 地区预算比例
siluzan-tso ad smart prepare \
  -a <mediaCustomerId> \
  --url "https://www.brand-a.com" \
  -w "running shoes,sport shoes" \
  --secondary-words "marathon shoes,trail running" \
  --budget 200

# 第三步：AI Agent 分析 ad smart prepare 的输出，生成方案
# AI Agent 依据以下数据规划：
#   - 行业代码、推荐语言 → 广告系列定向设置
#   - 地区预算比例 → 各地区广告系列预算分配
#   - 关键词推荐列表 → 广告组关键词
#   - 产品词 + 链接 → AI 自行生成标题和描述

# 第四步：查看现有广告系列（方案需要挂载在某个系列下）
siluzan-tso ad campaigns -a <mediaCustomerId> --json
# 若返回为空，需先创建广告系列（异步，完成后用 ad batch get --id <taskId> 跟踪状态）：
# siluzan-tso ad campaign-create -a <mediaCustomerId> --name "品牌A-搜索广告" --budget 100 --location-ids 2840

# 第五步：按方案创建广告组（以第一个地区/产品词方向为例）
siluzan-tso ad adgroup-create \
  -a <mediaCustomerId> \
  --campaign-id <campaignId> \
  --campaign-name "<campaignName>" \
  --name "核心词_running shoes" \
  --max-cpc 100000

# 第六步：查询新建广告组 ID
siluzan-tso ad groups -a <mediaCustomerId> --json

# 第七步：添加推荐关键词
siluzan-tso ad keyword-create \
  -a <mediaCustomerId> \
  --campaign-id <campaignId> \
  --campaign-name "<campaignName>" \
  --adgroup-id <adgroupId> \
  --adgroup-name "核心词_running shoes" \
  --keywords "running shoes,sport shoes,marathon shoes"

# 第八步：创建广告创意（RSA）
siluzan-tso ad ad-create \
  -a <mediaCustomerId> \
  --adgroup-id <adgroupId> \
  --adgroup-name "核心词_running shoes" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --headlines "专业跑步鞋,轻量透气设计,品牌直销价" \
  --descriptions "全球百万跑者信赖，专业助力每一步。,免费配送，30天无理由退换。" \
  --path1 "跑步鞋" \
  --path2 "特惠"

# 第九步：验证广告已创建
siluzan-tso ad list -a <mediaCustomerId>
```

### `ad smart prepare` 输出说明

| 字段                               | 说明                     | AI Agent 使用方式          |
| ---------------------------------- | ------------------------ | -------------------------- |
| `industry.industryName`            | 匹配的行业               | 确认产品方向是否正确       |
| `industry.language` / `languageId` | 推荐语言                 | 设置广告系列语言定向       |
| `keywordIdeas`                     | 关键词列表（含月搜索量） | 筛选高搜索量词加入广告组   |
| `budgetProportions`                | 地区预算比例             | 多地区方案中按比例分配预算 |
| `account.currencyCode`             | 货币单位                 | 换算 `max-cpc` 的实际金额  |

### JSON 输出格式（`--json`）

```bash
# 输出完整 JSON 供 AI Agent 程序化处理
siluzan-tso ad smart prepare \
  -a <mediaCustomerId> \
  --url "https://www.brand-a.com" \
  -w "running shoes" \
  --json
```

```json
{
  "account": { "mediaCustomerId": "...", "currencyCode": "USD" },
  "url": { "validated": true, "input": "https://..." },
  "industry": { "industryCode": "...", "industryName": "...", "language": "English", "languageId": "1000" },
  "languages": [...],
  "keywordIdeas": [
    { "keyword": "running shoes", "monthlySearch": 90500 },
    { "keyword": "sport running shoes", "monthlySearch": 22200 }
  ],
  "budgetProportions": [
    { "areaCode": "NA", "regionCodes": ["US", "CA"], "budgetProportion": 0.45 },
    { "areaCode": "EU", "regionCodes": ["GB", "DE", "FR"], "budgetProportion": 0.30 }
  ]
}
```

**AI Agent 行为规范**：

- 用户说「生成广告方案」「规划 Google 广告」时，**先运行 `ad smart prepare` 收集数据**，再基于数据规划方案
- 关键词来自 `keywordIdeas`，根据月搜索量筛选，同时结合用户的产品词
- 广告创意（标题/描述）由 AI Agent 自行生成，遵循 Google 广告规范（标题≤30字符，描述≤90字符）
- 如有多个地区方向，按 `budgetProportions` 的比例分配日预算，为每个地区创建独立广告组
- `ad campaign-create` / `ad smart create`（批量创建 API）的预算与 CPC 为**主币种展示金额**，与 Web 一致内部 `×100`；分步命令里 `ad adgroup-create`、`ad keyword-edit` 等走 Google 网关，金额单位以 `references/google-ads.md` 对应章节为准

---

## 流程十四：网站诊断与广告落地页评估

对应页面：`/advertising/AICreation`（落地页质量评估入口）

### 业务背景

广告投放前需评估落地页质量：页面访问速度、产品描述完整性、转化代码部署、移动端适配等。系统通过 Lighthouse + AI 分析给出评分和优化建议，判断该页面是否适合直接投放广告。

### Agent 操作流程

**网站诊断**（需在网页完成）：

```bash
# 引导用户打开网站诊断页面（在 AICreation 流程中内嵌，或直接访问）
siluzan-tso config show   # 取 webUrl

# 诊断入口（在 AIGC 智投向导内）：
# {webUrl}/v3/foreign_trade/tso/advertising/AICreation
# → 输入推广链接时，系统会自动触发网站诊断
```

**CLI 辅助验证**（与诊断配合使用）：

```bash
# 验证链接可访问性（接口：/query/media-account/GetSuitableLink）
# → 此为内部辅助，Agent 在 AIGC 创建流程中会自动调用，无需手动执行

# 如果链接验证失败，先确认账户 OAuth 正常
siluzan-tso list-accounts -m Google --json
# 检查 invalidOAuthToken 字段，若为 true 则先重新授权
siluzan-tso account auth -m Google
```

**诊断结果对投放的影响**：

| 诊断评级         | 建议操作                                             |
| ---------------- | ---------------------------------------------------- |
| 优秀（85分以上） | 可直接投放，继续完成 AIGC 方案生成                   |
| 良好（70-84分）  | 建议优化后投放，可先小预算测试                       |
| 一般（60-69分）  | 重点改善转化代码和页面速度后再投                     |
| 较差（60分以下） | 需先修复关键问题（参考诊断报告），否则广告效果会很差 |

---

## 流程十五：TikTok/Meta/Google 账户管理完整操作

对应页面：`/foreign_trade/tso/manageAccounts`

### 业务背景

账户管理包含多种权限操作：关闭账户、BM 绑定、BC 绑定/解绑、账户激活、邮箱授权管理等。其中关闭账户、BM 绑定、BC 绑定/解绑、MCC 绑定/解绑、账号分享、邮箱授权均有 CLI 支持；账户激活需网页完成。

### 场景 A：TikTok 关闭账户（CLI）

```bash
# 第一步：确认要关闭的 TikTok 账户
siluzan-tso list-accounts -m TikTok --json
# 记录目标账户的 mediaCustomerId

# 第二步：关闭账户（操作不可恢复，请再次确认）
siluzan-tso account close --accounts <mediaCustomerId>

# 批量关闭多个账户
siluzan-tso account close --accounts <id1>,<id2>

# 验证账户状态
siluzan-tso list-accounts -m TikTok
```

> ⚠️ TikTok 账户关闭后停止投放，如需恢复请联系丝路赞客服。

### 场景 B：Meta BM 绑定（CLI）

```bash
# 第一步：查出 Meta 账户 mediaCustomerId
siluzan-tso list-accounts --json   # 找到 MetaAd 类型账户的 mediaCustomerId

# 第二步：绑定到指定 Business Manager
siluzan-tso account bm-bind \
  --account-id <mediaCustomerId> \
  --bm-id <businessManagerId>

# 第三步：确认绑定状态（在网页确认）
# {webUrl}/v3/foreign_trade/tso/manageAccounts → 找到对应账户查看 BM 状态
```

### 场景 C：TikTok BC 绑定 / 解绑

```bash
# 第一步：查出 TikTok 账户的 mediaCustomerId
siluzan-tso list-accounts -m TikTok

# 第二步：绑定 BC
siluzan-tso account bc-bind --customers <mediaCustomerId> --bc-ids <bcId>

# 解绑（注意解绑用 --bc-id，绑定用 --bc-ids）
siluzan-tso account bc-unbind --customers <mediaCustomerId> --bc-id <bcId>
```

### 场景 D：Google 账户激活（网页）

> 账户激活分两种方式：充值激活（需要在平台充值）、邀请他人激活（被邀请人用已有账户授权）。两种方式均需网页交互。

```bash
siluzan-tso config show   # 取 webUrl

# 打开账户管理页：
# {webUrl}/v3/foreign_trade/tso/manageAccounts
# → 选中 Google 账户 → 点击「激活账户」→ 选择激活方式
```

激活/充值产生的账单明细可用 CLI 查询（`entityId` 来自 `list-accounts -m Google --json`）：

```bash
siluzan-tso account-active-bills -m Google --id <entityId> [--json]
```

详见 `references/accounts.md` 中 **account-active-bills**。

### 场景 E：Google 邮箱授权管理

```bash
# 查看账户已有邮箱授权列表
siluzan-tso account email-auth-list -c <mediaCustomerId>

# 向邮箱发送授权邀请（默认 Standard 权限）
siluzan-tso account email-auth -c <mediaCustomerId> --email user@gmail.com

# 只读权限
siluzan-tso account email-auth -c <mediaCustomerId> --email user@gmail.com --access-role ReadOnly

# 撤销邀请（先从 email-auth-list --json 取 invitationId 和 resourceName）
siluzan-tso account email-deauth -c <mediaCustomerId> --invitation-id <id> --resource-name <name>
# 若邀请尚未被接受，追加 --pending
siluzan-tso account email-deauth -c <mediaCustomerId> --invitation-id <id> --resource-name <name> --pending
```

---

## 流程十二：TSO 首页看板（`/foreign_trade/tso/home`）

对应页面：主应用 **`/v3/foreign_trade/tso/home`**（TSO 子应用内为 `/home`）。

### 业务背景

首页聚合展示：按媒体的昨日转化/消耗/充值、待充值账户数、开户申请概览、各媒体余额、广告投放图表等。部分数据来自 **`/report/media-account/Get-TSO-Overviews`**、**`Get-TSO-Open-Account-Overviews`**、**`GetAccountBalance`**、**`accountreportoverview`**、**`GetAccountDataOverview`** 等接口，**当前 CLI 未单独封装这些聚合接口**。

### Agent 建议

1. **用户要与网页首页数字完全一致**  
   → `siluzan-tso config show` 取 `webUrl`，引导打开 **`{webUrl}/v3/foreign_trade/tso/home`**（路径前缀以实际部署为准）。

2. **用 CLI 做「近似首页」的数据巡检**（单账户粒度）  
   → 与 **流程十** 相同思路：

```bash
siluzan-tso list-accounts -m Google --json
siluzan-tso balance -m Google -a <mediaCustomerId>
siluzan-tso stats -m Google -a <mediaCustomerId>
siluzan-tso account-history -m Google
```

3. **首页「服务推荐」跳转 AI / 建站 / 内容等**  
   → 属其他产品线，见 **`references/tso-home.md`** 中的外链说明，勿用 `siluzan-tso` 冒充。

**详细模块与接口对照** → **`references/tso-home.md`**。
