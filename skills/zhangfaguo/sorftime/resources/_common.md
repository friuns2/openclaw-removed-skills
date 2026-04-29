# Sorftime CLI 公共参考（_common.md）

> 所有 resources/*.md 共用的 Domain 表、错误码表、返回结构、CLI 调用模板。各接口文档**只保留接口本身的参数/字段/示例**，公共部分一律引用本文件。

---

## 1. CLI 调用模板

```bash
sorftime api <Endpoint> '<json-params>' --domain <N> --profile <name>
```

| 选项 | 说明 |
|------|------|
| `<Endpoint>` | 接口名，**严格区分大小写**，按本目录各文件中的 PascalCase 写法（如 `ProductRequest`、`KeywordBatchSubscription`）。CLI 的 README 里小写形式仅作示例，实际请求严格按 PascalCase。 |
| `<json-params>` | 单引号包裹的 JSON 字符串。多参数接口可省略不必需字段，按各接口文档要求传。 |
| `--domain` | 站点代码（见下表）。Amazon 1-14、Shopee 201-208、Walmart 21。**忘传或传错会直接 401/404**。 |
| `--profile` | profile 名称，对应 `sorftime add` 创建的鉴权配置（含 token 与默认 domain）。可省略，省略时用 `sorftime use` 当前选中的 profile。 |


**Profile 管理速查**：
```bash
sorftime add <profile-name> <api-key>          # 添加 profile-name
sorftime list                                  # 查看所有 profile-name
sorftime use <profile-name>                    # 切换默认 profile-name
sorftime whoami                                # 查看当前 profile-name
sorftime rm <profile-name>                     # 删除 profile-name
```

---

## 2. Amazon Domain 表（14 站）

| domain | 站点 | 国家 |
|--------|------|------|
| 1 | US | 美国 |
| 2 | UK | 英国 |
| 3 | DE | 德国 |
| 4 | FR | 法国 |
| 5 | IN | 印度 |
| 6 | CA | 加拿大 |
| 7 | JP | 日本 |
| 8 | ES | 西班牙 |
| 9 | IT | 意大利 |
| 10 | MX | 墨西哥 |
| 11 | AE | 阿联酋 |
| 12 | AU | 澳大利亚 |
| 13 | BR | 巴西 |
| 14 | SA | 沙特阿拉伯 |

---

## 3. Shopee Domain 表（8 站）

| domain | 站点 | 国家/地区 |
|--------|------|-----------|
| 201 | VN | 越南 |
| 202 | ID | 印度尼西亚 |
| 203 | SG | 新加坡 |
| 204 | TH | 泰国 |
| 205 | MY | 马来西亚 |
| 206 | TW | 中国台湾 |
| 207 | PH | 菲律宾 |
| 208 | BR | 巴西 |

---

## 4. Walmart Domain 表（1 站）

| domain | 站点 | 国家 |
|--------|------|------|
| 21 | US | 美国（Walmart 当前仅开放美国站）|

---

## 5. 通用返回结构

所有接口统一返回 JSON：

```json
{
  "requestleft": 3000,
  "requestconsumed ": 1,
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 说明 |
|------|------|
| `requestleft` | 剩余request数 |
| `requestconsumed` | 本次请求消耗请求数 |
| `code` | 业务状态码，**判断成功的唯一依据**（见错误码表）。`0` 表示成功；非 0 即为业务错误。 |
| `message` | 状态描述，错误时含具体原因。 |
| `data` | 业务数据，结构各接口不同。 |

---

## 6. 完整错误码表

### 业务错误码（HTTP 200 + JSON code 非 0）

| code | 含义 | 排查建议 |
|------|------|---------|
| `0` | 成功 | — |
| `4` | 参数错误 / 不合法 | 核对接口文档参数表，重点检查必填项、字段类型、枚举值 |
| `97` | 当日积分不足 | 查 `sorftime whoami` 看余额，或换 profile |
| `98` | 接口/数据未授权 | 套餐未开通该接口或站点；需联系 Sorftime 开通 |
| `99` | 服务端处理失败 | 重试；持续失败联系技术支持并保留 `requestId` |
| `-999` | 监控类接口任务异常 | 仅在 `monitoring` 系列接口出现；查 task schedule list 看任务状态 |

---

## 9. 限流与并发约束（通用）

| 维度 | 上限 | 备注 |
|------|------|------|
| 单 profile QPM | ≤ 200 | 超过200 QPM 请求会提示限流 |

---

## 10. 各接口文档引用方式

各 resources/*.md 头部应统一写：

```markdown
> 公共参考见 [`_common.md`](./_common.md)：CLI 调用模板、Domain 表、错误码、返回结构、限流约束。本文档只描述本类接口独有的参数与字段。
```

---

**最近更新**：2026-04-27
