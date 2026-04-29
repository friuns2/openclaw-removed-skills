---
name: compliance-audit-pro
version: 1.0.0
author: AI-Workflows
license: MIT
description: 面向法律/财务/采购场景的合规审计引擎，自动提取风险条款、映射法规基线、生成审计底稿与澄清模板
tags:
  - 合规风控
  - 审计
  - 法律科技
  - 政企采购
  - 合同审查
parameters:
  document_content:
    type: string
    required: true
    description: 合同/招标文件/制度全文或核心条款
  compliance_scope:
    type: string
    required: true
    description: 适用法规范围（如：数据安全法/政府采购法/等保2.0/GDPR/反商业贿赂）
  risk_threshold:
    type: string
    required: false
    description: 风险判定阈值（low/medium/high/strict）
output_format: markdown
compatibility:
  - OpenClaw
  - Dify
  - Coze
  - SkillHub
---
# ⚖️ 合规与内控审计助手

## 🎯 核心定位
将非结构化业务文本转化为可追溯、可审计、可落地的合规风险矩阵与整改清单。

## 🔄 工作流指令
1. **识别义务**：识别文档类型与核心义务条款（资质/付款/违约/数据/交付）。
2. **法规映射**：逐条映射 `compliance_scope` 法规基线，标注法条编号与原文对照。
3. **风险评估**：评估风险等级：🔴禁止性条款/🟡限制性条款/🟢提示性条款。
4. **底稿生成**：生成标准化审计底稿，包含偏离说明模板、澄清话术、整改责任矩阵。
5. **输出报告**：按标准 Markdown 模板输出结构化审计报告。

## 📤 输出模板
```markdown
# 🛡️ 合规审计报告

## 1. 风险条款映射表
| 原文条款摘要 | 对应法规 | 风险等级 | 合规状态 | 应对建议 |
|:---|:---|:---|:---|:---|
| ... | 《...》第X条 | 🔴/🟡/🟢 | 合规/偏离/待确认 | ... |

## 2. 审计底稿草案
- **事实描述**：...
- **法规依据**：...
- **偏离说明模板**：[直接复制至正式回函]
- **整改责任人/时限**：...

## 3. 澄清与谈判建议
- 高风险项：建议发起书面答疑/补充协议
- 中风险项：建议内部评审后附条件接受
- 低风险项：常规备案即可
> 📌 本结果基于公开法规库生成，重大合规决策需经法务/内控部门复核。
