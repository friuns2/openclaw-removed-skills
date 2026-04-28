# rocky-know-how v3.4.8

**经验诀窍自动学习系统 — Experience & Knowledge Auto-Learning System**

> 让 AI Agent 从失败中学习，在成功后自动记录，形成完整经验闭环。

[![Version](https://img.shields.io/badge/version-3.4.8-blue)]()
[![Models Tested](https://img.shields.io/badge/models_tested-deepseek_v4%20%7C%20glm_5.1%20%7C%20minimax_m2.7-green)]()
[![Code Lines](https://img.shields.io/badge/code-4632_lines-orange)]()

---

## 📚 简介

rocky-know-how 是一个为 OpenClaw Agent 设计的**全自动经验诀窍学习系统**。通过 4 事件 Hook 集成，实现了从对话中自动提取经验、LLM 智能判断、三层存储管理的完整闭环。

**核心特性：**
- 🔄 **全自动闭环** — 压缩时自动提取 → LLM 判断 → 写入经验，零人工干预
- 🧠 **LLM 双判断** — 先判断是否值得写，再判断新增还是追加
- 📦 **三层存储** — HOT（始终加载）/ WARM（按需）/ COLD（归档）
- 🛡️ **五重安全** — 正则注入防护、路径穿越过滤、并发写锁、去重晋升、降级容错
- 🔌 **全 Provider** — 支持 deepseek / glm / minimax / stepfun（含 OAuth）
- ✅ **三大模型实测** — deepseek-v4、glm-5.1、minimax-m2.7 全部通过正反向测试

---

## 🚀 快速开始

### 安装

```bash
git clone https://gitee.com/rocky_tian/skill.git
cd skill/rocky-know-how
bash scripts/install.sh
```

### 核心命令

```bash
# 搜索经验
bash scripts/search.sh "关键词"

# 写入经验
bash scripts/record.sh "问题" "踩坑过程" "正确方案" "预防措施" "tag1,tag2" "area"

# 查看全部
bash scripts/search.sh --all

# 统计面板
bash scripts/stats.sh
```

---

## 🏗️ 架构

### 四事件驱动

| 事件 | 触发时机 | 功能 |
|------|---------|------|
| `agent:bootstrap` | AI 启动 | 注入经验提醒到 systemPrompt |
| `before_compaction` | 压缩前 | **核心：pending → LLM → experiences.md → auto-review** |
| `after_compaction` | 压缩后 | (兼容旧版，pending 已提前处理) |
| `before_reset` | 重置前 | 兜底保存 pending |

### 三层存储

```
~/.openclaw/.learnings/
├── experiences.md    ← 主数据（v1 兼容，所有经验）
├── memory.md         ← HOT 层（≤100行，始终加载）
├── domains/          ← WARM 层（按领域：infra/code/global...）
├── projects/         ← WARM 层（按项目）
├── archive/          ← COLD 层（90天以上归档）
├── drafts/           ← 自动草稿（LLM 判断后处理）
└── pending/          ← 待处理会话上下文
```

### 全自动闭环流程

```
before_compaction 触发（压缩前）
  ├─ 保存上下文 → pending/*.json
  ├─ processPendingItem() → LLM 提取 problem/solution
  ├─ experiences.md 写入
  ├─ auto-review.sh → 同类检测 + 晋升检查
  └─ 压缩继续执行
```

---

## 🛡️ 安全机制

| 机制 | 实现 |
|------|------|
| 正则注入防护 | `escape_grep()` sed 转义特殊字符 |
| 路径穿越过滤 | `replace(/[^a-zA-Z0-9_-]/g, '')` |
| 并发写锁 | `.write_lock/` 目录原子锁 |
| Tag 去重晋升 | record.sh 去重 + promote.sh ≥3次/7天 |
| 降级容错 | LLM → 关键词匹配 → 写入，三级降级 |

---

## 📊 代码统计

| 模块 | 行数 |
|------|-----:|
| handler.js（核心 Hook） | 1,110 |
| 17 个脚本 | 3,522 |
| **总计** | **4,632** |

---

## ✅ 测试验证

### 已测试模型

| 模型 | Provider | 正向测试 | 逆向测试 | 状态 |
|------|---------|:--------:|:--------:|:----:|
| deepseek-v4 | deepseek (api-key) | ✅ 通过 | ✅ 144/150 | 已验证 |
| glm-5.1 | zai (api-key) | ✅ 通过 | ✅ 146/150 | 已验证 |
| MiniMax-M2.7-highspeed | minimax-portal (OAuth) | ✅ 通过 | ✅ 146/150 | 已验证 |

### 测试覆盖

- ✅ agent:bootstrap → systemPrompt 注入（12→952字符）
- ✅ before_compaction → pending 保存（task/tools/errors 提取）
- ✅ after_compaction → LLM 双判断 → 自动写入经验
- ✅ before_reset → 兜底保存
- ✅ record.sh 写入 + search.sh 搜索
- ✅ auto-review.sh 草稿处理 + 归档
- ✅ compact.sh 压缩检查
- ✅ promote.sh Tag 晋升
- ✅ stats.sh 统计面板
- ✅ 5 种安全机制实地确认

---

## 📈 核心优势

1. **零配置自动学习** — Hook 事件自动捕获经验，无需手动触发
2. **LLM 双重判断** — 先判断是否值得写，再决定新增还是追加
3. **三级降级容错** — LLM → 关键词 → 写入，永不丢失数据
4. **全 Provider 支持** — OpenAI、Anthropic、OAuth（zai/stepfun/minimax）
5. **生产验证** — 45+ 条真实经验，2.6MB 数据，稳定运行
6. **安全第一** — 5 种安全机制（正则注入、路径穿越、写锁等）

---

## 📦 仓库

- **Gitee**: https://gitee.com/rocky_tian/skill
- **GitHub**: https://github.com/rocky-tian/skill
- **ClawHub**: https://clawhub.ai/skills/rocky-know-how

---

_版本: 3.0.0 | 测试日期: 2026-04-24 | 许可: MIT_
