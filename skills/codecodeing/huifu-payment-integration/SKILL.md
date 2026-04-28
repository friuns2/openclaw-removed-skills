---
name: huifu-payment-integration
description: 汇付支付斗拱产品接入最佳实践。涵盖聚合支付、托管支付、H5/PC 收银台、checkout-js、查单关单、退款对账等场景的产品选型与集成指导。
---

# 汇付支付集成

## 版权声明

本 Skill 包中的汇付支付、斗拱支付接口资料整理自上海汇付支付有限公司官方开放平台与官方产品文档；原始文档及其更新维护权归汇付支付官方所有。本 Skill 包仅作技术学习交流与接口集成辅助使用，详细口径见 `references/shared-copyright-notice.md`。

目标：只读取当前场景必须的 3-5 份本地文档；优先暴露缺口和能力边界，不拼凑看似完整但当前链路不支持的方案；PHP 一旦需要落代码，默认体现官方 `dg-php-sdk` 落地。

## 什么时候使用

- 第一次接入汇付支付，还不确定该走聚合支付、托管支付还是前端 checkout
- 已经知道要接汇付，但还没判断清楚当前阶段是初始化、下单 / 预下单、查询 / 关单 / 对账、退款还是前端页面接入
- 用户直接提到“微信小程序支付”“支付宝正扫”“付款码支付”“二维码支付”“H5/PC 收银台”“checkout-js”“查单”“退款”等意图，需要先路由到正确 reference
- 需要先判断 Java、PHP、Browser / JS 哪条实现路径当前可落地

## 什么时候不要使用

- 用户已经明确指定某份具体文档，只需要读取那一份
- 用户已经进入某个专题文档，当前问题只和该专题内的参数、返回字段或代码示例有关
- 用户已经明确指定某个官方 PHP SDK request 类、已有业务专题文档或具体接口页，只需要读取那一份

## 决策优先级

1. 先判断当前问题是否已经落到具体专题文档；如果已经落到专题，不再回到总技能
2. 再判断产品线：聚合支付、托管支付，还是商户前端 checkout
3. 再判断当前能力是否被当前技术栈覆盖；如果不覆盖，立即显式说明，不继续把用户引到错误模板
4. 再判断阶段：首次接入、初始化、下单 / 预下单、查询 / 关单 / 对账、退款、前端支付组件
5. 最后判断渠道或端形态：微信 / 支付宝 / 银联、小程序、H5 / PC、付款码、二维码

## 最少澄清规则

- 如果用户已经明确给出“产品线 + 阶段 + 技术栈”，不要重复追问，直接给阅读顺序
- 如果缺少的信息不会影响主路由，不追问，先给主路径
- 如果用户已经明确说“已完成初始化”“已完成托管预下单”“已经能查单”，跳过 `*-quickstart.md` 和 `*-base.md`，直接进入当前阶段文档
- 如果用户已经明确说“已完成托管预下单和查单，现在只接 checkout-js”，不要再把 `hostingpay-preorder.md`、`hostingpay-query.md` 列为本轮主阅读文档；只补 `checkout-js` 专题和 `hostingpay-async-webhook.md`
- 只有在以下情况才追问：
  1. 无法判断是聚合支付还是托管支付
  2. 无法判断是服务端接入还是前端 checkout
  3. 用户指定 PHP，但当前阶段在 PHP 上没有现成覆盖

## 检查点机制

只允许两类检查点：`软检查点` 和 `硬检查点`。

### 软检查点

软检查点不等待用户回复，触发后直接继续给主路径。

触发条件：

- 用户已经声明某些前置阶段完成，本轮需要主动跳过 `*-quickstart.md`、`*-base.md` 或已完成的主文档
- 当前回答会明确排除一整条相邻路径，例如排除聚合支付、排除前端 checkout、排除非官方自维护 PHP client
- 需要提醒某个依赖关系，但不影响继续路由，例如 `checkout-js` 依赖托管预下单和最终结果确认闭环

输出要求：

- 先用 1 句写清当前判断
- 再用 1 句写清本轮主动跳过什么
- 不追加开放式追问，直接继续给阅读顺序或结论

### 硬检查点

硬检查点必须等待用户确认后再继续。

只在以下情况触发：

1. 无法区分聚合支付、托管支付、checkout 三条主链路，继续回答会把用户带到不同文档集合
2. 无法区分服务端接入、前端页面接入、最终状态确认三种职责，继续回答会导致读错阶段文档
3. 用户要求“直接给代码 / 现成模板”，但当前组合无模板，且存在两条以上可行回退路径，例如“切到 Java 主链路”或“保持当前技术栈只看协议级路径”
4. 用户想单独推进 `checkout-js`、只看前端回调、或只做页面集成，但是否已具备托管预下单和最终查单 / 异步通知闭环还不明确；即使用户要求“不用问”“直接给路线”“最省事”，也必须触发硬检查点
5. 用户要求“可直接联调 / 可上线 / 生产可用”的代码，但缺少 `project_id`、`notify_url`、`sys_id`、渠道标识、商户号等关键真实值，继续输出会制造伪完整代码
6. 本地 SDK 源码与当前文档口径冲突，且冲突点属于请求头、签名、版本、能力覆盖这类高风险事实

硬检查点输出要求：

- 第一行必须直接写 `硬检查点`
- 先写 `当前判断`
- 再写 `为什么不能直接继续`
- 最后只问 1 个最短确认问题
- 未得到确认前，不继续输出完整阅读顺序、代码骨架或技术栈切换方案
- 对 `checkout-js` 先决能力未确认的硬检查点，不输出安装步骤、前端接法或文档阅读顺序

以下情况不要触发硬检查点：

- 用户只问文档阅读顺序，不要求代码，且主路由已足够明确
- 缺少的信息不会改变主链路，只会影响后续真实参数填充
- 当前只能给出唯一正确结论，不存在需要用户二选一的分叉

## 默认裁决规则

- 用户一旦提到 `H5 / PC 收银台`、`project_id`、`checkout-js`、`createPreOrder`、商户自有页面嵌入组件，默认先走托管支付
- 只有用户明确要求“比较聚合支付和托管支付”时，才同时给两条产品线的 quickstart
- 用户已经明确后续阶段时，不要为了“完整”再回头补一串初始化文档
- 用户若已明确“托管预下单 + 查单都已完成，只差 checkout-js”，优先返回 `checkout-js` 组件接入、`callback` 确认和异步通知，不要把既有查单主文档重新抬成主阅读顺序

## 执行工作流

1. 先读 `references/shared-overview.md`
2. 从用户表达里提取 5 个标签：产品线、阶段、技术栈、渠道、是否首次接入
3. 先判断是否触发 `硬检查点`；如果触发，只输出检查点并等待用户确认
4. 如果不触发硬检查点，再做能力覆盖裁决
5. 如果当前组合不支持且用户要求“现成模板代码”，先判断是否存在多条回退路径；有分叉时触发硬检查点，无分叉时只输出缺口和唯一受支持主链路
6. 如果需要主动排除已完成阶段、相邻产品线或历史兼容实现，先输出 `软检查点`
7. 只给出当前场景最少必要的 3-5 份文档；不要一次性列出全量 `references/*.md`
8. 如果用户明确需要 PHP 代码或 PHP 落地方案，先读对应 `*-php-adapter.md` 和 `*-php-scenarios.md`；聚合支付核心主链路优先以官方 `huifurepo/dg-php-sdk` 的 `BsPaySdk\core\Payment` 落地，对账和托管支付优先 `BsPayClient::postRequest()`；需要核对来源头或签名口径时，读取 `shared-request-header-policy.md` 与 `shared-signing-v2.md`，必要时再检查项目实际安装的官方 SDK 源码
9. 输出时显式说明：
   - 当前判断结果
   - 先读哪些文档
   - 暂时不要读哪些方向
   - 还缺哪些真实参数或前置动作

下文提到的 `.md` 文件默认都位于 `references/` 目录。

## 澄清话术

只在触发 `硬检查点` 时，按下面最短话术澄清：

### 产品线不明确时

```text
请先确认你的接入目标：

1. 标准服务端支付接入，优先快速上线
2. 需要托管收银台、项目制预下单或更完整的托管支付闭环
3. 需要在商户自己的页面中嵌入 checkout 或支付按钮
```

### 任务阶段不明确时

```text
请确认你当前要做的是哪一步：

1. 初始化 / 公共配置
2. 下单 / 预下单
3. 查询 / 关单 / 对账
4. 退款
5. 前端页面接入
6. 签名 / 异步通知 / 共享协议确认
```

### 前后端职责不明确时

```text
请先分清当前问题属于哪一侧：

1. 服务端：配置凭据、下单、查询、退款、异步通知处理
2. 前端：渲染 checkout、支付按钮、接收前端流程回调
3. 闭环确认：即使前端返回成功，也仍需服务端查单或依赖异步通知确认最终状态
```

### 当前技术栈无模板但用户要代码时

```text
当前仓库没有这条组合的现成模板代码。

请确认你接下来要哪条路：

1. 切到当前受支持的主链路
2. 保持当前技术栈，只看协议级阅读路径
```

### checkout 先决能力未确认时

```text
`checkout-js` 不能单独成立。

请先确认你的服务端是否已经具备：

1. 托管预下单
2. 最终查单或异步通知确认
```

### 生产级代码前置参数不足时

```text
当前还缺少可直接联调代码必需的真实参数。

请确认你要我继续哪一种：

1. 先补关键真实值，再按生产口径继续
2. 先只看阅读顺序和待补参数清单
```

## 必须显式暴露的能力边界

| 组合 | 当前结论 | 正确处理方式 |
| --- | --- | --- |
| 聚合支付 + PHP + 下单 | 已支持官方 PHP SDK 主链路 | 先读 `aggregation-php-adapter.md` 与 `aggregation-query-php-scenarios.md`；优先 `Payment::create()` + `TradePaymentCreateRequest` |
| 聚合支付 + PHP + 交易查询 / 关单 / 关单查询 | 已支持官方 PHP SDK 主链路 | 交易查询优先 `Payment::query()`；关单 / 关单查询优先 `Payment::close()` / `closeQuery()`；原交易定位键必须来自落库结果 |
| 聚合支付 + PHP + 退款 / 退款查询 | 已支持官方 PHP SDK 主链路 | 优先 `Payment::refund()` / `refundQuery()`；退款最终状态仍以查询或异步通知为准 |
| 聚合支付 + PHP + 对账 | 已支持官方 request 类路径 | 走 `BsPayClient::postRequest()` + `V2TradeCheckFilequeryRequest` |
| PHP + 当前已支持场景 + 用户要代码 | 必须体现官方 phpsdk 落地 | 聚合支付核心主链路优先 `BsPaySdk\core\Payment`；聚合对账与托管支付优先 `BsPayClient::postRequest()`；不要默认生成 `HostingClient`、`AggregationClient` 或自写 `curl` 版本 |
| 不支持组合 + 用户要求现成模板代码 | 不允许现场补自造模板 | 固定输出“当前仓库无现成模板代码”，并停止在阅读路径、支持边界和缺失参数层 |
| checkout-js 单独使用 | 不成立 | 必须先有 `hostingpay-preorder` 服务端能力，最终状态还要回到 `hostingpay-query` |
| 非官方 Java SDK 自动补头以外的服务端调用 | 需要手动补头 | 必须额外读取 `shared-request-header-policy.md` |

## 不支持组合时的固定输出

当当前组合不支持，且用户要求“现成模板代码”“直接给代码”“按当前技术栈落地”时，固定按下面 4 句处理：

1. `现成模板代码结论：当前仓库无`
2. 明确仓库当前覆盖到哪一层，不要含糊写“部分支持”
3. 给出受支持的主链路或协议级阅读路径
4. 不要现场生成新的骨架类、适配器、伪模板，也不要混用另一条产品线的模板冒充当前方案

## 首次接入路由

### 聚合支付首次接入

按顺序读取：

1. `references/shared-overview.md`
2. `aggregation-quickstart.md`
3. `aggregation-customer-preparation.md`
4. `aggregation-base.md`
5. `aggregation-payload-construction.md`

### 托管支付首次接入

按顺序读取：

1. `references/shared-overview.md`
2. `hostingpay-quickstart.md`
3. `hostingpay-customer-preparation.md`
4. `hostingpay-base.md`
5. `hostingpay-payload-construction.md`

### 前端 checkout 首次接入

按顺序读取：

1. `references/shared-overview.md`
2. `hostingpay-quickstart.md`
3. `hostingpay-preorder.md`
4. `checkout-js.md`
5. `hostingpay-query.md`

## 阶段主路由

| 阶段 | 聚合支付 | 托管支付 | checkout |
| --- | --- | --- | --- |
| 初始化 / 公共配置 | `aggregation-base.md` | `hostingpay-base.md` | 先回到 `hostingpay-preorder.md` |
| 下单 / 预下单 | `aggregation-order.md` | `hostingpay-preorder.md` | `hostingpay-preorder.md` |
| 查询 / 关单 / 对账 | `aggregation-query.md` | `hostingpay-query.md` | 最终确认同时读 `hostingpay-query.md` + `hostingpay-async-webhook.md` |
| 退款 | `aggregation-refund.md` | `hostingpay-refund.md` | 不单独成立，仍是服务端退款 |
| 前端支付组件 | 不适用 | 可协同 `checkout-js.md` | `checkout-js.md`；若已完成托管预下单和查单，补 `checkout-js-callback-and-confirmation.md` + `hostingpay-async-webhook.md` |

## 技术栈主路由

| 技术栈 | 聚合支付 | 托管支付 | checkout |
| --- | --- | --- | --- |
| Java | `aggregation-java-adapter.md`、`aggregation-java-sdk-quickstart.md`、`aggregation-java-tech-spec.md` | `hostingpay-java-adapter.md`、`hostingpay-java-sdk-quickstart.md`、`hostingpay-java-tech-spec.md` | 服务端仍走托管 Java，前端再接 `checkout-js.md` |
| PHP | `aggregation-php-adapter.md` + `aggregation-query-php-scenarios.md` 已覆盖下单、扫码交易查询、关单 / 关单查询、退款 / 退款查询、对账；核心支付主链路优先 `BsPaySdk\core\Payment`，对账走 `BsPayClient::postRequest()`，且代码必须体现官方 `dg-php-sdk` | `hostingpay-php-adapter.md`、`hostingpay-preorder-php-scenarios.md`、`hostingpay-query-php-scenarios.md`、`hostingpay-refund-php-scenarios.md`，且代码必须体现官方 `dg-php-sdk` | 服务端 PHP 先读托管预下单，再读 `checkout-js.md` |
| Browser / JS | 不直接承担聚合服务端职责 | 商户页面配合托管服务端能力 | `shared-frontend-sdk-matrix.md`、`checkout-js.md`、`checkout-js-readme.md` |

## 高频场景速查

| 用户表达 | 判断结果 | 优先文档 |
| --- | --- | --- |
| “第一次接汇付，不知道走哪条线” | 先做产品线判断 | `references/shared-overview.md` + 对应 `*-quickstart.md` + 对应 `*-customer-preparation.md` |
| “我要做聚合微信小程序支付，Java” | 聚合支付 + 下单 + Java + 微信小程序 | `aggregation-base.md`、`aggregation-order.md`、`aggregation-order-method-wechat.md` |
| “我要做支付宝正扫” | 聚合支付 + 下单 + 渠道细分 | `aggregation-order.md`、`aggregation-order-method-alipay.md` |
| “我要做托管微信小程序预下单” | 托管支付 + 预下单 + 微信小程序 | `hostingpay-preorder.md`、`hostingpay-preorder-wechat-mini.md`、`hostingpay-query.md` |
| “我要做 H5 / PC 收银台” | 托管支付 + H5/PC 预下单 | `hostingpay-preorder.md`、`hostingpay-preorder-h5-pc.md`、`hostingpay-query.md` |
| “我要接 checkout-js” | checkout + 托管预下单协同 | `hostingpay-preorder.md`、`checkout-js.md`、`checkout-js-callback-and-confirmation.md`、`hostingpay-query.md`、`hostingpay-async-webhook.md` |
| “我要接 checkout-js 并确认最终结果” | checkout + 最终确认闭环 | `checkout-js-integration-flow.md`、`checkout-js-callback-and-confirmation.md`、`hostingpay-query.md`、`hostingpay-async-webhook.md` |
| “已完成托管预下单和查单，现在只接 checkout-js” | checkout 组件专题 + 复用既有服务端确认链路 | `checkout-js-integration-flow.md`、`checkout-js.md`、`checkout-js-create-preorder-contract.md`、`checkout-js-callback-and-confirmation.md`、`hostingpay-async-webhook.md` |
| “我要查单 / 关单 / 对账” | 查询链路 | `aggregation-query.md` 或 `hostingpay-query.md`，按产品线选一条 |
| “我要退款” | 退款链路 | `aggregation-refund.md` 或 `hostingpay-refund.md`，按产品线选一条 |
| “原交易既有分账又有补贴，退款字段怎么传” | 聚合支付 + 退款字段口径 | `aggregation-refund.md`、`aggregation-refund-query.md` |
| “托管支付退款字段、loan_flag、risk_check_data、bank_info_data” | 托管支付 + 退款字段口径 | `hostingpay-refund.md`、`hostingpay-refund-query.md` |

## PHP SDK / 模板读取规则

- PHP 代码示例、初始化入口和业务调用，默认体现官方 Composer 包 `huifurepo/dg-php-sdk`
- PHP 当前 Skill 包基线为 `huifurepo/dg-php-sdk 2.0.26`；如果用户现有项目低于该版本，必须先提示调整 `composer.json` 版本约束并升级 SDK，不要在旧 SDK 上继续生成新字段或新接口代码
- 聚合支付核心支付主链路优先 `BsPaySdk\core\Payment` + 官方 request 类；聚合对账与托管支付优先 `BsPayClient::postRequest()` + request 类
- PHP 如果输出可运行代码，必须先给出 `composer require "huifurepo/dg-php-sdk:^2.0.26"`、`composer update huifurepo/dg-php-sdk --with-all-dependencies`、`vendor/huifurepo/dg-php-sdk/BsPaySdk/init.php` 存在性检查，以及 `HUIFU_SYS_ID`、`HUIFU_PRODUCT_ID`、`HUIFU_RSA_PRIVATE_KEY`、`HUIFU_RSA_PUBLIC_KEY`、`HUIFU_SKILL_SOURCE`、`HUIFU_MERCHANT_ID` 等环境变量准备
- PHP 如果 Composer 不可用，必须给出当前基线对应的 Packagist / GitHub 分发包备用下载方式，并要求解压后设置 `HUIFU_SDK_ROOT` 且校验 `init.php`；不要把官方 SDK 文档里可访问的旧版本 OSS 包当作当前版本替代品
- PHP 可运行代码回答如果篇幅受限，宁可缩短业务示例，也不能省略 `composer update huifurepo/dg-php-sdk --with-all-dependencies` 和当前基线备用下载地址 `https://api.github.com/repos/huifurepo/bspay-php-sdk/zipball/cc7bf93d0e77230097efdd610996d237e4a26298`
- PHP 如果输出可运行代码，必须同时给出可落地的 `loader.php` 初始化模板，显式加载 `BsPaySdk/init.php`、调用 `BsPay::init(...)`，并定义 `HUIFU_SDK_ROOT` 供业务代码显式加载 request 类
- PHP 只要输出初始化或业务调用代码，必须显式出现 `skill_source` / `MerConfig.skill_source`，并说明官方 SDK 在配置后自动补 `jpt-x-skill-source`，请求参数存在非空 `huifu_id` 时自动补 `jpt-x-skill-huifu_id`；这两项必须明确称为 HTTP 请求头，不是 `data` 业务字段
- PHP 聚合查单、关单、关单查询回答必须提醒原交易定位键来自下单结果落库 / 持久化，不要临时猜测 `req_date`、`req_seq_id`、`hf_seq_id`
- 不要把 `BsPay::post(funcCode, ...)` 散落在业务层
- 如果当前阶段不在 PHP 覆盖范围内，先显式说明“不支持当前现成模板”，不要继续生成 PHP 代码制造假象
- 只有在需要核对官方 SDK 自动来源头实现或手工比对签名差异时，才检查项目实际安装的官方 SDK 源码；不要回到非官方自维护 client 方案
- 不要再默认生成 `HostingClient`、`AggregationClient` 或自写 `curl` 的业务代码
- 需要核对官方 SDK 自动来源头规则，或在非官方调用路径手动补头时，回看 `shared-request-header-policy.md`

## 输出模板

输出时固定按下面结构组织：

0. `检查点`
   - 只有触发检查点时才输出
   - 软检查点：写清当前判断和本轮主动跳过的路径，然后直接继续
   - 硬检查点：写清当前判断、阻塞原因和唯一确认问题；未确认前停止
1. `判断结果`
   - 产品线
   - 阶段
   - 技术栈
   - 渠道 / 端形态
   - 若用户要求代码且当前组合不支持，必须额外写：`现成模板代码结论：当前仓库无`
2. `先读这些`
   - 只列 3-5 份最必要文档，并说明每份文档解决什么问题
   - 参数、字段和接口口径类回答也必须先列实际读取的 reference 文件名，再给字段结论
   - 如果用户已明确某个前置阶段“已经完成”，不要把该阶段主文档再列入这里；最多在“还缺的真实参数 / 前置动作”里把它当现有依赖提醒
3. `暂时不要读`
   - 明确排除当前无关产品线、无关技术栈或当前不支持的模板方向
4. `还缺的真实参数 / 前置动作`
   - 只列当前场景真正阻塞落地的值或配置，不罗列无关字段
5. `禁止动作`
   - 当当前组合不支持时，不要现场补仓库中不存在的模板代码

## 当前版本事实

| 项目 | 当前口径 |
| --- | --- |
| Skill 包版本 | `1.2.0` |
| 托管支付 Java SDK 常量版本 | `dg-java-sdk 3.0.36` |
| 聚合支付 Java SDK 版本 | `dg-lightning-sdk 1.0.5` |
| 前端收银台 JS SDK | `@dg-elements/js-sdk`，接入时以项目锁定版本为准，升级前查询 npm registry |
| `HUIFU_SKILL_SOURCE` 最终上送格式 | `<skill_source>` |

## 全局边界

- 不要猜测 `project_id`、`callback_url`、`notify_url`、`sub_openid`、`buyer_id`、`buyer_logon_id`、`auth_code`、`devs_id`、`fee_sign` 等运行时值
- 不要把 `HUIFU_RSA_PRIVATE_KEY`、`HUIFU_RSA_PUBLIC_KEY` 写入前端、仓库或示例常量
- `HUIFU_SKILL_SOURCE` 如果存在，最终上送值保持 `<skill_source>` 原样透传，不再追加 `sys_id`
- Java 与 PHP 当前都要求 HTTP 请求头 `jpt-x-skill-source`；如果请求 `data.huifu_id` 存在且非空，还要额外带 HTTP 请求头 `jpt-x-skill-huifu_id`
- 当前 Java SDK 基线会在 `MerConfig.setSkillSource(...)` 生效后自动补来源头；当前 Skill 包对齐的官方 PHP SDK 主链路也会在 `MerConfig.skill_source` 已配置时，自动补 `jpt-x-skill-source`，并在请求参数里的 `huifu_id` 存在且非空时自动补 `jpt-x-skill-huifu_id`
- PHP 侧如果需要输出可落地代码，必须体现官方 `huifurepo/dg-php-sdk` 落地；当前 Skill 包不再内置 PHP 模板资产或非官方自维护 client
- PHP 可运行代码不能只写 `require_once` 或空 `loader.php`；必须包含 SDK 安装、`init.php` 存在性检查和环境变量缺失时报错
- 当前官方 PHP Composer 包没有提供 request 类 autoload；除 `init.php` 外，业务代码仍要通过 `HUIFU_SDK_ROOT` 显式加载所需 request 类
- 前端支付回调不等于最终支付成功，最终状态只能由服务端查询或异步通知确认
- 如果客户没有提供当前场景必需值，应先暴露缺口，不要继续输出“看起来完整”的代码
