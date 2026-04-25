---
name: auto-coding
description: 自主编程系统 - 需求拆解、分析需求、找方法、自我反思、迭代优化，达到交付标准
metadata: {"nanobot":{"emoji":"🤖","requires":{"bins":["python","pip"]},"install":[{"id":"dashscope","kind":"pip","package":"dashscope","label":"Install DashScope LLM SDK"},{"id":"ddgs","kind":"pip","package":"duckduckgo-search","label":"Install DuckDuckGo Search (optional)"}]}}
---

# Auto-Coding Skill 🤖

> **版本**: 2.1.1 (深度分析 + 交付检查)

**自主编程系统** - 不是简单的代码生成，而是具备**需求拆解**、**深度分析**和**自我反思**能力的智能编程系统。

---

## 🆕 v2.1.0 新增：交付标准检查 ✅

在代码交付前进行 8 项严格检查：
- ✅ 语法检查、安全检查、文档完整性
- ✅ 错误处理、基本测试、功能完整性
- ✅ TODO 检查、代码风格

## 🆕 v2.0.0 新增：深度分析模块 🔍

引入**深度分析模块** (`deep_analysis.py`)：
- ✅ 根因分析 (Root Cause Analysis)
- ✅ 模式识别 (Pattern Recognition)
- ✅ 多维度验证 (Multi-dimensional Verification)

## 🆕 v1.3.0 新增：需求拆解器 🎯

智能判断任务复杂度，动态调整执行流程：

| 任务类型 | 复杂度 | 耗时 |
|----------|--------|------|
| 简单任务 | 1-3/10 | ~15 秒 |
| 中等任务 | 4-6/10 | ~60 秒 |
| 复杂任务 | 7-10/10 | ~180 秒 |

---

## 核心能力

1. **需求拆解** - 分析任务复杂度，生成执行计划
2. **分析需求** - 识别领域、技能要求、潜在挑战
3. **找方法** - 搜索文档、工具、最佳实践
4. **实现代码** - 生成可运行的代码
5. **测试验证** - 运行测试确保代码工作
6. **深度分析** - 根因分析、模式识别 (v2.0+)
7. **自我反思** - 识别问题并改进（关键！）
8. **交付检查** - 8 项标准严格把关 (v2.1+)

---

## 使用方式

### 通过 nanobot 命令

```bash
/auto-coding 创建一个批量重命名文件的脚本
```

### 通过 Python API

```python
from worker import AutoCodingWorker, WorkMode

worker = AutoCodingWorker(mode=WorkMode.STANDARD)
result = await worker.run("创建一个批量重命名文件的脚本")

print(f"成功：{result.success}")
print(f"代码：{result.final_code}")
print(f"迭代：{result.iterations}")
```

---

## 工作模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `quick` | 快速模式，跳过测试和反思 | 简单脚本、单文件任务 |
| `standard` | 标准模式，完整流程 | 大多数任务 |
| `deep` | 深度模式，多次反思迭代 | 复杂功能、需要优化的代码 |

---

### 常见场景

**创建脚本**:
```
/auto-coding 创建一个 Python 脚本来处理 CSV 文件
/auto-coding 帮我写一个批量下载图片的脚本
```

**开发应用**:
```
/auto-coding 开发一个 Flask API 服务
/auto-coding 创建一个 React 组件
```

**功能实现**:
```
这个功能怎么实现？我需要给项目添加日志功能
我需要写一个函数来验证邮箱格式
```

---

## 文件结构

```
auto-coding/
├── SKILL.md              # 技能定义（本文件）
├── README.md             # 详细文档
├── USAGE.md              # 使用指南
├── DECOMPOSER_DESIGN.md  # 需求拆解器设计文档
├── decomposer.py         # 需求拆解器 (v1.3.0 新增)
├── worker.py             # 核心工作流引擎
├── self_reflect.py       # 自我反思模块
├── delivery_check.py     # 交付标准检查
├── llm_client.py         # LLM 调用客户端（复用 nanobot 配置）
├── prompts/              # 提示词模板
└── tests/                # 测试套件
```

---

## 依赖

- Python 3.10+
- dashscope (阿里云通义千问)
- duckduckgo-search (可选，用于搜索)

---

## 配置

### LLM 配置

复用 nanobot 的 LLM 配置（从 `~/.nanobot/config.json` 读取）

### 工作空间

默认：`~/.nanobot/workspace`

可以通过参数指定：
```python
worker = AutoCodingWorker(workspace="/path/to/workspace")
```

---

## 交付标准

代码必须通过以下检查才能交付：

- [ ] 运行无错误
- [ ] 有基本测试
- [ ] 有文档说明
- [ ] 有错误处理
- [ ] 通过安全检查

---

## 版本历史

- **v1.3.0** - 新增需求拆解器，智能判断复杂度
- **v1.2.0** - 新增自我反思模块
- **v1.1.0** - 新增交付检查
- **v1.0.0** - 初始版本

---

## 相关文档

- [README.md](README.md) - 详细文档
- [USAGE.md](USAGE.md) - 使用指南
- [DECOMPOSER_DESIGN.md](DECOMPOSER_DESIGN.md) - 需求拆解器设计
