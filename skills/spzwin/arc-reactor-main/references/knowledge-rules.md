# 知识编译规则 (Knowledge Compilation Rules)

> 借鉴 Karpathy LLM Wiki 理念：报告是"快照"，知识库是"活体"。

## 三层架构

```
Layer 1: Raw（原始素材层）
  reports/YYYY-MM-DD/raw/
  转录稿、截图、PDF — 只读存储，先全收

Layer 2: Wiki（知识编译层）
  knowledge/
  ├── entities/     实体页（项目/人物/公司）
  ├── concepts/     概念页（术语/方法论）
  ├── comparisons/  对比页（A vs B）
  └── index.md      知识导航目录

Layer 3: Schema（规则层）
  本文件 — 定义编译行为和交叉引用规则
```

## 编译触发

每次 ARC 完成一份报告后，自动执行知识编译：

### 1. 实体提取
- 从报告中识别关键实体（项目名、人物、公司）
- 已存在 `knowledge/entities/[实体].md` → **追加更新**
- 不存在 → **新建实体页**

### 2. 概念关联
- 识别报告中的核心概念
- 更新 `knowledge/concepts/`

### 3. 交叉引用
- 在相关实体页之间建立 `[[双向链接]]`（Obsidian 格式）
- 确保知识网络互相连通

### 4. 索引更新
- 更新 `knowledge/index.md` 目录
- 记录新增/更新的实体和概念

## 实体页模板

```markdown
# [实体名]

## 基本信息
| 字段 | 内容 |
|------|------|
| **类型** | 项目/人物/公司 |
| **首次调研** | YYYY-MM-DD |
| **最后更新** | YYYY-MM-DD |
| **信息来源数** | N |

## 核心描述
[一段话总结]

## 关键数据
[表格化的核心指标]

## 关联实体
- [[相关实体1]]
- [[相关实体2]]

## 来源报告
- [报告1](../reports/YYYY-MM-DD/xxx-调研报告.md)
- [报告2](../reports/YYYY-MM-DD/xxx-调研报告.md)
```

## 矛盾检测 (Self-Challenge)

当新调研内容与已有知识页存在矛盾时：
- 自动生成 `knowledge/conflicts/YYYY-MM-DD-[主题].md`
- 列出旧观点、新矛盾点、建议修正方案
- 数据类矛盾：直接用新值覆盖
- 观点类矛盾：两者并存，标注来源
