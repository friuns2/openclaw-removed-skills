# TSO 首页（`/foreign_trade/tso/home`）

主应用（微前端）完整路径为 **`/foreign_trade/tso/home`**；TSO 子应用内部路由为 **`/home`**，组件为 `views/home/Index.vue`。

## 页面入口（给 Agent 引导用户）

用 `siluzan-tso config show` 读取 **`webUrl`**，再拼接路径：

首页地址：`https://www.siluzan.com/v3/foreign_trade/tso/home`

> 若用户已登录 TSO，也可从左侧菜单进入「首页」。

---

## 页面业务模块（与前端一致）

### 1. 顶部运营 Banner

- 展示「出海营销大师 / 代运营」等运营图，点击跳转解决方案页。
- **无对应 CLI**，需浏览器打开首页查看。

### 2. 账户数据区（`AccountDataSection`）

按 **媒体类型 Tab**（Google / TikTok / Yandex / Meta / Bing / Kwai）切换。

| 模块                 | 说明                         | 前端调用的接口（相对 TSO `apiBaseUrl`）                                                    |
| -------------------- | ---------------------------- | ------------------------------------------------------------------------------------------ |
| 昨日转化             | 汇总昨日转化数               | `GET /report/media-account/Get-TSO-Overviews?MediaType={媒体}`                             |
| 昨日消耗             | 汇总昨日花费                 | 同上                                                                                       |
| 昨日充值金额         | 汇总昨日充值                 | 同上                                                                                       |
| 今日待充值账户数     | 余额不足等提示，可点「充值」 | 同上                                                                                       |
| 广告媒体开户申请概览 | 各媒体开户申请数量表格       | `GET /report/media-account/Get-TSO-Open-Account-Overviews`（`mediaTypesStr` 为 JSON 数组） |
| 各媒体账户余额       | 列表 + 单媒体「充值」按钮    | `GET /report/media-account/GetAccountBalance`                                              |

**CLI 对应关系（近似，非同一接口）：**

- 单账户余额、消耗趋势：**`balance`**、**`stats`**（`accountsoverview`），需已知 `mediaCustomerId`。
- 开户进度：**`account-history`**、**`open-account`** 系列。
- **充值**：无 CLI，见 `references/finance.md`，用 `webUrl` 引导至充值页。

> **说明**：首页的「昨日汇总」「全账户余额一览」等 **聚合报表接口**（`Get-TSO-Overviews`、`Get-TSO-Open-Account-Overviews`、`GetAccountBalance`）**当前 CLI 未单独封装**。若用户要「和首页一模一样的数字」，请引导打开网页；若只要分账户/分业务数据，用现有命令组合。

### 3. 广告数据概览（`AdDataSection`）

- 图表：全账户投放指标随时间变化；可切换指标、媒体筛选；国内贸易场景可能有占位数据。
- 子 Tab：**广告投放数据概览** / **内容数据概览**（文案来自 i18n）。

| 接口                                               | 用途                                                                                         |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `GET /report/media-account/accountreportoverview`  | 报表总览（图表数据源之一）                                                                   |
| `GET /report/media-account/GetAccountDataOverview` | 按媒体、账户、日期范围的账户级概览（`MediaType`、`MediaCustomerId`、`StartDate`、`EndDate`） |

**CLI 对应关系：**

- 单账户一段时间消耗/展示/点击：**`stats -m <媒体> -a <mediaCustomerId>`**（`accountsoverview`），日期可用默认或后续若支持传参则对齐页面。
- **图表级、多账户联动** 与 **`GetAccountDataOverview`**：**CLI 未封装**，需网页或后续扩展命令。

### 4. 服务推荐（`MoreFunctionSection`，部分首页布局显示）

跳转到丝路赞其他产品线（非 TSO CLI 范围）：

- AI：`/v3/foreign_trade/chatgpt/chat`
- 创意（SmartCut）：`/v3/foreign_trade/smartcut/cso/work?...`
- 建站：`/v3/foreign_trade/tso/website/template`
- 内容：`/v3/foreign_trade/cso/ContentHome`

**Agent 行为**：说明「属于平台其他模块」，用 `webUrl` + 上述路径新开标签页；**不要用 siluzan-tso 命令冒充能力**。

### 5. 右侧推荐（`RecommendSection`）

- 公众号文章、二维码等静态运营内容。
- **无 CLI**。

### 6. AI 落地页引导（`LandGuide`）

- 首次登录等场景弹窗，引导去落地页配置。
- **仅前端**，无 CLI。

---

## 推荐 Agent 话术示例

1. **「我要看和首页一样的总览」**  
   → 引导打开 `{webUrl}/v3/foreign_trade/tso/home`（或从菜单进首页）。

2. **「我只关心某个 Google 账户昨天花了多少」**  
   → `list-accounts -m Google` 取 `mediaCustomerId`，再 `stats -m Google -a <id>`。

3. **「首页说有待充值账户」**  
   → 说明聚合数据在网页；CLI 可 `list-accounts` + `balance` 逐账户排查，或引导去充值页（`references/finance.md`）。

---

## 与 `references/workflows.md` 的关系

首页是 **聚合看板**；多命令巡检流程见 **`references/workflows.md`** 中「投放数据快速巡检」等章节，逻辑上与首页「看数据」意图相近，但数据源接口不完全相同。
