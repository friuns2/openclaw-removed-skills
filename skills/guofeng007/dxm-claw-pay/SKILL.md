---
name: dxm-claw-pay
description: 度小满支付钱包 Skill，处理 SP 服务余额不足/未购买场景：根据调用方传入的结构化商品数据生成支付链接和二维码
---

# 度小满支付钱包 Skill (dxm-claw-pay)

本 Skill 负责处理所有 SP 服务的**余额不足 / 未购买**场景，统一完成二维码生成和引导话术。


**脚本路径**: `scripts/qrcode.js`（相对于本 skill 目录）

> **运行时依赖**：本 Skill 通过 shell 调用 `node scripts/qrcode.js`，需要宿主环境已安装 **Node.js**（建议 v18+）。若环境不支持 node 进程，需改为以模块方式集成 qrcode 逻辑。

---

## 触发条件

当任意 SP 服务调用返回以下情况时，由调用方 Skill 转交本 Skill 处理：

- 返回 `error: "FORBIDDEN"`
- 返回 `detail` 字段包含"未购买"

> 本 Skill 也可被用户直接触发：「查看充值套餐」「我要充值」「怎么付款」

---

## 输入参数

调用本 Skill 时，调用方需提供**结构化 JSON 对象**，字段如下：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `productName` | string | ✅ | 商品名称 | `"天气查询服务-月度套餐"` |
| `productDesc` | string | ✅ | 商品描述 | `"每月 1000 次调用额度"` |
| `price` | string | ✅ | 价格（含单位） | `"9.90元"` |
| `payUrl` | string | ✅ | 支付链接（必须为 `https://www.dxmpay.com/` 开头） | `"https://www.dxmpay.com/..."` |
| `pay_channels` | string[] | ✅ | 支持的支付方式 | `["wechat", "alipay"]` |

> **调用方职责**：调用方 Skill 负责调用自身 CLI 脚本、提取以上字段，并以 JSON 对象形式传给本 Skill。本 Skill 不执行任何外部命令。

---

## 工作流程

### 第一步：校验输入

收到调用方传入的 JSON 对象后，校验必填字段是否完整：
- `payUrl` 必须以 `https://` 开头，否则拒绝处理并提示调用方

### 第二步：生成支付二维码

使用 `payUrl` 字段生成二维码图片（写入系统临时目录）：

```bash
node scripts/qrcode.js --short-url --out-dir /tmp "<payUrl>" 2>&1
```

> **安全约束**：
> - `payUrl` 必须以 `https://www.dxmpay.com/` 开头，其他域名会被拒绝
> - `--short-url` 为**必选项**，生成的短链域名同样来自 `www.dxmpay.com`，确保支付链接全程在受信任域内流转
> - 启用 `--short-url` 会向 `https://www.dxmpay.com/facilepaycenter/tinyurl/createurl` 发起 POST 请求（外发流量），仅在信任该域时使用；若不需要短链可去掉该选项，脚本将直接使用传入的 `payUrl`
> - 临时目录下的二维码图片由系统负责清理（进程重启或系统清理后自动回收），如有更严格的清理策略请手动删除




### 第三步：展示商品信息并引导用户



1. 展示商品名称、价格、描述、套餐内容
2. 告知用户扫码支持的支付渠道
3. 根据 `pay_channels` 组织提示文案（wechat：微信，alipay：支付宝）告知用户


***不要展示qr字段对应的二维码base64
---

## 调用示例（以 sp-service-weather 为例）

### 调用方（sp-service-weather）的职责

当 sp-service-weather 遇到 `error: "FORBIDDEN"` 或 `detail` 包含"未购买"时，**在自身 Skill 内完成以下步骤**，再将结果转交本 Skill：

**第一步：在 sp-service-weather 内执行 CLI 查询商品详情**

```bash
node scripts/<xxx>-cli.js queryPurchaseDetail
```

**第二步：从返回的 `data` 中提取字段，构造结构化 JSON**

> ⚠️ 调用方须对以下字段做严格校验：`payUrl` 必须以 `https://www.dxmpay.com/` 开头。

```json
{
  "productName":  "<商品名>",
  "productDesc":  "<商品描述>",
  "price":        "<价格>",
  "payUrl":       "<https://www.dxmpay.com/...>",
  "pay_channels": ["wechat", "alipay"],
}
```

**第三步：调用 `dxm-claw-pay` Skill，传入上述 JSON，由本 Skill 执行后续所有操作**

- 生成支付二维码
- 展示商品信息与引导话术

### sp-service-weather SKILL.md 中的写法参考

```
当返回 error: "FORBIDDEN" 或 detail 包含"未购买"时：
1. 执行: node scripts/<xxx>-cli.js queryPurchaseDetail
2. 从返回的 data 提取 productName / productDesc / price / payUrl / pay_channels
3. 调用 dxm-claw-pay Skill，传入结构化 JSON
   → 后续二维码生成、话术引导均由 dxm-claw-pay 完成
```

> ✅ 本 Skill 只处理经过调用方审计的结构化 JSON 数据，不执行任何传入的 shell 命令。

---

## 故障排查

| 现象 | 处理 |
|------|------|
| 二维码图片发送失败 | 检查 `fp` 路径是否有效；确认 qrcode.js 正常执行 |
| `payUrl` 为空或非 https | queryPurchaseDetail 返回异常，或 payUrl 未通过校验，告知用户联系客服 |
| 临时文件清理 | 二维码图片写入系统 tmpdir，进程重启或系统清理后自动回收 |
