# 数据库设计

## 表结构

### teams（团队表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 团队名称 |
| description | TEXT | 描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名 |
| email | VARCHAR(100) | 邮箱 |
| team_id | UUID | 团队ID（外键） |
| git_username | VARCHAR(100) | Git用户名 |
| git_email | VARCHAR(100) | Git邮箱 |
| is_active | BOOLEAN | 是否活跃 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### projects（项目表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(200) | 项目名称 |
| repository | VARCHAR(500) | 仓库地址 |
| description | TEXT | 描述 |
| team_id | UUID | 团队ID（外键） |
| tech_stack | JSON | 技术栈 |
| is_active | BOOLEAN | 是否活跃 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### code_analyses（代码分析表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户ID（外键） |
| project_id | UUID | 项目ID（外键） |
| period_type | VARCHAR(20) | 周期类型（week/month） |
| period_value | VARCHAR(20) | 周期值 |
| commit_count | INTEGER | 提交数 |
| insertions | INTEGER | 新增行数 |
| deletions | INTEGER | 删除行数 |
| files_changed | INTEGER | 变更文件数 |
| task_count | INTEGER | 任务数 |
| branch | VARCHAR(200) | 分支名 |
| ai_quality_score | FLOAT | AI质量评分 |
| ai_quality_report | TEXT | AI质量报告 |
| commit_types | JSON | 提交类型统计 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### code_reviews（代码审查表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 分析ID（外键） |
| commit_hash | VARCHAR(100) | 提交哈希 |
| commit_message | TEXT | 提交信息 |
| commit_date | DATETIME | 提交日期 |
| commit_type | VARCHAR(50) | 提交类型 |
| insertions | INTEGER | 新增行数 |
| deletions | INTEGER | 删除行数 |
| files_changed | INTEGER | 变更文件数 |
| created_at | DATETIME | 创建时间 |

### code_issues（代码问题表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| analysis_id | UUID | 分析ID（外键） |
| file_path | VARCHAR(500) | 文件路径 |
| line_start | INTEGER | 起始行号 |
| line_end | INTEGER | 结束行号 |
| issue_type | VARCHAR(100) | 问题类型 |
| severity | VARCHAR(20) | 严重程度（P0/P1/P2） |
| description | TEXT | 问题描述 |
| suggestion | TEXT | 修改建议 |
| code_snippet | TEXT | 代码片段 |
| code_example | TEXT | 修复示例 |
| committer_name | VARCHAR(100) | 提交人 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 索引

```sql
-- 唯一约束
CREATE UNIQUE INDEX idx_code_analyses_unique 
ON code_analyses(user_id, project_id, period_type, period_value);

-- 查询优化
CREATE INDEX idx_code_analyses_period ON code_analyses(period_type, period_value);
CREATE INDEX idx_code_reviews_analysis ON code_reviews(analysis_id);
CREATE INDEX idx_code_issues_analysis ON code_issues(analysis_id);
```