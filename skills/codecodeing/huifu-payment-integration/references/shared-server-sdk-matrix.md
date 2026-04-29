# 服务端 SDK 能力矩阵

这份矩阵用于说明官方语言支持范围、当前 Skill 包的真实覆盖边界，以及 PHP 官方 SDK 的默认落地方式。

## 官方语言支持概览

| 语言 | 官方安装方式 | 最低运行时 | 当前说明 |
| --- | --- | --- | --- |
| Java | Maven | JDK 8+ | 聚合支付和托管支付都有稳定基线 |
| PHP | Composer `huifurepo/dg-php-sdk` | PHP 7.4+ | 托管支付覆盖核心场景；聚合支付已覆盖下单、查询、关单、退款、对账主链路 |
| C# | NuGet | .NET 4.8+ | 当前只保留入口说明 |
| Python | pip | Python 3.x | 当前只保留入口说明 |
| Go | go mod | Go 1.16+ | 当前只保留入口说明 |

## 当前 Skill 包的真实覆盖范围

| 能力 | Java | PHP | C# / Python / Go |
| --- | --- | --- | --- |
| 协议规则说明 | 完整 | 完整 | 入口说明 |
| SDK / API 安装说明 | 完整 | 完整 | 入口说明 |
| 初始化说明 | 完整 | 完整 | 入口说明 |
| 请求头对齐策略 | 完整 | 完整 | 需人工对照 |
| 聚合支付业务实现 | 完整 | 核心主链路覆盖 | 暂不提供 |
| 托管支付业务实现 | 完整 | 核心场景覆盖 | 暂不提供 |

## 当前版本口径

| 项目 | 版本 |
| --- | --- |
| 托管支付 Java SDK | `dg-java-sdk 3.0.36` |
| 聚合支付 Java SDK | `dg-lightning-sdk 1.0.5` |
| PHP SDK 包 | `huifurepo/dg-php-sdk 2.0.26` |
| 前端 JS SDK | `@dg-elements/js-sdk`，项目锁定版本 |

## PHP 默认落地方式

PHP 场景默认使用官方 Composer 包 `huifurepo/dg-php-sdk`，业务入口优先采用：

- 聚合支付核心主链路：`BsPaySdk\core\Payment`
- 聚合对账与托管支付：`BsPayClient::postRequest()`
- request 类提供 `funcCode`
- `params` 数组承载实际业务字段（适用于 `postRequest()` 路径）

当前 Skill 包的 PHP SDK 包基线是 `2.0.26`，优先通过 Composer 安装或升级：

```bash
composer require "huifurepo/dg-php-sdk:^2.0.26"
composer update huifurepo/dg-php-sdk --with-all-dependencies
composer show huifurepo/dg-php-sdk
test -f vendor/huifurepo/dg-php-sdk/BsPaySdk/init.php
```

Composer 不可用时，可以使用 Packagist 元数据指向的 GitHub 分发包手动下载当前基线：

- `https://api.github.com/repos/huifurepo/bspay-php-sdk/zipball/cc7bf93d0e77230097efdd610996d237e4a26298`
- 解压后设置 `HUIFU_SDK_ROOT=/absolute/path/to/BsPaySdk`
- 必须执行 `test -f "$HUIFU_SDK_ROOT/init.php"` 确认实际 SDK 路径

官方 PHP SDK 文档在 2026-04-24 直接校验时仍只列到 `v2.0.25`，且 `php-sdk_v2.0.25.7z` OSS 地址返回 404；不能用旧版本可访问链接静默替代当前 `2.0.26` 基线。

当前 Skill 包不再内置 PHP 模板资产或非官方自维护 client。

读取规则：

- 核对来源头时读 `references/shared-request-header-policy.md`
- 核对签名时读 `references/shared-signing-v2.md`
- 需要确认官方 SDK 实现细节时，检查项目实际安装的 `huifurepo/dg-php-sdk` 源码
- 不要回到历史自维护 PHP client 方案

推荐使用方式：

1. 先读 `references/shared-request-header-policy.md`
2. 再读对应 `*-php-adapter.md` 和 `*-php-scenarios.md`
3. 聚合支付核心主链路优先 `BsPaySdk\core\Payment`；聚合对账与托管支付优先 `BsPayClient::postRequest()`
4. 初始化 `MerConfig` 时显式配置 `skill_source`，让官方 SDK 自动带出来源头
5. 排查差异时先比对本地请求报文、签名串和官方 SDK 实际源码，不引入非官方 client

## 读法建议

- 要做聚合支付初始化：读 `references/aggregation-base.md`
- 要做聚合支付下单：读 `references/aggregation-order.md`
- 要做聚合支付关单 / 查单：读 `references/aggregation-query.md`
- 要做托管支付初始化：读 `references/hostingpay-base.md`
- 要做托管支付预下单：读 `references/hostingpay-preorder.md`
- 要做托管支付查询 / 关单 / 对账：读 `references/hostingpay-query.md`
- 要做托管支付退款：读 `references/hostingpay-refund.md`

## 语言边界提醒

- 聚合支付 PHP 已覆盖下单、扫码交易查询、关单、关单查询、退款、退款查询、对账
- 托管支付 PHP 已覆盖基础、预下单、查询 / 关单 / 对账、退款
- PHP 受支持场景如果需要输出代码，必须体现官方 `huifurepo/dg-php-sdk`
- Java 仍是聚合支付和托管支付的完整基线实现
