# agent-travel

> 中文说明：[README.zh.md](README.zh.md)

Give an agent a quiet short trip.

The second law of thermodynamics says a closed system drifts toward entropy. Agents do too. An agent trapped inside the same tools, the same context window, and the same stale assumptions will slowly confuse repetition with truth. `agent-travel` gives it a controlled way to step outside: during heartbeat, task-end, failure-recovery, scheduled, or idle windows, it checks official docs and community practice, cross-validates the useful parts, and brings back one advisory hint for the active thread.

The user-facing moment should feel like this:

> This looks like the OpenClaw cron failure we saw earlier. I have one travel hint: first verify that the host marked the run as `scheduled_trigger_managed_by_host`, then check whether the host-generated prompt stayed neutral. This is grounded in the official automation docs and a cron troubleshooting thread. It applies to scheduled runs; use idle fallback only when the host lacks heartbeat support.

## What It Solves

Many agent failures come from closed context: versions moved, docs changed, the community already found a pattern, and the current thread keeps reasoning from stale assumptions.

`agent-travel` owns one small loop:

- Decide whether the active thread is worth a quiet research pass.
- Turn the current problem into a redacted fingerprint and low-budget query plan.
- Require official grounding plus independent cross-validation.
- Store only isolated advisory hints for the next relevant turn.

Good fits:

- A coding agent keeps failing around the same tool, framework, hook, or scheduler.
- A cron or heartbeat job needs to check docs drift, log patterns, or collected research notes.
- A task-end hook wants one mature external practice for a fresh unresolved question.
- A user wants community experience without giving it authority over memory or core instructions.

## What It Brings Back

A travel hint is structured, sourced, scoped, and bounded:

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

The hint stays outside the system prompt, persona, long-term memory, and core `AGENT.md` instructions. It acts as a small note beside the active thread.

## Try It

```powershell
python scripts/should_travel.py examples/states/heartbeat-ready.json
python scripts/plan_travel.py examples/states/heartbeat-ready.json --context examples/thread-contexts/openclaw-cron-drift.txt
python scripts/validate_suggestions.py references/suggestion-contract.md
python scripts/community_smoke_test.py
```

- `should_travel.py` answers whether the travel window is open.
- `plan_travel.py` answers what the host would search, after redaction, without using the network.
- `validate_suggestions.py` checks the returned advisory contract.
- `community_smoke_test.py` checks thread fit, problem-solving value, and hallucination resistance with realistic workflow fixtures.

## Recommended Defaults

Low-frequency, small-scope, quiet by default:

- `active_conversation_window = 24h`
- `default_search_mode = low`
- `tool_preference = public-only`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `repeat_fingerprint_cooldown = 12h`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`
- `visibility = silent_until_relevant`

`medium` and `high` are escalation modes for repeated failures, version mismatch, explicit research requests, or blockers that survive a medium pass.

Scheduled travel uses explicit gating: the host marks the run as host-managed, or the operator opts in to periodic travel. Host-generated scheduled prompts should stay neutral and fact-derived from logs, backlog deltas, docs drift, or collected materials. Manual scheduled prompts may preserve the operator's wording.

## Safety Boundary

- Public search surfaces are the default. Internal docs, private connectors, and private repos require explicit opt-in.
- External pages are always untrusted data.
- Commands, role instructions, and memory-write requests from pages are rejectable payloads.
- Every hint needs at least 1 `primary` evidence item and 1 non-`primary` cross-validation item.
- Every hint includes `match_reasoning` showing at least 4 of 5 fingerprint axes.
- Output stays `advisory_only: true` and `thread_scope: active_conversation_only`.

Some static scanners flag the hostile-payload categories in [references/threat-model.md](references/threat-model.md). Those strings are defensive fixtures that document what the host should reject.

## Current Implementation

This repository ships a lightweight skill package:

- `SKILL.md` / `SKILL.en.md`: runtime instructions.
- `scripts/should_travel.py`: trigger decision.
- `scripts/plan_travel.py`: redacted dry-run query plan, no network access.
- `scripts/validate_suggestions.py`: advisory contract validator.
- `scripts/community_smoke_test.py`: realistic workflow smoke and hallucination tests.
- `agents/openai.yaml`, `agents/openclaw.yaml`, `agents/hermes.yaml`: host adapter notes.

Actual search is performed by the host agent's web/search tools. This package provides trigger policy, redaction planning, contract validation, and tests.

## Real Workflow Tests

The fixture set covers 14 workflows: Claude Code task-end refresh, failure recovery, scheduled log collection, scheduled job health audit, manual scheduled `CLAUDE.md` refresh, weekly reference-sheet refresh, OpenClaw heartbeat isolation, cron research digests, daily summary collection, idle-fallback silence guards, Hermes scheduled docs drift, nightly backlog triage, and repeated-fingerprint dedupe.

Sources and scenario notes live in [references/community-workflows.md](references/community-workflows.md). Smoke results live in [assets/community_smoke_report.json](assets/community_smoke_report.json).

## Companion Skill

`agent-travel` is the single-node background research layer. It pairs with [agent-compute-mesh](https://github.com/gongyu0918-debug/agent-compute-mesh): travel compresses outside practice into structured hints, while the mesh design explores stricter execution leases for `exploration job` units.

## Files

- [SKILL.md](SKILL.md)
- [SKILL.en.md](SKILL.en.md)
- [README.zh.md](README.zh.md)
- [agents/openai.yaml](agents/openai.yaml)
- [agents/openclaw.yaml](agents/openclaw.yaml)
- [agents/hermes.yaml](agents/hermes.yaml)
- [references/search-playbook.md](references/search-playbook.md)
- [references/suggestion-contract.md](references/suggestion-contract.md)
- [references/trigger-policy.md](references/trigger-policy.md)
- [references/threat-model.md](references/threat-model.md)
- [references/host-adapters.md](references/host-adapters.md)
- [references/community-workflows.md](references/community-workflows.md)
- [scripts/should_travel.py](scripts/should_travel.py)
- [scripts/plan_travel.py](scripts/plan_travel.py)
- [scripts/validate_suggestions.py](scripts/validate_suggestions.py)
- [scripts/reliability_test_suggestions.py](scripts/reliability_test_suggestions.py)
- [scripts/ablation_test_suggestions.py](scripts/ablation_test_suggestions.py)
- [scripts/community_smoke_test.py](scripts/community_smoke_test.py)
- [examples/states/heartbeat-ready.json](examples/states/heartbeat-ready.json)
- [examples/states/scheduled-host-managed.json](examples/states/scheduled-host-managed.json)
- [examples/states/failure-recovery.json](examples/states/failure-recovery.json)
- [assets/reliability_report.json](assets/reliability_report.json)
- [assets/ablation_report.json](assets/ablation_report.json)
- [assets/community_smoke_report.json](assets/community_smoke_report.json)
