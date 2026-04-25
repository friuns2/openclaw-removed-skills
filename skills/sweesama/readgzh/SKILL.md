# ReadGZH — 微信公众号文章 AI 阅读器

ReadGZH 是一款专为 AI 智能体设计的微信公众号内容解析工具。它通过服务端代理绕过微信的反爬虫机制，将复杂的公众号 HTML 转换为纯净、结构化的 Markdown 内容，大幅节省 Token 消耗。

## ⚠️ 使用前必读

| 情况 | 限制 | 解决方案 |
|------|------|---------|
| **匿名用户**（无 API Key） | 每天仅 **10 次/IP**，超出触发 429 | 注册获取 API Key |
| **带 API Key** | 每日 50 credits（需在控制台领取）/ Pro 最高 2000/月 | `-H "Authorization: Bearer sk_live_..."` |
| **缓存文章** | 已转换过的文章再次读取 | **完全免费**，不限次数 |

**429 错误原因**：匿名请求超出 IP 频率限制（每天10次），不是服务故障，
**注册 API Key 即可解决 → [免费注册 →](https://readgzh.site/dashboard)**

---

## 快速开始

直接对你的 AI 助手下令：

> **"帮我读一下这篇文章：[微信公众号链接]"**

---

## 接入方式选择

### 方式一：MCP 协议（推荐）

OpenClaw 原生支持 MCP，配置后**自动处理认证**，无需手动注入 Header。

**在 OpenClaw config 中添加：**

```json
{
  "mcpServers": {
    "readgzh": {
      "url": "https://api.readgzh.site/mcp-server"
    }
  }
}
```

重启 OpenClaw 后，ReadGZH 的 `readgzh.read` 等工具会自动被发现并使用。

**可用 MCP Tools：**
- `readgzh.read` — 读取微信文章（URL）
- `readgzh.get` — 通过 slug 获取已缓存文章
- `readgzh.search` — 按关键词搜索已缓存文章
- `readgzh.list` — 列出最近缓存的文章

---

### 方式二：REST API + curl

直接用 curl 调用（需手动加 Bearer Token）：

```bash
# 基础调用（需 Bearer 认证）
curl "https://api.readgzh.site/rd?url=https://mp.weixin.qq.com/s/xxxxx" \
  -H "Authorization: Bearer <YOUR_API_KEY>"

# POST 方式（抓取并缓存）
curl -X POST "https://api.readgzh.site/rd" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxxxx"}'
```

**响应示例（POST）：**
```json
{
  "success": true,
  "articleId": "abc123-...",
  "slug": "s/article-title",
  "cached": false,
  "data": {
    "title": "文章标题",
    "author": "作者名",
    "content": "文章纯文本内容...",
    "publishTime": "2025-01-01",
    "sourceUrl": "https://mp.weixin.qq.com/s/..."
  }
}
```

---

### 方式三：browser 读取（无需 API Key）

如果 OpenClaw 有 Chrome 会话（SS实战舱），可以直接用 CDP 打开微信文章 URL 读取 DOM，不需要 API：

```
browser(action=open, url="https://mp.weixin.qq.com/s/xxxxx")
```

---

## API 端点一览

| 端点 | 方式 | 说明 |
|------|------|------|
| `GET /rd?url=...` | 直接抓取并返回 HTML | 适合 AI 直接读取 |
| `POST /rd` | 抓取并缓存 | 返回 JSON（含 articleId + slug）|
| `GET /rd?s=slug` | 读取已缓存文章 | 返回 HTML |
| `GET /rd?id=...` | 通过 ID 读取 | 返回 HTML |
| `GET /rd?s=...&mode=summary` | AI 智能摘要（Pro 专属）| 返回结构化摘要 JSON |
| `POST https://api.readgzh.site/mcp-server` | MCP 协议 | JSON-RPC 2.0，自动认证 |

---

## Credits 说明

| 类型 | 消耗 | 说明 |
|------|------|------|
| 简单文章（< 5 图）| 1 credit | |
| 复杂文章（≥ 5 图）| 2 credits | |
| 缓存文章读取 | **免费** | 不限次数 |
| 免费额度 | 30 credits/天 | 需在控制台点击「领取今日积分」 |
| Pro 订阅 | 最高 2000/月 | 自动发放，无需领取 |

---

## 错误码

| 状态码 | 含义 |
|--------|------|
| `401` | 未提供 API Key 或 Key 无效 |
| `402` | API Key 积分已用完，需充值 |
| `403` | 功能需要 Pro 套餐（如 `?mode=summary`）|
| `429` | **匿名请求超出每天 10 次限制**，注册 API Key 即可解决 |

---

## 开发者信息

- **完整文档**：[readgzh.site/docs](https://readgzh.site/docs)
- **API Key 领取**：[readgzh.site/dashboard](https://readgzh.site/dashboard)
- **OpenAPI 规范**：[readgzh.site/.well-known/openapi.yaml](https://readgzh.site/.well-known/openapi.yaml)
- **技术支持**：[readgzh.site](https://readgzh.site)
- **开发维护**：Sweesama（[@sweesama](https://github.com/sweesama)）
