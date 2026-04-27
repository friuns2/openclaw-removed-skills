# Read Order

## Goal

写入治理只解决一半问题。

如果恢复时不知道先读哪层，系统还是会乱。

## Default Read Order

### General Task Startup

默认读取顺序：

1. `system_rules`
2. `tool_rules`
3. `long_term_memory`
4. relevant `reusable_lessons`
5. relevant `project_facts`
6. current `proactive_state` (read the current-task slice first if the adapter is split)
7. today's `daily_memory` only if recent context matters
8. `working_buffer` only when recovery risk is high
9. do not read `learning_candidates` during normal startup unless you are explicitly reviewing candidate promotions
10. do not read `DREAMS.md` during normal startup unless you are explicitly reviewing dreaming output or promotion quality

## Why This Order

- 先读全局规则，避免行为跑偏
- 再读稳定长期记忆，避免每次都从 daily note 里猜偏好
- 再读可复用经验，避免重复踩同样的坑
- 再读项目局部事实，避免把全局规则误用于局部例外
- 最后读当前状态和临时 breadcrumb
- 候选层默认不参与启动时主上下文，避免把未证明的规则提前当真
- Dream diary 不是默认 recall 层，避免把后台 consolidation 轨迹误当成当前真相

## Recovery Mode

当任务刚被打断、刚 compaction、或上下文明显脆弱时：

1. current `proactive_state` (current-task slice first if split)
2. `working_buffer`
3. relevant `reusable_lessons` when the task depends on learned execution patterns
4. relevant `project_facts`
5. today's `daily_memory`

恢复模式优先找“现在要继续什么”，不是先读全部历史。

`DREAMS.md` 在恢复模式里也不是默认入口。  
只有在你明确要检查 Dreaming 为什么 promote、没 promote、或 promotion 质量如何时才读。

## Conflict Precedence

### `project_facts` vs `long_term_memory`

项目局部事实优先于全局长期记忆。

原因：

- 项目局部例外不应被全局偏好覆盖

### `proactive_state` vs old `daily_memory`

较新的 `proactive_state` 优先。

原因：

- current state should beat historical notes

### `working_buffer` vs `proactive_state`

`proactive_state` 优先定义当前真相。  
`working_buffer` 只补充恢复细节。

不要让 breadcrumb 反过来覆盖 canonical task state。

### `system_rules` / `tool_rules` vs `reusable_lessons`

系统级和工具级规则优先。

原因：

- 它们是提炼后的更高治理层

### `reusable_lessons` vs old `daily_memory`

`reusable_lessons` 优先于旧 daily note 中的相似经验。

原因：

- 提炼后的经验应优先于历史事件里的未提炼片段

### `long_term_memory` vs `DREAMS.md`

`long_term_memory` 优先。

原因：

- `DREAMS.md` 是 dreaming process artifact，不是 canonical durable memory layer

### `learning_candidates` vs `DREAMS.md`

两者默认不直接冲突，因为职责不同：

- `learning_candidates` 保存显式纠错和待验证经验
- `DREAMS.md` 保存后台 consolidation 轨迹和摘要

如果看起来冲突，优先回到：

- `learning_candidates` 用于 review 是否升格
- `long_term_memory` 用于最终 durable truth

## Minimal-Load Principle

不要为了“完整”一次读完所有层。

推荐：

- 先读最小必要集合
- 只有在恢复风险高时再扩展读取
- 不要默认把 `working_buffer` 当成第一入口
- 不要把 `DREAMS.md` 当作普通启动记忆来加载
