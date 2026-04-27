# 安装与配置

## 前置条件

| 依赖        | 版本             | 用途                            |
| ----------- | ---------------- | ------------------------------- |
| Node.js     | 18+              | CLI 运行时及 `node -e` 数据过滤 |
| npm 或 pnpm | npm 8+ / pnpm 8+ | 安装全局包                      |

## 安装 CLI

```bash
npm install -g siluzan-tso-cli
```

---

## 初始化 Skill 文件

```bash
siluzan-tso init -d /path/to-your/skills       # 写入自定义目录
```

使用 `init -d /path/to/skills`的方式，将skill复制到你的skill目录下

支持的 `--ai` 目标：
| 值 | 写入路径 |
|----|---------|
| `cursor` | `.cursor/skills/siluzan-tso/` |
| `claude` | `.claude/skills/siluzan-tso/` |
| `openclaw-workspace` | `skills/siluzan-tso/` |
| `openclaw-global` | `~/.openclaw/skills/siluzan-tso/` |
| `workbuddy-workspace` | `.workbuddy/skills/siluzan-tso/` |
| `workbuddy-global` | `~/.workbuddy/skills/siluzan-tso/` |
| `all` | 以上全部 |

---

## 首次登录 / 配置凭据

`siluzan-tso` 与 `siluzan-cso` **共用同一份凭据**，存储在 `~/.siluzan/config.json`，配置一次两个 CLI 均可使用。

```bash
siluzan-tso login                          # 交互式登录，按提示创建 API Key 后粘贴
siluzan-tso login --api-key <YOUR_API_KEY> # 直接设置 API Key（跳过交互）
siluzan-tso config set --api-key <Key>     # 或通过 config set 直接写入
siluzan-tso config set --token <Token>     # 备用：设置 JWT Token
```

API Key 获取入口：`https://www.siluzan.com/v3/foreign_trade/settings/apiKeyManagement`

### 通过环境变量传入凭据（CI/CD 推荐）

无需写入 config.json，直接通过环境变量传入：

```bash
export SILUZAN_API_KEY=<YOUR_API_KEY>       # API Key（推荐）
# 或
export SILUZAN_AUTH_TOKEN=<YOUR_TOKEN>      # JWT Token
```

环境变量优先级高于 config.json，适合 CI/CD、Docker 容器、自动化脚本等场景。可通过 `siluzan-tso config show` 确认当前生效的凭据来源。

**凭据读取优先级（由高到低）：**

| 凭据类型  | 优先级                                                                           |
| --------- | -------------------------------------------------------------------------------- |
| API Key   | `SILUZAN_API_KEY` 环境变量 → `config.json` → `apiKey`                            |
| JWT Token | `--token` CLI 参数 → `SILUZAN_AUTH_TOKEN` 环境变量 → `config.json` → `authToken` |

> API Key 鉴权优先级高于 JWT Token，两者同时存在时使用 API Key。

---

## 查看当前配置

```bash
siluzan-tso config show
```

输出示例：

```
  构建环境     : production
  apiBaseUrl   : https://tso-api.siluzan.com
  googleApiUrl : https://googleapi.mysiluzan.com
  webUrl       : https://www.siluzan.com
  apiKey       : abcd****1234
```

`webUrl` 是前端页面基地址，需要引导用户打开网页时用此值拼接路径。

---

## 使用 webUrl 进行网页操作

- 涉及充值、账户激活、首页看板等**必须在网页完成**的操作时，应先通过 `siluzan-tso config show` 获取 `webUrl` 值，再按各业务文档提供的相对路径拼接完整链接，引导用户在浏览器中完成后续步骤。

## 更新

需要严格按照步骤执行

- 执行 npm install -g siluzan-tso-cli@[beta|latest]根据当前使用的是beta版本还是正式版本更新对应的版本到最新版
- 执行 siluzan-tso init -d /path/to/skills 复制项目中最新的skill文件来更新你的skill

---

## 修改其他配置

```bash
siluzan-tso config set --api-base <url>    # 切换 TSO API 地址
# Google API 地址从 TSO API 自动推导，如需覆盖可设置环境变量：
# export SILUZAN_GOOGLE_API=<url>
siluzan-tso config clear                   # 清空所有凭据
```

---
