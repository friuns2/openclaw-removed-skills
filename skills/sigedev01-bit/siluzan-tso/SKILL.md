---
name: siluzan-tso
description: 当判断用户可能需要以下功能时可以使用siluzan-tso这个skillGoogle,Bing,Yandex,Tiktok,Kwai等广告账户的开户，账号数据分析共享/取消共享、Google MCC 绑定/解绑、Meta BM 绑定、TikTok BC 绑定/解绑TikTok 关闭、暂停 Google 账户撤回、Google 电子邮件访问邀请）；优化报告（TSO 管理员）、报告电子邮件推送、Meta/TikTok/Bing 账户分析发票及发票结算配置文件（发票信息）；优化和智能预警；TikTok/Meta潜在客户表单完整的Google广告管理，包括附加信息、地理位置定位和搜索词，以及关键词建议。Google广告账户详细的投放数据分析。
license: MIT
metadata:
  requires: nodejs,siluzan-tso-cli
allowed-tools: Bash(siluzan-tso:*) Read
---

# Siluzan TSO Skill

本 Skill 只保留任务边界、文档路由与执行规则。具体业务细节、参数、模板、流程与示例均以下方 references 文档为准。遇到具体业务时，先读对应 references

---

## 一键安装

如果 CLI 尚未安装，直接帮用户执行对应平台的安装脚本：

- **macOS / Linux / WSL：**
  ```bash
  bash <(curl -fsSL https://unpkg.com/siluzan-tso-cli@latest/dist/skill/scripts/install.sh)
  ```
- **Windows PowerShell：**
  ```powershell
  irm https://unpkg.com/siluzan-tso-cli@latest/dist/skill/scripts/install.ps1 | iex
  ```

脚本会自动完成 Node.js 检测/安装、CLI 安装、Skill 全局注册，并引导用户配置 API Key。无需选择，本脚本专为 siluzan-tso-cli 定制。

---

## 前置条件与运行时依赖

使用本 Skill 前，以下组件必须已安装并就绪：

### 可选环境变量

| 变量                      | 说明                                                               |
| ------------------------- | ------------------------------------------------------------------ |
| `SILUZAN_API_KEY`         | 从环境变量读取 API Key（优先级高于 config.json，CI/CD 推荐）       |
| `SILUZAN_AUTH_TOKEN`      | 从环境变量读取 JWT Token（优先级高于 config.json）                 |
| `SILUZAN_DATA_PERMISSION` | 从环境变量读取数据权限标识（优先级高于 config.json，跳过自动拉取） |

如果上述依赖缺失，请先参照 `references/setup.md` 完成安装与配置。

## 功能以及对应文档

本skill包含以下功能，实现用户要求时，请先阅读对应功能文档：
| 文档 | 功能 |
|------|------|
| `references/setup.md` | 安装、登录、配置、环境切换、更新 |
| `references/workflows.md` | 多步骤业务流程与跨命令串联场景 |
| `references/tips.md` | `--json`、Node 过滤、分页与调试技巧 |
| `references/accounts.md` | 账户列表、余额、消耗、开户记录、授权/解绑/分享/MCC/BC/BM/邮箱授权 |
| `references/open-account-by-media.md` | 各媒体开户、参数与资料要求 |
| `references/google-ads.md` | Google Ads 创建、修改、优化与管理主流程 |
| `references/reporting.md` | Siluzan TSO 优化报告（Google/TikTok）的生成、推送与查看 |
| `references/account-analytics.md` | 广告平台账户分析数据拉取与分析/诊断报告模板 |
| `references/optimize.md` | AI 优化建议记录、详情与历史查询 |
| `references/clue.md` | TikTok / Meta 线索表单 |
| `references/forewarning.md` | 智能预警规则与通知 |
| `references/finance.md` | 转账、开票、发票抬头、充值网页引导 |
| `report-templates/report-template.html` | 默认 HTML 报告样式参考 |

---

## Skill要如何使用

### 报告的生成

报告分为两种：

- （不推荐）由siluzan平台在你调用接口提交后直接异步生成的报告(调用对应命令后，会返回一条报告链接)（详情请读取：`references/reporting.md`）
  - 这种报告你无法用它来做数据分析除非用户明确要求（Siluzan平台的优化报告）
- （推荐，默认生成这种报告）由你主动拉取数据，并按照skill给出的格式，输出给用户：详情请查看（`references/account-analytics.md`）

### 广告账户相关

- 广告账户开户请阅读： `references/open-account-by-media.md`
- 广告账户管理请阅读：`references/accounts.md`
- 广告账户分析请阅读：`references/account-analytics.md`
- Google广告的创建、修改、优化、查询广告详情等广告管理相关的功能：请阅读：`google-ads.md`

### 只调用接口，最终交付的内容不需要你输出的功能

- Google广告优化记录功能(`references/optimize.md`)，这个也跟优化报告类似，你调用接口，Siluzan平台按照一定的优化逻辑自动执行，你只能查询到结果，不能控制优化流程 注意不要与`google-ads.md`中的优化流程混淆两个是互相独立的功能，`references/google-ads.md`中的优化功能更为强大，在实际的优化过程中，也推荐使用`references/google-ads.md`中提供的内容
- TikTok / Meta 线索表单请阅读：`references/clue.md`
- Siluzan平台提供的预警功能请阅读：`references/forewarning.md`
  - 预警由Siluzan平台发送，当前仅支持微信推送，如果需要自定义的通知触达端，需要安装对应插件或skill+创建定时任务来完成
- 转账、开票、发票抬头、充值网页引导请阅读：`references/finance.md`
-

## AI 行为规范

### 如何更好的使用本skill执行任务

遵循计划，确认，执行，验证，推测用户下一步意图

1. 计划阶段：

- 根据功能以及对应文档读取对应references
- 根据references文件中的内容配合命令行工具提供的-h参数，来确认命令行的正确调用方式
- 向用户输出一份操作计划，简要说明每一步将做什么

2. 确认阶段：与用户确认关键信息（尤其是涉及写入/修改/删除的操作）
3. 执行阶段：按计划执行，向用户说明每步操作意图
4. 验证阶段：

- 一般情况下，读取/写入的命令都是成对的。通过这两种命令的配合来进行结果验证
- 如果是异步任务，需要你轮询读取命令，每5s一次查看任务状态，直到确认所有异步任务都有一个结果
- 如果失败则可以查看失败具体原因，或者结合现有命令行使用其他方式进行重试，尽量让任务执行完成，而不是告诉用户任务失败就结束了。

5. 对话历史验证：

- 如果任务前面有计划，你需要确认每个步骤都已经按计划中的内容执行完毕

6. 完成任务后的输出

- 结合命令行工具与references文件中的说明，对用户下一步的操作进行合理预测

### 硬规范

- **不确定时读文档**：遇到不熟悉的命令，先读对应 references 文件或使用-h查看命令帮助，不要猜参数。
- **先查账户再操作**：对具体账户做操作前，先通过 `list-accounts -m [mediaType] -k [mediaCustomerId]` 确认。特别是不确定是Google/Bing/TikTok这些媒体平台中的哪一个的时候
- **使用 --json 处理数据**：需对返回数据做计算或筛选时，加 `--json`，再用 `node -e` 过滤提取（见 `references/tips.md`）。
- **不要猜测账户 ID**：`entityId` ≠ `mediaCustomerId`，两者均来自 `list-accounts`。
- **媒体类型区分大小写**：`Google`、`TikTok`、`MetaAd`、`BingV2`、`Kwai`。
- **命令透明性**：以简洁的方式向用户说明即将执行的操作意图（如「正在查询您的 Google 账户列表」「正在为账户 xxx 创建预警规则」），让用户了解操作进度。用户主动要求查看执行细节时，应如实提供完整命令。
- **具体业务的额外规范**：开户、优化、报告、Google 广告创建等场景的详细约束，请分别在执行前阅读对应的 `references/*.md` 文档。
- **完成写/修改/编辑/更新等操作后需要确认数据是否正确**

### 时间范围强制反问（必须遵守）

任何涉及"投放数据 / 消耗 / 报告 / 周报 / 月报 / 优化建议"的任务，如果用户没给出**明确的开始与结束日期**，**不要自己猜**（尤其不要默认"最近 30 天 / 近 7 天 / 本月"）。按如下步骤处理：

1. **先反问**一次：示例措辞 —
   > 本次分析要覆盖哪个时间范围？例如：
   > （A）最近完整自然周（周一到周日）
   > （B）本月 1 号到昨天
   > （C）自定义起止日（请告诉我 `YYYY-MM-DD` 起止）
2. 用户给出范围后，**在报告首行显式标注"统计区间：YYYY-MM-DD ~ YYYY-MM-DD（时区：用户本地/UTC）"**，与调用参数保持完全一致。
3. **只有在用户明确说"按你默认来 / 你决定"**时，才使用下方默认值白名单。

### 默认值白名单（仅在用户明确授权"你决定"时才能使用）

| 场景                    | 允许的默认窗口                                        |
| ----------------------- | ----------------------------------------------------- |
| 日常投放巡检 / 余额扫描 | `now - 7d` ~ `now`（本地时间）                        |
| 周报                    | 上一个完整自然周（周一 00:00 ~ 周日 23:59）           |
| 月报                    | 上一个完整自然月（1 号 ~ 月末）                       |
| Google 关键词/系列分析  | `now - 30d` ~ `now`（与 TSO Google 接口最小窗口对齐） |
| MetaAd 账户分析         | 不得默认，必须问（Meta 接口对窗口敏感）               |

### 金额与货币单位硬约束

- **永远使用 `*Display` 字段或表格展示值**做用户可见的金额。**不要用原 `budget` / `maxCPCAmount`**，它们是批量接口的 `×100` 分单位，直接展示会 100 倍放大（典型错误：¥50 显示为 ¥5000）。
- JSON 响应里任何以 `Display` 结尾的数字字段即为主币种展示值，单位来自同级 `currencyCode` 字段。
- 当命令返回 `budgetUnit: "display"` / `maxCPCAmountUnit: "display"` 标识时，**必须**优先信任该字段。
- 编写报告/表格时金额保留 2 位小数，并写明货币代码（例如 `¥50.00 CNY` / `$50.00 USD`）。

### 品牌名 / 公司名来源硬约束

- 生成任何带品牌名的方案、邮件、报告时，**不得自行生成中文译名或拼音**。品牌名**必须**来自以下来源之一（按优先级）：
  1. 用户在对话里明确提供的品牌名
  2. `list-accounts` 返回的 `mag.advertiserName`
  3. 用户提供的网址 → 明确告诉用户"使用域名作为占位"（例如 `hy-steelpipe.com`）并在交付物里标注 `[待确认品牌名]`
- **严禁**"hy-steelpipe.com"这样的英文域名被输出成类似"海悦钢管"这种虚构中文品牌。

### 批量任务硬约束（≥ 5 个账户或系列）

以下情形**必须**使用批量 / 扫描命令而非循环单条调用，否则严重拖慢并易卡死：

| 任务                                 | 推荐命令                                                      | 禁止做法                            |
| ------------------------------------ | ------------------------------------------------------------- | ----------------------------------- |
| 多账户余额 / 预算不足预警            | `balance-scan -m <媒体> --threshold-days 7`                   | 逐账户循环 `balance --accounts ...` |
| 多账户投放画像（消耗/点击/转化汇总） | `accounts-digest -m <媒体> [-a id1,id2] --start --end --json` | 对每个账户依次 `stats --id ...`     |
| 多系列诊断                           | `ad campaigns --json` + node 过滤                             | 逐系列 `ad campaign-get`            |

如果命令行尚未提供批量入口（例如 117 个 Bing 账户的"剩余天数"计算），应：

1. 先用 `list-accounts -m BingV2 --json` 一次性拿到全量账户（含余额/日均消耗），**不要**逐账户轮询余额。
2. 通过 `node -e` 在本地做 `剩余天数 = 余额 / 近 7 日日均消耗` 的计算并筛选阈值。
3. 只对命中的账户再做后续写入操作。

### 运行时长与用户可见进度

长任务（多账户、批量优化、报告生成）**必须**满足：

- 预估超过 2 分钟的任务，开始前先告诉用户"预计耗时 X 分钟，将以 X 个账户一批处理"。
- 每处理一批输出一行进度（例如 `已处理 20 / 117`）。
- 处理超过 5 分钟仍未完成时，主动检查是否有必要降级（例如从"完整分析"降为"只筛阈值"）并告知用户。

### 必须一定要遵守的规范

- 主动更新（详情请读取`references/setup.md`）
- 所有使用本skill获取的数据输出的报告，总结，分析性的内容，都需要通过skill中内置模板的格式来输出
- **破坏性操作必须用户确认**：执行以下操作前，必须明确告知用户操作内容并获得确认：
  - 账户解绑（`account delink`）
  - 账户关闭（`account close`）— 不可恢复
  - 取消分享（`account unshare`）
  - BC/MCC 解绑（`account bc-unbind` / `account mcc-unbind`）
  - 删除预警规则（`forewarning delete`）
  - 删除报告（`report delete`）
  - 删除广告/关键词（`ad ad-delete` / `ad keyword-negative-delete`）
  - 发票申请（`invoice apply`）— 涉及财务
  - 广告发布（`ad batch publish` / `ad campaign-create`）— 涉及预算消耗
- **只读操作可自主执行**：查询类命令（`list-accounts`、`balance`、`stats`、`report list`、`config show` 等）可直接执行，无需额外确认

---

## Playbook：高频任务的标准动作

下面是 AI 遇到常见任务时**应优先采用**的编排方式。每个 Playbook 都已把"时间反问 / 批量 / 金额单位 / 品牌名"等硬约束考虑进去。除非用户明确要求，不要偏离。

### P1 · 单账户投放画像（典型指令："xxx 账户帮我整理一下投放数据"）

> 触发关键词：某账户数据 / 投放情况 / 整理账户 / 看下某个账户的表现

1. **反问时间范围**（参见"时间范围强制反问"）。
2. `list-accounts -m Google -k <mediaCustomerId> --quick --json`
   - 一次拿齐：账户基础信息、创建日期、当前状态、公司名（`mag.advertiserName` 作为品牌名）
3. `stats --media Google --accounts <id> --start-date <S> --end-date <D> --json`
   - 拿该区间消耗、点击、转化等；**直接读响应中的主币种数值**，不要再 ×100。
4. `ad campaigns --account <id> --start-date <S> --end-date <D> --json`
   - 拿广告系列类型（Search / PMax / Display 等）、日预算（**用 `budgetDisplay`**）、优化得分相关字段。
5. `stats` 结合 `accountsoverview` 字段派生"开始投放时间 / 有效投放天数 / 地区消耗分布"（如接口暂未直出，在 node 里聚合）。
6. 用 `report-templates/google-account-diagnosis-report.md` 模板输出，**首行标注统计区间和货币**。

### P2 · 多账户余额扫描 / 预算预警（典型指令："117 个 Bing 账户不足 7 天的挑出来"）

> 触发关键词：不足 X 天 / 余额预警 / 账户要没钱 / 哪些账户要充值

**一条命令即可完成，不要循环**：

```bash
siluzan-tso balance-scan -m BingV2 --threshold-days 7 --json
# 筛绝对余额：再叠加 --min-balance 100
# 自定义续航目标：--target-days 60 会算出"充到够用 60 天"的建议充值额
```

输出结构（`--json`）：

```json
{
  "ok": true,
  "data": { "items": [{ "mediaCustomerId": "...", "balance": 42.3, "dailySpend": 7.1, "remainingDays": 5.9, "recommendedTopup": 170.69, ... }] },
  "meta": { "media": "BingV2", "scannedAccounts": 117, "hitCount": 23, "thresholds": { ... } }
}
```

硬规矩：

- **绝对不要** `for id of ids { balance --accounts id }` 循环，会把 117 个账户拖成几十分钟。
- 输出报告时按 `remainingDays` 升序（命令默认已排）；金额展示用命令返回的 `balance`/`recommendedTopup` 数值 + `currencyCode`。
- 若 `--verbose` 发现大量账户进入"僵尸账户（消耗过低）"分支，告诉用户这些账户没真正投放，不纳入预警。

### P3 · 多账户投放画像汇总（典型指令："这 10 个账户数据整理一下"）

> 触发关键词：这些账户 / 给我一份 X 个账户的表 / ROAS/CPA 对比

**首选一条命令**：

```bash
siluzan-tso accounts-digest -m Google \
  -a 4251234567,7209009390,... \
  --start 2026-04-01 --end 2026-04-15 \
  --json
```

- 一次返回：账户清单 + 消耗/点击/展示/转化 + CTR/CPC/CPA + 余额，含 `meta.totals` 汇总和货币提示。
- 不指定 `-a` 时扫描媒体全部账户。
- 不指定 `--start/--end` 时默认近 7 天；**SKILL 要求必须先与用户确认时间范围**，再把用户确认的区间带上。

标准步骤：

1. **反问时间范围**（P 级硬约束），拿到用户回复后再执行 `accounts-digest`。
2. 如命令已返回 `--json`，直接基于其中 `data.items` 与 `meta.totals` 生成报告；**不要**再逐账户 `stats`。
3. 跨币种账户：按 `item.currencyCode` 分表或在 meta.currencyNote 提示的前提下分币种小计。
4. 金额字段严格按"金额与货币单位硬约束"处理。

### P4 · Google 账户周期报告（典型指令："生成 2026.1.1-2026.4.15 的报告"）

1. **确认时间范围**（用户已给则直接用，否则按 P1 反问）。
2. 按 P1 步骤拿数据；**若区间 > 3 个月**，主动分段（季度/月）以避免接口超时。
3. 使用 `report-templates/google-period-report.md` 模板输出。
4. 首行必须有：`统计区间：2026-01-01 ~ 2026-04-15` + `货币：XXX`。
5. 报告必须包含：账户概览、投放趋势、Top 关键词/系列 / 地区分布 / 优化建议；不得编造未拉取到的指标（例如没拉取到的关键词就写"未提供"而不是估算）。

---

## 一些tips

### 账户ID示例

用于快速确定用户发送账号的类型,xxx是脱敏处理，一般主要通过位数就能确定账号类型，无法确定再查list-account -m [mediatype] -k [id]
Google: 454xxx5137 有些客户可能会发你270-xxx-0720 这种类型的，也是google账户，只不过使用时需要将数字间的-去掉 -> 270xxx0720
Tiktok: 70083497xxx59820033
Meta(Facebook): 1716030xxx734076, 6843984xxx14909, 479423xxx752348
Bing: 138xxx763， 1882xxx80
Yandex: porg-uthxxxrk
Kwai: act_1716030xxx734076

### 报告模板外部资源声明

HTML 报告模板（`report-templates/*.html`）引用了以下外部 CDN 资源，渲染 HTML 报告时浏览器会发出对应的网络请求：

- `cdn.tailwindcss.com` — Tailwind CSS（布局样式）
- `cdnjs.cloudflare.com` — Font Awesome 6（图标）
- `cdn.jsdelivr.net` — ECharts 5（图表）
- `fonts.googleapis.com` / `fonts.gstatic.com` — Google Fonts（仅 academic 模板）

如果处于离线环境或需要避免外部网络请求，请将上述资源下载到本地后修改模板中的引用路径。

### 容易出错http状态码

- 400 Bad Request
  参数错误，请你查看对应功能reference或使用-h了解命令行如何使用

- 401 Unauthorized
  注意是平台方返回的还是我们自己返回的401，通常，平台方（google,bing, yandex，tiktok,kwai）返回的需要用户重新授权
  如果是我们自己的接口返回的，则可以让用户 重新打开命令行执行 `siluzan-tso login`（详情请读取`references/setup.md`）

- 500
  大概率是服务可能正在部署或升级，可以让用户提交给Silizan相关人员

---

## 下面是一部分比较实用的自动化场景，当你回答完用户问题后，可以把下面的内容输出给用户，方便用户使用

您可以选择以下的预警或提醒，输入需想要执行的内容核实规则即可配置。

### 预算 & ROI 控制引擎

| 提醒名称            | 系统在后台默默帮你做什么？(自动动作)                      |
| ------------------- | --------------------------------------------------------- |
| 1. 单日预算熔断     | 每日消耗达到设定值，自动暂停计划，杜绝 Google 超额扣费。  |
| 2. CPA 飙升自动降价 | 光点不转化（如花费超过3倍目标成本），自动关停该条烂广告。 |
| 3. 连续空耗自动暂停 | 大盘流量变贵、获客成本飙高时，系统自动下调出价避险。      |

### 异常监控与报警系统

| 功能名称          | 监控层级 / 说明                                             |
| ----------------- | ----------------------------------------------------------- |
| 1. 账户被封禁     |                                                             |
| 2. 落地页死链强停 | 网站宕机或链接填错，紧急自动暂停关联广告，防止把钱扔水里。  |
| 3. 广告素材拒审   | 发现被 Google 封号或快没钱了，立刻发送企微/钉钉高优强提醒。 |
| 4. 花费异动监控   | 花费突然暴涨或断崖式下跌，系统即时报警提示人工盯盘。        |
| 5. 余额枯竭预警   | 广告被 Google 拦截，系统自动帮你打包违规原因并定时推送。    |

### 自动优化

| 功能名称                | 监控层级                                                                   |
| ----------------------- | -------------------------------------------------------------------------- |
| 1. 表现差广告降价/关停  | 发现转化极好的「好苗子」，以安全幅度自动涨预算/提价去抢量。                |
| 2. 高转化广告提价扩量   | 连续几天表现垫底的垃圾素材，系统扮演无情杀手自动关停。                     |
| 3. A/B测试自动决出胜者  | 科学赛马，根据真实转化价值自动关停输家，把流量全给赢家。                   |
| 4. 异动根因自动排查建议 | 老板问为什么成本翻倍？系统一键生成诊断报告（揪出外部竞对或内部操作失误）。 |
