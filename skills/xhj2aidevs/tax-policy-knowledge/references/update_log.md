<!--
Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
Skill: tax-policy-knowledge | Version: 0.0.0
Author: QQ 1817694478 | Q-Group: 972156177
Unauthorized copying, modification, or distribution is prohibited.
-->
# 知识库更新日志 (Update Log)

> 版本：v1.3.0 | 创建日期：2026-04-20
> 本文件记录知识库的每一次自动更新内容。

---

## 更新记录

### [2] 2026-04-20 - v1.3.0 ClawHub兼容优化
- **更新类型**：结构优化 + 兼容修复
- **内容摘要**：
  1. SKILL.md 从 ~6300 tokens 拆分至 ~1700 tokens，符合 ClawHub 8192 tokens 限制
  2. 新增 references/vat-policy.md（增值税政策详解）
  3. 新增 references/cit-policy.md（企业所得税政策详解）
  4. 新增 references/pit-policy.md（个人所得税政策详解）
  5. 新增 references/risk-indicators.md（金税四期风险预警指标体系）
  6. 新增 references/self-learning.md（自学习机制详解）
  7. 修复 Python 脚本 Windows GBK 控制台兼容性问题
- **触发原因**：ClawHub 提交报错 "maximum context length is 8192 tokens"
- **验证状态**：[OK] 已验证

---

### [1] 2026-04-19 - v1.2.0 重大版本更新
- **更新类型**：全量更新 + 功能增强
- **内容摘要**：
  1. 新增「七、税务风险预警指标体系」章节，含金税四期22项预警指标（A类发票/B类收入/C类成本/D类费用/E类往来款/F类财务）
  2. 新增「八、自学习与自动更新机制」章节
  3. 新增 references/tax-policy-database.md 第六章「税务风险预警指标体系」详细数据库
  4. 新增 scripts/auto_update_knowledge.py 自动更新脚本
  5. 新增 scripts/self_learning.py 自主学习脚本
  6. 新增 references/learning_log.md 学习日志
  7. 新增 references/update_log.md 更新日志
- **发现来源**：用户交互触发 + 联网搜索验证
- **验证状态**：[OK] 已验证（官方来源）

---
### 更新记录 #1
- **更新时间**：2026-04-19
- **更新类型**：风险预警指标专项更新
- **内容摘要**：搜索了3个风险相关关键词，建议关注金税四期最新预警指标变化。
- **发现来源**：联网搜索
- **验证状态**：待验证
