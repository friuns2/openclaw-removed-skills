# Memory Governor

**Memory governance for AI agents. Complements OpenClaw Dreaming instead of replacing it.**

Languages: **English** | [中文](#中文)

`memory-governor` is a governance kernel for hosts that already have multiple memory layers, memory-writing skills, or optional adapters. It gives those systems one shared contract for deciding what should be remembered, where it should go, when it should stay temporary, and when it is safe to harden into durable guidance.

OpenClaw Dreaming is great at background consolidation from short-term signals into long-term memory. `memory-governor` focuses on the adjacent gap: explicit correction staging, memory routing, adapter boundaries, and manual hardening rules.

In short:

- Dreaming handles background consolidation.
- `memory-governor` handles capture rules, target classes, correction staging, and hardening boundaries.

## Why Install It

Install `memory-governor` when your agent memory is starting to drift:

- multiple skills write memory-like state
- explicit corrections are getting mixed into daily notes
- single observations harden into long-term rules too quickly
- optional adapters such as `self-improving` or `proactivity` create routing ambiguity
- you want one contract before the system becomes path-based chaos

This is not an execution-first productivity skill. It is infrastructure for memory-heavy agent systems.

## What It Adds

- Standard memory target classes:
  `long_term_memory`, `daily_memory`, `learning_candidates`, `reusable_lessons`, `proactive_state`, `working_buffer`, `project_facts`, `system_rules`, and `tool_rules`
- A routing model:
  `memory type -> target class -> adapter / fallback`
- A low-commitment `learning_candidates` layer for explicit corrections and first-sighting lessons
- Candidate review guidance for `keep / promote / discard`
- Clear promotion authority:
  Dreaming-preferred for `daily_memory -> long_term_memory`, manual review for correction hardening and system-rule promotion
- Boundaries for Dreaming artifacts:
  `DREAMS.md` and `memory/.dreams/` are engine-owned artifacts, not standard memory target classes
- Host manifest support through `memory-governor-host.toml`
- Host checker, frontmatter validator, candidate reviewer, and generic-host bootstrap scripts
- A generic host example that does not require OpenClaw-specific directories

## Core Model

`memory-governor` separates memory decisions into three layers:

1. **Memory type**
   What kind of information is this?
2. **Target class**
   Which abstract memory layer should own it?
3. **Adapter / fallback**
   Where does this host store that target class?

That keeps the core contract independent from any one plugin, folder layout, or host implementation.

## Dreaming Compatibility

`memory-governor` should not compete with Dreaming.

Recommended split:

- Dreaming:
  `daily_memory -> long_term_memory`
- `memory-governor`:
  capture rules, correction staging, adapter boundaries, and manual hardening
- Human / explicit review:
  `learning_candidates -> reusable_lessons -> system_rules / tool_rules`

Do not model `DREAMS.md` or `memory/.dreams/` as normal memory target classes. Treat them as Dreaming-owned artifacts.

See [dreaming-integration.md](references/dreaming-integration.md).

## Readiness Model

`memory-governor` uses three readiness states:

- `Installed`
  The skill is available and the rules can be read.
- `Integrated`
  The host has wired itself to the memory contract.
- `Validated`
  The host checker has confirmed the wiring.

Installation does **not** silently rewrite `AGENTS.md`, other skills, or existing memory files. Host integration should be explicit.

## Quick Start

Recommended first reading path:

1. [SKILL.md](SKILL.md)
2. [memory-routing.md](references/memory-routing.md)
3. [promotion-rules.md](references/promotion-rules.md)
4. [dreaming-integration.md](references/dreaming-integration.md)
5. [adapters.md](references/adapters.md)
6. [installation-integration.md](references/installation-integration.md)

For a generic host example:

- [examples/generic-host/README.md](examples/generic-host/README.md)

For package maintenance:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Scripts

- [check-memory-host.py](scripts/check-memory-host.py)
  checks host manifest wiring, fallback paths, and integration declarations
- [validate-memory-frontmatter.py](scripts/validate-memory-frontmatter.py)
  validates structured memory files
- [review-learning-candidates.py](scripts/review-learning-candidates.py)
  reviews candidate freshness and structure without auto-promoting
- [bootstrap-generic-host.sh](scripts/bootstrap-generic-host.sh)
  creates a minimal generic host skeleton
- [refresh-clawhub-package.sh](scripts/refresh-clawhub-package.sh)
  refreshes the publish-only ClawHub package

Python compatibility:

- Python 3.11+ uses standard-library `tomllib`
- Python 3.9 / 3.10 should install `tomli`

## Package Layout

Runtime package:

- `SKILL.md`
- `README.md`
- `VERSION`
- `references/`
- `assets/`
- `scripts/`
- `examples/generic-host/`

Maintainer-only material:

- `tests/`
- `dev/`
- `releases/`

ClawHub should be published from:

- `publish/clawhub/`

not from the repository root.

## What It Is Not

`memory-governor` is not:

- a second-brain platform
- a Notion / Obsidian sync engine
- a universal sync bus
- an auto-archiving system
- a replacement for Dreaming
- a runtime hook system that forces memory routing automatically

It gives the host a contract. The host still decides how to integrate it.

## Current Version

`0.2.9`

## 中文

**面向 AI agent 的记忆治理内核。它不是 Dreaming 的替代品，而是 Dreaming 的补完层。**

`memory-governor` 适合已经出现多层记忆、多种写记忆 skill、或者可选 adapter 越来越多的宿主系统。它提供一套统一 contract，用来判断什么值得记、应该进入哪一层、什么时候保持短期、什么时候可以被硬化成长期规则。

OpenClaw Dreaming 很适合做短期信号到长期记忆的后台巩固。`memory-governor` 负责旁边那个缺口：明确纠错的候选层、记忆路由、adapter 边界、人工升格边界。

一句话：

- Dreaming 负责后台巩固。
- `memory-governor` 负责捕获规则、target classes、纠错候选层和 hardening 边界。

## 为什么安装

当你的 agent 记忆开始变复杂时，`memory-governor` 会更有价值：

- 多个 skill 都在写 memory-like state
- 明确纠错混进了 daily notes
- 单次观察太快硬化成长期规则
- `self-improving`、`proactivity` 这类可选 adapter 开始带来路由歧义
- 你想在系统变乱之前先建立一套共享 contract

它不是一个“装上立刻替你干活”的生产力 skill。它更像复杂记忆系统的基础设施。

## 它提供什么

- 标准 memory target classes：
  `long_term_memory`、`daily_memory`、`learning_candidates`、`reusable_lessons`、`proactive_state`、`working_buffer`、`project_facts`、`system_rules`、`tool_rules`
- 路由模型：
  `memory type -> target class -> adapter / fallback`
- 低承诺候选层 `learning_candidates`，用于明确纠错和首次出现但尚未证明可复用的经验
- `keep / promote / discard` 的 candidate review 规则
- 清晰的 promotion authority：
  Dreaming 优先处理 `daily_memory -> long_term_memory`，人工 review 处理纠错 hardening 和系统规则升格
- Dreaming 产物边界：
  `DREAMS.md` 和 `memory/.dreams/` 是 engine-owned artifacts，不是标准 target classes
- `memory-governor-host.toml` 宿主 manifest
- host checker、frontmatter validator、candidate reviewer、generic-host bootstrap 等轻量工具
- 不依赖 OpenClaw 固定目录结构的 generic host 示例

## 核心模型

`memory-governor` 把记忆决策拆成三层：

1. **Memory type**
   这条信息是什么？
2. **Target class**
   它应该进入哪个抽象记忆层？
3. **Adapter / fallback**
   当前宿主把这个 target class 落到哪里？

这样治理内核就不会被某个插件、目录结构或宿主实现绑死。

## 和 Dreaming 的关系

`memory-governor` 不应该和 Dreaming 竞争。

推荐分工：

- Dreaming：
  `daily_memory -> long_term_memory`
- `memory-governor`：
  捕获规则、纠错候选层、adapter 边界、人工 hardening
- 人工 / 显式 review：
  `learning_candidates -> reusable_lessons -> system_rules / tool_rules`

不要把 `DREAMS.md` 或 `memory/.dreams/` 当成普通 memory target class。它们应被视为 Dreaming 的 engine-owned artifacts。

详见 [dreaming-integration.md](references/dreaming-integration.md)。

## 接入状态

`memory-governor` 推荐用三种状态理解：

- `Installed`
  skill 已安装，规则可读
- `Integrated`
  宿主已经显式接入这套 contract
- `Validated`
  host checker 已确认接线状态

安装不会静默修改 `AGENTS.md`、其他 skill 或已有记忆文件。宿主集成应该显式执行。

## 快速开始

推荐阅读顺序：

1. [SKILL.md](SKILL.md)
2. [memory-routing.md](references/memory-routing.md)
3. [promotion-rules.md](references/promotion-rules.md)
4. [dreaming-integration.md](references/dreaming-integration.md)
5. [adapters.md](references/adapters.md)
6. [installation-integration.md](references/installation-integration.md)

Generic host 示例：

- [examples/generic-host/README.md](examples/generic-host/README.md)

维护者测试入口：

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## 它不是什么

`memory-governor` 不是：

- second-brain 平台
- Notion / Obsidian 同步器
- 通用同步总线
- 自动归档系统
- Dreaming 替代品
- 强制执行记忆路由的 runtime hook 系统

它提供的是 contract。宿主仍然需要决定如何接入。
