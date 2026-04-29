# 批量重新学习计划

## 目标
重新学习已完成的46篇文档，并正确存入向量记忆

## 原因
之前学习的内容未正确索引到向量记忆，导致无法检索

## 待重新学习文档清单

### concepts/ 目录 (27篇)
1. retry.md - 重试机制
2. model-failover.md - 模型故障转移
3. agent.md - Agent运行时
4. agent-loop.md - Agent循环
5. agent-workspace.md - Agent工作区
6. architecture.md - Gateway架构
7. compaction.md - 上下文压缩
8. context.md - 上下文构成
9. context-engine.md - 上下文引擎
10. features.md - 功能特性
11. markdown-formatting.md - Markdown渲染
12. messages.md - 消息流
13. memory.md - 记忆系统
14. model-providers.md - 模型提供商
15. models.md - 模型选择
16. multi-agent.md - 多代理路由
17. oauth.md - OAuth认证
18. presence.md - 在线状态
19. queue.md - 命令队列
20. session.md - 会话管理
21. session-pruning.md - 会话修剪
22. session-tool.md - 会话工具
23. streaming.md - 流式响应
24. system-prompt.md - 系统提示词
25. timezone.md - 时区处理
26. typebox.md - TypeBox协议
27. typing-indicators.md - 输入指示器

### automation/ 和其他 (19篇)
28. date-time.md
29. brave-search.md
30. auth-credential-semantics.md
31. ci.md
32. prose.md
33. perplexity.md
34. pi.md
35. pi-dev.md
36. tts.md
37. vps.md
38. index.md
39. README.md
40. cron-jobs.md
41. cron-vs-heartbeat.md
42. hooks.md
43. ollama.md
44. gmail-pubsub.md
45. auth-monitoring.md
46. poll.md

## 正确索引流程

每篇文档学习后必须执行：
1. 读取文档内容
2. 提取关键知识点
3. **更新 MEMORY.md** （关键！只有这里的内容会被向量索引）
4. 使用 memory_search 验证可检索
5. 报告向量索引状态

## 执行方式

可选择：
- **方式1**: 批量执行（一次性学习多篇）
- **方式2**: 心跳逐个学习（每15分钟一篇，约11.5小时完成）
- **方式3**: 加速学习（每5分钟一篇，约4小时完成）

你想用哪种方式？
