---
name: epic-ai-swarm-orchestration
description: Production playbook for running parallel AI coding agents (Claude, Codex, Gemini) with automatic model selection via duty table, token-limit auto-fallback, human oversight, quality gates, and automated integration. Use when orchestrating multi-agent coding swarms, spawning parallel builders with review loops, managing model availability/rotation across vendors, or integrating branches from multiple AI agents. Triggers on phrases like "run the swarm", "spawn agents", "AI swarm", "multi-agent build", "duty table", "model rotation", "parallel coding agents".
---

# Epic AI Swarm Orchestration v3.2.1

Production system for running parallel AI coding agents with dynamic model selection, automatic token-limit failover, and quality gates.

## Prerequisites

### Required CLIs (on PATH)
- `tmux` — agent sandboxing (each agent in its own session)
- `git` — worktree creation, branching, commits, push
- `gh` — GitHub CLI (authenticated via `gh auth login`)
- `python3` — JSON manipulation (no pip packages)
- `openclaw` — notification delivery (Telegram/other)

### Model CLIs (at least one, authenticated)
- `claude` — Anthropic CLI (OAuth or API key)
- `codex` — OpenAI Codex CLI (optional)
- `gemini` — Google Gemini CLI (optional)

Scripts use host-authenticated CLIs — they do not store credentials.

## Quick Start

1. Copy `scripts/` to `~/workspace/swarm/`
2. Edit `scripts/swarm.conf` with notification target
3. Run `scripts/assess-models.sh` to initialize the duty table
4. Read [references/workflow.md](references/workflow.md) for the 3-phase workflow
5. Read [references/duty-table.md](references/duty-table.md) for model rotation system
6. Read [references/tools.md](references/tools.md) for spawn commands

## v3.2.1 Bookkeeping Fix

This release fixes a critical integration-watcher bookkeeping bug: `spawn-batch.sh` and `queue-watcher.sh` now record the actual tmux session emitted by `spawn-agent.sh` after duty-table/fallback resolution, instead of predicting names from the requested agent. `integration-watcher.sh` also refuses to treat unknown/misspelled expected sessions as complete.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DUTY TABLE                           │
│  assess-models.sh → duty-table.json (daily cron)       │
│  architect=claude/opus, builder=codex, reviewer=gemini  │
└───────────┬─────────────────────────────┬───────────────┘
            │                             │
    ┌───────▼───────┐           ┌─────────▼────────┐
    │ spawn-agent.sh│           │ spawn-batch.sh   │
    │ (single task) │           │ (parallel tasks)  │
    └───────┬───────┘           └────────┬─────────┘
            │  Reads role → agent/model  │
            │  from duty-table.json      │
    ┌───────▼────────────────────────────▼───────────┐
    │              RUNNER (in tmux)                    │
    │  On token limit → model-fallback.sh             │
    │  Auto-retry up to 2x with next available model  │
    │  Updates duty table for future spawns            │
    └───────┬─────────────────────────────────────────┘
            │
    ┌───────▼───────────────────────┐
    │  notify-on-complete.sh        │
    │  → auto-spawns reviewer       │
    │  → integration-watcher.sh     │
    │  → ESR + work log persistence │
    └───────────────────────────────┘
```

## Duty Table System

The duty table (`duty-table.json`) maps **roles** to **agents/models**:

| Role | Purpose | Default Assignment |
|------|---------|-------------------|
| architect | Planning, design | Claude Opus (best reasoning) |
| builder | Implementation | Codex or Claude Sonnet (fast) |
| reviewer | Code review + fixes | Gemini Flash or Sonnet |
| integrator | Branch merging | Claude Opus (deep thinking) |

### Auto-Assessment
`assess-models.sh` runs daily (or on-demand) to:
1. Test all models across all 3 vendors (45s timeout each)
2. Assign optimal 3-vendor spread to roles
3. If both Codex + Gemini down → fallback to all-Claude table

### Mid-Run Token Failover
When an agent hits a token/rate limit during execution:
1. Runner detects the error pattern in output
2. Calls `model-fallback.sh` with the role + failed model
3. Gets the next available model from the per-role fallback chain
4. Retries the task (up to 2 attempts)
5. Updates duty table so future spawns use the working model
6. Logs the switch to `pending-notifications.txt`

See [references/duty-table.md](references/duty-table.md) for full details.

## Core Scripts

| Script | Purpose |
|--------|---------|
| `spawn-agent.sh` | Spawn single agent (resolves role from duty table) |
| `spawn-batch.sh` | Spawn parallel agents with auto-queuing |
| `assess-models.sh` | Test models, update duty table |
| `model-fallback.sh` | Find next available model for a role |
| `fallback-swap.sh` | Pre-spawn primary/fallback test |
| `try-model.sh` | Quick model health check |
| `notify-on-complete.sh` | Watcher: auto-review + integration |
| `integration-watcher.sh` | Merge all branches after batch |
| `queue-watcher.sh` | Auto-spawn queued overflow tasks |
| `pulse-check.sh` | Detect stuck agents, auto-kill |
| `check-agents.sh` | Monitor all active agents |
| `endorse-task.sh` | Human endorsement gate |
| `esr-log.sh` | Engineering Status Report logging |
| `daily-standup.sh` | Daily status summary |
| `cleanup.sh` | Remove old worktrees + logs |

## Workflow

### Phase 1: PLAN (Architect)
- Read project context, ESR, codebase
- Break work into parallel tasks with prompts
- Present plan to human → **HOLD** until endorsed

### Phase 2: BUILD + REVIEW (Builder + Reviewer)
- `spawn-batch.sh` deploys agents in tmux + worktrees
- Each agent codes autonomously with structured work log
- `notify-on-complete.sh` auto-spawns reviewer (max 3 fix loops)
- Token limits trigger automatic model switch mid-run

### Phase 3: SHIP (Integrator)
- `integration-watcher.sh` merges all branches sequentially
- Conflict resolution, build verification
- ESR + work log persisted to project history
- Telegram notification with shipped summary

## Configuration

`swarm.conf`:
```bash
SWARM_NOTIFY_TARGET="<telegram-user-id>"
SWARM_NOTIFY_CHANNEL="telegram"
SWARM_MAX_CONCURRENT=8
```

## Endorsement System

Every task requires human approval before agents spawn:
```bash
endorse-task.sh <task-id>           # Single task
spawn-batch.sh ... <tasks.json>     # Batch endorsement (auto per-task)
```

30-second cooldown between endorsement and spawn prevents accidental double-runs.
