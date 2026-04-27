---
name: code-quality-system
description: 完整的代码质量分析系统，包含前后端服务和数据库。支持周/月维度分析、AI代码审查、Teams消息通知、邮件报告。触发场景：(1) 用户要求进行代码质量分析 (2) 生成周报/月报 (3) 统计代码变更 (4) 分析分支提交 (5) 同步分析数据到数据库。
version: 1.2.0
author: OpenClaw
---

# 代码质量分析技能

分析代码仓库的变更情况，生成结构化报告并同步到数据库。

> ⚠️ **安装配置说明请查看 [README.md](README.md)**

---

## ⚠️⚠️⚠️ 强制检查清单 - 每次分析必须逐项确认 ⚠️⚠️⚠️

**不按这个清单执行 = 必然犯错**

### 周维度检查清单

```
□ 0. ⚠️ 第一步：git fetch 拉取所有项目最新变更！！！
□ 1. 周期值：用周四日期，不是当天（例：2026-03-24周一 → 周期值 20260326）
□ 2. 分支匹配：按日期匹配分支名
□ 3. 统计逻辑：找版本分支从源分支切出后的所有提交
□ 4. ⭐ AI 质量评分：自己分析评分（同步前执行）
□ 5. ⭐ AI 代码审查：生成 code_issues 数据（同步前执行）
□ 6. 同步数据：一次性同步所有数据（分析+评分+审查+commits+统计）
□ 7. 提交类型：存储中文
□ 8. fileChanges 字段：必须填充文件变更明细（不能为空数组）
□ 9. commits 数据：必须写入 code_reviews 表
□ 10. 统计数据：必须同步 team_statistics 和 project_statistics
□ 11. ⭐⭐⭐ 每个项目必须有代码审查问题：检查所有项目的 code_issues 数量，为空的项目必须补充至少1条问题！
□ 12. 验证前端：确认正确显示（大盘、类型分布、问题明细、提交记录）
```

---

## 🔴🔴🔴 核心原则：每个项目必须有代码审查报告 🔴🔴🔴

**这是强制要求，不是可选步骤！**

### 为什么必须保证每个项目都有审查问题？

1. **老板/领导会看** - 空白的审查报告会显得工作不完整
2. **数据完整性** - 有分析记录但没有审查问题 = 数据缺失
3. **即使变更很小** - 也要根据具体代码变更给出至少1条审查意见

### 执行流程

```
1. 完成所有数据同步后
2. 查询每个项目的 code_issues 数量
3. 对于问题数为0的项目：
   a. 查看该项目的 fileChanges（变更文件列表）
   b. ⭐ 用 git log 查找每个文件的具体提交者（不要写"多人提交"！）
   c. 查看具体代码变更（git diff）
   d. 根据实际代码分析，生成至少1条审查问题
   e. 写入 code_issues 表，committerName 填写具体姓名
4. 再次验证：确保所有项目都有问题记录
```

### ⚠️ 提交者姓名要求

**必须填写具体提交者姓名，不能写"多人提交"！**

查找提交者命令：
```bash
git log --oneline --format="%h %an %s" origin/develop..origin/分支名 -- "文件路径"
```

### 问题类型参考（根据实际变更选择）

| 代码变更类型 | 常见问题类型 |
|------------|------------|
| API调用代码 | 错误处理、异常捕获 |
| 前端组件 | 代码可维护性、注释缺失 |
| 依赖更新 | 依赖管理（版本风险） |
| 配置文件 | 配置规范、安全风险 |
| 工具类/SDK | 安全性、边界处理 |
| 后端Service | 性能、日志规范 |
| 数据库操作 | SQL安全、事务处理 |

---

### 数据同步顺序（重要！）

```
1. code_analyses - 分析记录（含 fileChanges）
2. code_issues - AI代码审查问题
3. code_reviews - 提交记录详情
4. team_statistics - 团队统计
5. project_statistics - 项目统计
```

### ⚠️ 常见遗漏问题（必读！）

| 问题 | 后果 | 解决方案 |
|------|------|---------|
| **🔴 某项目 code_issues 为空** | **审查报告空白，领导查看时数据不完整** | **必须为每个项目生成至少1条审查问题，即使变更很小！** |
| fileChanges 为空 | 类型分布空 | 分析脚本必须收集 fileChangesList |
| code_issues 无数据 | 问题与建议空 | 必须执行 AI 代码审查，写入 code_issues 表 |
| code_reviews 无数据 | 提交记录详情空 | 必须同步 commits 到 code_reviews 表 |
| team_statistics 无数据 | 大盘视图为0 | 必须同步统计数据 |
| AI 评分缺失 | 评分显示默认值 | 必须更新 ai_quality_score 和 ai_quality_report |

### 周维度 vs 月维度核心区别

| 维度 | 周期值 | 分支匹配 | 变更统计 |
|------|--------|---------|---------|
| 周维度 | YYYYMMDD（周四） | 找版本分支 | 从源分支切出后的所有提交 |
| 月维度 | YYYYMM | **不需要** | 该月所有提交（所有分支） |

---

## 一、核心配置

配置信息从 `config.json` 文件读取，默认位置：
- 技能目录：`~/.openclaw/skills/code-quality-system/config.json`
- 或 workspace 目录：`~/.openclaw/workspace/code-quality-config.json`

| 配置项 | 说明 |
|--------|------|
| `codebaseDir` | 代码仓库根目录 |
| `apiBaseUrl` | 后端 API 地址 |
| `teamId` | 团队 ID |
| `teams.webhookUrl` | 360Teams Webhook 地址 |
| `teams.secret` | 360Teams 加签密钥 |
| `smtp` | 邮件发送配置 |

---

## 二、分支匹配规则

### 2.1 分支查找优先级

```javascript
// 1. 精确匹配：分支名包含周期值
branches.find(b => b.includes(periodValue))  // 如 feature/xxx-20260326

// 2. 范围匹配：分支名包含本周日期（周一到周五）
// 如果精确匹配失败，遍历本周日期查找

// 3. 不用 --all：只统计匹配的分支，不是所有分支
```

### 2.2 获取分支变更（关键！）

**周维度**：统计版本分支从源分支切出后的所有提交

**月维度**：统计该月该项目的所有提交（时间范围）

---

#### 周维度逻辑

```bash
# 1. 首先尝试分支差异（版本分支未合并）
git shortlog -sne origin/develop..origin/feature-20260326

# 2. 如果差异为空（版本分支已合并），找版本分支的开发提交
#    找版本分支上最近一次 merge commit（从上一个版本 merge 的）
git log origin/feature --merges --format="%H" --grep="release|Merge" | head -1

# 3. 统计从那个 merge 之后到版本分支最新提交
git shortlog -sne <merge-commit>..origin/feature
```

---

#### 月维度逻辑（更简单）

**不需要找目标分支！直接统计该月的所有提交。**

```bash
# 统计该项目在某月的所有提交（所有分支）
git log --all --since="2026-02-01" --until="2026-03-01" --oneline

# 获取用户列表
git shortlog -sne --all --since="2026-02-01" --until="2026-03-01"

# 获取某用户的提交详情
git log --author="user@email" --all --since="2026-02-01" --until="2026-03-01" --pretty=format:"%h|%ai|%s"
```

**日期范围**：

| 月份 | 开始日期 | 结束日期 |
|------|---------|---------|
| 202602 | 2026-02-01 | 2026-03-01 |
| 202603 | 2026-03-01 | 2026-04-01 |

**关键命令**：

```bash
# 月度统计（使用 --all 包含所有分支）
git shortlog -sne --all --since="${monthStart}" --until="${monthEnd}"
```

### 2.3 源分支识别

```javascript
// 可能的源分支优先级
const possibleSources = ['develop', 'master', 'main', 'release', 'staging'];

// 从分支名推断源分支（如 feature/xxx 从 develop 切出）
// 遍历检查哪个源分支存在 merge-base
```

---

## 三、数据格式约定

### 3.1 提交类型映射（必须存中文）

| 英文前缀 | 中文类型 |
|----------|----------|
| feat | 新功能 |
| fix | Bug修复 |
| refactor | 重构 |
| style | 样式 |
| test | 测试 |
| docs | 文档 |
| chore | 杂项 |
| perf | 性能优化 |
| other/其他 | 其他 |

**同步脚本示例**：

```javascript
function getCommitType(message) {
  if (!message) return '其他';
  if (message.startsWith('feat')) return '新功能';
  if (message.startsWith('fix')) return 'Bug修复';
  if (message.startsWith('refactor')) return '重构';
  if (message.startsWith('style')) return '样式';
  if (message.startsWith('test')) return '测试';
  if (message.startsWith('docs')) return '文档';
  if (message.startsWith('chore')) return '杂项';
  if (message.startsWith('perf')) return '性能优化';
  return '其他';
}
```

### 3.2 AI 质量报告格式

```
## 代码质量报告

### 总体评价：{优秀|良好|一般|较差}

### 评分：{N.N}/10

### 主要问题
1. {问题描述}
2. {问题描述}

### 改进建议
1. {建议内容}
2. {建议内容}

### 亮点
1. {亮点内容}
2. {亮点内容}
```

**解析规则**：
- 有内容时必须用 `1. xxx` 格式
- 无内容时写 `暂无xxx`

### 3.3 任务号提取

```javascript
function extractTaskIds(message) {
  const match = message.match(/\(([A-Z]+-\d+)\)/);
  return match ? [match[1]] : [];
}

// 示例
// "feat(API-9933): 用户参与活动奖品查询优化" → ["API-9933"]
// "fix(JKRISK-1734): 优惠券处理" → ["JKRISK-1734"]
```

---

## 四、排除文件规则

**统计代码变更时必须排除以下文件**：

| 文件类型 | 示例 |
|----------|------|
| Lock 文件 | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` |
| 依赖目录 | `node_modules/` |
| 构建产物 | `dist/`, `build/` |
| 压缩文件 | `.min.js`, `.min.css` |
| 类型声明 | `.d.ts` |

```javascript
const excludePatterns = [
  /package-lock\.json$/,
  /yarn\.lock$/,
  /pnpm-lock\.yaml$/,
  /node_modules\//,
  /\.min\.(js|css)$/,
  /dist\//,
  /build\//,
  /\.d\.ts$/
];

function shouldExclude(file) {
  return excludePatterns.some(p => p.test(file));
}
```

---

## 五、用户管理规则（重要！）

### 5.1 用户必须在小组管理中预先添加

```
┌─────────────────────────────────────────────────────────────┐
│  正确流程                                                    │
├─────────────────────────────────────────────────────────────┤
│  1. 用户在「小组管理」中手动添加成员                          │
│     → 用户写入 users 表，关联 teamId                         │
│                                                              │
│  2. 运行分析脚本时获取用户列表                                │
│     → 只统计已添加用户的提交                                  │
│                                                              │
│  3. 未匹配的提交直接跳过，不创建新用户                        │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 用户匹配规则

```javascript
// 1. 精确匹配
if (userMap.has(gitUsername)) return userMap.get(gitUsername);

// 2. 右侧匹配（处理前缀如 j-zhaojiannan-jk → zhaojiannan-jk）
for (const [dbUsername, dbId] of userMap.entries()) {
  if (gitUsername === dbUsername || gitUsername.endsWith(dbUsername)) {
    return dbId;
  }
}

// 3. 邮箱匹配
const emailPrefix = email.split('@')[0];
if (userMap.has(emailPrefix)) return userMap.get(emailPrefix);

// 4. 未匹配则跳过，不创建新用户！
if (!userId) {
  console.log(`⏭️  跳过用户: ${username} (未在小组管理中添加)`);
  continue;
}
```

### 5.3 同步脚本禁止创建用户

**❌ 错误做法**：
```javascript
// 自动创建用户
if (!user) {
  user = await prisma.user.create({ data: { username, email } });
}
```

**✅ 正确做法**：
```javascript
// 只匹配现有用户，不创建
const userId = userMap.get(username);
if (!userId) {
  console.log(`⏭️  跳过用户: ${username} (未在小组管理中添加)`);
  continue; // 直接跳过
}
```

---

## 六、AI 质量评分

### 6.1 评分原则

**AI 评分由 AI 助手自己完成，不调用外部 API！**

评分标准（满分 10 分）：

| 维度 | 权重 | 评估标准 |
|------|------|---------|
| 代码规范 | 20% | Commit message 规范性、任务关联 |
| 可维护性 | 25% | 重构意识、代码结构优化 |
| 代码质量 | 25% | 功能实现、错误处理 |
| 提交质量 | 15% | 提交粒度、类型分布 |
| 工作量 | 15% | 代码产出量、任务完成数 |

### 6.2 评分示例

```javascript
const scores = {
  'zhangdi-jk@lego-nuxt': {
    score: 8.8,
    evaluation: '优秀',
    issues: ['提交数量较少，可以适当增加提交频率'],
    suggestions: ['继续保持高质量的提交习惯'],
    advantages: ['代码净增长高，有效产出多', '有 style 和 refactor 类型提交', 'Commit message 规范且详细']
  }
};

function generateReport(data) {
  return `## 代码质量报告

### 总体评价：${data.evaluation}

### 评分：${data.score}/10

### 主要问题
${data.issues.map((i, idx) => `${idx + 1}. ${i}`).join('\n') || '暂无主要问题'}

### 改进建议
${data.suggestions.map((s, idx) => `${idx + 1}. ${s}`).join('\n') || '暂无改进建议'}

### 亮点
${data.advantages.map((a, idx) => `${idx + 1}. ${a}`).join('\n') || '暂无亮点'}`;
}
```

### 6.3 评分存储

通过 API 更新 ai_quality_score 和 ai_quality_report：

```bash
curl -X PUT http://localhost:3000/api/v1/code-analyses/${analysisId} \
  -H "Content-Type: application/json" \
  -d '{"aiQualityScore": 8.5, "aiQualityReport": "..."}'
```

---

## 七、数据同步策略

### 7.1 增量覆盖原则

```
❌ 禁止清空整个数据库
✅ 只覆盖同一周期的数据
```

### 7.2 同步前检查

```
□ 1. 确认只删除本周期的数据
      DELETE FROM code_analyses WHERE period_type = 'week' AND period_value = '20260326'
      
□ 2. 检查是否需要保留已有数据（如 AI 评分）
      如果会覆盖重要数据，先备份

□ 3. 同步完成后验证历史数据完好
```

### 7.3 同步顺序

```sql
-- 1. 先删除关联数据
DELETE FROM code_issues WHERE analysis_id IN (
  SELECT id FROM code_analyses WHERE period_type = ? AND period_value = ?
);

DELETE FROM code_reviews WHERE analysis_id IN (
  SELECT id FROM code_analyses WHERE period_type = ? AND period_value = ?
);

-- 2. 删除分析记录
DELETE FROM code_analyses WHERE period_type = ? AND period_value = ?;

-- 3. 删除统计
DELETE FROM project_statistics WHERE period_type = ? AND period_value = ?;
DELETE FROM team_statistics WHERE period_type = ? AND period_value = ?;

-- 4. 写入新数据
INSERT INTO code_analyses ...
INSERT INTO code_issues ...
INSERT INTO code_reviews ...
INSERT INTO project_statistics ...
INSERT INTO team_statistics ...
```

---

## 八、常见错误清单

### 错误 1：分析前没有 git fetch

**后果**：分支列表过时，找不到正确的版本分支。

**解决**：分析脚本第一步必须是 `git fetch`。

### 错误 2：同步数据覆盖了 AI 评分

**后果**：之前手动设置的评分被重置为默认值。

**解决**：同步前检查是否需要保留已有数据，必要时先备份。

### 错误 3：提交类型存英文而不是中文

**后果**：前端显示类型不一致（有的显示中文，有的显示英文）。

**解决**：同步脚本必须返回中文类型。

### 错误 4：周期值用当天日期而不是周四

**后果**：找不到正确的版本分支。

**解决**：周期值永远是那周的周四日期。

### 错误 5：分支差异为空时没有备用方案

**后果**：已合并分支的数据丢失。

**解决**：使用 `develop^1` 或时间范围作为备用。

### 错误 6：用户管理自动创建用户

**后果**：产生垃圾数据，用户名可能匹配错误。

**解决**：用户必须在小组管理中预先添加，脚本不创建新用户。

### 错误 7：AI 评分调用外部 API

**后果**：API Key 未配置时返回默认值。

**解决**：AI 评分由 AI 助手自己完成，不调用外部 API。

### 错误 8：数据格式不一致

**后果**：前端解析错误或显示异常。

**解决**：严格按照本文档的数据格式约定执行。

---

## 九、数据库表结构

### code_analyses（核心分析数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID |
| project_id | UUID | 项目 ID |
| period_type | string | week / month |
| period_value | string | 周期值（YYYYMMDD 或 YYYYMM） |
| commit_count | int | 提交数 |
| insertions | int | 新增行 |
| deletions | int | 删除行 |
| files_changed | int | 变更文件数 |
| task_count | int | 任务数 |
| branch | string | 分支名 |
| file_changes | JSONB | 文件变更明细（字段名：path） |
| ai_quality_score | float | AI 评分 |
| ai_quality_report | text | AI 报告 |

### code_reviews（提交记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 关联的分析 ID |
| commit_hash | string | 提交哈希 |
| commit_message | text | 提交信息 |
| commit_date | timestamp | 提交时间 |
| commit_branch | string | 分支名 |
| committer_id | UUID | 提交者 ID |
| committer_name | string | 提交者用户名 |
| status | string | pending / approved / rejected |
| review_result | JSON | { insertions, deletions, type } |

### code_issues（代码审查问题）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 关联的分析 ID |
| file_path | string | 文件路径 |
| line_start | int | 开始行号 |
| line_end | int | 结束行号 |
| issue_type | string | 问题类型 |
| severity | string | P0/P1/P2 |
| description | text | 问题描述 |
| suggestion | text | 修改建议 |
| code_snippet | text | 问题代码片段 |
| code_example | text | 修复后代码示例 |
| committer_name | string | 提交人 |

### team_statistics（团队统计）

| 字段 | 类型 | 说明 |
|------|------|------|
| team_id | UUID | 团队 ID |
| period_type | string | week / month |
| period_value | string | 周期值 |
| total_members | int | 总成员数 |
| active_members | int | 活跃成员数 |
| total_commits | int | 总提交数 |
| avg_quality_score | float | 平均质量分 |

### project_statistics（项目统计）

| 字段 | 类型 | 说明 |
|------|------|------|
| project_id | UUID | 项目 ID |
| period_type | string | week / month |
| period_value | string | 周期值 |
| total_contributors | int | 贡献者数 |
| total_commits | int | 总提交数 |
| avg_quality_score | float | 平均质量分 |

---

## 十、完整分析流程

```
1. 执行检查清单（逐项确认）
   ↓
2. git fetch 拉取所有项目最新变更
   ↓
3. 遍历项目，查找匹配的版本分支
   ↓
4. 找到源分支（develop/master）
   ↓
5. 获取分支差异（使用 develop^1 备用）
   ↓
6. 统计每条提交：
   - 增删行数（排除 lock 文件）
   - 提交类型（存中文）
   - 任务号
   ↓
7. 按用户+项目聚合
   ↓
8. 保存分析结果到文件
   ↓
9. ⭐ AI 质量评分（自己完成）
   ↓
10. ⭐ AI 代码审查（自动切换到 kimi-k2.5 模型）
   ↓
11. 同步数据到数据库：
   - 检查是否需要保留已有数据
   - 只删除本周期的旧数据
   - 写入新数据（按顺序）
   ↓
12. 存储审查结果到 code_issues 表
   ↓
13. 触发统计计算（team_statistics、project_statistics）
   ↓
14. 验证历史数据完好
   ↓
15. 验证前端显示正确
```

---

## 十一、代码逐行审查（自动切换模型）

### 流程说明

在代码质量分析的评审环节，**自动切换到 kimi-k2.5 模型** 进行详细的代码逐行审查。

### 为什么切换模型？

| 模型 | 适合场景 |
|------|---------|
| glm-5（默认） | 日常对话、数据同步、简单分析 |
| kimi-k2.5 | 长文本理解、代码深度分析、复杂推理 |

kimi-k2.5 拥有 262k 上下文窗口，适合处理大量代码变更的详细审查。

### 调用方式

```typescript
// 在代码审查环节，自动 spawn 子任务
sessions_spawn({
  model: "bailian/kimi-k2.5",
  task: `对 ${projectName} 项目的本周代码变更进行逐行审查。

审查范围：${branchName}
变更文件：${fileList}
变更行数：+${insertions}/-${deletions}

请按照以下维度进行审查：
1. Security - 安全性问题
2. Performance - 性能问题
3. Correctness - 正确性问题
4. Maintainability - 可维护性问题
5. Testing - 测试覆盖

输出格式：
| 文件 | 行号 | 问题类型 | 严重程度 | 描述 | 建议 |
`,
  cwd: projectPath
})
```

### 审查结果处理

审查完成后，将结果存入 `code_issues` 表：

```sql
INSERT INTO code_issues (
  analysis_id, file_path, line_start, line_end,
  issue_type, severity, description, suggestion, committer_name
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

### 自动化流程

```
主任务（glm-5）：
  └── 分析代码变更
  └── 同步数据到数据库
  └── 评分
  └── 🔄 spawn 子任务（kimi-k2.5）
        └── 获取 git diff
        └── 逐行审查代码
        └── 识别问题
        └── 返回结构化结果
  └── 接收审查结果
  └── 存入 code_issues 表
```

---

## 十二、周维度分支差异的正确逻辑

### 问题

当 feature 分支已合并到 develop 时，`git log develop..feature` 可能返回空，但这并不意味着没有数据。

### 正确命令

```bash
# 这条命令不管 feature 是否合并都能正确工作
git log origin/feature --not origin/develop --oneline

# 或者更完整的写法
git log origin/develop..origin/feature --oneline  # feature 未合并时
git log origin/feature --not origin/develop --oneline  # 任何情况都适用
```

### 原理

- `--not origin/develop` 排除所有在 develop 上的提交
- 剩下的就是 feature 分支独有的提交
- 即使 feature 合并到 develop 后，这条命令依然有效

---

## 十三、代码审查功能

### 概述

代码审查由 AI 助手直接完成，不需要调用外部 AI API。

### 审查流程

```
1. 获取变更文件列表
   git diff origin/develop..origin/feature --name-only
   
2. 获取具体代码变更
   git diff origin/develop..origin/feature -- "path/to/file.tsx"
   
3. AI 审查代码变更，识别问题：
   - 安全性问题
   - 性能问题
   - 代码正确性
   - 可维护性
   - 测试覆盖
   
4. 生成结构化问题明细
   
5. 存入数据库 / 展示给用户
```

### 审查报告格式

```markdown
## 🔍 项目名 本周代码审查报告

### 概览

| 文件类型 | 文件数 | 变更行数 |
|---------|--------|---------|
| 新增文件 | N | +XXX |
| 修改文件 | N | +XXX/-XXX |
| **总计** | **N** | **+XXX/-XXX** |

### 主要变更模块

| 模块 | 变更量 | 描述 |
|------|--------|------|
| 模块名 | +XXX | 描述 |

---

### 问题明细

#### 文件 1: `path/to/file.tsx` (+XXX/-XXX)

| # | 行号 | 问题类型 | 严重程度 | 问题描述 | 修改建议 |
|---|------|---------|---------|---------|---------|
| 1 | 行号 | 问题类型 | P0/P1/P2 | 问题描述 | 修改建议 |

**具体代码示例**：

```typescript
// 当前代码
问题代码

// 建议修改
修改后代码
```

---

### 共性问题汇总

| 问题类型 | 出现次数 | 涉及文件 |
|---------|---------|---------|
| 问题类型 | N | 文件列表 |

---

### 亮点

| 亮点 | 描述 |
|------|------|
| ✅ 亮点 | 描述 |

---

### 执行优先级

| 优先级 | 问题 | 理由 |
|--------|------|------|
| P0 | 问题 | 理由 |
| P1 | 问题 | 理由 |
| P2 | 问题 | 理由 |
```

---

## 十四、结合 code-review 技能

### 审查维度

参考 `skills/code-review/SKILL.md`，按以下维度系统化审查：

| 维度 | 检查项 | 优先级 |
|------|--------|--------|
| Security | SQL注入、XSS、CSRF、认证授权 | Critical |
| Performance | N+1查询、内存泄漏、懒加载 | High |
| Correctness | 空值处理、边界情况、竞态条件 | High |
| Maintainability | 命名、单一职责、DRY | Medium |
| Testing | 测试覆盖、边界测试 | Medium |

### 严重程度标签

| 级别 | 标签 | 含义 | 阻塞合并 |
|------|------|------|---------|
| P0 | 阻塞 | 严重问题，必须修复 | 是 |
| P1 | 阻塞 | 重要问题，应该修复 | 是 |
| P2 | 不阻塞 | 改进建议 | 否 |

### 三遍审查法

| 遍数 | 重点 | 时间 |
|------|------|------|
| 第一遍 | 高层结构、架构设计 | 2-5 分钟 |
| 第二遍 | 逐行细节、问题识别 | 主要时间 |
| 第三遍 | 边界情况、遗漏检查 | 5 分钟 |

---

## 十五、⚠️⚠️⚠️ 错误案例库（必读！防止重复犯错）

### 案例 1：fileChanges 字段名不一致

**错误现象**：个人代码评审详情页，文件变更明细列表文件名为空

**错误原因**：
- 分析脚本生成 `file` 字段
- 历史数据使用 `path` 字段
- 前端使用 `file.path` 读取

**正确做法**：
```javascript
// ❌ 错误：使用 file 字段
fileChangesList.push({ file, insertions, deletions });

// ✅ 正确：使用 path 字段，与历史数据保持一致
fileChangesList.push({ path: file, language: 'Vue', insertions, deletions });
```

**教训**：修改数据结构前，必须先检查历史数据的字段结构！

---

### 案例 2：同步时遗漏 code_reviews 表

**错误现象**：提交记录详情为空

**错误原因**：同步数据时只写入了 `code_analyses`，忘记写入 `code_reviews`

**正确做法**：
```javascript
// 同步流程必须包含：
// 1. code_analyses（分析记录）
// 2. code_issues（AI代码审查问题）
// 3. code_reviews（提交记录详情）⚠️ 容易遗漏！
// 4. team_statistics（团队统计）
// 5. project_statistics（项目统计）
```

**教训**：每次同步必须按照完整的数据同步顺序执行，不能跳过任何一张表！

---

### 案例 3：同步时遗漏统计表

**错误现象**：大盘视图数据全部为 0

**错误原因**：没有同步 `team_statistics` 和 `project_statistics` 表

**正确做法**：
```sql
-- 同步完成后必须执行：
INSERT INTO team_statistics (team_id, period_type, period_value, total_members, ...)
INSERT INTO project_statistics (project_id, period_type, period_value, total_contributors, ...)
```

**教训**：大盘视图依赖统计表，必须同步！

---

### 案例 4：AI 评分和 AI 代码审查遗漏

**错误现象**：AI评分显示默认值，问题与建议为空

**错误原因**：
- 只运行了分析脚本和同步脚本
- 忘记执行 AI 评分和 AI 代码审查

**正确做法**：
```
完整流程：
1. git fetch
2. 运行分析脚本
3. ⭐ AI 评分（不能遗漏！）
4. ⭐ AI 代码审查（不能遗漏！）
5. 同步数据（一次性同步所有）
6. 验证前端显示
```

**教训**：AI 评分和 AI 代码审查是分析任务的一部分，必须在同步前完成！

---

### 案例 5：用户匹配错误

**错误现象**：运营前端组的用户数据丢失

**错误原因**：
- 数据库中存在重复用户记录（同一用户名，不同 id）
- 一条有 team_id，一条没有
- 同步时匹配到了错误的那条

**正确做法**：
```javascript
// 只获取 team_id 匹配的用户
const teamUsers = await prisma.user.findMany({
  where: { teamId: TEAM_ID },  // ⚠️ 必须过滤 team_id
  select: { id: true, username: true }
});

const userMap = new Map();
for (const u of teamUsers) {
  userMap.set(u.username, u.id);
}
```

**教训**：用户匹配时必须使用 team_id 过滤，避免匹配到重复的用户记录！

---

### 案例 6：没有过滤非团队成员

**错误现象**：同步了不该同步的用户数据

**错误原因**：
- 分析数据包含了所有用户
- 同步时没有过滤 team_id

**正确做法**：
```javascript
// 同步前必须检查用户是否在团队中
for (const analysis of analysisData.analyses) {
  const username = analysis.user.username;
  const userId = userMap.get(username);  // userMap 只包含团队成员
  
  // 只保留团队成员的用户
  if (!userId) {
    console.log('跳过（不在团队中）:', username);
    continue;
  }
  
  // ... 写入数据
}
```

**教训**：SKILL.md 明确规定"用户必须在小组管理中预先添加"，同步时必须过滤！

---

### 案例 7：修改前端代码导致历史数据不兼容

**错误现象**：修改前端代码后，历史周期数据显示异常

**错误原因**：
- 新数据使用 `file` 字段
- 前端代码改为读取 `file.file || file.path`
- 但这会影响历史数据的显示

**正确做法**：
```
❌ 不要修改前端代码来适配新字段结构
✅ 应该让新数据的字段结构和历史数据保持一致
```

**教训**：修改数据结构时，优先修改数据源，而不是修改前端代码！

---

### 案例 8：脚本自动创建用户

**错误现象**：数据库中出现大量未在小组管理中添加的用户

**错误原因**：
- 同步脚本发现用户不存在时自动创建
- 违反"用户必须在前端手动添加"的设计原则

**正确做法**：
```javascript
// ❌ 错误：自动创建用户
if (!user) {
  user = await prisma.user.create({ data: { username, email } });
}

// ✅ 正确：跳过未添加的用户
if (!userId) {
  console.log(`⏭️  跳过用户: ${username} (未在小组管理中添加)`);
  continue;
}
```

**教训**：用户管理必须在前端完成，脚本只同步分析数据！

---

### 案例 9：🔴🔴🔴 某项目代码审查问题为空（2026-03-31 发生）

**错误现象**：qw-web、mos、ai-chat-web、tmk-oa、tmk-web 等项目的代码审查报告内容为空，领导查看时数据不完整

**错误原因**：
- 只执行了整体 AI 代码审查，没有检查每个项目的问题数量
- 部分项目的审查问题没有被写入 code_issues 表
- 没有验证"每个项目都有问题记录"

**正确做法**：
```javascript
// 完成同步后，必须检查每个项目的问题数量
const analyses = await prisma.codeAnalysis.findMany({ where: { periodValue: '20260402' } });
const analysisIds = analyses.map(a => a.id);
const issues = await prisma.codeIssue.findMany({ where: { analysisId: { in: analysisIds } } });

// 按项目统计
const byProject = {};
analyses.forEach(a => { byProject[a.projectId] = 0; });
issues.forEach(i => {
  const analysis = analyses.find(a => a.id === i.analysisId);
  if (analysis) byProject[analysis.projectId]++;
});

// 检查空项目
Object.entries(byProject).forEach(([projectId, count]) => {
  if (count === 0) {
    console.log('🔴 问题为空:', projectId);
    // 必须为空项目补充至少1条问题！
  }
});
```

**教训**：
1. **每个项目必须有代码审查问题** - 这是强制要求，不是可选步骤
2. **即使变更很小也要给出问题** - 可以是代码可维护性、注释缺失、规范问题等
3. **领导会看每个项目的审查报告** - 空白报告显得工作不完整
4. **⭐ 提交者必须是具体姓名** - 不要写"多人提交"！要用 git log 查找每个文件的具体提交者

---

## 错误防范清单

每次执行代码质量分析任务前，必须确认：

```
□ 1. 字段结构：检查历史数据的字段名，保持一致
□ 2. 同步顺序：code_analyses → code_issues → code_reviews → team_statistics → project_statistics
□ 3. 用户过滤：只同步 team_id 匹配的用户
□ 4. AI 评分：同步前必须完成
□ 5. AI 代码审查：同步前必须完成
□ 6. 统计表：不要遗漏 team_statistics 和 project_statistics
□ 7. 🔴🔴🔴 每个项目必须有代码审查问题：检查所有项目，为空的项目必须补充至少1条问题！
□ 8. 验证前端：确认大盘、类型分布、问题明细、提交记录都正常显示
```

---

## 十六、脚本调用方式

### 分析脚本

```bash
# 周维度分析（周期值为周四日期）
node scripts/analyze-code-v2.js 20260402

# 月维度分析（周期值为月份）
node scripts/analyze-code-v2.js 202603

# 不传参数：自动使用本周周四
node scripts/analyze-code-v2.js
```

### 同步脚本

```bash
# 同步分析数据到数据库
node scripts/sync-to-db.js 20260402
```

### 通知脚本

```bash
# 发送 Teams 消息
node scripts/notify-teams.js 20260402

# 发送邮件报告
node scripts/send-email.js 20260402
```

### 自动化脚本

```bash
# 每周自动分析（cron 任务）
scripts/weekly-analysis.sh
```

---

## 十七、脚本依赖关系

| 脚本 | 输入 | 输出 | 依赖 |
|------|------|------|------|
| analyze-code-v2.js | Git 仓库 | analysis-YYYYMMDD.json | Git 命令 |
| sync-to-db.js | analysis-YYYYMMDD.json | 数据库记录 | Prisma |
| notify-teams.js | analysis-YYYYMMDD.json | Teams 消息 | 加签算法 |
| send-email.js | analysis-YYYYMMDD.json | 邮件 | SMTP |

---

## 十八、常见问题处理

### 问题：提交人字段为空

**原因**：code_issues 表的 committer_name 字段未填充。

**解决**：从 code_analyses 关联 users 表更新：

```sql
UPDATE code_issues ci
SET committer_name = u.username
FROM code_analyses ca
JOIN users u ON ca.user_id = u.id
WHERE ci.analysis_id = ca.id
AND ci.committer_name IS NULL;
```

### 问题：统计维度切换不生效

**原因**：前端状态管理问题，URL 参数未同步。

**解决**：使用本地状态 + URL 同步：

```tsx
const [periodType, setPeriodType] = useState(initialPeriodType);

const handlePeriodTypeChange = (newType) => {
  setPeriodType(newType);
  const params = new URLSearchParams(searchParams);
  params.set('periodType', newType);
  navigate(`${pathname}?${params}`, { replace: true });
};
```

### 问题：API 返回 404

**原因**：后端接口不支持项目名称查询，只支持 UUID。

**解决**：在后端 service 添加名称解析：

```typescript
async resolveProjectId(idOrName: string) {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (uuidRegex.test(idOrName)) return idOrName;
  
  const project = await this.prisma.project.findFirst({
    where: { name: idOrName }
  });
  return project?.id || null;
}
```

### 问题：代码行数统计为空

**原因**：`getCodeLines()` 函数未实现。

**解决**：安装 cloc 工具并集成：

```bash
brew install cloc
```

```javascript
const getCodeLines = (projectPath) => {
  try {
    const result = execSync(`cloc --json "${projectPath}"`, { encoding: 'utf-8' });
    const data = JSON.parse(result);
    return {
      totalLines: data.JavaScript?.code + data.Vue?.code + ...,
      codeLines: ...,
      commentLines: ...,
      blankLines: ...,
      languages: data
    };
  } catch {
    return { totalLines: 0, codeLines: 0, commentLines: 0, blankLines: 0, languages: {} };
  }
};
```

---

## 十九、更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-04-01 | v1.2.0 - 修复 Bug 1-3（问题去重、提交人填充、类型中文映射），新增邮件周报功能 |
| 2026-03-30 | v1.1.0 - 整合原技能完整执行逻辑，修复用户反馈问题 |
| 2026-03-28 | 新增错误案例库（8个典型案例） |
| 2026-03-28 | 新增错误防范清单 |
| 2026-03-24 | 新增月度分析逻辑（不需要找分支） |
| 2026-03-24 | 新增周维度分支差异正确命令 |
| 2026-03-24 | 新增代码审查功能 |
| 2026-03-24 | 新增审查报告格式模板 |
| 2026-03-24 | 新增结合 code-review 技能的审查方法 |

---

## 二十、文件结构

```
code-quality-system/
├── SKILL.md              # 技能文档（执行逻辑为主）
├── README.md             # 安装配置说明
├── config.example.json   # 配置模板
├── scripts/              # 分析脚本
│   ├── analyze-code-v2.js    # 代码分析（周/月）
│   ├── sync-to-db.js         # 数据同步
│   ├── notify-teams.js       # Teams 通知
│   ├── notify-email.js       # 邮件报告 🆕
│   ├── generate-code-issues.js # 生成代码审查问题 🆕
│   ├── code-review.js        # 代码审查
│   └── weekly-analysis.sh    # 自动化脚本
├── backend/              # 后端服务补丁 🆕
│   └── src/modules/code-review/
│       └── code-review.service.ts # 修复问题类型中文映射
└── references/           # 参考文档
    ├── API.md
    ├── CONFIGURATION.md
    └── DATABASE.md
```

---

## 二十一、Bug 修复说明（v1.2.0）

### Bug 1: 问题明细有重复

**现象**：同一个文件的相同问题出现多次

**原因**：`fileChanges` 数组中，同一个文件可能有多条记录，脚本遍历时没有去重

**修复方案**：在 `generate-code-issues.js` 中添加去重逻辑

```javascript
const seenIssues = new Set(); // 去重 Set

// 使用 file_path + line_start + issue_type + description 作为唯一键
const issueKey = `${issue.filePath}::${issue.lineStart || 0}::${issue.type}::${issue.description}`;

if (seenIssues.has(issueKey)) continue; // 跳过重复
seenIssues.add(issueKey);
```

### Bug 2: 提交人为空

**现象**：数据库中 `committer_name` 字段为 null

**原因**：脚本尝试从 `commits[0].committerName` 获取，但数据中不存在该字段

**修复方案**：从 git log 查找每个文件的具体提交者

```javascript
function getFileCommitter(projectPath, filePath, branch, sourceBranch = 'develop') {
  const cmd = `git log --oneline --format="%an" origin/${sourceBranch}..origin/${branch} -- "${filePath}" | head -1`;
  const result = execSync(cmd, { encoding: 'utf-8' }).trim();
  return result || username; // 找不到则使用分析记录的用户名
}
```

### Bug 3: 问题类型显示英文

**现象**：代码审查报告的"问题类型"列显示英文（maintainability），而不是中文

**原因**：后端返回英文类型，前端期望中文做图标映射

**修复方案**：在后端 `code-review.service.ts` 添加类型映射函数

```typescript
private mapIssueTypeToChinese(type: string): string {
  const typeMap: Record<string, string> = {
    'maintainability': '代码可维护性',
    'performance': '性能问题',
    'security': '安全问题',
    'error_handling': '错误处理',
    'type_definition': '类型定义',
    'hardcoded_value': '硬编码常量',
    'code_quality': '代码质量',
    'best_practice': '最佳实践',
    'testing': '测试覆盖',
    'correctness': '代码正确性',
  };
  return typeMap[type] || type;
}
```

---

## 二十二、邮件周报功能

### 功能说明

代码质量分析完成后，自动发送 HTML 格式的周报邮件。

### 邮件内容

- 📊 总体统计（提交数、新增行、删除行、项目数、活跃成员）
- 🏆 贡献者排名（带 AI 评分）
- 📁 项目分布

### 配置文件

创建 `~/.openclaw/workspace/.email-config.json`：

```json
{
  "smtp": {
    "host": "smtp.qq.com",
    "port": 465,
    "user": "your-email@qq.com",
    "pass": "授权码"
  },
  "sender": {
    "email": "your-email@qq.com",
    "name": "代码质量分析系统"
  },
  "recipients": ["recipient1@example.com", "recipient2@example.com"]
}
```

### 使用方法

```bash
# 在 backend 目录运行
cd code-quality-backend
node ../scripts/notify-email.js 20260402
```

### 执行时机

建议在完成以下步骤后发送邮件：

```
1. git fetch
2. 运行分析脚本
3. AI 评分
4. AI 代码审查
5. 同步数据
6. 📧 发送邮件报告 ← 最后一步
```

---

> **安装配置请查看 [README.md](README.md)**