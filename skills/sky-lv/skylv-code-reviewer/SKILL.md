---
name: code-reviewer
description: Code review assistant. Analyzes code quality, detects bugs and security issues, and suggests improvements. Triggers: code review, security audit, code quality, bug detection.
metadata: {"openclaw": {"emoji": "🔍"}}
---

# Code Reviewer — 代码审查助手

## 功能说明

对代码进行全面审查，发现问题和优化机会。

## 使用方法

### 1. 代码质量检查

```
用户: 审查这段代码的质量：
[粘贴代码]
```

审查维度：
- 代码结构
- 命名规范
- 注释完整性
- 函数复杂度
- 重复代码

### 2. 安全漏洞检查

```
用户: 检查这段代码是否有安全问题
```

检查项：
- SQL注入风险
- XSS漏洞
- 敏感信息硬编码
- 不安全的依赖
- 权限控制缺失

### 3. 性能优化建议

```
用户: 这段代码有什么性能问题？如何优化？
```

分析项：
- 时间复杂度
- 空间复杂度
- 不必要的循环
- 数据结构选择
- 缓存机会

### 4. 代码重构建议

```
用户: 这段代码如何重构使其更清晰？
```

重构方向：
- 提取函数
- 消除重复
- 简化条件
- 改善命名
- 添加类型注解

## 示例输出

```
代码审查报告

【质量问题】
1. 函数 `processData` 过长（85行），建议拆分
   - 提取数据验证逻辑
   - 提取数据转换逻辑

2. 变量命名不清晰
   - `temp` → 建议改为 `processedResult`
   - `flag` → 建议改为 `isValidUser`

【安全问题】
⚠️ 高危：SQL查询使用字符串拼接
   第23行: `query = "SELECT * FROM users WHERE id=" + userId`
   建议：使用参数化查询

【性能问题】
1. O(n²) 嵌套循环可优化为 O(n)
   第45-52行：使用 Map 替代数组查找

2. 重复计算
   第67行：`calculateTotal()` 在循环内重复调用
   建议：提取到循环外

【优化建议】
- 添加输入验证
- 使用 TypeScript 类型注解
- 添加单元测试
```

## 支持语言

- JavaScript / TypeScript
- Python
- Go
- Java
- C / C++
- Rust
