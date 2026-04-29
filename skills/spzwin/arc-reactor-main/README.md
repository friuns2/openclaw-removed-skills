# ARC Reactor Skill - AI Agent 知识编译引擎

> **⚠️ Agent Entry Point**
> 此目录是 ARC Reactor 的分发核心。如果你是正在读取此文件的 AI Agent，请以 `SKILL.md` 作为你的行为准则。

## 🎯 功能概览 (v4.2.0)

本项目是基于 Karpathy **Compilation over Retrieval** 理念构建的知识库。

1. **Ingest**: 深度摄入，执行“四连击”归档（Source, Entity, Index, Log）。
2. **Context Injection**: 自动从 Wiki 中检索实体内容注入上下文，实现无感知识增强。
3. **Weekly Reporter**: 聚合过去一周的摄入内容，生成高维度洞察周报。
4. **Wiki Lint**: 自动化维护词条链接的完整性。

## 📦 目录结构

```text
skills/arc-reactor/
├── SKILL.md                  # Agent 核心指令集
├── arc-reactor-config.yaml   # 多模型路由与功能配置
├── _meta.json                # 元数据
├── scripts/
│   ├── archive-manager.py    # 存储与归档逻辑
│   ├── context-injector.py   # 潜意识注入探针
│   └── weekly-reporter.py    # 周报聚合引擎
└── references/               # 模板与审计规范
```

## 🚀 核心指令

### 1. 知识归档 (Ingest)
```bash
cat << 'EOF' | python3 scripts/archive-manager.py --type source --topic "标题" --stdin
[Markdown Content]
EOF
```

### 2. 潜意识探测 (Inject)
```bash
python3 scripts/context-injector.py --query "[用户的问题]"
```

### 3. 周汇总 (Weekly)
```bash
python3 scripts/weekly-reporter.py --days 7
```

## ⚙️ 配置说明
编辑 `arc-reactor-config.yaml` 可以调整：
- **models**: 不同任务分派给哪些模型（GPT-4o vs Flash）。
- **injection**: 开启/关闭自动注入，调整最大实体提取数。
- **weekly_brief**: 调整周报扫描天数。

---
*Powered by ARC Reactor v4.2.0*
