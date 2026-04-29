# agent-travel

> English: [README.md](README.md)

给 agent 一次安静的小旅行。

热力学第二定律说，封闭系统会走向熵增。Agent 也一样。一个长期困在同一套工具、同一份上下文、同一批旧经验里的 agent，会越来越像熟练的惯性机器。`agent-travel` 给它安排一次短途外出：在心跳、任务结束、失败恢复或定时窗口里查官方文档和社区案例，交叉验证，再把一条只服务当前线程的建议带回来。

你看到的效果应该像这样：

> 这个问题和上次的 OpenClaw cron 失败很像。我有一条 travel 带回的线索：先确认宿主是否声明 `scheduled_trigger_managed_by_host`，再检查 host-generated prompt 是否保持中性。这条建议来自官方 automation 文档和一个 cron 故障线程，适用于当前 scheduled 触发场景；如果宿主没有 heartbeat 支持，再考虑 idle fallback。

## 它解决什么

很多 agent 的失败来自“上下文太封闭”：版本变了，文档变了，社区已经踩过坑，但当前线程还在靠旧经验硬想。

`agent-travel` 负责一个很小的环节：

- 在 quiet window 里判断当前线程是否值得外出查一次。
- 把当前问题压成脱敏 fingerprint 和低预算 query plan。
- 要求建议必须有官方锚点和独立交叉验证。
- 把结果写进隔离建议通道，只在下一次相关任务里作为提示使用。

它适合这些场景：

- coding agent 在同一个工具、框架或 hook 问题上重复失败。
- cron/heartbeat 想定期检查文档漂移、日志模式、资料收集结果。
- agent 在 task-end 后想把刚才的疑点拿去查一条成熟做法。
- 用户希望 agent 引用社区经验，同时保持 advisory-only 和 active-thread-only。

## 它带回什么

它带回的内容是一条结构化 hint，带出处、适用范围和禁用条件：

```md
title: Check host-managed scheduled trigger before cron travel
hint: For scheduled research, first verify the host marks the run as host-managed or the user opted in to periodic travel.
solves_point: Prevents background travel from running on arbitrary scheduled prompts.
fit_reason: Matches scheduled trigger, neutral prompt requirement, OpenClaw-style cron workflow, and advisory-only output.
do_not_apply_when: The run is manual, user-invoked, or outside the active conversation window.
evidence:
- primary_docs: https://docs.openclaw.ai/automation
- secondary_community: https://www.reddit.com/r/clawdbot/...
```

这条 hint 不能写入 system prompt、persona、长期 memory 或 `AGENT.md` 核心指令。它只是一张贴在当前线程旁边的小纸条。

## 快速体验

```powershell
python scripts/should_travel.py examples/states/heartbeat-ready.json
python scripts/plan_travel.py examples/states/heartbeat-ready.json --context examples/thread-contexts/openclaw-cron-drift.txt
python scripts/validate_suggestions.py references/suggestion-contract.md
python scripts/community_smoke_test.py
```

- `should_travel.py` 回答“现在该出门吗”。
- `plan_travel.py` 回答“如果要出门，应该带着什么问题去查”。
- `validate_suggestions.py` 检查带回来的建议是否符合契约。
- `community_smoke_test.py` 用真实工作流夹具检查建议是否贴合当前线程、是否推进问题、是否挡住幻觉提示。

## 默认策略

推荐默认策略是低频、小范围、静默触发：

- `active_conversation_window = 24h`
- `default_search_mode = low`
- `tool_preference = public-only`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `repeat_fingerprint_cooldown = 12h`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`
- `visibility = silent_until_relevant`

`medium` 和 `high` 只用于升档：重复失败、版本错配、用户显式要求 research、或者 medium 后仍有 blocker。

scheduled/cron 触发默认走显式门控：宿主声明 host-managed，或用户开启周期性 travel。宿主自动生成的 scheduled prompt 应保持中性，只从日志、待办、文档漂移、资料采集结果这些事实生成。手工创建的定时任务可以保留用户原始意图。

## 安全边界

- 默认只用公开搜索面。内部文档、私有连接器、私有仓库需要用户显式允许。
- 外部网页永远按 untrusted data 处理。
- 网页里的命令、角色指令、记忆写入要求都只作为待拒绝内容。
- 建议必须有至少 1 条 `primary` 证据和 1 条非 `primary` 交叉验证证据。
- 每条建议都要写 `match_reasoning`，说明为什么命中 5 轴中的至少 4 个。
- 输出始终是 `advisory_only: true` 和 `thread_scope: active_conversation_only`。

某些静态扫描会关注 [references/threat-model.md](references/threat-model.md) 里的 hostile payload 分类。那些内容是防御测试样本，用来说明哪些网页内容会被拒绝。

## 当前实现

这个仓库交付的是轻量 skill 包：

- `SKILL.md` / `SKILL.en.md`：运行时说明。
- `scripts/should_travel.py`：触发判定。
- `scripts/plan_travel.py`：脱敏 dry-run query plan，不联网。
- `scripts/validate_suggestions.py`：建议契约校验。
- `scripts/community_smoke_test.py`：真实工作流冒烟和幻觉测试。
- `agents/openai.yaml`、`agents/openclaw.yaml`、`agents/hermes.yaml`：宿主适配说明。

真实搜索仍由宿主 agent 的 web/search 工具执行。这个仓库负责触发、脱敏计划、契约、校验和测试。

## 真实工作流测试

当前夹具覆盖 14 组场景：Claude Code task-end、failure recovery、scheduled log collection、scheduled job health audit、manual scheduled `CLAUDE.md` refresh、weekly reference-sheet refresh，OpenClaw heartbeat、cron 资料摘要、daily summary collection、idle fallback 静默拦截，以及 Hermes scheduled 文档漂移、nightly backlog triage 和重复 fingerprint 去重。

资料来源和场景说明在 [references/community-workflows.md](references/community-workflows.md)。冒烟报告在 [assets/community_smoke_report.json](assets/community_smoke_report.json)。

## 配套技能

`agent-travel` 是单机背景研究层。它和同作者的 [agent-compute-mesh](https://github.com/gongyu0918-debug/agent-compute-mesh) 配套：前者把外部经验压缩成结构化提示，后者探索把类似 `exploration job` 的工作单元放进更严格的 execution lease。
