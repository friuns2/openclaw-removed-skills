# 对 `late-context-safe --generate` 方案的对抗性评审

评审对象：`docs/late-context-generate-design.md`

结论：**建议推进，但必须缩 scope。**  
如果直接把“planner + renderer + targeted repair + 全量 script 化”一次推满，这个方案有明显过度设计风险。  
更稳妥的结论是：**先建立 render 边界和 deterministic owner，再决定是否需要完整的 `GENERATE_PLAN.json` 编排层。**

## Findings

### 1. Highest: 如果 render 仍然允许读取原始长对话，整个方案的主目标会直接失效

这个提案的价值建立在一个前提上：render 阶段只能看到 `.report.md` 和派生产物。  
如果实现时为了“兼容灵活性”继续让 renderer 读大量历史对话、planning 过程、口头补充说明，那么：

- `GENERATE_PLAN.json` 只会变成一个旁路提示
- late-context 噪音仍然会污染 render prompt
- 最终失败模式不会改善，只是多了一层复杂度

必须有硬边界：**context-backed 模式也只能抽取 IR 文本，不能把整段对话带进 render。**

### 2. Highest: `GENERATE_PLAN.json` 很容易演化成第二真相源

设计文档里说它是 derived artifact，但如果后续出现以下任一情况，它就会开始漂移：

- 某些逻辑只写在 plan builder，不写回 `.report.md`
- 某些修复直接改 plan，不改 IR
- 测试只验证 plan，不验证最终 HTML 与 IR 的一致性

一旦发生这种漂移，系统会变成：

- `.report.md` 看起来是一套规则
- `GENERATE_PLAN.json` 实际上是另一套规则
- 排错时没人知道该信哪一个

所以这份方案只有在一个条件下成立：**plan 必须是短生命周期、可重建、不可手工编辑、不可成为 contract 原点。**

### 3. High: “最小 reference 载入”会导致隐性规则丢失，除非先定义清楚 ownership

当前很多规则是跨文件分布的：

- `rendering-rules.md`
- `anti-patterns.md`
- `review-checklist.md`
- `design-quality.md`
- `html-shell-template.md`
- `theme-css.md`

如果只是粗暴追求“少读几个文件”，系统可能会出现一种更隐蔽的退化：

- shell 完整了，但视觉反模式回来了
- heading 修好了，但 component 语义 drift 了
- export menu 正常了，但 badge / summary / rhythm 约束丢了

所以“少加载”不是目标，**可证明地不漏 owner 才是目标**。  
没有 ownership matrix 的前提下，最小载入只是另一种形式的运气工程。

### 4. High: 方案默认问题发生在 `--generate`，但真实失真可能更早发生在压缩阶段

用户的原始问题是：最后一步才调用技能，前面已经聊了很多。  
这个问题不只会污染 `--generate`，也可能污染 `.report.md` 的生成本身。

如果 `.report.md` 已经在压缩阶段丢掉了：

- `must_include`
- `decision_goal`
- 关键结构关系
- 用户真正的输出意图

那么 render 再 deterministic，也只是稳定地产出一个“稳定错误”的结果。

因此这个方案最多只能修后半段。  
如果要真正解决 late-context，压缩阶段也要有自己的 artifact boundary 和 eval。

### 5. Medium: “script detect + LLM patch” 有价值，但 repair 编排很容易变成复杂控制流泥潭

听起来合理，但实践里很容易变成：

- detect 一轮
- patch 一轮
- 再 validate 一轮
- patch 再一轮
- 最后为了兼容 edge case 再加例外分支

最后系统可能从一个脆弱 prompt，变成一个难维护的多轮 orchestrator。

如果没有硬限制，repair loop 会带来：

- latency 上升
- 状态空间膨胀
- debug 复杂度增加

所以必须限制：

- 最多 1-2 轮 repair
- 每轮只允许修单一失败类别
- repair 失败时直接暴露错误，而不是无限兜底

### 6. Medium: 提案对 shell / theme 的脚本化判断是对的，但落地成本被低估了

当前 theme 和 shell 的不少知识仍然以 prose contract 形式存在。  
从“模型照着做”迁移到“脚本直接装配”，意味着要把这些 contract 真正变成代码 owner。

这件事是值得做的，但不便宜。  
尤其是：

- CSS split order
- shared CSS 插入点
- theme override precedence
- export JS binding
- edit mode / TOC / card mode scaffold

这些一旦 script 化，就需要一整套新的 snapshot / contract tests 保护。

### 7. Medium: 方案把很多 review 规则分成 A/B/C 类是正确的，但分类边界仍然有争议

例如：

- `anti-template heading` 看似可以脚本检测，但“是否 generic”常常要看上下文
- `prose wall detection` 可以脚本发现长段落，但如何切分仍是语义问题
- `scan-anchor coverage` 很容易被错误地机械化，反而制造视觉噪音

如果分类过于乐观，会把本来适合 review 的问题提前塞回 render 热路径。

### 8. Lower: 文档里默认 `GENERATE_PLAN.json` 是必要的，但更小的 V1 也许已经够用

对当前 repo 来说，可能不需要先引入完整 plan 文件。  
一个更小的 V1 可能已经足够显著改善：

- 强制 render 只吃 IR
- 把 shell / theme / export 先脚本化
- 保留现有 guard
- 只新增一个极薄的 routing summary，而不是完整 plan schema

如果这个更小的 V1 已经把 70% 的 late-context 回归压掉，那么完整 plan 可能不是第一优先级。

## Open Questions

1. `--generate` 是否继续支持“无文件、纯上下文”的模式？如果支持，是否只允许 context 中存在单个 IR 块？
2. `GENERATE_PLAN.json` 的 schema owner 是谁？是脚本实现先行，还是先写 contract 文档再实现？
3. 哪些 reference 会被彻底退出 render prompt，哪些只会被切成更小片段保留？

## 推荐的 Scope Reduction

如果按最稳妥路线推进，我建议把第一阶段压缩到下面 4 项：

1. **硬边界**：render 阶段只能读取 IR 文本，禁止读取原始长对话。
2. **脚本 owner**：先把 shell、theme、export、contract gate 收到脚本层。
3. **轻量 plan**：先做 routing summary，而不是一次做大而全的 `GENERATE_PLAN.json`。
4. **评估补齐**：先新增 late-context eval case，再决定是否引入 targeted repair orchestration。

## 推荐结论

这份设计的方向是对的，但有一个必须守住的底线：

**不要为了摆脱 prompt soup，造出一个更复杂的 orchestration soup。**

正确的推进方式不是“一次性系统重写”，而是：

- 先切断 raw conversation -> render 的直连
- 再把最稳定、最机械、最容易漏的步骤脚本化
- 最后才决定是否需要更重的 planner / repair loop

如果偏离这个顺序，这个方案很容易从“减少认知负担”演化成“把复杂度从 prompt 转移到 orchestration”，但并没有真正提高可靠性。
