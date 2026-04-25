# Late-Context-Safe `--generate` 设计文档

状态：Proposed  
范围：`kai-report-creator` 的 `--generate` 渲染链路  
目标问题：用户在生成最终报告前已经进行了复杂或多轮对话，最后一步才调用本技能，导致 render 阶段上下文过大，模型漏步骤、漏 reference、漏约束，最终输出质量不稳定。

配套对抗性评审：`docs/late-context-generate-adversarial-review.md`

## 1. 背景与问题定义

当前 repo 已经有一条正确方向的线：

- `scripts/guard_validate.py` 证明了一部分 IR 契约可以在生成前由脚本确定性执行。
- `evals/contract_checks.py` 证明了一部分规则已经从 prose 规则转成了可复用校验器。
- `references/spec-loading-matrix.md` 明确提出要“read fewer files, not more files”。

但 `SKILL.md` 当前的 `--generate` 说明仍然要求渲染前读取一整组 reference 文件，并依赖模型自己记住执行顺序、适用条件和失败补救方式。对于 late-context 场景，这种设计有三个问题：

1. render 阶段仍然暴露在大上下文噪音下。
2. prompt 中同时混有路由、契约、模板、质量规则，失败定位困难。
3. 一些本可确定性执行的步骤，仍然依赖模型“记得去做”。

这不是提示词轻微不足，而是架构边界不清。render 阶段没有被保护好。

## 2. 目标

### Goals

- 让 `--generate` 在 late-context 场景下不依赖原始长对话。
- 把可确定性执行的路由、装配、校验、补壳逻辑从 prompt 下沉到 script。
- 让模型只承担语义性重写和局部判断，而不是整条流水线协调。
- 把失败从“结果看起来不对”改成“某一层契约失败”。

### Non-Goals

- 不试图完全消灭 LLM 在 `--generate` 中的作用。
- 不试图一次性把所有 `references/*.md` 变成代码。
- 不引入新的用户可见复杂工作流。
- 不让 `GENERATE_PLAN.json` 成为新的手工维护真相源。

## 3. 设计原则

### 3.1 Render 只认工件，不认长对话

render 阶段的输入必须是一个小而硬的工件，而不是整段历史对话。对 `report-creator` 来说，主要工件是：

- 用户可见真相源：`.report.md`
- 内部派生产物：`GENERATE_PLAN.json`

原始对话只允许参与压缩阶段，不直接参与渲染阶段。

### 3.2 Script 优先接管确定性工作

以下工作如果还能靠 script 做，就不应继续靠 prompt：

- `report_class` / `archetype` / `theme` 路由
- reference 选择
- IR guard validation
- theme CSS 组装
- HTML shell 注入
- export 菜单与 JS binding 完整性
- HTML 结构 contract 检查
- 可机械修复的补壳与 fallback

### 3.3 模型只做局部语义任务

模型仍然保留，但职责收缩为：

- BLUF opening 重写
- heading 改写
- takeaway after data
- insight paragraph
- scan anchor 选择

也就是说，模型负责“写什么”，脚本负责“什么时候做、对哪里做、最低必须满足什么”。

### 3.4 不增加 prompt 负担来补救 prompt 负担

不能用“再多读几份 reference”“再追加几段 prose 规则”来修 render 阶段不稳定。  
新增质量机制若会增加生成期认知负担，应优先放进 deterministic gate、review 或 eval。

## 4. 提案概述

引入一个内部的、非用户可见的 generate orchestration 层。

```text
raw conversation / user context
        |
        |  compression only
        v
     .report.md  -----------------------> source of truth
        |
        |  scripts/build_generate_plan.py
        v
  GENERATE_PLAN.json -------------------> derived, ephemeral, not user-edited
        |
        |  renderer consumes only:
        |  - ir_text
        |  - generate_plan
        |  - minimal refs selected by plan
        v
  HTML draft
        |
        |  deterministic gates + targeted repair tasks
        v
  final HTML
```

核心变化不是“增加一个 JSON”，而是建立边界：

- `.report.md` 是唯一用户可编辑真相源。
- `GENERATE_PLAN.json` 是派生物，只存在于 `.tmp/` 或运行时内存中。
- render 阶段禁止直接依赖原始对话。

## 5. 关键设计

### 5.1 `GENERATE_PLAN.json` 作为内部执行契约

建议由新脚本 `scripts/build_generate_plan.py` 生成，输入是 `ir_text`，输出是 JSON。

建议字段：

```json
{
  "ir_hash": "sha256:abcd1234...",
  "resolved_theme": "corporate-blue",
  "resolved_report_class": "mixed",
  "resolved_archetype": "update",
  "required_refs": [
    "references/rendering-rules.md",
    "references/review-checklist.md",
    "references/anti-patterns.md",
    "references/html-shell-template.md",
    "references/theme-css.md"
  ],
  "component_inventory": {
    "kpi": 2,
    "chart": 1,
    "timeline": 1
  },
  "guard": {
    "status": "valid",
    "downgrades": []
  },
  "rewrite_tasks": [
    "check_bluf_opening",
    "check_heading_stack",
    "check_takeaway_after_data"
  ],
  "shell_contract": {
    "require_export_menu": true,
    "require_report_summary": true,
    "require_toc": true
  }
}
```

约束：

- 不进入 git 跟踪。
- 不允许用户手工编辑。
- 不允许成为新的 contract 真相源。
- 任意时候都可由 `.report.md` 重新生成。

### 5.2 严格的 render 输入边界

`--generate` 只接受两种 render 输入：

1. `.report.md` 文件内容
2. 明确可解析为 IR 的 context string

即使是 context-backed 模式，也只提取 IR 文本本身。IR 之外的聊天历史、讨论、风格争论、规划过程都不得进入 render prompt。

换句话说：

- “长对话生成了 IR” 是允许的。
- “长对话本身作为 render 背景” 是不允许的。

### 5.3 最小 reference 载入

`references/spec-loading-matrix.md` 负责静默分类，但不再要求模型在 `--generate` 中“read ALL of these”。  
相反，由 `build_generate_plan.py` 根据 `report_class`、`archetype`、component inventory 决定最小载入集。

建议规则：

| 条件 | 必载入 |
|------|--------|
| 所有报告 | `references/html-shell-template.md`, `references/theme-css.md` |
| 所有报告 | `references/review-checklist.md` 中仅被 `rewrite_tasks` 命中的条目 |
| 出现结构化组件 | `references/rendering-rules.md` |
| 需要防伪视觉锚点 | `references/anti-patterns.md` |
| 存在/候选 diagram | `references/diagram-decision-rules.md` |
| `regular-lumen` 或周期性报告 | `references/regular-report-content-rules.md` |

这里的关键不是“少读文件”本身，而是“把 reference 选择从模型记忆任务变成脚本路由任务”。

### 5.4 Script 化的责任边界

| 关注点 | 当前主要载体 | 建议 owner |
|--------|--------------|------------|
| IR block contract | prose + `contract_checks.py` | `contract_checks.py` + `guard_validate.py` |
| `report_class` / `archetype` 分类 | `SKILL.md` prose | `build_generate_plan.py` |
| theme 解析与 CSS 装配顺序 | `theme-css.md` prose | `render_theme_assets.py` 或 renderer 内确定性函数 |
| HTML shell 完整性 | `html-shell-template.md` + prompt 记忆 | `build_html_shell.py` |
| export menu / bindings | prompt + post-write search | `build_html_shell.py` + validator |
| generic heading 检测 | prompt | 脚本检测 + LLM 局部重写 |
| BLUF / takeaway / insight | prompt | LLM 局部重写 |
| render integrity | `run-report-evals.py` | 增强版 pre-write validator |

### 5.5 “脚本检测 + LLM 定点修复”替代“LLM 通读全局自检”

建议把 `references/review-checklist.md` 拆成三类执行方式：

- **A 类：script detect + script fix**
  - export menu completeness
  - shell marker completeness
  - timeline date syntax
  - KPI value length
  - icon normalization

- **B 类：script detect + LLM patch**
  - BLUF opening
  - heading stack logic
  - anti-template headings
  - takeaway after data
  - prose wall detection

- **C 类：review/eval only**
  - insight over data
  - scan-anchor coverage
  - conditional reader guidance

这样 render 阶段不再让模型“顺手把所有检查都做一遍”，而是只在脚本已经定位的问题点上进行最小编辑。

## 6. 建议流水线

### Phase 1: Prepare

- 读取 `.report.md`
- 解析 frontmatter / blocks
- 调用 `guard_validate.py`
- 生成 `GENERATE_PLAN.json`

### Phase 2: Deterministic Assembly

- resolve theme
- assemble CSS in canonical order
- build HTML shell
- inject export menu / report summary / TOC / edit mode scaffold
- 应用 auto-downgrade 后的 block 结构

### Phase 3: LLM Render

模型只接收：

- `ir_text`
- `generate_plan`
- 当前命中的最小 reference 片段

模型输出：

- section prose
- component body rendering
- 局部 rewrite patch

### Phase 4: Deterministic Validation

- 检查 HTML shell markers
- 检查 export bindings
- 检查 `ir_hash`
- 检查 raw `:::` 泄漏
- 检查 CSS assembly order

### Phase 5: Targeted Repair

若检测出 B 类问题，则生成局部 patch 任务，而不是重新整篇重写。  
每轮 repair 只允许修一个明确失败类别，最多 1-2 轮。

## 7. 失败行为

### Fatal

- 缺少 `title`
- IR 无法解析为 frontmatter + body
- CSS assembly 缺少必要 theme 资源
- HTML shell 无法构建

处理方式：停止输出，返回明确错误。

### Recoverable

- 非法 KPI / chart / timeline / diagram
- 缺失 export menu 某个 item
- 通用 heading
- opening 不满足 BLUF

处理方式：auto-downgrade 或 targeted repair。

### Non-Blocking

- scan-anchor 不理想
- insight 深度不足
- reader guidance 不够明确

处理方式：进入 review/eval，而不是阻塞写出。

## 8. 成功指标

### Functional

- `--generate` 不再要求加载全量 reference。
- render prompt 不再包含原始长对话。
- `report-summary`、export menu、TOC 等 shell markers 稳定存在。

### Quality

- late-context 场景下，漏 export / 漏 shell / 漏 CSS 顺序的回归显著下降。
- 同一 IR 多次生成的结构一致性提高。
- 失败能被定位为 guard / routing / render / repair / eval 某一层，而不是“整体效果不好”。

### Operational

- 生成耗时可增加少量开销，但不引入无限 repair loop。
- 脚本层新增逻辑有明确测试与 eval 对应。

## 9. 实施计划

### Phase A: 建边界，不改语义

- 新增 `build_generate_plan.py`
- `GENERATE_PLAN.json` 只做分类、路由、reference 选择、guard 结果汇总
- 删除 `--generate` 中“read ALL references”的要求，改为“按 plan 读取必要引用”

### Phase B: Script 化 shell / theme / export

- 把 CSS assembly 和 HTML shell 构建移出 prompt
- 新增 shell validator
- 把 export menu completeness 从 review checklist 提升为确定性 gate

### Phase C: 引入 targeted rewrite

- 脚本检测 BLUF / headings / takeaway 的失败点
- 只把失败片段交给模型定点修复

### Phase D: 强化 eval

- 新增 late-context 专项 case
- 新增“长对话 -> IR -> generate”模拟 case
- 记录 drift 发生在 prepare / render / repair 哪一层

## 10. 测试、Eval 与 ROI 验证

现有 repo 已经有一套四层 eval 骨架：

- `compression`
- `ir_contract`
- `async_readability`
- `render_integrity`

见 `scripts/run-report-evals.py` 与 `evals/failure-map.md`。  
这次改动不应该另起炉灶，而应该在现有骨架上补一层：**late-context isolation**。

### 10.1 验证的核心命题

这次改动要证明的不只是“感觉更稳”，而是两个更硬的因果命题。

#### 命题 A：render 阶段对长上下文噪音不再敏感

同一个 IR：

- file-backed 运行一次
- context-backed 且包裹大量无关对话再运行一次

两次结果应该在关键结构上保持一致。

#### 命题 B：额外脚本化开销，小于它减少的返工成本

也就是：

- latency 可以略升
- 但重跑次数、人工修补时间、漏壳/漏步骤回归次数要下降更多

如果只能证明 A，不能证明 B，这次改动仍然不算 ROI 过关。

### 10.2 测试层：证明“边界被守住”

#### Unit Tests

建议新增最小单元测试，专门验证 adapter / routing / isolation，而不是只看最终 HTML。

建议覆盖：

1. **IR extraction contract**
   - context 中只有一个 IR 块时，提取结果必须等于该 IR 原文
   - context 中有自然语言 + IR 时，只允许提取 IR
   - context 中存在多个 `---` 片段但不构成合法 IR 时，必须报错而不是猜

2. **context isolation contract**
   - renderer 接口只接收 `ir_text` 和派生 plan，不接收完整 conversation
   - file-backed 与 context-backed 最终传入 renderer 的 `ir_hash` 必须一致

3. **reference routing contract**
   - 同一 IR 在不同 noise wrapper 下，`required_refs` 必须一致
   - `diagram-decision-rules.md` 只在 diagram 相关 case 中载入
   - `regular-report-content-rules.md` 只在周期性报告 case 中载入

4. **deterministic owner contract**
   - shell / export / theme assembly 的关键步骤不再依赖 `SKILL.md` prose 顺序
   - 一旦脚本 owner 缺失某个 marker，测试直接失败

#### Integration Tests

建议新增端到端但不依赖人工目测的集成测试：

1. **same-IR, different-context**
   - 输入 A：裸 `.report.md`
   - 输入 B：`noise-prefix + report.report.md + noise-suffix`
   - 断言：
     - shell markers 一致
     - `report-summary` JSON 结构一致
     - component inventory 一致
     - `required_refs` 一致
     - heading stack / KPI labels / export menu 完整性一致

2. **file-backed vs context-backed parity**
   - 同一个 IR，分别通过文件路径与 context 提供
   - 断言结构等价，而不是要求全文字节级相等

3. **noisy-context regression fixture**
   - 选 2-3 个真实 case，外包一段刻意干扰的长对话：
     - 风格讨论
     - 不相关 TODO
     - 其他主题要求
     - 过时指令
   - 断言 route / shell / contract 不能被这些噪音改变

### 10.3 Eval 层：证明“质量提升不是错觉”

现有 `run-report-evals.py` 已覆盖四层，但还缺“噪音隔离”视角。  
建议新增两种 eval 方法。

#### 方法一：在现有 manifest 上增加 late-context 变体

为 `evals/report-cases.csv` 中的核心 case 增加 companion artifact：

- `context_path` 或 `noise_context_path`
- 内容为：长对话包裹的同一 IR

然后新增一层检查：

- `context_isolation`
  - renderer 使用的 `ir_hash` 是否与裸 IR 一致
  - `required_refs` 是否一致
  - `report_class` / `archetype` / `theme` 是否一致

这能直接衡量“抗噪音”能力。

#### 方法二：做 A/B eval，而不是只看绝对值

同一批 case，跑两套 pipeline：

- A：当前基线
- B：late-context-safe pipeline

比较：

- `render_integrity` fail rate
- `async_readability` rubric 通过率
- context noise 下的 route drift rate
- context noise 下的 shell drift rate

只有 A/B 对比，才能证明“这次改动带来了增量收益”。

### 10.4 新增指标

除了现有四层，建议新增 4 个专门服务这次改动的指标。

#### 1. Context Drift Rate

定义：同一 IR 在不同 noise wrapper 下，关键结构字段发生变化的比例。

关键字段包括：

- `resolved_theme`
- `resolved_report_class`
- `resolved_archetype`
- `required_refs`
- shell markers
- component inventory

目标：改动后显著下降，理想值接近 0。

#### 2. Re-run Avoidance Rate

定义：为了得到“可接受输出”，需要重复生成的平均次数。

测法：

- 对固定 case 集，记录 baseline 与新方案在首次通过 gate 的比例
- 记录“首次输出后仍需人工修补”的比例

如果脚本化只增加了几秒，但把平均重跑从 2.4 次降到 1.2 次，ROI 通常是正的。

#### 3. Human Repair Minutes

定义：同一 case 集，人工从初稿修到可交付版本所需时间。

这比纯 latency 更接近真实 ROI。  
用户真正付出的成本，不是多等 1-3 秒，而是多修 10 分钟。

#### 4. Deterministic Overhead

定义：新链路相对 baseline 增加的固定时间成本。

要单独拆开看：

- plan build
- guard
- shell assembly
- validation
- repair

这样才能避免把“脚本化太慢”说成一句模糊印象。

### 10.5 ROI 的判断标准

这次改动的 ROI 不应靠主观印象判断，而应满足下面的门槛。

#### 必须满足

- Context Drift Rate 明显下降
- `render_integrity` 回归下降
- 首次通过率上升或至少不下降

#### 最好满足

- Human Repair Minutes 下降
- `async_readability` rubric 不下降
- Deterministic Overhead 保持在可接受范围

#### 不应接受的结果

- shell 更稳定了，但 `async_readability` 明显变差
- 抗噪音更强了，但 latency / complexity 高到维护成本失控
- `GENERATE_PLAN.json` 自身变成第二真相源，导致 debug 更慢

### 10.6 推荐的最小验证包

如果只做一个最小可落地版本，建议先补这组验证：

1. **3 个 noisy-context regression cases**
   - narrative
   - mixed update
   - data-heavy business

2. **2 个 parity tests**
   - file-backed vs context-backed
   - bare IR vs noisy wrapped IR

3. **1 个 A/B summary script**
   - 输出 baseline vs new pipeline 的：
     - drift rate
     - shell failure rate
     - eval pass rate
     - average latency

4. **1 条 ROI gate**
   - 如果 drift 没显著下降，或者首次通过率没改善，就不继续扩大 orchestration scope

## 11. 不采纳的方案

### 11.1 继续扩充 `SKILL.md`

不采纳。问题已经不是单条规则写得不够清楚，而是 render 阶段仍依赖模型在大上下文里记住整条流程。

### 11.2 完全取消 LLM，仅靠模板生成

不采纳。报告的 opening、heading、takeaway、insight 仍需要语义重写能力。

### 11.3 让 `GENERATE_PLAN.json` 成为用户可编辑中间层

不采纳。这会制造第二真相源，并把 drift 风险放大。

## 12. 结论

这个方案的核心不是“再加一个步骤”，而是把 `--generate` 从“靠模型通读长上下文 + 记住大量 prose 规则的隐式流程”，改造成“IR 驱动、脚本路由、局部语义修复的显式流程”。

如果只能先做一刀，优先级是：

1. render 阶段禁止依赖原始长对话
2. 引入 `GENERATE_PLAN.json` 作为内部执行契约
3. 把 shell / theme / export / contract gate 下沉到 script
4. 保留模型做局部语义修复，不让它继续协调整条流水线
