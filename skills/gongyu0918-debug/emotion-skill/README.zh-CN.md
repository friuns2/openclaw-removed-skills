# 情绪.skill / Emotion Skill

[English](./README.md) · [GitHub](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill) · `clawhub install emotion-skill`

给 Coding Agent 用的正向路由层：用户变急、变谨慎、开始要证据、反复说没修好时，它把这些信号翻译成可执行的 system prompt 和宿主路由策略。

它的重点是“读懂状态后改善执行”，不是把负面情绪向量继续塞给模型。

![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Dependencies](https://img.shields.io/badge/dependencies-standard%20library-2E7D32)
![Runtime](https://img.shields.io/badge/runtime-no%20network-455A64)
![License](https://img.shields.io/badge/license-MIT-blue)

## 为什么值得装

Coding Agent 常在这些时刻掉质量：

- 用户说同一个 bug 还在，Agent 继续解释。
- 用户要依据，Agent 继续猜。
- 用户要求只改一个文件，Agent 顺手动了旁边配置。
- 用户说已经好了，Agent 又开新改动。
- 长时间没反馈后，用户变短变硬，Agent 没读出来。

这个 skill 把这些信号转成 host 可消费的路由字段和正向 `system_prompt_addendum`。raw affect 默认留在内部，审计时再显式打开。

## 它改变什么

| 用户信号 | 宿主行为 |
|---|---|
| “这个还没修好” | 提高验证强度，留在主线程，缩短进度更新间隔 |
| “先给我依据” | 先给命令、日志、测试或校验点，再给结论 |
| “只改这个文件” | 收紧范围，保护配置，说明回滚路径 |
| “路径对不上” | 先复述目标，再给一个可纠正的默认路径 |
| “已经好了，收口” | 进入 guard mode，做回归检查，停止扩 scope |

## 安装

从 ClawHub 安装：

```bash
clawhub install emotion-skill
cd skills/emotion-skill
python scripts/download_smoke.py
```

从 GitHub 安装：

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
python scripts/download_smoke.py
```

环境要求：

- Python `3.9+`
- 只用标准库
- 运行时引擎不发网络请求

## 30 秒试跑

```bash
python scripts/emotion_engine.py host \
  --message "这个问题还没修好，先给我依据，再继续改。" \
  --pretty
```

默认 host 输出面向生产提示词：

```json
{
  "mode": "skeptical",
  "route_reasons": ["repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps"],
  "guidance": {
    "system_prompt_addendum": "用户希望先看到依据。回复以校验点、命令或日志片段开头，再给结论和下一步。",
    "tone": "evidence_first"
  },
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true
  }
}
```

默认输出里没有 raw `labels`，没有 raw `emotion_vector`，也没有 `falling_trust` 这类负向状态词。

## Host 契约

真实接入优先使用 `host` 输出。关键字段：

- `guidance.system_prompt_addendum`：给宿主 LLM 的正向行动提示。
- `response_constraints`：下一轮回复的紧凑约束。
- `routing.reply_style`：回复姿态，例如 `evidence_then_act`、`repair_then_explain`、`verify_then_act`。
- `routing.verification_level`：动手前的检查强度。
- `routing.queue_mode`：继续收集、引导当前任务，或打断队列。
- `routing.progress_update_interval_sec`：长任务进度节奏。
- `satisfaction_lock`：成功后的收口守护。
- `interaction_state`：面向 host 的正向轴：clarity、trust、engagement。
- `state.state_delta`：动作命名的跨轮变化，比如 `needs_evidence_first`。
- `memory.should_persist`：是否建议宿主合并画像更新。

完整 `run` 命令保留 diagnostics、features、prompts、calibration 字段，给研究和回归测试用。

## Raw Affect 显式开启

生产 host 应该把 `guidance.system_prompt_addendum`、`response_constraints`、`routing` 喂给模型。

审计工具可以请求内部状态：

```json
{
  "message": "先给精确失败路径。",
  "host_capabilities": {
    "include_raw_emotion": true
  }
}
```

开启后会增加：

- `diagnostics.internal.labels`
- `diagnostics.internal.emotion_vector`
- `diagnostics.internal.state_delta`
- `diagnostics.internal.mode_scores`

## 反馈闭环

宿主可以把上一轮路由效果带进下一轮：

```json
{
  "runtime": {
    "last_routing_outcome": {
      "mode_was": "skeptical",
      "user_followed_up_with": "still broken"
    }
  }
}
```

这样不用训练模型，也能让路由器知道上一轮策略有没有起作用。

## 持久化边界

核心引擎无状态。它返回 JSON，不发网络请求；只有传入 `--output` 时才写文件。

最小宿主适配器可以在 `--store-dir` 下维护三个宿主文件：

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

用 `--no-persist` 做只读预览。用 `--ignore-bad-store` 跳过损坏的本地 store，从空值继续。

## 验证

发布包冒烟：

```bash
python scripts/download_smoke.py
```

完整仓库验证：

```bash
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python scripts/independent_audit.py
python scripts/marketplace_tag_audit.py
python scripts/feature_gate_audit.py
python scripts/bundle_manifest_check.py
```

当前本地结果：

- alignment regression: `70/70`
- ablation harness: `333/333`
- strict smoke: `ok`
- independent audit: `ok`
- marketplace scope audit: `ok`
- feature gate audit: `ok`
- download smoke: `ok`
- bundle manifest check: `ok`

## 发布包

ClawHub 发布包只带运行时需要的文件：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `agents/openai.yaml`
- `scripts/emotion_engine.py`
- `scripts/minimal_host_adapter.py`
- `scripts/download_smoke.py`
- `demo/local_history_event.json`
- `references/examples.md`
- `references/model-prompts.md`
- `references/emotion-value-model.md`
- `references/emotion-policy-matrix.md`
- `references/integration-openclaw-hermes.md`

完整 GitHub 仓库保留更重的回归、审计和校准文件。

## 适合谁

- 需要在高压对话里稳定输出的 Coding Agent。
- 需要路由字段、进度节奏和验证强度控制的宿主。
- 想做 emotion-aware 行为，并把 raw 情绪信号保留在 audit 模式的团队。

## License

MIT. See the [GitHub repository license](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill/blob/main/LICENSE).
