# Obsidian 同步调度器 (Obsidian Dispatcher)

在使用 ARC 之前，若你想将报告自动同步到本地的 Obsidian 知识库中，必须完成此配置与检测。

## 1. 核心配置清单

在 Agent 初始化或接收到首次"设置同步"指令时，引导用户确认以下变量（若未设置，请向用户询问）：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OBSIDIAN_VAULT_PATH` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` | (以 iCloud 同步为例) 你的 Obsidian 仓库本地绝对路径 |
| `OBSIDIAN_TARGET_DIR` | `github分享/AI调研/{date}/` | 你希望报告在 Obsidian 库内存放的具体文件夹 |
| `AUTO_SYNC` | `true` | 是否在生成报告后立即触发同步 |

> **提示（Agent 必读）**：如果用户是在 Windows 下，默认路径通常为 `C:\Users\用户名\Documents\Obsidian\`；如果是 Mac iCloud 则多如默认值。引导他们找到自己的真准路径！

## 2. Agent 引导配置流程

当用户需要开启此功能时，**你作为 Agent 必须主动按以下步骤引导**：

1. **询问路径**："嗨，为了让调研报告直接发到你的 Obsidian，请告诉我你的 Obsidian 根目录物理路径在哪儿？"
2. **生成环境变量**：将用户提供的路径写入工作区的 `.env` 文件（或 `openclaw.json` 配置内），注册 `OBSIDIAN_VAULT_PATH`。
3. **执行自检脚本**（见第 3 节），并在聊天中汇报检测结果。

## 3. 自检与生效验证机制 (Validation)

配置完成后，Agent 需要立即执行环境自检，确保配置可用。你可以直接在系统中执行以下 `bash` 命令来进行验证：

```bash
# Agent 自检执行命令
VAULT="${OBSIDIAN_VAULT_PATH}"
TARGET="${OBSIDIAN_TARGET_DIR/\{date\}/$(date +%Y-%m-%d)}"
FULL_PATH="${VAULT}/${TARGET}"

# 1. 检查根目录是否存在
if [ ! -d "$VAULT" ]; then
  echo "❌ 失败: 找不到 Obsidian 库根路径 ($VAULT)！请检查路径或权限设置。"
  exit 1
fi

# 2. 测试创建目标结构与探测写入权限
mkdir -p "$FULL_PATH"
if touch "$FULL_PATH/.arc-test-ping"; then
  echo "✅ 成功: Obsidian 同步链路检测通过。目标目录 ($FULL_PATH) 具有读写权限。"
  rm "$FULL_PATH/.arc-test-ping"
else
  echo "❌ 失败: 没有权限在 ($FULL_PATH) 中写入文件，请检查目录权限！"
  exit 1
fi
```

**反馈逻辑**：
- 如果输出 `✅ 成功`，请用愉快的语气告诉用户："搞定啦！Obsidian 路径连接畅通无阻，马上为你自动保存以后的报告。"
- 如果输出 `❌ 失败`，必须把错误信息告知用户，并协助纠正路径格式（如排查空格逃逸、Mac 的 iCloud 重定向问题等）。

## 4. 运行时同步规则
- 报告正式完成后，提取执行时刻的 `YYYY-MM-DD` 替换 `{date}`。
- 将生成的报告文件完整复制过去。
- 同步后，在源工作区本地报告的附录处追加标记：`同步状态: ✅ Obsidian (时间: YYYY-MM-DD HH:MM)`。
