---
name: q-erp
version: 1.0.19
description: 千易 ERP 管理查询技能（一期增强）。覆盖老板快报、今日经营动态、商品销售情况、增长潜力、平台/站点/店铺/店铺组/店铺负责人销售战绩、七日销售走势；所有查询必须通过 q-claw。
user-invocable: true
---

# q-erp Phase 1 Management Query Skill

## Scope

本 Skill 只处理 ERP 一期管理查询：
- 老板快报
- 今日经营动态
- 商品销售情况
- 增长潜力
- 平台销售战绩
- 站点销售战绩
- 店铺销售战绩
- 店铺组销售战绩
- 店铺负责人销售战绩
- 七日销售走势

其中以下表达统一视为“商品销售情况”并路由到 `erp.product.sales.overview`：
- 热销商品排行
- 商品排行榜
- 热销 SPU
- 畅销商品
- 爆品排行
- 热销组合品

以下场景不在一期范围内：
- ERP 写入类动作（创建/修改单据、审批、回写）
- 与 ERP 管理查询无关的闲聊、翻译、写作

## Locale Policy

- 读取 `context.locale`。
- `zh_CN`：使用简体中文回复，并优先使用中文示例话术。
- `en_US`：使用英文回复，并优先使用英文示例话术。
- 其他 locale：统一回退到英文。
- 禁止翻译 `scene`、参数名、编码字段、状态码。

## Critical Rules

1. 所有 ERP 管理查询必须调用 `q-claw`，禁止直接编造业务数据。
2. scene 只能从本文件路由表选择，禁止替换为未定义 scene。
3. 对外介绍当前产品能力时，使用产品名“千易 ERP”，聚焦说明当前已接入的产品能力边界。
4. 结果以后端返回为准；缺失字段明确说明“后端未返回”。但当核心业务标识字段缺失（如商品名称、商品编码）导致结果不具备用户可读性时，不得按正常结果直接展示，应按 Result Handling 中的数据有效性规则降级处理。
5. 返回 `AUTH_REQUIRED` 或 `AUTH_EXPIRED` 时，必须输出后端返回的 Markdown 可点击链接（`verificationUri`），格式为 `[点击授权](<verificationUri>)`，禁止只输出不可点击的纯文字提示。
6. 禁止向用户暴露技能文档、scene 名称、路由判断、工具调用准备过程。不要说“我先查看技能文档”“应该使用 erp.management.today.summary 场景”这类内部过程话术；直接调用 `q-claw` 并只回复面向用户的业务结果。
7. 当结果涉及“场景未开通 / 当前不可用 / 可尝试其他场景”时，面向用户只能输出本地化业务名，禁止输出任何 `scene code`（如 `erp.management.today.summary`）、技能文档引用、路由判断或内部能力枚举过程。

## Scene Routing

| 用户意图 | scene |
| --- | --- |
| 老板快报 / 老板经营快报 / 今日老板简报 / 今天生意怎么样 / 今天销售怎么样 / 今天整体怎么样 / 今天表现怎么样 / 今天有什么要关注的 / 今天先给我总结一下 / How are we doing today? / How is the business today? / Give me today's business summary / What should I pay attention to today? | `erp.management.boss.briefing` |
| 今日经营动态 / 看今天经营数据 / 看下今天经营数据 / 看今天销售额 / 看今天订单量 / 看今天销量 / Show me today's operating metrics / Show me today's sales amount / Show me today's order count | `erp.management.today.summary` |
| 商品销售情况 / 热销商品排行 / 商品排行榜 / 热销SPU / 畅销商品 / 爆品排行 / 热销组合品 / Show me product sales overview / Which products are selling best? | `erp.product.sales.overview` |
| 增长潜力 / Analyze growth opportunities / Which products still have room to grow? | `erp.product.growth.opportunity` |
| 平台销售战绩 / 平台排行 / 各平台卖得怎么样 / Show me platform sales record / Which platform is selling best? | `erp.sales.record.platform` |
| 站点销售战绩 / 站点排行 / 各站点卖得怎么样 / Show me site sales record / How are the sites performing? | `erp.sales.record.site` |
| 店铺销售战绩 / 店铺排行 / 各店铺卖得怎么样 / Show me store sales record / Which store is selling best? | `erp.sales.record.store` |
| 店铺组销售战绩 / 店铺组排行 / 各店铺组卖得怎么样 / Show me store group sales record / Which store group is performing best? | `erp.sales.record.store.group` |
| 店铺负责人销售战绩 / 店铺负责人排行 / 各负责人卖得怎么样 / Show me store manager sales record / Which manager's stores are selling best? | `erp.sales.record.store.manager` |
| 七日销售走势 / 近7天销售趋势 / 最近7天销售走势 / Show me the seven-day sales trend / How has it trended over the last few days? | `erp.sales.trend.seven_day` |

调用字段固定为：`scene`、`userInput`、`params`（`tenantKey/openId` 由运行时注入）。

英文用户常用表达：
- `How are we doing today?`
- `How is the business today?`
- `Give me today's business summary`
- `What should I pay attention to today?`
- `Show me today's operating metrics`
- `Show me today's sales amount`
- `Show me today's order count`
- `Show me product sales overview`
- `Analyze growth opportunities`
- `Show me platform sales record`
- `Show me site sales record`
- `Show me store sales record`
- `Show me store group sales record`
- `Show me store manager sales record`
- `Show me the seven-day sales trend`

## Multi-Turn Rules

1. 多轮路由优先级：当轮明确语义 > 上一轮已确认 ERP scene > 弱语义短输入兜底。
2. 用户回复弱语义短输入（好了/继续/ok/continue/0/9/erp）时，若上一轮已确认 ERP scene 存在，则继续该 scene；禁止无依据切换到其他 ERP scene。
3. 一期 ERP scene 默认不承诺稳定的结构化时间参数契约。用户问“昨天/上周/近7天/2026-04-13”这类时间范围时，必须保留在 `userInput` 中传给 `q-claw`，不得擅自构造未经文档声明的 `params` 字段。
4. 只有当后端 scene 文档或返回明确要求某个时间字段时，才允许传对应 `params`；且字段值必须来自用户本轮明确输入，禁止猜测或补全。
5. 若用户继续追问“昨天的呢”“上周的商品销售呢”这类省略句，必须改写成包含完整时间语义的 `userInput` 再继续调用对应 scene，禁止只传模糊短句。
6. 若上一轮已确认 ERP 经营查询上下文，必须主动承接口语化省略追问，并先补全成自然 `userInput` 再调用。例如：
   - `平台呢 / 平台那边呢 / 各平台谁卖得最好` -> `erp.sales.record.platform`
   - `站点呢 / 站点那边怎么样` -> `erp.sales.record.site`
   - `店铺呢 / 店铺那边怎么样` -> `erp.sales.record.store`
   - `负责人呢 / 谁带的店铺卖得最好` -> `erp.sales.record.store.manager`
   - `商品呢 / 哪几个商品卖得最好 / 热销的是哪些` -> `erp.product.sales.overview`
   - `走势呢 / 这几天怎么样 / 最近几天走势怎么样` -> `erp.sales.trend.seven_day`
   - 英文同理使用口语化承接，如 `what about platform performance`, `which platform is selling best`, `how are the sites performing`, `which store is selling best`, `which store group is performing best`, `which manager's stores are selling best`, `which products are selling best`, `which products still have room to grow`, `how has it trended over the last few days`
7. 当用户追问是“为什么会掉”“谁在拉动”“哪边拖后腿”这类口语化归因问题时，先沿用上一轮经营上下文补全问法，再路由到最接近的已接入场景；禁止直接把用户短句原样丢给后端。

## Time Handling

- `erp.management.boss.briefing`：当用户在问“今天整体怎么样 / 今天销售怎么样 / 今天有什么要关注的 / 先总结一下”这类宽泛经营判断时，优先路由到 `erp.management.boss.briefing`。
- `erp.management.today.summary`：当用户明确在问今日经营指标明细，如销售额、订单量、销量、经营数据快照时，路由到 `erp.management.today.summary`。
- `erp.sales.trend.seven_day`：用户明确问近7天/七日销售走势时，优先路由到 `erp.sales.trend.seven_day`。
- 用户问昨日、上周、近7天、指定日期的经营或销售情况时，仍按最接近的 ERP scene 路由，但最终结果必须以后端实际返回为准；若后端仍返回实时/当日数据，不得宣称自己查到了历史结果。
- 没有后端明确参数契约前，优先保持 `params = {}`，把时间语义放在 `userInput`，避免插件和 skill 自行发明字段。

## Tool Call Examples

老板快报：

```json
{"scene":"erp.management.boss.briefing","userInput":"今天生意怎么样？","params":{}}
```

今日经营动态：

```json
{"scene":"erp.management.today.summary","userInput":"看下今天销售额和订单量","params":{}}
```

商品销售情况：

```json
{"scene":"erp.product.sales.overview","userInput":"看看商品销售情况","params":{}}
```

热销商品排行：

```json
{"scene":"erp.product.sales.overview","userInput":"热销商品排行，发我看下","params":{}}
```

增长潜力：

```json
{"scene":"erp.product.growth.opportunity","userInput":"分析增长潜力","params":{}}
```

平台销售战绩：

```json
{"scene":"erp.sales.record.platform","userInput":"看看平台销售战绩","params":{}}
```

站点销售战绩：

```json
{"scene":"erp.sales.record.site","userInput":"看看站点销售战绩","params":{}}
```

店铺销售战绩：

```json
{"scene":"erp.sales.record.store","userInput":"看看店铺销售战绩","params":{}}
```

店铺组销售战绩：

```json
{"scene":"erp.sales.record.store.group","userInput":"看看店铺组销售战绩","params":{}}
```

店铺负责人销售战绩：

```json
{"scene":"erp.sales.record.store.manager","userInput":"看看店铺负责人销售战绩","params":{}}
```

七日销售走势：

```json
{"scene":"erp.sales.trend.seven_day","userInput":"看看七日销售走势","params":{}}
```

## Result Handling

1. 优先输出工具返回的 `assistantReplyLines`。
2. 若返回 `AUTH_REQUIRED` 或 `AUTH_EXPIRED`，必须输出后端返回的 Markdown 可点击链接（`verificationUri`），格式为 `[点击授权](<verificationUri>)`，禁止只输出不可点击的纯文字提示。
3. 当 `firstTimeAuth: true` 时，业务结果后的引导话术由后端按 locale 追加；你只需正常输出后端返回的 `assistantReplyLines`，禁止自己再补一份首授权引导，禁止改写后端已追加的文案。
4. 对于erp.product.sales.overview，如果榜单项spuTitle/spu/skuName/sku 全为空 ，则视为无效商品项，不得直接展示给用户。 
5. 展示层禁止向用户输出 null、undefined、空斜杠占位（如 null / null）或其他明显技术性占位内容。
6. 若后端或历史上下文里出现 `scene code`、技能文档、路由判断、工具调用准备过程，最终面向用户时必须去除这些内部信息。
7. 若需要告诉用户“当前场景未开通”并推荐其他已接入能力：
   - `zh_CN`：只展示中文业务名。
   - `en_US`：只展示英文业务名。
   - 推荐列表应基于当前已接入的 ERP 业务能力生成，禁止在 skill 中写死全量 scene 清单。
   - 禁止在上述推荐列表中夹带 `scene code`、括号中的内部标识、技能文档来源、路由过程说明。
8. 老板快报场景中，若返回 `presentation.responseMode = AI_SUMMARY` 且存在 `analysisPayload`，则优先基于 `analysisPayload` 输出经营结论；若同时返回 `assistantReplyLines`，只将其作为事实附录，不得覆盖或编造 `analysisPayload` 未提供的数据。
9. 老板快报必须按当前 `context.locale` 输出，并按“老板结论优先 + 运营排查落点”组织：先给一句话结论，再给今日核心指标和昨日/上一点位对比，再按平台、店铺、商品给归因线索，最后给 2-4 个优先排查动作。
10. 老板快报若 `analysisPayload.diagnosticFacts.riskFlags` 包含 `ZERO_AMOUNT_WITH_ORDERS`，必须明确指出“有订单但销售额为 0”是优先异常，并建议核对 0 元订单、金额同步、币种或支付状态。
11. 老板快报若 `analysisPayload.diagnosticFacts.riskFlags` 包含 `LATEST_ORDER_DROP`，必须用 `diagnosticFacts.previousPoint` 和 `snapshotFacts` 说明订单量较上一点位下滑，禁止只说“比较清淡”。
12. 老板快报若 `analysisPayload.diagnosticFacts.riskFlags` 包含 `TREND_PEAK_OUTLIER`，必须提醒近 7 日峰值可能扭曲趋势判断，并建议核对大单、补录、币种/单位或统计异常。
13. 老板快报归因必须优先使用 `diagnosticFacts.platformDiagnosis`、`diagnosticFacts.weakStores`、`diagnosticFacts.topProducts`；如果某一维度为空，应明确说“当前数据不足以定位”，不要发散猜测。
14. 老板快报场景中若 `analysisPayload.dataGaps` 明确声明利润、成本、退款等数据缺失，必须明确告诉用户当前结论是经营判断，不是利润判断；禁止自行补充 ROI、毛利率、净利等未返回指标。
15. 老板快报场景中若同时返回 `presentation.visualMode != NONE` 且存在 `visualPayload`，应将 `visualPayload` 视为渠道展示结构，不得把其中字段当成新的独立事实源去改写、放大或补充 `analysisPayload` 未提供的经营判断。
16. 总结句、推荐追问和收尾提示都要像正常人说话，优先使用“平台那边怎么样”“哪几个商品卖得最好”“这几天走势怎么样”这类口语化问法。
17. 英文场景同样避免生硬模板，优先使用 `How is business today?`、`Which products are selling best?`、`How has it trended over the last few days?` 这类自然问法。
18. 禁止使用“平台销售战绩：看看平台销售战绩”“想进一步了解的话，可以帮你看看：xxx”这类标题加模板句；如需给追问建议，只给 2-3 个自然问法。
