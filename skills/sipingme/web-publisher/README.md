# Web Publisher Skill

将任意网页文章自动提取、改写、发布到内容平台（目前支持微信公众号）的 OpenClaw Skill。
**纯 HTTP 调用，不安装任何 npm 依赖**——抓取、图片下载、AI 改写、发布全部由服务端完成。

## 功能

- **网页 → 公众号一键发布**：交给一个 URL，剩下交给服务端
- **平台适配**：微信、知乎、36kr、CSDN、今日头条、小红书、人人都是产品经理 + 通用回退
- **图片处理**：服务端下载文章图片并自动上传到微信媒体库
- **AI 改写**（可选）：Minimax 驱动的分段改写，多种风格
- **对话式接入**：登录、绑定公众号都通过浏览器一次性短链完成，**AppSecret 永不进入对话**

## 快速开始

只需两步浏览器跳转，全部在对话里完成：

### 1) 在对话里说「帮我登录」

AI 会执行 `scripts/run.js login`，CLI 会打印一条一次性短链：

```
请在浏览器中打开以下链接，确认绑定到你的账号：
  https://tools.siping.me/skill/bind?code=ABCD-EFGH
  绑定码: ABCD-EFGH
  有效期: 5 分钟
```

在浏览器完成注册/登录 + 点「确认绑定」，凭证会自动写入 `~/.web-publisher/credentials.json`（mode 0600，仅当前用户可读）。

### 2) 在对话里说「帮我配置公众号」

AI 调用 `scripts/run.js wechat config`，CLI 同样打印短链。在浏览器表单里填 AppID/AppSecret 即可，**AppSecret 直接 POST 到服务端 AES-256-GCM 加密落库，永不进入对话上下文**。

同一页面会展示需要在 mp.weixin.qq.com 后台加入 IP 白名单的服务器 IP——这一步只能你自己去公众号后台操作。

完成。直接说「把这篇文章发到公众号草稿 https://...」就能用了。

### 环境变量（可选，CI 使用）

凭证文件优先；以下变量仅在无浏览器环境（如 CI）使用，优先级更高：

| 变量 | 说明 |
|---|---|
| `WEB_PUBLISHER_TOOLS_URL` | 账号 API 地址（默认 `https://tools.siping.me/api`） |
| `WEB_PUBLISHER_API_URL` | pipeline API 地址（登录会自动写入凭证） |
| `WEB_PUBLISHER_USER_ID` | 用户 ID |
| `WEB_PUBLISHER_API_KEY` | API Key |

## 使用示例

在 OpenClaw 中与 AI 对话即可：

> 帮我登录

> 帮我配置一下公众号

> 帮我把这篇文章存到公众号草稿 https://mp.weixin.qq.com/s/xxxxx

> 把这篇文章改写成轻松的风格，存到草稿 https://example.com/article

> 把这篇文章直接发布到公众号 https://example.com/article

## 可用选项

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--theme <name>` | 发布主题 | `blackink` |
| `--rewrite` | 启用 AI 改写 | 关闭 |
| `--style <style>` | 改写风格：`casual` / `formal` / `technical` / `creative` | `casual` |
| `--prompt <text>` | 自定义改写提示 | - |

**可用主题**：`blackink`（默认）、`default`、`orangesun`、`redruby`、`greenmint`、`purplerain`

## 支持平台

**发布目标**：

| 平台 | 提取 | 发布 | 状态 |
|---|---|---|---|
| 微信公众号 | ✅ | ✅ | 已支持 |
| 今日头条 | ✅ | — | 计划中 |
| 小红书 | ✅ | — | 计划中 |

**内容来源**（任意 URL 都可以丢进来，服务端会选最合适的适配器）：
微信文章、知乎专栏、36kr、CSDN、今日头条、小红书、人人都是产品经理，以及任何标准网页（通用 readability 模式）。

## 工作原理

```
URL ──▶ /pipeline (服务端)
         │
         ├─ news-to-markdown        抓取正文 + 标题 + 封面
         ├─ markdown-ai-rewriter    可选，AI 改写
         └─ wechat-md-publisher     上传图片 + 创建草稿 / 发布
                ▼
         返回 jobId，CLI 轮询直到完成
```

CLI 只负责凭证管理 + HTTP 调用，**完全没有本地依赖**。

## License

MIT
