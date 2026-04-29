# OpenClaw 学习历史记录

> 记录从官方文档学习的所有内容
> 最后更新: 2026-03-19

---

## 学习统计

- **总进度**: 46/219 篇 (21.0%)
- **已完成目录**: concepts/ (27篇), automation/ (7篇), 其他 (12篇)
- **学习频率**: 每15分钟一篇

---

## 详细学习记录

### concepts/ 目录 (27篇全部完成)

#### 1. retry.md - 重试机制
**核心收获**:
- 默认配置: 3次尝试，最大延迟30秒，10%抖动
- Telegram策略: 最小延迟400ms，重试429/timeout错误
- Discord策略: 最小延迟500ms，仅重试429错误

#### 2. model-failover.md - 模型故障转移
**核心收获**:
- 两阶段故障处理: Auth轮换→模型回退
- 冷却机制: 1分钟→5分钟→25分钟→1小时

#### 3. agent.md - Agent运行时
**核心收获**:
- Agent Runtime: 工作区、启动文件、会话管理
- 配置优先级: Agent级 > Provider级 > Global级

#### 4. agent-loop.md - Agent循环
**核心收获**:
- Agent Loop: 完整的agent运行循环
- 消息处理流程: 接收→解析→执行→响应

#### 5. agent-workspace.md - Agent工作区
**核心收获**:
- 工作区结构: 代码、配置、数据分离
- Git备份: 自动备份到远程仓库

#### 6. architecture.md - Gateway架构
**核心收获**:
- 组件: Gateway、Agent、Model
- 协议: WebSocket + TypeBox Schema
- 连接生命周期: 建立→认证→会话→关闭

#### 7. compaction.md - 上下文压缩
**核心收获**:
- 自动压缩触发: 接近上下文窗口限制
- 手动压缩: `/compact [指令]`
- Compaction策略: 保留关键信息

#### 8. context.md - 上下文构成
**核心收获**:
- 上下文构成: System Prompt + User Messages + Assistant Messages
- 系统提示词结构: 角色定义+工具描述+安全规则

#### 9. context-engine.md - 上下文引擎
**核心收获**:
- Context Engine: 可插拔的上下文引擎
- 支持自定义上下文处理逻辑

#### 10. features.md - 功能特性
**核心收获**:
- 功能特性概览: Multi-Agent、Streaming、Queue、Memory
- 各特性使用场景和配置

#### 11. markdown-formatting.md - Markdown渲染
**核心收获**:
- 跨平台Markdown渲染
- Telegram/WhatsApp/Discord等平台差异处理

#### 12. messages.md - 消息流
**核心收获**:
- 消息流: 接收→解析→路由→执行→响应
- 队列管理: 串行化处理保证顺序

#### 13. memory.md - 记忆系统
**核心收获**:
- 记忆系统: 每日日志 + 长期记忆
- 向量搜索: 语义检索 + BM25混合
- 文件结构: memory/YYYY-MM-DD.md + MEMORY.md

#### 14. model-providers.md - 模型提供商
**核心收获**:
- 模型提供商配置与认证
- Auth Profile: API Key和OAuth支持
- 多Provider切换和故障转移

#### 15. models.md - 模型选择
**核心收获**:
- 模型选择: 通过CLI或配置
- 成本计算: Input/Output/Cache定价
- 上下文窗口管理

#### 16. multi-agent.md - 多代理路由
**核心收获**:
- 多代理隔离: dmScope配置
- 路由规则: 按频道/角色/账号路由
- per-channel-peer推荐用于多用户

#### 17. oauth.md - OAuth认证
**核心收获**:
- OAuth流程: 授权→Token获取→刷新
- Token管理: 自动刷新和过期处理
- 订阅认证: Webhook通知

#### 18. presence.md - 在线状态
**核心收获**:
- 在线状态管理
- 客户端可见性控制
- 状态同步机制

#### 19. queue.md - 命令队列
**核心收获**:
- Command Queue: 命令队列与会话串行化
- 三种模式: collect/steer/followup
- 队列优先级和超时处理

#### 20. session.md - 会话管理
**核心收获**:
- 会话生命周期: 创建→激活→休眠→关闭
- 会话工具: /status、/compact、/new
- 会话隔离和安全性

#### 21. session-pruning.md - 会话修剪
**核心收获**:
- 会话修剪: 成本优化策略
- 自动清理: 过期会话和无用数据
- 保留重要会话历史

#### 22. session-tool.md - 会话工具
**核心收获**:
- Session Tools: 会话管理工具集
- /context list: 查看上下文内容
- /compact: 压缩上下文释放空间

#### 23. streaming.md - 流式响应
**核心收获**:
- Streaming + Chunking: 流式响应与分块
- Block streaming: 结构化流式输出
- 实时响应和进度显示

#### 24. system-prompt.md - 系统提示词
**核心收获**:
- System Prompt结构: 角色+工具+安全+上下文
- 动态提示词: 根据场景调整
- 提示词模板和变量替换

#### 25. timezone.md - 时区处理
**核心收获**:
- 时区处理与标准化
- IANA时区数据库
- 跨时区时间计算

#### 26. typebox.md - TypeBox协议
**核心收获**:
- TypeBox: 协议Schema与代码生成
- Schema定义: JSON Schema + TypeScript类型
- 运行时类型验证

#### 27. typing-indicators.md - 输入指示器
**核心收获**:
- Typing Indicators: 输入状态显示
- 平台差异: 各平台实现方式
- 用户体验优化

---

### automation/ 目录 (7篇)

#### 28. date-time.md - 日期时间处理
**核心收获**:
- 日期时间处理最佳实践
- 时区感知计算

#### 29. brave-search.md - Brave搜索API
**核心收获**:
- Brave Search API配置
- 每月1000次免费搜索
- Web Search工具集成

#### 30. auth-credential-semantics.md - 认证凭证语义
**核心收获**:
- 认证凭证类型和格式
- 安全存储和传输
- 凭证轮换策略

#### 31. ci.md - CI流水线
**核心收获**:
- CI Pipeline: 持续集成流水线
- GitHub Actions集成
- 自动化测试和部署

#### 32. prose.md - OpenProse格式
**核心收获**:
- OpenProse: 多代理工作流格式
- YAML定义工作流
- Agent协作和任务分配

#### 33. perplexity.md - Perplexity搜索
**核心收获**:
- Perplexity Search API配置
- 学术搜索和引用

#### 34. pi.md - Pi集成
**核心收获**:
- Pi Integration: pi-coding-agent集成
- 架构设计和通信协议

#### 35. pi-dev.md - Pi开发工作流
**核心收获**:
- Pi Development Workflow
- 开发和调试最佳实践

#### 36. tts.md - 文字转语音
**核心收获**:
- TTS配置: Microsoft/ElevenLabs/OpenAI
- 语音选择和参数调整
- 自动语音模式设置

#### 37. vps.md - VPS部署
**核心收获**:
- VPS Hosting: VPS部署指南
- 服务器配置和安全加固
- 域名和SSL配置

#### 38. index.md - 项目主页
**核心收获**:
- OpenClaw项目主页
- 快速入门指南
- 文档结构概览

#### 39. README.md - 文档库说明
**核心收获**:
- 文档库结构
- 贡献指南

#### 40. automation/cron-jobs.md - Cron定时任务
**核心收获**:
- Cron Jobs: Gateway定时任务调度器
- 配置语法和参数
- 错误处理和重试

#### 41. automation/cron-vs-heartbeat.md - Cron vs Heartbeat
**核心收获**:
- Cron vs Heartbeat使用场景对比
- 何时使用Cron，何时使用Heartbeat
- 组合使用最佳实践

#### 42. automation/hooks.md - Hooks系统
**核心收获**:
- Hooks: 事件驱动的自动化系统
- 四种捆绑Hooks: session-memory、bootstrap-extra-files、command-logger、boot-md
- 事件类型: command/session/agent/gateway/message
- CLI管理: openclaw hooks list/enable/disable/info

#### 43. automation/ollama.md - Ollama集成
**核心收获**:
- Ollama本地模型部署
- 与OpenClaw集成配置
- 本地LLM使用场景

#### 44. automation/gmail-pubsub.md - Gmail Pub/Sub
**核心收获**:
- Gmail邮件推送集成
- Pub/Sub订阅配置
- 自动邮件处理流程

#### 45. automation/auth-monitoring.md - 认证监控
**核心收获**:
- Auth监控: `openclaw models status --check`
- 退出码含义: 0=OK, 1=过期, 2=即将过期
- systemd定时任务配置

#### 46. automation/poll.md - 投票功能
**核心收获**:
- Polls投票功能
- 支持平台: Telegram/WhatsApp/Discord/MS Teams
- CLI命令: `openclaw message poll`

---

## 待学习目录

| 目录 | 文档数 | 状态 |
|------|--------|------|
| gateway/ | 31篇 | ⏳ 待开始 |
| tools/ | 26篇 | ⏳ 待开始 |
| channels/ | 24篇 | ⏳ 待开始 |
| cli/ | 45篇 | ⏳ 待开始 |
| providers/ | 15篇 | ⏳ 待开始 |
| 其他 | 32篇 | ⏳ 待开始 |

---

_历史记录存档: 2026-03-19_
_记录者: 珮_
