---
name: claw-roundtable-skill
description: >
  多 Agent 深度讨论系统 V2。需求驱动的智能专家匹配系统，模拟真实圆桌会议。
  集成 146 个全领域专家（engineering/design/marketing/sales/product 等），支持任何复杂问题的多专家讨论。
  核心改进：
  1. 需求智能拆解 → 精准匹配专家（从 146 个专家库中选择）
  2. 按议题分治讨论 → 不再固定 5 轮
  3. 排除不相关专家 → 测试不参与设计阶段
  4. 动态适配复杂度 → 简单需求快速处理
  适用于复杂项目前期的头脑风暴或项目后期的优化和合规审查。
compatibility:
  requires:
    - Python 3、asyncio（内置）
    - agency-agents-zh（146 个专家库）
    - requirement_analyzer.py（需求分析器）
    - roundtable_engine_v2.py（V2 引擎）
triggers:
  - RoundTable
  - 圆桌会议
  - 圆桌讨论
  - 多 Agent 讨论
  - 多专家讨论
  - 需求分析
  - 方案评审
---

# RoundTable V2 Skill - 需求驱动的多专家讨论系统

## 技能说明

RoundTable V2 是一个**需求驱动**的多专家 Agent 讨论系统。核心理念：

1. **先拆解需求，再匹配专家** - 不再固定 3-5 个专家
2. **按议题分治讨论** - 不再固定 5 轮
3. **排除不相关专家** - 测试专家不参与设计阶段
4. **动态适配复杂度** - 简单需求快速处理

## 触发词

- RoundTable
- 圆桌会议
- 圆桌讨论
- 多 Agent 讨论
- 多专家讨论
- 需求分析
- 方案评审

## 使用示例

### 基础用法

```
RoundTable 讨论一下：智能待办应用的架构设计
```

### 指定复杂度

```
RoundTable 高复杂度：智能待办应用从 0 到 1 完整设计
RoundTable 中复杂度：用户认证模块设计
RoundTable 低复杂度：PR 代码审查
```

### 指定专家

```
RoundTable 指定专家 [engineering, ux_designer]：任务管理界面设计
```

## 核心改进（V2 vs V1）

| 维度 | V1（旧版） | V2（新版） |
|------|-----------|-----------|
| **需求分析** | ❌ 无，直接讨论 | ✅ 智能拆解需求 |
| **专家匹配** | ❌ 固定 3-5 个 | ✅ 按需动态选择 |
| **讨论流程** | ❌ 固定 5 轮 | ✅ 按议题分治 |
| **专家排除** | ❌ 无 | ✅ 测试不参与设计 |
| **复杂度适配** | ❌ 无 | ✅ 高/中/低自动适配 |

## 需求类型识别

系统自动识别以下需求类型：

| 类型 | 关键词 | 推荐专家 |
|------|--------|---------|
| **产品定位** | 产品、功能、用户、需求、定位 | 产品经理、商业分析师 |
| **技术架构** | 架构、技术栈、后端、前端、数据库 | 工程专家、架构师 |
| **安全合规** | 安全、认证、授权、加密、隐私 | 安全工程师、法务 |
| **用户体验** | 体验、界面、交互、设计、UI | UX 设计师、UI 设计师 |
| **AI/ML** | AI、智能、算法、模型、推荐 | AI 工程师、ML 工程师 |
| **性能优化** | 性能、并发、延迟、优化、缓存 | 性能工程师、DBA |
| **商业模式** | 商业、盈利、收入、市场、竞争 | 商业分析师、营销 |
| **数据设计** | 数据、数据库、表结构、字段 | DBA、数据工程师 |

## 专家库

### 技术类

| 专家 ID | 名称 | 擅长领域 |
|--------|------|---------|
| `engineering` | 工程专家 | 架构、性能、数据 |
| `architect` | 架构师 | 架构、安全 |
| `security_engineer` | 安全专家 | 安全、隐私 |
| `ai_engineer` | AI 工程师 | AI 功能、模型 |
| `ml_engineer` | ML 工程师 | 模型训练、优化 |
| `data_scientist` | 数据科学家 | 数据分析、统计 |
| `performance_engineer` | 性能工程师 | 性能优化、监控 |
| `database_admin` | 数据库专家 | 数据库设计、优化 |
| `devops` | DevOps 专家 | CI/CD、部署 |

### 设计类

| 专家 ID | 名称 | 擅长领域 |
|--------|------|---------|
| `ux_designer` | UX 设计师 | 用户体验、交互 |
| `ui_designer` | UI 设计师 | 视觉设计、品牌 |

### 产品类

| 专家 ID | 名称 | 擅长领域 |
|--------|------|---------|
| `product_manager` | 产品经理 | 产品定位、需求 |
| `business_analyst` | 商业分析师 | 商业模式、市场 |
| `marketing` | 营销专家 | 增长、品牌 |
| `legal` | 法务专家 | 合规、法律 |

### 测试类（特殊）

| 专家 ID | 名称 | 擅长领域 | 排除阶段 |
|--------|------|---------|---------|
| `qa_engineer` | 测试专家 | 性能测试 | 架构、产品阶段 |

## 讨论流程

### V2 流程

```
Step 1: 需求智能拆解
└─ 分析用户输入，识别需求类型

Step 2: 专家精准匹配
└─ 根据需求类型，匹配最相关的专家

Step 3: 用户确认配置
└─ 展示推荐的专家阵容和议题

Step 4: 按议题分治讨论
├─ 议题 1: 技术架构（工程专家主导）
├─ 议题 2: AI 功能（AI 工程师主导）
└─ 议题 3: 用户体验（UX 设计师主导）

Step 5: 整合方案
└─ 将各议题结论整合成完整方案
```

### 复杂度适配

| 复杂度 | 专家数 | 议题数 | 预计耗时 | 适用场景 |
|--------|--------|--------|---------|---------|
| **低** | 2 | 2 | 2-5 分钟 | 简单功能、代码审查 |
| **中** | 3 | 3 | 5-10 分钟 | 模块设计、功能规划 |
| **高** | 5 | 5 | 15-30 分钟 | 核心产品、技术选型 |

## 实际案例

### 案例 1：智能待办应用架构设计

```
输入：RoundTable 讨论一下：智能待办应用的架构设计

Step 1: 需求分析
检测到的需求类型：architecture, ai_ml, ux_design
推荐专家：engineering, ai_engineer, ux_designer
排除专家：qa_engineer（不参与架构阶段）

Step 2: 用户确认
📋 RoundTable V2 配置

讨论主题：智能待办应用的架构设计

推荐专家阵容：
- 工程专家（技术架构）
- AI 工程师（智能功能）
- UX 设计师（用户体验）

关键议题：
- 技术架构 (high)
- AI 功能 (high)
- 用户体验 (medium)

预计耗时：15 分钟
预计 Token：约 40,000

Step 3: 分议题讨论

议题 1: 技术架构（工程专家主导）
→ 结论：React + Node.js + PostgreSQL

议题 2: AI 功能（AI 工程师主导）
→ 结论：本地模型优先 + 云端备份

议题 3: 用户体验（UX 设计师主导）
→ 结论：自然语言输入 + 智能提醒

Step 4: 整合方案
→ 完整的技术架构文档
```

### 案例 2：简单功能评审

```
输入：RoundTable 低复杂度：任务标签功能设计

Step 1: 需求分析
检测到的需求类型：architecture
推荐专家：engineering
复杂度：低 → 最多 2 个专家，2 个议题

Step 2: 快速讨论
议题 1: 数据模型设计
议题 2: API 设计

Step 3: 整合方案
→ 简洁的设计文档

总耗时：3 分钟
Token 消耗：约 10,000
```

## API 参考

### 快捷函数

```python
# 分析需求
from roundtable_engine_v2 import analyze_requirement

result = analyze_requirement("智能待办应用的架构设计")
print(result)
# {
#     "topic": "智能待办应用的架构设计",
#     "detected_types": ["architecture", "ai_ml"],
#     "recommended_experts": ["engineering", "ai_engineer"],
#     "excluded_experts": ["qa_engineer"],
#     "key_topics": [...]
# }

# 选择专家
from requirement_analyzer import select_experts_for_topic

experts = select_experts_for_topic("智能待办应用的架构设计")
print(experts)  # ["engineering", "ai_engineer", "ux_designer"]
```

### 运行 RoundTable

```python
from roundtable_engine_v2 import run_roundtable_v2

# 自动复杂度
await run_roundtable_v2(
    topic="智能待办应用的架构设计",
    mode="pre-ac",
    complexity="auto",  # auto/high/medium/low
    user_channel="user_channel_id"
)

# 指定专家
await run_roundtable_v2(
    topic="任务标签功能设计",
    custom_experts=["engineering", "database_admin"],
    complexity="low"
)
```

## 配置选项

### 复杂度配置

```python
complexity="auto"     # 自动根据需求类型数量判断
complexity="high"     # 高复杂度（5 专家 +5 议题）
complexity="medium"   # 中复杂度（3 专家 +3 议题）
complexity="low"      # 低复杂度（2 专家 +2 议题）
```

### 模式配置

```python
mode="pre-ac"   # AC 前讨论（方案设计）
mode="post-ac"  # AC 后审查（代码审查、安全审计）
```

### 自定义专家

```python
custom_experts=["engineering", "ux_designer"]  # 指定专家列表
```

## 最佳实践

### ✅ 推荐做法

1. **明确需求类型** - 在主题中包含关键词（架构/AI/体验等）
2. **合理选择复杂度** - 简单需求用 low，核心产品用 high
3. **排除不相关专家** - 设计阶段排除测试专家
4. **聚焦关键议题** - 不要试图一次讨论所有问题

### ❌ 避免做法

1. **过度使用** - 简单问题用 RoundTable（杀鸡用牛刀）
2. **专家过多** - 超过 5 个专家会导致协调困难
3. **议题过散** - 一次讨论超过 5 个议题
4. **强行共识** - 不是所有议题都需要共识

## 成本对比

| 场景 | V1 成本 | V2 成本 | 节省 |
|------|--------|--------|------|
| **高复杂度** | 100% | 100% | 0% |
| **中复杂度** | 100% | 50% | 50% |
| **低复杂度** | 100% | 25% | 75% |

**整体节省**：约 50%（假设高 20% + 中 50% + 低 30%）

## 作者

虾软 Claw soft

## 版本历史

- **V2.0.0** (2026-03-21) - 需求驱动的专家匹配系统
  - 新增需求分析器
  - 按议题分治讨论
  - 排除不相关专家
  - 动态适配复杂度

- **V1.0.0** (2026-03-14) - 初始版本
  - 固定 5 轮讨论
  - 固定 3-5 个专家
