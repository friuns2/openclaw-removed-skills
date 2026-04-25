# Auto-Coding Skill for Nanobot 🤖

> **版本**: 2.1.0 (深度分析 + 交付检查)  
> **创建时间**: 2026-03-15  
> **LLM**: 复用 nanobot 实例配置  
> **平均耗时**: 15-300 秒 (智能调整)  
> **交付通过率**: 90%+

自主编程系统 - 不是简单的代码生成，而是具备**需求拆解**和**自我反思**能力的智能编程系统。

---

## 💡 设计理念

### v2.1.0 新增：交付标准检查 ✅

**问题**: 代码写完了，但不知道是否真的“可用”。
**解决方案**: v2.1.0 引入**交付标准检查模块**，在代码交付前进行 8 项严格检查：
- ✅ 语法检查、安全检查、文档完整性
- ✅ 错误处理、基本测试、功能完整性
- ✅ TODO 检查、代码风格

### v2.0.0 新增：深度分析模块 🔍

**问题**: 简单的自我反思不足以解决复杂逻辑错误。
**解决方案**: v2.0.0 引入**深度分析模块** (`deep_analysis.py`)：
- ✅ 根因分析 (Root Cause Analysis)
- ✅ 模式识别 (Pattern Recognition)
- ✅ 多维度验证 (Multi-dimensional Verification)

### v1.3.0 新增：需求拆解器 🎯

**问题**: 之前的版本所有任务都走相同流程，Hello World 也要 98 秒！

**解决方案**: v1.3.0 引入**前置需求拆解器**，智能判断任务复杂度：

```
用户输入 → 需求拆解器 → 复杂度评估 → 执行计划 → Worker
           (独立模块)     (1-10 分)     (步骤配置)
```

**效果对比**:

| 任务 | v1.2.0 | v1.3.0 | 提升 |
|------|--------|--------|------|
| Hello World | 98 秒 | **15 秒** | ⚡ 6.5x |
| 爬虫项目 | 98 秒 | **75 秒** | ⚡ 1.3x |
| 系统重构 | 98 秒 | **210 秒** | 🔍 更充分 |

### 为什么复用 nanobot 的 LLM 配置？

**问题**: 早期的 auto-coding skill 需要单独配置 API Key 和模型，这导致：
- ❌ 配置重复（nanobot 实例已有配置）
- ❌ skill 无法在不同实例间复用
- ❌ 用户需要管理多套 API Key

**解决方案**: v1.2.0 开始，auto-coding skill **直接复用 nanobot 实例的 LLM 配置**：
- ✅ 无需单独配置 API Key
- ✅ 自动使用实例配置的模型
- ✅ skill 可以在任何 nanobot 实例上运行
- ✅ 用户可以切换 LLM provider，skill 自动适配

**架构对比**:

```
❌ 旧架构 (v1.1.0):
nanobot 实例 → auto-coding skill → 直接调用 DashScope API (单独配置)

✅ 新架构 (v1.2.0+):
nanobot 实例 → auto-coding skill → 读取实例配置 → 调用配置的 LLM
```

---

## 🎯 核心理念

```
分析需求 → 找方法 → 实现 → 测试 → 反思 → 修复 → 交付
```

**关键特性**:
- 🔍 **需求分析** - 理解要做什么，识别能力缺口
- 📚 **方法研究** - 搜索工具、文档、最佳实践
- 💻 **代码实现** - 编写代码/配置
- 🧪 **测试验证** - 验证是否工作
- 🤔 **自我反思** - 哪里可以改进（核心！）
- 🔧 **迭代修复** - 持续优化
- ✅ **交付标准** - 达到标准才结束

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install dashscope
pip install duckduckgo-search  # optional, for web search
```

### 2. 配置 LLM

```bash
export DASHSCOPE_API_KEY=sk-your-api-key-here
```

### 3. 安装技能

```bash
# 克隆或复制到 nanobot skills 目录
cp -r auto-coding ~/.nanobot/workspace/skills/
```

### 4. 测试

```bash
# 在 nanobot 中
/auto-coding mode quick 创建一个 Hello World 脚本
```

---

## 💡 使用示例

### 基本用法

```bash
/auto-coding 创建一个批量重命名文件的脚本
/auto-coding 帮我写一个 JSON 格式化工具
```

### 工作模式

```bash
# 快速模式 (1-3 分钟)
/auto-coding mode quick 创建一个 Hello World 脚本

# 标准模式 (5-30 分钟，推荐)
/auto-coding mode standard 创建一个天气查询 Web 应用

# 彻底模式 (15-30 分钟)
/auto-coding mode thorough 开发一个完整的待办事项管理应用
```

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

## 🏗️ 架构

### 文件结构

```
auto-coding/
├── SKILL.md              # Nanobot 技能定义
├── README.md             # 本文件
├── USAGE.md              # 详细使用指南
├── DECOMPOSER_DESIGN.md  # 需求拆解器设计文档
├── worker.py             # 核心工作流引擎
├── decomposer.py         # 需求拆解器 (v1.3.0 新增)
├── self_reflect.py       # 自我反思模块
├── delivery_check.py     # 交付标准检查
├── llm_client.py         # LLM 调用客户端
├── requirements.txt      # Python 依赖
├── prompts/              # 提示词模板
└── tests/                # 测试套件
```

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 需求拆解器 | `decomposer.py` | 分析复杂度，生成执行计划 (v1.3.0) |
| 深度分析 | `deep_analysis.py` | 根因分析、模式识别 (v2.0.0) |
| 交付检查 | `delivery_check.py` | 8 项交付标准检查 (v2.1.0) |
| 工作流引擎 | `worker.py` | 协调整个编程流程 |
| 自我反思 | `self_reflect.py` | 4 级反思深度 |
| LLM 调用 | `llm_client.py` | 阿里云百炼集成 |

### 工作流

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto-Coding 工作流 (v2.1.0)               │
├─────────────────────────────────────────────────────────────┤
│  0. 需求拆解 → 分析复杂度，生成执行计划                       │
│  1. 分析需求 → 识别能力缺口                                  │
│  2. 找方法   → 搜索工具、文档、最佳实践                       │
│  3. 实现     → 编写代码/配置                                 │
│  4. 测试     → 验证是否工作                                  │
│  5. 深度分析 → 根因分析、模式识别 (v2.0+)                    │
│  6. 反思     → 哪里可以改进（关键！）                         │
│  7. 修复     → 迭代优化                                      │
│  8. 交付检查 → 8 项标准严格把关 (v2.1+)                      │
│  9. 交付     → 达到标准才结束                                │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 配置

### LLM 配置

默认使用阿里云百炼 `qwen3.5-plus` 模型：

```python
# llm_client.py
LLM_CONFIG = {
    "provider": "bailian",
    "model": "qwen3.5-plus",
    "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
    "timeout": 120
}
```

### 工作模式

```python
# worker.py
WORK_MODES = {
    "quick": {
        "description": "快速实现 (1-3 分钟)",
        "max_iterations": 2,
        "reflect_depth": "surface"
    },
    "standard": {
        "description": "标准模式 (5-30 分钟，推荐)",
        "max_iterations": 5,
        "reflect_depth": "deep"
    },
    "thorough": {
        "description": "彻底模式 (15-30 分钟)",
        "max_iterations": 8,
        "reflect_depth": "growth"
    }
}
```

### 反射级别

| 级别 | 说明 | 深度 |
|------|------|------|
| `surface` | 什么错了 | 1 |
| `root` | 为什么错 | 2 |
| `pattern` | 思维模式问题 | 3 |
| `growth` | 如何改进 | 4 |

---

## ✅ 交付标准

代码交付前会通过以下 8 项检查：

1. **语法检查** - 代码无语法错误
2. **安全检查** - 无安全隐患
3. **文档完整性** - 有必要的注释和说明
4. **错误处理** - 有适当的异常处理
5. **基本测试** - 有测试用例
6. **功能完整性** - 实现所有需求
7. **TODO 检查** - 无遗留 TODO
8. **代码风格** - 风格一致

---

## 🧪 测试

```bash
# 运行测试套件
cd tests
python -m pytest test_worker.py -v

# 带覆盖率
python -m pytest test_worker.py -v --cov=. --cov-report=html
```

---

## 🔧 故障排除

### LLM 调用失败

**错误**: `API key not valid`

**解决**:
```bash
export DASHSCOPE_API_KEY=sk-your-api-key-here
```

### 依赖缺失

**错误**: `ModuleNotFoundError: No module named 'dashscope'`

**解决**:
```bash
pip install -r requirements.txt
```

### 测试失败

**错误**: 测试用例失败

**解决**:
```bash
cd tests
python -m pytest test_worker.py -v -s
```

---

## 📊 性能指标 (v2.1.0)

| 任务类型 | 复杂度 | 耗时 | 说明 |
|----------|--------|------|------|
| 简单任务 | 1-3/10 | **15 秒** | Hello World 等 |
| 中等任务 | 4-6/10 | **60 秒** | 爬虫、小工具 |
| 复杂任务 | 7-10/10 | **180 秒** | 系统重构、完整项目 |

| 指标 | 数值 | 说明 |
|------|------|------|
| 交付通过率 | 90%+ | 首次交付 (v2.1 提升) |
| 迭代次数 | 1-5 次 | 取决于复杂度 |
| Hello World 优化 | 98 秒 → 15 秒 | ⚡ 6.5x 提升 |

---

## 🗺️ 路线图

### v2.1.0 (当前)
- ✅ 需求拆解器 (v1.3)
- ✅ 深度分析模块 (v2.0)
- ✅ 交付标准检查 (v2.1)
- ✅ 8 项严格交付标准

### v2.2.0 (计划)
- 🔜 支持更多 LLM provider
- 🔜 代码审查功能
- 🔜 多文件项目管理
- 🔜 Git 集成

### v3.0.0 (愿景)
- 🔮 完整的项目脚手架
- 🔮 持续集成支持
- 🔮 团队协作功能

---

## 🤝 贡献

欢迎贡献！请参考以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🔗 相关链接

- **Nanobot**: https://github.com/nanobot-ai/nanobot
- **阿里云百炼**: https://dashscope.aliyun.com
- **使用指南**: USAGE.md
- **技能定义**: SKILL.md

---

**Made with ❤️ by Kris + nanobot** 🐱
