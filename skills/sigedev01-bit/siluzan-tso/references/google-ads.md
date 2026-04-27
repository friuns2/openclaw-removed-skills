# Google 广告管理命令详解

> 所属 skill：`siluzan-tso`。

---

## 新建广告系列的流程

> **强制流程总览（AI 必须严格遵守）**  
> 1）先完整阅读所有规则文档 → 2）向用户补齐关键信息提问 → 3）在规则约束下设计广告计划 → 4）按模板输出方案并获得用户「明确确认」 → 5）**仅在已确认的前提下**执行任何结构性改动。

### 第一步：规则文档阅读（不得跳过）

操作开始前，**AI 必须先阅读完下面所有文档**，并在心智模型中内化规则后，才能进入任何「方案规划 / 广告创建 / 调整」步骤，严禁只读 `google-ads-launch-plan-template.md` 就直接出方案。

| 文档地址                                                            | 文档内容                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `references/google-ads-rules/google-ads-compliance.md`              | **Google 广告合规指南**：关键词 & 文案审核通过规则、编辑规范、禁止内容、虚假承诺处理、商标规则、多语言规则                                                                                                                                              |
| `references/google-ads-rules/sensitive-industries.md`               | **敏感行业合规细则**：酒精 / 赌博 / 金融 / 加密 / 医疗 / 法律等 15 个行业的关键词生成规则与地区限制                                                                                                                                                     |
| `references/google-ads-rules/google-ads-keyword-strategy.md`        | **关键词策略与优化技巧**：匹配类型策略、分组结构、否定词技巧、出价意图分层、搜索词挖掘、竞品策略、PMax/AI Max 协同、信号污染防治                                                                                                                        |
| `references/google-ads-rules/google-ads-keyword-optimization.md`    | **关键词持续优化指南**：基于投放数据的迭代优化闭环——指标解读、决策框架（暂停/提价/降价/加否定）、优化节奏、转化归因、预算再分配、衰减检测、竞争响应、CRM 反馈                                                                                           |
| `references/google-ads-rules/google-ads-creative-optimization.md`   | **广告创意与素材优化**：RSA 六类主题法、Ad Strength 评分、文案 A/B 测试、创意疲劳管理、附加信息（Sitelink/Callout/Snippet/Image）优化、DKI/倒计时/IF 函数、落地页 CRO、PMax 创意策略、多语言管理                                                        |
| `references/google-ads-rules/google-ads-campaign-optimization.md`   | **广告系列结构与投放优化**：系列类型选择决策树、电商/线索/本地/SaaS 架构模板、出价策略校准与启动协议、地域/设备优化、转化追踪（Enhanced Conversions/离线导入/价值规则）、预算优化、网络设置、实验设计、账户健康诊断                                     |
| `references/google-ads-rules/google-ads-launch-plan-template.md`    | **投放计划确认模板**：AI 生成完整投放方案的 Markdown 模板——信息收集清单、计划格式规范、字段与 CLI 参数映射、合规检查、执行命令预览；用于「用户确认后再执行」的工作流                                                                                    |
| `references/google-ads-rules/google-ads-account-audit.md`           | **账户诊断与审计指南**：三层审计框架（账户→系列→组/词）、5 分钟快速健康检查、结构/转化/出价/关键词/创意/地域/设备/落地页/预算审计、竞争态势分析、20 条常见问题诊断速查表、审计报告模板                                                                  |
| `references/google-ads-rules/google-ads-conversion-architecture.md` | **转化信号架构设计**：信号质量层级（L1-L5）、转化动作设计框架、多阶段漏斗价值设计、Enhanced Conversions 实施、离线转化导入策略、Consent Mode v2、利润导向出价（Profit-Based Bidding）、信号质量诊断与迁移路径、7 个行业推荐配置                         |
| `references/google-ads-rules/google-ads-audience-strategy.md`       | **受众策略与分析**：受众类型全览、业务类型×漏斗阶段策略矩阵、观察 vs 定向模式决策、再营销四层分级（hot/warm/cool/cold）、RLSA 三大策略、Customer Match、受众数据分析框架、受众排除策略、2025-2026 隐私趋势                                              |
| `references/google-ads-rules/google-ads-pmax-guide.md`              | **PMax 与 Demand Gen 深度运营**：PMax 运营原理、Search 蚕食诊断（20% 品牌花费阈值）、Asset Group 策略、渠道级分析（2025 新功能）、搜索词/否定词/品牌排除管理、受众信号优化、Demand Gen 战术、AI Max for Search 协同、AI Overview 广告策略、常见问题诊断 |

> **AI Agent 具体要求：**
>
> - 若当前会话中尚未阅读上述任一文件，AI 必须先主动阅读，再继续下一步流程，而不是直接生成广告计划或文案。
> - 在首次阅读后，AI 需用自己的话向用户**简要复述**上述文档中与本次任务强相关的 3～5 条关键合规/策略要点，并询问用户是否有本地特殊限制需要补充。
> - 后续生成的关键词、文案、出价与结构，必须**显式遵守这些规则**；一旦与规则冲突，应以规则优先，并向用户说明原因（例如：某些词因合规或商标问题被自动剔除）。

### 第二步：向用户补齐关键信息

在进入计划设计前，AI 应最少询问并确认以下关键信息（可按需追加）：

- **业务与转化目标**：行业、主营产品/服务、主要转化动作（表单提交 / 电话咨询 / 在线下单 等）。
- **目标地区与语言**：主要投放国家/地区、语言组合、多语言站点情况。
- **预算与节奏**：日预算区间、是否有阶段性活动（如大促 / 节日档期）、允许的试错周期。
- **历史投放情况**：是否已有历史账户/系列/关键词表现数据，是否有必须保留/禁止使用的词或文案。
- **合规与品牌限制**：是否涉及敏感行业、是否有品牌词 / 合作方词 / 法律风控要求等。

### 第三步：根据规则与信息生成计划并确认

最终需要按照 `references/google-ads-rules/google-ads-launch-plan-template.md`  
生成对应的计划，与用户沟通确认。**在该方案中，AI 必须：**

- **引用并遵守**前述规则文档中的关键条款（尤其是合规与敏感行业部分），必要时在方案对应章节标注「来源规则」。
- **解释核心决定的依据**，例如为何采用某类匹配结构、为何排除某类词、为何推荐某种出价策略。
- **明确列出风险点与替代方案**，帮助用户在确认前做出知情决策。

**只有在用户通过自然语言明确表示「同意 / 确认按此方案执行」之后**，AI 才能真正开始下面的操作；在用户未确认前，不得对账户做任何结构性改动（系列 / 广告组 / 关键词 / 创意）。

> **AI Agent 额外要求**：即使用户强烈要求「不用看方案、直接创建」，也必须先按上述模板输出一次完整 Markdown 投放方案，并在对话中列出**已参考的规则文档列表**（`google-ads.md` 与 `references/google-ads-rules/` 目录下的文件），让用户有机会发现问题后再执行，防止误投和配置错误。

- 如果创建失败
  - 部分失败：可以获取广告系列中哪些子项创建失败，然后通过对应子项的命令来重新创建
  - 完全失败：可以直接重新创建

## 广告的编辑

一个广告系列在创建后，发现完全失败，系列中的广告组、关键词、否定词、附加信息、地理位置、广告语、搜索字词就不能通过campaign-create来重新创建覆盖了，需要通过对应的命令来
无论是任何形式的编辑，都要读取`references/google-ads-rules/google-ads-launch-plan-template.md`来看下对应子项的输出格式，按照模板的格式输出

### 广告修改

- 对用户提出的修改内容进行评估与拓展评估标准基于（references/googles-ads-rules/\*.md）中的对应的文件来确认
- 确认修改方案按照
  - 读取`references/google-ads-rules/google-ads-launch-plan-template.md` 中关于计划模板的描述，节选用户需要修改的部分来按格式输出给用户确认
- 使用对应命令来进行修改
  - 使用ad -h 来查询有哪些修改命令
- 使用对应的获取命令进行校验

### 广告新增

参考修改的流程，将修改的命令改为新增

### 广告优化

参考修改的流程，优化的部分需要有新旧对照的表格，其他与修改流程一致

## 下面是相关命令的示例，参考就行

**ID 来源说明：**

| 需要的 ID           | 从哪里获取                                                   |
| ------------------- | ------------------------------------------------------------ |
| `accountId`（`-a`） | `siluzan-tso list-accounts --json` → `mediaCustomerId`       |
| 广告系列 `id`       | `siluzan-tso ad campaigns -a <accountId> --json` → `id`      |
| 广告组 `id`、`name` | `siluzan-tso ad groups -a <accountId> --json` → `id`、`name` |
| 广告 `id`           | `siluzan-tso ad list -a <accountId> --json` → `id`           |
| 关键词 `id`         | `siluzan-tso ad keywords -a <accountId> --json` → `id`       |

---

## ad campaigns — 广告系列管理

### 查询广告系列列表

```bash
siluzan-tso ad campaigns -a <accountId> [选项]
```

| 选项                   | 说明                           |
| ---------------------- | ------------------------------ |
| `-a, --account <id>`   | Google mediaCustomerId（必填） |
| `--start <YYYY-MM-DD>` | 统计开始日期                   |
| `--end <YYYY-MM-DD>`   | 统计结束日期                   |
| `--json`               | 输出原始 JSON                  |

**示例：**

```bash
# 查询账户下所有广告系列
siluzan-tso ad campaigns -a 6326027735

# 查询本月数据
siluzan-tso ad campaigns -a 6326027735 --start 2026-03-01 --end 2026-03-31

# JSON 输出，获取广告系列 id 供后续操作
siluzan-tso ad campaigns -a 6326027735 --json
```

输出字段：名称、状态（`statusV2`）、类型（`channelTypeV2`）、预算、点击数、展示数。

---

### 广告系列启停

```bash
siluzan-tso ad campaign-status \
  -a <accountId> \
  --id <campaignId> \
  --status <Enabled|Paused>
```

**示例：**

```bash
# 暂停广告系列
siluzan-tso ad campaign-status -a 6326027735 --id campaign_001 --status Paused

# 恢复广告系列
siluzan-tso ad campaign-status -a 6326027735 --id campaign_001 --status Enabled
```

---

### 广告系列删除

```bash
siluzan-tso ad campaign-delete -a <accountId> --id <campaignId>
```

**示例：**

```bash
siluzan-tso ad campaign-delete -a 6326027735 --id campaign_001
```

> ⚠️ 删除操作不可逆，建议先用 `campaigns` 命令确认目标广告系列名称再删除。

---

## ad groups — 广告组管理

### 查询广告组列表

```bash
siluzan-tso ad groups -a <accountId> [选项]
```

| 选项                     | 说明                           |
| ------------------------ | ------------------------------ |
| `-a, --account <id>`     | Google mediaCustomerId（必填） |
| `--start / --end <date>` | 统计日期范围                   |
| `--json`                 | 输出原始 JSON                  |

**示例：**

```bash
# 查询所有广告组
siluzan-tso ad groups -a 6326027735

# JSON 输出，获取 id 和 name
siluzan-tso ad groups -a 6326027735 --json
```

---

### 创建广告组

```bash
siluzan-tso ad adgroup-create \
  -a <accountId> \
  --campaign-id <campaignId> \
  --campaign-name <campaignName> \
  --name <adGroupName> \
  --max-cpc <金额（微单位）>
```

| 选项                     | 说明                                               | 必填 |
| ------------------------ | -------------------------------------------------- | ---- |
| `-a, --account <id>`     | Google mediaCustomerId                             | ✅   |
| `--campaign-id <id>`     | 所属广告系列 ID（来自 `campaigns --json`）         | ✅   |
| `--campaign-name <name>` | 所属广告系列名称                                   | ✅   |
| `--name <name>`          | 广告组名称                                         | ✅   |
| `--max-cpc <amount>`     | 最高 CPC 出价（最小货币单位，如 `100000` = 1 USD） | ✅   |
| `--status <status>`      | `ENABLED \| PAUSED`（默认 `ENABLED`）              |      |

**示例：**

```bash
# 在广告系列下创建广告组，最高 CPC 1 USD
siluzan-tso ad adgroup-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --name "核心词_跑步鞋" \
  --max-cpc 100000

# 创建时设为暂停状态
siluzan-tso ad adgroup-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --name "竞品词" \
  --max-cpc 150000 \
  --status PAUSED
```

---

### 广告组启停

```bash
siluzan-tso ad adgroup-status \
  -a <accountId> \
  --id <adGroupId> \
  --status <Enabled|Paused>
```

**示例：**

```bash
# 暂停广告组
siluzan-tso ad adgroup-status -a 6326027735 --id adgroup_001 --status Paused

# 恢复广告组
siluzan-tso ad adgroup-status -a 6326027735 --id adgroup_001 --status Enabled
```

---

### 广告组删除

```bash
siluzan-tso ad adgroup-delete -a <accountId> --id <adGroupId>
```

**示例：**

```bash
siluzan-tso ad adgroup-delete -a 6326027735 --id adgroup_001
```

---

## ad list — 广告创意管理

### 查询广告列表

```bash
siluzan-tso ad list -a <accountId> [选项]
```

| 选项                     | 说明                           |
| ------------------------ | ------------------------------ |
| `-a, --account <id>`     | Google mediaCustomerId（必填） |
| `--start / --end <date>` | 统计日期范围                   |
| `--json`                 | 输出原始 JSON                  |

**示例：**

```bash
# 查询所有广告
siluzan-tso ad list -a 6326027735

# JSON 输出，获取广告 id
siluzan-tso ad list -a 6326027735 --json
```

---

### 创建广告（自适应搜索广告 RSA）

```bash
siluzan-tso ad ad-create \
  -a <accountId> \
  --adgroup-id <adGroupId> \
  --adgroup-name <adGroupName> \
  --final-url <url> \
  --headlines "标题1,标题2,标题3" \
  --descriptions "描述1,描述2"
```

| 选项                     | 说明                                             | 必填 |
| ------------------------ | ------------------------------------------------ | ---- |
| `-a, --account <id>`     | Google mediaCustomerId                           | ✅   |
| `--adgroup-id <id>`      | 广告组 ID（来自 `groups --json`）                | ✅   |
| `--adgroup-name <name>`  | 广告组名称                                       | ✅   |
| `--final-url <url>`      | 最终落地页 URL                                   | ✅   |
| `--headlines <titles>`   | 标题列表，逗号分隔（**至少 3 个**，每个≤30字符） | ✅   |
| `--descriptions <descs>` | 描述列表，逗号分隔（**至少 2 个**，每个≤90字符） | ✅   |
| `--path1 <text>`         | 显示路径第1段（≤15字符）                         |      |
| `--path2 <text>`         | 显示路径第2段（≤15字符）                         |      |

**示例：**

```bash
# 创建基础 RSA 广告
siluzan-tso ad ad-create \
  -a 6326027735 \
  --adgroup-id adgroup_001 \
  --adgroup-name "核心词_跑步鞋" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --headlines "专业跑步鞋,轻量透气跑鞋,跑步必备神器" \
  --descriptions "全球百万跑者信赖，专业设计助你突破极限。,免费配送，30天无理由退换。"

# 带显示路径
siluzan-tso ad ad-create \
  -a 6326027735 \
  --adgroup-id adgroup_001 \
  --adgroup-name "核心词_跑步鞋" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --headlines "跑步鞋专场,品牌直销价,限时特惠" \
  --descriptions "正品保证，7天无理由退换。,百款跑鞋，一站购齐。" \
  --path1 "跑步鞋" \
  --path2 "特惠"
```

---

### 广告创意启停

```bash
siluzan-tso ad ad-status \
  -a <accountId> \
  --id <adId> \
  --status <Enabled|Paused>
```

**示例：**

```bash
siluzan-tso ad ad-status -a 6326027735 --id ad_001 --status Paused
siluzan-tso ad ad-status -a 6326027735 --id ad_001 --status Enabled
```

---

### 广告创意删除

```bash
siluzan-tso ad ad-delete -a <accountId> --id <adId>
```

**示例：**

```bash
siluzan-tso ad ad-delete -a 6326027735 --id ad_001
```

---

## ad keywords — 关键词管理

### 查询关键词列表

```bash
siluzan-tso ad keywords -a <accountId> [选项]
```

| 选项                     | 说明                               |
| ------------------------ | ---------------------------------- |
| `-a, --account <id>`     | Google mediaCustomerId（必填）     |
| `--negative`             | 查询否定关键词（默认查普通关键词） |
| `--start / --end <date>` | 统计日期范围                       |
| `--json`                 | 输出原始 JSON                      |

**示例：**

```bash
# 查询普通关键词
siluzan-tso ad keywords -a 6326027735

# 查询否定关键词
siluzan-tso ad keywords -a 6326027735 --negative

# JSON 输出，获取关键词 id
siluzan-tso ad keywords -a 6326027735 --json
```

---

### 添加关键词

```bash
siluzan-tso ad keyword-create \
  -a <accountId> \
  --adgroup-id <adGroupId> \
  --adgroup-name <adGroupName> \
  --campaign-id <campaignId> \
  --campaign-name <campaignName> \
  --keywords "词1,词2,词3"
```

| 选项                     | 说明                     | 必填 |
| ------------------------ | ------------------------ | ---- |
| `-a, --account <id>`     | Google mediaCustomerId   | ✅   |
| `--adgroup-id <id>`      | 广告组 ID                | ✅   |
| `--adgroup-name <name>`  | 广告组名称               | ✅   |
| `--campaign-id <id>`     | 广告系列 ID              | ✅   |
| `--campaign-name <name>` | 广告系列名称             | ✅   |
| `--keywords <words>`     | 关键词列表，逗号分隔     | ✅   |
| `--final-url <url>`      | 关键词独立落地页（可选） |      |

**示例：**

```bash
# 添加 3 个关键词到广告组
siluzan-tso ad keyword-create \
  -a 6326027735 \
  --adgroup-id adgroup_001 \
  --adgroup-name "核心词_跑步鞋" \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --keywords "跑步鞋,running shoes,专业跑鞋"

# 带独立落地页
siluzan-tso ad keyword-create \
  -a 6326027735 \
  --adgroup-id adgroup_001 \
  --adgroup-name "核心词_跑步鞋" \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --keywords "马拉松跑鞋" \
  --final-url "https://www.brand-a.com/marathon-shoes"
```

---

### 添加否定关键词

可在广告系列层级或广告组层级添加否定关键词。

```bash
siluzan-tso ad keyword-negative-create \
  -a <accountId> \
  --campaign-id <campaignId> \
  --campaign-name <campaignName> \
  --keywords "词1,词2"
```

| 选项                    | 说明                                                    |
| ----------------------- | ------------------------------------------------------- |
| `--adgroup-id <id>`     | 广告组 ID（传入则在广告组层级添加，否则在广告系列层级） |
| `--adgroup-name <name>` | 广告组名称（与 `--adgroup-id` 配套使用）                |

**示例：**

```bash
# 在广告系列层级添加否定关键词（屏蔽）
siluzan-tso ad keyword-negative-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --keywords "免费,破解,二手"

# 在广告组层级添加否定关键词
siluzan-tso ad keyword-negative-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --adgroup-id adgroup_001 \
  --adgroup-name "核心词_跑步鞋" \
  --keywords "拖鞋,凉鞋"
```

---

### 删除否定关键词

```bash
siluzan-tso ad keyword-negative-delete \
  -a <accountId> \
  --id <negativeKeywordId>
```

| 选项                     | 说明                                           |
| ------------------------ | ---------------------------------------------- |
| `--start / --end <date>` | 查询日期范围（用于定位关键词，默认最近 30 天） |

**示例：**

```bash
# 先查询获取否定关键词 id
siluzan-tso ad keywords -a 6326027735 --negative --json

# 然后删除
siluzan-tso ad keyword-negative-delete -a 6326027735 --id negkw_abc123
```

---

## ad batch — 异步批量创建记录

对应页面：`/advertising/AICreationList`。与 `ad campaign-create` 等同源异步创建链路，用于管理异步批量创建任务与草稿。

### list — 查询列表

```bash
siluzan-tso ad batch list [选项]
```

| 选项                     | 说明                                                                   |
| ------------------------ | ---------------------------------------------------------------------- |
| `-s, --state <state>`    | 状态：`Creating \| Successfully \| Failed \| HasFailed \| Unpublished` |
| `--customer-id <id>`     | Google mediaCustomerId                                                 |
| `--customer-name <name>` | 客户名称关键字                                                         |
| `-k, --keyword <text>`   | 关键字                                                                 |
| `--start / --end <date>` | 创建日期范围                                                           |
| `-p, --page <n>`         | 页码（默认 1）                                                         |
| `--page-size <n>`        | 每页数量（默认 20）                                                    |
| `--json`                 | 输出原始 JSON                                                          |

**示例：**

```bash
siluzan-tso ad batch list
siluzan-tso ad batch list --customer-id 6326027735
siluzan-tso ad batch list --state Failed --json
siluzan-tso ad batch list --state Unpublished --start 2026-03-01
```

### get — 获取记录 / 草稿详情

```bash
siluzan-tso ad batch get --id <recordId>
```

输出完整 JSON（含广告系列、预算、关键词、定向位置等），通常配合 `--json` 使用，供 AI 或脚本进一步分析。

### update — 更新草稿字段

只有 `draftStatus === "Draft"` 的记录可更新。

```bash
siluzan-tso ad batch update --id <recordId> [选项]
```

| 选项                     | 说明                                          |
| ------------------------ | --------------------------------------------- |
| `--budget <amount>`      | 新预算（最小货币单位，如 `8500` = 85 元 CNY） |
| `--url <url>`            | 新推广链接                                    |
| `--campaign-name <name>` | 新广告系列名称                                |

### publish — 发布草稿

只有 `draftStatus === "Draft"` 的记录可发布。发布后状态变为 `Creating`，Google 后台异步执行创建。

```bash
siluzan-tso ad batch publish --id <recordId>
```

---

## keyword — 关键字推荐

根据种子词或网址，从 Google Keyword Planner 获取相关关键词建议。

```bash
siluzan-tso keyword -k <搜索词> [选项]
```

| 选项                    | 说明                                               |
| ----------------------- | -------------------------------------------------- |
| `-k, --keyword <words>` | 种子词，多个逗号分隔（必填）                       |
| `--url <url>`           | 公司/产品网址（填写后触发「网址拓词 + 轮询」流程） |
| `--include <words>`     | 结果必须包含的词（逗号或空格分隔，本地过滤）       |
| `--exclude <words>`     | 结果不包含的词（本地过滤）                         |
| `--json`                | 输出原始 JSON                                      |

**示例：**

```bash
# 基础关键词推荐
siluzan-tso keyword -k "running shoes"

# 多种子词推荐
siluzan-tso keyword -k "running shoes,sports shoes,marathon"

# 网址拓词（爬取网址内容后推荐相关词）
siluzan-tso keyword -k "跑步鞋" --url "https://www.brand-a.com"

# 过滤：只保留含 "shoes" 的词，且排除 "cheap" 和 "kids"
siluzan-tso keyword -k "running shoes" --include "shoes" --exclude "cheap,kids"

# JSON 输出（含搜索量、竞争度、建议出价等）
siluzan-tso keyword -k "running shoes" --json
```

---

## ad campaign-create — 广告系列新增

新建搜索广告系列（异步批量任务）。支持两种创建模式：

> - 默认行为：不加 `--draft` 时，CLI 直接走「立即发布」路径（`DraftStatus: Published`）。
> - 草稿行为：加上 `--draft` 时，仅创建草稿记录（`DraftStatus: Draft`），需后续用 `ad batch publish` 才真正提交给 Google。  
>   广告组、关键词、广告创意的直接创建走另一套 Google 网关 API，均有对应的 `adgroup-create`、`keyword-create`、`ad-create` 等命令。  
>   任务异步处理，任务 ID 可通过 `ad batch get --id <id>` 跟进进度。

---

### --config-file（JSON 配置文件） -强烈推荐使用这种方式

**当参数复杂（多广告组、含附加功能、标题中有逗号）时，AI 应优先使用此方式**：将所有参数写入一个 JSON 文件，再用 `--config-file` 传入路径。

**优势：**

- `headlines` 是真正的字符串数组，元素内**允许含逗号**（如 `"Global Reach, Local Impact"`）
- `extensions` / `extraAdGroups` 直接写 JSON，不需要序列化为字符串
- 参数复杂时无 shell 转义问题，AI 一次生成即可成功

**AI 执行步骤：**

1. 用 Write 工具将配置写入 JSON 文件（如 `/tmp/campaign.json`）
2. 执行 `siluzan-tso ad campaign-create --config-file /tmp/campaign.json`
3. 用返回的任务 ID 查询进度

**JSON 配置文件完整 Schema：**

请阅读：`assets/campaign-create-template.json`

**JSON文件 字段说明：**

| 字段                    | 必填 | 类型     | 说明                                                                      |
| ----------------------- | ---- | -------- | ------------------------------------------------------------------------- |
| `account`               | ✅   | string   | Google 账户 mediaCustomerId                                               |
| `customerName`          | ✅   | string   | 账户名称（`list-accounts --json` 的 `mediaAccountName`）                  |
| `name`                  | ✅   | string   | 广告系列名称                                                              |
| `budget`                | ✅   | number   | 日预算，**主币种展示金额**（100 = 每天 100 USD/CNY，内部 ×100）           |
| `bidding`               | ✅   | string   | 出价策略：`TARGET_SPEND` \| `MANUAL_CPC` \| `TARGET_CPA` \| `TARGET_ROAS` |
| `locationIds`           | ✅   | string[] | 地理位置 ID 数组（`ad geo search` 获取）                                  |
| `adgroupName`           | ✅   | string   | 第一个广告组名称                                                          |
| `maxCpc`                | ✅   | number   | 第一个广告组最高 CPC，主币种展示金额（1.5 = 1.50 USD，内部 ×100）         |
| `bidCeiling`            | ✅   | number   | TARGET_SPEND 出价上限（主币种，内部 ×100）                                |
| `targetCpa`             | ✅   | number   | TARGET_CPA 目标 CPA（主币种，内部 ×100）                                  |
| `targetRoas`            | ✅   | number   | TARGET_ROAS 目标 ROAS（如 2.5）                                           |
| `languageIds`           | ✅   | string[] | 语言 ID 数组（默认 `["1000"]` = 英语，中文 = `"1017"`）                   |
| `startDate` / `endDate` | ✅   | string   | 日期 YYYY-MM-DD（默认：今天 / 2037-12-30）                                |
| `url`                   | ✅   | string   | 落地页 URL                                                                |
| `status`                | ✅   | string   | `Enabled` \| `Paused`（默认 Enabled）                                     |
| `matchType`             | ✅   | string   | 默认匹配类型：`BROAD` \| `PHRASE` \| `EXACT`                              |
| `keywords`              | ✅   | string[] | 第一个广告组关键词                                                        |
| `headlines`             | ✅   | string[] | 标题数组，至少 3 条，推荐 15 条，每条 ≤ 30 字符，**元素内允许含逗号**     |
| `descriptions`          | ✅   | string[] | 描述数组，至少 2 条，推荐 4 条，每条 ≤ 90 字符                            |
| `finalUrl`              | ✅   | string   | 广告落地页                                                                |
| `path1` / `path2`       | ✅   | string   | 展示 URL 路径（各 ≤ 15 字符）                                             |
| `productWords`          | ✅   | string[] | 推广产品词（用于 AI 关键词推荐）                                          |
| `negativeKeywords`      | ✅   | string[] | 否定关键词数组（默认 BROAD 匹配）                                         |
| `extensions`            | ✅   | array    | 广告附加功能（CALL / SITELINK / STRUCTURED_SNIPPET），见 Schema           |
| `extraAdGroups`         | ✅   | array    | 额外广告组，追加到 AdGroupsForBatchJob，见 Schema                         |
| `draft`                 | ✅   | boolean  | `true` = 仅保存草稿（需后续 `ad batch publish` 发布）                     |

---

### 命令行直接传参（简单场景适用）

所有参数也可以直接通过 CLI 选项传入（复杂场景推荐用 `--config-file`）：

| 选项                                           | 必填 | 说明                                                                  |
| ---------------------------------------------- | ---- | --------------------------------------------------------------------- |
| `-a, --account <id>`                           | ✅\* | Google 账户 mediaCustomerId（\*使用 `--config-file` 时可从文件读取）  |
| `--customer-name <name>`                       | ✅\* | 账户名称                                                              |
| `--name <name>`                                | ✅\* | 广告系列名称                                                          |
| `--budget <amount>`                            | ✅\* | 日预算（主币种展示金额）                                              |
| `--bidding <strategy>`                         | ✅\* | 出价策略                                                              |
| `--location-ids <ids>`                         | ✅\* | 地理位置 ID，逗号分隔                                                 |
| `--adgroup-name <name>`                        | ✅\* | 第一个广告组名称                                                      |
| `--max-cpc <amount>`                           | ✅\* | 最高 CPC（主币种展示金额）                                            |
| `--keywords <kws>`                             | —    | 关键词，逗号分隔                                                      |
| `--headlines <titles>`                         | —    | 广告标题，逗号分隔（⚠️ 标题内不能含逗号，含逗号请用 `--config-file`） |
| `--descriptions <descs>`                       | —    | 广告描述，逗号分隔                                                    |
| `--product-words <words>`                      | —    | 产品词，逗号分隔                                                      |
| `--negative-keywords <kws>`                    | —    | 否定关键词，逗号分隔                                                  |
| `--extensions-json <json>`                     | —    | 附加功能 JSON 数组字符串                                              |
| `--extra-adgroups-json <json>`                 | —    | 额外广告组 JSON 数组字符串                                            |
| `--lang-ids <ids>`                             | —    | 语言 ID，逗号分隔（默认 1000=英语）                                   |
| `--bid-ceiling / --target-cpa / --target-roas` | —    | 出价相关参数                                                          |
| `--start / --end`                              | —    | 日期 YYYY-MM-DD                                                       |
| `--url / --final-url`                          | —    | 落地页                                                                |
| `--path1 / --path2`                            | —    | 展示路径                                                              |
| `--status`                                     | —    | Enabled \| Paused                                                     |
| `--draft`                                      | —    | 仅保存草稿                                                            |
| `--config-file <path>`                         | —    | JSON 配置文件路径（AI 推荐）                                          |

**典型用法（简单场景）：**

```bash
# 前置：搜索投放地区 ID
siluzan-tso ad geo search -a 6326027735 -q "United States"
# 取出 id 字段，如 2840

# 一体化创建（CLI 直接传参，适合参数较少的场景）
siluzan-tso ad campaign-create \
  -a 6326027735 \
  --customer-name "测试账户" \
  --name "搜索-跑步鞋-2026" \
  --budget 100 \
  --bidding TARGET_SPEND \
  --location-ids 2840 \
  --adgroup-name "核心词_跑步鞋" \
  --max-cpc 5 \
  --url "https://www.brand-a.com/running-shoes" \
  --keywords "running shoes,sport shoes,trail running" \
  --headlines "Brand Running Shoes,Lightweight Design,Direct Factory Price" \
  --descriptions "Trusted by millions worldwide.,Free shipping and 30-day returns." \
  --final-url "https://www.brand-a.com/running-shoes" \
  --path1 "running" \
  --path2 "shoes"

# 查看创建进度
siluzan-tso ad batch get --id <taskId>
```

**典型用法（AI 推荐，config-file 方式）：**

```bash
# 1. AI 先写好 JSON 配置文件（使用 Write 工具）
# 2. 执行创建
siluzan-tso ad campaign-create --config-file /tmp/campaign-config.json

# 3. 查看进度
siluzan-tso ad batch get --id <返回的taskId>
```

---

## ad campaign-edit — 广告系列编辑

```bash
siluzan-tso ad campaign-edit \
  -a <accountId> \
  --id <campaignId> \
  [--name <新名称>] \
  [--budget <预算（最小货币单位）>] \
  [--bidding <出价策略>] \
  [--bid-ceiling <出价上限>] \
  [--search-network true|false] \
  [--content-network true|false]
```

| 选项                | 说明                                                                      |
| ------------------- | ------------------------------------------------------------------------- |
| `--name`            | 新广告系列名称                                                            |
| `--budget`          | 新预算，最小货币单位（如 100000 = 1 USD）                                 |
| `--bidding`         | 出价策略：`TARGET_SPEND` \| `TARGET_CPA` \| `TARGET_ROAS` \| `MANUAL_CPC` |
| `--bid-ceiling`     | `TARGET_SPEND` 出价上限（最小货币单位，0 = 不限）                         |
| `--target-cpa`      | `TARGET_CPA` 目标 CPA                                                     |
| `--search-network`  | 投放 Google 搜索：`true` \| `false`                                       |
| `--content-network` | 投放展示网络：`true` \| `false`                                           |

**示例：**

```bash
# 修改名称和预算
siluzan-tso ad campaign-edit -a 6326027735 --id 23509626948 \
  --name "搜索-春季促销-2026" --budget 500000

# 切换出价策略为 TARGET_CPA，目标 CPA 2 USD
siluzan-tso ad campaign-edit -a 6326027735 --id 23509626948 \
  --bidding TARGET_CPA --target-cpa 200000
```

---

## ad adgroup-rename — 广告组改名

```bash
siluzan-tso ad adgroup-rename \
  -a <accountId> \
  --id <adGroupId> \
  --name <新名称>
```

**示例：**

```bash
siluzan-tso ad adgroup-rename -a 6326027735 --id 195548094874 --name "核心词_跑步鞋_改"
```

---

## ad ad-edit — 广告创意编辑（自适应搜索广告 RSA）

与网页端一致：先按日期范围从 **`GET {googleApi}/admanagement/v2/list/{account}`** 拉取该广告完整对象，再 **`PUT {googleApi}/admanagement/campaign/{account}/{adId}`** 提交合并后的 JSON。成功时响应体与请求体字段结构一致（含 `id`、`activeuseridg`、`typeV2`、`statusV2` 等）。

CLI 会在请求前自动设置 **Datapermission**（与浏览器 `datapermission` 头同源逻辑），避免网关侧权限相关错误。

### 网关 JSON 与 CLI 参数对应（常用字段）

| 网关字段                                            | 说明                                    | CLI                                         |
| --------------------------------------------------- | --------------------------------------- | ------------------------------------------- |
| `id`                                                | 广告 ID                                 | `--id`                                      |
| `activeuseridg`                                     | 账户 mediaCustomerId                    | `-a` / `--account`                          |
| `headlinePart1` / `headlinePart2` / `headlinePart3` | 前 3 条标题                             | `--headlines` 前 3 项                       |
| `AddtionalHeadlines`                                | 第 4～15 条标题（网关拼写为 Addtional） | `--headlines` 第 4 项起                     |
| `adDescription` / `adDescription2`                  | 前 2 条描述                             | `--descriptions` 前 2 项                    |
| `AddtionalAdDescriptions`                           | 第 3～4 条描述                          | `--descriptions` 第 3 项起                  |
| `finalUrl`                                          | 落地页                                  | `--final-url`                               |
| `path1` / `path2`                                   | 显示路径                                | `--path1` / `--path2`                       |
| `adGroupId` / `adGroup`                             | 广告组                                  | 从列表结果保留，勿手改                      |
| `typeV2`                                            | 广告类型                                | 从列表保留（RSA 为 `RESPONSIVE_SEARCH_AD`） |
| `statusV2`                                          | `Enabled` / `Paused`                    | `--status Enabled` 或 `--status Paused`     |

**约束：** 至少指定一项：`--headlines` / `--descriptions` / `--final-url` / `--path1` / `--path2` / `--status`。若传 `--headlines` 须 ≥3 条；若传 `--descriptions` 须 ≥2 条。

```bash
siluzan-tso ad ad-edit \
  -a <accountId> \
  --id <adId> \
  [--headlines "标题1,标题2,标题3,..."] \
  [--descriptions "描述1,描述2,..."] \
  [--final-url <落地页>] \
  [--path1 <路径1>] \
  [--path2 <路径2>] \
  [--status Enabled|Paused]
```

**与 curl 等价的网页请求形态（示意，勿把真实 Token 写入文档或仓库）：**

```http
PUT {googleApi}/admanagement/campaign/{activeuseridg}/{id}
Content-Type: application/json

{
  "id": "<adId>",
  "activeuseridg": "<account>",
  "headlinePart1": "...",
  "headlinePart2": "...",
  "headlinePart3": "...",
  "adDescription": "...",
  "adDescription2": "...",
  "adGroupId": "...",
  "adGroup": "...",
  "finalUrl": "https://...",
  "path1": "...",
  "path2": "...",
  "typeV2": "RESPONSIVE_SEARCH_AD",
  "statusV2": "Paused"
}
```

**示例：**

```bash
# 只更新标题
siluzan-tso ad ad-edit -a 6326027735 --id 795205788626 \
  --headlines "专业跑步鞋,轻量透气设计,品牌直销价,全球热销款,运动首选品牌"

# 更新落地页
siluzan-tso ad ad-edit -a 6326027735 --id 795205788626 \
  --final-url "https://www.brand-a.com/shoes-2026"

# 仅暂停广告（与网页改状态一致，其余字段从列表原样带回）
siluzan-tso ad ad-edit -a 6326027735 --id 802428202775 --status Paused
```

---

## ad keyword-delete — 搜索关键词删除

与网页一致：**`DELETE {googleApi}/keywordmanagement/Keyword/{account}/batch`**，请求体为 **JSON 数组**，每项至少包含 **`adGroupId`**、**`id`**（关键词资源 id）。成功时 HTTP 2xx 下 **响应体常为空**，属正常现象；CLI 只要未报错即表示删除请求已送达网关。请求前会自动设置 **Datapermission**；DELETE 使用带 **Content-Length** 的原始请求，避免部分网关对带 body 的 DELETE 解析异常。

```bash
siluzan-tso ad keyword-delete \
  -a <accountId> \
  --id <keywordId> \
  --adgroup-id <adGroupId>
```

> `--id` 与 `--adgroup-id` 来自 `ad keywords --json` 的 `id`、`adGroupId`（与网关字段名一致）。

**与 curl 等价的请求形态（示意）：**

```http
DELETE {googleApi}/keywordmanagement/Keyword/{account}/batch
Content-Type: application/json

[{"adGroupId":"193360670606","id":"2474194779750"}]
```

**示例：**

```bash
# 先查询获取 id 和 adGroupId
siluzan-tso ad keywords -a 6326027735 --json

# 然后删除
siluzan-tso ad keyword-delete -a 6326027735 --id 2464982882313 --adgroup-id 195548094874
```

---

## ad keyword-edit — 搜索关键词编辑

与网页一致：**先**按日期范围从 **`GET {googleApi}/keywordmanagement/v2/list/{account}`** 取该关键词完整对象，**再** **`PUT {googleApi}/keywordmanagement/Keyword/{account}/batch`**，请求体为 **JSON 数组**（通常一条），元素为合并后的关键词对象。CLI 会自动设置 **Datapermission**。

### 网关字段与 CLI 对应（常用）

| 网关字段                      | 说明                                      | CLI                          |
| ----------------------------- | ----------------------------------------- | ---------------------------- |
| `id`                          | 关键词资源 id                             | `--id`                       |
| `keywordText`                 | 关键词文案（数组，一般一项）              | `--text` → `["..."]`         |
| `matchTypeV2`                 | 匹配类型（网页用 Broad / Phrase / Exact） | `--match-type`               |
| `matchType`                   | 另一套枚举（如 EXACT），列表里可能仍存在  | 一般随 list 结果保留，勿手改 |
| `maxCPC`                      | 最高每次点击费用                          | `--max-cpc`                  |
| `finalURL`                    | 关键词级最终到达网址                      | `--final-url`                |
| `adGroupId` / `campaignId` 等 | 层级与统计字段                            | 从列表保留                   |

**注意：** 成功响应也是数组；**`id` 可能与请求不一致**（网关可能返回新资源 id）。CLI 若检测到变化会打印提示，后续请用 **返回体中的新 `id`** 再查列表或再编辑。

**约束：** `--text`、`--match-type`、`--max-cpc`、`--final-url` 至少传一项。

```bash
siluzan-tso ad keyword-edit \
  -a <accountId> \
  --id <keywordId> \
  [--text <新关键词>] \
  [--match-type <Broad|Phrase|Exact>] \
  [--max-cpc <n>] \
  [--final-url <url>]
```

**与 curl 等价的请求形态（示意，勿写入真实 Token）：**

```http
PUT {googleApi}/keywordmanagement/Keyword/{account}/batch
Content-Type: application/json

[
  {
    "id": "<keywordId>",
    "keywordText": ["广告工具1"],
    "matchType": "EXACT",
    "matchTypeV2": "Broad",
    "maxCPC": 0,
    "finalURL": "https://example.com",
    "adGroupId": "...",
    "campaignId": "...",
    "...": "其余字段来自 list 接口"
  }
]
```

**示例：**

```bash
# 改匹配类型为精确匹配
siluzan-tso ad keyword-edit -a 6326027735 --id 310074153549 --match-type Exact

# 同时改文本和匹配类型
siluzan-tso ad keyword-edit -a 6326027735 --id 310074153549 \
  --text "professional running shoes" --match-type Phrase

# 与网页一致：改落地页与出价（maxCPC 为 0 时含义以 Google/平台为准）
siluzan-tso ad keyword-edit -a 6326027735 --id 2081924039951 \
  --final-url "https://www-ci.siluzan.com" --max-cpc 0
```

---

## ad keyword-negative-edit — 否词编辑

```bash
siluzan-tso ad keyword-negative-edit \
  -a <accountId> \
  --id <negativeKeywordId> \
  [--text <新文本>] \
  [--match-type <Broad|Phrase|Exact>]
```

**示例：**

```bash
siluzan-tso ad keyword-negative-edit -a 6326027735 --id 349349835545 \
  --text "cheap shoes" --match-type Phrase
```

---

## ad extension — 附加信息管理

附加信息（Ad Extensions）支持四种类型，**修改方式为先删后建**（无 PUT 编辑接口）。

### 查询附加信息列表

```bash
siluzan-tso ad extension list -a <accountId> [--type SITELINK|CALL|CALLOUT|STRUCTURED_SNIPPET]
```

### 添加附加链接（SITELINK）

```bash
siluzan-tso ad extension sitelink \
  -a <accountId> \
  --text "产品中心" \
  --url "https://www.example.com/products" \
  [--line2 "查看全系列产品"] \
  [--line3 "限时优惠进行中"] \
  [--level Account|Campaign|AdGroup] \
  [--campaign-id <id>]
```

### 添加附加电话（CALL）

```bash
siluzan-tso ad extension call \
  -a <accountId> \
  --country-code "+86" \
  --phone "4008001234" \
  [--level Account|Campaign|AdGroup]
```

### 添加附加宣传信息（CALLOUT，≤25 字符）

```bash
siluzan-tso ad extension callout \
  -a <accountId> \
  --text "免费送货上门" \
  [--level Account]
```

### 添加附加结构化摘要（STRUCTURED_SNIPPET）

```bash
siluzan-tso ad extension snippet \
  -a <accountId> \
  --header "Brands" \
  --values "品牌A,品牌B,品牌C" \
  [--level Account]
```

> `--header` 常用值：`Brands` | `Services` | `Amenities` | `Types` | `Styles` | `Courses` | `Featured hotels` | `Neighborhoods` | `Destinations` | `Degree programs` | `Insurance coverage` | `Models`

### 删除附加信息

```bash
# 先查 id
siluzan-tso ad extension list -a 6326027735 --json

# 再删除
siluzan-tso ad extension delete -a 6326027735 --id <extensionId>
```

---

## ad search-terms — 搜索字词报告

> 搜索字词为**只读报告**，不支持直接删除。若需屏蔽某个搜索词，先查到对应词，再通过 `keyword-negative-create` 将其加为否词。

```bash
siluzan-tso ad search-terms -a <accountId> [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```

**示例：**

```bash
# 查询近 30 天搜索字词
siluzan-tso ad search-terms -a 6326027735

# 查询指定区间
siluzan-tso ad search-terms -a 6326027735 --start 2026-03-01 --end 2026-03-23

# JSON 输出（可获取 campaignId/adGroupId 用于添加否词）
siluzan-tso ad search-terms -a 6326027735 --json
```

**搜索字词转否词示例（屏蔽无效流量）：**

```bash
# 1. 查到不想投放的搜索字词，记录其 campaignId 和 adGroupId
siluzan-tso ad search-terms -a 6326027735 --json

# 2. 在广告系列层级将其加为否词
siluzan-tso ad keyword-negative-create \
  -a 6326027735 \
  --campaign-id 23509626948 \
  --campaign-name "搜索-ces-1769764388" \
  --keywords "不想要的词1,不想要的词2"
```

---

## ad geo — 地理位置定向管理

### 搜索地理位置（获取 locationId）

```bash
siluzan-tso ad geo search -a <accountId> -q <地名>
```

```bash
# 搜索中国
siluzan-tso ad geo search -a 6326027735 -q "China"

# 搜索北京
siluzan-tso ad geo search -a 6326027735 -q "Beijing"
```

### 查询已定向地理位置

```bash
# 查已定位（普通定向）
siluzan-tso ad geo list -a 6326027735 --mode targeted

# 查已排除（否定定向）
siluzan-tso ad geo list -a 6326027735 --mode excluded

# 查消耗报告（哪些地区产生了展示/点击）
siluzan-tso ad geo list -a 6326027735 --mode report --start 2026-03-01 --end 2026-03-23
```

### 添加地理位置定向

```bash
# 添加普通定向（先 search 获取 locationId）
siluzan-tso ad geo add \
  -a 6326027735 \
  --campaign-id 23509626948 \
  --location-id 2156 \
  [--bid-modifier 1.2]

# 添加排除定向
siluzan-tso ad geo add \
  -a 6326027735 \
  --campaign-id 23509626948 \
  --location-id 1006093 \
  --exclude
```

### 删除地理位置定向

```bash
# 普通定向和排除定向均通过 geo remove 删除
siluzan-tso ad geo remove \
  -a 6326027735 \
  --campaign-id 23509626948 \
  --location-id 2156
```

---

## 完整操作示例：从零搭建 Google 广告

以下是一个完整的从头建立 Google 广告的操作示例：

```bash
# 第二步：查询账户, 确认用户信息
siluzan-tso list-accounts -m Google --json -k [mediaCustomerId]
# 假设 accountId = 6326027735

# 第三步：查看现有广告系列，确认 campaign_id
siluzan-tso ad campaigns -a 6326027735 --json
# 假设 campaignId = campaign_001，campaignName = "品牌推广_春季"

# 第四步：创建广告组（最高 CPC 1 USD = 100000 微单位）
siluzan-tso ad adgroup-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --name "核心词_跑步鞋" \
  --max-cpc 100000

# 第五步：查询新建广告组 id
siluzan-tso ad groups -a 6326027735 --json
# 假设 adGroupId = adgroup_new，adGroupName = "核心词_跑步鞋"

# 第六步：添加关键词
siluzan-tso ad keyword-create \
  -a 6326027735 \
  --campaign-id campaign_001 \
  --campaign-name "品牌推广_春季" \
  --adgroup-id adgroup_new \
  --adgroup-name "核心词_跑步鞋" \
  --keywords "跑步鞋,专业跑鞋,running shoes"

# 第七步：创建广告创意
siluzan-tso ad ad-create \
  -a 6326027735 \
  --adgroup-id adgroup_new \
  --adgroup-name "核心词_跑步鞋" \
  --final-url "https://www.brand-a.com/running-shoes" \
  --headlines "专业跑步鞋,轻量透气设计,品牌直销价" \
  --descriptions "全球百万跑者信赖，专业助力每一步。,免费配送，30天无理由退换。" \
  --path1 "跑步鞋" \
  --path2 "特惠"

# 第八步：验证广告已创建
siluzan-tso ad list -a 6326027735
```
