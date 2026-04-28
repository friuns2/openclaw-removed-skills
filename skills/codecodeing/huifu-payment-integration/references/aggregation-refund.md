# 聚合支付退款

这份文档覆盖聚合支付退款申请和退款查询。

## 目录

- 什么时候读这里
- 退款主流程
- 对应接口
- 请求头强制约束
- 退款申请 data 请求字段
- 退款查询 data 请求字段
- 关键定位字段
- 核心规则
- 退款期限
- 容易混淆的流水号
- 当前语言边界
- 回读建议

## 什么时候读这里

- 原交易已确认支付成功
- 需要调用聚合支付退款接口
- 需要轮询或查询退款结果

## 退款主流程

```text
确认原交易成功且定位键完整
  -> 发起退款
  -> 处理中时等待异步通知或主动查询
  -> 查询最终退款状态
  -> 成功后再更新业务退款状态
```

## 对应接口

| 场景 | 接口 |
| --- | --- |
| 退款申请 | `v4/trade/payment/scanpay/refund` |
| 退款查询 | `v4/trade/payment/scanpay/refundquery` |

## 请求头强制约束

- 上面 2 个接口都必须带 `jpt-x-skill-source: <skill_source>`
- 如果当前按 PHP 接入，且请求 `data` 中存在 `huifu_id`，还必须带 `jpt-x-skill-huifu_id: <data.huifu_id>`
- 当前 Skill 包对齐的官方 PHP SDK 主链路在 `MerConfig.skill_source` 已配置时，会自动带 `jpt-x-skill-source`，并在当前请求 `huifu_id` 存在且非空时自动带 `jpt-x-skill-huifu_id`
- 当前 Java SDK 基线也会在请求 `data` 中存在 `huifu_id` 且非空时自动带 `jpt-x-skill-huifu_id: <data.huifu_id>`
- 这两项属于 HTTP 请求头，不属于业务报文 `data`；具体明细以 `references/shared-request-header-policy.md` 为准

## 退款申请 data 请求字段

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `req_date` | Y | 本次退款请求日期，格式 `yyyyMMdd` |
| `req_seq_id` | Y | 本次退款请求流水号，同一 `huifu_id` 下当天唯一 |
| `huifu_id` | Y | 商户号 |
| `ord_amt` | Y | 申请退款金额，单位元，保留两位小数；延时交易退款金额必须小于等于待确认金额 |
| `org_req_date` | Y | 原交易请求日期，格式 `yyyyMMdd` |
| `org_hf_seq_id` | C | 原交易全局流水号；与 `org_party_order_id`、`org_req_seq_id` 三选一 |
| `org_party_order_id` | C | 原交易微信/支付宝用户账单上的商户单号；与另外两项三选一 |
| `org_req_seq_id` | C | 原交易请求流水号；与另外两项三选一 |
| `remark` | N | 备注，原样返回 |
| `notify_url` | N | 退款异步通知地址 |
| `tx_metadata` | N | 扩展参数集合，JSON Object 字符串 |

### `tx_metadata`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `acct_split_bunch` | N | 分账退款对象，JSON Object 字符串 |
| `combinedpay_data` | N | 补贴支付退款信息，JSON Array 字符串 |
| `terminal_device_data` | N | 设备信息，JSON Object 字符串 |

#### `acct_split_bunch.acct_infos[]`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `div_amt` | Y | 分账金额，单位元，保留两位小数 |
| `huifu_id` | Y | 分账接收方 ID |

#### `combinedpay_data[]`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `huifu_id` | Y | 渠道与一级代理商直属商户 ID |
| `user_type` | Y | 补贴方类型：`channel`、`merchant`、`agent`、`mertomer` |
| `acct_id` | Y | 营销补贴方账户号 |
| `amount` | Y | 补贴金额，单位元，保留两位小数 |

#### `terminal_device_data`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `device_type` | N | `1` 手机，`2` 平板，`3` 手表，`4` PC |
| `device_ip` | N | 交易设备公网 IP，当前建议按 IPv4 传 |
| `device_mac` | N | 交易设备 MAC |
| `device_imei` | N | 交易设备 IMEI |
| `device_imsi` | N | 交易设备 IMSI |
| `device_icc_id` | N | 交易设备 ICCID |
| `device_wifi_mac` | N | 交易设备 WIFI MAC |
| `device_gps` | N | 交易设备 GPS |

## 退款查询 data 请求字段

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `huifu_id` | Y | 商户号 |
| `org_req_date` | C | 退款请求日期；传退款全局流水号时可不传 |
| `org_hf_seq_id` | C | 退款全局流水号；与 `org_req_seq_id`、`mer_ord_id` 三选一 |
| `org_req_seq_id` | C | 退款请求流水号；与 `org_hf_seq_id`、`mer_ord_id` 三选一 |
| `mer_ord_id` | C | 终端订单号；与 `org_hf_seq_id`、`org_req_seq_id` 三选一 |

查询补充说明：

- 退款查询里的 `org_req_seq_id` 指的是退款请求流水号，不是原支付流水号。
- 查询返回字段和勘误说明继续看 `references/aggregation-refund-query.md`。

## 关键定位字段

- 原交易定位键：`org_hf_seq_id`、`org_party_order_id`、`org_req_seq_id` 三选一；退款申请时 `org_req_date` 仍是必带字段
- 退款查询定位键：退款交易自己的 `org_hf_seq_id`、退款 `org_req_seq_id`、`mer_ord_id` 三选一

## 核心规则

1. 退款金额不能超过原交易金额
2. `resp_code=00000000` 或 `00000100` 只表示请求已受理
3. 退款最终结果必须以异步通知或退款查询为准
4. 退款结果要做幂等处理

## 退款期限

| 渠道 | 最大退款期限 |
| --- | --- |
| 微信 | `360` 天 |
| 支付宝 | `360` 天 |
| 银联二维码 | `360` 天 |

## 容易混淆的流水号

```text
原交易下单：A001
退款请求：B001，且 org_req_seq_id = A001
退款查询：查询的是 B001，不是 A001
```

## 当前语言边界

- Java 提供完整路径
- 聚合支付 PHP 已支持 `Payment::refund()` 与 `Payment::refundQuery()`；示例入口见 `references/aggregation-query-php-scenarios.md`

## 回读建议

- 需要看退款查询完整返回字段：读 `references/aggregation-refund-query.md`
- 还没做最终支付确认：先读 `references/aggregation-query.md`
- 还没完成初始化：回到 `references/aggregation-base.md`
