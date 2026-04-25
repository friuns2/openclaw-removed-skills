# 🤖 Auto-Coding Skill for Nanobot - 发布指南

**版本**: 1.1.0  
**目标平台**: Nanobot  
**发布日期**: 2026-03-15

---

## 📋 发布前检查清单

### 1. 代码质量
- [ ] 所有 Python 文件语法正确
- [ ] 通过 flake8 代码风格检查
- [ ] 单元测试通过率 > 80%
- [ ] 无 TODO 注释（或明确标注）

### 2. 文档完整性
- [x] SKILL.md - Nanobot 技能定义（含 metadata）
- [x] README.md - GitHub 项目说明
- [x] USAGE.md - 详细使用指南
- [ ] CHANGELOG 更新版本号

### 3. 配置文件
- [x] requirements.txt - Python 依赖
- [x] LICENSE - MIT 许可证
- [x] .gitignore - Git 忽略配置
- [ ] 移除 OpenClaw 专用配置

### 4. 功能测试
- [ ] quick 模式测试通过
- [ ] standard 模式测试通过
- [ ] thorough 模式测试通过
- [ ] LLM 调用正常
- [ ] 自我反思功能正常
- [ ] 交付检查功能正常

---

## 🎯 Nanobot Skill 规范

### SKILL.md 格式

Nanobot 官方技能使用 **YAML front matter + metadata** 格式：

```markdown
---
name: auto-coding
description: 自主编程系统 - 分析需求、找方法、自我反思、迭代优化，达到交付标准
metadata: {"nanobot":{"emoji":"🤖","requires":{"bins":["python","pip"]},"install":[{"id":"dashscope","kind":"pip","package":"dashscope","label":"Install DashScope LLM SDK"}]}}
---

# Auto-Coding Skill 🤖

**自主编程系统** - 不是简单的代码生成，而是具备自我反思能力的智能编程系统。

## 使用方式

### 基本用法

```
/auto-coding 创建一个批量重命名文件的脚本
```

### 工作模式

```bash
/auto-coding mode quick 创建一个 Hello World 脚本
/auto-coding mode standard 创建一个天气查询 Web 应用
/auto-coding mode thorough 开发一个完整的待办事项管理应用
```

## 依赖

必需:
- Python >= 3.10
- dashscope (LLM 调用)

可选:
- duckduckgo-search (网络搜索)
```

### Metadata 字段说明

```json
{
  "nanobot": {
    "emoji": "🤖",                    // 技能图标
    "requires": {
      "bins": ["python", "pip"]      // 必需的二进制文件
    },
    "install": [                     // 安装指令
      {
        "id": "dashscope",
        "kind": "pip",
        "package": "dashscope",
        "label": "Install DashScope LLM SDK"
      }
    ]
  }
}
```

---

## 🚀 发布流程

### 步骤 1: 清理不必要的文件

```bash
cd ~/.nanobot/workspace/skills/auto-coding

# 移除 OpenClaw 专用配置
rm -f clawhub.openclaw.json
rm -f CONFIG_COMPARISON.md
rm -f OPENCLAW_READY.md

# 保留内部文档（可选）
# - CREATION_SUMMARY.md
# - INTEGRATION_REPORT.md
# - llm_client_v2.py (如果有用)
```

### 步骤 2: 更新版本号

编辑 `SKILL.md` 和 `README.md`：

```markdown
> **版本**: 1.1.0
```

编辑 `requirements.txt`（如有需要）：

```txt
dashscope>=1.0.0
duckduckgo-search>=4.0.0
```

### 步骤 3: 提交到 Git

```bash
cd ~/.nanobot/workspace/skills/auto-coding

# 初始化 Git（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "release: v1.1.0 - Nanobot Skill

- 符合 Nanobot 官方技能规范
- 添加 metadata 配置（emoji/依赖/安装）
- 完善 SKILL.md 和 README.md
- 添加 GitHub Actions CI
- MIT 开源许可证"

# 添加标签
git tag -a v1.1.0 -m "Release version 1.1.0 - Nanobot Skill"
```

### 步骤 4: 推送到 GitHub

```bash
# 添加远程仓库（首次）
git remote add origin https://github.com/krislu/enhance-claw.git

# 推送到分支
git push origin main

# 推送标签
git push origin v1.1.0
```

### 步骤 5: 创建 GitHub Release

1. 访问 https://github.com/krislu/enhance-claw/releases/new
2. 选择标签 `v1.1.0`
3. 填写发布说明（参考下方模板）
4. 点击 "Publish release"

---

## 📝 GitHub Release 模板

```markdown
## 🤖 Auto-Coding Skill v1.1.0 - Nanobot

自主编程系统 - 具备自我反思能力的智能编程系统。

### ✨ 特性

- **自我反思** - 4 级反思深度（surface/root/pattern/growth）
- **工作模式** - quick/standard/thorough 三种模式
- **交付标准** - 8 项检查确保代码质量
- **LLM 集成** - 阿里云百炼 Qwen3.5-Plus

### 📦 安装

```bash
# 1. 安装依赖
pip install dashscope
pip install duckduckgo-search  # optional

# 2. 配置 API Key
export DASHSCOPE_API_KEY=sk-your-key-here

# 3. 复制技能
cp -r auto-coding ~/.nanobot/workspace/skills/
```

### 💡 使用

```bash
# 在 nanobot 中
/auto-coding mode quick 创建一个 Hello World 脚本
/auto-coding mode standard 创建一个天气查询 Web 应用
```

### 📋 依赖

- Python >= 3.10
- dashscope >= 1.0.0
- duckduckgo-search >= 4.0.0 (optional)

### 📖 文档

- [使用指南](USAGE.md)
- [技能定义](SKILL.md)

---

**Full Changelog**: https://github.com/krislu/enhance-claw/compare/v1.0.0...v1.1.0
```

---

## 📁 最终目录结构

```
auto-coding/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── tests/
│   └── test_worker.py          # 测试套件
├── prompts/
│   └── analysis.txt            # 提示词模板
├── .gitignore                  # Git 忽略
├── LICENSE                     # MIT 许可证
├── requirements.txt            # Python 依赖
├── __init__.py                 # 包初始化
├── worker.py                   # 核心工作流
├── self_reflect.py             # 自我反思
├── delivery_check.py           # 交付检查
├── llm_client.py               # LLM 调用
├── SKILL.md                    # ⭐ Nanobot 技能定义
├── README.md                   # ⭐ GitHub 项目说明
├── USAGE.md                    # 详细使用指南
├── CREATION_SUMMARY.md         # 创建总结（可选）
└── PUBLISH_GUIDE.md            # 本文件
```

---

## 🔍 验证发布

### 1. 验证 SKILL.md 格式

```bash
# 检查 front matter
head -5 SKILL.md

# 应该看到：
# ---
# name: auto-coding
# description: ...
# metadata: {...}
# ---
```

### 2. 验证 metadata JSON

```bash
# 提取并验证 metadata
grep "^metadata:" SKILL.md | cut -d':' -f2- | python -c "import sys,json; json.load(sys.stdin)" && echo "✅ metadata 有效"
```

### 3. 测试技能

```bash
# 在 nanobot 中测试
/auto-coding mode quick 创建一个 Hello World 脚本

# 检查日志
tail -f ~/.nanobot/workspace/sessions/latest.log
```

### 4. 验证 GitHub 仓库

```bash
# 克隆验证
git clone https://github.com/krislu/enhance-claw.git
cd enhance-claw/skills/auto-coding

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

---

## 🐛 常见问题

### Q1: metadata 格式错误

**错误**: `Invalid metadata JSON`

**解决**:
```bash
# 检查 SKILL.md 的 front matter
head -5 SKILL.md

# 确保 metadata 是有效的 JSON
# 使用单引号包裹整个 JSON
```

### Q2: 依赖安装失败

**错误**: `Could not find a version that satisfies the requirement dashscope`

**解决**:
```bash
# 升级 pip
pip install --upgrade pip

# 重新安装
pip install dashscope
```

### Q3: LLM 调用失败

**错误**: `API key not valid`

**解决**:
```bash
# 检查 API Key
echo $DASHSCOPE_API_KEY

# 重新设置
export DASHSCOPE_API_KEY=sk-your-key-here
```

---

## 📊 Nanobot Skill 规范检查

| 项目 | 要求 | 状态 |
|------|------|------|
| **SKILL.md front matter** | YAML 格式 | ✅ |
| **name 字段** | 技能名称 | ✅ |
| **description 字段** | 技能描述 | ✅ |
| **metadata 字段** | JSON 格式 | ✅ |
| **metadata.nanobot.emoji** | 技能图标 | ✅ 🤖 |
| **metadata.nanobot.requires** | 依赖声明 | ✅ |
| **metadata.nanobot.install** | 安装指令 | ✅ |
| **使用示例** | 至少 1 个 | ✅ |
| **依赖说明** | 必需/可选 | ✅ |

---

## 🎉 发布后

1. **通知用户**: 在相关渠道发布更新通知
2. **监控反馈**: 关注 GitHub Issues
3. **持续改进**: 根据反馈规划下一版本

---

## 🔗 相关链接

- **Nanobot 官方**: https://github.com/nanobot-ai/nanobot
- **Nanobot Skills**: https://github.com/nanobot-ai/nanobot/tree/main/nanobot/skills
- **ClawHub**: https://clawhub.ai

---

**发布检查完成日期**: 2026-03-15  
**发布负责人**: Kris Lu  
**技能名称**: auto-coding  
**目标平台**: Nanobot  
**状态**: ✅ Nanobot Ready!

🐱 **Made with ❤️ by Kris + nanobot**
