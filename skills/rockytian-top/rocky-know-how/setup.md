# rocky-know-how 安装配置指南 (v2.9.1)

## 版本要求
- OpenClaw: 2026.4.21+（支持 4 个 Hook 事件）
- Node.js: 18+（Hook 集成）
- Bash: 3.x+（macOS/Linux 兼容）

---

## 🚀 快速安装（3 分钟）

### 方式1: ClawHub 一键安装（推荐）
```bash
openclaw skills install rocky-know-how
```

### 方式2: 手动安装
```bash
# 1. 克隆仓库
git clone https://gitee.com/rocky_tian/skill.git
cd skill/rocky-know-how

# 2. 运行安装脚本
bash scripts/install.sh
```

安装脚本会自动：
1. ✅ 复制脚本到 `~/.openclaw/skills/rocky-know-how/`
2. ✅ 创建符号链接到 `~/.openclaw/.learnings/`
3. ✅ **自动配置 Hook 到 openclaw.json**
4. ✅ 初始化数据文件（experiences.md、memory.md 等）
5. ✅ 输出验证命令

---

## 🔧 Hook 配置

### 自动配置（默认）

install.sh 已自动添加 Hook，无需手动操作。

配置示例（`openclaw.json`）：
```json
{
  "plugins": {
    "entries": {
      "rocky-know-how": {
        "enabled": true,
        "handler": "~/.openclaw/skills/rocky-know-how/hooks/handler.js",
        "events": [
          "agent:bootstrap",
          "before_compaction",
          "after_compaction",
          "before_reset"
        ],
        "env": {
          "OPENCLAW_STATE_DIR": "~/.openclaw"
        }
      }
    }
  }
}
```

### 关键参数说明

| 参数 | 说明 | v2.9.1 新增 |
|------|------|------------|
| `handler` | Hook 处理器路径（支持 `~` 展开） | ✅ OPENCLAW_STATE_DIR 支持 |
| `events` | 4 个事件列表 | ✅ 固定 |
| `env.OPENCLAW_STATE_DIR` | 动态 workspace 路径 | ✅ **新增** 多 workspace 支持 |

### 重启网关（必须）
```bash
openclaw gateway restart
```

---

## ✅ 验证安装

```bash
# 1. 检查脚本存在
ls -la ~/.openclaw/skills/rocky-know-how/scripts/

# 2. 检查 Hook 配置
grep -A 10 "rocky-know-how" ~/.openclaw/openclaw.json

# 3. 测试搜索（应返回空但无错误）
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --all

# 4. 测试自动写入（写入测试经验）
bash ~/.openclaw/skills/rocky-know-how/scripts/record.sh \
  "安装测试" \
  "执行 record.sh 写入测试数据" \
  "直接调用 record.sh 即可" \
  "完成后用 clean.sh 清理" \
  "test,install" \
  "global"

# 5. 验证写入成功（应看到测试条目）
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --tag test

# 6. 查看统计
bash ~/.openclaw/skills/rocky-know-how/scripts/stats.sh

# 7. 检查数据文件
ls -la ~/.openclaw/.learnings/
cat ~/.openclaw/.learnings/memory.md | tail -5
```

**预期输出**:
- search.sh 无错误（或显示测试条目）
- record.sh 输出 "✅ 记录成功"
- memory.md 末尾出现新条目摘要
- stats.sh 显示 experiences.md 条目数+1

**清理测试数据**:
```bash
# 删除测试条目（ID 包含 test 或 auto 标签）
bash ~/.openclaw/skills/rocky-know-how/scripts/clean.sh --tag test --dry-run
bash ~/.openclaw/skills/rocky-know-how/scripts/clean.sh --tag test
```

**自动写入验证**:
```bash
# 查看 experiences.md 最新条目（应看到刚才写入的）
tail -30 ~/.openclaw/.learnings/experiences.md

# 检查 memory.md 是否同步更新
grep -A 2 "最近（最近7天）" ~/.openclaw/.learnings/memory.md

# 检查锁机制是否工作
# （并发测试：同时开两个终端执行 record.sh）
```

---

## 🌐 多 workspace 支持 (v2.9.1+)

如果使用多个 workspace（如 `xiaoying/`、`xiaoduo/`），Handler 会自动检测 `OPENCLAW_STATE_DIR` 环境变量，监听对应 workspace 的 `.learnings/` 目录。

**无需额外配置，开箱即用。**

---

## 📦 数据存储结构

```
~/.openclaw/.learnings/
├── experiences.md          ← 主数据库（v1 兼容）
├── memory.md              ← HOT 层（≤100 行，始终加载）
├── index.md               ← 索引文件
├── corrections.md         ← 纠正日志
├── heartbeat-state.md     ← 心跳状态
├── domains/               ← WARM 层（领域隔离）
│   ├── infra.md
│   ├── wx.newstt.md
│   └── ...
├── projects/              ← WARM 层（项目隔离）
│   ├── project-a.md
│   └── ...
└── archive/               ← COLD 层（90天+ 自动归档）
    └── 2026-01/
```

---

## 🔒 安全特性 (v2.9.1)

| 特性 | 说明 | 影响版本 |
|------|------|----------|
| 并发写入锁 | `.write_lock` 目录锁，防数据交错 | 2.8.2+ |
| 输入严格验证 | ID 格式、路径、长度全检查 | 2.8.2+ |
| 正则元字符转义 | FILTER_DOMAIN/PROJECT 防注入 | 2.8.3 (H1) |
| 路径穿越检测 | `../` 和 `\\` 全面拦截 | 2.8.3 (H2+M1) |
| 标签格式统一 | `**Tags:**` 标准化 | 2.8.2+ |

---

## 🛠️ 常用操作

### 写入经验
```bash
bash ~/.openclaw/skills/rocky-know-how/scripts/record.sh \
  "Nginx 502 错误" \
  "排查过程：检查 upstream、php-fpm" \
  "方案：重启 php-fpm 并调整 pm.max_children" \
  "预防：监控 php-fpm 内存，设置合理 pm" \
  "nginx,php-fpm" \
  "infra"
```

### 搜索经验
```bash
# 多关键词
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh "502" "Nginx"

# 按标签
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --tag "nginx"

# 按领域
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --area infra

# 全部列出
bash ~/.openclaw/skills/rocky-know-how/scripts/search.sh --all
```

### 压缩与归档
```bash
# 手动压缩（HOT 层≤100 行）
bash ~/.openclaw/skills/rocky-know-how/scripts/compact.sh

# 自动归档（cron）
bash ~/.openclaw/skills/rocky-know-how/scripts/archive.sh --auto
```

---

## 📖 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| **3.3.0** | 2026-04-25 | 🔒 安全修复 - 路径穿越/选项注入/并发锁/输入校验
| **2.8.3** | 2026-04-24 | 🔒 安全加固 (H1/H2) + M1 路径检测；Bug #4 修复 (memory.md 压缩)；脚本全面优化 |
| 2.8.2 | 2026-04-24 | 🔐 并发锁、Hook 路径动态化、标签对齐、阈值调整、数据清理 |
| 2.8.1 | 2026-04-23 | 正则转义防注入、输入验证、Hook 自动配置 |
| 2.7.1 | 2026-04-21 | 支持 OpenClaw 2026.4.21 新 Hook 事件 |
| 2.5.1 | 2026-04-15 | 退回简单版，移除 hook 注入 |

---

## 🗑️ 卸载

```bash
bash ~/.openclaw/skills/rocky-know-how/scripts/uninstall.sh
```

卸载会：
- ✅ 删除技能目录
- ✅ 移除 openclaw.json 中的 Hook 配置
- ⚠️ **保留数据文件**（`~/.openclaw/.learnings/`，需手动删除）

---

## 📚 相关文档

- [README.md](./README.md) - 功能总览
- [README_EN.md](./README_EN.md) - English version
- [operations.md](./operations.md) - 操作手册
- [boundaries.md](./boundaries.md) - 边界条件
- [learning.md](./learning.md) - 学习机制
- [CHANGELOG.md](./CHANGELOG.md) - 版本日志

---

**最新更新**: 2026-04-25 15:29  
**版本**: 3.4.8  
**状态**: ✅ 生产就绪
