---
name: web-publisher
version: 0.5.0
description: 输入文章 URL，自动提取正文、可选 AI 改写、并发布到微信公众号。支持微信、知乎、36kr、CSDN、头条、小红书等平台提取，全部由服务端完成；CLI 不安装任何 npm 依赖。注册、登录、公众号配置全部通过对话 + 一次性浏览器跳转完成。可配合 browser-web-search 先搜索拿到 URL 再批量发布。
author: Ping Si <sipingme@gmail.com>
tags: [publish, wechat, article, content, onboarding]
---

# Web Publisher

输入文章 URL，自动提取正文、可选 AI 改写、并发布到微信公众号。**纯 HTTP 调用，无本地依赖**——抓取 / 图片 / 改写 / 发布全部由服务端完成。

## 给 AI 的使用说明（核心）

### 用户意图 → 命令

| 用户说什么 | 调用 | 然后做什么 |
|---|---|---|
| 帮我登录 / 注册 / 绑定账号 | `scripts/run.js login` | 把 CLI 输出的浏览器链接和绑定码**原文**交给用户；CLI 自己轮询并保存凭证，**不要自己重试** |
| 配置/绑定公众号 / 配 AppID | `scripts/run.js wechat config` | 把短链和"需要加入 IP 白名单的 IP 列表"**原文**交给用户 |
| 我现在是谁 / 看看账号 / 余额 | `scripts/run.js whoami` | 报告账号、apiKey 脱敏摘要、微信配置状态 |
| 公众号配好了吗 | `scripts/run.js wechat status` | 报告 `configured` 与当前 AppID |
| 退出登录 / 注销 | `scripts/run.js logout` | 报告"已清除本地凭证" |
| 把这篇文章存到草稿 `<url>` | `scripts/run.js draft <url>` | 等待返回，转告标题与 mediaId |
| 把这篇文章发布到公众号 `<url>` | `scripts/run.js publish <url>` | 仅当用户**明确说"发布"** 才用 publish；默认走 draft |
| 改写后存草稿 / 发布 | `... draft <url> --rewrite [--style casual]` | 同上 |
| 上次那个任务完成了吗 | `scripts/run.js status <jobId>` | 转告 status / progress / result |

### 关键约束（必须遵守）

1. **AppSecret 永不进入对话上下文**。`wechat config` 只输出短链，用户在浏览器表单提交，AI 不要询问、不要展示、不要日志化 AppSecret。
2. **默认 draft，不要主动 publish**。除非用户原话里明确说了"发布 / 直接发到公众号 / publish"，否则一律用 `draft`。
3. **耗时正常**。整体 30–90 秒（带 `--rewrite` 更久），CLI 每 5 s 打一次进度。**不要超时重试**——重复调用会创建多个草稿。
4. **错误恢复对照**：

   | CLI 错误 | 正确处置 |
   |---|---|
   | `尚未登录` | 提示用户跑 `scripts/run.js login` |
   | `WeChat credentials not configured` | 提示用户跑 `scripts/run.js wechat config` |
   | `余额不足 / insufficient credits` | 提示用户去 [tools.siping.me](https://tools.siping.me) 充值 |
   | 任务 `failed`，error 含 `抓取失败` | 把原 error 转给用户；目标网站可能反爬或 URL 无效 |

### 与 browser-web-search 配合（搜索 + 发布）

用户只给关键词没有 URL 时，先用 `browser-web-search` 拿 URL 列表，再逐条调本 skill：

```bash
# Step 1：搜索拿 URL（browser-web-search skill）
bws toutiao/search "AI Search" --count 3 --sort time

# Step 2：对每个 URL 调本 skill
scripts/run.js draft <url1>
scripts/run.js draft <url2>
scripts/run.js draft <url3>
```

如果用户已经给了 URL，**跳过 Step 1**。

## 前置要求

仅两步对话式接入，**无需安装任何 npm 依赖**。

### 1. 首次登录

用户说「帮我登录」→ AI 调 `scripts/run.js login` → CLI 打印一次性短链：

```
请在浏览器中打开以下链接，确认绑定到你的账号：
  https://tools.siping.me/skill/bind?code=ABCD-EFGH
  绑定码: ABCD-EFGH
  有效期: 5 分钟
```

用户在浏览器完成注册/登录 + 点「确认绑定」。CLI 自动轮询，凭证写入 `~/.web-publisher/credentials.json`（mode 0600，仅当前用户可读）。

### 2. 配置微信公众号

用户说「帮我配置公众号」→ AI 调 `scripts/run.js wechat config` → CLI 打印短链 + 需加白名单的服务器 IP。用户在浏览器表单填 AppID/AppSecret 提交（**AppSecret 直接 POST 到服务端 AES-256-GCM 加密落库，永不进入对话上下文**）。

加 IP 白名单只能在 mp.weixin.qq.com 后台完成，无法绕过。

### （可选）环境变量

仅 CI / 无浏览器场景使用，优先级高于本地凭证：

| 变量 | 说明 |
|---|---|
| `WEB_PUBLISHER_TOOLS_URL` | 账号 API（默认 `https://tools.siping.me/api`） |
| `WEB_PUBLISHER_API_URL` | pipeline API（登录后凭证文件里也会带） |
| `WEB_PUBLISHER_USER_ID` | 用户 ID（如 `usr_xxxx`） |
| `WEB_PUBLISHER_API_KEY` | API Key |

## 命令参考

```bash
# 账号
scripts/run.js login              # 浏览器一次性绑定
scripts/run.js logout             # 撤销 apiKey + 删本地凭证
scripts/run.js whoami             # 当前账号 + 微信配置 + 余额

# 公众号
scripts/run.js wechat config      # 浏览器表单填 AppID/AppSecret
scripts/run.js wechat status      # configured ? appId

# 发布
scripts/run.js draft   <url> [options]   # 创建草稿（默认）
scripts/run.js publish <url> [options]   # 直接发布
scripts/run.js status  <jobId>           # 查任务进度

# 帮助
scripts/run.js help
```

### 发布选项

| 选项 | 默认 | 说明 |
|---|---|---|
| `--theme <id>` | `blackink` | 主题：`blackink` / `default` / `orangesun` / `redruby` / `greenmint` / `purplerain` |
| `--rewrite` | 关闭 | 启用 AI 分段改写 |
| `--style <name>` | `casual` | 配合 `--rewrite`：`casual` / `formal` / `technical` / `creative` |
| `--prompt "<text>"` | — | 自定义改写提示，覆盖 `--style` |

### 调用样例

```bash
scripts/run.js draft   https://mp.weixin.qq.com/s/xxxxx
scripts/run.js draft   https://zhuanlan.zhihu.com/p/xxx --theme orangesun
scripts/run.js draft   https://36kr.com/p/xxx --rewrite --style casual
scripts/run.js publish https://example.com/article
scripts/run.js status  job_abc123
```

## 支持平台

**发布目标**：微信公众号（草稿 / 直接发布）。其他平台规划中。

**内容来源**（任意 URL，服务端自动选适配器）：

| 平台 | 适配器 | 配合 `bws <平台>/search` |
|---|---|---|
| 微信公众号 | ✅ | ✅ |
| 今日头条 | ✅ | ✅ |
| 知乎 | ✅ | ✅ |
| 36kr | ✅ | ✅ |
| CSDN | ✅ | ✅ |
| 小红书 | ✅ | ✅（部分内容需登录） |
| 人人都是产品经理 | ✅ | — |
| 任意网页 | ✅ 通用 readability | — |

## 工作原理

```
URL ──▶ POST /pipeline （X-User-Id + X-Api-Key）
         │
         ├─ news-to-markdown        服务端抓正文 + 标题 + 封面
         ├─ markdown-ai-rewriter    可选，AI 分段改写
         └─ wechat-md-publisher     下载图片 → 上传微信媒体库 → 草稿/发布
                ▼
         返回 jobId，CLI 轮询 GET /jobs/<jobId> 至 completed / failed
```

CLI 端只做**凭证管理 + HTTP 调用**，没有任何抓取 / 解析 / 图片下载逻辑，也不安装任何 npm 包。

## 安全与信任

- **数据流**：CLI 把 `{url, action, theme, rewrite?}` + 你的 API Key 发给服务端；服务端自行抓取目标网页全文与图片，并发布到微信。⚠️ **服务端会接收原始 URL 并下载全文 + 图片**。
- **AppSecret**：永不进入对话上下文；浏览器表单直传服务端，AES-256-GCM 加密落库。
- **apiKey**：device_code 在绑定成功后立刻 consumed，一次性下发；`logout` 远端撤销 + 删本地。
- **本地凭证**：`~/.web-publisher/credentials.json`（mode 0600）。
- **IP 白名单**：mp.weixin.qq.com 后台授权远程服务器 IP 直接调微信 API；请确认你信任该 IP 归属方（[tools.siping.me](https://tools.siping.me)）。
- **审计**：所有操作记录可在 tools.siping.me 个人页面查看；源码 [github.com/sipingme/web-publisher-skill](https://github.com/sipingme/web-publisher-skill)。
