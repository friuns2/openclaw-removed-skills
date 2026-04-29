---
name: learn-and-record
description: 学习新工具、新技术、新平台的完整流程。当你需要从零学习某个东西时使用此 skill。包含学习方法论、踩坑记录、探索清单和笔记模板。也用于回顾已有学习经验来指导新的学习。
---

# 学习与记录 Skill

## 核心理念

> 学习不固化 = 白学。每次学完一个东西，必须产出可复用的资产。

## 学习流程

### Phase 0: 准备（开始前）

1. **明确目标** — 学什么？学到什么程度？能用来干什么？
2. **收集入口** — 官方文档、GitHub repo、教程、示例项目
3. **建立笔记文件** — 在 `memory/learning-logs/<主题>-<日期>.md` 创建学习日志
4. **列出探索清单** — 预估要搞清楚的关键问题

### Phase 1: 环境搭建

记录以下内容：
- 安装命令（完整、可复现）
- 依赖冲突和解决方案
- 版本信息（`--version`）
- 环境变量配置
- **踩坑**：任何报错、意外行为、文档没说的注意事项

### Phase 2: 最小可用验证

- 写一个最简单的 hello world / demo
- 确认基本通路跑通
- 记录最小可用代码
- **踩坑**：初始化、权限、网络、路径等常见问题

### Phase 3: 系统探索

按以下维度逐一探索，每个都记录：

- **核心概念** — 这个工具的世界观是什么？关键术语？
- **API/命令** — 主要接口有哪些？参数含义？
- **配置项** — 可调的参数、默认值、最佳实践
- **边界情况** — 极端输入、错误处理、性能限制
- **集成方式** — 怎么和其他工具配合？
- **高级特性** — 不是必需但很强大的功能
- **常见坑** — 文档没提但你踩到了的
- **社区智慧** — GitHub issues、讨论区的高频问题

### Phase 4: 实战验证

- 用学到的知识做一个小项目
- 记录从构思到完成的全过程
- 遇到的问题和解决方案
- 和文档描述不一致的地方

### Phase 5: 固化输出（最重要！）

> 学习不固化 = 白学。每完成一个主题，必须产出可复用的资产。

#### 固化产物选择

| 产物 | 用途 | 示例 |
|------|------|------|
| **Skill** | 知识指南，让 AI 知道怎么做 | 火山方舟 API 用法、OpenClaw 配置 |
| **脚本** | 可执行的功能代码，直接跑 | 批量处理工具、数据转换 |
| **MCP Server** | 标准化工具接口，任何 AI 客户端可调用 | 天气查询、API 代理 |

**判断规则：**
- 只需要 AI "知道怎么用" → **Skill**（知识文档）
- 需要反复执行的具体操作 → **脚本**（scripts/ 目录）
- 需要 AI 主动调用的工具能力 → **MCP Server**（长期服务）
- 三者可组合：Skill 引导流程，Skill 内嵌脚本，MCP 提供工具接口

#### 5a: 创建 Skill（知识固化）

**当满足以下任一条件时，必须创建 Skill：**
- 学到了可重复使用的工作流或代码模式
- 涉及 API 调用、配置模板、最佳实践
- 未来可能再次用到这些知识

**⚠️ 必须严格按照 skill-creator 规范创建：**

**Step 1: 初始化（必须用脚本）**
```bash
python3 ~/.npm-global/lib/node_modules/openclaw/skills/skill-creator/scripts/init_skill.py \
  <skill-name> --path <输出目录> --resources references
```

**Step 2: 编辑 SKILL.md**
- 填写 YAML frontmatter：`name` + `description`（description 是触发机制，必须写清使用场景）
- 删除模板中的 TODO 和 Structuring 段落
- SKILL.md 保持 < 500 行，核心用法
- 详细内容放 `references/` 目录

**Step 3: 添加 references/**
- 从学习笔记中提取详细内容
- 按 `references/models.md`、`references/examples.md`、`references/best-practices.md` 等组织
- 大文件（>100行）顶部加目录索引

**Step 4: 如有可复用脚本，添加到 scripts/**
- 必须 `chmod +x`，支持 `--help`
- 参数通过命令行传入，禁止硬编码
- 输出结构化文本（JSON/表格）

**Step 5: 打包（必须用脚本）**
```bash
python3 ~/.npm-global/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py \
  <skill-folder路径> [输出目录]
```

**Step 6: 更新 TOOLS.md Skills 列表**

**Step 7: 删除或归档原始学习笔记**（知识已沉淀到 Skill 中）

#### 5b: 创建脚本（功能固化）

**脚本规范：**
- 放在 `skills/<主题>/scripts/` 或 `~/.openclaw/scripts/`
- 必须 `chmod +x`，支持 `--help`
- 关键参数通过命令行参数传入，禁止硬编码
- 输出结构化文本（JSON/表格），方便 AI 解析
- 包含错误处理和退出码

**脚本模板（Python）：**
```python
#!/usr/bin/env python3
"""<一句话描述>

用法: python3 script.py <参数>
"""
import argparse, sys, json

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', help='输入')
    p.add_argument('-o', '--output', help='输出')
    args = p.parse_args()
    # ... 逻辑 ...
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
```

#### 5c: 创建 MCP Server（工具服务固化）

**MCP Server 规范：**
- 放在 `~/.openclaw/mcp-servers/` 或独立 Git 仓库
- 使用 `@modelcontextprotocol/sdk` 或 `mcp` Python 包
- 每个工具必须有清晰的 name、description、inputSchema

**MCP Server 模板（Python）：**
```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('<名称>')

@mcp.tool()
def do_something(param: str) -> str:
    """<工具描述>"""
    # ... 逻辑 ...
    return result

if __name__ == '__main__':
    mcp.run(transport='stdio')
```

**注册到 OpenClaw（~/.openclaw/openclaw.json）：**
```json
{
  "mcpServers": {
    "<name>": {
      "command": "python3",
      "args": ["/path/to/server.py"],
      "env": { "API_KEY": "${ENV_VAR}" }
    }
  }
}
```

#### 5d: 更新记忆
- 更新 `memory/learning-logs/<主题>-summary.md`
- 更新 MEMORY.md 相关章节
- 更新 TOOLS.md 如果涉及新工具
- 标记探索清单完成度

#### 5e: 清理
- 已固化的学习笔记移到 `memory/learning-logs/archive/`
- 或直接删除（知识已沉淀到 Skill/脚本/MCP 中）

## 学习日志模板

```markdown
# 学习日志: <主题>
- **日期**: YYYY-MM-DD
- **状态**: 进行中 / 已完成
- **目标**: 学什么、为什么学

## Phase 0: 准备
- 学习目标: ...
- 入口资源: ...
- 探索清单: [ ] [ ] [ ]

## Phase 1: 环境搭建
- 安装步骤: ...
- 踩坑记录: ...

## Phase 2: 最小验证
- 验证代码: ...
- 结果: ✅/❌

## Phase 3: 系统探索
### 核心概念
- ...
### 踩坑汇总
1. ...

## Phase 4: 实战
- 项目描述: ...
- 结果: ...

## Phase 5: 固化
- Skill: <名称> ✅/❌
- 脚本: <列表> ✅/❌
- MCP: <名称> ✅/❌
```

## 探索清单模板

学习新东西时，主动回答这些问题：

- [ ] 它解决什么问题？不解决什么？
- [ ] 核心工作流是怎样的？
- [ ] 最常见的用法是什么？
- [ ] 配置项有哪些？默认值合理吗？
- [ ] 错误处理机制是什么？
- [ ] 性能特征？（速度、内存、限制）
- [ ] 和类似工具比，优劣势？
- [ ] 有什么隐藏功能/彩蛋？
- [ ] 社区最常问的问题是什么？
- [ ] 文档哪里写得不好/有误导？
- [ ] 如果要向别人介绍，三句话怎么讲？

## 记录规范

1. **所有踩坑必须记录** — 包括错误信息、原因分析、解决方案
2. **可复现性** — 别人（或未来的我）按记录能复现
3. **区分事实和推测** — 确认过的标 ✅，推测的标 ❓
4. **保留原始命令** — 不要省略，不要"类似地"
5. **记录版本** — 工具版本、OS、环境都可能影响
6. **交叉引用** — 相关的学习日志互相链接

## 存储结构

```
# 学习进行中
memory/learning-logs/
├── <主题>-<YYYY-MM-DD>.md        # 详细学习日志
├── <主题>-summary.md              # 总结提炼
└── _index.md                      # 学习目录索引

# 学习完成后 → 固化为 Skill（必须用 init_skill.py + package_skill.py）
skills/<主题>/
├── SKILL.md                       # 核心指南
├── scripts/                       # 可执行脚本（可选）
└── references/                    # 详细参考
```

## 回顾已有经验

学习新东西前：
1. 检查 `memory/learning-logs/_index.md` — 有没有类似工具的学习经验？
2. 检查 `skills/` 目录 — 是否已有相关 Skill？直接加载，不用从头学
3. 检查 MEMORY.md — 之前踩过的坑、积累的经验

**学习闭环：** 笔记 → Skill → 日常使用 → 发现不足 → 补充 Skill
