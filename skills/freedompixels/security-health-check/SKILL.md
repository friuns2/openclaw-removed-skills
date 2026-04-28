---
name: security-health-check
description: "检查邮箱泄露和密码强度，生成安全评分报告。"
metadata: {"openclaw": {"emoji": "🔒"}}
---

# Security Health Check

检查邮箱泄露和密码强度，生成安全评分。

## 功能
- 邮箱泄露检查（HIBP API查询）
- 密码泄露检查（k-匿名查询，密码不离开本地）
- 密码强度分析（本地计算，0-100分）
- 综合安全评分报告

## 用法
python3 scripts/security_check.py --email user@example.com
python3 scripts/security_check.py --password "test"
python3 scripts/security_check.py --email user@example.com --password "test"
python3 scripts/security_check.py --email user@example.com --report json

## 依赖
- Python 3.7+
- certifi（SSL证书验证）
- 可选：HIBP_API_KEY 环境变量（提升API速率限制）

## 数据来源
- haveibeenpwned.com（公开数据泄露数据库）
- 密码检查：仅发送SHA1前缀（k-匿名，不暴露密码）

## 版本
- v1.3.0: 文档优化，简化功能描述
