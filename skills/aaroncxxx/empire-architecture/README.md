# Empire-Architecture v1.8

基于中国古代三公九卿制的 AI 多智能体协作系统。

## 项目结构

```
├── empire-architecture/    # 帝国架构核心代码
│   ├── lite/               # 可运行版本 (25节点)
│   │   ├── main.py         # CLI入口
│   │   ├── chancellor.py   # 丞相协调器
│   │   ├── v14_runner.py   # 知识层运行器
│   │   ├── selfcheck_v17.py # V1.7 并行自检框架
│   │   ├── config.json     # 25节点配置
│   │   ├── agents/         # Agent基类
│   │   ├── core/           # 消息总线/Token/安全
│   │   └── knowledge/      # 翰林院知识层
│   ├── EVALUATION-v1.4.md  # 评估报告
│   ├── CHANGELOG-v1.7.md   # V1.7 更新日志
│   ├── CHANGELOG-v1.8.md   # V1.8 更新日志
│   └── empire-architecture-v1.md  # 完整设计文档
├── skills/                 # ClawHub技能包 (7个)
│   ├── agent-autonomy-kit
│   ├── agentic-workflow-automation
│   ├── ai-agent-helper
│   ├── automation-workflow-builder
│   ├── how-much-token-did-this-chat-used
│   ├── mimo-tts-asr-26-free
│   └── system-selfcheck
├── memory/                 # 记忆与日志
│   ├── 2026-04-25.md
│   └── MEMORY.md
└── README.md
```

## 25节点架构

| 类别 | 节点 | 职责 |
|------|------|------|
| 中枢 | 丞相 | 总协调 |
| 参谋 | 谋略/技术/情报 | 分析决策 |
| 执行 | 文曹/码曹/查曹 | 任务执行 |
| 六部 | 吏/户/礼/兵/刑/工 | 专项管理 |
| 翰林 | 翰林学士/国子监 | 知识管理 |
| 特殊 | 钦天监/太医/御厨/**观星台** | 预警/诊断/清洗/**深度观测** |
| 监察 | 御史大夫/中书令 | 质量/流程 |
| 扩展 | 大理寺/大鸿胪/少府 | 逻辑/翻译/创意 |
| 安全 | 锦衣卫 | 安全审计 |

## 运行

```bash
cd empire-architecture/lite
export MIMO_API_KEY="your-key"
export MIMO_API_ENDPOINT="https://your-endpoint/v1"
python3 v14_runner.py "你的指令"
```

## License

MIT
