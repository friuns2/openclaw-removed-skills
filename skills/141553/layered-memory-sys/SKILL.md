# layered-memory-sys

分层记忆系统 — 6层架构的智能记忆管理。

## 6层记忆架构

- **核心层** (永久) → MEMORY.md
- **沉淀层** (90天) → 重要决策/项目经验
- **关注层** (30天) → 反复讨论的话题
- **活跃层** (7天) → 正在进行的任务
- **闪存层** (3天) → 临时查询/一次性问答
- **Session** (实时) → 当前对话上下文

## 功能

- 📊 **分层 TTL 管理** — 自动升级/归档/遗忘
- 💤 **梦境模式** — 巩固、归档、遗忘、合并
- 🔍 **TF-IDF 搜索** — 中文关键词搜索
- 📈 **统计面板** — HTML 可视化健康报告
- ⚙️ **路径配置化** — 支持环境变量和配置文件
- 🤖 **自动写入检测** — 从对话中识别值得记住的内容

## 快速开始

### 测试
```bash
cd skills/layered-memory-sys
node scripts/test-v2.mjs
```

### 梦境模式
```bash
node scripts/dream-cycle.mjs
```

### 统计面板
```bash
node scripts/stats-panel.mjs
```

## 使用方式

该技能通过记忆索引 (`memory/index.json`) 管理记忆数据。

### 记忆层级

| 层级 | TTL | 说明 |
|------|-----|------|
| flash | 3天 | 临时查询、一次性问答 |
| active | 7天 | 正在进行的任务 |
| attention | 30天 | 反复讨论的话题 |
| settled | 90天 | 重要经验、决策记录 |

### 升级规则
- 同一话题被召回 ≥3 次 → flash → active
- 多天连续被召回 → active → attention
- 召回 ≥10 次 → attention → settled
- 用户说"记住这个" → 直接进沉淀层

## 配置

支持环境变量 + 配置文件 (`memory/config.json`) + 默认值三级覆盖：

| 环境变量 | 说明 |
|---------|------|
| MEMORY_DIR | 记忆数据目录 |
| SESSION_DIR | Session 日志目录 |

## 依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| sql.js | SQLite WASM 存储 | ✅ |
| nodejieba | 中文分词 | 推荐 |
| ws | WebSocket | 可选 |

## 版本历史

- **v1.1.2** — bug fix: 合并跳过提醒记忆 / 过滤系统消息
- **v1.1** — 向量搜索/路径配置化/统计面板/自动写入检测
- **v1.0** — 6层架构 + 梦境模式
