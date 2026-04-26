# RoundTable V2 发布说明

## 版本信息
- **版本号**: 0.9.1
- **发布日期**: 2026-03-21
- **作者**: 虾软 Claw soft

## 新增功能
- ✅ 集成 146 个全领域专家（engineering/design/marketing/sales 等）
- ✅ 需求智能分析器（8 种需求类型自动识别）
- ✅ 精准专家匹配（分类 + 关键词双匹配）
- ✅ 按议题分治讨论（不再固定 5 轮）
- ✅ 动态复杂度适配（auto/high/medium/low）

## 核心文件
- requirement_analyzer.py - 需求分析器
- roundtable_engine_v2.py - V2 引擎
- roundtable_notifier.py - 通知器
- agency_agents_loader.py - 146 个专家加载器

## 使用示例
```python
from roundtable_engine_v2 import run_roundtable_v2

await run_roundtable_v2(
    topic="智能待办应用的架构设计",
    complexity="auto"
)
```

## 安全检查
- ✅ 无个人路径
- ✅ 无硬编码地址
- ✅ 无敏感信息
- ✅ 版本一致

## 安装
上传到 ClawHub 后，用户可以通过以下方式安装：
```
openclaw skills install roundtable-skill
```

## 文档
- SKILL.md - 技能说明
- INSTALL.md - 安装与使用指南
- CHANGELOG.md - 变更日志
