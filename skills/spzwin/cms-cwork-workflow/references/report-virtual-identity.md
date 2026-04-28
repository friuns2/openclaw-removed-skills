### 写/发汇报：发送前虚拟身份检查规则

**作用范围**：仅用于写汇报/发汇报流程。  
**不适用**：回复汇报、创建任务。

---

## 触发词

- 发汇报 / 发送汇报 / 帮我发（汇报）
- 写汇报 / 提交汇报
- 以虚拟人身份发送 / 用虚拟人发（汇报）

---

## 核心流程

1. 用户发起“写/发汇报”请求  
2. 先查询虚拟身份列表：  
   `python3 scripts/cwork-virtual-employee.py --mode list`
3. 根据列表分支：
   - **无虚拟身份（`list=[]`）**：不要求用户先创建，按普通员工身份继续汇报发送流程。
   - **一个虚拟身份**：询问用户“是否以 [名称] 身份发送？”；仅在用户确认后传 `virtualEmpId`。
   - **多个虚拟身份**：列出选项让用户选择；用户明确选择后传对应 `virtualEmpId`。
4. 用户确认后，调用汇报脚本并按需透传：  
   - `cwork-send-report.py --virtual-emp-id <id>`  
   - 或 `cms-match-businessunit.py --virtual-emp-id <id>`

---

## 执行约束

1. 仅当用户确认要使用虚拟身份时，才允许传 `--virtual-emp-id`。  
2. 未确认或无虚拟身份时，禁止臆断选择任意虚拟人。  
3. 无虚拟身份不是错误场景，不中断汇报发送主流程。
4. `virtualEmpId` 为虚拟人提交参数；脚本鉴权主体仍为当前用户 AppKey。发送-only（`--draft-id --confirm-send`）若本次传入或草稿内已有 `virtualEmpId`，最终发出会走 5.1（携带 `id` + `virtualEmpId`）提交。
