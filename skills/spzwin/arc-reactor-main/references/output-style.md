# Output Style Guide — Display Layer vs Archive Layer

## 概述

ARC Reactor 输出分两层：**Display Layer**（展示层）和 **Archive Layer**（归档层）。Display Layer 是用户直接看到的回复；Archive Layer 是存储到知识库的结构化内容。

---

## 🖥️ Display Layer（展示层）

**用途**：直接回复用户，是唯一的"对外"输出层。

### 规范

| 属性 | 要求 |
|------|------|
| **字数** | ≤200 字 |
| **风格** | 模拟人类对话，像在聊天 |
| **结构** | 结论先行，用「·」列出要点 |
| **语气** | 自然、口语化，避免机械感 |

### 格式示例

```
这个项目讲的是 [一句话概括]。

核心结论：
· 要点1
· 要点2
· 要点3

想了解更多可以追问。
```

### 触发规则

- 用户说"详细"、"展开"、"展开说说" → 提供 Archive 层内容
- 用户说"搜一下"、"帮我看"、"这个讲了什么" → 自动触发 Ingest + Display

---

## 📦 Archive Layer（归档层）

**用途**：存入知识库，供长期查阅和检索。是内部存储格式。

### 规范

| 属性 | 要求 |
|------|------|
| **格式** | Markdown + YAML frontmatter |
| **结构** | `title`, `date`, `sources`, `tags` |
| **内容** | 完整的事实提炼，包含 `[[wiki-link]]` |
| **命名** | 使用 `--type source/entity/concept` 通过 archive-manager.py 归档 |

### 格式示例

```yaml
---
title: Hermes Agent 架构
date: 2026-04-09
sources: ["raw/hermes-paper.pdf"]
tags: [agent, llm, architecture]
---
# 正文内容

提到了 [[OpenClaw]] 框架...
```

---

## 📱 Channel 自适应规则

目标平台：Discord / Telegram（手机端）

### 规则列表

1. **不用 Markdown 表格** — 用「·」列表或「1. 2. 3.」代替
2. **不用超过3行的代码块** — 超过则折叠或改用描述
3. **分段要短** — 每段≤3行，关键信息放最前面
4. **列表用「·」或「1. 2. 3.」** — 不用「-」或「*」

### 自适应对照表

| 场景 | 标准格式 | Channel 自适应 |
|------|----------|----------------|
| 多项并列 | Markdown 表格 | 「·」列表 |
| 代码展示 | 多行代码块 | 单行 or 折叠描述 |
| 详细信息 | 段落展开 | 关键句 + "追问获取更多" |

---

## ✍️ 字数限制说明

| 层级 | 上限 | 说明 |
|------|------|------|
| Display Layer（展示层） | 200 字 | 用户直接看到的回复 |
| Archive Layer（归档层） | 无限制 | 知识库存档，完整为上 |
| 每段落（Channel 自适应） | 3 行 | Discord/Telegram 阅读友好 |
| 代码块（Channel 自适应） | 3 行 | 超过则折叠 |

---

## 🔄 分层协作流程

```
用户输入
   ↓
[自然触发词判断]
   ↓
Ingest + Query（底层4连击）
   ↓
Synthesize → Display Layer → 用户可见回复
           ↘ Archive Layer → 知识库存档
```

### Display Layer 优先

每次响应用户时，**必须**先输出 Display Layer。如果用户追问，再提供更深层的 Archive 内容。

### Archive Layer 按需触发

以下情况将内容存入 Archive Layer：
- Ingest 时生成 source/entity/concept
- Query 的答案具有长期留存价值
- Lint 时发现并修复了孤岛链接
