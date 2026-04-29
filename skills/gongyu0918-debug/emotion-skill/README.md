# Emotion Skill

[简体中文](./README.zh-CN.md) · [GitHub](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill) · `clawhub install emotion-skill`

Positive routing for coding agents when the conversation gets tense, vague, blocked, or ready to close.

Emotion Skill reads user-state signals internally, then gives the host LLM a positive execution policy: what to verify first, how much scope to protect, when to stay on the main thread, and when to stop expanding work after success.

![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Dependencies](https://img.shields.io/badge/dependencies-standard%20library-2E7D32)
![Runtime](https://img.shields.io/badge/runtime-no%20network-455A64)
![License](https://img.shields.io/badge/license-MIT-blue)

## Why People Install It

Coding agents often fail in the same human moments:

- The user says the same bug still happens, and the agent keeps explaining.
- The user asks for evidence, and the agent keeps guessing.
- The user protects scope, and the agent touches nearby files.
- The user says it works, and the agent starts a new refactor.
- The user gets vague after a long delay, and the agent misses the pressure.

This skill turns those moments into host-readable routing fields and a positive `system_prompt_addendum`. Raw affect signals stay internal unless you explicitly opt in for audit.

## What It Changes

| User signal | Host behavior |
|---|---|
| "This is still broken" | raise verification, keep work on the main thread, shorten progress updates |
| "Show me the basis" | start with a command, log, test, or exact check before the conclusion |
| "Only touch this file" | tighten scope, protect config, name rollback path |
| "I am lost on the path" | restate the target, give one correctable default path |
| "Works now, wrap it up" | enter guard mode, run regression checks, stop scope drift |

## Install

From ClawHub:

```bash
clawhub install emotion-skill
cd skills/emotion-skill
python scripts/download_smoke.py
```

From GitHub:

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
python scripts/download_smoke.py
```

Requirements:

- Python `3.9+`
- standard library only
- no network calls from the runtime engine

## Try It

```bash
python scripts/emotion_engine.py host \
  --message "This is still not fixed. Show me the basis before changing more files." \
  --pretty
```

Default host output is designed for production prompts:

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
    "prefer_main_thread": true
  }
}
```

Notice what is absent by default: no raw `labels`, no raw `emotion_vector`, no negative state phrase such as `falling_trust`.

## Host Contract

Use `host` for runtime integration. The most important fields are:

- `guidance.system_prompt_addendum`: positive instruction text for the host LLM.
- `response_constraints`: compact guardrails for the next reply.
- `routing.reply_style`: posture such as `evidence_then_act`, `repair_then_explain`, or `verify_then_act`.
- `routing.verification_level`: how much checking to do before editing.
- `routing.queue_mode`: collect, steer, or interrupt current work.
- `routing.progress_update_interval_sec`: progress cadence for long turns.
- `satisfaction_lock`: closeout guard after success.
- `interaction_state`: positive host-facing axes: clarity, trust, engagement.
- `state.state_delta`: action-named shifts such as `needs_evidence_first`.
- `memory.should_persist`: recommendation for host-owned profile storage.

The full `run` command keeps diagnostics, features, prompts, and calibration fields for research and regression work.

## Raw Affect Is Opt-In

Production hosts should feed the model `guidance.system_prompt_addendum`, `response_constraints`, and `routing`.

Audit tools can request raw internal state:

```json
{
  "message": "Show me the exact failing path first.",
  "host_capabilities": {
    "include_raw_emotion": true
  }
}
```

That adds:

- `diagnostics.internal.labels`
- `diagnostics.internal.emotion_vector`
- `diagnostics.internal.state_delta`
- `diagnostics.internal.mode_scores`

## Feedback Loop

Hosts can pass the previous route outcome into the next turn:

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

This gives the router a lightweight effect signal without adding a model-training pipeline.

## Persistence Boundary

The engine itself is stateless. It returns JSON, makes no network calls, and writes only when `--output` is provided.

The minimal host adapter can persist three host-owned files under `--store-dir`:

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

Use `--no-persist` for read-only previews. Use `--ignore-bad-store` to skip corrupt local store files and continue from empty values.

## Validation

Published-bundle smoke:

```bash
python scripts/download_smoke.py
```

Full repository validation:

```bash
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python scripts/independent_audit.py
python scripts/marketplace_tag_audit.py
python scripts/feature_gate_audit.py
python scripts/bundle_manifest_check.py
```

Current local results:

- alignment regression: `70/70`
- ablation harness: `333/333`
- strict smoke: `ok`
- independent audit: `ok`
- marketplace scope audit: `ok`
- feature gate audit: `ok`
- download smoke: `ok`
- bundle manifest check: `ok`

## Published Bundle

ClawHub ships the runtime-facing subset:

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

The GitHub repository keeps the heavier regression, audit, and calibration files.

## Good Fit

- Coding agents that need better turn-by-turn behavior under pressure.
- Hosts that want routing fields, progress cadence, and verification depth.
- Teams that want emotion-aware behavior with raw affect kept in audit mode.

## License

MIT. See the [GitHub repository license](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill/blob/main/LICENSE).
