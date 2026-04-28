---
name: huo15-openclaw-openai-knowledge-base
displayName: 火一五知识库技能
description: 基于 Karpathy LLM Knowledge Bases 方案。raw → LLM编译 → wiki，LLM 当 librarian 维护双链/索引/日志/合成式问答，支持 Obsidian 同步、知识图谱、微信公众号/GitHub 多源入库，以及 agent/shared 双作用域。触发词：知识库、入库、查询、编译、提问、知识图谱。
version: "2.7.0"
aliases:
  - 火一五知识库
  - 火一五知识库技能
  - 卡帕西知识库
  - 火一五卡帕西知识库技能
dependencies:
  obsidian-cli:
    description: 可选，用于 Obsidian vault 搜索
    install: brew install yakitrak/yakitrak/obsidian-cli
safety:
  virus_total_note: 无硬编码凭证，凭据从 OpenClaw models.json 运行时加载
---

# SKILL.md — huo15-knowledge-base

> 基于 Karpathy LLM Knowledge Bases 方案：raw → LLM编译 → wiki
> 双作用域：
> - **agent**（默认）：`~/.openclaw/agents/{agent-id}/agent/kb/` — 每个 Agent 独立，互不可见
> - **shared**：`~/.openclaw/kb/shared/` — 跨 Agent 共享；通过 @huo15/openclaw-enhance 并入龙虾原生 `memory_search`（corpus=\"kb\"）

---

## 核心脚本（Karpathy LLM Librarian 模式）

| 脚本 | 做什么 | 成功标准 |
|------|--------|----------|
| `kb-ingest` | 文档入库（URL/文件/文本/微信公众号/GitHub）；自动写日志 | raw/ 下文件存在 + log.md 追加一条 |
| `kb-compile` | LLM 编译 raw → wiki；外置 prompt + 注入 SCHEMA + 现有 wiki 列表；编译后自动重建 index.md + log | wiki/ 下 .md 生成 + index.md 更新 |
| `kb-ask` | **合成式问答**：候选页 → LLM → 带 [[]] 引用的答案；可 `--save` 把答案归档为新条目（"explorations compound"） | 终端输出答案 + log 一条 |
| `kb-search` | 关键词搜索（默认聚合 agent+shared+obsidian） | 搜索结果返回 |
| `kb-index` | 扫 wiki/，按 concepts 分组生成 `wiki/index.md`（每次 compile 自动跑） | index.md 重写 |
| `kb-log` | 追加日志到 `wiki/log.md`（事件: ingest/compile/ask/lint） | log.md 末尾多一行 |
| `kb-lint` | 体检：frontmatter / 断链 / **stub** / **orphan** / **stale** / 缺出处 | 报告问题数 + log 一条 |
| `kb-graph` | 知识图谱可视化（Mermaid） | kb/wiki/graph.mermaid 生成 |

**Wiki 内特殊文件**（由脚本维护，不要手改）：
- `wiki/SCHEMA.md` — 给 LLM 看的图书馆员守则（首次激活时种入）
- `wiki/index.md` — 自动生成的内容目录
- `wiki/log.md` — 追加式变更日志

所有写入类脚本均支持 `--scope agent|shared`（或 `--shared` 快捷），默认 `agent`。`obsidian-sync` 额外支持 `--all-scopes` 一次同步两层。

---

## 快速开始

```bash
# Agent 私有（默认）
kb-ingest --url "https://..."                        # 入库到当前 Agent
kb-compile                                             # 编译（自动调 LLM + 自动重建 index）
kb-ask "什么是 Karpathy Wiki Pattern"                 # 合成式问答（带 [[]] 引用）
kb-ask "如何判断条目该归档为 shared" --save           # 把答案归档为新 wiki 条目
kb-search "关键词"                                      # 关键词搜索：agent + shared + Obsidian

# 跨 Agent 共享（长期、稳定的知识资料）
kb-ingest --scope shared --url "https://..."          # 入库到共享库
kb-compile --scope shared                              # 编译共享库
kb-ask --shared "..."                                  # 共享库问答

# 体检 / 索引 / 日志
kb-lint                                                # 体检：断链/stub/orphan/stale/缺出处
kb-index                                               # 重建 index.md（compile 时自动跑，单独跑可手动重建）
kb-log --tail 20                                       # 看最近 20 条变更日志

# 特殊源
kb-ingest --source wechat --url "https://mp.weixin.qq.com/s/..."  # 微信公众号
kb-ingest --source github --url "https://github.com/user/repo"     # GitHub README
kb-graph                                               # 生成知识图谱（Mermaid）
```

---

## 架构

```
agent scope（隔离）：~/.openclaw/agents/{id}/agent/kb/
shared scope（共享）：~/.openclaw/kb/shared/
  ├─ raw/     原始文档（按日期分目录，status: pending/ready）
  ├─ wiki/    LLM 编译后的百科（Markdown，双向链接）
  │          graph.mermaid（知识图谱）
  └─ cache/   临时文件

可选: wiki/ → Obsidian vault（知识库/ 文件夹）
```

---

## 与 @huo15/openclaw-enhance 的协作

| 层 | 存什么 | 入口 |
|----|--------|------|
| L1 龙虾原生 memory | 向量+FTS 底座 | `memory_search` / `memory_get` |
| L2 enhance 结构化记忆 | 短条目「规则/为什么/怎么做」（per-agent） | `enhance_memory_*` 工具 |
| L3 本技能 shared KB | 长文档「事实/资料」（跨 agent） | `kb-*` 脚本；通过 corpus=\"kb\" 被 memory_search 搜到 |

**边界原则**：短规则 → L2；长资料 → L3 shared；agent 私有实验性知识 → L3 agent。

---

## Obsidian 集成

`config.json` 配置：
```json
{
  "obsidian": {
    "enabled": true,
    "vault_path": "/Users/xxx/Documents/我的笔记"
  }
}
```

`kb-search` 自动搜索 wiki/ + Obsidian vault（如果启用）。

同步命令：
```bash
obsidian-sync.sh                     # 默认同步 agent scope → vault/知识库/agent/
obsidian-sync.sh --shared            # 同步 shared scope → vault/知识库/shared/
obsidian-sync.sh --all-scopes        # 两层一起同步（分别入独立子目录）
obsidian-sync.sh --dry-run --all-scopes  # 预览
obsidian-sync.sh --watch --all-scopes    # 监听两层的变化
```

Vault 布局：
```
vault/知识库/
├── agent/    ← 本 Agent 私有 wiki
└── shared/   ← 跨 Agent 共享 wiki
```

---

## 触发词

- "知识库"、"入库知识库"、"查询知识库"
- "编译知识库"、"激活知识库"
- "提问知识库"、"问答知识库"、"kb-ask"
- "知识库体检"、"kb-lint"、"断链"、"孤儿条目"、"stub"
- "Obsidian 同步"
- "知识图谱"、"图谱可视化"、"kb-graph"
- "共享知识库"、"跨 Agent 知识库"、"shared kb"

---

## Karpathy Librarian 模式（v2.6.0）

设计参照 [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。LLM 不只是"翻译器"，而是**全职图书馆员**：

- **三层架构**：`raw/`（只读素材） · `wiki/`（LLM 维护的百科） · `wiki/SCHEMA.md`（守则）
- **原子条目**：一个 wiki 页 = 一个概念，不是"一篇文章一页"
- **强双链**：第一次提到其他条目必须 `[[]]`，断链由 lint 报告
- **三件套**：`index.md`（目录）+ `log.md`（变更日志）+ `SCHEMA.md`（守则）由系统/LLM 共同维护
- **合成式问答**：`kb-ask` 不只是 grep，是 LLM 综合多页给带引用的答案
- **explorations compound**：`kb-ask --save` 把答案归档回 wiki，下次问同类问题更快

## Schema 升级包（v2.7.0）— 对齐 LLM Wiki v2 / OmegaWiki

借鉴 [rohitg00 LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) + OmegaWiki 的 typed graph 设计。**纯约定升级，向后兼容**——老 wiki 不必改也能用。

- **Typed Relations**：frontmatter `relations:` 字段把 `[[]]` 升级成有类型的图边
  - 枚举：`uses` / `depends-on` / `extends` / `part-of` / `contradicts` / `supersedes` / `superseded-by` / `related`
  - 正文 `[[]]` 保持 Wikipedia 风格，关系类型只在 frontmatter
- **Confidence + Supersession**：每条 wiki 现在带可信度（0.0-1.0）
  - 高信度（≥0.9）才能 `status: stable`
  - 低信度（<0.5）必须 `<!-- TODO -->` 注释
  - 新事实推翻旧事实 → `supersedes` / `superseded-by` 双向标注，**不删旧条目**（保留证据链）
- **kb-graph typed edges**：Mermaid 图按关系类型用不同箭头（`-->`/`==>`/`-.->`）
- **kb-lint 新增检查**：未知关系类型、supersession 不对称、contradicts 单向、低信度无 TODO、高信度非 stable
- **kb-index 信号**：✅ 高信度 / 🟡 低信度 / ⚡ 已被取代 / 🚧 stub
- **kb-ask 优先级**：先采信高 confidence，看到 superseded-by 自动跳新页
