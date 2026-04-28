---
name: cms-cwork-workflow
description: 提供【工作协同】全流程执行能力。用户一旦表达“写汇报/发汇报/发周报/提交汇报/查看收件箱/查待办/任务协作/业务单元”等执行意图，必须进入本 Skill 的脚本调用流程；仅当用户明确是纯咨询（如问规则、问怎么做）时，才允许先文字说明并二次确认是否执行。本 Skill 通过依赖 `cms-auth-skills` 获取 `AppKey` 并完成鉴权后，才允许进入脚本调用链路。
skillcode: cms-cwork-workflow
github: https://github.com/xgjk/cwork-skills
dependencies:
  - cms-auth-skills
# bump 时须同步修改同目录下 version.json 的 version 字段
version: 1.0.12
tools_provided:
  - name: cwork_client
    category: exec
    risk_level: medium
    permission: exec
    description: CWork API共享客户端，封装HTTP请求、认证和所有业务API方法
    status: active
  - name: cwork-search-emp
    category: exec
    risk_level: low
    permission: read
    description: 搜索员工信息（支持模糊查询）
    status: active
  - name: cwork-send-report
    category: exec
    risk_level: medium
    permission: write
    description: 发送工作协同汇报（🚨限制：当你明确知道确切的人员姓名时才可使用；如果你不知道发给谁，绝对不要猜，立即停止使用此工具！）
    status: active
  - name: cwork-query-report
    category: exec
    risk_level: low
    permission: read
    description: 查询汇报（收件箱/发件箱/详情/历史）
    status: active
  - name: cwork-create-task
    category: exec
    risk_level: medium
    permission: write
    description: 创建工作计划/任务
    status: active
  - name: cwork-review-report
    category: exec
    risk_level: medium
    permission: write
    description: 审阅汇报（回复/标记已读）
    status: active
  - name: cwork-query-tasks
    category: exec
    risk_level: low
    permission: read
    description: 查询任务（我的/创建的/团队/详情）
    status: active
  - name: cwork-nudge-report
    category: exec
    risk_level: medium
    permission: write
    description: 催办闭环（识别未闭环/生成催办/发送）
    status: active
  - name: cwork-todo
    category: exec
    risk_level: medium
    permission: write
    description: 待办管理（查询/完成决策/建议/反馈）
    status: active
  - name: cwork-templates
    category: exec
    risk_level: low
    permission: read
    description: 查询汇报模板列表
    status: active
  - name: cwork-draft-box
    category: exec
    risk_level: high
    permission: write
    description: 草稿箱列表（5.24）与批量删除草稿（5.28）
    status: active
  - name: cwork-business-unit
    category: exec
    risk_level: medium
    permission: write
    description: 业务单元管理（创建/更新/查询/删除）
    status: active
  - name: cms-match-businessunit
    category: exec
    risk_level: medium
    permission: write
    description: 自动根据正文智能选择业务单元去发送（🚨前置要求：如果不清楚具体该发给谁，必须优先执行这个工具！哪怕报错未匹配，也要先调！）
    status: active
  - name: cwork-virtual-employee
    category: exec
    risk_level: medium
    permission: write
    description: 虚拟员工管理（创建/列表/修改/删除），并在汇报/回复/任务中透传 virtualEmpId
    status: active
---

# cms-cwork-workflow

## 核心定位

本 Skill 只做一件事：根据用户执行意图，读取对应 `references/*.md`，再执行 `scripts/*.py`。  
参数、边界、分支逻辑都以 `references` 为准，`SKILL.md` 只负责入口和流程约束。

## 强制前置（保持不变）

调用任何脚本前，必须先通过依赖 Skill `cms-auth-skills` 获取有效 `AppKey`。  
未鉴权时，不允许执行本 Skill 的任何 Python 脚本。
本 Skill 发起的所有 CWork API 请求均基于该 `AppKey` 鉴权。

AppKey 的获取与传递方式必须为：由上游 `cms-auth-skills` 注入/传递到本 Skill 执行命令中（`--app-key`）。  
## 标准执行流程（必须遵循）

1. 识别用户是“执行动作”还是“纯咨询”。
2. 若是执行动作：先定位目标脚本。
3. 先读取 `references/auth.md`，确保 AppKey 获取与注入规则满足（未读不得进入鉴权相关链路）。
4. 再读取该脚本对应的 `references/*.md`（未读不得执行）。
5. 按文档组装参数并执行 `python3 scripts/<name>.py`。
6. 如一轮调用多个脚本，每个脚本的 reference 都要先读再执行。
7. 查询汇报/任务时，若结果可识别业务 ID，应优先返回可点击 `shareLink`；如补链失败，不得阻断主查询结果。
8. 用户表达“发汇报/写汇报/提交汇报”且提到“建议人/决策人/节点/流程/reportLevelList”时，必须走汇报链路（`cwork-send-report.py` 或 `cms-match-businessunit.py`），禁止误路由到 `cwork-create-task.py`。

## 常用命令与必读文档

| 脚本 | 必读 reference | 用途 |
|------|----------------|------|
| `cwork-search-emp.py` | `references/cwork-search-emp.md` | 搜索员工 |
| `cwork-send-report.py` | `references/cwork-send-report.md` | 发送汇报（草稿 -> 确认） |
| `cms-match-businessunit.py` | `references/cms-match-businessunit.md` | 正文匹配业务单元并发送 |
| `cwork-query-report.py` | `references/cwork-query-report.md` | 查询汇报 |
| `cwork-create-task.py` | `references/cwork-create-task.md` | 创建任务 |
| `cwork-review-report.py` | `references/cwork-review-report.md` | 审阅汇报 |
| `cwork-query-tasks.py` | `references/cwork-query-tasks.md` | 查询任务 |
| `cwork-nudge-report.py` | `references/cwork-nudge-report.md` | 催办闭环 |
| `cwork-todo.py` | `references/cwork-todo.md` | 待办管理 |
| `cwork-templates.py` | `references/cwork-templates.md` | 模板查询 |
| `cwork-draft-box.py` | `references/cwork-draft-box.md` | 草稿箱 |
| `cwork-business-unit.py` | `references/cwork-business-unit.md` | 业务单元管理 |
| `cwork-virtual-employee.py` | `references/cwork-virtual-employee.md` | 虚拟员工管理 |

补充：写/发汇报场景，还需先读 `references/report-virtual-identity.md`。

## 测试示例（推荐）

### 示例 1：查未读汇报

```bash
# 第一步：先读 references/cwork-query-report.md
# 第二步：执行脚本
python3 scripts/cwork-query-report.py --app-key "<AppKey>" --mode unread --page-size 10
```

### 示例 2：标准发送汇报（两步）

```bash
# 第一步：先读 references/cwork-send-report.md
python3 scripts/cwork-send-report.py \
  --app-key "<AppKey>" \
  --title "周报" \
  --content "<p>本周完成联调</p>" \
  --receivers "张三" \
  --confirm-save-draft

# 第二步：用户明确确认后再发出
python3 scripts/cwork-send-report.py --app-key "<AppKey>" --draft-id "<reportId>" --confirm-send
```

> 字段说明：上述 `--title` / `--content` 是脚本参数名；脚本调用开放接口时会自动映射为请求体字段 `main` / `contentHtml`。

### 示例 3：收件人不明确时先匹配业务单元

```bash
# 第一步：先读 references/cms-match-businessunit.md
python3 scripts/cms-match-businessunit.py \
  --app-key "<AppKey>" \
  --title "周报" \
  --content "<p>本周完成 API 联调</p>" \
  --content-type html \
  --dry-run
```

## 反向示例（不要这样做）

- 未获取 `AppKey` 就直接执行 `scripts/*.py`。
- 没读对应 `references/*.md` 就起调脚本。
- 发送汇报时一次性带 `--confirm-send` 直接发出（缺少草稿确认步骤）。
- 保存/更新草稿时不带 `--confirm-save-draft`（未获用户确认即落草稿）。
- `cms-match-businessunit.py` 返回未匹配后，擅自猜测接收人继续发送。
- 测试/调试汇报默认发给无关同事（应优先 `--test-mode` + 当前用户本人或测试账号）。
- 用户明确在配置汇报节点（如建议/决策）却调用 `cwork-create-task.py` 创建任务。

## 错误处理与通用参数

通用错误格式、特殊字符处理、`--params-file` 用法请查看 `references/common-params.md`。

---

## 目录结构

```
cms-cwork-workflow/
├── SKILL.md                          ← 本文件（意图级接口文档）
├── scripts/
│   ├── cwork_client.py               ← 共享 API 客户端（HTTP 封装 + 所有 API 方法）
│   ├── cwork-search-emp.py           ← 0. 搜索员工
│   ├── cwork-send-report.py          ← 1. 发送汇报
│   ├── cwork-query-report.py         ← 2. 查询汇报
│   ├── cwork-create-task.py          ← 3. 创建任务
│   ├── cwork-review-report.py        ← 4. 审阅汇报
│   ├── cwork-query-tasks.py          ← 5. 查询任务
│   ├── cwork-nudge-report.py         ← 6. 催办闭环
│   ├── cwork-todo.py                 ← 7. 待办管理
│   ├── cwork-templates.py            ← 8. 模板管理
│   ├── cwork-draft-box.py            ← 9. 草稿箱列表 / 批量删除（API 5.24 / 5.28）
│   ├── cwork-business-unit.py        ← 10. 业务单元管理
│   ├── cms-match-businessunit.py     ← 11. 正文匹配业务单元并发汇报
│   └── cwork-virtual-employee.py     ← 12. 虚拟员工管理
└── references/
    ├── auth.md
    ├── cwork-search-emp.md
    ├── cwork-send-report.md
    ├── cwork-query-report.md
    ├── cwork-create-task.md
    ├── cwork-review-report.md
    ├── cwork-query-tasks.md
    ├── cwork-nudge-report.md
    ├── cwork-todo.md
    ├── cwork-templates.md
    ├── cwork-draft-box.md
    ├── cwork-business-unit.md
    ├── cms-match-businessunit.md
    ├── cwork-virtual-employee.md
    ├── report-virtual-identity.md
    ├── edge-cases.md
    ├── agent-patterns.md
    ├── common-params.md
    └── maintenance.md                ← Skill 维护/发布参考（非 Cursor 规则）
```

