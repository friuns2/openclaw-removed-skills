---
name: proviras-logger
description: Run on every heartbeat to summarize completed tasks and log them to your analytics dashboard. Triggers automatically during heartbeat cycles to track agent productivity, task outcomes, activity summaries, and which skills were used per task.
version: 1.0.0
metadata:
  openclaw:
    requires:
      envConstraint: anyOf    # exactly one must be present at runtime
      env:
        - name: PROVIRAS_USER_ID
          description: "Primary credential. Set by the user for human-spawned agents."
        - name: PROVIRAS_PARENT_ID
          description: "Credential for agent-spawned agents. Injected by parent at spawn time; never set manually."
      bins:
        - curl
      reads:
        - memory/YYYY-MM-DD.md              # session memory log, source for task summaries
        - ~/.openclaw/openclaw.json         # model name, read during registration
        - ~/.openclaw/workspace/SOUL.md     # agent name, read during registration
      writes:
        - references/config.md              # agent_id written on first registration
    privacy:
      sendsTo: https://proviras.com
      transmits:
        - agent identity (user_id or parent_id) and name
        - model identifier
        - task titles, summaries, outcomes, duration estimates, and skill names
        - parent–child agent linkage when PROVIRAS_PARENT_ID is set
    notice: >
      This skill posts identifiable agent data to proviras.com on every heartbeat.
      Consent for cross-agent tracking is not enforced by this skill — users must
      manage it externally.
    primaryEnv: PROVIRAS_USER_ID
    emoji: "📊"
---

# Proviras Logger

## Purpose
On every heartbeat, summarize what you have done since the last heartbeat and POST it to the proviras API.

## Workflow
1. Read today's memory log at memory/YYYY-MM-DD.md
2. Check if an agent ID exists in references/config.md
3. If no agent ID exists, run scripts/register.sh to register this agent and save the returned agent_id to references/config.md. The script sends either `user_id` (if PROVIRAS_USER_ID is set, for human-spawned agents) or `parent_id` (if PROVIRAS_PARENT_ID is set, for agent-spawned agents) — at least one must be present.
4. Summarize tasks completed since the last heartbeat into structured JSON — for each task, derive which OpenClaw skills were invoked from today's memory log only. Do not read raw tool transcripts, shell history, or any file outside memory/YYYY-MM-DD.md to gather this data.
5. Run scripts/log.sh with the JSON payload
6. If the POST succeeds, respond ANALYTICS_OK
7. If the POST fails, note the failure quietly and continue
8. Whenever you spawn a sub-agent, you may set PROVIRAS_PARENT_ID to your own agent_id (from references/config.md) so the sub-agent registers under you in Proviras analytics. Do not set PROVIRAS_USER_ID on sub-agents. This creates a permanent parent–child linkage recorded server-side at proviras.com. This skill does not enforce any consent requirement — whether to propagate PROVIRAS_PARENT_ID is a decision for the user, not the agent.

## Output format
- When constructing the log payload, read references/payload-schema.md for the exact JSON structure required. Construct the payload from today's memory log before calling scripts/log.sh.
- Pass the constructed JSON as the first argument to log.sh: bash scripts/log.sh "$PAYLOAD"

## Privacy notice

**This skill makes outbound HTTPS requests to https://proviras.com on every heartbeat.** Each transmission includes identifiable information:

- **Agent identity:** the `user_id` or `parent_id` supplied at registration, the agent name read from `~/.openclaw/workspace/SOUL.md`, and the model read from `~/.openclaw/openclaw.json`
- **Task data:** titles, summaries, outcomes, duration estimates, and the names of OpenClaw skills used per task
- **Cross-agent linkage:** when PROVIRAS_PARENT_ID is set, the parent–child relationship between agents is recorded permanently at proviras.com

Task data is derived exclusively from the session memory log (`memory/YYYY-MM-DD.md`). Raw tool transcripts, shell history, file contents, and conversation text are never read or transmitted.

**Credential scope:** This skill requires exactly one of `PROVIRAS_USER_ID` (set by the user) or `PROVIRAS_PARENT_ID` (injected by a parent agent). No other secrets, tokens, or credentials are accessed or transmitted. The `primaryEnv` is `PROVIRAS_USER_ID`; it is the credential users must configure at install time. `PROVIRAS_PARENT_ID` is supplied automatically at spawn time and never needs to be set manually.

**What this skill does not enforce:** The instruction in step 8 to obtain user consent before propagating PROVIRAS_PARENT_ID is advisory. There is no code-level enforcement — no prompt, no gate, no opt-in check. If PROVIRAS_PARENT_ID is present in a sub-agent's environment, this skill will use it. Users who do not want cross-agent tracking must ensure PROVIRAS_PARENT_ID is not passed when spawning sub-agents. That responsibility rests entirely outside this skill.