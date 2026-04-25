# 帝国架构 v1 精简版 / Empire Architecture v1 Lite

基于中国古代三公九卿制的 AI 多智能体协作系统。

A multi-agent AI collaboration system inspired by China's ancient Three Departments and Nine Ministries system.

---

## 架构概览 / Architecture Overview

```
帝国 v1 精简版 / Empire v1 Lite
├── 丞相 Chancellor       — 总协调 / Coordinator
├── 谋略参谋 Strategist    — 策略分析 / Strategy
├── 技术参谋 Tech Advisor  — 技术方案 / Technical
├── 情报参谋 Intel Analyst — 数据分析 / Intelligence
├── 文曹 Writer            — 文档撰写 / Documentation
├── 码曹 Coder             — 代码开发 / Development
├── 查曹 Researcher        — 信息检索 / Research
└── 锦衣卫 Security        — 安全审计 / Security Audit
```

## 核心设计 / Core Design

### 角色映射 / Role Mapping

| 历史角色 Historical | 系统角色 System Role | 职能 Function |
|---|---|---|
| 皇帝 Emperor | 用户 (User) | 最终决策权 / Final authority |
| 丞相 Chancellor | Mimo 协调器 | 任务编排与汇总 / Orchestration |
| 幕僚 Advisors | 参谋节点 ×3 | 多角度分析 / Multi-perspective analysis |
| 六曹 Executors | 执行节点 ×3 | 具体任务执行 / Task execution |
| 锦衣卫 Security | 安全审计节点 | 输出审查与合规 / Audit & compliance |

### 制衡机制 / Checks & Balances

- **生成与校验分离** — 丞相编排，锦衣卫审计
- **并行执行** — 多节点同时工作，加速决策
- **Token 追踪** — SQLite 记录消耗，预算控制
- **消息总线** — 异步队列，节点间解耦通信

## 快速开始 / Quick Start

```bash
# 交互模式 / Interactive mode
python3 empire/main.py

# 单次执行 / Single command
python3 empire/main.py "分析当前AI行业趋势"

# 查看状态 / Check status
python3 empire/main.py --status
python3 empire/main.py --agents
python3 empire/main.py --tokens
```

## 技术栈 / Tech Stack

| 组件 Component | 选型 Choice |
|---|---|
| 模型 Model | MiMo V2.5 Pro (小米) |
| 语言 Language | Python 3.12 |
| 并发 Concurrency | asyncio |
| 存储 Storage | SQLite |
| 依赖 Dependencies | 零外部依赖 / Zero external deps |

## 时间加速 / Time Acceleration

帝国支持 10x 时间加速模式：

The Empire supports 10x time acceleration:

```python
from empire.accelerator import AcceleratedExecutor
executor = AcceleratedExecutor(chancellor, max_parallel=2)
results = await executor.execute_batch(tasks)
# 现实20分钟 = 帝国3小时20分
# 20 real minutes = 3h20m empire time
```

## 文件结构 / File Structure

```
empire/
├── config.json          # 配置文件 / Configuration
├── main.py              # CLI 入口 / CLI entry point
├── chancellor.py        # 丞相协调器 / Chancellor orchestrator
├── accelerator.py       # 时间加速引擎 / Time acceleration
├── core/
│   ├── config.py        # 配置加载 / Config loader
│   ├── bus.py           # 消息总线 / Message bus
│   ├── tokens.py        # Token 追踪 / Token tracker
│   └── security.py      # 安全系统 / Security system
├── agents/
│   └── base.py          # Agent 基类 / Agent base class
└── data/
    └── tokens.db        # Token 数据库 / Token database
```

## 完整版设计 / Full Architecture

详见 [empire-architecture-v1.md](./empire-architecture-v1.md)

完整版包含 41 个 AI 节点 + 1 个人类皇帝，含联邦学习、投票制处决、替补池等机制。

The full version includes 41 AI nodes + 1 human emperor, with federated learning, voting-based execution, and backup pools.

## License

MIT
