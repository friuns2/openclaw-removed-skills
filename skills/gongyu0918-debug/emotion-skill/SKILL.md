---
name: emotion-skill
description: Positive routing for coding agents under pressure. Use when repo debugging, scoped implementation, repeated-failure recovery, evidence-demanding review, cautious file changes, or post-success closeout need better runtime behavior. Detect user-state signals internally, then return positive system prompt addenda, route reasons, response constraints, reply style, verification depth, queue mode, progress cadence, and guard behavior.
metadata:
  openclaw:
    emoji: "🎛️"
    os: ["darwin", "linux", "win32"]
---

# Emotion Skill

Emotion Skill is a small runtime router for coding agents.

It reads the latest user turn, recent dialogue, retries, delay pressure, optional host state, and optional feedback from the last routing decision. It then returns a compact host contract that tells the agent how to work this turn.

The core rule: internal user-state signals must become positive execution instructions. Production hosts should pass `guidance.system_prompt_addendum`, `response_constraints`, and `routing` into the model. Raw affect fields stay internal unless audit mode is explicitly enabled.

## Use It When

- A bug fix has failed more than once.
- The user asks for evidence, exact checks, logs, or root cause.
- The user says to touch only specific files or avoid config drift.
- A tool call, session, queue, or heartbeat path has gone silent.
- The user says the work is good and the agent should close out.
- The agent needs to choose between collect, steer, and interrupt modes.

## What It Returns

Use the `host` command for real integration:

```bash
python scripts/emotion_engine.py host --message "Show me the basis before changing more files." --pretty
```

Default host shape:

```json
{
  "mode": "skeptical",
  "route_reasons": ["repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps"],
  "guidance": {
    "system_prompt_addendum": "The user wants evidence before more changes. Start with a verification point, command, or log excerpt, then give the conclusion and next step.",
    "tone": "evidence_first"
  },
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true,
    "progress_update_interval_sec": 20
  }
}
```

Default output deliberately keeps raw `labels` and raw `emotion_vector` out of the host prompt path. This keeps the skill from amplifying negative state words inside the model context.

## Host Fields

- `guidance.system_prompt_addendum`: positive instruction text for the host LLM.
- `guidance.tone`: compact tone target such as `evidence_first`, `careful_and_bounded`, or `guarded_closeout`.
- `response_constraints`: compact reply guardrails.
- `route_reasons`: enum-like routing codes for logs and telemetry.
- `routing.reply_style`: response posture.
- `routing.verification_level`: checking depth.
- `routing.queue_mode`: collect, steer, or interrupt.
- `routing.prefer_main_thread`: keep the work on the main turn when user trust or clarity needs it.
- `routing.progress_update_interval_sec`: progress cadence for long-running work.
- `satisfaction_lock`: closeout guard after success.
- `interaction_state`: positive host-facing axes: clarity, trust, engagement.
- `state.state_delta`: action-named shifts such as `needs_concrete_unblock`, `needs_evidence_first`, or `needs_alignment_check`.
- `memory.should_persist`: host-side persistence recommendation.

## Input Contract

Smallest valid payload:

```json
{
  "message": "latest user message"
}
```

Production payload:

```json
{
  "message": "Only touch the parser file and show the failing path first.",
  "history": [
    {"role": "user", "text": "earlier user turn"},
    {"role": "assistant", "text": "earlier assistant turn"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2,
    "queue_depth": 1,
    "background_tasks_running": 1,
    "last_routing_outcome": {
      "mode_was": "skeptical",
      "user_followed_up_with": "still broken"
    }
  },
  "last_state": {
    "vector": {},
    "emotion_vector": {},
    "ttl_seconds": 1200
  },
  "calibration_state": {},
  "user_profile": {}
}
```

Malformed JSON, missing files, and top-level arrays return exit code `2` with a single-line error.

## Raw Affect Audit Mode

For audit and calibration only:

```json
{
  "host_capabilities": {
    "include_raw_emotion": true
  }
}
```

This adds `diagnostics.internal.labels`, `diagnostics.internal.emotion_vector`, raw `state_delta`, and `mode_scores`. Keep these fields out of normal LLM prompts.

## Runtime Commands

| Command | Purpose |
|---|---|
| `host` | compact production contract |
| `run` | full diagnostics |
| `screen` | deterministic first pass |
| `confirm` | final state and weight schedule |
| `predict` | risk, stall, patience, and semantic-pass budget |
| `route` | routing only |
| `guide` | short-probe guidance |
| `overlay` | overlay prompt inspection |
| `posthoc` | review-pass and calibration inspection |

## Persistence Boundary

The core engine is stateless. It returns JSON, makes no network calls, and writes only when `--output` is provided.

The minimal host adapter writes three host-owned JSON files under `--store-dir` when persistence is enabled:

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

Use `--no-persist` for read-only previews. Use `--ignore-bad-store` to skip corrupt store files and continue from empty values.

## Integration Pattern

1. Run `host` when a user turn arrives.
2. Put `guidance.system_prompt_addendum` before the model's task instructions.
3. Put `overlay_prompt` near the runtime metadata.
4. Feed `response_constraints` into reply planning.
5. Feed `routing` into queue, heartbeat, progress cadence, and subtask policy.
6. Apply `satisfaction_lock` after success.
7. Persist `memory.proposed_calibration_state` only in host-owned storage.

## Published Bundle

ClawHub publish now ships the runtime-facing subset only:

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

The full GitHub repo keeps the heavier regression, audit, and calibration assets.

## Validation

Published-bundle smoke:

```bash
python scripts/download_smoke.py
```

Full GitHub validation:

```bash
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python scripts/independent_audit.py
python scripts/marketplace_tag_audit.py
python scripts/feature_gate_audit.py
python scripts/bundle_manifest_check.py
```

Current local regression results:

- alignment: `70/70`
- ablation: `333/333`
- strict smoke: `ok`
- independent audit: `ok`
- download smoke: `ok`
- bundle manifest: `ok`

## Good Fit

Use it for coding-agent orchestration, repository debugging, scoped edits, verification-first replies, and closeout behavior after success.

Use a different skill for general emotional memory, roleplay, personal journaling, or long-term personality simulation.
